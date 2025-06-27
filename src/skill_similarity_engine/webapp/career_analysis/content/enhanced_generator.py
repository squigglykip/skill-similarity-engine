"""
Enhanced content generator for role-specific white paper analysis.
Addresses the core problem of generic content by generating unique, 
actionable insights for each career transition opportunity.
"""

from typing import Dict, List, Optional, Any
import sqlite3
import yaml
from pathlib import Path
from .dynamic_thresholds import AdaptiveContentSelector
from .thresholds import ContentPersonalizer

class EnhancedContentGenerator:
    """Generates role-specific, actionable content for white paper analysis."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.adaptive_selector = AdaptiveContentSelector(db_connection)
        self.personalizer = ContentPersonalizer(self._load_template)
        self.templates_path = Path(__file__).parent.parent / 'templates'
    
    def _load_template(self, template_path: str) -> Dict:
        """Load YAML template file."""
        full_path = self.templates_path / template_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Template file not found: {full_path}")
            return {}
    
    def generate_role_specific_analysis(self, job_from: str, top_matches: List[Dict], 
                                      analysis_data: Dict) -> Dict:
        """Generate unique, role-specific analysis for Top 3 opportunities."""
        
        print(f"ðŸŽ¯ Generating role-specific analysis for {job_from} with {len(top_matches)} matches")
        
        # Get enhanced context for source job
        source_context = self._get_comprehensive_job_context(job_from)
        
        # Generate unique analysis for each match
        role_analyses = []
        for i, match in enumerate(top_matches[:3]):
            role_analysis = self._generate_unique_role_analysis(
                job_from, match, source_context, i + 1
            )
            role_analyses.append(role_analysis)
        
        # Generate comprehensive summary
        summary_analysis = self._generate_comprehensive_summary(
            job_from, role_analyses, source_context, analysis_data
        )
        
        return {
            'source_job_context': source_context,
            'role_specific_analyses': role_analyses,
            'comprehensive_summary': summary_analysis,
            'executive_insights': self._generate_executive_insights(role_analyses, source_context),
            'implementation_roadmap': self._generate_implementation_roadmap(role_analyses)
        }
    
    def _get_comprehensive_job_context(self, job_id: str) -> Dict:
        """Get comprehensive business and organizational context for a job."""
        try:
            # Get job details with organizational context
            job_query = """
            SELECT j.JobProfileID, j.JobProfile, j.Job, j.ProfileTitleSuffix,
                   j.JobFunction, j.ManagementLevel, j.JobCategory, j.JobSubFunction,
                   COUNT(DISTINCT p."Position Number") as total_positions,
                   COUNT(DISTINCT p.Division) as division_count,
                   COUNT(DISTINCT p.Location) as location_count,
                   GROUP_CONCAT(DISTINCT p.Division || ' (' || 
                       (SELECT COUNT(*) FROM positions p2 WHERE p2.JobProfileID = j.JobProfileID AND p2.Division = p.Division) || 
                       ')') as division_breakdown,
                   GROUP_CONCAT(DISTINCT p.Location) as location_list,
                   GROUP_CONCAT(DISTINCT p."Business_Unit") as business_units,
                   (SELECT COUNT(*) FROM job_skills js WHERE js.JobProfileID = j.JobProfileID) as Skills_Count
            FROM jobs j
            LEFT JOIN positions p ON j.JobProfileID = p.JobProfileID
            WHERE j.JobProfileID = ?
            GROUP BY j.JobProfileID, j.JobProfile, j.Job, j.ProfileTitleSuffix,
                     j.JobFunction, j.ManagementLevel, j.JobCategory, j.JobSubFunction
            """
            
            job_result = self.db.execute(job_query, (job_id,)).fetchone()
            if not job_result:
                return {'error': f'Job {job_id} not found'}
            
            job_data = dict(job_result)
            
            # Get skills breakdown by category
            skills_query = """
            SELECT s.Category, s.Subcategory, COUNT(*) as skill_count,
                   GROUP_CONCAT(s.Skill_Name) as skills_list
            FROM job_skills js
            JOIN skills s ON js.Skill_ID = s.Skill_ID
            WHERE js.JobProfileID = ?
            GROUP BY s.Category, s.Subcategory
            ORDER BY skill_count DESC
            """
            
            skills_results = self.db.execute(skills_query, (job_id,)).fetchall()
            skills_breakdown = [dict(row) for row in skills_results]
            
            # Get strategic positioning
            strategic_context = self._analyze_strategic_positioning(job_data, skills_breakdown)
            
            return {
                'job_details': job_data,
                'skills_breakdown': skills_breakdown,
                'strategic_context': strategic_context,
                'business_communication': self._create_business_communication_framework(job_data)
            }
            
        except Exception as e:
            print(f"âš ï¸ Error getting comprehensive job context: {e}")
            return {'error': str(e)}
    
    def _generate_unique_role_analysis(self, job_from: str, match: Dict, 
                                     source_context: Dict, rank: int) -> Dict:
        """Generate unique, detailed analysis for a specific role match."""
        
        target_job_id = match.get('id') or match.get('JobProfileID')
        similarity_score = match.get('similarity_score', 0)
        
        # Validate target_job_id
        if not target_job_id:
            print(f"âš ï¸ No target job ID found in match: {match}")
            return {
                'error': 'Missing target job ID',
                'rank': rank,
                'target_job_id': None,
                'similarity_score': similarity_score
            }
        
        # Get comprehensive context for target role
        target_context = self._get_comprehensive_job_context(target_job_id)
        
        # Get enhanced similarity context
        enhanced_context = self.adaptive_selector.get_enhanced_analysis_context(
            similarity_score, job_from, target_job_id
        )
        
        # Generate detailed skills analysis
        skills_analysis = self._generate_detailed_skills_analysis(job_from, target_job_id)
        
        # Generate business positioning analysis
        business_analysis = self._generate_business_positioning_analysis(
            source_context, target_context, enhanced_context
        )
        
        # Generate actionable transition insights
        transition_insights = self._generate_actionable_transition_insights(
            similarity_score, skills_analysis, business_analysis, rank
        )
        
        return {
            'rank': rank,
            'target_job_id': target_job_id,
            'target_context': target_context,
            'similarity_score': similarity_score,
            'enhanced_context': enhanced_context,
            'skills_analysis': skills_analysis,
            'business_analysis': business_analysis,
            'transition_insights': transition_insights,
            'unique_narrative': self._create_unique_narrative(
                source_context, target_context, enhanced_context, skills_analysis, rank
            )
        }
    
    def _generate_detailed_skills_analysis(self, job_from: str, job_to: str) -> Dict:
        """Generate detailed, named skills analysis between two specific jobs."""
        try:
            # Get specific skills for both jobs
            skills_query = """
            SELECT 
                js1.JobProfileID as source_job,
                js2.JobProfileID as target_job,
                s.Skill_Name,
                s.Category,
                s.Subcategory,
                s.SkillType,
                CASE 
                    WHEN js1.Skill_ID IS NOT NULL AND js2.Skill_ID IS NOT NULL THEN 'shared'
                    WHEN js1.Skill_ID IS NOT NULL AND js2.Skill_ID IS NULL THEN 'transferable'
                    WHEN js1.Skill_ID IS NULL AND js2.Skill_ID IS NOT NULL THEN 'to_develop'
                END as skill_relationship
            FROM skills s
            LEFT JOIN job_skills js1 ON s.Skill_ID = js1.Skill_ID AND js1.JobProfileID = ?
            LEFT JOIN job_skills js2 ON s.Skill_ID = js2.Skill_ID AND js2.JobProfileID = ?
            WHERE js1.Skill_ID IS NOT NULL OR js2.Skill_ID IS NOT NULL
            ORDER BY s.Category, s.Skill_Name
            """
            
            skills_results = self.db.execute(skills_query, (job_from, job_to)).fetchall()
            skills_data = [dict(row) for row in skills_results]
            
            # Categorize skills
            shared_skills = [s for s in skills_data if s['skill_relationship'] == 'shared']
            transferable_skills = [s for s in skills_data if s['skill_relationship'] == 'transferable']
            skills_to_develop = [s for s in skills_data if s['skill_relationship'] == 'to_develop']
            
            # Group by category for better insight
            shared_by_category = self._group_skills_by_category(shared_skills)
            transferable_by_category = self._group_skills_by_category(transferable_skills)
            develop_by_category = self._group_skills_by_category(skills_to_develop)
            
            # Generate skill insights
            skill_insights = self._generate_skill_insights(
                shared_by_category, transferable_by_category, develop_by_category
            )
            
            return {
                'shared_skills': shared_skills,
                'transferable_skills': transferable_skills,
                'skills_to_develop': skills_to_develop,
                'shared_by_category': shared_by_category,
                'transferable_by_category': transferable_by_category,
                'develop_by_category': develop_by_category,
                'skill_insights': skill_insights,
                'metrics': {
                    'shared_count': len(shared_skills),
                    'transferable_count': len(transferable_skills),
                    'develop_count': len(skills_to_develop),
                    'overlap_percentage': (len(shared_skills) / max(len(shared_skills) + len(skills_to_develop), 1)) * 100
                }
            }
            
        except Exception as e:
            print(f"âš ï¸ Error in detailed skills analysis: {e}")
            return {'error': str(e), 'metrics': {'shared_count': 0, 'transferable_count': 0, 'develop_count': 0}}
    
    def _generate_business_positioning_analysis(self, source_context: Dict, 
                                              target_context: Dict, enhanced_context: Dict) -> Dict:
        """Generate business positioning and organizational context analysis."""
        
        source_job = source_context.get('job_details', {})
        target_job = target_context.get('job_details', {})
        
        # Analyze organizational positioning
        organizational_analysis = {
            'division_change': source_job.get('division_breakdown') != target_job.get('division_breakdown'),
            'function_change': source_job.get('JobFunction') != target_job.get('JobFunction'),
            'level_change': self._analyze_level_change(source_job, target_job),
            'scope_change': self._analyze_scope_change(source_job, target_job)
        }
        
        # Strategic importance analysis
        strategic_analysis = {
            'source_strategic_importance': source_context.get('strategic_context', {}).get('importance_level', 'Medium'),
            'target_strategic_importance': target_context.get('strategic_context', {}).get('importance_level', 'Medium'),
            'career_progression_type': self._determine_career_progression_type(organizational_analysis),
            'market_demand_context': self._analyze_market_demand_context(target_job)
        }
        
        return {
            'organizational_analysis': organizational_analysis,
            'strategic_analysis': strategic_analysis,
            'business_rationale': self._create_business_rationale(organizational_analysis, strategic_analysis),
            'stakeholder_impact': self._analyze_stakeholder_impact(source_job, target_job)
        }
    
    def _generate_actionable_transition_insights(self, similarity_score: float, 
                                               skills_analysis: Dict, business_analysis: Dict, rank: int) -> Dict:
        """Generate specific, actionable transition insights."""
        
        # Determine transition difficulty and timeline
        transition_assessment = self._assess_transition_difficulty(similarity_score, skills_analysis, business_analysis)
        
        # Generate specific development priorities
        development_priorities = self._prioritize_development_areas(skills_analysis, business_analysis)
        
        # Create concrete next steps
        next_steps = self._create_concrete_next_steps(transition_assessment, development_priorities, rank)
        
        # Resource recommendations
        resource_recommendations = self._generate_resource_recommendations(skills_analysis, business_analysis)
        
        return {
            'transition_assessment': transition_assessment,
            'development_priorities': development_priorities,
            'next_steps': next_steps,
            'resource_recommendations': resource_recommendations,
            'success_indicators': self._define_success_indicators(transition_assessment),
            'risk_mitigation': self._identify_risk_mitigation_strategies(business_analysis, skills_analysis)
        }
    
    def _create_unique_narrative(self, source_context: Dict, target_context: Dict, 
                               enhanced_context: Dict, skills_analysis: Dict, rank: int) -> Dict:
        """Create unique narrative content for this specific role transition."""
        
        source_job = source_context.get('job_details', {})
        target_job = target_context.get('job_details', {})
        source_comm = source_context.get('business_communication', {})
        target_comm = target_context.get('business_communication', {})
        
        # Create role-specific opening
        opening_narrative = self._create_role_specific_opening(
            source_comm, target_comm, enhanced_context, skills_analysis, rank
        )
        
        # Create detailed opportunity description
        opportunity_description = self._create_detailed_opportunity_description(
            target_context, enhanced_context, skills_analysis
        )
        
        # Create skills development narrative
        skills_narrative = self._create_skills_development_narrative(skills_analysis)
        
        # Create business case narrative
        business_case = self._create_business_case_narrative(source_context, target_context, enhanced_context)
        
        return {
            'opening_narrative': opening_narrative,
            'opportunity_description': opportunity_description,
            'skills_narrative': skills_narrative,
            'business_case': business_case,
            'implementation_approach': self._create_implementation_narrative(enhanced_context, skills_analysis)
        }
    
    def _create_business_communication_framework(self, job_data: Dict) -> Dict:
        """Create the JobProfile â†’ Positions business communication framework."""
        
        job_profile = job_data.get('JobProfile', 'Unknown Job Profile')
        total_positions = job_data.get('total_positions', 0)
        division_breakdown = job_data.get('division_breakdown', '')
        
        # Parse division breakdown to create position descriptions
        position_descriptions = []
        if division_breakdown:
            divisions = division_breakdown.split(',')
            for div in divisions[:3]:  # Top 3 divisions
                div_clean = div.strip()
                if '(' in div_clean and ')' in div_clean:
                    position_descriptions.append(div_clean)
        
        # Create the complete business communication structure
        business_framework = {
            'job_profile_lead': f"The {job_profile} job architecture",
            'position_translation': f"which encompasses {total_positions} positions across {len(position_descriptions)} divisions",
            'position_breakdown': ', '.join(position_descriptions) if position_descriptions else f"{total_positions} positions",
            'complete_structure': f"The {job_profile} job architecture, which encompasses {total_positions} positions including {', '.join(position_descriptions) if position_descriptions else 'various organizational positions'}"
        }
        
        return business_framework
    
    def _create_role_specific_opening(self, source_comm: Dict, target_comm: Dict, 
                                    enhanced_context: Dict, skills_analysis: Dict, rank: int) -> str:
        """Create a unique, role-specific opening using templates."""
        
        # Create rank-specific context
        rank_context = {
            1: "represents the strongest transition opportunity",
            2: "offers compelling career advancement potential", 
            3: "provides valuable alternative career pathway"
        }.get(rank, "presents career transition potential")
        
        enhanced_variables = {
            'rank': rank,
            'target_job_profile_lead': target_comm.get('job_profile_lead', 'Target Role'),
            'rank_context': rank_context,
            'similarity_score': enhanced_context.get('similarity_score', 0),
            'percentile_rank': enhanced_context.get('percentile_rank', 0),
            'source_structure': source_comm.get('complete_structure', 'current role'),
            'target_structure': target_comm.get('complete_structure', 'target opportunity'),
            'shared_count': skills_analysis.get('metrics', {}).get('shared_count', 0),
            'develop_count': skills_analysis.get('metrics', {}).get('develop_count', 0),
            'quality_level': enhanced_context.get('quality_level', 'Unknown').lower(),
            'development_intensity': self._get_development_intensity_description(skills_analysis.get('metrics', {}).get('develop_count', 0)),
            'strategic_context': self._get_strategic_context_description(enhanced_context, target_comm)
        }
        
        # Use template-based generation
        template = self._load_template('enhanced/role_opening.yaml')
        if template and 'content' in template:
            return self.personalizer.personalize_paragraph(
                template['content'], enhanced_variables, template.get('variables')
            )
        
        # Fallback to basic format if template not available
        return f"""**Career Opportunity #{enhanced_variables['rank']}: {enhanced_variables['target_job_profile_lead']}**

