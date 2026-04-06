"""
routes/student.py - Student Blueprint
All student-facing routes: dashboard, projects, AI, queries, profile, etc.
"""
import os
from datetime import datetime, date, timedelta
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, current_app, send_from_directory, jsonify)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import (db, Project, ProjectFile, ProjectUpdate, TeamMember,
                    Query, Notification, Certificate, ActivityLog, Announcement)
from utils.decorators import student_required
from utils.notifications import create_notification, log_activity
from utils.ai_utils import suggest_projects, generate_description, analyze_resume
from utils.pdf_utils import generate_certificate_pdf

student = Blueprint('student', __name__, url_prefix='/student')


def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
@student.route('/dashboard')
@login_required
@student_required
def dashboard():
    projects      = Project.query.filter_by(user_id=current_user.id).all()
    total         = len(projects)
    completed     = sum(1 for p in projects if p.status == 'completed')
    pending       = sum(1 for p in projects if p.status == 'pending')
    approved      = sum(1 for p in projects if p.status == 'approved')
    unread_notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    recent_notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(3).all()
    
    # Upcoming deadlines
    today = date.today()
    upcoming = [p for p in projects if p.deadline and p.deadline >= today and p.status != 'completed']
    upcoming.sort(key=lambda p: p.deadline)

    # Domain Data for Doughnut Chart
    domain_counts = {}
    for p in projects:
        d = p.domain or 'General'
        domain_counts[d] = domain_counts.get(d, 0) + 1
    
    domain_labels = list(domain_counts.keys())
    domain_values = list(domain_counts.values())

    # Weekly Activity Data for Performance Chart
    labels_7d = []
    daily_upd_counts = []
    
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        labels_7d.append(d.strftime('%b %d'))
        # Count updates for this user's projects on this day
        count = db.session.query(ProjectUpdate).join(Project).filter(
            Project.user_id == current_user.id,
            db.func.date(ProjectUpdate.created_at) == d
        ).count()
        daily_upd_counts.append(count)

    chart_data = {
        'labels': labels_7d,
        'counts': daily_upd_counts,
        'domain_labels': domain_labels,
        'domain_values': domain_values
    }

    # 28-Day Activity Dots
    activity_dots = []
    for i in range(27, -1, -1):
        d = today - timedelta(days=i)
        has_update = db.session.query(ProjectUpdate).join(Project).filter(
            Project.user_id == current_user.id,
            db.func.date(ProjectUpdate.created_at) == d
        ).first() is not None
        activity_dots.append({'day': d.strftime('%b %d'), 'active': has_update})

    return render_template('student/dashboard.html',
        total=total, completed=completed, pending=pending, approved=approved,
        unread_notifs=unread_notifs, recent_notifs=recent_notifs,
        announcements=announcements,
        upcoming=upcoming, chart_data=chart_data, projects=projects, 
        today=today, activity_dots=activity_dots)


# ─────────────────────────────────────────────
# SEARCH & SUGGESTIONS
# ─────────────────────────────────────────────
@student.route('/search_suggestions')
@login_required
def search_suggestions():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    
    matches = Project.query.filter(
        Project.user_id == current_user.id,
        Project.title.ilike(f'%{q}%')
    ).limit(10).all()
    
    results = [{'id': p.id, 'title': p.title} for p in matches]
    return jsonify(results)


# ─────────────────────────────────────────────
# PROJECTS LIST
# ─────────────────────────────────────────────
@student.route('/projects')
@login_required
@student_required
def projects():
    search  = request.args.get('search', '')
    domain  = request.args.get('domain', '')
    status  = request.args.get('status', '')
    tech    = request.args.get('tech', '')

    query = Project.query.filter_by(user_id=current_user.id)
    if search:
        # Search in title, domain, tech_stack
        query = query.filter(
            (Project.title.ilike(f'%{search}%')) | 
            (Project.domain.ilike(f'%{search}%')) |
            (Project.tech_stack.ilike(f'%{search}%'))
        )
    if domain:
        query = query.filter(Project.domain.ilike(f'%{domain}%'))
    if status:
        query = query.filter(Project.status == status)
    if tech:
        query = query.filter(Project.tech_stack.ilike(f'%{tech}%'))

    all_projects = query.order_by(Project.created_at.desc()).all()
    return render_template('student/projects.html', projects=all_projects,
                           search=search, domain=domain, status=status, tech=tech)


