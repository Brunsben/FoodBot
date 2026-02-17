# RFID Scanner Konfiguration - F-Tasten Problem beheben

## Problem
Der TWN4 MultiTech Scanner sendet F-Tasten, die im Samsung Browser die Shortcut-Leiste öffnen.

## Lösung 1: Scanner neu konfigurieren (Empfohlen)

### Zugriff auf Scanner-Konfiguration:
1. Scanner mit PC verbinden (USB)
2. TWN4 DevPack Software öffnen: https://www.elatec-rfid.com/de/support/downloads
3. Scanner-Konfiguration öffnen

### Änderungen:
**Keyboard Wedge Modus anpassen:**
```
Keyboard Layout: Standard (kein F-Tasten-Prefix)
Prefix: <leer>
Suffix: \r (Enter)
Format: Nur Kartennummer ohne Zusatzzeichen
```

**Oder: USB-HID Modus statt Keyboard Wedge:**
- Vorteil: Sendet direkte HID-Events, keine F-Tasten
- Nachteil: Benötigt ggf. Treiber/Library

## Lösung 2: Fullscreen API (Implementiert)

Die Touch-Seite hat jetzt einen **Vollbild-Button** (unten rechts).
- Im Vollbild-Modus blockiert der Browser die F-Tasten-Leiste
- Button erscheint automatisch beim Laden
- Beim ersten Klick auf die Seite wird automatisch Fullscreen aktiviert

**Nutzer-Anleitung:**
1. Seite auf Tablet öffnen
2. Auf beliebige Stelle tippen → Fullscreen aktiviert sich
3. Falls nicht: Button "⛶ Vollbild" unten rechts drücken

## Lösung 3: Kiosk-Modus Browser

### Samsung Internet Browser Kiosk:
```bash
# Per ADB oder Samsung Knox
adb shell am start -n com.sec.android.app.sbrowser/.SBrowserMainActivity \
  --es url "http://YOUR_IP:5000" \
  --ez kiosk_mode true
```

### Chrome Kiosk auf Android:
```bash
adb shell am start -n com.android.chrome/com.google.android.apps.chrome.Main \
  -d "http://YOUR_IP:5000" \
  --activity-clear-task \
  --activity-clear-top
```

Dann Chrome Flags aktivieren:
- `chrome://flags/#enable-kiosk-mode`
- `chrome://flags/#disable-keyboard-shortcuts`

## Lösung 4: Dedizierte Kiosk-App

**Fully Kiosk Browser** (Play Store):
- Blockiert alle System-Shortcuts
- Fullscreen ohne User-Interaction
- Remote-Management möglich

```
Settings → Advanced Web Settings
☑ Block System Keys (F-Keys, Back, Home)
☑ Force Fullscreen
☑ Disable Pull-Down Menu
```

## Test nach Konfiguration

1. Scanner testen in `word` oder Notepad
2. Sollte nur Nummer + Enter senden
3. Keine F-Tasten mehr

## Support

TWN4 Hotline: support@elatec-rfid.com
Dokumentation: https://www.elatec-rfid.com/de/support/downloads
