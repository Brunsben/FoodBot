# No-IP Setup für FoodBot

## Vorbereitung erledigt ✅

Der Code ist bereits vorbereitet und verwendet automatisch die `BASE_URL` aus der `.env`-Datei für alle QR-Codes.

## Setup auf dem Raspberry Pi

### 1. No-IP Dynamic Update Client installieren

```bash
# In temporäres Verzeichnis wechseln
cd /tmp

# No-IP Client herunterladen
wget http://www.no-ip.com/client/linux/noip-duc-linux.tar.gz

# Entpacken
tar xzf noip-duc-linux.tar.gz
cd noip-2.1.9-1/

# Kompilieren und installieren
sudo make
sudo make install
```

Während der Installation:
- **Email**: Deine No-IP Email-Adresse
- **Password**: Dein No-IP Passwort
- **Hostname**: Wähle deinen erstellten Hostname aus
- **Update interval**: 30 (Minuten) ist Standard

### 2. No-IP Client als Service einrichten

```bash
# Service erstellen
sudo nano /etc/systemd/system/noip2.service
```

Inhalt der Datei:
```ini
[Unit]
Description=No-IP Dynamic DNS Update Client
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/bin/noip2
Restart=always

[Install]
WantedBy=multi-user.target
```

Service aktivieren:
```bash
sudo systemctl enable noip2
sudo systemctl start noip2
sudo systemctl status noip2
```

### 3. Router konfigurieren

Port-Forwarding einrichten:
- **Externer Port**: 80
- **Interner Port**: 80 (oder 5001 für Test)
- **IP-Adresse**: Raspberry Pi IP (z.B. 192.168.1.100)
- **Protokoll**: TCP

**Hinweis**: Die genaue Vorgehensweise variiert je nach Router-Modell.

### 4. BASE_URL in FoodBot konfigurieren

```bash
cd /pfad/zu/foodBot
cp .env.example .env
nano .env
```

In der `.env` die BASE_URL anpassen:
```bash
BASE_URL=http://dein-hostname.no-ip.org
```

**Wichtig**: 
- Mit `http://` oder `https://` (bei SSL)
- Ohne abschließenden Slash

### 5. FoodBot neu starten

```bash
# Wenn als Service
sudo systemctl restart foodbot

# Oder manuell
pkill -f "python.*run.py"
python3 run.py
```

### 6. Testen

1. **Von außerhalb des Netzwerks**:
   - Mit Smartphone (mobile Daten, kein WLAN)
   - Öffne: `http://dein-hostname.no-ip.org`

2. **QR-Code prüfen**:
   - Im Admin-Bereich QR-Code öffnen
   - URL sollte mit deinem No-IP Hostname beginnen

## SSL/HTTPS einrichten (Optional aber empfohlen)

### Mit Let's Encrypt (kostenlos):

```bash
# Certbot installieren
sudo apt install certbot python3-certbot-nginx

# Nginx konfigurieren (siehe deployment/nginx-foodbot)
sudo certbot --nginx -d dein-hostname.no-ip.org
```

Dann in `.env`:
```bash
BASE_URL=https://dein-hostname.no-ip.org
```

## Troubleshooting

### No-IP Client läuft nicht
```bash
# Status prüfen
sudo systemctl status noip2

# Logs anschauen
journalctl -u noip2 -f

# Manuell starten zum Testen
sudo /usr/local/bin/noip2 -d
```

### Keine Verbindung von außen

1. **IP-Adresse prüfen**:
   ```bash
   curl ifconfig.me
   # Muss mit No-IP Hostname-IP übereinstimmen
   ```

2. **Port offen prüfen**:
   - Online Tool: https://www.yougetsignal.com/tools/open-ports/
   - Port 80 eingeben

3. **Firewall auf Raspberry Pi**:
   ```bash
   sudo ufw status
   sudo ufw allow 80/tcp
   ```

### QR-Codes zeigen falsche URL

```bash
# .env prüfen
cat .env | grep BASE_URL

# FoodBot neu starten nach Änderung
sudo systemctl restart foodbot
```

## Sicherheitshinweise

⚠️ **Wichtig bei öffentlichem Zugriff**:

1. **Starkes Admin-Passwort** in `.env` setzen:
   ```bash
   ADMIN_PASSWORD=Sehr-Sicheres-Passwort-123!
   ```

2. **SSL verwenden** (Let's Encrypt siehe oben)

3. **Rate Limiting** ist bereits aktiv (50 Anfragen/Stunde)

4. **Regelmäßige Updates**:
   ```bash
   sudo apt update && sudo apt upgrade
   ```

5. **Fail2Ban** installieren (optional):
   ```bash
   sudo apt install fail2ban
   ```

## Kosten

- **No-IP Free**: Kostenlos, Hostname muss alle 30 Tage bestätigt werden
- **No-IP Plus** (~25$/Jahr): Automatische Bestätigung, mehr Hostnames
- **SSL-Zertifikat**: Kostenlos mit Let's Encrypt

## Alternative: Cloudflare Tunnel (Zero Trust)

Falls Port-Forwarding nicht möglich:
```bash
# Cloudflare Tunnel = kein Port-Forwarding nötig
# Anleitung: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
```

---

Bei Fragen oder Problemen beim Setup, einfach melden! 🚀
