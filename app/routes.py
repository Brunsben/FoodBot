from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, render_template_string, make_response
from .models import db, User, Menu, Registration
from .utils import register_user_for_today
from .rfid import find_user_by_card
from .auth import login_required, check_auth, LOGIN_TEMPLATE
from datetime import date
import csv
from io import TextIOWrapper, StringIO
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
    need_menu_choice = False
    pending_user_id = None
    pending_card_id = None
    pending_personal_number = None
    
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
            # Prüfe ob zwei Menüs aktiv sind
            if today_menu and today_menu.zwei_menues_aktiv:
                # Prüfe ob User schon angemeldet ist
                existing_reg = Registration.query.filter_by(user_id=user.id, date=date.today()).first()
                if existing_reg:
                    # Abmelden
                    menu_name = today_menu.menu1_name if existing_reg.menu_choice == 1 else today_menu.menu2_name
                    db.session.delete(existing_reg)
                    db.session.commit()
                    message = f"{user.name}, du wurdest abgemeldet.\n{menu_name}"
                    status = 'cancel'
                    logger.info(f"Abmeldung: {user.name} ({user.personal_number})")
                else:
                    # Zeige Menüauswahl
                    need_menu_choice = True
                    pending_user_id = user.id
                    pending_card_id = card_id
                    pending_personal_number = personal_number
                    message = "Bitte wähle dein Menü"
                    status = 'info'
            else:
                # Normaler Modus ohne Menüauswahl
                registered = register_user_for_today(user)
                if registered:
                    menu_text = today_menu.description if today_menu else "Kein Menü"
                    message = f"{user.name}, du bist angemeldet!\n{menu_text}"
                    status = 'success'
                    logger.info(f"Anmeldung: {user.name} ({user.personal_number})")
                    notification_service.notify_new_registration(user.name)
                else:
                    menu_text = today_menu.description if today_menu else ""
                    message = f"{user.name}, du wurdest abgemeldet.\n{menu_text}"
                    status = 'cancel'
                    logger.info(f"Abmeldung: {user.name} ({user.personal_number})")
        else:
            message = "Unbekannte Personalnummer oder Karte. Bitte im Adminbereich anlegen."
            status = 'error'
            logger.warning(f"Fehlversuch Anmeldung: {personal_number or card_id}")
    
    return render_template('touch.html', 
                         menu=today_menu, 
                         message=message, 
                         status=status,
                         need_menu_choice=need_menu_choice,
                         pending_user_id=pending_user_id,
                         pending_card_id=pending_card_id,
                         pending_personal_number=pending_personal_number)

@bp.route('/register_with_menu', methods=['POST'])
def register_with_menu():
    """Route für Anmeldung mit Menüauswahl"""
    user_id = request.form.get('user_id')
    menu_choice = request.form.get('menu_choice', 1, type=int)
    
    user = User.query.get(user_id)
    if user:
        # Erstelle neue Registration mit Menüwahl
        existing_reg = Registration.query.filter_by(user_id=user.id, date=date.today()).first()
        if not existing_reg:
            reg = Registration(user_id=user.id, date=date.today(), menu_choice=menu_choice)
            db.session.add(reg)
            db.session.commit()
            
            today_menu = Menu.query.filter_by(date=date.today()).first()
            menu_name = today_menu.menu1_name if menu_choice == 1 else today_menu.menu2_name
            
            logger.info(f"Anmeldung mit Menü {menu_choice}: {user.name} ({user.personal_number})")
            notification_service.notify_new_registration(f"{user.name} - Menü {menu_choice}")
            
            return render_template('touch.html', 
                                 menu=today_menu,
                                 message=f"{user.name}, du bist angemeldet!\nMenü {menu_choice}: {menu_name}",
                                 status='success')
    
    return redirect(url_for('main.index'))

# Küche: Anzeige und Menü-Eingabe
from .models import Guest

