"""
utils/csrf.py - Lightweight, Zero-Dependency CSRF Protection
Provides session-backed CSRF validation matching Flask-WTF conventions.
"""
import secrets
import hmac
from flask import session, request, abort, current_app


def generate_csrf():
    """Generate or retrieve the active CSRF token for the current session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def rotate_csrf_token():
    """Generate a new CSRF token and replace the current session token."""
    session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


class CSRFProtect:
    """CSRF protection extension."""

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.jinja_env.globals['csrf_token'] = generate_csrf

        @app.before_request
        def _csrf_protect():
            if not app.config.get('WTF_CSRF_ENABLED', True):
                return None

            # Skip safe HTTP methods
            if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
                return None

            # Skip explicitly exempt endpoints
            if request.endpoint:
                view_func = app.view_functions.get(request.endpoint)
                if view_func and getattr(view_func, '_csrf_exempt', False):
                    return None

            expected_token = session.get('_csrf_token')

            # Extract client token from form or custom headers
            client_token = (
                request.form.get('csrf_token') or
                request.headers.get('X-CSRFToken') or
                request.headers.get('X-CSRF-Token')
            )

            if not client_token and request.is_json:
                json_data = request.get_json(silent=True)
                if isinstance(json_data, dict):
                    client_token = json_data.get('csrf_token')

            if not expected_token or not client_token:
                abort(400, description="CSRF token missing.")

            if not hmac.compare_digest(str(expected_token), str(client_token)):
                abort(400, description="CSRF token invalid.")

    @staticmethod
    def exempt(view):
        """Mark a view function as exempt from CSRF protection."""
        view._csrf_exempt = True
        return view
