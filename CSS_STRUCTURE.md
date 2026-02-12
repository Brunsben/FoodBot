# CSS/JS Strukturdokumentation

## Überblick

Die CSS- und JavaScript-Dateien sind nun modular organisiert, um Wartbarkeit und responsive Design zu verbessern.

## Verzeichnisstruktur

```
static/
├── css/
│   ├── base.css           # Grundlegende Styles, CSS-Variablen, Reset
│   ├── components.css     # Wiederverwendbare UI-Komponenten
│   ├── layouts.css        # Layout-Systeme und Grid
│   ├── shared.css         # Gemeinsame seitenübergreifende Elemente
│   └── pages/
│       ├── touch.css      # Touch-Screen spezifische Styles
│       ├── admin.css      # Admin-Panel Styles
│       ├── kitchen.css    # Kitchen Display Styles
│       ├── mobile.css     # Mobile Registration Styles
│       ├── weekly.css     # Weekly Planning Styles
│       ├── stats.css      # Statistics Page Styles
│       ├── history.css    # History Overview Styles
│       ├── history_detail.css  # User Detail History Styles
│       └── kitchen_print.css   # Kitchen Print Styles
├── js/
│   ├── utils.js           # Gemeinsame Utility-Funktionen
│   └── pages/
│       ├── touch.js       # Touch-Screen JavaScript-Logik
│       ├── admin.js       # Admin-Panel JavaScript
│       ├── kitchen.js     # Kitchen Display JavaScript
│       ├── mobile.js      # Mobile Registration JavaScript
│       ├── weekly.js      # Weekly Planning JavaScript
│       └── stats.js       # Statistics Page JavaScript
```

## CSS-Struktur

### base.css
**Zweck:** Grundlegende Styles für alle Seiten
- CSS Reset (`*, box-sizing`)
- CSS Custom Properties (Variablen):
  - Farben: `--primary`, `--accent`, `--bg-*`, `--text-*`
  - Abstände: `--space-xs` bis `--space-2xl`
  - Typografie: `--font-size-xs` bis `--font-size-4xl`
  - Border Radius: `--radius-sm` bis `--radius-full`
  - Schatten: `--shadow-sm` bis `--shadow-xl`
  - Übergänge: `--transition-fast`, `--transition-base`
- Utility-Klassen: `.text-*`, `.mt-*`, `.mb-*`, `.p-*`
- Keyframe-Animationen: `fadeIn`, `pulse`, `slideIn`

### components.css
**Zweck:** Wiederverwendbare UI-Komponenten
- Buttons: `.btn`, `.btn-primary`, `.btn-ghost`, `.btn-sm`, `.btn-lg`
- Cards: `.card`, `.card-header`, `.card-title`, `.card-body`
- Inputs: `.input`
- Badges: `.badge`, `.badge-success`, `.badge-warning`, `.badge-error`
- Modals: `.modal-overlay`, `.modal-content`
- Status Popup: `.status-popup`, `.status-icon`, `.status-title`, `.status-subtitle`

### layouts.css
**Zweck:** Layout-Systeme und responsive Strukturen
- Container: `.container`, `.container-fluid`
- Page-Struktur: `.page-wrapper`, `.page-header`, `.page-title`, `.main-content`
- Grid-System: `.grid`, `.grid-2`, `.grid-3`, `.grid-4`
- Flexbox-Utilities: `.flex`, `.flex-center`, `.flex-between`, `.flex-col`
- Responsive Breakpoints:
  - `@media (max-width: 480px)`: Mobile/Raspberry Pi
  - `@media (min-width: 768px)`: Tablet
  - `@media (min-width: 1024px)`: Desktop

### shared.css (NEU)
**Zweck:** Gemeinsame seitenübergreifende Komponenten
- **Header Variations**: `.header`, `.header-actions`
- **Form Elements**: `.form-group`, `.form-row`, Input-Styles
- **Tables**: `.data-table` mit responsivem Verhalten
- **Action Buttons**: `.action-btn` (edit, delete, qr)
- **Empty States**: `.empty-state`, `.empty-state-icon`
- **Loading States**: `.skeleton` mit Animation
- **Messages**: `.message-success`, `.message-error`, `.message-warning`, `.message-info`
- **Stats Display**: `.stats-grid`, `.stat-card`
- **Responsive Utilities**: Mobile-optimierte Tabellen und Forms

### pages/touch.css
**Zweck:** Touch-Screen spezifische Styles
- Seitenstruktur: `body`, `.page-header`, `.main-content`
- Menü-Anzeige: `.menu-card`, `.menu-grid`, `.menu-item`
- Scanner-Bereich: `.scanner-area`, `.scanner-icon`
- Numpad: `.numpad-wrapper`, `.numpad`, `.numpad-btn`, `.numpad-display`
- Menü-Auswahl: `.choice-overlay`, `.choice-box`, `.choice-btn`
- **Responsive Breakpoints** für optimale Darstellung:
  - **Raspberry Pi 3.5" (max-width: 480px)**:
    - Kleinere Paddings und Gaps
    - Numpad-Buttons: `padding: 0.5rem`, `font-size: 1.125rem`, `min-height: 2.5rem`
    - Optimiert für 320x480px Display
  - **Tablet (min-width: 768px)**:
    - Größere Abstände
    - Numpad-Buttons: `padding: 1rem`, `font-size: 1.5rem`, `min-height: 3.5rem`
    - 2-spaltiges Menu-Grid
  - **Desktop (min-width: 1024px)**:
    - Maximale Numpad-Breite: 400px
    - Numpad-Buttons: `min-height: 4rem`
    - Große Scanner-Icons: `font-size: 8rem`

