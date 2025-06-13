/**
 * Skill Similarity Engine - Main JavaScript
 * Common utilities and event handlers for webapp functionality
 */

// Global app object
window.SkillEngine = {
    // Configuration
    config: {
        searchDelay: 300,
        maxSearchResults: 10,
        similarityThreshold: 0.1
    },
    
    // Utility functions
    utils: {
        // Debounce function for search
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Format similarity score as percentage
        formatSimilarity(score) {
            return `${Math.round(score * 100)}%`;
        },
        
        // Get similarity level for styling
        getSimilarityLevel(score) {
            if (score >= 0.7) return 'high';
            if (score >= 0.4) return 'medium';
            return 'low';
        },
        
        // Show loading spinner
        showLoading(element) {
            element.innerHTML = '<span class="loading-spinner me-2"></span>Loading...';
            element.disabled = true;
        },
        
        // Hide loading spinner
        hideLoading(element, originalText) {
            element.innerHTML = originalText;
            element.disabled = false;
        }
    },
    
    // Search functionality
    search: {
        // Initialize search autocomplete
        initAutocomplete(inputElement, resultsElement) {
            const searchFunction = SkillEngine.utils.debounce(async (query) => {
                if (query.length < 2) {
                    resultsElement.style.display = 'none';
                    return;
                }
                
                try {
                    const response = await fetch(`/api/search-jobs?q=${encodeURIComponent(query)}`);
                    const jobs = await response.json();
                    
                    SkillEngine.search.displayResults(jobs, resultsElement);
                } catch (error) {
                    console.error('Search error:', error);
                    resultsElement.innerHTML = '<div class="search-result-item text-danger">Search error occurred</div>';
                    resultsElement.style.display = 'block';
                }
            }, SkillEngine.config.searchDelay);
            
            inputElement.addEventListener('input', (e) => {
                searchFunction(e.target.value);
            });
            
            // Hide results when clicking outside
            document.addEventListener('click', (e) => {
                if (!inputElement.contains(e.target) && !resultsElement.contains(e.target)) {
                    resultsElement.style.display = 'none';
                }
            });
        },
        
        // Display search results
        displayResults(jobs, resultsElement) {
            if (jobs.length === 0) {
                resultsElement.innerHTML = '<div class="search-result-item text-muted">No results found</div>';
            } else {
                resultsElement.innerHTML = jobs.map(job => `
                    <div class="search-result-item" data-job-id="${job.id}">
                        <div class="fw-medium">${job.name}</div>
                        <small class="text-muted">${job.family} • ${job.family_group}</small>
                    </div>
                `).join('');
                
                // Add click handlers
                resultsElement.querySelectorAll('.search-result-item').forEach(item => {
                    item.addEventListener('click', () => {
                        SkillEngine.search.selectJob(item, resultsElement);
                    });
                });
            }
            resultsElement.style.display = 'block';
        },
        
        // Handle job selection
        selectJob(item, resultsElement) {
            const jobId = item.dataset.jobId;
            const jobName = item.querySelector('.fw-medium').textContent;
            
            // Update input field
            const input = document.querySelector('.search-input');
            if (input) {
                input.value = jobName;
                input.dataset.selectedJobId = jobId;
            }
            
            // Hide results
            resultsElement.style.display = 'none';
            
            // Trigger custom event
            document.dispatchEvent(new CustomEvent('jobSelected', {
                detail: { jobId, jobName }
            }));
        }
    },
    
    // Similarity display functions
    similarity: {
        // Create similarity bar HTML
        createSimilarityBar(score) {
            const level = SkillEngine.utils.getSimilarityLevel(score);
            const percentage = Math.round(score * 100);
            
            return `
                <div class="similarity-bar">
                    <div class="similarity-bar-fill similarity-${level}" style="width: ${percentage}%"></div>
                </div>
                <small class="text-muted">${percentage}% similarity</small>
            `;
        },
        
        // Load similarities for a job
        async loadSimilarities(jobId, containerElement) {
            SkillEngine.utils.showLoading(containerElement);
            
            try {
                const response = await fetch(`/api/job-similarities/${jobId}`);
                const similarities = await response.json();
                
                SkillEngine.similarity.displaySimilarities(similarities, containerElement);
            } catch (error) {
                console.error('Error loading similarities:', error);
                containerElement.innerHTML = '<div class="alert alert-danger">Error loading similarities</div>';
            }
        },
        
        // Display similarities
        displaySimilarities(similarities, containerElement) {
            if (similarities.length === 0) {
                containerElement.innerHTML = '<div class="alert alert-info">No similar jobs found</div>';
                return;
            }
            
            const html = similarities.map(sim => `
                <div class="card card-hover card-similarity mb-3">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col-md-8">
                                <h6 class="card-title mb-1">${sim.job_name}</h6>
                                <small class="text-muted">
                                    <i class="bi bi-folder me-1"></i>${sim.job_family}
                                </small>
                                <div class="mt-2">
                                    <span class="badge badge-skill-count">
                                        ${sim.skill_overlap} skills overlap
                                    </span>
                                </div>
                            </div>
                            <div class="col-md-4 text-md-end">
                                <div class="similarity-score text-primary mb-2">
                                    ${SkillEngine.utils.formatSimilarity(sim.similarity_score)}
                                </div>
                                ${SkillEngine.similarity.createSimilarityBar(sim.similarity_score)}
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
            
            containerElement.innerHTML = html;
        }
    },
    
    // Initialize the application
    init() {
        // Update timestamp
        const timestampElement = document.getElementById('last-updated');
        if (timestampElement) {
            timestampElement.textContent = new Date().toLocaleDateString();
        }
        
        // Initialize search functionality
        const searchInput = document.querySelector('.search-input');
        const searchResults = document.querySelector('.search-results');
        if (searchInput && searchResults) {
            SkillEngine.search.initAutocomplete(searchInput, searchResults);
        }
        
        // Add smooth scrolling to anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
        
        console.log('🚀 Skill Similarity Engine webapp initialised');
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', SkillEngine.init);

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SkillEngine;
} 