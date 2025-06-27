/**
 * Career Transition Analysis Module
 * Handles Career Transition Analysis Generator, preview, and form interactions
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.CareerAnalysis = {
    // State management
    state: {
        isGenerating: false,
        lastFormData: null
    },

    // Initialize the Career Transition Analysis module
    init() {
        console.log('🚀 Loading Career Transition Analysis Generator Module...');
        
        try {
            this.initializeEventHandlers();
            this.initializeFormInteractions();
            this.setupJobSearch();
            this.setupTargetJobSelector();
            this.setupDynamicUpdates();
            this.loadJobOptions();
            
                        // Initialize displays and separate sliders
        this.initializeSeparateSliders();
        this.initializeTopNUpdates();
            
            console.log('✅ Career Transition Analysis Generator Module loaded');
        } catch (error) {
            console.error('❌ Error initializing Career Transition Analysis:', error);
        }
    },

    // Initialize event handlers
    initializeEventHandlers() {
        // Analysis mode toggle
        document.querySelectorAll('input[name="analysis_mode"]').forEach(radio => {
            radio.addEventListener('change', (e) => this.handleAnalysisModeChange(e));
        });

        // Preview button
        const previewBtn = document.getElementById('previewBtn');
        if (previewBtn) {
            previewBtn.addEventListener('click', () => this.handlePreviewClick());
        }

        // Generate button
        const generateBtn = document.getElementById('generateBtn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.handleGenerateClick());
        }

        // Form validation on input changes
        const sourceJobSelect = document.getElementById('jobFrom');
        if (sourceJobSelect) {
            sourceJobSelect.addEventListener('change', () => this.validateForm());
        }
    },

    // Setup job search functionality
    setupJobSearch() {
        console.log('✅ Job search now handled by Unified Search Module');
        
        // Setup integration with unified search module events
        this.setupUnifiedSearchIntegration();
        
        // Clear hidden input when search input is manually cleared
        const searchInput = document.getElementById('jobFromSearch');
        const hiddenInput = document.getElementById('jobFrom');
        
        if (searchInput && hiddenInput) {
            searchInput.addEventListener('input', (e) => {
                if (e.target.value.trim() === '') {
                    hiddenInput.value = '';
                    this.validateForm();
                }
            });
        }
    },

    // Initialize form interactions
    initializeFormInteractions() {
        // Set initial form state
        this.updateTargetJobVisibility();
        this.validateForm();
    },

    // Handle analysis mode change
    handleAnalysisModeChange(event) {
        console.log('📊 Analysis mode changed:', event.target.value);
        this.updateTargetJobVisibility();
        this.validateForm();
    },

    // Update target job section visibility
    updateTargetJobVisibility() {
        const analysisMode = document.querySelector('input[name="analysis_mode"]:checked')?.value;
        const targetSection = document.getElementById('targetJobSection');
        const jobToSelect = document.getElementById('jobTo');
        
                // Discovery-only sections
        const topNSection = document.getElementById('topNSection');
        const tieBreakingSection = document.getElementById('tieBreakingSection');
        const similarityRangeSection = document.getElementById('similarityRangeSection');

        // Mode-specific help text
        const discoveryHelp = document.getElementById('discoveryModeHelp');
        const specificHelp = document.getElementById('specificModeHelp');

        if (analysisMode === 'specific') {
            // Show specific transition mode elements
            targetSection.classList.remove('hidden');
            jobToSelect.required = true;
            
            // Hide discovery-only elements
            if (topNSection) topNSection.classList.add('hidden');
            if (tieBreakingSection) tieBreakingSection.classList.add('hidden');
            if (similarityRangeSection) similarityRangeSection.classList.add('hidden');
            
            // Update help text
            if (discoveryHelp) discoveryHelp.classList.add('hidden');
            if (specificHelp) specificHelp.classList.remove('hidden');
            
        } else {
            // Show discovery mode elements
            if (topNSection) topNSection.classList.remove('hidden');
            if (tieBreakingSection) tieBreakingSection.classList.remove('hidden');
            if (similarityRangeSection) similarityRangeSection.classList.remove('hidden');
            
            // Hide specific transition elements
            targetSection.classList.add('hidden');
            jobToSelect.required = false;
            jobToSelect.value = '';
            
            // Update help text
            if (discoveryHelp) discoveryHelp.classList.remove('hidden');
            if (specificHelp) specificHelp.classList.add('hidden');
        }
    },

    // Validate form inputs
    validateForm() {
        const jobFrom = document.getElementById('jobFrom').value;
        const analysisMode = document.querySelector('input[name="analysis_mode"]:checked')?.value;
        const jobTo = document.getElementById('jobTo').value;

        let isValid = !!jobFrom;

        // Check target job requirement for specific mode
        if (analysisMode === 'specific') {
            isValid = isValid && !!jobTo;
        }

        // Update button states
        this.updateButtonStates(isValid);
        return isValid;
    },

    // Update button states based on form validation
    updateButtonStates(isValid) {
        const previewBtn = document.getElementById('previewBtn');
        const generateBtn = document.getElementById('generateBtn');

        if (previewBtn) {
            previewBtn.disabled = !isValid || this.state.isGenerating;
        }

        if (generateBtn) {
            generateBtn.disabled = !isValid || this.state.isGenerating;
        }
    },

    // Handle preview button click
    async handlePreviewClick() {
        console.log('👁️ Preview button clicked');

        if (!this.validateForm()) {
            this.showAlert('Please select a source job first.', 'warning');
            return;
        }

        try {
            this.setLoadingState(true);
            const formData = this.getFormData();
            
            const response = await fetch('/api/career-analysis-preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                this.displayPreview(data);
            } else {
                throw new Error(data.error || 'Preview generation failed');
            }

        } catch (error) {
            console.error('❌ Preview error:', error);
            this.displayError('Failed to generate preview: ' + error.message);
        } finally {
            this.setLoadingState(false);
        }
    },

    // Handle generate button click
    async handleGenerateClick() {
        console.log('📄 Generate button clicked');

        if (!this.validateForm()) {
            this.showAlert('Please select a source job first.', 'warning');
            return;
        }

        try {
            this.setLoadingState(true);
            const formData = this.getFormData();
            formData.output_format = 'word'; // Generate Word document
            
            const response = await fetch('/api/generate-career-analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                this.displayResults(data);
            } else {
                throw new Error(data.error || 'Career Transition Analysis Generator failed');
            }

        } catch (error) {
            console.error('❌ Generation error:', error);
            this.displayError('Failed to Generate Career Report: ' + error.message);
        } finally {
            this.setLoadingState(false);
        }
    },

    // Initialize dual handle range slider
    initializeSeparateSliders() {
        const minSlider = document.getElementById('similarityMin');
        const maxSlider = document.getElementById('similarityMax');
        const rangeDisplay = document.getElementById('similarityRangeDisplay');
        const minValueDisplay = document.getElementById('minValueDisplay');
        const maxValueDisplay = document.getElementById('maxValueDisplay');
        
        if (!minSlider || !maxSlider || !rangeDisplay || !minValueDisplay || !maxValueDisplay) {
            console.error('❌ Slider elements not found');
            return;
        }
        
        console.log('🎛️ Initializing separate min/max sliders...');
        
        const updateValues = () => {
            let minValue = parseInt(minSlider.value);
            let maxValue = parseInt(maxSlider.value);
            
            // Enforce minimum gap of 5
            if (minValue >= maxValue - 5) {
                minValue = maxValue - 5;
                minSlider.value = minValue;
            }
            
            if (maxValue <= minValue + 5) {
                maxValue = minValue + 5;
                maxSlider.value = maxValue;
            }
            
            // Update individual displays
            minValueDisplay.textContent = `${minValue}%`;
            maxValueDisplay.textContent = `${maxValue}%`;
            
            // Update combined range display
            rangeDisplay.textContent = `${minValue}% - ${maxValue}%`;
            
            // Update visual feedback based on range
            if (maxValue >= 95) {
                rangeDisplay.style.color = '#ea580c'; // orange-600
                rangeDisplay.title = 'Including very high similarities (near-exact matches)';
            } else if (minValue <= 30) {
                rangeDisplay.style.color = '#ca8a04'; // yellow-600  
                rangeDisplay.title = 'Including low similarity matches (may require significant development)';
            } else {
                rangeDisplay.style.color = '#dc2626'; // red-600
                rangeDisplay.title = 'Optimal range for meaningful career transitions';
            }
            
            // Validate form
            this.validateForm();
        };
        
        // Event listeners for both sliders
        minSlider.addEventListener('input', updateValues);
        minSlider.addEventListener('change', updateValues);
        maxSlider.addEventListener('input', updateValues);
        maxSlider.addEventListener('change', updateValues);
        
        // Initialize values
        updateValues();
        
        console.log('✅ Separate sliders initialized successfully');
    },

    // Initialize Top N pathway configuration updates
    initializeTopNUpdates() {
        const topNInput = document.getElementById('topN');
        const topNDisplay = document.getElementById('topNDisplay');
        const discoveryPathwayCount = document.getElementById('discoveryPathwayCount');

        if (topNInput && topNDisplay) {
            topNInput.addEventListener('input', function(e) {
                const value = e.target.value;
                
                // Update display elements
                topNDisplay.textContent = value;
                if (discoveryPathwayCount) {
                    discoveryPathwayCount.textContent = `top ${value}`;
                }
                
                console.log(`🔢 Top N pathways updated to: ${value}`);
            });
        }
    },

    // Get form data
    getFormData() {
        const analysisMode = document.querySelector('input[name="analysis_mode"]:checked')?.value;
        
        const formData = {
            job_from: document.getElementById('jobFrom')?.value || '',
            analysis_mode: analysisMode || 'top_matches',
            job_to: analysisMode === 'specific' ? (document.getElementById('jobTo')?.value || '') : null,
            // Note: scenario, audience, division_from, division_to don't exist in current HTML template
            scenario: 'discovery', // Default scenario since element doesn't exist
            audience: 'executive', // Default audience since element doesn't exist
            division_from: null,
            division_to: null
        };

        // Include discovery-specific parameters only if in discovery mode
        if (analysisMode === 'top_matches') {
            formData.top_n = parseInt(document.getElementById('topN')?.value) || 3;
            formData.similarity_min = parseInt(document.getElementById('similarityMin')?.value) || 40;
            formData.similarity_max = parseInt(document.getElementById('similarityMax')?.value) || 90;
            
            // Add tie-breaking options
            formData.tie_breaking_options = {
                same_function_priority: document.getElementById('sameFunctionPriority')?.checked || false,
                career_progression_priority: document.getElementById('careerProgressionPriority')?.checked || false,
                minimal_level_jump: document.getElementById('minimalLevelJump')?.checked || false,
                skills_overlap_detail: document.getElementById('skillsOverlapDetail')?.checked || false
            };
        }

        // Store for potential reuse
        this.state.lastFormData = formData;
        return formData;
    },

    // Set loading state
    setLoadingState(isLoading) {
        this.state.isGenerating = isLoading;
        
        const loadingSpinner = document.getElementById('loadingSpinner');
        const previewContent = document.getElementById('previewContent');

        if (isLoading) {
            loadingSpinner.classList.remove('hidden');
            previewContent.classList.add('hidden');
        } else {
            loadingSpinner.classList.add('hidden');
            previewContent.classList.remove('hidden');
        }

        // Update button states
        this.updateButtonStates(!isLoading && this.validateForm());
    },

    /**
     * Display the full rich analysis preview from CLI output
     */
    displayPreview(data) {
        const previewContent = document.getElementById('previewContent');
        
        // DEBUG: Log the exact data structure we're receiving
        console.log('🔍 DEBUG: Received data structure:', JSON.stringify(data, null, 2));
        console.log('🔍 DEBUG: Data content keys:', Object.keys(data.content || {}));
        
        if (!data.success) {
            this.displayError(`Failed to generate preview: ${data.error || 'Unknown error'}`);
            return;
        }

        // Check if we have structured content from all 5 sections
        const content = data.content || {};
        const hasStructuredContent = Object.keys(content).length > 0;
        
        // DEBUG: Log content structure
        console.log('🔍 DEBUG: Has structured content:', hasStructuredContent);
        console.log('🔍 DEBUG: Content structure:', content);
        
        let htmlContent = '';
        
        if (hasStructuredContent) {
            // Use the structured content from all 5 sections
            htmlContent = this.parseStructuredContent(content);
        } else {
            // Fallback to parsing raw CLI output
            htmlContent = this.parseCliOutputToHtml(data.raw_output, data);
        }
        
        previewContent.innerHTML = `
            <div class="p-6 space-y-8">
                <div class="border-b border-gray-200 pb-4 mb-8">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-2xl font-epilogue font-bold text-gray-900">
                            Career Transition Analysis Preview
                        </h3>
                        <div class="flex items-center space-x-4 text-sm text-gray-600">
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800">
                                <i class="fas fa-chart-line mr-1"></i>
                                ${(data.metadata?.analysis_mode || data.analysis_mode) === 'top_matches' ? 'Top Discovery' : 'Specific Transition'}
                            </span>
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full bg-green-100 text-green-800">
                                <i class="fas fa-check-circle mr-1"></i>
                                ${data.metadata?.top_n || data.pathway_count || 3} Opportunities
                            </span>
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-800">
                                <i class="fas fa-percentage mr-1"></i>
                                ${data.metadata?.similarity_range ? 
                                    `${data.metadata.similarity_range.min}-${data.metadata.similarity_range.max}%` : 
                                    `${Math.round((data.similarity_score || 0) * 100)}%`} Avg Similarity
                            </span>
                            ${hasStructuredContent ? 
                                `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full bg-green-100 text-green-800">
                                    <i class="fas fa-file-alt mr-1"></i>
                                    ${data.metadata?.section_count || data.section_count || 5} Sections
                                </span>` : ''
                            }
                        </div>
                    </div>
                    <p class="text-gray-600 font-source">
                        Analysis for: <strong>${data.metadata?.source_job_title || data.job_title || 'Unknown Job'}</strong> | 
                        Range: ${data.metadata?.similarity_range ? 
                            `${data.metadata.similarity_range.min}%-${data.metadata.similarity_range.max}%` : 
                            (data.similarity_range || 'Unknown')} | 
                        ${data.metadata?.analysis_mode || data.tie_breaking_applied ? 'Tie-breaking applied' : 'Default ordering'}
                    </p>
                </div>
                
                <div class="prose prose-lg max-w-none space-y-12">
                    ${htmlContent}
                </div>
            </div>
        `;
    },

    /**
     * Parse structured content from all 5 sections (like Word document)
     */
    parseStructuredContent(content) {
        let html = '';
        
        // Section order matching Word document structure
        const sectionOrder = [
            { key: 'executive_summary', defaultTitle: 'Executive Summary', icon: 'fas fa-chart-line' },
            { key: 'current_role_context', defaultTitle: 'Current Role Context', icon: 'fas fa-user-tie' },
            { key: 'pathway_analysis', defaultTitle: 'Pathway Analysis: Strategic Opportunities', icon: 'fas fa-route' },
            { key: 'strategic_recommendations', defaultTitle: 'Strategic Recommendations', icon: 'fas fa-lightbulb' },
            { key: 'conclusion', defaultTitle: 'Conclusion', icon: 'fas fa-flag-checkered' }
        ];
        
        sectionOrder.forEach((section, index) => {
            if (content[section.key]) {
                const sectionData = content[section.key];
                const title = sectionData.title || section.defaultTitle;
                
                // DEBUG: Log pathway analysis structure
                if (section.key === 'pathway_analysis') {
                    console.log('🔍 DEBUG: Pathway Analysis structure:', JSON.stringify(sectionData, null, 2));
                    console.log('🔍 DEBUG: Pathway Analysis subsections keys:', Object.keys(sectionData.subsections || {}));
                }
                
                // Handle new subsections structure from service layer
                let sectionContent = '';
                if (sectionData.subsections && Object.keys(sectionData.subsections).length > 0) {
                    // Process subsections
                    sectionContent = this.formatSubsections(sectionData.subsections);
                } else {
                    // Fallback to direct content
                    sectionContent = this.formatSectionContent(sectionData.content || '');
                }
                
                html += `
                    <div class="mb-12">
                        <div class="flex items-center mb-6">
                            <div class="flex items-center justify-center w-10 h-10 bg-red-600 text-white rounded-full mr-4">
                                <i class="${section.icon} text-sm"></i>
                            </div>
                            <h2 class="text-2xl font-epilogue font-bold text-gray-900">${title}</h2>
                        </div>
                        <div class="ml-14">
                            ${sectionContent}
                        </div>
                    </div>
                `;
                
                // Add separator between sections (except last)
                if (index < sectionOrder.length - 1) {
                    html += `
                        <div class="my-8 border-t border-gray-200"></div>
                    `;
                }
            }
        });
        
        // If no structured sections were found, show a message
        if (!html) {
            html = `
                <div class="text-center py-12">
                    <i class="fas fa-info-circle text-4xl text-gray-400 mb-4"></i>
                    <p class="text-gray-600">Structured content parsing in progress...</p>
                    <p class="text-sm text-gray-500 mt-2">Falling back to raw output parsing</p>
                </div>
            `;
        }
        
        return html;
    },

    /**
     * Format subsections from service layer structure
     */
    formatSubsections(subsections) {
        let html = '';
        
        for (const [subsectionKey, subsectionData] of Object.entries(subsections)) {
            const title = subsectionData.title || this.formatSubsectionTitle(subsectionKey);
            
            // Use specialised formatters for Current Role Context subsections
            if (subsectionKey === 'core_competency_foundation') {
                html += this.formatCoreCompetencyFoundation(title, subsectionData);
            } else if (subsectionKey === 'profile_overview') {
                html += this.formatProfileOverview(title, subsectionData);
            } else if (subsectionKey === 'strategic_intelligence_metrics') {
                html += this.formatStrategicIntelligenceMetrics(title, subsectionData);
            } else if (subsectionKey === 'strategic_value_proposition') {
                html += this.formatStrategicValueProposition(title, subsectionData);
            } else if (subsectionKey === 'opportunities') {
                // Special handling for pathway analysis opportunities
                html += this.formatPathwayOpportunities(title, subsectionData);
            } else {
                // Generic subsection formatting
                html += this.formatGenericSubsection(title, subsectionData);
            }
        }
        
        return html;
    },

    /**
     * Format Core Competency Foundation subsection with skills table
     */
    formatCoreCompetencyFoundation(title, subsectionData) {
        const content = subsectionData.content || '';
        
        // Extract key information from the content
        const skillsMatch = content.match(/(\d+)\s+prescribed\s+skills\s+across\s+(\d+)\s+strategic\s+capability\s+areas/i);
        
        let html = `
            <div class="mb-8">
                <h3 class="text-xl font-epilogue font-semibold text-gray-800 mb-4">${title}</h3>
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-6">
        `;
        
        if (skillsMatch) {
            const [, totalSkills, categoryCount] = skillsMatch;
            
            html += `
                <div class="flex items-center mb-4">
                    <div class="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center mr-3">
                        <i class="fas fa-cogs text-white text-sm"></i>
                    </div>
                    <div>
                        <h4 class="text-lg font-semibold text-blue-900">Skills Portfolio Overview</h4>
                        <p class="text-sm text-blue-700">Comprehensive analysis of role capabilities</p>
                    </div>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div class="bg-white rounded-lg p-4 border border-blue-200">
                        <div class="text-2xl font-bold text-blue-600">${totalSkills}</div>
                        <div class="text-sm text-gray-600">Total Skills</div>
                    </div>
                    <div class="bg-white rounded-lg p-4 border border-blue-200">
                        <div class="text-2xl font-bold text-blue-600">${categoryCount}</div>
                        <div class="text-sm text-gray-600">Capability Areas</div>
                    </div>
                    <div class="bg-white rounded-lg p-4 border border-blue-200">
                        <div class="text-2xl font-bold text-green-600">High</div>
                        <div class="text-sm text-gray-600">Complexity Level</div>
                    </div>
                </div>
            `;
        }
        
        // Format the table content
        if (content.includes('|')) {
            html += this.formatMarkdownStyleTable(content);
        } else {
            html += `<div class="text-gray-700">${content}</div>`;
        }
        
        html += `
                </div>
            </div>
        `;
        
        return html;
    },

    /**
     * Format Profile Overview subsection with organisational deployment
     */
    formatProfileOverview(title, subsectionData) {
        const content = subsectionData.content || '';
        
        return `
            <div class="mb-8">
                <h3 class="text-xl font-epilogue font-semibold text-gray-800 mb-4">${title}</h3>
                <div class="bg-green-50 border border-green-200 rounded-lg p-6">
                    <div class="flex items-center mb-4">
                        <div class="w-10 h-10 bg-green-600 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-building text-white text-sm"></i>
                        </div>
                        <div>
                            <h4 class="text-lg font-semibold text-green-900">Organisational Deployment</h4>
                            <p class="text-sm text-green-700">Current role distribution across NAB</p>
                        </div>
                    </div>
                    <div class="text-gray-700 space-y-2">
                        ${this.formatBulletList(content)}
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Format Strategic Intelligence Metrics subsection with metrics table
     */
    formatStrategicIntelligenceMetrics(title, subsectionData) {
        const content = subsectionData.content || '';
        
        let html = `
            <div class="mb-8">
                <h3 class="text-xl font-epilogue font-semibold text-gray-800 mb-4">${title}</h3>
                <div class="bg-purple-50 border border-purple-200 rounded-lg p-6">
                    <div class="flex items-center mb-4">
                        <div class="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-chart-line text-white text-sm"></i>
                        </div>
                        <div>
                            <h4 class="text-lg font-semibold text-purple-900">Strategic Intelligence Metrics</h4>
                            <p class="text-sm text-purple-700">Quantitative workforce positioning analysis</p>
                        </div>
                    </div>
        `;
        
        // Split content into description and table parts
        const sections = content.split('\n\n');
        const descriptionSections = [];
        let tableSection = '';
        
        sections.forEach(section => {
            if (section.includes('Metric') && section.includes('Score') && section.includes('Assessment')) {
                tableSection = section;
            } else if (section.trim()) {
                descriptionSections.push(section.trim());
            }
        });
        
        // Add description text
        if (descriptionSections.length > 0) {
            html += `
                <div class="mb-4 text-gray-700">
                    ${descriptionSections.map(section => {
                        // Check if section contains bullet points
                        if (section.includes('• ')) {
                            return this.formatBulletList(section);
                        } else {
                            return `<p class="mb-2">${section}</p>`;
                        }
                    }).join('')}
                </div>
            `;
        }
        
        // Add metrics table
        if (tableSection) {
            html += this.formatMarkdownStyleTable(tableSection);
        }
        
        // Add context note
        html += `
                    <div class="mt-4 p-4 bg-white rounded-lg border border-purple-200">
                        <p class="text-sm text-purple-700">
                            <i class="fas fa-info-circle mr-2"></i>
                            These metrics assess workforce positioning and transition potential within NAB's career pathway network.
                        </p>
                    </div>
                </div>
            </div>
        `;
        
        return html;
    },

    /**
     * Format Strategic Value Proposition subsection
     */
    formatStrategicValueProposition(title, subsectionData) {
        const content = subsectionData.content || '';
        
        return `
            <div class="mb-8">
                <h3 class="text-xl font-epilogue font-semibold text-gray-800 mb-4">${title}</h3>
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                    <div class="flex items-center mb-4">
                        <div class="w-10 h-10 bg-yellow-600 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-star text-white text-sm"></i>
                        </div>
                        <div>
                            <h4 class="text-lg font-semibold text-yellow-900">Strategic Value Analysis</h4>
                            <p class="text-sm text-yellow-700">Role positioning and transferability assessment</p>
                        </div>
                    </div>
                    <div class="text-gray-700 space-y-3">
                        ${this.formatValuePropositionContent(content)}
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Format value proposition content with special handling for skills analysis
     */
    formatValuePropositionContent(content) {
        const sections = content.split('\n\n').filter(section => section.trim());
        let html = '';
        
        sections.forEach(section => {
            const trimmedSection = section.trim();
            
            // Handle skills portfolio analysis section
            if (trimmedSection.includes('Skills Portfolio Analysis:')) {
                html += `
                    <div class="mb-4">
                        <h5 class="font-semibold text-yellow-900 mb-2">Skills Portfolio Analysis</h5>
                        <div class="bg-white rounded-lg p-4 border border-yellow-200">
                            ${this.formatBulletList(trimmedSection.replace('Skills Portfolio Analysis:', ''))}
                        </div>
                    </div>
                `;
            }
            // Handle organisational context section
            else if (trimmedSection.includes('Organisational Context:')) {
                html += `
                    <div class="mb-4">
                        <h5 class="font-semibold text-yellow-900 mb-2">Organisational Context</h5>
                        <div class="bg-white rounded-lg p-4 border border-yellow-200">
                            ${this.formatBulletList(trimmedSection.replace('Organisational Context:', ''))}
                        </div>
                    </div>
                `;
            }
            // Handle other sections
            else {
                html += `<div class="mb-3 text-gray-700">${trimmedSection}</div>`;
            }
        });
        
        return html;
    },

    /**
     * Format Pathway Analysis opportunities
     */
    formatPathwayOpportunities(title, subsectionData) {
        let html = `
            <div class="space-y-8">
        `;
        
        // Parse opportunities data - it might come as a string representation of a Python list
        let opportunities = [];
        
        if (Array.isArray(subsectionData.content)) {
            opportunities = subsectionData.content;
        } else if (typeof subsectionData.content === 'string') {
            try {
                // Handle potentially truncated or malformed Python string content
                let contentStr = subsectionData.content.trim();
                
                console.log('🔍 DEBUG: Raw content string length:', contentStr.length);
                console.log('🔍 DEBUG: Content string starts with:', contentStr.substring(0, 100));
                console.log('🔍 DEBUG: Content string ends with:', contentStr.substring(contentStr.length - 100));
                
                // Check if string appears to be truncated (doesn't end with proper closing)
                if (!contentStr.endsWith(']') && !contentStr.endsWith('}]')) {
                    console.warn('⚠️ Content appears to be truncated, attempting to create fallback');
                    html += `<div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                        <div class="flex items-center">
                            <i class="fas fa-exclamation-triangle text-yellow-600 mr-2"></i>
                            <span class="text-yellow-800 font-medium">Pathway Analysis Data Loading</span>
                        </div>
                        <p class="text-yellow-700 mt-2">The pathway analysis data is being processed. This section contains detailed opportunity analysis with skills transition tables and strategic recommendations.</p>
                        <p class="text-yellow-600 text-sm mt-1">Please try refreshing the preview if this message persists.</p>
                    </div>`;
                    html += `</div>`;
                    return html;
                }
                
                // Use more robust Python-to-JSON conversion
                // This handles the complex nested structures with proper quote escaping
                opportunities = this.parsePythonStringToJSON(contentStr);
                console.log('🔍 DEBUG: Successfully parsed opportunities count:', opportunities.length);
            } catch (e) {
                console.error('❌ Failed to parse opportunities:', e);
                console.log('🔍 DEBUG: Failed content preview:', subsectionData.content.substring(0, 1000));
                
                // Provide helpful error message
                html += `<div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                    <div class="flex items-center">
                        <i class="fas fa-exclamation-circle text-red-600 mr-2"></i>
                        <span class="text-red-800 font-medium">Pathway Analysis Parsing Error</span>
                    </div>
                    <p class="text-red-700 mt-2">Unable to parse pathway analysis data. This may be due to data size limitations or formatting issues.</p>
                    <p class="text-red-600 text-sm mt-1">Error: ${e.message}</p>
                    <button onclick="location.reload()" class="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm">
                        Refresh Page
                    </button>
                </div>`;
                html += `</div>`;
                return html;
            }
        }
        
        // Handle the opportunities array
        if (Array.isArray(opportunities)) {
            opportunities.forEach((opportunity, index) => {
                html += this.formatSingleOpportunity(opportunity, index + 1);
            });
        } else if (opportunities) {
            // Handle single opportunity
            html += this.formatSingleOpportunity(opportunities, 1);
        } else {
            html += `<div class="text-gray-500">No opportunities available</div>`;
        }
        
        html += `</div>`;
        return html;
    },

    /**
     * Robust Python string to JSON parser
     * Handles complex nested structures with proper quote escaping
     */
    parsePythonStringToJSON(pythonStr) {
        // First, let's try a more sophisticated approach using eval in a safe context
        // We'll build a JSON-compatible string step by step
        
        try {
            // Method 1: Try direct conversion with careful replacements
            let jsonStr = pythonStr;
            
            // Replace Python boolean values
            jsonStr = jsonStr.replace(/\bTrue\b/g, 'true');
            jsonStr = jsonStr.replace(/\bFalse\b/g, 'false');
            jsonStr = jsonStr.replace(/\bNone\b/g, 'null');
            
            // Handle single quotes more carefully - avoid quotes inside URLs
            // This is a more sophisticated approach that preserves URLs
            jsonStr = this.convertPythonQuotesToJSON(jsonStr);
            
            // Try parsing
            return JSON.parse(jsonStr);
            
        } catch (e) {
            console.log('❌ Method 1 failed, trying method 2:', e.message);
            
            // Method 2: Use Function constructor to safely evaluate Python-like syntax
            try {
                // Create a safe evaluation environment
                const pythonToJS = new Function('return ' + pythonStr.replace(/'/g, '"').replace(/True/g, 'true').replace(/False/g, 'false').replace(/None/g, 'null'));
                return pythonToJS();
            } catch (e2) {
                console.log('❌ Method 2 failed, trying method 3:', e2.message);
                
                // Method 3: Manual parsing for known structure
                return this.manualParsePythonList(pythonStr);
            }
        }
    },

    /**
     * Convert Python single quotes to JSON double quotes while preserving URLs
     */
    convertPythonQuotesToJSON(str) {
        let result = '';
        let inString = false;
        let stringChar = null;
        let i = 0;
        
        while (i < str.length) {
            const char = str[i];
            const nextChar = str[i + 1];
            
            if (!inString) {
                if (char === "'" || char === '"') {
                    inString = true;
                    stringChar = char;
                    result += '"'; // Always use double quotes in JSON
                } else {
                    result += char;
                }
            } else {
                // We're inside a string
                if (char === stringChar) {
                    // Check if it's escaped
                    let escapedCount = 0;
                    let j = i - 1;
                    while (j >= 0 && str[j] === '\\') {
                        escapedCount++;
                        j--;
                    }
                    
                    if (escapedCount % 2 === 0) {
                        // Not escaped, this ends the string
                        inString = false;
                        stringChar = null;
                        result += '"'; // Always use double quotes in JSON
                    } else {
                        // This quote is escaped, include it
                        result += char;
                    }
                } else if (char === '"' && stringChar === "'") {
                    // Escape double quotes when we're in a single-quoted Python string
                    result += '\\"';
                } else {
                    result += char;
                }
            }
            i++;
        }
        
        return result;
    },

    /**
     * Manual parser for Python list structure when JSON parsing fails
     */
    manualParsePythonList(pythonStr) {
        // This is a fallback that creates a simplified structure
        // Extract the key information we need for display
        
        console.log('🔧 Using manual parsing fallback for pathway analysis');
        
        // Look for opportunity headers
        const opportunities = [];
        const headerMatches = pythonStr.match(/##\s*Strategic Opportunity \d+:[^']+/g);
        
        if (headerMatches) {
            headerMatches.forEach((header, index) => {
                opportunities.push({
                    header: header,
                    opportunity_overview: {
                        title: 'Opportunity Overview',
                        content: { text: 'Manual parsing - detailed metrics available in full system.' }
                    },
                    strategic_positioning: {
                        title: 'Why This Makes Sense',
                        content: 'This opportunity provides strategic value through skills transfer and career advancement.'
                    },
                    skills_transition_analysis: {
                        title: 'Skills Transition Analysis',
                        content: { text: 'Detailed skills analysis with Lightcast.io links available in full system.' }
                    },
                    business_case: {
                        title: 'Business Impact',
                        content: 'Cost savings through internal development and capability building.'
                    },
                    implementation_roadmap: {
                        title: 'Implementation Roadmap',
                        content: { text: 'Phased approach with timeline and success measures.' }
                    }
                });
            });
        }
        
        // If no headers found, create a placeholder
        if (opportunities.length === 0) {
            opportunities.push({
                header: '## Strategic Opportunity: Career Transition Analysis',
                opportunity_overview: {
                    title: 'Opportunity Overview',
                    content: { text: 'Pathway analysis data is available but requires manual parsing.' }
                }
            });
        }
        
        return opportunities;
    },

    /**
     * Format a single opportunity card
     */
    formatSingleOpportunity(opportunity, opportunityNumber) {
        let html = `
            <div class="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        `;
        
        // Parse and format header
        if (opportunity.header) {
            const headerInfo = this.parseOpportunityHeader(opportunity.header);
            html += `
                <div class="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-6">
                    <h3 class="text-xl font-bold mb-3">${headerInfo.title}</h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div class="flex items-center">
                            <i class="fas fa-bullseye mr-2"></i>
                            <span class="font-medium">Target:</span> 
                            <span class="ml-1">${headerInfo.targetRole}</span>
                        </div>
                        <div class="flex items-center">
                            <i class="fas fa-chart-line mr-2"></i>
                            <span class="font-medium">Similarity:</span> 
                            <span class="bg-white bg-opacity-20 px-2 py-1 rounded ml-1">${headerInfo.similarity}</span>
                        </div>
                        <div class="flex items-center">
                            <i class="fas fa-arrows-alt mr-2"></i>
                            <span class="font-medium">Type:</span> 
                            <span class="ml-1">${headerInfo.moveType}</span>
                        </div>
                    </div>
                    ${headerInfo.classification ? `
                        <div class="mt-3">
                            <span class="bg-yellow-400 text-yellow-900 px-3 py-1 rounded-full text-sm font-medium">
                                ${headerInfo.classification}
                            </span>
                        </div>
                    ` : ''}
                </div>
            `;
        }
        
        html += `<div class="p-6 space-y-6">`;
        
        // Format each subsection in order
        const subsectionOrder = [
            'opportunity_overview',
            'strategic_positioning', 
            'skills_transition_analysis',
            'business_case',
            'implementation_roadmap'
        ];
        
        subsectionOrder.forEach(subsectionKey => {
            if (opportunity[subsectionKey]) {
                html += this.formatOpportunitySubsection(opportunity[subsectionKey], subsectionKey);
            }
        });
        
        html += `</div></div>`;
        return html;
    },

    /**
     * Parse opportunity header string into structured data
     */
    parseOpportunityHeader(headerString) {
        const lines = headerString.split('\n');
        const result = {};
        
        // Parse title from first line (remove ## prefix)
        if (lines[0]) {
            result.title = lines[0].replace(/^##\s*/, '').trim();
        }
        
        // Parse metadata from subsequent lines
        lines.forEach(line => {
            if (line.includes('Target Role:')) {
                const match = line.match(/Target Role:\s*(.+?)\s*\|/);
                if (match) result.targetRole = match[1].trim();
            }
            if (line.includes('Similarity Score:')) {
                const match = line.match(/Similarity Score:\s*([0-9.]+%)/);
                if (match) result.similarity = match[1];
            }
            if (line.includes('Move Type:')) {
                const match = line.match(/Move Type:\s*(.+?)(?:\s*$|\s*\n)/);
                if (match) result.moveType = match[1].trim();
            }
            if (line.includes('Strategic Classification:')) {
                const match = line.match(/Strategic Classification:\s*(.+?)(?:\s*$|\s*\n)/);
                if (match) result.classification = match[1].trim();
            }
        });
        
        return result;
    },

    /**
     * Format opportunity subsection based on type
     */
    formatOpportunitySubsection(subsection, subsectionKey) {
        const title = subsection.title || this.formatSubsectionTitle(subsectionKey);
        
        let html = `
            <div class="border-l-4 border-purple-300 pl-4">
                <h4 class="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    ${this.getSubsectionIcon(subsectionKey)}
                    <span class="ml-2">${title}</span>
                </h4>
        `;
        
        // Handle different content types based on subsection
        if (subsectionKey === 'opportunity_overview') {
            html += this.formatOpportunityOverview(subsection);
        } else if (subsectionKey === 'strategic_positioning') {
            html += this.formatStrategicPositioning(subsection);
        } else if (subsectionKey === 'skills_transition_analysis') {
            html += this.formatSkillsTransitionAnalysis(subsection);
        } else if (subsectionKey === 'business_case') {
            html += this.formatBusinessCase(subsection);
        } else if (subsectionKey === 'implementation_roadmap') {
            html += this.formatImplementationRoadmap(subsection);
        } else {
            // Generic formatting
            html += `<div class="text-gray-700">${subsection.content || 'No content available'}</div>`;
        }
        
        html += `</div>`;
        return html;
    },

    /**
     * Get icon for subsection
     */
    getSubsectionIcon(subsectionKey) {
        const icons = {
            'opportunity_overview': '<i class="fas fa-chart-pie text-blue-500"></i>',
            'strategic_positioning': '<i class="fas fa-compass text-green-500"></i>',
            'skills_transition_analysis': '<i class="fas fa-exchange-alt text-orange-500"></i>',
            'business_case': '<i class="fas fa-dollar-sign text-purple-500"></i>',
            'implementation_roadmap': '<i class="fas fa-road text-indigo-500"></i>'
        };
        return icons[subsectionKey] || '<i class="fas fa-info-circle text-gray-500"></i>';
    },

    /**
     * Format opportunity overview (typically contains metrics table)
     */
    formatOpportunityOverview(subsection) {
        if (subsection.content && subsection.content.text) {
            return this.formatAdvancedTable(subsection.content.text, subsection.content.formatting);
        }
        return `<div class="text-gray-700">${subsection.content || 'No overview available'}</div>`;
    },

    /**
     * Format strategic positioning (paragraph content)
     */
    formatStrategicPositioning(subsection) {
        const content = subsection.content || '';
        const paragraphs = content.split('\n\n').filter(p => p.trim());
        
        let html = '<div class="space-y-3">';
        paragraphs.forEach(paragraph => {
            html += `<p class="text-gray-700 leading-relaxed">${paragraph.trim()}</p>`;
        });
        html += '</div>';
        
        return html;
    },

    /**
     * Format skills transition analysis (complex table with skills links)
     */
    formatSkillsTransitionAnalysis(subsection) {
        if (subsection.content && subsection.content.text) {
            return this.formatAdvancedSkillsTable(subsection.content.text, subsection.content.formatting);
        }
        return `<div class="text-gray-700">${subsection.content || 'No skills analysis available'}</div>`;
    },

    /**
     * Format business case (mixed content with bold labels)
     */
    formatBusinessCase(subsection) {
        if (subsection.content_type === 'mixed' && subsection.bold_labels) {
            return this.formatMixedContentWithLabels(subsection.content, subsection.bold_labels);
        }
        return `<div class="text-gray-700">${subsection.content || 'No business case available'}</div>`;
    },

    /**
     * Format implementation roadmap (timeline table)
     */
    formatImplementationRoadmap(subsection) {
        if (subsection.content && subsection.content.text) {
            return this.formatTimelineTable(subsection.content.text, subsection.content.formatting);
        }
        return `<div class="text-gray-700">${subsection.content || 'No roadmap available'}</div>`;
    },

    /**
     * Format advanced skills table with clickable links
     */
    formatAdvancedSkillsTable(content, formatting) {
        if (!content) return '';
        
        // Check if we have pre-structured data in formatting
        if (formatting && formatting.headers && formatting.rows) {
            console.log(`🔍 DEBUG: Using pre-structured Skills table data`);
            console.log(`🔍 DEBUG: Headers:`, formatting.headers);
            console.log(`🔍 DEBUG: Rows:`, formatting.rows.length);
            
            return this.formatPreStructuredSkillsTable(formatting.headers, formatting.rows);
        }
        
        // Fallback to parsing raw text content
        console.log(`🔍 DEBUG: Parsing raw Skills table text`);
        const lines = content.split('\n').filter(line => line.trim());
        if (lines.length < 2) return content;
        
        // Parse headers
        const headers = lines[0].split('|').map(h => h.trim()).filter(h => h);
        
        console.log(`🔍 DEBUG: Skills table headers (${headers.length}):`, headers);
        console.log(`🔍 DEBUG: Expected 4 columns: Category | Current Skills | New Skills Required | Gap Assessment`);
        
        // Skip separator line and parse data rows with skills URL protection
        const dataRows = lines.slice(2).map(line => 
            this.parseTableRowWithSkillsLinks(line, headers.length)
        );
        
        let html = `
            <div class="overflow-x-auto">
                <table class="min-w-full bg-white border border-gray-200 rounded-lg">
                    <thead class="bg-gray-50">
                        <tr>
        `;
        
        headers.forEach(header => {
            html += `<th class="px-4 py-3 text-left text-sm font-medium text-gray-700 border-b">${header}</th>`;
        });
        
        html += `
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">
        `;
        
        dataRows.forEach((row, index) => {
            html += `<tr class="${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}">`;
            row.forEach((cell, cellIndex) => {
                let cellContent = cell;
                
                // Handle skills with links (check for skills bullet points with URLs)
                if (cell.includes('•') && cell.includes('https://lightcast.io/')) {
                    cellContent = this.formatSkillsWithLinks(cell);
                } else if (cell.includes('\n•')) {
                    cellContent = this.formatBulletList(cell);
                } else {
                    cellContent = cell;
                }
                
                html += `<td class="px-4 py-3 text-sm text-gray-700 border-b align-top">${cellContent}</td>`;
            });
            html += `</tr>`;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        return html;
    },

    /**
     * Format pre-structured skills table data with clickable links
     */
    formatPreStructuredSkillsTable(headers, rows) {
        let html = `
            <div class="overflow-x-auto">
                <table class="min-w-full bg-white border border-gray-200 rounded-lg shadow-sm">
                    <thead class="bg-gray-50">
                        <tr>
        `;
        
        // Add headers
        headers.forEach(header => {
            html += `<th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">${header}</th>`;
        });
        
        html += `
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        // Add data rows
        rows.forEach((row, index) => {
            html += `<tr class="${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}">`;
            
            row.forEach((cell, cellIndex) => {
                let cellContent = cell;
                
                // Process skills with links (columns 1 and 2: Current Skills and New Skills Required)
                if (cellIndex === 1 || cellIndex === 2) {
                    if (cell && cell.trim() && cell.includes('|https://lightcast.io/')) {
                        cellContent = this.formatSkillsWithLinks(cell);
                    } else if (cell && cell.includes('\n•')) {
                        cellContent = this.formatBulletList(cell);
                    } else if (!cell || cell.trim() === '') {
                        cellContent = '<span class="text-gray-400 italic">No skills in this category</span>';
                    } else {
                        cellContent = cell;
                    }
                } else {
                    // Other columns (Category and Gap Assessment)
                    cellContent = cell || '';
                }
                
                html += `<td class="px-4 py-3 text-sm text-gray-700 border-b align-top">${cellContent}</td>`;
            });
            
            html += `</tr>`;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        return html;
    },

    /**
     * Parse a table row that may contain skills with embedded URLs
     * Handles the format: • SkillName|https://lightcast.io/open-skills/skills/ID
     * Expected 4 columns: Category | Current Skills | New Skills Required | Gap Assessment
     */
    parseTableRowWithSkillsLinks(line, expectedColumns) {
        if (!line || !line.trim()) return [];
        
        console.log(`🔍 DEBUG: Parsing table row with ${expectedColumns} expected columns:`);
        console.log(`🔍 DEBUG: Raw line: "${line}"`);
        
        // First, let's protect skill|URL patterns during splitting
        let protectedLine = line;
        const skillPatterns = [];
        let placeholderIndex = 0;
        
        // Find and protect skill|URL patterns (• SkillName|https://lightcast.io/...)
        const skillUrlRegex = /•\s*[^|]+\|https:\/\/lightcast\.io\/[^\s|]+/g;
        let match;
        
        while ((match = skillUrlRegex.exec(line)) !== null) {
            const placeholder = `__SKILL_URL_PLACEHOLDER_${placeholderIndex}__`;
            skillPatterns.push({
                placeholder: placeholder,
                original: match[0]
            });
            protectedLine = protectedLine.replace(match[0], placeholder);
            placeholderIndex++;
        }
        
        console.log(`🔍 DEBUG: Protected ${skillPatterns.length} skill|URL patterns`);
        console.log(`🔍 DEBUG: Protected line: "${protectedLine}"`);
        
        // For Skills Transition Analysis, we need to be more careful about splitting
        // The structure should be: Category | Current Skills | New Skills Required | Gap Assessment
        let cells;
        
        if (expectedColumns === 4) {
            // Special handling for 4-column Skills Transition table
            cells = this.parseSkillsTransitionRow(protectedLine);
        } else {
            // Standard pipe splitting for other tables
            cells = protectedLine.split('|').map(cell => cell.trim());
        }
        
        // Restore the skill|URL patterns
        cells = cells.map(cell => {
            let restoredCell = cell;
            skillPatterns.forEach(pattern => {
                restoredCell = restoredCell.replace(pattern.placeholder, pattern.original);
            });
            return restoredCell;
        });
        
        console.log(`🔍 DEBUG: Parsed ${cells.length} cells:`, cells);
        
        // Ensure we have the expected number of columns
        while (cells.length < expectedColumns) {
            cells.push('');
        }
        
        // Truncate if we have too many columns
        if (cells.length > expectedColumns) {
            console.log(`🔍 DEBUG: Truncating from ${cells.length} to ${expectedColumns} columns`);
            cells = cells.slice(0, expectedColumns);
        }
        
        return cells;
    },

    /**
     * Parse Skills Transition Analysis row with careful column handling
     * Expected format: Category | Current Skills | New Skills Required | Gap Assessment
     */
    parseSkillsTransitionRow(protectedLine) {
        // Look for pattern: starts with category, then has skills sections, ends with gap assessment
        const parts = protectedLine.split('|');
        
        if (parts.length < 4) {
            // Not enough parts, return as-is
            return parts.map(p => p.trim());
        }
        
        // Strategy: Category is first, Gap Assessment is last, middle parts are skills
        const category = parts[0].trim();
        const gapAssessment = parts[parts.length - 1].trim();
        
        // The middle parts need to be split into Current Skills and New Skills Required
        const middleParts = parts.slice(1, -1);
        
        // Heuristic: If we have exactly 4 parts, it's straightforward
        if (parts.length === 4) {
            return [category, middleParts[0].trim(), middleParts[1].trim(), gapAssessment];
        }
        
        // If we have more than 4 parts, we need to merge middle parts intelligently
        // Look for empty parts or "New Skills Required" indicators
        let currentSkills = '';
        let newSkills = '';
        let foundNewSkillsSection = false;
        
        for (let i = 0; i < middleParts.length; i++) {
            const part = middleParts[i].trim();
            
            // Check if this looks like it starts the "New Skills Required" section
            if (part === '' && !foundNewSkillsSection) {
                foundNewSkillsSection = true;
                continue;
            }
            
            if (!foundNewSkillsSection) {
                currentSkills += (currentSkills ? ' | ' : '') + part;
            } else {
                newSkills += (newSkills ? ' | ' : '') + part;
            }
        }
        
        return [category, currentSkills, newSkills, gapAssessment];
    },

    /**
     * Format skills with clickable links
     */
    formatSkillsWithLinks(content) {
        if (!content || typeof content !== 'string') return content || '';
        
        // Split by newlines to handle multiple skills
        const skills = content.split('\n').filter(line => line.trim() && line.includes('•'));
        
        if (skills.length === 0) {
            // If no bullet points found, but still contains lightcast URLs, try to parse as single skill
            if (content.includes('https://lightcast.io/')) {
                const match = content.match(/•\s*(.+?)\|https:\/\/lightcast\.io\/open-skills\/skills\/([^|\s]+)/);
                if (match) {
                    const skillName = match[1].trim();
                    const skillId = match[2].trim();
                    return `<a href="https://lightcast.io/open-skills/skills/${skillId}" 
                               target="_blank" 
                               class="text-blue-600 hover:text-blue-800 text-sm hover:underline">
                                ${skillName}
                            </a>`;
                }
            }
            return content;
        }
        
        let html = '<div class="space-y-1">';
        skills.forEach(skill => {
            const match = skill.match(/•\s*(.+?)\|https:\/\/lightcast\.io\/open-skills\/skills\/([^|\s]+)/);
            if (match) {
                const skillName = match[1].trim();
                const skillId = match[2].trim();
                html += `
                    <div class="flex items-start">
                        <span class="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                        <a href="https://lightcast.io/open-skills/skills/${skillId}" 
                           target="_blank" 
                           class="text-blue-600 hover:text-blue-800 text-sm hover:underline">
                            ${skillName}
                        </a>
                    </div>
                `;
            } else {
                // Handle skills without URLs or malformed entries
                html += `<div class="text-sm text-gray-700">${skill}</div>`;
            }
        });
        html += '</div>';
        
        return html;
    },

    /**
     * Format timeline table for implementation roadmap
     */
    formatTimelineTable(content, formatting) {
        return this.formatAdvancedTable(content, formatting);
    },

    /**
     * Format advanced table with enhanced styling
     */
    formatAdvancedTable(content, formatting) {
        if (!content) return '';
        
        const lines = content.split('\n').filter(line => line.trim());
        if (lines.length < 2) return content;
        
        // Parse headers
        const headers = lines[0].split('|').map(h => h.trim()).filter(h => h);
        
        // Skip separator line
        const dataRows = lines.slice(2).map(line => 
            line.split('|').map(cell => cell.trim()).filter(cell => cell)
        );
        
        let html = `
            <div class="overflow-x-auto">
                <table class="min-w-full bg-white border border-gray-200 rounded-lg">
                    <thead class="bg-gray-50">
                        <tr>
        `;
        
        headers.forEach(header => {
            html += `<th class="px-4 py-3 text-left text-sm font-medium text-gray-700 border-b">${header}</th>`;
        });
        
        html += `
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">
        `;
        
        dataRows.forEach((row, index) => {
            html += `<tr class="${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}">`;
            row.forEach((cell, cellIndex) => {
                html += `<td class="px-4 py-3 text-sm text-gray-700 border-b">${cell}</td>`;
            });
            html += `</tr>`;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        return html;
    },

    /**
     * Format mixed content with bold labels
     */
    formatMixedContentWithLabels(content, boldLabels) {
        let html = '<div class="space-y-4">';
        
        boldLabels.forEach(label => {
            const regex = new RegExp(`${label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*([^\\n]+(?:\\n(?![A-Z][^:]*:)[^\\n]+)*)`, 'g');
            const match = content.match(regex);
            
            if (match) {
                const labelContent = match[0].replace(label, '').trim();
                html += `
                    <div class="bg-gray-50 rounded-lg p-4">
                        <span class="font-semibold text-gray-800">${label}</span>
                        <span class="text-gray-700 ml-1">${labelContent}</span>
                    </div>
                `;
            }
        });
        
        html += '</div>';
        return html;
    },

    /**
     * Generic subsection formatting fallback
     */
    formatGenericSubsection(title, subsectionData) {
        let html = `
            <div class="mb-6">
                <h3 class="text-xl font-epilogue font-semibold text-gray-800 mb-3">${title}</h3>
                <div class="text-gray-700">
        `;
        
        // Handle different content types
        if (subsectionData.type === 'content_items' && subsectionData.items) {
            // Multiple content items
            subsectionData.items.forEach(item => {
                html += this.formatContentItem(item);
            });
        } else if (subsectionData.type === 'formatted_content' && subsectionData.content) {
            // Single formatted content
            html += this.formatContentWithFormatting(subsectionData.content, subsectionData.formatting);
        } else {
            // Fallback to direct content
            html += `<p>${subsectionData.content || 'No content available'}</p>`;
        }
        
        html += `
                </div>
            </div>
        `;
        
        return html;
    },

    /**
     * Format individual content item with its formatting metadata
     */
    formatContentItem(item) {
        const content = item.content || '';
        const formatting = item.formatting || {};
        
        return this.formatContentWithFormatting(content, formatting);
    },

    /**
     * Format content with formatting metadata
     */
    formatContentWithFormatting(content, formatting) {
        if (!content) return '<p class="text-gray-500">No content available</p>';
        
        // Special handling for References & Supporting Research
        if (typeof content === 'string' && content.includes('References & Supporting Research')) {
            return this.formatReferencesSection(content);
        }
        
        // Special handling for Strategic Intelligence Dashboard
        if (typeof content === 'string' && content.includes('Strategic Intelligence Dashboard')) {
            return this.formatStrategicIntelligenceDashboard(content);
        }
        
        const contentType = formatting.content_type || 'paragraph';
        const boldLabels = formatting.bold_labels || [];
        const boldNumberedHeaders = formatting.bold_numbered_headers || false;
        
        switch (contentType) {
            case 'mixed':
                return this.formatMixedContent(content, boldLabels, boldNumberedHeaders);
                
            case 'paragraph':
                return `<p class="leading-relaxed my-3">${this.formatInlineElements(content)}</p>`;
            
            case 'bullet_list':
                if (Array.isArray(content)) {
                    let html = '<ul class="list-disc list-inside space-y-2 my-4">';
                    content.forEach(item => {
                        html += `<li class="leading-relaxed">${this.formatInlineElements(String(item))}</li>`;
                    });
                    html += '</ul>';
                    return html;
                } else {
                    // Handle string content with bullet points
                    const lines = content.split('\n').filter(line => line.trim());
                    let html = '<ul class="list-disc list-inside space-y-2 my-4">';
                    lines.forEach(line => {
                        const cleanLine = line.replace(/^[-•*]\s*/, '').trim();
                        if (cleanLine) {
                            html += `<li class="leading-relaxed">${this.formatInlineElements(cleanLine)}</li>`;
                        }
                    });
                    html += '</ul>';
                    return html;
                }
            
            case 'table':
                return this.formatTableContent(content, formatting);
            
            case 'key_value':
                return `
                    <div class="bg-blue-50 border-l-4 border-blue-400 p-4 my-4">
                        <p class="text-gray-700">${this.formatInlineElements(content)}</p>
                    </div>
                `;
            
            default:
                return `<p class="leading-relaxed my-3">${this.formatInlineElements(content)}</p>`;
        }
    },

    /**
     * Format mixed content with numbered headers and bold labels
     */
    formatMixedContent(content, boldLabels = [], boldNumberedHeaders = false) {
        if (!content) return '<p class="text-gray-500">No content available</p>';
        
        // Split content into sections (by double newlines)
        const sections = content.split('\n\n').filter(section => section.trim());
        
        if (boldNumberedHeaders) {
            // Handle numbered recommendations format
            let html = '<ol class="space-y-6 my-4">';
            
            sections.forEach(section => {
                const lines = section.split('\n').filter(line => line.trim());
                if (lines.length === 0) return;
                
                // First line should be the numbered header
                const headerLine = lines[0];
                const bulletLines = lines.slice(1);
                
                // Extract number and title from header (e.g., "1. HR Business Partner - Team Member - Group 2 - 52.0% similarity")
                const numberMatch = headerLine.match(/^(\d+)\.\s*(.+)/);
                if (numberMatch) {
                    const [, number, title] = numberMatch;
                    
                    html += `
                        <li class="ml-0">
                            <div class="font-semibold text-gray-800 mb-2">${title}</div>
                            <ul class="list-none space-y-1 ml-4">
                    `;
                    
                    // Format the sub-bullets with bold labels
                    bulletLines.forEach(line => {
                        const trimmedLine = line.replace(/^-\s*/, '').trim();
                        if (trimmedLine) {
                            html += `<li class="text-gray-700 leading-relaxed">• ${this.formatBoldLabels(trimmedLine, boldLabels)}</li>`;
                        }
                    });
                    
                    html += `
                            </ul>
                        </li>
                    `;
                } else {
                    // Fallback if numbering doesn't match expected format
                    html += `<li class="ml-0">${this.formatInlineElements(section)}</li>`;
                }
            });
            
            html += '</ol>';
            return html;
        } else {
            // Handle regular mixed content
            let html = '';
            sections.forEach(section => {
                html += `<div class="mb-4">${this.formatBoldLabels(section, boldLabels)}</div>`;
            });
            return html;
        }
    },

    /**
     * Format text with bold labels
     */
    formatBoldLabels(text, boldLabels = []) {
        let formattedText = text;
        
        boldLabels.forEach(label => {
            // Make the label bold
            const regex = new RegExp(`(${this.escapeRegex(label)})`, 'g');
            formattedText = formattedText.replace(regex, `<strong class="font-semibold text-gray-900">$1</strong>`);
        });
        
        return this.formatInlineElements(formattedText);
    },

    /**
     * Format References & Supporting Research section as numbered footnotes
     */
    formatReferencesSection(content) {
        if (!content || !content.includes('References & Supporting Research')) {
            return content;
        }
        
        // Split by the header to get the references content
        const parts = content.split('References & Supporting Research');
        if (parts.length < 2) return content;
        
        const beforeReferences = parts[0];
        const referencesContent = parts[1].trim();
        
        let html = beforeReferences;
        
        if (referencesContent) {
            html += `
                <div class="mt-8 pt-6 border-t border-gray-200">
                    <h4 class="text-lg font-semibold text-gray-800 mb-4">References & Supporting Research</h4>
                    <div class="text-sm text-gray-600 italic space-y-3">
            `;
            
            // Parse references - look for patterns like "Author (Year)." or similar
            const references = this.parseReferences(referencesContent);
            
            references.forEach((reference, index) => {
                html += `
                    <div class="flex">
                        <span class="font-normal text-gray-700 mr-2">${index + 1}.</span>
                        <span class="italic leading-relaxed">${reference.trim()}</span>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
        
        return html;
    },

    /**
     * Parse references text into individual reference entries
     */
    parseReferences(referencesText) {
        // Common patterns for reference separation:
        // 1. Author (Year). Title. Publisher.
        // 2. Number. Author (Year).
        // 3. Look for sentences ending with periods followed by capital letters
        
        const references = [];
        
        // Split by numbered patterns first (1., 2., etc.)
        const numberedMatches = referencesText.match(/\d+\.\s*[^.]+\./g);
        if (numberedMatches && numberedMatches.length > 1) {
            return numberedMatches.map(ref => ref.replace(/^\d+\.\s*/, '').trim());
        }
        
        // Split by author-year patterns: Author, Name (Year).
        const authorYearPattern = /([^.]+\([12]\d{3}\)[^.]*\.)/g;
        const authorYearMatches = referencesText.match(authorYearPattern);
        if (authorYearMatches && authorYearMatches.length > 1) {
            return authorYearMatches.map(ref => ref.trim());
        }
        
        // Fallback: Split by sentence boundaries and group logically
        const sentences = referencesText.split(/\.\s+(?=[A-Z])/);
        
        // Group sentences that look like they belong together
        let currentRef = '';
        
        sentences.forEach((sentence, index) => {
            sentence = sentence.trim();
            if (!sentence) return;
            
            // Add the period back if it was removed by split
            if (!sentence.endsWith('.')) {
                sentence += '.';
            }
            
            // Check if this starts a new reference (contains author-year pattern)
            const hasAuthorYear = /[A-Z][a-z]+.*\([12]\d{3}\)/.test(sentence);
            
            if (hasAuthorYear && currentRef) {
                // Save previous reference and start new one
                references.push(currentRef.trim());
                currentRef = sentence;
            } else {
                // Continue building current reference
                currentRef += (currentRef ? ' ' : '') + sentence;
            }
            
            // If this is the last sentence, save the current reference
            if (index === sentences.length - 1 && currentRef) {
                references.push(currentRef.trim());
            }
        });
        
        // If no pattern matching worked, split by likely separators
        if (references.length === 0) {
            const fallbackRefs = referencesText.split(/(?<=\.)\s+(?=[A-Z][a-z]+.*\([12]\d{3}\)|Additional|HSBC|Amazon|ING|Unilever)/);
            return fallbackRefs.filter(ref => ref.trim().length > 10);
        }
        
        return references.length > 0 ? references : [referencesText];
    },

    /**
     * Format Strategic Intelligence Dashboard as responsive cards/table
     */
    formatStrategicIntelligenceDashboard(content) {
        if (!content || !content.includes('Strategic Intelligence Dashboard')) {
            return content;
        }
        
        // Split by the header to get the dashboard content
        const parts = content.split('Strategic Intelligence Dashboard');
        if (parts.length < 2) return content;
        
        const beforeDashboard = parts[0];
        const dashboardContent = parts[1].trim();
        
        let html = beforeDashboard;
        
        if (dashboardContent) {
            // Parse the table data
            const lines = dashboardContent.split('\n').filter(line => line.trim());
            if (lines.length < 3) {
                return content; // Fallback if not enough data
            }
            
            const headers = lines[0].split('|').map(h => h.trim()).filter(h => h);
            const dataRows = lines.slice(2).map(line => 
                line.split('|').map(cell => cell.trim()).filter(cell => cell)
            ).filter(row => row.length >= 4); // Ensure we have all columns
            
            html += `
                <div class="mt-8">
                    <h4 class="text-lg font-semibold text-gray-800 mb-6">Strategic Intelligence Dashboard</h4>
                    
                    <!-- Mobile-first responsive layout -->
                    <div class="space-y-4 lg:space-y-0 lg:space-x-0">
            `;
            
            // Create responsive cards that stack on mobile, table on larger screens
            dataRows.forEach((row, index) => {
                if (row.length >= 4) {
                    const [metric, currentState, opportunity, businessImpact] = row;
                    
                    html += `
                        <div class="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                <div class="lg:border-r lg:border-gray-200 lg:pr-4">
                                    <div class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Strategic Metric</div>
                                    <div class="text-sm font-semibold text-gray-900">${metric}</div>
                                </div>
                                <div class="lg:border-r lg:border-gray-200 lg:pr-4">
                                    <div class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Current State</div>
                                    <div class="text-sm text-gray-700">${currentState}</div>
                                </div>
                                <div class="lg:border-r lg:border-gray-200 lg:pr-4">
                                    <div class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Opportunity Assessment</div>
                                    <div class="text-sm text-gray-700">${opportunity}</div>
                                </div>
                                <div>
                                    <div class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Business Impact</div>
                                    <div class="text-sm text-gray-700">${businessImpact}</div>
                                </div>
                            </div>
                        </div>
                    `;
                }
            });
            
            html += `
                    </div>
                    
                    <div class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div class="flex items-start">
                            <i class="fas fa-info-circle text-blue-600 mt-0.5 mr-2"></i>
                            <p class="text-sm text-blue-800">
                                Strategic metrics provide insights into workforce positioning and transition potential within NAB's career pathway network.
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }
        
        return html;
    },

    /**
     * Escape special regex characters
     */
    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    },

    /**
     * Format table content with proper Tailwind CSS styling
     */
    formatTableContent(content, formatting) {
        if (!content) return '<p class="text-gray-500">No content available</p>';
        
        // Handle markdown-style tables (pipe-separated)
        if (typeof content === 'string' && content.includes('|')) {
            return this.formatMarkdownStyleTable(content);
        }
        
        // Handle structured table data
        if (formatting && formatting.table_type) {
            switch (formatting.table_type) {
                case 'skills_breakdown':
                    return this.formatSkillsBreakdownTable(content);
                case 'metrics_table':
                    return this.formatMetricsTable(content);
                case 'deployment_table':
                    return this.formatDeploymentTable(content);
                default:
                    return this.formatGenericTable(content);
            }
        }
        
        // Fallback for unstructured content
        return this.formatGenericTable(content);
    },

    /**
     * Format markdown-style table with proper styling
     */
    formatMarkdownStyleTable(content) {
        const lines = content.split('\n').filter(line => line.trim());
        if (lines.length < 2) return `<p class="text-gray-700">${content}</p>`;
        
        // Check if this looks like a table (has pipes and separators)
        const hasTableStructure = lines.some(line => line.includes('|')) && 
                                 lines.some(line => line.includes('---'));
        
        if (!hasTableStructure) {
            return `<p class="text-gray-700">${content}</p>`;
        }
        
        // Parse table
        const headers = lines[0].split('|').map(h => h.trim()).filter(h => h);
        const dataRows = lines.slice(2).map(line => 
            line.split('|').map(cell => cell.trim()).filter(cell => cell)
        ).filter(row => row.length > 0);
        
        if (headers.length === 0) return `<p class="text-gray-700">${content}</p>`;
        
        let html = `
            <div class="overflow-x-auto my-4">
                <table class="min-w-full bg-white border border-gray-300 rounded-lg shadow-sm">
                    <thead class="bg-gray-50">
                        <tr>
        `;
        
        headers.forEach(header => {
            html += `<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">${header}</th>`;
        });
        
        html += `</tr></thead><tbody class="bg-white divide-y divide-gray-200">`;
        
        dataRows.forEach((row, index) => {
            const rowClass = index % 2 === 0 ? 'bg-white' : 'bg-gray-50';
            html += `<tr class="${rowClass} hover:bg-blue-50">`;
            
            row.forEach((cell, cellIndex) => {
                const cellClass = cellIndex === 0 ? 'font-medium text-gray-900' : 'text-gray-700';
                html += `<td class="px-6 py-4 whitespace-nowrap text-sm ${cellClass}">${cell || '-'}</td>`;
            });
            
            html += `</tr>`;
        });
        
        html += `</tbody></table></div>`;
        return html;
    },

    /**
     * Format skills breakdown table
     */
    formatSkillsBreakdownTable(content) {
        // Extract skills data from content
        const skillsMatch = content.match(/(\d+)\s+prescribed\s+skills\s+across\s+(\d+)\s+strategic\s+capability\s+areas/i);
        
        if (skillsMatch) {
            const [, totalSkills, categoryCount] = skillsMatch;
            
            return `
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-6 my-4">
                    <div class="flex items-center mb-4">
                        <div class="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-cogs text-white text-sm"></i>
                        </div>
                        <h4 class="text-lg font-semibold text-blue-900">Skills Portfolio Overview</h4>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="bg-white rounded-lg p-4 border border-blue-200">
                            <div class="text-2xl font-bold text-blue-600">${totalSkills}</div>
                            <div class="text-sm text-gray-600">Total Skills</div>
                        </div>
                        <div class="bg-white rounded-lg p-4 border border-blue-200">
                            <div class="text-2xl font-bold text-blue-600">${categoryCount}</div>
                            <div class="text-sm text-gray-600">Capability Areas</div>
                        </div>
                        <div class="bg-white rounded-lg p-4 border border-blue-200">
                            <div class="text-2xl font-bold text-green-600">High</div>
                            <div class="text-sm text-gray-600">Complexity Level</div>
                        </div>
                    </div>
                    ${this.formatMarkdownStyleTable(content)}
                </div>
            `;
        }
        
        return this.formatMarkdownStyleTable(content);
    },

    /**
     * Format metrics table with enhanced styling
     */
    formatMetricsTable(content) {
        if (content.includes('Metric') && content.includes('Score') && content.includes('Assessment')) {
            return `
                <div class="bg-purple-50 border border-purple-200 rounded-lg p-6 my-4">
                    <div class="flex items-center mb-4">
                        <div class="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-chart-line text-white text-sm"></i>
                        </div>
                        <h4 class="text-lg font-semibold text-purple-900">Strategic Intelligence Metrics</h4>
                    </div>
                    ${this.formatMarkdownStyleTable(content)}
                    <div class="mt-4 p-4 bg-white rounded-lg border border-purple-200">
                        <p class="text-sm text-purple-700">
                            <i class="fas fa-info-circle mr-2"></i>
                            These metrics assess workforce positioning and transition potential within NAB's career pathway network.
                        </p>
                    </div>
                </div>
            `;
        }
        
        return this.formatMarkdownStyleTable(content);
    },

    /**
     * Format deployment/organisational table
     */
    formatDeploymentTable(content) {
        return `
            <div class="bg-green-50 border border-green-200 rounded-lg p-6 my-4">
                <div class="flex items-center mb-4">
                    <div class="w-10 h-10 bg-green-600 rounded-full flex items-center justify-center mr-3">
                        <i class="fas fa-building text-white text-sm"></i>
                    </div>
                    <h4 class="text-lg font-semibold text-green-900">Organisational Deployment</h4>
                </div>
                <div class="text-gray-700 space-y-2">
                    ${this.formatBulletList(content)}
                </div>
            </div>
        `;
    },

    /**
     * Format generic table with basic styling
     */
    formatGenericTable(content) {
        if (typeof content === 'string' && content.includes('|')) {
            return this.formatMarkdownStyleTable(content);
        }
        
        return `
            <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 my-4">
                <div class="text-gray-700">${content}</div>
            </div>
        `;
    },

    /**
     * Format bullet list content
     */
    formatBulletList(content) {
        if (!content) return '';
        
        const lines = content.split('\n').filter(line => line.trim());
        let html = '<ul class="space-y-3">';
        
        lines.forEach(line => {
            const trimmedLine = line.trim();
            if (trimmedLine.startsWith('-') || trimmedLine.startsWith('•')) {
                const cleanLine = trimmedLine.replace(/^[-•]\s*/, '');
                html += `<li class="flex items-start">
                    <span class="w-2 h-2 bg-purple-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                    <span class="text-sm text-gray-700 leading-relaxed">${cleanLine}</span>
                </li>`;
            } else if (trimmedLine) {
                html += `<li class="flex items-start">
                    <span class="w-2 h-2 bg-purple-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                    <span class="text-sm text-gray-700 leading-relaxed">${trimmedLine}</span>
                </li>`;
            }
        });
        
        html += '</ul>';
        return html;
    },

    /**
     * Format section content with proper styling
     */
    formatSectionContent(content) {
        if (!content) return '<p class="text-gray-500">No content available</p>';
        
        // Split content into paragraphs and format
        const paragraphs = content.split('\n\n').filter(p => p.trim());
        let html = '';
        
        paragraphs.forEach(paragraph => {
            const trimmedParagraph = paragraph.trim();
            
            // Handle subsection headers (###)
            if (trimmedParagraph.startsWith('###')) {
                html += `<h3 class="text-xl font-epilogue font-semibold text-gray-800 mt-6 mb-3">${trimmedParagraph.substring(3).trim()}</h3>`;
                return;
            }
            
            // Handle subheaders (####)
            if (trimmedParagraph.startsWith('####')) {
                html += `<h4 class="text-lg font-epilogue font-medium text-gray-700 mt-4 mb-2">${trimmedParagraph.substring(4).trim()}</h4>`;
                return;
            }
            
            // Handle bullet points
            if (trimmedParagraph.includes('\n- ') || trimmedParagraph.startsWith('- ')) {
                const bulletPoints = trimmedParagraph.split('\n').filter(line => line.trim().startsWith('- '));
                if (bulletPoints.length > 0) {
                    html += '<ul class="list-disc list-inside space-y-2 my-4 text-gray-700">';
                    bulletPoints.forEach(point => {
                        html += `<li class="leading-relaxed">${this.formatInlineElements(point.substring(2).trim())}</li>`;
                    });
                    html += '</ul>';
                    return;
                }
            }
            
            // Handle numbered lists
            if (trimmedParagraph.includes('\n1. ') || /^\d+\.\s/.test(trimmedParagraph)) {
                const numberedItems = trimmedParagraph.split('\n').filter(line => /^\d+\.\s/.test(line.trim()));
                if (numberedItems.length > 0) {
                    html += '<ol class="list-decimal list-inside space-y-2 my-4 text-gray-700">';
                    numberedItems.forEach(item => {
                        const text = item.replace(/^\d+\.\s*/, '').trim();
                        html += `<li class="leading-relaxed">${this.formatInlineElements(text)}</li>`;
                    });
                    html += '</ol>';
                    return;
                }
            }
            
            // Handle tables (simple markdown format)
            if (trimmedParagraph.includes('|') && trimmedParagraph.split('|').length > 2) {
                html += this.formatMarkdownTable(trimmedParagraph);
                return;
            }
            
            // Handle bold labels and key-value content
            if (trimmedParagraph.includes(':') && !trimmedParagraph.includes('\n')) {
                const [label, ...valueParts] = trimmedParagraph.split(':');
                const value = valueParts.join(':').trim();
                
                if (value) {
                    html += `
                        <div class="bg-blue-50 border-l-4 border-blue-400 p-4 my-4">
                            <p class="text-gray-700">
                                <span class="font-semibold text-blue-900">${label.trim()}:</span> 
                                ${this.formatInlineElements(value)}
                            </p>
                        </div>
                    `;
                    return;
                }
            }
            
            // Regular paragraphs
            html += `<p class="text-gray-700 leading-relaxed my-4">${this.formatInlineElements(trimmedParagraph)}</p>`;
        });
        
        return html;
    },

    /**
     * Format markdown table
     */
    formatMarkdownTable(tableText) {
        const lines = tableText.split('\n').filter(line => line.trim());
        if (lines.length < 2) return '';
        
        const headers = lines[0].split('|').map(h => h.trim()).filter(h => h);
        const rows = lines.slice(2).map(line => {
            return line.split('|').map(cell => cell.trim()).filter(cell => cell);
        }).filter(row => row.length > 0);
        
        let html = `
            <div class="overflow-x-auto my-6">
                <table class="min-w-full divide-y divide-gray-200 border border-gray-300 rounded-lg">
                    <thead class="bg-gray-50">
                        <tr>
        `;
        
        headers.forEach(header => {
            html += `<th class="px-4 py-3 text-left text-sm font-semibold text-gray-900 border-r border-gray-200">${header}</th>`;
        });
        
        html += `</tr></thead><tbody class="bg-white divide-y divide-gray-200">`;
        
        rows.forEach((row, rowIndex) => {
            html += `<tr class="${rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'} hover:bg-blue-50">`;
            row.forEach(cell => {
                html += `<td class="px-4 py-3 text-sm text-gray-900 border-r border-gray-200">${this.formatTableCell(cell)}</td>`;
            });
            html += `</tr>`;
        });
        
        html += `</tbody></table></div>`;
        return html;
    },

    /**
     * Parse CLI markdown-style output into structured HTML
     */
    parseCliOutputToHtml(rawOutput, metadata) {
        if (!rawOutput) return '<p class="text-gray-500">No output available</p>';
        
        // Split into lines and process
        const lines = rawOutput.split('\n');
        let html = '';
        let inCodeBlock = false;
        let inTable = false;
        let tableHeaders = [];
        let currentSection = '';
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmedLine = line.trim();
            
            // Skip debug sections and system messages but allow section headers
            if (trimmedLine.includes('🔧 PATHWAY ANALYSIS DEBUG INFO') || 
                trimmedLine.includes('📋 Global Parameters') ||
                trimmedLine.includes('🧪 Testing') ||
                trimmedLine.includes('📊 Connecting to database') ||
                trimmedLine.includes('🏗️ Initializing') ||
                trimmedLine.includes('✅ Pathway Analysis generation') ||
                trimmedLine.includes('🎯 Key Features Demonstrated') ||
                trimmedLine.includes('🎉 Test suite completed')) {
                continue;
            }
            
            // Handle main headers (# and ##)
            if (trimmedLine.startsWith('# ')) {
                html += `<h1 class="text-3xl font-epilogue font-bold text-gray-900 mt-8 mb-4 border-b-2 border-red-600 pb-2">${trimmedLine.substring(2)}</h1>`;
                continue;
            }
            
            if (trimmedLine.startsWith('## ')) {
                html += `<h2 class="text-2xl font-epilogue font-semibold text-gray-800 mt-6 mb-3">${trimmedLine.substring(3)}</h2>`;
                continue;
            }
            
            // Handle sub-headers (###)
            if (trimmedLine.startsWith('### ')) {
                html += `<h3 class="text-xl font-epilogue font-medium text-gray-700 mt-4 mb-2">${trimmedLine.substring(4)}</h3>`;
                continue;
            }
            
            // Handle emphasized lines (🎯 Generated X opportunities)
            if (trimmedLine.includes('🎯 Generated') && trimmedLine.includes('opportunities')) {
                html += `<div class="bg-green-50 border-l-4 border-green-400 p-4 my-4">
                            <div class="flex items-center">
                                <i class="fas fa-bullseye text-green-600 mr-2"></i>
                                <p class="text-green-800 font-semibold">${trimmedLine}</p>
                            </div>
                        </div>`;
                continue;
            }
            
            // Handle target role lines
            if (trimmedLine.startsWith('Target Role:') && trimmedLine.includes('Similarity Score:')) {
                const parts = trimmedLine.split('|');
                if (parts.length >= 3) {
                    const targetRole = parts[0].replace('Target Role:', '').trim();
                    const similarity = parts[1].replace('Similarity Score:', '').trim();
                    const moveType = parts[2].replace('Move Type:', '').trim();
                    
                    html += `<div class="bg-blue-50 border border-blue-200 rounded-lg p-4 my-4">
                                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <span class="text-sm font-medium text-blue-600 uppercase tracking-wide">Target Role</span>
                                        <p class="text-blue-900 font-semibold">${targetRole}</p>
                                    </div>
                                    <div>
                                        <span class="text-sm font-medium text-blue-600 uppercase tracking-wide">Similarity</span>
                                        <p class="text-blue-900 font-semibold">${similarity}</p>
                                    </div>
                                    <div>
                                        <span class="text-sm font-medium text-blue-600 uppercase tracking-wide">Move Type</span>
                                        <p class="text-blue-900 font-semibold">${moveType}</p>
                                    </div>
                                </div>
                            </div>`;
                    continue;
                }
            }
            
            // Handle section dividers
            if (trimmedLine.match(/^-{20,}$/)) {
                html += `<div class="my-12 border-t-4 border-gray-300 border-dashed"></div>
                         <div class="text-center my-8">
                             <div class="inline-flex items-center px-6 py-2 bg-gray-100 rounded-full">
                                 <i class="fas fa-arrow-down text-gray-500 mr-2"></i>
                                 <span class="text-sm font-medium text-gray-600">Next Opportunity</span>
                                 <i class="fas fa-arrow-down text-gray-500 ml-2"></i>
                             </div>
                         </div>`;
                continue;
            }
            
            // Handle table-like content from Python dicts (improved detection)
            if (trimmedLine.includes("'title':") && (trimmedLine.includes("'content':") || i < lines.length - 5)) {
                // Look ahead to collect the full dictionary across multiple lines
                let dictContent = trimmedLine;
                let j = i + 1;
                let braceCount = (trimmedLine.match(/{/g) || []).length - (trimmedLine.match(/}/g) || []).length;
                
                // Collect subsequent lines until we have a complete dictionary
                while (j < lines.length && (braceCount > 0 || !dictContent.includes("'formatting':"))) {
                    const nextLine = lines[j].trim();
                    dictContent += ' ' + nextLine;
                    braceCount += (nextLine.match(/{/g) || []).length - (nextLine.match(/}/g) || []).length;
                    j++;
                    if (j - i > 10) break; // Safety limit
                }
                
                // Parse the collected dictionary content
                const tableHtml = this.parsePythonDictTable(dictContent);
                if (tableHtml) {
                    html += tableHtml;
                    i = j - 1; // Skip the lines we've processed
                    continue;
                }
            }
            
            // Handle simple markdown tables (| header | header |)
            if (trimmedLine.includes('|') && trimmedLine.split('|').length > 2) {
                const cells = trimmedLine.split('|').map(cell => cell.trim()).filter(cell => cell);
                
                if (!inTable) {
                    // Start new table
                    inTable = true;
                    tableHeaders = cells;
                    html += `<div class="overflow-x-auto my-4">
                                <table class="min-w-full divide-y divide-gray-200 border border-gray-300">
                                    <thead class="bg-gray-50">
                                        <tr>`;
                    cells.forEach(header => {
                        html += `<th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">${header}</th>`;
                    });
                    html += `</tr></thead><tbody class="bg-white divide-y divide-gray-200">`;
                } else if (cells.every(cell => cell.match(/^-+$/))) {
                    // Skip separator rows (|---|---|)
                    continue;
                } else {
                    // Regular table row
                    html += `<tr class="hover:bg-gray-50">`;
                    cells.forEach(cell => {
                        html += `<td class="px-4 py-2 text-sm text-gray-900 border-r border-gray-200">${this.formatTableCell(cell)}</td>`;
                    });
                    html += `</tr>`;
                }
                continue;
            }
            
            // Close table if we're in one and hit a non-table line
            if (inTable && !trimmedLine.includes('|')) {
                html += `</tbody></table></div>`;
                inTable = false;
            }
            
            // Handle regular paragraphs
            if (trimmedLine && !trimmedLine.startsWith('=') && !trimmedLine.match(/^[🎯🔧📋🚀🧪📊🏗️✅🎉]/)) {
                html += `<p class="text-gray-700 leading-relaxed my-3">${this.formatInlineElements(trimmedLine)}</p>`;
            }
        }
        
        // Close any open table
        if (inTable) {
            html += `</tbody></table></div>`;
        }
        
        return html || '<p class="text-gray-500">No content available for preview</p>';
    },

    /**
     * Parse Python dictionary table format into HTML
     */
    parsePythonDictTable(dictLine) {
        try {
            // Clean up the line and try to extract table data
            let cleanLine = dictLine.trim();
            console.log('🔍 Parsing dict line:', cleanLine.substring(0, 100) + '...');
            
            // Handle Opportunity Overview tables
            if (cleanLine.includes("'title': 'Opportunity Overview'")) {
                console.log('📊 Found Opportunity Overview table');
                return this.parseOpportunityOverviewTable(cleanLine);
            }
            
            // Handle Skills Transition Analysis tables
            if (cleanLine.includes("'title': 'Skills Transition Analysis'")) {
                console.log('🔄 Found Skills Transition Analysis table');
                return this.parseSkillsTransitionTable(cleanLine);
            }
            
            // Handle Implementation Roadmap tables
            if (cleanLine.includes("'title': 'Implementation Roadmap'")) {
                console.log('🛣️ Found Implementation Roadmap table');
                return this.parseImplementationRoadmapTable(cleanLine);
            }
            
            // Generic table handler for other structured content
            if (cleanLine.includes("'content_type': 'table'")) {
                console.log('📋 Found generic table content');
                return this.parseGenericStructuredTable(cleanLine);
            }
            
            return '';
        } catch (e) {
            console.warn('Error parsing Python dict table:', e);
            return '';
        }
    },

    /**
     * Parse Opportunity Overview table
     */
    parseOpportunityOverviewTable(dictLine) {
        try {
            // Extract the table text portion
            const tableMatch = dictLine.match(/'text': '([^']+)'/);
            if (!tableMatch) return '';
            
            const tableText = tableMatch[1];
            const lines = tableText.split('\\n');
            
            if (lines.length < 2) return '';
            
            // Parse header and rows - need special handling for skill URLs
            const headers = lines[0].split('|').map(h => h.trim()).filter(h => h);
            const rows = lines.slice(2).map(line => {
                // Split by pipes, but merge back skill names with their URLs
                const rawCells = line.split('|').map(cell => cell.trim());
                const mergedCells = [];
                let i = 0;
                
                while (i < rawCells.length) {
                    const cell = rawCells[i];
                    
                    // Check if the next cell is a URL (starts with https://)
                    if (i + 1 < rawCells.length && rawCells[i + 1].startsWith('https://')) {
                        // This is a skill name followed by its URL - merge them
                        mergedCells.push(cell + '|' + rawCells[i + 1]);
                        i += 2; // Skip the next cell since we merged it
                    } else {
                        mergedCells.push(cell);
                        i++;
                    }
                }
                
                return mergedCells.filter(cell => cell);
            }).filter(row => row.length > 0);
            
            let html = `
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 my-6">
                    <h4 class="text-lg font-semibold text-blue-900 mb-4 flex items-center">
                        <i class="fas fa-chart-bar mr-2"></i>
                        Opportunity Overview
                    </h4>
                    <div class="overflow-x-auto">
                        <table class="min-w-full divide-y divide-blue-200">
                            <thead class="bg-blue-100">
                                <tr>`;
            
            headers.forEach(header => {
                html += `<th class="px-4 py-3 text-left text-sm font-semibold text-blue-900">${header}</th>`;
            });
            
            html += `</tr></thead><tbody class="bg-white divide-y divide-blue-100">`;
            
            rows.forEach(row => {
                html += `<tr class="hover:bg-blue-25">`;
                row.forEach((cell, index) => {
                    // Use the improved formatTableCell method
                    const formattedCell = this.formatTableCell(cell);
                    
                    const cellClass = index === 0 ? 'font-medium text-gray-900' : 
                                    index === 1 ? 'font-semibold text-blue-600' : 
                                    'text-gray-700';
                    html += `<td class="px-4 py-3 text-sm ${cellClass}">${formattedCell}</td>`;
                });
                html += `</tr>`;
            });
            
            html += `</tbody></table></div></div>`;
            return html;
        } catch (e) {
            return this.createTablePlaceholder('Opportunity Overview', 'Structured metrics table with role compatibility, skills match, and development timeline.');
        }
    },

    /**
     * Parse Skills Transition Analysis table
     */
    parseSkillsTransitionTable(dictLine) {
        try {
            // Extract the table text portion
            const tableMatch = dictLine.match(/'text': '([^']+)'/);
            if (!tableMatch) return '';
            
            const tableText = tableMatch[1];
            console.log('🔍 Raw table text:', tableText);
            const lines = tableText.split('\\n');
            console.log('📄 Table lines:', lines);
            
            if (lines.length < 2) return '';
            
            // Parse header 
            const headers = lines[0].split('|').map(h => h.trim()).filter(h => h);
            console.log('📋 Headers:', headers);
            
            // Group lines by category - each category starts with a category name followed by skills
            const categoryGroups = [];
            let currentCategory = null;
            let currentSkills = [];
            let requiredSkills = [];
            let gapAssessment = '';
            
            for (let i = 2; i < lines.length; i++) { // Skip header and separator
                const line = lines[i].trim();
                if (!line) continue;
                
                console.log(`🔍 Processing line ${i-2}:`, line);
                
                // Check if this line starts a new category (doesn't start with •)
                if (!line.startsWith('•') && line.includes('|')) {
                    // Save previous category if exists
                    if (currentCategory) {
                        categoryGroups.push({
                            category: currentCategory,
                            currentSkills: currentSkills.slice(),
                            requiredSkills: requiredSkills.slice(),
                            gapAssessment: gapAssessment
                        });
                    }
                    
                    // Parse new category line
                    const parts = line.split('|').map(p => p.trim());
                    currentCategory = parts[0];
                    currentSkills = [];
                    requiredSkills = [];
                    gapAssessment = '';
                    
                    console.log(`📂 New category: "${currentCategory}", parts:`, parts);
                    
                    // Handle different structures:
                    // 1. "Category | • CurrentSkill|URL | ... | Gap"
                    // 2. "Category |  | • RequiredSkill|URL | Gap"
                    
                    if (parts.length >= 2) {
                        const secondPart = parts[1];
                        
                        if (secondPart && secondPart.startsWith('•')) {
                            // Current skill in column 2
                            if (parts.length >= 3 && parts[2].startsWith('https://')) {
                                currentSkills.push(secondPart + '|' + parts[2]);
                            } else {
                                currentSkills.push(secondPart);
                            }
                        } else if (parts.length >= 3 && parts[2] && parts[2].startsWith('•')) {
                            // Required skill in column 3 (column 2 is empty)
                            if (parts.length >= 4 && parts[3].startsWith('https://')) {
                                requiredSkills.push(parts[2] + '|' + parts[3]);
                            } else {
                                requiredSkills.push(parts[2]);
                            }
                        }
                        
                        // Gap assessment is usually the last non-URL part
                        const lastPart = parts[parts.length - 1];
                        if (lastPart && !lastPart.startsWith('https://') && !lastPart.startsWith('•')) {
                            gapAssessment = lastPart;
                        }
                    }
                } else if (line.startsWith('•')) {
                    // This is a skill line within the current category
                    const parts = line.split('|');
                    const skillName = parts[0].trim();
                    
                    if (parts.length >= 2 && parts[1].startsWith('https://')) {
                        // Current skill with URL
                        currentSkills.push(skillName + '|' + parts[1].trim());
                        
                        // Check for gap assessment at the end
                        if (parts.length >= 4) {
                            const lastPart = parts[parts.length - 1].trim();
                            if (lastPart && !lastPart.startsWith('https://')) {
                                gapAssessment = lastPart;
                            }
                        }
                    } else {
                        // Required skill (appears in Required Skills column)
                        if (parts.length >= 2) {
                            requiredSkills.push(skillName + '|' + parts[1].trim());
                        } else {
                            requiredSkills.push(skillName);
                        }
                    }
                }
            }
            
            // Don't forget the last category
            if (currentCategory) {
                categoryGroups.push({
                    category: currentCategory,
                    currentSkills: currentSkills.slice(),
                    requiredSkills: requiredSkills.slice(),
                    gapAssessment: gapAssessment
                });
            }
            
            console.log('📊 Category groups:', categoryGroups);
            
            // Build HTML table with enhanced scrolling for comprehensive data
            let html = `
                <div class="bg-green-50 border border-green-200 rounded-lg p-4 my-6">
                    <h4 class="text-lg font-semibold text-green-900 mb-4 flex items-center">
                        <i class="fas fa-exchange-alt mr-2"></i>
                        Complete Skills Transition Analysis
                        <span class="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                            ${categoryGroups.length} Categories
                        </span>
                    </h4>
                    <div class="overflow-auto max-h-[600px] border border-green-200 rounded-lg bg-white">
                        <table class="w-full divide-y divide-green-200 text-sm">
                            <thead class="bg-green-100 sticky top-0 z-10">
                                <tr>`;
            
            headers.forEach((header, index) => {
                // Make columns wider and more readable
                const width = index === 0 ? 'w-1/6' : index === 3 ? 'w-1/6' : 'w-1/3';
                html += `<th class="px-6 py-4 text-left text-sm font-semibold text-green-900 ${width}">${header}</th>`;
            });
            
            html += `</tr></thead><tbody class="bg-white divide-y divide-green-100">`;
            
            categoryGroups.forEach((group, index) => {
                // Check if this is the summary row
                const isSummaryRow = group.category.includes('COMPREHENSIVE SUMMARY');
                const rowClass = isSummaryRow ? 'bg-green-100 border-t-2 border-green-300' : 'hover:bg-green-25';
                
                html += `<tr class="${rowClass}">`;
                
                // Category column
                const categoryClass = isSummaryRow ? 'text-sm font-bold text-green-900' : 'text-sm font-medium text-gray-900';
                html += `<td class="px-6 py-4 ${categoryClass} align-top">${group.category}</td>`;
                
                // Current Skills column - format as bullet list with links
                const currentSkillsFormatted = this.formatSkillsList(group.currentSkills);
                const currentSkillsClass = isSummaryRow ? 'text-sm font-semibold text-green-800' : 'text-sm text-gray-700';
                html += `<td class="px-6 py-4 ${currentSkillsClass} align-top">${currentSkillsFormatted}</td>`;
                
                // Required Skills column - format as bullet list with links
                const requiredSkillsFormatted = this.formatSkillsList(group.requiredSkills);
                const requiredSkillsClass = isSummaryRow ? 'text-sm font-semibold text-orange-800' : 'text-sm text-gray-700';
                html += `<td class="px-6 py-4 ${requiredSkillsClass} align-top">${requiredSkillsFormatted}</td>`;
                
                // Gap Assessment column - format with badges
                const gapAssessmentFormatted = this.formatTableCell(group.gapAssessment);
                const gapClass = isSummaryRow ? 'text-sm font-bold text-blue-800' : 'text-sm font-semibold text-green-600';
                html += `<td class="px-6 py-4 ${gapClass} align-top">${gapAssessmentFormatted}</td>`;
                
                html += `</tr>`;
            });
            
            html += `</tbody></table></div></div>`;
            return html;
        } catch (e) {
            console.error('❌ Error parsing Skills Transition table:', e);
            return this.createTablePlaceholder('Skills Transition Analysis', 'Detailed breakdown of current skills, required skills, and gap assessment across multiple categories.');
        }
    },

    /**
     * Format a list of skills with proper bullet points and clickable links
     */
    formatSkillsList(skills) {
        if (!skills || skills.length === 0) {
            return '<span class="text-gray-400 italic">-</span>';
        }
        
        console.log('🎨 Formatting skills list:', skills);
        
        const formattedSkills = skills.map((skill, index) => {
            console.log(`  Skill ${index}: "${skill}"`);
            
            if (skill.includes('|https://')) {
                const parts = skill.split('|');
                const skillName = parts[0].replace('•', '').trim();
                const skillUrl = parts[1].trim();
                console.log(`    -> With URL: "${skillName}" -> ${skillUrl}`);
                return `<li class="text-xs mb-0.5 flex items-center leading-tight">
                            <span class="font-medium mr-2">${skillName}</span>
                            <a href="${skillUrl}" target="_blank" class="text-blue-500 hover:text-blue-700 underline" title="View skill details">
                                <i class="fas fa-external-link-alt text-xs"></i>
                            </a>
                        </li>`;
            } else {
                const skillName = skill.replace('•', '').trim();
                console.log(`    -> Plain text: "${skillName}"`);
                return `<li class="text-xs mb-0.5 leading-tight">${skillName}</li>`;
            }
        }).join('');
        
        return `<div class="max-w-md max-h-32 overflow-y-auto">
                    <ul class="list-disc list-inside space-y-0 text-xs leading-tight">${formattedSkills}</ul>
                </div>`;
    },

    /**
     * Parse Implementation Roadmap table
     */
    parseImplementationRoadmapTable(dictLine) {
        try {
            // Extract the table text portion
            const tableMatch = dictLine.match(/'text': '([^']+)'/);
            if (!tableMatch) return '';
            
            const tableText = tableMatch[1];
            const lines = tableText.split('\\n');
            
            if (lines.length < 2) return '';
            
            // Parse header and rows
            const headers = lines[0].split('|').map(h => h.trim()).filter(h => h);
            const rows = lines.slice(2).map(line => 
                line.split('|').map(cell => cell.trim()).filter(cell => cell)
            ).filter(row => row.length > 0);
            
            let html = `
                <div class="bg-purple-50 border border-purple-200 rounded-lg p-4 my-6">
                    <h4 class="text-lg font-semibold text-purple-900 mb-4 flex items-center">
                        <i class="fas fa-road mr-2"></i>
                        Implementation Roadmap
                    </h4>
                    <div class="overflow-x-auto">
                        <table class="min-w-full divide-y divide-purple-200">
                            <thead class="bg-purple-100">
                                <tr>`;
            
            headers.forEach(header => {
                html += `<th class="px-4 py-3 text-left text-sm font-semibold text-purple-900">${header}</th>`;
            });
            
            html += `</tr></thead><tbody class="bg-white divide-y divide-purple-100">`;
            
            rows.forEach((row, rowIndex) => {
                html += `<tr class="hover:bg-purple-25">`;
                row.forEach((cell, index) => {
                    const cellClass = index === 0 ? 'font-medium text-purple-900' : 
                                    index === 1 ? 'font-semibold text-blue-600' : 
                                    index === 3 ? 'font-medium text-green-600' :
                                    'text-gray-700';
                    html += `<td class="px-4 py-3 text-sm ${cellClass}">${cell}</td>`;
                });
                html += `</tr>`;
            });
            
            html += `</tbody></table></div></div>`;
            return html;
        } catch (e) {
            return this.createTablePlaceholder('Implementation Roadmap', 'Step-by-step timeline with phases, activities, and success measures for career transition.');
        }
    },

    /**
     * Create a styled placeholder for tables that couldn't be parsed
     */
    createTablePlaceholder(title, description) {
        const iconMap = {
            'Opportunity Overview': 'fas fa-chart-bar',
            'Skills Transition Analysis': 'fas fa-exchange-alt',
            'Implementation Roadmap': 'fas fa-road'
        };
        
        const colorMap = {
            'Opportunity Overview': 'blue',
            'Skills Transition Analysis': 'green',
            'Implementation Roadmap': 'purple'
        };
        
        const icon = iconMap[title] || 'fas fa-table';
        const color = colorMap[title] || 'gray';
        
        return `
            <div class="bg-${color}-50 border border-${color}-200 rounded-lg p-6 my-6">
                <div class="flex items-center mb-3">
                    <i class="${icon} text-${color}-600 mr-3 text-lg"></i>
                    <h4 class="text-lg font-semibold text-${color}-900">${title}</h4>
                </div>
                <p class="text-${color}-700 mb-4">${description}</p>
                <div class="bg-white border border-${color}-200 rounded p-4">
                    <div class="flex items-center justify-center h-24">
                        <div class="text-center">
                            <i class="fas fa-table text-${color}-400 text-2xl mb-2"></i>
                            <p class="text-sm text-${color}-600">Structured table data will be displayed here</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Format table cell content (handle bullet points, links, etc.)
     */
    formatTableCell(cell) {
        // Handle empty cells
        if (!cell || cell.trim() === '') {
            return '<span class="text-gray-400 italic">-</span>';
        }
        
        // Handle bullet points with hyperlinks
        if (cell.includes('•')) {
            const items = cell.split('•').filter(item => item.trim());
            if (items.length > 1) {
                const formattedItems = items.map(item => {
                    const trimmedItem = item.trim();
                    
                    // Handle items with hyperlinks (format: "Skill Name|URL")
                    if (trimmedItem.includes('|https://')) {
                        const parts = trimmedItem.split('|');
                        const skillName = parts[0].trim();
                        const skillUrl = parts[1].trim();
                        return `<li class="text-xs mb-1 flex items-center">
                                    <span class="font-medium mr-2">${skillName}</span>
                                    <a href="${skillUrl}" target="_blank" class="text-blue-500 hover:text-blue-700" title="View skill details">
                                        <i class="fas fa-external-link-alt text-xs"></i>
                                    </a>
                                </li>`;
                    } else {
                        return `<li class="text-xs mb-1">${trimmedItem}</li>`;
                    }
                }).join('');
                
                return `<div class="max-w-sm">
                            <ul class="list-disc list-inside space-y-1">${formattedItems}</ul>
                        </div>`;
            }
        }
        
        // Handle single hyperlinks (without bullet points)
        if (cell.includes('https://')) {
            if (cell.includes('|https://')) {
                const parts = cell.split('|');
                const skillName = parts[0].trim();
                const skillUrl = parts[1].trim();
                return `<div class="flex items-center max-w-sm">
                            <span class="font-medium text-xs mr-2">${skillName}</span>
                            <a href="${skillUrl}" target="_blank" class="text-blue-500 hover:text-blue-700" title="View skill details">
                                <i class="fas fa-external-link-alt text-xs"></i>
                            </a>
                        </div>`;
            } else {
                // Replace standalone URLs with link icons
                return cell.replace(/https:\/\/[^\s]+/g, '<a href="$&" target="_blank" class="text-blue-500 hover:text-blue-700" title="View details"><i class="fas fa-external-link-alt text-xs"></i></a>');
            }
        }
        
        // Handle assessment text with special formatting
        if (cell.includes('Transferable skills available')) {
            return '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">Transferable skills available</span>';
        }
        
        if (cell.includes('New skills needed')) {
            return '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">New skills needed</span>';
        }
        
        if (cell.includes('Skills foundation:')) {
            return `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">${cell}</span>`;
        }
        
        // Handle long text - truncate and add word wrapping
        if (cell.length > 100) {
            return `<div class="max-w-sm text-xs leading-relaxed">${cell}</div>`;
        }
        
        return `<span class="text-xs">${cell}</span>`;
    },

    /**
     * Format inline elements (bold, emphasis, etc.)
     */
    formatInlineElements(text) {
        // Handle percentages
        text = text.replace(/(\d+\.?\d*)%/g, '<span class="font-semibold text-blue-600">$1%</span>');
        
        // Handle job transitions (arrow notation)
        text = text.replace(/Group\s+(\d+)\s+→\s+Group\s+(\d+)/g, '<span class="font-semibold text-purple-600">Group $1 → Group $2</span>');
        
        // Handle costs/savings
        text = text.replace(/\$(\d+[KM]?\+?)/g, '<span class="font-semibold text-green-600">$$$1</span>');
        
        return text;
    },

    // Display generation results
    displayResults(data) {
        console.log('📄 Displaying results:', data);

        const documentInfo = data.document || {};
        const filename = documentInfo.filename || 'CAREER_ANALYSIS.docx';
        const format = documentInfo.format || 'word';

        const content = `
            <div class="alert-custom bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 class="text-lg font-semibold text-green-900 mb-3">
                    <i class="fas fa-check-circle mr-2"></i>
                    Career Transition Analysis Generated Successfully
                </h3>
                <div class="space-y-2 text-sm">
                    <p><span class="font-medium">Narrative Type:</span> <span class="text-green-800">${data.narrative_type}</span></p>
                    <p><span class="font-medium">Confidence Level:</span> <span class="text-green-800">${data.confidence_level}</span></p>
                    <p><span class="font-medium">Document Format:</span> <span class="text-green-800">${format.toUpperCase()}</span></p>
                    <p><span class="font-medium">Filename:</span> <span class="text-green-800">${filename}</span></p>
                </div>
            </div>
            <div class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 class="font-semibold text-blue-900 mb-2">
                    <i class="fas fa-download mr-2"></i>
                    Document Ready
                </h4>
                <p class="text-blue-700 mb-3">Your Career Transition Analysis has been generated and is ready for download.</p>
                <button onclick="SkillEngine.CAREER_ANALYSISs.downloadDocument('${filename}')" 
                        class="btn-nab px-4 py-2 text-white font-source font-medium rounded-md hover:bg-red-700 transition-colors">
                    <i class="fas fa-file-download mr-2"></i>
                    Download ${format.toUpperCase()} Document
                </button>
            </div>
            ${data.document && data.document.content ? `
            <div class="mt-4">
                <h4 class="font-semibold text-gray-900 mb-2">Content Preview:</h4>
                <div class="bg-gray-100 p-4 rounded-lg text-sm max-h-96 overflow-y-auto border">
                    ${this.formatDocumentContent(data.document.content)}
                </div>
            </div>
            ` : ''}
        `;

        this.updatePreviewContent(content);
    },

    // Display error message
    displayError(errorMessage) {
        console.error('❌ Displaying error:', errorMessage);

        const content = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                <h3 class="text-lg font-semibold text-red-900 mb-2">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    Error
                </h3>
                <p class="text-red-700">${errorMessage}</p>
            </div>
        `;

        this.updatePreviewContent(content);
    },

    // Update preview content with animation
    updatePreviewContent(content) {
        const previewContent = document.getElementById('previewContent');
        if (previewContent) {
            previewContent.innerHTML = content;
            previewContent.classList.add('preview-content-enter');
            
            // Remove animation class after animation completes
            setTimeout(() => {
                previewContent.classList.remove('preview-content-enter');
            }, 300);
        }
    },

    // Show alert notification
    showAlert(message, type = 'info') {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Add to page
        document.body.appendChild(alertDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    },

    // Utility functions
    getSelectedJobTitle(selectId) {
        const select = document.getElementById(selectId);
        return select ? select.options[select.selectedIndex]?.text || '' : '';
    },

    // Helper methods for preview formatting
    renderSection(title, content) {
        if (!content) return '';
        
        let sectionHtml = `
            <div class="mb-6">
                <h3 class="text-lg font-epilogue font-semibold text-gray-900 mb-3">${title}</h3>
                <div class="space-y-3 text-sm text-gray-700 leading-relaxed">
        `;
        
        if (typeof content === 'string') {
            sectionHtml += `<p>${content}</p>`;
        } else if (typeof content === 'object') {
            for (const [key, value] of Object.entries(content)) {
                if (value) {
                    sectionHtml += `
                        <div class="mb-3">
                            <h4 class="font-medium text-gray-800 mb-1">${this.formatSubsectionTitle(key)}</h4>
                            <p>${value}</p>
                        </div>
                    `;
                }
            }
        }
        
        sectionHtml += `
                </div>
            </div>
        `;
        
        return sectionHtml;
    },

    formatSubsectionTitle(key) {
        return key.replace(/_/g, ' ')
                 .replace(/\b\w/g, l => l.toUpperCase());
    },

    formatScenarioName(scenario) {
        const scenarios = {
            'skills_gap_analysis': 'Skills Gap Analysis',
            'skill_sunsetting': 'Skill Sunsetting',
            'division_restructure': 'Division Restructure'
        };
        return scenarios[scenario] || scenario;
    },

    formatAudienceName(audience) {
        const audiences = {
            'business_leaders': 'Business Leaders',
            'hr_partners': 'HR Partners',
            'affected_colleagues': 'Affected Colleagues',
            'learning_teams': 'Learning Teams'
        };
        return audiences[audience] || audience;
    },

    formatNarrativeType(narrativeType) {
        const types = {
            'excellent_opportunities': 'Excellent Opportunities',
            'development_required': 'Development Required',
            'significant_challenges': 'Significant Challenges'
        };
        return types[narrativeType] || narrativeType;
    },

    // Helper method to format document content for preview
    formatDocumentContent(content) {
        if (typeof content === 'string') {
            return content.replace(/\n/g, '<br>');
        } else if (typeof content === 'object') {
            return Object.entries(content)
                .map(([key, value]) => `<strong>${this.formatSubsectionTitle(key)}:</strong><br>${value}<br><br>`)
                .join('');
        }
        return 'Content preview not available';
    },

    // Method to handle document download
    downloadDocument(filename) {
        // This would typically trigger a download from the server
        console.log('📥 Downloading document:', filename);
        this.showAlert('Document download functionality will be implemented with actual file generation.', 'info');
    },

    // Reset form to initial state
    resetForm() {
        const form = document.getElementById('CAREER_ANALYSISForm');
        if (form) {
            form.reset();
            this.updateTargetJobVisibility();
            this.validateForm();
        }
    },

    // Export functionality (future enhancement)
    async exportCareerAnalysis(format = 'pdf') {
        if (!this.state.lastFormData) {
            this.showAlert('Please generate a Career Transition Analysis first.', 'warning');
            return;
        }

        console.log('📤 Exporting Career Transition Analysis as:', format);
        
        try {
            const formData = { ...this.state.lastFormData, output_format: format };
            
            const response = await fetch('/api/export-CAREER_ANALYSIS', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                // Handle file download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `career_analysis_${Date.now()}.${format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                throw new Error('Export failed');
            }

        } catch (error) {
            console.error('❌ Export error:', error);
            this.showAlert('Failed to Export Career Analysis: ' + error.message, 'danger');
        }
    },

    // Load job options from API
    async loadJobOptions() {
        try {
            console.log('📋 Loading job options...');
            
            const response = await fetch('/api/career-analysis-jobs?limit=100');
            const data = await response.json();
            
            if (data.success && data.jobs) {
                this.populateJobDropdowns(data.jobs);
                console.log(`✅ Loaded ${data.jobs.length} job options`);
            } else {
                console.warn('⚠️ No jobs data received from API');
            }
        } catch (error) {
            console.error('❌ Error loading job options:', error);
            // Keep the existing static options as fallback
        }
    },

    // Populate job dropdown menus with real data
    populateJobDropdowns(jobs) {
        const jobFromSelect = document.getElementById('jobFrom');
        const jobToSelect = document.getElementById('jobTo');
        
        if (jobFromSelect) {
            // Clear existing options except the first placeholder
            jobFromSelect.innerHTML = '<option value="">Select source job...</option>';
            
            // Add job options
            jobs.forEach(job => {
                const option = document.createElement('option');
                option.value = job.id;
                // Use standardised dropdown display name with function context
                const displayText = job.display_name_dropdown || job.display_name_standard || job.job_title || 'Unknown Job';
                option.textContent = `${displayText} (${job.function || 'Unknown Function'})`;
                option.dataset.function = job.function;
                option.dataset.jobProfileId = job.id; // Always include JobProfileID for reference
                jobFromSelect.appendChild(option);
            });
        }
        
        if (jobToSelect) {
            // Clear existing options except the first placeholder
            jobToSelect.innerHTML = '<option value="">Select target job...</option>';
            
            // Add job options
            jobs.forEach(job => {
                const option = document.createElement('option');
                option.value = job.id;
                // Use standardised dropdown display name with function context
                const displayText = job.display_name_dropdown || job.display_name_standard || job.job_title || 'Unknown Job';
                option.textContent = `${displayText} (${job.function || 'Unknown Function'})`;
                option.dataset.function = job.function;
                option.dataset.jobProfileId = job.id; // Always include JobProfileID for reference
                jobToSelect.appendChild(option);
            });
        }
    },

    // Search functionality now handled by Unified Search Module
    // Listen for job selection events from the unified search module
    setupUnifiedSearchIntegration() {
        document.addEventListener('jobSelected', (event) => {
            const { jobId, jobName } = event.detail;
            console.log('✅ Job selected via unified search:', jobId, jobName);
            
            // Update validation when job is selected
            this.validateForm();
        });
    },

    // Setup target job selector with multi-target support
    setupTargetJobSelector() {
        this.targetJobSelector = {
            selectedJobs: [],
            maxJobs: 5,
            
            addJob(jobId, displayName) {
                if (this.selectedJobs.find(job => job.id === jobId)) {
                    SkillEngine.CareerAnalysis.showValidationMessage('Job already selected', 'error');
                    return;
                }
                
                if (this.selectedJobs.length >= this.maxJobs) {
                    SkillEngine.CareerAnalysis.showValidationMessage(`Maximum ${this.maxJobs} target jobs allowed for comparison`, 'error');
                    return;
                }
                
                this.selectedJobs.push({ id: jobId, name: displayName });
                this.updateUI();
                SkillEngine.CareerAnalysis.validateForm();
            },
            
            removeJob(jobId) {
                this.selectedJobs = this.selectedJobs.filter(job => job.id !== jobId);
                this.updateUI();
                SkillEngine.CareerAnalysis.validateForm();
            },
            
            updateUI() {
                const chipsContainer = document.getElementById('selectedTargets');
                const hiddenInput = document.getElementById('jobTo');
                const searchInput = document.getElementById('jobToSearch');
                
                if (chipsContainer) {
                    chipsContainer.innerHTML = this.selectedJobs.map(job => `
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
                            ${job.name}
                            <button type="button" class="ml-2 text-blue-600 hover:text-blue-800" onclick="SkillEngine.CareerAnalysis.targetJobSelector.removeJob('${job.id}')">
                                <i class="fas fa-times"></i>
                            </button>
                        </span>
                    `).join('');
                }
                
                if (hiddenInput) {
                    hiddenInput.value = this.selectedJobs.map(job => job.id).join(',');
                }
                
                if (searchInput) {
                    searchInput.value = '';
                }
            },

            clearAll() {
                this.selectedJobs = [];
                this.updateUI();
                SkillEngine.CareerAnalysis.validateForm();
            }
        };
    },

    // Setup dynamic updates for top N and mode switching
    setupDynamicUpdates() {
        // Top N updates
        const topNInput = document.getElementById('topN');
        if (topNInput) {
            topNInput.addEventListener('input', (e) => {
                const value = e.target.value;
                document.getElementById('topNDisplay').textContent = value;
                document.getElementById('discoveryModeLabel').textContent = `Top ${value}`;
                document.getElementById('discoveryPathwayCount').textContent = `top ${value}`;
                this.validateForm();
            });
        }

        // Mode switching with help text
        document.querySelectorAll('input[name="analysis_mode"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.updateModeUI(e.target.value);
            });
        });
    },

    // Update mode-specific UI elements
    updateModeUI(mode) {
        const targetJobSection = document.getElementById('targetJobSection');
        const discoveryHelp = document.getElementById('discoveryModeHelp');
        const specificHelp = document.getElementById('specificModeHelp');
        
        if (mode === 'specific') {
            targetJobSection?.classList.remove('hidden');
            discoveryHelp?.classList.add('hidden');
            specificHelp?.classList.remove('hidden');
        } else {
            targetJobSection?.classList.add('hidden');
            discoveryHelp?.classList.remove('hidden');
            specificHelp?.classList.add('hidden');
            this.targetJobSelector?.clearAll();
        }
        
        this.validateForm();
    },

    // Show validation messages
    showValidationMessage(message, type) {
        const container = document.getElementById('validationMessages');
        if (!container) return;

        // Clear existing messages
        container.innerHTML = '';

        // Get template
        const templateId = type === 'error' ? 'validationError' : 'validationSuccess';
        const template = document.getElementById(templateId);
        if (!template) return;

        // Create message element
        const messageElement = template.content.cloneNode(true);
        const messageSpan = messageElement.querySelector('.validation-message');
        if (messageSpan) {
            messageSpan.textContent = message;
        }

        container.appendChild(messageElement);

        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (container.firstChild) {
                container.removeChild(container.firstChild);
            }
        }, 5000);
    },

    // Clear validation messages
    clearValidationMessages() {
        const container = document.getElementById('validationMessages');
        if (container) {
            container.innerHTML = '';
        }
    },

    // Validate current configuration
    validateCurrentConfiguration() {
        const mode = document.querySelector('input[name="analysis_mode"]:checked')?.value;
        const sourceJob = document.getElementById('jobFrom').value;
        const targetJobs = document.getElementById('jobTo').value;
        
        this.clearValidationMessages();
        
        // Source job validation
        if (!sourceJob) {
            this.showValidationMessage('Please select a source job', 'error');
            return false;
        }
        
        // Mode-specific validation
        if (mode === 'specific') {
            if (!targetJobs) {
                this.showValidationMessage('Please select at least one target job for specific analysis', 'error');
                return false;
            }
            
            const targetCount = targetJobs.split(',').filter(t => t.trim()).length;
            if (targetCount === 1) {
                this.showValidationMessage(`Ready for single transition analysis`, 'success');
            } else {
                this.showValidationMessage(`Ready for comparative analysis: ${targetCount} targets`, 'success');
            }
        } else {
            const simMin = document.getElementById('similarityMin').value;
            const simMax = document.getElementById('similarityMax').value;
            this.showValidationMessage(`Ready for discovery analysis: ${simMin}% - ${simMax}% similarity range`, 'success');
        }
        
        return true;
    },

    // Update similarity display
    updateSimilarityDisplay() {
        const minValue = document.getElementById('similarityMin')?.value || 40;
        const maxValue = document.getElementById('similarityMax')?.value || 90;
        const display = document.getElementById('similarityRangeDisplay');
        
        if (display) {
            display.textContent = `${minValue}% - ${maxValue}%`;
        }
    }
};

// Global function for advanced options toggle
function toggleAdvancedOptions() {
    const options = document.getElementById('advancedOptions');
    const chevron = document.getElementById('advancedChevron');
    
    if (options && chevron) {
        const isHidden = options.classList.contains('hidden');
        
        if (isHidden) {
            options.classList.remove('hidden');
            chevron.classList.add('rotate-90');
        } else {
            options.classList.add('hidden');
            chevron.classList.remove('rotate-90');
        }
    }
}

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize on Career Transition Analysis page
    if (document.getElementById('careerAnalysisForm')) {
        SkillEngine.CareerAnalysis.init();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SkillEngine.CareerAnalysis;
}
