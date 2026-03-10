"""
Synchronisiert Kameraden-Daten vom Portal (via PostgREST).
Kameraden mit Personalnummer werden als lokale FoodBot-User gespiegelt.
"""
import os
import time
import logging

logger = logging.getLogger(__name__)

POSTGREST_URL = os.getenv('POSTGREST_URL', 'http://postgrest:3000')
JWT_SECRET = os.getenv('JWT_SECRET')


def _get_service_jwt():
    """Erstellt ein kurzlebiges Service-JWT für PostgREST-Zugriff."""
    import jwt
    return jwt.encode({
        'role': 'psa_user',
        'app_role': 'Admin',
        'sub': 'foodbot-sync',
        'iat': int(time.time()),
        'exp': int(time.time()) + 300,
    }, JWT_SECRET, algorithm='HS256')


def sync_kameraden():
    """
    Synchronisiert aktive Kameraden (mit Personalnummer) → lokale User-Tabelle.
    Returns (created, updated) tuple.
    """
    if not JWT_SECRET:
        logger.info("JWT_SECRET nicht gesetzt — Sync übersprungen (Standalone-Modus)")
        return 0, 0

    import requests as http_requests
    from .models import db, User

    token = _get_service_jwt()
    resp = http_requests.get(
        f'{POSTGREST_URL}/Kameraden',
        params={
            'select': 'id,Vorname,Name,Personalnummer,KartenID,Aktiv',
            'Personalnummer': 'not.is.null',
            'Aktiv': 'eq.true',
        },
        headers={
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
        },
        timeout=10,
    )
    resp.raise_for_status()
    kameraden = resp.json()

    created, updated = 0, 0
    for k in kameraden:
        pn = (k.get('Personalnummer') or '').strip()
        if not pn:
            continue

        name = f"{k.get('Vorname') or ''} {k.get('Name') or ''}".strip()
        card_id = (k.get('KartenID') or '').strip() or None

        user = User.query.filter_by(personal_number=pn).first()
        if user:
            changed = False
            if user.name != name:
                user.name = name
                changed = True
            if user.card_id != card_id:
                user.card_id = card_id
                changed = True
            if changed:
                updated += 1
        else:
            user = User(name=name, personal_number=pn, card_id=card_id)
            db.session.add(user)
            created += 1

    db.session.commit()
    logger.info(f"Kameraden-Sync: {created} erstellt, {updated} aktualisiert (von {len(kameraden)} Kameraden)")
    return created, updated
