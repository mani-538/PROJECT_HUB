"""
app.py - Flask Application Factory for Project Hub
"""
import os
from flask import Flask, render_template
from flask_login import LoginManager
from models import db, User
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

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
        _seed_admin(app)

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

    return app


def _seed_admin(app):
    """Create a default admin account if none exists."""
    with app.app_context():
        if not User.query.filter_by(role='admin').first():
            admin = User(
                username='admin',
                email='admin@projecthub.com',
                role='admin',
                name='System Administrator',
                department='Administration'
            )
            admin.set_password('Admin@123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin created: admin@projecthub.com / Admin@123")


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
