// Global utilities and shared functionality

// API helper functions
const API = {
    async get(url) {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
            }
        });
        return response.json();
    },

    async post(url, data) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        return response.json();
    },

    async put(url, data) {
        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        return response.json();
    },

    async delete(url) {
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        return response.json();
    }
};

// Notification system
const Notifications = {
    show(message, type = 'info', duration = 5000) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button type="button" class="close" onclick="this.parentElement.remove()">&times;</button>
        `;

        // Add to page
        let container = document.querySelector('.flash-messages');
        if (!container) {
            container = document.createElement('div');
            container.className = 'flash-messages';
            document.body.appendChild(container);
        }

        container.appendChild(notification);

        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);
    },

    success(message, duration) {
        this.show(message, 'success', duration);
    },

    error(message, duration) {
        this.show(message, 'danger', duration);
    },

    info(message, duration) {
        this.show(message, 'info', duration);
    }
};

// Form validation utilities
const Validation = {
    required(value, fieldName) {
        if (!value || value.trim() === '') {
            return `${fieldName} ist erforderlich`;
        }
        return null;
    },

    minLength(value, minLength, fieldName) {
        if (value && value.length < minLength) {
            return `${fieldName} muss mindestens ${minLength} Zeichen lang sein`;
        }
        return null;
    },

    isNumber(value, fieldName) {
        if (value && isNaN(parseInt(value))) {
            return `${fieldName} muss eine Zahl sein`;
        }
        return null;
    },

    range(value, min, max, fieldName) {
        const num = parseInt(value);
        if (num < min || num > max) {
            return `${fieldName} muss zwischen ${min} und ${max} liegen`;
        }
        return null;
    }
};

// Character calculation utilities
const CharacterCalcs = {
    calculateLife(strength, willpower) {
        return (strength + willpower) * 2 + 10;
    },

    calculateMaxStress(willpower) {
        return willpower * 3;
    },

    validateAttribute(value, attrName) {
        const errors = [
            Validation.required(value, attrName),
            Validation.isNumber(value, attrName),
            Validation.range(value, 1, 20, attrName)
        ].filter(e => e !== null);

        return errors.length > 0 ? errors[0] : null;
    }
};

// Image handling utilities
const ImageUtils = {
    // Convert file to base64
    fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                // Remove data URL prefix
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    },

    // Validate image file
    validateImageFile(file) {
        const maxSize = 16 * 1024 * 1024; // 16MB
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];

        if (file.size > maxSize) {
            return 'Bild darf maximal 16MB groß sein';
        }

        if (!allowedTypes.includes(file.type)) {
            return 'Nur JPEG, PNG, GIF und WebP Bilder sind erlaubt';
        }

        return null;
    },

    // Resize image if needed (basic implementation)
    resizeImage(file, maxWidth = 800, maxHeight = 600, quality = 0.8) {
        return new Promise((resolve) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();

            img.onload = () => {
                // Calculate new dimensions
                let { width, height } = img;

                if (width > maxWidth) {
                    height = (height * maxWidth) / width;
                    width = maxWidth;
                }

                if (height > maxHeight) {
                    width = (width * maxHeight) / height;
                    height = maxHeight;
                }

                // Set canvas size and draw image
                canvas.width = width;
                canvas.height = height;
                ctx.drawImage(img, 0, 0, width, height);

                // Convert back to blob
                canvas.toBlob(resolve, 'image/jpeg', quality);
            };

            img.src = URL.createObjectURL(file);
        });
    }
};

// Local storage utilities for caching
const Storage = {
    set(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
        } catch (error) {
            console.warn('Could not save to localStorage:', error);
        }
    },

    get(key) {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : null;
        } catch (error) {
            console.warn('Could not read from localStorage:', error);
            return null;
        }
    },

    remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.warn('Could not remove from localStorage:', error);
        }
    },

    clear() {
        try {
            localStorage.clear();
        } catch (error) {
            console.warn('Could not clear localStorage:', error);
        }
    }
};

// Debounce utility for input fields
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

// Throttle utility for events
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Format utilities
const Format = {
    // Format date for display
    formatDate(dateString) {
        if (!dateString) return 'Unbekannt';

        const date = new Date(dateString);
        return date.toLocaleDateString('de-DE', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Capitalize first letter
    capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    },

    // Truncate text
    truncate(text, maxLength = 50) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength - 3) + '...';
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add loading states to buttons
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (this.type === 'submit' || this.classList.contains('async-btn')) {
                this.classList.add('loading');
                this.disabled = true;

                // Remove loading state after 3 seconds as fallback
                setTimeout(() => {
                    this.classList.remove('loading');
                    this.disabled = false;
                }, 3000);
            }
        });
    });

    // Auto-hide flash messages
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(100%)';
            setTimeout(() => alert.remove(), 300);
        });
    }, 5000);

    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+S or Cmd+S to save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            const saveBtn = document.getElementById('btnSave');
            if (saveBtn && !saveBtn.disabled) {
                saveBtn.click();
            }
        }

        // Escape to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal[style*="block"]');
            modals.forEach(modal => {
                const closeBtn = modal.querySelector('.close');
                if (closeBtn) closeBtn.click();
            });
        }
    });
});

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    Notifications.error('Ein unerwarteter Fehler ist aufgetreten');
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    Notifications.error('Ein Netzwerkfehler ist aufgetreten');
    e.preventDefault();
});

// Export utilities to global scope
window.API = API;
window.Notifications = Notifications;
window.Validation = Validation;
window.CharacterCalcs = CharacterCalcs;
window.ImageUtils = ImageUtils;
window.Storage = Storage;
window.Format = Format;
window.debounce = debounce;
window.throttle = throttle;