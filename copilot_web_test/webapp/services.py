from sqlalchemy import desc, or_, func
from .models import Email, UserActivity, Comment
from .utils import parse_search_query, Pagination
from datetime import datetime, date, timedelta

def search_emails_service(query, page, per_page, sort_by, sort_order, sender, email_type, start_date, end_date, date_filter, has_references=False, has_comments=False):
    """Handles the business logic for searching emails."""
    search_terms, exact_phrases, exclusion_terms = parse_search_query(query)

    db_query = Email.query

    if sender:
        db_query = db_query.filter(Email.sender_name.ilike(f'%{sender}%'))
    if email_type:
        db_query = db_query.filter(Email.email_type == email_type)

    if has_references:
        db_query = db_query.filter(Email.references.isnot(None)).filter(func.length(Email.references) > 0)

    if has_comments:
        db_query = db_query.filter(Email.comments.any())

    # Date filtering logic
    start_date_obj = None
    end_date_obj = None

    if date_filter:
        today = date.today()
        if date_filter == 'yesterday':
            start_date_obj = today - timedelta(days=1)
            # Set end_date to the beginning of today to get all of yesterday
            end_date_obj = today
        elif date_filter == 'week':
            start_date_obj = today - timedelta(weeks=1)
        elif date_filter == 'month':
            # Approximation for last 30 days
            start_date_obj = today - timedelta(days=30)
        elif date_filter == 'year':
            # Approximation for last 365 days
            start_date_obj = today - timedelta(days=365)
    else:
        # Use date range picker if date_filter is not active
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                pass  # Ignore invalid date format
        if end_date:
            try:
                # Add one day to the end date to make the range inclusive
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() + timedelta(days=1)
            except ValueError:
                pass  # Ignore invalid date format

    if start_date_obj:
        db_query = db_query.filter(Email.date_sent >= start_date_obj)
    if end_date_obj:
        db_query = db_query.filter(Email.date_sent < end_date_obj)


    if search_terms:
        search_filters = [Email.body.ilike(f'%{term}%') for term in search_terms]
        db_query = db_query.filter(or_(*search_filters))

    for phrase in exact_phrases:
        db_query = db_query.filter(Email.body.ilike(f'%{phrase}%'))

    for term in exclusion_terms:
        db_query = db_query.filter(~Email.body.ilike(f'%{term}%'))

    if sort_by and hasattr(Email, sort_by):
        column = getattr(Email, sort_by)
        if sort_order == 'desc':
            db_query = db_query.order_by(desc(column))
        else:
            db_query = db_query.order_by(column)

    total = db_query.count()
    items = db_query.limit(per_page).offset((page - 1) * per_page).all()
    
    return Pagination(page=page, per_page=per_page, total=total, items=items)

def get_activity_logs_service(page, per_page, sort_by, sort_order, user_id_filter):
    """Handles the business logic for fetching user activity logs."""
    db_query = UserActivity.query

    if user_id_filter:
        db_query = db_query.filter(UserActivity.user_id == user_id_filter)

    if sort_by and hasattr(UserActivity, sort_by):
        column = getattr(UserActivity, sort_by)
        if sort_order == 'desc':
            db_query = db_query.order_by(desc(column))
        else:
            db_query = db_query.order_by(column)
    else:
        db_query = db_query.order_by(desc(UserActivity.timestamp))

    total = db_query.count()
    items = db_query.limit(per_page).offset((page - 1) * per_page).all()

    return Pagination(page=page, per_page=per_page, total=total, items=items)
