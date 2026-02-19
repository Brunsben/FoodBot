from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from .models import db, User, Menu, Registration, Guest, PresetMenu
from .utils import register_user_for_today, save_menu
from .rfid import find_user_by_card
from .auth import login_required, check_auth
from .api import limiter
from .qr_generator import generate_qr_code
from .notifications import notification_service
from sqlalchemy.orm import joinedload
from flask_limiter.util import get_remote_address
from datetime import date
from urllib.parse import urlparse
import csv
from io import TextIOWrapper, StringIO
import threading
import time
import logging
import os

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

# Login-Route
@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Max 5 Login-Versuche pro Minute
def login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password')
        if check_auth(password):
            session['admin_logged_in'] = True
            session.permanent = True  # Session bleibt 1 Stunde aktiv
            next_page = request.args.get('next')
            # Open Redirect verhindern: Nur relative URLs erlauben
            if next_page and urlparse(next_page).netloc == '':
                return redirect(next_page)
            return redirect(url_for('main.admin'))
        else:
            error = '❌ Authentifizierung fehlgeschlagen'
            logger.warning(f"Fehlgeschlagener Login-Versuch von {get_remote_address()}")
    return render_template('login.html', error=error)

@bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('main.index'))

# Thread-sicherer Speicher für den letzten RFID-Scan
_rfid_lock = threading.Lock()
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
        
        logger.info(f"POST erhalten - card_id: {card_id}, personal_number: {personal_number}")
        
        # QR-Code-Format: FOODBOT:Personalnummer
        if personal_number and personal_number.startswith('FOODBOT:'):
            personal_number = personal_number.replace('FOODBOT:', '').strip()
        if card_id and card_id.startswith('FOODBOT:'):
            card_id = card_id.replace('FOODBOT:', '').strip()
            personal_number = card_id
            card_id = None
        
        # Input-Validierung
        if personal_number:
            personal_number = personal_number[:20]  # Max 20 Zeichen
        if card_id:
            card_id = card_id[:50]  # Max 50 Zeichen
        
        if personal_number:
            user = User.query.filter_by(personal_number=personal_number).first()
        elif card_id:
            user = find_user_by_card(card_id)
            
        if user:
            # Deadline-Prüfung
            if today_menu and not today_menu.is_registration_open():
                # Abmeldung auch nach Deadline erlauben
                existing_reg = Registration.query.filter_by(user_id=user.id, date=date.today()).first()
                if not existing_reg:
                    message = f"Anmeldefrist abgelaufen ({today_menu.registration_deadline} Uhr)"
                    status = 'error'
                    return render_template('touch.html', menu=today_menu, message=message, status=status)
            
            # Prüfe ob zwei Menüs aktiv sind
            if today_menu and today_menu.zwei_menues_aktiv:
                # Prüfe ob User schon angemeldet ist
                existing_reg = Registration.query.filter_by(user_id=user.id, date=date.today()).first()
                if existing_reg:
                    # Abmelden
                    menu_name = today_menu.menu1_name if existing_reg.menu_choice == 1 else today_menu.menu2_name
                    try:
                        db.session.delete(existing_reg)
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                        message = "Datenbankfehler bei Abmeldung"
                        status = 'error'
                        return render_template('touch.html', menu=today_menu, message=message, status=status)
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
            message = "Benutzer nicht gefunden"
            status = 'error'
            logger.warning(f"Fehlversuch Anmeldung von {get_remote_address()}")
    
    # Bei AJAX/Fetch-Requests JSON zurückgeben (nur POST!)
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': status,
            'message': message,
            'need_menu_choice': need_menu_choice,
            'user_id': pending_user_id if need_menu_choice else None
        })
    
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
    
    # Input-Validierung
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        return redirect(url_for('main.index'))
    if menu_choice not in (1, 2):
        menu_choice = 1
    
    user = db.session.get(User, user_id_int)
    if user:
        # Erstelle neue Registration mit Menüwahl
        existing_reg = Registration.query.filter_by(user_id=user.id, date=date.today()).first()
        if not existing_reg:
            reg = Registration(user_id=user.id, date=date.today(), menu_choice=menu_choice)
            try:
                db.session.add(reg)
                db.session.commit()
            except Exception:
                db.session.rollback()
                return redirect(url_for('main.index'))
            
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
@bp.route('/kitchen', methods=['GET', 'POST'])
def kitchen():
    today_menu = Menu.query.filter_by(date=date.today()).first()
    registrations = Registration.query.options(
        joinedload(Registration.user)
    ).filter_by(date=date.today()).all()
    # Sortiere nach Username
    registrations = sorted(registrations, key=lambda r: r.user.name.lower())
    
    # Gäste nach Menü
    guests = Guest.query.filter_by(date=date.today()).all()
    guest_menu1 = next((g for g in guests if g.menu_choice == 1), None)
    guest_menu2 = next((g for g in guests if g.menu_choice == 2), None)
    guest_count = sum(g.count for g in guests)
    
    preset_menus = PresetMenu.get_all_ordered()

    # Menüstatistiken berechnen
    menu1_count = sum(1 for r in registrations if r.menu_choice == 1) + (guest_menu1.count if guest_menu1 else 0)
    menu2_count = sum(1 for r in registrations if r.menu_choice == 2) + (guest_menu2.count if guest_menu2 else 0)

    if request.method == 'POST':
        # Menü speichern
        if 'menu' in request.form or 'menu1' in request.form:
            try:
                today_menu = save_menu(date.today(), request.form)
                flash('Menü aktualisiert!')
            except Exception:
                flash('Fehler beim Speichern des Menüs.')

        # Gäste hinzufügen/entfernen
        elif 'guest_action' in request.form:
            action = request.form.get('guest_action')
            menu_choice = int(request.form.get('menu_choice', 1))
            
            guest_entry = Guest.query.filter_by(date=date.today(), menu_choice=menu_choice).first()
            if not guest_entry:
                guest_entry = Guest(date=date.today(), menu_choice=menu_choice, count=0)
                db.session.add(guest_entry)
                
            if action == 'add' and guest_entry.count < 50:
                guest_entry.count += 1
            elif action == 'remove' and guest_entry.count > 0:
                guest_entry.count -= 1
            db.session.commit()
        return redirect(url_for('main.kitchen'))

    total = len(registrations) + guest_count
    return render_template('kitchen.html',
                         menu=today_menu,
                         registrations=registrations,
                         guest_count=guest_count,
                         guest_menu1=guest_menu1,
                         guest_menu2=guest_menu2,
                         total=total,
                         menu1_count=menu1_count,
                         menu2_count=menu2_count,
                         preset_menus=preset_menus)

