/**
 * Job Explorer Main Controller
 * Coordinates all job explorer functionality and initializes components
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.JobExplorerController = {
    // State management
    state: {
        selectedJob: null,
        currentSimilarityThreshold: 0.9,
        careerPathways: []
    },

    /**
     * Initialize the job explorer page
     */
    async init() {
        console.log('🚀 Loading Job Explorer...');
        
        try {
            // Wait for required modules to load
            await this.waitForModules();
            
            // Initialize UI functionality first
            if (SkillEngine.JobExplorerUI && SkillEngine.JobExplorerUI.init) {
                SkillEngine.JobExplorerUI.init();
            }
            
            // Initialize components
            this.initializeSearch();
            this.initializeSimilaritySlider();
            this.initializeSimilarityMethodRadios();
            this.initializeEventHandlers();
            
            console.log('✅ Job Explorer loaded');
        } catch (error) {
            console.error('❌ Error initializing Job Explorer:', error);
        }
    },

    /**
     * Wait for required modules to be available
     */
    async waitForModules() {
        const requiredModules = [
            () => window.SkillEngine?.SearchModule,
            () => window.SkillEngine?.ApiClient,
            () => window.SkillEngine?.DOMHelpers,
            () => window.SkillEngine?.JobExplorerUI,
            () => window.SkillEngine?.JobDetails,
            () => window.SkillEngine?.CareerPathways,
            () => window.SkillEngine?.StrategicIntelligence
        ];

        for (const checkModule of requiredModules) {
            let attempts = 0;
            while (!checkModule() && attempts < 50) {
                await new Promise(resolve => setTimeout(resolve, 100));
                attempts++;
            }
            
            if (!checkModule()) {
                throw new Error(`Required module not available after ${attempts} attempts`);
            }
        }
    },

    /**
     * Initialize search functionality
     */
    initializeSearch() {
        if (!window.SkillEngine?.SearchModule) {
            console.error('❌ SearchModule not available');
            return;
        }

        // Initialize unified search module
        SkillEngine.SearchModule.init({
            inputId: 'job-explorer-search',
            resultsId: 'job-explorer-dropdown',
            hiddenInputId: 'selected-job-explorer-job',
            onSelect: (selection) => {
                console.log('🔍 Job selected:', selection.jobId, selection.displayTitle);
                
                const job = {
                    id: selection.jobId,
                    title: selection.displayTitle,
                    function: selection.jobFunction || 'Unknown'
                };
                
                this.state.selectedJob = job;
                
                // Add job pill for single selection (clear any existing first)
                this.addJobPill(job);
                
                // Clear search input
                const searchInput = document.getElementById('job-explorer-search');
                if (searchInput) {
                    searchInput.value = '';
                }
                
                // Load job details
                if (SkillEngine.JobDetails) {
                    SkillEngine.JobDetails.showJobProfile(this.state.selectedJob);
                }
            },
            config: {
                showDetailedResults: true,
                maxResults: 10,
                apiEndpoint: '/api/career-analysis-jobs'
            }
        });
    },

    /**
     * Initialize similarity threshold slider
     */
    initializeSimilaritySlider() {
        const slider = document.getElementById('similarity-slider');
        const display = document.getElementById('similarity-percentage');
        
        if (slider && display) {
            let debounceTimer = null;
            
            // Update display immediately, debounce API calls
            slider.addEventListener('input', (e) => {
                const percentage = parseInt(e.target.value);
                display.textContent = `${percentage}%`;
                
                // Calculate threshold based on similarity method
                const similarityMethod = document.querySelector('input[name="job-explorer-similarity-method"]:checked')?.value || 'enhanced';
                let threshold;
                
                if (similarityMethod === 'literal') {
                    threshold = percentage / 100; // For literal, use percentage directly
                } else {
                    threshold = Math.max(0.1, (percentage / 100) * 0.2); // For enhanced, scale down
                }
                
                this.state.currentSimilarityThreshold = threshold;
                
                // Clear previous timer
                if (debounceTimer) {
                    clearTimeout(debounceTimer);
                }
                
                // Update career pathways with debounce if job is selected
                if (this.state.selectedJob) {
                    console.log(`🎛️ Similarity slider changed to: ${percentage}% → threshold: ${threshold} (${similarityMethod}, debouncing...)`);
                    debounceTimer = setTimeout(() => {
                        console.log(`🔄 Loading career pathways with threshold: ${threshold} (${similarityMethod})`);
                        SkillEngine.CareerPathways.displayFilteredCareerPathways(
                            this.state.selectedJob.id, 
                            threshold
                        );
                    }, 300); // 300ms debounce
                }
            });
            
            // Also handle slider release for immediate update
            slider.addEventListener('change', (e) => {
                if (debounceTimer) {
                    clearTimeout(debounceTimer);
                }
                
                if (this.state.selectedJob) {
                    const percentage = parseInt(e.target.value);
                    
                    // Calculate threshold based on similarity method
                    const similarityMethod = document.querySelector('input[name="job-explorer-similarity-method"]:checked')?.value || 'enhanced';
                    let threshold;
                    
                    if (similarityMethod === 'literal') {
                        threshold = percentage / 100; // For literal, use percentage directly
                    } else {
                        threshold = Math.max(0.1, (percentage / 100) * 0.2); // For enhanced, scale down
                    }
                    
                    console.log(`🎯 Slider released at: ${percentage}% → threshold: ${threshold} (${similarityMethod} method)`);
                    
                    // Update state and display
                    this.state.currentSimilarityThreshold = threshold;
                    SkillEngine.CareerPathways.displayFilteredCareerPathways(
                        this.state.selectedJob.id, 
                        threshold
                    );
                }
            });
            
            // Set initial display from slider value
            const initialPercentage = parseInt(slider.value);
            display.textContent = `${initialPercentage}%`;
            this.state.currentSimilarityThreshold = initialPercentage / 100;
        }
    },

    /**
     * Initialize similarity method radio buttons
     */
    initializeSimilarityMethodRadios() {
        if (SkillEngine.CareerPathways && SkillEngine.CareerPathways.initializeSimilarityMethodRadios) {
            SkillEngine.CareerPathways.initializeSimilarityMethodRadios();
        }
    },

    /**
     * Add a job pill to the UI (single selection for job explorer)
     */
    addJobPill(job) {
        const pillsContainer = document.getElementById('job-explorer-selected-pills');
        if (!pillsContainer) return;

        // Clear any existing pills (single selection)
        pillsContainer.innerHTML = '';

        const pill = document.createElement('div');
        pill.className = 'inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full border border-blue-200 transition-colors hover:bg-blue-200';
        pill.dataset.jobId = job.id;
        
        pill.innerHTML = `
            <span class="font-source">${job.title}</span>
            <button type="button" 
                    class="flex-shrink-0 ml-1 h-4 w-4 rounded-full inline-flex items-center justify-center text-blue-600 hover:bg-blue-200 hover:text-blue-800 focus:outline-none focus:bg-blue-200 focus:text-blue-800 transition-colors"
                    onclick="SkillEngine.JobExplorerController.removeJobPill('${job.id}')">
                <span class="sr-only">Remove ${job.title}</span>
                <svg class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                </svg>
            </button>
        `;
        
        pillsContainer.appendChild(pill);
        
        // Update hidden input
        const hiddenInput = document.getElementById('selected-job-explorer-job');
        if (hiddenInput) {
            hiddenInput.value = job.id;
        }
    },

    /**
     * Remove a job pill from the UI
     */
    removeJobPill(jobId) {
        const pillsContainer = document.getElementById('job-explorer-selected-pills');
        if (!pillsContainer) return;

        const pill = pillsContainer.querySelector(`[data-job-id="${jobId}"]`);
        if (pill) {
            pill.remove();
        }
        
        // Clear state
        this.state.selectedJob = null;
        
        // Clear hidden input
        const hiddenInput = document.getElementById('selected-job-explorer-job');
        if (hiddenInput) {
            hiddenInput.value = '';
        }
        
        // Hide job details if shown
        if (SkillEngine.JobDetails) {
            // Hide job profile content 
            const welcomeState = document.getElementById('welcome-state');
            const jobProfileContent = document.getElementById('job-profile-content');
            if (welcomeState) welcomeState.classList.remove('hidden');
            if (jobProfileContent) jobProfileContent.classList.add('hidden');
        }
    },

    /**
     * Initialize event handlers
     */
    initializeEventHandlers() {
        // Career pathway navigation button
        const careerPathwayBtn = document.getElementById('career-pathway-btn');
        if (careerPathwayBtn) {
            careerPathwayBtn.addEventListener('click', () => {
                if (this.state.selectedJob) {
                    const url = `/career-pathways?start=${this.state.selectedJob.id}`;
                    window.location.href = url;
                } else {
                    alert('Please select a job first');
                }
            });
        }

        // Export functionality
        const exportBtn = document.getElementById('export-analysis-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                if (this.state.selectedJob) {
                    SkillEngine.JobDetails.exportAnalysis(this.state.selectedJob);
                } else {
                    alert('Please select a job first');
                }
            });
        }
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('job-search')) {
        SkillEngine.JobExplorerController.init();
    }
});
