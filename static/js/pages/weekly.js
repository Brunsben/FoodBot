/**
 * Weekly Planning Page JavaScript
 * Handles menu type toggling and form interactions
 */

/**
 * Toggle between single and dual menu inputs
 * @param {number} dayIndex - Index of the day card
 * @param {boolean} checked - Whether dual menu checkbox is checked
 */
function toggleDualMenu(dayIndex, checked) {
    const singleDiv = document.getElementById(`single-${dayIndex}`);
    const dualDiv = document.getElementById(`dual-${dayIndex}`);
    
    if (!singleDiv || !dualDiv) {
        console.warn(`Menu inputs not found for day index ${dayIndex}`);
        return;
    }
    
    if (checked) {
        singleDiv.classList.remove('active');
        dualDiv.classList.add('active');
        
        // Clear single menu input when switching to dual
        const singleInput = singleDiv.querySelector('input[type="text"]');
        if (singleInput && singleInput.value) {
            const confirmSwitch = confirm('Möchten Sie vom einzelnen Menü zu zwei Menüs wechseln? Das einzelne Menü wird gelöscht.');
            if (!confirmSwitch) {
                // Revert checkbox if user cancels
                const checkbox = document.getElementById(`zwei_menues_${dayIndex}`);
                if (checkbox) checkbox.checked = false;
                return;
            }
        }
    } else {
        singleDiv.classList.add('active');
        dualDiv.classList.remove('active');
        
        // Clear dual menu inputs when switching to single
        const dualInputs = dualDiv.querySelectorAll('input[type="text"]');
        if (dualInputs.length > 0 && Array.from(dualInputs).some(input => input.value)) {
            const confirmSwitch = confirm('Möchten Sie von zwei Menüs zu einem einzelnen Menü wechseln? Die beiden Menüs werden gelöscht.');
            if (!confirmSwitch) {
                // Revert checkbox if user cancels
                const checkbox = document.getElementById(`zwei_menues_${dayIndex}`);
                if (checkbox) checkbox.checked = true;
                return;
            }
        }
    }
}

/**
 * Initialize the weekly planning page
 */
function initWeeklyPlanning() {
    console.log('Weekly planning page initialized');
    
    setupFormEnhancements();
    setupAutoSave();
    highlightToday();
}

/**
 * Setup form enhancements for better UX
 */
function setupFormEnhancements() {
    // Add loading state to save buttons
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const button = this.querySelector('.btn-save');
            if (button && !button.disabled) {
                button.textContent = '💾 Speichert...';
                button.disabled = true;
                button.style.opacity = '0.7';
            }
        });
    });
    
    // Add change detection for unsaved changes warning
    let hasUnsavedChanges = false;
    
    const inputs = document.querySelectorAll('input[type="text"], input[type="time"], input[type="checkbox"]');
    inputs.forEach(input => {
        input.addEventListener('change', () => {
            hasUnsavedChanges = true;
        });
    });
    
    // Warn before leaving with unsaved changes
    window.addEventListener('beforeunload', (e) => {
        if (hasUnsavedChanges) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
    
    // Reset flag on successful save
    forms.forEach(form => {
        form.addEventListener('submit', () => {
            hasUnsavedChanges = false;
        });
    });
}

/**
 * Setup auto-save functionality (optional)
 * Currently disabled, but can be enabled for better UX
 */
function setupAutoSave() {
    // Could implement debounced auto-save here
    // For now, keeping manual save for better control
}

/**
 * Highlight today's card with a visual indicator
 */
function highlightToday() {
    const todayCard = document.querySelector('.day-card.today');
    if (todayCard) {
        todayCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

/**
 * Validate time input
 * @param {string} time - Time string in HH:MM format
 * @returns {boolean} - Whether the time is valid
 */
function isValidTime(time) {
    const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
    return timeRegex.test(time);
}

/**
 * Show a success message
 * @param {string} message - The message to display
 */
function showSuccessMessage(message) {
    const messageBox = document.createElement('div');
    messageBox.className = 'message-box';
    messageBox.textContent = message;
    messageBox.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 1000;
        min-width: 300px;
        text-align: center;
        animation: slideDown 0.3s ease-out;
    `;
    
    document.body.appendChild(messageBox);
    
    setTimeout(() => {
        messageBox.style.animation = 'slideUp 0.3s ease-out';
        setTimeout(() => messageBox.remove(), 300);
    }, 3000);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWeeklyPlanning);
} else {
    initWeeklyPlanning();
}

// Export functions for use in inline handlers
window.toggleDualMenu = toggleDualMenu;
