"""
Career Pathways Routes Blueprint
===============================

Career pathway visualization and analysis routes for the SSE webapp.
Extracted from app.py as part of Phase 2b webapp modularization.

Routes:
- /career-pathways: Career pathway exploration interface
"""

from flask import Blueprint, render_template, g

# Create blueprint
career_pathways_bp = Blueprint('career_pathways', __name__)

def get_db():
    """Get database connection from Flask g object."""
    return g.db

def get_sample_jobs(limit=None):
    """Get sample jobs for display."""
    from ..sql import queries
    
    try:
        db = get_db()
        
        if limit is None:
            limit = 10  # Default limit for career pathways
        
        # Get sample jobs
        jobs_query = queries.get('jobs', 'get_sample_jobs')
        jobs = db.execute(jobs_query, (limit,)).fetchall()
        
        return [dict(job) for job in jobs]
        
    except Exception as e:
        print(f"Error getting sample jobs: {e}")
        return []

@career_pathways_bp.route('/career-pathways')
def career_pathways():
    """Career pathway exploration interface."""
    from ..sql import queries
    
    try:
        db = get_db()
        
        # Get job families for starting point selection
        families_query = queries.get('jobs', 'get_job_families')
        families = db.execute(families_query).fetchall()
        
        sample_jobs = get_sample_jobs(10)
        
        return render_template('career_pathways.html', 
                             job_families=families,
                             jobs=sample_jobs)
    except Exception as e:
        print(f"Error loading career pathways: {e}")
        sample_jobs = get_sample_jobs(10)
        return render_template('career_pathways.html', 
                             job_families=[],
                             jobs=sample_jobs) 