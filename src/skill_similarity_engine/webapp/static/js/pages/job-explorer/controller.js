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
            
            // Initialize components
            this.initializeSearch();
            this.initializeSimilaritySlider();
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
            inputId: 'job-search-input',
            resultsId: 'job-search-results',
            hiddenInputId: 'selected-job-id',
            onSelect: (selection) => {
                console.log('🔍 Job selected:', selection.jobId, selection.displayTitle);
                this.state.selectedJob = {
                    id: selection.jobId,
                    title: selection.displayTitle,
                    function: selection.jobFunction || 'Unknown'
                };
                
                // Load job details
                SkillEngine.JobDetails.showJobProfile(this.state.selectedJob);
            }
        });
    },

    /**
     * Initialize similarity threshold slider
     */
    initializeSimilaritySlider() {
        const slider = document.getElementById('similarity-threshold');
        const display = document.getElementById('similarity-display');
        
        if (slider && display) {
            slider.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                this.state.currentSimilarityThreshold = value;
                display.textContent = `${Math.round(value * 100)}%`;
                
                // Update career pathways if job is selected
                if (this.state.selectedJob) {
                    SkillEngine.CareerPathways.displayFilteredCareerPathways(
                        this.state.selectedJob.id, 
                        value
                    );
                }
            });
            
            // Set initial display
            display.textContent = `${Math.round(this.state.currentSimilarityThreshold * 100)}%`;
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
    if (window.location.pathname.includes('job-explorer')) {
        SkillEngine.JobExplorerController.init();
    }
});
