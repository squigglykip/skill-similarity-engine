/**
 * Job Explorer UI Module
 * Handles UI interactions, collapsible sections, and visual state management
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.JobExplorerUI = {
    /**
     * Initialize UI functionality
     */
    init() {
        console.log('🎨 Job Explorer UI module loaded');
        this.initializeCollapsibleSections();
        this.scheduleDelayedDebug();
        this.enforceContainerIntegrity();
    },

    /**
     * Initialize collapsible sections functionality
     */
    initializeCollapsibleSections() {
        // Run debug check when DOM is loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                console.log('🔧 DEBUG: DOM Content Loaded - running collapsible sections debug');
                this.debugCollapsibleSections();
            });
        } else {
            // DOM already loaded
            this.debugCollapsibleSections();
        }
    },

    /**
     * Schedule delayed debug check to catch dynamic content
     */
    scheduleDelayedDebug() {
        // Also run debug check after a short delay to catch any dynamic content
        setTimeout(() => {
            console.log('🔧 DEBUG: Delayed check (3s) - running collapsible sections debug');
            this.debugCollapsibleSections();
            
            // Debug job-profile-content visibility
            this.debugContainerVisibility();
        }, 3000);
    },

    /**
     * Toggle skill section (collapsible functionality)
     */
    toggleSkillSection(sectionId) {
        console.log(`🔧 DEBUG: toggleSkillSection called with sectionId: "${sectionId}"`);
        
        const content = document.getElementById(sectionId + '-content');
        const chevron = document.getElementById(sectionId + '-chevron');
        
        console.log(`🔧 DEBUG: Elements found:`, {
            content: content ? 'EXISTS' : 'NULL',
            chevron: chevron ? 'EXISTS' : 'NULL',
            contentId: sectionId + '-content',
            chevronId: sectionId + '-chevron'
        });
        
        if (!content || !chevron) {
            console.error(`❌ Elements not found for section: ${sectionId}`);
            console.error(`Missing elements:`, {
                content: !content ? 'MISSING' : 'found',
                chevron: !chevron ? 'MISSING' : 'found'
            });
            return;
        }
        
        const isHidden = content.classList.contains('hidden');
        console.log(`🔧 DEBUG: Section "${sectionId}" current state: ${isHidden ? 'HIDDEN' : 'VISIBLE'}`);
        
        if (isHidden) {
            this.expandSection(sectionId, content, chevron);
        } else {
            this.collapseSection(sectionId, content, chevron);
        }
    },

    /**
     * Expand a collapsible section
     */
    expandSection(sectionId, content, chevron) {
        console.log(`📖 Opening section: ${sectionId}`);
        content.classList.remove('hidden');
        chevron.classList.remove('-rotate-90');
        
        // Add smooth animation by temporarily setting opacity and height
        content.style.opacity = '0';
        content.style.maxHeight = '0px';
        content.style.overflow = 'hidden';
        content.style.transition = 'opacity 300ms ease-out, max-height 300ms ease-out';
        
        // Trigger animation on next frame
        requestAnimationFrame(() => {
            content.style.opacity = '1';
            content.style.maxHeight = '2000px'; // Large enough value
            
            // Clean up styles after animation
            setTimeout(() => {
                content.style.cssText = '';
            }, 300);
        });
        
        console.log(`✅ Successfully opened section: ${sectionId}`);
    },

    /**
     * Collapse a collapsible section
     */
    collapseSection(sectionId, content, chevron) {
        console.log(`📚 Closing section: ${sectionId}`);
        content.style.transition = 'opacity 300ms ease-in, max-height 300ms ease-in';
        content.style.opacity = '0';
        content.style.maxHeight = '0px';
        content.style.overflow = 'hidden';
        
        setTimeout(() => {
            content.classList.add('hidden');
            content.style.cssText = '';
        }, 300);
        
        chevron.classList.add('-rotate-90');
        
        console.log(`✅ Successfully closed section: ${sectionId}`);
    },

    /**
     * Debug function to check all collapsible sections
     */
    debugCollapsibleSections() {
        console.log(`🔧 DEBUG: Checking all collapsible sections...`);
        
        const sections = ['defining-skills', 'rare-skills', 'specialised-skills'];
        sections.forEach(sectionId => {
            const content = document.getElementById(sectionId + '-content');
            const chevron = document.getElementById(sectionId + '-chevron');
            const button = document.querySelector(`[onclick*="toggleSkillSection('${sectionId}')"]`);
            
            console.log(`🔧 Section "${sectionId}":`, {
                content: content ? 'EXISTS' : 'MISSING',
                chevron: chevron ? 'EXISTS' : 'MISSING',
                button: button ? 'EXISTS' : 'MISSING',
                isHidden: content ? content.classList.contains('hidden') : 'N/A'
            });
            
            if (content) {
                console.log(`  - Content classes:`, content.className);
            }
            if (button) {
                console.log(`  - Button onclick:`, button.getAttribute('onclick'));
            }
        });
    },

    /**
     * Debug container visibility
     */
    debugContainerVisibility() {
        const jobProfileContent = document.getElementById('job-profile-content');
        const welcomeState = document.getElementById('welcome-state');
        const mainLayout = document.querySelector('.grid.grid-cols-1.lg\\:grid-cols-4');
        const sidebar = document.querySelector('.lg\\:col-span-1');
        const mainContent = document.querySelector('.lg\\:col-span-3');
        const jobFamilySection = document.getElementById('job-family-content');
        
        console.log(`🔧 DEBUG: Complete layout analysis:`, {
            mainLayout: {
                exists: !!mainLayout,
                className: mainLayout ? mainLayout.className : 'N/A',
                childrenCount: mainLayout ? mainLayout.children.length : 'N/A'
            },
            sidebar: {
                exists: !!sidebar,
                className: sidebar ? sidebar.className : 'N/A',
                childrenCount: sidebar ? sidebar.children.length : 'N/A'
            },
            mainContent: {
                exists: !!mainContent,
                className: mainContent ? mainContent.className : 'N/A',
                childrenCount: mainContent ? mainContent.children.length : 'N/A'
            },
            jobProfileContent: {
                exists: !!jobProfileContent,
                isHidden: jobProfileContent ? jobProfileContent.classList.contains('hidden') : 'N/A',
                className: jobProfileContent ? jobProfileContent.className : 'N/A',
                parent: jobProfileContent ? jobProfileContent.parentElement?.className : 'N/A'
            },
            welcomeState: {
                exists: !!welcomeState,
                isHidden: welcomeState ? welcomeState.classList.contains('hidden') : 'N/A',
                className: welcomeState ? welcomeState.className : 'N/A',
                parent: welcomeState ? welcomeState.parentElement?.className : 'N/A'
            },
            jobFamilySection: {
                exists: !!jobFamilySection,
                className: jobFamilySection ? jobFamilySection.className : 'N/A',
                parent: jobFamilySection ? jobFamilySection.parentElement?.className : 'N/A',
                grandParent: jobFamilySection ? jobFamilySection.parentElement?.parentElement?.className : 'N/A'
            }
        });
        
        // Check for any elements that might be outside the main container
        const allCards = document.querySelectorAll('.bg-white.rounded-lg.shadow-lg');
        console.log(`🔧 DEBUG: Found ${allCards.length} card elements`);
        allCards.forEach((card, index) => {
            const rect = card.getBoundingClientRect();
            const isJobFamily = card.querySelector('#job-family-content') !== null;
            
            console.log(`Card ${index}${isJobFamily ? ' (JOB FAMILY)' : ''}:`, {
                className: card.className,
                id: card.id,
                innerHTML: isJobFamily ? 'Job Family Section' : card.innerHTML.substring(0, 50) + '...',
                position: {
                    top: rect.top,
                    left: rect.left,
                    width: rect.width,
                    height: rect.height
                },
                parent: card.parentElement?.className,
                parentId: card.parentElement?.id,
                grandParent: card.parentElement?.parentElement?.className,
                grandParentId: card.parentElement?.parentElement?.id,
                isVisible: rect.width > 0 && rect.height > 0,
                isJobFamilyCard: isJobFamily
            });
            
            // Special focus on Card 6 (the problematic one)
            if (index === 6) {
                console.log(`🎯 CARD 6 DEEP DIVE:`, {
                    element: card,
                    parentChain: this.getParentChain(card),
                    isInsideJobProfile: card.closest('#job-profile-content') !== null,
                    isInsideMainContent: card.closest('.lg\\:col-span-3') !== null
                });
            }
        });
    },



    /**
     * Get parent chain for debugging
     */
    getParentChain(element) {
        const chain = [];
        let current = element.parentElement;
        while (current && chain.length < 5) {
            chain.push({
                tagName: current.tagName,
                className: current.className,
                id: current.id
            });
            current = current.parentElement;
        }
        return chain;
    },

    /**
     * Reset all collapsible sections to closed state
     */
    resetCollapsibleSections() {
        const sections = ['defining-skills', 'rare-skills', 'specialised-skills'];
        sections.forEach(sectionId => {
            const content = document.getElementById(sectionId + '-content');
            const chevron = document.getElementById(sectionId + '-chevron');
            
            if (content && chevron) {
                content.classList.add('hidden');
                chevron.classList.add('-rotate-90');
                content.style.cssText = ''; // Clear any inline styles
            }
        });
        
        console.log('🔄 All collapsible sections reset');
    },

    /**
     * Enforce container integrity and fix misplaced elements
     */
    enforceContainerIntegrity() {
        // Check for any cards that might be outside their proper containers
        const jobProfileContent = document.getElementById('job-profile-content');
        const jobFamilyCard = document.getElementById('job-family-intelligence-card');
        
        if (jobFamilyCard && jobProfileContent) {
            // Ensure the job family card is inside the job profile content
            if (!jobProfileContent.contains(jobFamilyCard)) {
                console.warn('🚨 Job Family card found outside its container - moving it back');
                // Move it to the end of job-profile-content
                jobProfileContent.appendChild(jobFamilyCard);
            }
        }
        
        // Check all cards with the standard styling
        const allCards = document.querySelectorAll('.bg-white.rounded-lg.shadow-lg');
        allCards.forEach((card, index) => {
            const isJobFamily = card.textContent.includes('Job Family & Clustering Intelligence');
            const isExpertLevel = card.textContent.includes('Expert-Level Requirements');
            
            if ((isJobFamily || isExpertLevel) && jobProfileContent) {
                if (!jobProfileContent.contains(card)) {
                    console.warn(`🚨 Misplaced card found (${isJobFamily ? 'Job Family' : 'Expert Level'}) - moving to proper container`);
                    jobProfileContent.appendChild(card);
                }
            }
        });
        
        console.log('✅ Container integrity check completed');
    }
};

// Make toggleSkillSection globally available for onclick handlers
window.toggleSkillSection = function(sectionId) {
    SkillEngine.JobExplorerUI.toggleSkillSection(sectionId);
};

console.log('✅ Job Explorer UI module loaded');
