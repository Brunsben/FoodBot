#!/bin/bash
# Automatisches Installations-Skript für FoodBot auf Raspberry Pi

set -e  # Bei Fehler abbrechen

echo "====================================="
echo "   FoodBot Installation (Raspberry Pi)"
echo "====================================="
echo ""

# Ermittle Projektverzeichnis und aktuellen User
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CURRENT_USER=$(whoami)

cd "$SCRIPT_DIR"

echo "[1/7] System-Pakete installieren..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git

echo "[2/7] Virtual Environment erstellen..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

echo "[3/7] Python-Dependencies installieren..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "[4/7] Logs-Verzeichnis erstellen..."
mkdir -p logs

echo "[5/7] Gunicorn-Config anpassen..."
cat > app/gunicorn_config.py << 'EOF'
"""
Gunicorn Konfiguration für Raspberry Pi
"""
import os

# Server
bind = "0.0.0.0:5001"
workers = 2
worker_class = "sync"
timeout = 30
keepalive = 2

# Logging - automatische Pfaderkennung
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
accesslog = os.path.join(base_dir, "logs", "access.log")
errorlog = os.path.join(base_dir, "logs", "error.log")
loglevel = "info"

# Process
proc_name = "foodbot"
EOF

echo "[6/7] Systemd Service einrichten..."
cat > /tmp/foodbot.service << EOF
[Unit]
Description=FoodBot Essensanmeldung
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$SCRIPT_DIR
Environment="PATH=$SCRIPT_DIR/venv/bin:/usr/bin:/usr/local/bin"
ExecStart=$SCRIPT_DIR/venv/bin/gunicorn -c $SCRIPT_DIR/app/gunicorn_config.py wsgi:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/foodbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable foodbot

echo "[7/7] Service starten..."
sudo systemctl start foodbot

echo ""
echo "====================================="
echo "   Installation erfolgreich!"
echo "====================================="
echo ""
echo "FoodBot läuft jetzt auf:"
echo "  - http://$(hostname -I | awk '{print $1}'):5001"
echo "  - http://localhost:5001"
echo ""
echo "Verfügbare Seiten:"
echo "  /          - Touch-Display (RFID/Personalnummer)"
echo "  /admin     - Admin-Bereich (Passwort: feuerwehr2026)"
echo "  /kitchen   - Küchenansicht"
echo "  /mobile    - Mobile QR-Anmeldung"
echo ""
echo "Nützliche Befehle:"
echo "  sudo systemctl status foodbot   - Status prüfen"
echo "  sudo systemctl restart foodbot  - Neu starten"
echo "  sudo journalctl -u foodbot -f  - Logs anzeigen"
echo ""
echo "Update von GitHub:"
echo "  cd $SCRIPT_DIR && git pull && sudo systemctl restart foodbot"
echo ""
