#!/usr/bin/env python3
"""
Migration: Anmeldefrist-Feature hinzufügen
Fügt registration_deadline und deadline_enabled zur menu-Tabelle hinzu
"""

from app import create_app
from app.models import db
import sqlite3
import os

def migrate():
    app = create_app()
    db_path = os.path.join(app.instance_path, 'foodbot.db')
    
    print("🔄 Starte Datenbank-Migration für Anmeldefrist...")
    
    with app.app_context():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Prüfen ob Spalten bereits existieren
            cursor.execute("PRAGMA table_info(menu)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # registration_deadline hinzufügen
            if 'registration_deadline' not in columns:
                cursor.execute("""
                    ALTER TABLE menu 
                    ADD COLUMN registration_deadline VARCHAR(5) DEFAULT '19:45'
                """)
                print("  ✓ 'registration_deadline' Spalte hinzugefügt")
            else:
                print("  ✓ 'registration_deadline' existiert bereits")
            
            # deadline_enabled hinzufügen
            if 'deadline_enabled' not in columns:
                cursor.execute("""
                    ALTER TABLE menu 
                    ADD COLUMN deadline_enabled BOOLEAN DEFAULT 1
                """)
                print("  ✓ 'deadline_enabled' Spalte hinzugefügt")
            else:
                print("  ✓ 'deadline_enabled' existiert bereits")
            
            conn.commit()
            print("✅ Migration erfolgreich abgeschlossen!")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Fehler bei der Migration: {e}")
            raise
        finally:
            conn.close()

if __name__ == '__main__':
    migrate()
