#!/bin/bash
# Update-Script für Display UI-Fixes

echo "🔧 Aktualisiere FoodBot UI..."

# CSS-Datei für Chromium kopieren
CSS_FILE="/home/brunsben/FoodBot/deployment/chromium-custom.css"

# ~/.xinitrc aktualisieren mit CSS-Stylesheet
cat > ~/.xinitrc << 'EOF'
#!/bin/bash

# Screensaver und Power Management deaktivieren
xset s off
xset -dpms
xset s noblank

# Mauszeiger verstecken nach 1 Sekunde
unclutter -idle 1 -root &

# Chromium im Kiosk-Modus starten mit allen Anti-Translate-Flags
chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-translate \
    --disable-features=Translate,TranslateUI \
    --lang=de \
    --user-stylesheet="file://${CSS_FILE}" \
    --disable-popup-blocking \
    --incognito \
    http://localhost:5001/
EOF

chmod +x ~/.xinitrc

echo "✅ ~/.xinitrc aktualisiert mit CSS-Stylesheet"
echo "📝 Bitte Chromium neu starten mit: pkill chromium && startx"
