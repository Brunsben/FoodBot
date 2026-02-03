# Deployment Dateien

## Service-Dateien

### `foodbot.service`
Template-Datei mit Platzhaltern (`%USER%`, `%INSTALL_DIR%`).
Wird vom `setup_production.sh` Skript automatisch konfiguriert.

### `foodbot.service.production`
Fertige Service-Datei für den Produktions-Pi (brunsben@/home/brunsben/FoodBot).

**Installation:**
```bash
sudo cp deployment/foodbot.service.production /etc/systemd/system/foodbot.service
sudo systemctl daemon-reload
sudo systemctl enable foodbot
sudo systemctl restart foodbot
```

## Andere Dateien

- `setup_production.sh` - Automatisches Setup-Skript
- `gunicorn.conf.py` - Gunicorn Konfiguration
- `nginx-foodbot` - Nginx Reverse Proxy Konfiguration
- `logrotate-foodbot` - Log-Rotation Konfiguration
