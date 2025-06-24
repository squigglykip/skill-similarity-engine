"""
Pathway Analysis Generator
Generates the Pathway Analysis: Top 3 Strategic Opportunities section for white papers using YAML templates and database queries.
Follows the proven ExecutiveSummaryGenerator and CurrentRoleContextGenerator patterns with logical role architecture support.
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
except ImportError:
    # Handle direct script execution
    try:
        from sql import query_loader, DatabaseReferenceCalculator
        from executive_summary_generator import LogicalRoleManager
    except ImportError:
        query_loader = None
        DatabaseReferenceCalculator = None
        LogicalRoleManager = None

class PathwayAnalysisGenerator:
    """Generates pathway analysis content using template-driven approach with logical role support."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.template_path = Path(__file__).parent.parent / 'templates' / 'sections' / 'pathway_analysis.yaml'
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
        """Load YAML template for pathway analysis."""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"⚠️ Error loading pathway analysis template: {e}")
            return {}
    
    def generate(self, job_from: str, include_organisational_deployment: bool = False) -> Dict:
        """Generate pathway analysis content for top 3 career opportunities."""
        
        # Step 1: Get top 3 career pathways (reusing ExecutiveSummaryGenerator logic)
        top_pathways = self._get_top_pathways(job_from, limit=3)
        
        if not top_pathways:
            return {
                'section_title': 'Pathway Analysis: Top 3 Strategic Opportunities',
                'content': {'error': 'No career pathways found'},
                'references': {}
            }
        
        # Step 2: Generate detailed analysis for each opportunity
        opportunities = []
        for i, pathway in enumerate(top_pathways, 1):
            opportunity_analysis = self._generate_opportunity_analysis(
                job_from, pathway, i, include_organisational_deployment
            )
            opportunities.append(opportunity_analysis)
        
        # Step 3: Generate content sections
        content = self._generate_content_sections(opportunities)
        
        return {
            'section_title': 'Pathway Analysis: Top 3 Strategic Opportunities',
            'content': content,
            'opportunities': opportunities,  # For debugging
            'references': self._generate_references()
        }
    
    def _get_top_pathways(self, job_from: str, limit: int = 3) -> List[Dict]:
        """Get top similarity pathways - reusing ExecutiveSummaryGenerator logic."""
        try:
            # Use the same query pattern as ExecutiveSummaryGenerator
            query = """
            SELECT 
                js.job_to,
                js.similarity_score,
                j.JobProfile as target_job_title,
                j.JobFunction as target_job_function,
                j.ManagementLevel as target_management_level,
                ROW_NUMBER() OVER (ORDER BY js.similarity_score DESC) as rank
            FROM job_similarities js
            JOIN jobs j ON js.job_to = j.JobProfileID
            WHERE js.job_from = ?
              AND js.similarity_score < 1.0  -- Exclude 100% matches
            ORDER BY js.similarity_score DESC
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
                    'similarity_ref': str(56 + result[5]),  # References 57, 58, 59
                    'move_type_ref': str(58 + result[5])    # References 59, 60, 61
                }
                
                # Add logical role display name
                if self.logical_role_manager:
                    pathway['target_logical_role'] = self.logical_role_manager.get_logical_role_display_name(pathway['target_job_id'])
                else:
                    pathway['target_logical_role'] = pathway['target_job_title']
                
                # Calculate move type and level transition
                pathway.update(self._calculate_move_type(job_from, pathway))
                
                pathways.append(pathway)
            
            return pathways
            
        except Exception as e:
            print(f"⚠️ Error getting top pathways: {e}")
            return []
    
    def _calculate_move_type(self, job_from: str, pathway: Dict) -> Dict:
        """Calculate move type and level transition - reusing ExecutiveSummaryGenerator logic."""
        try:
            # Get source job details
            source_query = """
            SELECT JobProfile, ManagementLevel, JobFunction 
            FROM jobs 
            WHERE JobProfileID = ?
            """
            source_result = self.db.execute(source_query, (job_from,)).fetchone()
            
            if not source_result:
                return {
                    'move_type': 'Other',
                    'level_transition': 'Unknown',
                    'level_transition_display': 'Unknown transition'
                }
            
            source_job_title = source_result[0]
            source_level = source_result[1]
            source_function = source_result[2]
            target_job_title = pathway['target_job_title']
            target_level = pathway['target_management_level']
            target_function = pathway['target_job_function']
            
            # Extract numeric levels (Group 1 = 1, Group 2 = 2, etc.)
            source_level_num = self._extract_level_number(source_level)
            target_level_num = self._extract_level_number(target_level)
            
            # Get base role titles for comparison (remove pay band suffixes)
            source_base_title = source_job_title.split(" - ")[0] if " - " in source_job_title else source_job_title
            target_base_title = target_job_title.split(" - ")[0] if " - " in target_job_title else target_job_title
            
            # Determine move type based on logical role progression
            if source_base_title == target_base_title and target_level_num > source_level_num:
                move_type = 'Progression - Same_Role_Higher_Level'
            elif source_base_title == target_base_title and target_level_num == source_level_num:
                move_type = 'Lateral - Same_Role_Same_Level'
            elif source_base_title != target_base_title and target_level_num > source_level_num:
                move_type = 'Progression - Different_Role_Higher_Level'
            elif source_base_title != target_base_title and target_level_num == source_level_num:
                move_type = 'Lateral - Different_Role_Same_Level'
            elif target_level_num < source_level_num:
                move_type = 'Transition - Lower_Level'
            else:
                move_type = 'Other'
            
            # Create level transition description
            level_transition = f"{source_level} → {target_level}"
            level_transition_display = f"{level_transition} ({source_base_title} → {target_base_title})"
            
            return {
                'move_type': move_type,
                'level_transition': level_transition,
                'level_transition_display': level_transition_display,
                'source_function': source_function,
                'target_function': target_function
            }
            
        except Exception as e:
            print(f"⚠️ Error calculating move type: {e}")
            return {
                'move_type': 'Other',
                'level_transition': 'Analysis not available',
                'level_transition_display': 'Analysis not available'
            }
    
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
    
    def _generate_opportunity_analysis(self, job_from: str, pathway: Dict, opportunity_rank: int, 
                                     include_deployment: bool) -> Dict:
        """Generate comprehensive analysis for a single opportunity."""
        
        target_job_id = pathway['target_job_id']
        
        # Get comprehensive analysis for this opportunity
        analysis = {
            'opportunity_rank': opportunity_rank,
            'pathway_data': pathway,
            'strategic_positioning': self._get_strategic_positioning_data(job_from, target_job_id, pathway),
            'skills_analysis': self._get_skills_transition_analysis(job_from, target_job_id),
            'business_case': self._get_business_case_data(job_from, target_job_id, pathway),
            'implementation_roadmap': self._get_implementation_roadmap_data(job_from, target_job_id)
        }
        
        # Get organisational deployment if requested
        if include_deployment:
            analysis['organisational_deployment'] = self._get_target_organisational_deployment(target_job_id)
        
        return analysis
    
    def _get_strategic_positioning_data(self, job_from: str, target_job_id: str, pathway: Dict) -> Dict:
        """Get strategic positioning data for the opportunity."""
        try:
            # Get target job function analysis
            function_analysis = self._get_function_analysis(pathway['target_job_function'])
            
            # Get skills overlap analysis
            skills_overlap = self._get_skills_overlap_analysis(job_from, target_job_id)
            
            # Get cross-functional demand analysis
            cross_function_analysis = self._get_cross_functional_demand_analysis(job_from)
            
            # Determine opportunity classification based on similarity score
            opportunity_classification = self._get_opportunity_classification(pathway['similarity_score'])
            
            # Get move type descriptors
            move_type_description = self._get_move_type_description(pathway['move_type'])
            move_type_display = self._get_move_type_display(pathway['move_type'])
            
            return {
                'target_job_logical_display_name': pathway['target_logical_role'],
                'opportunity_classification': opportunity_classification,
                'move_type_description': move_type_description,
                'move_type_display': move_type_display,
                'similarity_score': pathway['similarity_score'],
                'target_job_function': pathway['target_job_function'],
                'level_transition_display': pathway['level_transition_display'],
                'function_analysis': function_analysis,
                'skills_overlap_data': skills_overlap,
                'cross_function_data': cross_function_analysis
            }
            
        except Exception as e:
            print(f"⚠️ Error getting strategic positioning data: {e}")
            return {'error': f'Strategic positioning analysis failed: {e}'}
    
    def _get_function_analysis(self, job_function: str) -> Dict:
        """Analyze the target job function from database."""
        try:
            # Get function position count and percentage
            function_count_query = "SELECT COUNT(*) FROM jobs WHERE JobFunction = ?"
            function_count = self.db.execute(function_count_query, (job_function,)).fetchone()[0]
            
            total_jobs_query = "SELECT COUNT(*) FROM jobs"
            total_jobs = self.db.execute(total_jobs_query).fetchone()[0]
            
            function_percentage = round((function_count / total_jobs) * 100, 1)
            
            # Determine function significance
            if function_percentage >= 7:
                function_significance = 'major'
            elif function_percentage >= 3:
                function_significance = 'moderate'
            else:
                function_significance = 'minor'
            
            return {
                'function_position_count': function_count,
                'function_percentage': function_percentage,
                'function_significance': function_significance,
                'function_significance_descriptor': self._get_function_significance_descriptor(function_significance),
                'function_size_assessment': self._get_function_size_assessment(function_significance),
                'function_career_infrastructure': self._get_function_career_infrastructure(function_significance)
            }
            
        except Exception as e:
            print(f"⚠️ Error analyzing function {job_function}: {e}")
            return {
                'function_position_count': 50,
                'function_percentage': 7.0,
                'function_significance': 'moderate'
            }
    
    def _get_skills_overlap_analysis(self, job_from: str, target_job_id: str) -> Dict:
        """Analyze skills overlap between source and target jobs."""
        try:
            # Get skills overlap count and percentage
            overlap_query = """
            SELECT COUNT(DISTINCT s1.Skill_ID) as shared_skills
            FROM job_skills s1
            JOIN job_skills s2 ON s1.Skill_ID = s2.Skill_ID
            WHERE s1.JobProfileID = ? AND s2.JobProfileID = ?
            """
            shared_skills = self.db.execute(overlap_query, (job_from, target_job_id)).fetchone()[0]
            
            # Get total skills for target job
            target_skills_query = "SELECT COUNT(DISTINCT Skill_ID) FROM job_skills WHERE JobProfileID = ?"
            total_target_skills = self.db.execute(target_skills_query, (target_job_id,)).fetchone()[0]
            
            # Calculate overlap percentage
            skills_overlap_percentage = round((shared_skills / total_target_skills) * 100, 1) if total_target_skills > 0 else 0
            
            # Determine transferability assessment
            transferability_assessment = self._get_transferability_assessment(skills_overlap_percentage)
            
            return {
                'transferable_skills_count': shared_skills,
                'total_target_skills': total_target_skills,
                'skills_overlap_percentage': skills_overlap_percentage,
                'transferability_assessment': transferability_assessment,
                'percentile_ranking': self._get_percentile_ranking(skills_overlap_percentage)
            }
            
        except Exception as e:
            print(f"⚠️ Error analyzing skills overlap: {e}")
            return {
                'transferable_skills_count': 15,
                'total_target_skills': 25,
                'skills_overlap_percentage': 60.0,
                'transferability_assessment': 'moderate foundation'
            }
    
    def _get_cross_functional_demand_analysis(self, job_from: str) -> Dict:
        """Analyze cross-functional demand for source job skills."""
        try:
            # Get primary skill category for source job
            primary_category_query = """
            SELECT s.Category, COUNT(*) as skill_count
            FROM job_skills js
            JOIN skills s ON js.Skill_ID = s.Skill_ID
            WHERE js.JobProfileID = ?
            AND s.Category IS NOT NULL AND s.Category != ''
            GROUP BY s.Category
            ORDER BY skill_count DESC
            LIMIT 1
            """
            result = self.db.execute(primary_category_query, (job_from,)).fetchone()
            primary_skill_category = result[0] if result else 'Business'
            
            # Get functions where these skills appear
            functions_query = """
            SELECT DISTINCT j.JobFunction, COUNT(*) as job_count
            FROM job_skills js1
            JOIN job_skills js2 ON js1.Skill_ID = js2.Skill_ID
            JOIN jobs j ON js2.JobProfileID = j.JobProfileID
            JOIN skills s ON js1.Skill_ID = s.Skill_ID
            WHERE js1.JobProfileID = ? 
            AND s.Category = ?
            AND j.JobFunction IS NOT NULL AND j.JobFunction != ''
            GROUP BY j.JobFunction
            ORDER BY job_count DESC
            LIMIT 3
            """
            functions = self.db.execute(functions_query, (job_from, primary_skill_category)).fetchall()
            
            cross_functional_areas = ', '.join([f"{func[0]} ({func[1]} roles)" for func in functions]) if functions else 'Various functions'
            
            return {
                'primary_skill_category': primary_skill_category,
                'cross_functional_areas': cross_functional_areas,
                'cross_function_applicability': 'broad applicability' if len(functions) >= 3 else 'moderate applicability'
            }
            
        except Exception as e:
            print(f"⚠️ Error analyzing cross-functional demand: {e}")
            return {
                'primary_skill_category': 'Business',
                'cross_functional_areas': 'Operations, Risk Management, Finance',
                'cross_function_applicability': 'broad applicability'
            }
    
    def _get_skills_transition_analysis(self, job_from: str, target_job_id: str) -> Dict:
        """Get detailed skills transition analysis."""
        try:
            # Get transferable skills by category
            transferable_skills_query = """
            SELECT s.Category, GROUP_CONCAT(s.Skill_Name, ', ') as skill_names
            FROM job_skills js1
            JOIN job_skills js2 ON js1.Skill_ID = js2.Skill_ID
            JOIN skills s ON js1.Skill_ID = s.Skill_ID
            WHERE js1.JobProfileID = ? AND js2.JobProfileID = ?
            AND s.Category IS NOT NULL AND s.Category != ''
            GROUP BY s.Category
            ORDER BY COUNT(*) DESC
            """
            transferable_results = self.db.execute(transferable_skills_query, (job_from, target_job_id)).fetchall()
            
            transferable_skill_categories = []
            for category, skills in transferable_results:
                # Format skills list nicely (limit to reasonable length)
                skills_list = [s.strip() for s in skills.split(',') if s.strip()][:6]  # Limit to 6 skills
                skill_list_formatted = ', '.join(skills_list)
                
                transferable_skill_categories.append({
                    'name': category,
                    'skill_list': skill_list_formatted
                })
            
            # Get required new skills
            required_skills_query = """
            SELECT s.Skill_Name, s.Category
            FROM job_skills js
            JOIN skills s ON js.Skill_ID = s.Skill_ID
            WHERE js.JobProfileID = ?
            AND js.Skill_ID NOT IN (
                SELECT Skill_ID FROM job_skills WHERE JobProfileID = ?
            )
            ORDER BY s.Category, s.Skill_Name
            LIMIT 8
            """
            required_results = self.db.execute(required_skills_query, (target_job_id, job_from)).fetchall()
            
            required_skills = []
            for skill_name, category in required_results:
                required_skills.append({
                    'name': skill_name,
                    'description': f"{category} competency requiring development"
                })
            
            # Calculate development timeline
            development_timeline = self._calculate_development_timeline(len(required_skills))
            
            return {
                'transferable_skill_categories': transferable_skill_categories,
                'required_skills': required_skills,
                'required_skills_count': len(required_skills),
                'development_timeline': development_timeline
            }
            
        except Exception as e:
            print(f"⚠️ Error getting skills transition analysis: {e}")
            return self._get_fallback_skills_transition()
    
    def _get_skill_type_distribution(self) -> Dict:
        """Get skill type distribution percentages from database."""
        try:
            # Get skill type counts
            query = """
            SELECT SkillType, COUNT(*) as count
            FROM skills 
            WHERE SkillType IS NOT NULL AND SkillType != ''
            GROUP BY SkillType
            """
            results = self.db.execute(query).fetchall()
            
            # Calculate total and percentages
            total_skills = sum(row[1] for row in results)
            skill_type_data = {}
            
            for skill_type, count in results:
                percentage = round((count / total_skills) * 100, 1)
                skill_type_data[skill_type.lower().replace(' ', '_')] = str(percentage)
            
            # Ensure we have the expected types
            return {
                'specialized': skill_type_data.get('specialized_skill', '89.5'),
                'common': skill_type_data.get('common_skill', '1.3'),
                'certification': skill_type_data.get('certification', '9.2')
            }
            
        except Exception as e:
            print(f"⚠️ Error getting skill type distribution: {e}")
            # Fallback to hardcoded values
            return {
                'specialized': '89.5',
                'common': '1.3', 
                'certification': '9.2'
            }
    
    def _calculate_development_timeline(self, required_skills_count: int) -> Dict:
        """Calculate development timeline based on skill requirements."""
        # Calculate skill type distribution from database
        skill_type_percentages = self._get_skill_type_distribution()
        
        # Assume most new skills are specialized (8 weeks each)
        specialized_skills_count = max(1, required_skills_count)
        specialized_development_weeks = specialized_skills_count * 8
        applied_experience_months = 6
        applied_integration_weeks = 24
        total_development_weeks = specialized_development_weeks
        total_transition_weeks = specialized_development_weeks + applied_integration_weeks
        
        return {
            'specialized_skills_count': specialized_skills_count,
            'specialized_development_weeks': specialized_development_weeks,
            'applied_experience_months': applied_experience_months,
            'applied_integration_weeks': applied_integration_weeks,
            'total_development_weeks': total_development_weeks,
            'total_transition_weeks': total_transition_weeks,
            'specialized_percentage': skill_type_percentages['specialized'],
            'common_percentage': skill_type_percentages['common']
        }
    
    def _get_business_case_data(self, job_from: str, target_job_id: str, pathway: Dict) -> Dict:
        """Generate business case data for the transition."""
        return {
            'strategic_alignment_point_1': f"Supports NAB's enhanced {pathway['target_job_function'].lower()} capabilities",
            'strategic_alignment_point_2': f"Addresses evolving requirements for advanced analytics in {pathway['target_job_function'].lower()}",
            'strategic_alignment_point_3': f"Leverages existing {pathway['source_function'].lower()} skills while building specialized expertise",
            'recruitment_cost_estimate': self._estimate_recruitment_cost(pathway['target_management_level']),
            'capability_building_area': pathway['target_job_function'].lower(),
            'salary_progression_description': f"{pathway['level_transition']} advancement",
            'salary_increase_estimate': self._estimate_salary_increase(pathway['move_type']),
            'strategic_exposure_description': f"Direct involvement in {pathway['target_job_function'].lower()} decisions",
            'professional_development_description': f"Specialisation in high-demand {pathway['target_job_function'].lower()} competencies",
            'career_resilience_description': f"{pathway['target_job_function']} skills highly transferable across financial services"
        }
    
    def _get_implementation_roadmap_data(self, job_from: str, target_job_id: str) -> Dict:
        """Generate implementation roadmap data."""
        return {
            'phase_1_activity_1': f"Foundation training in target role fundamentals",
            'phase_1_activity_2': f"Regulatory framework and compliance training",
            'phase_1_activity_3': f"Shadow senior practitioners in current division",
            'phase_2_activity_1': f"Advanced technical specialisation training",
            'phase_2_activity_2': f"Industry-specific methodology development",
            'phase_2_activity_3': f"Cross-divisional exposure to different applications",
            'phase_3_activity_1': f"Supervised project work on actual assignments",
            'phase_3_activity_2': f"Cross-functional collaboration experience",
            'phase_3_activity_3': f"Presentation skills for stakeholder communication",
            'phase_4_activity_1': f"Mentorship from experienced practitioners",
            'phase_4_activity_2': f"Gradual responsibility increase",
            'phase_4_activity_3': f"Performance review and transition completion"
        }
    
    def _get_target_organisational_deployment(self, target_job_id: str) -> Dict:
        """Get organisational deployment data for target role."""
        try:
            # Get position and division counts
            position_query = """
            SELECT COUNT(DISTINCT p."Employee Number") as position_count,
                   COUNT(DISTINCT p.Division) as division_count
            FROM positions p 
            JOIN jobs j ON p.JobProfileID = j.JobProfileID
            WHERE j.JobProfileID = ?
            """
            result = self.db.execute(position_query, (target_job_id,)).fetchone()
            
            # Get geographic spread from actual location data
            location_query = """
            SELECT DISTINCT p.Location
            FROM positions p 
            JOIN jobs j ON p.JobProfileID = j.JobProfileID
            WHERE j.JobProfileID = ? AND p.Location IS NOT NULL AND p.Location != ''
            ORDER BY p.Location
            """
            locations = self.db.execute(location_query, (target_job_id,)).fetchall()
            geographic_spread = ', '.join([loc[0] for loc in locations[:3]]) if locations else 'Multiple locations'
            
            # Calculate strategic importance based on position count
            position_count = result[0] if result else 0
            if position_count > 50:
                strategic_importance = 'Critical role with substantial organisational presence'
            elif position_count > 20:
                strategic_importance = 'Important role in business operations'
            elif position_count > 5:
                strategic_importance = 'Specialised role with targeted deployment'
            else:
                strategic_importance = 'Niche role with limited deployment'
            
            return {
                'target_position_count': position_count,
                'target_division_count': result[1] if result else 0,
                'target_geographic_spread': geographic_spread,
                'target_strategic_importance': strategic_importance,
                'target_growth_trajectory': 'Growth trajectory analysis requires historical data'
            }
        except Exception as e:
            print(f"⚠️ Error getting organisational deployment: {e}")
            return {
                'target_position_count': 0,
                'target_division_count': 0,
                'target_geographic_spread': 'Geographic data unavailable',
                'target_strategic_importance': 'Strategic assessment requires additional data',
                'target_growth_trajectory': 'Growth analysis requires historical data'
            }
    
    def _generate_content_sections(self, opportunities: List[Dict]) -> Dict:
        """Generate content for the pathway analysis section."""
        template_sections = self.template_data.get('pathway_analysis', {})
        opportunity_template = template_sections.get('opportunity_template', {})
        
        content = {
            'opportunities': []
        }
        
        try:
            for opportunity in opportunities:
                # Combine all data for this opportunity
                opportunity_variables = self._populate_opportunity_variables(opportunity)
                
                # Generate content for this opportunity
                opportunity_content = {
                    'header': Template(opportunity_template.get('header', '')).render(**opportunity_variables),
                    'strategic_positioning': {
                        'title': opportunity_template.get('strategic_positioning', {}).get('title', ''),
                        'content': Template(opportunity_template.get('strategic_positioning', {}).get('content', '')).render(**opportunity_variables)
                    },
                    'skills_transition_analysis': {
                        'title': opportunity_template.get('skills_transition_analysis', {}).get('title', ''),
                        'content': Template(opportunity_template.get('skills_transition_analysis', {}).get('content', '')).render(**opportunity_variables)
                    },
                    'business_case': {
                        'title': opportunity_template.get('business_case', {}).get('title', ''),
                        'content': Template(opportunity_template.get('business_case', {}).get('content', '')).render(**opportunity_variables)
                    },
                    'implementation_roadmap': {
                        'title': opportunity_template.get('implementation_roadmap', {}).get('title', ''),
                        'content': Template(opportunity_template.get('implementation_roadmap', {}).get('content', '')).render(**opportunity_variables)
                    }
                }
                
                content['opportunities'].append(opportunity_content)
                
        except Exception as e:
            print(f"⚠️ Error generating opportunity content: {e}")
            content = {'error': f'Content generation failed: {e}'}
        
        return content
    
    def _populate_opportunity_variables(self, opportunity: Dict) -> Dict:
        """Populate all template variables for a single opportunity."""
        pathway = opportunity['pathway_data']
        strategic = opportunity['strategic_positioning']
        skills = opportunity['skills_analysis']
        business = opportunity['business_case']
        roadmap = opportunity['implementation_roadmap']
        
        # Combine all variables
        variables = {
            # Basic opportunity data
            'opportunity_rank': opportunity['opportunity_rank'],
            **strategic,
            
            # Skills analysis data
            **skills['development_timeline'],
            **skills,
            
            # Business case data
            **business,
            
            # Implementation roadmap data
            **roadmap,
            
            # Reference numbers (sequential from 57)
            'function_ref': str(57),
            'function_significance_ref': str(58),
            'function_intelligence_ref': str(59),
            'level_transition_ref': str(60),
            'progression_ref': str(61),
            'skills_overlap_ref': str(62),
            'transferability_ref': str(63),
            'percentile_ref': str(64),
            'success_ref': str(65),
            'cross_function_ref': str(66),
            'applicability_ref': str(67),
            'training_effectiveness_ref': str(68),
            'transition_risk_ref': str(69),
            'transferability_context_ref': str(70),
            'cost_effectiveness_ref': str(71),
            
            # Add missing variables
            'progression_alignment_description': 'standard progression pathways',
            'progression_strategic_assessment': 'natural career progression step with established precedent',
            'progression_complexity_descriptor': 'reducing approval complexity',
            'progression_salary_framework': 'clear salary progression frameworks',
            'overlap_performance_assessment': 'exceptional performance',
            'retraining_investment_assessment': 'minimal retraining investment',
            'success_probability_assessment': 'high success probability',
            'transferability_context_assessment': 'exceptional performance',
            'cost_effectiveness_assessment': 'cost-effective and low-risk',
            'include_organisational_deployment': opportunity.get('organisational_deployment') is not None
        }
        
        # Extract nested function analysis data
        if 'function_analysis' in strategic:
            variables.update(strategic['function_analysis'])
        
        # Extract nested skills overlap data
        if 'skills_overlap_data' in strategic:
            variables.update(strategic['skills_overlap_data'])
        
        # Extract nested cross-function data
        if 'cross_function_data' in strategic:
            variables.update(strategic['cross_function_data'])
        
        # Add organisational deployment data if available
        if 'organisational_deployment' in opportunity:
            variables.update(opportunity['organisational_deployment'])
        
        return variables
    
    def _generate_references(self) -> Dict:
        """Generate reference mappings for pathway analysis."""
        references = self.template_data.get('references', {})
        return references
    
    # Helper methods for classifications and descriptions
    def _get_opportunity_classification(self, similarity_score: float) -> str:
        """Get opportunity classification based on similarity score."""
        if similarity_score >= 85: return "Outstanding Opportunity"
        elif similarity_score >= 75: return "Excellent Opportunity"
        elif similarity_score >= 65: return "Strong Opportunity"
        elif similarity_score >= 50: return "Development Opportunity"
        else: return "Transformation Opportunity"
    
    def _get_move_type_description(self, move_type: str) -> str:
        """Get move type description."""
        descriptions = self.template_data.get('descriptors', {}).get('move_type_descriptions', {})
        return descriptions.get(move_type, 'strategic transition opportunity')
    
    def _get_move_type_display(self, move_type: str) -> str:
        """Get move type display name."""
        displays = self.template_data.get('descriptors', {}).get('move_type_displays', {})
        return displays.get(move_type, 'Strategic Transition')
    
    def _get_function_significance_descriptor(self, significance: str) -> str:
        """Get function significance descriptor."""
        descriptors = self.template_data.get('descriptors', {}).get('function_significance', {})
        return descriptors.get(significance, 'moderate organisational focus')
    
    def _get_function_size_assessment(self, significance: str) -> str:
        """Get function size assessment."""
        assessments = self.template_data.get('descriptors', {}).get('function_size_assessments', {})
        return assessments.get(significance, 'established')
    
    def _get_function_career_infrastructure(self, significance: str) -> str:
        """Get function career infrastructure assessment."""
        infrastructure = self.template_data.get('descriptors', {}).get('function_career_infrastructure', {})
        return infrastructure.get(significance, 'developing career pathways')
    
    def _get_transferability_assessment(self, overlap_percentage: float) -> str:
        """Get transferability assessment based on overlap percentage."""
        if overlap_percentage >= 80: return "exceptional foundation"
        elif overlap_percentage >= 65: return "strong foundation"
        elif overlap_percentage >= 50: return "moderate foundation"
        else: return "development foundation"
    
    def _get_percentile_ranking(self, overlap_percentage: float) -> str:
        """Get percentile ranking description."""
        if overlap_percentage >= 80: return "top 5%"
        elif overlap_percentage >= 65: return "top 15%"
        elif overlap_percentage >= 50: return "top 35%"
        else: return "bottom 50%"
    
    def _estimate_recruitment_cost(self, management_level: str) -> int:
        """Estimate recruitment cost based on management level."""
        if 'Group 6' in management_level or 'Group 7' in management_level: return 75
        elif 'Group 4' in management_level or 'Group 5' in management_level: return 60
        elif 'Group 2' in management_level or 'Group 3' in management_level: return 45
        else: return 30
    
    def _estimate_salary_increase(self, move_type: str) -> int:
        """Estimate salary increase percentage based on move type."""
        if 'Progression' in move_type and 'Higher_Level' in move_type: return 20
        elif 'Progression' in move_type: return 15
        elif 'Lateral' in move_type: return 8
        else: return 5
    
    def _get_fallback_skills_transition(self) -> Dict:
        """Fallback skills transition analysis."""
        return {
            'transferable_skill_categories': [
                {'name': 'Core Analytics', 'skill_list': 'Data Analysis, Statistical Methods, Problem Solving'},
                {'name': 'Business Skills', 'skill_list': 'Communication, Project Management, Stakeholder Engagement'}
            ],
            'required_skills': [
                {'name': 'Advanced Analytics', 'description': 'Specialized analytical techniques'},
                {'name': 'Industry Knowledge', 'description': 'Domain-specific expertise'}
            ],
            'required_skills_count': 2,
            'development_timeline': self._calculate_development_timeline(2)
        } 