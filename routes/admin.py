"""
routes/admin.py - Admin Blueprint
Full admin control panel: projects, users, queries, announcements, reports, etc.
"""
import os
from datetime import datetime
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, current_app, send_from_directory, jsonify)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import (db, User, Project, Query, Notification, Announcement,
                    ActivityLog, Certificate, ProjectFile, ProjectUpdate, TeamMember)
from utils.decorators import admin_required
from utils.notifications import create_notification, log_activity
from utils.pdf_utils import generate_certificate_pdf, generate_report_pdf

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

admin = Blueprint('admin', __name__, url_prefix='/admin')


# ─────────────────────────────────────────────
# SEARCH & SUGGESTIONS
# ─────────────────────────────────────────────
@admin.route('/search_suggestions')
@login_required
def search_suggestions():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    
    matches = Project.query.filter(
        Project.title.ilike(f'%{q}%')
    ).limit(10).all()
    
    results = [{'id': p.id, 'title': p.title} for p in matches]
    return jsonify(results)


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_users    = User.query.filter_by(role='student').count()
    total_projects = Project.query.count()
    pending_proj   = Project.query.filter_by(status='pending').count()
    open_queries   = Query.query.filter_by(status='open').count()
    recent_users   = User.query.filter_by(role='student').order_by(User.created_at.desc()).limit(5).all()
    recent_proj    = Project.query.order_by(Project.created_at.desc()).limit(5).all()

    # Department distribution
    students  = User.query.filter_by(role='student').all()
    dept_dist = {}
    for s in students:
        d = s.department or 'Unknown'
        dept_dist[d] = dept_dist.get(d, 0) + 1

    # Project status distribution
    status_dist = {
        'pending':   Project.query.filter_by(status='pending').count(),
        'approved':  Project.query.filter_by(status='approved').count(),
        'completed': Project.query.filter_by(status='completed').count(),
        'rejected':  Project.query.filter_by(status='rejected').count(),
    }

    # Monthly submissions (last 6 months)
    from collections import Counter
    all_proj = Project.query.all()
    monthly  = Counter()
    for p in all_proj:
        key = p.created_at.strftime('%b %Y')
        monthly[key] += 1

    # Tech stack frequency
    tech_counts = {}
    for p in all_proj:
        if p.tech_stack:
            for t in p.tech_stack.split(','):
                t = t.strip()
                if t:
                    tech_counts[t] = tech_counts.get(t, 0) + 1

    top_tech = sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)[:8]

    return render_template('admin/dashboard.html',
        total_users=total_users, total_projects=total_projects,
        pending_proj=pending_proj, open_queries=open_queries,
        recent_users=recent_users, recent_proj=recent_proj,
        dept_labels=list(dept_dist.keys()), dept_values=list(dept_dist.values()),
        status_dist=status_dist,
        monthly_labels=list(monthly.keys()), monthly_values=list(monthly.values()),
        tech_labels=[t[0] for t in top_tech], tech_values=[t[1] for t in top_tech]
    )


# ─────────────────────────────────────────────
# PROJECT MANAGEMENT
# ─────────────────────────────────────────────
@admin.route('/projects')
@login_required
@admin_required
def projects():
    status  = request.args.get('status', '')
    search  = request.args.get('search', '')
    query   = Project.query
    if status:
        query = query.filter(Project.status == status)
    if search:
        query = query.filter(Project.title.ilike(f'%{search}%'))
    all_projects = query.order_by(Project.created_at.desc()).all()
    return render_template('admin/projects.html', projects=all_projects, status=status, search=search)


@admin.route('/projects/<int:project_id>')
@login_required
@admin_required
def project_detail(project_id):
    project  = Project.query.get_or_404(project_id)
    updates  = ProjectUpdate.query.filter_by(project_id=project_id).order_by(ProjectUpdate.created_at.desc()).all()
    files    = ProjectFile.query.filter_by(project_id=project_id).order_by(ProjectFile.uploaded_at.desc()).all()
    members  = TeamMember.query.filter_by(project_id=project_id).all()
    return render_template('admin/project_detail.html', project=project, updates=updates, files=files, members=members)


@admin.route('/projects/<int:project_id>/action', methods=['POST'])
@login_required
@admin_required
def project_action(project_id):
    project  = Project.query.get_or_404(project_id)
    action   = request.form.get('action')
    feedback = request.form.get('feedback', '').strip()
    rating   = request.form.get('rating')

    if action in ('approve', 'reject', 'complete'):
        project.status          = {'approve': 'approved', 'reject': 'rejected', 'complete': 'completed'}[action]
        project.admin_feedback  = feedback
        if rating:
            try:
                project.rating = float(rating)
            except ValueError:
                pass
        db.session.commit()

        # Notify student
        msg = f"Your project '{project.title}' has been {project.status}."
        if feedback:
            msg += f" Feedback: {feedback}"
        create_notification(project.user_id, msg, 'success' if action == 'complete' else 'info')
        log_activity(current_user.id, f'Project {action}d: {project.title}', 'admin')
        flash(f'Project {action}d successfully!', 'success')

    return redirect(url_for('admin.projects'))


