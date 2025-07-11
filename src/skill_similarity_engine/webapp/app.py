"""
Flask Application for NAB Skills Intelligence Platform
======================================================

Modern Flask application using organised SQL queries and proper database schema.
Includes D3.js visualizations, career pathway analysis, and skills intelligence.

Features:
- Component library showcase with D3.js tree visualization
- Job search and similarity analysis
- Career pathway exploration with skills gap analysis
- Organised SQL query structure for maintainability
- NAB-style design system implementation
"""

import sqlite3
import os
import csv
import io
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, g, redirect, url_for, Response, make_response
import sys
import tempfile

# Import webapp configuration manager for externalized settings
from ..config.webapp_config_manager import get_webapp_config_manager
from .config import WebappConfig

# Import JobDisplayManager for standardised job display names
try:
    from ..utils.display import JobDisplayManager, DisplayFormat
    DISPLAY_MANAGER_AVAILABLE = True
except ImportError:
    print("⚠️ JobDisplayManager not available - using fallback job titles")
    DISPLAY_MANAGER_AVAILABLE = False

def create_app(config=None):
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Initialize webapp configuration following PTH patterns
    webapp_config_override = config.get('webapp_config', {}) if config else {}
    webapp_config = WebappConfig(webapp_config_override)
    
    # Apply Flask configuration from webapp config
    flask_config = webapp_config.get_flask_config()
    app.config.update(flask_config)
    
    # Apply any additional config overrides
    if config:
        app.config.update(config)
    
    # Get legacy webapp configuration manager for backward compatibility
    legacy_webapp_config = get_webapp_config_manager()
    
    def get_db():
        """Get database connection."""
        if 'db' not in g:
            g.db = sqlite3.connect(str(app.config['DATABASE_PATH']))
            g.db.row_factory = sqlite3.Row  # Enable dict-like access to rows
        return g.db

    def close_db(e=None):
        """Close database connection."""
        db = g.pop('db', None)
        if db is not None:
            db.close()

    @app.teardown_appcontext
    def close_db_handler(error):
        close_db()

    # Initialize services for modular functionality
    from .services import DatabaseService, JobService
    
    def get_display_manager():
        """Get JobDisplayManager instance for consistent job naming."""
        if DISPLAY_MANAGER_AVAILABLE:
            db = get_db()
            return JobDisplayManager(db)
        return None
    
    # Create service instances with proper dependency injection
    @app.before_request
    def setup_services():
        """Setup service instances for each request."""
        if not hasattr(g, 'database_service'):
            display_manager = get_display_manager()
            g.database_service = DatabaseService(
                db_connection=None,  # Uses Flask g context
                webapp_config=webapp_config,
                display_manager=display_manager
            )
            g.job_service = JobService(
                display_manager=display_manager,
                webapp_config=webapp_config
            )
    
    # Legacy helper functions that delegate to services (for backward compatibility)
    def add_display_names_to_job(job_data, display_manager=None):
        """Add standardised display names to job data."""
        return g.job_service.add_display_names_to_job(job_data, display_manager)

    def get_sample_jobs(limit=None):
        """Get sample jobs for testing using organised SQL with enhanced display names."""
        return g.database_service.get_sample_jobs(limit)

    def search_jobs(query, limit=None):
        """Search jobs by name using organised SQL."""
        return g.database_service.search_jobs(query, limit)

    def get_job_similarities(job_id, limit=10):
        """Get similar jobs using organised SQL."""
        return g.database_service.get_job_similarities(job_id, limit)

    def get_job_similarities_with_threshold(job_id, min_similarity, limit):
        """Get similar jobs using organised SQL with a specified similarity threshold."""
        return g.database_service.get_job_similarities_with_threshold(job_id, min_similarity, limit)

    # Register API blueprints for modular endpoint management
    from .api import register_api_blueprints
    register_api_blueprints(app)
    
    # Register route blueprints for modular page handlers  
    from .blueprints import register_route_blueprints
    register_route_blueprints(app)

    # Remaining Routes (Legacy - to be extracted in future phases)
    # NOTE: Main routes (/, /components, /job-search, /similarity-results, /career-pathways) 
    # moved to blueprints/ module as part of Phase 2b modularization

    # API endpoints for AJAX functionality
    # API endpoint /api/search-jobs moved to api/search_api.py

    # API endpoint /api/job-details/<job_id> moved to api/jobs_api.py

    # API endpoint /api/job-workforce/<job_id> moved to api/jobs_api.py

    # API endpoint /api/job-similarities/<job_id> moved to api/jobs_api.py

    # API endpoint /api/career-pathways-distribution/<job_id> moved to api/pathways_api.py

    # API endpoint /api/career-pathway/<start_job_id> moved to api/pathways_api.py

    # API endpoint /api/skills-gap/<source_job_id>/<target_job_id> moved to api/similarity_api.py

    # API endpoint /api/d3-tree-data moved to api/pathways_api.py

    # API endpoint /api/search-all-jobs moved to api/search_api.py

    # API endpoint /api/d3-tree-filtered moved to api/pathways_api.py

    # API endpoints /api/jobs-in-function/<function> and /api/job-functions moved to api/jobs_api.py

    # API endpoint /api/database-health moved to api/metadata_api.py

    # API endpoint /api/pathway-visualization-data moved to api/pathways_api.py

    # API endpoint /api/skills-analysis/<from_job_id>/<to_job_id> moved to api/similarity_api.py

    # API endpoint /api/workforce-analysis/<job_ids> moved to api/jobs_api.py

    # API endpoint /api/organizational-data moved to api/metadata_api.py

    # API endpoint /api/export/career-tree/<job_ids> moved to api/export_api.py

    # API endpoint /api/export/skills-analysis/<from_job_id>/<to_job_id> moved to api/export_api.py

    # API endpoint /api/export/workforce-analysis/<job_ids> moved to api/export_api.py

    # Career Transition Analysis Generator Routes
    # NOTE: /career-analysis route moved to blueprints/career_analysis.py as part of Phase 2b modularization
    # API endpoints /api/career-analysis-preview, /api/career-analysis-document, /api/career-analysis-jobs moved to api/career_analysis_api.py





    # Legacy career analysis helper functions moved to career_analysis/content/ modules
    # These are now available through ContentThresholds and ContentPersonalizer classes

    return app

if __name__ == '__main__':
    # Development server for direct running
    app = create_app()
    
    # Validate webapp configuration (this will be available after we fix the imports)
    # validation_results = webapp_config.validate_configuration()
    # if not validation_results['valid']:
    #     print("Configuration validation failed:")
    #     for error in validation_results['errors']:
    #         print(f"   ERROR: {error}")
    #     print("   Please fix configuration issues before starting the server.")
    #     exit(1)
    
    # Check if database exists
    if not app.config['DATABASE_PATH'].exists():
        print(f"âš ï¸  Database not found at: {app.config['DATABASE_PATH']}")
        print("   Run the CLI to generate business context database first.")
        exit(1)
    
    print(f"âœ… Database found at: {app.config['DATABASE_PATH']}")
    print("ðŸš€ Starting Flask development server...")
    print("   Available routes:")
    print("   - http://localhost:5000/ (Homepage)")
    print("   - http://localhost:5000/components (Component Library)")
    print("   - http://localhost:5000/job-search (Job Search)")
    print("   - http://localhost:5000/similarity-results (Similarity Results)")
    print("   - http://localhost:5000/career-pathways (Career Pathways)")
    
    app.run(debug=True, port=5000) 
