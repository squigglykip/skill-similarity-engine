/**
 * Career Pathways Page Controller
 * Coordinates all modules for the career pathways page functionality
 * Extracted from career_pathways.html embedded script
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.CareerPathwaysController = {
    // State management
    state: {
        selectedJobs: new Map(),
        treeData: null,
        lastBuiltParameters: null,
        lastBuiltTree: null,
        lastClickedNode: null,
        selectedBreadcrumbIndex: null
    },

    /**
     * Initialize the career pathways page
     */
    async init() {
        console.log('🚀 Loading Career Pathway Explorer...');
        console.log('🔍 Available modules:', Object.keys(window.SkillEngine || {}));
        
        try {
            // Wait for all required modules to load
            await this.waitForModules();
            
            console.log('✅ All modules loaded, initializing components...');
            
            // Initialize components
            this.initializeJobSearch();
            this.initializeTreeControls();
            this.initializeOrganisationalFilters();
            
            // Initialize expandable content functionality
            if (window.SkillEngine?.ExpandableContent) {
                SkillEngine.ExpandableContent.init();
            }
            
            // Check for URL parameters after initialization
            setTimeout(() => {
                this.checkForStartParameter();
            }, 100);
            
            console.log('✅ Career Pathway Explorer loaded');
        } catch (error) {
            console.error('❌ Error initializing Career Pathways:', error);
        }
    },

    /**
     * Wait for required modules to be available
     */
    async waitForModules() {
        const requiredModules = [
            () => window.SkillEngine?.SearchModule,
            () => window.SkillEngine?.TreeVisualization,
            () => window.SkillEngine?.SkillsAnalysis
        ];

        for (const checkModule of requiredModules) {
            let attempts = 0;
            while (!checkModule() && attempts < 50) {
                await new Promise(resolve => setTimeout(resolve, 100));
                attempts++;
            }
            if (!checkModule()) {
                throw new Error('Required module failed to load after 5 seconds');
            }
        }
    },

    /**
     * Check for start parameter in URL and pre-select job
     */
    async checkForStartParameter() {
        const urlParams = new URLSearchParams(window.location.search);
        const startJobId = urlParams.get('start');
        
        if (!startJobId) {
            console.log('🔍 No start parameter found in URL');
            return;
        }

        console.log(`🎯 Found start parameter: ${startJobId} - auto-loading from Job Explorer`);
        
        try {
            const response = await fetch(`/api/job-details/${startJobId}`);
            const data = await response.json();
            
            if (data.job) {
                const job = {
                    id: data.job.id,
                    title: data.job.title,
                    family: data.job.family,
                    group: data.job.group || 'N/A'
                };
                
                console.log(`✅ Pre-selecting job from URL: ${job.title} (${job.id})`);
                
                // Add to selected jobs
                this.state.selectedJobs.set(job.id, job);
                this.addJobPill(job);
                this.updateSelectedJobsData();
                this.updateBuildTreeButton();
                
                // Auto-build tree after delay
                setTimeout(() => {
                    if (typeof this.buildCareerPathwayTree === 'function') {
                        this.buildCareerPathwayTree();
                    }
                }, 1000);
                
            } else {
                console.warn(`⚠️ Job not found for ID: ${startJobId}`, data);
            }
        } catch (error) {
            console.error(`❌ Error loading job ${startJobId}:`, error);
        }
    },

    /**
     * Initialize job search functionality
     */
    initializeJobSearch() {
        const searchInput = document.getElementById('pathway-job-search');
        if (!searchInput) {
            console.error('❌ Search input not found: pathway-job-search');
            return;
        }

        console.log('🔍 Initializing search functionality...');
        console.log('🔍 SkillEngine available:', typeof window.SkillEngine);
        console.log('🔍 SearchModule available:', typeof window.SkillEngine?.SearchModule);

        if (!window.SkillEngine?.SearchModule) {
            console.error('❌ SearchModule not available! Retrying in 100ms...');
            setTimeout(() => this.initializeJobSearch(), 100);
            return;
        }

        // Initialize unified search module
        SkillEngine.SearchModule.init({
            inputId: 'pathway-job-search',
            resultsId: 'pathway-job-dropdown',
            hiddenInputId: 'selected-pathway-jobs',
            onSelect: (selection) => {
                console.log('🔍 Job selected:', selection.jobId, selection.displayTitle);
                
                const job = {
                    id: selection.jobId,
                    title: selection.displayTitle,
                    family: selection.jobFunction || 'Unknown'
                };
                
                if (!this.state.selectedJobs.has(job.id)) {
                    this.state.selectedJobs.set(job.id, job);
                    this.addJobPill(job);
                    this.updateSelectedJobsData();
                    this.updateBuildTreeButton();
                    
                    searchInput.value = '';
                    this.updateURLWithSelectedJob(job.id);
                }
            },
            config: {
                showDetailedResults: true,
                maxResults: 10,
                apiEndpoint: '/api/career-analysis-jobs'
            }
        });

        // Initialize clear button
        const clearButton = document.getElementById('clear-pathway-jobs');
        if (clearButton) {
            clearButton.addEventListener('click', () => {
                this.clearAllJobs();
            });
        }
    },

    /**
     * Add a job pill to the UI
     */
    addJobPill(job) {
        const pillsContainer = document.getElementById('selected-job-pills');
        if (!pillsContainer) return;

        const pill = document.createElement('div');
        pill.className = 'inline-flex items-center gap-1 px-3 py-1 bg-red-100 text-red-800 text-sm font-medium rounded-full border border-red-200 transition-colors hover:bg-red-200';
        pill.dataset.jobId = job.id;
        
        pill.innerHTML = `
            <span class="font-source">${job.title}</span>
            <button type="button" 
                    class="flex-shrink-0 ml-1 h-4 w-4 rounded-full inline-flex items-center justify-center text-red-600 hover:bg-red-200 hover:text-red-800 focus:outline-none focus:bg-red-200 focus:text-red-800 transition-colors"
                    onclick="SkillEngine.CareerPathwaysController.removeJobPill('${job.id}')">
                <span class="sr-only">Remove ${job.title}</span>
                <svg class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                </svg>
            </button>
        `;
        
        pillsContainer.appendChild(pill);
    },

    /**
     * Remove a job pill
     */
    removeJobPill(jobId) {
        const pill = document.querySelector(`[data-job-id="${jobId}"]`);
        if (pill) {
            pill.remove();
            this.state.selectedJobs.delete(jobId);
            this.updateSelectedJobsData();
            this.updateBuildTreeButton();
        }
    },

    /**
     * Clear all selected jobs
     */
    clearAllJobs() {
        const pillsContainer = document.getElementById('selected-job-pills');
        if (pillsContainer) {
            pillsContainer.innerHTML = '';
        }
        
        this.state.selectedJobs.clear();
        this.updateSelectedJobsData();
        this.updateBuildTreeButton();
        
        const searchInput = document.getElementById('pathway-job-search');
        if (searchInput) {
            searchInput.placeholder = 'Search for job profiles...';
        }
    },

    /**
     * Update selected jobs data in hidden input
     */
    updateSelectedJobsData() {
        const hiddenInput = document.getElementById('selected-pathway-jobs');
        const searchInput = document.getElementById('pathway-job-search');
        
        if (hiddenInput) {
            hiddenInput.value = Array.from(this.state.selectedJobs.keys()).join(',');
        }
        
        if (searchInput) {
            const count = this.state.selectedJobs.size;
            searchInput.placeholder = count > 0 
                ? `Add another job profile... (${count} selected)`
                : 'Search for job profiles...';
        }
    },

    /**
     * Update URL with selected job for bookmarking
     */
    updateURLWithSelectedJob(jobId) {
        const url = new URL(window.location);
        const selectedIds = Array.from(this.state.selectedJobs.keys());
        
        if (selectedIds.length > 0) {
            url.searchParams.set('start', selectedIds[0]); // Use first job as start param
        } else {
            url.searchParams.delete('start');
        }
        
        window.history.replaceState({}, '', url);
    },

    /**
     * Update build tree button state
     */
    updateBuildTreeButton() {
        const buildButton = document.getElementById('build-pathway-tree');
        if (!buildButton) return;

        const hasJobs = this.state.selectedJobs.size > 0;
        
        if (hasJobs) {
            buildButton.disabled = false;
            buildButton.classList.remove('opacity-50', 'cursor-not-allowed');
            buildButton.classList.add('hover:bg-red-700');
            buildButton.innerHTML = `
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path>
                </svg>
                Build Career Tree (${this.state.selectedJobs.size} ${this.state.selectedJobs.size === 1 ? 'job' : 'jobs'})
            `;
        } else {
            buildButton.disabled = true;
            buildButton.classList.add('opacity-50', 'cursor-not-allowed');
            buildButton.classList.remove('hover:bg-red-700');
            buildButton.innerHTML = `
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                </svg>
                Select Jobs to Build Tree
            `;
        }
    },

    /**
     * Initialize tree controls (sliders, etc.)
     */
    initializeTreeControls() {
        // Delegate to TreeVisualization module
        if (SkillEngine.TreeVisualization) {
            SkillEngine.TreeVisualization.initializeControls();
        }
    },

    /**
     * Initialize organisational filters
     */
    initializeOrganisationalFilters() {
        // This will be moved to a separate module
        console.log('🔧 Organizational filters initialization deferred to TreeVisualization module');
    },

    /**
     * Build career pathway tree
     */
    async buildCareerPathwayTree() {
        if (SkillEngine.TreeVisualization) {
            const jobIds = Array.from(this.state.selectedJobs.keys());
            await SkillEngine.TreeVisualization.buildTree(jobIds);
        }
    }
};

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('pathway-job-search')) {
        SkillEngine.CareerPathwaysController.init();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SkillEngine.CareerPathwaysController;
}

console.log('✅ Career Pathways Controller loaded');
