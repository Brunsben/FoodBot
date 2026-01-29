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

# Ermittle Projektverzeichnis (dynamisch)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
PROJECT_USER="${SUDO_USER:-$USER}"

# Konfiguration abfragen
echo "Installationsverzeichnis: $PROJECT_DIR"
echo "Installation für Benutzer: $PROJECT_USER"
echo ""
read -p "Ist dies korrekt? (j/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Jj]$ ]]; then
    read -p "Bitte gib das Installationsverzeichnis ein: " PROJECT_DIR
    read -p "Bitte gib den Benutzernamen ein: " PROJECT_USER
fi

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
chown -R "$PROJECT_USER:$PROJECT_USER" "$LOG_DIR"
chown -R "$PROJECT_USER:$PROJECT_USER" "$BACKUP_DIR"
echo -e "${GREEN}✓${NC} Verzeichnisse erstellt"
echo ""

# Python Virtual Environment prüfen/erstellen
echo -e "${YELLOW}🐍 Python Virtual Environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    echo "Erstelle Virtual Environment..."
    sudo -u "$PROJECT_USER" python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓${NC} Virtual Environment erstellt"
else
    echo -e "${GREEN}✓${NC} Virtual Environment existiert bereits"
fi

# Requirements installieren
echo "Installiere Python-Pakete..."
sudo -u "$PROJECT_USER" "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
echo -e "${GREEN}✓${NC} Python-Pakete installiert"
echo ""

# Datenbank initialisieren
echo -e "${YELLOW}💾 Datenbank initialisieren...${NC}"
cd "$PROJECT_DIR"
sudo -u "$PROJECT_USER" "$VENV_DIR/bin/python" -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('✓ Datenbank initialisiert')"
echo ""

# .env Datei erstellen falls nicht vorhanden
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}🔐 Erstelle .env Datei...${NC}"
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    
    # Generiere SECRET_KEY
    NEW_SECRET=$(python3 -c 'import os; print(os.urandom(24).hex())')
    sed -i "s/dev-secret-key-change-in-production/$NEW_SECRET/" "$PROJECT_DIR/.env"
    
    # Frage nach Admin-Passwort
    read -sp "Bitte gib ein Admin-Passwort ein: " ADMIN_PASS
    echo
    sed -i "s/change-this-password/$ADMIN_PASS/" "$PROJECT_DIR/.env"
    
    chown "$PROJECT_USER:$PROJECT_USER" "$PROJECT_DIR/.env"
    chmod 600 "$PROJECT_DIR/.env"
    echo -e "${GREEN}✓${NC} .env Datei erstellt mit sicheren Zugangsdaten"
else
    echo -e "${GREEN}✓${NC} .env Datei existiert bereits"
fi
echo ""

# Systemd Service installieren
echo -e "${YELLOW}⚙️  Systemd Service installieren...${NC}"
# Ersetze Platzhalter in Service-Datei
sed -e "s|%USER%|$PROJECT_USER|g" \
    -e "s|%INSTALL_DIR%|$PROJECT_DIR|g" \
    "$PROJECT_DIR/deployment/foodbot.service" > /etc/systemd/system/foodbot.service
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

# Cronjobs für den Projektuser hinzufügen
(sudo -u "$PROJECT_USER" crontab -l 2>/dev/null | grep -v "backup_db.py"; echo "$BACKUP_CRON") | sudo -u "$PROJECT_USER" crontab -
(sudo -u "$PROJECT_USER" crontab -l 2>/dev/null | grep -v "clear_registrations.py"; echo "$RESET_CRON") | sudo -u "$PROJECT_USER" crontab -
echo -e "${GREEN}✓${NC} Cronjobs eingerichtet"
echo ""

# Nginx installieren (optional)
echo -e "${YELLOW}🌐 Nginx (optional)...${NC}"
read -p "Möchtest du Nginx als Reverse Proxy installieren? (j/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Jj]$ ]]; then
    apt-get update
    apt-get install -y nginx
    # Ersetze Platzhalter in Nginx-Konfiguration
    sed "s|%INSTALL_DIR%|$PROJECT_DIR|g" "$PROJECT_DIR/deployment/nginx-foodbot" > /etc/nginx/sites-available/foodbot
    ln -sf /etc/nginx/sites-available/foodbot /etc/nginx/sites-enabled/foodbot
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
    systemctl enable nginx
    echo -e "${GREEN}✓${NC} Nginx installiert und konfiguriert"
else
    echo "Nginx übersprungen"
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
echo "🔐 Zugangsdaten wurden in $PROJECT_DIR/.env gespeichert"
echo "   (Zum Ändern: Bearbeite die .env Datei und starte den Service neu)"
echo ""
