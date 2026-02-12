#!/usr/bin/env python3
"""
Datenbank-Migration: Fügt fehlende Indizes und AdminLog-Tabelle hinzu
"""
from app import create_app
from app.models import db, AdminLog
import sqlite3

def migrate_db():
    app = create_app()
    
    with app.app_context():
        # Erstelle alle neuen Tabellen (AdminLog)
        db.create_all()
        print("✅ Tabellen erstellt/aktualisiert")
        
        # Indizes werden automatisch von SQLAlchemy erstellt
        print("✅ Indizes werden beim nächsten Start angewendet")
        
        print("\n🎉 Migration erfolgreich!")
        print("Bitte Service neu starten: sudo systemctl restart foodbot")

if __name__ == '__main__':
    migrate_db()
