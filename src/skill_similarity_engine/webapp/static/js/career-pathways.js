/**
 * Career Pathways Module
 * Handles D3.js tree visualization, breadcrumb navigation, and real-time analysis
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.CareerPathways = {
    // State management
    state: {
        currentTree: null,
        selectedNode: null,
        pathNodes: [],
        selectedStepIndex: 0,
        organizationalData: null,
        selectedJob: null
    },

    // Configuration
    config: {
        treeNodeSize: [50, 300],
        defaultSimilarity: 0.2,
        defaultDepth: 3,
        defaultMaxResults: 6
    },

    // Initialize the career pathways module
    async init() {
        console.log('🚀 Loading Career Pathway Explorer...');
        
        try {
            // Load organizational data
            await this.loadOrganizationalData();
            
            // Initialize UI components
            this.initializeFilters();
            this.initializeJobSearch();
            this.initializeEventHandlers();
            
            console.log('✅ Career Pathway Explorer loaded');
        } catch (error) {
            console.error('❌ Error initializing Career Pathways:', error);
        }
    },

    // Load organizational data for filters
    async loadOrganizationalData() {
        try {
            const response = await fetch('/api/organizational-data');
            this.state.organizationalData = await response.json();
            console.log('✅ Organizational data loaded');
        } catch (error) {
            console.error('❌ Error loading organizational data:', error);
        }
    },

    // Initialize filter components
    initializeFilters() {
        if (!this.state.organizationalData) return;

        // Populate filter dropdowns
        this.populateFilterDropdown('division-filter', this.state.organizationalData.divisions);
        this.populateFilterDropdown('business-unit-filter', this.state.organizationalData.business_units);
        this.populateFilterDropdown('location-filter', this.state.organizationalData.locations);
        this.populateFilterDropdown('region-filter', this.state.organizationalData.regions);

        console.log('✅ Organizational filters initialized');
    },

    // Populate a filter dropdown
    populateFilterDropdown(elementId, options) {
        const select = document.getElementById(elementId);
        if (!select || !options) return;

        // Clear existing options except the first one
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }

        // Add new options
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            select.appendChild(optionElement);
        });
    },

    // Initialize job search functionality
    initializeJobSearch() {
        const searchInput = document.getElementById('job-search-input');
        const searchResults = document.getElementById('job-search-results');
        
        if (searchInput && searchResults) {
            SkillEngine.search.initAutocomplete(searchInput, searchResults);
            
            // Listen for job selection
            document.addEventListener('jobSelected', (event) => {
                this.handleJobSelection(event.detail);
            });
        }
    },

    // Initialize event handlers
    initializeEventHandlers() {
        // Generate tree button
        const generateBtn = document.getElementById('generate-tree-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateCareerTree());
        }

        // Filter change handlers
        ['similarity-threshold', 'depth-limit', 'max-results'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => this.updateTreeIfExists());
            }
        });
    },

    // Handle job selection from search
    async handleJobSelection(jobDetail) {
        console.log('🔍 Job selected:', jobDetail);
        
        // Store selected job
        this.state.selectedJob = jobDetail;
        
        // Auto-generate tree if enabled
        const autoGenerate = document.getElementById('auto-generate')?.checked;
        if (autoGenerate) {
            await this.generateCareerTree();
        }
    },

    // Generate career tree
    async generateCareerTree() {
        const selectedJob = this.state.selectedJob;
        if (!selectedJob) {
            alert('Please select a job first');
            return;
        }

        console.log('🌳 Building career pathway tree for:', [selectedJob]);

        try {
            // Show loading
            this.showLoading();

            // Get filter values
            const similarity = parseFloat(document.getElementById('similarity-threshold')?.value || this.config.defaultSimilarity);
            const depth = parseInt(document.getElementById('depth-limit')?.value || this.config.defaultDepth);
            const maxResults = parseInt(document.getElementById('max-results')?.value || this.config.defaultMaxResults);

            // Build API URL
            const params = new URLSearchParams({
                jobs: selectedJob.jobId,
                similarity: similarity,
                depth: depth,
                max_results: maxResults
            });

            // Add organizational filters
            this.addOrganizationalFilters(params);

            console.log('🌳 Building tree: 1 job, depth=' + depth + ', max_results=' + maxResults);

            // Fetch tree data
            const response = await fetch(`/api/d3-tree-data?${params}`);
            const data = await response.json();

            console.log('🌳 API response:', data);

            if (data.success) {
                await this.buildD3Tree(data.tree);
                console.log('✅ Career tree built:', data.tree.children?.length || 0, 'nodes');
            } else {
                throw new Error(data.error || 'Failed to generate tree');
            }

        } catch (error) {
            console.error('❌ Error generating career tree:', error);
            this.showError('Failed to generate career tree: ' + error.message);
        } finally {
            this.hideLoading();
        }
    },

    // Add organizational filters to API params
    addOrganizationalFilters(params) {
        const filters = ['division-filter', 'business-unit-filter', 'location-filter', 'region-filter'];
        
        filters.forEach(filterId => {
            const element = document.getElementById(filterId);
            if (element && element.value) {
                const paramName = filterId.replace('-filter', '').replace('-', '_');
                params.append(paramName, element.value);
            }
        });
    },

    // Build D3.js tree visualization
    async buildD3Tree(treeData) {
        console.log('🌳 Building D3.js interactive tree...');

        // Store tree data
        this.state.currentTree = treeData;

        // Clear existing tree
        const treeContainer = d3.select('#tree-container');
        treeContainer.selectAll('*').remove();

        // Set up SVG
        const containerElement = document.getElementById('tree-container');
        const containerRect = containerElement.getBoundingClientRect();
        const width = Math.max(800, containerRect.width);
        const height = Math.max(600, containerRect.height);

        const svg = treeContainer
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .style('background', '#f8f9fa');

        const g = svg.append('g');

        // Create tree layout
        const tree = d3.tree().nodeSize(this.config.treeNodeSize);
        const root = d3.hierarchy(treeData);
        
        // Generate tree layout
        tree(root);

        console.log('🌳 Tree loaded:', root.children?.length || 0, 'children');

        // Create links
        const links = g.selectAll('.link')
            .data(root.links())
            .enter().append('path')
            .attr('class', 'link')
            .attr('d', d3.linkVertical()
                .x(d => d.x)
                .y(d => d.y))
            .style('fill', 'none')
            .style('stroke', '#ccc')
            .style('stroke-width', 2);

        // Create nodes
        const nodes = g.selectAll('.node')
            .data(root.descendants())
            .enter().append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${d.x},${d.y})`)
            .style('cursor', 'pointer')
            .on('click', (event, d) => this.handleNodeClick(event, d));

        // Add circles for nodes
        nodes.append('circle')
            .attr('r', 8)
            .style('fill', d => this.getNodeColor(d))
            .style('stroke', '#333')
            .style('stroke-width', 2);

        // Add text labels
        nodes.append('text')
            .attr('dy', -15)
            .attr('text-anchor', 'middle')
            .style('font-size', '12px')
            .style('font-weight', 'bold')
            .text(d => this.truncateText(d.data.name || d.data.job_title || 'Unknown', 20));

        // Add similarity scores
        nodes.append('text')
            .attr('dy', 25)
            .attr('text-anchor', 'middle')
            .style('font-size', '10px')
            .style('fill', '#666')
            .text(d => d.data.similarity_score ? `${Math.round(d.data.similarity_score * 100)}%` : '');

        // Center the tree
        const bounds = g.node().getBBox();
        const fullWidth = bounds.width;
        const fullHeight = bounds.height;
        const centerX = width / 2 - bounds.x - fullWidth / 2;
        const centerY = 50 - bounds.y;
        
        g.attr('transform', `translate(${centerX},${centerY})`);

        console.log('🌳 D3 Tree visualization complete');
    },

    // Handle node click
    handleNodeClick(event, d) {
        console.log('🔍 Node clicked:', d.data);
        
        // Update selected node
        this.state.selectedNode = d;
        
        // Update visual selection
        this.updateNodeSelection(d);
        
        // Build pathway trail
        this.buildPathwayTrail(d);
        
        // Update analysis sections
        this.updateAnalysisSections();
    },

    // Update node visual selection
    updateNodeSelection(selectedNode) {
        d3.selectAll('.node circle')
            .style('stroke', '#333')
            .style('stroke-width', 2);
            
        d3.select(selectedNode)
            .select('circle')
            .style('stroke', '#ffd700')
            .style('stroke-width', 4);
    },

    // Build pathway trail (breadcrumbs)
    buildPathwayTrail(targetNode) {
        // Get path from root to target
        const pathNodes = [];
        let current = targetNode;
        
        while (current) {
            pathNodes.unshift(current);
            current = current.parent;
        }
        
        this.state.pathNodes = pathNodes;
        this.state.selectedStepIndex = pathNodes.length - 1;
        
        // Update breadcrumb UI
        this.updateBreadcrumbUI(pathNodes);
    },

    // Update breadcrumb UI
    updateBreadcrumbUI(pathNodes) {
        const container = document.getElementById('career-progression-trail');
        if (!container) return;

        const breadcrumbsHtml = pathNodes.map((node, index) => {
            const data = node.data;
            const isSelected = index === this.state.selectedStepIndex;
            const similarity = data.similarity_score ? Math.round(data.similarity_score * 100) + '%' : '100%';
            
            return `
                <div class="job-breadcrumb ${isSelected ? 'selected' : ''}" 
                     onclick="SkillEngine.CareerPathways.selectBreadcrumbStep(${index})">
                    <div class="job-title">${data.name || data.job_title || 'Unknown Role'}</div>
                    <div class="job-similarity">${similarity}</div>
                    <div class="job-level">Level ${index}</div>
                </div>
            `;
        }).join('');

        container.innerHTML = breadcrumbsHtml;
        
        console.log('✅ Career pathway trail built successfully!');
    },

    // Select breadcrumb step
    selectBreadcrumbStep(stepIndex) {
        console.log('🔍 Breadcrumb step selected:', stepIndex);
        
        this.state.selectedStepIndex = stepIndex;
        
        // Get current path nodes from the global variable if available
        if (window.currentPathNodes && window.currentPathNodes.length > 0) {
            this.state.pathNodes = window.currentPathNodes.map(node => ({
                data: node.data || node
            }));
            console.log('✅ Updated pathNodes from global state:', this.state.pathNodes.length, 'nodes');
        }
        
        // Update breadcrumb visual selection
        document.querySelectorAll('.job-breadcrumb').forEach((el, index) => {
            el.classList.toggle('selected', index === stepIndex);
        });
        
        // Update breadcrumb highlighting in embedded system too
        if (typeof updateBreadcrumbHighlighting === 'function') {
            updateBreadcrumbHighlighting();
        }
        
        // Update analysis sections
        this.updateAnalysisSections();
    },

    // Update analysis sections with real data
    updateAnalysisSections() {
        if (!this.state.pathNodes || this.state.pathNodes.length === 0) return;
        
        // Update skills analysis
        this.updateSkillsAnalysis();
        
        // Update workforce analysis
        this.updateWorkforceAnalysis();
    },

    // Update skills analysis section
    async updateSkillsAnalysis() {
        const pathNodes = this.state.pathNodes;
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
        
        // Get job IDs - handle both node IDs and JobProfileIDs
        const startJobId = this.extractJobId(startData);
        const endJobId = this.extractJobId(endData);
        
        // Fetch and display skills analysis
        await this.fetchSkillsAnalysis(startJobId, endJobId, selectedStepIndex, contextText);
    },

    // Update comparison header
    updateComparisonHeader(startData, endData, selectedStepIndex, contextText) {
        const headerStartRole = startData.name || startData.job_title || 'Starting Role';
        const headerEndRole = endData.name || endData.job_title || 'Target Role';
        const headerElement = document.getElementById('skills-comparison-header');
        
        if (headerElement) {
            const headerText = selectedStepIndex === 0 ? 
                `Analyzing: Full Career Journey from "${headerStartRole}" to "${headerEndRole}"` :
                `Analyzing: "${headerStartRole}" → "${headerEndRole}"`;
            headerElement.querySelector('div').innerHTML = headerText;
        }
    },

    // Fetch skills analysis from API
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
            
            // Update UI with real data
            this.displaySkillsAnalysis(data, selectedStepIndex, contextText);
            
            console.log(`✅ Real skills analysis populated for step ${selectedStepIndex}`);
            
        } catch (error) {
            console.error('❌ Error fetching skills analysis:', error);
            this.showSkillsError(error.message);
        }
    },

    // Set loading state for skills section
    setSkillsLoadingState() {
        const elements = [
            'skills-matched-count',
            'skills-develop-count', 
            'skills-transferable-count',
            'transition-difficulty'
        ];
        
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.textContent = '...';
        });
    },

    // Display skills analysis results
    displaySkillsAnalysis(data, selectedStepIndex, contextText) {
        // Update summary cards
        this.updateElement('skills-matched-count', data.skills_matched);
        this.updateElement('skills-develop-count', data.skills_to_develop);
        this.updateElement('skills-transferable-count', data.skills_transferable);
        this.updateElement('transition-difficulty', data.transition_difficulty);
        
        // Update detailed breakdown
        this.updateSkillsBreakdown(data, selectedStepIndex, contextText);
    },

    // Update skills breakdown section
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
        const matchedSkills = data.detailed_skills.filter(skill => skill.status === 'matched').slice(0, 8);
        const developSkills = data.detailed_skills.filter(skill => skill.status === 'develop').slice(0, 8);
        const transferableSkills = data.detailed_skills.filter(skill => skill.status === 'transferable').slice(0, 6);
        
        const html = contextIndicator + `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="bg-green-50 border border-green-200 rounded-lg p-3">
                    <h5 class="text-sm font-epilogue font-medium text-green-800 mb-2">✓ Skills Already Matched (${data.skills_matched})</h5>
                    <div class="space-y-2 text-xs font-source text-green-700">
                        ${matchedSkills.map(skill => `
                            <div class="flex items-center justify-between">
                                <div>• ${skill.name}</div>
                                <div class="flex space-x-1">
                                    <span class="px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-700">${skill.skill_type}</span>
                                </div>
                            </div>
                        `).join('')}
                        ${data.skills_matched > 8 ? `<div class="text-green-600 font-medium">+${data.skills_matched - 8} more skills</div>` : ''}
                    </div>
                </div>
                <div class="bg-orange-50 border border-orange-200 rounded-lg p-3">
                    <h5 class="text-sm font-epilogue font-medium text-orange-800 mb-2">⚡ Skills to Develop (${data.skills_to_develop})</h5>
                    <div class="space-y-2 text-xs font-source text-orange-700">
                        ${developSkills.map(skill => `
                            <div class="flex items-center justify-between">
                                <div>• ${skill.name}</div>
                                <div class="flex space-x-1">
                                    <span class="px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-700">${skill.skill_type}</span>
                                </div>
                            </div>
                        `).join('')}
                        ${data.skills_to_develop > 8 ? `<div class="text-orange-600 font-medium">+${data.skills_to_develop - 8} more skills</div>` : ''}
                    </div>
                </div>
            </div>
            
            ${data.skills_transferable > 0 ? `
            <div class="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
                <h5 class="text-sm font-epilogue font-medium text-blue-800 mb-2">🔄 Additional Transferable Skills (${data.skills_transferable})</h5>
                <div class="space-y-2 text-xs font-source text-blue-700">
                    ${transferableSkills.map(skill => `
                        <div class="flex items-center justify-between">
                            <div>• ${skill.name}</div>
                            <div class="flex space-x-1">
                                <span class="px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-700">${skill.skill_type}</span>
                            </div>
                        </div>
                    `).join('')}
                    ${data.skills_transferable > 6 ? `<div class="text-blue-600 font-medium">+${data.skills_transferable - 6} more skills</div>` : ''}
                </div>
            </div>
            ` : ''}
            
            <div class="mt-4 p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
                <h5 class="text-sm font-epilogue font-medium text-indigo-800 mb-2">Skill Type Distribution</h5>
                <div class="grid grid-cols-3 gap-3 text-xs">
                    <div class="text-center">
                        <div class="text-lg font-bold text-blue-600">${data.skills_matched}</div>
                        <div class="text-blue-600">Skills Matched</div>
                    </div>
                    <div class="text-center">
                        <div class="text-lg font-bold text-orange-600">${data.skills_to_develop}</div>
                        <div class="text-orange-600">To Develop</div>
                    </div>
                    <div class="text-center">
                        <div class="text-lg font-bold text-green-600">${data.skills_transferable}</div>
                        <div class="text-green-600">Transferable</div>
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

    // Update workforce analysis section
    async updateWorkforceAnalysis() {
        const pathNodes = this.state.pathNodes;
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

    // Fetch workforce analysis from API
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

    // Set loading state for workforce section
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

    // Display workforce analysis results
    displayWorkforceAnalysis(data, selectedStepIndex, contextText, jobCount) {
        // Update summary cards
        this.updateElement('total-positions', data.total_positions.toLocaleString());
        this.updateElement('divisions-represented', data.divisions_represented);
        this.updateElement('locations-spread', data.locations_spread);
        
        // Update pathway count
        const stepContext = selectedStepIndex === 0 ? 
            `${jobCount} roles in full pathway` :
            `${jobCount} roles up to step ${selectedStepIndex}`;
        this.updateElement('workforce-pathway-count', stepContext);
        
        // Update workforce table
        this.updateWorkforceTable(data, selectedStepIndex, contextText);
    },

    // Update workforce table
    updateWorkforceTable(data, selectedStepIndex, contextText) {
        const workforceTable = document.getElementById('workforce-pathway-table');
        if (!workforceTable) return;
        
        // Context header
        const contextHeader = selectedStepIndex === 0 ?
            `<tr class="bg-blue-50">
                <td colspan="6" class="px-6 py-3 text-sm font-source text-blue-800">
                    <strong>Context:</strong> ${contextText} - All roles from start to final destination
                </td>
            </tr>` :
            `<tr class="bg-purple-50">
                <td colspan="6" class="px-6 py-3 text-sm font-source text-purple-800">
                    <strong>Context:</strong> ${contextText} - Roles involved in this specific transition
                </td>
            </tr>`;
        
        // Group data by job
        const jobGrouped = {};
        data.detailed_workforce.forEach(item => {
            const jobId = item.job_id;
            if (!jobGrouped[jobId]) {
                jobGrouped[jobId] = {
                    job_title: item.job_title,
                    job_function: item.job_function,
                    total_positions: 0,
                    divisions: new Set(),
                    business_units: new Set(),
                    locations: new Set(),
                    regions: new Set()
                };
            }
            
            const job = jobGrouped[jobId];
            job.total_positions += item.position_count;
            if (item.division) job.divisions.add(item.division);
            if (item.business_unit) job.business_units.add(item.business_unit);
            if (item.location) job.locations.add(item.location);
            if (item.region) job.regions.add(item.region);
        });
        
        // Create table rows
        const tableRows = Object.entries(jobGrouped).map(([jobId, job], index) => {
            // Determine role classification
            let pathwayRole, roleClass;
            if (index === 0) {
                pathwayRole = 'Starting Role';
                roleClass = 'bg-blue-100 text-blue-800';
            } else if (index === selectedStepIndex && selectedStepIndex > 0) {
                pathwayRole = `Selected (Step ${index})`;
                roleClass = 'bg-purple-100 text-purple-800';
            } else if (index === Object.keys(jobGrouped).length - 1 && selectedStepIndex === 0) {
                pathwayRole = 'Final Destination';
                roleClass = 'bg-indigo-100 text-indigo-800';
            } else {
                pathwayRole = `Step ${index}`;
                roleClass = 'bg-gray-100 text-gray-800';
            }
            
            const isCurrentStep = index === selectedStepIndex;
            const locationList = Array.from(job.locations).slice(0, 4).join(', ');
            const divisionList = Array.from(job.divisions).slice(0, 2).join(', ');
            const businessUnitList = Array.from(job.business_units).slice(0, 2).join(', ');
            
            return `
                <tr class="hover:bg-gray-50 ${isCurrentStep ? 'ring-2 ring-purple-300' : ''}">
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm font-source font-medium text-gray-900">${job.job_title}</div>
                        <div class="text-xs font-source text-gray-500">${jobId}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-source text-gray-900">
                        ${divisionList || 'N/A'}
                        ${job.divisions.size > 2 ? ` (+${job.divisions.size - 2} more)` : ''}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-source text-gray-900">
                        ${businessUnitList || 'N/A'}
                        ${job.business_units.size > 2 ? ` (+${job.business_units.size - 2} more)` : ''}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="text-sm font-source font-medium text-gray-900">${job.total_positions}</span>
                        <span class="text-xs font-source text-gray-500 ml-1">positions</span>
                    </td>
                    <td class="px-6 py-4 text-sm font-source text-gray-900">
                        ${locationList || 'N/A'}
                        ${job.locations.size > 4 ? ` (+${job.locations.size - 4} more)` : ''}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-source font-medium ${roleClass}">
                            ${pathwayRole}
                        </span>
                    </td>
                </tr>
            `;
        }).join('');
        
        workforceTable.innerHTML = contextHeader + tableRows;
    },

    // Utility functions
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    },

    // Extract job ID from node data, handling both formats
    extractJobId(nodeData) {
        if (!nodeData) return null;
        
        // Priority: Real JobProfileID first, then fallback to D3 node ID
        // The D3 tree uses 'job_id' for the real database JobProfileID
        // and 'id' for the D3 node identifier (node_0, node_1, etc.)
        return nodeData.job_id ||                                           // D3 tree: Real JobProfileID (R0001.5)
               nodeData.JobProfileID ||                                     // Direct database queries
               (nodeData.data && nodeData.data.job_id) ||                   // Nested D3 data
               (nodeData.data && nodeData.data.JobProfileID) ||             // Nested database data
               nodeData.id ||                                               // Fallback: D3 node ID
               (nodeData.data && nodeData.data.id) ||                       // Nested fallback
               null;
    },

    getNodeColor(node) {
        const similarity = node.data.similarity_score || 1;
        if (similarity >= 0.7) return '#22c55e'; // green
        if (similarity >= 0.4) return '#f59e0b'; // yellow
        return '#ef4444'; // red
    },

    truncateText(text, maxLength) {
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },

    showLoading() {
        const button = document.getElementById('generate-tree-btn');
        if (button) {
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span> Generating...';
        }
    },

    hideLoading() {
        const button = document.getElementById('generate-tree-btn');
        if (button) {
            button.disabled = false;
            button.innerHTML = 'Generate Career Tree';
        }
    },

    showError(message) {
        const container = document.getElementById('tree-container');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Error:</strong> ${message}
                </div>
            `;
        }
    },

    showSkillsError(message) {
        const elements = ['skills-matched-count', 'skills-develop-count', 'skills-transferable-count', 'transition-difficulty'];
        elements.forEach(id => this.updateElement(id, '—'));
        
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

    showWorkforceError(message) {
        const elements = ['total-positions', 'divisions-represented', 'locations-spread', 'workforce-pathway-count'];
        elements.forEach(id => this.updateElement(id, '—'));
        
        const workforceTable = document.getElementById('workforce-pathway-table');
        if (workforceTable) {
            workforceTable.innerHTML = `
                <tr>
                    <td colspan="6" class="px-6 py-4">
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
    },

    updateTreeIfExists() {
        if (this.state.currentTree && this.state.selectedJob) {
            this.generateCareerTree();
        }
    }
};

// Integration with existing breadcrumb system
window.showJourneyStep = function(stepIndex) {
    console.log('🔍 Showing journey step analysis for:', stepIndex);
    
    // Use the modular function if available
    if (SkillEngine.CareerPathways && SkillEngine.CareerPathways.selectBreadcrumbStep) {
        SkillEngine.CareerPathways.selectBreadcrumbStep(stepIndex);
    } else {
        console.warn('⚠️ SkillEngine.CareerPathways not available, falling back to minimal header update');
        
        // At minimum, update the comparison header
        if (window.currentPathNodes && window.currentPathNodes.length > stepIndex) {
            const pathNodes = window.currentPathNodes;
            let startNode, endNode;
            
            if (stepIndex === 0) {
                startNode = pathNodes[0];
                endNode = pathNodes[pathNodes.length - 1];
            } else {
                startNode = pathNodes[stepIndex - 1];
                endNode = pathNodes[stepIndex];
            }
            
            const startData = startNode.data || startNode;
            const endData = endNode.data || endNode;
            const headerStartRole = startData.name || startData.job_title || 'Starting Role';
            const headerEndRole = endData.name || endData.job_title || 'Target Role';
            const headerElement = document.getElementById('skills-comparison-header');
            
            if (headerElement) {
                const headerText = stepIndex === 0 ? 
                    `Analyzing: Full Career Journey from "${headerStartRole}" to "${headerEndRole}"` :
                    `Analyzing: "${headerStartRole}" → "${headerEndRole}"`;
                headerElement.querySelector('div').innerHTML = headerText;
            }
        }
    }
    
    // Also update the embedded system's selected index for compatibility
    if (typeof selectedBreadcrumbIndex !== 'undefined') {
        selectedBreadcrumbIndex = stepIndex;
    }
};

// Function for the embedded system to notify about pathway updates
window.notifyPathwayUpdate = function(pathNodes) {
    if (SkillEngine.CareerPathways) {
        SkillEngine.CareerPathways.state.pathNodes = pathNodes.map(node => ({
            data: node.data || node
        }));
        console.log('🔄 Pathway updated from embedded system:', pathNodes.length, 'nodes');
    }
};

// Disabled detailed transition analysis - user prefers simple header only
window.buildTransitionAnalysisForStep = function(fromNode, toNode, stepNumber, totalSteps) {
    // User feedback: Remove the detailed FROM/TO transition breakdown
    // The simple comparison header is sufficient
    console.log('🔍 Transition analysis disabled - using simple header only');
    
    // Clear the transition analysis content since we don't want the detailed breakdown
    const analysisContainer = document.getElementById('transition-analysis-content');
    if (analysisContainer) {
        analysisContainer.innerHTML = ''; // Clear any existing content
    }
};

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize on career pathways page
    if (document.getElementById('tree-container')) {
        SkillEngine.CareerPathways.init();
        
        // Set up integration with existing breadcrumb system
        setTimeout(() => {
            console.log('🔗 Setting up breadcrumb integration...');
            
            // Check if there are existing breadcrumbs and path nodes
            if (window.currentPathNodes && window.currentPathNodes.length > 0) {
                SkillEngine.CareerPathways.state.pathNodes = window.currentPathNodes.map(node => ({
                    data: node.data || node
                }));
                console.log('✅ Integrated with existing pathway:', SkillEngine.CareerPathways.state.pathNodes.length, 'nodes');
            }
        }, 1000);
    }
}); 