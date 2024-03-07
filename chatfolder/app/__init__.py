from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_migrate import Migrate
import os

# ініціалізуввання компонентів Flask 
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
migrate = None 

def create_app():
    app = Flask(__name__)    

    # Конфігурація програми
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_fallback_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///chat_server.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # прив'язати екземпляри до додатку
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    # Ініціалізування Flask-Migrate
    global migrate
    migrate = Migrate(app, db)

    # Налаштування Flask-Login
    login_manager.login_view = 'auth.login'

    # Регістрація Blueprints
    with app.app_context():
        from .auth import auth as auth_blueprint
        app.register_blueprint(auth_blueprint)

        from .chat_management import chat_management as chat_management_blueprint
        app.register_blueprint(chat_management_blueprint)

        from .routes import main as main_blueprint
        app.register_blueprint(main_blueprint)

    return app
