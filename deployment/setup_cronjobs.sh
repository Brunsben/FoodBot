#!/bin/bash
# Cronjob Setup für FoodBot
# Dieses Skript richtet die Cronjobs für automatisches Reset und Backup ein

echo "🚒 FoodBot Cronjob Setup"
echo "========================"
echo ""

# Aktuelles Verzeichnis ermitteln
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Project Directory: $PROJECT_DIR"
echo ""

# Python-Pfad ermitteln
PYTHON_PATH=$(which python3)
echo "Python Path: $PYTHON_PATH"
echo ""

# Backup Cronjob: Täglich um 00:30 Uhr
BACKUP_CRON="30 0 * * * $PYTHON_PATH $PROJECT_DIR/backup_db.py >> /var/log/foodbot/backup.log 2>&1"

# Reset Cronjob: Täglich um 00:00 Uhr
RESET_CRON="0 0 * * * $PYTHON_PATH $PROJECT_DIR/clear_registrations.py >> /var/log/foodbot/reset.log 2>&1"

echo "Cronjobs werden eingerichtet:"
echo ""
echo "1. Backup (täglich 00:30 Uhr):"
echo "   $BACKUP_CRON"
echo ""
echo "2. Reset (täglich 00:00 Uhr):"
echo "   $RESET_CRON"
echo ""

# Log-Verzeichnis erstellen
echo "Erstelle Log-Verzeichnis..."
sudo mkdir -p /var/log/foodbot
sudo chown $USER:$USER /var/log/foodbot
echo "✓ Log-Verzeichnis erstellt"
echo ""

# Aktuellen Crontab sichern
echo "Sichere aktuellen Crontab..."
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null
echo "✓ Backup erstellt"
echo ""

# Neue Cronjobs hinzufügen (nur wenn nicht bereits vorhanden)
(crontab -l 2>/dev/null | grep -v "backup_db.py"; echo "$BACKUP_CRON") | crontab -
(crontab -l 2>/dev/null | grep -v "clear_registrations.py"; echo "$RESET_CRON") | crontab -

echo "✓ Cronjobs installiert"
echo ""
echo "Aktuelle Cronjobs:"
echo "=================="
crontab -l
echo ""
echo "✅ Setup abgeschlossen!"
echo ""
echo "Die Logs finden sich in:"
echo "  - /var/log/foodbot/backup.log"
echo "  - /var/log/foodbot/reset.log"
echo ""
echo "Zum Testen kannst du die Skripte manuell ausführen:"
echo "  python3 $PROJECT_DIR/backup_db.py"
echo "  python3 $PROJECT_DIR/clear_registrations.py"
