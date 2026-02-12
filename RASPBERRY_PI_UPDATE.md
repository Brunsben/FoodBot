# 🔧 Raspberry Pi Update-Anleitung

## Nach Security-Update auf dem Raspberry Pi ausführen

### 1️⃣ SSH zum Raspberry Pi
```bash
ssh pi@foodbot.ddns.me
cd /home/pi/FoodBot  # oder dein Installations-Pfad
```

### 2️⃣ Code aktualisieren
```bash
git pull
```

### 3️⃣ Dependencies installieren
```bash
source venv/bin/activate  # oder: . venv/bin/activate
pip install -r requirements.txt
```

### 4️⃣ .env-Datei erstellen (WICHTIG!)
```bash
# .env.example als Vorlage kopieren
cp .env.example .env

# SECRET_KEY generieren und einfügen
echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" >> .env
echo "ADMIN_PASSWORD=DeinSicheresPasswort123" >> .env
echo "FLASK_ENV=production" >> .env

# .env-Datei prüfen
cat .env
```

### 5️⃣ Service neu starten
```bash
sudo systemctl restart foodbot
sudo systemctl status foodbot
```

### 6️⃣ Logs prüfen (bei Problemen)
```bash
# Service-Logs
sudo journalctl -u foodbot -n 50 -f

# Gunicorn-Logs
tail -f /var/log/foodbot/error.log
tail -f /var/log/foodbot/access.log
```

---

## 🔒 Was wurde geändert?

**Breaking Changes:**
- `.env`-Datei mit `SECRET_KEY` und `ADMIN_PASSWORD` ist jetzt **PFLICHT**
- Keine Default-Secrets mehr im Code
- Flask-WTF für CSRF-Schutz (neue Dependency)

**Neue Security-Features:**
- ✅ CSRF-Protection
- ✅ Sichere Session-Cookies (HTTPONLY, SECURE, SAMESITE)
- ✅ Rate-Limiting auf Login (5 Versuche/Minute)
- ✅ Timing-sichere Passwortprüfung
- ✅ Input-Validierung
- ✅ N+1 Query-Optimierung

---

## ❌ Fehlerbehebung

### Error: "ValueError: SECRET_KEY muss in .env gesetzt werden"
→ `.env`-Datei fehlt oder `SECRET_KEY` ist leer
→ Siehe Schritt 4

### Service startet nicht
```bash
# Status prüfen
sudo systemctl status foodbot

# Vollständige Logs
sudo journalctl -xe -u foodbot

# Manuell testen
cd /home/pi/FoodBot
source venv/bin/activate
gunicorn -c app/gunicorn_config.py wsgi:app
```

### Port 8080 nicht erreichbar
```bash
# Prüfe ob Service läuft
sudo lsof -i :5001

# Prüfe nginx
sudo systemctl status nginx
sudo nginx -t

# Firewall prüfen
sudo ufw status
```

### ModuleNotFoundError: flask_wtf
```bash
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart foodbot
```
