from flask import Blueprint, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .models import (
    db, Menu, Registration, Guest, RfidCard,
    get_member_name, get_member_by_personal_number, get_all_members
)
from .auth import login_required
from datetime import date, datetime, timedelta

api = Blueprint('api', __name__, url_prefix='/api')

# Rate Limiter (wird in __init__.py initialisiert)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

@api.route('/status', methods=['GET'])
@limiter.limit("30 per minute")
def status():
    """Aktueller Status: Menü, Anmeldungen, Gäste"""
    today = date.today()
    today_menu = Menu.query.filter_by(datum=today).first()
    
    registrations = Registration.query.filter_by(datum=today).all()
    
    guest_data = Guest.query.filter_by(datum=today).all()
    guest_count = sum(g.anzahl for g in guest_data)
    
    return jsonify({
        'date': today.isoformat(),
        'menu': today_menu.beschreibung if today_menu else None,
        'registrations': len(registrations),
        'guests': guest_count,
        'total': len(registrations) + guest_count
    })

@api.route('/register', methods=['POST'])
@limiter.limit("10 per minute")
def register():
    """An-/Abmelden per API (Karten-ID oder Personalnummer)"""
    data = request.json or {}
    card_id = data.get('card_id', '')[:50]
    personal_number = data.get('personal_number', '')[:20]
    try:
        menu_choice = int(data.get('menu_choice', 1))
    except (TypeError, ValueError):
        menu_choice = 1
    if menu_choice not in (1, 2):
        menu_choice = 1
    
    member_id = None
    if card_id:
        card = RfidCard.query.filter_by(card_id=card_id).first()
        if card:
            member_id = card.member_id
    elif personal_number:
        member_id = get_member_by_personal_number(personal_number)
    
    if not member_id:
        return jsonify({'success': False, 'message': 'Benutzer nicht gefunden'}), 404
    
    member_name = get_member_name(member_id)
    today = date.today()
    today_menu = Menu.query.filter_by(datum=today).first()
    
    # Deadline-Prüfung (Abmeldung nach Deadline erlauben)
    if today_menu and not today_menu.is_registration_open():
        existing_reg = Registration.query.filter_by(member_id=member_id, datum=today).first()
        if not existing_reg:
            return jsonify({
                'success': False,
                'message': f'Anmeldefrist abgelaufen ({today_menu.anmeldefrist} Uhr)'
            }), 403
    
    if today_menu and today_menu.zwei_menues_aktiv:
        existing_reg = Registration.query.filter_by(member_id=member_id, datum=today).first()
        if existing_reg:
            try:
                db.session.delete(existing_reg)
                db.session.commit()
            except Exception:
                db.session.rollback()
                return jsonify({'success': False, 'message': 'Datenbankfehler'}), 500
            return jsonify({
                'success': True,
                'registered': False,
                'user': {'name': member_name}
            })
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
            
            reg = Registration(member_id=member_id, datum=today, menu_wahl=menu_choice)
            try:
                db.session.add(reg)
                db.session.commit()
            except Exception:
                db.session.rollback()
                return jsonify({'success': False, 'message': 'Datenbankfehler'}), 500
            return jsonify({
                'success': True,
                'registered': True,
                'user': {'name': member_name}
            })
    
    # Normaler Modus ohne Menüauswahl
    from .utils import register_member_for_today
    registered = register_member_for_today(member_id)
    
    return jsonify({
        'success': True,
        'registered': registered,
        'user': {'name': member_name}
    })

@api.route('/stats', methods=['GET'])
@limiter.limit("30 per minute")
def stats():
    """Statistiken über die letzten 7 Tage"""
    try:
        days = min(int(request.args.get('days', 7)), 90)
    except (TypeError, ValueError):
        days = 7
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    
    from sqlalchemy import func
    reg_counts = dict(
        db.session.query(Registration.datum, func.count(Registration.id))
        .filter(Registration.datum >= start_date, Registration.datum <= today)
        .group_by(Registration.datum).all()
    )
    guest_entries = {
        g.datum: g.anzahl for g in
        Guest.query.filter(Guest.datum >= start_date, Guest.datum <= today).all()
    }
    menu_entries = {
        m.datum: m.beschreibung for m in
        Menu.query.filter(Menu.datum >= start_date, Menu.datum <= today).all()
    }
    
    result = []
    for i in range(days):
        day = today - timedelta(days=i)
        regs = reg_counts.get(day, 0)
        guests = guest_entries.get(day, 0)
        result.append({
            'date': day.isoformat(),
            'registrations': regs,
            'guests': guests,
            'total': regs + guests,
            'menu': menu_entries.get(day)
        })
    
    return jsonify({'stats': result})

@api.route('/users', methods=['GET'])
@login_required
@limiter.limit("30 per minute")
def users():
    """Liste aller Mitglieder (aus fw_common.members)"""
    members = get_all_members()
    return jsonify({
        'users': [{'id': m['id'], 'name': m['name']} for m in members],
        'total': len(members)
    })
