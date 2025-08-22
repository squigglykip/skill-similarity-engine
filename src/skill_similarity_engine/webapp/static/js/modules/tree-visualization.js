/**
 * Tree Visualization Module
 * Handles D3.js tree creation, manipulation, and visualization
 * Extracted from massive embedded script in career_pathways.html
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.TreeVisualization = {
    // State management
    state: {
        treeData: null,
        svg: null,
        g: null,
        tree: null,
        root: null,
        pathwayRoot: null,
        margin: { top: 40, right: 120, bottom: 40, left: 120 },
        width: 800,
        height: 600,
        lastBuiltParameters: null,
        lastBuiltTree: null,
        lastClickedNode: null,
        cachedTreeState: null,
        treeStateCache: null,
        i: 0
    },

    // Configuration - Updated to match old_tree.html
    config: {
        duration: 750,
        // Tree layout dimensions (from old version)
        nodeWidth: 50,              // Fixed horizontal space per node
        nodeHeight: 300,            // Fixed vertical space per node
        
        // Node styling
        nodeRadius: 8,              // Variable radius (will be overridden by getNodeSize)
        
        // Tree positioning handled by zoom/pan interactions (no manual offsets needed)
        
        // Text styling
        maxTextLines: 3,
        textLineHeight: 13,
        textWrapWidth: 180,         // Width for text wrapping (from old version)
        
        // Legacy compatibility
        standardNodeHeight: 68      // Keep for any existing references
    },

    /**
     * Initialize tree controls (sliders, filters, etc.)
     */
    async initializeControls() {
        this.initializeSliders();
        await this.initializeFilters(); // Wait for filters to load
        this.initializeBuildButton();
    },

    /**
     * Initialize slider controls
     */
    initializeSliders() {
        const similaritySlider = document.getElementById('similarity-threshold');
        const depthSlider = document.getElementById('depth-limit');
        const maxResultsSlider = document.getElementById('max-results');

        if (similaritySlider) {
            // Set initial display value
            this.updateSliderDisplay('similarity-threshold', 'similarity-display');
            
            similaritySlider.addEventListener('input', () => {
                this.updateSliderDisplay('similarity-threshold', 'similarity-display');
                if (this.state.lastBuiltTree) {
                    this.scheduleTreeRefresh();
                }
            });
        }

        if (depthSlider) {
            // Set initial display value
            this.updateSliderDisplay('depth-limit', 'depth-display');
            
            depthSlider.addEventListener('input', () => {
                this.updateSliderDisplay('depth-limit', 'depth-display');
                if (this.state.lastBuiltTree) {
                    this.scheduleTreeRefresh();
                }
            });
        }

        if (maxResultsSlider) {
            // Set initial display value
            this.updateSliderDisplay('max-results', 'max-results-display');
            
            maxResultsSlider.addEventListener('input', () => {
                this.updateSliderDisplay('max-results', 'max-results-display');
                if (this.state.lastBuiltTree) {
                    this.scheduleTreeRefresh();
                }
            });
        }

        // Initialize similarity method radio buttons
        this.initializeSimilarityMethodRadios();
    },

    /**
     * Initialize similarity method radio buttons
     */
    initializeSimilarityMethodRadios() {
        const similarityMethodRadios = document.querySelectorAll('input[name="similarity-method"]');
        const descriptionElement = document.getElementById('similarity-method-description');

        if (similarityMethodRadios.length === 0) return;

        // Set initial description
        this.updateSimilarityMethodDescription();

        // Add event listeners
        similarityMethodRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                this.updateSimilarityMethodDescription();
                if (this.state.lastBuiltTree) {
                    this.scheduleTreeRefresh();
                }
            });
        });
    },

    /**
     * Update similarity method description text
     */
    updateSimilarityMethodDescription() {
        const selectedMethod = document.querySelector('input[name="similarity-method"]:checked')?.value;
        const descriptionElement = document.getElementById('similarity-method-description');
        
        if (descriptionElement) {
            if (selectedMethod === 'literal') {
                descriptionElement.textContent = 'Direct skill overlap - produces larger trees, use higher thresholds';
            } else {
                descriptionElement.textContent = 'Weighted analysis with advanced analytics';
            }
        }
    },

    /**
     * Update slider display values
     */
    updateSliderDisplay(sliderId, displayId) {
        const slider = document.getElementById(sliderId);
        const display = document.getElementById(displayId);
        
        if (slider && display) {
            let value = slider.value;
            if (sliderId === 'similarity-threshold') {
                value = (parseFloat(value) * 100).toFixed(0) + '%';
            }
            display.textContent = value;
        }
    },

    /**
     * Initialize organizational filters
     */
    async initializeFilters() {
        const filterIds = ['division-filter', 'business-unit-filter', 'location-filter', 'region-filter'];
        
        // Add change listeners
        filterIds.forEach(filterId => {
            const filterElement = document.getElementById(filterId);
            if (filterElement) {
                filterElement.addEventListener('change', () => {
                    if (this.state.lastBuiltTree) {
                        this.scheduleTreeRefresh();
                    }
                });
            }
        });

        // Populate filter options from API
        try {
            console.log('🔧 Loading organizational filter data...');
            if (window.SkillEngine && window.SkillEngine.ApiClient) {
                console.log('✅ ApiClient is available, fetching organizational data...');
                const orgData = await window.SkillEngine.ApiClient.getOrganizationalData();
                console.log('📊 Organizational data response:', orgData);
                if (orgData.success) {
                    console.log('✅ Success! Populating filter options...');
                    this.populateFilterOptions(orgData.data);
                } else {
                    console.warn('⚠️ API returned success=false:', orgData);
                }
            } else {
                console.warn('⚠️ ApiClient not available:', {
                    SkillEngine: !!window.SkillEngine,
                    ApiClient: !!window.SkillEngine?.ApiClient
                });
            }
        } catch (error) {
            console.error('❌ Error loading organizational filter data:', error);
        }
    },

    /**
     * Populate filter dropdown options
     */
    populateFilterOptions(data) {
        console.log('🔧 Populating filter options with data:', data);
        const filterMappings = {
            'division-filter': data.divisions || [],
            'business-unit-filter': data.business_units || [],
            'location-filter': data.locations || [],
            'region-filter': data.regions || []
        };
        console.log('🔧 Filter mappings:', filterMappings);

        Object.entries(filterMappings).forEach(([filterId, options]) => {
            const filterElement = document.getElementById(filterId);
            if (filterElement && Array.isArray(options)) {
                // Clear existing options (except "All" option)
                const allOptionText = filterElement.querySelector('option[value=""]')?.textContent || 'All';
                filterElement.innerHTML = '';
                
                // Re-add "All" option
                const allOption = document.createElement('option');
                allOption.value = '';
                allOption.textContent = allOptionText;
                filterElement.appendChild(allOption);

                // Add new options
                options.forEach(option => {
                    const optionElement = document.createElement('option');
                    optionElement.value = option;
                    optionElement.textContent = option;
                    filterElement.appendChild(optionElement);
                });
                
                console.log(`✅ Populated ${filterId} with ${options.length} options:`, options.slice(0, 5));
            } else {
                console.warn(`⚠️ Could not populate ${filterId}:`, {
                    elementExists: !!filterElement,
                    isArray: Array.isArray(options),
                    optionsLength: options?.length
                });
            }
        });
    },

    /**
     * Initialize build tree button
     */
    initializeBuildButton() {
        const buildButton = document.getElementById('build-pathway-tree');
        if (buildButton) {
            buildButton.addEventListener('click', () => {
                this.buildCareerPathwayTree();
            });
        }
    },

    /**
     * Schedule tree refresh with debouncing
     */
    scheduleTreeRefresh() {
        clearTimeout(this.refreshTimeout);
        this.refreshTimeout = setTimeout(() => {
            this.buildCareerPathwayTree();
        }, 500);
    },

    /**
     * Get current tree parameters
     */
    getCurrentParameters() {
        const similarity = parseFloat(document.getElementById('similarity-threshold')?.value || 0.2);
        const depth = parseInt(document.getElementById('depth-limit')?.value || 3);
        const maxResults = parseInt(document.getElementById('max-results')?.value || 6);
        
        // Get similarity method from radio buttons
        const similarityMethod = document.querySelector('input[name="similarity-method"]:checked')?.value || 'enhanced';
        
        const filters = {};
        ['division-filter', 'business-unit-filter', 'location-filter', 'region-filter'].forEach(filterId => {
            const element = document.getElementById(filterId);
            if (element && element.value) {
                const paramName = filterId.replace('-filter', '').replace('-', '_');
                filters[paramName] = element.value;
            }
        });

        return { similarity, depth, maxResults, similarityMethod, filters };
    },

    /**
     * Build career pathway tree
     */
    async buildCareerPathwayTree() {
        const controller = SkillEngine.CareerPathwaysController;
        if (!controller || controller.state.selectedJobs.size === 0) {
            console.warn('No jobs selected for tree building');
            return;
        }

        const jobIds = Array.from(controller.state.selectedJobs.keys());
        await this.buildTree(jobIds);
    },

    /**
     * Build tree with given job IDs
     */
    async buildTree(jobIds) {
        if (!jobIds || jobIds.length === 0) {
            console.warn('No job IDs provided for tree building');
            return;
        }

        try {
            const params = this.getCurrentParameters();
            
            // Calculate estimated duration based on query complexity
            const estimatedDuration = this.calculateEstimatedDuration(params);
            
            // Start progress tracking with real timing
            this.showLoadingState(estimatedDuration);
            
            const queryParams = new URLSearchParams({
                jobs: jobIds.join(','),
                similarity: params.similarity,
                depth: params.depth,
                max_results: params.maxResults,
                similarity_method: params.similarityMethod,
                ...params.filters
            });

            // Track API call timing
            const apiStartTime = Date.now();
            const response = await fetch(`/api/d3-tree-data?${queryParams}`);
            const apiEndTime = Date.now();
            const actualApiDuration = apiEndTime - apiStartTime;
            
            // Store timing for future estimates
            this.updateTimingHistory(params, actualApiDuration);
            
            const data = await response.json();

            if (data.success && data.tree) {
                // Complete progress and render tree
                this.completeProgress();
                await this.renderTree(data.tree);
                this.state.lastBuiltTree = data.tree;
                this.state.lastBuiltParameters = params;
            } else {
                throw new Error(data.error || 'Failed to build tree');
            }

        } catch (error) {
            console.error('❌ Error building tree:', error);
            this.showErrorState(error.message);
        } finally {
            this.hideLoadingState();
        }
    },

    /**
     * Render D3 tree visualization
     */
    async renderTree(treeData) {
        
        // Store tree data
        this.state.treeData = treeData;
        
        // Clear existing tree
        const container = d3.select('#tree-container');
        container.selectAll('*').remove();
        
        // Hide empty state
        const emptyState = document.getElementById('tree-empty-state');
        if (emptyState) {
            emptyState.style.display = 'none';
        }

        // Get container dimensions
        const containerElement = document.getElementById('tree-container');
        const containerRect = containerElement.getBoundingClientRect();
        
        this.state.width = Math.max(800, containerRect.width);
        this.state.height = Math.max(600, containerRect.height);
        


        // Create SVG
        this.state.svg = container
            .append('svg')
            .attr('width', this.state.width)
            .attr('height', this.state.height)
            .style('background', '#f8f9fa');

        this.state.g = this.state.svg.append('g');

        // Initialize tree interactions (pan, zoom, navigation)
        if (window.SkillEngine?.TreeInteractions) {
            SkillEngine.TreeInteractions.init(this.state.svg, containerElement);
        } else {
            console.warn('⚠️ TreeInteractions module not available');
        }

        // Initialize tree control buttons
        this.initializeTreeControls();

        // Create tree layout - Updated to match old_tree.html approach
        this.state.tree = d3.tree()
            .nodeSize([this.config.nodeWidth, this.config.nodeHeight])
            .separation(this.getNodeSeparation.bind(this));

        this.state.root = d3.hierarchy(treeData);
        this.state.pathwayRoot = this.state.root; // Store for other functions
        
        // Set initial positions for transitions (D3 will recompute actual positions)
        // Note: In D3 trees, x = vertical position, y = horizontal position
        // Start from origin - let D3 tree layout determine natural positions
        this.state.root.x0 = 0;  
        this.state.root.y0 = 0;   
        


        // Collapse children initially (except root)
        if (this.state.root.children) {
            this.state.root.children.forEach(this.collapseNode.bind(this));
        }

        // Update tree display
        this.updateTree(this.state.root);

        // Initial tree positioning will be handled by updateTree() centering


    },

    /**
     * Initialize tree control buttons
     */
    initializeTreeControls() {
        // Expand All button
        const expandBtn = document.getElementById('expand-all-btn');
        if (expandBtn) {
            expandBtn.addEventListener('click', () => {

                this.expandAllNodes();
            });
        }

        // Collapse All button
        const collapseBtn = document.getElementById('collapse-all-btn');
        if (collapseBtn) {
            collapseBtn.addEventListener('click', () => {

                this.collapseAllNodes();
            });
        }

        // Fullscreen button
        const fullscreenBtn = document.getElementById('fullscreen-btn');
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', () => {

                this.enterFullscreen();
            });
        }


    },

    /**
     * Get node separation for tree layout - Updated to match old_tree.html
     */
    getNodeSeparation(a, b) {
        // With nodeSize(), separation values can be simpler and more predictable
        const isDirectRelation = a.parent === b.parent;
        return isDirectRelation ? 1.0 : 1.5;  // Siblings vs cousins (from old version)
    },

    /**
     * Collapse a node and its children
     */
    collapseNode(d) {
        if (d.children) {
            d._children = d.children;
            d._children.forEach(this.collapseNode.bind(this));
            d.children = null;
        }
    },

    /**
     * Toggle node expansion/collapse - Updated to track last clicked node
     */
    toggleNode(event, d) {
        // Track last clicked node for highlighting (from old_tree.html)
        this.state.lastClickedNode = d;
        
        if (d.children) {
            d._children = d.children;
            d.children = null;
        } else {
            d.children = d._children;
            d._children = null;
        }
        this.updateTree(d);
        
        // Update breadcrumb trail
        this.updateBreadcrumbTrail(d);
    },

    /**
     * Update tree visualization
     */
    updateTree(source) {
        
        // Compute the new tree layout
        const treeData = this.state.tree(this.state.root);
        const nodes = treeData.descendants();
        const links = treeData.descendants().slice(1);
        
        // Let D3 compute natural tree positions without manual offset manipulation
        // Centering will be handled by the zoom/pan transform system

        // Note: Tree positioning is now handled by zoom/pan interactions
        // No need for manual offsets since we have proper zoom/pan controls

        // Update node positions
        nodes.forEach((d, i) => {
            d.id = d.id || ++this.state.i;
        });

        // Create nodes
        const node = this.state.g.selectAll('.node')
            .data(nodes, d => d.id);

        // Enter new nodes
        const nodeEnter = node.enter().append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${source.y0},${source.x0})`)
            .style('cursor', 'pointer')
            .on('click', this.toggleNode.bind(this));

        // Add circles for nodes - Updated to use variable sizing and highlighting
        nodeEnter.append('circle')
            .attr('class', 'pathway-node-circle')
            .attr('r', d => this.getNodeSize(d.data))
            .style('fill', d => this.getNodeColor(d))
            .style('stroke', d => this.isLastClickedNode(d) ? '#fbbf24' : '#333') // Highlight last clicked
            .style('stroke-width', d => this.isLastClickedNode(d) ? '4px' : '2px') // Thicker stroke for highlight
            .style('filter', d => this.isLastClickedNode(d) ? 'drop-shadow(0 0 8px #fbbf24)' : 'none') // Glow effect for selected
            .style('cursor', 'pointer');

        // Add expand/collapse indicator for nodes with hidden children (from old_tree.html)
        nodeEnter.append('text')
            .attr('class', 'pathway-node-indicator')
            .attr('text-anchor', 'middle')
            .attr('dy', '0.35em')  // Center vertically in the circle
            .style('font-family', 'monospace')
            .style('font-size', '12px')
            .style('font-weight', 'bold')
            .style('fill', '#fff')
            .style('cursor', 'pointer')
            .style('pointer-events', 'none')  // Let clicks pass through to the node
            .text(d => {
                if (d._children) return '►';  // Right arrow for collapsed nodes
                if (d.children) return '▼';   // Down arrow for expanded nodes  
                return '';                    // No arrow for leaf nodes
            });

        // Add labels for the nodes - Updated to match old_tree.html styling
        nodeEnter.append('text')
            .attr('dy', '1.8em')
            .attr('x', 0)
            .attr('text-anchor', 'middle')
            .text(d => {
                let displayName = d.data.display_name_compact || d.data.name || 'Unknown';
                // Add similarity percentage directly to similar job names (from old version)
                if (d.data.type === 'similar_job' && d.data.similarity_score > 0) {
                    displayName += ` (${Math.round(d.data.similarity_score * 100)}%)`;
                }
                return displayName;
            })
            .style('font-family', 'Source Sans Pro, sans-serif')
            .style('font-size', '11px')
            .style('fill', '#374151')
            .style('cursor', 'pointer')
            .call(this.wrapText(this.config.textWrapWidth)); // Use wrapText with 180px width

        // Update existing nodes
        const nodeUpdate = nodeEnter.merge(node);

        nodeUpdate.transition()
            .duration(this.config.duration)
            .attr('transform', d => `translate(${d.y},${d.x})`);

        // Update node colors and highlighting
        nodeUpdate.select('circle')
            .style('fill', d => this.getNodeColor(d))
            .style('stroke', d => this.isLastClickedNode(d) ? '#fbbf24' : '#333') // Update highlight
            .style('stroke-width', d => this.isLastClickedNode(d) ? '4px' : '2px') // Update stroke width
            .style('filter', d => this.isLastClickedNode(d) ? 'drop-shadow(0 0 8px #fbbf24)' : 'none'); // Update glow

        // Update expand/collapse indicators
        nodeUpdate.select('.pathway-node-indicator')
            .text(d => {
                if (d._children) return '►';  // Right arrow for collapsed nodes
                if (d.children) return '▼';   // Down arrow for expanded nodes  
                return '';                    // No arrow for leaf nodes
            });

        // Remove exiting nodes
        const nodeExit = node.exit().transition()
            .duration(this.config.duration)
            .attr('transform', d => `translate(${source.y},${source.x})`)
            .remove();

        nodeExit.select('circle')
            .attr('r', 0);

        nodeExit.select('text')
            .style('fill-opacity', 0);

        // Create links
        const link = this.state.g.selectAll('.link')
            .data(links, d => d.id);

        // Enter new links
        const linkEnter = link.enter().insert('path', 'g')
            .attr('class', 'link')
            .attr('d', d => {
                const o = { x: source.x0, y: source.y0 };
                return this.diagonal(o, o);
            })
            .style('fill', 'none')
            .style('stroke', '#ccc')
            .style('stroke-width', 2);

        // Update existing links
        const linkUpdate = linkEnter.merge(link);

        linkUpdate.transition()
            .duration(this.config.duration)
            .attr('d', d => this.diagonal(d, d.parent));

        // Remove exiting links
        link.exit().transition()
            .duration(this.config.duration)
            .attr('d', d => {
                const o = { x: source.x, y: source.y };
                return this.diagonal(o, o);
            })
            .remove();

        // Store old positions for transition
        nodes.forEach(d => {
            d.x0 = d.x;
            d.y0 = d.y;
        });
        
        // Auto-center the tree on initial render using zoom/pan transform
        if (source === this.state.root) {
            // Use a small delay to ensure DOM is fully updated
            setTimeout(() => {
                // Trigger automatic centering via the interactions module
                if (window.SkillEngine?.TreeInteractions) {
                    SkillEngine.TreeInteractions.fitToView();
                }
            }, 100);
        }
    },

    /**
     * Create diagonal path for links
     */
    diagonal(s, d) {
        return `M ${s.y} ${s.x}
                C ${(s.y + d.y) / 2} ${s.x},
                  ${(s.y + d.y) / 2} ${d.x},
                  ${d.y} ${d.x}`;
    },

    /**
     * Get node color based on type and similarity score (from old_tree.html)
     */
    getNodeColor(node) {
        const data = node.data;
        
        // Root/starting jobs always get a distinct colour
        if (data.type === 'starting_job' || data.type === 'root') {
            return '#1e40af'; // Blue for starting jobs (distinct from similarity colours)
        }
        
        // For similar jobs, use similarity-based colouring with inline calculation for performance
        if (data.type === 'similar_job' && data.similarity_score !== undefined) {
            const similarity = data.similarity_score;
            if (similarity >= 0.8) return '#16a34a'; // Green for high (80%+)
            else if (similarity >= 0.6) return '#ca8a04'; // Yellow for good (60%+)
            else if (similarity >= 0.4) return '#ea580c'; // Orange for fair (40%+)
            else if (similarity >= 0.2) return '#dc2626'; // Red for low (20%+)
            else return '#6b7280'; // Gray for very low (<20%)
        }
        
        // Fallback for other types
        return '#6b7280'; // Gray for other types
    },

    /**
     * Get node size based on data (from old_tree.html)
     */
    getNodeSize(data) {
        if (data.type === 'starting_job' || data.type === 'root') {
            return 8; // Larger for starting jobs
        } else if (data.similarity_score && data.similarity_score > 0.6) {
            return 7; // Larger for high similarity
        } else {
            return 6; // Standard size
        }
    },

    /**
     * Check if node is the last clicked node (from old_tree.html)
     */
    isLastClickedNode(d) {
        return this.state.lastClickedNode && this.state.lastClickedNode.data.id === d.data.id;
    },

    /**
     * Wrap text for better readability (from old_tree.html)
     */
    wrapText(text, width) {
        const self = this;
        return function() {
            const text = d3.select(this);
            const textContent = text.text();
            
            // Safety check: if no text content, skip wrapping
            if (!textContent || textContent.trim() === '') {
                return;
            }
            
            const words = textContent.split(/\s+/).reverse();
            let word;
            let line = [];
            let lineNumber = 0;
            const lineHeight = 1.1; // ems
            const y = text.attr("y");
            const dy = parseFloat(text.attr("dy")) || 0;
            let tspan = text.text(null).append("tspan").attr("x", 0).attr("y", y).attr("dy", dy + "em");
            
            while (word = words.pop()) {
                line.push(word);
                tspan.text(line.join(" "));
                if (tspan.node().getComputedTextLength() > width) {
                    line.pop();
                    tspan.text(line.join(" "));
                    line = [word];
                    tspan = text.append("tspan").attr("x", 0).attr("y", y).attr("dy", ++lineNumber * lineHeight + dy + "em").text(word);
                }
            }
        };
    },

    /**
     * Truncate text to fit in node
     */
    truncateText(text, maxLength) {
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },

    /**
     * Center the tree in viewport - Delegate to interactions module
     */
    centerTree() {
        // Delegate to TreeInteractions module which handles zoom/pan properly
        if (window.SkillEngine && window.SkillEngine.TreeInteractions) {
            window.SkillEngine.TreeInteractions.centerTree();
        }
    },

    /**
     * Update breadcrumb trail when node is clicked
     */
    updateBreadcrumbTrail(targetNode) {
        // Get path from root to target
        const pathNodes = [];
        let current = targetNode;
        
        while (current) {
            pathNodes.unshift(current);
            current = current.parent;
        }
        
        // Update breadcrumb UI - delegate to Skills Analysis module
        if (SkillEngine.SkillsAnalysis) {
            SkillEngine.SkillsAnalysis.updateBreadcrumbs(pathNodes);
        }
    },

    /**
     * Calculate estimated duration based on query complexity
     */
    calculateEstimatedDuration(params) {
        // Base duration in milliseconds
        let estimatedMs = 2000; // 2 seconds base
        
        // Factors that increase complexity
        const depth = parseInt(params.depth) || 3;
        const maxResults = parseInt(params.maxResults) || 6;
        const similarity = parseFloat(params.similarity) || 0.2;
        const isLiteral = params.similarityMethod === 'literal';
        
        // Depth factor (exponential growth)
        estimatedMs += (depth - 1) * 1500; // +1.5s per depth level
        
        // Results factor
        estimatedMs += Math.max(0, (maxResults - 6)) * 200; // +200ms per extra result
        
        // Similarity threshold factor (lower = more results = slower)
        const similarityFactor = 1 - similarity; // 0.8 similarity = 0.2 factor
        estimatedMs += similarityFactor * 3000; // Up to +3s for very low thresholds
        
        // Literal method is typically slower
        if (isLiteral) {
            estimatedMs *= 1.5;
        }
        
        // Check timing history for more accurate estimates
        const historyKey = this.getTimingKey(params);
        if (this.state.timingHistory && this.state.timingHistory[historyKey]) {
            const history = this.state.timingHistory[historyKey];
            const avgTime = history.reduce((sum, time) => sum + time, 0) / history.length;
            // Blend estimated with historical data (70% history, 30% calculation)
            estimatedMs = (avgTime * 0.7) + (estimatedMs * 0.3);
        }
        
        // Cap between 1-30 seconds
        return Math.max(1000, Math.min(30000, estimatedMs));
    },

    /**
     * Generate timing key for caching estimates
     */
    getTimingKey(params) {
        return `${params.depth}_${params.maxResults}_${params.similarityMethod}_${Math.floor(params.similarity * 10)}`;
    },

    /**
     * Update timing history for better future estimates
     */
    updateTimingHistory(params, actualDuration) {
        if (!this.state.timingHistory) {
            this.state.timingHistory = {};
        }
        
        const key = this.getTimingKey(params);
        if (!this.state.timingHistory[key]) {
            this.state.timingHistory[key] = [];
        }
        
        // Keep last 5 measurements for rolling average
        this.state.timingHistory[key].push(actualDuration);
        if (this.state.timingHistory[key].length > 5) {
            this.state.timingHistory[key].shift();
        }
        
        console.log(`📊 Timing updated: ${key} = ${actualDuration}ms (avg: ${Math.round(this.state.timingHistory[key].reduce((a,b) => a+b, 0) / this.state.timingHistory[key].length)}ms)`);
    },

    /**
     * Complete progress animation
     */
    completeProgress() {
        if (this.state.progressComplete) return;
        
        this.state.progressComplete = true;
        
        // Stop the dots animation
        this.stopDotsAnimation();
        
        // Quickly animate to 100%
        const progressBar = document.getElementById('career-progress-bar');
        const progressText = document.getElementById('career-progress-text');
        
        if (progressBar && progressText) {
            progressBar.style.width = '100%';
            progressText.textContent = '100%';
            
            // Complete all remaining steps
            for (let i = this.state.currentStep; i <= 5; i++) {
                const stepElement = document.getElementById(`step-${i}`);
                if (stepElement) {
                    stepElement.style.color = '#059669';
                    stepElement.style.fontWeight = '500';
                    stepElement.style.animation = ''; // Remove any pulse animation
                    const icon = stepElement.querySelector('div');
                    if (icon) {
                        icon.style.background = '#10b981';
                        icon.style.animation = ''; // Remove any pulse animation
                        icon.innerHTML = '<span style="color: white; font-size: 8px; font-weight: bold; display: flex; align-items: center; justify-content: center; width: 100%; height: 100%;">✓</span>';
                    }
                }
            }
            
            // Update subtitle
            const subtitle = document.querySelector('div[style*="font-size: 0.875rem"][style*="color: #6b7280"]');
            if (subtitle) {
                subtitle.textContent = 'Career pathway tree ready!';
                subtitle.style.color = '#059669'; // green-600
            }
        }
    },

    /**
     * Show loading state with progress bar
     */
    showLoadingState(estimatedDuration = 5000) {
        const container = document.getElementById('tree-container');
        if (container) {
            container.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; height: 16rem; padding: 2rem;">
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1rem; padding: 2rem; max-width: 400px; margin: 0 auto;">
                        <div style="font-size: 1.125rem; font-weight: 600; color: #1f2937; text-align: center; margin-bottom: 0.5rem;">Building Career Pathway Tree</div>
                        <div style="font-size: 0.875rem; color: #6b7280; text-align: center; margin-bottom: 1rem;">Analysing job profiles and skill relationships...</div>
                        
                        <div style="width: 100%; background: #e5e7eb; border-radius: 8px; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1); position: relative;">
                            <div id="career-progress-bar" style="height: 8px; background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%); border-radius: 8px; transition: width 0.3s ease-out; width: 0%; position: relative; overflow: hidden;"></div>
                        </div>
                        <div id="career-progress-text" style="font-size: 0.875rem; color: #2563eb; font-weight: 500; margin-top: 0.5rem; text-align: center;">0%</div>
                        
                        <div style="display: flex; flex-direction: column; gap: 0.25rem; width: 100%; margin-top: 1rem;">
                            <div id="step-1" style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.75rem; color: #2563eb; font-weight: 500; padding: 0.25rem 0; transition: color 0.3s ease;">
                                <div style="width: 12px; height: 12px; border-radius: 50%; background: #3b82f6; flex-shrink: 0;"></div>
                                <span>Validating job profiles...</span>
                            </div>
                            <div id="step-2" style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.75rem; color: #6b7280; padding: 0.25rem 0; transition: color 0.3s ease;">
                                <div style="width: 12px; height: 12px; border-radius: 50%; background: #d1d5db; flex-shrink: 0;"></div>
                                <span>Calculating skill similarities...</span>
                            </div>
                            <div id="step-3" style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.75rem; color: #6b7280; padding: 0.25rem 0; transition: color 0.3s ease;">
                                <div style="width: 12px; height: 12px; border-radius: 50%; background: #d1d5db; flex-shrink: 0;"></div>
                                <span>Building pathway relationships...</span>
                            </div>
                            <div id="step-4" style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.75rem; color: #6b7280; padding: 0.25rem 0; transition: color 0.3s ease;">
                                <div style="width: 12px; height: 12px; border-radius: 50%; background: #d1d5db; flex-shrink: 0;"></div>
                                <span>Optimising tree structure...</span>
                            </div>
                            <div id="step-5" style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.75rem; color: #6b7280; padding: 0.25rem 0; transition: color 0.3s ease;">
                                <div style="width: 12px; height: 12px; border-radius: 50%; background: #d1d5db; flex-shrink: 0;"></div>
                                <span>Finalising visualisation...</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Start the real progress simulation
        this.startProgressSimulation(estimatedDuration);
    },

    /**
     * Start progress simulation based on estimated duration
     */
    startProgressSimulation(estimatedDuration) {
        this.state.progressStartTime = Date.now();
        this.state.estimatedDuration = estimatedDuration;
        this.state.currentProgress = 0;
        this.state.currentStep = 1;
        this.state.progressComplete = false;
        
        // Define progress milestones with timing based on estimated duration
        // Never go to 100% - stop at 95% until API completes
        const stepDuration = estimatedDuration / 5;
        this.state.progressSteps = [
            { step: 1, progress: 15, duration: stepDuration * 0.8, text: 'Validating job profiles...' },
            { step: 2, progress: 35, duration: stepDuration * 1.0, text: 'Calculating skill similarities...' },
            { step: 3, progress: 65, duration: stepDuration * 1.2, text: 'Building pathway relationships...' },
            { step: 4, progress: 85, duration: stepDuration * 1.0, text: 'Optimising tree structure...' },
            { step: 5, progress: 95, duration: stepDuration * 1.5, text: 'Finalising visualisation...' } // Stop at 95%
        ];
        
        console.log(`🚀 Starting progress with estimated duration: ${estimatedDuration}ms`);
        this.updateProgress();
    },

    /**
     * Update progress bar and steps
     */
    updateProgress() {
        if (this.state.progressComplete) {
            return; // Stop updating if already completed
        }
        
        if (!this.state.progressSteps || this.state.currentStep > this.state.progressSteps.length) {
            // We've reached the end of our estimated steps but API hasn't returned yet
            // Hold at 95% and show waiting message
            this.showWaitingState();
            return;
        }
        
        const currentStepData = this.state.progressSteps[this.state.currentStep - 1];
        const progressBar = document.getElementById('career-progress-bar');
        const progressText = document.getElementById('career-progress-text');
        
        if (!progressBar || !progressText) return;
        
        // Calculate smooth progress within current step
        const stepStartTime = this.state.progressStartTime + 
            this.state.progressSteps.slice(0, this.state.currentStep - 1)
                .reduce((total, step) => total + step.duration, 0);
        
        const elapsed = Date.now() - stepStartTime;
        const stepProgress = Math.min(elapsed / currentStepData.duration, 1);
        
        // Calculate overall progress
        const previousProgress = this.state.currentStep > 1 ? 
            this.state.progressSteps[this.state.currentStep - 2].progress : 0;
        const targetProgress = currentStepData.progress;
        const currentProgress = previousProgress + (targetProgress - previousProgress) * stepProgress;
        
        // Never exceed 95% until API completes
        const cappedProgress = Math.min(currentProgress, 95);
        
        // Update UI
        progressBar.style.width = `${cappedProgress}%`;
        progressText.textContent = `${Math.round(cappedProgress)}%`;
        
        // Update step states
        this.updateStepStates(currentStepData, stepProgress);
        
        // Continue animation or move to next step
        if (stepProgress >= 1) {
            // Mark current step as completed (except the last one if we're at 95%)
            const stepElement = document.getElementById(`step-${this.state.currentStep}`);
            if (stepElement && (currentProgress < 95 || this.state.currentStep < 5)) {
                stepElement.style.color = '#059669'; // green-600
                stepElement.style.fontWeight = '500';
                const icon = stepElement.querySelector('div');
                if (icon) {
                    icon.style.background = '#10b981'; // green-500
                    icon.innerHTML = '<span style="color: white; font-size: 8px; font-weight: bold; display: flex; align-items: center; justify-content: center; width: 100%; height: 100%;">✓</span>';
                }
            }
            
            this.state.currentStep++;
            
            // Start next step or wait at 95%
            if (this.state.currentStep <= this.state.progressSteps.length) {
                const nextStepElement = document.getElementById(`step-${this.state.currentStep}`);
                if (nextStepElement) {
                    nextStepElement.style.color = '#2563eb'; // blue-600
                    nextStepElement.style.fontWeight = '500';
                    const nextIcon = nextStepElement.querySelector('div');
                    if (nextIcon) {
                        nextIcon.style.background = '#3b82f6'; // blue-500
                    }
                }
                setTimeout(() => this.updateProgress(), 50);
            } else {
                // We've reached the end of our steps, show waiting state
                this.showWaitingState();
            }
        } else {
            setTimeout(() => this.updateProgress(), 50);
        }
    },

    /**
     * Show waiting state when we've reached 95% but API is still processing
     */
    showWaitingState() {
        if (this.state.waitingStateShown) return;
        
        this.state.waitingStateShown = true;
        
        const subtitle = document.querySelector('div[style*="font-size: 0.875rem"][style*="color: #6b7280"]');
        if (subtitle) {
            subtitle.innerHTML = 'Processing large dataset, almost ready<span id="loading-dots">...</span>';
            subtitle.style.color = '#f59e0b'; // amber-500
        }
        
        // Add a subtle pulse animation to the last step
        const lastStepElement = document.getElementById('step-5');
        if (lastStepElement) {
            lastStepElement.style.color = '#f59e0b'; // amber-600
            const icon = lastStepElement.querySelector('div');
            if (icon) {
                icon.style.background = '#f59e0b'; // amber-500
                icon.style.animation = 'pulse 1.5s infinite';
            }
        }
        
        // Start the three dots animation
        this.startDotsAnimation();
        
        console.log('⏳ Reached 95%, waiting for API response...');
    },

    /**
     * Animate the three dots loading indicator
     */
    startDotsAnimation() {
        const dotsElement = document.getElementById('loading-dots');
        if (!dotsElement) return;
        
        let dotCount = 0;
        
        this.state.dotsInterval = setInterval(() => {
            dotCount = (dotCount + 1) % 4; // Cycle through 0, 1, 2, 3
            
            switch (dotCount) {
                case 0:
                    dotsElement.textContent = '';
                    break;
                case 1:
                    dotsElement.textContent = '.';
                    break;
                case 2:
                    dotsElement.textContent = '..';
                    break;
                case 3:
                    dotsElement.textContent = '...';
                    break;
            }
        }, 500); // Change every 500ms for a nice rhythm
    },

    /**
     * Stop the dots animation
     */
    stopDotsAnimation() {
        if (this.state.dotsInterval) {
            clearInterval(this.state.dotsInterval);
            this.state.dotsInterval = null;
        }
    },

    /**
     * Update step visual states
     */
    updateStepStates(currentStepData, stepProgress) {
        // Update subtitle with current step text
        const subtitle = document.querySelector('div[style*="font-size: 0.875rem"][style*="color: #6b7280"]');
        if (subtitle && stepProgress > 0.2 && !this.state.waitingStateShown) {
            subtitle.textContent = currentStepData.text;
        }
    },

    /**
     * Hide loading state
     */
    hideLoadingState() {
        // Stop any running animations
        this.stopDotsAnimation();
        
        // Reset state flags
        this.state.progressComplete = false;
        this.state.waitingStateShown = false;
        this.state.currentStep = 1;
        
        // Loading state is cleared when new tree is rendered
    },

    /**
     * Show error state
     */
    showErrorState(message) {
        const container = document.getElementById('tree-container');
        if (container) {
            container.innerHTML = `
                <div class="flex items-center justify-center h-64">
                    <div class="text-center">
                        <div class="text-red-500 text-lg mb-2">⚠️ Error Building Tree</div>
                        <div class="text-gray-600">${message}</div>
                    </div>
                </div>
            `;
        }
    },

    /**
     * Expand all nodes in the tree
     */
    expandAllNodes() {
        if (!this.state.root) return;
        
        this.state.root.descendants().forEach(d => {
            if (d._children) {
                d.children = d._children;
                d._children = null;
            }
        });
        
        this.updateTree(this.state.root);
    },

    /**
     * Collapse all nodes back to just the root node
     */
    collapseAllNodes() {
        if (!this.state.root) return;
        

        
        // Recursively collapse all descendants
        this.collapseAllDescendants(this.state.root);
        
        this.updateTree(this.state.root);
    },

    /**
     * Recursively collapse all descendants of a node
     */
    collapseAllDescendants(node) {
        if (node.children) {
            // First, recursively collapse all children's descendants
            node.children.forEach(child => {
                this.collapseAllDescendants(child);
            });
            
            // Then collapse this node's children
            node._children = node.children;
            node.children = null;
        }
    },

    /**
     * Enter fullscreen mode for tree visualization
     */
    enterFullscreen() {
        const overlay = document.getElementById('fullscreen-tree-overlay');
        const fullscreenContainer = document.getElementById('fullscreen-tree-container');
        
        if (!overlay || !fullscreenContainer) {
            console.warn('⚠️ Fullscreen overlay elements not found');
            return;
        }

        // Show overlay
        overlay.classList.remove('hidden');
        
        // Clone the current SVG to fullscreen container
        const currentSvg = this.state.svg.node();
        if (currentSvg) {
            const clonedSvg = currentSvg.cloneNode(true);
            
            // Clear fullscreen container and add cloned SVG
            fullscreenContainer.innerHTML = '';
            fullscreenContainer.appendChild(clonedSvg);
            
            // Resize cloned SVG for fullscreen
            const fullscreenRect = fullscreenContainer.getBoundingClientRect();
            clonedSvg.setAttribute('width', fullscreenRect.width);
            clonedSvg.setAttribute('height', fullscreenRect.height);
            

        }

        // Setup fullscreen controls
        this.setupFullscreenControls();
    },

    /**
     * Setup fullscreen control buttons
     */
    setupFullscreenControls() {
        // Close fullscreen button
        const closeBtn = document.getElementById('close-fullscreen-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.exitFullscreen());
        }

        // Fullscreen expand all button
        const fullscreenExpandBtn = document.getElementById('fullscreen-expand-all-btn');
        if (fullscreenExpandBtn) {
            fullscreenExpandBtn.addEventListener('click', () => {
                this.expandAllNodes();
                // Re-clone the updated tree to fullscreen
                setTimeout(() => this.updateFullscreenTree(), 100);
            });
        }

        // Fullscreen collapse all button
        const fullscreenCollapseBtn = document.getElementById('fullscreen-collapse-all-btn');
        if (fullscreenCollapseBtn) {
            fullscreenCollapseBtn.addEventListener('click', () => {
                this.collapseAllNodes();
                // Re-clone the updated tree to fullscreen
                setTimeout(() => this.updateFullscreenTree(), 100);
            });
        }

        // Escape key to close fullscreen
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                this.exitFullscreen();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
    },

    /**
     * Update fullscreen tree after changes
     */
    updateFullscreenTree() {
        const fullscreenContainer = document.getElementById('fullscreen-tree-container');
        const currentSvg = this.state.svg.node();
        
        if (fullscreenContainer && currentSvg) {
            const clonedSvg = currentSvg.cloneNode(true);
            fullscreenContainer.innerHTML = '';
            fullscreenContainer.appendChild(clonedSvg);
            
            const fullscreenRect = fullscreenContainer.getBoundingClientRect();
            clonedSvg.setAttribute('width', fullscreenRect.width);
            clonedSvg.setAttribute('height', fullscreenRect.height);
        }
    },

    /**
     * Exit fullscreen mode
     */
    exitFullscreen() {
        const overlay = document.getElementById('fullscreen-tree-overlay');
        if (overlay) {
            overlay.classList.add('hidden');

        }
    }
};

console.log('✅ Tree Visualization module loaded');
