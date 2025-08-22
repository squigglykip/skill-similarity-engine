"""
Search API Module for NAB Skills Intelligence Platform
======================================================

This module contains all search-related API endpoints:
- /api/search-jobs
- /api/search-all-jobs  
- /api/career-analysis-jobs

These endpoints provide job search, autocomplete functionality,
and specialized search for career analysis features.
"""

from flask import Blueprint, request, jsonify, g
from ..sql import queries

# Create blueprint for search API
search_bp = Blueprint('search_api', __name__, url_prefix='/api')

def get_db():
    """Get database connection from Flask g object."""
    from flask import current_app
    import sqlite3
    if 'db' not in g:
        g.db = sqlite3.connect(str(current_app.config['DATABASE_PATH']))
        g.db.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return g.db

def get_display_manager():
    """Get JobDisplayManager instance for consistent job naming."""
    try:
        from ...utils.display import JobDisplayManager, DisplayFormat
        db = get_db()
        return JobDisplayManager(db) if db else None
    except ImportError:
        return None

def add_display_names_to_job(job_data, display_manager=None):
    """Add standardised display names to job data."""
    if not display_manager:
        display_manager = get_display_manager()
    
    if display_manager and job_data:
        job_id = job_data.get('id') or job_data.get('job_id') or job_data.get('JobProfileID')
        if job_id:
            from ...utils.display import DisplayFormat
            job_data['display_name_standard'] = display_manager.get_display_name(job_id, DisplayFormat.STANDARD)
            job_data['display_name_search'] = display_manager.get_display_name(job_id, DisplayFormat.SEARCH) 
            job_data['display_name_dropdown'] = display_manager.get_display_name(job_id, DisplayFormat.DROPDOWN)
            job_data['display_name_compact'] = display_manager.get_display_name(job_id, DisplayFormat.COMPACT)
    
    return job_data

def search_jobs(query, limit=None):
    """Search jobs by name using organised SQL."""
    from ...config.webapp_config_manager import get_webapp_config_manager
    webapp_config = get_webapp_config_manager()
    
    if limit is None:
        limit = webapp_config.get_core_api_config().get('default_search_limit', 10)
    
    db = get_db()
    search_query = queries.get('jobs', 'search_jobs')
    if not search_query:
        return []
    cursor = db.execute(search_query, (f'%{query}%', None, None))
    return cursor.fetchmany(limit)

@search_bp.route('/search-jobs')
def api_search_jobs():
    """API endpoint for job search autocomplete."""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    jobs = search_jobs(query, 10)
    display_manager = get_display_manager()
    
    result = []
    for job in jobs:
        job_data = {
            'id': job['id'],
            'title': job['job_title'],
            'function': job['job_function'],
            'function_id': job['job_function_id']
        }
        # Add standardised display names
        add_display_names_to_job(job_data, display_manager)
        result.append(job_data)
    
    return jsonify(result)

