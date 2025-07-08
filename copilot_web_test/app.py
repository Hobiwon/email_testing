from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from sqlalchemy import or_
import uuid
import os
import math
from datetime import datetime
import json
import re
from functools import wraps
from dotenv import load_dotenv
from database import db_session, init_db
from models import User, Email, UserActivity

load_dotenv()

username = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')

# Helper class for pagination
class Pagination:
    def __init__(self, page, per_page, total, items):
        self.page = page
        self.per_page = per_page
        self.total = total
        self.items = items

    @property
    def pages(self):
        return math.ceil(self.total / self.per_page)

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def prev_num(self):
        return self.page - 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def next_num(self):
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

def track_activity(activity_template):
    """A decorator to track user activity."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_authenticated and 'user_token' in session:
                # format activity string with arguments from the view
                activity_description = activity_template.format(**kwargs)
                
                # gather details for logging
                details = {
                    'to_page': request.path,
                    'from_page': request.referrer,
                }

                # for search, include the filter/search terms
                if request.endpoint == 'search':
                    search_params = {k: v for k, v in request.values.items() if k != 'page'}
                    if search_params:
                        details['search_params'] = search_params
                        activity_description = "search_with_filters"

                activity = UserActivity(
                    user_id=current_user.id,
                    token=session['user_token'],
                    activity=activity_description,
                    details=json.dumps(details, indent=2) # added indent for readability in DB
                )
                db_session.add(activity)
                db_session.commit()
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Initialize Flask application
database_url = f'oracle+oracledb://{username}:{password}@localhost:1521/?service_name=XEPDB1'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['DATABASE'] = database_url

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db_session.get(User, int(user_id))

@app.route('/')
@login_required
@track_activity('navigate_to_home')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            session['user_token'] = str(uuid.uuid4())
            activity = UserActivity(user_id=user.id, token=session['user_token'], activity='login')
            db_session.add(activity)
            db_session.commit()
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user is None:
            new_user = User(username=username)
            new_user.set_password(password)
            db_session.add(new_user)
            db_session.commit()
            flash('Registration successful, please login.')
            return redirect(url_for('login'))
        else:
            flash('Username already exists')
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    activity = UserActivity(user_id=current_user.id, token=session['user_token'], activity='logout')
    db_session.add(activity)
    db_session.commit()
    session.pop('user_token', None)
    logout_user()
    return redirect(url_for('login'))

@app.route('/search', methods=['GET', 'POST'])
@login_required
@track_activity('search')
def search():
    # This route now only renders the initial page shell.
    # The actual search logic is handled by the /api/search endpoint.
    return render_template('search.html', 
                           search_term='', sender='', email_type='',
                           start_date='', end_date='', per_page=50,
                           emails=[], pagination=None)

@app.route('/api/search')
@login_required
def api_search():
    args = request.args
    page = args.get('page', 1, type=int)
    per_page = args.get('per_page', 50, type=int)
    
    query = Email.query

    search_term = args.get('search_term', '')
    sender = args.get('sender', '')
    email_type = args.get('email_type', '')
    start_date = args.get('start_date', '')
    end_date = args.get('end_date', '')

    if search_term:
        query = query.filter(or_(Email.unique_email_id.ilike(f'%{search_term}%'), Email.title.ilike(f'%{search_term}%'), Email.body.ilike(f'%{search_term}%')))
    if sender:
        query = query.filter(Email.sender_name.ilike(f'%{sender}%'))
    if email_type:
        query = query.filter(Email.email_type == email_type)
    if start_date and end_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Email.date_sent.between(start_date_obj, end_date_obj))
        except ValueError:
            pass # Ignore invalid date formats for API calls

    total = query.count()
    emails = query.order_by(Email.date_sent.desc()).limit(per_page).offset((page - 1) * per_page).all()
    pagination = Pagination(page=page, per_page=per_page, total=total, items=emails)

    return jsonify({
        'results_html': render_template('search_results.html', emails=emails),
        'pagination_html': render_template('pagination.html', pagination=pagination, endpoint='api_search', args=args)
    })


@app.route('/email/<string:email_id>')
@login_required
@track_activity('view_email_{email_id}')
def view_email(email_id):
    email = db_session.get(Email, email_id)
    if not email:
        flash('Email not found.', 'danger')
        return redirect(url_for('index'))

    # Get the referrer to pass back to the template for the "back" button
    back_url = request.referrer or url_for('search')

    # The email body is stored in the 'body' attribute
    email_body = email.body

    # Find all potential unique_email_ids in the email body
    potential_ids = re.findall(r'([a-zA-Z0-9]+-\d{2}-\d{4,})', email_body)
    
    if potential_ids:
        # Query the database to see which of these potential IDs actually exist
        referenced_emails = Email.query.filter(Email.unique_email_id.in_(potential_ids)).all()
        
        # Create a mapping from unique_email_id to the URL
        reference_map = {e.unique_email_id: url_for('view_email', email_id=e.unique_email_id) for e in referenced_emails}
        
        # Replace the unique_email_ids with hyperlinks
        for unique_id, url in reference_map.items():
            email_body = email_body.replace(unique_id, f'<a href="{url}">{unique_id}</a>')

    return render_template('email_reader.html', email=email, email_body=email_body, back_url=back_url)


@app.route('/activity')
@login_required
@track_activity('view_activity')
def activity():
    if current_user.username != 'admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))

    users = User.query.order_by(User.username).all()
    
    return render_template('activity.html', 
                           activities=[], 
                           pagination=None,
                           users=users,
                           selected_user_id='',
                           per_page=25)

@app.route('/api/activity')
@login_required
def api_activity():
    if current_user.username != 'admin':
        return jsonify({'error': 'Permission denied'}), 403

    args = request.args
    page = args.get('page', 1, type=int)
    per_page = args.get('per_page', 25, type=int)
    selected_user_id = args.get('user_id', '')

    query = UserActivity.query

    if selected_user_id:
        query = query.filter(UserActivity.user_id == selected_user_id)

    total = query.count()
    activities = query.order_by(UserActivity.timestamp.desc()).limit(per_page).offset((page - 1) * per_page).all()
    pagination = Pagination(page=page, per_page=per_page, total=total, items=activities)
    
    return jsonify({
        'table_html': render_template('activity_table.html', activities=activities),
        'pagination_html': render_template('pagination.html', pagination=pagination, endpoint='api_activity', args=args)
    })

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
