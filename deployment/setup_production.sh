#!/bin/bash
# Production Deployment Setup für FoodBot
# Dieses Skript richtet den FoodBot für Production auf einem Raspberry Pi ein

set -e

echo "🚒 FoodBot Production Setup"
echo "============================"
echo ""

# Farben für Output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Prüfe ob als root ausgeführt wird
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}⚠️  Bitte als root ausführen (sudo ./setup_production.sh)${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 System-Voraussetzungen prüfen...${NC}"
echo ""

# Projektverzeichnis
PROJECT_DIR="/home/pi/FoodBot"
LOG_DIR="/var/log/foodbot"
BACKUP_DIR="$PROJECT_DIR/backups"
VENV_DIR="$PROJECT_DIR/venv"

# Prüfe ob Projektverzeichnis existiert
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Projektverzeichnis $PROJECT_DIR nicht gefunden!${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Projektverzeichnis gefunden"

# Log-Verzeichnis erstellen
echo -e "${YELLOW}📁 Erstelle Verzeichnisse...${NC}"
mkdir -p "$LOG_DIR"
mkdir -p "$BACKUP_DIR"
chown -R pi:pi "$LOG_DIR"
chown -R pi:pi "$BACKUP_DIR"
echo -e "${GREEN}✓${NC} Verzeichnisse erstellt"
echo ""

# Python Virtual Environment prüfen/erstellen
echo -e "${YELLOW}🐍 Python Virtual Environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    echo "Erstelle Virtual Environment..."
    sudo -u pi python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓${NC} Virtual Environment erstellt"
else
    echo -e "${GREEN}✓${NC} Virtual Environment existiert bereits"
fi

# Requirements installieren
echo "Installiere Python-Pakete..."
sudo -u pi "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
echo -e "${GREEN}✓${NC} Python-Pakete installiert"
echo ""

# Datenbank initialisieren
echo -e "${YELLOW}💾 Datenbank initialisieren...${NC}"
cd "$PROJECT_DIR"
sudo -u pi "$VENV_DIR/bin/python" -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('✓ Datenbank initialisiert')"
echo ""

# Systemd Service installieren
echo -e "${YELLOW}⚙️  Systemd Service installieren...${NC}"
cp "$PROJECT_DIR/deployment/foodbot.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable foodbot.service
echo -e "${GREEN}✓${NC} Service installiert und aktiviert"
echo ""

# Logrotate konfigurieren
echo -e "${YELLOW}📝 Logrotate konfigurieren...${NC}"
cp "$PROJECT_DIR/deployment/logrotate-foodbot" /etc/logrotate.d/foodbot
chmod 644 /etc/logrotate.d/foodbot
echo -e "${GREEN}✓${NC} Logrotate konfiguriert"
echo ""

# Cronjobs einrichten
echo -e "${YELLOW}⏰ Cronjobs einrichten...${NC}"
# Backup Cronjob: Täglich um 00:30 Uhr
BACKUP_CRON="30 0 * * * $VENV_DIR/bin/python $PROJECT_DIR/backup_db.py >> $LOG_DIR/backup.log 2>&1"
# Reset Cronjob: Täglich um 00:00 Uhr
RESET_CRON="0 0 * * * $VENV_DIR/bin/python $PROJECT_DIR/clear_registrations.py >> $LOG_DIR/reset.log 2>&1"

# Cronjobs für pi-User hinzufügen
(sudo -u pi crontab -l 2>/dev/null | grep -v "backup_db.py"; echo "$BACKUP_CRON") | sudo -u pi crontab -
(sudo -u pi crontab -l 2>/dev/null | grep -v "clear_registrations.py"; echo "$RESET_CRON") | sudo -u pi crontab -
echo -e "${GREEN}✓${NC} Cronjobs eingerichtet"
echo ""

# Nginx installieren (optional)
echo -e "${YELLOW}🌐 Nginx (optional)...${NC}"
read -p "Möchtest du Nginx als Reverse Proxy installieren? (j/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Jj]$ ]]; then
    apt-get update
    apt-get install -y nginx
    cp "$PROJECT_DIR/deployment/nginx-foodbot" /etc/nginx/sites-available/foodbot
    ln -sf /etc/nginx/sites-available/foodbot /etc/nginx/sites-enabled/foodbot
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
    systemctl enable nginx
    echo -e "${GREEN}✓${NC} Nginx installiert und konfiguriert"
else
    echo "Nginx übersprungen"
fi
echo ""

# Environment-Variablen setzen
echo -e "${YELLOW}🔐 Environment-Variablen...${NC}"
echo "Bitte setze folgende Variablen in /etc/systemd/system/foodbot.service:"
echo "  - ADMIN_PASSWORD (aktuell: feuerwehr2026)"
echo "  - SECRET_KEY (generiere mit: python3 -c 'import os; print(os.urandom(24).hex())')"
echo ""
read -p "Möchtest du jetzt einen neuen SECRET_KEY generieren? (j/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Jj]$ ]]; then
    NEW_SECRET=$(python3 -c 'import os; print(os.urandom(24).hex())')
    echo -e "${GREEN}Neuer SECRET_KEY:${NC} $NEW_SECRET"
    echo "Trage diesen in /etc/systemd/system/foodbot.service ein"
fi
echo ""

# Service starten
echo -e "${YELLOW}🚀 Service starten...${NC}"
systemctl start foodbot.service
sleep 2
systemctl status foodbot.service --no-pager
echo ""

# Zusammenfassung
echo -e "${GREEN}✅ Production Setup abgeschlossen!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 FoodBot läuft jetzt als System-Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔧 Wichtige Befehle:"
echo "   systemctl start foodbot    - Service starten"
echo "   systemctl stop foodbot     - Service stoppen"
echo "   systemctl restart foodbot  - Service neu starten"
echo "   systemctl status foodbot   - Status anzeigen"
echo "   journalctl -u foodbot -f   - Logs live ansehen"
echo ""
echo "📂 Verzeichnisse:"
echo "   Logs:    $LOG_DIR"
echo "   Backups: $BACKUP_DIR"
echo "   Projekt: $PROJECT_DIR"
echo ""
echo "🌐 Zugriff:"
if systemctl is-active --quiet nginx; then
    echo "   http://$(hostname -I | awk '{print $1}')    (Nginx Reverse Proxy)"
    echo "   http://localhost:5001              (Direkt zu Gunicorn)"
else
    echo "   http://$(hostname -I | awk '{print $1}'):5001"
fi
echo ""
echo "⏰ Cronjobs:"
echo "   00:00 Uhr - Automatisches Reset der Anmeldungen"
echo "   00:30 Uhr - Automatisches Backup der Datenbank"
echo ""
echo "🔐 Standard-Login:"
echo "   Passwort: feuerwehr2026"
echo "   (Ändern in /etc/systemd/system/foodbot.service)"
echo ""
