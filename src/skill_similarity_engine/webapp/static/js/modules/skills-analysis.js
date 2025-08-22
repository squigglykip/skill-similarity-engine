/**
 * Skills Analysis Module
 * Handles enhanced skills analysis display, breadcrumbs, and contextual insights
 * Extracted from career_pathways.html embedded script
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.SkillsAnalysis = {
    // State management
    state: {
        currentPathNodes: [],
        selectedStepIndex: 0,
        analysisData: null
    },

    /**
     * Update breadcrumb trail
     */
    updateBreadcrumbs(pathNodes) {
        this.state.currentPathNodes = pathNodes;
        this.state.selectedStepIndex = pathNodes.length - 1;
        
        const container = document.getElementById('career-progression-trail');
        if (!container) return;

        const breadcrumbsHtml = pathNodes.map((node, index) => {
            const data = node.data;
            const isSelected = index === this.state.selectedStepIndex;
            const similarity = data.similarity_score ? Math.round(data.similarity_score * 100) + '%' : '100%';
            
            return `
                <div class="job-breadcrumb ${isSelected ? 'selected' : ''}" 
                     onclick="SkillEngine.SkillsAnalysis.selectBreadcrumbStep(${index})">
                    <div class="job-title">${data.display_name_compact || data.name || data.job_title || 'Unknown Role'}</div>
                    <div class="job-similarity">${similarity}</div>
                    <div class="job-level">Level ${index}</div>
                </div>
            `;
        }).join('');

        container.innerHTML = breadcrumbsHtml;
        
        // Trigger analysis update
        this.updateAnalysisSections();
        
        console.log('✅ Career pathway trail built successfully!');
    },

    /**
     * Select breadcrumb step
     */
    selectBreadcrumbStep(stepIndex) {
        console.log('🔍 Breadcrumb step selected:', stepIndex);
        
        this.state.selectedStepIndex = stepIndex;
        
        // Update breadcrumb visual selection
        document.querySelectorAll('.job-breadcrumb').forEach((el, index) => {
            el.classList.toggle('selected', index === stepIndex);
        });
        
        // Update analysis sections
        this.updateAnalysisSections();
    },

    /**
     * Update analysis sections with real data
     */
    async updateAnalysisSections() {
        if (!this.state.currentPathNodes || this.state.currentPathNodes.length === 0) return;
        
        // Update skills analysis
        await this.updateSkillsAnalysis();
        
        // Update workforce analysis
        await this.updateWorkforceAnalysis();
    },

    /**
     * Update skills analysis section
     */
    async updateSkillsAnalysis() {
        const pathNodes = this.state.currentPathNodes;
        const selectedStepIndex = this.state.selectedStepIndex;
        
        if (!pathNodes || pathNodes.length === 0) return;
        
        let startNode, endNode, contextText;
        
        if (selectedStepIndex === 0) {
            startNode = pathNodes[0];
            endNode = pathNodes[pathNodes.length - 1];
            contextText = 'Full Career Journey';
        } else {
            startNode = pathNodes[selectedStepIndex - 1];
            endNode = pathNodes[selectedStepIndex];
            contextText = `Step ${selectedStepIndex} Transition`;
        }
        
        const startData = startNode.data;
        const endData = endNode.data;
        
        // Update comparison header
        this.updateComparisonHeader(startData, endData, selectedStepIndex, contextText);
        
        // Get job IDs
        const startJobId = this.extractJobId(startData);
        const endJobId = this.extractJobId(endData);
        
        // Fetch and display skills analysis
        await this.fetchSkillsAnalysis(startJobId, endJobId, selectedStepIndex, contextText);
    },

    /**
     * Update comparison header
     */
    updateComparisonHeader(startData, endData, selectedStepIndex, contextText) {
        const headerStartRole = startData.display_name_standard || startData.name || startData.job_title || 'Starting Role';
        const headerEndRole = endData.display_name_standard || endData.name || endData.job_title || 'Target Role';
        const headerElement = document.getElementById('skills-comparison-header');
        
        if (headerElement) {
            const headerText = selectedStepIndex === 0 ? 
                `Analyzing: Full Career Journey from "${headerStartRole}" to "${headerEndRole}"` :
                `Analyzing: "${headerStartRole}" → "${headerEndRole}"`;
            headerElement.querySelector('div').innerHTML = headerText;
        }
    },

    /**
     * Fetch skills analysis from API
     */
    async fetchSkillsAnalysis(startJobId, endJobId, selectedStepIndex, contextText) {
        console.log(`🔍 Fetching skills analysis: ${startJobId} → ${endJobId}`);
        
        // Show loading indicators
        this.setSkillsLoadingState();
        
        try {
            const response = await fetch(`/api/skills-analysis/${startJobId}/${endJobId}`);
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Unknown error');
            }
            
            // Store analysis data
            this.state.analysisData = data;
            
            // Update UI with real data
            this.displaySkillsAnalysis(data, selectedStepIndex, contextText);
            
            console.log(`✅ Real skills analysis populated for step ${selectedStepIndex}`);
            
        } catch (error) {
            console.error('❌ Error fetching skills analysis:', error);
            this.showSkillsError(error.message);
        }
    },

    /**
     * Set loading state for skills section
     */
        setSkillsLoadingState() {
        const elements = [
            'skills-matched-count',
            'skills-develop-count',
            'defining-skills-match',
            'transition-difficulty',
            'defining-matched-count',
            'defining-develop-count'
        ];
        
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.textContent = '...';
        });
        
        // Hide the defining skills section while loading
        const definingSection = document.getElementById('defining-skills-section');
        if (definingSection) {
            definingSection.classList.add('hidden');
        }
    },

    /**
     * Display skills analysis results
     */
    displaySkillsAnalysis(data, selectedStepIndex, contextText) {
        // Update summary cards
        this.updateElement('skills-matched-count', data.skills_matched);
        this.updateElement('skills-develop-count', data.skills_to_develop);
        this.updateElement('transition-difficulty', data.transition_difficulty);
        
        // Update defining skills data
        this.updateDefiningSkillsSection(data);
        
        // Update detailed breakdown
        this.updateSkillsBreakdown(data, selectedStepIndex, contextText);
    },

    /**
     * Update defining skills section
     */
    updateDefiningSkillsSection(data) {
        const insights = data.enhanced_insights || {};
        const definingMatched = insights.defining_skills_matched || 0;
        const definingToDevelop = insights.defining_skills_to_develop || 0;
        const totalDefining = definingMatched + definingToDevelop;
        
        // Update the main defining skills card
        if (totalDefining > 0) {
            this.updateElement('defining-skills-match', `${definingMatched}/${totalDefining}`);
        } else {
            this.updateElement('defining-skills-match', '—');
        }
        
        // Update individual counts in the detailed section
        this.updateElement('defining-matched-count', definingMatched);
        this.updateElement('defining-develop-count', definingToDevelop);
        
        // Show/hide the defining skills sections
        const definingSection = document.getElementById('defining-skills-section');
        const noDefiningSection = document.getElementById('no-defining-skills');
        
        if (totalDefining > 0) {
            if (definingSection) definingSection.classList.remove('hidden');
            if (noDefiningSection) noDefiningSection.classList.add('hidden');
        } else {
            if (definingSection) definingSection.classList.add('hidden');
            if (noDefiningSection) noDefiningSection.classList.remove('hidden');
        }
    },

    /**
     * Update skills breakdown section
     */
    updateSkillsBreakdown(data, selectedStepIndex, contextText) {
        const skillsBreakdown = document.getElementById('skills-breakdown-content');
        if (!skillsBreakdown) return;
        
        // Context indicator
        const contextIndicator = selectedStepIndex === 0 ? 
            `<div class="mb-3 p-2 bg-blue-50 border border-blue-200 rounded-md">
                <div class="text-xs font-source text-blue-800">
                    <strong>Analysis Context:</strong> ${contextText} - Overview from start to final destination
                </div>
            </div>` :
            `<div class="mb-3 p-2 bg-purple-50 border border-purple-200 rounded-md">
                <div class="text-xs font-source text-purple-800">
                    <strong>Analysis Context:</strong> ${contextText} - Transition analysis
                </div>
            </div>`;
        
        // Group skills by status
        const allMatchedSkills = data.detailed_skills.filter(skill => skill.status === 'matched');
        const allDevelopSkills = data.detailed_skills.filter(skill => skill.status === 'develop');
        
        const html = contextIndicator + `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                ${this.renderSkillsSection({
                    title: '✓ Skills Already Matched',
                    count: data.skills_matched,
                    skills: allMatchedSkills,
                    visibleCount: 8,
                    sectionId: 'matched-skills',
                    colorClass: 'green',
                    bgClass: 'bg-green-50 border-green-200',
                    textClass: 'text-green-800',
                    contentClass: 'text-green-700',
                    triggerClass: 'text-green-600'
                })}
                ${this.renderSkillsSection({
                    title: '⚡ Skills to Develop',
                    count: data.skills_to_develop,
                    skills: allDevelopSkills,
                    visibleCount: 8,
                    sectionId: 'develop-skills',
                    colorClass: 'orange',
                    bgClass: 'bg-orange-50 border-orange-200',
                    textClass: 'text-orange-800',
                    contentClass: 'text-orange-700',
                    triggerClass: 'text-orange-600'
                })}
            </div>
            
            <div class="mt-4 p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
                <h5 class="text-sm font-epilogue font-medium text-indigo-800 mb-2">Skill Type Distribution</h5>
                <div class="grid grid-cols-2 gap-3 text-xs">
                    <div class="text-center">
                        <div class="text-lg font-bold text-blue-600">${data.skills_matched}</div>
                        <div class="text-blue-600">Skills Matched</div>
                    </div>
                    <div class="text-center">
                        <div class="text-lg font-bold text-orange-600">${data.skills_to_develop}</div>
                        <div class="text-orange-600">To Develop</div>
                    </div>
                </div>
            </div>
            
            <div class="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div class="text-sm font-source text-blue-800">
                    <strong>Transition Summary:</strong> ${contextText === 'Full Career Journey' ? 
                        `Complete career journey analysis` :
                        `Specific transition analysis`
                    } shows ${data.skills_matched} matching skills and ${data.skills_to_develop} skills to develop.
                    Transition difficulty: <strong>${data.transition_difficulty}</strong>
                </div>
            </div>
        `;
        
        skillsBreakdown.innerHTML = html;
    },

    /**
     * Render an expandable skills section
     */
    renderSkillsSection(config) {
        const {
            title,
            count,
            skills,
            visibleCount,
            sectionId,
            colorClass,
            bgClass,
            textClass,
            contentClass,
            triggerClass
        } = config;

        const visibleSkills = skills.slice(0, visibleCount);
        const hiddenSkills = skills.slice(visibleCount);
        const hasHiddenSkills = hiddenSkills.length > 0;

        return `
            <div class="${bgClass} border rounded-lg p-3">
                <h5 class="text-sm font-epilogue font-medium ${textClass} mb-2">${title} (${count})</h5>
                <div class="space-y-2 text-xs font-source ${contentClass}">
                    ${visibleSkills.map(skill => `
                        <div class="flex items-center justify-between">
                            <div>• ${this.renderSkillName(skill)}</div>
                            <div class="flex space-x-1">
                                ${this.renderSkillTypeBadge(skill.skill_type, skill)}
                                ${this.renderDefiningSkillBadge(skill)}
                            </div>
                        </div>
                    `).join('')}
                    
                    ${hasHiddenSkills ? `
                        <div class="expandable-hidden-content space-y-2" data-expandable-content="${sectionId}" aria-hidden="true" style="display: none;">
                            ${hiddenSkills.map(skill => `
                                <div class="flex items-center justify-between">
                                    <div>• ${this.renderSkillName(skill)}</div>
                                    <div class="flex space-x-1">
                                        ${this.renderSkillTypeBadge(skill.skill_type, skill)}
                                        ${this.renderDefiningSkillBadge(skill)}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        
                        <button class="expandable-trigger skills-expandable-trigger ${colorClass}" 
                                data-expandable-trigger="${sectionId}"
                                data-expand-text="+${hiddenSkills.length} more skills"
                                data-collapse-text="Show less"
                                aria-expanded="false">
                            <span class="expandable-trigger-text">+${hiddenSkills.length} more skills</span>
                            <span class="expandable-trigger-icon">▼</span>
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    },

    /**
     * Get CSS class for skill type badge
     */
    getSkillTypeBadgeClass(skillType) {
        if (!skillType) return 'default';
        
        const type = skillType.toLowerCase();
        if (type.includes('specialized')) return 'specialized';
        if (type.includes('core')) return 'core';
        if (type.includes('common')) return 'common';
        if (type.includes('certification')) return 'certification';
        if (type.includes('technical')) return 'technical';
        return 'default';
    },

    /**
     * Render skill name with optional link
     */
    renderSkillName(skill) {
        const skillName = skill.name || 'Unknown Skill';
        const infoUrl = skill.info_url || skill.infoUrl || '';
        
        if (infoUrl && infoUrl.trim() !== '') {
            return `<a href="${infoUrl}" target="_blank" rel="noopener noreferrer" class="skill-name-link">${skillName}</a>`;
        } else {
            return skillName;
        }
    },

    /**
     * Render skill type badge with color coding and link
     */
    renderSkillTypeBadge(skillType, skill) {
        const displayType = skillType || 'Skill';
        const badgeClass = this.getSkillTypeBadgeClass(skillType);
        const infoUrl = skill?.info_url || skill?.infoUrl || '';
        
        if (infoUrl && infoUrl.trim() !== '') {
            return `<a href="${infoUrl}" target="_blank" rel="noopener noreferrer" class="skill-type-badge ${badgeClass}">${displayType}</a>`;
        } else {
            return `<span class="skill-type-badge ${badgeClass}">${displayType}</span>`;
        }
    },

    /**
     * Render defining skill badge if the skill is marked as defining
     */
    renderDefiningSkillBadge(skill) {
        if (!skill || !skill.is_defining) {
            return '';
        }
        
        return `<span class="skill-type-badge defining-skill-badge" title="Critical skill for role success">Defining</span>`;
    },

    /**
     * Update workforce analysis section
     */
    async updateWorkforceAnalysis() {
        const pathNodes = this.state.currentPathNodes;
        const selectedStepIndex = this.state.selectedStepIndex;
        
        if (!pathNodes || pathNodes.length === 0) return;
        
        // Determine which nodes to analyze
        let analysisNodes, contextText;
        
        if (selectedStepIndex === 0) {
            analysisNodes = pathNodes;
            contextText = 'Full Career Journey Context';
        } else {
            analysisNodes = pathNodes.slice(0, selectedStepIndex + 1);
            contextText = `Step ${selectedStepIndex} Transition Context`;
        }
        
        // Get job IDs
        const jobIds = analysisNodes.map(node => {
            const nodeData = node.data || node;
            return this.extractJobId(nodeData);
        }).filter(id => id);
        
        // Fetch and display workforce analysis
        await this.fetchWorkforceAnalysis(jobIds, selectedStepIndex, contextText);
    },

    /**
     * Fetch workforce analysis from API
     */
    async fetchWorkforceAnalysis(jobIds, selectedStepIndex, contextText) {
        console.log(`🔍 Fetching workforce analysis for jobs: ${jobIds.join(', ')}`);
        
        // Show loading indicators
        this.setWorkforceLoadingState();
        
        try {
            const response = await fetch(`/api/workforce-analysis/${jobIds.join(',')}`);
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Unknown error');
            }
            
            // Update UI with real data
            this.displayWorkforceAnalysis(data, selectedStepIndex, contextText, jobIds.length);
            
            console.log(`✅ Real workforce analysis populated for step ${selectedStepIndex}`);
            
        } catch (error) {
            console.error('❌ Error fetching workforce analysis:', error);
            this.showWorkforceError(error.message);
        }
    },

    /**
     * Set loading state for workforce section
     */
    setWorkforceLoadingState() {
        const elements = [
            'total-positions',
            'divisions-represented',
            'locations-spread',
            'workforce-pathway-count'
        ];
        
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.textContent = '...';
        });
    },

    /**
     * Display workforce analysis results
     */
    displayWorkforceAnalysis(data, selectedStepIndex, contextText, jobCount) {
        // Update summary cards
        this.updateElement('total-positions', data.total_positions.toLocaleString());
        this.updateElement('divisions-represented', data.divisions_represented);
        this.updateElement('locations-spread', data.locations_spread);
        
        // Update workforce table
        this.updateWorkforceTable(data, selectedStepIndex, contextText);
    },

    /**
     * Update workforce table with detailed data
     */
    updateWorkforceTable(data, selectedStepIndex, contextText) {
        const workforceTable = document.getElementById('workforce-pathway-table');
        if (!workforceTable) return;
        
        // Filter data to only show the selected node (the "from" role)
        // For step 0, show the starting role; for other steps, show the selected step role
        const targetJobIndex = selectedStepIndex;
        
        // Find the target job ID based on the selected step
        const availableJobs = [...new Set(data.detailed_workforce.map(item => item.job_id))];
        const targetJobId = availableJobs[targetJobIndex];
        
        if (!targetJobId) {
            workforceTable.innerHTML = `
                <tr>
                    <td colspan="4" class="px-3 py-8 text-center text-sm text-gray-500 break-words">
                        No workforce data available for selected role
                    </td>
                </tr>
            `;
            return;
        }
        
        // Filter data for only the selected job and aggregate by Division + Business Unit + Location
        const selectedJobData = data.detailed_workforce.filter(item => item.job_id === targetJobId);
        const aggregatedData = {};
        
        selectedJobData.forEach(item => {
            const key = `${item.division || 'N/A'}|${item.business_unit || 'N/A'}|${item.location || 'N/A'}`;
            
            if (!aggregatedData[key]) {
                aggregatedData[key] = {
                    division: item.division || 'N/A',
                    business_unit: item.business_unit || 'N/A',
                    location: item.location || 'N/A',
                    total_positions: 0
                };
            }
            
            aggregatedData[key].total_positions += item.position_count;
        });
        
        // Sort by total positions (descending)
        const sortedData = Object.values(aggregatedData).sort((a, b) => b.total_positions - a.total_positions);
        
        if (sortedData.length === 0) {
            workforceTable.innerHTML = `
                <tr>
                    <td colspan="4" class="px-3 py-8 text-center text-sm text-gray-500 break-words">
                        No organisational data found for this role
                    </td>
                </tr>
            `;
            return;
        }
        
        // Create table rows
        const tableRows = sortedData.map((row, index) => {
            const isHighVolume = row.total_positions > 10;
            return `
                <tr class="hover:bg-gray-50">
                    <td class="px-3 py-4 break-words text-sm font-source text-gray-900">
                        ${row.division}
                    </td>
                    <td class="px-3 py-4 break-words text-sm font-source text-gray-900">
                        ${row.business_unit}
                    </td>
                    <td class="px-3 py-4 break-words text-sm font-source text-gray-900">
                        ${row.location}
                    </td>
                    <td class="px-3 py-4 break-words">
                        <span class="text-sm font-source font-medium ${isHighVolume ? 'text-green-600' : 'text-gray-900'}">${row.total_positions}</span>
                        <span class="text-xs font-source text-gray-500 ml-1">positions</span>
                    </td>
                </tr>
            `;
        }).join('');
        
        workforceTable.innerHTML = tableRows;
    },

    /**
     * Extract job ID from node data
     */
    extractJobId(nodeData) {
        if (!nodeData) return null;
        
        return nodeData.job_id ||
               nodeData.JobProfileID ||
               (nodeData.data && nodeData.data.job_id) ||
               (nodeData.data && nodeData.data.JobProfileID) ||
               nodeData.id ||
               (nodeData.data && nodeData.data.id) ||
               null;
    },

    /**
     * Update element text content
     */
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    },

    /**
     * Show skills error message
     */
    showSkillsError(message) {
        const elements = [
            'skills-matched-count', 
            'skills-develop-count', 
            'defining-skills-match',
            'transition-difficulty',
            'defining-matched-count',
            'defining-develop-count'
        ];
        elements.forEach(id => this.updateElement(id, '—'));
        
        // Hide the defining skills section and show no-defining state on error
        const definingSection = document.getElementById('defining-skills-section');
        const noDefiningSection = document.getElementById('no-defining-skills');
        
        if (definingSection) definingSection.classList.add('hidden');
        if (noDefiningSection) noDefiningSection.classList.remove('hidden');
        
        const skillsBreakdown = document.getElementById('skills-breakdown-content');
        if (skillsBreakdown) {
            skillsBreakdown.innerHTML = `
                <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div class="text-sm text-red-800">
                        <strong>Unable to load skills analysis</strong><br>
                        Error: ${message}
                    </div>
                </div>
            `;
        }
    },

    /**
     * Show workforce error message
     */
    showWorkforceError(message) {
        const elements = ['total-positions', 'divisions-represented', 'locations-spread'];
        elements.forEach(id => this.updateElement(id, '—'));
        
        const workforceTable = document.getElementById('workforce-pathway-table');
        if (workforceTable) {
            workforceTable.innerHTML = `
                <tr>
                    <td colspan="4" class="px-3 py-4 break-words">
                        <div class="text-center p-4 bg-red-50 border border-red-200 rounded-lg">
                            <div class="text-sm text-red-800">
                                <strong>Unable to load workforce analysis</strong><br>
                                Error: ${message}
                            </div>
                        </div>
                    </td>
                </tr>
            `;
        }
    }
};

// Global function for backward compatibility
window.showJourneyStep = function(stepIndex) {
    console.log('🔍 Showing journey step analysis for:', stepIndex);
    SkillEngine.SkillsAnalysis.selectBreadcrumbStep(stepIndex);
};

console.log('✅ Skills Analysis module loaded');