# ─────────────────────────────────────────────
# ADD PROJECT
# ─────────────────────────────────────────────
@student.route('/projects/add', methods=['GET', 'POST'])
@login_required
@student_required
def add_project():
    if request.method == 'POST':
        title           = request.form.get('title', '').strip()
        description     = request.form.get('description', '').strip()
        project_type    = request.form.get('project_type', 'individual')
        team_size       = int(request.form.get('team_size', 1))
        domain          = request.form.get('domain', '').strip()
        problem_stmt    = request.form.get('problem_statement', '').strip()
        tech_stack      = request.form.get('tech_stack', '').strip()
        deadline_str    = request.form.get('deadline', '')
        github_link     = request.form.get('github_link', '').strip()

        if not title:
            flash('Project title is required.', 'danger')
            return render_template('student/add_project.html')

        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        project = Project(
            user_id=current_user.id, title=title, description=description,
            project_type=project_type, team_size=team_size, domain=domain,
            problem_statement=problem_stmt, tech_stack=tech_stack,
            deadline=deadline, github_link=github_link
        )
        db.session.add(project)
        db.session.flush()  # get project.id

        # Team members
        if project_type == 'team':
            member_names   = request.form.getlist('member_name[]')
            member_roles   = request.form.getlist('member_role[]')
            member_emails  = request.form.getlist('member_email[]')
            for n, r, e in zip(member_names, member_roles, member_emails):
                if n.strip():
                    tm = TeamMember(project_id=project.id, name=n.strip(), role=r.strip(), email=e.strip())
                    db.session.add(tm)

        # File upload
        if 'project_file' in request.files:
            file = request.files['project_file']
            if file and file.filename:
                allowed = current_app.config['ALLOWED_PROJECT_EXTENSIONS']
                if allowed_file(file.filename, allowed):
                    fn = secure_filename(file.filename)
                    save_path = os.path.join(current_app.config['PROJECT_FILE_FOLDER'], fn)
                    file.save(save_path)
                    pf = ProjectFile(project_id=project.id, filename=fn, file_path=save_path, version='1.0')
                    db.session.add(pf)

        db.session.commit()
        log_activity(current_user.id, f'Added project: {title}', 'project')
        flash('Project created successfully!', 'success')
        return redirect(url_for('student.project_detail', project_id=project.id))

    return render_template('student/add_project.html')


# ─────────────────────────────────────────────
# PROJECT DETAIL
# ─────────────────────────────────────────────
@student.route('/projects/<int:project_id>')
@login_required
@student_required
def project_detail(project_id):
    project  = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    updates  = ProjectUpdate.query.filter_by(project_id=project_id).order_by(ProjectUpdate.created_at.desc()).all()
    files    = ProjectFile.query.filter_by(project_id=project_id).order_by(ProjectFile.uploaded_at.desc()).all()
    members  = TeamMember.query.filter_by(project_id=project_id).all()
    return render_template('student/project_detail.html', project=project, updates=updates, files=files, members=members)


# ─────────────────────────────────────────────
# UPDATES MANAGER
# ─────────────────────────────────────────────
@student.route('/updates')
@login_required
@student_required
def updates():
    # Fetch all projects to allow selecting one to add an update
    projects = Project.query.filter_by(user_id=current_user.id).all()
    all_updates = db.session.query(ProjectUpdate).join(Project).filter(
        Project.user_id == current_user.id
    ).order_by(ProjectUpdate.created_at.desc()).all()
    
    return render_template('student/updates.html', updates=all_updates, projects=projects)


