"""
Content personalization engine for white paper generation.
"""

from typing import Dict, Any
from .thresholds import ContentThresholds

class ContentPersonalizer:
    """Personalizes content based on user context and data analysis."""
    
    def __init__(self):
        self.personalization_rules = {}
        self.thresholds = ContentThresholds()
    
    def personalize_content(self, content: str, context: Dict[str, Any]) -> str:
        """Personalize content based on context."""
        # TODO: Implement content personalization logic
        personalized = content
        
        # Replace placeholders with actual values
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in personalized:
                personalized = personalized.replace(placeholder, str(value))
        
        return personalized
    
    def manual_template_replacement(self, content, analysis_data: Dict[str, Any], job_details: Dict[str, Any]) -> Any:
        """Manually replace template variables in content."""
        import re
        
        # Define replacement values using the threshold helper functions
        replacements = {
            'transition_quality': self.thresholds.get_opportunity_descriptor(analysis_data.get('avg_similarity', 0)),
            'source_job_title': job_details.get('Job', 'Unknown Position'),
            'colleague_count': str(analysis_data.get('colleague_count', 0)),
            'avg_similarity_percent': f"{analysis_data.get('avg_similarity', 0)*100:.1f}",
            'opportunity_descriptor': self.thresholds.get_opportunity_descriptor(analysis_data.get('avg_similarity', 0)),
            'disruption_level': 'manageable' if analysis_data.get('avg_similarity', 0) >= 0.6 else 'moderate',
            'timeline_weeks': self.thresholds.get_timeline_estimate(analysis_data.get('avg_similarity', 0)),
            'skill_retention_percent': str(self.thresholds.get_skills_overlap_estimate(analysis_data.get('avg_similarity', 0))),
            'confidence_level': analysis_data.get('confidence_level', 'Medium'),
            'pathway_count': str(analysis_data.get('pathway_count', 1)),
            'success_probability_percent': "85-95" if analysis_data.get('avg_similarity', 0) >= 0.8 else "70-85",
            'transferable_skills': 'technical and analytical competencies',
            'skills_shared': str(analysis_data.get('skills_shared', 0)),
            'skills_to_develop': '3-5 key skill areas',
            'development_intensity': self.thresholds.get_development_intensity(analysis_data.get('avg_similarity', 0)),
            'development_approach': 'structured skill enhancement',
            'support_level': self.thresholds.get_support_level(analysis_data.get('avg_similarity', 0)),
            'success_factors': 'strong skill foundation, organisational support, and structured development',
            'risk_mitigation': 'phased transition and mentoring support',
            'monitoring_metrics': 'skill development progress and performance indicators',
            'implementation_phases': '3',
            # Additional missing variables
            'business_driver': 'strategic workforce planning and career development',
            'transferability_assessment': self.thresholds.get_opportunity_descriptor(analysis_data.get('avg_similarity', 0)) + ' skill transferability',
            'viability_assessment': 'highly viable' if analysis_data.get('avg_similarity', 0) >= 0.8 else 'viable',
            'skill_development_level': self.thresholds.get_development_intensity(analysis_data.get('avg_similarity', 0)).lower(),
            'development_priorities': 'technical competencies, domain knowledge, and process familiarisation',
            'development_timeline': self.thresholds.get_timeline_estimate(analysis_data.get('avg_similarity', 0)) + ' weeks',
            'location_count': '3-5',
            'location_distribution': 'Melbourne, Sydney, and Brisbane'
        }
        
        # Recursively replace variables in content
        def replace_in_dict(obj):
            if isinstance(obj, dict):
                return {k: replace_in_dict(v) for k, v in obj.items()}
            elif isinstance(obj, str):
                result = obj
                for key, value in replacements.items():
                    result = result.replace(f'{{{key}}}', str(value))
                return result
            else:
                return obj
        
        return replace_in_dict(content)
