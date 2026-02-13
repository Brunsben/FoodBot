/* ===================================
   Shared Utility Functions
   =================================== */

/**
 * Format date to German locale
 * @param {Date|string} date - Date object or ISO string
 * @returns {string} Formatted date (DD.MM.YYYY)
 */
function formatDate(date) {
    const d = typeof date === 'string' ? new Date(date) : date;
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}.${month}.${year}`;
}

/**
 * Format date to German weekday
 * @param {Date|string} date - Date object or ISO string
 * @returns {string} Weekday name (e.g., "Montag")
 */
function formatWeekday(date) {
    const d = typeof date === 'string' ? new Date(date) : date;
    const weekdays = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag'];
    return weekdays[d.getDay()];
}

/**
 * Debounce function to limit execution rate
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type of notification (success, error, warning, info)
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // Add toast styles if not already present
    if (!document.getElementById('toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            .toast {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 1rem 1.5rem;
                border-radius: 8px;
                color: white;
                font-weight: 600;
                z-index: 10000;
                animation: slideIn 0.3s ease-out;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
            }
            .toast-success { background: linear-gradient(135deg, #10b981, #059669); }
            .toast-error { background: linear-gradient(135deg, #ef4444, #dc2626); }
            .toast-warning { background: linear-gradient(135deg, #f59e0b, #d97706); }
            .toast-info { background: linear-gradient(135deg, #3b82f6, #2563eb); }
            @keyframes slideIn {
                from { transform: translateX(400px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Confirm dialog with custom styling
 * @param {string} message - Confirmation message
 * @returns {Promise<boolean>} User's choice
 */
function confirmDialog(message) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'confirm-overlay';
        overlay.innerHTML = `
            <div class="confirm-dialog">
                <p class="confirm-message">${message}</p>
                <div class="confirm-buttons">
                    <button class="btn btn-secondary" id="confirmNo">Abbrechen</button>
                    <button class="btn btn-primary" id="confirmYes">Bestätigen</button>
                </div>
            </div>
        `;
        
        // Add styles if not present
        if (!document.getElementById('confirm-styles')) {
            const style = document.createElement('style');
            style.id = 'confirm-styles';
            style.textContent = `
                .confirm-overlay {
                    position: fixed;
                    inset: 0;
                    background: rgba(0, 0, 0, 0.8);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 9999;
                    animation: fadeIn 0.2s ease-out;
                }
                .confirm-dialog {
                    background: var(--bg-elevated, #1e293b);
                    border: 2px solid var(--primary, #6366f1);
                    border-radius: 16px;
                    padding: 2rem;
                    max-width: 500px;
                    width: 90%;
                    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
                }
                .confirm-message {
                    font-size: 1.25rem;
                    margin-bottom: 1.5rem;
                    text-align: center;
                    color: var(--text-primary, #ffffff);
                }
                .confirm-buttons {
                    display: flex;
                    gap: 1rem;
                    justify-content: center;
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(overlay);
        
        document.getElementById('confirmYes').onclick = () => {
            overlay.remove();
            resolve(true);
        };
        
        document.getElementById('confirmNo').onclick = () => {
            overlay.remove();
            resolve(false);
        };
    });
}

/**
 * Make API request with error handling
 * @param {string} url - API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise<any>} Response data
 */
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Request failed:', error);
        showToast('Fehler bei der Anfrage: ' + error.message, 'error');
        throw error;
    }
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<void>}
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('In Zwischenablage kopiert', 'success', 2000);
    } catch (error) {
        console.error('Copy failed:', error);
        showToast('Kopieren fehlgeschlagen', 'error');
    }
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Parse query string parameters
 * @returns {Object} Object with query parameters
 */
function getQueryParams() {
    const params = {};
    const queryString = window.location.search.substring(1);
    const pairs = queryString.split('&');
    
    pairs.forEach(pair => {
        const [key, value] = pair.split('=');
        if (key) {
            params[decodeURIComponent(key)] = decodeURIComponent(value || '');
        }
    });
    
    return params;
}

/**
 * Add loading spinner to element
 * @param {HTMLElement} element - Element to add spinner to
 */
