from flask import render_template, redirect, url_for, flash, session, request
from flask_login import login_user, logout_user, current_user
import uuid
from . import auth_bp
from ..database import db_session
from ..models import User, UserActivity
from ..utils import log_activity

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            session['user_token'] = str(uuid.uuid4())
            log_activity('login') # Use the new logger
            return redirect(url_for('main.index'))
        else:
            log_activity('login_failed', details={'username': username}) # Log failed attempt
            flash('Invalid username or password')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        log_activity('logout') # Use the new logger
    session.pop('user_token', None)
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
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
            log_activity('register_success', details={'username': username})
            flash('Registration successful, please login.')
            return redirect(url_for('auth.login'))
        else:
            log_activity('register_failed', details={'username': username})
            flash('Username already exists')
    return render_template('register.html')
