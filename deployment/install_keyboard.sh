#!/bin/bash
# Finale UI-Fixes und Bildschirmtastatur-Installation

echo "🔧 Installiere Bildschirmtastatur und aktualisiere UI..."

# matchbox-keyboard installieren (kleine Touch-Tastatur)
sudo apt-get update
sudo apt-get install -y matchbox-keyboard

echo "✅ matchbox-keyboard installiert"

# Automatisches Starten der Tastatur bei Input-Focus
cat > ~/.matchbox/keyboard.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<keyboard>
  <options>
    <font>Sans 20</font>
    <row>
      <key>1</key>
      <key>2</key>
      <key>3</key>
    </row>
    <row>
      <key>4</key>
      <key>5</key>
      <key>6</key>
    </row>
    <row>
      <key>7</key>
      <key>8</key>
      <key>9</key>
    </row>
    <row>
      <key>0</key>
      <key fill="2">Backspace</key>
    </row>
  </options>
</keyboard>
EOF

mkdir -p ~/.matchbox
chmod +x ~/.matchbox/keyboard.xml

# Aktualisiere xinitrc um Tastatur im Hintergrund zu starten
cat > ~/.xinitrc << 'EOF'
#!/bin/bash

# Screensaver und Power Management deaktivieren
xset s off
xset -dpms
xset s noblank

# Mauszeiger verstecken nach 1 Sekunde
unclutter -idle 1 -root &

# Bildschirmtastatur starten (versteckt, öffnet sich bei Input-Focus)
matchbox-keyboard -d &

# Chromium im Kiosk-Modus starten
chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-translate \
    --disable-features=Translate,TranslateUI \
    --lang=de \
    --disable-popup-blocking \
    --incognito \
    http://localhost:5001/
EOF

chmod +x ~/.xinitrc

echo "✅ Alle Updates abgeschlossen!"
echo "📝 Bitte System neu starten: sudo reboot"
echo ""
echo "Nach dem Neustart:"
echo "- Feuerwehr-Icon wird als SVG angezeigt"
echo "- Google Translate Leiste ist weg"
echo "- Bildschirmtastatur öffnet sich bei Personalnummer-Eingabe"
