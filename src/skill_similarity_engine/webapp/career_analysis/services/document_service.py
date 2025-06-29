"""
Document Service

Service for generating downloadable Word/PDF documents using the existing
DocumentFormatter and maintaining compatibility with the current document generation.
"""

from typing import Dict, List, Optional, Any
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
    from formatter import DocumentFormatter
except ImportError:
    try:
        from ..formatter import DocumentFormatter
    except ImportError:
        # Final fallback - create a simple formatter
        class DocumentFormatter:
            def format_document(self, content, output_format, analysis_data):
                return {
                    'format': output_format,
                    'filename': f'career_analysis.{output_format}',
                    'content': b'Error: DocumentFormatter not available',
                    'status': 'error',
                    'message': 'DocumentFormatter import failed'
                }

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
        self.formatter = DocumentFormatter()
        
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
                **parameters
            )
            
            if not result['success']:
                return result
            
            # Format the document using existing DocumentFormatter
            document_result = self.formatter.format_document(
                content=result['sections'],
                output_format=output_format,
                analysis_data=result['metadata']
            )
            
            logger.info(f"Successfully generated {output_format} document")
            
            return {
                'success': True,
                'document': document_result,
                'metadata': result['metadata'],
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