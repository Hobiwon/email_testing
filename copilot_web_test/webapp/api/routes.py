from flask import request, jsonify, render_template, g
from flask_login import login_required, current_user
from . import api_bp
from ..models import User, Email, Comment
from ..utils import log_activity
from ..services import search_emails_service, get_activity_logs_service
from .. import db_session

@api_bp.route('/search')
@login_required
def api_search():
    args = request.args
    log_activity('api_search', details={k: v for k, v in args.items()})

    page = args.get('page', 1, type=int)
    per_page = args.get('per_page', 50, type=int)
    sort_by = args.get('sort_by', 'date_sent')
    sort_order = args.get('sort_order', 'desc')
    query = args.get('search_term', '')
    sender = args.get('sender', '')
    email_type = args.get('email_type', '')
    start_date = args.get('start_date', '')
    end_date = args.get('end_date', '')
    date_filter = args.get('date_filter', '')
    has_references = args.get('has_references') == 'true'
    has_comments = args.get('has_comments') == 'true'

    pagination = search_emails_service(query, page, per_page, sort_by, sort_order, sender, email_type, start_date, end_date, date_filter, has_references, has_comments)
    
    emails = pagination.items

    return jsonify({
        'results_html': render_template('search_results.html', emails=emails, sort_by=sort_by, sort_order=sort_order),
        'pagination_html': render_template('pagination.html', pagination=pagination, endpoint='api.api_search', args=args)
    })

@api_bp.route('/activity')
@login_required
def api_activity():
    if current_user.username != 'admin':
        log_activity('api_activity_denied', details={'reason': 'Non-admin user tried to access'})
        return jsonify({'error': 'Permission denied'}), 403

    args = request.args
    log_activity('api_activity_view', details={k: v for k, v in args.items()})

    page = args.get('page', 1, type=int)
    per_page = args.get('per_page', 25, type=int)
    selected_user_id = args.get('user_id', '')
    sort_by = args.get('sort_by', 'timestamp')
    sort_order = args.get('sort_order', 'desc')

    pagination = get_activity_logs_service(page, per_page, sort_by, sort_order, selected_user_id)
    
    activities = pagination.items
    
    return jsonify({
        'table_html': render_template('activity_table.html', activities=activities, sort_by=sort_by, sort_order=sort_order),
        'pagination_html': render_template('pagination.html', pagination=pagination, endpoint='api.api_activity', args=args)
    })

@api_bp.route('/comments/add', methods=['POST'])
@login_required
def add_comment():
    email_id = request.form.get('email_id')
    parent_id = request.form.get('parent_id')
    body = request.form.get('body')

    if not body:
        return jsonify({'success': False, 'error': 'Comment body cannot be empty.'}), 400

    email = db_session.get(Email, email_id)
    if not email:
        return jsonify({'success': False, 'error': 'Email not found.'}), 404
    
    new_comment = Comment(
        body=body,
        user_id=current_user.id,
        email_id=email.unique_email_id,
        parent_id=int(parent_id) if parent_id and parent_id != 'null' else None
    )
    db_session.add(new_comment)
    db_session.commit()

    log_activity(f"Posted a {'reply' if parent_id else 'comment'} on email: {email.title}")

    # Render the single new comment using the macro
    html = render_template('_comments.html', comment=new_comment)
    
    return jsonify({
        'success': True,
        'html': html,
        'parentId': new_comment.parent_id
    })
