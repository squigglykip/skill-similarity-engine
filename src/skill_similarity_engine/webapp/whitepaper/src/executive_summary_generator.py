"""
Executive Summary Generator
Generates the Executive Summary section for white papers using YAML templates and database queries.
Updated to support logical role architecture (Job + ManagementLevel combinations).
"""

import sqlite3
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
from jinja2 import Template

# Import SQL query modules
try:
    from ..sql import query_loader, DatabaseReferenceCalculator
except ImportError:
    # Handle direct script execution
    try:
        from sql import query_loader, DatabaseReferenceCalculator
    except ImportError:
        query_loader = None
        DatabaseReferenceCalculator = None

# Import ContentFormatter for structured content generation
try:
    from ..formatter import ContentFormatter
except ImportError:
    # Handle direct script execution or missing formatter
    try:
        from formatter import ContentFormatter
    except ImportError:
        ContentFormatter = None

# LogicalRoleManager has been replaced by JobDisplayManager
# Import the new centralized display utility
try:
    from skill_similarity_engine.utils.display import JobDisplayManager, DisplayFormat
except ImportError:
    # Handle relative imports when running from within the whitepaper directory
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(src_path))
    from skill_similarity_engine.utils.display import JobDisplayManager, DisplayFormat

class ExecutiveSummaryGenerator:
    """Generates executive summary content using template-driven approach with logical role support."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.template_path = Path(__file__).parent.parent / 'templates' / 'sections' / 'executive_summary.yaml'
        self.specific_template_path = Path(__file__).parent.parent / 'templates' / 'sections' / 'executive_summary_specific.yaml'
        self.template_data = self._load_template()
        self.specific_template_data = self._load_specific_template()
        self.display_manager = JobDisplayManager(db_connection)
        
        # Initialize advanced SQL integration if available
        if DatabaseReferenceCalculator:
            self.ref_calc = DatabaseReferenceCalculator(db_connection)
            self.queries = query_loader
        else:
            self.ref_calc = None
            self.queries = None
        
    def _load_template(self) -> Dict:
        """Load YAML template for executive summary."""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"⚠️ Error loading executive summary template: {e}")
            return {}
    
    def _load_specific_template(self) -> Dict:
        """Load YAML template for specific transition executive summary."""
        try:
            with open(self.specific_template_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"⚠️ Error loading specific transition template: {e}")
            return self.template_data  # Fallback to standard template
    
    def generate(self, job_from: str, analysis_mode: str = 'top_matches', job_to: Optional[str] = None, 
                 similarity_range: tuple = (0.4, 0.9)) -> Dict:
        """Generate executive summary content for a given source job with mode support."""
        
        # Step 1: Get database-derived values
        db_values = self._get_database_values(job_from)
        
        # Step 2: Get analysis data based on mode
        if analysis_mode == 'specific' and job_to:
            # Use SpecificTransitionAnalyzer for specific transitions
            try:
                from specific_transition_analyzer import SpecificTransitionAnalyzer
            except ImportError:
                # Handle absolute import for test environment
                import sys
                from pathlib import Path
                current_dir = Path(__file__).parent
                sys.path.insert(0, str(current_dir))
                from specific_transition_analyzer import SpecificTransitionAnalyzer
            analyzer = SpecificTransitionAnalyzer(self.db)
            
            if isinstance(job_to, str) and ',' in job_to:
                # Multiple targets
                job_to_list = [j.strip() for j in job_to.split(',')]
                analysis_data = analyzer.analyze_multiple_transitions(job_from, job_to_list, similarity_range)
            else:
                # Single target
                analysis_data = analyzer.analyze_single_transition(job_from, job_to, similarity_range)
            
            # Convert specific analysis to pathways format for template compatibility
            pathways_data = self._convert_specific_to_pathways(analysis_data)
        else:
            # Default: Top 3 pathways analysis
            pathways_data = self._get_top_pathways(job_from, limit=3)
            analysis_data = None
        
        # Step 3: Calculate dynamic thresholds and descriptors
        dynamic_descriptors = self._calculate_dynamic_descriptors(pathways_data, db_values)
        
        # Step 4: Populate template variables
        template_variables = self._populate_template_variables(
            job_from, db_values, pathways_data, dynamic_descriptors
        )
        
        # Add specific analysis context to template variables
        if analysis_data:
            template_variables.update(self._add_specific_analysis_context(analysis_data, analysis_mode))
        
        # Step 5: Generate content sections
        content = self._generate_content_sections(template_variables)
        
        return {
            'section_title': 'Executive Summary',
            'content': content,
            'references': self._generate_references(job_from, pathways_data),
            'template_variables': template_variables  # For debugging
        }
    
    def _get_database_values(self, job_from: str) -> Dict:
        """Execute database queries to get reference values with logical role support."""
        
        values = {}
        
        try:
            # Use advanced SQL integration if available
            if self.ref_calc:
                values['total_job_count'] = self.ref_calc.ref_01_total_job_profiles()
                values['active_competencies_count'] = self.ref_calc.ref_14_active_competencies()
                values['pathways_count'] = self.ref_calc.ref_15_precomputed_pathways()
                values['division_count'] = self.ref_calc.ref_16_divisional_structure()
                
                # Get confidence factors
                confidence_data = self.ref_calc.ref_13_confidence_factors()
                values['confidence_level'] = confidence_data['confidence_level']
                
                # Get similarity distribution for thresholds
                values['similarity_distribution'] = self.ref_calc.ref_03_similarity_percentiles()
                
                # Get source job details with logical role display
                values['source_job_details'] = self.ref_calc.get_source_job_details(job_from)
                values['source_job_details']['logical_display_name'] = self.display_manager.get_display_name(job_from, DisplayFormat.STANDARD)
                
                # Get top 3 similarities range for this specific job
                min_sim, max_sim, pathway_count = self.ref_calc.ref_02_top_similarities_range(job_from)
                values['top_similarities'] = {
                    'min_similarity': min_sim,
                    'max_similarity': max_sim,
                    'pathway_count': pathway_count
                }
            else:
                # Fallback to direct SQL queries
                # Reference (1): Total job profiles
                cursor = self.db.execute("SELECT COUNT(*) as total_job_count FROM jobs")
                result = cursor.fetchone()
                values['total_job_count'] = result[0] if result else 0
                
                # Reference (14): Active competencies
                cursor = self.db.execute("SELECT COUNT(DISTINCT Skill_ID) as active_competencies_count FROM job_skills")
                result = cursor.fetchone()
                values['active_competencies_count'] = result[0] if result else 0
                
                # Reference (15): Pre-computed pathways
                cursor = self.db.execute("SELECT COUNT(*) as pathways_count FROM career_pathways")
                result = cursor.fetchone()
                values['pathways_count'] = result[0] if result else 0
                
                # Reference (16): Division count
                cursor = self.db.execute("SELECT COUNT(DISTINCT Division) as division_count FROM positions")
                result = cursor.fetchone()
                values['division_count'] = result[0] if result else 0
                
                # Reference (13): Confidence level calculation
                values['confidence_level'] = self._calculate_confidence_level(values)
                
                # Get similarity distribution for thresholds
                values['similarity_distribution'] = self._get_similarity_distribution()
                
                # Get source job details with logical role display
                values['source_job_details'] = self._get_source_job_details(job_from)
                values['source_job_details']['logical_display_name'] = self.display_manager.get_display_name(job_from, DisplayFormat.STANDARD)
            
        except Exception as e:
            print(f"⚠️ Error getting database values: {e}")
            import traceback
            traceback.print_exc()
            values = self._get_fallback_values()
        
        return values
    
    def _get_top_pathways(self, job_from: str, limit: int = 3) -> List[Dict]:
        """Get top similarity pathways with consistent ordering."""
        
        try:
            # Use centralized pathway ordering for consistency across all sections
            from pathway_ordering_utils import get_consistent_pathways
            return get_consistent_pathways(self.db, job_from, limit, executive_refs=True)
            
        except ImportError:
            print("⚠️ PathwayOrderingUtils not available, using fallback method")
            # Fallback to original logic
            try:
                # Use advanced SQL integration if available
                if self.ref_calc:
                    pathways = self.ref_calc.get_top_pathways(job_from, limit)
                    
                    # Add logical role display names and level transition descriptions
                    for pathway in pathways:
                        # Add logical role display name
                        pathway['target_logical_role'] = self.display_manager.get_display_name(pathway['target_job_id'], DisplayFormat.STANDARD)
                        
                        # Add transition data
                        transition_data = self._calculate_move_type(job_from, pathway)
                        pathway.update(transition_data)
                    
                    return pathways
                else:
                    # Fallback to direct SQL query with deterministic ordering
                    query = """
                    SELECT 
                        js.job_to,
                        js.similarity_score,
                        j.JobProfile as target_job_title,
                        j.JobFunction as target_job_function,
                        j.ManagementLevel as target_management_level,
                        ROW_NUMBER() OVER (ORDER BY js.similarity_score DESC, js.job_to ASC) as rank
                    FROM job_similarities js
                    JOIN jobs j ON js.job_to = j.JobProfileID
                    WHERE js.job_from = ?
                      AND js.similarity_score < 1.0  -- Exclude 100% matches
                    ORDER BY js.similarity_score DESC, js.job_to ASC  -- Secondary sort for deterministic ordering
                    LIMIT ?
                    """
                    
                    cursor = self.db.execute(query, (job_from, limit))
                    results = cursor.fetchall()
                    
                    pathways = []
                    for result in results:
                        pathway = {
                            'target_job_id': result[0],
                            'similarity_score': round(result[1] * 100, 1),  # Convert to percentage
                            'target_job_title': result[2],
                            'target_job_function': result[3],
                            'target_management_level': result[4],
                            'rank': result[5],
                            'similarity_ref': str(4 + result[5]),  # References 5, 7, 9
                            'move_type_ref': str(5 + result[5])    # References 6, 8, 10
                        }
                        
                        # Add logical role display name
                        pathway['target_logical_role'] = self.display_manager.get_display_name(pathway['target_job_id'], DisplayFormat.STANDARD)
                        
                        # Calculate move type and level transition
                        pathway.update(self._calculate_move_type(job_from, pathway))
                        
                        pathways.append(pathway)
                    
                    return pathways
                
            except Exception as e:
                print(f"⚠️ Error getting top pathways: {e}")
                return []
            
        except Exception as e:
            print(f"⚠️ Error getting top pathways: {e}")
            return []
    
    def _calculate_move_type(self, job_from: str, pathway: Dict) -> Dict:
        """Calculate move type and level transition for a pathway."""
        
        try:
            # Get source job details
            source_query = """
            SELECT JobProfile, ManagementLevel 
            FROM jobs 
            WHERE JobProfileID = ?
            """
            source_result = self.db.execute(source_query, (job_from,)).fetchone()
            
            if not source_result:
                return {
                    'move_type': 'Other',
                    'level_transition': 'Unknown',
                    'strategic_context_explanation': 'Analysis not available'
                }
            
            source_job_title = source_result[0]
            source_level = source_result[1]
            target_job_title = pathway['target_job_title']
            target_level = pathway['target_management_level']
            
            # Extract numeric levels (Group 1 = 1, Group 2 = 2, etc.)
            source_level_num = self._extract_level_number(source_level)
            target_level_num = self._extract_level_number(target_level)
            
            # Get base role titles for comparison (remove pay band suffixes)
            source_base_title = source_job_title.split(" - ")[0] if " - " in source_job_title else source_job_title
            target_base_title = target_job_title.split(" - ")[0] if " - " in target_job_title else target_job_title
            
            # Store source base title for use in transition description
            pathway['source_base_title'] = source_base_title
            
            # Determine move type based on logical role progression
            if source_base_title == target_base_title and target_level_num > source_level_num:
                move_type = 'Progression - Same_Role_Higher_Level'
            elif source_base_title == target_base_title and target_level_num == source_level_num:
                move_type = 'Lateral - Same_Role_Same_Level'  # Different pay bands
            elif source_base_title != target_base_title and target_level_num > source_level_num:
                move_type = 'Progression - Different_Role_Higher_Level'
            elif source_base_title != target_base_title and target_level_num == source_level_num:
                move_type = 'Lateral - Different_Role_Same_Level'
            elif target_level_num < source_level_num:
                move_type = 'Transition - Lower_Level'  # Could be strategic move
            else:
                move_type = 'Other'
            
            # Create level transition description with business context
            level_transition = f"{source_level} → {target_level}"
            
            # For logical roles, focus on the role type rather than organizational function
            source_base_title = pathway.get('source_base_title', 'Current Role')
            target_base_title = pathway['target_job_title'].split(" - ")[0] if " - " in pathway['target_job_title'] else pathway['target_job_title']
            
            if source_base_title != target_base_title:
                level_transition += f" ({source_base_title} → {target_base_title})"
            else:
                level_transition += " (same role type)"
            
            # Add divisional deployment context
            divisional_context = self._get_divisional_deployment_context(pathway['target_job_id'])
            if divisional_context:
                pathway['divisional_deployment'] = divisional_context
            
            # Get strategic context explanation
            explanations = self.template_data.get('executive_summary', {}).get('primary_recommendations', {}).get('strategic_context_explanations', {})
            strategic_context = explanations.get(move_type, 'Strategic transition opportunity')
            
            # Replace placeholders in explanation (using role titles instead of functions)
            strategic_context = strategic_context.replace('{source_function}', source_base_title.lower())
            strategic_context = strategic_context.replace('{target_function}', target_base_title.lower())
            
            return {
                'move_type': move_type,
                'level_transition': level_transition,
                'strategic_context_explanation': strategic_context
            }
            
        except Exception as e:
            print(f"⚠️ Error calculating move type: {e}")
            return {
                'move_type': 'Other',
                'level_transition': 'Analysis not available',
                'strategic_context_explanation': 'Move type analysis not available'
            }
    
    def _extract_level_number(self, management_level: str) -> int:
        """Extract numeric level from management level string."""
        if not management_level:
            return 1
        
        try:
            # Look for "Group X" pattern
            if 'Group' in management_level:
                parts = management_level.split()
                for part in parts:
                    if part.isdigit():
                        return int(part)
            return 1
        except:
            return 1
    
    def _get_divisional_deployment_context(self, target_job_id: str) -> Optional[Dict]:
        """Get divisional deployment context for a target job to show business presence."""
        try:
            # Get base job title for logical role grouping
            job_query = """
            SELECT JobProfile, ManagementLevel
            FROM jobs 
            WHERE JobProfileID = ?
            """
            job_result = self.db.execute(job_query, (target_job_id,)).fetchone()
            
            if not job_result:
                return None
            
            job_title = job_result[0]
            management_level = job_result[1]
            
            # Remove pay band suffix to get base role
            base_job_title = job_title.split(" - ")[0] if " - " in job_title else job_title
            
            # Get divisional deployment for this logical role (base title + management level)
            deployment_query = """
            SELECT 
                p.Division,
                COUNT(DISTINCT p."Employee Number") as position_count,
                COUNT(DISTINCT p.Business_Unit) as business_unit_count
            FROM positions p
            JOIN jobs j ON p.JobProfileID = j.JobProfileID
            WHERE (j.JobProfile LIKE ? OR j.JobProfile = ?)
              AND j.ManagementLevel = ?
              AND p.Division IS NOT NULL
              AND p.Division != ''
            GROUP BY p.Division
            ORDER BY position_count DESC
            """
            
            like_pattern = f"{base_job_title} - %"
            results = self.db.execute(deployment_query, (like_pattern, base_job_title, management_level)).fetchall()
            
            if not results:
                return None
            
            # Format divisional deployment data
            divisions = []
            total_positions = 0
            total_business_units = 0
            
            for division, pos_count, bu_count in results:
                divisions.append({
                    'division': division,
                    'position_count': pos_count,
                    'business_unit_count': bu_count
                })
                total_positions += pos_count
                total_business_units += bu_count
            
            # Create deployment summary
            division_names = [d['division'] for d in divisions[:4]]  # Top 4 divisions
            division_summary = ", ".join(division_names[:3])
            if len(division_names) > 3:
                division_summary += f", and {len(division_names) - 3} other{'s' if len(division_names) > 4 else ''}"
            
            return {
                'base_role_title': base_job_title,
                'management_level': management_level,
                'divisions': divisions,
                'division_count': len(divisions),
                'total_positions': total_positions,
                'total_business_units': total_business_units,
                'division_summary': division_summary,
                'deployment_description': f"found across {len(divisions)} division{'s' if len(divisions) != 1 else ''} ({division_summary}) with {total_positions} positions in {total_business_units} business units"
            }
            
        except Exception as e:
            print(f"⚠️ Error getting divisional deployment context: {e}")
            return None
    
    def _calculate_confidence_level(self, values: Dict) -> str:
        """Calculate confidence level based on data volume."""
        
        active_competencies = values.get('active_competencies_count', 0)
        pathways_count = values.get('pathways_count', 0)
        division_count = values.get('division_count', 0)
        
        if (active_competencies > 2000 and 
            pathways_count > 8000 and 
            division_count >= 6):
            return 'High'
        elif (active_competencies > 1000 and 
              pathways_count > 5000 and 
              division_count >= 4):
            return 'Medium-high'
        else:
            return 'Medium'
    
    def _get_similarity_distribution(self) -> Dict:
        """Get NAB-specific similarity distribution for threshold calculation."""
        
        try:
            query = """
            SELECT 
                similarity_score,
                PERCENT_RANK() OVER (ORDER BY similarity_score) * 100 as percentile_rank
            FROM job_similarities 
            WHERE similarity_score > 0.0 AND similarity_score < 1.0
            ORDER BY similarity_score
            """
            
            cursor = self.db.execute(query)
            results = cursor.fetchall()
            
            if not results:
                return self._get_default_distribution()
            
            scores = [r[0] for r in results]
            
            # Calculate key percentiles
            import numpy as np
            percentiles = {
                95: np.percentile(scores, 95),
                90: np.percentile(scores, 90),
                75: np.percentile(scores, 75),
                50: np.percentile(scores, 50)
            }
            
            return {
                'percentiles': percentiles,
                'total_scores': len(scores),
                'mean': np.mean(scores),
                'scores': scores
            }
            
        except Exception as e:
            print(f"⚠️ Error getting similarity distribution: {e}")
            return self._get_default_distribution()
    
    def _get_default_distribution(self) -> Dict:
        """Fallback similarity distribution."""
        return {
            'percentiles': {95: 0.65, 90: 0.58, 75: 0.48, 50: 0.35},
            'total_scores': 0,
            'mean': 0.35,
            'scores': []
        }
    
    def _get_source_job_details(self, job_from: str) -> Dict:
        """Get source job details for template variables."""
        
        try:
            query = """
            SELECT JobProfile, JobFunction, ManagementLevel, JobCategory
            FROM jobs
            WHERE JobProfileID = ?
            """
            
            result = self.db.execute(query, (job_from,)).fetchone()
            
            if result:
                return {
                    'job_title': result[0],
                    'job_function': result[1],
                    'management_level': result[2],
                    'job_category': result[3]
                }
            else:
                return {
                    'job_title': 'Unknown Job',
                    'job_function': 'Unknown Function',
                    'management_level': 'Group 1',
                    'job_category': 'Unknown Category'
                }
                
        except Exception as e:
            print(f"⚠️ Error getting source job details: {e}")
            return {
                'job_title': 'Unknown Job',
                'job_function': 'Unknown Function', 
                'management_level': 'Group 1',
                'job_category': 'Unknown Category'
            }
    
    def _calculate_dynamic_descriptors(self, top_pathways: List[Dict], db_values: Dict) -> Dict:
        """Calculate dynamic descriptors based on similarity percentiles."""
        
        if not top_pathways:
            return {
                'opportunity_descriptor': 'transformation',
                'percentile_descriptor': '50th',
                'contextual_performance_descriptor': 'challenging but viable',
                'ranking_quality_descriptor': 'alternative',
                'risk_cost_descriptor': 'necessitating comprehensive transformation support',
                'data_quality_descriptor': 'limited data with significant estimates'
            }
        
        # Get highest similarity score from top pathways
        max_similarity = max(p['similarity_score'] for p in top_pathways) / 100.0
        
        # Get percentile thresholds
        distribution = db_values.get('similarity_distribution', {})
        percentiles = distribution.get('percentiles', {95: 0.65, 90: 0.58, 75: 0.48, 50: 0.35})
        
        # Determine category based on NAB-specific percentiles
        if max_similarity >= percentiles[95]:
            category = 'outstanding'
            percentile_desc = '95th'
        elif max_similarity >= percentiles[90]:
            category = 'excellent'
            percentile_desc = '90th'
        elif max_similarity >= percentiles[75]:
            category = 'good'
            percentile_desc = '75th'
        elif max_similarity >= percentiles[50]:
            category = 'development'
            percentile_desc = '50th'
        else:
            category = 'transformation'
            percentile_desc = 'below 50th'
        
        # Get descriptors from template
        template_descriptors = self.template_data.get('executive_summary', {}).get('key_findings', {})
        
        return {
            'opportunity_descriptor': template_descriptors.get('opportunity_descriptors', {}).get(category, category),
            'percentile_descriptor': percentile_desc,
            'contextual_performance_descriptor': template_descriptors.get('contextual_performance_descriptors', {}).get(category, category),
            'ranking_quality_descriptor': template_descriptors.get('ranking_quality_descriptors', {}).get(category, category),
            'risk_cost_descriptor': template_descriptors.get('risk_cost_descriptors', {}).get(category, category),
            'data_quality_descriptor': self._get_data_quality_descriptor(db_values['confidence_level'])
        }
    
    def _get_data_quality_descriptor(self, confidence_level: str) -> str:
        """Get data quality descriptor based on confidence level."""
        explanations = self.template_data.get('executive_summary', {}).get('confidence_assessment', {}).get('confidence_explanations', {})
        # Convert to uppercase for template lookup, but display in proper case
        confidence_key = confidence_level.upper().replace('-', '-')
        return explanations.get(confidence_key, 'balanced real data and validated estimates')
    
    def _populate_template_variables(self, job_from: str, db_values: Dict, 
                                   top_pathways: List[Dict], dynamic_descriptors: Dict) -> Dict:
        """Populate all template variables."""
        
        source_job = db_values['source_job_details']
        
        # Calculate similarity range from top pathways
        if top_pathways:
            min_similarity = min(p['similarity_score'] for p in top_pathways)
            max_similarity = max(p['similarity_score'] for p in top_pathways)
        else:
            min_similarity = max_similarity = 0
        
        variables = {
            # Source job context (with logical role support) - handle both ref_calc and direct query structures
            'source_job_title': source_job.get('logical_display_name', source_job.get('job_title', source_job.get('title', 'Unknown Job'))),
            'source_job_title_plural': source_job.get('logical_display_name', source_job.get('job_title', source_job.get('title', 'Unknown Job'))) + 's',  # Simple pluralization
            'source_management_level': source_job['management_level'],
            'source_job_function': source_job.get('job_function', source_job.get('function', 'Unknown Function')),
            'source_job_function_lower': source_job.get('job_function', source_job.get('function', 'Unknown Function')).lower() + ' and technical',
            'source_function': source_job.get('job_function', source_job.get('function', 'Unknown Function')),
            
            # Database metrics
            'total_job_count': f"{db_values['total_job_count']:,}",
            'pathway_count': len(top_pathways),
            'min_similarity': f"{min_similarity:.1f}",
            'max_similarity': f"{max_similarity:.1f}",
            'active_competencies_count': db_values['active_competencies_count'],
            'pathways_count': db_values['pathways_count'],
            'division_count': db_values['division_count'],
            'confidence_level': db_values['confidence_level'],
            
            # Dynamic descriptors
            **dynamic_descriptors,
            
            # Top pathways
            'top_pathways': top_pathways,
            
            # Example values
            'example_good_similarity': '65'
        }
        
        return variables
    
    def _generate_content_sections(self, variables: Dict) -> Dict:
        """Generate content for each section using Jinja2 templates."""
        
        # Use specific template if in specific mode
        if variables.get('analysis_mode') == 'specific':
            template_sections = self.specific_template_data.get('executive_summary', {})
        else:
            template_sections = self.template_data.get('executive_summary', {})
        content = {}
        
        try:
            # Strategic Context
            strategic_context = template_sections.get('strategic_context', {})
            content['strategic_context'] = {
                'title': strategic_context.get('title', 'Strategic Context'),
                'content': Template(strategic_context.get('content', '')).render(**variables)
            }
            
            # Key Findings - Use structured formatting if available
            key_findings = template_sections.get('key_findings', {})
            if key_findings.get('content_type') and ContentFormatter:
                key_findings_text = Template(key_findings.get('content', '')).render(**variables)
                content['key_findings'] = {
                    'title': key_findings.get('title', 'Key Findings'),
                    'content': ContentFormatter.create_formatted_content(
                        key_findings_text,
                        {
                            'content_type': key_findings.get('content_type'),
                            'bold_labels': key_findings.get('bold_labels', [])
                        }
                    )
                }
            else:
                content['key_findings'] = {
                    'title': key_findings.get('title', 'Key Findings'),
                    'content': Template(key_findings.get('content', '')).render(**variables)
                }
            
            # Primary Recommendations - Use structured formatting
            primary_rec = template_sections.get('primary_recommendations', {})
            content['primary_recommendations'] = {
                'title': primary_rec.get('title', 'Primary Recommendations'),
                'content': self._generate_structured_recommendations(primary_rec, variables)
            }
            
            # Skip empty data-driven classification section
            # classification = template_sections.get('data_driven_classification', {})
            # content['data_driven_classification'] = {
            #     'content': Template(classification.get('content', '')).render(**variables)
            # }
            
            # Skip academic sections that don't add business value
            # benchmarking = template_sections.get('similarity_benchmarking', {})
            # content['similarity_benchmarking'] = {
            #     'content': Template(benchmarking.get('content', '')).render(**variables)
            # }
            
            # template_note = template_sections.get('template_logic_note', {})
            # content['template_logic_note'] = {
            #     'content': Template(template_note.get('content', '')).render(**variables)
            # }
            
            # Confidence Assessment - Use structured formatting if available
            confidence = template_sections.get('confidence_assessment', {})
            if confidence.get('content_type') and ContentFormatter:
                confidence_text = Template(confidence.get('content', '')).render(**variables)
                content['confidence_assessment'] = {
                    'title': confidence.get('title', 'Confidence Assessment'),
                    'content': ContentFormatter.create_formatted_content(
                        confidence_text,
                        {
                            'content_type': confidence.get('content_type'),
                            'bold_labels': confidence.get('bold_labels', [])
                        }
                    )
                }
            else:
                content['confidence_assessment'] = {
                    'title': confidence.get('title', 'Confidence Assessment'),
                    'content': Template(confidence.get('content', '')).render(**variables)
                }
            
        except Exception as e:
            print(f"⚠️ Error generating content sections: {e}")
            content = {'error': f'Content generation failed: {e}'}
        
        return content
    
    def _generate_structured_recommendations(self, primary_rec_config: Dict, variables: Dict) -> Dict:
        """Generate structured recommendations content with explicit formatting metadata."""
        
        if not ContentFormatter:
            # Fallback to legacy string-based content if ContentFormatter not available
            fallback_content = Template(primary_rec_config.get('content', '')).render(**variables)
            return {'text': fallback_content, 'formatting': {}}
        
        top_pathways = variables.get('top_pathways', [])
        bold_labels = primary_rec_config.get('bold_labels', ['Move Type:', 'Strategic Context:'])
        
        # Generate numbered recommendation items
        recommendation_items = []
        
        for i, recommendation in enumerate(top_pathways, 1):
            # Create main recommendation header (will be bold)
            header = f"{recommendation.get('target_logical_role', 'Unknown Role')} - {recommendation.get('similarity_score', 0)}% similarity"
            
            # Create detail items with labels that will be bold
            details = []
            if 'move_type' in recommendation:
                details.append(f"Move Type: {recommendation['move_type']}")
            
            # Add function transition information if available
            source_function = variables.get('source_job_function', '')
            target_function = recommendation.get('target_job_function', '')
            target_level = recommendation.get('target_management_level', '')
            source_level = variables.get('source_management_level', '')
            
            if source_function and target_function:
                details.append(f"Function Transition: {source_function} → {target_function}")
            
            if source_level and target_level:
                details.append(f"Management Level: {source_level} → {target_level}")
            
            if 'strategic_context_explanation' in recommendation:
                details.append(f"Strategic Context: {recommendation['strategic_context_explanation']}")
            
            # Add divisional deployment if available
            if recommendation.get('divisional_deployment'):
                divisional_text = f"This role is {recommendation['divisional_deployment']['deployment_description']}"
                details.append(divisional_text)
            
            # Create the full recommendation text
            recommendation_text = header
            if details:
                detail_bullets = '\n'.join([f"- {detail}" for detail in details])
                recommendation_text += f"\n{detail_bullets}"
            
            recommendation_items.append(recommendation_text)
        
        # Create structured content with numbered list for headers and bullet sub-items
        if recommendation_items:
            # Combine all recommendations into a single text block
            full_text = ""
            for i, item in enumerate(recommendation_items, 1):
                full_text += f"{i}. {item}"
                if i < len(recommendation_items):
                    full_text += "\n\n"
            
            # Return structured content with formatting metadata
            return ContentFormatter.create_formatted_content(
                full_text,
                {
                    'content_type': 'mixed',  # Contains both numbered items and bullets
                    'bold_labels': bold_labels,
                    'bold_numbered_headers': True  # Make numbered recommendation headers bold
                }
            )
        else:
            # Fallback if no recommendations available
            return ContentFormatter.create_paragraph(
                "No pathway recommendations available for this analysis.",
                []
            )
    
    def _generate_references(self, job_from: str, top_pathways: List[Dict]) -> Dict:
        """Generate reference mappings for the executive summary."""
        
        references = self.template_data.get('references', {})
        
        # Add job-specific references
        job_specific_refs = {}
        for pathway in top_pathways:
            ref_num = pathway.get('similarity_ref')
            if ref_num:
                job_specific_refs[ref_num] = f"SELECT similarity_score FROM job_similarities WHERE job_from = '{job_from}' AND job_to = '{pathway['target_job_id']}'"
        
        return {**references, **job_specific_refs}
    
    def _get_fallback_values(self) -> Dict:
        """Fallback values when database queries fail."""
        return {
            'total_job_count': 715,
            'active_competencies_count': 2091,
            'pathways_count': 8580,
            'division_count': 6,
            'confidence_level': 'High',
            'similarity_distribution': self._get_default_distribution(),
            'source_job_details': {
                'job_title': 'Unknown Job',
                'job_function': 'Unknown Function',
                'management_level': 'Group 1',
                'job_category': 'Unknown Category'
            }
        }
    
    def _convert_specific_to_pathways(self, analysis_data: Dict) -> List[Dict]:
        """Convert specific transition analysis to pathways format for template compatibility."""
        if analysis_data['analysis_mode'] == 'specific_single':
            # Single transition - create pathway-like structure
            return [{
                'target_job_id': analysis_data['target_job']['job_id'],
                'target_logical_role': analysis_data['target_job']['logical_display_name'],
                'similarity_score': analysis_data['transition_metrics']['similarity_score'],
                'target_job_title': analysis_data['target_job']['logical_display_name'],
                'target_job_function': analysis_data['target_job']['job_function'],
                'target_management_level': analysis_data['target_job']['management_level'],
                'move_type': analysis_data['move_classification']['move_type_display'],
                'level_transition': analysis_data['move_classification']['level_transition'],
                'rank': 1
            }]
        elif analysis_data['analysis_mode'] == 'specific_multiple':
            # Multiple transitions - convert each to pathway format
            pathways = []
            for i, transition in enumerate(analysis_data['transitions'], 1):
                pathways.append({
                    'target_job_id': transition['target_job']['job_id'],
                    'target_logical_role': transition['target_job']['logical_display_name'],
                    'similarity_score': transition['transition_metrics']['similarity_score'],
                    'target_job_title': transition['target_job']['logical_display_name'],
                    'target_job_function': transition['target_job']['job_function'],
                    'target_management_level': transition['target_job']['management_level'],
                    'move_type': transition['move_classification']['move_type_display'],
                    'level_transition': transition['move_classification']['level_transition'],
                    'rank': i
                })
            return pathways
        else:
            return []
    
    def _add_specific_analysis_context(self, analysis_data: Dict, analysis_mode: str) -> Dict:
        """Add specific analysis context to template variables."""
        context = {
            'analysis_mode': analysis_mode,
            'specific_analysis_data': analysis_data
        }
        
        if analysis_data['analysis_mode'] == 'specific_single':
            context.update({
                'target_job_logical_name': analysis_data['target_job']['logical_display_name'],
                'transition_similarity': analysis_data['transition_metrics']['similarity_score'],
                'transition_viability': analysis_data['strategic_context']['transition_viability'],
                'move_classification': analysis_data['move_classification']['move_type_display'],
                'estimated_timeline': analysis_data['move_classification']['estimated_timeline']
            })
        elif analysis_data['analysis_mode'] == 'specific_multiple':
            context.update({
                'target_count': analysis_data['target_count'],
                'highest_similarity': analysis_data['comparative_metrics']['highest_similarity'],
                'average_similarity': analysis_data['comparative_metrics']['average_similarity'],
                'portfolio_strength': analysis_data['strategic_portfolio']['portfolio_strength']
            })
        
        return context 