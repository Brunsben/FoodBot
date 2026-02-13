#!/usr/bin/env python3
"""
Migrationsskript für vordefinierte Menüs
"""
from app import create_app
from app.models import db, PresetMenu
from sqlalchemy import text
import sys

def migrate_database():
    app = create_app()
    
    with app.app_context():
        print("🔄 Starte Datenbank-Migration für vordefinierte Menüs...")
        
        try:
            # Erstelle Tabelle falls nicht vorhanden
            db.create_all()
            print("✅ Tabelle 'preset_menu' erstellt/geprüft")
            
            # Füge Standard-Menüs hinzu falls Tabelle leer ist
            if PresetMenu.query.count() == 0:
                print("  ➕ Füge Standard-Menüs hinzu...")
                default_menus = [
                    "Schnitzel mit Pommes",
                    "Spaghetti Bolognese",
                    "Currywurst mit Pommes",
                    "Gulasch mit Nudeln",
                    "Hähnchen mit Reis",
                    "Kassler mit Sauerkraut",
                    "Fischfilet mit Kartoffeln",
                    "Chili con Carne",
                    "Pizza",
                    "Lasagne",
                    "Eintopf",
                    "Salat"
                ]
                
                for i, menu_name in enumerate(default_menus):
                    preset = PresetMenu(name=menu_name, sort_order=i)
                    db.session.add(preset)
                
                db.session.commit()
                print(f"  ✅ {len(default_menus)} Standard-Menüs hinzugefügt")
            else:
                print("  ✓ Vordefinierte Menüs existieren bereits")
            
            print("✅ Migration erfolgreich abgeschlossen!")
            return True
            
        except Exception as e:
            print(f"❌ Fehler bei der Migration: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = migrate_database()
    sys.exit(0 if success else 1)
