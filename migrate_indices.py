#!/usr/bin/env python3
"""
Migrations-Skript zur Optimierung der Datenbank-Indizes
Fügt Composite-Index für Guest und Index für AdminLog.admin_user hinzu
"""

from app import create_app, db
from sqlalchemy import inspect, Index

def migrate_indices():
    """Fügt fehlende Indizes hinzu"""
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        print("🔍 Überprüfe Datenbank-Indizes...")
        
        # Prüfe Guest-Tabelle
        guest_indices = inspector.get_indexes('guest')
        guest_index_names = [idx['name'] for idx in guest_indices]
        
        if 'idx_guest_date_menu' not in guest_index_names:
            print("➕ Erstelle Index 'idx_guest_date_menu' auf Guest(date, menu_choice)...")
            try:
                # SQLite unterstützt CREATE INDEX IF NOT EXISTS
                db.engine.execute('CREATE INDEX IF NOT EXISTS idx_guest_date_menu ON guest (date, menu_choice)')
                print("✅ Guest-Index erfolgreich erstellt")
            except Exception as e:
                print(f"⚠️  Fehler beim Erstellen des Guest-Index: {e}")
        else:
            print("✅ Guest-Index bereits vorhanden")
        
        # Prüfe AdminLog-Tabelle
        admin_log_indices = inspector.get_indexes('admin_log')
        admin_log_index_names = [idx['name'] for idx in admin_log_indices]
        
        if 'ix_admin_log_admin_user' not in admin_log_index_names:
            print("➕ Erstelle Index auf AdminLog.admin_user...")
            try:
                db.engine.execute('CREATE INDEX IF NOT EXISTS ix_admin_log_admin_user ON admin_log (admin_user)')
                print("✅ AdminLog-Index erfolgreich erstellt")
            except Exception as e:
                print(f"⚠️  Fehler beim Erstellen des AdminLog-Index: {e}")
        else:
            print("✅ AdminLog-Index bereits vorhanden")
        
        print("\n✨ Index-Migration abgeschlossen!")
        
        # Zeige alle Indizes
        print("\n📊 Aktuelle Indizes:")
        for table in ['user', 'menu', 'registration', 'guest', 'admin_log']:
            indices = inspector.get_indexes(table)
            if indices:
                print(f"\n{table.upper()}:")
                for idx in indices:
                    cols = ', '.join(idx['column_names'])
                    unique = " (UNIQUE)" if idx.get('unique') else ""
                    print(f"  - {idx['name']}: {cols}{unique}")

if __name__ == '__main__':
    migrate_indices()
