#!/usr/bin/env python3
"""
FoodBot - Systemcheck und Wartung
Prüft Konfiguration, Datenbank und Abhängigkeiten
"""

import sys
import os

def check_dependencies():
    """Prüfe ob alle Python-Abhängigkeiten installiert sind"""
    print("📦 Prüfe Abhängigkeiten...")
    required = ['flask', 'flask_sqlalchemy', 'dotenv', 'serial']
    missing = []
    
    for module in required:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError:
            print(f"  ✗ {module} fehlt")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️  Fehlende Module: {', '.join(missing)}")
        print("Installiere mit: pip3 install -r requirements.txt")
        return False
    return True

def check_config():
    """Prüfe Konfigurationsdateien"""
    print("\n⚙️  Prüfe Konfiguration...")
    
    if not os.path.exists('.env'):
        print("  ⚠️  .env fehlt - verwende .env.example als Vorlage")
        return False
    else:
        print("  ✓ .env vorhanden")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key or secret_key == 'dev-secret-key-change-in-production':
        print("  ⚠️  SECRET_KEY ist unsicher - bitte in .env ändern!")
        return False
    else:
        print("  ✓ SECRET_KEY gesetzt")
    
    return True

def check_database():
    """Prüfe Datenbankverbindung"""
    print("\n🗄️  Prüfe Datenbank...")
    
    try:
        from app import create_app
        from app.models import User, Menu, Registration
        
        app = create_app()
        with app.app_context():
            user_count = User.query.count()
            menu_today = Menu.query.filter_by(date=__import__('datetime').date.today()).first()
            reg_count = Registration.query.filter_by(date=__import__('datetime').date.today()).count()
            
            print(f"  ✓ Datenbank verbunden")
            print(f"  📊 {user_count} User angelegt")
            print(f"  📊 {reg_count} Anmeldungen heute")
            print(f"  📊 Menü heute: {menu_today.description if menu_today else 'nicht gesetzt'}")
        return True
    except Exception as e:
        print(f"  ✗ Datenbankfehler: {e}")
        return False

def check_rfid():
    """Prüfe RFID-Reader"""
    print("\n🔖 Prüfe RFID-Reader...")
    
    port = os.environ.get('RFID_PORT', '/dev/ttyUSB0')
    
    if not os.path.exists(port):
        print(f"  ⚠️  RFID-Port {port} nicht gefunden")
        print(f"  💡 Verfügbare Ports: {', '.join([f for f in os.listdir('/dev') if 'tty' in f][:5])}")
        return False
    else:
        print(f"  ✓ RFID-Port {port} vorhanden")
    
    return True

def main():
    print("=" * 50)
    print("🚒 FoodBot System-Check")
    print("=" * 50)
    
    checks = [
        check_dependencies(),
        check_config(),
        check_database(),
        check_rfid()
    ]
    
    print("\n" + "=" * 50)
    if all(checks):
        print("✅ Alle Checks erfolgreich!")
        return 0
    else:
        print("⚠️  Einige Checks fehlgeschlagen - bitte Fehler beheben")
        return 1

if __name__ == '__main__':
    sys.exit(main())
