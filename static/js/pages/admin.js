/**
 * Admin Page JavaScript
 * Handles menu switching, user editing modal, and form interactions
 */

// ===================================
// Menu Management
// ===================================

/**
 * Toggle between single and dual menu input fields
 * @param {boolean} isDual - Whether dual menu mode is enabled
 */
function toggleMenuInputs(isDual) {
    const singleMenu = document.getElementById('single-menu');
    const dualMenu = document.getElementById('dual-menu');
    
    if (singleMenu && dualMenu) {
        singleMenu.classList.toggle('active', !isDual);
        dualMenu.classList.toggle('active', isDual);
    }
}

// ===================================
// User Management Modal
// ===================================

/**
 * Open the edit user modal with pre-filled data
 * @param {number} id - User ID
 * @param {string} name - User name
 * @param {string} personalNumber - User personal number
 * @param {string} cardId - User card ID (RFID)
 */
function editUser(id, name, personalNumber, cardId) {
    const modal = document.getElementById('editModal');
    const idField = document.getElementById('edit_user_id');
    const nameField = document.getElementById('edit_name');
    const personalNumberField = document.getElementById('edit_personal_number');
    const cardIdField = document.getElementById('edit_card_id');
    
    if (modal && idField && nameField && personalNumberField && cardIdField) {
        idField.value = id;
        nameField.value = name;
        personalNumberField.value = personalNumber;
        cardIdField.value = cardId || '';
        modal.style.display = 'flex';
    }
}

/**
 * Close the edit user modal
 */
function closeEditModal() {
    const modal = document.getElementById('editModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// ===================================
// Event Listeners
// ===================================

/**
 * Initialize event listeners when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // Close modal when clicking outside the modal content
    const modal = document.getElementById('editModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeEditModal();
            }
        });
    }
    
    // Close modal on ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeEditModal();
        }
    });
    
    // Auto-focus first input in modal when opened
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'style') {
                const modal = document.getElementById('editModal');
                if (modal && modal.style.display === 'flex') {
                    const firstInput = modal.querySelector('input[type="text"]');
                    if (firstInput) {
                        firstInput.focus();
                    }
                }
            }
        });
    });
    
    if (modal) {
        observer.observe(modal, { attributes: true, attributeFilter: ['style'] });
    }
});

// ===================================
// Utility Functions
// ===================================

/**
 * Confirm delete action
 * @param {string} userName - Name of the user to delete
 * @returns {boolean} - True if confirmed, false otherwise
 */
function confirmDelete(userName) {
    return confirm(`User ${userName} wirklich löschen?`);
}

/**
 * Validate form before submission
 * @param {HTMLFormElement} form - The form element to validate
 * @returns {boolean} - True if valid, false otherwise
 */
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.style.borderColor = 'var(--error)';
            isValid = false;
        } else {
            field.style.borderColor = '';
        }
    });
    
    return isValid;
}