# ─────────────────────────────────────────────
# USER MANAGEMENT
# ─────────────────────────────────────────────
@admin.route('/users')
@login_required
@admin_required
def users():
    search  = request.args.get('search', '')
    dept    = request.args.get('dept', '')
    query   = User.query.filter_by(role='student')
    if search:
        query = query.filter((User.name.ilike(f'%{search}%')) | (User.email.ilike(f'%{search}%')))
    if dept:
        query = query.filter(User.department.ilike(f'%{dept}%'))
    all_users = query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users, search=search, dept=dept)


@admin.route('/users/<int:user_id>/block', methods=['POST'])
@login_required
@admin_required
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blocked = not user.is_blocked
    db.session.commit()
    status = 'blocked' if user.is_blocked else 'unblocked'
    log_activity(current_user.id, f'User {status}: {user.username}', 'admin')
    flash(f'User {status} successfully.', 'success')
    return redirect(url_for('admin.users'))


@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    log_activity(current_user.id, f'Deleted user: {user.username}', 'admin')
    flash('User deleted.', 'success')
    return redirect(url_for('admin.users'))


# ─────────────────────────────────────────────
# QUERY MANAGEMENT
# ─────────────────────────────────────────────
@admin.route('/queries')
@login_required
@admin_required
def queries():
    status      = request.args.get('status', '')
    q           = Query.query
    if status:
        q = q.filter(Query.status == status)
    all_queries = q.order_by(Query.created_at.desc()).all()
    return render_template('admin/queries.html', queries=all_queries, status=status)


@admin.route('/queries/<int:query_id>/reply', methods=['POST'])
@login_required
@admin_required
def reply_query(query_id):
    query   = Query.query.get_or_404(query_id)
    reply   = request.form.get('reply', '').strip()
    if reply:
        query.reply      = reply
        query.status     = 'resolved'
        query.replied_at = datetime.utcnow()
        db.session.commit()
        create_notification(query.user_id, f"Your query '{query.subject}' has been answered.", 'info')
        log_activity(current_user.id, f'Replied to query: {query.subject}', 'admin')
        flash('Reply sent!', 'success')
    return redirect(url_for('admin.queries'))


# ─────────────────────────────────────────────
# ANNOUNCEMENTS
# ─────────────────────────────────────────────
@admin.route('/announcements', methods=['GET', 'POST'])
@login_required
@admin_required
def announcements():
    if request.method == 'POST':
        title   = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if title and content:
            a = Announcement(admin_id=current_user.id, title=title, content=content)
            db.session.add(a)
            db.session.commit()
            # Notify all students
            students = User.query.filter_by(role='student').all()
            for s in students:
                create_notification(s.id, f'Announcement: {title}', 'info')
            log_activity(current_user.id, f'Posted announcement: {title}', 'admin')
            flash('Announcement posted!', 'success')
        return redirect(url_for('admin.announcements'))

    anns = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin/announcements.html', announcements=anns)


