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
            
            // Update users list
            const usersList = document.getElementById('users-list');
            usersList.innerHTML = data.users
                .map(user => `<div class="user-badge">${user.name}</div>`)
                .join('');
            
            // Update menu display
            const menuDisplay = document.querySelector('.menu-display');
            if (data.menu.zwei_menues_aktiv) {
                menuDisplay.innerHTML = `
                    <div class="menu-dual">
                        <div class="menu-item">
                            <div class="menu-item-label">Menü 1</div>
                            <div class="menu-item-text">${data.menu.menu1_name || 'Nicht gesetzt'}</div>
                        </div>
                        <div class="menu-item">
                            <div class="menu-item-label">Menü 2</div>
                            <div class="menu-item-text">${data.menu.menu2_name || 'Nicht gesetzt'}</div>
                        </div>
                    </div>
                `;
            } else if (data.menu.description) {
                menuDisplay.innerHTML = `<strong>${data.menu.description}</strong>`;
            } else {
                menuDisplay.innerHTML = '<span style="color: #64748b;">Kein Menü eingetragen</span>';
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
