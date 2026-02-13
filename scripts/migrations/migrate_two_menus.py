#!/usr/bin/env python3
"""
Migrationsskript für Zwei-Menü-System
Fügt neue Spalten zu Menu und Registration hinzu
"""
from app import create_app
from app.models import db
from sqlalchemy import text
import sys

def migrate_database():
    app = create_app()
    
    with app.app_context():
        print("🔄 Starte Datenbank-Migration für Zwei-Menü-System...")
        
        try:
            # Prüfe ob Spalten schon existieren
            inspector = db.inspect(db.engine)
            menu_columns = [col['name'] for col in inspector.get_columns('menu')]
            registration_columns = [col['name'] for col in inspector.get_columns('registration')]
            
            # Migration für Menu-Tabelle
            if 'zwei_menues_aktiv' not in menu_columns:
                print("  ➕ Füge 'zwei_menues_aktiv' zu Menu hinzu...")
                db.session.execute(text('ALTER TABLE menu ADD COLUMN zwei_menues_aktiv BOOLEAN DEFAULT 0'))
            else:
                print("  ✓ 'zwei_menues_aktiv' existiert bereits")
            
            if 'menu1_name' not in menu_columns:
                print("  ➕ Füge 'menu1_name' zu Menu hinzu...")
                db.session.execute(text('ALTER TABLE menu ADD COLUMN menu1_name VARCHAR(200)'))
            else:
                print("  ✓ 'menu1_name' existiert bereits")
            
            if 'menu2_name' not in menu_columns:
                print("  ➕ Füge 'menu2_name' zu Menu hinzu...")
                db.session.execute(text('ALTER TABLE menu ADD COLUMN menu2_name VARCHAR(200)'))
            else:
                print("  ✓ 'menu2_name' existiert bereits")
            
            # Migration für Registration-Tabelle
            if 'menu_choice' not in registration_columns:
                print("  ➕ Füge 'menu_choice' zu Registration hinzu...")
                db.session.execute(text('ALTER TABLE registration ADD COLUMN menu_choice INTEGER DEFAULT 1'))
            else:
                print("  ✓ 'menu_choice' existiert bereits")
            
            db.session.commit()
            print("✅ Migration erfolgreich abgeschlossen!")
            return True
            
        except Exception as e:
            print(f"❌ Fehler bei der Migration: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = migrate_database()
    sys.exit(0 if success else 1)