@admin.route('/announcements/<int:ann_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_announcement(ann_id):
    a = Announcement.query.get_or_404(ann_id)
    db.session.delete(a)
    db.session.commit()
    flash('Announcement deleted.', 'success')
    return redirect(url_for('admin.announcements'))


# ─────────────────────────────────────────────
# LEADERBOARD / PERFORMANCE
# ─────────────────────────────────────────────
@admin.route('/leaderboard')
@login_required
@admin_required
def leaderboard():
    students  = User.query.filter_by(role='student').all()
    board     = []
    for s in students:
        projs     = Project.query.filter_by(user_id=s.id).all()
        completed = sum(1 for p in projs if p.status == 'completed')
        approved  = sum(1 for p in projs if p.status == 'approved')
        score     = completed * 10 + approved * 5 + len(projs) * 2
        board.append({'user': s, 'total': len(projs), 'completed': completed, 'approved': approved, 'score': score})
    board.sort(key=lambda x: x['score'], reverse=True)
    return render_template('admin/leaderboard.html', board=board)


# ─────────────────────────────────────────────
# ACTIVITY LOGS
# ─────────────────────────────────────────────
@admin.route('/activity-logs')
@login_required
@admin_required
def activity_logs():
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(200).all()
    return render_template('admin/activity_logs.html', logs=logs)


# ─────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────
@admin.route('/reports', methods=['GET', 'POST'])
@login_required
@admin_required
def reports():
    if request.method == 'POST':
        # Generate the Report
        stats = {
            'total_students': User.query.filter_by(role='student').count(),
            'total_projects': Project.query.count(),
            'completed_projects': Project.query.filter_by(status='completed').count(),
            'total_queries': Query.query.count(),
            'total_certificates_issued': Certificate.query.filter_by(status='approved').count(),
            'total_showcase_projects': Project.query.filter_by(is_public=True).count()
        }
        report_folder = current_app.config['UPLOAD_FOLDER']  # using general upload folder 
        filename = generate_report_pdf(stats, report_folder)
        log_activity(current_user.id, 'Generated system report', 'admin')
        flash('Report generated successfully.', 'success')
        return redirect(url_for('admin.download_report', filename=filename))

    return render_template('admin/reports.html')


@admin.route('/reports/download/<filename>')
@login_required
@admin_required
def download_report(filename):
    import os
    from flask import make_response
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return render_template('errors/404.html'), 404
    
    with open(filepath, 'rb') as f:
        file_data = f.read()
    
    response = make_response(file_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
    return response



# ─────────────────────────────────────────────
# CERTIFICATES
# ─────────────────────────────────────────────
@admin.route('/certificates')
@login_required
@admin_required
def certificates():
    certs = Certificate.query.order_by(Certificate.created_at.desc()).all()
    return render_template('admin/certificates.html', certificates=certs)


@admin.route('/certificates/<int:cert_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_certificate(cert_id):
    cert    = Certificate.query.get_or_404(cert_id)
    project = Project.query.get(cert.project_id)
    user    = User.query.get(cert.user_id)

    # Generate PDF
    cert_folder = current_app.config['CERTIFICATE_FOLDER']
    filename    = generate_certificate_pdf(user.name or user.username, project.title, cert_folder)
    cert.pdf_path  = filename
    cert.status    = 'approved'
    cert.issued_at = datetime.utcnow()
    db.session.commit()

    create_notification(cert.user_id, f"Your certificate for '{project.title}' is ready!", 'success')
    log_activity(current_user.id, f'Approved certificate for: {user.username}', 'admin')
    flash('Certificate approved and generated!', 'success')
    return redirect(url_for('admin.certificates'))


@admin.route('/certificates/<int:cert_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_certificate(cert_id):
    cert        = Certificate.query.get_or_404(cert_id)
    cert.status = 'rejected'
    db.session.commit()
    create_notification(cert.user_id, "Your certificate request was rejected.", 'warning')
    flash('Certificate rejected.', 'warning')
    return redirect(url_for('admin.certificates'))


# ─────────────────────────────────────────────
# SHOWCASE MODERATION
# ─────────────────────────────────────────────
@admin.route('/showcase')
@login_required
@admin_required
def showcase():
    projects = Project.query.filter_by(is_public=True).order_by(Project.created_at.desc()).all()
    return render_template('admin/showcase.html', projects=projects)


@admin.route('/showcase/<int:project_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_showcase(project_id):
    project           = Project.query.get_or_404(project_id)
    project.is_public = not project.is_public
    db.session.commit()
    status = 'added to' if project.is_public else 'removed from'
    flash(f'Project {status} showcase.', 'success')
    return redirect(url_for('admin.showcase'))


# ─────────────────────────────────────────────
# SYSTEM HEALTH
# ─────────────────────────────────────────────
@admin.route('/system-health')
@login_required
@admin_required
def system_health():
    import shutil
    total, used, free = shutil.disk_usage('/')
    db_path   = os.path.join(current_app.root_path, 'project_hub.db')
    db_size   = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    uploads_size = 0
    upload_dir = current_app.config['UPLOAD_FOLDER']
    for dirpath, _, filenames in os.walk(upload_dir):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            uploads_size += os.path.getsize(fp)

    return render_template('admin/system_health.html',
        total_disk=total, used_disk=used, free_disk=free,
        db_size=db_size, uploads_size=uploads_size,
        total_users=User.query.count(),
        total_projects=Project.query.count(),
        total_logs=ActivityLog.query.count()
    )


# ─────────────────────────────────────────────
# AI INSIGHTS
# ─────────────────────────────────────────────
@admin.route('/ai-insights')
@login_required
@admin_required
def ai_insights():
    projects    = Project.query.all()
    domain_freq = {}
    tech_freq   = {}
    for p in projects:
        d = p.domain or 'Unknown'
        domain_freq[d] = domain_freq.get(d, 0) + 1
        if p.tech_stack:
            for t in p.tech_stack.split(','):
                t = t.strip()
                if t:
                    tech_freq[t] = tech_freq.get(t, 0) + 1

    top_domains = sorted(domain_freq.items(), key=lambda x: x[1], reverse=True)[:6]
    top_tech    = sorted(tech_freq.items(), key=lambda x: x[1], reverse=True)[:8]

    return render_template('admin/ai_insights.html',
        top_domains=top_domains, top_tech=top_tech, total_projects=len(projects)
    )


# ─────────────────────────────────────────────
# ADMIN PROFILE
# ─────────────────────────────────────────────
@admin.route('/profile', methods=['GET', 'POST'])
@login_required
@admin_required
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
                    fn = secure_filename(f"admin_{current_user.id}_{img.filename}")
                    img.save(os.path.join(current_app.config['PROFILE_IMAGE_FOLDER'], fn))
                    current_user.profile_image = fn

        db.session.commit()
        log_activity(current_user.id, 'Updated admin profile', 'admin')
        flash('Profile updated!', 'success')
        return redirect(url_for('admin.profile'))

    return render_template('admin/profile.html')

