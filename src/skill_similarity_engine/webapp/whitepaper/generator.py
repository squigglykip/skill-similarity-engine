"""
Main white paper generation engine with enhanced role-specific content generation.
"""

from .content.thresholds import ContentThresholds, ContentPersonalizer
from .content.dynamic_thresholds import DynamicSimilarityThresholds, AdaptiveContentSelector
from .content.enhanced_generator import EnhancedContentGenerator
from .analyzer import DataAnalyzer
from .formatter import DocumentFormatter
import yaml
from pathlib import Path
from typing import Dict, List, Optional

class WhitePaperGenerator:
    """Main white paper generation engine with dynamic thresholds and enhanced content."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.analyzer = DataAnalyzer(db_connection)
        self.thresholds = ContentThresholds()  # Legacy thresholds for fallback
        self.dynamic_thresholds = DynamicSimilarityThresholds(db_connection)
        self.adaptive_selector = AdaptiveContentSelector(db_connection)
        self.enhanced_generator = EnhancedContentGenerator(db_connection)
        self.templates_path = Path(__file__).parent / 'templates'
        
    def generate(self, job_from: str, job_to: Optional[str] = None, 
                scenario: str = 'skills_gap_analysis',
                audience: str = 'business_leaders',
                output_format: str = 'word',
                filters: Optional[Dict] = None) -> Dict:
        """Generate complete white paper with enhanced role-specific content."""
        
        print(f"🚀 Generating white paper: {job_from} → {job_to or 'Top 3 Discovery'}")
        
        # 1. Analyze data and determine thresholds
        analysis_data = self.analyzer.analyze_transition(
            job_from, job_to, scenario, filters or {}
        )
        
        # 2. Use dynamic thresholds for more accurate classification
        try:
            narrative_type = self.dynamic_thresholds.get_narrative_type(
                analysis_data['avg_similarity']
            )
            print(f"📊 Dynamic threshold classification: {narrative_type} (similarity: {analysis_data['avg_similarity']:.3f})")
            
            # Get enhanced similarity context
            similarity_context = self.dynamic_thresholds.get_similarity_context(
                analysis_data['avg_similarity']
            )
            analysis_data.update(similarity_context)
            
        except Exception as e:
            print(f"⚠️ Dynamic thresholds failed, using legacy: {e}")
            narrative_type = self.thresholds.get_narrative_type(
                analysis_data['avg_similarity']
            )
        
        # 3. Generate enhanced content for Top 3 analysis or specific transitions
        if job_to is None and analysis_data.get('top_matches'):
            print("🎯 Generating enhanced Top 3 role-specific analysis...")
            try:
                enhanced_content = self.enhanced_generator.generate_role_specific_analysis(
                    job_from, analysis_data['top_matches'], analysis_data
                )
                
                # Create comprehensive content combining templates and enhanced analysis
                content = self._generate_enhanced_content(
                    narrative_type, audience, scenario, analysis_data, enhanced_content
                )
                
            except Exception as e:
                print(f"⚠️ Enhanced content generation failed, using templates: {e}")
                content = self._generate_template_content(narrative_type, audience, scenario, analysis_data)
        else:
            print("📋 Generating template-based content for specific transition...")
            content = self._generate_template_content(narrative_type, audience, scenario, analysis_data)
        
        # 4. Format into requested output
        formatter = DocumentFormatter()
        document = formatter.format_document(content, output_format, analysis_data)
        
        return {
            'success': True,
            'narrative_type': narrative_type,
            'confidence_level': analysis_data.get('confidence_level', 'Medium'),
            'document': document,
            'analysis_summary': analysis_data.get('summary', 'Analysis completed'),
            'enhanced_analysis': job_to is None and analysis_data.get('top_matches') is not None,
            'similarity_context': analysis_data.get('percentile_rank', 0)
        }
    
    def _load_template(self, template_path: str) -> Dict:
        """Load YAML template file."""
        full_path = self.templates_path / template_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Template file not found: {full_path}")
            return {}
    
    def _generate_enhanced_content(self, narrative_type: str, audience: str, scenario: str,
                                 analysis_data: Dict, enhanced_content: Dict) -> Dict:
        """Generate enhanced content combining templates with role-specific analysis."""
        
        # Start with template-based content as foundation
        template_content = self._generate_template_content(narrative_type, audience, scenario, analysis_data)
        
        # Enhance with role-specific insights
        role_analyses = enhanced_content.get('role_specific_analyses', [])
        
        if role_analyses:
            # Create enhanced executive summary with specific role insights
            template_content['executive_summary'] = self._create_enhanced_executive_summary(
                analysis_data, role_analyses, enhanced_content
            )
            
            # Add role-specific opportunity analysis
            template_content['opportunity_analysis'] = self._create_role_specific_opportunities(
                role_analyses, enhanced_content
            )
            
            # Enhanced skills development section
            template_content['skills_development'] = self._create_enhanced_skills_development(
                role_analyses
            )
            
            # Add implementation roadmap with specific pathways
            template_content['implementation_roadmap'] = self._create_enhanced_implementation_roadmap(
                role_analyses, enhanced_content
            )
        
        return template_content
    
    def _generate_template_content(self, narrative_type: str, audience: str, scenario: str,
                                 analysis_data: Dict) -> Dict:
        """Generate content using traditional template approach."""
        
        # Load appropriate templates
        narrative_template = self._load_template(f'narratives/{narrative_type}.yaml')
        audience_template = self._load_template(f'audiences/{audience}.yaml')
        scenario_template = self._load_template(f'scenarios/{scenario}.yaml')
        
        # Generate personalized content
        return self._generate_content(narrative_template, audience_template, scenario_template, analysis_data)
    
    def _generate_content(self, narrative_template: Dict, 
                         audience_template: Dict, scenario_template: Dict,
                         analysis_data: Dict) -> Dict:
        """Generate personalized content using templates."""
        personalizer = ContentPersonalizer(self._load_template)
        
        # Merge templates with audience and scenario adaptations
        content = {}
        
        # Generate each section
        if 'paragraphs' in narrative_template:
            for section_name, section_template in narrative_template['paragraphs'].items():
                if isinstance(section_template, str):
                    # Simple paragraph
                    content[section_name] = personalizer.personalize_paragraph(
                        section_template, analysis_data, narrative_template.get('variables')
                    )
                elif isinstance(section_template, dict):
                    # Complex section with subsections
                    content[section_name] = {}
                    for subsection, subsection_template in section_template.items():
                        content[section_name][subsection] = personalizer.personalize_paragraph(
                            subsection_template, analysis_data, narrative_template.get('variables')
                        )
        
        return content
    
    def _create_enhanced_executive_summary(self, analysis_data: Dict, role_analyses: List[Dict], 
                                         enhanced_content: Dict) -> Dict:
        """Create enhanced executive summary with role-specific insights."""
        
        source_context = enhanced_content.get('source_job_context', {})
        job_details = source_context.get('job_details', {})
        business_comm = source_context.get('business_communication', {})
        
        avg_similarity = analysis_data.get('avg_similarity', 0)
        percentile_rank = analysis_data.get('percentile_rank', 0)
        
        # Create role-specific opening
        opening = f"""
        **Strategic Career Transition Analysis**
        
        {business_comm.get('complete_structure', 'Current role analysis')} presents {len(role_analyses)} 
        high-value career transition opportunities with an average similarity score of {avg_similarity:.1%} 
        (ranking in the {percentile_rank:.0f}th percentile of all analyzed pathways).
        
        **Key Findings**: Analysis identifies distinct transition pathways across {len(set(r.get('target_context', {}).get('job_details', {}).get('JobFunction', 'Unknown') for r in role_analyses))} 
        job functions with {analysis_data.get('quality_level', 'good')} transition readiness.
        """
        
        # Create recommendations based on actual role analysis
        recommendations = []
        for i, role in enumerate(role_analyses[:3], 1):
            target_job = role.get('target_context', {}).get('job_details', {})
            similarity = role.get('similarity_score', 0)
            recommendations.append(
                f"**Option {i}**: {target_job.get('JobProfile', 'Career Opportunity')} "
                f"({similarity:.1%} similarity) - {role.get('enhanced_context', {}).get('quality_level', 'Transition opportunity')}"
            )
        
        recommendation = f"""
        **Recommended Approach**: 
        
        {chr(10).join(recommendations)}
        
        Proceed with structured assessment and development planning focusing on highest-similarity opportunities first.
        """
        
        confidence_factors = []
        for role in role_analyses:
            factors = role.get('enhanced_context', {}).get('confidence_factors', [])
            confidence_factors.extend(factors[:2])  # Top 2 factors per role
        
        confidence_statement = f"""
        **Confidence Assessment**: {analysis_data.get('confidence_level', 'Medium')} confidence based on:
        {chr(10).join(f"• {factor}" for factor in confidence_factors[:4])}
        """
        
        return {
            'opening': opening.strip(),
            'recommendation': recommendation.strip(),
            'confidence_statement': confidence_statement.strip()
        }
    
    def _create_role_specific_opportunities(self, role_analyses: List[Dict], enhanced_content: Dict) -> Dict:
        """Create role-specific opportunity analysis section."""
        
        opportunities_text = "**Individual Role Analysis:**\n\n"
        
        for role in role_analyses:
            unique_narrative = role.get('unique_narrative', {})
            opportunities_text += unique_narrative.get('opening_narrative', f"Role {role.get('rank', 'N/A')} analysis")
            opportunities_text += "\n\n"
            opportunities_text += unique_narrative.get('opportunity_description', "Detailed opportunity analysis")
            opportunities_text += "\n\n---\n\n"
        
        pathway_quality = f"""
        **Pathway Quality Assessment**: 
        
        Analysis reveals {len(role_analyses)} distinct career pathways with varying similarity scores and development requirements.
        Each pathway has been evaluated for skills alignment, business context, and implementation feasibility.
        """
        
        return {
            'pathway_quality': pathway_quality.strip(),
            'skills_alignment': opportunities_text.strip()
        }
    
    def _create_enhanced_skills_development(self, role_analyses: List[Dict]) -> Dict:
        """Create enhanced skills development section with specific skill names."""
        
        development_summary = "**Role-Specific Skills Development:**\n\n"
        
        for role in role_analyses:
            skills_analysis = role.get('skills_analysis', {})
            metrics = skills_analysis.get('metrics', {})
            unique_narrative = role.get('unique_narrative', {})
            
            development_summary += f"""
            **Option {role.get('rank', 'N/A')}**: {metrics.get('shared_count', 0)} shared skills, 
            {metrics.get('develop_count', 0)} skills to develop
            
            {unique_narrative.get('skills_narrative', 'Skills development requirements')}
            """
            development_summary += "\n\n"
        
        # Aggregate development plan
        all_priorities = []
        for role in role_analyses:
            transition_insights = role.get('transition_insights', {})
            priorities = transition_insights.get('development_priorities', [])
            all_priorities.extend(priorities)
        
        unique_priorities = list(dict.fromkeys(all_priorities))  # Remove duplicates while preserving order
        
        development_plan = f"""
        **Integrated Development Plan**:
        
        Priority development areas across all pathways:
        {chr(10).join(f"• {priority}" for priority in unique_priorities[:5])}
        
        Recommended approach: Begin with shared skill development areas that benefit multiple pathways,
        then specialize based on preferred career direction.
        """
        
        return {
            'development_summary': development_summary.strip(),
            'development_plan': development_plan.strip()
        }
    
    def _create_enhanced_implementation_roadmap(self, role_analyses: List[Dict], enhanced_content: Dict) -> Dict:
        """Create enhanced implementation roadmap with specific timelines and milestones."""
        
        # Aggregate timeline estimates
        timelines = []
        for role in role_analyses:
            assessment = role.get('transition_insights', {}).get('transition_assessment', {})
            timeline = assessment.get('timeline_weeks', 12)
            timelines.append(timeline)
        
        avg_timeline = sum(timelines) / len(timelines) if timelines else 12
        
        timeline_text = f"""
        **Implementation Timeline**: {avg_timeline:.0f}-week structured transition program
        
        **Phase 1 (Weeks 1-4)**: Assessment and pathway selection
        • Detailed skills assessment across all {len(role_analyses)} opportunities
        • Stakeholder alignment and preference clarification
        • Final pathway selection and commitment
        
        **Phase 2 (Weeks 5-{avg_timeline/2:.0f})**: Skill development and preparation
        • Targeted skill development in priority areas
        • Cross-functional exposure and networking
        • Progress monitoring and adjustment
        
        **Phase 3 (Weeks {avg_timeline/2+1:.0f}-{avg_timeline:.0f})**: Transition execution
        • Role transition planning and coordination
        • Knowledge transfer and handover
        • New role integration and support
        """
        
        # Aggregate success factors
        all_success_factors = []
        for role in role_analyses:
            factors = role.get('transition_insights', {}).get('success_indicators', [])
            all_success_factors.extend(factors)
        
        unique_factors = list(dict.fromkeys(all_success_factors))
        
        success_factors = f"""
        **Success Factors**:
        {chr(10).join(f"• {factor}" for factor in unique_factors[:5])}
        
        **Risk Mitigation**: Phased approach with regular checkpoints, multiple pathway options maintained until final selection,
        and comprehensive support structure throughout transition process.
        """
        
        return {
            'timeline': timeline_text.strip(),
            'success_factors': success_factors.strip()
        }
