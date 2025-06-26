"""
Conclusion Generator
Generates the Conclusion section for white papers using YAML templates and database queries.
Follows the proven pattern from pathway_analysis_generator.py with logical role architecture support.

This generator creates a strategic synthesis that:
- Summarizes transition opportunities with actual similarity scores
- Provides strategic alignment context
- Recommends concrete next steps (pilot program approach)
- Reinforces value proposition for organization and individuals
"""

import sqlite3
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
from jinja2 import Template
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import SQL query modules and JobDisplayManager from utilities
try:
    from ..sql import query_loader, DatabaseReferenceCalculator
    from skill_similarity_engine.utils.display import JobDisplayManager, DisplayFormat
except ImportError:
    # Handle direct script execution
    try:
        from sql import query_loader, DatabaseReferenceCalculator
        # Try importing JobDisplayManager with path adjustment
        try:
            from skill_similarity_engine.utils.display import JobDisplayManager, DisplayFormat
        except ImportError:
            import sys
            from pathlib import Path
            src_path = Path(__file__).parent.parent.parent.parent.parent
            sys.path.insert(0, str(src_path))
            from skill_similarity_engine.utils.display import JobDisplayManager, DisplayFormat
    except ImportError:
        query_loader = None
        DatabaseReferenceCalculator = None
        JobDisplayManager = None
        DisplayFormat = None

