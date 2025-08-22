/**
 * Tree Visualization - Interactions Module
 * Handles pan, zoom, drag, and navigation controls for D3 tree
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.TreeInteractions = {
    // State
    state: {
        zoom: null,
        currentTransform: null,
        isPanning: false,
        minZoom: 0.1,
        maxZoom: 5,
        zoomStep: 0.2
    },

    /**
     * Initialize tree interactions
     */
    init(svg, container) {
        this.svg = svg;
        this.container = container;
        this.setupZoomBehavior();
        this.setupNavigationControls();
        this.setupInstructionsOverlay();
        
        console.log('🖱️ Tree interactions initialized');
    },

    /**
     * Setup D3 zoom and pan behavior
     */
    setupZoomBehavior() {
        // Create zoom behavior
        this.state.zoom = d3.zoom()
            .scaleExtent([this.state.minZoom, this.state.maxZoom])
            .on('start', (event) => this.onZoomStart(event))
            .on('zoom', (event) => this.onZoom(event))
            .on('end', (event) => this.onZoomEnd(event));

        // Apply zoom behavior to SVG
        this.svg.call(this.state.zoom);

        // Store initial transform
        this.state.currentTransform = d3.zoomIdentity;
    },

    /**
     * Handle zoom start
     */
    onZoomStart(event) {
        if (event.sourceEvent && event.sourceEvent.type === 'mousedown') {
            this.state.isPanning = true;
            this.container.classList.add('panning');
        }
    },

    /**
     * Handle zoom/pan events
     */
    onZoom(event) {
        // Store current transform
        this.state.currentTransform = event.transform;

        // Apply transform to the main tree group
        const treeGroup = this.svg.select('g');
        if (!treeGroup.empty()) {
            treeGroup.attr('transform', event.transform);
        }

        // Update instructions visibility based on activity
        this.updateInstructionsVisibility();
    },

    /**
     * Handle zoom end
     */
    onZoomEnd(event) {
        if (this.state.isPanning) {
            this.state.isPanning = false;
            this.container.classList.remove('panning');
        }
    },

    /**
     * Setup navigation control buttons
     */
    setupNavigationControls() {
        // Center tree button
        const centerBtn = document.getElementById('center-tree-btn');
        if (centerBtn) {
            centerBtn.addEventListener('click', () => this.centerTree());
        }

        // Fit to view button
        const fitBtn = document.getElementById('fit-tree-btn');
        if (fitBtn) {
            fitBtn.addEventListener('click', () => this.fitToView());
        }

        // Zoom in button
        const zoomInBtn = document.getElementById('zoom-in-btn');
        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', () => this.zoomIn());
        }

        // Zoom out button
        const zoomOutBtn = document.getElementById('zoom-out-btn');
        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', () => this.zoomOut());
        }
    },

    /**
     * Center the tree in the viewport
     */
    centerTree() {
        console.log('🎯 Starting centerTree process...');
        
        if (!this.svg) {
            console.warn('⚠️ No SVG available for centerTree');
            return;
        }

        // Use SVG dimensions for proper centering
        const svgElement = this.svg.node();
        const svgWidth = parseFloat(svgElement.getAttribute('width')) || this.container.getBoundingClientRect().width;
        const svgHeight = parseFloat(svgElement.getAttribute('height')) || this.container.getBoundingClientRect().height;
        const centerX = svgWidth / 2;
        const centerY = svgHeight / 2;

        // Get current scale
        const currentScale = this.state.currentTransform.k;

        console.log('🎯 CenterTree debug:', {
            svgDimensions: {
                width: svgWidth,
                height: svgHeight,
                centerX,
                centerY
            },
            currentScale,
            currentTransform: {
                x: this.state.currentTransform.x,
                y: this.state.currentTransform.y,
                k: this.state.currentTransform.k
            }
        });

        // Create transform to center
        const transform = d3.zoomIdentity
            .translate(centerX, centerY)
            .scale(currentScale);

        console.log('🔄 Applying centerTree transform:', {
            translateX: transform.x,
            translateY: transform.y,
            scale: transform.k
        });

        // Animate to center
        this.svg.transition()
            .duration(750)
            .call(this.state.zoom.transform, transform);

        console.log('🎯 Tree centered successfully');
    },

    /**
     * Fit tree to view
     */
    fitToView() {
        console.log('📏 Starting fitToView process...');
        
        if (!this.svg) {
            console.warn('⚠️ No SVG available for fitToView');
            return;
        }

        const treeGroup = this.svg.select('g');
        if (treeGroup.empty()) {
            console.warn('⚠️ No tree group found for fitToView');
            return;
        }

        try {
            // Get bounding box of tree content
            const bbox = treeGroup.node().getBBox();
            console.log('📦 Tree bounding box:', bbox);
            
            if (bbox.width === 0 || bbox.height === 0) {
                console.warn('⚠️ Tree has no content to fit');
                return;
            }

            // Get SVG dimensions for proper centering calculations
            const svgElement = this.svg.node();
            const svgWidth = parseFloat(svgElement.getAttribute('width')) || this.container.getBoundingClientRect().width;
            const svgHeight = parseFloat(svgElement.getAttribute('height')) || this.container.getBoundingClientRect().height;
            const padding = 40; // Padding around the tree
            
            console.log('📐 SVG dimensions for fitToView:', {
                svgWidth,
                svgHeight,
                containerWidth: this.container.getBoundingClientRect().width,
                containerHeight: this.container.getBoundingClientRect().height
            });

            // Calculate scale to fit
            const scaleX = (svgWidth - padding * 2) / bbox.width;
            const scaleY = (svgHeight - padding * 2) / bbox.height;
            const scale = Math.min(scaleX, scaleY, this.state.maxZoom);

            // Calculate translation to center
            const translateX = svgWidth / 2 - (bbox.x + bbox.width / 2) * scale;
            const translateY = svgHeight / 2 - (bbox.y + bbox.height / 2) * scale;

            console.log('🧮 FitToView calculations:', {
                scaleX,
                scaleY,
                finalScale: scale,
                translateX,
                translateY,
                bboxCenter: {
                    x: bbox.x + bbox.width / 2,
                    y: bbox.y + bbox.height / 2
                },
                svgCenter: {
                    x: svgWidth / 2,
                    y: svgHeight / 2
                }
            });

            // Create and apply transform
            const transform = d3.zoomIdentity
                .translate(translateX, translateY)
                .scale(scale);

            console.log('🔄 Applying transform:', {
                translateX: transform.x,
                translateY: transform.y,
                scale: transform.k
            });

            this.svg.transition()
                .duration(750)
                .call(this.state.zoom.transform, transform);

            console.log('📏 Tree fitted to view successfully');
        } catch (error) {
            console.error('❌ Error fitting tree to view:', error);
            // Fallback to center
            this.centerTree();
        }
    },

    /**
     * Zoom in
     */
    zoomIn() {
        if (!this.svg) return;

        const newScale = Math.min(
            this.state.currentTransform.k + this.state.zoomStep,
            this.state.maxZoom
        );

        this.zoomToScale(newScale);
        console.log(`🔍+ Zoomed in to ${(newScale * 100).toFixed(0)}%`);
    },

    /**
     * Zoom out
     */
    zoomOut() {
        if (!this.svg) return;

        const newScale = Math.max(
            this.state.currentTransform.k - this.state.zoomStep,
            this.state.minZoom
        );

        this.zoomToScale(newScale);
        console.log(`🔍- Zoomed out to ${(newScale * 100).toFixed(0)}%`);
    },

    /**
     * Zoom to specific scale
     */
    zoomToScale(scale) {
        const containerRect = this.container.getBoundingClientRect();
        const centerX = containerRect.width / 2;
        const centerY = containerRect.height / 2;

        // Calculate new translation to keep center point stable
        const currentCenterX = (centerX - this.state.currentTransform.x) / this.state.currentTransform.k;
        const currentCenterY = (centerY - this.state.currentTransform.y) / this.state.currentTransform.k;

        const newTranslateX = centerX - currentCenterX * scale;
        const newTranslateY = centerY - currentCenterY * scale;

        const transform = d3.zoomIdentity
            .translate(newTranslateX, newTranslateY)
            .scale(scale);

        this.svg.transition()
            .duration(300)
            .call(this.state.zoom.transform, transform);
    },

    /**
     * Setup instructions overlay
     */
    setupInstructionsOverlay() {
        const instructions = document.getElementById('tree-instructions');
        if (!instructions) return;

        // Show instructions briefly when tree is first loaded
        setTimeout(() => {
            instructions.style.opacity = '1';
            setTimeout(() => {
                instructions.style.opacity = '0';
            }, 3000);
        }, 1000);
    },

    /**
     * Update instructions visibility based on interaction
     */
    updateInstructionsVisibility() {
        const instructions = document.getElementById('tree-instructions');
        if (!instructions) return;

        if (this.state.isPanning) {
            instructions.style.opacity = '1';
        }
    },

    /**
     * Get current zoom level as percentage
     */
    getZoomPercentage() {
        return Math.round(this.state.currentTransform.k * 100);
    },

    /**
     * Reset zoom and pan to initial state
     */
    reset() {
        if (!this.svg) return;

        this.svg.transition()
            .duration(750)
            .call(this.state.zoom.transform, d3.zoomIdentity);

        console.log('🔄 Tree view reset');
    },

    /**
     * Enable/disable interactions
     */
    setEnabled(enabled) {
        if (!this.svg) return;

        if (enabled) {
            this.svg.call(this.state.zoom);
        } else {
            this.svg.on('.zoom', null);
        }
    },

    /**
     * Get current transform for external use
     */
    getCurrentTransform() {
        return this.state.currentTransform;
    }
};
