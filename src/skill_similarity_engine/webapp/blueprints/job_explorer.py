"""
Job Explorer Routes Blueprint
============================

Job search, exploration, and similarity analysis routes for the SSE webapp.
Extracted from app.py as part of Phase 2b webapp modularization.

Routes:
- /job-search: Job search and exploration interface
- /similarity-results: Job similarity analysis results
"""

from flask import Blueprint, render_template, request, g

# Create blueprint
job_explorer_bp = Blueprint('job_explorer', __name__)

def get_db():
    """Get database connection from Flask g object."""
    return g.db

def get_display_manager():
    """Get job display manager from Flask g object.""" 
    return g.display_manager

def get_sample_jobs(limit=None):
    """Get sample jobs for display."""
    from ..sql import queries
    
    try:
        db = get_db()
        
        if limit is None:
            limit = 20  # Default limit for architectural pattern demo
        
        # Get sample jobs with display names
        jobs_query = queries.get('jobs', 'get_sample_jobs')
        jobs = db.execute(jobs_query, (limit,)).fetchall()
        
        # Add display names using display manager
        display_manager = get_display_manager()
        jobs_with_display_names = []
        
        for job in jobs:
            job_dict = dict(job)
            # Add display names for consistent presentation
            job_dict['display_name'] = display_manager.get_job_display_name(
                job_dict.get('JobProfileID', ''),
                job_dict.get('JobProfile', ''),
                job_dict.get('Job', ''),
                job_dict.get('ProfileTitleSuffix', '')
            )
            jobs_with_display_names.append(job_dict)
        
        return jobs_with_display_names
        
    except Exception as e:
        print(f"Error getting sample jobs: {e}")
        return []

def get_job_similarities(job_id, limit=10):
    """Get similar jobs for a given job ID."""
    from ..sql import queries
    
    try:
        db = get_db()
        
        # Get job similarities
        similarities_query = queries.get('similarities', 'get_job_similarities')
        similarities = db.execute(similarities_query, (job_id, limit)).fetchall()
        
        # Add display names using display manager
        display_manager = get_display_manager()
        similarities_with_display_names = []
        
        for sim in similarities:
            sim_dict = dict(sim)
            # Add display names for consistent presentation
            sim_dict['display_name'] = display_manager.get_job_display_name(
                sim_dict.get('JobProfileID', ''),
                sim_dict.get('JobProfile', ''),
                sim_dict.get('Job', ''),
                sim_dict.get('ProfileTitleSuffix', '')
            )
            similarities_with_display_names.append(sim_dict)
        
        return similarities_with_display_names
        
    except Exception as e:
        print(f"Error getting job similarities: {e}")
        return []

@job_explorer_bp.route('/job-search')
def job_search():
    """Job search and exploration interface."""
    from ..sql import queries
    
    try:
        db = get_db()
        
        # Get job functions for filter dropdown
        functions_query = queries.get('jobs', 'get_job_functions')
        functions = db.execute(functions_query).fetchall()
        
        # Get sample jobs for initial display
        sample_jobs = get_sample_jobs(20)
        
        return render_template('job_explorer.html', 
                             job_functions=functions,
                             jobs=sample_jobs)
    except Exception as e:
        print(f"Error loading job search: {e}")
        sample_jobs = get_sample_jobs(20)
        return render_template('job_explorer.html', 
                             job_functions=[], 
                             jobs=sample_jobs)

@job_explorer_bp.route('/job-search-v2')
def job_search_v2():
    """Job search and exploration interface - V2 Clean Layout."""
    from ..sql import queries
    
    try:
        db = get_db()
        
        # Get job functions for filter dropdown
        functions_query = queries.get('jobs', 'get_job_functions')
        functions = db.execute(functions_query).fetchall()
        
        # Get sample jobs for initial display
        sample_jobs = get_sample_jobs(20)
        
        return render_template('job_explorer_v2.html', 
                             job_functions=functions,
                             jobs=sample_jobs)
    except Exception as e:
        print(f"Error loading job search v2: {e}")
        sample_jobs = get_sample_jobs(20)
        return render_template('job_explorer_v2.html', 
                             job_functions=[], 
                             jobs=sample_jobs)

@job_explorer_bp.route('/similarity-results')
def similarity_results():
    """Similarity results page."""
    job_id = request.args.get('job_id')
    
    if job_id:
        # Get specific job details
        from ..sql import queries
        db = get_db()
        job_query = queries.get('jobs', 'get_job_details')
        job = db.execute(job_query, (job_id,)).fetchone()
        
        if job:
            similar_jobs = get_job_similarities(job['id'], 10)
            return render_template('similarity_results.html', 
                                 source_job=job, 
                                 similar_jobs=similar_jobs)
    
    # Use first available job for demo if no specific job requested
    sample_jobs = get_sample_jobs(1)
    if sample_jobs:
        job = sample_jobs[0]
        similar_jobs = get_job_similarities(job['id'], 10)
        return render_template('similarity_results.html', 
                             source_job=job, 
                             similar_jobs=similar_jobs)
    
    return render_template('similarity_results.html', 
                         source_job=None, 
                         similar_jobs=[]) 