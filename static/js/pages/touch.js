/* ===================================
   Touch Screen JavaScript
   =================================== */

let currentUserId = null;
let currentCardId = null;
let currentPersonalNumber = null;

/**
 * Display status popup with message
 */
function showStatus(type, title, subtitle) {
    const popup = document.getElementById('statusPopup');
    const icon = document.getElementById('statusIcon');
    
    popup.className = 'status-popup show ' + type;
    document.getElementById('statusTitle').textContent = title;
    document.getElementById('statusSubtitle').textContent = subtitle;
    
    icon.textContent = type === 'success' ? '✓' : (type === 'error' ? '✗' : '⚠');
    
    setTimeout(() => popup.classList.remove('show'), 3000);
}

/**
 * Show menu choice overlay
 */
function showMenuChoice(userId, cardId, menu1, menu2) {
    currentUserId = userId;
    currentCardId = cardId;
    
    document.getElementById('choice1').textContent = menu1;
    document.getElementById('choice2').textContent = menu2;
    document.getElementById('choiceOverlay').classList.add('show');
}

/**
 * Handle menu selection
 */
async function selectMenu(choice) {
    document.getElementById('choiceOverlay').classList.remove('show');
    
    if (currentPersonalNumber) {
        // Handle personal number selection
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                personal_number: currentPersonalNumber,
                menu_choice: choice
            })
        });
        
        const data = await res.json();
        if (data.success) {
            showStatus('success', 'Angemeldet!', data.user.name);
            currentPersonalNumber = null;
            updateMenu();
        }
    } else {
        // Handle RFID selection
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

/**
 * Poll RFID scanner for card detection
 */
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
    } catch(e) {
        // Silent fail - RFID not available
    }
}

/**
 * Update menu display with latest menu data
 */
async function updateMenu() {
    try {
        const res = await fetch(`/menu/data?t=${Date.now()}`);
        const data = await res.json();
        const display = document.getElementById('menuDisplay');
        
        if (data.zwei_menues_aktiv) {
            display.textContent = '';
            const grid = document.createElement('div');
            grid.className = 'menu-grid';
            
            const item1 = document.createElement('div');
            item1.className = 'menu-item';
            const label1 = document.createElement('div');
            label1.className = 'menu-item-label';
            label1.textContent = 'Menü 1';
            const name1 = document.createElement('div');
            name1.className = 'menu-item-name';
            name1.textContent = data.menu1 || 'Nicht gesetzt';
            item1.appendChild(label1);
            item1.appendChild(name1);
            
            const item2 = document.createElement('div');
            item2.className = 'menu-item';
            const label2 = document.createElement('div');
            label2.className = 'menu-item-label';
            label2.textContent = 'Menü 2';
            const name2 = document.createElement('div');
            name2.className = 'menu-item-name';
            name2.textContent = data.menu2 || 'Nicht gesetzt';
            item2.appendChild(label2);
            item2.appendChild(name2);
            
            grid.appendChild(item1);
            grid.appendChild(item2);
            display.appendChild(grid);
        } else {
            display.textContent = data.menu || 'Kein Menü verfügbar';
        }
    } catch(e) {
        console.error('Error updating menu:', e);
    }
}

/**
 * Show input for personal number input
 */
function showInput() {
    document.getElementById('inputWrapper').style.display = 'block';
    document.getElementById('showInputBtn').style.display = 'none';
    document.getElementById('scannerIcon').style.display = 'none';
    document.getElementById('scannerText').style.display = 'none';
    document.querySelector('.main-content').classList.add('numpad-active');
    
    // Fokussiere Input-Feld
    setTimeout(() => {
        document.getElementById('personalNumberInput').focus();
    }, 100);
}

/**
 * Hide input
 */
function hideInput() {
    document.getElementById('inputWrapper').style.display = 'none';
    document.getElementById('showInputBtn').style.display = 'block';
    document.getElementById('scannerIcon').style.display = 'block';
    document.getElementById('scannerText').style.display = 'block';
    document.getElementById('personalNumberInput').value = '';
    document.querySelector('.main-content').classList.remove('numpad-active');
}

/**
 * Handle form submission
 */
async function handleSubmit(e) {
    e.preventDefault();
    
    const personalNumber = document.getElementById('personalNumberInput').value.trim();
    if (!personalNumber) return;
    
    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({personal_number: personalNumber})
        });
        
        const data = await res.json();
        
        if (data.success) {
            if (data.need_menu_choice) {
                currentUserId = data.user_id;
                currentPersonalNumber = personalNumber;
                
                document.getElementById('choice1').textContent = data.menu1;
                document.getElementById('choice2').textContent = data.menu2;
                document.getElementById('choiceOverlay').classList.add('show');
                
                hideInput();
            } else {
                const message = data.registered ? 'Angemeldet!' : 'Abgemeldet';
                const type = data.registered ? 'success' : 'warning';
                
                showStatus(type, message, data.user.name);
                hideInput();
                updateMenu();
            }
        } else {
            showStatus('error', 'Fehler', data.message || 'Personalnummer nicht gefunden');
        }
    } catch(e) {
        showStatus('error', 'Fehler', 'Anmeldung fehlgeschlagen');
    }
}

// Initialize polling and updates
setInterval(pollRFID, 500);
setInterval(updateMenu, 5000);
updateMenu();