This transition {enhanced_variables['rank_context']} with a {enhanced_variables['similarity_score']:.1%} skill similarity score.

**Skills Alignment**: {enhanced_variables['shared_count']} directly transferable skills with {enhanced_variables['develop_count']} key areas requiring focused development."""
    
    # Helper methods for narrative generation
    def _group_skills_by_category(self, skills: List[Dict]) -> Dict:
        """Group skills by category for better organization."""
        grouped = {}
        for skill in skills:
            category = skill.get('Category', 'General')
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(skill)
        return grouped
    
    def _generate_skill_insights(self, shared: Dict, transferable: Dict, develop: Dict) -> List[str]:
        """Generate specific skill insights based on categorized skills."""
        insights = []
        
        # Shared skills insights
        if shared:
            top_shared_category = max(shared.keys(), key=lambda k: len(shared[k]))
            insights.append(f"Strong foundation in {top_shared_category} with {len(shared[top_shared_category])} directly applicable skills")
        
        # Development insights
        if develop:
            top_develop_category = max(develop.keys(), key=lambda k: len(develop[k]))
            insights.append(f"Primary development focus required in {top_develop_category} ({len(develop[top_develop_category])} skills)")
        
        # Transferable insights
        if transferable:
            insights.append(f"Additional {sum(len(skills) for skills in transferable.values())} transferable skills provide career flexibility")
        
        return insights
    
    def _analyze_strategic_positioning(self, job_data: Dict, skills_breakdown: List[Dict]) -> Dict:
        """Analyze strategic positioning of the role within the organization."""
        
        total_positions = job_data.get('total_positions', 0)
        division_count = job_data.get('division_count', 0)
        skills_count = job_data.get('Skills_Count', 0)
        
        # Determine importance level based on various factors
        if total_positions > 50:
            importance_level = "High"
        elif total_positions > 20:
            importance_level = "Medium-High"
        elif total_positions > 5:
            importance_level = "Medium"
        else:
            importance_level = "Specialized"
        
        return {
            'importance_level': importance_level,
            'organizational_reach': 'Broad' if division_count > 3 else 'Focused',
            'skill_complexity': 'High' if skills_count > 50 else 'Medium' if skills_count > 30 else 'Standard',
            'workforce_impact': f"{total_positions} positions across {division_count} divisions"
        }
    
    def _get_development_intensity_description(self, develop_count: int) -> str:
        """Get description of development intensity based on skill count."""
        if develop_count <= 3:
            return "minimal"
        elif develop_count <= 7:
            return "moderate"
        elif develop_count <= 12:
            return "substantial"
        else:
            return "comprehensive"
    
    def _get_strategic_context_description(self, enhanced_context: Dict, target_comm: Dict) -> str:
        """Get strategic context description for the transition."""
        confidence_factors = enhanced_context.get('confidence_factors', [])
        
        if confidence_factors:
            return f"Key considerations include {', '.join(confidence_factors[:2])}."
        else:
            return f"Transition aligns with internal mobility best practices and career development frameworks."
    
    # Additional helper methods would continue here...
    def _analyze_level_change(self, source_job: Dict, target_job: Dict) -> str:
        """Analyze level change between roles."""
        source_level = source_job.get('ManagementLevel', 'Group 1')
        target_level = target_job.get('ManagementLevel', 'Group 1')
        
        try:
            # Extract numeric part from "Group X" format
            source_num = int(source_level.split()[-1]) if 'Group' in source_level else 1
            target_num = int(target_level.split()[-1]) if 'Group' in target_level else 1
            
            if target_num > source_num:
                return 'promotion'
            elif target_num < source_num:
                return 'lateral_down'
            else:
                return 'lateral'
        except:
            return 'lateral'
    
    def _analyze_scope_change(self, source_job: Dict, target_job: Dict) -> str:
        """Analyze scope change between roles."""
        source_positions = source_job.get('total_positions', 0)
        target_positions = target_job.get('total_positions', 0)
        
        if target_positions > source_positions * 1.5:
            return 'expanded'
        elif target_positions < source_positions * 0.5:
            return 'focused'
        else:
            return 'similar'
    
    def _determine_career_progression_type(self, org_analysis: Dict) -> str:
        """Determine the type of career progression."""
        if org_analysis.get('level_change') == 'promotion':
            return 'vertical_progression'
        elif org_analysis.get('function_change'):
            return 'cross_functional_move'
        elif org_analysis.get('division_change'):
            return 'cross_divisional_move'
        else:
            return 'lateral_development'
    
    def _analyze_market_demand_context(self, target_job: Dict) -> str:
        """Analyze market demand context for target role."""
        total_positions = target_job.get('total_positions', 0)
        
        if total_positions > 100:
            return 'high_demand'
        elif total_positions > 50:
            return 'medium_high_demand'
        elif total_positions > 20:
            return 'medium_demand'
        else:
            return 'specialized_demand'
    
    def _create_business_rationale(self, org_analysis: Dict, strategic_analysis: Dict) -> str:
        """Create business rationale for the transition."""
        progression_type = strategic_analysis.get('career_progression_type', 'lateral_development')
        
        rationales = {
            'vertical_progression': 'Supports career advancement and leadership development within existing expertise areas',
            'cross_functional_move': 'Enables skill diversification and cross-functional capability building',
            'cross_divisional_move': 'Facilitates organizational knowledge transfer and business unit integration',
            'lateral_development': 'Provides skill enhancement and role optimization within current career trajectory'
        }
        
        return rationales.get(progression_type, 'Supports strategic workforce development and internal mobility')
    
    def _analyze_stakeholder_impact(self, source_job: Dict, target_job: Dict) -> List[str]:
        """Analyze stakeholder impact of the transition."""
        impacts = []
        
        source_positions = source_job.get('total_positions', 0)
        if source_positions > 20:
            impacts.append(f"Significant workforce planning consideration ({source_positions} source positions)")
        
        if source_job.get('JobFunction') != target_job.get('JobFunction'):
            impacts.append("Cross-functional leadership alignment required")
        
        if source_job.get('division_breakdown') != target_job.get('division_breakdown'):
            impacts.append("Multi-divisional coordination needed")
        
        return impacts or ["Standard internal mobility process applies"]
    
    # Placeholder methods for remaining functionality
    def _assess_transition_difficulty(self, similarity_score: float, skills_analysis: Dict, business_analysis: Dict) -> Dict:
        return {'difficulty': 'Medium', 'timeline_weeks': 12, 'success_probability': 75}
    
    def _prioritize_development_areas(self, skills_analysis: Dict, business_analysis: Dict) -> List[str]:
        develop_by_category = skills_analysis.get('develop_by_category', {})
        return list(develop_by_category.keys())[:3]
    
    def _create_concrete_next_steps(self, assessment: Dict, priorities: List[str], rank: int) -> List[str]:
        return [
            f"Conduct detailed skills assessment focusing on {priorities[0] if priorities else 'key competencies'}",
            f"Develop {assessment.get('timeline_weeks', 12)}-week transition plan",
            f"Identify internal mentors and subject matter experts"
        ]
    
    def _generate_resource_recommendations(self, skills_analysis: Dict, business_analysis: Dict) -> List[str]:
        return ["Internal training programs", "Cross-functional project assignments", "Mentoring partnerships"]
    
    def _define_success_indicators(self, assessment: Dict) -> List[str]:
        return ["Skills competency achievement", "Performance milestone completion", "Stakeholder feedback scores"]
    
    def _identify_risk_mitigation_strategies(self, business_analysis: Dict, skills_analysis: Dict) -> List[str]:
        return ["Phased transition approach", "Regular progress reviews", "Backup development pathways"]
    
    def _create_detailed_opportunity_description(self, target_context: Dict, enhanced_context: Dict, skills_analysis: Dict) -> str:
        """Create detailed, specific opportunity description using templates."""
        
        # Prepare enhanced variables for template processing
        target_job = target_context.get('job_details', {})
        target_comm = target_context.get('business_communication', {})
        
        enhanced_variables = {
            'target_role_architecture': target_comm.get('complete_structure', 'Target role structure'),
            'target_total_positions': target_job.get('total_positions', 0),
            'target_division_count': target_job.get('division_count', 0),
            'target_skills_count': target_job.get('Skills_Count', 0),
            'target_job_function': target_job.get('JobFunction', 'new functional'),
            'target_job_family': target_job.get('JobFunction', 'career function'),
            'shared_skills_count': skills_analysis.get('metrics', {}).get('shared_count', 0),
            'development_categories_count': len(skills_analysis.get('develop_by_category', {})),
            'similarity_score': enhanced_context.get('similarity_score', 0),
            'percentile_rank': enhanced_context.get('percentile_rank', 0)
        }
        
        # Use template-based generation with enhanced variables
        template = self._load_template('enhanced/opportunity_description.yaml')
        if template and 'content' in template:
            return self.personalizer.personalize_paragraph(
                template['content'], enhanced_variables, template.get('variables')
            )
        
        # Fallback to structured format if template not available
        return f"""**Role Architecture**: {enhanced_variables['target_role_architecture']}

