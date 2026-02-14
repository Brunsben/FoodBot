/* ===================================
   Kitchen Display - JavaScript
   =================================== */

/**
 * Updates the kitchen display with fresh data from the server
 */
function updateKitchen() {
    fetch(`/kitchen/data?t=${Date.now()}`)
        .then(response => response.json())
        .then(data => {
            // Update statistics counters
            document.getElementById('total-count').textContent = data.total;
            document.getElementById('menu1-count').textContent = data.menu1_count;
            document.getElementById('menu2-count').textContent = data.menu2_count;
            document.getElementById('guest-count').textContent = data.guest_count;
            document.getElementById('user-count').textContent = data.users.length;
            
            // Update users list (escape names to prevent XSS)
            const usersList = document.getElementById('users-list');
            usersList.innerHTML = data.users
                .map(user => {
                    const safe = document.createElement('div');
                    safe.className = 'user-badge';
                    safe.textContent = user.name;
                    return safe.outerHTML;
                })
                .join('');
            
            // Update menu display (safe DOM manipulation)
            const menuDisplay = document.querySelector('.menu-display');
            if (data.menu.zwei_menues_aktiv) {
                menuDisplay.textContent = '';
                const dual = document.createElement('div');
                dual.className = 'menu-dual';
                
                const item1 = document.createElement('div');
                item1.className = 'menu-item';
                const label1 = document.createElement('div');
                label1.className = 'menu-item-label';
                label1.textContent = 'Menü 1';
                const text1 = document.createElement('div');
                text1.className = 'menu-item-text';
                text1.textContent = data.menu.menu1_name || 'Nicht gesetzt';
                item1.appendChild(label1);
                item1.appendChild(text1);
                
                const item2 = document.createElement('div');
                item2.className = 'menu-item';
                const label2 = document.createElement('div');
                label2.className = 'menu-item-label';
                label2.textContent = 'Menü 2';
                const text2 = document.createElement('div');
                text2.className = 'menu-item-text';
                text2.textContent = data.menu.menu2_name || 'Nicht gesetzt';
                item2.appendChild(label2);
                item2.appendChild(text2);
                
                dual.appendChild(item1);
                dual.appendChild(item2);
                menuDisplay.appendChild(dual);
            } else if (data.menu.description) {
                menuDisplay.textContent = '';
                const strong = document.createElement('strong');
                strong.textContent = data.menu.description;
                menuDisplay.appendChild(strong);
            } else {
                menuDisplay.textContent = 'Kein Menü eingetragen';
            }
        })
        .catch(error => {
            console.error('Error updating kitchen display:', error);
        });
}

/**
 * Toggles menu input fields based on dual menu checkbox
 */
function toggleMenuInputs() {
    const checkbox = document.querySelector('input[name="zwei_menues_aktiv"]');
    const dualInputs = document.getElementById('dual-menu-inputs');
    const singleInput = document.getElementById('single-menu-input');
    
    if (checkbox && dualInputs && singleInput) {
        const isDualMode = checkbox.checked;
        dualInputs.style.display = isDualMode ? 'block' : 'none';
        singleInput.style.display = isDualMode ? 'none' : 'block';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Start auto-refresh
    setInterval(updateKitchen, 5000);
    
    // Initial update
    updateKitchen();
    
    // Setup menu toggle if checkbox exists
    const menuCheckbox = document.querySelector('input[name="zwei_menues_aktiv"]');
    if (menuCheckbox) {
        menuCheckbox.addEventListener('change', toggleMenuInputs);
    }
});
