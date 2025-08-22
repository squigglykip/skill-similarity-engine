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
        const state = SkillEngine.JobExplorerController.state;
        
        if (!state.careerPathways || state.careerPathways.length === 0) {
            // Load career pathways first
            this.loadCareerPathways(jobId).then(() => {
                this.renderFilteredPathways(similarityThreshold);
            });
            return;
        }

        this.renderFilteredPathways(similarityThreshold);
    },

    /**
     * Load career pathways from API
     */
    async loadCareerPathways(jobId) {
        try {
            const response = await fetch(`/api/career-pathways-distribution?job_id=${jobId}`);
            const data = await response.json();
            
            if (data.error) {
                console.error('Error loading career pathways:', data.error);
                return;
            }

            // Store in controller state
            SkillEngine.JobExplorerController.state.careerPathways = data.pathways || [];
            
            // Update strategic intelligence
            SkillEngine.StrategicIntelligence.updateStrategicIntelligence(data.pathways);
            
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

        // Filter pathways by current similarity threshold
        const filteredPathways = state.careerPathways.filter(pathway =>
            pathway.similarity_score <= similarityThreshold
        );

        const thresholdPercent = Math.round(similarityThreshold * 100);

        console.log(`🎯 Filtered pathways: ${filteredPathways.length}/${state.careerPathways.length} pathways up to ${thresholdPercent}% threshold`);

        if (filteredPathways.length === 0) {
            SkillEngine.DOMHelpers.updateElementHTML('similar-jobs-list', `
                <div class="text-center p-6 text-gray-500">
                    <p class="text-sm font-source">No pathways found with ≤${thresholdPercent}% similarity</p>
                    <p class="text-xs font-source mt-1">Try raising the similarity threshold</p>
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
                        <span class="similarity-score-badge">${(pathway.similarity_score * 100).toFixed(1)}%</span>
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
     * Handle clicking on a career pathway
     */
    handlePathwayClick(jobId) {
        // Navigate to career pathways page with this job as starting point
        const url = `/career-pathways?start=${jobId}`;
        window.location.href = url;
    },

    /**
     * Update distribution chart (placeholder for future chart implementation)
     */
    updateDistributionChart(pathways) {
        const chartContainer = document.getElementById('pathways-distribution-chart');
        if (!chartContainer) return;

        // Group pathways by job function
        const functionGroups = {};
        pathways.forEach(pathway => {
            const func = pathway.job_function || 'Unknown';
            if (!functionGroups[func]) {
                functionGroups[func] = [];
            }
            functionGroups[func].push(pathway);
        });

        // Create simple bar chart representation
        const chartData = Object.entries(functionGroups).map(([func, paths]) => ({
            function: func,
            count: paths.length,
            avgSimilarity: paths.reduce((sum, p) => sum + p.similarity_score, 0) / paths.length
        }));

        // Sort by count descending
        chartData.sort((a, b) => b.count - a.count);

        // Create simple HTML representation
        const maxCount = Math.max(...chartData.map(d => d.count));
        const html = chartData.map(data => {
            const barWidth = (data.count / maxCount) * 100;
            const similarityPercent = Math.round(data.avgSimilarity * 100);
            
            return `
                <div class="mb-3">
                    <div class="flex justify-between items-center mb-1">
                        <span class="text-sm font-medium text-gray-700">${data.function}</span>
                        <span class="text-xs text-gray-500">${data.count} roles (${similarityPercent}% avg similarity)</span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-2">
                        <div class="bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: ${barWidth}%"></div>
                    </div>
                </div>
            `;
        }).join('');

        chartContainer.innerHTML = `
            <h4 class="text-lg font-medium text-gray-900 mb-4">Career Pathways by Function</h4>
            ${html}
        `;
    }
};
