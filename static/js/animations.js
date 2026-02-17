/* =====================================================================
   FoodBot – Interactive Animation Effects (JavaScript)
   ===================================================================== */

// ==================== ELASTIC/GUMMI HOVER EFFEKT ====================
document.addEventListener('DOMContentLoaded', () => {
    // Elastic Hover Effekt (Maus-folge-Effekt)
    const elasticElements = document.querySelectorAll('.elastic-hover');
    
    elasticElements.forEach(el => {
        el.addEventListener('mousemove', (e) => {
            const rect = el.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            el.style.setProperty('--mouse-x', `${x}px`);
            el.style.setProperty('--mouse-y', `${y}px`);
        });
        
        el.addEventListener('mouseleave', () => {
            el.style.setProperty('--mouse-x', '50%');
            el.style.setProperty('--mouse-y', '50%');
        });
    });
    
    // ==================== MAGNETISCHER BUTTON EFFEKT ====================
    const magneticButtons = document.querySelectorAll('.magnetic-btn');
    
    magneticButtons.forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const rect = btn.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            
            const deltaX = (e.clientX - centerX) / (rect.width / 2);
            const deltaY = (e.clientY - centerY) / (rect.height / 2);
            
            btn.style.setProperty('--btn-x', deltaX.toFixed(2));
            btn.style.setProperty('--btn-y', deltaY.toFixed(2));
        });
        
        btn.addEventListener('mouseleave', () => {
            btn.style.setProperty('--btn-x', '0');
            btn.style.setProperty('--btn-y', '0');
        });
    });
    
    // ==================== 3D TILT EFFEKT ====================
    const tiltElements = document.querySelectorAll('.tilt-btn');
    
    tiltElements.forEach(el => {
        el.addEventListener('mousemove', (e) => {
            const rect = el.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            
            const deltaX = (e.clientY - centerY) / (rect.height / 2);
            const deltaY = -(e.clientX - centerX) / (rect.width / 2);
            
            const tiltX = deltaX * 15; // Max 15 Grad
            const tiltY = deltaY * 15;
            
            el.style.setProperty('--tilt-x', `${tiltX}deg`);
            el.style.setProperty('--tilt-y', `${tiltY}deg`);
        });
        
        el.addEventListener('mouseleave', () => {
            el.style.setProperty('--tilt-x', '0deg');
            el.style.setProperty('--tilt-y', '0deg');
        });
    });
    
    // ==================== RIPPLE EFFEKT FÜR ALLE BUTTONS ====================
    const rippleButtons = document.querySelectorAll('.ripple-btn');
    
    rippleButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            ripple.classList.add('ripple-effect');
            
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.5);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s ease-out;
                pointer-events: none;
            `;
            
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
    
    // ==================== FLOATING LABEL SUPPORT ====================
    const floatingInputs = document.querySelectorAll('.floating-label-input');
    
    floatingInputs.forEach(input => {
        // Bei Autofill-Erkennung Label anheben
        input.addEventListener('animationstart', (e) => {
            if (e.animationName === 'onAutoFillStart') {
                input.classList.add('has-value');
            }
        });
        
        // Prüfe ob Input Wert hat
        const checkValue = () => {
            if (input.value.trim() !== '') {
                input.classList.add('has-value');
            } else {
                input.classList.remove('has-value');
            }
        };
        
        input.addEventListener('input', checkValue);
        input.addEventListener('change', checkValue);
        checkValue(); // Initial check
    });
    
    // ==================== SHAKE ANIMATION FÜR FEHLER ====================
    window.shakeElement = (selector) => {
        const el = typeof selector === 'string' ? document.querySelector(selector) : selector;
        if (el) {
            el.classList.add('shake');
            setTimeout(() => el.classList.remove('shake'), 500);
        }
    };
    
    // ==================== GLITCH EFFEKT FÜR FEHLER ====================
    window.glitchElement = (selector, duration = 1000) => {
        const el = typeof selector === 'string' ? document.querySelector(selector) : selector;
        if (el) {
            el.classList.add('glitch');
            setTimeout(() => el.classList.remove('glitch'), duration);
        }
    };
    
    // ==================== SMOOTH SCROLL ====================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href !== '') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    // ==================== LAZY ANIMATION ON SCROLL ====================
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fadeIn');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Beobachte alle Elemente mit .lazy-animate Klasse
    document.querySelectorAll('.lazy-animate').forEach(el => {
        observer.observe(el);
    });
});

// ==================== CSS RIPPLE ANIMATION ====================
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ==================== AUTO-FILL DETECTION FÜR FLOATING LABELS ====================
const autoFillStyle = document.createElement('style');
autoFillStyle.textContent = `
    @keyframes onAutoFillStart {
        from { /*dummy*/ }
        to { /*dummy*/ }
    }
    
    input:-webkit-autofill {
        animation-name: onAutoFillStart;
    }
`;
document.head.appendChild(autoFillStyle);

// ==================== PERFORMANCE: REDUCE MOTION ====================
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.documentElement.style.setProperty('--transition-fast', '0.01ms');
    document.documentElement.style.setProperty('--transition-base', '0.01ms');
    document.documentElement.style.setProperty('--transition-slow', '0.01ms');
}

console.log('🎨 FoodBot Enhanced Animations loaded');