function showLoadingSpinner(element) {
    if (!element) return;
    
    element.style.position = 'relative';
    element.style.pointerEvents = 'none';
    element.style.opacity = '0.6';
    
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    spinner.innerHTML = '<div class="spinner"></div>';
    
    if (!document.getElementById('spinner-styles')) {
        const style = document.createElement('style');
        style.id = 'spinner-styles';
        style.textContent = `
            .loading-spinner {
                position: absolute;
                inset: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 100;
            }
            .spinner {
                width: 40px;
                height: 40px;
                border: 4px solid rgba(255, 255, 255, 0.3);
                border-top-color: var(--primary, #6366f1);
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
    
    element.appendChild(spinner);
}

/**
 * Remove loading spinner from element
 * @param {HTMLElement} element - Element to remove spinner from
 */
function hideLoadingSpinner(element) {
    if (!element) return;
    
    element.style.pointerEvents = '';
    element.style.opacity = '';
    
    const spinner = element.querySelector('.loading-spinner');
    if (spinner) spinner.remove();
}

/**
 * Format number with thousands separator
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
function formatNumber(num) {
    return new Intl.NumberFormat('de-DE').format(num);
}

/**
 * Validate email address
 * @param {string} email - Email to validate
 * @returns {boolean} Is valid
 */
function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

/**
 * Get cookie value by name
 * @param {string} name - Cookie name
 * @returns {string|null} Cookie value or null
 */
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

/**
 * Set cookie
 * @param {string} name - Cookie name
 * @param {string} value - Cookie value
 * @param {number} days - Expiry in days
 */
function setCookie(name, value, days = 365) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = `expires=${date.toUTCString()}`;
    document.cookie = `${name}=${value};${expires};path=/`;
}

/* ===================================
   DOM Manipulation Helpers
   =================================== */

/**
 * Create element with attributes and content
 * @param {string} tag - HTML tag name
 * @param {Object} attributes - Element attributes
 * @param {string|HTMLElement|Array} content - Element content
 * @returns {HTMLElement} Created element
 */
function createElement(tag, attributes = {}, content = null) {
    const element = document.createElement(tag);
    
    Object.entries(attributes).forEach(([key, value]) => {
        if (key === 'class') {
            element.className = value;
        } else if (key === 'style' && typeof value === 'object') {
            Object.assign(element.style, value);
        } else if (key.startsWith('on') && typeof value === 'function') {
            element.addEventListener(key.substring(2).toLowerCase(), value);
        } else {
            element.setAttribute(key, value);
        }
    });
    
    if (content) {
        if (Array.isArray(content)) {
            content.forEach(child => {
                if (typeof child === 'string') {
                    element.appendChild(document.createTextNode(child));
                } else {
                    element.appendChild(child);
                }
            });
        } else if (typeof content === 'string') {
            element.textContent = content;
        } else {
            element.appendChild(content);
        }
    }
    
    return element;
}

/**
 * Toggle class on element
 * @param {HTMLElement|string} element - Element or selector
 * @param {string} className - Class name to toggle
 */
function toggleClass(element, className) {
    const el = typeof element === 'string' ? document.querySelector(element) : element;
    if (el) el.classList.toggle(className);
}

/**
 * Add multiple event listeners
 * @param {HTMLElement|string} element - Element or selector
 * @param {string} events - Space-separated event names
 * @param {Function} handler - Event handler
 */
function onMultiple(element, events, handler) {
    const el = typeof element === 'string' ? document.querySelector(element) : element;
    if (!el) return;
    
    events.split(' ').forEach(event => {
        el.addEventListener(event, handler);
    });
}

/* ===================================
   Form Helpers
   =================================== */

/**
 * Get form data as object
 * @param {HTMLFormElement|string} form - Form element or selector
 * @returns {Object} Form data
 */
function getFormData(form) {
    const formEl = typeof form === 'string' ? document.querySelector(form) : form;
    if (!formEl) return {};
    
    const formData = new FormData(formEl);
    const data = {};
    
    formData.forEach((value, key) => {
        if (data[key]) {
            if (!Array.isArray(data[key])) {
                data[key] = [data[key]];
            }
            data[key].push(value);
        } else {
            data[key] = value;
        }
    });
    
    return data;
}

/**
 * Validate form fields
 * @param {HTMLFormElement|string} form - Form element or selector
 * @returns {Object} Validation result {valid: boolean, errors: Object}
 */
function validateForm(form) {
    const formEl = typeof form === 'string' ? document.querySelector(form) : form;
    if (!formEl) return { valid: false, errors: {} };
    
    const errors = {};
    const inputs = formEl.querySelectorAll('input[required], textarea[required], select[required]');
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            errors[input.name] = 'Dieses Feld ist erforderlich';
        } else if (input.type === 'email' && !isValidEmail(input.value)) {
            errors[input.name] = 'Ungültige E-Mail-Adresse';
        } else if (input.pattern) {
            const regex = new RegExp(input.pattern);
            if (!regex.test(input.value)) {
                errors[input.name] = input.title || 'Ungültiges Format';
            }
        }
    });
    
    return {
        valid: Object.keys(errors).length === 0,
        errors
    };
}

/**
 * Show validation errors on form
 * @param {HTMLFormElement|string} form - Form element or selector
 * @param {Object} errors - Error object {fieldName: errorMessage}
 */
function showFormErrors(form, errors) {
    const formEl = typeof form === 'string' ? document.querySelector(form) : form;
    if (!formEl) return;
    
    // Clear previous errors
    formEl.querySelectorAll('.error-message').forEach(el => el.remove());
    formEl.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
    
    Object.entries(errors).forEach(([field, message]) => {
        const input = formEl.querySelector(`[name="${field}"]`);
        if (input) {
            input.classList.add('error');
            const errorEl = createElement('div', { class: 'error-message' }, message);
            input.parentElement.appendChild(errorEl);
        }
    });
}

/* ===================================
   Data Fetching Helpers
   =================================== */

/**
 * Fetch data with automatic retry and error handling
 * @param {string} url - API endpoint
 * @param {Object} options - Fetch options
 * @param {number} retries - Number of retries (default: 2)
 * @returns {Promise<any>} Response data
 */
async function fetchWithRetry(url, options = {}, retries = 2) {
    for (let i = 0; i <= retries; i++) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            if (i === retries) {
                console.error(`Fetch failed after ${retries + 1} attempts:`, error);
                throw error;
            }
            // Wait before retry (exponential backoff)
            await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
        }
    }
}

/**
 * POST request helper
 * @param {string} url - API endpoint
 * @param {Object} data - Data to send
 * @returns {Promise<any>} Response data
 */
async function post(url, data) {
    return apiRequest(url, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

/**
 * PUT request helper
 * @param {string} url - API endpoint
 * @param {Object} data - Data to send
 * @returns {Promise<any>} Response data
 */
async function put(url, data) {
    return apiRequest(url, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

/**
 * DELETE request helper
 * @param {string} url - API endpoint
 * @returns {Promise<any>} Response data
 */
async function del(url) {
    return apiRequest(url, {
        method: 'DELETE'
    });
}

/* ===================================
   Storage Helpers
   =================================== */

/**
 * Save to localStorage with JSON serialization
 * @param {string} key - Storage key
 * @param {any} value - Value to store
 */
function saveToStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
        console.error('Storage save failed:', error);
    }
}

/**
 * Load from localStorage with JSON deserialization
 * @param {string} key - Storage key
 * @param {any} defaultValue - Default value if not found
 * @returns {any} Stored value or default
 */
function loadFromStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Storage load failed:', error);
        return defaultValue;
    }
}

/**
 * Remove from localStorage
 * @param {string} key - Storage key
 */
function removeFromStorage(key) {
    try {
        localStorage.removeItem(key);
    } catch (error) {
        console.error('Storage remove failed:', error);
    }
}

/* ===================================
   URL & Navigation Helpers
   =================================== */

/**
 * Build URL with query parameters
 * @param {string} baseUrl - Base URL
 * @param {Object} params - Query parameters
 * @returns {string} Full URL with parameters
 */
function buildUrl(baseUrl, params = {}) {
    const url = new URL(baseUrl, window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
            url.searchParams.append(key, value);
        }
    });
    return url.toString();
}

/**
 * Navigate to URL with optional delay
 * @param {string} url - Target URL
 * @param {number} delay - Delay in milliseconds
 */
function navigateTo(url, delay = 0) {
    if (delay > 0) {
        setTimeout(() => window.location.href = url, delay);
    } else {
        window.location.href = url;
    }
}

/**
 * Reload page with cache busting
 * @param {boolean} forceReload - Force reload from server
 */
function reloadPage(forceReload = true) {
    window.location.reload(forceReload);
}
