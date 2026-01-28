#!/usr/bin/env python3
"""
Backup-Skript für FoodBot-Datenbank
Erstellt tägliche Backups der SQLite-Datenbank
"""

import shutil
import os
from datetime import datetime

# Konfiguration
DB_FILE = 'foodbot.db'
BACKUP_DIR = 'backups'
MAX_BACKUPS = 14  # Behalte die letzten 14 Backups

def create_backup():
    """Erstelle ein Backup der Datenbank"""
    if not os.path.exists(DB_FILE):
        print(f"⚠️  Datenbank {DB_FILE} nicht gefunden!")
        return False
    
    # Backup-Verzeichnis erstellen
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Dateiname mit Zeitstempel
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'foodbot_backup_{timestamp}.db')
    
    # Kopiere Datenbank
    shutil.copy2(DB_FILE, backup_file)
    file_size = os.path.getsize(backup_file) / 1024  # KB
    print(f"✅ Backup erstellt: {backup_file} ({file_size:.1f} KB)")
    
    # Alte Backups löschen
    cleanup_old_backups()
    
    return True

def cleanup_old_backups():
    """Lösche alte Backups, behalte nur die letzten MAX_BACKUPS"""
    if not os.path.exists(BACKUP_DIR):
        return
    
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')])
    
    if len(backups) > MAX_BACKUPS:
        to_delete = backups[:-MAX_BACKUPS]
        for old_backup in to_delete:
            path = os.path.join(BACKUP_DIR, old_backup)
            os.remove(path)
            print(f"🗑️  Altes Backup gelöscht: {old_backup}")

if __name__ == '__main__':
    print("🔄 Starte Datenbank-Backup...")
    success = create_backup()
    exit(0 if success else 1)
