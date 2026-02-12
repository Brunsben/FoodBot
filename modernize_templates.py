#!/usr/bin/env python3
"""
Script to modernize all FoodBot templates with the new design system
"""

MODERN_TOUCH_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Essensanmeldung</title>
    <link rel="stylesheet" href="/static/modern-design.css">
    <style>
        body {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .page-header {
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            padding: var(--space-lg);
            text-align: center;
            border-bottom: 3px solid var(--primary);
            box-shadow: var(--shadow-lg);
        }
        
        .page-title {
            font-size: clamp(1.5rem, 5vw, 2.5rem);
            font-weight: 800;
            margin: 0;
            background: linear-gradient(135deg, var(--primary-light), var(--accent-light));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: var(--space-lg);
            overflow-y: auto;
            gap: var(--space-lg);
        }
        
        .menu-card {
            background: var(--bg-glass);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: var(--radius-xl);
            padding: var(--space-lg);
            box-shadow: var(--shadow-xl);
        }
        
        .menu-label {
            font-size: 0.875rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: var(--space-sm);
            text-align: center;
        }
        
        .menu-text {
            font-size: clamp(1.25rem, 4vw, 1.75rem);
            font-weight: 700;
            text-align: center;
            line-height: 1.4;
        }
        
        .menu-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: var(--space-md);
        }
        
        .menu-item {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            border-radius: var(--radius-lg);
            padding: var(--space-lg);
            text-align: center;
            box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3);
        }
        
        .menu-item-label {
            font-size: 0.75rem;
            opacity: 0.8;
            margin-bottom: var(--space-xs);
        }
        
        .menu-item-name {
            font-size: 1.25rem;
            font-weight: 700;
        }
        
        .scanner-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 200px;
            gap: var(--space-lg);
        }
        
        .scanner-icon {
            font-size: clamp(4rem, 12vw, 6rem);
            animation: pulse 2s ease-in-out infinite;
            filter: drop-shadow(0 0 20px var(--primary));
        }
        
        .scanner-text {
            font-size: clamp(1.25rem, 3vw, 1.75rem);
            font-weight: 600;
            color: var(--text-secondary);
        }
        
        .numpad-wrapper {
            width: 100%;
            max-width: 360px;
            margin-top: var(--space-md);
        }
        
        .numpad-display {
            width: 100%;
            padding: var(--space-lg);
            font-size: 1.5rem;
            font-weight: 600;
            text-align: center;
            background: var(--bg-glass);
            border: 2px solid rgba(99, 102, 241, 0.3);
            border-radius: var(--radius-lg);
            color: var(--text-primary);
            margin-bottom: var(--space-md);
        }
        
        .numpad {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: var(--space-sm);
            margin-bottom: var(--space-sm);
        }
        
        .numpad-btn {
            padding: var(--space-lg);
            font-size: 1.5rem;
            font-weight: 700;
            background: var(--bg-glass);
            border: 2px solid rgba(99, 102, 241, 0.2);
            border-radius: var(--radius-md);
            color: var(--text-primary);
            cursor: pointer;
            transition: all var(--transition-fast);
        }
        
        .numpad-btn:active {
            transform: scale(0.95);
            background: rgba(99, 102, 241, 0.3);
        }
        
        .numpad-btn.delete {
            background: rgba(239, 68, 68, 0.2);
        }
        
        .numpad-btn.submit {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
            border: none;
        }
        
        .status-popup {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) scale(0);
            background: var(--bg-elevated);
            border-radius: var(--radius-xl);
            padding: var(--space-2xl);
            text-align: center;
            z-index: 1000;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.8);
            transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            min-width: 300px;
        }
        
        .status-popup.show { transform: translate(-50%, -50%) scale(1); }
        .status-popup.success { border: 3px solid var(--success); }
        .status-popup.error { border: 3px solid var(--error); }
        .status-popup.warning { border: 3px solid var(--warning); }
        
        .status-icon {
            font-size: 4rem;
            margin-bottom: var(--space-md);
        }
        
        .status-title {
            font-size: 1.75rem;
            margin-bottom: var(--space-sm);
            font-weight: 700;
        }
        
        .status-subtitle {
            font-size: 1.25rem;
            color: var(--text-muted);
        }
        
        .choice-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.95);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 2000;
            padding: var(--space-lg);
        }
        
        .choice-overlay.show { display: flex; }
        
        .choice-box {
            background: var(--bg-elevated);
            border: 3px solid var(--primary);
            border-radius: var(--radius-xl);
            padding: var(--space-2xl);
            max-width: 600px;
            width: 100%;
        }
        
        .choice-title {
            font-size: clamp(1.5rem, 4vw, 2rem);
            margin-bottom: var(--space-xl);
            font-weight: 700;
            text-align: center;
        }
        
        .choice-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: var(--space-md);
        }
        
        .choice-btn {
            padding: var(--space-xl);
            font-size: 1.25rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            border: none;
            border-radius: var(--radius-lg);
            color: white;
            cursor: pointer;
            transition: all var(--transition-base);
            box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
        }
        
        .choice-btn:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 30px rgba(99, 102, 241, 0.5);
        }
        
        .choice-btn:active {
            transform: translateY(0);
        }
    </style>
