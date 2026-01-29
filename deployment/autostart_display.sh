#!/bin/bash
# Autostart-Skript für FoodBot Touch-Display
# Startet Chromium im Kiosk-Modus für das Touch-Display

# Warte bis der Service läuft
sleep 10

# Deaktiviere Bildschirmschoner
xset s off
xset -dpms
xset s noblank

# Verstecke Mauszeiger nach 5 Sekunden Inaktivität
unclutter -idle 5 &

# Chromium im Kiosk-Modus starten
chromium-browser \
  --kiosk \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --disable-features=TranslateUI \
  --check-for-update-interval=604800 \
  --start-fullscreen \
  http://localhost:5001/
