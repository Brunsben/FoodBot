"""
FoodBot REST API (v2) – Alle Endpoints für das Vue 3 Frontend.
Prefix: /api
"""
from flask import Blueprint, jsonify, request, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .models import (
    db, Menu, Registration, Guest, RfidCard, MobileToken, PresetMenu, AdminLog,
    get_member_name, get_member_by_personal_number, get_all_members, get_member
)
from .auth import login_required, check_auth, verify_jwt, ADMIN_PASSWORD
from .utils import save_menu as _save_menu_form, register_member_for_today, get_menu_for_date, get_guests_for_date
from datetime import date, datetime, timedelta
from sqlalchemy import func
import secrets
import logging

logger = logging.getLogger(__name__)

api = Blueprint('api', __name__, url_prefix='/api')

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# ═══════════════════════════════════════════════════════════════════════════════
# Öffentliche Endpoints (kein Auth)
# ═══════════════════════════════════════════════════════════════════════════════

@api.route('/status', methods=['GET'])
@api.route('/today', methods=['GET'])
@limiter.limit("60 per minute")
def today():
    """Tages-Status: Menü, Anmeldungen, Gäste, Deadline"""
    today_date = date.today()
    today_menu = Menu.query.filter_by(datum=today_date).first()
    regs = Registration.query.filter_by(datum=today_date).all()
    guests_data = get_guests_for_date(today_date)

    # Anmeldungen mit Namen anreichern
    reg_list = []
    for r in regs:
        reg_list.append({
            'id': str(r.id),
            'member_id': str(r.member_id),
            'datum': r.datum.isoformat(),
            'menu_wahl': r.menu_wahl,
            'member_name': get_member_name(r.member_id),
        })

    # Gäste
    guest_list = []
    for g in guests_data['all']:
        guest_list.append({
            'id': str(g.id),
            'datum': g.datum.isoformat(),
            'menu_wahl': g.menu_wahl,
            'anzahl': g.anzahl,
        })

    menu_dict = None
    if today_menu:
        menu_dict = _menu_to_dict(today_menu)

    regs_menu1 = [r for r in regs if r.menu_wahl == 1]
    regs_menu2 = [r for r in regs if r.menu_wahl == 2]
    g1 = guests_data['menu1']
    g2 = guests_data['menu2']

    return jsonify({
        'menu': menu_dict,
        'registrations': reg_list,
        'guests': guest_list,
        'total': len(regs) + guests_data['total_count'],
        'total_menu1': len(regs_menu1) + (g1.anzahl if g1 else 0),
        'total_menu2': len(regs_menu2) + (g2.anzahl if g2 else 0),
        'guest_count': guests_data['total_count'],
        'guest_count_menu1': g1.anzahl if g1 else 0,
        'guest_count_menu2': g2.anzahl if g2 else 0,
        'deadline_passed': not today_menu.is_registration_open() if today_menu else False,
        'member_count': len(get_all_members()),
    })


