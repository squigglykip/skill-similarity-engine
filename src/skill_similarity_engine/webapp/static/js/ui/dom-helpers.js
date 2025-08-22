/**
 * DOM Helper Utilities
 * Common DOM manipulation and utility functions
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.DOMHelpers = {
    /**
     * Safely get element by ID
     */
    getElementById(id) {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`Element with ID '${id}' not found`);
        }
        return element;
    },

    /**
     * Safely update element text content
     */
    updateElementText(id, text) {
        const element = this.getElementById(id);
        if (element) {
            element.textContent = text;
        }
    },

    /**
     * Safely update element HTML content
     */
    updateElementHTML(id, html) {
        const element = this.getElementById(id);
        if (element) {
            element.innerHTML = html;
        }
    },

    /**
     * Show loading state for an element
     */
    showLoading(elementId, loadingText = 'Loading...') {
        const element = this.getElementById(elementId);
        if (element) {
            element.innerHTML = `
                <div class="flex items-center justify-center py-4">
                    <div class="pathway-spinner"></div>
                    <span class="ml-3 text-gray-600">${loadingText}</span>
                </div>
            `;
        }
    },

    /**
     * Show error state for an element
     */
    showError(elementId, errorMessage) {
        const element = this.getElementById(elementId);
        if (element) {
            element.innerHTML = `
                <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div class="text-sm text-red-800">
                        <strong>Error:</strong> ${errorMessage}
                    </div>
                </div>
            `;
        }
    },

    /**
     * Create element with attributes and content
     */
    createElement(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);
        
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'dataset') {
                Object.entries(value).forEach(([dataKey, dataValue]) => {
                    element.dataset[dataKey] = dataValue;
                });
            } else {
                element.setAttribute(key, value);
            }
        });
        
        if (content) {
            element.innerHTML = content;
        }
        
        return element;
    },

    /**
     * Remove all children from element
     */
    clearElement(elementId) {
        const element = this.getElementById(elementId);
        if (element) {
            element.innerHTML = '';
        }
    },

    /**
     * Add event listener with error handling
     */
    addEventListener(elementId, event, handler) {
        const element = this.getElementById(elementId);
        if (element) {
            element.addEventListener(event, (e) => {
                try {
                    handler(e);
                } catch (error) {
                    console.error(`Error in event handler for ${elementId}:`, error);
                }
            });
        }
    },

    /**
     * Toggle element visibility
     */
    toggle(elementId, show = null) {
        const element = this.getElementById(elementId);
        if (element) {
            if (show === null) {
                element.classList.toggle('hidden');
            } else {
                element.classList.toggle('hidden', !show);
            }
        }
    },

    /**
     * Show element
     */
    show(elementId) {
        const element = this.getElementById(elementId);
        if (element) {
            element.classList.remove('hidden');
            element.style.display = '';
        }
    },

    /**
     * Hide element
     */
    hide(elementId) {
        const element = this.getElementById(elementId);
        if (element) {
            element.classList.add('hidden');
            element.style.display = 'none';
        }
    },

    /**
     * Wait for element to exist in DOM
     */
    async waitForElement(selector, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const element = document.querySelector(selector);
            if (element) {
                resolve(element);
                return;
            }

            const observer = new MutationObserver((mutations, obs) => {
                const element = document.querySelector(selector);
                if (element) {
                    obs.disconnect();
                    resolve(element);
                }
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });

            setTimeout(() => {
                observer.disconnect();
                reject(new Error(`Element ${selector} not found within ${timeout}ms`));
            }, timeout);
        });
    },

    /**
     * Debounce function calls
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function calls
     */
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Format numbers for display
     */
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    },

    /**
     * Format similarity score as percentage
     */
    formatSimilarity(score) {
        return `${Math.round(score * 100)}%`;
    },

    /**
     * Get similarity level for styling
     */
    getSimilarityLevel(score) {
        if (score >= 0.7) return 'high';
        if (score >= 0.4) return 'medium';
        return 'low';
    }
};

console.log('✅ DOM Helpers utility loaded');
