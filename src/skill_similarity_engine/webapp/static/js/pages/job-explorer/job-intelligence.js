/**
 * Job Intelligence Analytics Module
 * Handles defining skills, job family, and rarity analysis for single job views
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.JobIntelligence = {
    /**
     * Load and display job intelligence analytics for a specific job
     */
    async loadJobIntelligence(jobId) {
        try {
            console.log(`🧠 Loading job intelligence for: ${jobId}`);
            
            // Load all job intelligence data in parallel
            const [
                definingSkills,
                jobFamily,
                skillRarity,
                specializedSkills
            ] = await Promise.all([
                this.fetchDefiningSkills(jobId),
                this.fetchJobFamily(jobId),
                this.fetchSkillRarity(jobId),
                this.fetchSpecializedSkills(jobId)
            ]);

            // Update summary metrics
            this.updateSummaryMetrics(definingSkills, jobFamily, skillRarity, specializedSkills);
            
            // Update detailed sections
            console.log('📊 Updating sections with data:', {
                definingSkills: definingSkills.length,
                rareSkills: skillRarity.rare_skills?.length || 0,
                specializedSkills: specializedSkills.length,
                jobFamily: jobFamily ? 'available' : 'none'
            });
            
            this.updateDefiningSkillsSection(definingSkills);
            this.updateRareSkillsSection(skillRarity);
            this.updateSpecialisedSkillsSection(specializedSkills);
            this.updateJobFamilySection(jobFamily);
            
            console.log(`✅ Job intelligence loaded for ${jobId}`);
            
        } catch (error) {
            console.error('Error loading job intelligence:', error);
            this.displayError();
        }
    },

    /**
     * Fetch defining skills for the job
     */
    async fetchDefiningSkills(jobId) {
        try {
            const response = await fetch(`/api/v2/job-defining-skills/${jobId}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            // Return the all_defining_skills array from the response
            return data.success ? data.data.all_defining_skills : [];
        } catch (error) {
            console.warn('Defining skills data not available:', error);
            return [];
        }
    },

    /**
     * Fetch job family information
     */
    async fetchJobFamily(jobId) {
        try {
            const response = await fetch(`/api/v2/job-family/${jobId}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.warn('Job family data not available:', error);
            return null;
        }
    },

    /**
     * Fetch skill rarity information for job skills
     */
    async fetchSkillRarity(jobId) {
        try {
            const response = await fetch(`/api/v2/skill-rarity-analysis/${jobId}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            // Return the data part of the response
            return data.success ? data.data : { rare_skills: [], total_skills: 0 };
        } catch (error) {
            console.warn('Skill rarity data not available:', error);
            return { rare_skills: [], total_skills: 0 };
        }
    },

    /**
     * Fetch specialized skills for the job
     */
    async fetchSpecializedSkills(jobId) {
        try {
            const response = await fetch(`/api/v2/specialized-skills/${jobId}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            // The specialized skills API returns an array directly, not wrapped in a data object
            return Array.isArray(data) ? data : [];
        } catch (error) {
            console.warn('Specialized skills data not available:', error);
            return [];
        }
    },

    /**
     * Update summary metrics cards
     */
    updateSummaryMetrics(definingSkills, jobFamily, skillRarity, specializedSkills) {
        // Defining skills count
        SkillEngine.DOMHelpers.updateElementText(
            'job-defining-skills-count', 
            definingSkills.length || '0'
        );

        // Rare skills count
        SkillEngine.DOMHelpers.updateElementText(
            'job-rare-skills-count', 
            skillRarity.rare_skills?.length || '0'
        );

        // Job family size
        SkillEngine.DOMHelpers.updateElementText(
            'job-family-size', 
            jobFamily?.cluster_size || '—'
        );

        // Specialized skills count
        SkillEngine.DOMHelpers.updateElementText(
            'job-specialised-skills-count', 
            specializedSkills.length || '0'
        );
    },

    /**
     * Update defining skills deep dive section
     */
    updateDefiningSkillsSection(definingSkills) {
        console.log(`🔧 DEBUG: updateDefiningSkillsSection called with:`, definingSkills?.length || 0, 'skills');
        
        const container = document.getElementById('defining-skills-content');
        console.log(`🔧 DEBUG: defining-skills-content container:`, container ? 'FOUND' : 'NOT FOUND');
        
        if (!container) {
            console.error(`❌ Could not find defining-skills-content container`);
            return;
        }

        console.log(`🔧 DEBUG: Container before update:`, {
            className: container.className,
            innerHTML: container.innerHTML.substring(0, 100) + '...',
            isHidden: container.classList.contains('hidden')
        });

        if (!definingSkills || definingSkills.length === 0) {
            console.log(`🔧 DEBUG: No defining skills data, showing placeholder`);
            container.innerHTML = `
                <div class="text-sm text-gray-500 italic">
                    No defining skills analysis available for this job profile
                </div>
            `;
            return;
        }

        // Group skills by category
        const skillsByCategory = this.groupSkillsByCategory(definingSkills);
        console.log(`🔧 DEBUG: Skills grouped by category:`, Object.keys(skillsByCategory));
        
        const html = Object.entries(skillsByCategory).map(([category, skills]) => `
            <div class="mb-4">
                <div class="flex items-center mb-2">
                    <div class="w-2 h-2 bg-indigo-500 rounded-full mr-2"></div>
                    <h5 class="text-sm font-medium text-gray-800">${category}</h5>
                    <span class="ml-2 px-2 py-1 bg-indigo-100 text-indigo-700 text-xs rounded-full">
                        ${skills.length} skills
                    </span>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                    ${skills.map(skill => `
                        <div class="flex items-center justify-between p-2 bg-white border border-gray-200 rounded text-sm">
                            <span class="font-medium text-gray-700">${skill.skill_name}</span>
                            <div class="flex items-center space-x-2">
                                <span class="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded">
                                    Rank ${skill.defining_skill_rank}
                                </span>
                                <span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                                    ${skill.prevalence_percentage?.toFixed(1)}%
                                </span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');

        console.log(`🔧 DEBUG: Generated HTML length:`, html.length, 'characters');
        container.innerHTML = html;
        
        // Keep sections collapsed by default - users can expand manually
        console.log(`🔧 DEBUG: Defining skills section loaded but kept collapsed for user control`);
        
        console.log(`🔧 DEBUG: Container after update:`, {
            className: container.className,
            innerHTML: container.innerHTML.substring(0, 100) + '...',
            isHidden: container.classList.contains('hidden')
        });
        
        console.log(`✅ Successfully updated defining skills section`);
    },

    /**
     * Update rare skills section
     */
    updateRareSkillsSection(skillRarity) {
        const container = document.getElementById('rare-skills-content');
        if (!container) return;

        if (!skillRarity || !skillRarity.rare_skills || skillRarity.rare_skills.length === 0) {
            container.innerHTML = `
                <div class="text-sm text-gray-500 italic">
                    No rare skills found for this job profile
                </div>
            `;
            return;
        }

        const rareSkills = skillRarity.rare_skills;
        
        // Group rare skills by category
        const skillsByCategory = this.groupSkillsByCategory(rareSkills);
        
        const html = Object.entries(skillsByCategory).map(([category, skills]) => `
            <div class="mb-4">
                <div class="flex items-center mb-2">
                    <div class="w-2 h-2 bg-orange-500 rounded-full mr-2"></div>
                    <h5 class="text-sm font-medium text-gray-800">${category}</h5>
                    <span class="ml-2 px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded-full">
                        ${skills.length} skills
                    </span>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                    ${skills.map(skill => `
                        <div class="flex items-center justify-between p-2 bg-white border border-gray-200 rounded text-sm">
                            <span class="font-medium text-gray-700">${skill.skill_name}</span>
                            <div class="flex items-center space-x-2">
                                <span class="px-2 py-1 bg-red-100 text-red-700 text-xs rounded">
                                    ${skill.rarity_category}
                                </span>
                                <span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                                    ${skill.prevalence_percentage?.toFixed(1)}%
                                </span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
        
        // Keep sections collapsed by default - users can expand manually
        console.log(`🔧 DEBUG: Rare skills section loaded but kept collapsed for user control`);
    },

    /**
     * Update specialised skills section
     */
    updateSpecialisedSkillsSection(specializedSkills) {
        const container = document.getElementById('specialised-skills-content');
        if (!container) return;

        if (!specializedSkills || specializedSkills.length === 0) {
            container.innerHTML = `
                <div class="text-sm text-gray-500 italic">
                    No specialised skills found for this job profile
                </div>
            `;
            return;
        }

        // Group specialised skills by category
        const skillsByCategory = this.groupSkillsByCategory(specializedSkills);
        
        const html = Object.entries(skillsByCategory).map(([category, skills]) => `
            <div class="mb-4">
                <div class="flex items-center mb-2">
                    <div class="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                    <h5 class="text-sm font-medium text-gray-800">${category}</h5>
                    <span class="ml-2 px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">
                        ${skills.length} skills
                    </span>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                    ${skills.map(skill => `
                        <div class="flex items-center justify-between p-2 bg-white border border-gray-200 rounded text-sm">
                            <span class="font-medium text-gray-700">${skill.skill_name}</span>
                            <div class="flex items-center space-x-2">
                                <span class="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded">
                                    ${skill.specialization_category || 'Specialised'}
                                </span>
                                <span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                                    ${skill.prevalence_percent?.toFixed(1)}%
                                </span>
                                ${skill.strategic_importance ? `
                                    <span class="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                                        ${skill.strategic_importance}
                                    </span>
                                ` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
        
        // Keep sections collapsed by default - users can expand manually
        console.log(`🔧 DEBUG: Specialised skills section loaded but kept collapsed for user control`);
    },

    /**
     * Update job family section
     */
    updateJobFamilySection(jobFamily) {
        const container = document.getElementById('job-family-content');
        if (!container) return;

        if (!jobFamily) {
            container.innerHTML = `
                <div class="text-sm text-gray-500 italic">
                    No job family analysis available for this job profile
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="space-y-3">
                <div class="flex items-center justify-between p-3 bg-white border border-gray-200 rounded">
                    <div>
                        <div class="font-medium text-gray-800">${jobFamily.cluster_name || 'Unknown Family'}</div>
                        <div class="text-xs text-gray-600">${jobFamily.cluster_description || 'No description available'}</div>
                    </div>
                    <div class="text-right">
                        <div class="text-lg font-semibold text-green-600">${jobFamily.cluster_size || 0}</div>
                        <div class="text-xs text-gray-500">Related roles</div>
                    </div>
                </div>
                
                ${jobFamily.sample_jobs ? `
                <div class="p-3 bg-blue-50 border border-blue-200 rounded">
                    <div class="text-sm font-medium text-blue-900 mb-1">Sample Roles in Family</div>
                    <div class="text-xs text-blue-700">${jobFamily.sample_jobs}</div>
                </div>
                ` : ''}
                
                ${jobFamily.silhouette_score ? `
                <div class="flex items-center justify-between text-xs text-gray-600">
                    <span>Family Similarity Score:</span>
                    <span class="px-2 py-1 bg-gray-100 rounded font-medium" title="How well this job fits within its family cluster (higher is better)">
                        ${(jobFamily.silhouette_score * 100).toFixed(0)}%
                    </span>
                </div>
                ` : ''}
            </div>
        `;
        
        // Job family is now always visible (not collapsible)
        console.log(`🔧 DEBUG: Job family content updated - section is always visible`);
    },

    /**
     * Group skills by category
     */
    groupSkillsByCategory(skills) {
        return skills.reduce((groups, skill) => {
            const category = skill.category || 'Other';
            if (!groups[category]) groups[category] = [];
            groups[category].push(skill);
            return groups;
        }, {});
    },

    /**
     * Display error state
     */
    displayError() {
        const containers = [
            'defining-skills-content',
            'rare-skills-content', 
            'specialised-skills-content',
            'job-family-content'
        ];

        containers.forEach(containerId => {
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = `
                    <div class="text-sm text-red-500 italic">
                        Error loading job intelligence data
                    </div>
                `;
            }
        });

        // Reset metrics to error state
        ['job-defining-skills-count', 'job-rare-skills-count', 'job-family-size', 'job-specialised-skills-count'].forEach(id => {
            SkillEngine.DOMHelpers.updateElementText(id, '—');
        });
    }
};