class ConclusionGenerator:
    """Generates conclusion content using template-driven approach with logical role support."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.template_path = Path(__file__).parent.parent / 'templates' / 'sections' / 'conclusion.yaml'
        self.specific_template_path = Path(__file__).parent.parent / 'templates' / 'sections' / 'conclusion_specific.yaml'
        self.template_data = self._load_template()
        
        # Initialize display manager for job name formatting
        if JobDisplayManager:
            self.display_manager = JobDisplayManager(db_connection)
        else:
            self.display_manager = None
        
        # Initialize advanced SQL integration if available
        if DatabaseReferenceCalculator:
            self.ref_calc = DatabaseReferenceCalculator(db_connection)
            self.queries = query_loader
        else:
            self.ref_calc = None
            self.queries = None
        
    def _load_template(self, analysis_mode: str = 'top_matches') -> Dict:
        """Load YAML template for conclusion based on mode."""
        try:
            if analysis_mode == 'specific':
                template_path = self.specific_template_path
            else:
                template_path = self.template_path
                
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as file:
                    return yaml.safe_load(file)
            else:
                logger.warning(f"Template not found at {template_path}")
                # Fallback to standard template
                if template_path != self.template_path and self.template_path.exists():
                    with open(self.template_path, 'r', encoding='utf-8') as file:
                        return yaml.safe_load(file)
                return {}
        except Exception as e:
            logger.warning(f"Error loading conclusion template: {e}")
            return {}
    
    def generate(self, job_from: str, analysis_mode: str = 'top_matches', job_to: Optional[str] = None, 
                 similarity_range: tuple = (0.4, 0.9), include_organisational_deployment: bool = False) -> Dict:
        """Generate conclusion content for the white paper."""
        
        logger.info(f"Generating conclusion for job: {job_from}")
        
        # Load appropriate template for mode
        self.template_data = self._load_template(analysis_mode)
        
        # Handle specific mode with SpecificTransitionAnalyzer
        if analysis_mode == 'specific' and job_to:
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
            
            # Get database values
            db_values = self._get_database_summary(job_from)
            
            # Get pathway and strategic context (but use specific data)
            pathway_summary = self._get_pathway_analysis_summary(job_from)
            strategic_context = self._get_strategic_context(job_from)
            
            # Populate template variables with specific analysis data
            template_variables = self._populate_template_variables(
                job_from, db_values, pathway_summary, strategic_context, include_organisational_deployment
            )
            
            # Add specific analysis variables
            template_variables['analysis_mode'] = analysis_mode
            template_variables['specific_analysis_data'] = analysis_data
            
            # Extract key variables from specific analysis
            if analysis_data['analysis_mode'] == 'specific_single':
                template_variables.update({
                    'target_job_logical_name': analysis_data['target_job']['logical_display_name'],
                    'transition_similarity': analysis_data['transition_metrics']['similarity_score'],
                    'transition_viability': analysis_data['strategic_context']['transition_viability'],
                    'move_classification': analysis_data['move_classification']['move_type_display'],
                    'estimated_timeline': analysis_data['move_classification']['estimated_timeline']
                })
            elif analysis_data['analysis_mode'] == 'specific_multiple':
                template_variables.update({
                    'target_count': analysis_data['target_count'],
                    'lowest_similarity': analysis_data['comparative_metrics']['lowest_similarity'],
                    'highest_similarity': analysis_data['comparative_metrics']['highest_similarity'],
                    'portfolio_strength': analysis_data['strategic_portfolio']['portfolio_strength']
                })
        else:
            # Default: Discovery mode
            # Step 1: Get database-derived analysis summary
            db_values = self._get_database_summary(job_from)
            logger.info(f"Retrieved database summary for conclusion: {len(db_values)} metrics")
            
            # Step 2: Get pathway analysis summary
            pathway_summary = self._get_pathway_analysis_summary(job_from)
            
            # Step 3: Get strategic context
            strategic_context = self._get_strategic_context(job_from)
            
            # Step 4: Populate template variables
            template_variables = self._populate_template_variables(
                job_from, db_values, pathway_summary, strategic_context, include_organisational_deployment
            )
            logger.info(f"Populated {len(template_variables)} template variables for conclusion")
        
        # Step 5: Generate content sections
        content = self._generate_content_sections(template_variables)
        logger.info("Generated conclusion content sections")
        
        logger.info("Conclusion generation completed successfully")
        
        return {
            'section_title': 'Conclusion',
            'content': content,
            'references': self._generate_references(),
            'template_variables': template_variables  # For debugging
        }
    
    def _get_database_summary(self, job_from: str) -> Dict:
        """Get high-level database summary for conclusion synthesis."""
        try:
            # Get source job logical display name
            if self.display_manager and DisplayFormat:
                source_job_logical_display_name = self.display_manager.get_display_name(job_from, DisplayFormat.STANDARD)
            else:
                source_job_logical_display_name = self._get_job_title_fallback(job_from)
            
            # Get total job count
            total_jobs = self.db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            
            # Get pathway count and similarity range
            pathways = self.db.execute("""
                SELECT similarity_score
                FROM career_pathways
                WHERE source_job_id = ?
                ORDER BY similarity_score DESC
                LIMIT 3
            """, (job_from,)).fetchall()
            
            if pathways:
                similarity_scores = [p[0] * 100 for p in pathways]  # Convert to percentage
                min_similarity = min(similarity_scores)
                max_similarity = max(similarity_scores)
                pathway_count = len(pathways)
            else:
                min_similarity = max_similarity = 0
                pathway_count = 0
            
            # Determine opportunity classification
            opportunity_classification = self._classify_opportunity_quality(max_similarity)
            
            return {
                'source_job_logical_display_name': source_job_logical_display_name,
                'total_job_profiles': total_jobs,
                'pathway_count': pathway_count,
                'min_similarity': min_similarity,
                'max_similarity': max_similarity,
                'opportunity_classification': opportunity_classification,
                'similarity_range_description': f"{min_similarity:.1f}-{max_similarity:.1f}%" if pathway_count > 0 else "0.0%"
            }
            
        except Exception as e:
            logger.error(f"Error getting database summary: {e}")
            return self._get_fallback_summary(job_from)
    
    def _get_pathway_analysis_summary(self, job_from: str) -> Dict:
        """Get pathway analysis summary for strategic context."""
        try:
            # Get source job function
            source_job = self.db.execute("""
                SELECT JobFunction, ManagementLevel
                FROM jobs
                WHERE JobProfileID = ?
            """, (job_from,)).fetchone()
            
            source_function = source_job[0] if source_job else "Unknown Function"
            source_level = source_job[1] if source_job else "Group 1"
            
            # Get pathway progression types
            pathways_query = """
                SELECT j.JobFunction, j.ManagementLevel, cp.similarity_score
                FROM career_pathways cp
                JOIN jobs j ON cp.target_job_id = j.JobProfileID
                WHERE cp.source_job_id = ?
                ORDER BY cp.similarity_score DESC
                LIMIT 3
            """
            pathways = self.db.execute(pathways_query, (job_from,)).fetchall()
            
            # Analyze progression types
            progression_types = []
            for target_function, target_level, similarity in pathways:
                if target_function == source_function:
                    if self._extract_level_number(target_level) > self._extract_level_number(source_level):
                        progression_types.append("career progression")
                    else:
                        progression_types.append("lateral expansion")
                else:
                    progression_types.append("cross-functional expansion")
            
            # Get unique progression types description
            unique_types = list(set(progression_types))
            if len(unique_types) == 1:
                progression_value_description = f"clear {unique_types[0]}"
            elif len(unique_types) == 2:
                progression_value_description = f"{unique_types[0]} and {unique_types[1]} value"
            else:
                progression_value_description = "diverse progression value"
            
            return {
                'source_function': source_function,
                'progression_types': progression_types,
                'progression_value_description': progression_value_description,
                'pathway_diversity': len(unique_types)
            }
            
        except Exception as e:
            logger.error(f"Error getting pathway analysis summary: {e}")
            return {
                'source_function': 'Unknown Function',
                'progression_types': ['career progression'],
                'progression_value_description': 'clear progression value',
                'pathway_diversity': 1
            }
    
    def _get_strategic_context(self, job_from: str) -> Dict:
        """Get strategic context for organizational alignment."""
        try:
            # Get position count for pilot sizing
            job_query = """
            SELECT JobProfile, ManagementLevel
            FROM jobs 
            WHERE JobProfileID = ?
            """
            job_result = self.db.execute(job_query, (job_from,)).fetchone()
            
            if job_result:
                job_title = job_result[0]
                management_level = job_result[1]
                
                # Remove pay band suffix for logical role grouping
                base_job_title = job_title.split(" - ")[0] if " - " in job_title else job_title
                
                # Get position count for this logical role
                like_pattern = f"{base_job_title} - %"
                position_count = self.db.execute("""
                    SELECT COUNT(DISTINCT p."Employee Number")
                    FROM positions p
                    JOIN jobs j ON p.JobProfileID = j.JobProfileID
                    WHERE (j.JobProfile LIKE ? OR j.JobProfile = ?)
                      AND j.ManagementLevel = ?
                """, (like_pattern, base_job_title, management_level)).fetchone()[0]
            else:
                position_count = 0
            
            # Calculate recommended pilot size (2-3 candidates as per gold standard)
            if position_count >= 10:
                pilot_size = "2-3"
                pilot_scale_descriptor = "high-potential candidates"
            elif position_count >= 5:
                pilot_size = "1-2"
                pilot_scale_descriptor = "selected candidates"
            else:
                pilot_size = "1"
                pilot_scale_descriptor = "suitable candidate"
            
            # Determine strategic priority based on pathway quality
            strategic_priority = self._determine_strategic_priority(job_from)
            
            return {
                'source_position_count': position_count,
                'pilot_size': pilot_size,
                'pilot_scale_descriptor': pilot_scale_descriptor,
                'strategic_priority': strategic_priority,
                'implementation_approach': "structured pilot program",
                'scaling_approach': f"learnings to refine and scale the approach across the broader {base_job_title if job_result else 'professional'} population"
            }
            
        except Exception as e:
            logger.error(f"Error getting strategic context: {e}")
            return {
                'source_position_count': 0,
                'pilot_size': "2-3",
                'pilot_scale_descriptor': "high-potential candidates",
                'strategic_priority': "workforce development",
                'implementation_approach': "structured pilot program",
                'scaling_approach': "learnings to scale across the broader population"
            }
    
    def _populate_template_variables(self, job_from: str, db_values: Dict, 
                                   pathway_summary: Dict, strategic_context: Dict,
                                   include_deployment: bool) -> Dict:
        """Populate all template variables for conclusion content."""
        
        variables = {
            # Database summary
            **db_values,
            
            # Pathway analysis summary  
            **pathway_summary,
            
            # Strategic context
            **strategic_context,
            
            # Additional synthesis variables
            'analysis_scope_description': f"comprehensive analysis of NAB's {db_values['total_job_profiles']} job profiles",
            'transition_quality_assessment': self._get_transition_quality_assessment(db_values['opportunity_classification']),
            'strategic_alignment_description': self._get_strategic_alignment_description(pathway_summary['source_function']),
            'value_proposition_summary': self._get_value_proposition_summary(db_values['opportunity_classification']),
            'foundation_description': "strategic workforce planning conversations and individual career development discussions",
            'dual_benefit_description': "both organisational capability building and professional growth objectives"
        }
        
        return variables
    
    def _generate_content_sections(self, variables: Dict) -> Dict:
        """Generate content for the conclusion section using Jinja2 templates."""
        
        template_sections = self.template_data.get('conclusion', {})
        content_sections = template_sections.get('content_sections', {})
        content = {}
        
        try:
            logger.info(f"Template sections found: {list(content_sections.keys())}")
            
            # Opportunity Summary
            opportunity_summary = content_sections.get('opportunity_summary', {})
            content['opportunity_summary'] = {
                'title': opportunity_summary.get('title', 'Bottom Line'),
                'content': Template(opportunity_summary.get('content', '')).render(**variables)
            }
            
            # Strategic Alignment  
            strategic_alignment = content_sections.get('strategic_alignment', {})
            content['strategic_alignment'] = {
                'title': strategic_alignment.get('title', 'Strategic Alignment'),
                'content': Template(strategic_alignment.get('content', '')).render(**variables)
            }
            
            # Recommended Approach
            recommended_approach = content_sections.get('recommended_approach', {})
            content['recommended_approach'] = {
                'title': recommended_approach.get('title', 'Next Steps'),
                'content': Template(recommended_approach.get('content', '')).render(**variables)
            }
            
            # Foundation Value
            foundation_value = content_sections.get('foundation_value', {})
            content['foundation_value'] = {
                'title': foundation_value.get('title', 'Foundation Value'),
                'content': Template(foundation_value.get('content', '')).render(**variables)
            }
            
        except Exception as e:
            logger.error(f"Error generating content sections: {e}")
            content = {'error': f'Content generation failed: {e}'}
        
        return content
    
    def _generate_references(self) -> Dict:
        """Generate reference mappings for the conclusion."""
        references = self.template_data.get('references', {})
        return references
    
    # Helper methods for content analysis
    def _get_job_title_fallback(self, job_from: str) -> str:
        """Fallback method to get job title when LogicalRoleManager is not available."""
        try:
            query = "SELECT JobProfile FROM jobs WHERE JobProfileID = ?"
            result = self.db.execute(query, (job_from,)).fetchone()
            return result[0] if result else job_from
        except:
            return job_from
    
    def _extract_level_number(self, management_level: str) -> int:
        """Extract numeric level from management level string."""
        if not management_level:
            return 1
        
        try:
            if 'Group' in management_level:
                parts = management_level.split()
                for part in parts:
                    if part.isdigit():
                        return int(part)
            return 1
        except:
            return 1
    
    def _classify_opportunity_quality(self, max_similarity: float) -> str:
        """Classify opportunity quality based on similarity score."""
        if max_similarity >= 85: return "exceptional"
        elif max_similarity >= 75: return "excellent"
        elif max_similarity >= 65: return "strong"
        elif max_similarity >= 50: return "development"
        else: return "transformation"
    
    def _determine_strategic_priority(self, job_from: str) -> str:
        """Determine strategic priority based on pathway analysis."""
        try:
            # Get average similarity for strategic priority assessment
            avg_similarity = self.db.execute("""
                SELECT AVG(similarity_score) 
                FROM career_pathways 
                WHERE source_job_id = ?
            """, (job_from,)).fetchone()[0]
            
            if avg_similarity and avg_similarity > 0.7:
                return "workforce agility and internal mobility"
            elif avg_similarity and avg_similarity > 0.5:
                return "capability development and career progression"
            else:
                return "workforce transformation and skills development"
                
        except:
            return "workforce development and career advancement"
    
    def _get_transition_quality_assessment(self, classification: str) -> str:
        """Get transition quality assessment description."""
        assessments = {
            'exceptional': 'exceptional transition opportunities',
            'excellent': 'excellent transition opportunities', 
            'strong': 'strong transition opportunities',
            'development': 'valuable development-focused opportunities',
            'transformation': 'strategic transformation opportunities'
        }
        return assessments.get(classification, 'transition opportunities')
    
    def _get_strategic_alignment_description(self, source_function: str) -> str:
        """Get strategic alignment description based on function."""
        if 'Analytics' in source_function or 'Data' in source_function:
            return "NAB's data-driven transformation priorities"
        elif 'Risk' in source_function:
            return "NAB's risk management excellence objectives"
        elif 'Technology' in source_function:
            return "NAB's digital transformation initiatives"
        else:
            return "NAB's strategic priorities"
    
    def _get_value_proposition_summary(self, classification: str) -> str:
        """Get value proposition summary based on opportunity classification."""
        propositions = {
            'exceptional': 'optimal career advancement for analytical professionals',
            'excellent': 'meaningful career advancement for analytical professionals',
            'strong': 'valuable career advancement for analytical professionals', 
            'development': 'strategic career development for analytical professionals',
            'transformation': 'transformative career opportunities for analytical professionals'
        }
        return propositions.get(classification, 'career advancement for analytical professionals')
    
    def _get_fallback_summary(self, job_from: str) -> Dict:
        """Fallback summary when database queries fail."""
        return {
            'source_job_logical_display_name': f'Job {job_from}',
            'total_job_profiles': 715,
            'pathway_count': 3,
            'min_similarity': 60.0,
            'max_similarity': 80.0,
            'opportunity_classification': 'strong',
            'similarity_range_description': '60.0-80.0%'
        } 