@api.route('/register', methods=['POST'])
@limiter.limit("20 per minute")
def register():
    """An-/Abmelden per Personalnummer oder RFID."""
    data = request.json or {}
    personalnummer = (data.get('personalnummer') or data.get('personal_number') or '')[:20]
    rfid = (data.get('rfid') or data.get('card_id') or '')[:50]
    try:
        menu_choice = int(data.get('menu_choice', 1))
    except (TypeError, ValueError):
        menu_choice = 1
    if menu_choice not in (1, 2):
        menu_choice = 1

    member_id = None
    if rfid:
        card = RfidCard.query.filter_by(card_id=rfid).first()
        if card:
            member_id = card.member_id
    if not member_id and personalnummer:
        # Personalnummer = Dienstgrad-basierte Nummer in fw_common
        result = db.session.execute(
            db.text('''SELECT id FROM fw_common.members
                       WHERE "Aktiv" = true AND (
                         CAST(id AS TEXT) = :pn OR
                         "Email" = :pn OR
                         "Vorname" || ' ' || "Name" = :pn
                       ) LIMIT 1'''),
            {'pn': personalnummer}
        ).fetchone()
        if result:
            member_id = result[0]
        else:
            # Fallback: RFID-Karten-ID als Personalnummer
            card = RfidCard.query.filter_by(card_id=personalnummer).first()
            if card:
                member_id = card.member_id

    if not member_id:
        return jsonify({'success': False, 'message': 'Mitglied nicht gefunden'}), 404

    member_name = get_member_name(member_id)
    today_date = date.today()
    today_menu = Menu.query.filter_by(datum=today_date).first()

    # Deadline
    if today_menu and not today_menu.is_registration_open():
        existing = Registration.query.filter_by(member_id=member_id, datum=today_date).first()
        if not existing:
            return jsonify({
                'success': False,
                'message': f'Anmeldefrist abgelaufen ({today_menu.anmeldefrist} Uhr)'
            }), 403

    # Zwei-Menü-Modus
    if today_menu and today_menu.zwei_menues_aktiv:
        existing = Registration.query.filter_by(member_id=member_id, datum=today_date).first()
        if existing:
            try:
                db.session.delete(existing)
                db.session.commit()
            except Exception:
                db.session.rollback()
                return jsonify({'success': False, 'message': 'Datenbankfehler'}), 500
            return jsonify({'success': True, 'registered': False, 'user': {'name': member_name}})
        else:
            if 'menu_choice' not in data:
                return jsonify({
                    'success': True,
                    'need_menu_choice': True,
                    'member_id': str(member_id),
                    'menu1': today_menu.menu1_name,
                    'menu2': today_menu.menu2_name,
                    'user': {'name': member_name}
                })
            reg = Registration(member_id=member_id, datum=today_date, menu_wahl=menu_choice)
            try:
                db.session.add(reg)
                db.session.commit()
            except Exception:
                db.session.rollback()
                return jsonify({'success': False, 'message': 'Datenbankfehler'}), 500
            return jsonify({'success': True, 'registered': True, 'user': {'name': member_name}})

    # Normal-Modus (Toggle)
    registered = register_member_for_today(member_id)
    return jsonify({'success': True, 'registered': registered, 'user': {'name': member_name}})


@api.route('/menu/today', methods=['GET'])
@limiter.limit("60 per minute")
def menu_today():
    """Menü für heute (Touch-Polling)."""
    today_menu = get_menu_for_date()
    if not today_menu:
        return jsonify({'menu': None, 'deadline_passed': False})
    return jsonify({
        'menu': _menu_to_dict(today_menu),
        'deadline_passed': not today_menu.is_registration_open(),
    })


@api.route('/kitchen/data', methods=['GET'])
@limiter.limit("60 per minute")
def kitchen_data():
    """Küchendaten (Live-Polling)."""
    today_date = date.today()
    today_menu = Menu.query.filter_by(datum=today_date).first()
    regs = Registration.query.filter_by(datum=today_date).order_by(Registration.created_at.desc()).all()
    guests_data = get_guests_for_date(today_date)

    reg_list = []
    for r in regs:
        reg_list.append({
            'id': str(r.id),
            'member_id': str(r.member_id),
            'member_name': get_member_name(r.member_id),
            'menu_wahl': r.menu_wahl,
        })

    g1 = guests_data['menu1']
    g2 = guests_data['menu2']

    return jsonify({
        'menu': _menu_to_dict(today_menu) if today_menu else None,
        'registrations': reg_list,
        'total': len(regs) + guests_data['total_count'],
        'total_menu1': len([r for r in regs if r.menu_wahl == 1]) + (g1.anzahl if g1 else 0),
        'total_menu2': len([r for r in regs if r.menu_wahl == 2]) + (g2.anzahl if g2 else 0),
        'guest_count': guests_data['total_count'],
        'guest_count_menu1': g1.anzahl if g1 else 0,
        'guest_count_menu2': g2.anzahl if g2 else 0,
    })


@api.route('/kitchen/print-data', methods=['GET'])
@limiter.limit("30 per minute")
def kitchen_print_data():
    """Druckliste als JSON."""
    today_date = date.today()
    today_menu = Menu.query.filter_by(datum=today_date).first()
    regs = Registration.query.filter_by(datum=today_date).all()
    guests_data = get_guests_for_date(today_date)

    # Gruppiert nach Menü
    menu1_names = sorted([get_member_name(r.member_id) for r in regs if r.menu_wahl == 1])
    menu2_names = sorted([get_member_name(r.member_id) for r in regs if r.menu_wahl == 2])
    g1 = guests_data['menu1']
    g2 = guests_data['menu2']

    return jsonify({
        'menu': _menu_to_dict(today_menu) if today_menu else None,
        'menu1_names': menu1_names,
        'menu2_names': menu2_names,
        'guest_count_menu1': g1.anzahl if g1 else 0,
        'guest_count_menu2': g2.anzahl if g2 else 0,
        'total_menu1': len(menu1_names) + (g1.anzahl if g1 else 0),
        'total_menu2': len(menu2_names) + (g2.anzahl if g2 else 0),
        'total': len(regs) + guests_data['total_count'],
        'date': today_date.isoformat(),
    })


