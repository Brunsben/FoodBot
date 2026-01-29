from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, render_template_string
from .models import db, User, Menu, Registration
from .utils import register_user_for_today
from .rfid import find_user_by_card
from .auth import login_required, check_auth, LOGIN_TEMPLATE
from datetime import date
import csv
from io import TextIOWrapper
import threading
import time
import logging
from .qr_generator import generate_qr_code
from .notifications import notification_service

# Logging zentral konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

# Login-Route
@bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password')
        if check_auth(password):
            session['admin_logged_in'] = True
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.admin'))
        else:
            error = 'Falsches Passwort'
    return render_template_string(LOGIN_TEMPLATE, error=error)

@bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('main.index'))

# Simulierter Speicher für den letzten RFID-Scan (in echt: Queue, Shared Memory, etc.)
last_card_id = {'value': None}

@bp.route('/', methods=['GET', 'POST'])
def index():
    today_menu = Menu.query.filter_by(date=date.today()).first()
    message = None
    status = None
    if request.method == 'POST':
        personal_number = request.form.get('personal_number')
        card_id = request.form.get('card_id')
        user = None
        
        # QR-Code-Format: FOODBOT:Personalnummer
        if personal_number and personal_number.startswith('FOODBOT:'):
            personal_number = personal_number.replace('FOODBOT:', '')
        if card_id and card_id.startswith('FOODBOT:'):
            card_id = card_id.replace('FOODBOT:', '')
            personal_number = card_id
            card_id = None
        
        if personal_number:
            user = User.query.filter_by(personal_number=personal_number).first()
        elif card_id:
            user = find_user_by_card(card_id)
        if user:
            registered = register_user_for_today(user)
            if registered:
                message = f"{user.name}, du hast dich zum Essen angemeldet."
                status = 'success'
                logger.info(f"Anmeldung: {user.name} ({user.personal_number})")
                notification_service.notify_new_registration(user.name)
            else:
                message = f"{user.name}, du hast dich abgemeldet."
                status = 'info'
                logger.info(f"Abmeldung: {user.name} ({user.personal_number})")
        else:
            message = "Unbekannte Personalnummer oder Karte. Bitte im Adminbereich anlegen."
            status = 'error'
            logger.warning(f"Fehlversuch Anmeldung: {personal_number or card_id}")
    return render_template('touch.html', menu=today_menu, message=message, status=status)

# Küche: Anzeige und Menü-Eingabe
from .models import Guest

@bp.route('/kitchen', methods=['GET', 'POST'])
def kitchen():
    today_menu = Menu.query.filter_by(date=date.today()).first()
    registrations = Registration.query.filter_by(date=date.today()).all()
    users = sorted([r.user for r in registrations], key=lambda u: u.name.lower())
    guest_entry = Guest.query.filter_by(date=date.today()).first()
    guest_count = guest_entry.count if guest_entry else 0
    
    if request.method == 'POST':
        # Menü speichern
        if 'menu' in request.form:
            menu_text = request.form.get('menu')
            if today_menu:
                today_menu.description = menu_text
            else:
                today_menu = Menu(date=date.today(), description=menu_text)
                db.session.add(today_menu)
            db.session.commit()
            flash('Menü aktualisiert!')
        # Gäste hinzufügen/entfernen
        elif 'guest_action' in request.form:
            action = request.form.get('guest_action')
            if not guest_entry:
                guest_entry = Guest(date=date.today(), count=0)
                db.session.add(guest_entry)
            if action == 'add' and guest_entry.count < 50:
                guest_entry.count += 1
            elif action == 'remove' and guest_entry.count > 0:
                guest_entry.count -= 1
            db.session.commit()
        return redirect(url_for('main.kitchen'))
    
    total = len(users) + guest_count
    return render_template('kitchen.html', menu=today_menu, users=users, guest_count=guest_count, total=total)

