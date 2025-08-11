"""
Flask Integration for Career Analysis Services

This module provides the Flask endpoint implementations that use the new service layer
instead of subprocess calls to the CLI.
"""

from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)

def create_career_analysis_preview_endpoint(app, get_db_func):
    """
    Create the career analysis preview endpoint that uses the service layer.
    
    Args:
        app: Flask application instance
        get_db_func: Function to get database connection
    """
    
    @app.route('/api/career-analysis-preview', methods=['POST'])
    def api_career_analysis_preview():
        """Generate a preview using the new service layer architecture."""
        try:
            logger.info("Starting career analysis preview using service layer...")
            
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
            
            logger.info(f"Processing request for job: {data.get('job_from', 'Unknown')}")
            
            # Import services
            from .preview_service import PreviewService
            from .validation_service import ValidationService
            
            db = get_db_func()
            
            # Validate form data first
            validation_service = ValidationService(db)
            is_valid, cleaned_data, errors = validation_service.validate_form_data(data)
            
            if not is_valid:
                logger.warning(f"Validation failed: {errors}")
                return jsonify({
                    'success': False,
                    'error': 'Validation failed',
                    'validation_errors': errors
                }), 400
            
            # Generate preview using service layer
            preview_service = PreviewService(db)
            result = preview_service.generate_preview(cleaned_data)
            
            if result['success']:
                logger.info(f"Successfully generated preview with {len(result.get('content', {}))} sections")
                return jsonify(result)
            else:
                logger.error(f"Preview generation failed: {result.get('error', 'Unknown error')}")
                return jsonify(result), 500
                
        except Exception as e:
            logger.error(f"Unexpected error in preview endpoint: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }), 500

def create_career_analysis_document_endpoint(app, get_db_func):
    """
    Create the career analysis document generation endpoint.
    
    Args:
        app: Flask application instance
        get_db_func: Function to get database connection
    """
    
    @app.route('/api/career-analysis-document', methods=['POST'])
    def api_career_analysis_document():
        """Generate a downloadable document using the service layer."""
        try:
            logger.info("Starting document generation using service layer...")
            
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
            
            output_format = data.get('output_format', 'word')
            logger.info(f"Processing {output_format} document request for job: {data.get('job_from', 'Unknown')}")
            
            # TODO: Implement simplified HTML-to-Word pipeline in Phase 3
            logger.info("Document generation temporarily disabled during V2 migration...")
            
            result = {
                'success': False,
                'error': 'Document generation temporarily disabled during V2 migration. Will be restored with simplified HTML-to-Word pipeline.',
                'status': 'coming_soon',
                'planned_implementation': 'Phase 3: Simplified Document Generation',
                'alternative': 'Use HTML preview for now - document export will return soon!'
            }
            
            # Return not implemented status during migration
            return jsonify(result), 501  # Not Implemented
                
        except Exception as e:
            logger.error(f"Unexpected error in document endpoint: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }), 500 