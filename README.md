# 🚒 FoodBot - Feuerwehr Essensanmeldung

Ein System zur Essensanmeldung für die Feuerwehr, optimiert für den Raspberry Pi mit 3,5" Touchscreen.

## ✨ Features

### Registrierung
- 🆔 **RFID-Transponder**: Automatische Anmeldung per ELATEC TWN4 HID Reader
- 📱 **QR-Code**: Persönlicher QR-Code für jeden User zum Ausdrucken
- 🔢 **Personalnummer**: Manuelle Eingabe am Touchscreen mit eingebetteter Tastatur
- 👥 **Gäste**: Schnelle +/- Buttons für Besucher ohne Account

### Menüverwaltung
- 🍽️ **Zwei-Menü-System**: Optional zwei verschiedene Menüs pro Tag
- 📝 **Menü-Auswahl**: Benutzer wählen bei Anmeldung ihr Wunschmenü
- 📊 **Getrennte Zählung**: Separate Anzeige für Menü 1 und Menü 2
- ✅ **Farbcodierte Bestätigung**: Grün für Anmeldung, Rot für Abmeldung

### Interfaces
- 📱 **Touch-Display** (3,5" 320x480): Modernes Dark-Theme mit Card-Layout, optimiert für Raspberry Pi
- 🍽️ **Küchenansicht**: Große Teilnehmerzahl-Anzeige, Menü-Breakdown, alphabetische Namensliste (Auto-Refresh 10s)
- ⚙️ **Admin-Panel**: Card-basiertes Design, Drag & Drop CSV-Import, Beispiel-CSV-Download, manuelle Registrierung
- 📊 **Statistiken**: 14-Tage-Übersicht, CSV-Export, geschützt durch Login
- 📈 **Historie**: Top-10-Esser, persönliche Statistiken (90/30/7 Tage), monatliche Übersicht

### Security & Performance
- 🔐 **Admin-Login**: Session-basierte Authentifizierung (Standard-Passwort: feuerwehr2026)
- ⚡ **Rate Limiting**: Schutz vor API-Missbrauch (200/Tag, 50/Stunde)
- 📝 **Logrotate**: Automatische Log-Verwaltung (täglich, 14 Tage Retention)
- 🔔 **Webhooks**: Benachrichtigungen via Slack, Discord, etc.
- 🔌 **REST-API**: Integration mit externen Systemen (z.B. FeuerON)

### Automation
- 💾 **Auto-Backup**: Tägliches Datenbank-Backup (00:30 Uhr)
- 🌙 **Auto-Reset**: Anmeldungen werden täglich gelöscht (00:00 Uhr)
- ⏰ **Cronjobs**: Vollständig konfigurierte automatische Aufgaben

### Design
- 🎨 **Modernes Dark-Theme**: CSS-Variablen, Gradients, Card-basiertes Layout
- 📐 **Touch-optimiert**: Große Buttons, kompakte Tastatur, optimiert für 320px Display
- 📱 **Responsive**: Grid-Layout passt sich an alle Bildschirmgrößen an
- ⚡ **Hover-Effekte**: Smooth Transitions und visuelle Feedbacks

## 🚀 Installation

### Option 1: Automatisches Setup (empfohlen)

Für Production-Deployment auf Raspberry Pi:

```bash
# Repository klonen
cd /home/pi
git clone https://github.com/Brunsben/FoodBot
cd FoodBot

# Automatisches Setup (als root)
sudo ./deployment/setup_production.sh
```

Das Skript installiert:
- ✅ Python Virtual Environment + Dependencies
- ✅ Systemd Service für automatischen Start
- ✅ Logrotate Konfiguration
- ✅ Cronjobs für Backup & Reset
- ✅ Optional: Nginx Reverse Proxy

**📖 Ausführliche Deployment-Anleitung: [DEPLOYMENT.md](DEPLOYMENT.md)**

### Option 2: Docker

```bash
git clone <repository-url> FoodBot
cd FoodBot
docker-compose up -d
```

### Option 3: Manuelle Installation

```bash
# Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Datenbank initialisieren
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

# Starten
gunicorn -c deployment/gunicorn.conf.py "app:create_app()"
```

## 🖥️ Interfaces

Nach der Installation erreichbar unter:

- **Touch-Display**: `http://<raspberry-pi>:5001/` - Hauptinterface für Anmeldung
- **Küchenansicht**: `http://<raspberry-pi>:5001/kitchen` - Für Tablet/PC in der Küche
- **Admin-Panel**: `http://<raspberry-pi>:5001/admin` - Benutzerverwaltung (Login erforderlich)
- **Statistiken**: `http://<raspberry-pi>:5001/stats` - Auswertungen (Login erforderlich)
- **Historie**: `http://<raspberry-pi>:5001/history` - Essenshistorie & Top-10 (Login erforderlich)

### 🔐 Standard-Login
- **Passwort**: `feuerwehr2026`
- Ändern via Environment-Variable: `ADMIN_PASSWORD=dein-passwort`

## 🔌 REST-API

Die API ist erreichbar unter `/api/` und bietet folgende Endpoints:

### Status abrufen
```bash
GET /api/status
```
Gibt aktuelles Menü, Anzahl Anmeldungen und Gäste zurück.

**Rate Limit**: 30 Requests/Minute

### An-/Abmelden
```bash
POST /api/register
Content-Type: application/json

{
  "personal_number": "12345"
}
```

**Rate Limit**: 10 Requests/Minute

### Statistiken
```bash
GET /api/stats?days=7
```

### Benutzerliste
```bash
GET /api/users
```

## ⚙️ Konfiguration

### Environment-Variablen

Erstelle eine `.env`-Datei oder setze die Variablen im System:

```bash
# Admin-Passwort (Standard: feuerwehr2026)
ADMIN_PASSWORD=dein-sicheres-passwort

# Secret Key für Sessions (WICHTIG in Production!)
SECRET_KEY=$(python3 -c 'import os; print(os.urandom(24).hex())')

# Flask Environment
FLASK_ENV=production

# RFID-Port (optional, Standard: /dev/ttyUSB0)
RFID_PORT=/dev/ttyUSB0

# Webhook für Benachrichtigungen (optional)
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Systemd Service verwalten

```bash
# Status prüfen
sudo systemctl status foodbot

# Starten/Stoppen/Neustarten
sudo systemctl start foodbot
sudo systemctl stop foodbot
sudo systemctl restart foodbot

# Logs ansehen
journalctl -u foodbot -f
```

Beispiel:
```bash
curl http://localhost:5000/api/status
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"personal_number": "12345"}'
```

## 📁 Projektstruktur

```
FoodBot/
├── app/
│   ├── __init__.py           # Flask App Factory
│   ├── models.py             # Datenbank-Modelle (User, Registration, Menu, AdminLog)
│   ├── routes.py             # Hauptrouten (Touch, Kitchen, Admin)
│   ├── api.py                # REST API mit Rate Limiting
│   ├── stats.py              # Statistik-Routes
│   ├── history.py            # Essenshistorie & Top-10
│   ├── auth.py               # Admin-Authentifizierung
│   ├── rfid.py               # RFID-Reader Integration (optional)
│   └── gunicorn_config.py    # Gunicorn für Docker
├── templates/
│   ├── touch.html            # 3,5" Touch-Interface (modernes Dark-Theme)
│   ├── kitchen.html          # Küchenansicht (Card-Layout)
│   ├── admin.html            # Admin-Panel (Drag & Drop CSV-Import)
│   ├── stats.html            # Statistiken
│   ├── history.html          # Historie-Übersicht
│   ├── history_detail.html   # User-Detail-Historie
│   ├── *_modern.html         # Moderne Design-Varianten (Backup)
│   └── *_old.html            # Legacy-Templates (Backup)
├── deployment/
│   ├── setup_production.sh   # Automatisches Production-Setup
│   ├── setup_cronjobs.sh     # Cronjob-Installation
│   ├── gunicorn.conf.py      # Gunicorn Konfiguration
│   ├── foodbot.service       # Systemd Service
│   ├── nginx-foodbot         # Nginx Reverse Proxy Config
│   ├── logrotate-foodbot     # Log-Rotation Config
│   └── DISPLAY_SETUP.md      # 3,5" Display Konfiguration (LCD-show)
├── backup_db.py              # Automatisches Datenbank-Backup
├── clear_registrations.py    # Täglich Anmeldungen löschen
├── docker-compose.yml        # Docker Deployment
├── Dockerfile                # Container-Image
├── requirements.txt          # Python Dependencies
├── README.md                 # Diese Datei
└── DEPLOYMENT.md             # Ausführliche Deployment-Anleitung
```

## 🛠️ Wartung

### Backups

Backups werden automatisch täglich um 00:30 Uhr erstellt:
- Speicherort: `/home/pi/FoodBot/backups/`
- Format: `foodbot_backup_YYYYMMDD_HHMMSS.db`
- Manuell: `python backup_db.py`

### Logs

```bash
# Application Logs
tail -f /var/log/foodbot/error.log
tail -f /var/log/foodbot/access.log

