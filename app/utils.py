from .models import db, User, Menu, Registration, Guest
from datetime import date
import logging

logger = logging.getLogger(__name__)


def get_guests_for_date(target_date=None):
    """Lade Gäste für ein Datum und gib strukturierte Daten zurück.
    
    Returns:
        dict mit: {
            'all': [Guest objects],
            'menu1': Guest object oder None,
            'menu2': Guest object oder None,
            'total_count': int
        }
    """
    if target_date is None:
        target_date = date.today()
    
    guests = Guest.query.filter_by(date=target_date).all()
    guest_menu1 = next((g for g in guests if g.menu_choice == 1), None)
    guest_menu2 = next((g for g in guests if g.menu_choice == 2), None)
    
    return {
        'all': guests,
        'menu1': guest_menu1,
        'menu2': guest_menu2,
        'total_count': sum(g.count for g in guests)
    }


def save_menu(menu_date, form_data, field_prefix=''):
    """Menü speichern/aktualisieren. Einheitliche Logik für Admin, Kitchen und Weekly.
    
    Args:
        menu_date: date Objekt für welchen Tag
        form_data: request.form dict
        field_prefix: Prefix für Formfeld-Namen (z.B. '' oder 'menu')
    
    Returns:
        Menu Objekt
    """
    existing_menu = Menu.query.filter_by(date=menu_date).first()
    zwei_menues = form_data.get('zwei_menues_aktiv') == '1'
    deadline_enabled = form_data.get('deadline_enabled') == '1'
    registration_deadline = form_data.get('registration_deadline', '19:45')
    
    if zwei_menues:
        # Verschiedene Feld-Namen je nach Formular unterstützen
        menu1_text = (form_data.get(f'{field_prefix}menu1_text') or 
                      form_data.get('menu1') or '').strip()
        menu2_text = (form_data.get(f'{field_prefix}menu2_text') or 
                      form_data.get('menu2') or '').strip()
        description = f"{menu1_text} / {menu2_text}"
        
        if existing_menu:
            existing_menu.zwei_menues_aktiv = True
            existing_menu.menu1_name = menu1_text
            existing_menu.menu2_name = menu2_text
            existing_menu.description = description
            existing_menu.deadline_enabled = deadline_enabled
            existing_menu.registration_deadline = registration_deadline
        else:
            existing_menu = Menu(
                date=menu_date,
                description=description,
                zwei_menues_aktiv=True,
                menu1_name=menu1_text,
                menu2_name=menu2_text,
                deadline_enabled=deadline_enabled,
                registration_deadline=registration_deadline
            )
            db.session.add(existing_menu)
    else:
        menu_text = (form_data.get(f'{field_prefix}menu_text') or 
                     form_data.get('menu') or '').strip()
        
        if existing_menu:
            existing_menu.zwei_menues_aktiv = False
            existing_menu.description = menu_text
            existing_menu.menu1_name = None
            existing_menu.menu2_name = None
            existing_menu.deadline_enabled = deadline_enabled
            existing_menu.registration_deadline = registration_deadline
        else:
            existing_menu = Menu(
                date=menu_date,
                description=menu_text,
                zwei_menues_aktiv=False,
                deadline_enabled=deadline_enabled,
                registration_deadline=registration_deadline
            )
            db.session.add(existing_menu)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fehler beim Menü-Speichern: {e}")
        raise
    
    return existing_menu

def register_user_for_today(user: User, menu_choice: int = 1):
    """An-/Abmeldung eines Users für heute. Gibt True zurück wenn angemeldet, False wenn abgemeldet."""
    try:
        existing = Registration.query.filter_by(user_id=user.id, date=date.today()).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            return False  # Abgemeldet
        else:
            reg = Registration(user_id=user.id, date=date.today(), menu_choice=menu_choice)
            db.session.add(reg)
            db.session.commit()
            return True  # Angemeldet
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fehler bei Registrierung für User {user.id}: {e}")
        raise
