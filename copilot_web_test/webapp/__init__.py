from flask import Flask
from flask_login import LoginManager
from .database import db_session, init_db
from .models import User
from config import Config

login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config_class)

    # Initialize extensions
    login_manager.init_app(app)

    # Register blueprints
    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .main import main_bp
    app.register_blueprint(main_bp)

    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    @login_manager.user_loader
    def load_user(user_id):
        return db_session.get(User, int(user_id))

    with app.app_context():
        init_db()

    return app
