/**
 * Career Analysis V2 Controller
 * Coordinates all functionality for the new career analysis page
 * Following the established SkillEngine architecture pattern
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.CareerAnalysisV2Controller = {
    // State management
    state: {
        selectedSourceJob: null,
        selectedTargetJobs: [],
        currentAnalysisMode: 'top_matches',
        isGenerating: false,
        lastFormData: null,
        validationErrors: []
    },

    /**
     * Initialize the Career Analysis V2 page
     */
    async init() {
        console.log('🚀 Loading Career Analysis V2 Generator...');
        console.log('🔍 Available modules:', Object.keys(window.SkillEngine || {}));
        
        try {
            // Wait for required modules to load
            await this.waitForModules();
            
            console.log('✅ All modules loaded, initializing components...');
            
            // Initialize core components
            this.initializeSearch();
            this.initializeAnalysisModeToggle();
            this.initializeRangeSliders();
            this.initializeFormValidation();
            this.initializeEventHandlers();
            this.initializeV2Analytics();
            
            // Initialize dynamic updates
            this.setupDynamicUpdates();
            
            console.log('✅ Career Analysis V2 loaded successfully');
        } catch (error) {
            console.error('❌ Error initializing Career Analysis V2:', error);
        }
    },

    /**
     * Wait for required modules to be available
     */
    async waitForModules() {
        const requiredModules = [
            () => window.SkillEngine?.SearchModule,
            () => window.SkillEngine?.ApiClient,
            () => window.SkillEngine?.DOMHelpers
        ];

        for (const checkModule of requiredModules) {
            let attempts = 0;
            while (!checkModule() && attempts < 50) {
                await new Promise(resolve => setTimeout(resolve, 100));
                attempts++;
            }
            if (!checkModule()) {
                throw new Error(`Required module failed to load after ${attempts} attempts`);
            }
        }
    },

    /**
     * Initialize job search functionality
     */
    initializeSearch() {
        if (!window.SkillEngine?.SearchModule) {
            console.error('❌ SearchModule not available');
            return;
        }

        // Initialize source job search
        SkillEngine.SearchModule.init({
            inputId: 'jobFromSearch',
            resultsId: 'jobFromResults',
            hiddenInputId: 'jobFrom',
            onSelect: (selection) => {
                console.log('🔍 Source job selected:', selection.jobId, selection.displayTitle);
                this.state.selectedSourceJob = {
                    id: selection.jobId,
                    title: selection.displayTitle,
                    function: selection.jobFunction || 'Unknown'
                };
                this.validateForm();
            },
            config: {
                showDetailedResults: true,
                maxResults: 10,
                apiEndpoint: '/api/career-analysis-jobs'
            }
        });

        // Initialize target job search (for specific transition mode)
        SkillEngine.SearchModule.init({
            inputId: 'jobToSearch',
            resultsId: 'jobToResults',
            hiddenInputId: 'jobTo',
            onSelect: (selection) => {
                console.log('🔍 Target job selected:', selection.jobId, selection.displayTitle);
                this.addTargetJob(selection);
            },
            config: {
                showDetailedResults: true,
                maxResults: 10,
                apiEndpoint: '/api/career-analysis-jobs'
            }
        });
    },

    /**
     * Add target job for specific transition mode
     */
    addTargetJob(selection) {
        const targetJob = {
            id: selection.jobId,
            title: selection.displayTitle,
            function: selection.jobFunction || 'Unknown'
        };

        // Check if already selected
        if (this.state.selectedTargetJobs.find(job => job.id === targetJob.id)) {
            console.log('🔍 Job already selected:', targetJob.id);
            return;
        }

        // Add to state
        this.state.selectedTargetJobs.push(targetJob);

        // Update UI
        this.updateTargetJobsDisplay();
        
        // Clear search input
        const searchInput = document.getElementById('jobToSearch');
        if (searchInput) {
            searchInput.value = '';
        }

        // Update hidden field
        this.updateTargetJobsHiddenField();
        
        console.log('🔍 Updated selected target jobs:', this.state.selectedTargetJobs);
    },

    /**
     * Remove target job
     */
    removeTargetJob(jobId) {
        this.state.selectedTargetJobs = this.state.selectedTargetJobs.filter(job => job.id !== jobId);
        this.updateTargetJobsDisplay();
        this.updateTargetJobsHiddenField();
        this.validateForm();
        console.log('🔍 Removed target job:', jobId, 'Remaining:', this.state.selectedTargetJobs);
    },

    /**
     * Update target jobs visual display
     */
    updateTargetJobsDisplay() {
        const container = document.getElementById('selectedTargets');
        if (!container) return;

        container.innerHTML = '';
        
        this.state.selectedTargetJobs.forEach(job => {
            const chip = document.createElement('div');
            chip.className = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800';
            chip.innerHTML = `
                <span class="mr-2">${job.title}</span>
                <button type="button" onclick="SkillEngine.CareerAnalysisV2Controller.removeTargetJob('${job.id}')" 
                        class="inline-flex items-center justify-center w-4 h-4 ml-1 text-red-600 hover:text-red-800 hover:bg-red-200 rounded-full">
                    <i class="fas fa-times text-xs"></i>
                </button>
            `;
            container.appendChild(chip);
        });
    },

    /**
     * Update hidden field for form submission
     */
    updateTargetJobsHiddenField() {
        const hiddenField = document.getElementById('jobTo');
        if (hiddenField) {
            hiddenField.value = this.state.selectedTargetJobs.map(job => job.id).join(',');
        }
    },

    /**
     * Initialize analysis mode toggle functionality
     */
    initializeAnalysisModeToggle() {
        const modeRadios = document.querySelectorAll('input[name="analysis_mode"]');
        
        modeRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.state.currentAnalysisMode = e.target.value;
                this.handleAnalysisModeChange(e.target.value);
            });
        });
    },

    /**
     * Handle analysis mode change
     */
    handleAnalysisModeChange(mode) {
        const targetJobSection = document.getElementById('targetJobSection');
        const topNSection = document.getElementById('topNSection');
        const topNInput = document.getElementById('topN');
        const discoveryModeLabel = document.getElementById('discoveryModeLabel');
        const pathwayCountText = document.getElementById('pathwayCountText');

        if (mode === 'specific') {
            // Show target job section
            targetJobSection?.classList.remove('hidden');
            
            // Disable pathway count (always 1 for specific)
            if (topNInput) {
                topNInput.disabled = true;
                topNInput.value = 1;
                this.updateTopNDisplay(1);
            }
        } else {
            // Hide target job section
            targetJobSection?.classList.add('hidden');
            
            // Clear target jobs
            this.state.selectedTargetJobs = [];
            this.updateTargetJobsDisplay();
            this.updateTargetJobsHiddenField();
            
            // Enable pathway count
            if (topNInput) {
                topNInput.disabled = false;
                this.updateTopNDisplay(parseInt(topNInput.value) || 3);
            }
        }

        this.validateForm();
    },

    /**
     * Initialize range sliders for similarity configuration
     */
    initializeRangeSliders() {
        // Pathway count slider
        const topNSlider = document.getElementById('topN');
        if (topNSlider) {
            topNSlider.addEventListener('input', (e) => {
                this.updateTopNDisplay(parseInt(e.target.value));
            });
        }

        // Similarity range sliders
        const minSlider = document.getElementById('similarityMin');
        const maxSlider = document.getElementById('similarityMax');
        
        if (minSlider && maxSlider) {
            minSlider.addEventListener('input', () => this.updateSimilarityRange());
            maxSlider.addEventListener('input', () => this.updateSimilarityRange());
            
            // Initialize display
            this.updateSimilarityRange();
        }
    },

    /**
     * Update pathway count display
     */
    updateTopNDisplay(value) {
        const displays = ['topNDisplay', 'pathwayCountText', 'discoveryModeLabel'];
        displays.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    },

    /**
     * Update similarity range display
     */
    updateSimilarityRange() {
        const minSlider = document.getElementById('similarityMin');
        const maxSlider = document.getElementById('similarityMax');
        const display = document.getElementById('similarityRangeDisplay');
        
        if (!minSlider || !maxSlider || !display) return;

        let minVal = parseInt(minSlider.value);
        let maxVal = parseInt(maxSlider.value);

        // Ensure min is less than max
        if (minVal >= maxVal) {
            minVal = maxVal - 5;
            minSlider.value = minVal;
        }

        display.textContent = `${minVal}% - ${maxVal}%`;
        
        // Update range fill visualization if it exists
        this.updateRangeFill(minVal, maxVal);
    },

    /**
     * Update range slider fill visualization
     */
    updateRangeFill(min, max) {
        const rangeFill = document.querySelector('.range-fill');
        if (!rangeFill) return;

        const minPercent = (min / 100) * 100;
        const maxPercent = (max / 100) * 100;
        
        rangeFill.style.left = `${minPercent}%`;
        rangeFill.style.width = `${maxPercent - minPercent}%`;
    },

    /**
     * Initialize form validation
     */
    initializeFormValidation() {
        const form = document.getElementById('careerAnalysisForm');
        if (!form) return;

        // Real-time validation on form changes
        form.addEventListener('input', () => {
            this.validateForm();
        });

        form.addEventListener('change', () => {
            this.validateForm();
        });
    },

    /**
     * Validate the form and update button states
     */
    validateForm() {
        const errors = [];
        
        // Validate source job
        if (!this.state.selectedSourceJob) {
            errors.push('Please select a source job profile');
        }

        // Validate target jobs for specific mode
        if (this.state.currentAnalysisMode === 'specific' && this.state.selectedTargetJobs.length === 0) {
            errors.push('Please select at least one target job for specific transition analysis');
        }

        // Validate similarity range
        const minSlider = document.getElementById('similarityMin');
        const maxSlider = document.getElementById('similarityMax');
        if (minSlider && maxSlider) {
            const min = parseInt(minSlider.value);
            const max = parseInt(maxSlider.value);
            if (min >= max) {
                errors.push('Maximum similarity must be greater than minimum');
            }
        }

        this.state.validationErrors = errors;
        this.updateButtonStates(errors.length === 0);
        this.displayValidationMessages(errors);

        return errors.length === 0;
    },

    /**
     * Update button states based on validation
     */
    updateButtonStates(isValid) {
        const previewBtn = document.getElementById('previewBtn');
        const generateBtn = document.getElementById('generateBtn');

        if (previewBtn) {
            previewBtn.disabled = !isValid || this.state.isGenerating;
            previewBtn.textContent = this.state.isGenerating ? 'Generating...' : 'Preview Analysis';
        }

        if (generateBtn) {
            generateBtn.disabled = !isValid || this.state.isGenerating;
            generateBtn.textContent = this.state.isGenerating ? 'Generating...' : 'Generate Word Document';
        }
    },

    /**
     * Display validation messages
     */
    displayValidationMessages(errors) {
        const container = document.getElementById('validationMessages');
        if (!container) return;

        container.innerHTML = '';

        if (errors.length === 0) {
            // Show success message if form is valid and source job selected
            if (this.state.selectedSourceJob) {
                const successDiv = document.createElement('div');
                successDiv.className = 'flex items-center p-3 text-sm text-green-800 bg-green-100 rounded-md';
                successDiv.innerHTML = `
                    <i class="fas fa-check-circle mr-2"></i>
                    <span>Configuration valid - ready to generate analysis</span>
                `;
                container.appendChild(successDiv);
            }
            return;
        }

        // Show error messages
        errors.forEach(error => {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'flex items-center p-3 text-sm text-red-800 bg-red-100 rounded-md';
            errorDiv.innerHTML = `
                <i class="fas fa-exclamation-triangle mr-2"></i>
                <span>${error}</span>
            `;
            container.appendChild(errorDiv);
        });
    },

    /**
     * Initialize event handlers
     */
    initializeEventHandlers() {
        // Preview button
        const previewBtn = document.getElementById('previewBtn');
        if (previewBtn) {
            previewBtn.addEventListener('click', () => this.handlePreview());
        }

        // Generate button
        const generateBtn = document.getElementById('generateBtn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.handleGenerate());
        }

        // Close preview button
        const closePreview = document.getElementById('closePreview');
        if (closePreview) {
            closePreview.addEventListener('click', () => this.hidePreview());
        }
    },

    /**
     * Initialize V2 analytics checkboxes
     */
    initializeV2Analytics() {
        // All V2 analytics are checked by default, just track state changes
        const checkboxes = document.querySelectorAll('input[name^="v2_"]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateEstimatedTime();
            });
        });
        
        this.updateEstimatedTime();
    },

    /**
     * Update estimated generation time based on configuration
     */
    updateEstimatedTime() {
        const v2Checkboxes = document.querySelectorAll('input[name^="v2_"]:checked');
        const topN = parseInt(document.getElementById('topN')?.value) || 3;
        
        let baseTime = 90; // Base 90 seconds
        baseTime += v2Checkboxes.length * 15; // 15 seconds per V2 feature
        baseTime += topN * 10; // 10 seconds per pathway
        
        const minutes = Math.ceil(baseTime / 60);
        const timeText = minutes === 1 ? '1-2 minutes' : `${minutes}-${minutes + 1} minutes`;
        
        const timeDisplay = document.getElementById('estimatedTime');
        if (timeDisplay) {
            timeDisplay.textContent = timeText;
        }
    },

    /**
     * Setup dynamic updates
     */
    setupDynamicUpdates() {
        // Update discovery mode labels when pathway count changes
        const topNSlider = document.getElementById('topN');
        if (topNSlider) {
            topNSlider.addEventListener('input', () => {
                this.updateEstimatedTime();
            });
        }

        // Update algorithm descriptions
        const algorithmRadios = document.querySelectorAll('input[name="primary_algorithm"]');
        algorithmRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                console.log('🔧 Algorithm changed to:', radio.value);
            });
        });
    },

    /**
     * Handle preview generation
     */
    async handlePreview() {
        if (!this.validateForm()) {
            console.warn('❌ Form validation failed');
            return;
        }

        this.state.isGenerating = true;
        this.updateButtonStates(false);
        this.showLoadingSpinner();

        try {
            const formData = this.collectFormData();
            this.state.lastFormData = formData;
            
            console.log('🔄 Generating preview with data:', formData);
            
            const response = await fetch('/api/career-analysis-preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.displayPreview(result);
                console.log('✅ Preview generated successfully');
            } else {
                throw new Error(result.error || 'Unknown error');
            }
            
        } catch (error) {
            console.error('❌ Preview generation failed:', error);
            this.displayError(`Failed to generate preview: ${error.message}`);
        } finally {
            this.state.isGenerating = false;
            this.updateButtonStates(true);
            this.hideLoadingSpinner();
        }
    },

    /**
     * Handle document generation
     */
    async handleGenerate() {
        if (!this.validateForm()) {
            console.warn('❌ Form validation failed');
            return;
        }

        this.showProgressModal();

        try {
            const formData = this.collectFormData();
            
            console.log('🔄 Generating document with data:', formData);
            
            const response = await fetch('/api/career-analysis-document', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Handle file download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `career-analysis-${Date.now()}.docx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            console.log('✅ Document generated and downloaded successfully');
            
        } catch (error) {
            console.error('❌ Document generation failed:', error);
            this.displayError(`Failed to generate document: ${error.message}`);
        } finally {
            this.hideProgressModal();
        }
    },

    /**
     * Collect form data for submission
     */
    collectFormData() {
        const formData = {
            // Required fields
            job_from: this.state.selectedSourceJob?.id || document.getElementById('jobFrom')?.value,
            analysis_mode: this.state.currentAnalysisMode,
            top_n: parseInt(document.getElementById('topN')?.value) || 3,
            similarity_min: parseInt(document.getElementById('similarityMin')?.value) || 0,
            similarity_max: parseInt(document.getElementById('similarityMax')?.value) || 95,
            primary_algorithm: document.querySelector('input[name="primary_algorithm"]:checked')?.value || 'enhanced',
            
            // V2 analytics configuration
            v2_analytics: {
                defining_skills: document.getElementById('includeDefiningSkills')?.checked || false,
                job_family_context: document.getElementById('includeJobFamilies')?.checked || false,
                movement_patterns: document.getElementById('includeMovementPatterns')?.checked || false,
                skills_rarity: document.getElementById('includeSkillsRarity')?.checked || false,
                transition_insights: document.getElementById('includeTransitionInsights')?.checked || false,
                dual_similarity_analysis: document.getElementById('includeDualSimilarity')?.checked || false
            }
        };

        // Add target jobs for specific transition mode
        if (this.state.currentAnalysisMode === 'specific' && this.state.selectedTargetJobs.length > 0) {
            formData.job_to = this.state.selectedTargetJobs.map(job => job.id).join(',');
        }

        return formData;
    },

    /**
     * Display preview content
     */
    displayPreview(result) {
        console.log('🎨 Displaying preview with result:', result);
        
        const previewPanel = document.getElementById('previewPanel');
        const previewContent = document.getElementById('previewContent');
        const placeholder = document.getElementById('preview-placeholder');
        
        if (!previewPanel || !previewContent) {
            console.error('❌ Preview panel elements not found');
            return;
        }

        // Hide placeholder
        if (placeholder) {
            placeholder.style.display = 'none';
        }

        // Show preview panel
        previewPanel.classList.remove('hidden');
        
        // Debug the result structure
        console.log('🎨 Result keys:', Object.keys(result));
        console.log('🎨 Result.content:', result.content);
        
        // Render preview content
        const htmlContent = this.renderPreviewHTML(result.content);
        console.log('🎨 Generated HTML length:', htmlContent.length);
        
        previewContent.innerHTML = htmlContent;
        
        // Scroll to preview
        previewPanel.scrollIntoView({ behavior: 'smooth' });
    },

    /**
     * Render preview HTML from result data
     */
    renderPreviewHTML(content) {
        if (!content) return '<p class="text-gray-500">No content available</p>';

        let html = '';
        
        console.log('🎨 Rendering preview content:', content);
        
        // Render each section
        Object.keys(content).forEach(sectionKey => {
            const section = content[sectionKey];
            console.log(`🎨 Processing section: ${sectionKey}`, section);
            
            if (section) {
                // Handle sections with direct content
                if (section.content) {
                    html += this.renderSection(sectionKey, section.title || this.formatSectionTitle(sectionKey), section.content);
                }
                // Handle sections with subsections (main case for our content)
                else if (section.subsections && typeof section.subsections === 'object') {
                    html += `<div class="mb-8 bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
                        <div class="bg-gradient-to-r from-red-600 to-red-700 px-6 py-4">
                            <h3 class="text-xl font-bold text-white flex items-center">
                                <i class="fas fa-chart-line mr-3"></i>
                                ${section.title || this.formatSectionTitle(sectionKey)}
                            </h3>
                        </div>
                        <div class="p-6 space-y-6">`;
                    
                    Object.keys(section.subsections).forEach(subKey => {
                        const subsection = section.subsections[subKey];
                        console.log(`🎨 Processing subsection: ${subKey}`, subsection);
                        
                        if (subsection) {
                            if (subsection.content) {
                                html += this.renderSubsection(subKey, subsection.title || this.formatSectionTitle(subKey), subsection.content);
                            } else if (typeof subsection === 'string') {
                                html += this.renderSubsection(subKey, this.formatSectionTitle(subKey), subsection);
                            } else if (Array.isArray(subsection)) {
                                html += this.renderSubsection(subKey, this.formatSectionTitle(subKey), subsection);
                            }
                        }
                    });
                    
                    html += '</div></div>';
                }
                // Handle sections that are direct content (V2 analytics style)
                else if (typeof section === 'object' && !Array.isArray(section)) {
                    // Check if this is a subsection object with direct content
                    const subsectionKeys = Object.keys(section);
                    if (subsectionKeys.length > 0) {
                        html += `<div class="mb-8">
                            <h3 class="text-lg font-semibold text-gray-900 mb-4">${this.formatSectionTitle(sectionKey)}</h3>
                            <div class="space-y-4">`;
                        
                        subsectionKeys.forEach(subKey => {
                            const subsection = section[subKey];
                            if (subsection && subsection.content) {
                                html += this.renderSubsection(subKey, subsection.title || this.formatSectionTitle(subKey), subsection.content);
                            }
                        });
                        
                        html += '</div></div>';
                    }
                }
                // Handle direct content
                else if (typeof section === 'string') {
                    html += this.renderSection(sectionKey, this.formatSectionTitle(sectionKey), section);
                }
            }
        });

        return html || '<div class="text-center py-8"><p class="text-gray-500">Preview content generated but no displayable sections found</p><details class="mt-4 text-left"><summary class="cursor-pointer text-blue-600">Show raw data</summary><pre class="mt-2 p-4 bg-gray-100 rounded text-xs overflow-auto">' + JSON.stringify(content, null, 2) + '</pre></details></div>';
    },

    /**
     * Render a section
     */
    renderSection(sectionKey, title, content) {
        return `
            <div class="mb-8 bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
                <div class="bg-gradient-to-r from-red-600 to-red-700 px-6 py-4">
                    <h3 class="text-xl font-bold text-white flex items-center">
                        <i class="fas fa-chart-line mr-3"></i>
                        ${title}
                    </h3>
                </div>
                <div class="p-6">
                    <div class="prose prose-gray max-w-none">
                        ${this.formatContent(content)}
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Render a subsection
     */
    renderSubsection(subKey, title, content) {
        return `
            <div class="mb-6 p-4 bg-gray-50 rounded-lg border-l-4 border-blue-400">
                <h4 class="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <i class="fas fa-chevron-right text-blue-600 mr-2"></i>
                    ${title}
                </h4>
                <div class="text-gray-700 leading-relaxed">
                    ${this.formatContent(content)}
                </div>
            </div>
        `;
    },

    /**
     * Format content based on type
     */
    formatContent(content) {
        if (typeof content === 'string') {
            // Convert newlines to proper HTML
            return content.replace(/\n/g, '<br>');
        } else if (Array.isArray(content)) {
            // Handle array content (like opportunities or structured content)
            return content.map(item => {
                if (typeof item === 'string') {
                    return `<p class="mb-2">${item}</p>`;
                } else if (typeof item === 'object') {
                    // Handle structured content objects
                    if (item.type === 'table' && item.headers && item.rows) {
                        return this.renderTable(item);
                    } else if (item.type === 'paragraph' && item.content) {
                        return `<div class="mb-4 p-3 bg-white rounded-lg border border-gray-200">
                            <p class="text-gray-700 leading-relaxed">${item.content.replace(/\n/g, '<br>')}</p>
                        </div>`;
                    } else if (item.content) {
                        return `<div class="mb-3">
                            <h5 class="font-medium text-gray-700 mb-1">${item.title || 'Item'}</h5>
                            <p class="text-gray-600">${item.content}</p>
                        </div>`;
                    } else {
                        // Handle opportunity objects or other structured data
                        return `<div class="mb-3 p-3 bg-blue-50 rounded-lg border-l-4 border-blue-400">
                            ${Object.keys(item).map(key => 
                                `<div class="mb-1">
                                    <strong class="text-blue-700">${this.formatSectionTitle(key)}:</strong>
                                    <span class="ml-2 text-gray-700">${this.formatContent(item[key])}</span>
                                </div>`
                            ).join('')}
                        </div>`;
                    }
                }
                return `<p class="mb-2">${JSON.stringify(item)}</p>`;
            }).join('');
        } else if (typeof content === 'object') {
            // Handle structured content objects
            if (content.type === 'table' && content.headers && content.rows) {
                return this.renderTable(content);
            } else if (content.type === 'paragraph' && content.content) {
                return `<div class="mb-4 p-3 bg-white rounded-lg border border-gray-200">
                    <p class="text-gray-700 leading-relaxed">${content.content.replace(/\n/g, '<br>')}</p>
                </div>`;
            } else {
                // Handle generic object content
                return Object.keys(content).map(key => {
                    return `<div class="mb-2">
                        <strong class="text-gray-700">${this.formatSectionTitle(key)}:</strong>
                        <span class="ml-2">${this.formatContent(content[key])}</span>
                    </div>`;
                }).join('');
            }
        }
        
        return content.toString();
    },

    /**
     * Render a table from structured data
     */
    renderTable(tableData) {
        if (!tableData.headers || !tableData.rows) return '';
        
        return `
            <div class="overflow-x-auto mb-6 shadow-sm rounded-lg border border-gray-200">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gradient-to-r from-blue-50 to-indigo-50">
                        <tr>
                            ${tableData.headers.map(header => 
                                `<th class="px-6 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wider">
                                    ${header}
                                </th>`
                            ).join('')}
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        ${tableData.rows.map((row, index) => 
                            `<tr class="hover:bg-blue-50 transition-colors duration-150 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}">
                                ${row.map(cell => 
                                    `<td class="px-6 py-4 text-sm text-gray-900 whitespace-nowrap">
                                        ${cell}
                                    </td>`
                                ).join('')}
                            </tr>`
                        ).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    /**
     * Format section title for display
     */
    formatSectionTitle(key) {
        return key
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase())
            .replace(/([A-Z])/g, ' $1')
            .trim();
    },

    /**
     * Hide preview panel
     */
    hidePreview() {
        const previewPanel = document.getElementById('previewPanel');
        if (previewPanel) {
            previewPanel.classList.add('hidden');
        }
    },

    /**
     * Show loading spinner
     */
    showLoadingSpinner() {
        const spinner = document.getElementById('loadingSpinner');
        const placeholder = document.getElementById('preview-placeholder');
        
        if (spinner) {
            spinner.classList.remove('hidden');
        }
        if (placeholder) {
            placeholder.style.display = 'none';
        }
    },

    /**
     * Hide loading spinner
     */
    hideLoadingSpinner() {
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) {
            spinner.classList.add('hidden');
        }
    },

    /**
     * Show progress modal
     */
    showProgressModal() {
        const modal = document.getElementById('progressModal');
        if (modal) {
            modal.classList.remove('hidden');
            this.updateProgress(0, 'Initialising analysis...');
            
            // Simulate progress updates
            let progress = 0;
            const interval = setInterval(() => {
                progress += Math.random() * 15;
                if (progress >= 90) {
                    progress = 90;
                    clearInterval(interval);
                }
                this.updateProgress(progress, this.getProgressMessage(progress));
            }, 1000);
            
            this.progressInterval = interval;
        }
    },

    /**
     * Hide progress modal
     */
    hideProgressModal() {
        const modal = document.getElementById('progressModal');
        if (modal) {
            modal.classList.add('hidden');
        }
        
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
    },

    /**
     * Update progress bar
     */
    updateProgress(percent, message) {
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        
        if (progressBar) {
            progressBar.style.width = `${Math.min(percent, 100)}%`;
        }
        
        if (progressText) {
            progressText.textContent = message;
        }
    },

    /**
     * Get progress message based on completion percentage
     */
    getProgressMessage(percent) {
        if (percent < 20) return 'Initialising analysis...';
        if (percent < 40) return 'Analysing job requirements...';
        if (percent < 60) return 'Generating career pathways...';
        if (percent < 80) return 'Building strategic recommendations...';
        return 'Finalising document...';
    },

    /**
     * Display error message
     */
    displayError(message) {
        const container = document.getElementById('validationMessages');
        if (!container) {
            alert(message);
            return;
        }

        const errorDiv = document.createElement('div');
        errorDiv.className = 'flex items-center p-3 text-sm text-red-800 bg-red-100 rounded-md';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle mr-2"></i>
            <span>${message}</span>
        `;
        container.appendChild(errorDiv);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (container.contains(errorDiv)) {
                container.removeChild(errorDiv);
            }
        }, 10000);
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.SkillEngine !== 'undefined') {
        // Module will be initialized by the template script
        console.log('✅ Career Analysis V2 Controller loaded and ready');
    }
});