@bp.route('/kitchen/data', methods=['GET'])
def kitchen_data():
    """API-Endpunkt für AJAX-Updates der Küchenseite"""
    registrations = Registration.query.filter_by(date=date.today()).all()
    users = sorted([r.user for r in registrations], key=lambda u: u.name.lower())
    guest_entry = Guest.query.filter_by(date=date.today()).first()
    guest_count = guest_entry.count if guest_entry else 0
    
    return jsonify({
        'users': [{'id': u.id, 'name': u.name} for u in users],
        'guest_count': guest_count,
        'total': len(users) + guest_count
    })

@bp.route('/menu/data', methods=['GET'])
def menu_data():
    """API-Endpunkt für AJAX-Updates des Menüs auf der Touch-Seite"""
    today_menu = Menu.query.filter_by(date=date.today()).first()
    return jsonify({
        'menu': today_menu.description if today_menu else None
    })

@bp.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    today_menu = Menu.query.filter_by(date=date.today()).first()
    guest_entry = Guest.query.filter_by(date=date.today()).first()
    guest_count = guest_entry.count if guest_entry else 0
    message = None
    
    if request.method == 'POST':
        # Menü speichern
        if 'menu_text' in request.form:
            menu_text = request.form.get('menu_text').strip()
            if today_menu:
                today_menu.description = menu_text
            else:
                today_menu = Menu(date=date.today(), description=menu_text)
                db.session.add(today_menu)
            db.session.commit()
            message = "Menü gespeichert."
        # Tagesan-/abmeldung
        elif 'user_id' in request.form and 'edit_user' not in request.form:
            user_id = request.form.get('user_id')
            user = User.query.get(user_id)
            if user:
                from .utils import register_user_for_today
                registered = register_user_for_today(user)
                if registered:
                    message = f"{user.name} wurde für heute angemeldet."
                else:
                    message = f"{user.name} wurde für heute abgemeldet."
            else:
                message = "Unbekannter User."
        # User anlegen
        elif 'new_name' in request.form and 'new_personal_number' in request.form:
            name = request.form.get('new_name').strip()
            personal_number = request.form.get('new_personal_number').strip()
            card_id = request.form.get('new_card_id').strip() or None
            if not name or not personal_number:
                message = "Name und Personalnummer erforderlich."
            elif User.query.filter_by(personal_number=personal_number).first():
                message = "Personalnummer existiert bereits."
            else:
                user = User(name=name, personal_number=personal_number, card_id=card_id)
                db.session.add(user)
                db.session.commit()
                message = f"User {name} angelegt."
        # User bearbeiten
        elif 'edit_user' in request.form:
            user_id = request.form.get('edit_user')
            user = User.query.get(user_id)
            if user:
                user.name = request.form.get('edit_name').strip()
                user.personal_number = request.form.get('edit_personal_number').strip()
                user.card_id = request.form.get('edit_card_id').strip() or None
                db.session.commit()
                message = f"User {user.name} aktualisiert."
        # User löschen
        elif 'delete_user' in request.form:
            user_id = request.form.get('delete_user')
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
                message = f"User {user.name} gelöscht."
        # CSV-Import
        elif 'csv_file' in request.files:
            file = request.files['csv_file']
            if file and file.filename.endswith('.csv'):
                try:
                    reader = csv.DictReader(TextIOWrapper(file, encoding='utf-8'))
                    count = 0
                    skipped = 0
                    for row in reader:
                        name = row.get('name') or row.get('Name')
                        personal_number = row.get('personal_number') or row.get('Personalnummer')
                        card_id = row.get('card_id') or row.get('Karte')
                        if name and personal_number:
                            if not User.query.filter_by(personal_number=personal_number).first():
                                user = User(name=name.strip(), personal_number=personal_number.strip(), card_id=(card_id or '').strip() or None)
                                db.session.add(user)
                                count += 1
                            else:
                                skipped += 1
                    db.session.commit()
                    message = f"{count} User importiert, {skipped} übersprungen (bereits vorhanden)."
                    logger.info(f"CSV-Import: {count} User importiert, {skipped} übersprungen")
                except Exception as e:
                    message = f"Fehler beim Import: {str(e)}"
                    logger.error(f"CSV-Import-Fehler: {e}")
        # Gäste verwalten
        elif 'guest_action' in request.form:
            action = request.form.get('guest_action')
            if not guest_entry:
                guest_entry = Guest(date=date.today(), count=0)
                db.session.add(guest_entry)
            if action == 'add' and guest_entry.count < 50:
                guest_entry.count += 1
            elif action == 'remove' and guest_entry.count > 0:
                guest_entry.count -= 1
            elif action == 'set':
                try:
                    count = int(request.form.get('guest_count', 0))
                    guest_entry.count = max(0, min(50, count))
                except ValueError:
                    pass
            db.session.commit()
            message = f"Gästezahl aktualisiert: {guest_entry.count}"
    
    # Daten NACH allen POST-Operationen neu laden
    users = User.query.order_by(User.name).all()
    registrations = Registration.query.filter_by(date=date.today()).all()
    registered_ids = {r.user_id for r in registrations}
    
    return render_template('admin.html', users=users, registered_ids=registered_ids, message=message, menu=today_menu, guest_count=guest_count)

