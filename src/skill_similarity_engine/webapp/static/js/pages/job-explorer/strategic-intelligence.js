/**
 * Job Explorer - Strategic Intelligence Analysis
 * Handles strategic workforce intelligence calculations and display
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.StrategicIntelligence = {
    /**
     * Update strategic intelligence section
     */
    updateStrategicIntelligence(pathways) {
        const state = SkillEngine.JobExplorerController.state;
        
        if (!state.selectedJob || !pathways || pathways.length === 0) {
            SkillEngine.DOMHelpers.updateElementHTML('strategic-indicators', `
                <div class="col-span-2 text-center p-6 text-gray-500">
                    <p class="text-sm font-source">Strategic analysis requires career pathway data</p>
                </div>
            `);
            SkillEngine.DOMHelpers.updateElementHTML('context-insights', `
                <div class="text-center p-4 text-gray-500">
                    <p class="text-sm font-source">No workforce context insights available</p>
                </div>
            `);
            return;
        }

        // Calculate strategic metrics
        const strategicMetrics = this.calculateStrategicMetrics(pathways);

        // Display strategic indicators
        this.displayStrategicIndicators(strategicMetrics);

        // Display context insights
        this.displayContextInsights(strategicMetrics);
    },

    /**
     * Calculate strategic metrics for the job
     */
    calculateStrategicMetrics(pathways) {
        const metrics = {
            mobilityScore: 0,
            transitionReadiness: 0,
            crossFamilyConnections: 0,
            hubPotential: 'LOW',
            riskLevel: 'LOW',
            strategicValue: 'MEDIUM'
        };

        // Mobility Score (0-100) - based on number of pathways and average similarity
        metrics.mobilityScore = Math.min(100, (pathways.length / 12) * 100);

        // Transition Readiness - average similarity of all pathways
        const avgSimilarity = pathways.reduce((sum, p) => sum + p.similarity_score, 0) / pathways.length;
        metrics.transitionReadiness = Math.round(avgSimilarity * 100);

        // Cross-family connections - count unique job families in pathways
        const uniqueFunctions = new Set(pathways.map(p => p.job_function));
        metrics.crossFamilyConnections = uniqueFunctions.size;

        // Hub potential - high if many pathways with good similarity
        const highSimilarityPaths = pathways.filter(p => p.similarity_score > 0.5).length;
        if (highSimilarityPaths >= 8) {
            metrics.hubPotential = 'HIGH';
        } else if (highSimilarityPaths >= 5) {
            metrics.hubPotential = 'MEDIUM';
        }

        // Risk level - based on cross-family diversity and transition readiness
        if (metrics.crossFamilyConnections <= 2 && metrics.transitionReadiness < 50) {
            metrics.riskLevel = 'HIGH';
        } else if (metrics.crossFamilyConnections <= 3 && metrics.transitionReadiness < 70) {
            metrics.riskLevel = 'MEDIUM';
        }

        // Strategic value - combination of mobility and hub potential
        if (metrics.mobilityScore >= 80 && metrics.hubPotential === 'HIGH') {
            metrics.strategicValue = 'HIGH';
        } else if (metrics.mobilityScore >= 60 && metrics.hubPotential !== 'LOW') {
            metrics.strategicValue = 'MEDIUM';
        } else {
            metrics.strategicValue = 'LOW';
        }

        return metrics;
    },

    /**
     * Display strategic indicators
     */
    displayStrategicIndicators(metrics) {
        const indicators = [
            {
                title: 'Mobility Hub Score',
                value: `${metrics.mobilityScore}%`,
                description: 'Career pathway connectivity',
                color: metrics.mobilityScore >= 80 ? 'green' : metrics.mobilityScore >= 60 ? 'yellow' : 'red',
                icon: '🔄',
                tooltip: 'Measures this role\'s connectivity within the career pathway network. Higher scores indicate roles that serve as excellent transition points with many viable career pathways.'
            },
            {
                title: 'Transition Readiness',
                value: `${metrics.transitionReadiness}%`,
                description: 'Average pathway similarity',
                color: metrics.transitionReadiness >= 70 ? 'green' : metrics.transitionReadiness >= 50 ? 'yellow' : 'red',
                icon: '🎯',
                tooltip: 'Indicates how easily employees can transition from this role to other positions. Higher percentages mean stronger skill overlap with potential career moves.'
            },
            {
                title: 'Cross-Family Reach',
                value: `${metrics.crossFamilyConnections}`,
                description: 'Connected job functions',
                color: metrics.crossFamilyConnections >= 5 ? 'green' : metrics.crossFamilyConnections >= 3 ? 'yellow' : 'red',
                icon: '🌐',
                tooltip: 'Shows the diversity of job functions accessible from this role. Higher numbers indicate excellent cross-training potential and inter-departmental mobility opportunities.'
            },
            {
                title: 'Strategic Value',
                value: metrics.strategicValue,
                description: 'Workforce planning priority',
                color: metrics.strategicValue === 'HIGH' ? 'green' : metrics.strategicValue === 'MEDIUM' ? 'yellow' : 'red',
                icon: '⭐',
                tooltip: 'Overall assessment of this role\'s importance in workforce planning strategy. Combines mobility score and hub potential to identify key positions for succession planning.'
            }
        ];

        const colorClasses = {
            green: 'border-green-500 bg-green-50',
            yellow: 'border-yellow-500 bg-yellow-50',
            red: 'border-red-500 bg-red-50'
        };

        const textColorClasses = {
            green: 'text-green-700',
            yellow: 'text-yellow-700',
            red: 'text-red-700'
        };

        const html = indicators.map(indicator => `
            <div class="strategic-indicator-card border-l-4 ${colorClasses[indicator.color]} rounded-lg p-4">
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center space-x-2">
                        <span class="text-lg">${indicator.icon}</span>
                        <h5 class="text-sm font-source font-semibold text-gray-700">${indicator.title}</h5>
                        <div class="relative">
                            <button class="text-gray-400 hover:text-blue-600 transition-colors duration-200 group">
                                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"></path>
                                </svg>
                                <div class="absolute left-0 bottom-full mb-3 w-72 px-4 py-3 bg-slate-800 text-white text-sm leading-relaxed rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-all duration-300 z-20 border border-slate-600 pointer-events-none text-left">
                                    <div class="font-medium text-slate-100 mb-1">${indicator.title}</div>
                                    <div class="text-slate-200">${indicator.tooltip}</div>
                                    <div class="absolute top-full left-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-800"></div>
                                </div>
                            </button>
                        </div>
                    </div>
                    <span class="text-lg font-epilogue font-bold ${textColorClasses[indicator.color]}">${indicator.value}</span>
                </div>
                <p class="text-xs font-source text-gray-600">${indicator.description}</p>
            </div>
        `).join('');

        SkillEngine.DOMHelpers.updateElementHTML('strategic-indicators', html);
    },

    /**
     * Display context insights
     */
    displayContextInsights(metrics) {
        const insights = [];

        // Generate insights based on metrics
        if (metrics.hubPotential === 'HIGH') {
            insights.push({
                type: 'success',
                title: 'Career Progression Hub',
                description: 'This role serves as an excellent stepping stone with multiple progression pathways',
                icon: '🚀'
            });
        }

        if (metrics.riskLevel === 'HIGH') {
            insights.push({
                type: 'warning',
                title: 'Limited Mobility Options',
                description: 'Consider cross-training opportunities to increase workforce flexibility',
                icon: '⚠️'
            });
        }

        if (metrics.strategicValue === 'HIGH') {
            insights.push({
                type: 'info',
                title: 'High Strategic Value',
                description: 'Priority role for succession planning and talent development initiatives',
                icon: '🎯'
            });
        }

        if (metrics.crossFamilyConnections >= 5) {
            insights.push({
                type: 'success',
                title: 'Cross-Functional Versatility',
                description: 'Excellent opportunities for cross-departmental career moves',
                icon: '🌐'
            });
        }

        if (metrics.transitionReadiness >= 80) {
            insights.push({
                type: 'success',
                title: 'High Transition Readiness',
                description: 'Strong skill overlap enables smooth career transitions',
                icon: '✅'
            });
        } else if (metrics.transitionReadiness < 50) {
            insights.push({
                type: 'warning',
                title: 'Skill Development Needed',
                description: 'Additional training may be required for most career moves',
                icon: '📚'
            });
        }

        // Default insight if no specific conditions are met
        if (insights.length === 0) {
            insights.push({
                type: 'info',
                title: 'Standard Career Mobility',
                description: 'This role offers typical career progression opportunities within the organization',
                icon: 'ℹ️'
            });
        }

        const typeClasses = {
            success: 'border-green-200 bg-green-50 text-green-800',
            warning: 'border-yellow-200 bg-yellow-50 text-yellow-800',
            info: 'border-blue-200 bg-blue-50 text-blue-800',
            error: 'border-red-200 bg-red-50 text-red-800'
        };

        const html = insights.map(insight => `
            <div class="insight-card border-l-4 ${typeClasses[insight.type]} rounded-lg p-4 mb-3">
                <div class="flex items-start space-x-3">
                    <span class="text-lg flex-shrink-0 mt-0.5">${insight.icon}</span>
                    <div>
                        <h6 class="text-sm font-source font-semibold mb-1">${insight.title}</h6>
                        <p class="text-xs font-source leading-relaxed">${insight.description}</p>
                    </div>
                </div>
            </div>
        `).join('');

        SkillEngine.DOMHelpers.updateElementHTML('context-insights', html);
    }
};
