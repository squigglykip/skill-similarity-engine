"""
Career Analysis Routes Blueprint
===============================

Career analysis generation and document creation routes for the SSE webapp.
Extracted from app.py as part of Phase 2b webapp modularization.

Routes:
- /career-analysis: Career analysis generation interface
- API routes moved to api/ module in Phase 2a
"""

from flask import Blueprint, render_template, g

# Create blueprint
career_analysis_bp = Blueprint('career_analysis', __name__)

def get_db():
    """Get database connection from Flask g object."""
    return g.db

def get_sample_jobs(limit=None):
    """Get sample jobs for display."""
    from ..sql import queries
    
    try:
        db = get_db()
        
        if limit is None:
            limit = 20  # Default limit for career analysis
        
        # Get sample jobs
        jobs_query = queries.get('jobs', 'get_sample_jobs')
        jobs = db.execute(jobs_query, (limit,)).fetchall()
        
        return [dict(job) for job in jobs]
        
    except Exception as e:
        print(f"Error getting sample jobs: {e}")
        return []

@career_analysis_bp.route('/career-analysis')
def career_analysis():
    """Career Transition Analysis Generator interface."""
    try:
        # Get sample data for the interface
        sample_jobs = get_sample_jobs(20)
        
        # Get available divisions and locations for filters
        db = get_db()
        divisions_query = "SELECT DISTINCT Division FROM positions WHERE Division IS NOT NULL ORDER BY Division"
        divisions = [row[0] for row in db.execute(divisions_query).fetchall()]
        
        locations_query = "SELECT DISTINCT Location FROM positions WHERE Location IS NOT NULL ORDER BY Location"
        locations = [row[0] for row in db.execute(locations_query).fetchall()]
        
        return render_template('career_analysis.html', 
                             sample_jobs=sample_jobs,
                             divisions=divisions,
                             locations=locations)
    except Exception as e:
        print(f"Error loading Career Transition Analysis page: {e}")
        return render_template('career_analysis.html', 
                             sample_jobs=[],
                             divisions=[],
                             locations=[]) 