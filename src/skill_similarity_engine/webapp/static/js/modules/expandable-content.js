/**
 * Expandable Content Module
 * Handles expandable/collapsible content sections with smooth animations
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.ExpandableContent = {
    // State management
    state: {
        expandedSections: new Set(),
        animationDuration: 300
    },

    /**
     * Initialize expandable content functionality
     */
    init() {
        this.bindExpandableEvents();
        console.log('✅ Expandable Content module loaded');
    },

    /**
     * Bind click events to expandable triggers
     */
    bindExpandableEvents() {
        // Use event delegation for dynamically added content
        document.addEventListener('click', (event) => {
            const trigger = event.target.closest('[data-expandable-trigger]');
            if (trigger) {
                event.preventDefault();
                this.toggleSection(trigger);
            }
        });
    },

    /**
     * Toggle an expandable section
     */
    toggleSection(trigger) {
        const sectionId = trigger.getAttribute('data-expandable-trigger');
        const targetSection = document.querySelector(`[data-expandable-content="${sectionId}"]`);
        
        if (!targetSection) {
            console.warn(`Expandable section not found: ${sectionId}`);
            return;
        }

        const isExpanded = this.state.expandedSections.has(sectionId);
        
        if (isExpanded) {
            this.collapseSection(sectionId, trigger, targetSection);
        } else {
            this.expandSection(sectionId, trigger, targetSection);
        }
    },

    /**
     * Expand a section
     */
    expandSection(sectionId, trigger, targetSection) {
        // Add to expanded state
        this.state.expandedSections.add(sectionId);
        
        // Update trigger text and styling
        this.updateTriggerState(trigger, true);
        
        // Show the hidden content with animation
        this.animateExpand(targetSection);
        
        // Update ARIA attributes for accessibility
        trigger.setAttribute('aria-expanded', 'true');
        targetSection.setAttribute('aria-hidden', 'false');
    },

    /**
     * Collapse a section
     */
    collapseSection(sectionId, trigger, targetSection) {
        // Remove from expanded state
        this.state.expandedSections.delete(sectionId);
        
        // Update trigger text and styling
        this.updateTriggerState(trigger, false);
        
        // Hide the content with animation
        this.animateCollapse(targetSection);
        
        // Update ARIA attributes for accessibility
        trigger.setAttribute('aria-expanded', 'false');
        targetSection.setAttribute('aria-hidden', 'true');
    },

    /**
     * Update trigger button state and text
     */
    updateTriggerState(trigger, isExpanded) {
        const expandText = trigger.getAttribute('data-expand-text') || 'Show more';
        const collapseText = trigger.getAttribute('data-collapse-text') || 'Show less';
        
        // Update text content
        const textElement = trigger.querySelector('.expandable-trigger-text') || trigger;
        textElement.textContent = isExpanded ? collapseText : expandText;
        
        // Update CSS classes
        trigger.classList.toggle('expanded', isExpanded);
        
        // Update icon if present
        const icon = trigger.querySelector('.expandable-trigger-icon');
        if (icon) {
            icon.classList.toggle('rotated', isExpanded);
        }
    },

    /**
     * Animate content expansion
     */
    animateExpand(element) {
        // Set initial state
        element.style.display = 'block';
        element.style.opacity = '0';
        element.style.maxHeight = '0';
        element.style.overflow = 'hidden';
        element.style.transition = `all ${this.state.animationDuration}ms ease-out`;
        
        // Force reflow
        element.offsetHeight;
        
        // Get natural height
        const naturalHeight = element.scrollHeight;
        
        // Animate to natural state
        requestAnimationFrame(() => {
            element.style.opacity = '1';
            element.style.maxHeight = naturalHeight + 'px';
        });
        
        // Clean up after animation
        setTimeout(() => {
            element.style.maxHeight = 'none';
            element.style.overflow = 'visible';
        }, this.state.animationDuration);
    },

    /**
     * Animate content collapse
     */
    animateCollapse(element) {
        // Set current height
        const currentHeight = element.scrollHeight;
        element.style.maxHeight = currentHeight + 'px';
        element.style.overflow = 'hidden';
        element.style.transition = `all ${this.state.animationDuration}ms ease-in`;
        
        // Force reflow
        element.offsetHeight;
        
        // Animate to collapsed state
        requestAnimationFrame(() => {
            element.style.opacity = '0';
            element.style.maxHeight = '0';
        });
        
        // Hide element after animation
        setTimeout(() => {
            element.style.display = 'none';
            element.style.transition = '';
        }, this.state.animationDuration);
    },

    /**
     * Create expandable content structure
     * Utility method for dynamically creating expandable sections
     */
    createExpandableSection(config) {
        const {
            sectionId,
            visibleItems = [],
            hiddenItems = [],
            expandText = `+${hiddenItems.length} more`,
            collapseText = 'Show less',
            containerClass = '',
            itemRenderer = null
        } = config;

        // Create container
        const container = document.createElement('div');
        container.className = `expandable-section ${containerClass}`;

        // Create visible content
        const visibleContent = document.createElement('div');
        visibleContent.className = 'expandable-visible-content';
        
        visibleItems.forEach(item => {
            const itemElement = itemRenderer ? itemRenderer(item) : this.defaultItemRenderer(item);
            visibleContent.appendChild(itemElement);
        });

        // Create hidden content
        const hiddenContent = document.createElement('div');
        hiddenContent.className = 'expandable-hidden-content';
        hiddenContent.setAttribute('data-expandable-content', sectionId);
        hiddenContent.setAttribute('aria-hidden', 'true');
        hiddenContent.style.display = 'none';
        
        hiddenItems.forEach(item => {
            const itemElement = itemRenderer ? itemRenderer(item) : this.defaultItemRenderer(item);
            hiddenContent.appendChild(itemElement);
        });

        // Create trigger button
        const trigger = document.createElement('button');
        trigger.className = 'expandable-trigger';
        trigger.setAttribute('data-expandable-trigger', sectionId);
        trigger.setAttribute('data-expand-text', expandText);
        trigger.setAttribute('data-collapse-text', collapseText);
        trigger.setAttribute('aria-expanded', 'false');
        trigger.innerHTML = `
            <span class="expandable-trigger-text">${expandText}</span>
            <span class="expandable-trigger-icon">▼</span>
        `;

        // Assemble the section
        container.appendChild(visibleContent);
        container.appendChild(hiddenContent);
        container.appendChild(trigger);

        return container;
    },

    /**
     * Default item renderer for skills
     */
    defaultItemRenderer(item) {
        const div = document.createElement('div');
        div.className = 'flex items-center justify-between';
        div.innerHTML = `
            <div>• ${item.name || item}</div>
            <div class="flex space-x-1">
                <span class="px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-700">
                    ${item.type || 'Specialized Skill'}
                </span>
            </div>
        `;
        return div;
    },

    /**
     * Check if a section is expanded
     */
    isExpanded(sectionId) {
        return this.state.expandedSections.has(sectionId);
    },

    /**
     * Expand all sections
     */
    expandAll() {
        document.querySelectorAll('[data-expandable-trigger]').forEach(trigger => {
            const sectionId = trigger.getAttribute('data-expandable-trigger');
            if (!this.state.expandedSections.has(sectionId)) {
                this.toggleSection(trigger);
            }
        });
    },

    /**
     * Collapse all sections
     */
    collapseAll() {
        document.querySelectorAll('[data-expandable-trigger]').forEach(trigger => {
            const sectionId = trigger.getAttribute('data-expandable-trigger');
            if (this.state.expandedSections.has(sectionId)) {
                this.toggleSection(trigger);
            }
        });
    },

    /**
     * Reset module state
     */
    reset() {
        this.state.expandedSections.clear();
        
        // Reset all triggers and content
        document.querySelectorAll('[data-expandable-trigger]').forEach(trigger => {
            trigger.classList.remove('expanded');
            trigger.setAttribute('aria-expanded', 'false');
            
            const expandText = trigger.getAttribute('data-expand-text') || 'Show more';
            const textElement = trigger.querySelector('.expandable-trigger-text') || trigger;
            textElement.textContent = expandText;
            
            const icon = trigger.querySelector('.expandable-trigger-icon');
            if (icon) {
                icon.classList.remove('rotated');
            }
        });
        
        document.querySelectorAll('[data-expandable-content]').forEach(content => {
            content.style.display = 'none';
            content.setAttribute('aria-hidden', 'true');
            content.style.transition = '';
            content.style.maxHeight = '';
            content.style.opacity = '';
            content.style.overflow = '';
        });
    }
};

console.log('✅ Expandable Content module loaded');
