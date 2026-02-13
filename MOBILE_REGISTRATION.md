# 📱 Mobile Essensanmeldung

## Übersicht

Die mobile Essensanmeldung ermöglicht es Kameraden, sich bequem von ihrem Smartphone aus zum Essen an- und abzumelden, ohne RFID-Karte oder Zugang zum Touch-Display zu benötigen.

## Funktionsweise

Jeder Benutzer erhält einen persönlichen QR-Code mit einem einzigartigen, sicheren Token. Dieser QR-Code kann:
- **Gedruckt** und verteilt werden
- **Per E-Mail** verschickt werden (zukünftige Funktion)
- **Im Spind** aufbewahrt werden

## QR-Codes generieren und verteilen

### Im Adminbereich

1. Gehe zu **http://localhost:5001/admin** (Passwort: `feuerwehr2026`)
2. In der Benutzertabelle findest du bei jedem User ein **📱**-Symbol in der "QR"-Spalte
3. Klicke auf das Symbol, um den persönlichen QR-Code anzuzeigen
4. Nutze die **"🖨️ Drucken"**-Funktion zum Ausdrucken

### QR-Code Seite

Die QR-Code-Seite zeigt:
- Name des Benutzers
- Personalnummer
- QR-Code zum Scannen
- Mobile URL (für manuelles Kopieren)

## Nutzung für Kameraden

### 1. QR-Code scannen
- Smartphone-Kamera auf QR-Code richten
- Oder QR-Scanner-App nutzen
- Auf den Link tippen, der angezeigt wird

### 2. Mobile Anmeldeseite
Die mobile Seite zeigt:
- **Aktuelles Menü** des Tages
- **Anmeldestatus** (angemeldet/nicht angemeldet)
- Bei zwei Menüs: Auswahl zwischen Menü 1 und Menü 2

### 3. An- oder Abmelden
- **Anmelden**: Große rote Buttons für Menü 1 oder Menü 2
- **Abmelden**: Grauer "Abmelden"-Button (wenn bereits angemeldet)
- Bestätigung wird nach jeder Aktion angezeigt

## Zwei-Menü-System

Wenn die Küche zwei Menüs anbietet:
- Der Kamerad sieht beide Menüoptionen
- Separate Buttons: "Anmelden für Menü 1" und "Anmelden für Menü 2"
- Die Menübeschreibung wird direkt auf dem Button angezeigt
- Nach Anmeldung wird angezeigt, für welches Menü man angemeldet ist

## Sicherheit

- **Einzigartige Tokens**: Jeder Benutzer hat einen 64-Zeichen langen, kryptografisch sicheren Token
- **Keine Passwörter erforderlich**: Der Link selbst dient als Authentifizierung
- **Tokens sind persistent**: Einmal generiert, bleiben sie gültig

## Technische Details

### URL-Format
```
http://[SERVER-ADRESSE]/m/[BENUTZER-TOKEN]
```

Beispiel:
```
http://192.168.1.100:5001/m/xY7k2P9mN4qR8tL6wS3vH1jF5bC0aZ9e
```

### Token-Generierung
- Tokens werden automatisch beim ersten Aufruf des QR-Codes generiert
- Verwendet `secrets.token_urlsafe(32)` für maximale Sicherheit
- Werden in der Datenbank gespeichert (Spalte: `mobile_token`)

### Datenbankstruktur
```sql
ALTER TABLE user ADD COLUMN mobile_token VARCHAR(64) UNIQUE;
```

## Vorteile

✅ **Einfach**: QR-Code scannen und fertig  
✅ **Schnell**: Ein Klick zum An-/Abmelden  
✅ **Mobil**: Von überall erreichbar (bei Netzwerkzugang)  
✅ **Barrierefrei**: Große Buttons, klare Beschriftung  
✅ **Flexibel**: Funktioniert mit Ein- und Zwei-Menü-System  

## Workflow-Beispiele

### Erstmalige Einrichtung
1. Admin generiert QR-Code im Adminbereich
2. QR-Code wird ausgedruckt oder per E-Mail verschickt
3. Kamerad scannt QR-Code und speichert Link als Lesezeichen
4. Ab jetzt: Direkt über Lesezeichen zum Essen an-/abmelden

### Tägliche Nutzung
1. Kamerad öffnet gespeicherten Link auf dem Smartphone
2. Sieht aktuelles Menü des Tages
3. Tippt auf "Anmelden" (oder wählt Menü bei zwei Optionen)
4. Erhält sofortige Bestätigung
5. Fertig! ✅

### Kurzfristige Änderung
1. Kamerad hat sich angemeldet, kann aber nicht kommen
2. Öffnet mobile Seite
3. Tippt auf "Abmelden"
4. Bestätigung erscheint
5. Küche sieht aktualisierte Anzahl

## Browser-Kompatibilität

Die mobile Seite ist optimiert für:
- ✅ Safari (iOS)
- ✅ Chrome (Android)
- ✅ Firefox Mobile
- ✅ Edge Mobile
- ✅ Samsung Internet

## Offline-Funktionalität

⚠️ **Hinweis**: Mobile Anmeldung benötigt Netzwerkverbindung zum FoodBot-Server.

Für zukünftige Versionen geplant:
- PWA (Progressive Web App) für Offline-Caching
- Push-Benachrichtigungen für Menüänderungen

## Fehlerbehebung

### "Ungültiger Link"
- Token wurde möglicherweise zurückgesetzt
- Neuen QR-Code im Adminbereich generieren

### Seite lädt nicht
- Prüfen, ob Server erreichbar ist
- WLAN-Verbindung überprüfen
- Bei externem Zugriff: Firewall-Einstellungen prüfen

### Menü wird nicht angezeigt
- Küche hat noch kein Menü für heute eingetragen
- Später nochmal versuchen

## Datenschutz

- Tokens sind nicht personenbezogen lesbar
- Keine Speicherung von Geräteinformationen
- Keine Tracking-Cookies
- Reine Funktionalität ohne Werbung/Analytics

## Zukünftige Erweiterungen

Geplante Features:
- 📧 E-Mail-Versand von QR-Codes direkt aus dem Adminbereich
- 🔔 Push-Benachrichtigungen bei neuem Menü
- 📊 Persönliche Statistiken (Wie oft angemeldet, Lieblingsmenüs)
- ⏰ Erinnerungen zur Anmeldung
- 📅 Mehrere Tage im Voraus anmelden

---

**FoodBot Mobile** - Essensanmeldung leicht gemacht! 🍽️
