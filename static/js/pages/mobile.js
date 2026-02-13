/**
 * Mobile Page JavaScript
 * Handles interactions on the mobile registration page
 */

/**
 * Initialize mobile page functionality
 */
function initMobile() {
    console.log('Mobile page initialized');
    
    // Add any additional initialization logic here
    setupFormValidation();
    setupTouchFeedback();
}

/**
 * Setup form validation
 * Prevents double submissions and validates form data
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const button = this.querySelector('button[type="submit"]');
            
            if (button && !button.disabled) {
                // Disable button to prevent double submission
                button.disabled = true;
                button.style.opacity = '0.5';
                
                // Re-enable after 2 seconds in case of error
                setTimeout(() => {
                    button.disabled = false;
                    button.style.opacity = '1';
                }, 2000);
            }
        });
    });
}

/**
 * Setup touch feedback for better mobile UX
 * Adds visual feedback on touch/click
 */
function setupTouchFeedback() {
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(button => {
        button.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.98)';
        });
        
        button.addEventListener('touchend', function() {
            setTimeout(() => {
                this.style.transform = '';
            }, 100);
        });
    });
}

/**
 * Show a temporary notification
 * @param {string} message - The message to display
 * @param {string} type - Type of notification (success, error, warning)
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: ${type === 'error' ? '#dc2626' : type === 'success' ? '#10b981' : '#f59e0b'};
        color: white;
        padding: 15px 30px;
        border-radius: 8px;
        z-index: 1000;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        animation: slideDown 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideUp 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMobile);
} else {
    initMobile();
}
