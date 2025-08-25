"""
API Module for NAB Skills Intelligence Platform
==============================================

This module contains all API endpoints organized by domain:
- jobs_api: Job-related endpoints (/api/job-details, /api/job-similarities, etc.)
- search_api: Search and autocomplete endpoints
- similarity_api: Skills analysis and similarity endpoints  
- pathways_api: Career pathway and visualization endpoints
- export_api: CSV export endpoints
- metadata_api: Database health and organizational data
- career_analysis_api: Career analysis generation endpoints

Usage:
    from .jobs_api import jobs_bp
    from .search_api import search_bp
    
    app.register_blueprint(jobs_bp)
    app.register_blueprint(search_bp)
"""

from flask import Blueprint

# Import all API blueprints
from .jobs_api import jobs_bp
from .search_api import search_bp
from .similarity_api import similarity_bp
from .pathways_api import pathways_bp
from .export_api import export_bp
from .metadata_api import metadata_bp
from .career_analysis_api import career_analysis_bp


# Import V2 Analytics API blueprints
from .job_intelligence_api import job_intelligence_bp
from .skills_intelligence_api import skills_intelligence_bp
from .movement_analytics_api import movement_analytics_bp
from .v2_dashboard_api import v2_dashboard_bp

# List of all blueprints for easy registration
API_BLUEPRINTS = [
    jobs_bp,
    search_bp,
    similarity_bp,
    pathways_bp,
    export_bp,
    metadata_bp,
    career_analysis_bp,

    # V2 Analytics APIs
    job_intelligence_bp,
    skills_intelligence_bp,
    movement_analytics_bp,
    v2_dashboard_bp
]

def register_api_blueprints(app):
    """Register all API blueprints with the Flask app."""
    for blueprint in API_BLUEPRINTS:
        app.register_blueprint(blueprint)

__version__ = "2.0.0"
__all__ = ["API_BLUEPRINTS", "register_api_blueprints", "jobs_bp", "search_bp", 
           "similarity_bp", "pathways_bp", "export_bp", "metadata_bp", "career_analysis_bp",
           "job_intelligence_bp", "skills_intelligence_bp", "movement_analytics_bp", "v2_dashboard_bp"] 