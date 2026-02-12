# FoodBot Installation auf Raspberry Pi

## Schnellinstallation (Ein Befehl!)

```bash
git clone https://github.com/Brunsben/FoodBot.git && cd FoodBot && chmod +x install.sh && ./install.sh
```

Das war's! Das Skript erledigt automatisch:
- ✅ System-Pakete installieren
- ✅ Virtual Environment erstellen
- ✅ Dependencies installieren
- ✅ Logs-Verzeichnis anlegen
- ✅ Gunicorn konfigurieren
- ✅ Systemd Service einrichten
- ✅ Service automatisch starten

Nach der Installation ist FoodBot erreichbar unter:
- `http://<raspberry-ip>:5001`

## Update von GitHub

```bash
cd ~/FoodBot
git pull
sudo systemctl restart foodbot
```

## Nützliche Befehle

```bash
# Status prüfen
sudo systemctl status foodbot

# Service neu starten
sudo systemctl restart foodbot

# Logs live anzeigen
sudo journalctl -u foodbot -f

# Service stoppen
sudo systemctl stop foodbot

# Service deaktivieren (startet nicht mehr automatisch)
sudo systemctl disable foodbot
```

## Manuelle Installation (falls gewünscht)

Falls du die Installation Schritt für Schritt durchführen möchtest:

```bash
# 1. Repository klonen
git clone https://github.com/Brunsben/FoodBot.git
cd FoodBot

# 2. System-Pakete
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git

# 3. Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 4. Dependencies
pip install -r requirements.txt

# 5. Logs-Verzeichnis
mkdir -p logs

# 6. Service einrichten
sudo cp foodbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable foodbot
sudo systemctl start foodbot
```

## Fehlerbehebung

**Service startet nicht:**
```bash
sudo journalctl -u foodbot -n 50 --no-pager
```

**Port bereits belegt:**
```bash
sudo lsof -i :5001
# Prozess beenden:
sudo kill -9 <PID>
```

**Berechtigungsprobleme:**
```bash
sudo chown -R $USER:$USER ~/FoodBot
```
