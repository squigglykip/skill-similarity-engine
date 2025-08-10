"""
Career Analysis Service

Main orchestrator for career analysis generation that integrates with existing generators
and provides proper separation between web preview and document generation modes.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
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
        
        print("CareerAnalysisService initialized with database connection")
    
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
            print(f"Generating {output_mode} analysis for {job_from} in {analysis_mode} mode")
            
            # Extract parameters
            job_to = kwargs.get('job_to')
            similarity_min = kwargs.get('similarity_min', 40)
            similarity_max = kwargs.get('similarity_max', 90)
            top_n = kwargs.get('top_n', 3)
            include_deployment = kwargs.get('include_organisational_deployment', True)  # Default to True for web previews
            tie_breaking_options = kwargs.get('tie_breaking_options', {})
            
            # Generate all 5 sections using existing generators
            sections = {}
            
            # 1. Executive Summary
            logger.debug("Generating Executive Summary")
            exec_result = self.executive_generator.generate(
                job_from=job_from,
                analysis_mode=analysis_mode,
                job_to=job_to,
                similarity_range=(similarity_min/100.0, similarity_max/100.0),
                top_n=top_n,
                tie_breaking_options=tie_breaking_options
            )
            # Use the section title from the generator, fallback to default if not available
            exec_title = exec_result.get('section_title', 'Executive Summary')
            if not isinstance(exec_title, str):
                exec_title = 'Executive Summary'
            sections['executive_summary'] = self._format_section_for_mode(
                exec_result, output_mode, exec_title
            )
            
            # 2. Current Role Context
            print("Generating Current Role Context")
            try:
                context_result = self.context_generator.generate(
                    job_from=job_from,
                    include_organisational_deployment=include_deployment
                )
                print("Current Role Context generation completed successfully")
            except Exception as e:
                logger.error(f"Current Role Context generation failed: {str(e)}")
                context_result = {'content': {}}
            
            try:
                # Use the section title from the generator, fallback to default if not available
                context_title = context_result.get('section_title', 'Current Role Context')
                if not isinstance(context_title, str):
                    context_title = 'Current Role Context'
                sections['current_role_context'] = self._format_section_for_mode(
                    context_result, output_mode, context_title
                )
                print("Current Role Context formatting completed successfully")
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
                top_n=top_n,
                tie_breaking_options=tie_breaking_options,
                output_format=output_mode  # Pass web/document format to generator
            )
            
            # 🚨 EARLY DETECTION: Check if pathway analysis found no opportunities
            print(f"🔍 DEBUG: Checking pathway result for opportunities...")
            print(f"🔍 DEBUG: Pathway result type: {type(pathway_result)}")
            if isinstance(pathway_result, dict):
                print(f"🔍 DEBUG: Pathway result keys: {list(pathway_result.keys())}")
                content = pathway_result.get('content', {})
                if isinstance(content, dict):
                    print(f"🔍 DEBUG: Pathway result content keys: {list(content.keys())}")
                else:
                    print(f"🔍 DEBUG: Pathway content is not a dict: {type(content)}")
            else:
                print(f"🔍 DEBUG: Pathway result is not a dict: {pathway_result}")
            
            if self._has_no_opportunities(pathway_result):
                print("🚫 No career pathways found within similarity range - returning simplified no-results response")
                return self._create_no_results_response(job_from, similarity_min, similarity_max, output_mode)
            else:
                print("✅ Opportunities found - continuing with full analysis")
            
            # Use the section title from the generator, with intelligent fallback
            pathway_title = pathway_result.get('section_title')
            if not isinstance(pathway_title, str) or not pathway_title:
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
            # Use the section title from the generator, fallback to default if not available
            recommendations_title = recommendations_result.get('section_title', 'Strategic Recommendations')
            if not isinstance(recommendations_title, str):
                recommendations_title = 'Strategic Recommendations'
            sections['strategic_recommendations'] = self._format_section_for_mode(
                recommendations_result, output_mode, recommendations_title
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
            # Use the section title from the generator, fallback to default if not available
            conclusion_title = conclusion_result.get('section_title', 'Conclusion')
            if not isinstance(conclusion_title, str):
                conclusion_title = 'Conclusion'
            sections['conclusion'] = self._format_section_for_mode(
                conclusion_result, output_mode, conclusion_title
            )
            
            # Generate metadata
            metadata = self._generate_metadata(job_from, analysis_mode, **kwargs)
            
            print(f"Successfully generated {output_mode} analysis with {len(sections)} sections")
            
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
            
            # Special handling for when subsection_data is directly a list (opportunities case)
            if isinstance(subsection_data, list) and subsection_key == 'opportunities' and ('pathway' in section_title.lower() or 'transition' in section_title.lower()):
                print(f"🎯 TRIGGERED special handling for direct opportunities list")
                print(f"🎯 Opportunities list length: {len(subsection_data)}")
                print(f"🎯 First opportunity type: {type(subsection_data[0]) if subsection_data else 'EMPTY'}")
                
                # Convert opportunities list to JSON-serializable format
                formatted_opportunities = self._format_opportunities_for_web(subsection_data)
                
                # Store opportunities in a special structure for frontend
                subsections[subsection_key] = {
                    'title': subsection_key.replace('_', ' ').title(),
                    'content': formatted_opportunities,  # Store as list directly
                    'formatting': {},
                    'type': 'opportunities_list'  # Special type for frontend handling
                }
                print(f"🎯 Stored direct opportunities as list with {len(formatted_opportunities)} items")
                continue  # Skip the normal processing below
            
            if isinstance(subsection_data, dict):
                # Extract title
                title = subsection_data.get('title', subsection_key.replace('_', ' ').title())
                
                # Extract content - handle simple, complex, and ContentFormatter structures
                content_data = subsection_data.get('content', '')
                logger.debug(f"DEBUG: Content data type for {subsection_key}: {type(content_data)}")
                logger.debug(f"DEBUG: Content data for {subsection_key}: {content_data}")
                
                if isinstance(content_data, list):
                    # Debug the section matching
                    print(f"🔍 CHECKING special handling - subsection_key: '{subsection_key}', section_title: '{section_title}'")
                    print(f"🔍 Content data length: {len(content_data)}")
                    print(f"🔍 Is opportunities? {subsection_key == 'opportunities'}")
                    print(f"🔍 Contains pathway? {'pathway' in section_title.lower()}")
                    print(f"🔍 Contains transition? {'transition' in section_title.lower()}")
                    
                    # Special handling for pathway analysis opportunities
                    print(f"🔍 Special handling condition evaluation:")
                    print(f"   - subsection_key == 'opportunities': {subsection_key == 'opportunities'}")
                    print(f"   - section_title.lower(): '{section_title.lower()}'")
                    print(f"   - 'pathway' in section_title.lower(): {'pathway' in section_title.lower()}")
                    print(f"   - 'transition' in section_title.lower(): {'transition' in section_title.lower()}")
                    print(f"   - Combined condition: {subsection_key == 'opportunities' and ('pathway' in section_title.lower() or 'transition' in section_title.lower())}")
                    
                    if subsection_key == 'opportunities' and ('pathway' in section_title.lower() or 'transition' in section_title.lower()):
                        print(f"🎯 TRIGGERED special handling for pathway analysis opportunities")
                        print(f"🎯 Content list length: {len(content_data)}")
                        print(f"🎯 Content data type: {type(content_data)}")
                        print(f"🎯 First item type: {type(content_data[0]) if content_data else 'EMPTY'}")
                        
                        # Convert opportunities list to JSON-serializable format
                        formatted_opportunities = self._format_opportunities_for_web(content_data)
                        
                        # Store opportunities in a special structure for frontend
                        subsections[subsection_key] = {
                            'title': title,
                            'content': formatted_opportunities,  # Store as list directly
                            'formatting': {},
                            'type': 'opportunities_list'  # Special type for frontend handling
                        }
                        print(f"🎯 Stored opportunities as list with {len(formatted_opportunities)} items")
                        print(f"🎯 First opportunity keys: {list(formatted_opportunities[0].keys()) if formatted_opportunities else 'EMPTY'}")
                        print(f"🎯 About to continue - skipping normal processing")
                        continue  # Skip the normal processing below
                    
                    # 🔧 FIX: Special handling for Core Competency Foundation with mixed content (intro + table)
                    elif subsection_key == 'core_competency_foundation':
                        print(f"🔧 CHECKING Core Competency Foundation condition")
                        print(f"🔧 subsection_key: '{subsection_key}'")
                        print(f"🔧 section_title: '{section_title}'")
                        print(f"🔧 section_title.lower(): '{section_title.lower()}'")
                        print(f"🔧 'current role context' in section_title.lower(): {'current role context' in section_title.lower()}")
                        
                        if 'current role context' in section_title.lower():
                            print(f"🔧 TRIGGERED special handling for Core Competency Foundation with structured content")
                            print(f"🔧 Content list length: {len(content_data)}")
                            print(f"🔧 Content data items: {[type(item) for item in content_data]}")
                            
                            # Keep the content as a structured array instead of converting to text
                            # This preserves the separation between intro paragraph and table
                            structured_content = []
                            for i, item in enumerate(content_data):
                                print(f"🔧 Processing item {i}: type={type(item)}, keys={list(item.keys()) if isinstance(item, dict) else 'Not dict'}")
                                if isinstance(item, dict):
                                    if item.get('type') == 'structured_table':
                                        # Preserve structured table for frontend
                                        structured_content.append(item)
                                        print(f"🔧 Preserved structured table with {len(item.get('headers', []))} headers")
                                    elif 'text' in item:
                                        # Convert ContentFormatter paragraph to simple text item
                                        structured_content.append({
                                            'type': 'formatted_content',
                                            'content_type': item.get('content_type', 'paragraph'),
                                            'text': item['text']
                                        })
                                        print(f"🔧 Preserved paragraph content: {item['text'][:50]}...")
                                    else:
                                        structured_content.append(item)
                                        print(f"🔧 Preserved other dict item with keys: {list(item.keys())}")
                                else:
                                    structured_content.append({'type': 'text', 'text': str(item)})
                                    print(f"🔧 Converted non-dict item to text: {str(item)[:50]}...")
                            
                            subsections[subsection_key] = {
                                'title': title,
                                'content': structured_content,  # Keep as structured array
                                'formatting': {'content_type': 'structured_mixed'},
                                'type': 'structured_mixed_content'  # Special type for frontend
                            }
                            print(f"🔧 Stored Core Competency Foundation as structured content with {len(structured_content)} items")
                            print(f"🔧 Final subsection type: {subsections[subsection_key]['type']}")
                            continue  # Skip normal processing
                        else:
                            print(f"🔧 Section title doesn't match - falling through to normal processing")
                    
                    # List of ContentFormatter objects - extract and combine
                    logger.debug(f"DEBUG: Processing ContentFormatter list for {subsection_key}, length: {len(content_data)}")
                    actual_content = self._extract_from_content_list(content_data)
                    formatting = self._extract_formatting_from_list(content_data)
                    logger.debug(f"DEBUG: Extracted content length: {len(actual_content) if actual_content else 0}")
                    
                    # Create standardized subsection structure for lists
                    subsections[subsection_key] = {
                        'title': title,
                        'content': actual_content,
                        'formatting': formatting,
                        'type': 'formatted_content'
                    }
                elif isinstance(content_data, dict):
                    # Complex structure: {"text": "...", "formatting": {...}}
                    actual_content = content_data.get('text', '')
                    formatting = content_data.get('formatting', {})
                    logger.debug(f"DEBUG: Dict content length: {len(actual_content) if actual_content else 0}")
                    
                    # Create standardized subsection structure for dicts
                    subsections[subsection_key] = {
                        'title': title,
                        'content': actual_content,
                        'formatting': formatting,
                        'type': 'formatted_content'
                    }
                else:
                    # Simple structure: just a string
                    actual_content = content_data
                    formatting = {}
                    logger.debug(f"DEBUG: String content length: {len(actual_content) if actual_content else 0}")
                    
                    # Create standardized subsection structure for strings
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
            'section_title': section_title,  # Add section_title for backward compatibility
            'section_key': section_title.lower().replace(' ', '_'),
            'subsections': subsections
        }
    
    def _format_for_document_generation(self, section_data: Dict, section_title: str) -> Dict[str, Any]:
        """
        Format section data for document generation (Word/PDF).
        
        Returns the data in the format expected by the DocumentFormatter.
        The DocumentFormatter expects sections with 'title' and 'content' structure.
        """
        logger.debug(f"Formatting section '{section_title}' for document generation")
        
        # Get the generator content from section_data
        generator_content = section_data.get('content', {})
        
        # Special handling for pathway analysis with opportunities
        if 'opportunities' in generator_content:
            logger.debug("🎯 Special handling for pathway analysis opportunities")
            opportunities_list = generator_content['opportunities']
            
            # Process opportunities while preserving structure for document generation
            formatted_opportunities = []
            
            for i, opportunity in enumerate(opportunities_list):
                if isinstance(opportunity, dict):
                    # Convert ContentFormatter objects to document-friendly format
                    formatted_opportunity = {}
                    
                    for key, value in opportunity.items():
                        if isinstance(value, dict) and 'content' in value:
                            # Extract text content but preserve title
                            content_data = value['content']
                            if isinstance(content_data, list):
                                text_content = self._extract_from_content_list(content_data)
                            elif isinstance(content_data, dict) and 'text' in content_data:
                                text_content = content_data['text']
                            elif isinstance(content_data, str):
                                text_content = content_data
                            else:
                                text_content = str(content_data)
                            
                            formatted_opportunity[key] = {
                                'title': value.get('title', key.replace('_', ' ').title()),
                                'content': text_content
                            }
                        else:
                            # Keep other fields as-is
                            formatted_opportunity[key] = value
                    
                    formatted_opportunities.append(formatted_opportunity)
                else:
                    logger.warning(f"Opportunity {i} is not a dict: {type(opportunity)}")
            
            return {
                'opportunities': formatted_opportunities
            }
        
        # Regular subsection processing for non-pathway sections
        formatted_subsections = {}
        
        for subsection_key, subsection_data in generator_content.items():
            logger.debug(f"Formatting subsection '{subsection_key}' for document generation")
            
            if isinstance(subsection_data, dict):
                # Extract title and content
                title = subsection_data.get('title', self._format_subsection_title(subsection_key))
                
                # Extract content from various formats
                if 'content' in subsection_data:
                    content_data = subsection_data['content']
                    
                    if isinstance(content_data, list):
                        # Extract text from ContentFormatter objects
                        content_text = self._extract_from_content_list(content_data)
                    elif isinstance(content_data, dict) and 'text' in content_data:
                        # ContentFormatter object
                        content_text = content_data['text']
                    elif isinstance(content_data, str):
                        # Plain string
                        content_text = content_data
                    else:
                        # Convert to string
                        content_text = str(content_data)
                else:
                    # Use the subsection_data directly if it's a string
                    if isinstance(subsection_data, str):
                        content_text = subsection_data
                        title = self._format_subsection_title(subsection_key)
                    else:
                        # Extract from the dict structure
                        content_text = str(subsection_data)
                
                formatted_subsections[subsection_key] = {
                    'title': title,
                    'content': content_text
                }
            elif isinstance(subsection_data, str):
                # Simple string subsection
                formatted_subsections[subsection_key] = {
                    'title': self._format_subsection_title(subsection_key),
                    'content': subsection_data
                }
            else:
                # Convert anything else to string
                formatted_subsections[subsection_key] = {
                    'title': self._format_subsection_title(subsection_key),
                    'content': str(subsection_data)
                }
        
        logger.debug(f"Formatted {len(formatted_subsections)} subsections for document generation")
        return formatted_subsections
    
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
                elif item.get('type') == 'structured_table' and 'headers' in item and 'rows' in item:
                    # Structured table from ContentFormatter (web format) - convert to markdown for text extraction
                    logger.debug(f"DEBUG: Item {i} is structured table with {len(item['headers'])} headers and {len(item['rows'])} rows")
                    table_text = self._convert_structured_table_to_text(item)
                    combined_text.append(table_text)
                else:
                    logger.warning(f"WARNING: Dict item {i} has no 'text' key and is not a structured table: {item}")
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
    
    def _convert_structured_table_to_text(self, table_item: dict) -> str:
        """Convert a structured table to markdown text format for legacy text processing."""
        try:
            headers = table_item.get('headers', [])
            rows = table_item.get('rows', [])
            
            if not headers or not rows:
                return "Empty table"
            
            # Create markdown table
            table_lines = []
            
            # Headers
            table_lines.append(" | ".join(headers))
            
            # Separator
            table_lines.append("|".join(["-" * len(header) for header in headers]))
            
            # Rows
            for row in rows:
                if isinstance(row, list):
                    table_lines.append(" | ".join(str(cell) for cell in row))
                else:
                    table_lines.append(str(row))
            
            return "\n".join(table_lines)
            
        except Exception as e:
            logger.warning(f"Failed to convert structured table to text: {e}")
            return f"Table conversion error: {e}"
    
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
                            
                            # Check for all structured table types
                            STRUCTURED_TABLE_TYPES = [
                                'structured_skills_table',
                                'structured_timeline_table', 
                                'structured_overview_table',
                                'structured_deployment_table',
                                'structured_strategic_table',
                                'structured_table'
                            ]
                            
                            if isinstance(content_data, dict) and content_data.get('type') in STRUCTURED_TABLE_TYPES:
                                # Keep structured data intact for frontend
                                table_type = content_data.get('type')
                                formatted_opportunity[key] = {
                                    'title': value.get('title', key.replace('_', ' ').title()),
                                    'content': content_data,  # Keep full structured data
                                    'formatting': {'content_type': table_type},
                                    'content_type': table_type
                                }
                                logger.debug(f"DEBUG: Preserved {table_type} for {key}")
                            elif isinstance(content_data, dict) and 'text' in content_data:
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
    
    def _has_no_opportunities(self, pathway_result: Dict[str, Any]) -> bool:
        """
        Check if the pathway analysis result indicates no opportunities were found.
        
        Args:
            pathway_result: Result from pathway generator
            
        Returns:
            True if no opportunities found, False otherwise
        """
        try:
            content = pathway_result.get('content', {})
            
            # Check for error subsection (indicates no results)
            if 'error' in content:
                print("🔍 Found 'error' subsection - no opportunities detected")
                return True
            
            # Check for empty opportunities list
            opportunities = content.get('opportunities', [])
            if isinstance(opportunities, list):
                has_opportunities = len(opportunities) > 0
                print(f"🔍 Found {len(opportunities)} opportunities in list")
                return not has_opportunities
            elif isinstance(opportunities, dict):
                # Handle case where opportunities is a dict with content
                opp_content = opportunities.get('content', [])
                if isinstance(opp_content, list):
                    has_opportunities = len(opp_content) > 0
                    print(f"🔍 Found {len(opp_content)} opportunities in dict content")
                    return not has_opportunities
            
            # Default: assume opportunities exist if we can't clearly determine otherwise
            print("🔍 Could not clearly determine opportunity count - assuming opportunities exist")
            return False
            
        except Exception as e:
            logger.warning(f"Error checking for opportunities: {e}")
            return False
    
    def _create_no_results_response(self, job_from: str, similarity_min: int, similarity_max: int, output_mode: str) -> Dict[str, Any]:
        """
        Create a simplified response when no career opportunities are found.
        
        Args:
            job_from: Source job ID
            similarity_min: Minimum similarity percentage
            similarity_max: Maximum similarity percentage
            output_mode: 'web' or 'document'
            
        Returns:
            Simplified response with no-results message
        """
        # Create a single, clean "no results found" section
        no_results_content = {
            'no_results_found': {
                'title': 'No Career Pathways Found',
                'content': f"No career opportunities were found within the {similarity_min}%-{similarity_max}% similarity range.\n\n" +
                          "This could mean:\n" +
                          "• The similarity range is too narrow\n" +
                          "• No suitable career transitions exist within this range\n" +
                          "• Try adjusting the similarity range to explore more options\n\n" +
                          "**Suggestion:** Consider expanding your similarity range (e.g., 0%-60%) to discover more career opportunities.",
                'formatting': {'content_type': 'informational_message'},
                'type': 'formatted_content'
            }
        }
        
        sections = {
            'no_results': {
                'title': 'Career Transition Analysis Results',
                'section_title': 'Career Transition Analysis Results',
                'section_key': 'no_results',
                'subsections': no_results_content
            }
        }
        
        # Create metadata
        metadata = {
            'job_from': job_from,
            'similarity_range': f"{similarity_min}%-{similarity_max}%",
            'analysis_type': 'no_results_found',
            'timestamp': str(datetime.now()),
            'status': 'no_opportunities_found'
        }
        
        print(f"✅ Created no-results response for job {job_from} with range {similarity_min}%-{similarity_max}%")
        
        return {
            'success': True,
            'sections': sections,
            'metadata': metadata,
            'output_mode': output_mode,
            'no_results': True  # Flag to help frontend identify this response type
        }