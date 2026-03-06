from flask import Flask, request
from .models import db
import os
from datetime import timedelta

def create_app():
    app = Flask(__name__, static_folder='../static', template_folder='../templates')

    # Reverse-Proxy Base-Path (z.B. /food wenn hinter Portal)
    base_path = os.environ.get('APPLICATION_ROOT', '').rstrip('/')
    if base_path:
        app.config['APPLICATION_ROOT'] = base_path

        # ProxyFix: vertraut dem Reverse-Proxy für korrekten SCRIPT_NAME
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)
    
    # Konfiguration laden
    try:
        from .config import load_config
        config = load_config()
        app.config.update(config.to_flask_config())
    except (ImportError, ValueError) as e:
        import warnings
        warnings.warn(f"Config-Validierung fehlgeschlagen, nutze Fallback: {e}")
        
        from dotenv import load_dotenv
        load_dotenv()
        
        # PostgreSQL als Default
        db_uri = os.environ.get('DATABASE_URI',
            os.environ.get('DATABASE_URL',
                'postgresql://nocodb:nocodb@localhost:5432/nocodb'))
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Database Connection Pooling (PostgreSQL)
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'max_overflow': 5,
            'pool_timeout': 30
        }
        
        # SECRET_KEY
        secret_key = os.environ.get('SECRET_KEY')
        if not secret_key or secret_key in ('dev-secret-key-change-in-production', 'change-me-in-production'):
            raise ValueError("SECRET_KEY muss gesetzt werden!")
        app.config['SECRET_KEY'] = secret_key
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
        
        # Session/CSRF Config
        app.config['SESSION_COOKIE_SECURE'] = False
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['SESSION_COOKIE_PATH'] = base_path or '/'
        app.config['WTF_CSRF_ENABLED'] = True
        app.config['WTF_CSRF_TIME_LIMIT'] = 3600
        app.config['WTF_CSRF_SSL_STRICT'] = False
        app.config['WTF_CSRF_CHECK_DEFAULT'] = True
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
    
    db.init_app(app)
    
    # Hinweis: Tabellen werden per postgres-food.sql erstellt, NICHT per db.create_all()
    # db.create_all() würde die fw_food-Tabellen korrekt finden, aber
    # fw_common ist ein anderes Schema und wird separat verwaltet.
    
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
    csrf.exempt(api.api)  # Gesamtes API-Blueprint (Vue-Frontend nutzt JWT, kein CSRF)
    
    # Touch-Display Routen ohne CSRF (kein Form-Token möglich)
    csrf.exempt(routes.index)                  # POST / (Touch-Anmeldung)
    csrf.exempt(routes.register_with_menu)     # POST /register_with_menu
    csrf.exempt(routes.mobile_registration)    # POST /m/<token>
    
    # Rate Limiter initialisieren
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["500 per day", "100 per hour"],
        storage_uri="memory://",
        # Wichtig: Erlaube Touchscreen-Zugriff, aber rate-limited
        headers_enabled=True
    )
    
    # API-spezifische Limits werden in api.py gesetzt
    from .api import limiter as api_limiter
    api_limiter.init_app(app)
    
    # Blueprints registrieren
    app.register_blueprint(routes.bp)
    app.register_blueprint(api.api)
    app.register_blueprint(stats_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(system_bp)
    
    # Jinja2 filter for cache busting
    import time
    ASSET_VERSION = str(int(time.time()))  # Timestamp als Version
    
    @app.context_processor
    def inject_asset_version():
        return {'asset_version': ASSET_VERSION}
    
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
        elif request.path.startswith('/app/assets/'):
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        # No cache for HTML pages to ensure fresh content
        elif 'text/html' in response.headers.get('Content-Type', ''):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    # ── Vue 3 Frontend Serving ──────────────────────────────────────────────
    # Serviert das gebaute Vue-Frontend aus frontend_dist/
    # SPA-Fallback: alle unbekannten Routen → index.html
    vue_dist = os.path.join(os.path.dirname(__file__), '..', 'frontend_dist')
    if os.path.isdir(vue_dist):
        from flask import send_from_directory

        @app.route('/app/')
        @app.route('/app/<path:filename>')
        def vue_app(filename='index.html'):
            """Vue SPA serving mit Fallback auf index.html"""
            filepath = os.path.join(vue_dist, filename)
            if os.path.isfile(filepath):
                return send_from_directory(vue_dist, filename)
            return send_from_directory(vue_dist, 'index.html')

        @app.route('/app/config.js')
        def vue_config():
            """Dynamische config.js für Vue-Frontend"""
            fw_name = os.environ.get('FEUERWEHR_NAME', 'FF Wietmarschen')
            config_js = f"window.CONFIG = {{ api: '/api', feuerwehrName: '{fw_name}' }};"
            return config_js, 200, {'Content-Type': 'application/javascript', 'Cache-Control': 'no-cache'}

    return app
