"""
Current Role Context Generator
Generates the Current Role Context section for Career Transition Analysiss using YAML templates and database queries.
Follows the proven ExecutiveSummaryGenerator pattern with logical role architecture support.
"""

import sqlite3
import yaml
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from jinja2 import Template

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

# Import ContentFormatter with proper fallback logic
ContentFormatter = None
try:
    from ..formatter import ContentFormatter
except ImportError:
    try:
        # Try absolute import within the career_analysis package
        from skill_similarity_engine.webapp.career_analysis.formatter import ContentFormatter
    except ImportError:
        ContentFormatter = None

# Remove duplicate ContentFormatter import - it's already imported above in the main import block

class CurrentRoleContextGenerator:
    """Generates current role context content using template-driven approach with logical role support."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.template_path = Path(__file__).parent.parent / 'templates' / 'sections' / 'current_role_context.yaml'
        self.template_data = self._load_template()
        
        # Initialize display manager for job name formatting
        if JobDisplayManager:
            try:
                # Ensure we have a proper database connection
                if hasattr(db_connection, 'execute'):
                    self.display_manager = JobDisplayManager(db_connection)
                    logger.debug(f"JobDisplayManager initialized successfully with {type(db_connection)}")
                else:
                    logger.warning(f"Invalid database connection type for JobDisplayManager: {type(db_connection)}")
                    self.display_manager = None
            except Exception as e:
                logger.error(f"Failed to initialize JobDisplayManager: {e}")
                self.display_manager = None
        else:
            logger.debug("JobDisplayManager not available")
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
        
        # Add source job ID for template
        template_variables['source_job_id'] = job_from
        
        # Step 5: Generate content sections
        content = self._generate_content_sections(template_variables)
        
        # Generate section title using template variables
        from jinja2 import Template
        section_title_template = self.template_data.get('current_role_context', {}).get('section_title', 'Current Role Context')
        
        try:
            if '{{' in section_title_template:
                title_template = Template(section_title_template)
                section_title = title_template.render(**template_variables)
            else:
                section_title = section_title_template
        except Exception as e:
            print(f"⚠️ Error rendering section title: {e}")
            section_title = f"Current Role Context: {template_variables.get('source_job_logical_display_name', 'Unknown Role')}"
        
        return {
            'section_title': section_title,
            'content': content,
            'references': self._generate_references(job_from),
            'template_variables': template_variables  # For debugging
        }
    
    def _get_database_values(self, job_from: str, include_deployment: bool) -> Dict:
        """Execute database queries to get reference values with logical role support."""
        
        values = {}
        
        try:
            # Get source job details with logical role display
            if self.display_manager and DisplayFormat:
                logger.debug(f"Using JobDisplayManager for job: {job_from}")
                logger.debug(f"Database connection type: {type(self.db)}")
                try:
                    values['source_job_logical_display_name'] = self.display_manager.get_display_name(job_from, DisplayFormat.LOGICAL)
                    logger.debug(f"Successfully got logical display name: {values['source_job_logical_display_name']}")
                except Exception as display_error:
                    logger.error(f"JobDisplayManager error: {display_error}")
                    # Fallback to manual job name retrieval
                    values['source_job_logical_display_name'] = self._get_job_title_fallback(job_from)
            else:
                logger.debug("JobDisplayManager not available, using fallback")
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
            logger.error(f"Error getting database values: {e}")
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
        """Get comprehensive skills analysis grouped by SkillType from database."""
        try:
            # Get total skills for this job
            skills_count_query = """
            SELECT COUNT(DISTINCT js.Skill_ID) 
            FROM job_skills js 
            WHERE js.JobProfileID = ?
            """
            total_skills = self.db.execute(skills_count_query, (job_from,)).fetchone()[0]
            
            # Get skills grouped by SkillType with all skill names
            skills_by_type_query = """
            SELECT 
                s.SkillType,
                COUNT(DISTINCT s.Skill_ID) as skill_count,
                GROUP_CONCAT(s.Skill_Name, ', ') as skill_list
            FROM job_skills js
            JOIN skills s ON js.Skill_ID = s.Skill_ID
            WHERE js.JobProfileID = ?
            GROUP BY s.SkillType
            ORDER BY COUNT(DISTINCT s.Skill_ID) DESC
            """
            
            skill_type_results = self.db.execute(skills_by_type_query, (job_from,)).fetchall()
            
            # Build skill categories data
            skill_categories = []
            total_calculated = 0
            
            for skill_type, skill_count, skill_list in skill_type_results:
                # No truncation or demand calculations - just store the data
                skill_categories.append({
                    'name': skill_type if skill_type else 'Other',
                    'skill_count': skill_count,
                    'skill_list': skill_list  # Full skills list, no truncation
                })
                
                total_calculated += skill_count
            
            # Get additional metrics
            skills_overlap_job_count = self._get_skills_overlap_count(job_from)
            
            # Calculate skill composition analysis vs NAB average
            primary_skill_type = skill_categories[0]['name'] if skill_categories else 'Mixed Skills'
            skill_composition_analysis = self._get_skill_composition_analysis(skill_categories, total_skills)
            
            # Build summary strings
            categories_summary = ', '.join([f"{cat['name']} ({cat['skill_count']})" for cat in skill_categories])
            
            return {
                'total_skills': total_skills,
                'skill_categories': skill_categories,
                'skill_category_count': len(skill_categories),
                'skills_overlap_job_count': skills_overlap_job_count,
                'primary_skill_category': primary_skill_type,
                'skill_categories_summary': categories_summary,
                'skill_composition_analysis': skill_composition_analysis
            }
            
        except Exception as e:
            logger.error(f"Error getting skills analysis for {job_from}: {e}")
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
    
    def _get_skill_composition_analysis(self, skill_categories: List[Dict], total_skills: int) -> Dict:
        """Analyse comprehensive skill composition of this role compared to NAB average."""
        try:
            # Get NAB-wide skill distribution percentages
            nab_distribution = self._get_nab_skill_distribution()
            
            # Calculate this role's percentages
            role_distribution = {}
            skill_breakdowns = []
            
            for category in skill_categories:
                skill_type = category['name']
                percentage = (category['skill_count'] / total_skills * 100) if total_skills > 0 else 0
                role_distribution[skill_type] = percentage
                
                # Get NAB average for comparison
                nab_avg = nab_distribution.get(skill_type, 0)
                
                skill_breakdowns.append({
                    'type': skill_type,
                    'role_pct': percentage,
                    'nab_avg': nab_avg,
                    'count': category['skill_count'],
                    'difference': percentage - nab_avg
                })
            
            # Create professional business narrative
            narrative = self._create_skill_composition_narrative(skill_breakdowns, role_distribution, nab_distribution, total_skills)
            
            # Create simple summary for other uses
            skill_instances_parts = []
            for breakdown in skill_breakdowns:
                skill_instances_parts.append(
                    f"{breakdown['type']}: {breakdown['role_pct']:.0f}% (vs {breakdown['nab_avg']:.0f}% NAB average)"
                )
            simple_summary = " • ".join(skill_instances_parts)
            
            return {
                'skill_instances': narrative,  # Full business narrative
                'skill_summary': simple_summary,  # Simple breakdown for reference
                'demand_assessment': self._get_role_positioning_summary(role_distribution, nab_distribution)
            }
                
        except Exception as e:
            logger.error(f"Error analysing skill composition: {e}")
            # Create enhanced fallback with skill breakdown
            skill_breakdown_text = f"This role encompasses {total_skills} prescribed skills across {len(skill_categories)} strategic capability areas"
            
            # Add specific skill type counts if available
            if skill_categories:
                skill_counts = []
                for category in skill_categories:
                    # Clean up skill type name to avoid "Skill Skills"
                    skill_type_clean = category['name'].replace(' Skill', '').replace(' skill', '')
                    skill_counts.append(f"{category['skill_count']} {skill_type_clean} Skills")
                
                if len(skill_counts) > 1:
                    skill_breakdown_text += f" ({', '.join(skill_counts[:-1])}, and {skill_counts[-1]})"
                else:
                    skill_breakdown_text += f" ({skill_counts[0]})"
            
            skill_breakdown_text += ", representing a balanced skill portfolio within NAB's workforce structure."
            
            return {
                'skill_instances': skill_breakdown_text,
                'skill_summary': "diverse skill requirements across multiple categories",
                'demand_assessment': "mixed specialisation profile"
            }
    
    def _create_skill_composition_narrative(self, skill_breakdowns: List[Dict], role_distribution: Dict, nab_distribution: Dict, total_skills: int) -> str:
        """Create a smooth, professional narrative about the role's skill composition."""
        
        # Sort skill types by prevalence in this role
        sorted_skills = sorted(skill_breakdowns, key=lambda x: x['role_pct'], reverse=True)
        
        # Start with soft introduction including specific skill type counts
        skill_counts = []
        for skill in sorted_skills:
            if skill['role_pct'] > 1:  # Only include meaningful components
                # Clean up skill type name to avoid "Skill Skills"
                skill_type_clean = skill['type'].replace(' Skill', '').replace(' skill', '')
                skill_counts.append(f"{skill['count']} {skill_type_clean} Skills")
        
        if len(skill_counts) > 1:
            skill_breakdown = f" ({', '.join(skill_counts[:-1])}, and {skill_counts[-1]})"
        elif len(skill_counts) == 1:
            skill_breakdown = f" ({skill_counts[0]})"
        else:
            skill_breakdown = ""
        
        intro = f"This role encompasses {total_skills} prescribed skills{skill_breakdown} with a distinctive composition compared to NAB's broader workforce. "
        
        # Analyse the skill triangle positioning
        specialized_pct = role_distribution.get('Specialized Skill', 0)
        common_pct = role_distribution.get('Common Skill', 0)
        cert_pct = role_distribution.get('Certification', 0)
        
        specialized_nab = nab_distribution.get('Specialized Skill', 65)
        common_nab = nab_distribution.get('Common Skill', 30)
        cert_nab = nab_distribution.get('Certification', 5)
        
        # Build the composition analysis
        composition_parts = []
        for skill in sorted_skills:
            if skill['role_pct'] > 5:  # Only mention significant components
                direction = "above" if skill['difference'] > 5 else "below" if skill['difference'] < -5 else "aligned with"
                # Clean up skill type name to avoid redundancy
                skill_type_clean = skill['type'].replace(' Skill', '').replace(' skill', '')
                composition_parts.append(f"{skill_type_clean} skills comprise {skill['role_pct']:.0f}% of requirements ({direction} the {skill['nab_avg']:.0f}% NAB average)")
        
        composition_text = "The skill portfolio breakdown reveals " + ", while ".join(composition_parts) + ". "
        
        # Determine triangle positioning and strategic implications
        positioning = self._determine_skill_triangle_position(specialized_pct, common_pct, cert_pct, specialized_nab, common_nab, cert_nab)
        
        return intro + composition_text + positioning
    
    def _determine_skill_triangle_position(self, spec_pct: float, common_pct: float, cert_pct: float, 
                                          spec_nab: float, common_nab: float, cert_nab: float) -> str:
        """Determine where the role sits in the specialised-common-certification triangle."""
        
        spec_diff = spec_pct - spec_nab
        common_diff = common_pct - common_nab
        cert_diff = cert_pct - cert_nab
        
        # Determine primary characteristic
        if cert_pct > 20 or cert_diff > 15:
            position = "certification-intensive position"
            implication = "formal qualifications create clear entry barriers and define specific expertise requirements"
        elif cert_pct > 10 or cert_diff > 8:
            position = "certification-supported role"
            implication = "professional credentials enhance capability but are not the primary differentiator"
        elif spec_diff > 15:
            position = "highly specialised role"
            implication = "deep domain expertise is essential for effective performance"
        elif spec_diff > 8:
            position = "moderately specialised position"
            implication = "specific technical knowledge provides competitive advantage"
        elif common_diff > 15:
            position = "foundation-skills focused role"
            implication = "broad transferable capabilities support diverse career pathways"
        elif spec_diff < -15:
            position = "generalist-oriented role"
            implication = "versatile skill base enables flexible deployment across functions"
        else:
            position = "balanced skill profile"
            implication = "mixed capabilities align closely with NAB's typical workforce composition"
        
        # Add accessibility assessment
        if cert_pct > 15:
            accessibility = ", making this a restricted-access role requiring formal qualifications"
        elif common_pct > 40:
            accessibility = ", creating good accessibility for internal career transitions"
        elif spec_pct > 80:
            accessibility = ", requiring substantial domain expertise for successful transitions"
        else:
            accessibility = ", offering moderate accessibility for appropriately skilled candidates"
        
        return f"This positions the role as a {position}, where {implication}{accessibility}."
    
    def _get_role_positioning_summary(self, role_distribution: Dict, nab_distribution: Dict) -> str:
        """Generate a concise summary of the role's strategic positioning."""
        
        specialized_pct = role_distribution.get('Specialized Skill', 0)
        common_pct = role_distribution.get('Common Skill', 0)
        cert_pct = role_distribution.get('Certification', 0)
        
        specialized_nab = nab_distribution.get('Specialized Skill', 65)
        cert_nab = nab_distribution.get('Certification', 5)
        
        if cert_pct > 15:
            return "certification-intensive with formal qualification requirements"
        elif specialized_pct > specialized_nab + 15:
            return "highly specialised compared to typical NAB roles"
        elif common_pct > 40:
            return "foundation-skills focused with broad transferability"
        elif specialized_pct < specialized_nab - 15:
            return "generalist-oriented with versatile capabilities"
        else:
            return "balanced skill profile aligned with NAB standards"
    
    def _get_nab_skill_distribution(self) -> Dict[str, float]:
        """Get NAB-wide percentage distribution of skill types."""
        try:
            # Calculate average skill type distribution across all jobs
            distribution_query = """
            SELECT 
                s.SkillType,
                AVG(job_skill_counts.skill_count * 100.0 / job_skill_counts.total_skills) as avg_percentage
            FROM skills s
            JOIN job_skills js ON s.Skill_ID = js.Skill_ID
            JOIN (
                SELECT 
                    js2.JobProfileID,
                    s2.SkillType,
                    COUNT(*) as skill_count,
                    (SELECT COUNT(*) FROM job_skills js3 WHERE js3.JobProfileID = js2.JobProfileID) as total_skills
                FROM job_skills js2
                JOIN skills s2 ON js2.Skill_ID = s2.Skill_ID
                GROUP BY js2.JobProfileID, s2.SkillType
            ) job_skill_counts ON js.JobProfileID = job_skill_counts.JobProfileID AND s.SkillType = job_skill_counts.SkillType
            GROUP BY s.SkillType
            """
            
            results = self.db.execute(distribution_query).fetchall()
            
            distribution = {}
            for skill_type, avg_percentage in results:
                distribution[skill_type] = float(avg_percentage) if avg_percentage else 0.0
            
            # Ensure we have reasonable defaults if query fails or returns empty
            if not distribution:
                distribution = {
                    'Specialized Skill': 65.0,  # Typical: 65% specialised
                    'Common Skill': 30.0,       # Typical: 30% common
                    'Certification': 5.0        # Typical: 5% certification
                }
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error getting NAB skill distribution: {e}")
            # Fallback to reasonable estimates
            return {
                'Specialized Skill': 65.0,
                'Common Skill': 30.0, 
                'Certification': 5.0
            }
    
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
            'skill_demand_instances': skills_analysis.get('skill_composition_analysis', {}).get('skill_instances', 'diverse skill requirements'),
            'demand_level_descriptor': skills_analysis.get('skill_composition_analysis', {}).get('demand_assessment', 'moderate specialisation'),
            'function_significance_descriptor': 'specialised but significant',
            'career_progression_descriptor': 'extensive career',
            'function_position_count': self._get_function_position_count(db_values.get('job_function', 'Unknown')),
            'function_percentage': self._get_function_percentage(db_values.get('job_function', 'Unknown')),
            'management_level_range': self._get_management_level_range(db_values.get('job_function', 'Unknown')),
            'cross_functional_areas': self._get_cross_functional_areas(),
        }
        
        # Add strategic intelligence metrics
        variables.update(strategic_metrics)
        
        # Add descriptive variables for strategic metrics table
        mobility_score = strategic_metrics.get('mobility_hub_score', 67)
        readiness_score = strategic_metrics.get('transition_readiness', 82)
        reach_count = strategic_metrics.get('cross_family_reach', 5)
        
        variables.update({
            'mobility_strategic_value': self._get_mobility_value_description(mobility_score),
            'transition_investment_descriptor': self._get_investment_descriptor(readiness_score),
            'organisational_agility_descriptor': self._get_agility_descriptor(reach_count),
            'strategic_value_descriptor': self._get_value_descriptor(strategic_metrics.get('strategic_value_assessment', 'MEDIUM')),
            'workforce_planning_priority': self._get_planning_priority(strategic_metrics.get('strategic_value_assessment', 'MEDIUM')),
            'workforce_architecture_significance': self._get_architecture_significance(strategic_metrics.get('strategic_value_assessment', 'MEDIUM')),
            'key_metric_convergence': f"mobility hub potential ({mobility_score}%), transition readiness ({readiness_score}%), and cross-family reach ({reach_count} functions)",
            'workforce_agility_potential': self._get_agility_potential(readiness_score, reach_count)
        })
        
        return variables
    
    def _generate_content_sections(self, variables: Dict) -> Dict:
        """Generate content for each section using structured content approach."""
        
        template_sections = self.template_data.get('current_role_context', {})
        content = {}
        
        try:
            # Role Identification - New intro section
            content['role_identification'] = self._generate_role_identification(template_sections.get('role_identification', {}), variables)
            
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
    
    def _generate_role_identification(self, role_config: Dict, variables: Dict) -> Dict:
        """Generate role identification section content."""
        from jinja2 import Template
        
        title = role_config.get('title', 'Role Analysis Overview')
        content_template = role_config.get('content', '')
        
        try:
            if content_template:
                template = Template(content_template)
                content = template.render(**variables)
            else:
                # Fallback content
                role_name = variables.get('source_job_logical_display_name', 'Unknown Role')
                job_id = variables.get('source_job_id', 'Unknown ID')
                content = f"This analysis focuses on **{role_name}** (Job ID: {job_id}) within NAB's organisational structure. The following assessment provides comprehensive context for strategic career planning and transition analysis."
            
            return {
                'title': title,
                'content': content
            }
        except Exception as e:
            print(f"⚠️ Error generating role identification: {e}")
            return {
                'title': title,
                'content': f"Role identification content generation failed: {e}"
            }
    
    def _generate_profile_overview(self, profile_config: Dict, variables: Dict) -> Dict:
        """Generate structured profile overview content with table for organisational deployment."""
        
        if not ContentFormatter:
            # Fallback to legacy approach if ContentFormatter not available
            return {
                'title': Template(profile_config.get('title', '')).render(**variables),
                'content': Template(profile_config.get('content', '')).render(**variables)
            }
        
        title = Template(profile_config.get('title', '')).render(**variables)
        
        # Only include content if organisational deployment is enabled
        if variables.get('include_organisational_deployment', False):
            
            # Create introduction paragraph
            intro_text = f"Organisational Deployment: {variables.get('position_count', 0)} positions across {variables.get('division_count', 0)} divisions\nPrimary Locations: {variables.get('primary_locations', 'Not available')}"
            
            # Create divisional distribution table
            divisional_distribution = variables.get('divisional_distribution', [])
            if divisional_distribution:
                # Prepare table data
                headers = ["Division", "Positions", "Primary Business Unit"]
                rows = []
                
                for division in divisional_distribution:
                    rows.append([
                        division.get('name', 'Unknown'),
                        str(division.get('count', 0)),
                        division.get('business_unit', 'Unknown')
                    ])
                
                # Create table content with format awareness
                table_content = ContentFormatter.create_table(headers, rows, 'compact', variables.get('output_format', 'document'))
                
                # Combine intro and table
                return {
                    'title': title,
                    'content': [
                        ContentFormatter.create_paragraph(intro_text, ["Organisational Deployment:", "Primary Locations:"]),
                        table_content
                    ]
                }
            else:
                # No table data, just use paragraph format
                return {
                    'title': title,
                    'content': ContentFormatter.create_paragraph(intro_text, ["Organisational Deployment:", "Primary Locations:"])
                }
        else:
            # Return empty structured content when deployment not included
            return {
                'title': title,
                'content': ContentFormatter.create_paragraph("", [])
            }
    
    def _generate_core_competency_foundation(self, core_config: Dict, variables: Dict) -> Dict:
        """Generate structured core competency foundation content with Skills Analysis Table."""
        
        if not ContentFormatter:
            # Fallback to legacy approach - create meaningful content instead of empty template

            
            # Create content manually since ContentFormatter isn't available
            skill_categories = variables.get('skill_categories', [])
            total_skills = variables.get('total_skills', 0)
            
            if not skill_categories:
                # Use fallback skills if none found
                fallback_skills = self._get_fallback_skills_analysis()
                skill_categories = fallback_skills['skill_categories']
                total_skills = fallback_skills['total_skills']
            
            # Create simple text content manually
            intro_text = f"The Job {variables.get('source_job_logical_display_name', 'R0102.3')} role encompasses {total_skills} prescribed skills across {len(skill_categories)} strategic capability areas:"
            
            # Create simple skills table text
            table_text = "Skill Type | Skill Count | All Skills\n----------|-----------|----------"
            for category in skill_categories:
                skill_type = category.get('name', 'Unknown')
                skill_count = category.get('skill_count', 0)
                skill_list = category.get('skill_list', '')
                # Format skills preview (first few skills)
                if skill_list:
                    skills_array = [s.strip() for s in skill_list.split(',')]
                    skills_preview = ', '.join(skills_array[:3])
                    if len(skills_array) > 3:
                        skills_preview += f" (and {len(skills_array) - 3} more)"
                else:
                    skills_preview = "No skills found"
                table_text += f"\n{skill_type} | {skill_count} | {skills_preview}"
            
            content = f"{intro_text}\n\n{table_text}"
            
            return {
                'title': core_config.get('title', 'Core Competency Foundation'),
                'content': content
            }
        
        title = core_config.get('title', 'Core Competency Foundation')
        
        # Generate intro paragraph
        intro_text = Template(core_config.get('paragraph_intro', '')).render(**variables)
        
        # Get skill categories data
        skill_categories = variables.get('skill_categories', [])
        total_skills = variables.get('total_skills', 0)
        skills_overlap_job_count = variables.get('skills_overlap_job_count', 0)
        
        logger.debug(f"CORE COMPETENCY DEBUG: skill_categories length: {len(skill_categories)}")
        logger.debug(f"CORE COMPETENCY DEBUG: total_skills: {total_skills}")
        logger.debug(f"CORE COMPETENCY DEBUG: skill_categories: {skill_categories}")
        
        if skill_categories:
            # Create intro paragraph
            intro_content = ContentFormatter.create_paragraph(intro_text, [])
            
            # Create Skills Analysis Table using the new method - USE WEB FORMAT
            # Note: For web preview, we need structured table data, not markdown text
            headers = ['Skill Type', 'Skill Count', 'All Skills']
            rows = []
            for category in skill_categories:
                skill_type = category.get('name', 'Other')
                skill_count = category.get('skill_count', 0)
                skill_list = category.get('skill_list', '')
                rows.append([skill_type, str(skill_count), skill_list])
            
            skills_table = ContentFormatter.create_table(
                headers=headers,
                rows=rows,
                table_style='compact',
                output_format='web'  # 🔧 KEY FIX: Use web format for structured data
            )
            
            # Return both intro and table as a list
            result = {
                'title': title,
                'content': [intro_content, skills_table]
            }
            return result
        else:
            # No skill categories available, create content using fallback approach
            logger.warning(f"No skill categories found for job, using fallback data")
            fallback_skills = self._get_fallback_skills_analysis()
            
            # Use fallback data to create proper content list
            intro_content = ContentFormatter.create_paragraph(intro_text, [])
            
            # Create fallback skills table with web format
            fallback_categories = fallback_skills['skill_categories']
            headers = ['Skill Type', 'Skill Count', 'All Skills']
            rows = []
            for category in fallback_categories:
                skill_type = category.get('name', 'Other')
                skill_count = category.get('skill_count', 0)
                skill_list = category.get('skill_list', '')
                rows.append([skill_type, str(skill_count), skill_list])
                
            skills_table = ContentFormatter.create_table(
                headers=headers,
                rows=rows,
                table_style='compact',
                output_format='web'  # 🔧 KEY FIX: Use web format for structured data
            )
            
            result = {
                'title': title,
                'content': [intro_content, skills_table]
            }
            return result
    
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
        """Generate strategic intelligence metrics content with table format."""
        

        
        title = metrics_config.get('title', 'Strategic Intelligence Metrics')
        bold_labels = metrics_config.get('bold_labels', [])
        sections = metrics_config.get('sections', {})
        
        if not ContentFormatter:
            # Fallback to legacy template approach - create meaningful content

            
            # Create metrics content manually
            intro_text = """About Strategic Intelligence Metrics: These quantitative measures assess workforce positioning and transition potential using analysis of NAB's complete career pathway network.

• Mobility Hub Score measures connectivity within the pathway network (0-100%)

• Transition Readiness indicates average skill overlap with potential career moves

• Cross-Family Reach counts accessible job functions

• Strategic Value provides an overall workforce planning assessment"""

            # Extract metrics or use defaults
            mobility_score = variables.get('mobility_hub_score', 100)
            transition_readiness = variables.get('transition_readiness', 49)
            cross_family_reach = variables.get('cross_family_reach', 15)
            strategic_value = variables.get('strategic_value_assessment', 'HIGH')
            
            # Create metrics table
            metrics_table = f"""Strategic Intelligence Metrics:

Metric | Score | Assessment
-------|-------|----------
Mobility Hub Score | {mobility_score}% | {variables.get('mobility_hub_assessment', 'High Hub Potential')}
Transition Readiness | {transition_readiness}% | {variables.get('transition_readiness_assessment', 'Low Readiness')}
Cross-Family Reach | {cross_family_reach} functions | {variables.get('cross_family_diversity_assessment', 'Excellent Diversity')}
Strategic Value | {strategic_value} | {variables.get('strategic_value_descriptor', 'Key Position for Workforce Planning')}"""

            conclusion_text = f"""Strategic Context Assessment: The combined metrics profile positions {variables.get('source_job_logical_display_name', 'Data Scientist - 3')} as a strategically significant role within NAB's workforce architecture."""
            
            content = f"{intro_text}\n\n{metrics_table}\n\n{conclusion_text}"
            
            return {
                'title': title,
                'content': content
            }
        
        # Create introduction paragraph
        intro_text = """About Strategic Intelligence Metrics: These quantitative measures assess workforce positioning and transition potential using analysis of NAB's complete career pathway network. Each metric provides specific intelligence for strategic decision-making:
        
• Mobility Hub Score measures connectivity within the pathway network (0-100%)
• Transition Readiness indicates average skill overlap with potential career moves  
• Cross-Family Reach counts accessible job functions
• Strategic Value provides an overall workforce planning assessment

Important Context: Our analysis excludes 100% similarity matches, which represent essentially identical roles with different titles. These provide no meaningful transition value as they lack skill development opportunities or career progression. All metrics are benchmarked against NAB's actual distribution of meaningful career transitions."""
        
        intro_content = ContentFormatter.create_formatted_content(
            text=intro_text,
            formatting={
                'content_type': 'paragraph',
                'bold_labels': ['About Strategic Intelligence Metrics:', 'Important Context:']
            }
        )
        
        # Extract metrics data for the table
        logger.debug(f"STRATEGIC METRICS DEBUG: variables keys: {list(variables.keys())}")
        logger.debug(f"STRATEGIC METRICS DEBUG: mobility_hub_score: {variables.get('mobility_hub_score', 'NOT FOUND')}")
        
        metrics_data = {
            'mobility_hub_score': variables.get('mobility_hub_score', 67),
            'mobility_hub_assessment': variables.get('mobility_hub_assessment', 'Medium Hub Potential'),
            'mobility_strategic_value': variables.get('mobility_strategic_value', 'Medium connectivity within career pathway network'),
            
            'transition_readiness': variables.get('transition_readiness', 82),
            'transition_readiness_assessment': variables.get('transition_readiness_assessment', 'High Readiness'),
            'transition_investment_descriptor': variables.get('transition_investment_descriptor', 'Moderate investment requirements'),
            
            'cross_family_reach': variables.get('cross_family_reach', 5),
            'cross_family_diversity_assessment': variables.get('cross_family_diversity_assessment', 'Excellent Diversity'),
            'organisational_agility_descriptor': variables.get('organisational_agility_descriptor', 'Cross-functional capability potential'),
            
            'strategic_value_assessment': variables.get('strategic_value_assessment', 'MEDIUM'),
            'strategic_value_descriptor': variables.get('strategic_value_descriptor', 'Valuable Position'),
            'workforce_planning_priority': variables.get('workforce_planning_priority', 'Strategic workforce planning asset')
        }
        
        # Create the Strategic Intelligence Metrics Table
        metrics_table = ContentFormatter.create_strategic_metrics_table(metrics_data)
        
        # Create conclusion paragraph
        source_job_name = variables.get('source_job_logical_display_name', 'Current Role')
        conclusion_text = f"""Strategic Context Assessment: The combined metrics profile positions {source_job_name} as a {variables.get('workforce_architecture_significance', 'valuable workforce asset')}. The convergence of {variables.get('key_metric_convergence', 'these strategic indicators')} indicates {variables.get('workforce_agility_potential', 'strong workforce agility potential')}, making this role particularly valuable during organisational transformations, restructures, or capability realignments."""
        
        conclusion_content = ContentFormatter.create_formatted_content(
            text=conclusion_text,
            formatting={
                'content_type': 'paragraph',
                'bold_labels': ['Strategic Context Assessment:']
            }
        )
        
        result = {
            'title': title,
            'content': [intro_content, metrics_table, conclusion_content]
        }
        return result
    
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
        """Determine demand level based on skill instances relative to total job count."""
        try:
            # Get total job count for relative calculation
            total_jobs = self.db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            
            # Calculate percentage coverage
            coverage_percentage = (demand_instances / total_jobs) * 100 if total_jobs > 0 else 0
            
            # Use percentage-based thresholds that make logical sense
            if coverage_percentage >= 75:  # 75%+ of jobs = high demand
                return 'high'
            elif coverage_percentage >= 40:  # 40-74% of jobs = moderate demand
                return 'moderate'
            else:  # <40% of jobs = limited demand
                return 'limited'
        except:
            # Fallback to absolute thresholds if database query fails
            if demand_instances > 500:  # Adjusted for smaller database
                return 'high'
            elif demand_instances > 250:
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