@bp.route('/kitchen/data', methods=['GET'])
def kitchen_data():
    """API-Endpunkt für AJAX-Updates der Küchenseite"""
    today_menu = Menu.query.filter_by(date=date.today()).first()
    registrations = Registration.query.options(
        joinedload(Registration.user)
    ).filter_by(date=date.today()).all()
    users = sorted([r.user for r in registrations], key=lambda u: u.name.lower())
    
    # Gäste nach Menü
    guests = Guest.query.filter_by(date=date.today()).all()
    guest_menu1 = next((g for g in guests if g.menu_choice == 1), None)
    guest_menu2 = next((g for g in guests if g.menu_choice == 2), None)
    guest_count = sum(g.count for g in guests)
    
    # Menüstatistiken
    menu1_count = sum(1 for r in registrations if r.menu_choice == 1) + (guest_menu1.count if guest_menu1 else 0)
    menu2_count = sum(1 for r in registrations if r.menu_choice == 2) + (guest_menu2.count if guest_menu2 else 0)
    
    # Liefere für jeden User auch menu_choice und Menüname
    user_entries = []
    for r in registrations:
        entry = {
            'name': r.user.name,
            'menu_choice': r.menu_choice,
        }
        if today_menu:
            if today_menu.zwei_menues_aktiv:
                if r.menu_choice == 1:
                    entry['menu_name'] = today_menu.menu1_name or 'Menü 1'
                elif r.menu_choice == 2:
                    entry['menu_name'] = today_menu.menu2_name or 'Menü 2'
            else:
                entry['menu_name'] = today_menu.description or ''
        else:
            entry['menu_name'] = ''
        user_entries.append(entry)
    return jsonify({
        'users': user_entries,
        'guest_count': guest_count,
        'total': len(users) + guest_count,
        'menu1_count': menu1_count,
        'menu2_count': menu2_count,
        'menu': {
            'zwei_menues_aktiv': today_menu.zwei_menues_aktiv if today_menu else False,
            'menu1_name': today_menu.menu1_name if today_menu else None,
            'menu2_name': today_menu.menu2_name if today_menu else None,
            'description': today_menu.description if today_menu else None
        }
    })