@api.route('/stats', methods=['GET'])
@limiter.limit("30 per minute")
def stats():
    """Statistiken über die letzten N Tage."""
    try:
        days = min(int(request.args.get('days', 14)), 90)
    except (TypeError, ValueError):
        days = 14
    today_date = date.today()
    start = today_date - timedelta(days=days - 1)

    reg_counts = dict(
        db.session.query(Registration.datum, func.count(Registration.id))
        .filter(Registration.datum >= start, Registration.datum <= today_date)
        .group_by(Registration.datum).all()
    )
    guest_sums = {}
    for g in Guest.query.filter(Guest.datum >= start, Guest.datum <= today_date).all():
        guest_sums[g.datum] = guest_sums.get(g.datum, 0) + g.anzahl
    menu_map = {
        m.datum: m.beschreibung for m in
        Menu.query.filter(Menu.datum >= start, Menu.datum <= today_date).all()
    }

    result = []
    for i in range(days):
        day = today_date - timedelta(days=i)
        regs = reg_counts.get(day, 0)
        guests = guest_sums.get(day, 0)
        result.append({
            'datum': day.isoformat(),
            'beschreibung': menu_map.get(day, ''),
            'anzahl': regs,
            'gaeste': guests,
            'total': regs + guests,
        })
    return jsonify(result)


# ═══════════════════════════════════════════════════════════════════════════════
# Auth
# ═══════════════════════════════════════════════════════════════════════════════

@api.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def auth_login():
    """Admin-Login → JWT oder Session."""
    data = request.json or {}
    password = data.get('password', '')
    if not check_auth(password):
        return jsonify({'error': 'Falsches Passwort'}), 401
    # JWT generieren (einfacher HMAC-Token für Standalone)
    import os, json, base64, hmac, hashlib, time
    jwt_secret = os.getenv('JWT_SECRET', os.getenv('ADMIN_PASSWORD', 'foodbot-default-secret'))
    payload = {
        'sub': 'admin',
        'role': 'admin',
        'app_role': 'Admin',
        'iat': int(time.time()),
        'exp': int(time.time()) + 86400 * 7,  # 7 Tage
    }
    header = base64.urlsafe_b64encode(json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode()).rstrip(b'=').decode()
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()
    sig = hmac.new(jwt_secret.encode(), f"{header}.{payload_b64}".encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b'=').decode()
    token = f"{header}.{payload_b64}.{sig_b64}"
    # Auch Session setzen
    session['admin_logged_in'] = True
    session['jwt_token'] = token
    return jsonify({'token': token})


@api.route('/auth/check', methods=['GET'])
def auth_check():
    """Auth-Status prüfen."""
    from .auth import get_jwt_from_request
    claims = get_jwt_from_request()
    if claims:
        return jsonify({'authenticated': True, 'role': claims.get('app_role', 'admin')})
    if session.get('admin_logged_in'):
        return jsonify({'authenticated': True, 'role': 'admin'})
    return jsonify({'authenticated': False})


# ═══════════════════════════════════════════════════════════════════════════════
# Admin-Endpoints (Auth required)
# ═══════════════════════════════════════════════════════════════════════════════

@api.route('/members', methods=['GET'])
@login_required
@limiter.limit("30 per minute")
def members():
    """Alle aktiven Mitglieder."""
    all_members = get_all_members()
    # RFID-Status und Registrierungsstatus hinzufügen
    today_date = date.today()
    reg_member_ids = {str(r.member_id) for r in Registration.query.filter_by(datum=today_date).all()}
    rfid_member_ids = {str(c.member_id) for c in RfidCard.query.all()}

    result = []
    for m in all_members:
        result.append({
            **m,
            'registered_today': m['id'] in reg_member_ids,
            'has_rfid': m['id'] in rfid_member_ids,
        })
    return jsonify(result)


