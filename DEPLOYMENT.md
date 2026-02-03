# Deployment Guide für FoodBot

## 🚀 Deployment-Optionen

FoodBot kann auf verschiedene Arten deployed werden:

1. **Systemd Service** (empfohlen für Raspberry Pi)
2. **Docker Container** (einfaches Setup, isoliert)
3. **Manuell** (für Entwicklung)

---

## 📦 Option 1: Systemd Service (Production)

### Voraussetzungen
- Raspberry Pi OS (oder Debian/Ubuntu)
- Python 3.8+
- Root-Zugriff (sudo)

### Automatische Installation

```bash
# Projekt klonen
cd /home/pi
git clone <repository-url> FoodBot
cd FoodBot

# Setup-Skript ausführen (als root!)
sudo ./deployment/setup_production.sh
```

Das Skript installiert automatisch:
- ✅ Python Virtual Environment mit allen Paketen
- ✅ Systemd Service für automatischen Start
- ✅ Logrotate für Log-Management
- ✅ Cronjobs für Reset & Backup
- ✅ Optional: Nginx als Reverse Proxy

### Manuelle Installation

Falls du das Setup-Skript nicht nutzen möchtest:

```bash
# 1. Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Verzeichnisse erstellen
sudo mkdir -p /var/log/foodbot
sudo chown pi:pi /var/log/foodbot
mkdir -p backups

# 3. Datenbank initialisieren
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

# 4. Service installieren
sudo cp deployment/foodbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable foodbot
sudo systemctl start foodbot

# 5. Logrotate einrichten
sudo cp deployment/logrotate-foodbot /etc/logrotate.d/foodbot

# 6. Cronjobs einrichten
./deployment/setup_cronjobs.sh
```

### Service-Befehle

```bash
# Status prüfen
sudo systemctl status foodbot

# Starten/Stoppen/Neustarten
sudo systemctl start foodbot
sudo systemctl stop foodbot
sudo systemctl restart foodbot

# Logs ansehen
journalctl -u foodbot -f
tail -f /var/log/foodbot/error.log
```

### Nginx Reverse Proxy (Optional)

```bash
# Nginx installieren
sudo apt install nginx

# Konfiguration kopieren
sudo cp deployment/nginx-foodbot /etc/nginx/sites-available/foodbot
sudo ln -s /etc/nginx/sites-available/foodbot /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Nginx neu starten
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🐳 Option 2: Docker Container

### Voraussetzungen
- Docker & Docker Compose installiert

### Installation

```bash
# Repository klonen
git clone <repository-url> FoodBot
cd FoodBot

# Environment-Variablen setzen (optional)
cp .env.example .env
# Bearbeite .env und setze ADMIN_PASSWORD und SECRET_KEY

# Container bauen und starten
docker-compose up -d

# Logs ansehen
docker-compose logs -f
```

### Zugriff
- FoodBot: http://localhost:5001
- Mit Nginx: http://localhost

### Docker-Befehle

```bash
# Status prüfen
docker-compose ps

# Stoppen
docker-compose down

# Neu starten
docker-compose restart

# Logs
docker-compose logs -f foodbot

# Container neu bauen (nach Code-Änderungen)
docker-compose build
docker-compose up -d
```

### Daten-Persistenz

Die folgenden Verzeichnisse werden automatisch gemountet:
- `./data` - SQLite Datenbank
- `./backups` - Automatische Backups
- `./logs` - Application Logs

---

## 🔧 Konfiguration

### Environment-Variablen

Erstelle eine `.env` Datei oder setze die Variablen in der Service-Datei:

```bash
# Admin-Passwort (Standard: feuerwehr2026)
ADMIN_PASSWORD=dein-sicheres-passwort

# Secret Key für Sessions (WICHTIG: ändern in Production!)
SECRET_KEY=$(python3 -c 'import os; print(os.urandom(24).hex())')

# Flask Environment
FLASK_ENV=production
```

### Systemd Service editieren

```bash
sudo nano /etc/systemd/system/foodbot.service

# Nach Änderungen:
sudo systemctl daemon-reload
sudo systemctl restart foodbot
```

### Nginx anpassen

```bash
sudo nano /etc/nginx/sites-available/foodbot

# Nach Änderungen:
sudo nginx -t
sudo systemctl reload nginx
```

---

## ⏰ Automatische Aufgaben

### Cronjobs

Die Cronjobs werden automatisch eingerichtet:

```
# Anmeldungen zurücksetzen (täglich 00:00 Uhr)
0 0 * * * /home/pi/FoodBot/venv/bin/python /home/pi/FoodBot/clear_registrations.py

# Datenbank-Backup (täglich 00:30 Uhr)
30 0 * * * /home/pi/FoodBot/venv/bin/python /home/pi/FoodBot/backup_db.py
```

Prüfen mit:
```bash
crontab -l
```

Manuell bearbeiten:
```bash
crontab -e
```

---

## 📊 Monitoring

### Logs prüfen

```bash
# Application Logs
tail -f /var/log/foodbot/error.log
tail -f /var/log/foodbot/access.log

