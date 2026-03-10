"""
Authentifizierung für den Admin-Bereich
Unterstützt Portal-SSO via fw_jwt Cookie und Passwort-Fallback.
"""
from functools import wraps
from flask import session, redirect, url_for, request
import os
import secrets
import logging

try:
    import jwt as pyjwt
except ImportError:
    pyjwt = None

logger = logging.getLogger(__name__)

# Admin-Passwort aus Environment (Fallback für Standalone-Betrieb)
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
if not ADMIN_PASSWORD or ADMIN_PASSWORD == 'change-this-password':
    raise ValueError("ADMIN_PASSWORD muss in .env gesetzt werden!")

# Portal JWT Secret für SSO (optional — ohne JWT_SECRET nur Passwort-Login)
PORTAL_JWT_SECRET = os.getenv('JWT_SECRET')

# Portal-Rollen die FoodBot-Admin-Zugriff erhalten
FOOD_ADMIN_ROLES = {'Admin'}


def check_auth(password):
    """Prüft ob das Passwort korrekt ist (timing-safe)"""
    if not password:
        return False
    return secrets.compare_digest(password, ADMIN_PASSWORD)


def verify_portal_jwt(token):
    """Verifiziert ein Portal-JWT (fw_jwt Cookie). Returns claims dict oder None."""
    if not pyjwt or not PORTAL_JWT_SECRET or not token:
        return None
    try:
        claims = pyjwt.decode(
            token,
            PORTAL_JWT_SECRET,
            algorithms=['HS256'],
            options={'require': ['exp', 'sub']}
        )
        return claims
    except (pyjwt.ExpiredSignatureError, pyjwt.InvalidTokenError) as e:
        logger.debug(f"Portal JWT ungültig: {e}")
        return None


def login_required(f):
    """Decorator für geschützte Routen — prüft Session UND Portal-JWT"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Flask-Session (bestehende Logik)
        if session.get('admin_logged_in'):
            return f(*args, **kwargs)
        # 2. Portal-JWT Cookie (SSO)
        fw_jwt = request.cookies.get('fw_jwt')
        if fw_jwt:
            claims = verify_portal_jwt(fw_jwt)
            if claims and claims.get('app_role') in FOOD_ADMIN_ROLES:
                session['admin_logged_in'] = True
                session['portal_user'] = claims.get('sub')
                session.permanent = True
                return f(*args, **kwargs)
        # 3. Redirect zum Login
        return redirect(url_for('main.login', next=request.url))
    return decorated_function
