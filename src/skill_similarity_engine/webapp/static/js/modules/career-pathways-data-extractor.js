/**
 * Career Pathways Data Extractor
 * Handles extraction of all data from DOM, state, and APIs for CSV export
 * 
 * Extracts:
 * - Selected jobs and configuration
 * - Tree structure and pathways
 * - Skills analysis data
 * - Workforce context information
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.CareerPathwaysDataExtractor = {

    /**
     * Extract selected jobs information
     */
    extractSelectedJobs() {
        const controller = SkillEngine.CareerPathwaysController;
        const selectedJobs = [];

        if (controller?.state?.selectedJobs) {
            controller.state.selectedJobs.forEach((job, jobId) => {
                selectedJobs.push({
                    id: jobId,
                    title: job.title,
                    family: job.family,
                    group: job.group || 'N/A'
                });
            });
        }

        return selectedJobs;
    },

    /**
     * Extract tree configuration parameters
     */
    extractTreeConfiguration() {
        const config = {
            similarityThreshold: 'N/A',
            treeDepth: 'N/A',
            resultsPerLevel: 'N/A',
            similarityMethod: 'N/A'
        };

        // Extract from sliders and controls
        const similaritySlider = document.getElementById('similarity-threshold');
        if (similaritySlider) {
            const value = parseFloat(similaritySlider.value);
            config.similarityThreshold = `${(value * 100).toFixed(0)}%`;
        }

        const depthSlider = document.getElementById('depth-limit');
        if (depthSlider) {
            config.treeDepth = depthSlider.value;
        }

        const maxResultsSlider = document.getElementById('max-results');
        if (maxResultsSlider) {
            config.resultsPerLevel = maxResultsSlider.value;
        }

        const similarityMethodRadio = document.querySelector('input[name="similarity-method"]:checked');
        if (similarityMethodRadio) {
            config.similarityMethod = similarityMethodRadio.value.charAt(0).toUpperCase() + similarityMethodRadio.value.slice(1);
        }

        return config;
    },

    /**
     * Extract organizational filters
     */
    extractOrganizationalFilters() {
        const filters = {
            division: 'All Divisions',
            businessUnit: 'All Business Units',
            location: 'All Locations',
            region: 'All Regions'
        };

        const divisionFilter = document.getElementById('division-filter');
        if (divisionFilter && divisionFilter.value) {
            filters.division = divisionFilter.value;
        }

        const businessUnitFilter = document.getElementById('business-unit-filter');
        if (businessUnitFilter && businessUnitFilter.value) {
            filters.businessUnit = businessUnitFilter.value;
        }

        const locationFilter = document.getElementById('location-filter');
        if (locationFilter && locationFilter.value) {
            filters.location = locationFilter.value;
        }

        const regionFilter = document.getElementById('region-filter');
        if (regionFilter && regionFilter.value) {
            filters.region = regionFilter.value;
        }

        return filters;
    },

    /**
     * Extract tree structure data
     */
    extractTreeStructure() {
        const treeViz = SkillEngine.TreeVisualization;
        const treeNodes = [];

        console.log('🔍 DEEP DIVE: TreeVisualization state:', treeViz?.state);
        console.log('🔍 DEEP DIVE: TreeVisualization treeData:', treeViz?.state?.treeData);

        if (treeViz?.state?.treeData) {
            // Recursively extract tree nodes
            this.extractTreeNodes(treeViz.state.treeData, treeNodes, 0, null);
        }

        const result = {
            totalNodes: treeNodes.length,
            maxDepth: treeNodes.reduce((max, node) => Math.max(max, node.depth), 0),
            nodes: treeNodes,
            // Include raw tree data for skill gaps analysis
            data: treeViz?.state?.treeData || null
        };

        console.log('🔍 DEEP DIVE: Tree structure result:', result);
        return result;
    },

    /**
     * Recursively extract tree nodes
     */
    extractTreeNodes(node, nodesList, depth, parentId) {
        const nodeData = {
            id: node.id || `node_${nodesList.length}`,
            title: node.title || node.name || 'Unknown',
            jobFunction: node.job_function || 'N/A',
            similarity: node.similarity_score ? `${(node.similarity_score * 100).toFixed(1)}%` : 'N/A',
            depth: depth,
            parentId: parentId,
            hasChildren: !!(node.children && node.children.length > 0),
            isExpanded: !node._children, // If _children exists, it means it's collapsed
            nodeType: depth === 0 ? 'Root' : depth === 1 ? 'Direct Connection' : 'Extended Pathway'
        };

        nodesList.push(nodeData);

        // Process children
        if (node.children) {
            node.children.forEach(child => {
                this.extractTreeNodes(child, nodesList, depth + 1, nodeData.id);
            });
        }

        // Also process collapsed children for completeness
        if (node._children) {
            node._children.forEach(child => {
                this.extractTreeNodes(child, nodesList, depth + 1, nodeData.id);
            });
        }
    },

    /**
     * Extract career pathways data (API call for comprehensive data)
     */
    async extractCareerPathways() {
        const controller = SkillEngine.CareerPathwaysController;
        const pathways = [];

        if (!controller?.state?.selectedJobs || controller.state.selectedJobs.size === 0) {
            return pathways;
        }

        try {
            // Get pathways for each selected job
            for (const [jobId, job] of controller.state.selectedJobs) {
                const response = await fetch(`/api/career-pathways-distribution/${jobId}?limit=50`);
                if (response.ok) {
                    const data = await response.json();
                    if (Array.isArray(data)) {
                        data.forEach(pathway => {
                            pathways.push({
                                fromJob: job.title,
                                fromJobId: jobId,
                                toJob: pathway.job_title || 'Unknown',
                                toJobId: pathway.job_id || 'Unknown',
                                jobFunction: pathway.job_function || 'N/A',
                                similarity: pathway.similarity_score ? `${(pathway.similarity_score * 100).toFixed(1)}%` : 'N/A',
                                enhancedSimilarity: pathway.enhanced_similarity_score ? `${(pathway.enhanced_similarity_score * 100).toFixed(1)}%` : 'N/A'
                            });
                        });
                    }
                }
            }
        } catch (error) {
            console.warn('Failed to fetch comprehensive pathways data:', error);
        }

        return pathways;
    },

    /**
     * Extract skills analysis data (if available)
     */
    extractSkillsAnalysis() {
        const analysis = {
            isAvailable: false,
            skillsMatched: 'N/A',
            skillsUnique: 'N/A',
            definingSkillsMatch: 'N/A',
            roleSimilarity: 'N/A',
            selectedPathway: null
        };

        // Check if skills analysis is visible and populated
        const skillsMatchedElement = document.getElementById('skills-matched-count');
        const skillsDevelopElement = document.getElementById('skills-develop-count');
        const definingMatchElement = document.getElementById('defining-skills-match');
        const similarityElement = document.getElementById('transition-difficulty');

        if (skillsMatchedElement && skillsMatchedElement.textContent !== '—') {
            analysis.isAvailable = true;
            analysis.skillsMatched = skillsMatchedElement.textContent.trim();
            analysis.skillsUnique = skillsDevelopElement ? skillsDevelopElement.textContent.trim() : 'N/A';
            analysis.definingSkillsMatch = definingMatchElement ? definingMatchElement.textContent.trim() : 'N/A';
            analysis.roleSimilarity = similarityElement ? similarityElement.textContent.trim() : 'N/A';
        }

        return analysis;
    },

    /**
     * Extract defining skills analysis (if available)
     */
    extractDefiningSkillsAnalysis() {
        const analysis = {
            isAvailable: false,
            sharedSkills: 'N/A',
            uniqueToTarget: 'N/A',
            skillsBreakdown: []
        };

        // Check if defining skills section is visible
        const definingSkillsSection = document.getElementById('defining-skills-section');
        if (definingSkillsSection && !definingSkillsSection.classList.contains('hidden')) {
            analysis.isAvailable = true;

            // Extract summary counts
            const sharedCountElement = document.getElementById('defining-matched-count');
            const uniqueCountElement = document.getElementById('defining-develop-count');

            if (sharedCountElement) {
                analysis.sharedSkills = sharedCountElement.textContent.trim();
            }
            if (uniqueCountElement) {
                analysis.uniqueToTarget = uniqueCountElement.textContent.trim();
            }

            // Extract detailed breakdown if available
            const skillsBreakdownContainer = document.getElementById('skills-breakdown-content');
            if (skillsBreakdownContainer) {
                const skillElements = skillsBreakdownContainer.querySelectorAll('[data-skill-name]');
                skillElements.forEach(element => {
                    analysis.skillsBreakdown.push({
                        skillName: element.dataset.skillName || element.textContent.trim(),
                        category: element.dataset.category || 'N/A',
                        status: element.dataset.status || 'N/A'
                    });
                });
            }
        }

        return analysis;
    },

    /**
     * Extract workforce context data (if available)
     */
    extractWorkforceContext() {
        const context = {
            isAvailable: false,
            totalPositions: 'N/A',
            divisionsRepresented: 'N/A',
            locationsSpread: 'N/A',
            organizationalDistribution: []
        };

        // Check if workforce metrics are populated
        const totalPositionsElement = document.getElementById('total-positions');
        const divisionsElement = document.getElementById('divisions-represented');
        const locationsElement = document.getElementById('locations-spread');

        if (totalPositionsElement && totalPositionsElement.textContent !== '—') {
            context.isAvailable = true;
            context.totalPositions = totalPositionsElement.textContent.trim();
            context.divisionsRepresented = divisionsElement ? divisionsElement.textContent.trim() : 'N/A';
            context.locationsSpread = locationsElement ? locationsElement.textContent.trim() : 'N/A';
        }

        // Extract organizational distribution table
        const workforceTable = document.getElementById('workforce-pathway-table');
        if (workforceTable) {
            const rows = workforceTable.querySelectorAll('tr');
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length === 4 && !cells[0].textContent.includes('Select a career')) {
                    context.organizationalDistribution.push({
                        division: cells[0].textContent.trim(),
                        businessUnit: cells[1].textContent.trim(),
                        location: cells[2].textContent.trim(),
                        totalPositions: cells[3].textContent.trim()
                    });
                }
            });
        }

        return context;
    },

    /**
     * Extract career progression trail (breadcrumb)
     */
    extractCareerProgressionTrail() {
        const trail = {
            isAvailable: false,
            steps: []
        };

        // Extract breadcrumb trail
        const breadcrumbContainer = document.getElementById('career-progression-trail');
        if (breadcrumbContainer) {
            const breadcrumbItems = breadcrumbContainer.querySelectorAll('[data-step]');
            if (breadcrumbItems.length > 0) {
                trail.isAvailable = true;
                breadcrumbItems.forEach((item, index) => {
                    trail.steps.push({
                        stepNumber: index + 1,
                        jobTitle: item.textContent.trim(),
                        isSelected: item.classList.contains('selected') || item.classList.contains('active')
                    });
                });
            }
        }

        return trail;
    },

    /**
     * Extract skills comparison data between source and target jobs
     */
    async extractSkillsComparison(sourceJobId, targetJobId) {
        if (!sourceJobId || !targetJobId) {
            console.warn('⚠️ DEEP DIVE: Missing job IDs for skills comparison:', { sourceJobId, targetJobId });
            return null;
        }

        console.log(`🔗 DEEP DIVE: Fetching skills comparison: ${sourceJobId} → ${targetJobId}`);

        try {
            // Use the correct API endpoint that actually exists
            const url = `/api/skills-analysis/${sourceJobId}/${targetJobId}`;
            console.log('📡 DEEP DIVE: API call URL (CORRECTED):', url);
            
            const response = await fetch(url);
            console.log('📡 DEEP DIVE: Response status:', response.status, response.statusText);
            console.log('📡 DEEP DIVE: Response headers:', [...response.headers.entries()]);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.warn(`⚠️ DEEP DIVE: API response not OK: ${response.status} ${response.statusText}`);
                console.warn(`⚠️ DEEP DIVE: Error response body:`, errorText);
                return null;
            }
            
            const rawData = await response.text();
            console.log('📡 DEEP DIVE: Raw response data:', rawData);
            
            let data;
            try {
                data = JSON.parse(rawData);
            } catch (parseError) {
                console.error('❌ DEEP DIVE: JSON parse error:', parseError);
                return null;
            }
            
            console.log('📡 DEEP DIVE: Parsed API response data:', data);
            console.log('📡 DEEP DIVE: Response structure:');
            console.log('  - success:', data.success);
            console.log('  - skills_matched:', data.skills_matched);
            console.log('  - skills_to_develop:', data.skills_to_develop);
            console.log('  - detailed_skills:', data.detailed_skills);
            console.log('  - transition_difficulty:', data.transition_difficulty);
            
            // Map the skills-analysis API response to our expected format
            const skillsMatched = (data.detailed_skills || []).filter(skill => skill.status === 'matched');
            const skillsUnique = (data.detailed_skills || []).filter(skill => skill.status === 'develop');
            const definingSkillsMatched = skillsMatched.filter(skill => skill.is_defining).length;
            
            // Calculate similarity based on overlap (since this API doesn't provide similarity score)
            const totalSkills = skillsMatched.length + skillsUnique.length;
            const similarity = totalSkills > 0 ? skillsMatched.length / totalSkills : 0;
            
            const result = {
                sourceJob: { id: sourceJobId },
                targetJob: { id: targetJobId },
                skillsMatched: skillsMatched.map(skill => ({
                    skill_name: skill.name,
                    skill_category: skill.category,
                    is_defining: skill.is_defining
                })),
                skillsUnique: skillsUnique.map(skill => ({
                    skill_name: skill.name,
                    skill_category: skill.category,
                    is_defining: skill.is_defining
                })),
                definingSkillsMatch: definingSkillsMatched,
                similarity: similarity,
                transitionDifficulty: data.transition_difficulty
            };
            
            console.log('✅ DEEP DIVE: Processed skills comparison result:', result);
            return result;
        } catch (error) {
            console.error('❌ DEEP DIVE: Failed to extract skills comparison:', error);
            console.error('❌ DEEP DIVE: Error stack:', error.stack);
            return null;
        }
    },

    /**
     * Extract comprehensive skill gaps analysis for career pathway
     * This is critical for understanding what skills need development for each transition
     */
    async extractSkillGapsAnalysis(treeData) {
        console.log('🔍 DEEP DIVE: Starting skill gaps analysis with tree data:', treeData);
        console.log('🔍 DEEP DIVE: Tree data type:', typeof treeData);
        console.log('🔍 DEEP DIVE: Tree data keys:', treeData ? Object.keys(treeData) : 'null');
        
        if (!treeData) {
            console.warn('⚠️ DEEP DIVE: No tree data provided for skill gaps analysis');
            return [];
        }

        // If treeData is an array, use it directly
        // If it's a single node, wrap it in an array
        let rootNodes = Array.isArray(treeData) ? treeData : [treeData];
        console.log('🔍 DEEP DIVE: Root nodes for analysis:', rootNodes.length, rootNodes);
        
        // Let's examine the first root node in detail
        if (rootNodes.length > 0) {
            const firstNode = rootNodes[0];
            console.log('🔍 DEEP DIVE: First root node details:');
            console.log('  - Name:', firstNode.name);
            console.log('  - Job ID:', firstNode.job_id);
            console.log('  - Children count:', firstNode.children ? firstNode.children.length : 0);
            console.log('  - Children:', firstNode.children);
            
            if (firstNode.children && firstNode.children.length > 0) {
                console.log('🔍 DEEP DIVE: First child details:');
                const firstChild = firstNode.children[0];
                console.log('  - Child Name:', firstChild.name);
                console.log('  - Child Job ID:', firstChild.job_id);
                console.log('  - Child object:', firstChild);
            }
        }

        const skillGaps = [];
        
        // Analyze skill gaps for each parent-child relationship in the tree
        const analyzeNode = async (parentNode) => {
            console.log('🔍 Analyzing node:', parentNode?.name || parentNode?.data?.job_title || 'Unknown');
            
            if (!parentNode.children || parentNode.children.length === 0) {
                console.log('📄 No children for node:', parentNode?.name || parentNode?.data?.job_title);
                return;
            }
            
            for (const childNode of parentNode.children) {
                try {
                    const parentJobId = parentNode.job_id || parentNode.data?.job_id;
                    const parentJobTitle = parentNode.name || parentNode.data?.job_title || 'Unknown';
                    const childJobId = childNode.job_id || childNode.data?.job_id;
                    const childJobTitle = childNode.name || childNode.data?.job_title || 'Unknown';
                    
                    console.log(`🔗 Analyzing transition: ${parentJobTitle} → ${childJobTitle}`);
                    console.log(`🔗 Job IDs: ${parentJobId} → ${childJobId}`);
                    
                    const comparison = await this.extractSkillsComparison(parentJobId, childJobId);
                    
                    if (comparison) {
                        console.log('✅ Got skills comparison:', comparison);
                        
                        // Extract detailed skill gaps
                        const gapAnalysis = {
                            transition: {
                                from: {
                                    id: parentJobId,
                                    title: parentJobTitle,
                                    function: parentNode.category || parentNode.data?.job_function || 'Unknown'
                                },
                                to: {
                                    id: childJobId,
                                    title: childJobTitle,
                                    function: childNode.category || childNode.data?.job_function || 'Unknown'
                                }
                            },
                            similarity: comparison.similarity || 0,
                            skillsAlreadyHave: (comparison.skillsMatched || []).map(skill => ({
                                name: skill.skill_name || skill.name || 'Unknown',
                                category: skill.skill_category || skill.category || 'General',
                                isDefining: skill.is_defining || false
                            })),
                            skillsNeedToDevelop: (comparison.skillsUnique || []).map(skill => ({
                                name: skill.skill_name || skill.name || 'Unknown',
                                category: skill.skill_category || skill.category || 'General',
                                isDefining: skill.is_defining || false,
                                priority: skill.is_defining ? 'High' : 'Medium'
                            })),
                            definingSkillsAlignment: comparison.definingSkillsMatch || 0,
                            transitionDifficulty: this.calculateTransitionDifficulty(comparison)
                        };
                        
                        skillGaps.push(gapAnalysis);
                        console.log('✅ Added skill gap analysis:', gapAnalysis);
                    } else {
                        console.warn(`⚠️ No comparison data for ${parentJobTitle} -> ${childJobTitle}`);
                    }
                    
                    // Recursively analyze child nodes
                    await analyzeNode(childNode);
                } catch (error) {
                    console.error(`❌ Failed to analyze skill gap for ${parentNode?.name || 'Unknown'} -> ${childNode?.name || 'Unknown'}:`, error);
                }
            }
        };
        
        // Start analysis from root nodes
        try {
            console.log('🌳 Analyzing tree roots, count:', rootNodes.length);
            for (const rootNode of rootNodes) {
                await analyzeNode(rootNode);
            }
        } catch (error) {
            console.error('❌ Error in skill gaps analysis:', error);
        }
        
        console.log('🎯 Skill gaps analysis complete. Found', skillGaps.length, 'transitions');
        return skillGaps;
    },

    /**
     * Calculate transition difficulty based on skill comparison
     */
    calculateTransitionDifficulty(comparison) {
        const totalSkillsNeeded = comparison.skillsUnique.length;
        const definingSkillsNeeded = comparison.skillsUnique.filter(skill => skill.is_defining).length;
        const similarity = comparison.similarity || 0;
        
        if (similarity >= 0.8) return 'Easy';
        if (similarity >= 0.6) return 'Moderate';
        if (similarity >= 0.4) return 'Challenging';
        if (definingSkillsNeeded > 3 || totalSkillsNeeded > 10) return 'Very Challenging';
        return 'Difficult';
    }
};

console.log('✅ Career Pathways Data Extractor module loaded');
