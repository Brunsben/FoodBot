#!/bin/bash
# Display Cache Clear Script
# Löscht Browser-Cache und lädt Chromium neu

# Chromium stoppen
pkill -f chromium

# Cache löschen
rm -rf ~/.cache/chromium/*
rm -rf ~/.config/chromium/Default/Cache/*
rm -rf ~/.config/chromium/Default/Code\ Cache/*

# FoodBot neu starten (um sicherzugehen)
sudo systemctl restart foodbot

# 3 Sekunden warten
sleep 3

# Chromium im Kiosk-Modus neu starten
DISPLAY=:0 chromium-browser --kiosk --incognito --disable-cache --disk-cache-size=1 http://localhost:5001 &

echo "✓ Display-Cache gelöscht und Chromium neu gestartet"