@bp.route('/kitchen/print')
def kitchen_print():
    """Druckansicht für die Küche - gruppiert nach Menü"""
    today_menu = Menu.query.filter_by(date=date.today()).first()
    registrations = Registration.query.options(
        joinedload(Registration.user)
    ).filter_by(date=date.today()).all()
    guest_entry = Guest.query.filter_by(date=date.today()).first()
    guest_count = guest_entry.count if guest_entry else 0
    
    # Nach Menüwahl gruppieren und alphabetisch sortieren
    menu1_users = sorted([r.user for r in registrations if r.menu_choice == 1], key=lambda u: u.name.lower())
    menu2_users = sorted([r.user for r in registrations if r.menu_choice == 2], key=lambda u: u.name.lower())
    
    total = len(registrations) + guest_count
    
    return render_template('kitchen_print.html', 
                         menu=today_menu,
                         menu1_users=menu1_users,
                         menu2_users=menu2_users,
                         guest_count=guest_count,
                         total=total)

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
    today_menu = Menu.query.filter_by(date=date.today()).first()
    guests = Guest.query.filter_by(date=date.today()).all()
    guest_menu1 = next((g for g in guests if g.menu_choice == 1), None)
    guest_count = sum(g.count for g in guests)  # Gesamt für Kompatibilität
    preset_menus = PresetMenu.get_all_ordered()
    message = None

    
    if request.method == 'POST':
        # Menü speichern (neue Logik für ein oder zwei Menüs)
        if 'save_menu' in request.form:
            try:
                today_menu = save_menu(date.today(), request.form)
                message = "Menü gespeichert."
            except Exception:
                message = "Fehler beim Speichern des Menüs."
            
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
            preset = db.session.get(PresetMenu, int(preset_id))
            if preset:
                menu_name = preset.name
                db.session.delete(preset)
                db.session.commit()
                message = f"Menü '{menu_name}' gelöscht."
                preset_menus = PresetMenu.get_all_ordered()
                
        # Tagesan-/abmeldung
        elif 'user_id' in request.form and 'edit_user' not in request.form:
            user_id = request.form.get('user_id')
            user = db.session.get(User, int(user_id))
            if user:
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
            user = db.session.get(User, int(user_id))
            if user:
                edit_name = request.form.get('edit_name', '')
                edit_pn = request.form.get('edit_personal_number', '')
                if not edit_name or not edit_pn:
                    message = "Name und Personalnummer dürfen nicht leer sein."
                else:
                    edit_name = edit_name.strip()
                    edit_pn = edit_pn.strip()
                    # Duplikat-Prüfung (andere User mit gleicher Personalnummer)
                    duplicate = User.query.filter(User.personal_number == edit_pn, User.id != user.id).first()
                    if duplicate:
                        message = f"Personalnummer {edit_pn} ist bereits vergeben."
                    else:
                        user.name = edit_name
                        user.personal_number = edit_pn
                        user.card_id = (request.form.get('edit_card_id') or '').strip() or None
                        try:
                            db.session.commit()
                            message = f"User {user.name} aktualisiert."
                        except Exception:
                            db.session.rollback()
                            message = "Fehler beim Speichern."
        # User löschen
        elif 'delete_user' in request.form:
            user_id = request.form.get('delete_user')
            user = db.session.get(User, int(user_id))
            if user:
                db.session.delete(user)
                db.session.commit()
                message = f"User {user.name} gelöscht."
        # CSV-Import
        elif 'csv_file' in request.files:
            file = request.files['csv_file']
            if file and file.filename and file.filename.endswith('.csv'):
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
                    db.session.rollback()
                    message = "Fehler beim CSV-Import. Bitte Format prüfen."
                    logger.error(f"CSV-Import-Fehler: {e}")
        # Gäste verwalten (nur Menü 1 in Admin, da einfaches Interface)
        elif 'guest_action' in request.form:
            action = request.form.get('guest_action')
            guest_entry = Guest.query.filter_by(date=date.today(), menu_choice=1).first()
            if not guest_entry:
                guest_entry = Guest(date=date.today(), menu_choice=1, count=0)
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