# ─────────────────────────────────────────────
# ADD UPDATE
# ─────────────────────────────────────────────
@student.route('/projects/<int:project_id>/update', methods=['POST'])
@login_required
@student_required
def add_update(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    content = request.form.get('content', '').strip()
    if content:
        upd = ProjectUpdate(project_id=project_id, content=content)
        db.session.add(upd)
        db.session.commit()
        log_activity(current_user.id, f'Added update to project: {project.title}', 'project')
        flash('Update added!', 'success')
    return redirect(url_for('student.project_detail', project_id=project_id))


# ─────────────────────────────────────────────
# UPLOAD VERSION
# ─────────────────────────────────────────────
@student.route('/projects/<int:project_id>/version', methods=['POST'])
@login_required
@student_required
def upload_version(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    file    = request.files.get('version_file')
    version = request.form.get('version', '').strip()
    desc    = request.form.get('description', '').strip()

    if file and file.filename and version:
        allowed = current_app.config['ALLOWED_PROJECT_EXTENSIONS']
        if allowed_file(file.filename, allowed):
            fn        = secure_filename(file.filename)
            save_path = os.path.join(current_app.config['PROJECT_FILE_FOLDER'], fn)
            file.save(save_path)
            pf = ProjectFile(project_id=project_id, filename=fn, file_path=save_path, version=version, description=desc)
            db.session.add(pf)
            db.session.commit()
            log_activity(current_user.id, f'Uploaded version {version} for: {project.title}', 'project')
            flash(f'Version {version} uploaded!', 'success')
        else:
            flash('File type not allowed.', 'danger')
    else:
        flash('Please provide a file and version number.', 'warning')
    return redirect(url_for('student.project_detail', project_id=project_id))


# ─────────────────────────────────────────────
# DOWNLOAD FILE
# ─────────────────────────────────────────────
@student.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    pf = ProjectFile.query.get_or_404(file_id)
    folder = current_app.config['PROJECT_FILE_FOLDER']
    return send_from_directory(folder, pf.filename, as_attachment=True)


# ─────────────────────────────────────────────
# QUERY SYSTEM
# ─────────────────────────────────────────────
@student.route('/queries')
@login_required
@student_required
def queries():
    all_queries = Query.query.filter_by(user_id=current_user.id).order_by(Query.created_at.desc()).all()
    return render_template('student/queries.html', queries=all_queries)


@student.route('/queries/new', methods=['GET', 'POST'])
@login_required
@student_required
def new_query():
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        if subject and message:
            q = Query(user_id=current_user.id, subject=subject, message=message)
            db.session.add(q)
            db.session.commit()
            log_activity(current_user.id, f'Sent query: {subject}', 'query')
            flash('Query submitted successfully!', 'success')
            return redirect(url_for('student.queries'))
        flash('Please fill all fields.', 'danger')
    return render_template('student/new_query.html')


# ─────────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────────
@student.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.name       = request.form.get('name', '').strip()
        current_user.mobile     = request.form.get('mobile', '').strip()
        current_user.dob        = request.form.get('dob', '').strip()
        current_user.college    = request.form.get('college', '').strip()
        current_user.department = request.form.get('department', '').strip()
        current_user.year       = request.form.get('year', '').strip()
        current_user.bio        = request.form.get('bio', '').strip()

        # Profile image upload
        if 'profile_image' in request.files:
            img = request.files['profile_image']
            if img and img.filename:
                allowed = current_app.config['ALLOWED_IMAGE_EXTENSIONS']
                if allowed_file(img.filename, allowed):
                    fn = secure_filename(f"user_{current_user.id}_{img.filename}")
                    img.save(os.path.join(current_app.config['PROFILE_IMAGE_FOLDER'], fn))
                    current_user.profile_image = fn

        # Resume upload
        if 'resume' in request.files:
            res = request.files['resume']
            if res and res.filename:
                allowed = current_app.config['ALLOWED_RESUME_EXTENSIONS']
                if allowed_file(res.filename, allowed):
                    fn = secure_filename(f"resume_{current_user.id}_{res.filename}")
                    res.save(os.path.join(current_app.config['RESUME_FOLDER'], fn))
                    current_user.resume = fn

        db.session.commit()
        log_activity(current_user.id, 'Updated profile', 'profile')
        flash('Profile updated!', 'success')
        return redirect(url_for('student.profile'))

    return render_template('student/profile.html')


@student.route('/profile/resume/download')
@login_required
def download_resume():
    if current_user.resume:
        return send_from_directory(current_app.config['RESUME_FOLDER'], current_user.resume, as_attachment=True)
    flash('No resume uploaded.', 'warning')
    return redirect(url_for('student.profile'))


@student.route('/profile/image/<filename>')
def profile_image(filename):
    return send_from_directory(current_app.config['PROFILE_IMAGE_FOLDER'], filename)


# ─────────────────────────────────────────────
# NOTIFICATIONS
# ─────────────────────────────────────────────
@student.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    # Mark all as read
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return render_template('student/notifications.html', notifications=notifs)


# ─────────────────────────────────────────────
# AI FEATURES
# ─────────────────────────────────────────────
@student.route('/ai/suggest', methods=['GET', 'POST'])
@login_required
@student_required
def ai_suggest():
    suggestions = []
    form        = {}
    if request.method == 'POST':
        department = request.form.get('department', current_user.department or 'CSE')
        year       = request.form.get('year', current_user.year or '3rd')
        domain     = request.form.get('domain', 'AI/ML')
        form       = {'department': department, 'year': year, 'domain': domain}
        suggestions = suggest_projects(department, year, domain)
        log_activity(current_user.id, 'Used AI Project Suggester', 'ai')
    return render_template('student/ai_suggest.html', suggestions=suggestions, form=form)


@student.route('/ai/describe', methods=['GET', 'POST'])
@login_required
@student_required
def ai_describe():
    result = None
    form   = {}
    if request.method == 'POST':
        title   = request.form.get('title', '').strip()
        domain  = request.form.get('domain', '').strip()
        tech    = request.form.get('tech_stack', '').strip()
        form    = {'title': title, 'domain': domain, 'tech_stack': tech}
        result  = generate_description(title, domain, tech)
        log_activity(current_user.id, 'Used AI Description Generator', 'ai')
    return render_template('student/ai_describe.html', result=result, form=form)


@student.route('/ai/resume', methods=['GET', 'POST'])
@login_required
@student_required
def ai_resume():
    result = None
    if request.method == 'POST':
        file = request.files.get('resume_file')
        if file and file.filename:
            result = analyze_resume(file.filename)
            log_activity(current_user.id, 'Used AI Resume Analyzer', 'ai')
        else:
            flash('Please upload a resume file.', 'warning')
    return render_template('student/ai_resume.html', result=result)


# ─────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────
@student.route('/analytics')
@login_required
@student_required
def analytics():
    projects = Project.query.filter_by(user_id=current_user.id).all()

    # Domain distribution
    domain_counts = {}
    for p in projects:
        d = p.domain or 'Other'
        domain_counts[d] = domain_counts.get(d, 0) + 1

    # Tech stack frequency
    tech_counts = {}
    for p in projects:
        if p.tech_stack:
            for t in p.tech_stack.split(','):
                t = t.strip()
                if t:
                    tech_counts[t] = tech_counts.get(t, 0) + 1

    # Monthly submissions
    from collections import Counter
    monthly = Counter()
    for p in projects:
        key = p.created_at.strftime('%b %Y')
        monthly[key] += 1

    # Activity per day (last 7 days)
    activity_data = ActivityLog.query.filter_by(user_id=current_user.id).order_by(ActivityLog.created_at.desc()).limit(50).all()

    return render_template('student/analytics.html',
        projects=projects,
        domain_labels=list(domain_counts.keys()),
        domain_values=list(domain_counts.values()),
        tech_labels=list(tech_counts.keys())[:10],
        tech_values=list(tech_counts.values())[:10],
        monthly_labels=list(monthly.keys()),
        monthly_values=list(monthly.values()),
        activity_data=activity_data
    )


# ─────────────────────────────────────────────
# PUBLIC SHOWCASE
# ─────────────────────────────────────────────
@student.route('/showcase')
@login_required
def showcase():
    public_projects = Project.query.filter_by(is_public=True, status='completed').order_by(Project.created_at.desc()).all()
    return render_template('student/showcase.html', projects=public_projects)


# ─────────────────────────────────────────────
# CERTIFICATE
# ─────────────────────────────────────────────
@student.route('/certificate/<int:project_id>', methods=['GET', 'POST'])
@login_required
@student_required
def certificate(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    cert    = Certificate.query.filter_by(project_id=project_id, user_id=current_user.id).first()

    if request.method == 'POST':
        if project.status != 'completed':
            flash('Certificate can only be requested for completed projects.', 'warning')
            return redirect(url_for('student.project_detail', project_id=project_id))
        if not cert:
            cert = Certificate(user_id=current_user.id, project_id=project_id, status='pending')
            db.session.add(cert)
            db.session.commit()
            log_activity(current_user.id, f'Requested certificate for: {project.title}', 'project')
            flash('Certificate request submitted! Admin will approve it.', 'success')
        else:
            flash('Certificate already requested.', 'info')
        return redirect(url_for('student.certificate', project_id=project_id))

    return render_template('student/certificate.html', project=project, cert=cert)


@student.route('/certificate/download/<int:cert_id>')
@login_required
def download_certificate(cert_id):
    if current_user.role == 'admin':
        cert = Certificate.query.get(cert_id)
    else:
        cert = Certificate.query.filter_by(id=cert_id, user_id=current_user.id).first()
        
    if not cert:
        return render_template('errors/404.html'), 404
        
    if cert.status == 'approved' and cert.pdf_path:
        from flask import make_response
        filepath = os.path.join(current_app.config['CERTIFICATE_FOLDER'], cert.pdf_path)
        if not os.path.exists(filepath):
            return render_template('errors/404.html'), 404
        
        with open(filepath, 'rb') as f:
            file_data = f.read()
            
        response = make_response(file_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{cert.pdf_path}"'
        return response
        
    flash('Certificate not available for download yet.', 'warning')
    return redirect(url_for('student.dashboard'))
