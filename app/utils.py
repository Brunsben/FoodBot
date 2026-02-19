from .models import db, User, Menu, Registration, Guest
from datetime import date as date_type
from contextlib import contextmanager
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@contextmanager
def db_transaction():
    """
    Context Manager für sichere Datenbank-Transaktionen
    
    Automatisches Commit bei Erfolg, Rollback bei Fehler.
    Verhindert vergessene Rollbacks und verbessert Code-Lesbarkeit.
    
    Usage:
        with db_transaction():
            user = User(name="Test", personal_number="123")
            db.session.add(user)
            # Commit erfolgt automatisch bei Success
            
    Raises:
        Exception: Bei DB-Fehler (nach Rollback)
    """
    try:
        yield
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Transaction failed, rolled back: {e}")
        raise  # Re-raise für Error-Handling im Caller


def get_menu_for_date(target_date: Optional[date_type] = None) -> Optional[Menu]:
    """
    Lade Menü für ein Datum.
    
    Args:
        target_date: date object, default ist heute
        
    Returns:
        Menu object oder None
    """
    if target_date is None:
        target_date = date_type.today()
    return Menu.query.filter_by(date=target_date).first()


def get_guests_for_date(target_date: Optional[date_type] = None) -> Dict[str, Any]:
    """
    Lade Gäste für ein Datum und gib strukturierte Daten zurück.
    
    Args:
        target_date: date object, default ist heute
    
    Returns:
        dict mit: {
            'all': [Guest objects],
            'menu1': Guest object oder None,
            'menu2': Guest object oder None,
            'total_count': int
        }
    """
    if target_date is None:
        target_date = date_type.today()
    
    guests = Guest.query.filter_by(date=target_date).all()
    guest_menu1 = next((g for g in guests if g.menu_choice == 1), None)
    guest_menu2 = next((g for g in guests if g.menu_choice == 2), None)
    
    return {
        'all': guests,
        'menu1': guest_menu1,
        'menu2': guest_menu2,
        'total_count': sum(g.count for g in guests)
    }


def save_menu(menu_date: date_type, form_data: Dict[str, Any], field_prefix: str = '') -> Menu:
    """
    Menü speichern/aktualisieren. Einheitliche Logik für Admin, Kitchen und Weekly.
    
    Args:
        menu_date: date Objekt für welchen Tag
        form_data: request.form dict
        field_prefix: Prefix für Formfeld-Namen (z.B. '' oder 'menu')
    
    Returns:
        Menu Objekt (neu oder aktualisiert)
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


def register_user_for_today(user: User, menu_choice: int = 1) -> bool:
    """
    An-/Abmeldung eines Users für heute (Toggle).
    
    Args:
        user: User-Objekt
        menu_choice: Menü-Auswahl (1 oder 2)
    
    Returns:
        True wenn User angemeldet wurde, False wenn abgemeldet
        
    Raises:
        Exception: Bei Datenbankfehlern
    """
    try:
        existing = Registration.query.filter_by(user_id=user.id, date=date_type.today()).first()
        if existing:
            with db_transaction():
                db.session.delete(existing)
            return False  # Abgemeldet
        else:
            reg = Registration(user_id=user.id, date=date_type.today(), menu_choice=menu_choice)
            with db_transaction():
                db.session.add(reg)
            return True  # Angemeldet
    except Exception as e:
        logger.error(f"Fehler bei Registrierung für User {user.id}: {e}")
        raise
