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
        console.log('📄 Generate button clicked - Using HTML capture approach');

        // Prevent double-clicks and multiple rapid requests
        if (this.state.isGenerating) {
            console.log('⚠️ Generation already in progress, ignoring duplicate click');
            return;
        }

        // Debug: Check form validation status
        const formValid = this.validateForm();
        console.log('🔍 Form validation result:', formValid);
        if (!formValid) {
            this.showAlert('Please select a source job first.', 'warning');
            return;
        }

        // Debug: Check preview content availability
        const previewContent = document.getElementById('previewContent');
        const hasPreviewData = this.state.hasPreviewData;
        const previewHtmlLength = previewContent ? previewContent.innerHTML.length : 0;
        console.log('🔍 Preview content element exists:', !!previewContent);
        console.log('🔍 Preview data state:', hasPreviewData);
        console.log('🔍 Preview content HTML length:', previewHtmlLength);
        
        // Check if preview is available (either state flag or substantial HTML content)
        const hasValidPreview = hasPreviewData || (previewContent && previewHtmlLength > 1000);
        console.log('🔍 Has valid preview (state OR content):', hasValidPreview);
        
        if (!previewContent || !hasValidPreview) {
            console.log('❌ Preview check failed - showing warning');
            this.showAlert('Please generate a preview first before downloading the document.', 'warning');
            return;
        }

        try {
            this.state.isGenerating = true;
            this.setLoadingState(true);
            
            // Capture the HTML content from the preview panel
            const htmlContent = this.capturePreviewHTML();
            
            // Get form data for metadata
            const formData = this.getFormData();
            
            // Prepare payload for HTML-to-document conversion
            const payload = {
                html: htmlContent,
                format: 'word', // or 'pdf'
                metadata: {
                    job_from: formData.job_from,
                    analysis_mode: formData.analysis_mode,
                    generated_date: new Date().toISOString().split('T')[0]
                }
            };
            
            console.log('📄 Sending HTML content for document generation...');
            console.log('📄 Payload HTML length:', payload.html.length);
            console.log('📄 Payload metadata:', payload.metadata);
            
            // Check if server is responsive before attempting document generation
            try {
                console.log('🏥 Checking server health...');
                const healthResponse = await fetch('/api/career-analysis-jobs?limit=1');
                if (!healthResponse.ok) {
                    throw new Error('Server health check failed');
                }
                console.log('✅ Server is responsive');
            } catch (healthError) {
                console.log('⚠️ Server health check failed, but proceeding anyway:', healthError.message);
            }
            
            // Add retry logic for server restarts
            let response;
            let retryCount = 0;
            const maxRetries = 3;
            
            while (retryCount < maxRetries) {
                try {
                    // Add timeout to handle potential server restarts
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
                    
                    console.log(`🔄 Attempt ${retryCount + 1}/${maxRetries} - Making request...`);
                    
                    response = await fetch('/api/career-analysis-html-to-document', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(payload),
                        signal: controller.signal
                    });
                    
                    clearTimeout(timeoutId);
                    break; // Success, exit retry loop
                    
                } catch (fetchError) {
                    retryCount++;
                    console.log(`⚠️ Attempt ${retryCount} failed:`, fetchError.message);
                    
                    if (retryCount >= maxRetries) {
                        throw fetchError; // Re-throw if all retries exhausted
                    }
                    
                    // Wait before retry (exponential backoff)
                    const waitTime = Math.min(1000 * Math.pow(2, retryCount - 1), 5000);
                    console.log(`⏳ Server might be restarting. Waiting ${waitTime}ms before retry...`);
                    await new Promise(resolve => setTimeout(resolve, waitTime));
                }
            }

            if (response.ok) {
                console.log('✅ API response successful');
                
                // Handle direct file download
                const blob = await response.blob();
                console.log('📄 Created blob:', blob.size, 'bytes, type:', blob.type);
                
                const url = window.URL.createObjectURL(blob);
                console.log('🔗 Created blob URL:', url);
                
                // Extract filename from Content-Disposition header
                const contentDisposition = response.headers.get('Content-Disposition');
                console.log('📁 Content-Disposition header:', contentDisposition);
                
                let filename = 'career_analysis.docx';
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                    if (filenameMatch) {
                        filename = filenameMatch[1];
                    }
                }
                console.log('📁 Final filename:', filename);
                
                // Create temporary anchor and trigger download
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                a.style.display = 'none';
                document.body.appendChild(a);
                
                console.log('🖱️ Triggering download click...');
                a.click();
                
                // Fallback: If click doesn't work, try opening in new window
                setTimeout(() => {
                    // Check if download worked by seeing if the anchor is still there
                    if (document.body.contains(a)) {
                        console.log('⚠️ Anchor click may have failed, trying window.open fallback');
                        window.open(url, '_blank');
                    }
                }, 1000);
                
                // Cleanup with delay to ensure download starts
                setTimeout(() => {
                    if (document.body.contains(a)) {
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                        console.log('🧹 Cleanup completed');
                    }
                }, 3000);
                
                console.log('✅ Document download initiated:', filename);
                this.showAlert('Career Analysis document generated and downloaded successfully!', 'success');
                
            } else {
                // Handle error response (still JSON)
                const errorData = await response.json();
                throw new Error(errorData.error || 'Document generation failed');
            }

        } catch (error) {
            console.error('❌ Generation error:', error);
            
            // Handle specific error types
            let errorMessage = 'Failed to Generate Career Report: ';
            
            if (error.name === 'AbortError') {
                errorMessage += 'Request timed out after multiple attempts. The server might be restarting due to code changes. Please wait a moment and try again.';
            } else if (error.message.includes('Failed to fetch') || error.message.includes('ERR_CONNECTION_RESET') || error.message.includes('fetch')) {
                errorMessage += 'Connection lost during document generation. The Flask server restarted (likely due to file changes in development mode). Please try again - the server should be ready now.';
            } else {
                errorMessage += error.message;
            }
            
            this.displayError(errorMessage);
        } finally {
            this.state.isGenerating = false;
            this.setLoadingState(false);
        }
    },

    /**
     * Capture HTML content from the preview panel for document generation
     */
    capturePreviewHTML() {
        console.log('📸 Capturing preview HTML content...');
        
        // Get the preview content container
        const previewContent = document.getElementById('previewContent');
        if (!previewContent) {
            throw new Error('Preview content not found');
        }
        
        console.log('📸 Original HTML content length:', previewContent.innerHTML.length);
        console.log('📸 First 500 chars of original HTML:', previewContent.innerHTML.substring(0, 500));
        
        // Clone the content to avoid modifying the original
        const contentClone = previewContent.cloneNode(true);
        
        console.log('📸 Cloned HTML content length:', contentClone.innerHTML.length);
        
        // Remove any loading states, placeholders, or interactive elements
        this.cleanHTMLForDocument(contentClone);
        
        // Get the cleaned HTML
        const htmlContent = contentClone.innerHTML;
        
        console.log('📸 Final cleaned HTML content length:', htmlContent.length);
        console.log('📸 First 500 chars of cleaned HTML:', htmlContent.substring(0, 500));
        
        if (htmlContent.length < 100) {
            console.error('⚠️ WARNING: Cleaned HTML is very short, might be empty!');
            console.log('📸 Full cleaned HTML:', htmlContent);
        }
        
        return htmlContent;
    },

    /**
     * Clean HTML content for document generation
     */
    cleanHTMLForDocument(element) {
        console.log('🧹 Starting HTML cleanup - initial length:', element.innerHTML.length);
        
        // Remove loading spinners
        const loadingElements = element.querySelectorAll('#loadingSpinner, .animate-spin, [id*="loading"]');
        console.log(`🧹 Removing ${loadingElements.length} loading elements`);
        loadingElements.forEach(el => el.remove());
        
        // Remove placeholder content
        const placeholders = element.querySelectorAll('#preview-placeholder, [id*="placeholder"]');
        console.log(`🧹 Removing ${placeholders.length} placeholder elements`);
        placeholders.forEach(el => el.remove());
        
        // Remove empty sections
        const emptySections = element.querySelectorAll('.hidden, [style*="display: none"]');
        console.log(`🧹 Removing ${emptySections.length} hidden elements`);
        emptySections.forEach(el => el.remove());
        
        // Remove buttons and interactive elements
        const interactiveElements = element.querySelectorAll('button, [onclick], .cursor-pointer');
        console.log(`🧹 Removing ${interactiveElements.length} interactive elements`);
        interactiveElements.forEach(el => el.remove());
        
        // Clean up any remaining empty containers
        const emptyDivs = element.querySelectorAll('div:empty');
        console.log(`🧹 Removing ${emptyDivs.length} empty div elements`);
        emptyDivs.forEach(el => el.remove());
        
        console.log('🧹 HTML cleanup completed - final length:', element.innerHTML.length);
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
            formData.similarity_min = parseInt(document.getElementById('similarityMin')?.value) || 0;
            formData.similarity_max = parseInt(document.getElementById('similarityMax')?.value) || 95;
            
            // Add tie-breaking options
            formData.tie_breaking_options = {
                same_function_priority: document.getElementById('sameFunctionPriority')?.checked || false,
                career_progression_priority: document.getElementById('careerProgressionPriority')?.checked || false,
                minimal_level_jump: document.getElementById('minimalLevelJump')?.checked || false,
                skills_overlap_detail: document.getElementById('skillsOverlapDetail')?.checked || false
            };
        }

        // Add Primary Algorithm Selection
        const primaryAlgorithm = document.querySelector('input[name="primary_algorithm"]:checked')?.value;
        formData.primary_algorithm = primaryAlgorithm || 'enhanced'; // Default to enhanced

        // Add V2 Analytics preferences
        formData.v2_analytics = {
            defining_skills: document.getElementById('include-defining-skills')?.checked || false,
            job_family_context: document.getElementById('include-job-families')?.checked || false,
            movement_patterns: document.getElementById('include-movement-patterns')?.checked || false,
            skills_rarity: document.getElementById('include-rarity-analysis')?.checked || false,
            transition_insights: document.getElementById('include-transition-insights')?.checked || false,
            dual_similarity_analysis: document.getElementById('include-dual-similarity')?.checked || false
        };

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
        
        // DEBUG: Check if we're receiving the dual similarity data properly
        console.log('🔍 BACKEND DATA CHECK - pathways section:', data.content?.pathways?.subsections?.opportunities?.[0]?.header);
        
        // Also check if we can see the debug values from backend
        if (data.content?.pathways?.subsections?.opportunities?.[0]?.header) {
            console.log('🔍 CHECKING FOR DEBUG VALUES in header:', data.content.pathways.subsections.opportunities[0].header.includes('DEBUG:'));
        }
        
        if (!data.success) {
            this.displayError(`Failed to generate preview: ${data.error || 'Unknown error'}`);
            return;
        }

        // Check if we have structured content from all 5 sections
        const content = data.content || {};
        const hasStructuredContent = Object.keys(content).length > 0;
        
        // DEBUG: Log content structure
        // DEBUG: (removed verbose content structure logging)
        
        let htmlContent = '';
        
        if (hasStructuredContent) {
            // Use the structured content from all 5 sections
            htmlContent = this.parseStructuredContent(content, data);
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
                
                <!-- V2 Analytics Sections (now integrated within sections) -->
            </div>
        `;
        
        // Set preview data state to enable document generation
        this.state.hasPreviewData = true;
        console.log('✅ Preview data state set to:', this.state.hasPreviewData);
    },

    /**
     * Parse structured content from all 5 sections (like Word document)
     */
    parseStructuredContent(content, data) {
        let html = '';
        
        // 🚨 SPECIAL CASE: Check for no_results section first
        if (content.no_results) {
            console.log('🚫 DEBUG: Detected no_results section - showing clean no-results message');
            return this.formatNoResultsMessage(content.no_results);
        }
        
        // Focused section order: Introduction + Current Role Context + Top N Career Pathways
        const sectionOrder = [
            { key: 'introduction', defaultTitle: 'Introduction', icon: 'fas fa-chart-line' },
            { key: 'current_role_context', defaultTitle: 'Current Role Context', icon: 'fas fa-user-circle' },
            { key: 'pathways', defaultTitle: 'Top Career Pathways', icon: 'fas fa-route' }
        ];
        
        sectionOrder.forEach((section, index) => {
            if (content[section.key]) {
                const sectionData = content[section.key];
                const title = sectionData.title || section.defaultTitle;
                
                // DEBUG: Log pathways structure
                if (section.key === 'pathways') {
                    // DEBUG: (removed verbose pathway structure logging)
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
                            ${this.renderSectionSpecificV2Analytics(section.key, data)}
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
            } else if (subsectionKey === 'error') {
                // Special handling for pathway analysis errors (e.g., no results found)
                html += this.formatPathwayError(title, subsectionData);
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
        let content = subsectionData.content || '';
        
        // 🔧 FIX: Handle new structured content type from backend
        console.log('🔧 DEBUG: formatCoreCompetencyFoundation called');
        console.log('🔧 DEBUG: subsectionData.type:', subsectionData.type);
        console.log('🔧 DEBUG: content type:', typeof content);
        console.log('🔧 DEBUG: content:', content);
        
        let introText = '';
        let tableContent = '';
        
        // 🔧 WORKAROUND: Handle case where backend sends string content but we need to parse it as structured
        if (subsectionData.type === 'formatted_content' && typeof content === 'string' && content.includes('prescribed skills across')) {
            console.log('🔧 DEBUG: Detected Core Competency Foundation string content - attempting to parse as structured');
            
            // Split the content into intro text and table parts
            const parts = content.split('\n\n');
            let foundIntro = false;
            let tableStarted = false;
            
            for (let i = 0; i < parts.length; i++) {
                const part = parts[i].trim();
                console.log(`🔧 DEBUG: Processing part ${i}:`, part.substring(0, 50) + '...');
                
                // Look for the intro text (contains "prescribed skills across")
                if (part.includes('prescribed skills across') && !foundIntro) {
                    introText = part;
                    foundIntro = true;
                    console.log('🔧 DEBUG: Found intro in string content:', introText.substring(0, 50) + '...');
                }
                // Look for table content (contains headers like "Skill Type" or markdown table indicators)
                else if ((part.includes('|') && part.includes('Skill Type')) || 
                         (part.includes('Specialised Skill') && part.includes('Common Skill'))) {
                    // This looks like table content
                    tableContent = part;
                    tableStarted = true;
                    console.log('🔧 DEBUG: Found table in string content');
                }
                // If we've started a table, continue adding to it
                else if (tableStarted && part.includes('|')) {
                    tableContent += '\n' + part;
                }
            }
            
            // If we didn't find clear separation, try a different approach
            if (!foundIntro && !tableStarted) {
                console.log('🔧 DEBUG: Falling back to regex parsing');
                
                // Use regex to extract the intro sentence
                const introMatch = content.match(/(.*?prescribed skills across.*?strategic capability areas[:.!]?)/i);
                if (introMatch) {
                    introText = introMatch[1].trim();
                    console.log('🔧 DEBUG: Extracted intro via regex:', introText.substring(0, 50) + '...');
                    
                    // The rest should be table content
                    const remainingContent = content.substring(introMatch[0].length).trim();
                    if (remainingContent && remainingContent.length > 0) {
                        tableContent = remainingContent;
                        console.log('🔧 DEBUG: Extracted table via regex');
                    }
                }
            }
        }
        // Check for new structured mixed content type
        else if (subsectionData.type === 'structured_mixed_content' && Array.isArray(content)) {
            console.log('🔧 DEBUG: Processing structured_mixed_content with', content.length, 'items');
            
            // Extract intro text and table from structured content
            content.forEach((item, index) => {
                console.log(`🔧 DEBUG: Item ${index}:`, item);
                
                if (item && typeof item === 'object') {
                    // Check for paragraph content (intro text)
                    if (item.type === 'formatted_content' && item.content_type === 'paragraph') {
                        introText = item.text || '';
                        console.log('🔧 DEBUG: Found intro text:', introText.substring(0, 50) + '...');
                    }
                    // Check for structured table
                    else if (item.type === 'structured_table' && item.headers && item.rows) {
                        tableContent = item;
                        console.log('🔧 DEBUG: Found structured table with', item.headers.length, 'headers and', item.rows.length, 'rows');
                    }
                }
            });
        } 
        // Handle legacy structured content array from ContentFormatter
        else if (Array.isArray(content)) {
            console.log('🔧 DEBUG: Processing legacy array content with', content.length, 'items');
            
            // Extract intro text and table from structured content
            content.forEach((item, index) => {
                if (item && typeof item === 'object') {
                    // Check for paragraph content (intro text)
                    if (item.type === 'formatted_content' && item.content_type === 'paragraph') {
                        introText = item.text || '';
                    }
                    // Check for table content
                    else if (item.type === 'structured_table' || (item.headers && item.rows)) {
                        tableContent = item;
                    }
                    // Check for formatted table content
                    else if (item.type === 'formatted_content' && item.content_type === 'table') {
                        tableContent = item.text || '';
                    }
                } else if (typeof item === 'string') {
                    // Fallback: treat string items as content
                    if (item.includes('prescribed skills across')) {
                        introText = item;
                    } else if (item.includes('|')) {
                        tableContent = item;
                    }
                }
            });
            
            // Use introText for skills match, combine for full content if needed
            content = introText || content.join('\n\n');
        } else {
            // Handle legacy string content
            content = content.toString();
        }
        
        // Extract key information from the intro text
        const skillsMatch = (introText || content).match(/(\d+)\s+prescribed\s+skills\s+across\s+(\d+)\s+strategic\s+capability\s+areas/i);
        
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
        
        // 🔧 FIX: Add intro text as separate paragraph BEFORE the table
        if (introText && introText.trim()) {
            console.log('🔧 DEBUG: Adding intro text paragraph');
            html += `
                <div class="mb-4 p-4 bg-white rounded-lg border border-blue-200">
                    <p class="text-gray-700 leading-relaxed">${introText}</p>
                </div>
            `;
        }
        
        // Format the table content
        if (tableContent) {
            console.log('🔧 DEBUG: Rendering table content');
            if (typeof tableContent === 'object' && tableContent.headers && tableContent.rows) {
                // Handle structured table from ContentFormatter
                html += this.formatStructuredSkillsTable(tableContent);
            } else if (typeof tableContent === 'string' && tableContent.includes('|')) {
                // Handle legacy markdown table format
                html += this.formatMarkdownStyleTable(tableContent);
            } else {
                html += `<div class="text-gray-700">${tableContent}</div>`;
            }
        } else if (content.includes('|')) {
            // Fallback for legacy content
            html += this.formatMarkdownStyleTable(content);
        } else if (!introText) {
            // Only show content if we haven't already shown intro text
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
                    <div class="text-gray-700 space-y-4">
                        ${this.formatOrganisationalDeploymentContent(content)}
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Format organisational deployment content with proper separation of bullet points and table
     */
    formatOrganisationalDeploymentContent(content) {
        if (!content) return '';
        
        const lines = content.split('\n').filter(line => line.trim());
        let bulletPoints = [];
        let tableLines = [];
        let inTable = false;
        
        lines.forEach(line => {
            const trimmed = line.trim();
            
            // Skip table separator lines
            if (trimmed.match(/^[\-\|\s]+$/)) {
                return;
            }
            
            // Detect table header (Division | Positions | Primary Business Unit)
            if (trimmed.includes('Division') && trimmed.includes('Positions') && trimmed.includes('Primary Business Unit')) {
                inTable = true;
                tableLines.push(trimmed);
                return;
            }
            
            // If we're in table mode and line has pipes, it's a table row
            if (inTable && trimmed.includes('|') && trimmed.split('|').length >= 3) {
                tableLines.push(trimmed);
                return;
            }
            
            // If it's not a table line and we have content, it's a bullet point
            if (trimmed && !inTable) {
                bulletPoints.push(trimmed);
            }
        });
        
        let html = '';
        
        // Add bullet points first
        if (bulletPoints.length > 0) {
            html += '<ul class="space-y-2 mb-4">';
            bulletPoints.forEach(point => {
                html += `<li class="flex items-start">
                    <span class="w-2 h-2 bg-purple-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                    <span class="text-sm text-gray-700 leading-relaxed">${point}</span>
                </li>`;
            });
            html += '</ul>';
        }
        
        // Add table if we have table content
        if (tableLines.length > 0) {
            // Create proper markdown table format with separator line
            const headerLine = tableLines[0];
            const dataLines = tableLines.slice(1);
            
            // Create separator line based on header columns
            const headerColumns = headerLine.split('|').map(h => h.trim()).filter(h => h);
            const separatorLine = '|' + headerColumns.map(() => '--------').join('|') + '|';
            
            // Construct complete markdown table
            const completeTable = [
                headerLine,
                separatorLine,
                ...dataLines
            ].join('\n');
            
            html += `<div class="mt-4">
                ${this.formatMarkdownStyleTable(completeTable)}
            </div>`;
        }
        
        return html;
    },

    /**
     * Format Strategic Intelligence Metrics subsection with enhanced layout
     */
    formatStrategicIntelligenceMetrics(title, subsectionData) {
        const content = subsectionData.content || '';
        
        let html = `
            <div class="mb-8">
                <h3 class="text-xl font-epilogue font-semibold text-gray-800 mb-4">${title}</h3>
                <div class="bg-purple-50 border border-purple-200 rounded-lg p-6">
                    <div class="flex items-center mb-6">
                        <div class="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-chart-line text-white text-sm"></i>
                        </div>
                        <div>
                            <h4 class="text-lg font-semibold text-purple-900">Strategic Intelligence Metrics</h4>
                            <p class="text-sm text-purple-700">Quantitative workforce positioning analysis</p>
                        </div>
                    </div>
        `;
        
        // Split content and handle more simply
        const sections = content.split('\n\n');
        let tableSection = '';
        let bulletContent = '';
        
        sections.forEach(section => {
            const trimmed = section.trim();
            if (trimmed.includes('Metric') && trimmed.includes('Score') && trimmed.includes('Assessment')) {
                tableSection = trimmed;
            } else if (trimmed) {
                bulletContent += (bulletContent ? '\n\n' : '') + trimmed;
            }
        });
        
        // Add bullet point content (simplified)
        if (bulletContent) {
            html += `
                <div class="mb-6">
                    ${this.formatBulletList(bulletContent)}
                </div>
            `;
        }
        
        // Add metrics table
        if (tableSection) {
            html += `
                <div class="mb-4">
                    <h5 class="text-md font-semibold text-purple-900 mb-4">Current Metrics Assessment</h5>
                    ${this.formatMarkdownStyleTable(tableSection)}
                </div>
            `;
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
     * Format Pathway Analysis error messages (e.g., no results found)
     */
    formatPathwayError(title, subsectionData) {
        const content = subsectionData.content || '';
        
        // Check if this is a "no results found" type error
        const isNoResultsError = content.includes('No career pathways found') || 
                                content.includes('no opportunities') || 
                                content.includes('no results');
        
        let html = `
            <div class="space-y-6">
        `;
        
        if (isNoResultsError) {
            // Style as an informational message rather than an error
            html += `
                <div class="bg-amber-50 border border-amber-200 rounded-lg p-8 text-center">
                    <div class="flex flex-col items-center">
                        <div class="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mb-4">
                            <i class="fas fa-search text-amber-600 text-2xl"></i>
                        </div>
                        <h3 class="text-xl font-epilogue font-semibold text-amber-900 mb-2">
                            No Career Pathways Found
                        </h3>
                        <p class="text-amber-800 mb-4 max-w-md">
                            No opportunities were found within the selected similarity range. 
                            Try adjusting your similarity criteria to explore more options.
                        </p>
                        <div class="bg-white border border-amber-200 rounded-lg p-4 max-w-lg">
                            <h4 class="font-semibold text-amber-900 mb-2">
                                <i class="fas fa-lightbulb text-amber-600 mr-2"></i>
                                Suggestions:
                            </h4>
                            <ul class="text-sm text-amber-800 space-y-1 text-left">
                                <li>• Expand your similarity range (try 0-80% for broader results)</li>
                                <li>• Lower the minimum similarity threshold</li>
                                <li>• Consider that this may indicate a highly specialised role</li>
                                <li>• Review if this is the correct source job profile</li>
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        } else {
            // Generic error formatting
            html += `
                <div class="bg-red-50 border border-red-200 rounded-lg p-6">
                    <div class="flex items-center">
                        <div class="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center mr-4">
                            <i class="fas fa-exclamation-triangle text-red-600"></i>
                        </div>
                        <div>
                            <h3 class="text-lg font-semibold text-red-900">Analysis Error</h3>
                            <p class="text-red-800 mt-1">${content}</p>
                        </div>
                    </div>
                </div>
            `;
        }
        
        html += `
            </div>
        `;
        
        return html;
    },

    /**
     * Format a clean no-results message for the entire preview area
     */
    formatNoResultsMessage(noResultsSection) {
        const subsections = noResultsSection.subsections || {};
        const noResultsData = subsections.no_results_found || {};
        const content = noResultsData.content || 'No career opportunities were found within the selected similarity range.';
        
        // Extract suggestions from the content
        const suggestions = [
            'Expand your similarity range (try 0-80% for broader results)',
            'Lower the minimum similarity threshold',
            'Consider that this may indicate a highly specialised role',
            'Review if this is the correct source job profile'
        ];
        
        return `
            <div class="flex items-center justify-center min-h-96">
                <div class="text-center max-w-2xl mx-auto px-8">
                    <!-- Icon and main message -->
                    <div class="mb-8">
                        <div class="w-24 h-24 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-6">
                            <i class="fas fa-search text-amber-600 text-4xl"></i>
                        </div>
                        <h2 class="text-3xl font-epilogue font-bold text-gray-900 mb-4">
                            No Career Pathways Found
                        </h2>
                        <p class="text-lg text-gray-600 mb-8 leading-relaxed">
                            No opportunities were found within your selected similarity range. 
                            This suggests the current criteria may be too restrictive for meaningful career transitions.
                        </p>
                    </div>
                    
                    <!-- Suggestions card -->
                    <div class="bg-amber-50 border border-amber-200 rounded-xl p-8 mb-8">
                        <h3 class="text-xl font-epilogue font-semibold text-amber-900 mb-4 flex items-center justify-center">
                            <i class="fas fa-lightbulb text-amber-600 mr-3"></i>
                            What You Can Try
                        </h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                            ${suggestions.map(suggestion => `
                                <div class="flex items-start space-x-3">
                                    <div class="w-2 h-2 bg-amber-500 rounded-full mt-2 flex-shrink-0"></div>
                                    <span class="text-amber-800">${suggestion}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <!-- Action buttons -->
                    <div class="flex flex-col sm:flex-row gap-4 justify-center">
                        <button onclick="window.SkillEngine.CareerAnalysis.resetSimilaritySliders()" 
                                class="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium">
                            <i class="fas fa-sliders-h mr-2"></i>
                            Reset Similarity Range
                        </button>
                        <button onclick="window.SkillEngine.CareerAnalysis.expandSimilarityRange()" 
                                class="px-6 py-3 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors font-medium">
                            <i class="fas fa-expand-arrows-alt mr-2"></i>
                            Try Broader Range (0-80%)
                        </button>
                    </div>
                    
                    <!-- Help text -->
                    <div class="mt-8 p-6 bg-blue-50 border border-blue-200 rounded-lg">
                        <div class="flex items-center justify-center mb-3">
                            <i class="fas fa-info-circle text-blue-600 mr-2"></i>
                            <span class="font-semibold text-blue-900">Understanding Similarity Ranges</span>
                        </div>
                        <p class="text-blue-800 text-sm leading-relaxed">
                            Career transitions typically occur between 25-75% similarity. Higher ranges (80%+) indicate very similar roles 
                            with minimal change, while lower ranges (below 25%) may represent significant career pivots requiring substantial retraining.
                        </p>
                    </div>
                </div>
            </div>
        `;
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
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 text-sm">
                        <div class="flex items-center">
                            <i class="fas fa-bullseye mr-2"></i>
                            <span class="font-medium">Target:</span> 
                            <span class="ml-1">${headerInfo.targetRole}</span>
                        </div>
                        <div class="flex items-center">
                            <i class="fas fa-arrows-alt mr-2"></i>
                            <span class="font-medium">Type:</span> 
                            <span class="ml-1">${headerInfo.moveType}</span>
                        </div>
                    </div>
                    <!-- Dual Similarity Display -->
                    <div class="mt-4 pt-4 border-t border-white border-opacity-20">
                        <div class="flex items-center justify-between text-sm">
                            <div class="flex items-center">
                                <i class="fas fa-chart-line mr-2"></i>
                                <span class="font-medium">Similarity Analysis:</span>
                            </div>
                            <div class="flex space-x-4">
                                <div class="text-right">
                                    <div class="bg-white bg-opacity-20 px-2 py-1 rounded">
                                        <span class="font-semibold">${headerInfo.enhancedSimilarity || headerInfo.similarity}</span>
                                        <span class="text-xs opacity-75 ml-1">Enhanced</span>
                                    </div>
                                </div>
                                <div class="text-right">
                                    <div class="bg-white bg-opacity-10 px-2 py-1 rounded">
                                        <span class="font-semibold">${headerInfo.literalSimilarity || 'N/A'}</span>
                                        <span class="text-xs opacity-75 ml-1">Literal</span>
                                    </div>
                                </div>
                            </div>
                        </div>
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
        console.log('🔍 TARGETED DEBUG: Parsing opportunity header');
        console.log('📝 Header content:', JSON.stringify(headerString, null, 2));
        const lines = headerString.split('\n').filter(line => line.trim()); // Filter out empty lines
        console.log('📋 Header lines after split:', lines);
        const result = {};
        
        // Parse title from first line (remove ## prefix)
        if (lines[0]) {
            result.title = lines[0].replace(/^##\s*/, '').trim();
            // DEBUG: (removed title parsing log)
        }
        
        // Parse metadata from subsequent lines
        lines.forEach((line, index) => {
            console.log(`🔍 Processing line ${index}: "${line}"`);
            
            if (line.includes('Target Role:')) {
                console.log('🎯 Found Target Role line:', line);
                const match = line.match(/Target Role:\s*(.+?)\s*\|/);
                console.log('🎯 Target Role regex match:', match);
                if (match) {
                    result.targetRole = match[1].trim();
                    console.log('✅ Extracted targetRole via regex:', result.targetRole);
                } else {
                    // Fallback: try to extract from the line directly
                    const fallbackMatch = line.match(/Target Role:\s*(.+?)(?:\s*$|\s*\n)/);
                    console.log('🎯 Target Role fallback match:', fallbackMatch);
                    if (fallbackMatch) {
                        result.targetRole = fallbackMatch[1].trim();
                        console.log('✅ Extracted targetRole via fallback:', result.targetRole);
                    }
                }
            } else if (line.includes('Target:')) {
                console.log('🎯 Found Target line:', line);
                // Handle "Target: Software Engineer - 0 (R0041.0)" format
                const match = line.match(/Target:\s*(.+)/);
                console.log('🎯 Target regex match:', match);
                if (match) {
                    result.targetRole = match[1].trim();
                    console.log('✅ Extracted targetRole from Target:', result.targetRole);
                }
            }
            if (line.includes('Similarity Score:')) {
                console.log('📊 Found Similarity Score line:', line);
                const match = line.match(/Similarity Score:\s*([0-9.]+%)/);
                console.log('📊 Similarity Score regex match:', match);
                if (match) {
                    result.similarity = match[1];
                    console.log('✅ Extracted similarity:', result.similarity);
                }
            } else if (line.includes('Enhanced (PRIMARY):')) {
                console.log('📊 Found Enhanced similarity line:', line);
                const match = line.match(/Enhanced \(PRIMARY\):\s*([0-9.]+%)/);
                console.log('📊 Enhanced similarity regex match:', match);
                if (match) {
                    result.similarity = match[1]; // Primary similarity
                    result.enhancedSimilarity = match[1]; // Enhanced similarity
                    result.primaryAlgorithm = 'enhanced';
                    console.log('✅ Extracted enhanced similarity:', result.enhancedSimilarity);
                }
            } else if (line.includes('Literal (PRIMARY):')) {
                console.log('📊 Found Literal similarity line:', line);
                const match = line.match(/Literal \(PRIMARY\):\s*([0-9.]+%)/);
                console.log('📊 Literal similarity regex match:', match);
                if (match) {
                    result.similarity = match[1]; // Primary similarity
                    result.literalSimilarity = match[1]; // Literal similarity
                    result.primaryAlgorithm = 'literal';
                    console.log('✅ Extracted literal similarity:', result.literalSimilarity);
                }
            } else if (line.includes('• Enhanced:')) {
                console.log('📊 Found secondary Enhanced similarity line:', line);
                const match = line.match(/Enhanced:\s*([0-9.]+%)/);
                if (match) {
                    result.enhancedSimilarity = match[1];
                    console.log('✅ Extracted secondary enhanced similarity:', result.enhancedSimilarity);
                }
            } else if (line.includes('• Literal:')) {
                console.log('📊 Found secondary Literal similarity line:', line);
                const match = line.match(/Literal:\s*([0-9.]+%)/);
                if (match) {
                    result.literalSimilarity = match[1];
                    console.log('✅ Extracted secondary literal similarity:', result.literalSimilarity);
                }
            }
            if (line.includes('Move Type:')) {
                console.log('🏷️ Found Move Type line:', line);
                const match = line.match(/Move Type:\s*(.+?)(?:\s*$|\s*\n)/);
                console.log('🏷️ Move Type regex match:', match);
                if (match) {
                    result.moveType = match[1].trim();
                    console.log('✅ Extracted moveType:', result.moveType);
                }
            }
            if (line.includes('Type:') && !line.includes('Move Type:')) {
                console.log('🏷️ Found Type line:', line);
                const match = line.match(/Type:\s*(.+?)(?:\s*$|\s*\n)/);
                console.log('🏷️ Type regex match:', match);
                if (match) {
                    result.type = match[1].trim();
                    result.moveType = match[1].trim(); // Also set moveType for template compatibility
                    console.log('✅ Extracted type and moveType:', result.type);
                }
            }
            if (line.includes('Strategic Classification:')) {
                const match = line.match(/Strategic Classification:\s*(.+?)(?:\s*$|\s*\n)/);
                if (match) {
                    result.classification = match[1].trim();
                    console.log('🔍 DEBUG: Found classification:', result.classification);
                }
            }
        });
        
        // If targetRole is still undefined, set a fallback
        if (!result.targetRole || result.targetRole === 'undefined') {
            result.targetRole = 'Target Role';
            console.log('⚠️ Using fallback targetRole');
        }
        
        console.log('🎯 FINAL PARSED RESULT:', result);
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
        // DEBUG: (removed overview formatting log)
        
        // Check for new structured overview table format
        if (subsection.content_type === 'structured_overview_table' && subsection.content && typeof subsection.content === 'object') {
            // DEBUG: (removed table detection log)
            return this.formatStructuredTable(subsection.content, 'structured_overview_table');
        }
        // Legacy format handling
        else if (subsection.content && subsection.content.text) {
            console.log('🔍 DEBUG: Found content.text, using formatAdvancedTable');
            return this.formatAdvancedTable(subsection.content.text, subsection.content.formatting);
        } else if (subsection.content && typeof subsection.content === 'string') {
            console.log('🔍 DEBUG: Found string content, treating as table');
            return this.formatAdvancedTable(subsection.content, null);
        }
        
        console.log('🔍 DEBUG: No valid content found for opportunity overview');
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
        // DEBUG: (removed skills formatting log)
        
        // Check for new structured skills table format from backend
        if (subsection.content_type === 'structured_skills_table' && subsection.content && typeof subsection.content === 'object') {
            // DEBUG: (removed skills table detection log)
            // DEBUG: (removed table data log)
            return this.formatStructuredSkillsTable(subsection.content);
        } 
        // Legacy format handling
        else if (subsection.content && subsection.content.text) {
            console.log('🔍 DEBUG: Found content.text, using formatAdvancedSkillsTable');
            return this.formatAdvancedSkillsTable(subsection.content.text, subsection.content.formatting);
        } else if (subsection.content && typeof subsection.content === 'string') {
            console.log('🔍 DEBUG: Found string content, treating as skills table');
            return this.formatAdvancedSkillsTable(subsection.content, null);
        }
        
        console.log('🔍 DEBUG: No valid content found for skills transition analysis');
        return `<div class="text-gray-700">${subsection.content || 'No skills analysis available'}</div>`;
    },

    /**
     * Format structured skills table from backend (new format)
     */
    /**
     * Universal Structured Table Renderer - handles all structured table types
     */
    formatStructuredTable(tableData, tableType = 'default') {
        // DEBUG: (removed verbose table formatting logs)
        
        if (!tableData || !tableData.headers || !tableData.rows) {
            return '<div class="text-gray-700">Invalid table data</div>';
        }
        
        const { headers, rows, metadata } = tableData;
        
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
        
        // Add data rows with type-specific formatting
        rows.forEach((row, index) => {
            html += `<tr class="${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}">`;
            html += this.formatTableRowByType(row, headers, tableType);
            html += `</tr>`;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        // Add type-specific metadata summary
        html += this.formatTableMetadata(metadata, tableType);
        
        return html;
    },

    /**
     * Format table row based on table type
     */
    formatTableRowByType(row, headers, tableType) {
        let rowHtml = '';
        
        switch(tableType) {
            case 'structured_skills_table':
                rowHtml = this.formatSkillsTableRow(row, headers);
                break;
            case 'structured_timeline_table':
                rowHtml = this.formatTimelineTableRow(row, headers);
                break;
            case 'structured_overview_table':
                rowHtml = this.formatOverviewTableRow(row, headers);
                break;
            case 'structured_deployment_table':
                rowHtml = this.formatDeploymentTableRow(row, headers);
                break;
            case 'structured_strategic_table':
                rowHtml = this.formatStrategicTableRow(row, headers);
                break;
            default:
                rowHtml = this.formatGenericTableRow(row, headers);
                break;
        }
        
        return rowHtml;
    },

    /**
     * Format skills table row (existing logic)
     */
    formatSkillsTableRow(row, headers) {
        const rowArray = [
            row.category || '',
            row.current_skills || '',
            row.required_skills || '',
            row.gap_assessment || ''
        ];
        
        let html = '';
        rowArray.forEach((cell, cellIndex) => {
            let cellContent = cell || '';
            
            // Process skills columns (current and required skills)
            if (cellIndex === 1 || cellIndex === 2) {
                if (cellContent && cellContent.includes('|https://lightcast.io/')) {
                    cellContent = this.formatSkillsWithLinks(cellContent);
                } else if (cellContent && cellContent.includes('\n•')) {
                    cellContent = this.formatBulletList(cellContent);
                } else if (!cellContent.trim()) {
                    cellContent = '<span class="text-gray-400 italic">No skills in this category</span>';
                }
            }
            
            html += `<td class="px-4 py-3 text-sm text-gray-700 border-b align-top">${cellContent}</td>`;
        });
        
        return html;
    },

    /**
     * Format timeline table row 
     */
    formatTimelineTableRow(row, headers) {
        return `
            <td class="px-4 py-3 text-sm font-medium text-gray-900 border-b">${row.phase || ''}</td>
            <td class="px-4 py-3 text-sm text-gray-700 border-b">${row.timeline || ''}</td>
            <td class="px-4 py-3 text-sm text-gray-700 border-b">${row.key_activities || ''}</td>
            <td class="px-4 py-3 text-sm text-gray-700 border-b">${row.success_measures || ''}</td>
        `;
    },

    /**
     * Format overview table row
     */
    formatOverviewTableRow(row, headers) {
        const rowArray = Array.isArray(row) ? row : [
            row.metric || row[0] || '',
            row.value || row[1] || '',
            row.assessment || row[2] || ''
        ];
        
        let html = '';
        rowArray.forEach((cell, cellIndex) => {
            const cellClass = cellIndex === 0 ? 'font-medium text-gray-900' : 'text-gray-700';
            html += `<td class="px-4 py-3 text-sm ${cellClass} border-b">${cell}</td>`;
        });
        
        return html;
    },

    /**
     * Format deployment table row
     */
    formatDeploymentTableRow(row, headers) {
        const rowArray = Array.isArray(row) ? row : [
            row.division || row[0] || '',
            row.positions || row[1] || '',
            row.business_unit || row[2] || ''
        ];
        
        let html = '';
        rowArray.forEach((cell, cellIndex) => {
            html += `<td class="px-4 py-3 text-sm text-gray-700 border-b">${cell}</td>`;
        });
        
        return html;
    },

    /**
     * Format strategic table row
     */
    formatStrategicTableRow(row, headers) {
        const rowArray = Array.isArray(row) ? row : [
            row.metric || row[0] || '',
            row.score || row[1] || '',
            row.assessment || row[2] || '',
            row.significance || row[3] || ''
        ];
        
        let html = '';
        rowArray.forEach((cell, cellIndex) => {
            const cellClass = cellIndex === 0 ? 'font-medium text-gray-900' : 'text-gray-700';
            html += `<td class="px-4 py-3 text-sm ${cellClass} border-b">${cell}</td>`;
        });
        
        return html;
    },

    /**
     * Format generic table row
     */
    formatGenericTableRow(row, headers) {
        const rowArray = Array.isArray(row) ? row : headers.map((_, i) => row[i] || '');
        
        let html = '';
        rowArray.forEach((cell, cellIndex) => {
            html += `<td class="px-4 py-3 text-sm text-gray-700 border-b">${cell}</td>`;
        });
        
        return html;
    },

    /**
     * Format table metadata by type
     */
    formatTableMetadata(metadata, tableType) {
        if (!metadata) return '';
        
        switch(tableType) {
            case 'structured_skills_table':
                if (metadata.total_categories) {
                    return `
                        <div class="mt-4 p-3 bg-blue-50 rounded-lg">
                            <p class="text-sm text-blue-800">
                                <strong>Skills Analysis Summary:</strong> 
                                ${metadata.total_categories} skill categories analyzed, 
                                ${metadata.categories_with_current_skills || 0} with transferable skills, 
                                ${metadata.categories_with_new_skills || 0} requiring new skills development.
                            </p>
                        </div>
                    `;
                }
                break;
            case 'structured_timeline_table':
                return `
                    <div class="mt-4 p-3 bg-blue-50 border-l-4 border-blue-400">
                        <p class="text-sm text-blue-700">
                            <strong>Timeline Summary:</strong> 
                            ${metadata.total_phases || 'Multiple'} phases over ${metadata.estimated_duration || 'multiple months'}, 
                            targeting ${metadata.specialized_skills_count || 'N/A'} competencies.
                        </p>
                    </div>
                `;
            case 'structured_overview_table':
                return `
                    <div class="mt-4 p-3 bg-green-50 border-l-4 border-green-400">
                        <p class="text-sm text-green-700">
                            <strong>Opportunity Overview:</strong> 
                            ${metadata.table_style || 'Compact'} format with key transition metrics.
                        </p>
                    </div>
                `;
            default:
                return '';
        }
        
        return '';
    },

    /**
     * Legacy method - now delegates to universal renderer
     */
    formatStructuredSkillsTable(tableData) {
        return this.formatStructuredTable(tableData, 'structured_skills_table');
    },

    /**
     * Format skills list with expandable functionality
     */
    formatSkillsWithExpandable(skillsText, maxSkills = 3) {
        if (!skillsText || typeof skillsText !== 'string') {
            return skillsText || '';
        }

        // Split skills by common delimiters
        const skills = skillsText.split(/[,|;]/).map(skill => skill.trim()).filter(skill => skill.length > 0);
        
        if (skills.length <= maxSkills) {
            // If we have few skills, just show them all
            return skills.map(skill => `<span class="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full mr-1 mb-1">${skill}</span>`).join('');
        }

        // Show first few skills + expandable button
        const visibleSkills = skills.slice(0, maxSkills);
        const hiddenSkills = skills.slice(maxSkills);
        const uniqueId = `skills-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        return `
            <div class="skills-container">
                <div class="visible-skills">
                    ${visibleSkills.map(skill => `<span class="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full mr-1 mb-1">${skill}</span>`).join('')}
                    <button onclick="this.style.display='none'; document.getElementById('${uniqueId}').style.display='inline'" 
                            class="inline-block bg-gray-200 hover:bg-gray-300 text-gray-700 text-xs px-2 py-1 rounded-full mr-1 mb-1 cursor-pointer transition-colors">
                        +${hiddenSkills.length} more
                    </button>
                </div>
                <div id="${uniqueId}" class="hidden-skills" style="display: none;">
                    ${hiddenSkills.map(skill => `<span class="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full mr-1 mb-1">${skill}</span>`).join('')}
                </div>
            </div>
        `;
    },

    /**
     * Legacy method - now delegates to universal renderer
     */
    formatStructuredTimelineTable(tableData) {
        return this.formatStructuredTable(tableData, 'structured_timeline_table');
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
        // Check for new structured timeline table format from backend
        if (subsection.content_type === 'structured_timeline_table' && subsection.content && typeof subsection.content === 'object') {
            console.log('🔧 DEBUG: Found structured timeline table from backend');
            console.log('📊 DEBUG: Structured timeline data:', subsection.content);
            return this.formatStructuredTimelineTable(subsection.content);
        }
        // Legacy format handling
        else if (subsection.content && subsection.content.text) {
            return this.formatTimelineTable(subsection.content.text, subsection.content.formatting);
        }
        return `<div class="text-gray-700">${subsection.content || 'No roadmap available'}</div>`;
    },

    /**
     * Format advanced skills table with clickable links
     */
    formatAdvancedSkillsTable(content, formatting) {
        if (!content) return '';
        
        console.log(`🔍 DEBUG: formatAdvancedSkillsTable called with content length: ${content.length}`);
        
        // Check if we have pre-structured data in formatting
        if (formatting && formatting.headers && formatting.rows) {
            console.log(`🔍 DEBUG: Using pre-structured Skills table data`);
            console.log(`🔍 DEBUG: Headers:`, formatting.headers);
            console.log(`🔍 DEBUG: Rows:`, formatting.rows.length);
            
            return this.formatPreStructuredSkillsTable(formatting.headers, formatting.rows);
        }
        
        // Parse the malformed table content from backend
        console.log(`🔍 DEBUG: Parsing malformed Skills table text`);
        const lines = content.split('\n').filter(line => line.trim());
        if (lines.length < 3) return content;
        
        // Parse headers (first line)
        const headers = lines[0].split('|').map(h => h.trim()).filter(h => h);
        console.log(`🔍 DEBUG: Skills table headers (${headers.length}):`, headers);
        
        // Skip separator line (second line)
        // Reconstruct proper table rows from malformed data
        const reconstructedRows = this.reconstructSkillsTableRows(lines.slice(2));
        
        console.log(`🔍 DEBUG: Reconstructed ${reconstructedRows.length} table rows`);
        
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
        
        reconstructedRows.forEach((row, index) => {
            html += `<tr class="${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}">`;
            row.forEach((cell, cellIndex) => {
                // The cell content is already formatted HTML from finalizeSkillsRow
                // Don't double-process it, just insert it directly
                const cellContent = cell || '';
                
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
                // If the rows come from finalizeSkillsRow, they're already formatted HTML
                // If they come from raw data, we need to process them
                let cellContent = cell || '';
                
                // Only process if this looks like raw data (not already formatted HTML)
                if (cellContent && !cellContent.includes('<') && cellIndex >= 1 && cellIndex <= 2) {
                    // Process skills with links (columns 1 and 2: Current Skills and New Skills Required)
                    if (cellContent.includes('|https://lightcast.io/')) {
                        cellContent = this.formatSkillsWithLinks(cellContent);
                    } else if (cellContent.includes('\n•')) {
                        cellContent = this.formatBulletList(cellContent);
                    } else if (!cellContent.trim()) {
                        cellContent = '<span class="text-gray-400 italic">No skills in this category</span>';
                    }
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
     * Reconstruct proper table rows from malformed Skills Transition Analysis data
     * The backend sends malformed data where each skill is on a separate line
     * We need to group them back into proper 4-column rows
     */
    reconstructSkillsTableRows(dataLines) {
        console.log(`🔍 DEBUG: reconstructSkillsTableRows called with ${dataLines.length} lines`);
        
        const rows = [];
        let currentRow = null;
        let isInNewSkillsSection = false;
        
        for (let i = 0; i < dataLines.length; i++) {
            const line = dataLines[i].trim();
            if (!line) continue;
            
            console.log(`🔍 DEBUG: Processing line ${i}: "${line.substring(0, 80)}..."`);
            
            // Check if this line starts a new row (has category)
            // Pattern: "Category | • Skill|URL" or "Category |" (2+ pipes)
            const pipeCount = line.split('|').length - 1;
            
            if (pipeCount >= 2 && !line.startsWith('•')) {
                // This starts a new row
                if (currentRow) {
                    // Finalize previous row
                    rows.push(this.finalizeSkillsRow(currentRow));
                }
                
                // Start new row
                const parts = line.split('|');
                currentRow = {
                    category: parts[0].trim(),
                    currentSkills: [],
                    newSkills: [],
                    gapAssessment: '',
                    rawParts: parts
                };
                isInNewSkillsSection = false;
                
                // Add any skills from this line
                for (let j = 1; j < parts.length; j++) {
                    const part = parts[j].trim();
                    if (part && part.startsWith('•')) {
                        currentRow.currentSkills.push(part);
                    } else if (part && !part.startsWith('•') && j === parts.length - 1) {
                        // Last part might be gap assessment
                        const gapKeywords = ['ready', 'foundation', 'development', 'strong', 'moderate', 'limited', 'assessment'];
                        if (gapKeywords.some(keyword => part.toLowerCase().includes(keyword))) {
                            currentRow.gapAssessment = part;
                        }
                    }
                }
                
                console.log(`🔍 DEBUG: Started new row for category: "${currentRow.category}"`);
            } else if (line.startsWith('•') && currentRow) {
                // This is a skill line that belongs to current row
                // Use heuristics to determine if this is a new skill or current skill
                
                // Simple heuristic: if we've seen many current skills, start treating as new skills
                if (currentRow.currentSkills.length > 5 && !isInNewSkillsSection) {
                    isInNewSkillsSection = true;
                    console.log(`🔍 DEBUG: Switching to new skills section after ${currentRow.currentSkills.length} current skills`);
                }
                
                if (isInNewSkillsSection) {
                    currentRow.newSkills.push(line);
                    console.log(`🔍 DEBUG: Added to new skills: "${line.substring(0, 50)}..."`);
                } else {
                    currentRow.currentSkills.push(line);
                    console.log(`🔍 DEBUG: Added to current skills: "${line.substring(0, 50)}..."`);
                }
            } else if (currentRow && !line.startsWith('•')) {
                // This might be new skills or gap assessment
                const gapKeywords = ['ready', 'foundation', 'development', 'strong', 'moderate', 'limited', 'assessment'];
                if (gapKeywords.some(keyword => line.toLowerCase().includes(keyword))) {
                    currentRow.gapAssessment = line;
                    console.log(`🔍 DEBUG: Set gap assessment: "${line}"`);
                } else {
                    // Treat as new skills text
                    currentRow.newSkills.push(line);
                    console.log(`🔍 DEBUG: Added to new skills: "${line.substring(0, 50)}..."`);
                }
            }
        }
        
        // Finalize last row
        if (currentRow) {
            rows.push(this.finalizeSkillsRow(currentRow));
        }
        
        console.log(`🔍 DEBUG: Reconstructed ${rows.length} rows`);
        return rows;
    },

    /**
     * Finalize a skills row by formatting the content properly
     */
    finalizeSkillsRow(rowData) {
        console.log(`🔍 DEBUG: Finalizing row for category: "${rowData.category}"`);
        console.log(`🔍 DEBUG: Current skills count: ${rowData.currentSkills.length}`);
        console.log(`🔍 DEBUG: New skills count: ${rowData.newSkills.length}`);
        
        const category = rowData.category || '';
        
        // Format current skills with links - keep empty if no current skills
        const currentSkillsHtml = rowData.currentSkills.length > 0 
            ? this.formatSkillsWithLinks(rowData.currentSkills.join('\n'))
            : '';
        
        // Format new skills with links - keep empty if no new skills
        let newSkillsHtml;
        if (rowData.newSkills.length > 0) {
            newSkillsHtml = this.formatSkillsWithLinks(rowData.newSkills.join('\n'));
        } else {
            // If no new skills, leave empty (don't add fallback text)
            newSkillsHtml = '';
        }
        
        // Gap assessment based on NEW SKILLS REQUIRED (not current skills)
        let gapAssessment = rowData.gapAssessment;
        if (!gapAssessment || gapAssessment === 'Assessment pending') {
            if (rowData.newSkills.length === 0) {
                // No new skills needed = strong foundation
                gapAssessment = '<span class="text-green-600 font-medium">Strong foundation - ready for transition</span>';
            } else if (rowData.newSkills.length <= 3) {
                // Few new skills needed = moderate development
                gapAssessment = '<span class="text-yellow-600 font-medium">Moderate foundation - some development needed</span>';
            } else {
                // Many new skills needed = significant development
                gapAssessment = '<span class="text-red-600 font-medium">Limited foundation - significant development required</span>';
            }
        }
        
        return [category, currentSkillsHtml, newSkillsHtml, gapAssessment];
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
        console.log('🔍 DEBUG: parseSkillsTransitionRow input:', protectedLine);
        
        // For Skills Transition Analysis, we need to be very careful about the pipe splitting
        // The format is: Category | Current Skills (with bullets and URLs) | New Skills Required | Gap Assessment
        
        // Strategy: Find the first pipe (after category), then find the last pipe (before gap assessment)
        // Everything in between needs to be split into Current Skills and New Skills Required
        
        const firstPipeIndex = protectedLine.indexOf('|');
        if (firstPipeIndex === -1) {
            return [protectedLine.trim()];
        }
        
        const category = protectedLine.substring(0, firstPipeIndex).trim();
        const remainingContent = protectedLine.substring(firstPipeIndex + 1);
        
        // Find the last meaningful pipe (before gap assessment)
        // Gap assessment typically contains words like "ready", "foundation", "development", etc.
        const gapAssessmentKeywords = ['ready', 'foundation', 'development', 'strong', 'moderate', 'limited', 'assessment'];
        
        let lastPipeIndex = -1;
        let gapAssessment = '';
        
        // Work backwards to find the gap assessment
        const pipes = [];
        let currentIndex = 0;
        while ((currentIndex = remainingContent.indexOf('|', currentIndex)) !== -1) {
            pipes.push(currentIndex);
            currentIndex++;
        }
        
        // Try each pipe position from the end to find the gap assessment
        for (let i = pipes.length - 1; i >= 0; i--) {
            const potentialGapAssessment = remainingContent.substring(pipes[i] + 1).trim();
            
            // Check if this looks like a gap assessment
            const hasGapKeywords = gapAssessmentKeywords.some(keyword => 
                potentialGapAssessment.toLowerCase().includes(keyword)
            );
            
            if (hasGapKeywords && potentialGapAssessment.length < 100) { // Gap assessments are usually short
                lastPipeIndex = pipes[i];
                gapAssessment = potentialGapAssessment;
                break;
            }
        }
        
        if (lastPipeIndex === -1) {
            // Fallback: assume last pipe is the gap assessment
            lastPipeIndex = pipes[pipes.length - 1] || remainingContent.length;
            gapAssessment = remainingContent.substring(lastPipeIndex + 1).trim();
        }
        
        // Extract the skills content (between category and gap assessment)
        const skillsContent = remainingContent.substring(0, lastPipeIndex).trim();
        
        // Now split the skills content into Current Skills and New Skills Required
        // Look for empty sections or patterns that indicate the split
        const skillsParts = skillsContent.split('|').map(p => p.trim());
        
        let currentSkills = '';
        let newSkills = '';
        
        // Simple heuristic: if we have an even number of parts, split in half
        // If odd, give more to current skills
        const midPoint = Math.ceil(skillsParts.length / 2);
        
        currentSkills = skillsParts.slice(0, midPoint).join(' | ').trim();
        newSkills = skillsParts.slice(midPoint).join(' | ').trim();
        
        // Clean up empty sections
        if (currentSkills === '|' || currentSkills === '') currentSkills = '';
        if (newSkills === '|' || newSkills === '') newSkills = '';
        
        const result = [category, currentSkills, newSkills, gapAssessment];
        console.log('🔍 DEBUG: parseSkillsTransitionRow result:', result);
        
        return result;
    },

    /**
     * Format skills with clickable links
     */
    formatSkillsWithLinks(content) {
        if (!content) return '';
        
        // Handle both array-style input and string input
        let skillsArray = [];
        if (Array.isArray(content)) {
            skillsArray = content;
            // DEBUG: (removed array input log)
        } else if (typeof content === 'string') {
            // DEBUG: (removed string input log)
            // Split by newlines to handle multiple skills
            skillsArray = content.split('\n').filter(line => line.trim());
        } else {
            // DEBUG: (removed unknown type log)
            return content || '';
        }
        
        const formattedSkills = [];
        
        for (const skill of skillsArray) {
            const trimmedSkill = skill.trim();
            if (!trimmedSkill) continue;
            
            // Enhanced regex to catch various URL patterns
            const skillUrlMatch = trimmedSkill.match(/•\s*(.+?)\|https:\/\/lightcast\.io\/open-skills\/skills\/([A-Z0-9]+)/);
            
            if (skillUrlMatch) {
                const skillName = skillUrlMatch[1].trim();
                const skillId = skillUrlMatch[2].trim();
                const skillLink = `<a href="https://lightcast.io/open-skills/skills/${skillId}" 
                                   target="_blank" 
                                   class="text-blue-600 hover:text-blue-800 text-sm hover:underline"
                                   title="View skill details on Lightcast.io">
                                    • ${skillName}
                                  </a>`;
                formattedSkills.push(skillLink);
                // DEBUG: (removed skill link log)
            } else if (trimmedSkill.includes('https://lightcast.io/')) {
                // Try alternative parsing for malformed URLs
                const parts = trimmedSkill.split('|');
                if (parts.length >= 2) {
                    const skillName = parts[0].trim();
                    const url = parts[1].trim();
                    const skillIdMatch = url.match(/skills\/([A-Z0-9]+)/);
                    if (skillIdMatch) {
                        const skillId = skillIdMatch[1];
                        const skillLink = `<a href="https://lightcast.io/open-skills/skills/${skillId}" 
                                           target="_blank" 
                                           class="text-blue-600 hover:text-blue-800 text-sm hover:underline"
                                           title="View skill details on Lightcast.io">
                                            ${skillName}
                                          </a>`;
                        formattedSkills.push(skillLink);
                        console.log(`🔍 DEBUG: Alternative parsing - skill with link: "${skillName}" -> ${skillId}`);
                        continue;
                    }
                }
                // Fallback for malformed URL
                formattedSkills.push(`<span class="text-gray-700">${trimmedSkill}</span>`);
                console.log(`🔍 DEBUG: Malformed URL skill: "${trimmedSkill.substring(0, 30)}..."`);
            } else if (trimmedSkill.startsWith('•')) {
                // Skill without URL, keep as is
                formattedSkills.push(`<span class="text-gray-700">${trimmedSkill}</span>`);
                // DEBUG: (removed skill without link log)
            } else {
                // Non-skill content, keep as is
                formattedSkills.push(`<span class="text-gray-600">${trimmedSkill}</span>`);
            }
        }
        
        if (formattedSkills.length === 0) {
            console.log(`🔍 DEBUG: No skills found in content`);
            return content;
        }
        
        const result = formattedSkills.join('<br>');
        // DEBUG: (removed result count log)
        return result;
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
                // Check if this is a references section (small italic text)
                const isReferencesSection = formatting.small_italic_text === true;
                const listClass = isReferencesSection 
                    ? 'list-disc list-inside space-y-3 my-6 text-sm italic text-gray-600' 
                    : 'list-disc list-inside space-y-2 my-4';
                const itemClass = isReferencesSection 
                    ? 'leading-relaxed pl-2' 
                    : 'leading-relaxed';
                
                if (Array.isArray(content)) {
                    let html = `<ul class="${listClass}">`;
                    content.forEach(item => {
                        html += `<li class="${itemClass}">${this.formatInlineElements(String(item))}</li>`;
                    });
                    html += '</ul>';
                    return html;
                } else {
                    // Handle string content with bullet points
                    const lines = content.split('\n').filter(line => line.trim());
                    let html = `<ul class="${listClass}">`;
                    lines.forEach(line => {
                        const cleanLine = line.replace(/^[-•*]\s*/, '').trim();
                        if (cleanLine) {
                            html += `<li class="${itemClass}">${this.formatInlineElements(cleanLine)}</li>`;
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
        
        // Check for markdown-style bold headers (e.g., **Header:** content)
        if (content.includes('**') && content.includes(':**')) {
            return this.formatMarkdownBoldContent(content, boldNumberedHeaders);
        }
        
        // Split content into sections (by double newlines)
        const sections = content.split('\n\n').filter(section => section.trim());
        
        if (boldNumberedHeaders) {
            // Handle numbered recommendations format
            let html = '<div class="space-y-6 my-4">';
            
            sections.forEach((section, index) => {
                // Check if this section has markdown-style bold headers
                if (section.includes('**') && section.includes(':**')) {
                    html += this.formatMarkdownBoldSection(section, index + 1);
                } else {
                    // Handle regular numbered sections
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
                            <div class="mb-6">
                                <div class="font-semibold text-gray-800 mb-2">${number}. ${title}</div>
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
                            </div>
                        `;
                    } else {
                        // Fallback if numbering doesn't match expected format
                        html += `<div class="mb-4">${this.formatInlineElements(section)}</div>`;
                    }
                }
            });
            
            html += '</div>';
            return html;
        } else {
            // Handle regular mixed content
            let html = '';
            sections.forEach(section => {
                // Check if this section contains bullet points
                const lines = section.split('\n').filter(line => line.trim());
                const hasBulletPoints = lines.some(line => 
                    line.trim().match(/^[-•*]\s+/) || 
                    line.includes(': - ') || 
                    line.includes('- ') && lines.length > 1
                );
                
                if (hasBulletPoints) {
                    // Format as bullet list
                    html += this.formatSectionWithBullets(section, boldLabels);
                } else {
                    // Check if this section has structured content (headers followed by content)
                    const hasStructuredHeaders = section.match(/^[A-Z][^.]*\([^)]*\)/m) || 
                                               section.match(/^[A-Z][^.]*Strategy/m) ||
                                               section.match(/^[A-Z][^.]*Actions/m);
                    
                    if (hasStructuredHeaders) {
                        html += this.formatStructuredSection(section, boldLabels);
                    } else {
                        // Format as regular paragraph
                        html += `<div class="mb-4">${this.formatInlineElements(this.formatBoldLabels(section, boldLabels))}</div>`;
                    }
                }
            });
            return html;
        }
    },

    /**
     * Format a section that contains bullet points
     */
    formatSectionWithBullets(section, boldLabels = []) {
        const lines = section.split('\n').filter(line => line.trim());
        let html = '';
        let currentBulletList = [];
        let currentParagraph = '';
        
        lines.forEach(line => {
            const trimmedLine = line.trim();
            
            // Check if this line contains a bullet point pattern
            if (trimmedLine.match(/^[-•*]\s+/) || trimmedLine.includes(': - ')) {
                // If we have a current paragraph, add it first
                if (currentParagraph) {
                    html += `<div class="mb-3">${this.formatBoldLabels(currentParagraph, boldLabels)}</div>`;
                    currentParagraph = '';
                }
                
                // If we have accumulated bullets, render them
                if (currentBulletList.length > 0) {
                    html += '<ul class="list-disc list-inside space-y-2 my-4 ml-4">';
                    currentBulletList.forEach(bullet => {
                        html += `<li class="leading-relaxed text-gray-700">${this.formatBoldLabels(bullet, boldLabels)}</li>`;
                    });
                    html += '</ul>';
                    currentBulletList = [];
                }
                
                // Extract the bullet content
                let bulletContent = '';
                if (trimmedLine.includes(': - ')) {
                    // Handle "Label: - content" format
                    const parts = trimmedLine.split(': - ');
                    if (parts.length >= 2) {
                        const label = parts[0];
                        const content = parts.slice(1).join(': - ');
                        bulletContent = `<strong class="font-semibold text-gray-900">${label}:</strong> ${content}`;
                    }
                } else {
                    // Handle standard "- content" format
                    bulletContent = trimmedLine.replace(/^[-•*]\s+/, '');
                }
                
                currentBulletList.push(bulletContent);
            } else {
                // This is a regular line
                if (currentBulletList.length > 0) {
                    // We're in the middle of bullet points, add to the last bullet
                    if (currentBulletList.length > 0) {
                        currentBulletList[currentBulletList.length - 1] += ' ' + trimmedLine;
                    }
                } else {
                    // Add to current paragraph
                    currentParagraph += (currentParagraph ? ' ' : '') + trimmedLine;
                }
            }
        });
        
        // Handle any remaining content
        if (currentParagraph) {
            html += `<div class="mb-3">${this.formatBoldLabels(currentParagraph, boldLabels)}</div>`;
        }
        
        if (currentBulletList.length > 0) {
            html += '<ul class="list-disc list-inside space-y-2 my-4 ml-4">';
            currentBulletList.forEach(bullet => {
                html += `<li class="leading-relaxed text-gray-700">${this.formatBoldLabels(bullet, boldLabels)}</li>`;
            });
            html += '</ul>';
        }
        
        return html || `<div class="mb-4">${this.formatBoldLabels(section, boldLabels)}</div>`;
    },

    /**
     * Format structured sections with headers and content
     */
    formatStructuredSection(section, boldLabels = []) {
        const lines = section.split('\n').filter(line => line.trim());
        let html = '';
        let currentHeader = '';
        let currentContent = '';
        
        lines.forEach((line, index) => {
            const trimmedLine = line.trim();
            
            // Check if this line looks like a header
            const isHeader = 
                trimmedLine.match(/^[A-Z][^.]*\([^)]*\)/) || // "Title (timeframe)"
                trimmedLine.match(/^[A-Z][^.]*Strategy/) ||   // "Something Strategy"
                trimmedLine.match(/^[A-Z][^.]*Actions/) ||    // "Something Actions"
                trimmedLine.match(/^[A-Z][^.]*Implementation/) || // "Something Implementation"
                (index === 0 && trimmedLine.length > 10 && !trimmedLine.includes('**')); // First long line without markdown
            
            if (isHeader) {
                // Save previous section if it exists
                if (currentHeader && currentContent) {
                    html += this.formatHeaderContentPair(currentHeader, currentContent, boldLabels);
                }
                
                // Start new section
                currentHeader = trimmedLine;
                currentContent = '';
            } else {
                // Add to current content
                currentContent += (currentContent ? ' ' : '') + trimmedLine;
            }
            
            // Handle last section
            if (index === lines.length - 1 && currentHeader && currentContent) {
                html += this.formatHeaderContentPair(currentHeader, currentContent, boldLabels);
            }
        });
        
        // If no headers were found, treat as regular content
        if (!html) {
            html = `<div class="mb-4">${this.formatInlineElements(this.formatBoldLabels(section, boldLabels))}</div>`;
        }
        
        return html;
    },

    /**
     * Format a header-content pair
     */
    formatHeaderContentPair(header, content, boldLabels = []) {
        let html = `
            <div class="mb-6">
                <h4 class="text-lg font-semibold text-gray-800 mb-3">${this.formatInlineElements(header)}</h4>
                <div class="text-gray-700">
        `;
        
        // Check if content has markdown bold patterns that should be treated as sub-headers
        if (content.includes('**') && content.includes(':**')) {
            // Split by bold patterns and process each part
            const parts = content.split(/(\*\*[^*]+\*\*:)/);
            let isExpectingContent = false;
            
            parts.forEach((part, index) => {
                const trimmedPart = part.trim();
                
                if (part.match(/^\*\*[^*]+\*\*:$/)) {
                    // This is a sub-header like **Transition Readiness Assessment:**
                    const subHeader = part.replace(/\*\*/g, '').replace(/:$/, '');
                    html += `<h5 class="font-semibold text-gray-800 mb-2 mt-4">${subHeader}:</h5>`;
                    isExpectingContent = true;
                } else if (trimmedPart && isExpectingContent) {
                    // This is content following a sub-header
                    html += `<p class="text-gray-700 leading-relaxed mb-4">${this.formatInlineElements(this.formatBoldLabels(trimmedPart, boldLabels))}</p>`;
                    isExpectingContent = false;
                } else if (trimmedPart && !part.match(/^\*\*[^*]+\*\*:$/)) {
                    // This is regular content without a preceding sub-header
                    html += `<p class="mb-3 leading-relaxed">${this.formatInlineElements(this.formatBoldLabels(trimmedPart, boldLabels))}</p>`;
                }
            });
        } else {
            // Regular content without sub-headers
            html += `<p class="leading-relaxed">${this.formatInlineElements(this.formatBoldLabels(content, boldLabels))}</p>`;
        }
        
        html += `
                </div>
            </div>
        `;
        
        return html;
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

    formatMarkdownBoldContent(content, isNumbered = false) {
        // Split by bold headers pattern **Header:** to create sections
        const sections = content.split(/(?=\*\*[^*]+:\*\*)/g).filter(section => section.trim());
        
        let html = '<div class="space-y-4">';
        
        sections.forEach((section, index) => {
            html += this.formatMarkdownBoldSection(section, isNumbered ? index + 1 : null);
        });
        
        html += '</div>';
        return html;
    },

    formatMarkdownBoldSection(section, sectionNumber = null) {
        // Extract bold header and content
        const headerMatch = section.match(/^\*\*([^*]+):\*\*\s*([\s\S]*)/);
        
        if (headerMatch) {
            const [, header, content] = headerMatch;
            const cleanContent = content.trim();
            
            return `
                <div class="mb-4">
                    <div class="font-semibold text-gray-800 mb-2">
                        ${sectionNumber ? `${sectionNumber}. ` : ''}${header}:
                    </div>
                    <div class="ml-4 text-gray-700 leading-relaxed">
                        ${this.formatInlineElements(cleanContent)}
                    </div>
                </div>
            `;
        } else {
            // Fallback for sections without proper markdown headers
            return `<div class="mb-4 text-gray-700">${this.formatInlineElements(section)}</div>`;
        }
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
                    <h4 class="text-lg font-semibold text-gray-800 mb-6">References & Supporting Research</h4>
                    <div class="space-y-4">
            `;
            
            // Parse references - look for patterns like "Author (Year)." or similar
            const references = this.parseReferences(referencesContent);
            
            references.forEach((reference, index) => {
                html += `
                    <div class="flex items-start">
                        <span class="font-medium text-gray-700 mr-3 mt-0.5 flex-shrink-0">${index + 1}.</span>
                        <span class="text-sm text-gray-600 italic leading-relaxed">${this.formatInlineElements(reference.trim())}</span>
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
        const references = [];
        
        // First, try to split by numbered patterns (1., 2., 3., etc.)
        // This handles cases where references are already numbered
        const numberedPattern = /(\d+)\.\s*([^0-9]+?)(?=\d+\.\s*|$)/g;
        let numberedMatches = [...referencesText.matchAll(numberedPattern)];
        
        if (numberedMatches.length > 1) {
            return numberedMatches.map(match => match[2].trim().replace(/\.$/, '') + '.');
        }
        
        // Try to split by author-year pattern: "Author (Year). Title"
        // Look for patterns like "Bersin, J. (2022). The ROI of Internal Talent Development."
        const authorYearSplitPattern = /(?<=\.)\s+(?=[A-Z][a-z]+[^.]*\([12]\d{3}\))/;
        const authorYearSplit = referencesText.split(authorYearSplitPattern);
        
        if (authorYearSplit.length > 1) {
            return authorYearSplit
                .map(ref => ref.trim())
                .filter(ref => ref.length > 10)
                .map(ref => ref.endsWith('.') ? ref : ref + '.');
        }
        
        // Try to split by sentence boundaries followed by capital letters
        // This handles cases where each reference is a complete sentence
        const sentenceSplitPattern = /(?<=\.)\s+(?=[A-Z])/;
        const sentences = referencesText.split(sentenceSplitPattern);
        
        if (sentences.length > 1) {
            // Group sentences that belong together (same author/topic)
            let currentRef = '';
            
            sentences.forEach((sentence, index) => {
                sentence = sentence.trim();
                if (!sentence) return;
                
                // Ensure sentence ends with period
                if (!sentence.endsWith('.')) {
                    sentence += '.';
                }
                
                // Check if this looks like the start of a new reference
                const looksLikeNewRef = 
                    sentence.match(/^[A-Z][a-z]+[^.]*\([12]\d{3}\)/) || // Author (Year)
                    sentence.match(/^(Lightcast|McKinsey|LinkedIn|Gallup|Additional)/) || // Known sources
                    sentence.match(/^[A-Z][a-z]+\s+[A-Z]/) || // "Author Name"
                    index === 0; // First sentence
                
                if (looksLikeNewRef && currentRef) {
                    // Save the previous reference and start a new one
                    references.push(currentRef.trim());
                    currentRef = sentence;
                } else {
                    // Continue building the current reference
                    currentRef += (currentRef ? ' ' : '') + sentence;
                }
                
                // If this is the last sentence, save current reference
                if (index === sentences.length - 1 && currentRef) {
                    references.push(currentRef.trim());
                }
            });
            
            if (references.length > 1) {
                return references;
            }
        }
        
        // Fallback: Try to split by known research organization names
        const orgSplitPattern = /(?<=\.)\s+(?=(Lightcast|McKinsey|LinkedIn|Gallup|Bersin|Additional|HSBC|Amazon|ING|Unilever))/;
        const orgSplit = referencesText.split(orgSplitPattern);
        
        if (orgSplit.length > 1) {
            return orgSplit
                .map(ref => ref.trim())
                .filter(ref => ref.length > 10)
                .map(ref => ref.endsWith('.') ? ref : ref + '.');
        }
        
        // Final fallback: Split by double spaces or line breaks
        const basicSplit = referencesText.split(/\s{2,}|\n+/);
        if (basicSplit.length > 1) {
            return basicSplit
                .map(ref => ref.trim())
                .filter(ref => ref.length > 10)
                .map(ref => ref.endsWith('.') ? ref : ref + '.');
        }
        
        // If all else fails, return the entire text as one reference
        return [referencesText.trim()];
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
     * Format markdown-style table with proper styling and expandable skills
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
        
        // Check if this is a skills table (has "All Skills" column)
        const isSkillsTable = headers.some(header => header.toLowerCase().includes('all skills') || header.toLowerCase().includes('skills'));
        const skillsColumnIndex = headers.findIndex(header => header.toLowerCase().includes('all skills') || header.toLowerCase().includes('skills'));
        
        let html = `
            <div class="my-4 w-full">
                <table class="w-full bg-white border border-gray-300 rounded-lg shadow-sm table-fixed">
                    <thead class="bg-gray-50">
                        <tr>
        `;
        
        headers.forEach((header, index) => {
            // Set column widths for better layout
            let widthClass = '';
            if (isSkillsTable) {
                if (index === 0) widthClass = 'w-1/5'; // Skill Type
                else if (index === 1) widthClass = 'w-1/6'; // Skill Count
                else if (index === skillsColumnIndex) widthClass = 'w-3/5'; // All Skills (widest)
                else widthClass = 'w-1/5'; // Default
            }
            
            html += `<th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200 ${widthClass}">${header}</th>`;
        });
        
        html += `</tr></thead><tbody class="bg-white divide-y divide-gray-200">`;
        
        dataRows.forEach((row, index) => {
            const rowClass = index % 2 === 0 ? 'bg-white' : 'bg-gray-50';
            html += `<tr class="${rowClass} hover:bg-blue-50">`;
            
            row.forEach((cell, cellIndex) => {
                const cellClass = cellIndex === 0 ? 'font-medium text-gray-900' : 'text-gray-700';
                let cellContent = cell || '-';
                
                // Apply expandable skills formatting to the skills column
                if (isSkillsTable && cellIndex === skillsColumnIndex && cellContent !== '-') {
                    cellContent = this.formatSkillsWithExpandable(cellContent, 3);
                }
                
                // Use proper text wrapping classes and remove whitespace-nowrap
                html += `<td class="px-4 py-3 text-sm ${cellClass} align-top break-words">${cellContent}</td>`;
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
        
        const lines = content.split('\n').filter(line => {
            const trimmed = line.trim();
            // Filter out empty lines
            if (!trimmed) return false;
            
            // Filter out table separator lines (like ---------|---------|-------)
            if (trimmed.match(/^[\-\|\s]+$/)) return false;
            
            // Filter out markdown table headers that don't start with bullet points
            if (trimmed.includes('|') && trimmed.split('|').length > 2 && 
                !trimmed.startsWith('-') && !trimmed.startsWith('•') && 
                !trimmed.toLowerCase().includes('division') && 
                !trimmed.toLowerCase().includes('business')) {
                return false;
            }
            
            return true;
        });
        
        let html = '<ul class="space-y-3">';
        
        lines.forEach(line => {
            const trimmedLine = line.trim();
            
            // Handle explicit bullet points
            if (trimmedLine.startsWith('-') || trimmedLine.startsWith('•')) {
                const cleanLine = trimmedLine.replace(/^[-•]\s*/, '').trim();
                html += `<li class="flex items-start">
                    <span class="w-2 h-2 bg-purple-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                    <span class="text-sm text-gray-700 leading-relaxed">${cleanLine}</span>
                </li>`;
            } 
            // Handle table-like content with pipes (divisional deployment)
            else if (trimmedLine.includes('|') && trimmedLine.split('|').length >= 3) {
                // Parse as table row for divisional deployment
                const cells = trimmedLine.split('|').map(cell => cell.trim()).filter(cell => cell);
                if (cells.length >= 2) {
                    // Format as structured bullet point
                    const division = cells[0];
                    const positions = cells[1];
                    const businessUnit = cells.length > 2 ? cells[2] : '';
                    
                    let displayText = `${division} | ${positions}`;
                    if (businessUnit) {
                        displayText += ` | ${businessUnit}`;
                    }
                    
                    html += `<li class="flex items-start">
                        <span class="w-2 h-2 bg-purple-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                        <span class="text-sm text-gray-700 leading-relaxed">${displayText}</span>
                    </li>`;
                }
            }
            // Handle regular content lines as bullet points
            else if (trimmedLine) {
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
     * Format inline elements (bold, emphasis, markdown, etc.)
     */
    formatInlineElements(text) {
        if (!text) return '';
        
        // Handle markdown bold formatting (**text**)
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
        
        // Handle markdown italic formatting (*text*)
        text = text.replace(/\*([^*]+)\*/g, '<em class="italic">$1</em>');
        
        // Handle percentages
        text = text.replace(/(\d+\.?\d*)%/g, '<span class="font-semibold text-blue-600">$1%</span>');
        
        // Handle job transitions (arrow notation)
        text = text.replace(/Group\s+(\d+)\s+→\s+Group\s+(\d+)/g, '<span class="font-semibold text-purple-600">Group $1 → Group $2</span>');
        
        // Handle costs/savings
        text = text.replace(/\$(\d+[KM]?\+?)/g, '<span class="font-semibold text-green-600">$$$1</span>');
        text = text.replace(/£(\d+[KM]?\+?)/g, '<span class="font-semibold text-green-600">£$1</span>');
        
        // Handle time periods (months, weeks, days)
        text = text.replace(/(\d+\+?)\s*(months?|weeks?|days?)/gi, '<span class="font-medium text-orange-600">$1 $2</span>');
        
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
        console.log('📥 Downloading document:', filename);
        
        try {
            // Create download URL - the document should be available at this path
            const downloadUrl = `/api/download/${filename}`;
            
            // Create a temporary anchor element and trigger download
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = filename;
            a.style.display = 'none';
            
            // Append to body, click, and remove
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            console.log('✅ Download initiated for:', filename);
            this.showAlert('Document download started. Check your downloads folder.', 'success');
            
        } catch (error) {
            console.error('❌ Download error:', error);
            this.showAlert('Failed to download document: ' + error.message, 'danger');
        }
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
            console.log('🔍 API Response status:', response.status, response.statusText);
            
            const data = await response.json();
            console.log('🔍 API Response data:', data);
            
            if (data.jobs && data.jobs.length > 0) {
                this.populateJobDropdowns(data.jobs);
                console.log(`✅ Loaded ${data.jobs.length} job options`);
            } else {
                console.warn('⚠️ No jobs data received from API. Response:', data);
                console.warn('⚠️ data.success:', data.success);
                console.warn('⚠️ data.jobs length:', data.jobs ? data.jobs.length : 'undefined');
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

    /**
     * Render V2 Analytics Sections (Legacy - now integrated within sections)
     */
    renderV2AnalyticsSections(data) {
        // Legacy method - V2 analytics are now integrated within sections
        return '';
    },

    /**
     * Render section-specific V2 Analytics
     */
    renderSectionSpecificV2Analytics(sectionKey, data) {
        if (!data.v2_analytics) {
            return '';
        }

        let html = '';
        
        if (sectionKey === 'current_role_context' && data.v2_analytics.current_role_context) {
            html += '<div class="mt-8 space-y-6">';
            
            const contextV2 = data.v2_analytics.current_role_context;
            
            // Defining Skills Analysis
            if (contextV2.defining_skills) {
                html += this.renderDefiningSkillsSection(contextV2.defining_skills);
            }
            
            // Job Family Context
            if (contextV2.job_family_context) {
                html += this.renderJobFamilySection(contextV2.job_family_context);
            }
            
            // Skills Rarity Analysis
            if (contextV2.skills_rarity) {
                html += this.renderSkillsRaritySection(contextV2.skills_rarity);
            }
            
            html += '</div>';
        }
        
        if (sectionKey === 'pathways' && data.v2_analytics.pathway_analysis) {
            // Note: Dual Similarity Analysis is now integrated into individual pathway opportunities
            // rather than being a separate section for cleaner UX without duplication
            return '';
        }
        
        return html;
    },

    /**
     * Render Defining Skills Section
     */
    renderDefiningSkillsSection(definingSkills) {
        return `
            <div id="v2-defining-skills" class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-6">
                <div class="flex items-center mb-4">
                    <div class="flex items-center justify-center w-10 h-10 bg-blue-600 text-white rounded-lg mr-3">
                        <i class="fas fa-star"></i>
                    </div>
                    <div>
                        <h3 class="text-lg font-epilogue font-semibold text-gray-900">Defining Skills Analysis</h3>
                        <p class="text-sm font-source text-gray-600">Core competencies that distinguish these roles</p>
                    </div>
                    <span class="ml-auto inline-flex items-center px-3 py-1 rounded-full text-xs font-source font-medium bg-blue-100 text-blue-800">
                        <i class="fas fa-database mr-1"></i>
                        V2 Enhanced
                    </span>
                </div>
                
                <div class="space-y-4">
                    ${this.formatDefiningSkillsContent(definingSkills)}
                </div>
            </div>
        `;
    },

    /**
     * Render Job Family Section
     */
    renderJobFamilySection(jobFamily) {
        return `
            <div id="v2-job-family" class="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200 p-6">
                <div class="flex items-center mb-4">
                    <div class="flex items-center justify-center w-10 h-10 bg-purple-600 text-white rounded-lg mr-3">
                        <i class="fas fa-sitemap"></i>
                    </div>
                    <div>
                        <h3 class="text-lg font-epilogue font-semibold text-gray-900">Job Family Context</h3>
                        <p class="text-sm font-source text-gray-600">Clustering insights and related roles</p>
                    </div>
                    <span class="ml-auto inline-flex items-center px-3 py-1 rounded-full text-xs font-source font-medium bg-purple-100 text-purple-800">
                        <i class="fas fa-database mr-1"></i>
                        V2 Enhanced
                    </span>
                </div>
                
                <div class="space-y-4">
                    ${this.formatJobFamilyContent(jobFamily)}
                </div>
            </div>
        `;
    },

    /**
     * Render Movement Patterns Section
     */
    renderMovementPatternsSection(movementPatterns) {
        return `
            <div id="v2-movement-patterns" class="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200 p-6">
                <div class="flex items-center mb-4">
                    <div class="flex items-center justify-center w-10 h-10 bg-green-600 text-white rounded-lg mr-3">
                        <i class="fas fa-route"></i>
                    </div>
                    <div>
                        <h3 class="text-lg font-epilogue font-semibold text-gray-900">Movement Patterns</h3>
                        <p class="text-sm font-source text-gray-600">Career transition trends and pathways</p>
                    </div>
                    <span class="ml-auto inline-flex items-center px-3 py-1 rounded-full text-xs font-source font-medium bg-green-100 text-green-800">
                        <i class="fas fa-database mr-1"></i>
                        V2 Enhanced
                    </span>
                </div>
                
                <div class="space-y-4">
                    ${this.formatMovementPatternsContent(movementPatterns)}
                </div>
            </div>
        `;
    },

    /**
     * Render Skills Rarity Section
     */
    renderSkillsRaritySection(skillsRarity) {
        return `
            <div id="v2-skills-rarity" class="bg-gradient-to-r from-amber-50 to-yellow-50 rounded-lg border border-amber-200 p-6">
                <div class="flex items-center mb-4">
                    <div class="flex items-center justify-center w-10 h-10 bg-amber-600 text-white rounded-lg mr-3">
                        <i class="fas fa-gem"></i>
                    </div>
                    <div>
                        <h3 class="text-lg font-epilogue font-semibold text-gray-900">Skills Rarity Analysis</h3>
                        <p class="text-sm font-source text-gray-600">Market scarcity and competitive advantage</p>
                    </div>
                    <span class="ml-auto inline-flex items-center px-3 py-1 rounded-full text-xs font-source font-medium bg-amber-100 text-amber-800">
                        <i class="fas fa-database mr-1"></i>
                        V2 Enhanced
                    </span>
                </div>
                
                <div class="space-y-4">
                    ${this.formatSkillsRarityContent(skillsRarity)}
                </div>
            </div>
        `;
    },

    /**
     * Render Transition Insights Section
     */
    renderTransitionInsightsSection(transitionInsights) {
        return `
            <div id="v2-transition-insights" class="bg-gradient-to-r from-red-50 to-rose-50 rounded-lg border border-red-200 p-6">
                <div class="flex items-center mb-4">
                    <div class="flex items-center justify-center w-10 h-10 bg-red-600 text-white rounded-lg mr-3">
                        <i class="fas fa-lightbulb"></i>
                    </div>
                    <div>
                        <h3 class="text-lg font-epilogue font-semibold text-gray-900">Strategic Transition Insights</h3>
                        <p class="text-sm font-source text-gray-600">Actionable intelligence for career moves</p>
                    </div>
                    <span class="ml-auto inline-flex items-center px-3 py-1 rounded-full text-xs font-source font-medium bg-red-100 text-red-800">
                        <i class="fas fa-database mr-1"></i>
                        V2 Enhanced
                    </span>
                </div>
                
                <div class="space-y-4">
                    ${this.formatTransitionInsightsContent(transitionInsights)}
                </div>
            </div>
        `;
    },

    /**
     * Render Dual Similarity Analysis Section
     */
    renderDualSimilaritySection(data) {
        if (!data || data.error) {
            return `
                <div id="v2-dual-similarity" class="bg-red-50 border border-red-200 rounded-lg p-6">
                    <div class="flex items-center mb-4">
                        <div class="flex items-center justify-center w-10 h-10 bg-red-600 text-white rounded-lg mr-3">
                            <i class="fas fa-balance-scale"></i>
                        </div>
                        <div>
                            <h3 class="text-lg font-epilogue font-semibold text-gray-900">Dual Similarity Analysis</h3>
                            <p class="text-sm font-source text-gray-600">Basic vs Enhanced Similarity Comparison</p>
                        </div>
                        <span class="ml-auto inline-flex items-center px-3 py-1 rounded-full text-xs font-source font-medium bg-red-100 text-red-800">
                            <i class="fas fa-exclamation-triangle mr-1"></i>
                            Error
                        </span>
                    </div>
                    <p class="text-red-600">${data?.error || 'Unable to load dual similarity analysis'}</p>
                </div>
            `;
        }

        let html = `
            <div id="v2-dual-similarity" class="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-6">
                <div class="flex items-center mb-4">
                    <div class="flex items-center justify-center w-10 h-10 bg-purple-600 text-white rounded-lg mr-3">
                        <i class="fas fa-balance-scale"></i>
                    </div>
                    <div>
                        <h3 class="text-lg font-epilogue font-semibold text-gray-900">Dual Similarity Analysis</h3>
                        <p class="text-sm font-source text-gray-600">Basic vs Enhanced Similarity Comparison</p>
                    </div>
                    <span class="ml-auto inline-flex items-center px-3 py-1 rounded-full text-xs font-source font-medium bg-purple-100 text-purple-800">
                        <i class="fas fa-database mr-1"></i>
                        V2 Enhanced
                    </span>
                </div>
                
                <div class="mb-4 p-4 bg-white rounded-lg border border-purple-200">
                    <p class="text-sm text-gray-700">
                        <strong>Basic Similarity:</strong> Standard skill overlap percentage (Jaccard similarity)<br>
                        <strong>Enhanced Similarity:</strong> Weighted by defining skills and rarity scores for strategic value
                    </p>
                </div>
        `;

        // Handle different analysis types
        if (data.type === 'specific_transitions' && data.comparisons) {
            html += this.formatSpecificTransitionComparisons(data.comparisons, data.summary);
        } else if (data.type === 'top_pathways' && data.pathways) {
            html += this.formatPathwayComparisons(data.pathways, data.insights);
        } else {
            html += '<p class="text-gray-600 p-4 bg-white rounded-lg">No similarity comparison data available.</p>';
        }

        html += '</div>';
        return html;
    },

    /**
     * Format specific transition comparisons
     */
    formatSpecificTransitionComparisons(comparisons, summary) {
        let html = '<div class="space-y-4">';
        
        if (summary) {
            html += `
                <div class="bg-white p-4 rounded-lg border border-purple-200">
                    <h5 class="font-semibold text-purple-800 mb-3">Analysis Summary</h5>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div class="text-center p-2 bg-blue-50 rounded">
                            <div class="text-lg font-bold text-blue-600">${summary.total_transitions || 0}</div>
                            <div class="text-xs text-gray-600">Transitions</div>
                        </div>
                        <div class="text-center p-2 bg-green-50 rounded">
                            <div class="text-lg font-bold text-green-600">${summary.high_strategic_count || 0}</div>
                            <div class="text-xs text-gray-600">High Strategic</div>
                        </div>
                        <div class="text-center p-2 bg-purple-50 rounded">
                            <div class="text-lg font-bold text-purple-600">${summary.average_basic_similarity || 0}%</div>
                            <div class="text-xs text-gray-600">Avg Basic</div>
                        </div>
                        <div class="text-center p-2 bg-indigo-50 rounded">
                            <div class="text-lg font-bold text-indigo-600">${summary.average_enhanced_similarity || 0}%</div>
                            <div class="text-xs text-gray-600">Avg Enhanced</div>
                        </div>
                    </div>
                    ${summary.recommendation ? `<p class="mt-3 text-sm text-gray-700 italic bg-gray-50 p-3 rounded">${summary.recommendation}</p>` : ''}
                </div>
            `;
        }

        // Individual comparisons
        comparisons.forEach(comp => {
            const differenceColor = comp.similarity_difference > 0 ? 'text-green-600' : comp.similarity_difference < 0 ? 'text-red-600' : 'text-gray-600';
            const strategicColor = this.getStrategicValueColor(comp.strategic_value);
            
            html += `
                <div class="bg-white p-4 rounded-lg border border-gray-200">
                    <div class="flex justify-between items-start mb-3">
                        <div>
                            <h6 class="font-medium text-gray-900">${comp.job_title}</h6>
                            <p class="text-sm text-gray-600">${comp.job_function} • ${comp.management_level}</p>
                        </div>
                        <span class="px-2 py-1 text-xs rounded-full ${strategicColor}">${comp.strategic_value}</span>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4 mb-3">
                        <div class="text-center p-3 bg-blue-50 rounded">
                            <div class="text-lg font-bold text-blue-600">${comp.basic_similarity}%</div>
                            <div class="text-xs text-gray-600">Basic Similarity</div>
                        </div>
                        <div class="text-center p-3 bg-indigo-50 rounded">
                            <div class="text-lg font-bold text-indigo-600">${comp.enhanced_similarity}%</div>
                            <div class="text-xs text-gray-600">Enhanced Similarity</div>
                        </div>
                    </div>
                    
                    <div class="text-sm space-y-1 bg-gray-50 p-3 rounded">
                        <div class="flex justify-between">
                            <span class="text-gray-600">Score Difference:</span>
                            <span class="${differenceColor} font-medium">${comp.similarity_difference > 0 ? '+' : ''}${comp.similarity_difference}%</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Defining Skills:</span>
                            <span class="font-medium">${comp.shared_defining_skills || 0}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Rarity Score:</span>
                            <span class="font-medium">${comp.rarity_weighted_score || 0}%</span>
                        </div>
                    </div>
                    
                    <p class="text-xs text-gray-600 mt-2 italic bg-blue-50 p-2 rounded">${comp.interpretation}</p>
                </div>
            `;
        });

        html += '</div>';
        return html;
    },

    /**
     * Format pathway comparisons
     */
    formatPathwayComparisons(pathways, insights) {
        let html = '<div class="space-y-4">';
        
        if (insights && insights.length > 0) {
            html += `
                <div class="bg-white p-4 rounded-lg border border-purple-200">
                    <h5 class="font-semibold text-purple-800 mb-2">Key Insights</h5>
                    <ul class="text-sm text-gray-700 space-y-1">
                        ${insights.map(insight => `<li class="flex items-start"><i class="fas fa-arrow-right text-purple-500 mt-1 mr-2 text-xs"></i>${insight}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // Get ranking information from first pathway if available
        const rankingInfo = pathways.length > 0 ? pathways[0] : {};
        const rankingDescription = rankingInfo.ranking_description || "Ranked by Enhanced Skill Matching";
        const primaryAlgorithm = rankingInfo.primary_algorithm || 'enhanced';
        
        // Top pathways comparison
        html += '<div class="bg-white rounded-lg border border-gray-200 overflow-hidden">';
        html += `
            <div class="bg-gray-50 px-4 py-3 border-b">
                <h5 class="font-semibold text-gray-800">Career Pathways Similarity Comparison</h5>
                <p class="text-sm text-gray-600">${rankingDescription}</p>
                <p class="text-xs text-gray-500 mt-1">Both scores shown for transparency • Primary algorithm emphasized</p>
            </div>
            <div class="divide-y divide-gray-200">
        `;

        pathways.slice(0, 8).forEach((pathway, index) => {
            const differenceColor = pathway.similarity_difference > 0 ? 'text-green-600' : pathway.similarity_difference < 0 ? 'text-red-600' : 'text-gray-600';
            const strategicColor = this.getStrategicValueColor(pathway.strategic_value);
            
            html += `
                <div class="p-4 hover:bg-gray-50">
                    <div class="flex justify-between items-start mb-2">
                        <div class="flex-1">
                            <h6 class="font-medium text-gray-900 text-sm">${index + 1}. ${pathway.job_title}</h6>
                            <p class="text-xs text-gray-600">${pathway.job_function} • ${pathway.management_level}</p>
                        </div>
                        <span class="px-2 py-1 text-xs rounded-full ${strategicColor} ml-2">${pathway.strategic_value}</span>
                    </div>
                    
                    <div class="flex items-center justify-between mb-2">
                        ${this.renderDualScoreDisplay(pathway, primaryAlgorithm)}
                    </div>
                    
                    <p class="text-xs text-gray-600 mt-2 italic">${pathway.interpretation}</p>
                </div>
            `;
        });

        html += '</div></div></div>';
        return html;
    },

    /**
     * Get strategic value color classes
     */
    getStrategicValueColor(value) {
        switch(value) {
            case 'High Strategic Value':
                return 'bg-green-100 text-green-800';
            case 'Medium Strategic Value':
                return 'bg-yellow-100 text-yellow-800';
            case 'Emerging Opportunity':
                return 'bg-blue-100 text-blue-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    },

    /**
     * Render dual similarity score display with visual hierarchy
     */
    renderDualScoreDisplay(pathway, primaryAlgorithm) {
        const isEnhancedPrimary = primaryAlgorithm === 'enhanced';
        
        // Determine primary and secondary scores
        const primaryScore = isEnhancedPrimary ? pathway.enhanced_similarity : pathway.basic_similarity;
        const secondaryScore = isEnhancedPrimary ? pathway.basic_similarity : pathway.enhanced_similarity;
        
        // Icons and styling
        const primaryIcon = isEnhancedPrimary ? '🎯' : '📊';
        const secondaryIcon = isEnhancedPrimary ? '📊' : '🎯';
        const primaryLabel = isEnhancedPrimary ? 'Enhanced' : 'Literal';
        const secondaryLabel = isEnhancedPrimary ? 'Literal' : 'Enhanced';
        
        return `
            <div class="flex items-center space-x-4 text-sm">
                <div class="flex items-center space-x-2 px-3 py-2 bg-purple-100 border-2 border-purple-300 rounded-lg">
                    <span class="text-lg">${primaryIcon}</span>
                    <div class="text-center">
                        <div class="font-bold text-lg text-purple-800">${primaryScore}%</div>
                        <div class="text-xs text-purple-600 font-medium uppercase">${primaryLabel} (PRIMARY)</div>
                    </div>
                </div>
                
                <div class="text-gray-400 font-bold">|</div>
                
                <div class="flex items-center space-x-2 px-3 py-2 bg-gray-100 border border-gray-300 rounded-lg">
                    <span class="text-sm">${secondaryIcon}</span>
                    <div class="text-center">
                        <div class="font-semibold text-gray-700">${secondaryScore}%</div>
                        <div class="text-xs text-gray-500">${secondaryLabel}</div>
                    </div>
                </div>
                
                <div class="text-xs text-gray-500 italic">
                    ${pathway.similarity_difference > 0 ? '+' : ''}${pathway.similarity_difference}% difference
                </div>
            </div>
        `;
    },

    /**
     * Format Defining Skills Content
     */
    formatDefiningSkillsContent(definingSkills) {
        if (!definingSkills || !definingSkills.skills) {
            return '<p class="text-gray-500">No defining skills data available</p>';
        }

        let html = '<div class="grid grid-cols-1 md:grid-cols-2 gap-4">';
        
        definingSkills.skills.forEach(skill => {
            html += `
                <div class="bg-white rounded-lg p-4 border border-gray-200">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-semibold text-gray-900">${skill.name}</h4>
                        <span class="text-sm text-blue-600 font-medium">${skill.rarity_score}% rare</span>
                    </div>
                    <p class="text-sm text-gray-600 mb-2">${skill.description || 'Core competency for role differentiation'}</p>
                    <div class="flex items-center text-xs text-gray-500">
                        <i class="fas fa-chart-bar mr-1"></i>
                        <span>Market demand: ${skill.demand_level || 'High'}</span>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    },

    /**
     * Format Job Family Content
     */
    formatJobFamilyContent(jobFamily) {
        if (!jobFamily) {
            return '<p class="text-gray-500">No job family data available</p>';
        }

        return `
            <div class="bg-white rounded-lg p-4 border border-gray-200">
                <h4 class="font-semibold text-gray-900 mb-2">Family: ${jobFamily.family_name || 'Professional Services'}</h4>
                <p class="text-sm text-gray-600 mb-3">${jobFamily.description || 'Related roles with similar skill requirements and career progression patterns.'}</p>
                
                <div class="space-y-2">
                    <div class="flex items-center text-sm">
                        <i class="fas fa-users text-purple-600 mr-2"></i>
                        <span class="font-medium">Family Size:</span>
                        <span class="ml-1">${jobFamily.family_size || '12'} related roles</span>
                    </div>
                    <div class="flex items-center text-sm">
                        <i class="fas fa-chart-line text-purple-600 mr-2"></i>
                        <span class="font-medium">Avg Similarity:</span>
                        <span class="ml-1">${jobFamily.avg_similarity || '78'}%</span>
                    </div>
                    <div class="flex items-center text-sm">
                        <i class="fas fa-exchange-alt text-purple-600 mr-2"></i>
                        <span class="font-medium">Transition Rate:</span>
                        <span class="ml-1">${jobFamily.transition_rate || '23'}% annually</span>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Format Movement Patterns Content
     */
    formatMovementPatternsContent(movementPatterns) {
        if (!movementPatterns || !movementPatterns.patterns) {
            return '<p class="text-gray-500">No movement patterns data available</p>';
        }

        let html = '<div class="space-y-4">';
        
        movementPatterns.patterns.forEach((pattern, index) => {
            html += `
                <div class="bg-white rounded-lg p-4 border border-gray-200">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-semibold text-gray-900">${pattern.pattern_name}</h4>
                        <span class="text-sm text-green-600 font-medium">${pattern.frequency}% of transitions</span>
                    </div>
                    <p class="text-sm text-gray-600 mb-2">${pattern.description}</p>
                    <div class="flex items-center text-xs text-gray-500">
                        <i class="fas fa-clock mr-1"></i>
                        <span>Avg timeframe: ${pattern.avg_timeframe || '18 months'}</span>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    },

    /**
     * Format Skills Rarity Content
     */
    formatSkillsRarityContent(skillsRarity) {
        if (!skillsRarity || !skillsRarity.rare_skills) {
            return '<p class="text-gray-500">No skills rarity data available</p>';
        }

        let html = '<div class="grid grid-cols-1 md:grid-cols-3 gap-4">';
        
        skillsRarity.rare_skills.forEach(skill => {
            const rarityLevel = skill.rarity_score >= 90 ? 'Extremely Rare' : 
                               skill.rarity_score >= 70 ? 'Very Rare' : 
                               skill.rarity_score >= 50 ? 'Moderately Rare' : 'Common';
            
            const rarityColor = skill.rarity_score >= 90 ? 'text-red-600' : 
                               skill.rarity_score >= 70 ? 'text-orange-600' : 
                               skill.rarity_score >= 50 ? 'text-yellow-600' : 'text-green-600';
                               
            html += `
                <div class="bg-white rounded-lg p-4 border border-gray-200">
                    <h4 class="font-semibold text-gray-900 mb-1">${skill.name}</h4>
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm ${rarityColor} font-medium">${rarityLevel}</span>
                        <span class="text-sm text-gray-500">${skill.rarity_score}%</span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-2 mb-2">
                        <div class="bg-amber-600 h-2 rounded-full" style="width: ${skill.rarity_score}%"></div>
                    </div>
                    <p class="text-xs text-gray-500">Market advantage potential</p>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    },

    /**
     * Format Transition Insights Content
     */
    formatTransitionInsightsContent(transitionInsights) {
        if (!transitionInsights || !transitionInsights.insights) {
            return '<p class="text-gray-500">No transition insights available</p>';
        }

        let html = '<div class="space-y-4">';
        
        transitionInsights.insights.forEach(insight => {
            const priorityColor = insight.priority === 'high' ? 'text-red-600' : 
                                 insight.priority === 'medium' ? 'text-yellow-600' : 'text-green-600';
            
            html += `
                <div class="bg-white rounded-lg p-4 border border-gray-200">
                    <div class="flex items-start justify-between mb-2">
                        <h4 class="font-semibold text-gray-900">${insight.title}</h4>
                        <span class="text-sm ${priorityColor} font-medium capitalize">${insight.priority} Priority</span>
                    </div>
                    <p class="text-sm text-gray-600 mb-3">${insight.description}</p>
                    <div class="bg-gray-50 rounded-lg p-3">
                        <p class="text-sm font-medium text-gray-900 mb-1">Recommended Action:</p>
                        <p class="text-sm text-gray-700">${insight.recommendation}</p>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    },

    // Setup target job selector with multi-target support
    setupTargetJobSelector() {
        this.targetJobSelector = {
            selectedJobs: [],
            maxJobs: 999, // Effectively unlimited for comparison analysis
            
            addJob(jobId, displayName) {
                if (this.selectedJobs.find(job => job.id === jobId)) {
                    SkillEngine.CareerAnalysis.showValidationMessage('Job already selected', 'error');
                    return;
                }
                
                // Removed maxJobs limit check - now supports unlimited comparisons
                
                this.selectedJobs.push({ id: jobId, name: displayName });
                this.updateUI();
                SkillEngine.CareerAnalysis.validateForm();
                
                console.log('🔍 Target job added via CareerAnalysis module:', jobId, displayName);
            },
            
            removeJob(jobId) {
                this.selectedJobs = this.selectedJobs.filter(job => job.id !== jobId);
                this.updateUI();
                SkillEngine.CareerAnalysis.validateForm();
                
                console.log('🔍 Target job removed via CareerAnalysis module:', jobId);
            },
            
            updateUI() {
                const chipsContainer = document.getElementById('selectedTargets');
                const hiddenInput = document.getElementById('jobTo');
                const searchInput = document.getElementById('jobToSearch');
                
                if (chipsContainer) {
                    chipsContainer.innerHTML = this.selectedJobs.map(job => `
                        <div class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            <span class="mr-2">${job.name}</span>
                            <button type="button" class="inline-flex items-center justify-center w-4 h-4 ml-1 text-red-600 hover:text-red-800 hover:bg-red-200 rounded-full" onclick="SkillEngine.CareerAnalysis.targetJobSelector.removeJob('${job.id}')">
                                <i class="fas fa-times text-xs"></i>
                            </button>
                        </div>
                    `).join('');
                }
                
                if (hiddenInput) {
                    hiddenInput.value = this.selectedJobs.map(job => job.id).join(',');
                }
                
                if (searchInput) {
                    searchInput.value = '';
                }
                
                // Update help text based on number of selections
                this.updateHelpText();
            },
            
            updateHelpText() {
                const helpText = this.selectedJobs.length === 0 ? 
                    'Search and select target jobs (supports multiple selection)' :
                    this.selectedJobs.length === 1 ? 
                        'Single job selected - detailed analysis will be generated' :
                        `${this.selectedJobs.length} jobs selected - comparative analysis will be generated`;
                
                const helpElement = document.querySelector('#selectedTargets + .text-xs');
                if (helpElement) {
                    helpElement.innerHTML = `
                        <i class="fas fa-info-circle text-blue-500 mr-1"></i>
                        ${helpText}
                    `;
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
    },

    /**
     * Reset similarity sliders to default values
     */
    resetSimilaritySliders() {
        const minSlider = document.getElementById('similarityMin');
        const maxSlider = document.getElementById('similarityMax');
        
        if (minSlider && maxSlider) {
            minSlider.value = 0;
            maxSlider.value = 95;
            this.updateSimilarityDisplay();
            
            // Show a brief success message
            this.showAlert('Similarity range reset to 0%-95%', 'success');
        }
    },

    /**
     * Expand similarity range to broader settings (0-80%)
     */
    expandSimilarityRange() {
        const minSlider = document.getElementById('similarityMin');
        const maxSlider = document.getElementById('similarityMax');
        
        if (minSlider && maxSlider) {
            minSlider.value = 0;
            maxSlider.value = 80;
            this.updateSimilarityDisplay();
            
            // Show a brief success message
            this.showAlert('Similarity range expanded to 0%-80% for broader results', 'success');
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
