import math
from functools import wraps
import json
from flask import request, session
from flask_login import current_user
from .models import UserActivity
from . import db_session

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

def log_activity(activity_type, details=None):
    """Logs a user activity to the database."""
    if not current_user.is_authenticated or 'user_token' not in session:
        return

    # Ensure details is a dictionary
    if details is None:
        details = {}

    # Add standard details
    details['endpoint'] = request.endpoint
    details['path'] = request.path
    if request.referrer:
        details['referrer'] = request.referrer

    activity = UserActivity(
        user_id=current_user.id,
        token=session['user_token'],
        activity=activity_type,
        details=json.dumps(details, indent=2)
    )
    db_session.add(activity)
    db_session.commit()


def track_activity(activity_template):
    """A decorator to track user activity for standard page loads."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Log the activity *after* the request is handled
            response = f(*args, **kwargs)
            
            if current_user.is_authenticated:
                activity_description = activity_template.format(**kwargs)
                log_activity(activity_description)
            
            return response
        return decorated_function
    return decorator


def parse_search_query(query):
    """
    Parses a search query into three lists:
    - search_terms: for general matching
    - exact_phrases: for exact phrase matching (in quotes)
    - exclusion_terms: for words to exclude (prefixed with -)
    """
    import re
    # Find all quoted phrases
    exact_phrases = re.findall(r'\"(.+?)\"', query)
    # Remove the quoted phrases from the query to not process them again
    query = re.sub(r'\"(.+?)\"', '', query)

    terms = query.split()
    
    exclusion_terms = [term[1:] for term in terms if term.startswith('-') and len(term) > 1]
    search_terms = [term for term in terms if not term.startswith('-')]
    
    return search_terms, exact_phrases, exclusion_terms
