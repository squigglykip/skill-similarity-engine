/**
 * Career Pathways Export Controller
 * Main orchestrator for CSV export functionality on the Career Pathways page
 * 
 * Handles:
 * - Export button initialization
 * - State validation
 * - Coordination between data extraction and CSV generation
 * - User feedback and error handling
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.CareerPathwaysExportController = {
    /**
     * Initialize the export functionality
     */
    init() {
        console.log('🚀 Initializing Career Pathways Export Controller...');
        this.initializeExportButton();
        console.log('✅ Career Pathways Export Controller initialized');
    },

    /**
     * Initialize the export CSV button
     */
    initializeExportButton() {
        // Check if we're on the career pathways page
        if (!document.getElementById('pathway-job-search')) {
            return; // Not on career pathways page
        }

        // Find the export button (already in template)
        const exportButton = document.getElementById('export-career-csv-btn');
        
        if (exportButton) {
            exportButton.addEventListener('click', () => this.handleExportClick());
            this.updateExportButtonState();
            console.log('✅ Export button initialized and event listener added');
        } else {
            console.warn('⚠️ Export button not found in template');
        }
    },

    /**
     * Handle export button click
     */
    async handleExportClick() {
        try {
            console.log('📊 Starting Career Pathways CSV export...');
            
            // Validate that we have minimum required data
            const validationResult = this.validateExportRequirements();
            if (!validationResult.isValid) {
                alert(validationResult.message);
                return;
            }

            // Show loading state
            this.setExportButtonLoading(true);

            // Extract all available data
            const exportData = await this.gatherExportData();

            // Generate CSV content
            const csvContent = SkillEngine.CareerPathwaysCSVGenerator.generateCSV(exportData);

            // Download CSV file
            this.downloadCSV(csvContent, this.generateFileName(exportData));

            console.log('✅ Career Pathways CSV export completed successfully');

        } catch (error) {
            console.error('❌ Error exporting Career Pathways CSV:', error);
            alert('Error exporting CSV: ' + error.message);
        } finally {
            this.setExportButtonLoading(false);
        }
    },

    /**
     * Validate that we have minimum required data for export
     */
    validateExportRequirements() {
        const controller = SkillEngine.CareerPathwaysController;
        const treeViz = SkillEngine.TreeVisualization;

        // Check if jobs are selected
        if (!controller?.state?.selectedJobs || controller.state.selectedJobs.size === 0) {
            return {
                isValid: false,
                message: 'Please select at least one job profile before exporting.'
            };
        }

        // Check if tree has been built
        if (!treeViz?.state?.treeData) {
            return {
                isValid: false,
                message: 'Please build the career pathway tree before exporting.'
            };
        }

        return { isValid: true };
    },

    /**
     * Gather all export data from various sources
     */
    async gatherExportData() {
        console.log('🔍 Gathering Career Pathways export data...');

        const exportData = {
            // Metadata
            timestamp: new Date(),
            exportType: this.determineExportType(),

            // Configuration and selections
            selectedJobs: await SkillEngine.CareerPathwaysDataExtractor.extractSelectedJobs(),
            treeConfiguration: SkillEngine.CareerPathwaysDataExtractor.extractTreeConfiguration(),
            organizationalFilters: SkillEngine.CareerPathwaysDataExtractor.extractOrganizationalFilters(),

            // Tree structure and pathways
            treeStructure: SkillEngine.CareerPathwaysDataExtractor.extractTreeStructure(),
            careerPathways: await SkillEngine.CareerPathwaysDataExtractor.extractCareerPathways(),

            // Analysis data (if available)
            skillsAnalysis: SkillEngine.CareerPathwaysDataExtractor.extractSkillsAnalysis(),
            definingSkillsAnalysis: SkillEngine.CareerPathwaysDataExtractor.extractDefiningSkillsAnalysis(),
            workforceContext: SkillEngine.CareerPathwaysDataExtractor.extractWorkforceContext(),
            
            // Progression trail
            careerProgressionTrail: SkillEngine.CareerPathwaysDataExtractor.extractCareerProgressionTrail(),
            
            // Skill gaps analysis will be added after tree structure is available
            skillGapsAnalysis: []
        };

        // Extract critical skill gaps analysis for career transitions
        console.log('🔍 DEEP DIVE: Analyzing skill gaps between career transitions...');
        console.log('🔍 DEEP DIVE: Tree structure data for analysis:', exportData.treeStructure);
        console.log('🔍 DEEP DIVE: Tree structure .data property:', exportData.treeStructure.data);
        
        try {
            console.log('🔍 DEEP DIVE: About to call extractSkillGapsAnalysis with:', exportData.treeStructure.data);
            exportData.skillGapsAnalysis = await SkillEngine.CareerPathwaysDataExtractor.extractSkillGapsAnalysis(exportData.treeStructure.data);
            console.log('✅ DEEP DIVE: Skill gaps analysis completed:', exportData.skillGapsAnalysis.length, 'transitions analyzed');
            console.log('🎯 DEEP DIVE: Final skill gaps data structure:', exportData.skillGapsAnalysis);
            
            if (exportData.skillGapsAnalysis.length > 0) {
                console.log('🎯 DEEP DIVE: First skill gap entry:', exportData.skillGapsAnalysis[0]);
            } else {
                console.warn('⚠️ DEEP DIVE: No skill gaps found - investigating why...');
            }
        } catch (error) {
            console.error('❌ DEEP DIVE: Failed to extract skill gaps analysis:', error);
            console.error('❌ DEEP DIVE: Error stack:', error.stack);
            exportData.skillGapsAnalysis = [];
        }

        console.log('✅ Export data gathered:', exportData);
        return exportData;
    },

    /**
     * Determine the type of export based on current state
     */
    determineExportType() {
        const controller = SkillEngine.CareerPathwaysController;
        const treeViz = SkillEngine.TreeVisualization;

        if (!controller?.state?.selectedJobs || controller.state.selectedJobs.size === 0) {
            return 'No Selection';
        }

        if (!treeViz?.state?.treeData) {
            return 'Jobs Selected Only';
        }

        if (!treeViz?.state?.lastClickedNode) {
            return 'Tree Built';
        }

        return 'Complete Analysis';
    },

    /**
     * Update export button state based on available data
     */
    updateExportButtonState() {
        const exportButton = document.getElementById('export-career-csv-btn');
        if (!exportButton) {
            console.warn('⚠️ Export button not found in DOM');
            return;
        }

        const validation = this.validateExportRequirements();
        
        console.log('🔍 Export button validation result:', {
            isValid: validation.isValid,
            message: validation.message,
            selectedJobsSize: SkillEngine.CareerPathwaysController?.state?.selectedJobs?.size || 0,
            hasTreeData: !!SkillEngine.TreeVisualization?.state?.treeData,
            treeDataType: typeof SkillEngine.TreeVisualization?.state?.treeData
        });
        
        if (validation.isValid) {
            exportButton.disabled = false;
            exportButton.title = 'Export career pathways analysis to CSV';
            exportButton.classList.remove('opacity-50', 'cursor-not-allowed');
            console.log('✅ Export button enabled');
        } else {
            exportButton.disabled = true;
            exportButton.title = validation.message;
            exportButton.classList.add('opacity-50', 'cursor-not-allowed');
            console.log('❌ Export button disabled:', validation.message);
        }
    },

    /**
     * Set loading state for export button
     */
    setExportButtonLoading(isLoading) {
        const exportButton = document.getElementById('export-career-csv-btn');
        if (!exportButton) return;

        if (isLoading) {
            exportButton.disabled = true;
            exportButton.innerHTML = `
                <svg class="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Exporting...
            `;
        } else {
            exportButton.innerHTML = `
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                Export CSV
            `;
            this.updateExportButtonState();
        }
    },

    /**
     * Generate filename for CSV download
     */
    generateFileName(exportData) {
        const timestamp = exportData.timestamp.toISOString().slice(0, 19).replace(/[:-]/g, '');
        const jobCount = exportData.selectedJobs?.length || 0;
        const exportType = exportData.exportType.replace(/\s+/g, '_').toLowerCase();
        
        return `career_pathways_analysis_${jobCount}jobs_${exportType}_${timestamp}.csv`;
    },

    /**
     * Download CSV file
     */
    downloadCSV(csvContent, filename) {
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }
    }
};

// Auto-initialize when modules are ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait for other modules to load
    const initWhenReady = () => {
        if (window.SkillEngine?.CareerPathwaysDataExtractor && 
            window.SkillEngine?.CareerPathwaysCSVGenerator) {
            SkillEngine.CareerPathwaysExportController.init();
        } else {
            setTimeout(initWhenReady, 100);
        }
    };
    
    setTimeout(initWhenReady, 500); // Give other modules time to load
});

console.log('✅ Career Pathways Export Controller module loaded');
