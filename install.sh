#!/bin/bash
# Installations-Skript für Raspberry Pi

echo "=== FoodBot Installation ==="

# Ermittle Projektverzeichnis
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Python und Pip prüfen
if ! command -v python3 &> /dev/null; then
    echo "Python 3 wird installiert..."
    sudo apt update
    sudo apt install -y python3 python3-pip
fi

# Dependencies installieren
echo "Installiere Python-Abhängigkeiten..."
pip3 install -r requirements.txt

# .env-Datei erstellen falls nicht vorhanden
if [ ! -f .env ]; then
    echo "Erstelle .env-Datei..."
    cp .env.example .env
    
    # Generiere SECRET_KEY
    NEW_SECRET=$(python3 -c 'import os; print(os.urandom(24).hex())')
    sed -i "s/dev-secret-key-change-in-production/$NEW_SECRET/" .env
    
    echo "Bitte bearbeite die .env-Datei und setze ein sicheres ADMIN_PASSWORD!"
fi

# Cronjob für nächtliches Reset einrichten
echo "Möchtest du einen Cronjob für das nächtliche Reset einrichten? (j/n)"
read -r response
if [[ "$response" =~ ^([jJ][aA]|[jJ])$ ]]; then
    SCRIPT_PATH="$SCRIPT_DIR"
    (crontab -l 2>/dev/null; echo "0 3 * * * cd $SCRIPT_PATH && python3 clear_registrations.py >> /var/log/foodbot.log 2>&1") | crontab -
    echo "Cronjob wurde eingerichtet (täglich um 3 Uhr)"
fi

echo ""
echo "=== Installation abgeschlossen ==="
echo "Starte die App mit: python3 app/main.py"
echo "Touch-Display: http://localhost:5000/"
echo "Küche: http://localhost:5000/kitchen"
echo "Admin: http://localhost:5000/admin"
