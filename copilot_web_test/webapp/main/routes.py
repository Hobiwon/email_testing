from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from . import main_bp
from ..database import db_session
from ..models import Email, User, UserActivity, Comment
from ..utils import track_activity, Pagination
import re
from sqlalchemy import or_
from datetime import datetime

@main_bp.route('/')
@login_required
@track_activity('navigate_to_home')
def index():
    return render_template('index.html')

@main_bp.route('/search', methods=['GET', 'POST'])
@login_required
@track_activity('search')
def search():
    return render_template('search.html', 
                           search_term='', sender='', email_type='',
                           start_date='', end_date='', per_page=50,
                           emails=[], pagination=None)

@main_bp.route('/email/<string:email_id>')
@login_required
@track_activity('view_email_{email_id}')
def view_email(email_id):
    email = db_session.get(Email, email_id)
    if not email:
        flash('Email not found.', 'danger')
        return redirect(url_for('main.index'))

    back_url = request.referrer or url_for('main.search')
    email_body = email.body
    potential_ids = re.findall(r'([a-zA-Z0-9]+-\d{2}-\d{4,})', email_body)
    
    referenced_emails = []
    if potential_ids:
        referenced_emails = Email.query.filter(Email.unique_email_id.in_(potential_ids)).all()
        
        for ref_email in referenced_emails:
            unique_id = ref_email.unique_email_id
            # Create a link that toggles the collapse element in the side panel
            replacement_link = (
                f'<a href="#collapse-{unique_id}" '
                f'data-bs-toggle="collapse" '
                f'aria-expanded="false" '
                f'aria-controls="collapse-{unique_id}">'
                f'{unique_id}</a>'
            )
            email_body = email_body.replace(unique_id, replacement_link)

    # Fetch top-level comments for this email
    comments = Comment.query.filter_by(email_id=email.unique_email_id, parent_id=None).order_by(Comment.timestamp.desc()).all()

    return render_template('email_reader.html', 
                           email=email, 
                           email_body=email_body, 
                           back_url=back_url, 
                           referenced_emails=referenced_emails,
                           comments=comments)

@main_bp.route('/activity')
@login_required
@track_activity('view_activity')
def activity():
    if current_user.username != 'admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))

    users = User.query.order_by(User.username).all()
    
    return render_template('activity.html', 
                           activities=[], 
                           pagination=None,
                           users=users,
                           selected_user_id='',
                           per_page=25)
