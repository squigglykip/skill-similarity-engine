"""
Career Analysis API Module for NAB Skills Intelligence Platform
==============================================================

This module contains career analysis generation endpoints:
- /api/career-analysis-preview (POST)
- /api/career-analysis-document (POST)
- /api/career-analysis-jobs (GET)

These endpoints provide career analysis generation capabilities using the service layer
architecture instead of subprocess calls.
"""

from flask import Blueprint, request, jsonify, g
from ..sql import queries
import logging

logger = logging.getLogger(__name__)

# Create blueprint for career analysis API
career_analysis_bp = Blueprint('career_analysis_api', __name__, url_prefix='/api')

def get_db():
    """Get database connection from Flask g object."""
    from flask import current_app
    import sqlite3
    if 'db' not in g:
        g.db = sqlite3.connect(str(current_app.config['DATABASE_PATH']))
        g.db.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return g.db

@career_analysis_bp.route('/career-analysis-preview', methods=['POST'])
def api_career_analysis_preview():
    """Generate a preview using the new service layer architecture."""
    try:
        print("Starting career analysis preview using service layer...")
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        print(f"Processing request for job: {data.get('job_from', 'Unknown')}")
        
        # Import services
        from ..career_analysis.services.preview_service import PreviewService
        from ..career_analysis.services.validation_service import ValidationService
        
        db = get_db()
        
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
            print(f"Successfully generated preview with {len(result.get('content', {}))} sections")
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

@career_analysis_bp.route('/career-analysis-document', methods=['POST'])
def api_career_analysis_document():
    """Generate a downloadable document using the service layer."""
    try:
        print("Starting document generation using service layer...")
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        output_format = data.get('output_format', 'word')
        print(f"Processing {output_format} document request for job: {data.get('job_from', 'Unknown')}")
        
        # Import services
        from ..career_analysis.services.document_service import DocumentService
        from ..career_analysis.services.validation_service import ValidationService
        
        db = get_db()
        
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
        
        # Generate document using service layer
        document_service = DocumentService(db)
        result = document_service.generate_document(cleaned_data, output_format)
        
        if result['success']:
            print(f"Successfully generated {output_format} document")
            
            # Handle document content for JSON response
            import base64
            import io
            
            def clean_for_json(obj):
                """Recursively clean an object to make it JSON-serializable."""
                if isinstance(obj, bytes):
                    return base64.b64encode(obj).decode('utf-8')
                elif isinstance(obj, io.BytesIO):
                    return "<BytesIO object (removed for JSON serialization)>"
                elif isinstance(obj, dict):
                    return {k: clean_for_json(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [clean_for_json(item) for item in obj]
                else:
                    return obj
            
            # Clean the entire result for JSON serialization
            clean_result = clean_for_json(result)
            
            return jsonify(clean_result)
        else:
            logger.error(f"Document generation failed: {result.get('error', 'Unknown error')}")
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in document endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@career_analysis_bp.route('/career-analysis-jobs')
def api_career_analysis_jobs():
    """API endpoint to get jobs for career analysis dropdowns."""
    try:
        db = get_db()
        
        # Get all jobs for career analysis selection
        jobs_query = queries.get('jobs', 'get_all_jobs_for_selection')
        jobs = db.execute(jobs_query).fetchall()
        
        # Format for dropdown consumption
        formatted_jobs = []
        for job in jobs:
            formatted_jobs.append({
                'id': job['JobProfileID'],
                'title': job['JobProfile'],
                'function': job['JobFunction'],
                'display_name': f"{job['JobProfile']} ({job['JobProfileID']})"
            })
        
        return jsonify({
            'success': True,
            'jobs': formatted_jobs,
            'total_count': len(formatted_jobs)
        })
        
    except Exception as e:
        logger.error(f"Error fetching jobs for career analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'jobs': []
        }), 500 