# API-Route für das Touch-Display, um den letzten Scan abzufragen
@bp.route('/rfid_scan')
def rfid_scan():
    card_id = last_card_id['value']
    last_card_id['value'] = None  # Nach Abfrage löschen
    return jsonify({'card_id': card_id})

# Hintergrundthread zum Polling des RFID-Lesers
def rfid_background():
    from .rfid import read_rfid
    while True:
        try:
            card_id = read_rfid()
            if card_id:
                last_card_id['value'] = card_id
        except Exception as e:
            logger.error(f"RFID-Fehler: {e}")
        time.sleep(0.1)

# Starte den Thread beim App-Start
def start_rfid_thread():
    import os
    # Nur starten wenn das RFID-Device existiert
    if os.path.exists('/dev/ttyUSB0'):
        try:
            t = threading.Thread(target=rfid_background, daemon=True)
            t.start()
            logger.info("RFID-Thread gestartet")
        except Exception as e:
            logger.warning(f"RFID-Thread konnte nicht gestartet werden: {e}")
    else:
        logger.info("RFID-Reader nicht verfügbar - Demo-Modus ohne RFID")

@bp.record_once
def on_load(state):
    start_rfid_thread()

@bp.route('/qr/<int:user_id>')
def qr_code(user_id):
    """Generiere QR-Code für User"""
    user = User.query.get_or_404(user_id)
    qr_data = f"FOODBOT:{user.personal_number}"
    qr_image = generate_qr_code(qr_data)
    
    from flask import render_template_string
    template = """
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <title>QR-Code für {{ user.name }}</title>
        <style>
            body { font-family: sans-serif; text-align: center; padding: 40px; }
            .qr-card { display: inline-block; border: 2px solid #000; padding: 20px; border-radius: 12px; }
            img { margin: 20px 0; }
            @media print {
                .no-print { display: none; }
            }
        </style>
    </head>
    <body>
        <div class="qr-card">
            <h1>{{ user.name }}</h1>
            <img src="{{ qr_image }}" alt="QR Code">
            <p><b>Personalnummer:</b> {{ user.personal_number }}</p>
        </div>
        <div class="no-print" style="margin-top:30px;">
            <button onclick="window.print()" style="padding:12px 24px;font-size:1.1em;cursor:pointer;">🖨️ Drucken</button>
            <a href="/admin"><button style="padding:12px 24px;font-size:1.1em;cursor:pointer;">Zurück</button></a>
        </div>
    </body>
    </html>
    """
    return render_template_string(template, user=user, qr_image=qr_image)
    start_rfid_thread()
