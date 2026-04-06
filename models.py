"""
models.py - SQLAlchemy Database Models for Project Hub
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ─────────────────────────────────────────────
# USER MODEL
# ─────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id              = db.Column(db.Integer, primary_key=True)
    username        = db.Column(db.String(80), unique=True, nullable=False)
    email           = db.Column(db.String(120), unique=True, nullable=False)
    password_hash   = db.Column(db.String(256), nullable=False)
    role            = db.Column(db.String(20), default='student')  # student / admin / reviewer

    # Personal Details
    name            = db.Column(db.String(100))
    mobile          = db.Column(db.String(20))
    dob             = db.Column(db.String(20))
    college         = db.Column(db.String(200))
    department      = db.Column(db.String(100))
    year            = db.Column(db.String(10))
    bio             = db.Column(db.Text)

    # Files
    profile_image   = db.Column(db.String(300))
    resume          = db.Column(db.String(300))

    # Status
    is_active       = db.Column(db.Boolean, default=True)
    is_blocked      = db.Column(db.Boolean, default=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    projects        = db.relationship('Project', backref='owner', lazy=True, foreign_keys='Project.user_id')
    queries         = db.relationship('Query', backref='student', lazy=True)
    notifications   = db.relationship('Notification', backref='recipient', lazy=True)
    activity_logs   = db.relationship('ActivityLog', backref='actor', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


# ─────────────────────────────────────────────
# PROJECT MODEL
# ─────────────────────────────────────────────
class Project(db.Model):
    __tablename__ = 'projects'
    id                  = db.Column(db.Integer, primary_key=True)
    user_id             = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title               = db.Column(db.String(200), nullable=False)
    description         = db.Column(db.Text)
    project_type        = db.Column(db.String(20), default='individual')  # individual / team
    team_size           = db.Column(db.Integer, default=1)
    domain              = db.Column(db.String(100))
    problem_statement   = db.Column(db.Text)
    tech_stack          = db.Column(db.String(300))
    deadline            = db.Column(db.Date)
    github_link         = db.Column(db.String(300))
    status              = db.Column(db.String(30), default='pending')  # pending / approved / rejected / completed
    admin_feedback      = db.Column(db.Text)
    rating              = db.Column(db.Float)
    is_public           = db.Column(db.Boolean, default=True)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at          = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    files               = db.relationship('ProjectFile', backref='project', lazy=True, cascade='all, delete-orphan')
    updates             = db.relationship('ProjectUpdate', backref='project', lazy=True, cascade='all, delete-orphan')
    team_members        = db.relationship('TeamMember', backref='project', lazy=True, cascade='all, delete-orphan')
    certificate         = db.relationship('Certificate', backref='project', lazy=True, uselist=False)

    def __repr__(self):
        return f'<Project {self.title}>'


# ─────────────────────────────────────────────
# PROJECT FILE (VERSION CONTROL)
# ─────────────────────────────────────────────
class ProjectFile(db.Model):
    __tablename__ = 'project_files'
    id          = db.Column(db.Integer, primary_key=True)
    project_id  = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    filename    = db.Column(db.String(300))
    file_path   = db.Column(db.String(500))
    version     = db.Column(db.String(20), default='1.0')
    description = db.Column(db.String(300))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
# PROJECT UPDATE (DAILY LOG)
# ─────────────────────────────────────────────
class ProjectUpdate(db.Model):
    __tablename__ = 'project_updates'
    id          = db.Column(db.Integer, primary_key=True)
    project_id  = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    content     = db.Column(db.Text, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
# TEAM MEMBER
# ─────────────────────────────────────────────
class TeamMember(db.Model):
    __tablename__ = 'team_members'
    id          = db.Column(db.Integer, primary_key=True)
    project_id  = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    name        = db.Column(db.String(100))
    role        = db.Column(db.String(100))
    email       = db.Column(db.String(120))


# ─────────────────────────────────────────────
# QUERY SYSTEM
# ─────────────────────────────────────────────
class Query(db.Model):
    __tablename__ = 'queries'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject     = db.Column(db.String(200), nullable=False)
    message     = db.Column(db.Text, nullable=False)
    reply       = db.Column(db.Text)
    status      = db.Column(db.String(20), default='open')  # open / resolved
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    replied_at  = db.Column(db.DateTime)


# ─────────────────────────────────────────────
# NOTIFICATION
# ─────────────────────────────────────────────
class Notification(db.Model):
    __tablename__ = 'notifications'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message     = db.Column(db.Text, nullable=False)
    notif_type  = db.Column(db.String(50), default='info')  # info / warning / success / deadline
    is_read     = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
# ANNOUNCEMENT
# ─────────────────────────────────────────────
class Announcement(db.Model):
    __tablename__ = 'announcements'
    id          = db.Column(db.Integer, primary_key=True)
    admin_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    content     = db.Column(db.Text, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    admin       = db.relationship('User', foreign_keys=[admin_id])


# ─────────────────────────────────────────────
# ACTIVITY LOG
# ─────────────────────────────────────────────
class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action      = db.Column(db.String(300), nullable=False)
    category    = db.Column(db.String(50), default='general')  # project / auth / admin / query
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
# CERTIFICATE
# ─────────────────────────────────────────────
class Certificate(db.Model):
    __tablename__ = 'certificates'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id  = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    status      = db.Column(db.String(20), default='pending')  # pending / approved / rejected
    pdf_path    = db.Column(db.String(500))
    issued_at   = db.Column(db.DateTime)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    user        = db.relationship('User', foreign_keys=[user_id])
