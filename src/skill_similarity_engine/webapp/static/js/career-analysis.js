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
        
        if (!data.success) {
            this.displayError(`Failed to generate preview: ${data.error || 'Unknown error'}`);
            return;
        }

        // Check if we have structured content from all 5 sections
        const content = data.content || {};
        const hasStructuredContent = Object.keys(content).length > 0;
        
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
                                ${data.analysis_mode === 'top_matches' ? 'Top Discovery' : 'Specific Transition'}
                            </span>
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full bg-green-100 text-green-800">
                                <i class="fas fa-check-circle mr-1"></i>
                                ${data.pathway_count} Opportunities
                            </span>
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-800">
                                <i class="fas fa-percentage mr-1"></i>
                                ${Math.round(data.similarity_score * 100)}% Avg Similarity
                            </span>
                            ${hasStructuredContent ? 
                                `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full bg-green-100 text-green-800">
                                    <i class="fas fa-file-alt mr-1"></i>
                                    ${data.section_count || 5} Sections
                                </span>` : ''
                            }
                        </div>
                    </div>
                    <p class="text-gray-600 font-source">
                        Analysis for: <strong>${data.job_title}</strong> | 
                        Range: ${data.similarity_range} | 
                        ${data.tie_breaking_applied ? 'Tie-breaking applied' : 'Default ordering'}
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
                const sectionContent = sectionData.content || '';
                
                html += `
                    <div class="mb-12">
                        <div class="flex items-center mb-6">
                            <div class="flex items-center justify-center w-10 h-10 bg-red-600 text-white rounded-full mr-4">
                                <i class="${section.icon} text-sm"></i>
                            </div>
                            <h2 class="text-2xl font-epilogue font-bold text-gray-900">${title}</h2>
                        </div>
                        <div class="ml-14">
                            ${this.formatSectionContent(sectionContent)}
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