@bp.route('/kitchen', methods=['GET', 'POST'])
def kitchen():
    from .models import PresetMenu
    
    today_menu = Menu.query.filter_by(date=date.today()).first()
    registrations = Registration.query.filter_by(date=date.today()).all()
    users = sorted([r.user for r in registrations], key=lambda u: u.name.lower())
    guest_entry = Guest.query.filter_by(date=date.today()).first()
    guest_count = guest_entry.count if guest_entry else 0
    preset_menus = PresetMenu.get_all_ordered()
    
    # Menüstatistiken berechnen
    menu1_count = sum(1 for r in registrations if r.menu_choice == 1)
    menu2_count = sum(1 for r in registrations if r.menu_choice == 2)
    
    if request.method == 'POST':
        # Menü speichern
        if 'menu' in request.form or 'menu1' in request.form:
            zwei_menues = request.form.get('zwei_menues_aktiv') == '1'
            
            if zwei_menues:
                menu1_text = request.form.get('menu1', '').strip()
                menu2_text = request.form.get('menu2', '').strip()
                
                if today_menu:
                    today_menu.zwei_menues_aktiv = True
                    today_menu.menu1_name = menu1_text
                    today_menu.menu2_name = menu2_text
                    today_menu.description = f"{menu1_text} / {menu2_text}"  # Für Kompatibilität
                else:
                    today_menu = Menu(
                        date=date.today(),
                        description=f"{menu1_text} / {menu2_text}",
                        zwei_menues_aktiv=True,
                        menu1_name=menu1_text,
                        menu2_name=menu2_text
                    )
                    db.session.add(today_menu)
            else:
                menu_text = request.form.get('menu', '').strip()
                
                if today_menu:
                    today_menu.zwei_menues_aktiv = False
                    today_menu.description = menu_text
                    today_menu.menu1_name = None
                    today_menu.menu2_name = None
                else:
                    today_menu = Menu(
                        date=date.today(),
                        description=menu_text,
                        zwei_menues_aktiv=False
                    )
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
    return render_template('kitchen.html', 
                         menu=today_menu, 
                         users=users, 
                         guest_count=guest_count, 
                         total=total,
                         menu1_count=menu1_count,
                         menu2_count=menu2_count,
                         preset_menus=preset_menus)

@bp.route('/kitchen/data', methods=['GET'])
def kitchen_data():
    """API-Endpunkt für AJAX-Updates der Küchenseite"""
    registrations = Registration.query.filter_by(date=date.today()).all()
    users = sorted([r.user for r in registrations], key=lambda u: u.name.lower())
    guest_entry = Guest.query.filter_by(date=date.today()).first()
    guest_count = guest_entry.count if guest_entry else 0
    
    # Menüstatistiken
    menu1_count = sum(1 for r in registrations if r.menu_choice == 1)
    menu2_count = sum(1 for r in registrations if r.menu_choice == 2)
    
    return jsonify({
        'users': [{'id': u.id, 'name': u.name} for u in users],
        'guest_count': guest_count,
        'total': len(users) + guest_count,
        'menu1_count': menu1_count,
        'menu2_count': menu2_count
    })

@bp.route('/menu/data', methods=['GET'])
def menu_data():
    """API-Endpunkt für AJAX-Updates des Menüs auf der Touch-Seite"""
    today_menu = Menu.query.filter_by(date=date.today()).first()
    if today_menu:
        return jsonify({
            'menu': today_menu.description if not today_menu.zwei_menues_aktiv else None,
            'zwei_menues_aktiv': today_menu.zwei_menues_aktiv,
            'menu1': today_menu.menu1_name if today_menu.zwei_menues_aktiv else None,
            'menu2': today_menu.menu2_name if today_menu.zwei_menues_aktiv else None
        })
    return jsonify({'menu': None, 'zwei_menues_aktiv': False})

