"""
app.py - Flask Application Factory for Project Hub
"""
import os
import click
from flask import Flask, render_template, send_from_directory, request, jsonify
from flask_login import LoginManager
from models import db, User
from config import Config
from utils.csrf import CSRFProtect

csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        user = User.query.get(int(user_id))
        if user is None or user.is_blocked or not user.is_active:
            return None
        return user

    # Register blueprints
    from routes.auth import auth
    from routes.student import student
    from routes.admin import admin
    app.register_blueprint(auth)
    app.register_blueprint(student)
    app.register_blueprint(admin)

    # Ensure upload directories exist
    for folder in [
        app.config['PROFILE_IMAGE_FOLDER'],
        app.config['RESUME_FOLDER'],
        app.config['PROJECT_FILE_FOLDER'],
        app.config['CERTIFICATE_FOLDER'],
    ]:
        os.makedirs(folder, exist_ok=True)

    # Create database tables
    with app.app_context():
        db.create_all()

    # CLI command: create-admin
    @app.cli.command('create-admin')
    @click.option('--username', prompt=True, help='Admin username')
    @click.option('--email', prompt=True, help='Admin email address')
    @click.password_option(help='Admin password')
    @click.option('--name', default='System Administrator', prompt=True, help='Full name')
    @click.option('--department', default='Administration', prompt=True, help='Department')
    def create_admin_command(username, email, password, name, department):
        """Create an administrator account securely without overwriting existing accounts."""
        username = username.strip()
        email = email.strip().lower()

        if not username or not email or not password:
            click.secho("Error: Username, email, and password cannot be empty.", fg="red")
            return

        existing = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing:
            click.secho(
                f"Error: Account with username '{username}' or email '{email}' already exists. "
                "Existing accounts are never overwritten.",
                fg="yellow"
            )
            return

        admin_user = User(
            username=username,
            email=email,
            role='admin',
            name=name.strip(),
            department=department.strip()
        )
        admin_user.set_password(password)
        db.session.add(admin_user)
        db.session.commit()
        click.secho(f"Successfully created admin account: {username} ({email})", fg="green")

    @app.cli.command('init-db')
    @click.option('--seed-trial-accounts/--no-seed', default=True, help='Seed initial trial admin and student accounts if absent')
    def init_db_command(seed_trial_accounts):
        """Safely create database tables and seed trial accounts if absent."""
        db.create_all()
        click.secho("Database tables verified / created successfully.", fg="green")
        if seed_trial_accounts:
            # Seed trial admin if absent
            admin = User.query.filter_by(role='admin').first()
            if not admin:
                trial_admin = User(
                    username="trial_admin",
                    name="Trial Administrator",
                    email="admin@projecthub.com",
                    role="admin",
                    department="Administration"
                )
                admin_pw = os.environ.get('INITIAL_ADMIN_PASSWORD', 'AdminTrial@ProjectHub2026')
                trial_admin.set_password(admin_pw)
                db.session.add(trial_admin)
                click.secho("Created trial admin account (admin@projecthub.com).", fg="green")
            else:
                click.secho(f"Admin account already exists ({admin.email}). Skipped.", fg="cyan")

            # Seed trial student if absent
            student = User.query.filter_by(role='student').first()
            if not student:
                trial_student = User(
                    username="trial_student",
                    name="Trial Student",
                    email="student@projecthub.com",
                    role="student",
                    college="Project Hub Demo Academy",
                    department="Computer Science & Engineering",
                    year="Final Year",
                    bio="Trial student account for testing and exploring Project Hub features."
                )
                trial_student.set_password(os.environ.get('INITIAL_STUDENT_PASSWORD', 'Student@123'))
                db.session.add(trial_student)
                click.secho("Created trial student account (student@projecthub.com).", fg="green")
            else:
                click.secho(f"Student account already exists ({student.email}). Skipped.", fg="cyan")

            db.session.commit()

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    # Health Check
    @app.route('/health')
    def health():
        db_status = 'ok'
        try:
            db.session.execute(db.text('SELECT 1'))
        except Exception:
            db_status = 'unavailable'
        status_code = 200 if db_status == 'ok' else 503
        return jsonify({
            'status': 'healthy' if db_status == 'ok' else 'degraded',
            'database': db_status
        }), status_code

    # SEO Routes
    @app.route('/robots.txt')
    @app.route('/sitemap.xml')
    @app.route('/googled4c284a321eea07d.html')
    def static_from_root():
        return send_from_directory(app.static_folder, request.path[1:])

    return app


if __name__ == '__main__':
    app = create_app()
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() in ('true', '1', 'yes')
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