</head>
<body>
    <header class="page-header">
        <h1 class="page-title">🍽️ Essensanmeldung</h1>
    </header>
    
    <main class="main-content">
        <div class="menu-card">
            <div class="menu-label">Heutiges Menü</div>
            <div id="menuDisplay" class="menu-text">
                {% if menu %}
                    {% if menu.zwei_menues_aktiv %}
                        <div class="menu-grid">
                            <div class="menu-item">
                                <div class="menu-item-label">Menü 1</div>
                                <div class="menu-item-name">{{ menu.menu1_name }}</div>
                            </div>
                            <div class="menu-item">
                                <div class="menu-item-label">Menü 2</div>
                                <div class="menu-item-name">{{ menu.menu2_name }}</div>
                            </div>
                        </div>
                    {% else %}
                        {{ menu.description }}
                    {% endif %}
                {% else %}
                    <span style="color: var(--text-muted);">Kein Menü verfügbar</span>
                {% endif %}
            </div>
        </div>
        
        <div class="scanner-area">
            <div class="scanner-icon">📡</div>
            <div class="scanner-text">Karte auflegen</div>
            
            <button class="btn btn-primary" id="showNumpadBtn" onclick="showNumpad()">
                oder mit Personalnummer
            </button>
            
            <div id="numpadWrapper" class="numpad-wrapper" style="display: none;">
                <form onsubmit="handleSubmit(event)">
                    <input type="text" id="numpadDisplay" class="numpad-display" placeholder="Personalnummer" readonly>
                    
                    <div class="numpad">
                        <button type="button" class="numpad-btn" onclick="addDigit('1')">1</button>
                        <button type="button" class="numpad-btn" onclick="addDigit('2')">2</button>
                        <button type="button" class="numpad-btn" onclick="addDigit('3')">3</button>
                        <button type="button" class="numpad-btn" onclick="addDigit('4')">4</button>
                        <button type="button" class="numpad-btn" onclick="addDigit('5')">5</button>
                        <button type="button" class="numpad-btn" onclick="addDigit('6')">6</button>
                        <button type="button" class="numpad-btn" onclick="addDigit('7')">7</button>
                        <button type="button" class="numpad-btn" onclick="addDigit('8')">8</button>
                        <button type="button" class="numpad-btn" onclick="addDigit('9')">9</button>
                        <button type="button" class="numpad-btn delete" onclick="deleteDigit()">⌫</button>
                        <button type="button" class="numpad-btn" onclick="addDigit('0')">0</button>
                        <button type="submit" class="numpad-btn submit">✓</button>
                    </div>
                    
                    <button type="button" class="btn btn-ghost" onclick="hideNumpad()">Abbrechen</button>
                </form>
            </div>
        </div>
    </main>
    
    <div id="statusPopup" class="status-popup">
        <div class="status-icon" id="statusIcon">✓</div>
        <div class="status-title" id="statusTitle">Angemeldet</div>
        <div class="status-subtitle" id="statusSubtitle">Max Mustermann</div>
    </div>
    
    <div id="choiceOverlay" class="choice-overlay">
        <div class="choice-box">
            <div class="choice-title">Welches Menü?</div>
            <div class="choice-buttons">
                <button class="choice-btn" onclick="selectMenu(1)" id="choice1">Menü 1</button>
                <button class="choice-btn" onclick="selectMenu(2)" id="choice2">Menü 2</button>
            </div>
        </div>
    </div>
    
    <script>
        let currentUserId = null, currentCardId = null, currentPersonalNumber = null;
        
        function showStatus(type, title, subtitle) {
            const popup = document.getElementById('statusPopup');
            const icon = document.getElementById('statusIcon');
            popup.className = 'status-popup show ' + type;
            document.getElementById('statusTitle').textContent = title;
            document.getElementById('statusSubtitle').textContent = subtitle;
            icon.textContent = type === 'success' ? '✓' : (type === 'error' ? '✗' : '⚠');
            setTimeout(() => popup.classList.remove('show'), 3000);
        }
        
        function showMenuChoice(userId, cardId, menu1, menu2) {
            currentUserId = userId;
            currentCardId = cardId;
            document.getElementById('choice1').textContent = menu1;
            document.getElementById('choice2').textContent = menu2;
            document.getElementById('choiceOverlay').classList.add('show');
        }
        
        async function selectMenu(choice) {
            document.getElementById('choiceOverlay').classList.remove('show');
            
            if (currentPersonalNumber) {
                const res = await fetch('/api/register', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({personal_number: currentPersonalNumber, menu_choice: choice})
                });
                const data = await res.json();
                if (data.success) {
                    showStatus('success', 'Angemeldet!', data.user.name);
                    currentPersonalNumber = null;
                    updateMenu();
                }
            } else {
                const res = await fetch('/register', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `user_id=${currentUserId}&card_id=${currentCardId}&menu_choice=${choice}`
                });
                const data = await res.json();
                showStatus(data.status, data.message, data.name);
                updateMenu();
            }
        }
        
        async function pollRFID() {
            try {
                const res = await fetch('/rfid_scan');
                const data = await res.json();
                if (data.card_id) {
                    const regRes = await fetch('/register', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: `card_id=${data.card_id}`
                    });
                    const result = await regRes.json();
                    if (result.need_menu_choice) {
                        showMenuChoice(result.user_id, data.card_id, result.menu1, result.menu2);
                    } else {
                        showStatus(result.status, result.message, result.name);
                    }
                }
            } catch(e) {}
        }
        
        async function updateMenu() {
            try {
                const res = await fetch(`/menu/data?t=${Date.now()}`);
                const data = await res.json();
                const display = document.getElementById('menuDisplay');
                if (data.zwei_menues_aktiv) {
                    display.innerHTML = `<div class="menu-grid">
                        <div class="menu-item">
                            <div class="menu-item-label">Menü 1</div>
                            <div class="menu-item-name">${data.menu1||'Nicht gesetzt'}</div>
                        </div>
                        <div class="menu-item">
                            <div class="menu-item-label">Menü 2</div>
                            <div class="menu-item-name">${data.menu2||'Nicht gesetzt'}</div>
                        </div>
                    </div>`;
                } else {
                    display.textContent = data.menu || 'Kein Menü verfügbar';
                }
            } catch(e) {}
        }
        
        function showNumpad() {
            document.getElementById('numpadWrapper').style.display = 'block';
            document.getElementById('showNumpadBtn').style.display = 'none';
        }
        
        function hideNumpad() {
            document.getElementById('numpadWrapper').style.display = 'none';
            document.getElementById('showNumpadBtn').style.display = 'block';
            document.getElementById('numpadDisplay').value = '';
        }
        
        function addDigit(d) { document.getElementById('numpadDisplay').value += d; }
        function deleteDigit() { 
            const inp = document.getElementById('numpadDisplay');
            inp.value = inp.value.slice(0, -1);
        }
        
        async function handleSubmit(e) {
            e.preventDefault();
            const num = document.getElementById('numpadDisplay').value;
            if (!num) return;
            
            try {
                const res = await fetch('/api/register', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({personal_number: num})
                });
                const data = await res.json();
                if (data.success) {
                    if (data.need_menu_choice) {
                        currentUserId = data.user_id;
                        currentPersonalNumber = num;
                        document.getElementById('choice1').textContent = data.menu1;
                        document.getElementById('choice2').textContent = data.menu2;
                        document.getElementById('choiceOverlay').classList.add('show');
                        hideNumpad();
                    } else {
                        const msg = data.registered ? 'Angemeldet!' : 'Abgemeldet';
                        const type = data.registered ? 'success' : 'warning';
                        showStatus(type, msg, data.user.name);
                        hideNumpad();
                        updateMenu();
                    }
                } else {
                    showStatus('error', 'Fehler', data.message||'Personalnummer nicht gefunden');
                }
            } catch(e) {
                showStatus('error', 'Fehler', 'Anmeldung fehlgeschlagen');
            }
        }
        
        setInterval(pollRFID, 500);
        setInterval(updateMenu, 5000);
        updateMenu();
    </script>
</body>
</html>
"""

# Write the new template
with open('templates/touch.html', 'w', encoding='utf-8') as f:
    f.write(MODERN_TOUCH_TEMPLATE)

print("✓ touch.html modernisiert")
