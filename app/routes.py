from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from .models import (
    db, Menu, Registration, Guest, PresetMenu, AdminLog,
    RfidCard, MobileToken,
    get_member_name, get_member_by_personal_number, get_member,
    get_all_members, get_member_cards, get_member_token
)
from .utils import register_member_for_today, save_menu, get_guests_for_date, get_menu_for_date, db_transaction
from .validation import (
    validate_personal_number, validate_card_id, validate_name,
    validate_integer, validate_menu_choice, validate_date, validate_time
)
from .rfid import find_user_by_card
from .auth import login_required, check_auth
from .api import limiter
from .qr_generator import generate_qr_code
from .notifications import notification_service
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
@limiter.limit("60 per minute")  # Max 60 Scans pro Minute (1 pro Sekunde)
def index():
    today_menu = get_menu_for_date()
    message = None
    status = None
    need_menu_choice = False
    pending_member_id = None
    pending_card_id = None
    pending_personal_number = None
    
    if request.method == 'POST':
        personal_number = request.form.get('personal_number', '').strip()
        card_id = request.form.get('card_id', '').strip()
        member_id = None
        
        # QR-Code-Format: FOODBOT:Personalnummer
        if personal_number and personal_number.startswith('FOODBOT:'):
            personal_number = personal_number.replace('FOODBOT:', '').strip()
        if card_id and card_id.startswith('FOODBOT:'):
            card_id = card_id.replace('FOODBOT:', '').strip()
            personal_number = card_id
            card_id = None
        
        # Input-Validierung mit Sicherheits-Funktionen
        if personal_number:
            personal_number = validate_personal_number(personal_number)
        if card_id:
            card_id = validate_card_id(card_id)
        
        if personal_number:
            member_id = get_member_by_personal_number(personal_number)
        elif card_id:
            member_id = find_user_by_card(card_id)
            
        if member_id:
            member_name = get_member_name(member_id)
            
            # Deadline-Prüfung
            if today_menu and not today_menu.is_registration_open():
                # Abmeldung auch nach Deadline erlauben
                existing_reg = Registration.query.filter_by(member_id=member_id, datum=date.today()).first()
                if not existing_reg:
                    message = f"Anmeldefrist abgelaufen ({today_menu.registration_deadline} Uhr)"
                    status = 'error'
                    return render_template('touch.html', menu=today_menu, message=message, status=status)
            
            # Prüfe ob zwei Menüs aktiv sind
            if today_menu and today_menu.zwei_menues_aktiv:
                # Prüfe ob Mitglied schon angemeldet ist
                existing_reg = Registration.query.filter_by(member_id=member_id, datum=date.today()).first()
                if existing_reg:
                    # Abmelden
                    menu_name = today_menu.menu1_name if existing_reg.menu_wahl == 1 else today_menu.menu2_name
                    try:
                        with db_transaction():
                            db.session.delete(existing_reg)
                    except Exception as e:
                        logger.error(f"Abmeldung fehlgeschlagen für {member_name}: {e}")
                        message = "Datenbankfehler bei Abmeldung"
                        status = 'error'
                        return render_template('touch.html', menu=today_menu, message=message, status=status)
                    message = f"{member_name}, du wurdest abgemeldet.\n{menu_name}"
                    status = 'cancel'
                    logger.info(f"Abmeldung: {member_name}")
                else:
                    # Zeige Menüauswahl
                    need_menu_choice = True
                    pending_member_id = str(member_id)
                    pending_card_id = card_id
                    pending_personal_number = personal_number
                    message = "Bitte wähle dein Menü"
                    status = 'info'
            else:
                # Normaler Modus ohne Menüauswahl
                registered = register_member_for_today(member_id)
                if registered:
                    menu_text = today_menu.beschreibung if today_menu else "Kein Menü"
                    message = f"{member_name}, du bist angemeldet!\n{menu_text}"
                    status = 'success'
                    logger.info(f"Anmeldung: {member_name}")
                    notification_service.notify_new_registration(member_name)
                else:
                    menu_text = today_menu.beschreibung if today_menu else ""
                    message = f"{member_name}, du wurdest abgemeldet.\n{menu_text}"
                    status = 'cancel'
                    logger.info(f"Abmeldung: {member_name}")
        else:
            message = "Benutzer nicht gefunden"
            status = 'error'
            logger.warning(f"Fehlversuch Anmeldung von {get_remote_address()}")
    
    # Bei AJAX/Fetch-Requests JSON zurückgeben (nur POST!)
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        response_data = {
            'status': status,
            'message': message,
            'need_menu_choice': need_menu_choice,
            'member_id': pending_member_id if need_menu_choice else None
        }
        # Menünamen hinzufügen wenn Auswahl benötigt wird
        if need_menu_choice and today_menu:
            response_data['menu1'] = today_menu.menu1_name or 'Menü 1'
            response_data['menu2'] = today_menu.menu2_name or 'Menü 2'
        return jsonify(response_data)
    
    return render_template('touch.html', 
                         menu=today_menu, 
                         message=message, 
                         status=status,
                         need_menu_choice=need_menu_choice,
                         pending_member_id=pending_member_id,
                         pending_card_id=pending_card_id,
                         pending_personal_number=pending_personal_number)