# Compat: altes /api/users
@api.route('/users', methods=['GET'])
@login_required
@limiter.limit("30 per minute")
def users_compat():
    all_m = get_all_members()
    return jsonify({'users': [{'id': m['id'], 'name': m['name']} for m in all_m], 'total': len(all_m)})


@api.route('/menu', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def save_menu():
    """Menü für ein Datum speichern/aktualisieren."""
    data = request.json or {}
    datum_str = data.get('datum', date.today().isoformat())
    try:
        menu_date = date.fromisoformat(datum_str)
    except ValueError:
        return jsonify({'error': 'Ungültiges Datum'}), 400

    beschreibung = data.get('beschreibung', '').strip()
    zwei_menues = data.get('zwei_menues', False)
    menu1_name = data.get('menu1_name', '').strip() if zwei_menues else None
    menu2_name = data.get('menu2_name', '').strip() if zwei_menues else None
    anmeldefrist = data.get('anmeldefrist', '19:45')
    frist_aktiv = data.get('frist_aktiv', True)

    if zwei_menues:
        beschreibung = f"{menu1_name or ''} / {menu2_name or ''}"

    existing = Menu.query.filter_by(datum=menu_date).first()
    if existing:
        existing.beschreibung = beschreibung
        existing.zwei_menues_aktiv = zwei_menues
        existing.menu1_name = menu1_name
        existing.menu2_name = menu2_name
        existing.anmeldefrist = anmeldefrist
        existing.frist_aktiv = frist_aktiv
    else:
        existing = Menu(
            datum=menu_date, beschreibung=beschreibung,
            zwei_menues_aktiv=zwei_menues, menu1_name=menu1_name, menu2_name=menu2_name,
            anmeldefrist=anmeldefrist, frist_aktiv=frist_aktiv,
        )
        db.session.add(existing)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Datenbankfehler'}), 500

    _log_action('menu_save', f'Menü für {datum_str}: {beschreibung}')
    return jsonify(_menu_to_dict(existing))


@api.route('/menu/<datum>', methods=['DELETE'])
@login_required
def delete_menu(datum):
    """Menü für ein Datum löschen."""
    try:
        menu_date = date.fromisoformat(datum)
    except ValueError:
        return jsonify({'error': 'Ungültiges Datum'}), 400
    existing = Menu.query.filter_by(datum=menu_date).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        _log_action('menu_delete', f'Menü für {datum} gelöscht')
    return '', 204


# ── Gäste ──────────────────────────────────────────────────────────────────

@api.route('/guests', methods=['POST'])
@login_required
def set_guests_count():
    """Gäste-Anzahl direkt setzen."""
    data = request.json or {}
    datum_str = data.get('datum', date.today().isoformat())
    menu_wahl = int(data.get('menu_wahl', 1))
    anzahl = max(0, int(data.get('anzahl', 0)))
    try:
        target = date.fromisoformat(datum_str)
    except ValueError:
        return jsonify({'error': 'Ungültiges Datum'}), 400

    guest = Guest.query.filter_by(datum=target, menu_wahl=menu_wahl).first()
    if guest:
        guest.anzahl = anzahl
    else:
        guest = Guest(datum=target, menu_wahl=menu_wahl, anzahl=anzahl)
        db.session.add(guest)
    db.session.commit()
    return jsonify({'datum': target.isoformat(), 'menu_wahl': menu_wahl, 'anzahl': guest.anzahl})


@api.route('/guests/add', methods=['POST'])
def add_guest():
    """Gäste +1."""
    data = request.json or {}
    datum_str = data.get('datum', date.today().isoformat())
    menu_wahl = int(data.get('menu_wahl', 1))
    try:
        target = date.fromisoformat(datum_str)
    except ValueError:
        return jsonify({'error': 'Ungültiges Datum'}), 400

    guest = Guest.query.filter_by(datum=target, menu_wahl=menu_wahl).first()
    if guest:
        guest.anzahl = max(0, guest.anzahl + 1)
    else:
        guest = Guest(datum=target, menu_wahl=menu_wahl, anzahl=1)
        db.session.add(guest)
    db.session.commit()
    return jsonify({'anzahl': guest.anzahl})


@api.route('/guests/remove', methods=['POST'])
def remove_guest():
    """Gäste -1."""
    data = request.json or {}
    datum_str = data.get('datum', date.today().isoformat())
    menu_wahl = int(data.get('menu_wahl', 1))
    try:
        target = date.fromisoformat(datum_str)
    except ValueError:
        return jsonify({'error': 'Ungültiges Datum'}), 400

    guest = Guest.query.filter_by(datum=target, menu_wahl=menu_wahl).first()
    if guest and guest.anzahl > 0:
        guest.anzahl -= 1
        db.session.commit()
        return jsonify({'anzahl': guest.anzahl})
    return jsonify({'anzahl': 0})


# ── RFID ───────────────────────────────────────────────────────────────────

@api.route('/rfid', methods=['GET'])
@login_required
def list_rfid():
    """Alle RFID-Karten mit Mitgliedsnamen."""
    cards = RfidCard.query.all()
    result = []
    for c in cards:
        result.append({
            'id': str(c.id),
            'card_id': c.card_id,
            'member_id': str(c.member_id),
            'member_name': get_member_name(c.member_id),
        })
    return jsonify(result)


@api.route('/rfid', methods=['POST'])
@login_required
def assign_rfid():
    """RFID-Karte einem Mitglied zuweisen."""
    data = request.json or {}
    member_id = data.get('member_id')
    card_id = data.get('card_id', '').strip()
    if not member_id or not card_id:
        return jsonify({'error': 'member_id und card_id erforderlich'}), 400

    existing = RfidCard.query.filter_by(card_id=card_id).first()
    if existing:
        return jsonify({'error': 'Karte bereits zugewiesen'}), 409

    card = RfidCard(card_id=card_id, member_id=member_id)
    db.session.add(card)
    db.session.commit()
    _log_action('rfid_assign', f'RFID {card_id} → {get_member_name(member_id)}')
    return jsonify({'id': str(card.id), 'card_id': card.card_id, 'member_id': str(card.member_id)}), 201


@api.route('/rfid/<card_id>', methods=['DELETE'])
@login_required
def remove_rfid(card_id):
    """RFID-Karte entfernen."""
    card = RfidCard.query.filter_by(card_id=card_id).first()
    if not card:
        card = RfidCard.query.filter_by(id=card_id).first()
    if card:
        _log_action('rfid_remove', f'RFID {card.card_id} entfernt')
        db.session.delete(card)
        db.session.commit()
    return '', 204


# ── Presets ────────────────────────────────────────────────────────────────

@api.route('/presets', methods=['GET'])
@login_required
def list_presets():
    return jsonify([{'id': str(p.id), 'name': p.name, 'sort_order': p.sort_order}
                    for p in PresetMenu.get_all_ordered()])


@api.route('/presets', methods=['POST'])
@login_required
def add_preset():
    data = request.json or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Name erforderlich'}), 400
    existing = PresetMenu.query.filter_by(name=name).first()
    if existing:
        return jsonify({'error': 'Preset existiert bereits'}), 409
    p = PresetMenu(name=name)
    db.session.add(p)
    db.session.commit()
    return jsonify({'id': str(p.id), 'name': p.name}), 201


@api.route('/presets/<preset_id>', methods=['DELETE'])
@login_required
def delete_preset(preset_id):
    p = PresetMenu.query.filter_by(id=preset_id).first()
    if p:
        db.session.delete(p)
        db.session.commit()
    return '', 204


# ── Wochenplan ─────────────────────────────────────────────────────────────

@api.route('/weekly', methods=['GET'])
@login_required
def weekly_plan():
    """14-Tage-Wochenplan."""
    today_date = date.today()
    days = []
    for i in range(14):
        d = today_date + timedelta(days=i)
        menu = Menu.query.filter_by(datum=d).first()
        reg_count = Registration.query.filter_by(datum=d).count()
        days.append({
            'datum': d.isoformat(),
            'menu': _menu_to_dict(menu) if menu else None,
            'registrations_count': reg_count,
        })
    return jsonify(days)


@api.route('/weekly/<datum>', methods=['POST'])
@login_required
def save_weekly_day(datum):
    """Tag im Wochenplan speichern."""
    data = request.json or {}
    data['datum'] = datum
    # Delegieren an /menu endpoint Logik
    try:
        menu_date = date.fromisoformat(datum)
    except ValueError:
        return jsonify({'error': 'Ungültiges Datum'}), 400

    beschreibung = data.get('beschreibung', '').strip()
    zwei_menues = data.get('zwei_menues', False)
    menu1_name = data.get('menu1_name', '').strip() if zwei_menues else None
    menu2_name = data.get('menu2_name', '').strip() if zwei_menues else None
    anmeldefrist = data.get('anmeldefrist', '19:45')
    frist_aktiv = data.get('frist_aktiv', True)

    if zwei_menues:
        beschreibung = f"{menu1_name or ''} / {menu2_name or ''}"

    existing = Menu.query.filter_by(datum=menu_date).first()
    if existing:
        existing.beschreibung = beschreibung
        existing.zwei_menues_aktiv = zwei_menues
        existing.menu1_name = menu1_name
        existing.menu2_name = menu2_name
        existing.anmeldefrist = anmeldefrist
        existing.frist_aktiv = frist_aktiv
    else:
        existing = Menu(
            datum=menu_date, beschreibung=beschreibung,
            zwei_menues_aktiv=zwei_menues, menu1_name=menu1_name, menu2_name=menu2_name,
            anmeldefrist=anmeldefrist, frist_aktiv=frist_aktiv,
        )
        db.session.add(existing)
    db.session.commit()
    return jsonify(_menu_to_dict(existing))


@api.route('/weekly/<datum>', methods=['DELETE'])
@login_required
def delete_weekly_day(datum):
    try:
        menu_date = date.fromisoformat(datum)
    except ValueError:
        return jsonify({'error': 'Ungültiges Datum'}), 400
    menu = Menu.query.filter_by(datum=menu_date).first()
    if menu:
        db.session.delete(menu)
        db.session.commit()
    return '', 204


# ── Historie ───────────────────────────────────────────────────────────────

@api.route('/history', methods=['GET'])
@login_required
def history_overview():
    """Historie-Übersicht: Alle Mitglieder mit Essens-Statistik."""
    all_members = get_all_members()
    # Aggregierte Daten pro Mitglied
    member_stats = dict(
        db.session.query(Registration.member_id, func.count(Registration.id))
        .group_by(Registration.member_id).all()
    )
    last_dates = dict(
        db.session.query(Registration.member_id, func.max(Registration.datum))
        .group_by(Registration.member_id).all()
    )

    result = []
    for m in all_members:
        mid = m['id']
        total = member_stats.get(mid, 0)
        if total == 0:
            # UUID-Suche
            import uuid as uuid_mod
            try:
                uid = uuid_mod.UUID(mid)
                total = member_stats.get(uid, 0)
                letzte = last_dates.get(uid)
            except ValueError:
                letzte = None
        else:
            letzte = last_dates.get(mid)

        result.append({
            'member_id': mid,
            'name': m['name'],
            'total': total,
            'letzte': letzte.isoformat() if letzte else None,
        })

    # Top-10 sortieren
    result.sort(key=lambda x: x['total'], reverse=True)
    return jsonify({'members': result, 'top10': result[:10]})


@api.route('/history/<member_id>', methods=['GET'])
@login_required
def history_detail(member_id):
    """Detail-Historie eines Mitglieds (paginiert)."""
    page_nr = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page_nr - 1) * per_page

    regs = (Registration.query
            .filter_by(member_id=member_id)
            .order_by(Registration.datum.desc())
            .offset(offset).limit(per_page + 1).all())

    has_more = len(regs) > per_page
    regs = regs[:per_page]

    # Menü-Infos
    dates = [r.datum for r in regs]
    menus = {m.datum: m.beschreibung for m in Menu.query.filter(Menu.datum.in_(dates)).all()} if dates else {}

    member = get_member(member_id)
    return jsonify({
        'member': member,
        'registrations': [{
            'datum': r.datum.isoformat(),
            'menu_wahl': r.menu_wahl,
            'menu': menus.get(r.datum, ''),
        } for r in regs],
        'page': page_nr,
        'has_more': has_more,
    })


