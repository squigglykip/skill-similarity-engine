"""
Preview Service

Specialized service for generating structured data for web preview consumption
that JavaScript can easily consume and render.
"""

from typing import Dict, List, Optional, Any
import logging

try:
    from .career_analysis_service import CareerAnalysisService
except ImportError:
    # Fallback for when running as script
    from career_analysis_service import CareerAnalysisService

logger = logging.getLogger(__name__)

class PreviewService:
    """
    Specialized service for generating web preview data.
    
    This service focuses on creating structured JSON responses that the frontend
    JavaScript can easily parse and display with proper formatting.
    """
    
    def __init__(self, db_connection):
        """Initialize the preview service with database connection."""
        self.db = db_connection
        self.analysis_service = CareerAnalysisService(db_connection)
        
        logger.info("PreviewService initialized")
    
    def generate_preview(self, form_data: Dict) -> Dict[str, Any]:
        """
        Generate structured preview data for JavaScript display.
        
        Args:
            form_data: Form data from the frontend containing job_from, analysis_mode, etc.
            
        Returns:
            Dict with structured content ready for frontend consumption
        """
        try:
            logger.info(f"Generating preview for form data: {form_data}")
            
            # Extract and validate parameters
            parameters = self._extract_parameters(form_data)
            
            # Validate required parameters
            if not parameters['job_from']:
                return {
                    'success': False,
                    'error': 'job_from is required',
                    'content': {},
                    'metadata': {}
                }
            
            # Generate analysis using the main service in web mode
            result = self.analysis_service.generate_analysis(
                job_from=parameters['job_from'],
                analysis_mode=parameters['analysis_mode'],
                output_mode='web',  # Always web mode for preview
                job_to=parameters.get('job_to'),
                similarity_min=parameters.get('similarity_min', 40),
                similarity_max=parameters.get('similarity_max', 90),
                top_n=parameters.get('top_n', 3),
                include_organisational_deployment=parameters.get('include_organisational_deployment', False)
            )
            
            if not result['success']:
                return result
            
            # Process the sections for optimal web display
            processed_content = self._process_content_for_web(result['sections'])
            
            # Add preview-specific metadata
            preview_metadata = self._enhance_metadata_for_preview(result['metadata'], parameters)
            
            logger.info(f"Successfully generated preview with {len(processed_content)} sections")
            
            return {
                'success': True,
                'content': processed_content,
                'metadata': preview_metadata,
                'preview_ready': True
            }
            
        except Exception as e:
            logger.error(f"Error generating preview: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'content': {},
                'metadata': {}
            }
    
    def _extract_parameters(self, form_data: Dict) -> Dict[str, Any]:
        """Extract and validate parameters from form data."""
        return {
            'job_from': form_data.get('job_from', ''),
            'job_to': form_data.get('job_to'),
            'analysis_mode': form_data.get('analysis_mode', 'top_matches'),
            'similarity_min': int(form_data.get('similarity_min', 40)),
            'similarity_max': int(form_data.get('similarity_max', 90)),
            'top_n': int(form_data.get('top_n', 3)),
            'include_organisational_deployment': form_data.get('include_deployment', True),  # Default to True for web previews
            'tie_breaking_options': form_data.get('tie_breaking_options', {}),
        }
    
    def _process_content_for_web(self, sections: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process section content for optimal web display.
        
        This method enhances the content with additional formatting hints
        and ensures all data is in a format that JavaScript can easily consume.
        """
        processed_sections = {}
        
        for section_key, section_data in sections.items():
            processed_sections[section_key] = self._process_section_for_web(
                section_data, section_key
            )
        
        return processed_sections
    
    def _process_section_for_web(self, section_data: Dict[str, Any], section_key: str) -> Dict[str, Any]:
        """Process an individual section for web display."""
        
        processed_section = {
            'title': section_data.get('title', self._format_section_title(section_key)),
            'section_key': section_key,
            'subsections': {}
        }
        
        # Process subsections
        subsections = section_data.get('subsections', {})
        for subsection_key, subsection_data in subsections.items():
            processed_section['subsections'][subsection_key] = self._process_subsection_for_web(
                subsection_data, subsection_key
            )
        
        return processed_section
    
    def _process_subsection_for_web(self, subsection_data: Dict[str, Any], subsection_key: str) -> Dict[str, Any]:
        """Process an individual subsection for web display."""
        
        # Handle different content types
        if 'content_items' in subsection_data:
            # List of formatted content items (from generators)
            return {
                'title': subsection_data.get('title', self._format_subsection_title(subsection_key)),
                'type': 'content_items',
                'items': self._process_content_items(subsection_data['content_items'])
            }
        else:
            # Single content item with formatting
            return {
                'title': subsection_data.get('title', self._format_subsection_title(subsection_key)),
                'type': 'formatted_content',
                'content': subsection_data.get('content', ''),
                'formatting': subsection_data.get('formatting', {'content_type': 'paragraph'})
            }
    
    def _process_content_items(self, content_items: List[Dict]) -> List[Dict[str, Any]]:
        """Process a list of content items for web display."""
        processed_items = []
        
        for item in content_items:
            if isinstance(item, dict):
                # Item with formatting metadata
                processed_items.append({
                    'content': item.get('text', ''),
                    'formatting': item.get('formatting', {'content_type': 'paragraph'})
                })
            else:
                # String item - wrap in basic formatting
                processed_items.append({
                    'content': str(item),
                    'formatting': {'content_type': 'paragraph'}
                })
        
        return processed_items
    
    def _enhance_metadata_for_preview(self, metadata: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance metadata with preview-specific information."""
        
        preview_metadata = metadata.copy()
        
        # Add preview-specific fields
        preview_metadata.update({
            'preview_mode': True,
            'section_count': 5,
            'parameters_used': parameters,
            'display_hints': {
                'show_section_navigation': True,
                'enable_section_collapsing': True,
                'highlight_tables': True,
                'format_bold_labels': True
            }
        })
        
        return preview_metadata
    
    def _format_section_title(self, section_key: str) -> str:
        """Convert section keys to proper display titles."""
        title_map = {
            'executive_summary': 'Executive Summary',
            'current_role_context': 'Current Role Context',
            'pathway_analysis': 'Pathway Analysis',
            'strategic_recommendations': 'Strategic Recommendations',
            'conclusion': 'Conclusion'
        }
        return title_map.get(section_key, section_key.replace('_', ' ').title())
    
    def _format_subsection_title(self, subsection_key: str) -> str:
        """Convert subsection keys to proper display titles."""
        return subsection_key.replace('_', ' ').title()
    
    def validate_job_exists(self, job_id: str) -> bool:
        """Validate that a job ID exists in the database."""
        try:
            result = self.db.execute(
                "SELECT 1 FROM jobs WHERE JobProfileID = ?", 
                (job_id,)
            ).fetchone()
            return result is not None
        except Exception as e:
            logger.error(f"Error validating job {job_id}: {e}")
            return False 