@bp.route('/register_with_menu', methods=['POST'])
@limiter.limit("60 per minute")  # Max 60 Menü-Auswahlen pro Minute
def register_with_menu():
    """Route für Anmeldung mit Menüauswahl"""
    member_id = request.form.get('member_id', '').strip()
    menu_choice = validate_menu_choice(request.form.get('menu_choice', 1), zwei_menues_aktiv=False)
    
    if not member_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'Ungültige Mitglied-ID'})
        return redirect(url_for('main.index'))
    if menu_choice not in (1, 2):
        menu_choice = 1
    
    member = get_member(member_id)
    if member:
        today_menu = get_menu_for_date()
        member_name = member['name']
        
        # Erstelle neue Registration mit Menüwahl
        existing_reg = Registration.query.filter_by(member_id=member_id, datum=date.today()).first()
        if not existing_reg:
            reg = Registration(member_id=member_id, datum=date.today(), menu_wahl=menu_choice)
            try:
                with db_transaction():
                    db.session.add(reg)
            except Exception as e:
                logger.error(f"Registrierung mit Menü fehlgeschlagen für member_id {member_id}: {e}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'status': 'error', 'message': 'Datenbankfehler'})
                return redirect(url_for('main.index'))
            
            menu_name = today_menu.menu1_name if menu_choice == 1 else today_menu.menu2_name
            message = f"{member_name}, du bist angemeldet!\n{menu_name}"
            
            logger.info(f"Anmeldung mit Menü {menu_choice}: {member_name}")
            notification_service.notify_new_registration(f"{member_name} - Menü {menu_choice}")
            
            # Bei AJAX JSON zurückgeben
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'success',
                    'message': message,
                    'name': member_name
                })
            
            return render_template('touch.html', 
                                 menu=today_menu,
                                 message=f"{member_name}, du bist angemeldet!\nMenü {menu_choice}: {menu_name}",
                                 status='success')
    
    return redirect(url_for('main.index'))

