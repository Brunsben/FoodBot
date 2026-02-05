#!/bin/bash
# Cleanup Script für FoodBot Templates
# Entfernt alle alten/cached Templates und holt frische Versionen

set -e

echo "=== FoodBot Template Cleanup ==="
echo ""

cd ~/FoodBot

echo "1. Stoppe Service..."
sudo systemctl stop foodbot

echo "2. Sichere aktuelle Datenbank..."
cp foodbot.db foodbot.db.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

echo "3. Entferne alle lokalen Template-Änderungen..."
git checkout -- templates/*.html 2>/dev/null || true

echo "4. Entferne untracked Files..."
git clean -fd templates/ 2>/dev/null || true

echo "5. Hole neueste Version von GitHub..."
git fetch origin
git reset --hard origin/main

echo "6. Verifiziere Templates..."
echo "   - Admin.html hat CSS-Variablen: $(grep -c ':root' templates/admin.html || echo 'FEHLER')"
echo "   - Touch.html hat CSS-Variablen: $(grep -c ':root' templates/touch.html || echo 'FEHLER')"
echo "   - Kitchen.html hat CSS-Variablen: $(grep -c ':root' templates/kitchen.html || echo 'FEHLER')"

echo "7. Starte Service neu..."
sudo systemctl start foodbot

echo ""
echo "✅ Cleanup abgeschlossen!"
echo "Öffne http://$(hostname -I | awk '{print $1}'):5001/admin"
echo ""
