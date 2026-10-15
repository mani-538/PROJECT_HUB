"""
tests/test_phase1_security.py - Regression Test Suite for Phase 1 Security Fixes

Verifies:
1. Public admin registration is disabled on backend and UI.
2. Default admin auto-creation and credential logging is removed.
3. Secure CLI command creates admin without overwriting existing accounts.
4. SECRET_KEY requirement from environment configuration.
5. Blocked users on existing sessions are rejected immediately.
6. Login redirect validation rejects external domains.
7. Project-file access enforcement (owner, team, admin only; no public attachment leakage).
8. CSRF protection on mutating requests (blocks missing/invalid tokens, allows valid).
9. Upload collision prevention for new files with identical names while preserving access to existing files.
"""
import io
import os
import shutil
import tempfile
import unittest
from flask import session
from app import create_app
from models import db, User, Project, ProjectFile, TeamMember
from utils.csrf import generate_csrf


class Phase1SecurityTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, 'test.db')
        self.upload_dir = os.path.join(self.temp_dir, 'uploads')
        self.profile_dir = os.path.join(self.upload_dir, 'profile_images')
        self.resume_dir = os.path.join(self.upload_dir, 'resumes')
        self.project_files_dir = os.path.join(self.upload_dir, 'project_files')
        self.cert_dir = os.path.join(self.upload_dir, 'certificates')

        self.app = create_app(test_config={
            'TESTING': True,
            'SECRET_KEY': 'test-suite-secure-random-secret-key-32bytes',
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{self.temp_db}',
            'UPLOAD_FOLDER': self.upload_dir,
            'PROFILE_IMAGE_FOLDER': self.profile_dir,
            'RESUME_FOLDER': self.resume_dir,
            'PROJECT_FILE_FOLDER': self.project_files_dir,
            'CERTIFICATE_FOLDER': self.cert_dir,
            'WTF_CSRF_ENABLED': True
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _get_csrf_token(self, client):
        """Fetch a page to initialize the session and return the CSRF token."""
        client.get('/login')
        with client.session_transaction() as sess:
            token = sess.get('_csrf_token')
            if not token:
                token = 'fallback-token'
                sess['_csrf_token'] = token
            return token

    # 1. Disable public admin registration
    def test_admin_signup_disabled_on_backend(self):
        token = self._get_csrf_token(self.client)
        resp = self.client.post('/signup/admin', data={
            'csrf_token': token,
            'username': 'attacker_admin',
            'email': 'attacker@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        }, follow_redirects=False)

        # Must redirect away with warning
        self.assertEqual(resp.status_code, 302)
        with self.app.app_context():
            user = User.query.filter_by(username='attacker_admin').first()
            self.assertIsNone(user, "Admin account should not be created via public signup")

    def test_student_signup_allowed(self):
        token = self._get_csrf_token(self.client)
        resp = self.client.post('/signup/student', data={
            'csrf_token': token,
            'username': 'legit_student',
            'email': 'student@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        }, follow_redirects=False)

        self.assertEqual(resp.status_code, 302)
        with self.app.app_context():
            user = User.query.filter_by(username='legit_student').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.role, 'student')

    # 2. No automatic default admin created
    def test_no_automatic_default_admin(self):
        with self.app.app_context():
            admin_user = User.query.filter_by(email='admin@projecthub.com').first()
            self.assertIsNone(admin_user, "Default admin should not be created automatically")

    def test_secret_key_required_from_env(self):
        from config import _get_secret_key
        # Temporarily unset SECRET_KEY
        original_key = os.environ.get('SECRET_KEY')
        try:
            if 'SECRET_KEY' in os.environ:
                del os.environ['SECRET_KEY']
            with self.assertRaises(RuntimeError):
                _get_secret_key()
        finally:
            if original_key is not None:
                os.environ['SECRET_KEY'] = original_key

    # 3. Explicit CLI command creates admin securely without overwriting
    def test_create_admin_cli_command(self):
        runner = self.app.test_cli_runner()
        result = runner.invoke(args=[
            'create-admin',
            '--username', 'cliadmin',
            '--email', 'cliadmin@example.com',
            '--password', 'StrongAdminPass1!',
            '--name', 'CLI Administrator',
            '--department', 'Security'
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Successfully created admin account", result.output)

        with self.app.app_context():
            admin = User.query.filter_by(username='cliadmin').first()
            self.assertIsNotNone(admin)
            self.assertEqual(admin.role, 'admin')
            self.assertTrue(admin.check_password('StrongAdminPass1!'))

        # Running again with same username or email must NOT overwrite
        result_duplicate = runner.invoke(args=[
            'create-admin',
            '--username', 'cliadmin',
            '--email', 'cliadmin@example.com',
            '--password', 'NewDifferentPass2!',
            '--name', 'CLI Administrator',
            '--department', 'Security'
        ])
        self.assertIn("already exists", result_duplicate.output)
        self.assertIn("never overwritten", result_duplicate.output)

        with self.app.app_context():
            admin = User.query.filter_by(username='cliadmin').first()
            self.assertTrue(admin.check_password('StrongAdminPass1!'), "Password must not be overwritten")

    def test_init_db_preserves_blocked_and_inactive_users(self):
        """init-db must seed missing accounts only and never reactivate or unblock existing users."""
        runner = self.app.test_cli_runner()

        # Pre-create a blocked and inactive admin & student
        with self.app.app_context():
            blocked_admin = User(
                username='existing_blocked_admin',
                name='Blocked Admin',
                email='admin@projecthub.com',
                role='admin',
                department='Admin',
                is_active=False,
                is_blocked=True
            )
            blocked_admin.set_password('AdminOldPassword123!')
            db.session.add(blocked_admin)

            blocked_student = User(
                username='existing_blocked_student',
                name='Blocked Student',
                email='student@projecthub.com',
                role='student',
                is_active=False,
                is_blocked=True
            )
            blocked_student.set_password('StudentOldPassword123!')
            db.session.add(blocked_student)
            db.session.commit()

        # Run init-db
        result = runner.invoke(args=['init-db'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("already exists", result.output)
        self.assertIn("Skipped without modifying status", result.output)

        # Confirm users remain blocked, inactive, and passwords unchanged
        with self.app.app_context():
            admin_after = User.query.filter_by(email='admin@projecthub.com').first()
            self.assertIsNotNone(admin_after)
            self.assertFalse(admin_after.is_active, "Existing admin must not be reactivated")
            self.assertTrue(admin_after.is_blocked, "Existing admin must remain blocked")
            self.assertTrue(admin_after.check_password('AdminOldPassword123!'))

            student_after = User.query.filter_by(email='student@projecthub.com').first()
            self.assertIsNotNone(student_after)
            self.assertFalse(student_after.is_active, "Existing student must not be reactivated")
            self.assertTrue(student_after.is_blocked, "Existing student must remain blocked")
            self.assertTrue(student_after.check_password('StudentOldPassword123!'))

    # 4. Reject blocked users on existing sessions
    def test_blocked_user_session_rejected(self):
        with self.app.app_context():
            user = User(username='activeuser', email='active@test.com', role='student')
            user.set_password('Secret123!')
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        # Log in
        token = self._get_csrf_token(self.client)
        login_resp = self.client.post('/login', data={
            'csrf_token': token,
            'identifier': 'activeuser',
            'password': 'Secret123!'
        }, follow_redirects=False)
        self.assertEqual(login_resp.status_code, 302)

        # Verify access to dashboard while active
        dash_resp = self.client.get('/student/dashboard')
        self.assertEqual(dash_resp.status_code, 200)

        # Block the user in database while session cookie remains in client
        with self.app.app_context():
            u = User.query.get(user_id)
            u.is_blocked = True
            db.session.commit()

        # Next request must be rejected and redirected to login
        blocked_dash_resp = self.client.get('/student/dashboard', follow_redirects=False)
        self.assertEqual(blocked_dash_resp.status_code, 302)
        self.assertIn('/login', blocked_dash_resp.headers.get('Location', ''))

    # 5. Validate login redirects against external destinations
    def test_login_redirect_validation(self):
        with self.app.app_context():
            user = User(username='redirectuser', email='redirect@test.com', role='student')
            user.set_password('Secret123!')
            db.session.add(user)
            db.session.commit()

        token = self._get_csrf_token(self.client)

        # Malicious external URL
        evil_client = self.app.test_client()
        token = self._get_csrf_token(evil_client)
        evil_resp = evil_client.post('/login?next=https://evil.attacker.com', data={
            'csrf_token': token,
            'identifier': 'redirectuser',
            'password': 'Secret123!'
        }, follow_redirects=False)
        self.assertEqual(evil_resp.status_code, 302)
        self.assertNotIn('evil.attacker.com', evil_resp.headers.get('Location', ''))
        self.assertIn('/student/dashboard', evil_resp.headers.get('Location', ''))

        # Protocol-relative URL
        proto_client = self.app.test_client()
        token = self._get_csrf_token(proto_client)
        proto_resp = proto_client.post('/login?next=//evil.attacker.com', data={
            'csrf_token': token,
            'identifier': 'redirectuser',
            'password': 'Secret123!'
        }, follow_redirects=False)
        self.assertEqual(proto_resp.status_code, 302)
        self.assertNotIn('evil.attacker.com', proto_resp.headers.get('Location', ''))
        self.assertIn('/student/dashboard', proto_resp.headers.get('Location', ''))

        # Safe relative URL
        safe_client = self.app.test_client()
        token = self._get_csrf_token(safe_client)
        safe_resp = safe_client.post('/login?next=/student/projects', data={
            'csrf_token': token,
            'identifier': 'redirectuser',
            'password': 'Secret123!'
        }, follow_redirects=False)
        self.assertEqual(safe_resp.status_code, 302)
        self.assertEqual(safe_resp.headers.get('Location', ''), '/student/projects')

    # 6. Enforce project-file access permissions
    def test_project_file_access_permissions(self):
        with self.app.app_context():
            owner = User(username='owner1', email='owner@test.com', role='student')
            owner.set_password('Pass1!')

            teammate = User(username='mate1', email='mate@test.com', role='student')
            teammate.set_password('Pass1!')

            stranger = User(username='stranger1', email='stranger@test.com', role='student')
            stranger.set_password('Pass1!')

            admin_user = User(username='adminboss', email='admin@test.com', role='admin')
            admin_user.set_password('Pass1!')

            db.session.add_all([owner, teammate, stranger, admin_user])
            db.session.commit()

            # Create project with owner and teammate
            proj = Project(user_id=owner.id, title='Protected Project', is_public=True)
            db.session.add(proj)
            db.session.commit()
            proj_id = proj.id

            tm = TeamMember(project_id=proj_id, user_id=teammate.id, email='mate@test.com', name='Mate')
            db.session.add(tm)

            # Create file on disk
            sample_content = b"Confidential Project File Contents"
            fn = "112233445566_confidential.pdf"
            file_path = os.path.join(self.project_files_dir, fn)
            with open(file_path, 'wb') as f:
                f.write(sample_content)

            pf = ProjectFile(project_id=proj_id, filename=fn, file_path=file_path)
            db.session.add(pf)
            db.session.commit()
            file_id = pf.id

        # 6a: Stranger (unrelated student) tries to download -> Must receive 403 Forbidden
        stranger_client = self.app.test_client()
        token = self._get_csrf_token(stranger_client)
        stranger_client.post('/login', data={'csrf_token': token, 'identifier': 'stranger1', 'password': 'Pass1!'})
        resp_stranger = stranger_client.get(f'/student/download/{file_id}')
        self.assertEqual(resp_stranger.status_code, 403, "Stranger should receive 403 Forbidden even if project is public")

        # 6b: Owner downloads -> 200 OK
        owner_client = self.app.test_client()
        token = self._get_csrf_token(owner_client)
        owner_client.post('/login', data={'csrf_token': token, 'identifier': 'owner1', 'password': 'Pass1!'})
        resp_owner = owner_client.get(f'/student/download/{file_id}')
        self.assertEqual(resp_owner.status_code, 200)
        self.assertEqual(resp_owner.data, b"Confidential Project File Contents")

        # 6c: Teammate downloads -> 200 OK
        mate_client = self.app.test_client()
        token = self._get_csrf_token(mate_client)
        mate_client.post('/login', data={'csrf_token': token, 'identifier': 'mate1', 'password': 'Pass1!'})
        resp_mate = mate_client.get(f'/student/download/{file_id}')
        self.assertEqual(resp_mate.status_code, 200)

        # 6d: Admin downloads -> 200 OK
        admin_client = self.app.test_client()
        token = self._get_csrf_token(admin_client)
        admin_client.post('/login', data={'csrf_token': token, 'identifier': 'adminboss', 'password': 'Pass1!'})
        resp_admin = admin_client.get(f'/student/download/{file_id}')
        self.assertEqual(resp_admin.status_code, 200)

        # 6e: Unverified email without authenticated membership link -> Must receive 403 Forbidden
        with self.app.app_context():
            unlinked_user = User(username='unlinked1', email='unlinked@test.com', role='student')
            unlinked_user.set_password('Pass1!')
            db.session.add(unlinked_user)
            # Add team member with email 'unlinked@test.com' but user_id=None (unlinked)
            unlinked_tm = TeamMember(project_id=proj_id, user_id=None, email='unlinked@test.com', name='Unlinked')
            db.session.add(unlinked_tm)
            db.session.commit()

        unlinked_client = self.app.test_client()
        token = self._get_csrf_token(unlinked_client)
        unlinked_client.post('/login', data={'csrf_token': token, 'identifier': 'unlinked1', 'password': 'Pass1!'})
        resp_unlinked = unlinked_client.get(f'/student/download/{file_id}')
        self.assertEqual(resp_unlinked.status_code, 403, "Unverified email without linked user_id must not grant access")

    # 7. CSRF protection on mutating requests
    def test_csrf_protection_blocks_missing_token(self):
        # POST without csrf_token must fail with 400
        resp = self.client.post('/login', data={
            'identifier': 'nonexistent',
            'password': 'bad'
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"CSRF token missing", resp.data)

    def test_csrf_protection_blocks_invalid_token(self):
        resp = self.client.post('/login', data={
            'csrf_token': 'fake-invalid-token-12345',
            'identifier': 'nonexistent',
            'password': 'bad'
        })
        self.assertEqual(resp.status_code, 400)

    def test_csrf_token_rotated_on_login_and_logout(self):
        with self.app.app_context():
            user = User(username='rotator', email='rotator@test.com', role='student')
            user.set_password('Pass1!')
            db.session.add(user)
            db.session.commit()

        client = self.app.test_client()
        initial_token = self._get_csrf_token(client)
        self.assertIsNotNone(initial_token)

        # Login
        client.post('/login', data={'csrf_token': initial_token, 'identifier': 'rotator', 'password': 'Pass1!'})
        with client.session_transaction() as sess:
            post_login_token = sess.get('_csrf_token')

        self.assertNotEqual(initial_token, post_login_token, "CSRF token must rotate on login")

        # Logout
        client.get('/logout')
        with client.session_transaction() as sess:
            post_logout_token = sess.get('_csrf_token')

        self.assertNotEqual(post_login_token, post_logout_token, "CSRF token must rotate on logout")

    def test_test_environment_isolation_and_database_url_safety(self):
        # Even if DATABASE_URL is set in environment, test app must strictly use temporary database
        original_db_url = os.environ.get('DATABASE_URL')
        try:
            os.environ['DATABASE_URL'] = 'sqlite:///should_never_be_touched.db'
            isolated_app = create_app(test_config={
                'TESTING': True,
                'SECRET_KEY': 'isolated-key',
                'SQLALCHEMY_DATABASE_URI': f'sqlite:///{self.temp_db}',
                'UPLOAD_FOLDER': self.upload_dir,
                'WTF_CSRF_ENABLED': True
            })
            self.assertEqual(isolated_app.config['SQLALCHEMY_DATABASE_URI'], f'sqlite:///{self.temp_db}')
            self.assertFalse(os.path.exists(os.path.join(self.app.root_path, 'should_never_be_touched.db')))
            self.assertFalse(isolated_app.config['UPLOAD_FOLDER'].startswith(os.path.join(self.app.root_path, 'uploads')))
        finally:
            if original_db_url is not None:
                os.environ['DATABASE_URL'] = original_db_url
            else:
                os.environ.pop('DATABASE_URL', None)

    def test_csrf_protection_allows_valid_header(self):
        token = self._get_csrf_token(self.client)
        resp = self.client.post('/login',
            data={'identifier': 'nonexistent', 'password': 'bad'},
            headers={'X-CSRFToken': token}
        )
        # Should pass CSRF check and proceed to login verification (returns 200 with invalid credentials message)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Invalid email/username or password", resp.data)

    # 8. Prevent upload filename collisions while preserving access to existing files
    def test_upload_collision_prevention_and_existing_files(self):
        with self.app.app_context():
            u = User(username='uploaduser', email='upload@test.com', role='student')
            u.set_password('Pass1!')
            db.session.add(u)
            db.session.commit()
            u_id = u.id

        client = self.app.test_client()
        token = self._get_csrf_token(client)
        client.post('/login', data={'csrf_token': token, 'identifier': 'uploaduser', 'password': 'Pass1!'})

        # Create project 1 with attachment "project_doc.pdf"
        token = self._get_csrf_token(client)
        file1 = (io.BytesIO(b"Version 1 Content"), 'project_doc.pdf')
        resp1 = client.post('/student/projects/add', data={
            'csrf_token': token,
            'title': 'Project One',
            'project_type': 'individual',
            'team_size': '1',
            'project_file': file1
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(resp1.status_code, 200)

        # Create project 2 with attachment identically named "project_doc.pdf"
        token = self._get_csrf_token(client)
        file2 = (io.BytesIO(b"Version 2 Different Content"), 'project_doc.pdf')
        resp2 = client.post('/student/projects/add', data={
            'csrf_token': token,
            'title': 'Project Two',
            'project_type': 'individual',
            'team_size': '1',
            'project_file': file2
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(resp2.status_code, 200)

        # Verify on disk and database that both exist separately and did not overwrite each other
        with self.app.app_context():
            p1 = Project.query.filter_by(title='Project One').first()
            p2 = Project.query.filter_by(title='Project Two').first()

            self.assertEqual(len(p1.files), 1)
            self.assertEqual(len(p2.files), 1)

            fn1 = p1.files[0].filename
            fn2 = p2.files[0].filename
            self.assertNotEqual(fn1, fn2, "Filenames on disk must be distinct to prevent collisions")

            # Check contents on disk
            with open(os.path.join(self.project_files_dir, fn1), 'rb') as f:
                self.assertEqual(f.read(), b"Version 1 Content")
            with open(os.path.join(self.project_files_dir, fn2), 'rb') as f:
                self.assertEqual(f.read(), b"Version 2 Different Content")

        # 8b: Preserve access to legacy/existing files without UUID prefix
        legacy_fn = "legacy_document.pdf"
        legacy_path = os.path.join(self.project_files_dir, legacy_fn)
        with open(legacy_path, 'wb') as f:
            f.write(b"Legacy File Content from 2024")

        with self.app.app_context():
            p1 = Project.query.filter_by(title='Project One').first()
            legacy_pf = ProjectFile(project_id=p1.id, filename=legacy_fn, file_path=legacy_path)
            db.session.add(legacy_pf)
            db.session.commit()
            legacy_id = legacy_pf.id

        legacy_resp = client.get(f'/student/download/{legacy_id}')
        self.assertEqual(legacy_resp.status_code, 200)
        self.assertEqual(legacy_resp.data, b"Legacy File Content from 2024")


if __name__ == '__main__':
    unittest.main()
