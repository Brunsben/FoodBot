#!/usr/bin/env python3
"""
Migration: Guest-Tabelle um menu_choice erweitern
Migriert bestehende Gäste zu Menü 1
"""

from app import create_app, db
from app.models import Guest
from sqlalchemy import text, inspect

app = create_app()

with app.app_context():
    print("Starte Guest-Migration...")
    
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('guest')]
    
    if 'menu_choice' in columns:
        print("✓ Spalte 'menu_choice' existiert bereits")
        print("✅ Migration bereits durchgeführt!")
    else:
        print("Führe Migration durch...")
        
        # SQLite kann keine Constraints direkt ändern, daher:
        # 1. Alte Daten sichern
        old_guests = db.session.execute(text("SELECT id, date, count FROM guest")).fetchall()
        print(f"  Gefunden: {len(old_guests)} bestehende Gast-Einträge")
        
        # 2. Tabelle löschen
        db.session.execute(text("DROP TABLE IF EXISTS guest"))
        db.session.commit()
        print("  ✓ Alte Tabelle entfernt")
        
        # 3. Neue Tabelle erstellen (mit neuem Model)
        db.create_all()
        print("  ✓ Neue Tabelle mit menu_choice erstellt")
        
        # 4. Alte Daten zurück migrieren (alles zu menu_choice=1)
        for guest_id, date, count in old_guests:
            db.session.execute(
                text("INSERT INTO guest (id, date, menu_choice, count) VALUES (:id, :date, :menu_choice, :count)"),
                {"id": guest_id, "date": date, "menu_choice": 1, "count": count}
            )
        db.session.commit()
        print(f"  ✓ {len(old_guests)} Einträge zu Menü 1 migriert")
        
        print("\n✅ Migration abgeschlossen!")
        print("Gäste haben jetzt eine Menüauswahl (1 oder 2)")

