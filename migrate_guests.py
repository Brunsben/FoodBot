#!/usr/bin/env python3
"""
Migration: Guest-Tabelle um menu_choice erweitern
Migriert bestehende Gäste zu Menü 1
"""

from app import create_app, db
from app.models import Guest
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Starte Guest-Migration...")
    
    # Prüfe ob Spalte bereits existiert
    try:
        result = db.session.execute(text("SELECT menu_choice FROM guest LIMIT 1"))
        print("✓ Spalte 'menu_choice' existiert bereits")
    except Exception:
        # Spalte existiert nicht, füge sie hinzu
        print("Füge Spalte 'menu_choice' hinzu...")
        db.session.execute(text("ALTER TABLE guest ADD COLUMN menu_choice INTEGER DEFAULT 1"))
        db.session.commit()
        print("✓ Spalte hinzugefügt")
    
    # Entferne old unique constraint wenn vorhanden
    try:
        db.session.execute(text("DROP INDEX IF EXISTS guest.date"))
        print("✓ Alter Index entfernt")
    except Exception as e:
        print(f"  Index konnte nicht entfernt werden: {e}")
    
    # Setze menu_choice auf 1 für alle bestehenden Einträge
    db.session.execute(text("UPDATE guest SET menu_choice = 1 WHERE menu_choice IS NULL"))
    db.session.commit()
    print("✓ Bestehende Gäste zu Menü 1 migriert")
    
    # Erstelle neuen unique constraint
    try:
        db.session.execute(text("CREATE UNIQUE INDEX _guest_date_menu_uc ON guest(date, menu_choice)"))
        print("✓ Neuer Unique-Index erstellt")
    except Exception as e:
        print(f"  Index bereits vorhanden: {e}")
    
    print("\n✅ Migration abgeschlossen!")
    print("Gäste haben jetzt eine Menüauswahl (1 oder 2)")
