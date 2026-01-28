## Beispiel für CSV-Import

Die CSV-Datei sollte folgende Spalten enthalten (Reihenfolge egal, Groß-/Kleinschreibung egal):

```
Name,Personalnummer,Karte
Max Mustermann,12345,ABC1234
Erika Musterfrau,23456,XYZ5678
```

Alternativ sind auch die englischen Spaltennamen möglich:
```
name,personal_number,card_id
```

Jede Zeile entspricht einem User. Die Karten-ID ist optional.
# FoodBot

Ein System zur Essensanmeldung für die Feuerwehr, optimiert für den Raspberry Pi.

## Features
- Anmeldung/Abmeldung per Transponder (RFID) oder Personalnummer am Touch-Display
- Web-Interface für Küche (Menü, Anzahl, Namensliste)
- Adminbereich (Userverwaltung, CSV-Import, Bearbeiten/Löschen, manuelle Anmeldung)
- Automatisches Leeren der Anmeldungen jede Nacht (Cronjob)

## Installation (Raspberry Pi)
1. Python 3 installieren (z.B. `sudo apt install python3 python3-pip`)
2. Abhängigkeiten installieren:
	```
	pip3 install -r requirements.txt
	```
3. Konfiguration anpassen:
   ```
   cp .env.example .env
   # Bearbeite .env und setze SECRET_KEY und RFID-Port
   ```
4. Seriellen Treiber für TWN4 ggf. installieren (z.B. `sudo apt install python3-serial`)
5. Projekt starten:
- Küche: http://<raspberrypi>:5000/kitchen (Tablet/PC im Netz)
- Admin: http://<raspberrypi>:5000/admin

### RFID-Leser
- Standardport: `/dev/ttyUSB0` (anpassbar in `app/rfid.py`)
- Karten-IDs werden automatisch erkannt und verarbeitet

### Datenbank
- SQLite-Datei `foodbot.db` (wird automatisch angelegt, nicht ins Git einchecken)

### Nächtlicher Reset (Cronjob)
Füge folgenden Cronjob hinzu, um jeden Tag um 3 Uhr die Anmeldungen zu löschen:
```
0 3 * * * cd /Pfad/zu/FoodBot && python3 clear_registrations.py
```

### Autostart (systemd)
Um FoodBot beim Systemstart automatisch zu starten:
```bash
sudo cp foodbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable foodbot
sudo systemctl start foodbot
```
Status prüfen: `sudo systemctl status foodbot`

## Troubleshooting

### RFID-Leser wird nicht erkannt
- Prüfe mit `ls -l /dev/ttyUSB*` ob der Reader erkannt wurde
- Stelle sicher, dass dein User zur dialout-Gruppe gehört: `sudo usermod -a -G dialout $USER`
- Passe den Port in `.env` an falls nötig (z.B. `/dev/ttyACM0`)

### Datenbank-Fehler
- Lösche die Datenbank und starte neu: `rm foodbot.db && python3 app/main.py`

### Port 5000 bereits belegt
- Ändere den Port in `app/main.py`: `app.run(host='0.0.0.0', port=8080)`

## Hinweise
- Die SQLite-Datenbank wird automatisch angelegt
- Sensible Daten (z.B. DB) sind durch `.gitignore` geschützt
- CSV-Import: Spaltennamen z.B. Name, Personalnummer, Karte
