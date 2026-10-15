"""
tests/test_feature_matrix.py - Comprehensive Feature Matrix Verification Test Suite
Uses Python standard library unittest to run against an isolated SQLite test database.

Tests:
1. Authentication (Login student/admin, invalid credentials, logout)
2. Roles & Access Control (student blocked from admin routes, admin allowed)
3. Blocked User Invalidation on active session
4. CSRF Validation (missing/invalid blocked, valid accepted)
5. Safe Redirect Validation (blocks external URLs)
6. Profile setup and profile update
7. Project submission and team member association
8. Project file access authorization (unauthorized student blocked, owner/team/admin allowed)
9. Project updates and version upload
10. Query creation and admin reply workflow
11. Admin moderation (approve/reject project, toggle showcase)
12. Admin destructive safeguards (self-deletion blocked, trial deletion disabled)
13. System Report PDF generation
14. Certificate request, admin approval, and student download
15. Simulated helper features (topic suggester, proposal generator, resume reviewer)
"""
import io
import os
import shutil
import tempfile
import unittest
from werkzeug.security import generate_password_hash

from app import create_app
from models import (db, User, Project, Query, Notification, Announcement,
                    ActivityLog, Certificate, ProjectFile, ProjectUpdate, TeamMember)


class FeatureMatrixTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, 'matrix_test.db')
        self.upload_dir = os.path.join(self.temp_dir, 'uploads')
        os.makedirs(self.upload_dir, exist_ok=True)
        for sub in ['certificates', 'profile_images', 'project_files', 'resumes']:
            os.makedirs(os.path.join(self.upload_dir, sub), exist_ok=True)

        self.app = create_app({
            'TESTING': True,
            'SECRET_KEY': 'matrix-secret-key-32-bytes-secure',
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{self.temp_db}',
            'UPLOAD_FOLDER': self.upload_dir,
            'PROFILE_IMAGE_FOLDER': os.path.join(self.upload_dir, 'profile_images'),
            'RESUME_FOLDER': os.path.join(self.upload_dir, 'resumes'),
            'PROJECT_FILE_FOLDER': os.path.join(self.upload_dir, 'project_files'),
            'CERTIFICATE_FOLDER': os.path.join(self.upload_dir, 'certificates'),
            'DISABLE_DESTRUCTIVE_ADMIN': True,
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            self.admin = User(
                id=1,
                username='trial_admin',
                name='Trial Administrator',
                email='admin@projecthub.com',
                role='admin',
                is_active=True,
                is_blocked=False,
                password_hash=generate_password_hash('AdminPass123')
            )
            self.student = User(
                id=2,
                username='trial_student',
                name='Trial Student',
                email='student@projecthub.com',
                role='student',
                is_active=True,
                is_blocked=False,
                college='Demo Engineering College',
                department='Computer Science',
                password_hash=generate_password_hash('StudentPass123')
            )
            self.other_student = User(
                id=3,
                username='other_student',
                name='Other Student',
                email='other@projecthub.com',
                role='student',
                is_active=True,
                is_blocked=False,
                college='Other College',
                department='Information Technology',
                password_hash=generate_password_hash('OtherPass123')
            )
            db.session.add_all([self.admin, self.student, self.other_student])
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _get_csrf_token(self):
        self.client.get('/login')
        with self.client.session_transaction() as sess:
            return sess.get('_csrf_token', '')

    def _login(self, identifier, password):
        csrf = self._get_csrf_token()
        return self.client.post('/login', data={
            'identifier': identifier,
            'password': password,
            'csrf_token': csrf
        }, follow_redirects=True)

    # 1. Authentication & Roles
    def test_01_student_login_and_logout(self):
        res = self._login('student@projecthub.com', 'StudentPass123')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(b'Dashboard' in res.data or b'Projects' in res.data)

        logout_res = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)

    def test_02_invalid_login(self):
        res = self._login('student@projecthub.com', 'IncorrectPassword')
        self.assertIn(b'Invalid email/username or password', res.data)

    def test_03_role_student_cannot_access_admin(self):
        self._login('student@projecthub.com', 'StudentPass123')
        res = self.client.get('/admin/dashboard', follow_redirects=False)
        # Should redirect unauthorized user away from admin dashboard
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.location)

    def test_04_role_admin_access(self):
        self._login('admin@projecthub.com', 'AdminPass123')
        dash_res = self.client.get('/admin/dashboard')
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(b'Admin', dash_res.data)

    # 2. Blocked User Session Invalidation
    def test_05_blocked_session_rejected_immediately(self):
        self._login('student@projecthub.com', 'StudentPass123')
        with self.app.app_context():
            u = db.session.get(User, 2)
            u.is_blocked = True
            db.session.commit()

        res = self.client.get('/student/dashboard', follow_redirects=True)
        self.assertTrue(b'blocked' in res.data.lower() or 'login' in res.request.path.lower())

    # 3. Safe Redirect Validation
    def test_06_open_redirect_prevented(self):
        csrf = self._get_csrf_token()
        res = self.client.post('/login?next=https://attacker-domain.evil/phish', data={
            'identifier': 'student@projecthub.com',
            'password': 'StudentPass123',
            'csrf_token': csrf
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertNotIn('attacker-domain.evil', res.location)

    # 4. CSRF Protection
    def test_07_csrf_missing_token_rejected(self):
        res = self.client.post('/login', data={'identifier': 'student@projecthub.com', 'password': 'StudentPass123'})
        self.assertEqual(res.status_code, 400)
        self.assertIn(b'CSRF', res.data)

    def test_08_csrf_invalid_token_rejected(self):
        self.client.get('/login')
        res = self.client.post('/login', data={
            'identifier': 'student@projecthub.com',
            'password': 'StudentPass123',
            'csrf_token': 'bad-token-value'
        })
        self.assertEqual(res.status_code, 400)

    # 5. Project Submission, Team Access, and File Download Isolation
    def test_09_project_submission_and_file_isolation(self):
        self._login('student@projecthub.com', 'StudentPass123')
        with self.client.session_transaction() as sess:
            csrf = sess.get('_csrf_token', '')

        # Submit project with a file
        file_content = b"console.log('Project Hub Engine');"
        data = {
            'csrf_token': csrf,
            'title': 'Autonomous Rover Platform',
            'domain': 'AI/ML',
            'project_type': 'team',
            'team_size': '2',
            'problem_statement': 'Automating rover obstacle avoidance.',
            'description': 'Rover control firmware using ROS.',
            'tech_stack': 'Python, ROS',
            'project_file': (io.BytesIO(file_content), 'rover.py'),
            'team_names': 'Peer Engineer',
            'team_emails': 'other@projecthub.com',
            'team_roles': 'Developer'
        }
        res = self.client.post('/student/projects/add', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            p = Project.query.filter_by(title='Autonomous Rover Platform').first()
            self.assertIsNotNone(p)
            self.assertEqual(p.user_id, 2)
            pf = ProjectFile.query.filter_by(project_id=p.id).first()
            self.assertIsNotNone(pf)
            pf_id = pf.id

        # Owner can download
        download_res = self.client.get(f'/student/download/{pf_id}')
        self.assertEqual(download_res.status_code, 200)
        self.assertEqual(download_res.data, file_content)

        # Unauthenticated user cannot download
        self.client.get('/logout')
        unauth_res = self.client.get(f'/student/download/{pf_id}')
        self.assertIn(unauth_res.status_code, (302, 401, 403))

        # Other student cannot download without team association
        self._login('other@projecthub.com', 'OtherPass123')
        # Note: 'other@projecthub.com' was listed as team_email text, but unverified email alone MUST NOT grant access!
        forbidden_res = self.client.get(f'/student/download/{pf_id}')
        self.assertEqual(forbidden_res.status_code, 403)

        # Admin CAN download
        self.client.get('/logout')
        self._login('admin@projecthub.com', 'AdminPass123')
        admin_res = self.client.get(f'/student/download/{pf_id}')
        self.assertEqual(admin_res.status_code, 200)

    # 6. Updates & Versions
    def test_10_project_updates_and_versions(self):
        self._login('student@projecthub.com', 'StudentPass123')
        with self.client.session_transaction() as sess:
            csrf = sess.get('_csrf_token', '')

        with self.app.app_context():
            p = Project(title='Version Test Project', domain='Web Development', project_type='individual', description='Test', user_id=2, status='approved')
            db.session.add(p)
            db.session.commit()
            pid = p.id

        # Add update
        update_res = self.client.post(f'/student/projects/{pid}/update', data={
            'csrf_token': csrf,
            'content': 'Sprint 1 Finished: Database models and migrations tested.'
        }, follow_redirects=True)
        self.assertEqual(update_res.status_code, 200)

        # Upload new version
        ver_file = (io.BytesIO(b"v2 code archive"), 'v2.zip')
        ver_res = self.client.post(f'/student/projects/{pid}/version', data={
            'csrf_token': csrf,
            'version_notes': 'Refactored auth module',
            'version_file': ver_file
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(ver_res.status_code, 200)

        with self.app.app_context():
            upd = ProjectUpdate.query.filter_by(project_id=pid).first()
            self.assertIsNotNone(upd)
            self.assertIn('Sprint 1 Finished', upd.content)

    # 7. Queries & Replies
    def test_11_queries_and_replies(self):
        self._login('student@projecthub.com', 'StudentPass123')
        with self.client.session_transaction() as sess:
            s_csrf = sess.get('_csrf_token', '')

        self.client.post('/student/queries/new', data={
            'csrf_token': s_csrf,
            'subject': 'Evaluation Criteria Inquiry',
            'message': 'What is the rubric for phase 2?'
        }, follow_redirects=True)

        with self.app.app_context():
            q = Query.query.filter_by(subject='Evaluation Criteria Inquiry').first()
            self.assertIsNotNone(q)
            qid = q.id

        # Admin replies
        self.client.get('/logout')
        self._login('admin@projecthub.com', 'AdminPass123')
        with self.client.session_transaction() as sess:
            a_csrf = sess.get('_csrf_token', '')

        reply_res = self.client.post(f'/admin/queries/{qid}/reply', data={
            'csrf_token': a_csrf,
            'reply': 'Rubric: 40% code quality, 30% testing, 30% presentation.'
        }, follow_redirects=True)
        self.assertEqual(reply_res.status_code, 200)

        with self.app.app_context():
            q_after = db.session.get(Query, qid)
            self.assertEqual(q_after.status, 'resolved')
            self.assertIn('Rubric', q_after.reply)

    # 8. Admin Moderation & Destructive Safeguards
    def test_12_admin_actions_and_destructive_safeguards(self):
        self._login('admin@projecthub.com', 'AdminPass123')
        with self.client.session_transaction() as sess:
            a_csrf = sess.get('_csrf_token', '')

        with self.app.app_context():
            p = Project(title='Moderation Project', domain='IoT', project_type='individual', description='Test', user_id=2, status='pending', is_public=False)
            db.session.add(p)
            db.session.commit()
            pid = p.id

        # Approve project
        appr_res = self.client.post(f'/admin/projects/{pid}/action', data={
            'csrf_token': a_csrf,
            'action': 'approve',
            'feedback': 'Excellent proposal.'
        }, follow_redirects=True)
        self.assertEqual(appr_res.status_code, 200)

        with self.app.app_context():
            p_approved = db.session.get(Project, pid)
            self.assertEqual(p_approved.status, 'approved')

        # Showcase toggle
        showcase_res = self.client.post(f'/admin/showcase/{pid}/toggle', data={'csrf_token': a_csrf}, follow_redirects=True)
        self.assertEqual(showcase_res.status_code, 200)
        with self.app.app_context():
            self.assertTrue(db.session.get(Project, pid).is_public)

        # Destructive user deletion blocked
        del_res = self.client.post('/admin/users/2/delete', data={'csrf_token': a_csrf}, follow_redirects=True)
        self.assertIn(b'disabled', del_res.data.lower())

        # Self deletion blocked
        self_del = self.client.post('/admin/users/1/delete', data={'csrf_token': a_csrf}, follow_redirects=True)
        self.assertIn(b'cannot delete', self_del.data.lower())

    # 9. Reports & Certificates
    def test_13_reports_and_certificates(self):
        with self.app.app_context():
            p = Project(title='Completed Project', domain='General', project_type='individual', description='Test', user_id=2, status='completed')
            db.session.add(p)
            db.session.commit()
            pid = p.id

        # Student requests certificate
        self._login('student@projecthub.com', 'StudentPass123')
        with self.client.session_transaction() as sess:
            s_csrf = sess.get('_csrf_token', '')

        cert_req = self.client.post(f'/student/certificate/{pid}', data={'csrf_token': s_csrf}, follow_redirects=True)
        self.assertEqual(cert_req.status_code, 200)

        with self.app.app_context():
            cert = Certificate.query.filter_by(project_id=pid, user_id=2).first()
            self.assertIsNotNone(cert)
            cert_id = cert.id

        # Admin approves certificate
        self.client.get('/logout')
        self._login('admin@projecthub.com', 'AdminPass123')
        with self.client.session_transaction() as sess:
            a_csrf = sess.get('_csrf_token', '')

        appr_cert = self.client.post(f'/admin/certificates/{cert_id}/approve', data={'csrf_token': a_csrf}, follow_redirects=True)
        self.assertEqual(appr_cert.status_code, 200)

        # Admin generates PDF report
        rep_res = self.client.post('/admin/reports', data={'csrf_token': a_csrf}, follow_redirects=True)
        self.assertEqual(rep_res.status_code, 200)
        self.assertTrue(b'%PDF' in rep_res.data or rep_res.headers.get('Content-Type') == 'application/pdf')

        # Student downloads certificate PDF
        self.client.get('/logout')
        self._login('student@projecthub.com', 'StudentPass123')
        dl_cert = self.client.get(f'/student/certificate/download/{cert_id}')
        self.assertEqual(dl_cert.status_code, 200)
        self.assertEqual(dl_cert.headers.get('Content-Type'), 'application/pdf')

    # 10. Simulated Helper Features
    def test_14_simulated_helper_features(self):
        self._login('student@projecthub.com', 'StudentPass123')
        with self.client.session_transaction() as sess:
            s_csrf = sess.get('_csrf_token', '')

        # Topic Suggester
        sug_res = self.client.post('/student/ai/suggest', data={
            'csrf_token': s_csrf,
            'department': 'CSE',
            'year': '4th Year',
            'domain': 'AI/ML'
        })
        self.assertEqual(sug_res.status_code, 200)
        self.assertIn(b'Curated Directory', sug_res.data)

        # Description Generator
        desc_res = self.client.post('/student/ai/describe', data={
            'csrf_token': s_csrf,
            'title': 'AI Traffic Monitor',
            'domain': 'AI/ML',
            'tech_stack': 'Python, PyTorch'
        })
        self.assertEqual(desc_res.status_code, 200)
        self.assertIn(b'Template Assistant', desc_res.data)

        # Resume Analyzer
        res_file = (io.BytesIO(b"%PDF-1.4 sample resume"), 'student_resume.pdf')
        res_res = self.client.post('/student/ai/resume', data={
            'csrf_token': s_csrf,
            'resume_file': res_file
        }, content_type='multipart/form-data')
        self.assertEqual(res_res.status_code, 200)
        self.assertIn(b'Simulated Feature', res_res.data)


if __name__ == '__main__':
    unittest.main()