@bp.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    from .models import PresetMenu
    
    today_menu = Menu.query.filter_by(date=date.today()).first()
    guest_entry = Guest.query.filter_by(date=date.today()).first()
    guest_count = guest_entry.count if guest_entry else 0
    preset_menus = PresetMenu.get_all_ordered()
    message = None
    
    if request.method == 'POST':
        # Menü speichern (neue Logik für ein oder zwei Menüs)
        if 'save_menu' in request.form:
            zwei_menues = request.form.get('zwei_menues_aktiv') == '1'
            
            if zwei_menues:
                menu1_text = request.form.get('menu1_text', '').strip()
                menu2_text = request.form.get('menu2_text', '').strip()
                
                if today_menu:
                    today_menu.zwei_menues_aktiv = True
                    today_menu.menu1_name = menu1_text
                    today_menu.menu2_name = menu2_text
                    today_menu.description = f"{menu1_text} / {menu2_text}"
                else:
                    today_menu = Menu(
                        date=date.today(),
                        description=f"{menu1_text} / {menu2_text}",
                        zwei_menues_aktiv=True,
                        menu1_name=menu1_text,
                        menu2_name=menu2_text
                    )
                    db.session.add(today_menu)
            else:
                menu_text = request.form.get('menu_text', '').strip()
                
                if today_menu:
                    today_menu.zwei_menues_aktiv = False
                    today_menu.description = menu_text
                    today_menu.menu1_name = None
                    today_menu.menu2_name = None
                else:
                    today_menu = Menu(
                        date=date.today(),
                        description=menu_text,
                        zwei_menues_aktiv=False
                    )
                    db.session.add(today_menu)
            
            db.session.commit()
            message = "Menü gespeichert."
            
        # Vordefiniertes Menü hinzufügen
        elif 'add_preset_menu' in request.form:
            new_menu = request.form.get('new_preset_menu', '').strip()
            if new_menu:
                if not PresetMenu.query.filter_by(name=new_menu).first():
                    max_order = db.session.query(db.func.max(PresetMenu.sort_order)).scalar() or 0
                    preset = PresetMenu(name=new_menu, sort_order=max_order + 1)
                    db.session.add(preset)
                    db.session.commit()
                    message = f"Menü '{new_menu}' hinzugefügt."
                    preset_menus = PresetMenu.get_all_ordered()
                else:
                    message = "Dieses Menü existiert bereits."
                    
        # Vordefiniertes Menü löschen
        elif 'delete_preset_menu' in request.form:
            preset_id = request.form.get('delete_preset_id')
            preset = PresetMenu.query.get(preset_id)
            if preset:
                menu_name = preset.name
                db.session.delete(preset)
                db.session.commit()
                message = f"Menü '{menu_name}' gelöscht."
                preset_menus = PresetMenu.get_all_ordered()
                
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
    
    return render_template('admin.html', 
                         users=users, 
                         registered_ids=registered_ids, 
                         message=message, 
                         menu=today_menu, 
                         guest_count=guest_count,
                         preset_menus=preset_menus)

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
    """Generiere QR-Code für User - Mobile Registrierung"""
    user = User.query.get_or_404(user_id)
    
    # Sicherstellen, dass User einen Token hat
    if not user.mobile_token:
        user.mobile_token = User.generate_token()
        db.session.commit()
    
    # QR-Code mit Mobile-URL generieren
    # Verwendet BASE_URL aus .env falls gesetzt, sonst automatische Erkennung
    import os
    base_url = os.getenv('BASE_URL', request.host_url.rstrip('/'))
    mobile_url = f"{base_url}/m/{user.mobile_token}"
    qr_image = generate_qr_code(mobile_url)
    
    from flask import render_template_string
    template = """
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QR-Code für {{ user.name }}</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
                text-align: center; 
                padding: 40px; 
                background: linear-gradient(135deg, #1a0000 0%, #450a0a 50%, #1a0000 100%);
                color: #fff;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            }
            .qr-card { 
                display: inline-block; 
                background: rgba(20,20,20,0.95);
                border: 3px solid #dc2626; 
                padding: 30px; 
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(220,38,38,0.5);
            }
            h1 { 
                color: #ef4444; 
                margin-top: 0;
                font-size: 2em;
                text-shadow: 0 0 20px rgba(220,38,38,0.6);
            }
            img { margin: 20px 0; background: white; padding: 15px; border-radius: 8px; }
            .info { color: #9ca3af; margin: 15px 0; }
            .info b { color: #fca5a5; }
            .url { 
                background: rgba(69,10,10,0.4); 
                padding: 10px 15px; 
                border-radius: 8px; 
                font-family: monospace; 
                font-size: 0.9em;
                color: #d1d5db;
                word-break: break-all;
                margin: 15px 0;
            }
            .buttons { margin-top: 30px; display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; }
            button, .btn { 
                padding: 12px 24px; 
                font-size: 1.1em; 
                cursor: pointer; 
                border: none;
                border-radius: 8px;
                font-weight: 600;
                transition: all 0.3s;
                text-decoration: none;
                display: inline-block;
            }
            .btn-print {
                background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
                color: white;
                border: 2px solid #ef4444;
            }
            .btn-back {
                background: linear-gradient(135deg, #374151 0%, #4b5563 100%);
                color: white;
                border: 2px solid #6b7280;
            }
            button:hover, .btn:hover { transform: translateY(-2px); }
            @media print {
                body { background: white; color: black; }
                .qr-card { border-color: black; box-shadow: none; background: white; }
                h1 { color: black; text-shadow: none; }
                .info, .info b, .url { color: black; background: white; }
                .no-print { display: none; }
            }
        </style>
    </head>
    <body>
        <div class="qr-card">
            <h1>📱 Mobile Anmeldung</h1>
            <img src="{{ qr_image }}" alt="QR Code" style="max-width: 300px;">
            <div class="info"><b>Name:</b> {{ user.name }}</div>
            <div class="info"><b>Personalnummer:</b> {{ user.personal_number }}</div>
            <div class="url">{{ mobile_url }}</div>
            <div class="info" style="font-size: 0.9em; color: #6b7280; margin-top: 20px;">
                QR-Code mit Smartphone scannen für schnelle Essensanmeldung
            </div>
        </div>
        <div class="no-print buttons">
            <button onclick="window.print()" class="btn-print">🖨️ Drucken</button>
            <a href="/admin" class="btn btn-back">← Zurück zum Admin</a>
        </div>
    </body>
    </html>
    """
    return render_template_string(template, user=user, qr_image=qr_image, mobile_url=mobile_url)