@search_bp.route('/search-all-jobs')
def api_search_all_jobs():
    """API endpoint for comprehensive job search with detailed job information."""
    try:
        search_term = request.args.get('search', '')
        limit = int(request.args.get('limit', 50))
        
        db = get_db()
        
        if search_term:
            # Search jobs with full job profile information
            search_query = """
            SELECT 
                JobProfileID as id,
                JobProfile as job_title,
                JobFunction as job_function,
                JobFunctionID as job_function_id,
                JobSubFunction as job_subfunction,
                ManagementLevel as management_level,
                Job as job_name,
                ProfileTitleSuffix as suffix
            FROM core_job_architecture 
            WHERE JobProfile LIKE ? OR JobProfileID LIKE ? OR Job LIKE ?
              AND JobProfile IS NOT NULL  -- FAIL-FAST validation
            ORDER BY 
                CASE 
                    WHEN JobProfileID LIKE ? THEN 1 
                    WHEN JobProfile LIKE ? THEN 2 
                    WHEN Job LIKE ? THEN 3
                    ELSE 4 
                END,
                JobProfile 
            LIMIT ?
            """
            search_pattern = f'%{search_term}%'
            exact_pattern = f'{search_term}%'
            jobs = db.execute(search_query, (
                search_pattern, search_pattern, search_pattern,
                exact_pattern, exact_pattern, exact_pattern,
                limit
            )).fetchall()
        else:
            # Get sample jobs when no search term
            sample_query = """
            SELECT 
                JobProfileID as id,
                JobProfile as job_title,
                JobFunction as job_function,
                JobFunctionID as job_function_id,
                JobSubFunction as job_subfunction,
                ManagementLevel as management_level,
                Job as job_name,
                ProfileTitleSuffix as suffix
            FROM core_job_architecture 
            WHERE JobProfile IS NOT NULL  -- FAIL-FAST validation
            ORDER BY JobProfile 
            LIMIT ?
            """
            jobs = db.execute(sample_query, (limit,)).fetchall()
        
        # Add display names and return enhanced job data
        display_manager = get_display_manager()
        result = []
        
        for job in jobs:
            job_data = {
                'id': job['id'],
                'job_title': job['job_title'],
                'job_function': job['job_function'],
                'job_function_id': job['job_function_id'],
                'job_subfunction': job['job_subfunction'],
                'management_level': job['management_level'],
                'job_name': job['job_name'],
                'suffix': job['suffix']
            }
            
            # Add standardised display names
            add_display_names_to_job(job_data, display_manager)
            result.append(job_data)
        
        return jsonify({
            'jobs': result,
            'total_found': len(result),
            'search_term': search_term
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@search_bp.route('/career-analysis-jobs')
def api_career_analysis_jobs():
    """Get jobs for Career Transition Analysis dropdowns with search capability."""
    try:
        search_term = request.args.get('search', '')
        limit = int(request.args.get('limit', 50))
        
        db = get_db()
        
        if search_term:
            # Search jobs by JobProfile text OR JobProfileID
            query = """
            SELECT 
                JobProfileID as id,
                JobProfile as job_profile,
                Job as job_title,
                ProfileTitleSuffix as suffix,
                ManagementLevel as management_level,
                JobFunction as function,
                JobFunctionID as function_id,
                JobSubFunction as sub_function
            FROM core_job_architecture 
            WHERE (JobProfile LIKE ? OR JobProfileID LIKE ?)
              AND JobProfile IS NOT NULL  -- FAIL-FAST validation
            ORDER BY 
                CASE 
                    WHEN JobProfileID LIKE ? THEN 1 
                    WHEN JobProfile LIKE ? THEN 2 
                    ELSE 3 
                END,
                JobProfile 
            LIMIT ?
            """
            search_pattern = f'%{search_term}%'
            exact_id_pattern = f'{search_term}%'
            exact_title_pattern = f'{search_term}%'
            jobs = db.execute(query, (search_pattern, search_pattern, exact_id_pattern, exact_title_pattern, limit)).fetchall()
        else:
            # Get sample jobs with detailed information
            query = """
            SELECT 
                JobProfileID as id,
                JobProfile as job_profile,
                Job as job_title,
                ProfileTitleSuffix as suffix,
                ManagementLevel as management_level,
                JobFunction as function,
                JobFunctionID as function_id,
                JobSubFunction as sub_function
            FROM core_job_architecture 
            WHERE JobProfile IS NOT NULL  -- FAIL-FAST validation
            ORDER BY JobProfile 
            LIMIT ?
            """
            jobs = db.execute(query, (limit,)).fetchall()
        
        # Add display names to job results
        display_manager = get_display_manager()
        jobs_with_display_names = []
        
        for job in jobs:
            job_data = {
                'id': job['id'],
                'job_profile': job['job_profile'],
                'job_title': job['job_title'],
                'suffix': job['suffix'],
                'management_level': job['management_level'],
                'function': job['function'],
                'function_id': job['function_id'],
                'sub_function': job['sub_function']
            }
            
            # Add standardised display names
            add_display_names_to_job(job_data, display_manager)
            jobs_with_display_names.append(job_data)
        
        return jsonify({
            'jobs': jobs_with_display_names,
            'total_found': len(jobs_with_display_names),
            'search_term': search_term
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 