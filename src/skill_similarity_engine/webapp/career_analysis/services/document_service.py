"""
Document Service

Service for generating downloadable Word/PDF documents using the existing
DocumentFormatter and maintaining compatibility with the current document generation.
"""

from typing import Dict, List, Optional, Any, Union
import logging
import sys
from pathlib import Path

# Import the services we need
try:
    # Try to import from the same package first
    from career_analysis_service import CareerAnalysisService
except ImportError:
    # Fallback to relative import
    from .career_analysis_service import CareerAnalysisService

# Import the DocumentFormatter
try:
    # Add the parent directory to import the formatter
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from skill_similarity_engine.webapp.career_analysis.formatter import DocumentFormatter as NABDocumentFormatter
except ImportError:
    try:
        from ..formatter import DocumentFormatter as NABDocumentFormatter
    except ImportError:
        # Final fallback - create a simple formatter
        class NABDocumentFormatter:
            def format_document(self, content, output_format, analysis_data):
                return {
                    'format': output_format,
                    'filename': f'career_analysis.{output_format}',
                    'content': b'Error: DocumentFormatter not available',
                    'status': 'error',
                    'message': 'DocumentFormatter import failed'
                }

# Import configuration system
try:
    from .config.settings import CareerAnalysisSettings
    from .config.document_styles import DocumentStyles
    SETTINGS_AVAILABLE = True
except ImportError:
    try:
        from config.settings import CareerAnalysisSettings  
        from config.document_styles import DocumentStyles
        SETTINGS_AVAILABLE = True
    except ImportError:
        CareerAnalysisSettings = None
        DocumentStyles = None
        SETTINGS_AVAILABLE = False

logger = logging.getLogger(__name__)

