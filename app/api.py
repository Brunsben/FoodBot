from flask import Blueprint, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .models import db, User, Menu, Registration, Guest
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
    today_menu = Menu.query.filter_by(date=date.today()).first()
    registrations = Registration.query.filter_by(date=date.today()).all()
    guest_entry = Guest.query.filter_by(date=date.today()).first()
    
    return jsonify({
        'date': date.today().isoformat(),
        'menu': today_menu.description if today_menu else None,
        'registrations': len(registrations),
        'guests': guest_entry.count if guest_entry else 0,
        'total': len(registrations) + (guest_entry.count if guest_entry else 0),
        'users': [{'name': r.user.name, 'personal_number': r.user.personal_number} for r in registrations]
    })

@api.route('/register', methods=['POST'])
@limiter.limit("10 per minute")
def register():
    """An-/Abmelden per API (Karten-ID oder Personalnummer)"""
    data = request.json
    card_id = data.get('card_id')
    personal_number = data.get('personal_number')
    
    user = None
    if card_id:
        user = User.query.filter_by(card_id=card_id).first()
    elif personal_number:
        user = User.query.filter_by(personal_number=personal_number).first()
    
    if not user:
        return jsonify({'success': False, 'message': 'User nicht gefunden'}), 404
    
    from .utils import register_user_for_today
    registered = register_user_for_today(user)
    
    return jsonify({
        'success': True,
        'registered': registered,
        'user': {'name': user.name, 'personal_number': user.personal_number}
    })

@api.route('/stats', methods=['GET'])
def stats():
    """Statistiken über die letzten 7 Tage"""
    days = int(request.args.get('days', 7))
    stats = []
    
    for i in range(days):
        day = date.today() - timedelta(days=i)
        regs = Registration.query.filter_by(date=day).count()
        guest_entry = Guest.query.filter_by(date=day).first()
        guests = guest_entry.count if guest_entry else 0
        menu_entry = Menu.query.filter_by(date=day).first()
        
        stats.append({
            'date': day.isoformat(),
            'registrations': regs,
            'guests': guests,
            'total': regs + guests,
            'menu': menu_entry.description if menu_entry else None
        })
    
    return jsonify({'stats': stats})

@api.route('/users', methods=['GET'])
def users():
    """Liste aller User"""
    all_users = User.query.order_by(User.name).all()
    return jsonify({
        'users': [{'id': u.id, 'name': u.name, 'personal_number': u.personal_number, 'card_id': u.card_id} for u in all_users]
    })
