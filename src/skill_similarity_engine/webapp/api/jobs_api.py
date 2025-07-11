"""
Jobs API Module for NAB Skills Intelligence Platform
===================================================

This module contains all job-related API endpoints:
- /api/job-details/<job_id>
- /api/job-similarities/<job_id>
- /api/job-workforce/<job_id>
- /api/job-functions
- /api/jobs-in-function/<function>

These endpoints provide core job data, similarities, workforce context,
and organizational structure information.
"""

from flask import Blueprint, request, jsonify, g
from ..sql import queries

# Create blueprint for jobs API
jobs_bp = Blueprint('jobs_api', __name__, url_prefix='/api')

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

@jobs_bp.route('/job-details/<job_id>')
def api_job_details(job_id):
    """API endpoint for getting detailed job information including skills."""
    try:
        db = get_db()
        
        # Get complete job information with all 16 columns
        job_query = """
        SELECT JobProfileID, JobProfile, JobFunctionID, JobFunction, JobID, Job,
               ProfileTitleSuffix, ManagementLevel, JobSubFunctionID, JobSubFunction,
               JobCategoryID, JobCategory, Customer_Facing, is_Banker, 
               Executive_Leadership_Group, Accountability_Scope
        FROM jobs 
        WHERE JobProfileID = ?
        """
        job = db.execute(job_query, (job_id,)).fetchone()
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Get skills for this job
        skills_query = """
        SELECT s.Skill_ID, s.Skill_Name, s.Category, s.Subcategory, s.SkillType, s.Info_URL
        FROM job_skills js
        JOIN skills s ON js.Skill_ID = s.Skill_ID
        WHERE js.JobProfileID = ?
        ORDER BY s.Category, s.Skill_Name
        """
        skills = db.execute(skills_query, (job_id,)).fetchall()
        
        # Get position and employee counts for this job
        workforce_stats_query = """
        SELECT 
            COUNT(DISTINCT "Position Number") as position_count,
            COUNT(*) as employee_count
        FROM positions p
        WHERE p.JobProfileID = ?
        """
        workforce_stats = db.execute(workforce_stats_query, (job_id,)).fetchone()
        
        # Get similarity count (career pathways)
        pathways_query = """
        SELECT COUNT(*) as pathway_count
        FROM career_pathways cp
        WHERE cp.source_job_id = ?
        """
        pathway_count = db.execute(pathways_query, (job_id,)).fetchone()
        
        # Prepare job data with display names
        job_data = {
            'id': job['JobProfileID'],
            'title': job['JobProfile'],
            'function': job['JobFunction'],
            'function_id': job['JobFunctionID'],
            'job_id': job['JobID'],
            'job_name': job['Job'],
            'profile_title_suffix': job['ProfileTitleSuffix'],
            'management_level': job['ManagementLevel'],
            'job_subfunction_id': job['JobSubFunctionID'],
            'job_subfunction': job['JobSubFunction'],
            'job_category_id': job['JobCategoryID'],
            'job_category': job['JobCategory'],
            'customer_facing': job['Customer_Facing'] if job['Customer_Facing'] and job['Customer_Facing'].strip() else None,
            'is_banker': job['is_Banker'] if job['is_Banker'] and job['is_Banker'].strip() else None,
            'executive_leadership_group': job['Executive_Leadership_Group'] if job['Executive_Leadership_Group'] and job['Executive_Leadership_Group'].strip() else None,
            'accountability_scope': job['Accountability_Scope'] if job['Accountability_Scope'] and job['Accountability_Scope'].strip() else None
        }
        
        # Add standardised display names
        display_manager = get_display_manager()
        add_display_names_to_job(job_data, display_manager)

        return jsonify({
            'job': job_data,
            'skills': [{
                'id': skill['Skill_ID'],
                'name': skill['Skill_Name'],
                'category': skill['Category'],
                'subcategory': skill['Subcategory'],
                'type': skill['SkillType'],
                'info_url': skill['Info_URL']
            } for skill in skills],
            'stats': {
                'skills_count': len(skills),
                'positions_count': workforce_stats['position_count'] if workforce_stats else 0,
                'employee_count': workforce_stats['employee_count'] if workforce_stats else 0,
                'pathways_count': pathway_count['pathway_count'] if pathway_count else 0
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/job-workforce/<job_id>')
def api_job_workforce(job_id):
    """API endpoint for getting workforce context for a specific job."""
    try:
        db = get_db()
        
        # Get workforce distribution by division, business unit, and location
        # Note: COUNT(*) gives employee count (since each row = one employee)
        workforce_query = """
        SELECT 
            p.Division,
            p.Business_Unit,
            p.Location,
            COUNT(*) as employee_count
        FROM positions p
        WHERE p.JobProfileID = ?
        GROUP BY p.Division, p.Business_Unit, p.Location
        ORDER BY employee_count DESC
        """
        workforce_data = db.execute(workforce_query, (job_id,)).fetchall()
        
        # Aggregate by division, business unit, and location
        by_division = {}
        by_business_unit = {}
        by_location = {}
        total_employees = 0
        
        for row in workforce_data:
            total_employees += row['employee_count']
            
            # By division
            div = row['Division'] or 'Other'
            by_division[div] = by_division.get(div, 0) + row['employee_count']
            
            # By business unit
            bu = row['Business_Unit'] or 'Other'
            by_business_unit[bu] = by_business_unit.get(bu, 0) + row['employee_count']
            
            # By location
            loc = row['Location'] or 'Other'
            by_location[loc] = by_location.get(loc, 0) + row['employee_count']
        
        return jsonify({
            'total_employees': total_employees,
            'by_division': [{'division': k, 'count': v} for k, v in sorted(by_division.items(), key=lambda x: x[1], reverse=True)],
            'by_business_unit': [{'business_unit': k, 'count': v} for k, v in sorted(by_business_unit.items(), key=lambda x: x[1], reverse=True)],
            'by_location': [{'location': k, 'count': v} for k, v in sorted(by_location.items(), key=lambda x: x[1], reverse=True)]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/job-similarities/<job_id>')
def api_job_similarities(job_id):
    """API endpoint for getting job similarities."""
    try:
        # Get configuration for thresholds and limits
        from ...config.webapp_config_manager import get_webapp_config_manager
        webapp_config = get_webapp_config_manager()
        
        min_similarity = float(request.args.get('min_similarity', webapp_config.get_similarity_threshold('default')))
        limit = int(request.args.get('limit', webapp_config.get_result_limit('search')))
        
        db = get_db()
        similarities_query = queries.get('similarities', 'get_similar_jobs_with_threshold')
        similarities = db.execute(similarities_query, (job_id, min_similarity, limit)).fetchall()
        
        display_manager = get_display_manager()
        
        result = []
        for sim in similarities:
            sim_data = {
                'job_id': sim['id'],
                'job_title': sim['job_title'],
                'job_function': sim['job_function'],
                'job_function_id': sim['job_function_id'],
                'similarity_score': round(sim['similarity_score'], 3),
                'similarity_category': sim['similarity_category']
            }
            # Add standardised display names
            add_display_names_to_job(sim_data, display_manager)
            result.append(sim_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/job-functions')
def api_job_functions():
    """API endpoint for getting all job functions."""
    try:
        db = get_db()
        functions_query = queries.get('jobs', 'get_job_functions')
        functions = db.execute(functions_query).fetchall()
        
        return jsonify([{
            'id': func['JobFunctionID'],
            'name': func['JobFunction'],
            'job_count': func['job_count']
        } for func in functions])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/jobs-in-function/<function>')
def api_jobs_in_function(function):
    """API endpoint for getting jobs in a specific function."""
    try:
        db = get_db()
        jobs_query = queries.get('jobs', 'get_jobs_in_function')
        jobs = db.execute(jobs_query, (function,)).fetchall()
        
        display_manager = get_display_manager()
        
        result = []
        for job in jobs:
            job_data = {
                'id': job['JobProfileID'],
                'title': job['JobProfile'],
                'function': job['JobFunction'],
                'function_id': job['JobFunctionID']
            }
            # Add standardised display names
            add_display_names_to_job(job_data, display_manager)
            result.append(job_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/workforce-analysis/<job_ids>')
def api_workforce_analysis(job_ids):
    """API endpoint for workforce intelligence analysis for one or more jobs."""
    try:
        db = get_db()
        
        # Parse job IDs and filter out any D3 node IDs
        job_id_list = job_ids.split(',')
        job_id_list = [job_id.strip() for job_id in job_id_list if job_id.strip()]
        
        # Filter out D3 node IDs (which start with 'node_') and log them
        actual_job_ids = []
        node_ids = []
        for job_id in job_id_list:
            if job_id.startswith('node_'):
                node_ids.append(job_id)
            else:
                actual_job_ids.append(job_id)
        
        if node_ids:
            print(f"⚠️ Filtering out D3 node IDs from workforce analysis: {node_ids}")
            print(f"   Using actual JobProfileIDs only: {actual_job_ids}")
        
        if not actual_job_ids:
            return jsonify({
                'success': False,
                'error': 'No valid JobProfileIDs provided (only D3 node IDs received)',
                'node_ids_received': node_ids
            }), 400
        
        placeholders = ','.join(['?' for _ in actual_job_ids])
        
        # Get detailed workforce distribution for the jobs
        workforce_query = f"""
        SELECT 
            j.JobProfileID,
            j.JobProfile,
            j.JobFunction,
            (j.JobProfile || ' (' || j.JobProfileID || ')') as job_profile,
            p."Position Name" as position_name,
            p.Division,
            p.Business_Unit,
            p.Team,
            p."Salary Group",
            p."Employee Group",
            p.Location,
            p.Rg,
            COUNT(DISTINCT p."Position Number") as position_count,
            COUNT(DISTINCT p."Employee Number") as headcount
        FROM jobs j
        LEFT JOIN positions p ON j.JobProfileID = p.JobProfileID
        WHERE j.JobProfileID IN ({placeholders})
        GROUP BY j.JobProfileID, j.JobProfile, j.JobFunction, p."Position Name", p.Division, p.Business_Unit, p.Team, p."Salary Group", p."Employee Group", p.Location, p.Rg
        ORDER BY j.JobProfile, p.Division, p.Business_Unit, position_count DESC
        """
        
        workforce_data = db.execute(workforce_query, actual_job_ids).fetchall()
        
        # Calculate summary metrics
        total_positions = sum(row['position_count'] for row in workforce_data)
        unique_divisions = len(set(row['Division'] for row in workforce_data if row['Division']))
        unique_locations = len(set(row['Location'] for row in workforce_data if row['Location']))
        
        # Group by job for detailed analysis
        jobs_analysis = {}
        for row in workforce_data:
            job_id = row['JobProfileID']
            if job_id not in jobs_analysis:
                jobs_analysis[job_id] = {
                    'job_title': row['JobProfile'],
                    'job_function': row['JobFunction'],
                    'total_positions': 0,
                    'divisions': {},
                    'locations': {},
                    'business_units': {}
                }
            
            job_data = jobs_analysis[job_id]
            job_data['total_positions'] += row['position_count']
            
            if row['Division']:
                job_data['divisions'][row['Division']] = job_data['divisions'].get(row['Division'], 0) + row['position_count']
            
            if row['Location']:
                job_data['locations'][row['Location']] = job_data['locations'].get(row['Location'], 0) + row['position_count']
            
            if row['Business_Unit']:
                job_data['business_units'][row['Business_Unit']] = job_data['business_units'].get(row['Business_Unit'], 0) + row['position_count']
        
        return jsonify({
            'success': True,
            'total_positions': total_positions,
            'divisions_represented': unique_divisions,
            'locations_spread': unique_locations,
            'jobs_analysis': jobs_analysis,
            'detailed_workforce': [
                {
                    'job_id': row['JobProfileID'],
                    'job_title': row['JobProfile'],
                    'job_family': row['JobFunction'],
                    'job_profile': row['job_profile'],
                    'position_name': row['position_name'],
                    'division': row['Division'],
                    'business_unit': row['Business_Unit'],
                    'team': row['Team'],
                    'salary_group': row['Salary Group'],
                    'employee_group': row['Employee Group'],
                    'location': row['Location'],
                    'region': row['Rg'],
                    'position_count': row['position_count'],
                    'headcount': row['headcount']
                }
                for row in workforce_data
            ]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500 