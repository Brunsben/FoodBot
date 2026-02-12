"""
Authentifizierung für den Admin-Bereich
"""
from functools import wraps
from flask import session, redirect, url_for, request
import os

# Admin-Passwort aus Environment oder Default
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'feuerwehr2026')

def check_auth(password):
    """Prüft ob das Passwort korrekt ist"""
    return password == ADMIN_PASSWORD

def login_required(f):
    """Decorator für geschützte Routen"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('main.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
