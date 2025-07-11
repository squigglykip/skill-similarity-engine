"""
Webapp Route Blueprints Module
=============================

Domain-specific route handlers for the SSE webapp.
Part of Phase 2b webapp modularization - Route Handler Extraction.

Blueprints:
- main: Homepage, components, basic navigation
- job_explorer: Job search and exploration features  
- career_analysis: Career analysis generation workflows
- career_pathways: Career pathway visualization and analysis

Integration: These blueprints work with the API module (Phase 2a) 
to provide complete webapp functionality through modular architecture.
"""

from flask import Blueprint

def register_route_blueprints(app):
    """Register all route blueprints with the Flask app."""
    
    # Import blueprints
    from .main import main_bp
    from .job_explorer import job_explorer_bp
    from .career_analysis import career_analysis_bp  
    from .career_pathways import career_pathways_bp
    
    # Register with URL prefixes for organization
    app.register_blueprint(main_bp)  # No prefix - root level routes
    app.register_blueprint(job_explorer_bp)  # No prefix - top-level pages
    app.register_blueprint(career_analysis_bp)  # No prefix - top-level pages
    app.register_blueprint(career_pathways_bp)  # No prefix - top-level pages
    
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[OK] Route blueprints registered at {timestamp}: main, job_explorer, career_analysis, career_pathways") 