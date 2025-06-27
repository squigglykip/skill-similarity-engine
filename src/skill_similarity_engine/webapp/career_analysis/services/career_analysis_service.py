"""
Career Analysis Service

Main orchestrator for career analysis generation that integrates with existing generators
and provides proper separation between web preview and document generation modes.
"""

from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

# Import existing generators - use absolute imports to avoid relative import issues
import sys
from pathlib import Path

# Add src directory to path for importing generators
src_path = Path(__file__).parent.parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
    
# Import path is working correctly now

try:
    from executive_summary_generator import ExecutiveSummaryGenerator
    from current_role_context_generator import CurrentRoleContextGenerator
    from pathway_analysis_generator import PathwayAnalysisGenerator
    from strategic_recommendations_generator import StrategicRecommendationsGenerator
    from conclusion_generator import ConclusionGenerator
    GENERATORS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Could not import generators: {e}")
    print(f"Tried importing from: {src_path}")
    GENERATORS_AVAILABLE = False
    
    # Create mock classes for testing
    class MockGenerator:
        def __init__(self, *args, **kwargs):
            pass
        def generate(self, *args, **kwargs):
            return {"mock": "data", "content": "Mock generator content"}
    
    ExecutiveSummaryGenerator = MockGenerator
    CurrentRoleContextGenerator = MockGenerator
    PathwayAnalysisGenerator = MockGenerator
    StrategicRecommendationsGenerator = MockGenerator
    ConclusionGenerator = MockGenerator

logger = logging.getLogger(__name__)