class DocumentService:
    """
    Service for generating downloadable documents.
    
    This service handles Word document generation for download while maintaining
    compatibility with the existing DocumentFormatter system.
    """
    
    def __init__(self, db_connection):
        """Initialize the document service with database connection."""
        self.db = db_connection
        self.analysis_service = CareerAnalysisService(db_connection)
        self.formatter = NABDocumentFormatter()
        
        logger.info("DocumentService initialized")
    
    def generate_document(self, form_data: Dict, output_format: str = 'word') -> Dict[str, Any]:
        """
        Generate a downloadable document (Word/PDF).
        
        Args:
            form_data: Form data from the frontend
            output_format: 'word', 'pdf', etc.
            
        Returns:
            Dict with document data and metadata
        """
        try:
            logger.info(f"Generating {output_format} document for form data: {form_data}")
            
            # Extract parameters
            parameters = self._extract_parameters(form_data)
            
            # Validate required parameters
            if not parameters['job_from']:
                return {
                    'success': False,
                    'error': 'job_from is required',
                    'document': None
                }
            
            # Generate analysis using the main service in document mode
            result = self.analysis_service.generate_analysis(
                job_from=parameters['job_from'],
                analysis_mode=parameters['analysis_mode'],
                output_mode='document',  # Document mode for Word generation
                job_to=parameters.get('job_to'),
                similarity_min=parameters['similarity_min'],
                similarity_max=parameters['similarity_max'],
                top_n=parameters['top_n'],
                include_organisational_deployment=parameters['include_organisational_deployment'],
                tie_breaking_options=parameters['tie_breaking_options']
            )
            
            if not result['success']:
                return result
            
            # TASK 1 & 2: Build rich analysis data with dynamic section titles (CLI approach)
            rich_analysis_data = self._build_rich_analysis_data(result, parameters)
            
            # Generate enhanced filename using business-friendly format
            job_name = rich_analysis_data.get('source_job_logical_display_name', 'Professional Role')
            job_id = parameters.get('job_from', 'Unknown')
            analysis_mode = parameters.get('analysis_mode', 'top_matches')
            target_job = parameters.get('job_to')
            enhanced_filename = self._generate_filename(job_name, output_format, analysis_mode, target_job, job_id)
            rich_analysis_data['enhanced_filename'] = enhanced_filename
            
            # Format the document using existing DocumentFormatter with enriched metadata
            document_result = self.formatter.format_document(
                content=result['sections'],
                output_format=output_format,
                analysis_data=rich_analysis_data
            )
            
            logger.info(f"Successfully generated {output_format} document")
            
            return {
                'success': True,
                'document': document_result,
                'metadata': rich_analysis_data,
                'output_format': output_format
            }
            
        except Exception as e:
            logger.error(f"Error generating document: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'document': None
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
            'include_organisational_deployment': form_data.get('include_deployment', True),  # Usually True for documents
            'tie_breaking_options': form_data.get('tie_breaking_options', {}),
        }
    
    def _extract_dynamic_section_titles(self, sections: Dict) -> List[tuple]:
        """
        Extract dynamic section titles from generator results (CLI approach).
        
        Args:
            sections: Dict of section results from generators
            
        Returns:
            List of (section_name, section_title) tuples
        """
        section_titles = []
        
        # Static title fallbacks (matching CLI logic)
        static_titles = {
            'executive_summary': 'Executive Summary',
            'current_role_context': 'Current Role Context',
            'pathway_analysis': 'Pathway Analysis: Top 3 Strategic Opportunities',
            'strategic_recommendations': 'Strategic Recommendations',
            'conclusion': 'Conclusion'
        }
        
        logger.debug("🔍 Extracting section titles from generator results...")
        
        for section_name in ['executive_summary', 'current_role_context', 'pathway_analysis', 'strategic_recommendations', 'conclusion']:
            if section_name in sections:
                # Extract dynamic title from generator result, fallback to static title
                generator_title = sections[section_name].get('section_title', '')
                logger.debug(f"   📋 {section_name}: generator_title = '{generator_title}'")
                
                if generator_title:
                    # Clean up any newline characters from section title
                    clean_title = generator_title.strip()
                    section_titles.append((section_name, clean_title))
                    logger.debug(f"      ✅ Using dynamic title: '{generator_title}'")
                else:
                    # Fallback to static titles for sections that don't generate dynamic titles
                    section_titles.append((section_name, static_titles[section_name]))
                    logger.debug(f"      ⚠️ Using fallback title: '{static_titles[section_name]}'")
        
        logger.debug(f"🔍 Final section_titles = {section_titles}")
        return section_titles
    
    def _build_rich_analysis_data(self, result: Dict, parameters: Dict) -> Dict[str, Any]:
        """
        Build comprehensive analysis_data structure matching CLI approach.
        
        Args:
            result: Analysis result from service
            parameters: Form parameters
            
        Returns:
            Rich analysis data dict with CLI-compatible structure
        """
        logger.debug("🏗️ Building rich analysis data (CLI approach)...")
        
        # Extract template variables from executive summary (like CLI does)
        exec_variables = {}
        if 'executive_summary' in result['sections']:
            exec_variables = result['sections']['executive_summary'].get('template_variables', {})
        
        # FIX 1: Get real job name directly from database instead of relying on template variables
        real_job_name = self._get_job_name_from_database(parameters['job_from'])
        
        # Extract dynamic section titles
        section_titles = self._extract_dynamic_section_titles(result['sections'])
        
        # Build rich analysis data structure (matching CLI logic)
        rich_data = {
            # Core job information - NOW USING REAL DATABASE VALUES
            'source_job_id': parameters['job_from'],
            'source_job_logical_display_name': real_job_name,  # FIX 1: Use real job name
            'source_job_function': exec_variables.get('source_job_function', 'Professional Services'),
            
            # Analysis metadata
            'analysis_mode': parameters['analysis_mode'],
            'similarity_range': f"{parameters['similarity_min']}%-{parameters['similarity_max']}%",
            'summary': f'Career pathway analysis for {real_job_name}',  # FIX 1: Use real job name
            
            # Key metrics from executive summary
            'avg_similarity': exec_variables.get('max_similarity', 0) / 100 if exec_variables.get('max_similarity') else 0,
            'pathway_count': exec_variables.get('pathway_count', 0),
            'confidence_level': exec_variables.get('confidence_level', 'High'),
            
            # Dynamic section titles (key CLI feature)
            'section_titles': section_titles,
            
            # Additional target job info for specific mode
            'target_job': parameters.get('job_to'),
            'top_n': parameters.get('top_n', 3),
        }
        
        # Merge with existing metadata from service
        if 'metadata' in result:
            rich_data.update(result['metadata'])
        
        logger.debug(f"✅ Rich analysis data built with real job name: {real_job_name}")
        return rich_data 
    
    def _get_job_name_from_database(self, job_id: str) -> str:
        """
        Get the standardized job display name using JobDisplayManager.
        
        Args:
            job_id: JobProfileID to look up (e.g., 'R0102.3')
            
        Returns:
            Standardized job display name (e.g., 'Risk Analyst (Group 2)')
        """
        try:
            # FIX 1 ENHANCED: Use JobDisplayManager for consistent job name formatting
            from skill_similarity_engine.utils.display import JobDisplayManager, DisplayFormat
            
            display_manager = JobDisplayManager(self.db)
            
            # Use search format for documents: "Job - ProfileTitleSuffix (ManagementLevel)"
            # This gives us the most descriptive format for document titles
            standardized_name = display_manager.get_display_name(job_id, DisplayFormat.SEARCH)
            
            logger.debug(f"🎯 Standardized job name for {job_id}: {standardized_name}")
            return standardized_name
                
        except Exception as e:
            logger.error(f"❌ Error getting standardized job name for {job_id}: {e}")
            
            # Fallback to direct database query if JobDisplayManager fails
            try:
                query = """
                SELECT JobProfile, JobFunction, ManagementLevel 
                FROM jobs 
                WHERE JobProfileID = ?
                """
                
                result = self.db.execute(query, (job_id,)).fetchone()
                
                if result:
                    job_profile = result['JobProfile']
                    logger.debug(f"🎯 Fallback job name for {job_id}: {job_profile}")
                    return job_profile
                else:
                    logger.warning(f"⚠️ Job ID {job_id} not found in database, using final fallback")
                    return f"Professional Role ({job_id})"
                    
            except Exception as fallback_error:
                logger.error(f"❌ Fallback query also failed for {job_id}: {fallback_error}")
                return f"Professional Role ({job_id})"
    
    def _generate_filename(self, job_name: str, output_format: str, analysis_mode: str = 'top_matches', target_job: str = None, job_id: str = None) -> str:
        """
        Generate business-friendly filename for executive audience.
        
        Args:
            job_name: Name of the job being analyzed
            output_format: Output format (word, pdf, etc.)
            analysis_mode: Type of analysis ('top_matches', 'specific')
            target_job: Target job ID if specific analysis
            
        Returns:
            Human-readable filename string for business leaders
        """
        try:
            from datetime import datetime
            
            # Clean job name for business readability
            clean_job = job_name.replace(" - ", " ").replace("(", "").replace(")", "").strip()
            
            # Create analysis type description for business audience
            if analysis_mode == 'specific' and target_job:
                if ',' in str(target_job):
                    # Multiple targets
                    target_count = len([j.strip() for j in str(target_job).split(',')])
                    analysis_desc = f"Transition to {target_count} Roles"
                else:
                    # Single target - get readable name
                    try:
                        target_name = self._get_job_name_from_database(target_job)
                        clean_target = target_name.replace(" - ", " ").replace("(", "").replace(")", "").strip()
                        analysis_desc = f"Transition to {clean_target}"
                    except Exception:
                        analysis_desc = "Career Transition"
            else:
                # Top matches analysis
                analysis_desc = "Career Opportunities"
            
            # Generate date in business format
            date_str = datetime.now().strftime('%B %Y')  # e.g., "June 2025"
            
            # Create business-friendly filename with JobProfileID prefix
            # Example: "R0102.3 Data Scientist Career Opportunities - June 2025.docx"
            if len(clean_job) > 30:  # Truncate very long job names
                clean_job = clean_job[:30].strip()
            
            # Use the provided JobProfileID or fallback to "Unknown"
            job_profile_id = job_id if job_id else "Unknown"
            
            # Map output formats to file extensions for business audience
            format_extensions = {
                'word': 'docx',
                'pdf': 'pdf', 
                'powerpoint': 'pptx',
                'html': 'html',
                'markdown': 'md'
            }
            file_extension = format_extensions.get(output_format, output_format)
            
            filename = f"{job_profile_id} {clean_job} {analysis_desc} - {date_str}.{file_extension}"
            
            # Replace any remaining problematic characters for file systems
            filename = filename.replace("/", " or ").replace("\\", " or ").replace(":", " -")
            
            logger.debug(f"📁 Generated business-friendly filename: {filename}")
            return filename
            
        except Exception as e:
            logger.warning(f"⚠️ Business filename generation failed, using fallback: {e}")
            # Fallback to technical filename
            try:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                clean_name = job_name.replace(" ", "_").replace("(", "").replace(")", "")
                return f'career_analysis_{clean_name}_{timestamp}.{output_format}'
            except Exception:
                return f'career_analysis.{output_format}' 