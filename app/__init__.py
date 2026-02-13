from flask import Flask, request
from .models import db
import os
from datetime import timedelta
from dotenv import load_dotenv

def create_app():
    # Lade Umgebungsvariablen aus .env
    load_dotenv()
    
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foodbot.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # SECRET_KEY ist zwingend erforderlich
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key or secret_key == 'dev-secret-key-change-in-production':
        raise ValueError("SECRET_KEY muss in .env gesetzt werden! Generiere einen mit: python3 -c 'import secrets; print(secrets.token_hex(32))'")
    app.config['SECRET_KEY'] = secret_key
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
    
    # Sichere Session-Cookies
    # SECURE nur bei HTTPS aktivieren (nicht bei HTTP!)
    app.config['SESSION_COOKIE_SECURE'] = False  # Auf True setzen wenn HTTPS genutzt wird
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # CSRF-Schutz
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = None  # Token läuft nicht ab
    app.config['WTF_CSRF_SSL_STRICT'] = False  # Erlaube HTTP in Dev
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    
    # Performance: Static file caching
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 Jahr für statische Assets
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    # Blueprints importieren
    from . import routes
    from . import api
    from .stats import stats_bp
    from .history import history_bp
    from .system import system_bp
    
    # CSRF-Schutz initialisieren (NACH Blueprint-Import)
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect(app)
    
    # Nur spezifische API-Endpunkte von CSRF ausnehmen
    # (Touch-Display und RFID haben keine CSRF-Token)
    csrf.exempt(api.register)  # POST /api/register (Touch/RFID)
    csrf.exempt(api.status)    # GET /api/status
    csrf.exempt(api.stats)     # GET /api/stats
    
    # Touch-Display Routen ohne CSRF (kein Form-Token möglich)
    csrf.exempt(routes.index)                  # POST / (Touch-Anmeldung)
    csrf.exempt(routes.register_with_menu)     # POST /register_with_menu
    csrf.exempt(routes.mobile_registration)    # POST /m/<token>
    
    # Rate Limiter initialisieren
    from .api import limiter
    limiter.init_app(app)
    
    # Blueprints registrieren
    app.register_blueprint(routes.bp)
    app.register_blueprint(api.api)
    app.register_blueprint(stats_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(system_bp)
    
    # Error Handler
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Seite nicht gefunden'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Interner Serverfehler'}, 500
    
    # Performance: Add cache headers for static files
    @app.after_request
    def add_cache_headers(response):
        # Cache static assets (CSS, JS, images) for 1 year
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        # No cache for HTML pages to ensure fresh content
        elif 'text/html' in response.headers.get('Content-Type', ''):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    
    return app
