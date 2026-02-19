"""
Input Validation und Sanitization
Sicherheits-Layer für alle Benutzereingaben
"""

import re
from datetime import datetime, date as date_type
from typing import Optional, Any


def sanitize_string(value: Any, max_length: Optional[int] = None, allow_empty: bool = False) -> Optional[str]:
    """
    Bereinigt String-Eingaben
    
    Args:
        value: Eingabewert
        max_length: Maximale Länge
        allow_empty: Ob leere Strings erlaubt sind
    
    Returns:
        Bereinigter String oder None bei Fehler
    """
    if value is None:
        return None if allow_empty else None
    
    # Zu String konvertieren und trimmen
    cleaned = str(value).strip()
    
    # Leere Strings behandeln
    if not cleaned:
        return cleaned if allow_empty else None
    
    # Maximale Länge prüfen
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    # XSS-gefährliche Zeichen entfernen/escapen
    # Entfernt < > für grundlegenden XSS-Schutz
    cleaned = cleaned.replace('<', '&lt;').replace('>', '&gt;')
    
    return cleaned


def validate_personal_number(personal_number: str) -> Optional[str]:
    """
    Validiert Personalnummer (alphanumerisch, 1-20 Zeichen)
    
    Args:
        personal_number: Zu validierende Personalnummer
    
    Returns:
        Bereinigte Personalnummer oder None bei Fehler
    """
    if not personal_number:
        return None
    
    cleaned = sanitize_string(personal_number, max_length=20)
    if not cleaned:
        return None
    
    # Nur alphanumerische Zeichen und Bindestriche erlauben
    if not re.match(r'^[A-Za-z0-9\-]+$', cleaned):
        return None
    
    return cleaned


def validate_card_id(card_id: str) -> Optional[str]:
    """
    Validiert RFID-Karten-ID (hexadezimal, 1-50 Zeichen)
    
    Args:
        card_id: Zu validierende Karten-ID
    
    Returns:
        Bereinigte Karten-ID oder None
    """
    if not card_id:
        return None
    
    cleaned = sanitize_string(card_id, max_length=50)
    if not cleaned:
        return None
    
    # Nur hexadezimale Zeichen erlauben (0-9, A-F, a-f)
    if not re.match(r'^[0-9A-Fa-f]+$', cleaned):
        return None
    
    return cleaned.upper()  # Normalisierung zu Großbuchstaben


def validate_name(name: str) -> Optional[str]:
    """
    Validiert Benutzernamen (Unicode-Buchstaben, Leerzeichen, Bindestriche)
    
    Args:
        name: Zu validierender Name
    
    Returns:
        Bereinigter Name oder None bei Fehler
    """
    if not name:
        return None
    
    cleaned = sanitize_string(name, max_length=100)
    if not cleaned:
        return None
    
    # Mindestens 2 Zeichen
    if len(cleaned) < 2:
        return None
    
    # Nur Buchstaben, Leerzeichen, Bindestriche und Punkte
    if not re.match(r'^[A-Za-zÄÖÜäöüß\s\.\-]+$', cleaned):
        return None
    
    return cleaned


def validate_integer(value: Any, min_value: Optional[int] = None, max_value: Optional[int] = None, default: Optional[int] = None) -> Optional[int]:
    """
    Validiert Integer-Eingaben
    
    Args:
        value: Zu validierender Wert
        min_value: Minimaler erlaubter Wert
        max_value: Maximaler erlaubter Wert
        default: Standardwert bei Fehler
    
    Returns:
        Integer-Wert oder default
    """
    try:
        num = int(value)
        
        if min_value is not None and num < min_value:
            return default
        
        if max_value is not None and num > max_value:
            return default
        
        return num
    except (TypeError, ValueError):
        return default


def validate_date(date_string: str) -> Optional[date_type]:
    """
    Validiert Datums-String im Format YYYY-MM-DD
    
    Args:
        date_string: Datums-String
    
    Returns:
        date-Objekt oder None bei Fehler
    """
    if not date_string:
        return None
    
    try:
        # Parsen mit datetime
        parsed = datetime.strptime(str(date_string).strip(), '%Y-%m-%d')
        return parsed.date()
    except (ValueError, AttributeError):
        return None


def validate_time(time_string: str) -> Optional[str]:
    """
    Validiert Zeit-String im Format HH:MM
    
    Args:
        time_string: Zeit-String
    
    Returns:
        Zeit-String oder None bei Fehler
    """
    if not time_string:
        return None
    
    cleaned = str(time_string).strip()
    
    # Format HH:MM prüfen
    if not re.match(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$', cleaned):
        return None
    
    return cleaned


def validate_menu_choice(choice: Any, zwei_menues_aktiv: bool = False) -> int:
    """
    Validiert Menü-Auswahl (1 oder 2)
    
    Args:
        choice: Menü-Nummer
        zwei_menues_aktiv: Ob zwei Menüs aktiv sind
    
    Returns:
        1 oder 2, default 1
    """
    choice = validate_integer(choice, min_value=1, max_value=2, default=1)
    
    # Wenn nur ein Menü aktiv ist, immer 1 zurückgeben
    if not zwei_menues_aktiv:
        return 1
    
    return choice


def validate_token(token: str) -> Optional[str]:
    """
    Validiert Mobile Token (URL-safe base64, 32-64 Zeichen)
    
    Args:
        token: Zu validierender Token
    
    Returns:
        Token oder None bei Fehler
    """
    if not token:
        return None
    
    cleaned = str(token).strip()
    
    # Länge prüfen
    if len(cleaned) < 32 or len(cleaned) > 64:
        return None
    
    # Nur URL-safe Zeichen erlauben (a-z, A-Z, 0-9, -, _)
    if not re.match(r'^[A-Za-z0-9\-_]+$', cleaned):
        return None
    
    return cleaned


def sanitize_sql_like_pattern(pattern: str, max_length: int = 50) -> str:
    """
    Bereinigt Suchpattern für SQL LIKE-Queries
    
    Args:
        pattern: Suchmuster
        max_length: Maximale Länge
    
    Returns:
        Bereinigtes Pattern
    """
    if not pattern:
        return ''
    
    cleaned = sanitize_string(pattern, max_length=max_length, allow_empty=True)
    if not cleaned:
        return ''
    
    # SQL-Wildcards escapen (außer user möchte sie verwenden)
    # % und _ haben spezielle Bedeutung in LIKE
    cleaned = cleaned.replace('\\', '\\\\')  # Backslash zuerst
    
    return cleaned


# Validierungs-Fehler-Klasse
class ValidationError(Exception):
    """Exception für Validierungsfehler"""
    pass
