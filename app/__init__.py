from flask import Flask, request
from .models import db
from .config import load_config
import os
from datetime import timedelta

def create_app():
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    
    # Lade und validiere Konfiguration
    config = load_config()
    app.config.update(config.to_flask_config())
    
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
        # No cache for HTML pages to ensure fresh content
        elif 'text/html' in response.headers.get('Content-Type', ''):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    
    return app
