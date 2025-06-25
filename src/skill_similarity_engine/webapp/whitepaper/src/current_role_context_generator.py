"""
Current Role Context Generator
Generates the Current Role Context section for white papers using YAML templates and database queries.
Follows the proven ExecutiveSummaryGenerator pattern with logical role architecture support.
"""

import sqlite3
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
from jinja2 import Template

# Import SQL query modules and LogicalRoleManager from executive summary
try:
    from ..sql import query_loader, DatabaseReferenceCalculator
    from .executive_summary_generator import LogicalRoleManager
    from ..formatter import ContentFormatter
except ImportError:
    # Handle direct script execution
    try:
        from sql import query_loader, DatabaseReferenceCalculator
        from executive_summary_generator import LogicalRoleManager
        from formatter import ContentFormatter
    except ImportError:
        query_loader = None
        DatabaseReferenceCalculator = None
        LogicalRoleManager = None
        ContentFormatter = None

class CurrentRoleContextGenerator:
    """Generates current role context content using template-driven approach with logical role support."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.template_path = Path(__file__).parent.parent / 'templates' / 'sections' / 'current_role_context.yaml'
        self.template_data = self._load_template()
        
        # Initialize logical role manager if available
        if LogicalRoleManager:
            self.logical_role_manager = LogicalRoleManager(db_connection)
        else:
            self.logical_role_manager = None
        
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
    
    def generate(self, job_from: str, include_organisational_deployment: bool = False) -> Dict:
        """Generate current role context content for a given source job."""
        
        # Step 1: Get database-derived values
        db_values = self._get_database_values(job_from, include_organisational_deployment)
        
        # Step 2: Get skills analysis
        skills_analysis = self._get_skills_analysis(job_from)
        
        # Step 3: Get strategic intelligence metrics
        strategic_metrics = self._get_strategic_intelligence_metrics(job_from)
        
        # Step 4: Populate template variables
        template_variables = self._populate_template_variables(
            job_from, db_values, skills_analysis, strategic_metrics, include_organisational_deployment
        )
        
        # Step 5: Generate content sections
        content = self._generate_content_sections(template_variables)
        
        return {
            'section_title': 'Current Role Context',
            'content': content,
            'references': self._generate_references(job_from),
            'template_variables': template_variables  # For debugging
        }
    
    def _get_database_values(self, job_from: str, include_deployment: bool) -> Dict:
        """Execute database queries to get reference values with logical role support."""
        
        values = {}
        
        try:
            # Get source job details with logical role display
            if self.logical_role_manager:
                values['source_job_logical_display_name'] = self.logical_role_manager.get_logical_role_display_name(job_from)
            else:
                values['source_job_logical_display_name'] = self._get_job_title_fallback(job_from)
            
            # Get basic job information
            job_details = self._get_job_details(job_from)
            values.update(job_details)
            
            # Get total job count for context
            if self.ref_calc:
                values['total_job_count'] = self.ref_calc.ref_01_total_job_profiles()
            else:
                cursor = self.db.execute("SELECT COUNT(*) FROM jobs")
                values['total_job_count'] = cursor.fetchone()[0]
            
            # Get organisational deployment if requested
            if include_deployment:
                deployment_data = self._get_organisational_deployment(job_from)
                values.update(deployment_data)
                values['include_organisational_deployment'] = True
            else:
                values['include_organisational_deployment'] = False
            
        except Exception as e:
            print(f"⚠️ Error getting database values: {e}")
            import traceback
            traceback.print_exc()
            values = self._get_fallback_values(job_from)
        
        return values
    
    def _get_job_details(self, job_from: str) -> Dict:
        """Get basic job details from database."""
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
            print(f"⚠️ Error getting job details: {e}")
            return {
                'job_title': 'Unknown Job',
                'job_function': 'Unknown Function', 
                'management_level': 'Group 1',
                'job_category': 'Unknown Category'
            }
    
    def _get_job_title_fallback(self, job_from: str) -> str:
        """Fallback method to get job title when LogicalRoleManager is not available."""
        try:
            query = "SELECT JobProfile FROM jobs WHERE JobProfileID = ?"
            result = self.db.execute(query, (job_from,)).fetchone()
            return result[0] if result else job_from
        except:
            return job_from
    
    def _get_organisational_deployment(self, job_from: str) -> Dict:
        """Get organisational deployment data using the proven approach from ExecutiveSummaryGenerator."""
        try:
            # Use the same logical role grouping approach as ExecutiveSummaryGenerator
            # Get base job title for logical role grouping
            job_query = """
            SELECT JobProfile, ManagementLevel
            FROM jobs 
            WHERE JobProfileID = ?
            """
            job_result = self.db.execute(job_query, (job_from,)).fetchone()
            
            if not job_result:
                return {'has_deployment': False, 'position_count': 0, 'division_count': 0}
            
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
            division_results = self.db.execute(deployment_query, (like_pattern, base_job_title, management_level)).fetchall()
            
            # Get primary locations (concatenate Location + Rg + Cty)
            locations_query = """
            SELECT 
                (p.Location || ', ' || p.Rg || ', ' || p.Cty) as full_location,
                COUNT(*) as count 
            FROM positions p
            JOIN jobs j ON p.JobProfileID = j.JobProfileID
            WHERE (j.JobProfile LIKE ? OR j.JobProfile = ?)
              AND j.ManagementLevel = ?
              AND p.Location IS NOT NULL
            GROUP BY p.Location, p.Rg, p.Cty
            ORDER BY count DESC 
            LIMIT 3
            """
            locations = self.db.execute(locations_query, (like_pattern, base_job_title, management_level)).fetchall()
            
            if not division_results:
                return {'has_deployment': False, 'position_count': 0, 'division_count': 0}
            
            # Format divisional deployment data
            divisions = []
            total_positions = 0
            total_business_units = 0
            
            for division, pos_count, bu_count in division_results:
                divisions.append({
                    'name': division,
                    'position_count': pos_count,
                    'business_unit_count': bu_count
                })
                total_positions += pos_count
                total_business_units += bu_count
            
            # Create deployment summary matching ExecutiveSummaryGenerator pattern
            division_names = [d['name'] for d in divisions[:4]]  # Top 4 divisions
            division_summary = ", ".join(division_names[:3])
            if len(division_names) > 3:
                division_summary += f", and {len(division_names) - 3} other{'s' if len(division_names) > 4 else ''}"
            
            # Format primary locations
            primary_locations = ", ".join([f"{loc[0]} ({loc[1]})" for loc in locations]) if locations else "Not available"
            
            # Format divisional distribution for template
            divisional_distribution = []
            for i, div in enumerate(divisions):
                # Get first business unit for this division
                bu_query = """
                SELECT Business_Unit, COUNT(*) as count
                FROM positions p
                JOIN jobs j ON p.JobProfileID = j.JobProfileID
                WHERE (j.JobProfile LIKE ? OR j.JobProfile = ?)
                  AND j.ManagementLevel = ?
                  AND p.Division = ?
                  AND p.Business_Unit IS NOT NULL
                GROUP BY p.Business_Unit
                ORDER BY count DESC
                LIMIT 1
                """
                bu_result = self.db.execute(bu_query, (like_pattern, base_job_title, management_level, div['name'])).fetchone()
                primary_bu = bu_result[0] if bu_result else 'Unknown Business Unit'
                
                divisional_distribution.append({
                    'name': div['name'],
                    'count': div['position_count'],
                    'reference': str(19 + i),  # References 19, 20, 21, etc.
                    'business_unit': primary_bu
                })
            
            return {
                'has_deployment': True,
                'position_count': total_positions,
                'division_count': len(divisions),
                'primary_locations': primary_locations,
                'divisional_distribution': divisional_distribution,
                'deployment_summary': f"{total_positions} positions across {len(divisions)} division{'s' if len(divisions) != 1 else ''} ({division_summary})"
            }
            
        except Exception as e:
            print(f"⚠️ Error getting organisational deployment: {e}")
            return {
                'has_deployment': False,
                'position_count': 0,
                'division_count': 0,
                'primary_locations': 'Not available',
                'divisional_distribution': []
            }
    
    def _get_skills_analysis(self, job_from: str) -> Dict:
        """Get comprehensive skills analysis directly from database without hardcoded mappings."""
        try:
            # Get total skills for this job
            skills_count_query = """
            SELECT COUNT(DISTINCT js.Skill_ID) 
            FROM job_skills js 
            WHERE js.JobProfileID = ?
            """
            total_skills = self.db.execute(skills_count_query, (job_from,)).fetchone()[0]
            
            # Get skills grouped by their actual database categories
            skills_by_category_query = """
            SELECT 
                s.Category,
                COUNT(*) as skill_count,
                GROUP_CONCAT(s.Skill_Name, ', ') as skill_names
            FROM job_skills js
            JOIN skills s ON js.Skill_ID = s.Skill_ID
            WHERE js.JobProfileID = ?
            AND s.Category IS NOT NULL AND s.Category != ''
            GROUP BY s.Category
            ORDER BY skill_count DESC
            """
            
            category_results = self.db.execute(skills_by_category_query, (job_from,)).fetchall()
            
            # Create skill categories list using actual database categories
            skill_categories = []
            reference_counter = 23  # Starting reference number
            
            for category, count, skill_names in category_results:
                # Format skill names nicely
                skills_list = [name.strip() for name in skill_names.split(',') if name.strip()]
                skill_list_formatted = self._format_skills_list(skills_list)
                
                skill_categories.append({
                    'name': category,
                    'skill_count': count,
                    'reference': str(reference_counter),
                    'skill_list': skill_list_formatted
                })
                reference_counter += 1
            
            # Calculate additional metrics
            skills_overlap_count = self._get_skills_overlap_count(job_from)
            primary_category = skill_categories[0]['name'] if skill_categories else 'Information Technology'
            skill_demand = self._get_skill_demand_instances_real(primary_category)
            
            return {
                'total_skills': total_skills,
                'skill_categories': skill_categories,
                'skill_category_count': len(skill_categories),
                'skills_overlap_job_count': skills_overlap_count,
                'primary_skill_category': primary_category,
                'skill_demand_instances': skill_demand,
                'skill_categories_summary': ', '.join([f"{cat['name']} ({cat['skill_count']})" for cat in skill_categories])
            }
            
        except Exception as e:
            print(f"⚠️ Error getting skills analysis: {e}")
            return self._get_fallback_skills_analysis()
    
    def _format_skills_list(self, skills_list):
        """Format skills list to match gold standard presentation."""
        if not skills_list:
            return "No specific skills identified"
        
        # Take first 6-8 skills and format them nicely
        formatted_skills = []
        for skill in skills_list[:8]:  # Limit to reasonable number
            # Clean up skill names
            clean_skill = skill.strip()
            if clean_skill and clean_skill not in formatted_skills:
                formatted_skills.append(clean_skill)
        
        if len(formatted_skills) <= 3:
            return ', '.join(formatted_skills)
        else:
            # Split into lines like gold standard
            mid_point = len(formatted_skills) // 2
            line1 = ', '.join(formatted_skills[:mid_point])
            line2 = ', '.join(formatted_skills[mid_point:])
            return f"{line1}\n      - {line2}"
    
    def _get_skills_overlap_count(self, job_from: str) -> int:
        """Calculate how many jobs share skills with this role."""
        try:
            query = """
            SELECT COUNT(DISTINCT j.JobProfileID) 
            FROM jobs j 
            WHERE EXISTS (
                SELECT 1 FROM job_skills js1 
                JOIN job_skills js2 ON js1.Skill_ID = js2.Skill_ID 
                WHERE js1.JobProfileID = ? 
                AND js2.JobProfileID = j.JobProfileID 
                AND js1.JobProfileID != js2.JobProfileID
            )
            """
            result = self.db.execute(query, (job_from,)).fetchone()
            return result[0] if result else 400  # Fallback value
        except:
            return 400  # Fallback
    
    def _get_skill_demand_instances_real(self, category: str) -> int:
        """Calculate total instances of skills in this actual database category across organisation."""
        try:
            # Count job-skill instances where skills are in this exact category
            query = """
            SELECT COUNT(*) 
            FROM job_skills js 
            JOIN skills s ON js.Skill_ID = s.Skill_ID 
            WHERE s.Category = ?
            """
            
            result = self.db.execute(query, (category,)).fetchone()
            return result[0] if result else 1000  # Fallback value
        except Exception as e:
            print(f"⚠️ Error calculating skill demand for {category}: {e}")
            return 1000  # Fallback
    
    def _get_strategic_intelligence_metrics(self, job_from: str) -> Dict:
        """Calculate strategic intelligence metrics from actual database career pathways."""
        try:
            # Use job_similarities table instead of career_pathways (which may not exist yet)
            # Get mobility hub score - count of similar jobs
            mobility_query = """
            SELECT COUNT(*) as pathway_count
            FROM job_similarities 
            WHERE job_from = ?
            AND similarity_score >= 0.4
            """
            pathway_count = self.db.execute(mobility_query, (job_from,)).fetchone()[0]
            mobility_hub_score = min(100, (pathway_count * 100) // 12)  # Scale to 0-100
            
            # Get transition readiness - average similarity score of top pathways
            readiness_query = """
            SELECT AVG(similarity_score) as avg_similarity
            FROM job_similarities 
            WHERE job_from = ?
            AND similarity_score >= 0.4
            """
            result = self.db.execute(readiness_query, (job_from,)).fetchone()
            avg_similarity = result[0] if result and result[0] else 0.5
            transition_readiness = round(avg_similarity * 100) if avg_similarity else 50
            
            # Get cross-family reach - count distinct job functions in similar jobs
            reach_query = """
            SELECT COUNT(DISTINCT j.JobFunction) as function_count
            FROM job_similarities js
            JOIN jobs j ON js.job_to = j.JobProfileID
            WHERE js.job_from = ?
            AND js.similarity_score >= 0.4
            """
            reach_result = self.db.execute(reach_query, (job_from,)).fetchone()
            cross_family_reach = reach_result[0] if reach_result else 3
            
            # Get connected functions list
            functions_query = """
            SELECT DISTINCT j.JobFunction
            FROM job_similarities js
            JOIN jobs j ON js.job_to = j.JobProfileID
            WHERE js.job_from = ?
            AND js.similarity_score >= 0.4
            AND j.JobFunction IS NOT NULL AND j.JobFunction != ''
            LIMIT 5
            """
            functions = self.db.execute(functions_query, (job_from,)).fetchall()
            connected_functions_list = ', '.join([f[0] for f in functions]) if functions else 'Various functions'
            
            # Determine assessments based on actual values
            mobility_assessment = self._get_mobility_assessment(mobility_hub_score)
            readiness_assessment = self._get_readiness_assessment(transition_readiness)
            diversity_assessment = self._get_diversity_assessment(cross_family_reach)
            strategic_value = self._get_strategic_value_assessment(mobility_hub_score, transition_readiness, cross_family_reach)
            
            return {
                'mobility_hub_score': mobility_hub_score,
                'mobility_hub_assessment': mobility_assessment,
                'mobility_strategic_value': self._get_mobility_value_description(mobility_hub_score),
                'mobility_pathway_description': self._get_pathway_description(pathway_count),
                'transition_readiness': transition_readiness,
                'transition_readiness_assessment': readiness_assessment,
                'transition_investment_descriptor': self._get_investment_descriptor(transition_readiness),
                'transition_timeline_descriptor': self._get_timeline_descriptor(transition_readiness),
                'cross_family_reach': cross_family_reach,
                'cross_family_diversity_assessment': diversity_assessment,
                'connected_functions_list': connected_functions_list,
                'organisational_agility_descriptor': self._get_agility_descriptor(cross_family_reach),
                'strategic_value_assessment': strategic_value,
                'strategic_value_descriptor': self._get_value_descriptor(strategic_value),
                'workforce_planning_priority': self._get_planning_priority(strategic_value),
                'investment_return_descriptor': self._get_return_descriptor(strategic_value),
                'organisational_resilience_descriptor': self._get_resilience_descriptor(strategic_value),
                'workforce_architecture_significance': self._get_architecture_significance(strategic_value),
                'key_metric_convergence': f'{readiness_assessment.lower()} transition readiness ({transition_readiness}%) and {diversity_assessment.lower().replace(" diversity", "")} cross-family reach ({cross_family_reach} functions)',
                'workforce_agility_potential': self._get_agility_potential(transition_readiness, cross_family_reach)
            }
            
        except Exception as e:
            print(f"⚠️ Error calculating strategic intelligence metrics: {e}")
            return self._get_fallback_strategic_metrics()
    
    def _populate_template_variables(self, job_from: str, db_values: Dict, 
                                   skills_analysis: Dict, strategic_metrics: Dict, 
                                   include_deployment: bool) -> Dict:
        """Populate all template variables for current role context."""
        
        variables = {
            # Basic job context
            **db_values,
            
            # Skills analysis
            **skills_analysis,
            
            # Strategic metrics
            **strategic_metrics,
            
            # Additional calculated values from database
            'total_skills_database': self._get_total_skills_in_database(),
            'functional_discipline': self._get_functional_discipline(db_values.get('job_function', 'Unknown')),
            'role_capability_descriptor': self._get_role_capability_descriptor(db_values.get('job_function', 'Unknown')),
            'transferability_descriptor': self._get_transferability_descriptor(skills_analysis.get('skills_overlap_job_count', 0)),
            'demand_level_descriptor': self._get_demand_level_descriptor(skills_analysis.get('skill_demand_instances', 0)),
            'function_significance_descriptor': 'specialised but significant',
            'career_progression_descriptor': 'extensive career',
            'function_position_count': self._get_function_position_count(db_values.get('job_function', 'Unknown')),
            'function_percentage': self._get_function_percentage(db_values.get('job_function', 'Unknown')),
            'management_level_range': self._get_management_level_range(db_values.get('job_function', 'Unknown')),
            'cross_functional_areas': self._get_cross_functional_areas(),
        }
        
        return variables
    
    def _generate_content_sections(self, variables: Dict) -> Dict:
        """Generate content for each section using structured content approach."""
        
        template_sections = self.template_data.get('current_role_context', {})
        content = {}
        
        try:
            # Profile Overview - Structured bullet list
            content['profile_overview'] = self._generate_profile_overview(template_sections.get('profile_overview', {}), variables)
            
            # Core Competency Foundation - Mixed content with paragraphs and skill categories
            content['core_competency_foundation'] = self._generate_core_competency_foundation(template_sections.get('core_competency_foundation', {}), variables)
            
            # Strategic Value Proposition - Mixed content with sections and bullet points
            content['strategic_value_proposition'] = self._generate_strategic_value_proposition(template_sections.get('strategic_value_proposition', {}), variables)
            
            # Strategic Intelligence Metrics - Complex structured content
            content['strategic_intelligence_metrics'] = self._generate_strategic_intelligence_metrics(template_sections.get('strategic_intelligence_metrics', {}), variables)
            
        except Exception as e:
            print(f"⚠️ Error generating content sections: {e}")
            import traceback
            traceback.print_exc()
            content = {'error': f'Content generation failed: {e}'}
        
        return content
    
    def _generate_profile_overview(self, profile_config: Dict, variables: Dict) -> Dict:
        """Generate structured profile overview content."""
        
        if not ContentFormatter:
            # Fallback to legacy approach if ContentFormatter not available
            return {
                'title': Template(profile_config.get('title', '')).render(**variables),
                'content': Template(profile_config.get('content', '')).render(**variables)
            }
        
        title = Template(profile_config.get('title', '')).render(**variables)
        
        # Only include content if organisational deployment is enabled
        if variables.get('include_organisational_deployment', False):
            content_template = Template(profile_config.get('content', '')).render(**variables)
            bold_labels = profile_config.get('bold_labels', [])
            
            return {
                'title': title,
                'content': ContentFormatter.create_formatted_content(
                    text=content_template,
                    formatting={
                        'content_type': 'bullet_list',
                        'bold_labels': bold_labels
                    }
                )
            }
        else:
            # Return empty structured content when deployment not included
            return {
                'title': title,
                'content': ContentFormatter.create_paragraph("", [])
            }
    
    def _generate_core_competency_foundation(self, core_config: Dict, variables: Dict) -> Dict:
        """Generate structured core competency foundation content."""
        
        if not ContentFormatter:
            # Fallback to legacy approach
            return {
                'title': core_config.get('title', 'Core Competency Foundation'),
                'content': Template(core_config.get('content', '')).render(**variables)
            }
        
        title = core_config.get('title', 'Core Competency Foundation')
        
        # Generate intro paragraph
        intro_text = Template(core_config.get('paragraph_intro', '')).render(**variables)
        
        # Generate skill categories with formatting
        skill_categories = variables.get('skill_categories', [])
        if skill_categories:
            # Create formatted skill categories text
            categories_text = ""
            for category in skill_categories:
                categories_text += f"{category['name']} ({category['skill_count']} skills): {category['skill_list']}\n"
            
            # Combine intro and categories
            full_text = f"{intro_text}\n\n{categories_text.strip()}"
            
            # Create bold labels from category names
            bold_labels = [f"{cat['name']} ({cat['skill_count']} skills):" for cat in skill_categories]
            
            return {
                'title': title,
                'content': ContentFormatter.create_formatted_content(
                    text=full_text,
                    formatting={
                        'content_type': 'mixed',
                        'bold_labels': bold_labels
                    }
                )
            }
        else:
            # No skill categories available
            return {
                'title': title,
                'content': ContentFormatter.create_paragraph(intro_text, [])
            }
    
    def _generate_strategic_value_proposition(self, strategic_config: Dict, variables: Dict) -> Dict:
        """Generate structured strategic value proposition content."""
        
        if not ContentFormatter:
            # Fallback to legacy approach
            return {
                'title': strategic_config.get('title', 'Strategic Value Proposition'),
                'content': Template(strategic_config.get('content', '')).render(**variables)
            }
        
        title = strategic_config.get('title', 'Strategic Value Proposition')
        
        # Generate intro paragraph
        intro_text = Template(strategic_config.get('intro_paragraph', '')).render(**variables)
        
        # Generate main content
        content_text = Template(strategic_config.get('content', '')).render(**variables)
        
        # Combine intro and content
        full_text = f"{intro_text}\n\n{content_text}"
        
        # Get bold labels from config
        bold_labels = strategic_config.get('bold_labels', [])
        bold_sub_labels = strategic_config.get('bold_sub_labels', [])
        
        # Combine all bold labels
        all_bold_labels = bold_labels + bold_sub_labels
        
        return {
            'title': title,
            'content': ContentFormatter.create_formatted_content(
                text=full_text,
                formatting={
                    'content_type': 'mixed',
                    'bold_labels': all_bold_labels
                }
            )
        }
    
    def _generate_strategic_intelligence_metrics(self, metrics_config: Dict, variables: Dict) -> Dict:
        """Generate structured strategic intelligence metrics content."""
        
        if not ContentFormatter:
            # Fallback to legacy approach
            return {
                'title': metrics_config.get('title', 'Strategic Intelligence Metrics'),
                'content': Template(metrics_config.get('content', '')).render(**variables)
            }
        
        title = metrics_config.get('title', 'Strategic Intelligence Metrics')
        sections = metrics_config.get('sections', {})
        bold_labels = metrics_config.get('bold_labels', [])
        
        # Build the complete content by combining all sections
        content_parts = []
        
        # Overview intro
        if 'overview_intro' in sections:
            intro_content = Template(sections['overview_intro']['content']).render(**variables)
            content_parts.append(intro_content)
        
        # Metrics overview bullet list
        if 'metrics_overview' in sections:
            metrics_list = Template(sections['metrics_overview']['content']).render(**variables)
            content_parts.append(metrics_list)
        
        # Context paragraph
        if 'context_paragraph' in sections:
            context_content = Template(sections['context_paragraph']['content']).render(**variables)
            content_parts.append(context_content)
        
        # Results header
        if 'results_header' in sections:
            results_header = Template(sections['results_header']['content']).render(**variables)
            content_parts.append(results_header)
        
        # Individual metric sections
        metric_sections = ['mobility_section', 'readiness_section', 'reach_section', 'value_section']
        for section_key in metric_sections:
            if section_key in sections:
                section_data = sections[section_key]
                header = Template(section_data['header']).render(**variables)
                content = Template(section_data['content']).render(**variables)
                content_parts.append(f"{header}\n{content}")
        
        # Conclusion paragraph
        if 'conclusion_paragraph' in sections:
            conclusion_content = Template(sections['conclusion_paragraph']['content']).render(**variables)
            content_parts.append(conclusion_content)
        
        # Combine all parts
        full_content = '\n\n'.join(content_parts)
        
        return {
            'title': title,
            'content': ContentFormatter.create_formatted_content(
                text=full_content,
                formatting={
                    'content_type': 'mixed',
                    'bold_labels': bold_labels
                }
            )
        }
    
    def _generate_references(self, job_from: str) -> Dict:
        """Generate reference mappings for the current role context."""
        
        references = self.template_data.get('references', {})
        return references
    
    def _get_fallback_values(self, job_from: str) -> Dict:
        """Fallback values when database queries fail."""
        return {
            'source_job_logical_display_name': f'Job {job_from}',
            'job_title': 'Unknown Job',
            'job_function': 'Unknown Function',
            'management_level': 'Group 1',
            'job_category': 'Unknown Category',
            'total_job_count': 715,
            'include_organisational_deployment': False
        }
    
    def _get_fallback_skills_analysis(self) -> Dict:
        """Fallback skills analysis when database queries fail."""
        return {
            'total_skills': 20,
            'skill_categories': [
                {'name': 'Technical Skills', 'skill_count': 8, 'reference': '23', 'skill_list': 'Analysis skills'},
                {'name': 'Business Skills', 'skill_count': 6, 'reference': '24', 'skill_list': 'Communication skills'},
                {'name': 'Industry Skills', 'skill_count': 6, 'reference': '25', 'skill_list': 'Domain knowledge'}
            ],
            'skill_category_count': 3,
            'skills_overlap_job_count': 400,
            'primary_skill_category': 'Technical Skills',
            'skill_demand_instances': 1000,
            'skill_categories_summary': 'Technical Skills (8), Business Skills (6), Industry Skills (6)'
        }
    
    def _get_fallback_strategic_metrics(self) -> Dict:
        """Fallback strategic metrics when calculation fails."""
        return {
            'mobility_hub_score': 67,
            'mobility_hub_assessment': 'Medium Hub Potential',
            'transition_readiness': 82,
            'transition_readiness_assessment': 'High Readiness',
            'cross_family_reach': 5,
            'cross_family_diversity_assessment': 'Excellent Diversity',
            'strategic_value_assessment': 'HIGH'
        }
    
    # Database-driven helper methods for dynamic content
    def _get_total_skills_in_database(self) -> int:
        """Get total count of skills in database."""
        try:
            result = self.db.execute("SELECT COUNT(*) FROM skills").fetchone()
            return result[0] if result else 38430
        except:
            return 38430  # Fallback from schema
    
    def _get_functional_discipline(self, job_function: str) -> str:
        """Determine functional discipline based on job function."""
        if 'Analytics' in job_function or 'Data' in job_function:
            return 'analytical'
        elif 'Technology' in job_function or 'Engineering' in job_function:
            return 'technical'
        elif 'Business' in job_function or 'Management' in job_function:
            return 'business'
        else:
            return 'operational'
    
    def _get_role_capability_descriptor(self, job_function: str) -> str:
        """Get role capability descriptor based on function."""
        return self._get_functional_discipline(job_function)
    
    def _get_transferability_descriptor(self, overlap_count: int) -> str:
        """Determine transferability based on job overlap count."""
        if overlap_count > 500:
            return 'broad'
        elif overlap_count > 300:
            return 'moderate'
        else:
            return 'limited'
    
    def _get_demand_level_descriptor(self, demand_instances: int) -> str:
        """Determine demand level based on skill instances."""
        if demand_instances > 2000:
            return 'high'
        elif demand_instances > 1000:
            return 'moderate'
        else:
            return 'limited'
    
    def _get_function_position_count(self, job_function: str) -> int:
        """Get count of positions in this job function."""
        try:
            result = self.db.execute("SELECT COUNT(*) FROM jobs WHERE JobFunction = ?", (job_function,)).fetchone()
            return result[0] if result else 41
        except:
            return 41  # Fallback
    
    def _get_function_percentage(self, job_function: str) -> float:
        """Get percentage of total jobs this function represents."""
        try:
            total_jobs = self.db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            function_jobs = self._get_function_position_count(job_function)
            return round((function_jobs / total_jobs) * 100, 1) if total_jobs > 0 else 5.7
        except:
            return 5.7  # Fallback
    
    def _get_management_level_range(self, job_function: str) -> str:
        """Get management level range for this function."""
        try:
            query = """
            SELECT MIN(ManagementLevel), MAX(ManagementLevel) 
            FROM jobs 
            WHERE JobFunction = ? AND ManagementLevel IS NOT NULL AND ManagementLevel != ''
            """
            result = self.db.execute(query, (job_function,)).fetchone()
            if result and result[0] and result[1]:
                return f"{result[0]}-{result[1]}"
            else:
                return "Group 1-6"
        except:
            return "Group 1-6"  # Fallback
    
    def _get_cross_functional_areas(self) -> str:
        """Get cross-functional areas where similar skills appear."""
        try:
            # Get top 3 job functions by job count
            query = """
            SELECT JobFunction, COUNT(*) as job_count 
            FROM jobs 
            WHERE JobFunction IS NOT NULL AND JobFunction != ''
            GROUP BY JobFunction 
            ORDER BY job_count DESC 
            LIMIT 3
            """
            results = self.db.execute(query).fetchall()
            
            if results:
                areas = []
                for func, count in results:
                    areas.append(f"{func} ({count} roles)")
                return ', '.join(areas)
            else:
                return 'Operations & Processing (78 roles), Risk Management (55 roles), Finance & Treasury (54 roles)'
        except:
            return 'Operations & Processing (78 roles), Risk Management (55 roles), Finance & Treasury (54 roles)'
    
    # Assessment helper methods for strategic intelligence metrics
    def _get_mobility_assessment(self, score: int) -> str:
        """Convert mobility hub score to assessment."""
        if score >= 80: return "High Hub Potential"
        elif score >= 60: return "Medium Hub Potential"
        else: return "Limited Hub Potential"
    
    def _get_readiness_assessment(self, score: int) -> str:
        """Convert transition readiness to assessment."""
        if score >= 80: return "High Readiness"
        elif score >= 60: return "Medium Readiness"
        else: return "Low Readiness"
    
    def _get_diversity_assessment(self, count: int) -> str:
        """Convert cross-family reach to assessment."""
        if count >= 5: return "Excellent Diversity"
        elif count >= 3: return "Good Diversity"
        else: return "Limited Diversity"
    
    def _get_strategic_value_assessment(self, mobility: int, readiness: int, diversity: int) -> str:
        """Calculate overall strategic value."""
        avg_score = (mobility + readiness + (diversity * 20)) / 3  # Weight diversity higher
        if avg_score >= 70: return "HIGH"
        elif avg_score >= 50: return "MEDIUM"
        else: return "LOW"
    
    def _get_mobility_value_description(self, score: int) -> str:
        """Get mobility strategic value description."""
        if score >= 80: return "exceptional role for workforce flexibility"
        elif score >= 60: return "strategically valuable role for workforce flexibility"
        else: return "limited strategic flexibility"
    
    def _get_pathway_description(self, count: int) -> str:
        """Get pathway description based on count."""
        if count >= 10: return "extensive pathway options"
        elif count >= 5: return "sufficient pathway options"
        else: return "limited pathway options"
    
    def _get_investment_descriptor(self, readiness: int) -> str:
        """Get investment description based on readiness."""
        if readiness >= 80: return "minimal retraining investment required"
        elif readiness >= 60: return "moderate retraining investment required"
        else: return "significant retraining investment required"
    
    def _get_timeline_descriptor(self, readiness: int) -> str:
        """Get timeline description based on readiness."""
        if readiness >= 80: return "rapid workforce redeployment"
        elif readiness >= 60: return "standard workforce redeployment"
        else: return "extended workforce redeployment"
    
    def _get_agility_descriptor(self, count: int) -> str:
        """Get agility description based on reach."""
        if count >= 5: return "exceptional organisational agility"
        elif count >= 3: return "good organisational agility"
        else: return "limited organisational agility"
    
    def _get_value_descriptor(self, value: str) -> str:
        """Get value descriptor based on assessment."""
        if value == "HIGH": return "Key Position for Workforce Planning"
        elif value == "MEDIUM": return "Important Position for Development"
        else: return "Standard Position with Limited Strategic Value"
    
    def _get_planning_priority(self, value: str) -> str:
        """Get planning priority based on value."""
        if value == "HIGH": return "prime candidates for succession planning investments"
        elif value == "MEDIUM": return "suitable candidates for development programs"
        else: return "standard workforce planning consideration"
    
    def _get_return_descriptor(self, value: str) -> str:
        """Get return description based on value."""
        if value == "HIGH": return "optimal returns on development spending"
        elif value == "MEDIUM": return "good returns on development spending"
        else: return "limited returns on development spending"
    
    def _get_resilience_descriptor(self, value: str) -> str:
        """Get resilience description based on value."""
        if value == "HIGH": return "maximum organisational resilience benefits"
        elif value == "MEDIUM": return "moderate organisational resilience benefits"
        else: return "minimal organisational resilience benefits"
    
    def _get_architecture_significance(self, value: str) -> str:
        """Get architecture significance based on value."""
        if value == "HIGH": return "strategically significant role within NAB's workforce architecture"
        elif value == "MEDIUM": return "moderately significant role within NAB's workforce architecture"
        else: return "standard role within NAB's workforce architecture"
    
    def _get_agility_potential(self, readiness: int, diversity: int) -> str:
        """Get agility potential based on combined metrics."""
        if readiness >= 80 and diversity >= 4: return "exceptional workforce agility potential"
        elif readiness >= 60 and diversity >= 3: return "good workforce agility potential"
        else: return "limited workforce agility potential" 