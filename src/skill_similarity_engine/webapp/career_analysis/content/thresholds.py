"""
Threshold-based content selection logic for white paper generation.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import yaml

@dataclass
class ThresholdRange:
    """Represents a threshold range with associated content."""
    min_value: float
    max_value: float
    content_key: str
    descriptor: str

class ContentThresholds:
    """Manages threshold-based content selection."""
    
    def __init__(self):
        self.similarity_thresholds = [
            ThresholdRange(0.9, 1.0, "excellent_opportunities", "Outstanding"),
            ThresholdRange(0.7, 0.9, "excellent_opportunities", "Excellent"), 
            ThresholdRange(0.4, 0.7, "good_opportunities", "Good"),
            ThresholdRange(0.2, 0.4, "development_required", "Development Required"),
            ThresholdRange(0.0, 0.2, "transformation_required", "Transformation Required")
        ]
        
        self.pathway_count_thresholds = [
            ThresholdRange(5, 999, "multiple_pathways", "Multiple viable pathways"),
            ThresholdRange(2, 4, "several_pathways", "Several pathway options"),
            ThresholdRange(1, 1, "limited_pathways", "Limited pathway options")
        ]
        
        self.confidence_thresholds = [
            ThresholdRange(0.8, 1.0, "high_confidence", "High"),
            ThresholdRange(0.6, 0.8, "medium_high_confidence", "Medium-High"),
            ThresholdRange(0.4, 0.6, "medium_confidence", "Medium"),
            ThresholdRange(0.2, 0.4, "medium_low_confidence", "Medium-Low"),
            ThresholdRange(0.0, 0.2, "low_confidence", "Low")
        ]
    
    def get_narrative_type(self, similarity_score: float) -> str:
        """Determine narrative type based on similarity score."""
        for threshold in self.similarity_thresholds:
            if threshold.min_value <= similarity_score <= threshold.max_value:
                return threshold.content_key
        return "transformation_required"  # fallback
    
    def get_dynamic_descriptor(self, variable_name: str, value: float, 
                             variable_config: Dict) -> str:
        """Get dynamic descriptor based on threshold ranges."""
        if variable_name not in variable_config:
            return str(value)
        
        thresholds = variable_config[variable_name].get('thresholds', [])
        for threshold in thresholds:
            range_vals = threshold['range']
            if range_vals[0] <= value <= range_vals[1]:
                return threshold['value']
        
        return str(value)  # fallback to raw value
    
    def get_pathway_descriptor(self, pathway_count: int) -> str:
        """Get descriptor for pathway count."""
        for threshold in self.pathway_count_thresholds:
            if threshold.min_value <= pathway_count <= threshold.max_value:
                return threshold.descriptor
        return "No viable pathways"
    
    def get_confidence_descriptor(self, confidence_score: float) -> str:
        """Get confidence level descriptor."""
        for threshold in self.confidence_thresholds:
            if threshold.min_value <= confidence_score <= threshold.max_value:
                return threshold.descriptor
        return "Unknown"

    @staticmethod
    def get_timeline_estimate(similarity_score: float) -> str:
        """Get timeline estimate based on similarity score."""
        if similarity_score >= 0.8:
            return "8-12"
        elif similarity_score >= 0.6:
            return "12-16"
        else:
            return "16-24"
    
    @staticmethod
    def get_opportunity_descriptor(similarity_score: float) -> str:
        """Get opportunity descriptor based on similarity score."""
        if similarity_score >= 0.8:
            return "excellent"
        elif similarity_score >= 0.6:
            return "good"
        else:
            return "moderate"
    
    @staticmethod
    def get_skills_overlap_estimate(similarity_score: float) -> int:
        """Get skills overlap estimate based on similarity score."""
        return int(similarity_score * 85)  # Convert to percentage with some buffer
    
    @staticmethod
    def get_development_intensity(similarity_score: float) -> str:
        """Get development intensity based on similarity score."""
        if similarity_score >= 0.8:
            return "Light"
        elif similarity_score >= 0.6:
            return "Moderate"
        else:
            return "Intensive"
    
    @staticmethod
    def get_support_level(similarity_score: float) -> str:
        """Get support level based on similarity score."""
        if similarity_score >= 0.8:
            return "minimal"
        elif similarity_score >= 0.6:
            return "moderate"
        else:
            return "comprehensive"

class ContentPersonalizer:
    """Personalizes content based on calculated data and thresholds."""
    
    def __init__(self, template_loader):
        self.template_loader = template_loader
        self.thresholds = ContentThresholds()
    
    def personalize_paragraph(self, template_text: str, data: Dict[str, Any], 
                            variable_config: Optional[Dict] = None) -> str:
        """Replace template variables with personalized content."""
        if not template_text:
            return ""
        
        personalized = template_text
        variable_config = variable_config or {}
        
        # Replace basic variables first
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            if placeholder in personalized:
                # Convert value to string, handling different types
                if isinstance(value, (int, float)):
                    str_value = str(value)
                elif isinstance(value, dict):
                    # For complex objects, try to get a meaningful string representation
                    str_value = value.get('job_title', str(value))
                elif isinstance(value, list):
                    # For lists, join with commas
                    str_value = ', '.join(str(item) for item in value)
                else:
                    str_value = str(value)
                
                personalized = personalized.replace(placeholder, str_value)
        
        # Replace threshold-based variables
        for var_name, var_data in variable_config.items():
            if 'thresholds' in var_data and var_name in data:
                descriptor = self.thresholds.get_dynamic_descriptor(
                    var_name, float(data[var_name]), variable_config
                )
                placeholder = f"{{{var_name}}}"
                personalized = personalized.replace(placeholder, descriptor)
        
        # Handle special computed variables
        personalized = self._handle_computed_variables(personalized, data)
        
        return personalized
    
    def _handle_computed_variables(self, text: str, data: Dict[str, Any]) -> str:
        """Handle computed variables that need special logic."""
        
        # Handle percentage calculations
        if '{avg_similarity_percent}' in text:
            similarity = data.get('avg_similarity', 0)
            percentage = f"{similarity * 100:.1f}"
            text = text.replace('{avg_similarity_percent}', percentage)
        
        if '{skills_overlap_percentage}' in text:
            skills_data = data.get('skills_breakdown', {})
            overlap = skills_data.get('skills_overlap_percentage', 0)
            text = text.replace('{skills_overlap_percentage}', f"{overlap:.1f}")
        
        # Handle job title extraction
        if '{source_job_title}' in text:
            source_job = data.get('source_job_details', {})
            title = source_job.get('job_title', 'Unknown Position')
            text = text.replace('{source_job_title}', title)
        
        if '{target_job_title}' in text:
            target_job = data.get('target_job_details', {})
            title = target_job.get('job_title', 'Target Position')
            text = text.replace('{target_job_title}', title)
        
        # Handle workforce breakdown
        if '{position_breakdown}' in text:
            workforce = data.get('workforce_breakdown', {})
            divisions = workforce.get('divisional_distribution', [])
            if divisions:
                breakdown = ', '.join([f"{div['division']} ({div['position_count']})" 
                                     for div in divisions[:3]])  # Top 3 divisions
                text = text.replace('{position_breakdown}', breakdown)
            else:
                text = text.replace('{position_breakdown}', 'various positions')
        
        # Handle geographic distribution
        if '{location_distribution}' in text:
            workforce = data.get('workforce_breakdown', {})
            locations = workforce.get('geographic_distribution', [])
            if locations:
                location_list = ', '.join([loc['location'] for loc in locations[:3]])
                text = text.replace('{location_distribution}', location_list)
            else:
                text = text.replace('{location_distribution}', 'multiple locations')
        
        # Handle timeline estimates
        if '{timeline_weeks}' in text:
            confidence = data.get('confidence_level', 'Medium')
            if confidence in ['High', 'Medium-High']:
                timeline = "8-12"
            elif confidence == 'Medium':
                timeline = "12-16"
            else:
                timeline = "16-24"
            text = text.replace('{timeline_weeks}', timeline)
        
        # Handle success probability
        if '{success_probability_percent}' in text:
            similarity = data.get('avg_similarity', 0)
            if similarity >= 0.8:
                probability = "85-95"
            elif similarity >= 0.6:
                probability = "70-85"
            elif similarity >= 0.4:
                probability = "55-70"
            else:
                probability = "40-55"
            text = text.replace('{success_probability_percent}', probability)
        
        # Handle skill retention
        if '{skill_retention_percent}' in text:
            skills_data = data.get('skills_breakdown', {})
            overlap = skills_data.get('skills_overlap_percentage', 0)
            # Skill retention is typically higher than overlap due to transferable skills
            retention = min(100, overlap + 15)
            text = text.replace('{skill_retention_percent}', f"{retention:.0f}")
        
        return text
    
    def personalize_content_section(self, section_template: Dict, data: Dict[str, Any], 
                                  variable_config: Optional[Dict] = None) -> Dict[str, str]:
        """Personalize an entire content section with multiple paragraphs."""
        personalized_section = {}
        
        for key, template_text in section_template.items():
            if isinstance(template_text, str):
                personalized_section[key] = self.personalize_paragraph(
                    template_text, data, variable_config
                )
            elif isinstance(template_text, dict):
                # Nested section
                personalized_section[key] = self.personalize_content_section(
                    template_text, data, variable_config
                )
        
        return personalized_section
    
    def apply_audience_adaptations(self, content: Dict, audience_template: Dict, 
                                 data: Dict[str, Any]) -> Dict:
        """Apply audience-specific adaptations to content."""
        if not audience_template or 'adaptations' not in audience_template:
            return content
        
        adaptations = audience_template['adaptations']
        adapted_content = content.copy()
        
        # Apply tone adjustments
        if 'tone' in adaptations:
            tone_config = adaptations['tone']
            # This is a simplified implementation - in reality, you might use NLP
            # to adjust language complexity, formality, etc.
            adapted_content['tone_applied'] = tone_config.get('style', 'professional')
        
        # Apply focus adjustments
        if 'focus_areas' in adaptations:
            focus_areas = adaptations['focus_areas']
            adapted_content['focus_areas'] = focus_areas
        
        # Apply additional context based on audience
        if 'additional_context' in adaptations:
            context_template = adaptations['additional_context']
            adapted_content['additional_context'] = self.personalize_paragraph(
                context_template, data
            )
        
        return adapted_content
    
    def apply_scenario_adaptations(self, content: Dict, scenario_template: Dict,
                                 data: Dict[str, Any]) -> Dict:
        """Apply scenario-specific adaptations to content."""
        if not scenario_template or 'adaptations' not in scenario_template:
            return content
        
        adaptations = scenario_template['adaptations']
        adapted_content = content.copy()
        
        # Apply urgency indicators
        if 'urgency' in adaptations:
            urgency_level = data.get('scenario_context', {}).get('timeline_urgency', 'Medium')
            adapted_content['urgency_level'] = urgency_level
            
            # Add urgency-specific language
            if urgency_level == 'High':
                adapted_content['urgency_indicator'] = "immediate attention required"
            elif urgency_level == 'Medium':
                adapted_content['urgency_indicator'] = "timely action recommended"
            else:
                adapted_content['urgency_indicator'] = "planned approach suggested"
        
        # Apply business driver context
        if 'business_context' in adaptations:
            driver = data.get('scenario_context', {}).get('business_driver', 'Unknown')
            adapted_content['business_driver'] = driver
        
        return adapted_content