# Küche: Anzeige und Menü-Eingabe
@bp.route('/kitchen', methods=['GET', 'POST'])
def kitchen():
    today_menu = get_menu_for_date()
    registrations = Registration.query.filter_by(datum=date.today()).all()
    # Namen laden und nach Name sortieren
    reg_entries = []
    for r in registrations:
        reg_entries.append({'reg': r, 'name': get_member_name(r.member_id)})
    reg_entries.sort(key=lambda e: e['name'].lower())
    
    # Gäste laden
    guest_data = get_guests_for_date()
    guest_menu1 = guest_data['menu1']
    guest_menu2 = guest_data['menu2']
    guest_count = guest_data['total_count']
    
    preset_menus = PresetMenu.get_all_ordered()

    # Menüstatistiken berechnen
    menu1_count = sum(1 for r in registrations if r.menu_wahl == 1) + (guest_menu1.anzahl if guest_menu1 else 0)
    menu2_count = sum(1 for r in registrations if r.menu_wahl == 2) + (guest_menu2.anzahl if guest_menu2 else 0)

    if request.method == 'POST':
        # Menü speichern
        if 'menu' in request.form or 'menu1' in request.form:
            try:
                today_menu = save_menu(date.today(), request.form)
                flash('Menü aktualisiert!')
            except Exception as e:
                logger.error(f"Menü-Speichern fehlgeschlagen: {e}")
                flash('Fehler beim Speichern des Menüs.')

        # Gäste hinzufügen/entfernen
        elif 'guest_action' in request.form:
            action = request.form.get('guest_action')
            menu_choice = validate_menu_choice(request.form.get('menu_choice', 1), zwei_menues_aktiv=today_menu.zwei_menues_aktiv if today_menu else False)
            
            guest_entry = Guest.query.filter_by(datum=date.today(), menu_wahl=menu_choice).first()
            if not guest_entry:
                guest_entry = Guest(datum=date.today(), menu_wahl=menu_choice, anzahl=0)
                db.session.add(guest_entry)
                
            if action == 'add' and guest_entry.anzahl < 50:
                guest_entry.anzahl += 1
            elif action == 'remove' and guest_entry.anzahl > 0:
                guest_entry.anzahl -= 1
            
            with db_transaction():
                pass  # Changes werden automatisch committed
        return redirect(url_for('main.kitchen'))

    total = len(registrations) + guest_count
    return render_template('kitchen.html',
                         menu=today_menu,
                         reg_entries=reg_entries,
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
    today_menu = get_menu_for_date()
    registrations = Registration.query.filter_by(datum=date.today()).all()
    
    # Gäste laden
    guest_data = get_guests_for_date()
    guest_menu1 = guest_data['menu1']
    guest_menu2 = guest_data['menu2']
    guest_count = guest_data['total_count']
    
    # Menüstatistiken
    menu1_count = sum(1 for r in registrations if r.menu_wahl == 1) + (guest_menu1.anzahl if guest_menu1 else 0)
    menu2_count = sum(1 for r in registrations if r.menu_wahl == 2) + (guest_menu2.anzahl if guest_menu2 else 0)
    
    # Liefere für jede Registration Name und Menüwahl
    user_entries = []
    for r in registrations:
        name = get_member_name(r.member_id)
        entry = {
            'name': name,
            'menu_choice': r.menu_wahl,
        }
        if today_menu:
            if today_menu.zwei_menues_aktiv:
                if r.menu_wahl == 1:
                    entry['menu_name'] = today_menu.menu1_name or 'Menü 1'
                elif r.menu_wahl == 2:
                    entry['menu_name'] = today_menu.menu2_name or 'Menü 2'
            else:
                entry['menu_name'] = today_menu.beschreibung or ''
        else:
            entry['menu_name'] = ''
        user_entries.append(entry)
    user_entries.sort(key=lambda e: e['name'].lower())
    return jsonify({
        'users': user_entries,
        'guest_count': guest_count,
        'total': len(registrations) + guest_count,
        'menu1_count': menu1_count,
        'menu2_count': menu2_count,
        'menu': {
            'zwei_menues_aktiv': today_menu.zwei_menues_aktiv if today_menu else False,
            'menu1_name': today_menu.menu1_name if today_menu else None,
            'menu2_name': today_menu.menu2_name if today_menu else None,
            'description': today_menu.beschreibung if today_menu else None
        }
    })

@bp.route('/kitchen/print')
def kitchen_print():
    """Druckansicht für die Küche - gruppiert nach Menü"""
    today_menu = Menu.query.filter_by(datum=date.today()).first()
    registrations = Registration.query.filter_by(datum=date.today()).all()
    guest_data = get_guests_for_date()
    guest_count = guest_data['total_count']
    
    # Nach Menüwahl gruppieren und alphabetisch sortieren
    menu1_names = sorted([get_member_name(r.member_id) for r in registrations if r.menu_wahl == 1], key=str.lower)
    menu2_names = sorted([get_member_name(r.member_id) for r in registrations if r.menu_wahl == 2], key=str.lower)
    
    total = len(registrations) + guest_count
    
    return render_template('kitchen_print.html', 
                         menu=today_menu,
                         menu1_names=menu1_names,
                         menu2_names=menu2_names,
                         guest_count=guest_count,
                         total=total)

@bp.route('/menu/data', methods=['GET'])
def menu_data():
    """API-Endpunkt für AJAX-Updates des Menüs auf der Touch-Seite"""
    today_menu = Menu.query.filter_by(datum=date.today()).first()
    if today_menu:
        return jsonify({
            'menu': today_menu.beschreibung if not today_menu.zwei_menues_aktiv else None,
            'zwei_menues_aktiv': today_menu.zwei_menues_aktiv,
            'menu1': today_menu.menu1_name if today_menu.zwei_menues_aktiv else None,
            'menu2': today_menu.menu2_name if today_menu.zwei_menues_aktiv else None
        })
    return jsonify({'menu': None, 'zwei_menues_aktiv': False})

@bp.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    today_menu = get_menu_for_date()
    guest_data = get_guests_for_date()
    guest_menu1 = guest_data['menu1']
    guest_count = guest_data['total_count']
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
            preset = db.session.get(PresetMenu, preset_id)
            if preset:
                menu_name = preset.name
                db.session.delete(preset)
                db.session.commit()
                message = f"Menü '{menu_name}' gelöscht."
                preset_menus = PresetMenu.get_all_ordered()
                
        # Tagesan-/abmeldung
        elif 'member_id' in request.form and 'assign_card' not in request.form:
            member_id = request.form.get('member_id', '').strip()
            member = get_member(member_id)
            if member:
                registered = register_member_for_today(member_id)
                if registered:
                    message = f"{member['name']} wurde für heute angemeldet."
                else:
                    message = f"{member['name']} wurde für heute abgemeldet."
            else:
                message = "Unbekanntes Mitglied."

        # RFID-Karte zuweisen
        elif 'assign_card' in request.form:
            member_id = request.form.get('member_id', '').strip()
            card_id = validate_card_id(request.form.get('card_id', ''))
            if member_id and card_id:
                existing = RfidCard.query.filter_by(card_id=card_id).first()
                if existing:
                    message = "Diese Karten-ID ist bereits vergeben."
                else:
                    card = RfidCard(card_id=card_id, member_id=member_id)
                    db.session.add(card)
                    db.session.commit()
                    message = "RFID-Karte zugewiesen."
            else:
                message = "Mitglied-ID und Karten-ID erforderlich."

        # RFID-Karte entfernen
        elif 'remove_card' in request.form:
            card_id = request.form.get('remove_card', '').strip()
            card = RfidCard.query.filter_by(card_id=card_id).first()
            if card:
                db.session.delete(card)
                db.session.commit()
                message = "RFID-Karte entfernt."

        # Gäste verwalten (nur Menü 1 in Admin, da einfaches Interface)
        elif 'guest_action' in request.form:
            action = request.form.get('guest_action')
            guest_entry = Guest.query.filter_by(datum=date.today(), menu_wahl=1).first()
            if not guest_entry:
                guest_entry = Guest(datum=date.today(), menu_wahl=1, anzahl=0)
                db.session.add(guest_entry)
            if action == 'add' and guest_entry.anzahl < 50:
                guest_entry.anzahl += 1
            elif action == 'remove' and guest_entry.anzahl > 0:
                guest_entry.anzahl -= 1
            elif action == 'set':
                try:
                    count = int(request.form.get('guest_count', 0))
                    guest_entry.anzahl = max(0, min(50, count))
                except ValueError:
                    pass
            db.session.commit()
            message = f"Gästezahl aktualisiert: {guest_entry.anzahl}"
    
    # Daten NACH allen POST-Operationen neu laden
    members = get_all_members()
    # RFID-Karten pro Mitglied laden
    all_cards = RfidCard.query.all()
    cards_by_member = {}
    for c in all_cards:
        mid = str(c.member_id)
        if mid not in cards_by_member:
            cards_by_member[mid] = []
        cards_by_member[mid].append(c.card_id)

    registrations = Registration.query.filter_by(datum=date.today()).all()
    registered_ids = {str(r.member_id) for r in registrations}
    
    return render_template('admin.html', 
                         members=members,
                         cards_by_member=cards_by_member,
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
                    existing_menu = Menu.query.filter_by(datum=new_date).first()
                    if not existing_menu:
                        menu = Menu(
                            datum=new_date,
                            beschreibung='',
                            zwei_menues_aktiv=False,
                            frist_aktiv=True,
                            anmeldefrist='19:45'
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
                    menu = Menu.query.filter_by(datum=menu_date).first()
                    if menu:
                        Registration.query.filter_by(datum=menu_date).delete()
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
    menus = Menu.query.filter(Menu.datum >= today).order_by(Menu.datum).all()
    
    weekdays_de = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    
    days = []
    for menu in menus:
        days.append({
            'date_iso': menu.datum.isoformat(),
            'date_str': menu.datum.strftime('%d.%m.%Y'),
            'weekday': weekdays_de[menu.datum.weekday()],
            'is_today': menu.datum == today,
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

@bp.route('/qr/<member_id>')
@login_required
def qr_code(member_id):
    """Generiere QR-Code für Mitglied - Mobile Registrierung"""
    member = get_member(member_id)
    if not member:
        return {'error': 'Mitglied nicht gefunden'}, 404
    
    # Sicherstellen, dass Mitglied einen Token hat
    token_entry = get_member_token(member_id)
    if not token_entry:
        token_entry = MobileToken(member_id=member_id, token=MobileToken.generate_token())
        db.session.add(token_entry)
        db.session.commit()
    
    # QR-Code mit Mobile-URL generieren
    base_url = os.getenv('BASE_URL', request.host_url.rstrip('/'))
    mobile_url = f"{base_url}/m/{token_entry.token}"
    qr_image = generate_qr_code(mobile_url)
    
    return render_template('qr.html', member=member, qr_image=qr_image, mobile_url=mobile_url)


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
    token_entry = MobileToken.query.filter_by(token=token).first()
    if not token_entry:
        return render_template('invalid_token.html'), 404
    
    member_id = token_entry.member_id
    member_name = get_member_name(member_id)
    member = {'id': str(member_id), 'name': member_name}
    
    today_menu = Menu.query.filter_by(datum=date.today()).first()
    registration = Registration.query.filter_by(member_id=member_id, datum=date.today()).first()
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
                message = f"Anmeldefrist abgelaufen ({today_menu.anmeldefrist} Uhr)"
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
                    member_id=member_id,
                    datum=date.today(),
                    menu_wahl=menu_choice
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
                         member=member,
                         menu=today_menu,
                         is_registered=is_registered,
                         registration=registration,
                         registration_closed=registration_closed,
                         message=message,
                         status=status_type)