**Organizational Scope**: {enhanced_variables['target_total_positions']} positions across {enhanced_variables['target_division_count']} divisions

**Skills Utilization**: {enhanced_variables['shared_skills_count']} existing skills directly applicable"""
    
    def _create_skills_development_narrative(self, skills_analysis: Dict) -> str:
        """Create narrative focused on specific skill names using templates."""
        shared_skills = skills_analysis.get('shared_skills', [])
        skills_to_develop = skills_analysis.get('skills_to_develop', [])
        develop_by_category = skills_analysis.get('develop_by_category', {})
        
        # Prepare enhanced variables for template processing
        top_shared_skills = [s.get('Skill_Name', 'skill') for s in shared_skills[:5]]
        development_categories = []
        
        for category, skills in list(develop_by_category.items())[:2]:  # Top 2 categories
            skill_names = [s.get('Skill_Name', 'skill') for s in skills[:3]]  # Top 3 skills per category
            development_categories.append({
                'category': category,
                'skills': skill_names
            })
        
        # Compute development categories text
        development_categories_text = ""
        for cat_info in development_categories:
            development_categories_text += f"**{cat_info['category']} Development**: Focus on {', '.join(cat_info['skills'])}\n"
        
        enhanced_variables = {
            'shared_skills_list': ', '.join(top_shared_skills),
            'shared_skills_count': len(shared_skills),
            'development_categories': development_categories,
            'development_categories_text': development_categories_text.strip(),
            'total_skills_to_develop': len(skills_to_develop)
        }
        
        # Use template-based generation
        template = self._load_template('enhanced/skills_development.yaml')
        if template and 'content' in template:
            return self.personalizer.personalize_paragraph(
                template['content'], enhanced_variables, template.get('variables')
            )
        
        # Fallback to basic format if template not available
        foundation_text = f"**Foundation Skills**: Direct transferability in {enhanced_variables['shared_skills_list']}" if top_shared_skills else ""
        development_text = ""
        for cat_info in development_categories:
            development_text += f"\n**{cat_info['category']} Development**: Focus on {', '.join(cat_info['skills'])}"
        
        return f"{foundation_text}\n{development_text}".strip()
    
    def _create_business_case_narrative(self, source_context: Dict, target_context: Dict, enhanced_context: Dict) -> str:
        """Create business case explaining strategic value using templates."""
        source_job = source_context.get('job_details', {})
        target_job = target_context.get('job_details', {})
        
        enhanced_variables = {
            'source_job_function': source_job.get('JobFunction', 'current functional'),
            'target_job_function': target_job.get('JobFunction', 'target functional'),
            'similarity_score': enhanced_context.get('similarity_score', 0),
            'percentile_rank': enhanced_context.get('percentile_rank', 0),
            'source_total_positions': source_job.get('total_positions', 0),
            'target_total_positions': target_job.get('total_positions', 0)
        }
        
        # Use template-based generation
        template = self._load_template('enhanced/business_case.yaml')
        if template and 'content' in template:
            return self.personalizer.personalize_paragraph(
                template['content'], enhanced_variables, template.get('variables')
            )
        
        # Fallback to basic format if template not available
        return f"""**Strategic Value**: Leverages existing {enhanced_variables['source_job_function']} expertise while building {enhanced_variables['target_job_function']} capabilities.