@bp.route('/admin/weekly', methods=['GET', 'POST'])
@login_required
def admin_weekly():
    message = None
    
    if request.method == 'POST':
        # Neuen Tag anlegen
        if 'add_day' in request.form:
            new_date_str = request.form.get('new_date')
            if new_date_str:
                try:
                    new_date = date.fromisoformat(new_date_str)
                except ValueError:
                    new_date = None
                    message = "Ungültiges Datumsformat."
                if new_date:
                    existing_menu = Menu.query.filter_by(date=new_date).first()
                    if not existing_menu:
                        menu = Menu(
                            date=new_date,
                            description='',
                            zwei_menues_aktiv=False,
                            deadline_enabled=True,
                            registration_deadline='19:45'
                        )
                        db.session.add(menu)
                        db.session.commit()
                        message = f"Tag {new_date.strftime('%d.%m.%Y')} hinzugefügt."
                    else:
                        message = f"Menü für {new_date.strftime('%d.%m.%Y')} existiert bereits."
        
        # Tag löschen
        elif 'delete_day' in request.form:
            date_str = request.form.get('date')
            if date_str:
                try:
                    menu_date = date.fromisoformat(date_str)
                except ValueError:
                    menu_date = None
                    message = "Ungültiges Datumsformat."
                if menu_date:
                    menu = Menu.query.filter_by(date=menu_date).first()
                    if menu:
                        Registration.query.filter_by(date=menu_date).delete()
                        db.session.delete(menu)
                        db.session.commit()
                        message = f"Tag {menu_date.strftime('%d.%m.%Y')} gelöscht."
        
        # Tag speichern/bearbeiten
        elif 'save_day' in request.form:
            date_str = request.form.get('date')
            if date_str:
                try:
                    menu_date = date.fromisoformat(date_str)
                except ValueError:
                    message = "Ungültiges Datumsformat."
                    menu_date = None
                if menu_date:
                    try:
                        save_menu(menu_date, request.form)
                        message = f"Menü für {menu_date.strftime('%d.%m.%Y')} gespeichert."
                    except Exception:
                        message = "Fehler beim Speichern des Menüs."
    
    # Alle zukünftigen und heutigen Menüs laden (sortiert nach Datum)
    today = date.today()
    menus = Menu.query.filter(Menu.date >= today).order_by(Menu.date).all()
    
    weekdays_de = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    
    days = []
    for menu in menus:
        days.append({
            'date_iso': menu.date.isoformat(),
            'date_str': menu.date.strftime('%d.%m.%Y'),
            'weekday': weekdays_de[menu.date.weekday()],
            'is_today': menu.date == today,
            'menu': menu
        })
    
    preset_menus = PresetMenu.get_all_ordered()
    
    return render_template('weekly.html', days=days, preset_menus=preset_menus, message=message, today=today.isoformat())

# API-Route für das Touch-Display, um den letzten Scan abzufragen
@bp.route('/rfid_scan')
@limiter.limit("60 per minute")
def rfid_scan():
    with _rfid_lock:
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
                with _rfid_lock:
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
@login_required
def qr_code(user_id):
    """Generiere QR-Code für User - Mobile Registrierung"""
    user = db.session.get(User, user_id)
    if not user:
        return {'error': 'User nicht gefunden'}, 404
    
    # Sicherstellen, dass User einen Token hat
    if not user.mobile_token:
        user.mobile_token = User.generate_token()
        db.session.commit()
    
    # QR-Code mit Mobile-URL generieren
    base_url = os.getenv('BASE_URL', request.host_url.rstrip('/'))
    mobile_url = f"{base_url}/m/{user.mobile_token}"
    qr_image = generate_qr_code(mobile_url)
    
    return render_template('qr.html', user=user, qr_image=qr_image, mobile_url=mobile_url)


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
        return render_template('invalid_token.html'), 404
    
    today_menu = Menu.query.filter_by(date=date.today()).first()
    registration = Registration.query.filter_by(user_id=user.id, date=date.today()).first()
    is_registered = registration is not None
    registration_closed = today_menu and not today_menu.is_registration_open() if today_menu else False
    
    message = None
    status_type = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'register':
            if not today_menu:
                message = "Heute ist kein Menü verfügbar"
                status_type = "info"
            elif today_menu and not today_menu.is_registration_open():
                message = f"Anmeldefrist abgelaufen ({today_menu.registration_deadline} Uhr)"
                status_type = "error"
            elif is_registered:
                message = "Du bist bereits angemeldet"
                status_type = "info"
            else:
                menu_choice = 1
                if today_menu.zwei_menues_aktiv:
                    try:
                        menu_choice = int(request.form.get('menu_choice', 1))
                    except (TypeError, ValueError):
                        menu_choice = 1
                    if menu_choice not in (1, 2):
                        menu_choice = 1
                
                new_registration = Registration(
                    user_id=user.id,
                    date=date.today(),
                    menu_choice=menu_choice
                )
                try:
                    db.session.add(new_registration)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    message = "Datenbankfehler"
                    status_type = "error"
                else:
                    message = "✓ Erfolgreich angemeldet!"
                    status_type = "success"
                    is_registered = True
                    registration = new_registration
                
        elif action == 'unregister':
            if registration:
                try:
                    db.session.delete(registration)
                    db.session.commit()
                    message = "✓ Erfolgreich abgemeldet"
                    status_type = "info"
                    is_registered = False
                    registration = None
                except Exception:
                    db.session.rollback()
                    message = "Datenbankfehler"
                    status_type = "error"
            else:
                message = "Du warst nicht angemeldet"
                status_type = "info"
    
    return render_template('mobile.html',
                         user=user,
                         menu=today_menu,
                         is_registered=is_registered,
                         registration=registration,
                         registration_closed=registration_closed,
                         message=message,
                         status=status_type)