class CareerAnalysisService:
    """
    Main service for coordinating career analysis generation for web requests.
    
    This service replaces the subprocess CLI approach with direct Python calls
    to the existing generators, providing both web preview and document modes.
    """
    
    def __init__(self, db_connection):
        """Initialize the service with database connection."""
        self.db = db_connection
        
        # Initialize generators
        self.executive_generator = ExecutiveSummaryGenerator(db_connection)
        self.context_generator = CurrentRoleContextGenerator(db_connection)
        self.pathway_generator = PathwayAnalysisGenerator(db_connection)
        self.recommendations_generator = StrategicRecommendationsGenerator(db_connection)
        self.conclusion_generator = ConclusionGenerator(db_connection)
        
        logger.info("CareerAnalysisService initialized with database connection")
    
    def generate_analysis(self, job_from: str, analysis_mode: str = 'top_matches', 
                         output_mode: str = 'web', **kwargs) -> Dict[str, Any]:
        """
        Generate complete career analysis with proper output mode separation.
        
        Args:
            job_from: Source job profile ID
            analysis_mode: 'top_matches' or 'specific'
            output_mode: 'web' for preview or 'document' for Word generation
            **kwargs: Additional parameters (job_to, similarity_min, similarity_max, top_n, etc.)
            
        Returns:
            Dict with sections, metadata, and success status
        """
        try:
            logger.info(f"Generating {output_mode} analysis for {job_from} in {analysis_mode} mode")
            
            # Extract parameters
            job_to = kwargs.get('job_to')
            similarity_min = kwargs.get('similarity_min', 40)
            similarity_max = kwargs.get('similarity_max', 90)
            top_n = kwargs.get('top_n', 3)
            include_deployment = kwargs.get('include_organisational_deployment', True)  # Default to True for web previews
            
            # Generate all 5 sections using existing generators
            sections = {}
            
            # 1. Executive Summary
            logger.debug("Generating Executive Summary")
            exec_result = self.executive_generator.generate(
                job_from=job_from,
                analysis_mode=analysis_mode,
                job_to=job_to,
                similarity_range=(similarity_min/100.0, similarity_max/100.0),
                top_n=top_n
            )
            sections['executive_summary'] = self._format_section_for_mode(
                exec_result, output_mode, 'Executive Summary'
            )
            
            # 2. Current Role Context
            logger.info("Generating Current Role Context")
            try:
                context_result = self.context_generator.generate(
                    job_from=job_from,
                    include_organisational_deployment=include_deployment
                )
                logger.info("Current Role Context generation completed successfully")
            except Exception as e:
                logger.error(f"Current Role Context generation failed: {str(e)}")
                context_result = {'content': {}}
            
            try:
                sections['current_role_context'] = self._format_section_for_mode(
                    context_result, output_mode, 'Current Role Context'
                )
                logger.info("Current Role Context formatting completed successfully")
            except Exception as e:
                logger.error(f"Current Role Context formatting failed: {str(e)}")
                # Provide a safe fallback
                sections['current_role_context'] = {
                    'title': 'Current Role Context',
                    'section_key': 'current_role_context',
                    'subsections': {
                        'error': {
                            'title': 'Processing Error',
                            'content': f'Error formatting current role context: {str(e)}',
                            'formatting': {},
                            'type': 'formatted_content'
                        }
                    }
                }
            
            # 3. Pathway Analysis
            logger.debug("Generating Pathway Analysis")
            pathway_result = self.pathway_generator.generate(
                job_from=job_from,
                analysis_mode=analysis_mode,
                job_to=job_to,
                similarity_range=(similarity_min/100.0, similarity_max/100.0),
                include_organisational_deployment=include_deployment,
                top_n=top_n
            )
            pathway_title = f"Pathway Analysis: Top {top_n} Strategic Opportunities"
            if analysis_mode == 'specific' and job_to:
                pathway_title = "Strategic Transition Analysis"
            sections['pathway_analysis'] = self._format_section_for_mode(
                pathway_result, output_mode, pathway_title
            )
            
            # 4. Strategic Recommendations
            logger.debug("Generating Strategic Recommendations")
            recommendations_result = self.recommendations_generator.generate(
                job_from=job_from,
                analysis_mode=analysis_mode,
                job_to=job_to,
                similarity_range=(similarity_min/100.0, similarity_max/100.0),
                include_organisational_deployment=include_deployment,
                top_n=top_n
            )
            sections['strategic_recommendations'] = self._format_section_for_mode(
                recommendations_result, output_mode, 'Strategic Recommendations'
            )
            
            # 5. Conclusion
            logger.debug("Generating Conclusion")
            conclusion_result = self.conclusion_generator.generate(
                job_from=job_from,
                analysis_mode=analysis_mode,
                job_to=job_to,
                similarity_range=(similarity_min/100.0, similarity_max/100.0),
                include_organisational_deployment=include_deployment,
                top_n=top_n
            )
            sections['conclusion'] = self._format_section_for_mode(
                conclusion_result, output_mode, 'Conclusion'
            )
            
            # Generate metadata
            metadata = self._generate_metadata(job_from, analysis_mode, **kwargs)
            
            logger.info(f"Successfully generated {output_mode} analysis with {len(sections)} sections")
            
            return {
                'success': True,
                'sections': sections,
                'metadata': metadata,
                'output_mode': output_mode
            }
            
        except Exception as e:
            logger.error(f"Error generating analysis: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'sections': {},
                'metadata': {}
            }
    
    def _format_section_for_mode(self, section_data: Dict, output_mode: str, section_title: str) -> Dict[str, Any]:
        """
        Format section data appropriately for web preview vs document generation.
        
        Args:
            section_data: Raw section data from generators
            output_mode: 'web' or 'document'
            section_title: Title for the section
            
        Returns:
            Formatted section data
        """
        if output_mode == 'web':
            return self._format_for_web_preview(section_data, section_title)
        elif output_mode == 'document':
            return self._format_for_document_generation(section_data, section_title)
        else:
            return section_data
    
    def _format_for_web_preview(self, section_data: Dict, section_title: str) -> Dict[str, Any]:
        """
        Format section data for web preview consumption.
        
        Converts the generator output into structured JSON that the JavaScript
        can easily parse and render with proper formatting.
        """
        # Only log section title for non-debug modes
        logger.debug(f"Formatting section '{section_title}' for web preview")
        
        # Extract the main content sections from generator output
        generator_content = section_data.get('content', {})
        
        # Format subsections for web preview
        subsections = {}
        
        for subsection_key, subsection_data in generator_content.items():
            logger.debug(f"DEBUG: Processing subsection '{subsection_key}'")
            logger.debug(f"DEBUG: Subsection data type: {type(subsection_data)}")
            logger.debug(f"DEBUG: Subsection data: {subsection_data}")
            
            if isinstance(subsection_data, dict):
                # Extract title
                title = subsection_data.get('title', subsection_key.replace('_', ' ').title())
                
                # Extract content - handle simple, complex, and ContentFormatter structures
                content_data = subsection_data.get('content', '')
                logger.debug(f"DEBUG: Content data type for {subsection_key}: {type(content_data)}")
                logger.debug(f"DEBUG: Content data for {subsection_key}: {content_data}")
                
                if isinstance(content_data, list):
                    # Debug the section matching
                    logger.debug(f"DEBUG: Checking special handling - subsection_key: '{subsection_key}', section_title: '{section_title}'")
                    
                    # Special handling for pathway analysis opportunities
                    if subsection_key == 'opportunities' and 'pathway' in section_title.lower():
                        logger.debug(f"DEBUG: ✅ TRIGGERED special handling for pathway analysis opportunities")
                        logger.debug(f"DEBUG: Content list length: {len(content_data)}")
                        # Convert opportunities list to JSON-serializable format
                        actual_content = self._format_opportunities_for_web(content_data)
                        formatting = {}
                        logger.debug(f"DEBUG: Formatted opportunities result length: {len(actual_content) if actual_content else 0}")
                    else:
                        # List of ContentFormatter objects - extract and combine
                        logger.debug(f"DEBUG: Processing ContentFormatter list for {subsection_key}, length: {len(content_data)}")
                        actual_content = self._extract_from_content_list(content_data)
                        formatting = self._extract_formatting_from_list(content_data)
                        logger.debug(f"DEBUG: Extracted content length: {len(actual_content) if actual_content else 0}")
                elif isinstance(content_data, dict):
                    # Complex structure: {"text": "...", "formatting": {...}}
                    actual_content = content_data.get('text', '')
                    formatting = content_data.get('formatting', {})
                    logger.debug(f"DEBUG: Dict content length: {len(actual_content) if actual_content else 0}")
                else:
                    # Simple structure: just a string
                    actual_content = content_data
                    formatting = {}
                    logger.debug(f"DEBUG: String content length: {len(actual_content) if actual_content else 0}")
                
                # Create standardized subsection structure
                subsections[subsection_key] = {
                    'title': title,
                    'content': actual_content,
                    'formatting': formatting,
                    'type': 'formatted_content'
                }
            else:
                # Handle edge case where subsection_data is not a dict
                subsections[subsection_key] = {
                    'title': subsection_key.replace('_', ' ').title(),
                    'content': str(subsection_data) if subsection_data else '',
                    'formatting': {},
                    'type': 'formatted_content'
                }
        
        return {
            'title': section_title,
            'section_key': section_title.lower().replace(' ', '_'),
            'subsections': subsections
        }
    
    def _format_for_document_generation(self, section_data: Dict, section_title: str) -> Dict[str, Any]:
        """
        Format section data for document generation (Word/PDF).
        
        Returns the data in the format expected by the DocumentFormatter.
        """
        # Document generation uses the existing format from generators
        return section_data
    
    def _format_subsection_title(self, subsection_key: str) -> str:
        """Convert subsection keys to proper display titles."""
        # Convert snake_case to Title Case
        return subsection_key.replace('_', ' ').title()
    
    def _extract_from_content_list(self, content_list: list) -> str:
        """Extract text content from a list of ContentFormatter objects."""
        combined_text = []
        
        logger.debug(f"DEBUG: EXTRACTING from content list with {len(content_list)} items")
        logger.debug(f"DEBUG: Content list structure: {content_list}")
        
        for i, item in enumerate(content_list):
            logger.debug(f"DEBUG: Item {i}: type={type(item)}")
            logger.debug(f"DEBUG: Item {i} content: {item}")
            
            if isinstance(item, dict):
                logger.debug(f"DEBUG: Item {i} keys: {list(item.keys())}")
                
                if 'text' in item:
                    # ContentFormatter object with text field
                    text_content = item['text']
                    logger.debug(f"DEBUG: Item {i} text length: {len(text_content)}")
                    logger.debug(f"DEBUG: Item {i} text preview: {text_content[:100]}...")
                    combined_text.append(text_content)
                else:
                    logger.warning(f"WARNING: Dict item {i} has no 'text' key: {item}")
            elif isinstance(item, str):
                # Plain string
                logger.debug(f"DEBUG: Item {i} is string, length: {len(item)}")
                combined_text.append(item)
            else:
                # Convert to string as fallback
                str_content = str(item)
                logger.debug(f"DEBUG: Item {i} converted to string, length: {len(str_content)}")
                combined_text.append(str_content)
        
        result = '\n\n'.join(combined_text)
        logger.debug(f"DEBUG: FINAL combined text length: {len(result)}")
        logger.debug(f"DEBUG: FINAL combined text preview: {result[:200]}...")
        return result
    
    def _extract_formatting_from_list(self, content_list: list) -> dict:
        """Extract formatting metadata from the first ContentFormatter object in the list."""
        for item in content_list:
            if isinstance(item, dict) and 'formatting' in item:
                return item['formatting']
        
        # Default formatting if no ContentFormatter objects found
        return {'content_type': 'mixed'}
    
    def _generate_metadata(self, job_from: str, analysis_mode: str, **kwargs) -> Dict[str, Any]:
        """Generate metadata about the analysis for frontend consumption."""
        
        # Get job details for metadata
        try:
            job_query = self.db.execute("""
                SELECT JobProfile, Job, ProfileTitleSuffix, ManagementLevel, JobFunction
                FROM jobs WHERE JobProfileID = ?
            """, (job_from,)).fetchone()
            
            if job_query:
                source_job_title = f"{job_query['Job']}"
                if job_query['ProfileTitleSuffix']:
                    source_job_title += f" {job_query['ProfileTitleSuffix']}"
                if job_query['ManagementLevel']:
                    source_job_title += f" ({job_query['ManagementLevel']})"
                
                source_job_function = job_query['JobFunction']
            else:
                source_job_title = job_from
                source_job_function = 'Unknown'
                
        except Exception as e:
            logger.warning(f"Could not fetch job details for metadata: {e}")
            source_job_title = job_from
            source_job_function = 'Unknown'
        
        return {
            'job_from': job_from,
            'job_to': kwargs.get('job_to'),
            'analysis_mode': analysis_mode,
            'source_job_title': source_job_title,
            'source_job_function': source_job_function,
            'similarity_range': {
                'min': kwargs.get('similarity_min', 40),
                'max': kwargs.get('similarity_max', 90)
            },
            'top_n': kwargs.get('top_n', 3),
            'include_deployment': kwargs.get('include_organisational_deployment', False),
            'generated_sections': 5,
            'timestamp': None  # Will be set by frontend
        }
    
    def _format_opportunities_for_web(self, opportunities_list: list) -> list:
        """
        Format pathway analysis opportunities list for web consumption.
        
        Converts the list of opportunity dictionaries into JSON-serializable format
        instead of returning the string representation.
        """
        try:
            logger.debug(f"DEBUG: Formatting {len(opportunities_list)} opportunities for web")
            
            formatted_opportunities = []
            
            for i, opportunity in enumerate(opportunities_list):
                logger.debug(f"DEBUG: Processing opportunity {i}, type: {type(opportunity)}")
                
                if isinstance(opportunity, dict):
                    # Convert ContentFormatter objects to simple dict structure
                    formatted_opportunity = {}
                    
                    for key, value in opportunity.items():
                        logger.debug(f"DEBUG: Processing opportunity key '{key}', value type: {type(value)}")
                        
                        if isinstance(value, dict) and 'content' in value:
                            # This is a ContentFormatter-like object
                            content_data = value['content']
                            
                            if isinstance(content_data, dict) and 'text' in content_data:
                                # Extract text and formatting
                                formatted_opportunity[key] = {
                                    'title': value.get('title', key.replace('_', ' ').title()),
                                    'content': content_data.get('text', ''),
                                    'formatting': content_data.get('formatting', {}),
                                    'content_type': content_data.get('formatting', {}).get('content_type', 'text')
                                }
                            else:
                                # Simple content
                                formatted_opportunity[key] = {
                                    'title': value.get('title', key.replace('_', ' ').title()),
                                    'content': str(content_data),
                                    'formatting': value.get('formatting', {}),
                                    'content_type': 'text'
                                }
                        else:
                            # Simple value or string
                            formatted_opportunity[key] = value
                    
                    formatted_opportunities.append(formatted_opportunity)
                else:
                    # Convert non-dict to string
                    formatted_opportunities.append({'content': str(opportunity)})
            
            logger.debug(f"DEBUG: Successfully formatted {len(formatted_opportunities)} opportunities")
            return formatted_opportunities
            
        except Exception as e:
            logger.error(f"ERROR: Failed to format opportunities for web: {e}", exc_info=True)
            # Return original data as fallback
            return opportunities_list