# ── Admin-Aktionen ────────────────────────────────────────────────────────

@api.route('/admin/register', methods=['POST'])
@login_required
def admin_register():
    """Admin meldet ein Mitglied für heute an/ab."""
    data = request.json or {}
    member_id = data.get('member_id')
    menu_choice = data.get('menu_choice', 1)
    if not member_id:
        return jsonify({'error': 'member_id erforderlich'}), 400

    today_date = date.today()
    today_menu = Menu.query.filter_by(datum=today_date).first()

    # Zwei-Menü: direkt mit Wahl
    if today_menu and today_menu.zwei_menues_aktiv:
        existing = Registration.query.filter_by(member_id=member_id, datum=today_date).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            return jsonify({'registered': False, 'name': get_member_name(member_id)})
        if not menu_choice or menu_choice not in (1, 2):
            return jsonify({
                'need_menu_choice': True,
                'menu1': today_menu.menu1_name,
                'menu2': today_menu.menu2_name,
            })
        reg = Registration(member_id=member_id, datum=today_date, menu_wahl=int(menu_choice))
        db.session.add(reg)
        db.session.commit()
        return jsonify({'registered': True, 'name': get_member_name(member_id)})

    # Normal-Modus
    registered = register_member_for_today(member_id, int(menu_choice) if menu_choice else 1)
    return jsonify({'registered': registered, 'name': get_member_name(member_id)})


