import random
from datetime import datetime, timedelta
from app import create_app
from models import db, User, Project, Notification, ActivityLog

app = create_app()

with app.app_context():
    print("Seeding test data...")
    
    # Check if student exists
    student_email = 'student@projecthub.com'
    if not User.query.filter_by(email=student_email).first():
        student = User(
            username='johndoe',
            email=student_email,
            role='student',
            name='John Doe',
            college='XYZ Engineering',
            department='Computer Science',
            year='Junior',
            bio='Passionate developer.'
        )
        student.set_password('Student@123')
        db.session.add(student)
        db.session.commit()
        print(f"Created student test user: {student_email} / Student@123")
    else:
        student = User.query.filter_by(email=student_email).first()

    # Add dummy projects
    if not Project.query.filter_by(user_id=student.id).first():
        p1 = Project(
            user_id=student.id,
            title='AI Chatbot Assistant',
            description='A chatbot built with NLP and Python.',
            project_type='individual',
            domain='AI / ML',
            deadline=datetime.utcnow() + timedelta(days=15),
            status='pending',
            created_at=datetime.utcnow() - timedelta(days=5)
        )
        p2 = Project(
            user_id=student.id,
            title='E-Commerce Platform',
            description='Full-stack web application with payment integration.',
            project_type='team',
            team_size=3,
            domain='Web Development',
            deadline=datetime.utcnow() - timedelta(days=2),
            status='completed',
            created_at=datetime.utcnow() - timedelta(days=40)
        )
        db.session.add_all([p1, p2])
        
        # Add basic logs and notifications
        log = ActivityLog(user_id=student.id, action='Created project AI Chatbot Assistant', category='project')
        notif = Notification(user_id=student.id, message='Welcome to Project Hub!', notif_type='success')
        db.session.add_all([log, notif])
        
        db.session.commit()
        print("Created sample projects and activity logs.")

    print("Database seeding completed.")
