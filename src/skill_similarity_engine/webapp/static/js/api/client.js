/**
 * API Client Utility Module
 * Centralized API calls with error handling and loading states
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.ApiClient = {
    /**
     * Base fetch wrapper with error handling
     */
    async fetch(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, defaultOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error(`API Error [${url}]:`, error);
            throw error;
        }
    },

    /**
     * Get job details by ID
     */
    async getJobDetails(jobId) {
        return this.fetch(`/api/job-details/${jobId}`);
    },

    /**
     * Search for jobs
     */
    async searchJobs(query, limit = 10) {
        const params = new URLSearchParams({
            search: query,
            limit: limit
        });
        return this.fetch(`/api/career-analysis-jobs?${params}`);
    },

    /**
     * Get D3 tree data
     */
    async getTreeData(jobIds, options = {}) {
        const params = new URLSearchParams({
            jobs: Array.isArray(jobIds) ? jobIds.join(',') : jobIds,
            similarity: options.similarity || 0.2,
            depth: options.depth || 3,
            max_results: options.maxResults || 6,
            ...options.filters
        });
        
        return this.fetch(`/api/d3-tree-data?${params}`);
    },

    /**
     * Get skills analysis
     */
    async getSkillsAnalysis(startJobId, endJobId) {
        return this.fetch(`/api/skills-analysis/${startJobId}/${endJobId}`);
    },

    /**
     * Get workforce analysis
     */
    async getWorkforceAnalysis(jobIds) {
        const jobIdString = Array.isArray(jobIds) ? jobIds.join(',') : jobIds;
        return this.fetch(`/api/workforce-analysis/${jobIdString}`);
    },

    /**
     * Get organizational data for filters
     */
    async getOrganizationalData() {
        return this.fetch('/api/organizational-data');
    },

    /**
     * Get job similarities
     */
    async getJobSimilarities(jobId) {
        return this.fetch(`/api/job-similarities/${jobId}`);
    }
};

console.log('✅ API Client utility loaded');