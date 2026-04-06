"""
routes/auth.py - Authentication Blueprint
Handles role selection, signup, profile setup, login, and logout.
"""
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User
from utils.notifications import log_activity

auth = Blueprint('auth', __name__)


@auth.route('/', methods=['GET', 'POST'])
def role_select():
    """Role selection landing page."""
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
    return render_template('auth/role_select.html')


@auth.route('/signup/<role>', methods=['GET', 'POST'])
def signup(role):
    """Student or Admin signup."""
    if role not in ('student', 'admin'):
        return redirect(url_for('auth.role_select'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('auth/signup.html', role=role)

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/signup.html', role=role)

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/signup.html', role=role)

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('auth/signup.html', role=role)

        # Create user
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Store user id in session for profile setup
        session['new_user_id'] = user.id
        flash('Account created! Please complete your profile.', 'success')
        return redirect(url_for('auth.profile_setup'))

    return render_template('auth/signup.html', role=role)


@auth.route('/profile-setup', methods=['GET', 'POST'])
def profile_setup():
    """Personal details setup after signup."""
    user_id = session.get('new_user_id')
    if not user_id:
        return redirect(url_for('auth.role_select'))

    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('auth.role_select'))

    if request.method == 'POST':
        user.name       = request.form.get('name', '').strip()
        user.mobile     = request.form.get('mobile', '').strip()
        user.dob        = request.form.get('dob', '').strip()
        user.college    = request.form.get('college', '').strip()
        user.department = request.form.get('department', '').strip()
        user.year       = request.form.get('year', '').strip()
        user.bio        = request.form.get('bio', '').strip()

        db.session.commit()
        session.pop('new_user_id', None)
        log_activity(user.id, 'Completed profile setup', 'auth')
        flash('Profile complete! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/profile_setup.html', user=user)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('auth.role_select'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password   = request.form.get('password', '')
        remember   = True if request.form.get('remember') else False

        # Find user by email or username
        user = User.query.filter(
            (User.email == identifier.lower()) | (User.username == identifier)
        ).first()

        if not user or not user.check_password(password):
            flash('Invalid email/username or password.', 'danger')
            return render_template('auth/login.html')

        if user.is_blocked:
            flash('Your account has been blocked. Contact admin.', 'danger')
            return render_template('auth/login.html')

        login_user(user, remember=remember)
        log_activity(user.id, 'Logged in', 'auth')

        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))

    return render_template('auth/login.html')


@auth.route('/logout')
@login_required
def logout():
    """Logout."""
    log_activity(current_user.id, 'Logged out', 'auth')
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
