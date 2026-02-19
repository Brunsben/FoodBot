#!/bin/bash
#
# JavaScript Build & Optimization Script
# Minimiert JS-Dateien für schnellere Ladezeiten
#

set -e  # Exit bei Fehler

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATIC_DIR="$SCRIPT_DIR/static"
JS_DIR="$STATIC_DIR/js"

echo "🔧 FoodBot - JavaScript Build Script"
echo "====================================="
echo ""

# Prüfe ob terser installiert ist
if ! command -v terser &> /dev/null; then
    echo "❌ terser ist nicht installiert!"
    echo ""
    echo "Installation:"
    echo "  npm install -g terser"
    echo ""
    echo "Oder mit npx (ohne globale Installation):"
    echo "  npx terser --version"
    echo ""
    exit 1
fi

echo "✅ terser gefunden: $(terser --version)"
echo ""

# Funktion zum Minifizieren einer Datei
minify_file() {
    local input_file="$1"
    local output_file="${input_file%.js}.min.js"
    
    echo "📦 Minifying: $(basename "$input_file")"
    
    terser "$input_file" \
        --compress \
        --mangle \
        --output "$output_file" \
        --source-map "url=$(basename "$output_file").map"
    
    # Größenvergleich
    local original_size=$(wc -c < "$input_file" | tr -d ' ')
    local minified_size=$(wc -c < "$output_file" | tr -d ' ')
    local reduction=$((100 - (minified_size * 100 / original_size)))
    
    echo "   Original:  ${original_size} bytes"
    echo "   Minified:  ${minified_size} bytes"
    echo "   Saved:     ${reduction}%"
    echo ""
}

# Minifiziere alle JS-Dateien in pages/
if [ -d "$JS_DIR/pages" ]; then
    echo "📁 Processing: js/pages/"
    for js_file in "$JS_DIR/pages"/*.js; do
        # Überspringe bereits minifizierte Dateien
        if [[ ! "$js_file" =~ \.min\.js$ ]]; then
            minify_file "$js_file"
        fi
    done
fi

# Minifiziere Root-Level JS
echo "📁 Processing: js/"
for js_file in "$JS_DIR"/*.js; do
    # Überspringe bereits minifizierte Dateien
    if [[ ! "$js_file" =~ \.min\.js$ ]] && [ -f "$js_file" ]; then
        minify_file "$js_file"
    fi
done

# Optional: Service Worker minifizieren
if [ -f "$STATIC_DIR/sw.js" ]; then
    echo "📁 Processing: root"
    minify_file "$STATIC_DIR/sw.js"
fi

echo "✨ Build abgeschlossen!"
echo ""
echo "💡 Tipp: Für Produktion .min.js Dateien verwenden:"
echo "   <script src=\"/static/js/pages/touch.min.js\"></script>"
echo ""
