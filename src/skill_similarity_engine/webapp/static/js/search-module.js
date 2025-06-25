/**
 * NAB Skills Intelligence Platform - Unified Search Module
 * Provides consistent job search functionality across all webapp pages
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.SearchModule = {
    // Configuration
    config: {
        searchDelay: 300,
        maxResults: 10,
        minQueryLength: 2,
        apiEndpoint: '/api/whitepaper-jobs', // Use the enhanced endpoint
        keyboardNavigation: true,
        showDetailedResults: true
    },

    // Active search instances
    instances: new Map(),

    /**
     * Initialize a search instance
     * @param {Object} options - Configuration options
     * @param {string} options.inputId - ID of the search input element
     * @param {string} options.resultsId - ID of the results container element
     * @param {string} options.hiddenInputId - ID of hidden input to store selected job ID (optional)
     * @param {Function} options.onSelect - Callback when job is selected
     * @param {Object} options.config - Override default configuration
     */
    init(options) {
        const {
            inputId,
            resultsId,
            hiddenInputId = null,
            onSelect = null,
            config = {}
        } = options;

        // Merge configuration
        const instanceConfig = { ...this.config, ...config };

        // Get DOM elements
        const inputElement = document.getElementById(inputId);
        const resultsElement = document.getElementById(resultsId);
        const hiddenInputElement = hiddenInputId ? document.getElementById(hiddenInputId) : null;

        if (!inputElement || !resultsElement) {
            console.error(`SearchModule: Could not find elements with IDs '${inputId}' or '${resultsId}'`);
            return null;
        }

        // Create instance
        const instance = {
            id: inputId,
            config: instanceConfig,
            elements: {
                input: inputElement,
                results: resultsElement,
                hiddenInput: hiddenInputElement
            },
            state: {
                isOpen: false,
                selectedIndex: -1,
                lastQuery: '',
                lastResults: []
            },
            callbacks: {
                onSelect: onSelect
            }
        };

        // Store instance
        this.instances.set(inputId, instance);

        // Initialize event handlers
        this.bindEvents(instance);

        console.log(`✅ SearchModule initialized for '${inputId}'`);
        return instance;
    },

    /**
     * Bind event handlers for a search instance
     */
    bindEvents(instance) {
        const { input, results, hiddenInput } = instance.elements;
        let searchTimeout;

        // Search input handler with debouncing
        input.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();

            if (query.length < instance.config.minQueryLength) {
                this.hideResults(instance);
                if (hiddenInput) {
                    hiddenInput.value = '';
                }
                return;
            }

            // Debounce search
            searchTimeout = setTimeout(() => {
                this.performSearch(instance, query);
            }, instance.config.searchDelay);
        });

        // Focus handler
        input.addEventListener('focus', () => {
            if (instance.state.lastQuery.length >= instance.config.minQueryLength) {
                this.showResults(instance);
            }
        });

        // Keyboard navigation
        if (instance.config.keyboardNavigation) {
            input.addEventListener('keydown', (e) => {
                this.handleKeydown(instance, e);
            });
        }

        // Click outside to close
        document.addEventListener('click', (e) => {
            if (!input.contains(e.target) && !results.contains(e.target)) {
                this.hideResults(instance);
            }
        });
    },

    /**
     * Perform search API call
     */
    async performSearch(instance, query) {
        try {
            console.log(`🔍 Searching for: "${query}"`);
            
            const url = `${instance.config.apiEndpoint}?search=${encodeURIComponent(query)}&limit=${instance.config.maxResults}`;
            const response = await fetch(url);
            const data = await response.json();

            if (data.success && data.jobs) {
                instance.state.lastQuery = query;
                instance.state.lastResults = data.jobs;
                instance.state.selectedIndex = -1;
                
                this.displayResults(instance, data.jobs);
            } else {
                this.displayNoResults(instance);
            }
        } catch (error) {
            console.error('SearchModule: Search error:', error);
            this.displayError(instance);
        }
    },

    /**
     * Display search results
     */
    displayResults(instance, jobs) {
        const { results } = instance.elements;

        if (jobs.length === 0) {
            this.displayNoResults(instance);
            return;
        }

        let html;
        
        if (instance.config.showDetailedResults) {
            // Detailed results (like white papers) - use standardised display names
            html = jobs.map((job, index) => {
                // Prefer standardised display names from JobDisplayManager
                const displayTitle = job.display_name_search || job.display_name_standard || 
                    job.name || job.title || job.job_title || 'Unknown Job';
                
                return `
                    <div class="search-result-item" 
                         data-index="${index}"
                         data-job-id="${job.id}"
                         data-display-title="${displayTitle}">
                        <div class="search-result-title">${displayTitle}</div>
                        <div class="search-result-meta">
                            <span class="search-result-function"><strong>Function:</strong> ${job.function || 'N/A'}</span>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            // Simple results (legacy compatibility) - use compact display names
            html = jobs.map((job, index) => {
                // Prefer compact display names for simple results
                const title = job.display_name_compact || job.display_name_standard || 
                    job.name || job.title || job.job_title || 'Unknown Job';
                return `
                    <div class="search-result-item" 
                         data-index="${index}"
                         data-job-id="${job.id}"
                         data-display-title="${title}">
                        <div class="search-result-title">${title}</div>
                        <div class="search-result-meta">
                            <strong>Function:</strong> ${job.function || job.job_function || 'N/A'}
                        </div>
                    </div>
                `;
            }).join('');
        }

        results.innerHTML = html;
        this.bindResultEvents(instance);
        this.showResults(instance);
    },

    /**
     * Display no results message
     */
    displayNoResults(instance) {
        const { results } = instance.elements;
        
        results.innerHTML = `
            <div class="search-no-results">
                <div class="search-no-results-icon">🔍</div>
                <div class="search-no-results-text">No job profiles found</div>
                <div class="search-no-results-hint">Try searching by job title or profile ID</div>
            </div>
        `;
        this.showResults(instance);
    },

    /**
     * Display error message
     */
    displayError(instance) {
        const { results } = instance.elements;
        
        results.innerHTML = `
            <div class="search-error">
                <div class="search-error-icon">⚠️</div>
                <div class="search-error-text">Search error occurred</div>
            </div>
        `;
        this.showResults(instance);
    },

    /**
     * Bind click events to result items
     */
    bindResultEvents(instance) {
        const { results } = instance.elements;
        
        results.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                this.selectResult(instance, item);
            });
        });
    },

    /**
     * Handle keyboard navigation
     */
    handleKeydown(instance, event) {
        const { results } = instance.elements;
        const items = results.querySelectorAll('.search-result-item');
        
        if (!instance.state.isOpen || items.length === 0) return;

        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                instance.state.selectedIndex = Math.min(
                    instance.state.selectedIndex + 1, 
                    items.length - 1
                );
                this.updateSelection(instance);
                break;
                
            case 'ArrowUp':
                event.preventDefault();
                instance.state.selectedIndex = Math.max(
                    instance.state.selectedIndex - 1, 
                    0
                );
                this.updateSelection(instance);
                break;
                
            case 'Enter':
                event.preventDefault();
                if (instance.state.selectedIndex >= 0) {
                    this.selectResult(instance, items[instance.state.selectedIndex]);
                }
                break;
                
            case 'Escape':
                this.hideResults(instance);
                break;
        }
    },

    /**
     * Update visual selection for keyboard navigation
     */
    updateSelection(instance) {
        const { results } = instance.elements;
        const items = results.querySelectorAll('.search-result-item');
        
        items.forEach((item, index) => {
            if (index === instance.state.selectedIndex) {
                item.classList.add('search-result-selected');
            } else {
                item.classList.remove('search-result-selected');
            }
        });
    },

    /**
     * Select a search result
     */
    selectResult(instance, item) {
        const jobId = item.dataset.jobId;
        const displayTitle = item.dataset.displayTitle;
        
        console.log(`✅ Selected job: ${jobId} - ${displayTitle}`);
        
        // Update input field
        instance.elements.input.value = displayTitle;
        
        // Update hidden input if exists
        if (instance.elements.hiddenInput) {
            instance.elements.hiddenInput.value = jobId;
        }
        
        // Hide results
        this.hideResults(instance);
        
        // Call custom callback
        if (instance.callbacks.onSelect) {
            instance.callbacks.onSelect({
                jobId: jobId,
                displayTitle: displayTitle,
                element: item
            });
        }
        
        // Trigger custom event for backward compatibility
        document.dispatchEvent(new CustomEvent('jobSelected', {
            detail: {
                jobId: jobId,
                jobName: displayTitle,
                instanceId: instance.id
            }
        }));
    },

    /**
     * Show results dropdown
     */
    showResults(instance) {
        instance.elements.results.classList.remove('hidden');
        instance.elements.results.style.display = 'block';
        instance.state.isOpen = true;
    },

    /**
     * Hide results dropdown
     */
    hideResults(instance) {
        instance.elements.results.classList.add('hidden');
        instance.elements.results.style.display = 'none';
        instance.state.isOpen = false;
        instance.state.selectedIndex = -1;
    },

    /**
     * Get instance by ID
     */
    getInstance(inputId) {
        return this.instances.get(inputId);
    },

    /**
     * Destroy an instance
     */
    destroy(inputId) {
        const instance = this.instances.get(inputId);
        if (instance) {
            // Remove event listeners would go here if needed
            this.instances.delete(inputId);
            console.log(`🗑️ SearchModule instance '${inputId}' destroyed`);
        }
    },

    /**
     * Update instance configuration
     */
    updateConfig(inputId, newConfig) {
        const instance = this.instances.get(inputId);
        if (instance) {
            instance.config = { ...instance.config, ...newConfig };
            console.log(`⚙️ SearchModule instance '${inputId}' config updated`);
        }
    }
};

// Auto-initialize search instances with data attributes
document.addEventListener('DOMContentLoaded', () => {
    // Look for elements with data-search-module attribute
    document.querySelectorAll('[data-search-module]').forEach(input => {
        const config = {
            inputId: input.id,
            resultsId: input.dataset.searchResults,
            hiddenInputId: input.dataset.searchHidden || null,
            config: {
                showDetailedResults: input.dataset.searchDetailed === 'true',
                maxResults: parseInt(input.dataset.searchLimit) || 10
            }
        };
        
        SkillEngine.SearchModule.init(config);
    });
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SkillEngine.SearchModule;
} 