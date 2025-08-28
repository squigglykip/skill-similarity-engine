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
    """Generate a downloadable document using simplified HTML-to-PDF/Word pipeline."""
    try:
        print("Generating document using simplified HTML-to-PDF/Word pipeline...")
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        output_format = data.get('output_format', 'pdf')
        job_from = data.get('job_from', 'Unknown')
        
        print(f"Document generation request received for {job_from} (format: {output_format})")
        
        # Import the simplified document service
        from ..career_analysis.services.simplified_document_service import SimplifiedDocumentService
        
        db = get_db()
        
        # Generate document using simplified service
        document_service = SimplifiedDocumentService(db)
        success, result = document_service.generate_document(data, output_format)
        
        if success:
            # Return the document as a file download
            from flask import make_response
            
            response = make_response(result['content'])
            response.headers['Content-Type'] = result['content_type']
            response.headers['Content-Disposition'] = f'attachment; filename="{result["filename"]}"'
            response.headers['Content-Length'] = len(result['content'])
            
            print(f"Successfully generated {result['format']} document: {result['filename']}")
            return response
        else:
            logger.error(f"Document generation failed: {result.get('error', 'Unknown error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Document generation failed'),
                'details': result.get('details', '')
            }), 500
            
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
        if not jobs_query:
            raise ValueError("Query 'get_all_jobs_for_selection' not found")
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


@career_analysis_bp.route('/career-analysis-html-to-document', methods=['POST'])
def generate_document_from_html():
    """
    Generate Word/PDF document from frontend HTML capture.
    
    This endpoint takes the rendered HTML from the frontend preview
    and converts it directly to Word/PDF format, ensuring 100% consistency
    between what users see and what they download.
    
    Expected payload:
    {
        "html": "<div>...rendered preview content...</div>",
        "format": "pdf" | "word",
        "metadata": {
            "job_from": "R0041.4",
            "analysis_mode": "top_matches",
            "generated_date": "2024-01-15"
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        html_content = data.get('html', '')
        output_format = data.get('format', 'pdf')
        metadata = data.get('metadata', {})
        
        if not html_content:
            return jsonify({'success': False, 'error': 'No HTML content provided'}), 400
        
        print(f"HTML-to-document request: format={output_format}, metadata={metadata}")
        
        # Import the HTML document service
        from ..career_analysis.services.html_document_service import HTMLDocumentService
        
        # Generate document using HTML capture
        html_document_service = HTMLDocumentService()
        success, result = html_document_service.generate_document_from_html(
            html_content, output_format, metadata
        )
        
        if success:
            # Return the document as a file download
            from flask import make_response
            
            response = make_response(result['content'])
            response.headers['Content-Type'] = result['content_type']
            response.headers['Content-Disposition'] = f'attachment; filename="{result["filename"]}"'
            
            print(f"Successfully generated {result['format']} document: {result['filename']}")
            return response
        else:
            print(f"Document generation failed: {result.get('error', 'Unknown error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Document generation failed')
            }), 500
            
    except Exception as e:
        logger.error(f"Error in HTML-to-document generation: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'HTML document generation failed: {str(e)}'
        }), 500 