"""
utils/notifications.py - Helper functions for creating notifications
"""
from models import db, Notification, ActivityLog
from datetime import datetime


def create_notification(user_id, message, notif_type='info'):
    """Create a notification for a user."""
    notif = Notification(
        user_id=user_id,
        message=message,
        notif_type=notif_type
    )
    db.session.add(notif)
    db.session.commit()


def log_activity(user_id, action, category='general'):
    """Log a user action to the activity log."""
    log = ActivityLog(
        user_id=user_id,
        action=action,
        category=category,
        created_at=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()