**Resource Optimization**: Internal transition reduces recruitment costs and accelerates capability building.

**Risk Mitigation**: {enhanced_variables['similarity_score']:.1%} skill similarity provides strong foundation for successful transition."""
    
    def _create_implementation_narrative(self, enhanced_context: Dict, skills_analysis: Dict) -> str:
        """Create implementation approach with concrete timelines and milestones."""
        develop_count = skills_analysis.get('metrics', {}).get('develop_count', 0)
        timeline_weeks = 8 + (develop_count * 2)  # Base 8 weeks + 2 weeks per skill to develop
        
        implementation_plan = f"""
        **Implementation Timeline**: {timeline_weeks}-week structured transition program
        
        **Phase 1 (Weeks 1-3)**: Skills assessment and gap analysis with current role responsibilities maintained
        
        **Phase 2 (Weeks 4-{timeline_weeks-3})**: Targeted skill development through cross-functional assignments, 
        training programs, and mentoring partnerships
        
        **Phase 3 (Weeks {timeline_weeks-2}-{timeline_weeks})**: Transition execution with knowledge transfer, 
        stakeholder alignment, and new role integration
        
        **Success Metrics**: Competency achievement in {develop_count} development areas, 
        stakeholder satisfaction scores, and 90-day performance milestone completion.
        """
        
        return implementation_plan.strip()
    
    def _generate_comprehensive_summary(self, job_from: str, role_analyses: List[Dict], 
                                      source_context: Dict, analysis_data: Dict) -> Dict:
        """Generate comprehensive summary across all role analyses."""
        
        # Aggregate similarity scores
        similarities = [r.get('similarity_score', 0) for r in role_analyses]
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
        
        # Aggregate development requirements
        total_develop = sum(r.get('skills_analysis', {}).get('metrics', {}).get('develop_count', 0) for r in role_analyses)
        avg_develop = total_develop / len(role_analyses) if role_analyses else 0
        
        # Identify unique job functions
        job_functions = set(r.get('target_context', {}).get('job_details', {}).get('JobFunction', 'Unknown') for r in role_analyses)
        
        summary = {
            'transition_quality': 'Excellent' if avg_similarity > 0.8 else 'Good' if avg_similarity > 0.6 else 'Moderate',
            'development_intensity': 'Low' if avg_develop < 5 else 'Medium' if avg_develop < 10 else 'High',
            'career_breadth': f"{len(job_functions)} distinct job functions",
            'recommended_approach': f"Pursue highest-similarity opportunity ({max(similarities):.1%}) while maintaining alternative pathways",
            'strategic_recommendation': f"Focus development on {int(avg_develop)} average skills per pathway for optimal transition readiness"
        }
        
        return summary
    
    def _generate_executive_insights(self, role_analyses: List[Dict], source_context: Dict) -> Dict:
        """Generate executive-level insights and strategic recommendations."""
        
        # Identify highest-value opportunity
        best_opportunity = max(role_analyses, key=lambda r: r.get('similarity_score', 0))
        best_target = best_opportunity.get('target_context', {}).get('job_details', {})
        
        # Strategic insights
        insights = {
            'primary_recommendation': f"Prioritize {best_target.get('JobProfile', 'top opportunity')} pathway with {best_opportunity.get('similarity_score', 0):.1%} similarity",
            'workforce_impact': f"Transition affects {source_context.get('job_details', {}).get('total_positions', 0)} source positions across {source_context.get('job_details', {}).get('division_count', 0)} divisions",
            'business_alignment': "Supports strategic workforce development and internal mobility initiatives",
            'resource_requirements': f"Estimated {sum(r.get('transition_insights', {}).get('transition_assessment', {}).get('timeline_weeks', 12) for r in role_analyses) / len(role_analyses):.0f}-week average transition timeline",
            'success_probability': f"{sum(r.get('transition_insights', {}).get('transition_assessment', {}).get('success_probability', 75) for r in role_analyses) / len(role_analyses):.0f}% average success probability"
        }
        
        return insights
    
    def _generate_implementation_roadmap(self, role_analyses: List[Dict]) -> Dict:
        """Generate implementation roadmap across all analyzed roles."""
        
        # Aggregate implementation timelines
        timelines = [r.get('transition_insights', {}).get('transition_assessment', {}).get('timeline_weeks', 12) for r in role_analyses]
        max_timeline = max(timelines) if timelines else 12
        
        # Create phased roadmap
        roadmap = {
            'total_timeline': f"{max_timeline} weeks maximum",
            'phase_1': "Assessment and pathway selection (Weeks 1-4)",
            'phase_2': f"Skill development and preparation (Weeks 5-{max_timeline-4})",
            'phase_3': f"Transition execution and integration (Weeks {max_timeline-3}-{max_timeline})",
            'parallel_activities': [
                "Cross-functional exposure programs",
                "Mentoring and coaching relationships", 
                "Progress monitoring and adjustment",
                "Stakeholder communication and alignment"
            ],
            'success_factors': [
                "Clear pathway selection criteria",
                "Structured skill development programs",
                "Regular progress checkpoints",
                "Strong leadership support and sponsorship"
            ]
        }
        
        return roadmap 