## JavaScript-Struktur

### pages/touch.js
**Zweck:** Touch-Screen Logik
- **State Management**: `currentUserId`, `currentCardId`, `currentPersonalNumber`
- **Funktionen**:
  - `showStatus(type, title, subtitle)`: Zeigt Status-Popup an
  - `showMenuChoice(userId, cardId, menu1, menu2)`: Zeigt Menü-Auswahl an
  - `selectMenu(choice)`: Verarbeitet Menü-Auswahl
  - `pollRFID()`: Fragt RFID-Scanner ab (alle 500ms)
  - `updateMenu()`: Aktualisiert Menü-Anzeige (alle 5 Sekunden)
  - `showNumpad()`, `hideNumpad()`: Zeigt/Versteckt Numpad
  - `addDigit(digit)`, `deleteDigit()`: Numpad-Eingabe
  - `handleSubmit(e)`: Verarbeitet Personalnummer-Eingabe

### utils.js (ERWEITERT)
**Zweck:** Gemeinsame Utility-Funktionen
- **Date/Time**: `formatDate()`, `formatWeekday()`
- **UI**: `showToast()`, `confirmDialog()`, `showLoadingSpinner()`, `hideLoadingSpinner()`
- **API**: `apiRequest()`, `fetchWithRetry()`, `post()`, `put()`, `del()`
- **DOM**: `createElement()`, `toggleClass()`, `onMultiple()`
- **Forms**: `getFormData()`, `validateForm()`, `showFormErrors()`
- **Storage**: `saveToStorage()`, `loadFromStorage()`, `removeFromStorage()`
- **URL**: `buildUrl()`, `navigateTo()`, `reloadPage()`, `getQueryParams()`
- **Utilities**: `debounce()`, `copyToClipboard()`, `escapeHtml()`, `formatNumber()`, `isValidEmail()`, `getCookie()`, `setCookie()`

## Template-Integration

Templates müssen folgende Links enthalten:

```html
<head>
    <link rel="stylesheet" href="/static/css/base.css">
    <link rel="stylesheet" href="/static/css/components.css">
    <link rel="stylesheet" href="/static/css/layouts.css">
    <link rel="stylesheet" href="/static/css/shared.css">
    <link rel="stylesheet" href="/static/css/pages/[pagename].css">
</head>
<body>
    <!-- Content -->
    <script src="/static/js/utils.js"></script>
    <script src="/static/js/pages/[pagename].js"></script>
</body>
```

## Vorteile der neuen Struktur

1. **Wartbarkeit**: Styles und Scripts sind logisch getrennt und leicht zu finden
2. **Wiederverwendbarkeit**: Komponenten können auf mehreren Seiten genutzt werden
3. **Deduplizierung**: Gemeinsame Elemente in shared.css und utils.js (NEU)
4. **Responsive Design**: Klare Breakpoints für verschiedene Geräte
5. **Performance**: Browser kann CSS/JS-Dateien cachen
6. **Entwicklung**: Änderungen an einer Komponente wirken sich auf alle Seiten aus
7. **Übersichtlichkeit**: Templates sind deutlich schlanker und fokussierter

## Deduplizierung (NEU)

### Was wurde zusammengelegt:

**CSS (shared.css):**
- Header-Styles (waren in 5+ Templates dupliziert)
- Form-Elemente und Input-Styles (waren in 4+ Templates dupliziert)
- Tabellen-Styles mit responsivem Verhalten (waren in 3+ Templates dupliziert)
- Action-Buttons (Edit, Delete, QR)
- Message/Alert-Komponenten
- Loading States und Skeleton Screens
- Stats-Display-Komponenten

**JavaScript (utils.js erweitert):**
- DOM-Manipulation: `createElement()`, `toggleClass()`, `onMultiple()`
- Form-Handling: `getFormData()`, `validateForm()`, `showFormErrors()`
- API-Requests: `fetchWithRetry()`, `post()`, `put()`, `del()`
- Storage-Helpers: `saveToStorage()`, `loadFromStorage()`
- URL-Building: `buildUrl()`, `navigateTo()`, `getQueryParams()`

### Migration Guide:

Alle Templates wurden bereits aktualisiert:
1. ✅ `<link rel="stylesheet" href="/static/css/shared.css">` ist überall eingebunden
2. ✅ Duplizierte Header/Form/Table-Styles wurden aus page-CSS entfernt
3. ✅ Gemeinsame Funktionen nutzen jetzt utils.js

## CSS-Variablen verwenden

In neuen Styles sollten immer die CSS-Variablen aus `base.css` verwendet werden:

```css
.mein-element {
    color: var(--text-primary);
    background: var(--bg-glass);
    padding: var(--space-md);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    transition: all var(--transition-base);
}
```

## Status

**✅ Alle Templates vollständig modularisiert:**
- touch.html → pages/touch.css + pages/touch.js
- admin.html → pages/admin.css + pages/admin.js  
- kitchen.html → pages/kitchen.css + pages/kitchen.js
- mobile.html → pages/mobile.css + pages/mobile.js
- weekly.html → pages/weekly.css + pages/weekly.js
- stats.html → pages/stats.css + pages/stats.js
- history.html → pages/history.css + pages/history.js
- history_detail.html → pages/history_detail.css
- kitchen_print.html → pages/kitchen_print.css

**✅ Base Template erstellt:**
- templates/base.html mit Jinja2 Inheritance für zukünftige Verwendung

**✅ Performance-Optimierungen:**
- Alle Scripts mit `defer` Attribut
- Cache-Control Headers für statische Assets
- Font-display: swap für bessere Font-Loading Performance
- Viewport-fit: cover für moderne Devices