@bp.route('/admin/example-csv')
@login_required
def example_csv():
    """Generiert eine Beispiel-CSV-Datei zum Download"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['name', 'personal_number', 'card_id'])
    
    # Beispieldaten
    writer.writerow(['Max Mustermann', '12345', ''])
    writer.writerow(['Anna Schmidt', '67890', '0123456789ABCDEF'])
    writer.writerow(['Peter Müller', '11111', ''])
    
    # UTF-8 BOM für Excel-Kompatibilität
    csv_content = '\ufeff' + output.getvalue()
    
    response = make_response(csv_content)
    response.headers['Content-Disposition'] = 'attachment; filename=beispiel_user.csv'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    
    return response

# Mobile Registrierung via Token
@bp.route('/m/<token>', methods=['GET', 'POST'])
def mobile_registration(token):
    user = User.query.filter_by(mobile_token=token).first()
    if not user:
        return render_template_string("""
        <!DOCTYPE html>
        <html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ungültiger Link</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px; background: #1a0000; color: #fff;">
        <h1 style="color: #ef4444;">❌ Ungültiger Link</h1>
        <p style="font-size: 1.2em; color: #9ca3af;">Dieser QR-Code ist nicht mehr gültig.</p>
        </body></html>
        """), 404
    
    today_menu = Menu.query.filter_by(date=date.today()).first()
    registration = Registration.query.filter_by(user_id=user.id, date=date.today()).first()
    is_registered = registration is not None
    
    message = None
    status_type = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'register':
            if not today_menu:
                message = "Heute ist kein Menü verfügbar"
                status_type = "info"
            elif is_registered:
                message = "Du bist bereits angemeldet"
                status_type = "info"
            else:
                menu_choice = None
                if today_menu.zwei_menues_aktiv:
                    menu_choice = int(request.form.get('menu_choice', 1))
                
                new_registration = Registration(
                    user_id=user.id,
                    date=date.today(),
                    menu_choice=menu_choice
                )
                db.session.add(new_registration)
                db.session.commit()
                message = "✓ Erfolgreich angemeldet!"
                status_type = "success"
                is_registered = True
                registration = new_registration
                
        elif action == 'unregister':
            if registration:
                db.session.delete(registration)
                db.session.commit()
                message = "✓ Erfolgreich abgemeldet"
                status_type = "info"
                is_registered = False
                registration = None
            else:
                message = "Du warst nicht angemeldet"
                status_type = "info"
    
    return render_template('mobile.html',
                         user=user,
                         menu=today_menu,
                         is_registered=is_registered,
                         registration=registration,
                         message=message,
                         status=status_type)

start_rfid_thread()
