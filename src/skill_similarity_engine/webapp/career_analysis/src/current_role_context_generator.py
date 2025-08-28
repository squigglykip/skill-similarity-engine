"""
Current Role Context Generator
Generates the Current Role Context section for Career Transition Analysis using YAML templates and database queries.
Follows the proven ExecutiveSummaryGenerator and PathwayAnalysisGenerator patterns with logical role architecture support.
"""

import sqlite3
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
from jinja2 import Template

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

# Import ContentFormatter for structured content generation
ContentFormatter = None
try:
    from ..formatter import ContentFormatter
except ImportError:
    try:
        # Try absolute import within the career_analysis package
        from skill_similarity_engine.webapp.career_analysis.formatter import ContentFormatter
    except ImportError:
        ContentFormatter = None

class CurrentRoleContextGenerator:
    """Generates current role context content using template-driven approach with logical role support."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.template_path = Path(__file__).parent.parent / 'templates' / 'sections' / 'current_role_context.yaml'
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
        
    def _load_template(self) -> Dict:
        """Load YAML template for current role context."""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"⚠️ Error loading current role context template: {e}")
            return {}
    
    def generate(self, job_from: str, include_organisational_deployment: bool = False, 
                 primary_algorithm: str = 'enhanced') -> Dict:
        """Generate current role context content for a given source job."""
        
        # Step 1: Get database-derived values
        db_values = self._get_database_values(job_from)
        
        # Step 2: Calculate dynamic thresholds and descriptors
        dynamic_descriptors = self._calculate_dynamic_descriptors(db_values)
        
        # Step 3: Populate template variables
        template_variables = self._populate_template_variables(
            job_from, db_values, dynamic_descriptors, include_organisational_deployment
        )
        
        # Step 4: Generate content sections
        content = self._generate_content_sections(template_variables)
        
        # Extract section title from YAML template
        current_role_config = self.template_data.get('current_role_context', {})
        section_config = current_role_config.get('section_config', {})
        section_title_template = section_config.get('title', 'Current Role Context: {{source_job_logical_display_name}}')
        
        # Render the section title with template variables
        title_template = Template(section_title_template)
        section_title = title_template.render(**template_variables)
        
        return {
            'section_title': section_title,
            'content': content,
            'references': self._generate_references(job_from),
            'template_variables': template_variables  # For debugging
        }
    
    def _get_database_values(self, job_from: str) -> Dict:
        """Get core database values for the current role context."""
        values = {}
        
        try:
            cursor = self.db.cursor()
            
            # Get basic job information
            cursor.execute("""
                SELECT JobProfile, JobFunction, ManagementLevel 
                FROM core_job_architecture 
                WHERE JobProfileID = ?
            """, (job_from,))
            job_info = cursor.fetchone()
            
            if job_info:
                values['job_title'] = job_info[0]
                values['job_function'] = job_info[1]
                values['management_level'] = job_info[2]
            
            # Get skills count
            cursor.execute("""
                SELECT COUNT(DISTINCT js.Skill_ID) 
                FROM core_job_skill_requirements js 
                WHERE js.JobProfileID = ?
            """, (job_from,))
            skills_result = cursor.fetchone()
            values['total_skills'] = skills_result[0] if skills_result else 0
            
            # Get skill categories
            cursor.execute("""
                SELECT s.Category, COUNT(DISTINCT js.Skill_ID) as skill_count
                FROM core_job_skill_requirements js 
                JOIN core_skills_taxonomy s ON js.Skill_ID = s.Skill_ID 
                WHERE js.JobProfileID = ?
                GROUP BY s.Category
                ORDER BY skill_count DESC
            """, (job_from,))
            categories = cursor.fetchall()
            values['skill_categories'] = [
                {'name': cat[0], 'skill_count': cat[1]} 
                for cat in categories
            ]
            values['skill_category_count'] = len(categories)
            
            # Get position count (if deployment data available)
            try:
                cursor.execute("""
                    SELECT COUNT(DISTINCT employee_number), COUNT(DISTINCT ORG_UNIT_NAME_2) 
                    FROM core_workforce_current 
                    WHERE JobProfileID = ?
                """, (job_from,))
                deployment_result = cursor.fetchone()
                if deployment_result:
                    values['position_count'] = deployment_result[0] or 0
                    values['division_count'] = deployment_result[1] or 0
            except:
                values['position_count'] = 0
                values['division_count'] = 0
            
            # Calculate strategic metrics (simplified)
            values['mobility_hub_score'] = self._calculate_mobility_hub_score(job_from)
            values['transition_readiness'] = self._calculate_transition_readiness(job_from)
            values['cross_family_reach'] = self._calculate_cross_family_reach(job_from)
            
            # Get skills overlap analysis
            values.update(self._get_skills_overlap_analysis(job_from))
            
            # Get job function statistics
            values.update(self._get_job_function_statistics(job_from))
            
            # Get cross-functional analysis
            values.update(self._get_cross_functional_analysis(job_from))
            
        except Exception as e:
            print(f"⚠️ Error getting database values: {e}")
        
        return values
    
    def _calculate_dynamic_descriptors(self, db_values: Dict) -> Dict:
        """Calculate dynamic descriptors based on database values."""
        descriptors = {}
        
        # Role capability descriptor
        total_skills = db_values.get('total_skills', 0)
        if total_skills > 50:
            descriptors['role_capability_descriptor'] = 'high-capability'
        elif total_skills > 25:
            descriptors['role_capability_descriptor'] = 'moderate-capability'
        else:
            descriptors['role_capability_descriptor'] = 'focused-capability'
        
        # Mobility assessment
        mobility_score = db_values.get('mobility_hub_score', 0)
        if mobility_score > 70:
            descriptors['mobility_hub_assessment'] = 'High Hub Potential'
        elif mobility_score > 50:
            descriptors['mobility_hub_assessment'] = 'Medium Hub Potential'
        else:
            descriptors['mobility_hub_assessment'] = 'Limited Hub Potential'
        
        # Transition readiness assessment
        readiness_score = db_values.get('transition_readiness', 0)
        if readiness_score > 75:
            descriptors['transition_readiness_assessment'] = 'High Readiness'
        elif readiness_score > 50:
            descriptors['transition_readiness_assessment'] = 'Medium Readiness'
        else:
            descriptors['transition_readiness_assessment'] = 'Development Required'
        
        # Cross-family diversity assessment
        cross_family = db_values.get('cross_family_reach', 0)
        if cross_family >= 5:
            descriptors['cross_family_diversity_assessment'] = 'Excellent Diversity'
        elif cross_family >= 3:
            descriptors['cross_family_diversity_assessment'] = 'Good Diversity'
        elif cross_family >= 2:
            descriptors['cross_family_diversity_assessment'] = 'Moderate Diversity'
        else:
            descriptors['cross_family_diversity_assessment'] = 'Limited Diversity'
        
        # Strategic value assessment
        if mobility_score > 70 and readiness_score > 75:
            descriptors['strategic_value_assessment'] = 'HIGH'
            descriptors['strategic_value_descriptor'] = 'Key Position for Workforce Planning'
        elif mobility_score > 50 and readiness_score > 50:
            descriptors['strategic_value_assessment'] = 'MEDIUM'
            descriptors['strategic_value_descriptor'] = 'Valuable Position for Workforce Planning'
        else:
            descriptors['strategic_value_assessment'] = 'LOW'
            descriptors['strategic_value_descriptor'] = 'Standard Position for Workforce Planning'
        
        return descriptors
    
    def _calculate_mobility_hub_score(self, job_from: str) -> float:
        """Calculate mobility hub score (simplified version)."""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT COUNT(*) 
                FROM analytics_job_similarities 
                WHERE job_from = ? AND similarity_score > 0.4
            """, (job_from,))
            result = cursor.fetchone()
            pathway_count = result[0] if result else 0
            
            # Normalize to 0-100 scale (simplified)
            return min(100, (pathway_count / 10) * 100)
        except:
            return 50.0  # Default moderate score
    
    def _calculate_transition_readiness(self, job_from: str) -> float:
        """Calculate transition readiness score (simplified version)."""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT AVG(similarity_score) 
                FROM analytics_job_similarities 
                WHERE job_from = ? AND similarity_score > 0.4
            """, (job_from,))
            result = cursor.fetchone()
            avg_similarity = result[0] if result else 0.5
            
            return round(avg_similarity * 100, 1)
        except:
            return 60.0  # Default moderate readiness
    
    def _calculate_cross_family_reach(self, job_from: str) -> int:
        """Calculate cross-family reach count."""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT j.JobFunction) 
                FROM analytics_job_similarities s
                JOIN core_job_architecture j ON s.job_to = j.JobProfileID
                WHERE s.job_from = ? AND s.similarity_score > 0.4
            """, (job_from,))
            result = cursor.fetchone()
            return result[0] if result else 1
        except:
            return 2  # Default moderate reach
    
    def _populate_template_variables(self, job_from: str, db_values: Dict, 
                                   dynamic_descriptors: Dict, include_organisational_deployment: bool) -> Dict:
        """Populate all template variables for content generation."""
        variables = {}
        
        # Basic job information
        variables['source_job_id'] = job_from
        variables['source_job_title'] = db_values.get('job_title', 'Unknown Job')
        variables['job_function'] = db_values.get('job_function', 'Unknown Function')
        variables['management_level'] = db_values.get('management_level', 'Unknown Level')
        
        # Use display manager for logical display name if available
        if self.display_manager:
            try:
                variables['source_job_logical_display_name'] = self.display_manager.get_logical_display_name(job_from)
            except Exception as e:
                print(f"⚠️ Error getting logical display name: {e}")
                variables['source_job_logical_display_name'] = variables['source_job_title']
        else:
            variables['source_job_logical_display_name'] = variables['source_job_title']
        
        # Skills information
        variables['total_skills'] = db_values.get('total_skills', 0)
        variables['skill_category_count'] = db_values.get('skill_category_count', 0)
        variables['skill_categories'] = db_values.get('skill_categories', [])
        
        # Organizational deployment
        variables['include_organisational_deployment'] = include_organisational_deployment
        variables['position_count'] = db_values.get('position_count', 0)
        variables['division_count'] = db_values.get('division_count', 0)
        
        # Strategic metrics
        variables['mobility_hub_score'] = round(db_values.get('mobility_hub_score', 50), 1)
        variables['transition_readiness'] = round(db_values.get('transition_readiness', 60), 1)
        variables['cross_family_reach'] = db_values.get('cross_family_reach', 2)
        
        # Skills overlap analysis (from database)
        variables['skills_overlap_job_count'] = db_values.get('skills_overlap_job_count', 0)
        variables['total_job_count'] = db_values.get('total_job_count', 0)
        variables['transferability_descriptor'] = db_values.get('transferability_descriptor', 'limited')
        variables['skill_categories_summary'] = db_values.get('skill_categories_summary', 'Analysis unavailable')
        variables['skill_demand_instances'] = db_values.get('skill_demand_instances', 'Data unavailable')
        
        # Job function statistics (from database)
        variables['function_position_count'] = db_values.get('function_position_count', 0)
        variables['function_percentage'] = db_values.get('function_percentage', 0)
        variables['function_significance_descriptor'] = db_values.get('function_significance_descriptor', 'specialised')
        
        # Cross-functional analysis (from database)
        variables['cross_functional_areas'] = db_values.get('cross_functional_areas', 'Analysis unavailable')
        variables['management_level_range'] = db_values.get('management_level_range', 'Analysis unavailable')
        variables['career_progression_descriptor'] = db_values.get('career_progression_descriptor', 'limited')
        variables['functional_discipline'] = db_values.get('functional_discipline', 'technical')
        
        # Additional template variables from template analysis
        variables['primary_locations'] = "Sydney, Melbourne, Brisbane (primary hubs)"
        variables['primary_skill_category'] = db_values.get('skill_categories', [{}])[0].get('name', 'Technical') if db_values.get('skill_categories') else 'Technical'
        variables['role_capability_descriptor'] = "specialised" if variables['total_skills'] > 30 else "foundational"
        
        # Mobility assessments
        mobility_score = variables['mobility_hub_score']
        if mobility_score >= 75:
            variables['mobility_hub_assessment'] = "Excellent Mobility Hub"
            variables['mobility_strategic_value'] = "strategic mobility hub"
            variables['mobility_pathway_description'] = "extensive pathway opportunities"
        elif mobility_score >= 50:
            variables['mobility_hub_assessment'] = "Good Mobility Potential"
            variables['mobility_strategic_value'] = "valuable mobility point"
            variables['mobility_pathway_description'] = "solid pathway options"
        else:
            variables['mobility_hub_assessment'] = "Developing Mobility"
            variables['mobility_strategic_value'] = "emerging mobility candidate"
            variables['mobility_pathway_description'] = "focused pathway development"
        
        # Transition readiness assessments
        transition_score = variables['transition_readiness']
        if transition_score >= 75:
            variables['transition_readiness_assessment'] = "High Readiness"
            variables['transition_investment_descriptor'] = "minimal additional investment required"
            variables['transition_timeline_descriptor'] = "rapid transition capability"
        elif transition_score >= 50:
            variables['transition_readiness_assessment'] = "Moderate Readiness"
            variables['transition_investment_descriptor'] = "moderate skill development investment"
            variables['transition_timeline_descriptor'] = "structured transition planning"
        else:
            variables['transition_readiness_assessment'] = "Development Required"
            variables['transition_investment_descriptor'] = "substantial capability building required"
            variables['transition_timeline_descriptor'] = "extended development timelines"
        
        # Cross-family diversity assessment
        cross_family_reach = variables['cross_family_reach']
        if cross_family_reach >= 4:
            variables['cross_family_diversity_assessment'] = "High Cross-Functional Mobility"
            variables['connected_functions_list'] = "Technology, Operations, Risk, Customer, Commercial functions"
            variables['organisational_agility_descriptor'] = "exceptional organisational agility"
        elif cross_family_reach >= 2:
            variables['cross_family_diversity_assessment'] = "Moderate Cross-Functional Reach"
            variables['connected_functions_list'] = "Technology, Operations, Customer functions"
            variables['organisational_agility_descriptor'] = "good organisational agility"
        else:
            variables['cross_family_diversity_assessment'] = "Limited Cross-Functional Scope"
            variables['connected_functions_list'] = "primarily within immediate function"
            variables['organisational_agility_descriptor'] = "focused functional agility"
        
        # Strategic value assessment
        combined_score = (mobility_score + transition_score + (cross_family_reach * 20)) / 3
        if combined_score >= 70:
            variables['strategic_value_assessment'] = "High Strategic Value"
            variables['strategic_value_descriptor'] = "critical workforce capability"
            variables['workforce_planning_priority'] = "high-priority workforce assets"
            variables['investment_return_descriptor'] = "excellent return on investment"
            variables['organisational_resilience_descriptor'] = "enhanced organisational resilience"
        elif combined_score >= 50:
            variables['strategic_value_assessment'] = "Moderate Strategic Value"
            variables['strategic_value_descriptor'] = "valuable workforce capability"
            variables['workforce_planning_priority'] = "important workforce resources"
            variables['investment_return_descriptor'] = "solid return on investment"
            variables['organisational_resilience_descriptor'] = "improved organisational flexibility"
        else:
            variables['strategic_value_assessment'] = "Developing Strategic Value"
            variables['strategic_value_descriptor'] = "emerging workforce capability"
            variables['workforce_planning_priority'] = "development-focused positions"
            variables['investment_return_descriptor'] = "long-term investment potential"
            variables['organisational_resilience_descriptor'] = "specialised resilience contribution"
        
        # Workforce architecture significance
        variables['workforce_architecture_significance'] = f"{variables['strategic_value_assessment'].lower()} component in NAB's workforce architecture"
        variables['key_metric_convergence'] = f"{variables['mobility_hub_assessment'].lower()}, {variables['transition_readiness_assessment'].lower()}, and {variables['cross_family_diversity_assessment'].lower()}"
        variables['workforce_agility_potential'] = f"{variables['organisational_agility_descriptor']} and strategic workforce positioning"
        
        # Dynamic descriptors
        variables.update(dynamic_descriptors)
        
        return variables
    
    def _generate_content_sections(self, template_variables: Dict) -> Dict:
        """Generate all content sections using template variables."""
        content_sections = {}
        
        # Get the current role context template
        current_role_template = self.template_data.get('current_role_context', {})
        
        # Generate each section defined in the YAML template
        for section_key, section_config in current_role_template.items():
            if section_key in ['section_title', 'section_config']:
                continue  # Skip metadata
            
            try:
                if isinstance(section_config, dict) and 'content' in section_config:
                    # Render the title template as well
                    title_template = Template(section_config.get('title', section_key.replace('_', ' ').title()))
                    rendered_title = title_template.render(**template_variables)
                    
                    content_template = Template(section_config['content'])
                    rendered_content = content_template.render(**template_variables)
                    
                    content_sections[section_key] = {
                        'title': rendered_title,
                        'content': rendered_content,
                        'content_type': section_config.get('content_type', 'paragraph')
                    }
            except Exception as e:
                print(f"⚠️ Error generating section {section_key}: {e}")
                content_sections[section_key] = {
                    'title': section_key.replace('_', ' ').title(),
                    'content': f"Error generating content: {e}",
                    'content_type': 'paragraph'
                }
        
        return content_sections
    
    def _get_skills_overlap_analysis(self, job_from: str) -> Dict:
        """Get skills overlap analysis for template variables."""
        try:
            cursor = self.db.cursor()
            
            # Get total job count in database
            cursor.execute("SELECT COUNT(DISTINCT JobProfileID) FROM core_job_architecture")
            total_jobs_result = cursor.fetchone()
            total_job_count = total_jobs_result[0] if total_jobs_result else 0
            
            # Get skills overlap job count (jobs that share at least one skill)
            cursor.execute("""
                SELECT COUNT(DISTINCT js2.JobProfileID)
                FROM core_job_skill_requirements js1
                JOIN core_job_skill_requirements js2 ON js1.Skill_ID = js2.Skill_ID
                WHERE js1.JobProfileID = ? AND js2.JobProfileID != ?
            """, (job_from, job_from))
            overlap_result = cursor.fetchone()
            skills_overlap_job_count = overlap_result[0] if overlap_result else 0
            
            # Calculate transferability descriptor
            if total_job_count > 0:
                overlap_percentage = (skills_overlap_job_count / total_job_count) * 100
                if overlap_percentage >= 70:
                    transferability_descriptor = "high"
                elif overlap_percentage >= 40:
                    transferability_descriptor = "moderate"
                else:
                    transferability_descriptor = "limited"
            else:
                transferability_descriptor = "limited"
            
            # Get skill categories summary
            cursor.execute("""
                SELECT s.Category, COUNT(DISTINCT js.Skill_ID) as skill_count
                FROM core_job_skill_requirements js 
                JOIN core_skills_taxonomy s ON js.Skill_ID = s.Skill_ID 
                WHERE js.JobProfileID = ?
                GROUP BY s.Category
                ORDER BY skill_count DESC
                LIMIT 3
            """, (job_from,))
            top_categories = cursor.fetchall()
            skill_categories_summary = ", ".join([f"{cat[0]} ({cat[1]} skills)" for cat in top_categories])
            
            return {
                'total_job_count': total_job_count,
                'skills_overlap_job_count': skills_overlap_job_count,
                'transferability_descriptor': transferability_descriptor,
                'skill_categories_summary': skill_categories_summary,
                'skill_demand_instances': f"Applied across {skills_overlap_job_count} different role types"
            }
            
        except Exception as e:
            print(f"⚠️ Error in skills overlap analysis: {e}")
            return {
                'total_job_count': 0,
                'skills_overlap_job_count': 0,
                'transferability_descriptor': 'limited',
                'skill_categories_summary': 'Analysis unavailable',
                'skill_demand_instances': 'Data unavailable'
            }
    
    def _get_job_function_statistics(self, job_from: str) -> Dict:
        """Get job function statistics for template variables."""
        try:
            cursor = self.db.cursor()
            
            # Get job function for this role
            cursor.execute("""
                SELECT JobFunction FROM core_job_architecture WHERE JobProfileID = ?
            """, (job_from,))
            function_result = cursor.fetchone()
            job_function = function_result[0] if function_result else "Unknown"
            
            # Get total positions in NAB
            cursor.execute("SELECT COUNT(*) FROM core_workforce_current")
            total_positions_result = cursor.fetchone()
            total_positions = total_positions_result[0] if total_positions_result else 1
            
            # Get positions in this function
            cursor.execute("""
                SELECT COUNT(*)
                FROM core_workforce_current cwc
                JOIN core_job_architecture cja ON cwc.JobProfileID = cja.JobProfileID
                WHERE cja.JobFunction = ?
            """, (job_function,))
            function_positions_result = cursor.fetchone()
            function_position_count = function_positions_result[0] if function_positions_result else 0
            
            # Calculate percentage
            function_percentage = round((function_position_count / total_positions) * 100, 1) if total_positions > 0 else 0
            
            # Determine significance descriptor
            if function_percentage >= 20:
                function_significance_descriptor = "major"
            elif function_percentage >= 10:
                function_significance_descriptor = "significant"
            elif function_percentage >= 5:
                function_significance_descriptor = "moderate"
            else:
                function_significance_descriptor = "specialised"
            
            return {
                'function_position_count': function_position_count,
                'function_percentage': function_percentage,
                'function_significance_descriptor': function_significance_descriptor
            }
            
        except Exception as e:
            print(f"⚠️ Error in job function statistics: {e}")
            return {
                'function_position_count': 0,
                'function_percentage': 0,
                'function_significance_descriptor': 'specialised'
            }
    
    def _get_cross_functional_analysis(self, job_from: str) -> Dict:
        """Get cross-functional analysis for template variables."""
        try:
            cursor = self.db.cursor()
            
            # Get job functions where this role's skills appear
            cursor.execute("""
                SELECT DISTINCT cja.JobFunction, COUNT(DISTINCT cja.JobProfileID) as job_count
                FROM core_job_skill_requirements js1
                JOIN core_job_skill_requirements js2 ON js1.Skill_ID = js2.Skill_ID
                JOIN core_job_architecture cja ON js2.JobProfileID = cja.JobProfileID
                WHERE js1.JobProfileID = ? AND js2.JobProfileID != ?
                GROUP BY cja.JobFunction
                ORDER BY job_count DESC
                LIMIT 5
            """, (job_from, job_from))
            cross_functions = cursor.fetchall()
            
            cross_functional_areas = ", ".join([f"{func[0]} ({func[1]} roles)" for func in cross_functions])
            if not cross_functional_areas:
                cross_functional_areas = "Limited cross-functional applications identified"
            
            # Get management level analysis
            cursor.execute("""
                SELECT DISTINCT cja.ManagementLevel
                FROM core_job_skill_requirements js1
                JOIN core_job_skill_requirements js2 ON js1.Skill_ID = js2.Skill_ID  
                JOIN core_job_architecture cja ON js2.JobProfileID = cja.JobProfileID
                WHERE js1.JobProfileID = ? AND js2.JobProfileID != ?
                ORDER BY cja.ManagementLevel
            """, (job_from, job_from))
            management_levels = [row[0] for row in cursor.fetchall() if row[0]]
            
            if len(management_levels) >= 3:
                management_level_range = f"{min(management_levels)} to {max(management_levels)}"
                career_progression_descriptor = "excellent"
            elif len(management_levels) >= 2:
                management_level_range = f"{min(management_levels)} to {max(management_levels)}"
                career_progression_descriptor = "good"
            else:
                management_level_range = "limited range"
                career_progression_descriptor = "limited"
            
            # Get functional discipline
            cursor.execute("""
                SELECT JobFunction FROM core_job_architecture WHERE JobProfileID = ?
            """, (job_from,))
            function_result = cursor.fetchone()
            functional_discipline = function_result[0].lower() if function_result and function_result[0] else "technical"
            
            return {
                'cross_functional_areas': cross_functional_areas,
                'management_level_range': management_level_range,
                'career_progression_descriptor': career_progression_descriptor,
                'functional_discipline': functional_discipline
            }
            
        except Exception as e:
            print(f"⚠️ Error in cross-functional analysis: {e}")
            return {
                'cross_functional_areas': 'Analysis unavailable',
                'management_level_range': 'Analysis unavailable',
                'career_progression_descriptor': 'limited',
                'functional_discipline': 'technical'
            }
    
    def _generate_references(self, job_from: str) -> Dict:
        """Generate reference data for the current role context."""
        return {
            'source_job': job_from,
            'reference_type': 'current_role_context',
            'generated_at': 'runtime'
        }