/**
 * Job Explorer - Job Details Display
 * Handles job profile display, skills visualization, and detailed information
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.JobDetails = {
    /**
     * Show job profile and hide welcome state
     */
    showJobProfile(selectedJob) {
        const welcomeState = document.getElementById('welcome-state');
        const jobProfileContent = document.getElementById('job-profile-content');
        const gettingStartedPanel = document.getElementById('getting-started-panel');
        const jobArchitecturePanel = document.getElementById('job-architecture-panel');

        if (welcomeState) welcomeState.classList.add('hidden');
        if (jobProfileContent) jobProfileContent.classList.remove('hidden');
        if (gettingStartedPanel) gettingStartedPanel.classList.add('hidden');
        if (jobArchitecturePanel) jobArchitecturePanel.classList.remove('hidden');

        // Load job details
        this.loadJobDetails(selectedJob.id);
    },

    /**
     * Load job details
     */
    async loadJobDetails(jobId) {
        const selectedJob = SkillEngine.JobExplorerController.state.selectedJob;
        
        // Update job header
        SkillEngine.DOMHelpers.updateElementText('job-title-header', selectedJob.title);
        SkillEngine.DOMHelpers.updateElementText('job-function-badge', selectedJob.function);
        SkillEngine.DOMHelpers.updateElementText('job-function-id-badge', selectedJob.function_id || 'N/A');
        SkillEngine.DOMHelpers.updateElementText('job-profile-id', selectedJob.id);

        // Update sidebar quick stats
        this.updateSidebarInfo();

        // Load detailed data
        await Promise.all([
            this.loadJobSkills(jobId),
            this.loadWorkforceContext(jobId),
            this.loadCareerPathways(jobId)
        ]);
    },

    /**
     * Update sidebar information
     */
    updateSidebarInfo() {
        const job = SkillEngine.JobExplorerController.state.selectedJob;
        
        SkillEngine.DOMHelpers.updateElementText('sidebar-job-profile-id', job.id);
        SkillEngine.DOMHelpers.updateElementText('sidebar-job-profile', job.title);
        SkillEngine.DOMHelpers.updateElementText('sidebar-job-id', job.id);
        SkillEngine.DOMHelpers.updateElementText('sidebar-job-name', job.title);
        SkillEngine.DOMHelpers.updateElementText('sidebar-job-function', job.function);
        SkillEngine.DOMHelpers.updateElementText('sidebar-job-function-id', job.function_id || 'N/A');
    },

    /**
     * Load job skills and related data
     */
    async loadJobSkills(jobId) {
        try {
            const data = await SkillEngine.ApiClient.getJobDetails(jobId);
            
            if (data.error) {
                console.error('Error loading job details:', data.error);
                return;
            }

            // Update sidebar stats
            SkillEngine.DOMHelpers.updateElementText('sidebar-skills-count', data.stats.skills_count);
            SkillEngine.DOMHelpers.updateElementText('sidebar-positions-count', data.stats.positions_count);
            SkillEngine.DOMHelpers.updateElementText('sidebar-employees-count', data.stats.employee_count);
            SkillEngine.DOMHelpers.updateElementText('sidebar-pathways-count', data.stats.pathways_count);

            // Update detailed job architecture info
            this.updateJobArchitectureDetails(data.job);

            // Update header badges
            this.updateHeaderBadges(data.job);

            // Display skills
            this.displaySkills(data.skills);

        } catch (error) {
            console.error('Error loading job skills:', error);
        }
    },

    /**
     * Update job architecture details in sidebar
     */
    updateJobArchitectureDetails(job) {
        const updates = {
            'sidebar-job-profile-id': job.id,
            'sidebar-job-profile': job.title,
            'sidebar-job-id': job.job_id || '-',
            'sidebar-job-name': job.job_name || '-',
            'sidebar-job-function': job.function,
            'sidebar-job-function-id': job.function_id || '-',
            'sidebar-profile-title-suffix': job.profile_title_suffix || '-',
            'sidebar-management-level': job.management_level || '-',
            'sidebar-job-category': job.job_category || '-',
            'sidebar-job-subfunction': job.job_subfunction || '-'
        };

        Object.entries(updates).forEach(([id, value]) => {
            SkillEngine.DOMHelpers.updateElementText(id, value);
        });

        // Handle conditional fields
        this.updateConditionalFields(job);
    },

    /**
     * Update conditional fields that only show when data exists
     */
    updateConditionalFields(job) {
        const conditionalFields = document.getElementById('sidebar-conditional-fields');
        let hasConditionalData = false;

        // Customer Facing
        const customerFacingRow = document.getElementById('customer-facing-row');
        if (job.customer_facing) {
            customerFacingRow.classList.remove('hidden');
            SkillEngine.DOMHelpers.updateElementText('sidebar-customer-facing', job.customer_facing);
            hasConditionalData = true;
        } else {
            customerFacingRow.classList.add('hidden');
        }

        // Banking Role
        const bankerRow = document.getElementById('is-banker-row');
        if (job.is_banker) {
            bankerRow.classList.remove('hidden');
            SkillEngine.DOMHelpers.updateElementText('sidebar-is-banker', job.is_banker);
            hasConditionalData = true;
        } else {
            bankerRow.classList.add('hidden');
        }

        // Executive Leadership
        const executiveRow = document.getElementById('executive-leadership-row');
        if (job.executive_leadership_group) {
            executiveRow.classList.remove('hidden');
            hasConditionalData = true;
        } else {
            executiveRow.classList.add('hidden');
        }

        // Accountability Scope
        const accountabilityRow = document.getElementById('accountability-scope-row');
        if (job.accountability_scope) {
            accountabilityRow.classList.remove('hidden');
            SkillEngine.DOMHelpers.updateElementText('sidebar-accountability-scope', job.accountability_scope);
            hasConditionalData = true;
        } else {
            accountabilityRow.classList.add('hidden');
        }

        // Show/hide conditional fields section
        if (hasConditionalData) {
            conditionalFields.classList.remove('hidden');
        } else {
            conditionalFields.classList.add('hidden');
        }
    },

    /**
     * Update header badges
     */
    updateHeaderBadges(job) {
        // Management level badge
        const managementBadge = document.getElementById('management-level-badge');
        if (job.management_level) {
            managementBadge.textContent = job.management_level;
            managementBadge.classList.remove('hidden');
        } else {
            managementBadge.classList.add('hidden');
        }

        // Job category badge
        const categoryBadge = document.getElementById('job-category-badge');
        if (job.job_category) {
            categoryBadge.textContent = job.job_category;
            categoryBadge.classList.remove('hidden');
        } else {
            categoryBadge.classList.add('hidden');
        }
    },

    /**
     * Display skills by category and as a complete list
     */
    displaySkills(skills) {
        // Group skills by category
        const skillsByCategory = {};
        skills.forEach(skill => {
            const category = skill.category || 'Other';
            if (!skillsByCategory[category]) {
                skillsByCategory[category] = [];
            }
            skillsByCategory[category].push(skill);
        });

        // Display skills by category
        const categoryColors = {
            'Technical': 'bg-blue-100 text-blue-800',
            'Leadership': 'bg-purple-100 text-purple-800',
            'Communication': 'bg-green-100 text-green-800',
            'Analytical': 'bg-yellow-100 text-yellow-800',
            'Other': 'bg-gray-100 text-gray-800'
        };

        const skillsByCategoryContainer = document.getElementById('skills-by-category');
        if (skillsByCategoryContainer) {
            const html = Object.entries(skillsByCategory).map(([category, categorySkills]) => {
                const colorClass = categoryColors[category] || categoryColors['Other'];
                const skillsHtml = categorySkills.map(skill => 
                    `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${colorClass} mr-2 mb-2">
                        ${skill.name}
                    </span>`
                ).join('');
                
                return `
                    <div class="mb-6">
                        <h4 class="text-sm font-medium text-gray-700 mb-3">${category} Skills (${categorySkills.length})</h4>
                        <div class="flex flex-wrap">
                            ${skillsHtml}
                        </div>
                    </div>
                `;
            }).join('');
            
            skillsByCategoryContainer.innerHTML = html;
        }

        // Display complete skills list
        const skillsListContainer = document.getElementById('skills-complete-list');
        if (skillsListContainer) {
            const skillsHtml = skills.map(skill => 
                `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${this.getSkillTypeClass(skill.category)} mr-2 mb-2">
                    ${skill.name}
                </span>`
            ).join('');
            
            skillsListContainer.innerHTML = skillsHtml;
        }
    },

    /**
     * Get CSS class for skill type
     */
    getSkillTypeClass(skillType) {
        const typeClasses = {
            'Technical': 'bg-blue-100 text-blue-800',
            'Leadership': 'bg-purple-100 text-purple-800', 
            'Communication': 'bg-green-100 text-green-800',
            'Analytical': 'bg-yellow-100 text-yellow-800',
            'Strategic': 'bg-red-100 text-red-800',
            'Operational': 'bg-indigo-100 text-indigo-800',
            'Interpersonal': 'bg-pink-100 text-pink-800',
            'Other': 'bg-gray-100 text-gray-800'
        };
        
        return typeClasses[skillType] || typeClasses['Other'];
    },

    /**
     * Load workforce context data
     */
    async loadWorkforceContext(jobId) {
        try {
            const response = await fetch(`/api/job-workforce/${jobId}`);
            const data = await response.json();
            
            if (data.error) {
                console.error('Error loading workforce context:', data.error);
                return;
            }

            // Update workforce metrics in UI
            // This would be implemented based on your specific UI structure
            console.log('Workforce context loaded:', data);
            
        } catch (error) {
            console.error('Error loading workforce context:', error);
        }
    },

    /**
     * Load career pathways for this job
     */
    async loadCareerPathways(jobId) {
        try {
            // Use the career pathways module
            SkillEngine.CareerPathways.displayFilteredCareerPathways(
                jobId, 
                SkillEngine.JobExplorerController.state.currentSimilarityThreshold
            );
        } catch (error) {
            console.error('Error loading career pathways:', error);
        }
    },

    /**
     * Export job analysis
     */
    exportAnalysis(selectedJob) {
        // Create export data
        const exportData = {
            job: selectedJob,
            timestamp: new Date().toISOString(),
            analysis_type: 'job_explorer'
        };

        // Create and download file
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `job_analysis_${selectedJob.id}_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        URL.revokeObjectURL(url);
    }
};
