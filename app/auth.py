"""
Authentifizierung für den Admin-Bereich
"""
from functools import wraps
from flask import session, redirect, url_for, request
import os
import secrets

# Admin-Passwort aus Environment (zwingend erforderlich)
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
if not ADMIN_PASSWORD or ADMIN_PASSWORD == 'change-this-password':
    raise ValueError("ADMIN_PASSWORD muss in .env gesetzt werden!")

def check_auth(password):
    """Prüft ob das Passwort korrekt ist (timing-safe)"""
    if not password:
        return False
    # Timing-safe Vergleich verhindert Timing-Attacks
    return secrets.compare_digest(password, ADMIN_PASSWORD)

def login_required(f):
    """Decorator für geschützte Routen"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('main.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