# Systemd Logs
journalctl -u foodbot -f

# Nginx Logs (falls installiert)
tail -f /var/log/nginx/foodbot_access.log
tail -f /var/log/nginx/foodbot_error.log

# Backup/Reset Logs
tail -f /var/log/foodbot/backup.log
tail -f /var/log/foodbot/reset.log
```

### Logrotate

Logs werden automatisch rotiert (täglich, 14 Tage behalten).  
Konfiguration: `/etc/logrotate.d/foodbot`

Manuell rotieren:
```bash
sudo logrotate -f /etc/logrotate.d/foodbot
```

---

## 🔒 Sicherheit

### Firewall konfigurieren

```bash
# UFW Firewall aktivieren
sudo apt install ufw
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### SSL/TLS mit Let's Encrypt (Optional)

```bash
# Certbot installieren
sudo apt install certbot python3-certbot-nginx

# Zertifikat erstellen (Domain erforderlich!)
sudo certbot --nginx -d foodbot.yourdomain.com

# Auto-Renewal ist automatisch eingerichtet
sudo certbot renew --dry-run
```

### Admin-Passwort ändern

```bash
# Systemd Service
sudo nano /etc/systemd/system/foodbot.service
# Ändere: Environment="ADMIN_PASSWORD=neues-passwort"
sudo systemctl daemon-reload
sudo systemctl restart foodbot

# Docker
# Ändere ADMIN_PASSWORD in .env
docker-compose restart
```

---

## 🛠️ Wartung

### Backup manuell erstellen

```bash
python backup_db.py
```

Backups landen in: `/home/pi/FoodBot/backups/`

### Backup wiederherstellen

```bash
# Service stoppen
sudo systemctl stop foodbot

# Backup kopieren
cp backups/foodbot_backup_YYYYMMDD_HHMMSS.db data/registrations.db

# Service starten
sudo systemctl start foodbot
```

### Datenbank zurücksetzen

```bash
# WARNUNG: Löscht alle Anmeldungen!
python clear_registrations.py
```

### Updates installieren

```bash
cd /home/pi/FoodBot
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart foodbot
```

---

## 🐛 Troubleshooting

### Service startet nicht

```bash
# Status prüfen
sudo systemctl status foodbot

# Logs prüfen
journalctl -u foodbot -n 50

# Manuelle Tests
cd /home/pi/FoodBot
source venv/bin/activate
gunicorn -c deployment/gunicorn.conf.py "app:create_app()"
```

### RFID funktioniert nicht

```bash
# Device prüfen
ls -l /dev/ttyUSB*

# Berechtigungen prüfen
sudo usermod -a -G dialout pi
# Danach neu anmelden!

# Test
python -c "import serial; print(serial.Serial('/dev/ttyUSB0'))"
```

### Nginx 502 Bad Gateway

```bash
# Ist der FoodBot-Service aktiv?
sudo systemctl status foodbot

# Lauscht Gunicorn auf Port 5001?
sudo netstat -tlnp | grep 5001

# Nginx Fehler-Log
tail -f /var/log/nginx/foodbot_error.log
```

### Cronjobs laufen nicht

```bash
# Cronjobs prüfen
crontab -l

# Cron-Service prüfen
sudo systemctl status cron

# Logs prüfen
tail -f /var/log/foodbot/backup.log
tail -f /var/log/foodbot/reset.log

# Manuell testen
/home/pi/FoodBot/venv/bin/python /home/pi/FoodBot/backup_db.py
```

---

## 📱 Zugriff

Nach erfolgreichem Setup:

### Lokales Netzwerk
- Touch-Interface: `http://<raspberry-pi-ip>:5001`
- Kitchen-View: `http://<raspberry-pi-ip>:5001/kitchen`
- Admin-Panel: `http://<raspberry-pi-ip>:5001/admin`
- Historie: `http://<raspberry-pi-ip>:5001/history`

### Mit Nginx
- Alle Interfaces: `http://<raspberry-pi-ip>`

### IP-Adresse finden
```bash
hostname -I
```

---

## 📞 Support

Bei Problemen:
1. Logs prüfen (siehe Monitoring-Sektion)
2. Troubleshooting-Sektion durchgehen
3. Service-Status prüfen: `sudo systemctl status foodbot`
4. GitHub Issues öffnen

---

## 🎯 Checkliste für Production

- [ ] Admin-Passwort geändert
- [ ] SECRET_KEY generiert und gesetzt
- [ ] Systemd Service läuft
- [ ] Cronjobs eingerichtet und getestet
- [ ] Logrotate konfiguriert
- [ ] Nginx installiert (optional)
- [ ] Firewall konfiguriert
- [ ] Erster Backup erfolgreich
- [ ] RFID-Reader getestet
- [ ] Alle Interfaces erreichbar
- [ ] SSL/TLS eingerichtet (optional)

---

**🚒 Viel Erfolg mit dem FoodBot! 🚒**
