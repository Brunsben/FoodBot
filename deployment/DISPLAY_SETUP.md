# FoodBot Touch-Display Setup

## Voraussetzungen

Auf dem Raspberry Pi muss eine Desktop-Umgebung installiert sein:
- Raspberry Pi OS (mit Desktop)
- X Server läuft
- Chromium Browser installiert

## Installation

### 1. Benötigte Pakete installieren

```bash
sudo apt update
sudo apt install -y chromium-browser unclutter
```

### 2. Autostart einrichten

#### Methode A: LXDE Autostart (Standard bei Raspberry Pi OS)

```bash
# Erstelle Autostart-Verzeichnis falls nicht vorhanden
mkdir -p ~/.config/lxsession/LXDE-pi

# Bearbeite autostart
nano ~/.config/lxsession/LXDE-pi/autostart
```

Füge folgende Zeilen hinzu:

```bash
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 5
@chromium-browser --kiosk --noerrdialogs --disable-infobars --start-fullscreen http://localhost:5001/
```

#### Methode B: Verwende das mitgelieferte Skript

```bash
# Skript ausführbar machen
chmod +x ~/FoodBot/deployment/autostart_display.sh

# In Autostart eintragen
mkdir -p ~/.config/lxsession/LXDE-pi
echo "@/home/brunsben/FoodBot/deployment/autostart_display.sh" >> ~/.config/lxsession/LXDE-pi/autostart
```

### 3. Raspberry Pi neu starten

```bash
sudo reboot
```

Nach dem Neustart sollte automatisch die FoodBot-Webseite im Vollbildmodus angezeigt werden.

## Fehlerbehebung

### Display zeigt nichts an

1. Prüfe ob der Desktop läuft:
```bash
echo $DISPLAY
# Sollte :0 oder ähnlich ausgeben
```

2. Prüfe ob Chromium installiert ist:
```bash
which chromium-browser
```

3. Prüfe ob FoodBot läuft:
```bash
sudo systemctl status foodbot
curl http://localhost:5001
```

### Chromium beenden (für Wartung)

```bash
# Von einem anderen Terminal/SSH:
killall chromium-browser

# Oder Alt+F4 auf der Tastatur
```

### Bildschirmschoner deaktiviert sich nicht

```bash
# Zusätzlich in /etc/X11/xorg.conf (falls vorhanden):
Section "ServerLayout"
    Identifier "ServerLayout0"
    Option "BlankTime" "0"
    Option "StandbyTime" "0"
    Option "SuspendTime" "0"
    Option "OffTime" "0"
EndSection
```

## Alternativen

### Firefox statt Chromium

```bash
sudo apt install firefox-esr

# In autostart:
@firefox --kiosk http://localhost:5001/
```

### Kweb (Minimaler Browser für Pi)

```bash
wget http://steinerdatenbank.de/software/kweb-1.7.9.5.tar.gz
tar -xzf kweb-1.7.9.5.tar.gz
sudo mv kweb-1.7.9.5/kweb /usr/bin/

# In autostart:
@kweb -KJEHSA http://localhost:5001/
```

## Touch-Kalibrierung (falls nötig)

```bash
sudo apt install xinput-calibrator
xinput_calibrator
```

Folge den Anweisungen und speichere die Konfiguration in:
`/usr/share/X11/xorg.conf.d/99-calibration.conf`
