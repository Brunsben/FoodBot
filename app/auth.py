"""
Authentifizierung für den Admin-Bereich.
Unterstützt:
  1. JWT-Token (aus fw_common, shared Auth) – bevorzugt
  2. Session-basiert (Admin-Passwort Fallback für Standalone-Betrieb)
"""
from functools import wraps
from flask import session, redirect, url_for, request, jsonify, current_app
import os
import secrets
import hmac
import hashlib
import base64
import json
import time
import logging

logger = logging.getLogger(__name__)

# Admin-Passwort aus Environment (optional – JWT wird bevorzugt)
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')

def _b64decode(data: str) -> bytes:
    """Base64URL-Decode mit Padding."""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)

def verify_jwt(token: str) -> dict | None:
    """
    Validiert ein JWT gegen das shared JWT_SECRET (fw_common).
    Gibt die Claims zurück oder None bei ungültigem Token.
    """
    jwt_secret = os.getenv('JWT_SECRET', '')
    if not jwt_secret:
        return None
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        # Signatur prüfen
        expected_sig = hmac.new(
            jwt_secret.encode('utf-8'),
            f"{header_b64}.{payload_b64}".encode('utf-8'),
            hashlib.sha256
        ).digest()
        actual_sig = _b64decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        # Payload decodieren
        payload = json.loads(_b64decode(payload_b64))
        # Ablauf prüfen
        if payload.get('exp', 0) < time.time():
            return None
        return payload
    except Exception as e:
        logger.debug(f"JWT-Validierung fehlgeschlagen: {e}")
        return None

def check_auth(password: str) -> bool:
    """Prüft Passwort ODER JWT-Token."""
    if not password:
        return False
    # Zuerst als JWT versuchen
    claims = verify_jwt(password)
    if claims and claims.get('app_role') in ('Admin', 'Kleiderwart'):
        return True
    # Fallback: Admin-Passwort
    if ADMIN_PASSWORD and ADMIN_PASSWORD != 'change-this-password':
        return secrets.compare_digest(password, ADMIN_PASSWORD)
    return False

def get_jwt_from_request() -> dict | None:
    """Extrahiert und validiert JWT aus Authorization-Header oder Session."""
    # Authorization: Bearer <token>
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return verify_jwt(auth_header[7:])
    # Session-JWT
    token = session.get('jwt_token')
    if token:
        return verify_jwt(token)
    return None

def login_required(f):
    """Decorator für geschützte Routen. Akzeptiert JWT oder Session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # JWT im Authorization-Header?
        claims = get_jwt_from_request()
        if claims:
            request._jwt_claims = claims
            return f(*args, **kwargs)
        # Session-basiert (altes Verhalten)
        if session.get('admin_logged_in'):
            return f(*args, **kwargs)
        # API-Request → 401 JSON
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({'error': 'Nicht authentifiziert'}), 401
        return redirect(url_for('main.login', next=request.url))
    return decorated_function