# Systemd Logs
journalctl -u foodbot -f

# Backup/Reset Logs
tail -f /var/log/foodbot/backup.log
tail -f /var/log/foodbot/reset.log
```

### Datenbank zurücksetzen

```bash
# WARNUNG: Löscht alle Anmeldungen des heutigen Tages!
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

## 📊 CSV-Import

Im Admin-Panel können Benutzer per CSV importiert werden.

**Format:**
```csv
Name,Personalnummer,Karte
Max Mustermann,12345,ABC1234
Erika Musterfrau,23456,XYZ5678
```

Oder englisch:
```csv
name,personal_number,card_id
```

Die Karten-ID (RFID) ist optional.

## 🔔 Benachrichtigungen

FoodBot kann Webhooks senden (Slack, Discord, Teams):

**Konfiguration:**
```bash
NOTIFICATIONS_ENABLED=true
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Events:**
- ✅ Neue Anmeldung
- ⚠️ Niedrige Teilnehmerzahl (< 5)
- 🔥 Hohe Teilnehmerzahl (> 30)

## 🐛 Troubleshooting

### Service startet nicht
```bash
sudo systemctl status foodbot
journalctl -u foodbot -n 50
```

### RFID funktioniert nicht
```bash
# Device prüfen
ls -l /dev/ttyUSB*

