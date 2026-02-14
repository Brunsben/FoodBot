from flask import Blueprint, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .models import db, User, Menu, Registration, Guest
from .auth import login_required
from datetime import date, datetime, timedelta
from sqlalchemy.orm import joinedload

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
    today_menu = Menu.query.filter_by(date=today).first()
    
    # Performance: N+1 Query-Problem behoben mit joinedload
    registrations = Registration.query.options(
        joinedload(Registration.user)
    ).filter_by(date=today).all()
    
    guest_entry = Guest.query.filter_by(date=today).first()
    
    return jsonify({
        'date': today.isoformat(),
        'menu': today_menu.description if today_menu else None,
        'registrations': len(registrations),
        'guests': guest_entry.count if guest_entry else 0,
        'total': len(registrations) + (guest_entry.count if guest_entry else 0)
    })

@api.route('/register', methods=['POST'])
@limiter.limit("10 per minute")
def register():
    """An-/Abmelden per API (Karten-ID oder Personalnummer)"""
    data = request.json or {}
    card_id = data.get('card_id', '')[:50]  # Input-Validierung
    personal_number = data.get('personal_number', '')[:20]  # Input-Validierung
    try:
        menu_choice = int(data.get('menu_choice', 1))
    except (TypeError, ValueError):
        menu_choice = 1
    if menu_choice not in (1, 2):
        menu_choice = 1
    
    user = None
    if card_id:
        user = User.query.filter_by(card_id=card_id).first()
    elif personal_number:
        user = User.query.filter_by(personal_number=personal_number).first()
    
    if not user:
        return jsonify({'success': False, 'message': 'Benutzer nicht gefunden'}), 404
    
    today = date.today()
    today_menu = Menu.query.filter_by(date=today).first()
    
    # Deadline-Prüfung (Abmeldung nach Deadline erlauben)
    if today_menu and not today_menu.is_registration_open():
        existing_reg = Registration.query.filter_by(user_id=user.id, date=today).first()
        if not existing_reg:
            return jsonify({
                'success': False,
                'message': f'Anmeldefrist abgelaufen ({today_menu.registration_deadline} Uhr)'
            }), 403
    
    if today_menu and today_menu.zwei_menues_aktiv:
        # Prüfe ob User schon angemeldet ist
        existing_reg = Registration.query.filter_by(user_id=user.id, date=today).first()
        if existing_reg:
            # Abmelden
            try:
                db.session.delete(existing_reg)
                db.session.commit()
            except Exception:
                db.session.rollback()
                return jsonify({'success': False, 'message': 'Datenbankfehler'}), 500
            return jsonify({
                'success': True,
                'registered': False,
                'user': {'name': user.name, 'personal_number': user.personal_number}
            })
        else:
            # Wenn menu_choice nicht übergeben wurde, Menüauswahl anfordern
            if 'menu_choice' not in data:
                return jsonify({
                    'success': True,
                    'need_menu_choice': True,
                    'user_id': user.id,
                    'menu1': today_menu.menu1_name,
                    'menu2': today_menu.menu2_name,
                    'user': {'name': user.name, 'personal_number': user.personal_number}
                })
            
            # Anmeldung mit Menüwahl
            reg = Registration(user_id=user.id, date=today, menu_choice=menu_choice)
            try:
                db.session.add(reg)
                db.session.commit()
            except Exception:
                db.session.rollback()
                return jsonify({'success': False, 'message': 'Datenbankfehler'}), 500
            return jsonify({
                'success': True,
                'registered': True,
                'user': {'name': user.name, 'personal_number': user.personal_number}
            })
    
    # Normaler Modus ohne Menüauswahl
    from .utils import register_user_for_today
    registered = register_user_for_today(user)
    
    return jsonify({
        'success': True,
        'registered': registered,
        'user': {'name': user.name, 'personal_number': user.personal_number}
    })

@api.route('/stats', methods=['GET'])
@limiter.limit("30 per minute")
def stats():
    """Statistiken über die letzten 7 Tage"""
    try:
        days = min(int(request.args.get('days', 7)), 90)  # Max 90 Tage
    except (TypeError, ValueError):
        days = 7
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    
    # Batch-Queries statt N+1
    from sqlalchemy import func
    reg_counts = dict(
        db.session.query(Registration.date, func.count(Registration.id))
        .filter(Registration.date >= start_date, Registration.date <= today)
        .group_by(Registration.date).all()
    )
    guest_entries = {
        g.date: g.count for g in
        Guest.query.filter(Guest.date >= start_date, Guest.date <= today).all()
    }
    menu_entries = {
        m.date: m.description for m in
        Menu.query.filter(Menu.date >= start_date, Menu.date <= today).all()
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
    """Liste aller User (mit Pagination)"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)  # Max 100
    
    pagination = User.query.order_by(User.name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'users': [{'id': u.id, 'name': u.name, 'personal_number': u.personal_number, 'card_id': u.card_id} 
                  for u in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })
