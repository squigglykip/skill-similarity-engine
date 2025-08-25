/**
 * Job Explorer - Career Pathways Display
 * Handles career pathway visualization and filtering for job explorer
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.CareerPathways = {
    /**
     * Display filtered career pathways based on similarity threshold
     */
    displayFilteredCareerPathways(jobId, similarityThreshold) {
        console.log(`🎯 Displaying filtered career pathways for job: ${jobId}, threshold: ${similarityThreshold}`);
        
        // Only re-filter existing data, don't reload from API (chart stays unchanged)
        this.renderFilteredPathways(similarityThreshold);
    },
    
    /**
     * Get filtered pathways based on threshold and similarity method
     */
    getFilteredPathways(threshold) {
        const state = SkillEngine.JobExplorerController.state;
        if (!state.careerPathways || state.careerPathways.length === 0) {
            return [];
        }
        
        const similarityMethod = document.querySelector('input[name="job-explorer-similarity-method"]:checked')?.value || 'enhanced';
        const scoreField = similarityMethod === 'literal' ? 'similarity_score' : 'enhanced_similarity_score';
        
        return state.careerPathways.filter(pathway => {
            const score = pathway[scoreField] || 0;
            return score >= threshold;
        });
    },

    /**
     * Load career pathways from API with similarity method support
     */
    async loadCareerPathways(jobId) {
        try {
            // Get similarity method for API call
            const similarityMethod = document.querySelector('input[name="job-explorer-similarity-method"]:checked')?.value || 'enhanced';
            
            console.log(`🔍 Loading ALL career pathways for distribution chart with method: ${similarityMethod}`);
            
            // Load ALL pathways for the job (no min_similarity filter, high limit for distribution chart)
            const response = await fetch(`/api/career-pathways-distribution/${jobId}?similarity_method=${similarityMethod}&min_similarity=0&limit=100`);
            
            if (!response.ok) {
                console.error(`❌ HTTP ${response.status}: ${response.statusText}`);
                // Try to get more detailed error info
                try {
                    const errorData = await response.json();
                    console.error('❌ Server error details:', errorData);
                } catch (e) {
                    console.error('❌ Could not parse error response as JSON');
                }
                return;
            }
            
            const data = await response.json();
            
            if (data.error) {
                console.error('❌ API returned error:', data.error);
                return;
            }

            // Store ALL pathways in controller state
            SkillEngine.JobExplorerController.state.careerPathways = Array.isArray(data) ? data : [];
            
            console.log(`✅ Loaded ${SkillEngine.JobExplorerController.state.careerPathways.length} total career pathways for ${similarityMethod} method`);
            

            
            // Get current slider value and calculate filtering threshold
            const similaritySlider = document.getElementById('similarity-slider');
            const sliderValue = similaritySlider ? parseFloat(similaritySlider.value) : 90;
            let sliderThreshold;
            
            if (similarityMethod === 'literal') {
                sliderThreshold = sliderValue / 100;
            } else {
                sliderThreshold = Math.max(0.1, (sliderValue / 100) * 0.2);
            }
            
            // Filter and render the job list based on slider
            this.renderFilteredPathways(sliderThreshold);
            
            // Update strategic intelligence with all data
            SkillEngine.StrategicIntelligence.updateStrategicIntelligence(SkillEngine.JobExplorerController.state.careerPathways);
            
        } catch (error) {
            console.error('Error loading career pathways:', error);
        }
    },

    /**
     * Render filtered pathways based on threshold
     */
    renderFilteredPathways(similarityThreshold) {
        const state = SkillEngine.JobExplorerController.state;
        
        if (!state.careerPathways || state.careerPathways.length === 0) {
            SkillEngine.DOMHelpers.updateElementHTML('similar-jobs-list', `
                <div class="text-center p-6 text-gray-500">
                    <p class="text-sm font-source">No career pathways available</p>
                </div>
            `);
            return;
        }

        // Filter pathways by current similarity threshold and method
        const similarityMethod = document.querySelector('input[name="job-explorer-similarity-method"]:checked')?.value || 'enhanced';
        const scoreField = similarityMethod === 'literal' ? 'similarity_score' : 'enhanced_similarity_score';
        
        const filteredPathways = state.careerPathways.filter(pathway => {
            const score = pathway[scoreField] || 0;
            return score >= similarityThreshold; // Jobs with similarity >= threshold
        });

        const thresholdPercent = Math.round(similarityThreshold * 100);

        console.log(`🎯 Filtered pathways: ${filteredPathways.length}/${state.careerPathways.length} pathways with ${similarityMethod} similarity >= ${thresholdPercent}%`);

        if (filteredPathways.length === 0) {
            SkillEngine.DOMHelpers.updateElementHTML('similar-jobs-list', `
                <div class="text-center p-6 text-gray-500">
                    <p class="text-sm font-source">No pathways found with ≥${thresholdPercent}% similarity</p>
                    <p class="text-xs font-source mt-1">Try lowering the similarity threshold</p>
                </div>
            `);
        } else {
            const html = filteredPathways.slice(0, 5).map(pathway => `
                <div class="similar-job-item flex justify-between items-center p-3 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors cursor-pointer"
                     data-job-id="${pathway.job_id}">
                    <div>
                        <p class="text-sm font-source font-medium text-gray-900">${pathway.job_title}</p>
                        <p class="text-xs font-source text-gray-500">${pathway.job_function}</p>
                    </div>
                    <div class="text-right">
                        <span class="similarity-score-badge">${(pathway[scoreField] * 100).toFixed(1)}%</span>
                        <p class="text-xs font-source text-gray-500 mt-1">similarity</p>
                    </div>
                </div>
            `).join('');

            SkillEngine.DOMHelpers.updateElementHTML('similar-jobs-list', html);
            
            // Add click handlers for pathway items
            this.addPathwayClickHandlers();
        }
    },

    /**
     * Add click handlers to pathway items
     */
    addPathwayClickHandlers() {
        const pathwayItems = document.querySelectorAll('.similar-job-item[data-job-id]');
        pathwayItems.forEach(item => {
            item.addEventListener('click', () => {
                const jobId = item.dataset.jobId;
                this.handlePathwayClick(jobId);
            });
        });
    },

    /**
     * Initialize similarity method radio buttons for job explorer
     */
    initializeSimilarityMethodRadios() {
        const similarityMethodRadios = document.querySelectorAll('input[name="job-explorer-similarity-method"]');
        const descriptionElement = document.getElementById('job-explorer-similarity-description');

        if (similarityMethodRadios.length === 0) return;

        // Set initial description
        this.updateSimilarityMethodDescription();

        // Add event listeners
        similarityMethodRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                this.updateSimilarityMethodDescription();
                
                // Reload career pathways with new method if a job is selected
                const selectedJob = SkillEngine.JobExplorerController.state.selectedJob;
                if (selectedJob) {
                    console.log(`🔄 Similarity method changed to: ${radio.value}, reloading pathways...`);
                    
                    // First reload the data with new similarity method
                    this.loadCareerPathways(selectedJob.id).then(() => {
                        // Then get current slider value and display filtered results
                        const similaritySlider = document.getElementById('similarity-slider');
                        const sliderValue = similaritySlider ? parseFloat(similaritySlider.value) : 0;
                        let threshold;
                        
                        if (radio.value === 'literal') {
                            threshold = sliderValue / 100; // For literal, use percentage directly
                        } else {
                            threshold = Math.max(0.1, (sliderValue / 100) * 0.2); // For enhanced, scale down
                        }
                        
                        console.log(`🎯 Applying threshold: ${threshold} for ${radio.value} method with slider at ${sliderValue}%`);
                        
                        // Update state and display
                        SkillEngine.JobExplorerController.state.currentSimilarityThreshold = threshold;
                        this.displayFilteredCareerPathways(selectedJob.id, threshold);
                    }).catch(error => {
                        console.error('❌ Error reloading pathways after method change:', error);
                    });
                }
            });
        });
    },

    /**
     * Update similarity method description text for job explorer
     */
    updateSimilarityMethodDescription() {
        const selectedMethod = document.querySelector('input[name="job-explorer-similarity-method"]:checked')?.value;
        const descriptionElement = document.getElementById('job-explorer-similarity-description');
        
        if (descriptionElement) {
            if (selectedMethod === 'literal') {
                descriptionElement.textContent = 'Direct skill overlap count - may show more results';
            } else {
                descriptionElement.textContent = 'Weighted analysis prioritising defining skills';
            }
        }
    },

    /**
     * Handle clicking on a career pathway
     */
    handlePathwayClick(jobId) {
        // Navigate to career pathways page with this job as starting point
        const url = `/career-pathways?start=${jobId}`;
        window.location.href = url;
    },


};