# Berechtigungen
sudo usermod -a -G dialout pi
# Neu anmelden!
```

### Nginx 502 Bad Gateway
```bash
# Service aktiv?
sudo systemctl status foodbot

# Port 5001 lauscht?
sudo netstat -tlnp | grep 5001
```

**Mehr Hilfe:** [DEPLOYMENT.md - Troubleshooting](DEPLOYMENT.md#-troubleshooting)

## 📝 Technische Details

### Stack
- **Backend**: Python 3.11+, Flask 3.1
- **Datenbank**: SQLite mit SQLAlchemy 2.0
- **Server**: Gunicorn mit 4 Workern (Production)
- **Reverse Proxy**: Nginx (optional)
- **Hardware**: Raspberry Pi 4, ELATEC TWN4 HID RFID Reader, 3,5" ILI9486 Touchscreen (320x480)
- **Display**: LCD-show Treiber für SPI-basierte Displays

### Design System
- **CSS**: CSS Custom Properties (Variablen)
- **Layout**: CSS Grid & Flexbox
- **Theme**: Dark Mode (#0f172a Base, #dc2626 Primary, #10b981 Success)
- **Typography**: System Fonts (-apple-system, BlinkMacSystemFont, Segoe UI)
- **Components**: Card-basiert, Gradients, Shadow-Effekte

### Dependencies
- `flask` - Web Framework
- `flask-sqlalchemy` - ORM
- `flask-limiter` - Rate Limiting
- `pyserial` - RFID-Reader Kommunikation
- `qrcode[pil]` - QR-Code Generierung
- `gunicorn` - WSGI Server
- `python-dotenv` - Environment Configuration

### Security Features
- ✅ Session-basierte Admin-Authentifizierung
- ✅ Rate Limiting auf API-Endpoints
- ✅ CSRF-Protection (Flask-WTF)
- ✅ Prepared Statements (SQLAlchemy)
- ✅ Input Validation

## 📄 Lizenz

MIT License - Frei verwendbar für private und kommerzielle Projekte.

## 🤝 Beitragen

Pull Requests sind willkommen! Für größere Änderungen bitte zuerst ein Issue öffnen.

## 📞 Support

Bei Problemen:
1. [DEPLOYMENT.md](DEPLOYMENT.md) lesen
2. Logs prüfen (siehe Wartung)
3. GitHub Issue öffnen

---

**🚒 Entwickelt für die Feuerwehr - Mit ❤️ und Python 🚒**
