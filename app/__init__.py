from flask import Flask
from .models import db
import os
from dotenv import load_dotenv

def create_app():
    # Lade Umgebungsvariablen aus .env
    load_dotenv()
    
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foodbot.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Verwende festen Fallback-Key für Entwicklung, damit Sessions über Restarts hinweg funktionieren
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-feuerwehr-2026-change-in-production')
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 Stunde
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    from . import routes
    from . import api
    from .stats import stats_bp
    from .history import history_bp
    from .system import system_bp
    
    # Rate Limiter initialisieren
    from .api import limiter
    limiter.init_app(app)
    
    app.register_blueprint(routes.bp)
    app.register_blueprint(api.api)
    app.register_blueprint(stats_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(system_bp)
    return app