@api.route('/system/log', methods=['GET'])
@login_required
def system_log():
    """Admin-Log (letzte 100)."""
    logs = AdminLog.query.order_by(AdminLog.zeitpunkt.desc()).limit(100).all()
    return jsonify([{
        'id': str(l.id),
        'zeitpunkt': l.zeitpunkt.isoformat() if l.zeitpunkt else None,
        'aktion': l.aktion,
        'details': l.details,
    } for l in logs])


# ── Mobile ─────────────────────────────────────────────────────────────────

@api.route('/mobile/<token>', methods=['GET'])
@limiter.limit("30 per minute")
def mobile_status(token):
    """Mobile Status per Token."""
    mt = MobileToken.query.filter_by(token=token).first()
    if not mt:
        return jsonify({'error': 'Ungültiger Token'}), 404

    member = get_member(mt.member_id)
    today_date = date.today()
    today_menu = Menu.query.filter_by(datum=today_date).first()
    reg = Registration.query.filter_by(member_id=mt.member_id, datum=today_date).first()

    return jsonify({
        'member': member,
        'menu': _menu_to_dict(today_menu) if today_menu else None,
        'registered': reg is not None,
        'menu_wahl': reg.menu_wahl if reg else None,
        'deadline_passed': not today_menu.is_registration_open() if today_menu else False,
    })


@api.route('/mobile/<token>', methods=['POST'])
@limiter.limit("10 per minute")
def mobile_register(token):
    """Mobile An-/Abmeldung per Token."""
    mt = MobileToken.query.filter_by(token=token).first()
    if not mt:
        return jsonify({'error': 'Ungültiger Token'}), 404

    data = request.json or {}
    menu_choice = data.get('menu_choice', 1)
    today_date = date.today()
    today_menu = Menu.query.filter_by(datum=today_date).first()

    if today_menu and not today_menu.is_registration_open():
        existing = Registration.query.filter_by(member_id=mt.member_id, datum=today_date).first()
        if not existing:
            return jsonify({'error': f'Anmeldefrist abgelaufen ({today_menu.anmeldefrist} Uhr)'}), 403

    if today_menu and today_menu.zwei_menues_aktiv:
        existing = Registration.query.filter_by(member_id=mt.member_id, datum=today_date).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            return jsonify({'registered': False})
        if not menu_choice or menu_choice not in (1, 2):
            return jsonify({
                'need_menu_choice': True,
                'menu1': today_menu.menu1_name,
                'menu2': today_menu.menu2_name,
            })
        reg = Registration(member_id=mt.member_id, datum=today_date, menu_wahl=int(menu_choice))
        db.session.add(reg)
        db.session.commit()
        return jsonify({'registered': True})

    registered = register_member_for_today(mt.member_id, int(menu_choice) if menu_choice else 1)
    return jsonify({'registered': registered})


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _menu_to_dict(menu):
    """Menu-Objekt → JSON-Dict."""
    if not menu:
        return None
    return {
        'id': str(menu.id),
        'datum': menu.datum.isoformat(),
        'beschreibung': menu.beschreibung,
        'zwei_menues': menu.zwei_menues_aktiv,
        'menu1_name': menu.menu1_name,
        'menu2_name': menu.menu2_name,
        'anmeldefrist': menu.anmeldefrist,
        'frist_aktiv': menu.frist_aktiv,
    }


def _log_action(action, details=''):
    """Admin-Aktion loggen."""
    try:
        log = AdminLog(admin_user='api', aktion=action, details=details)
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()
