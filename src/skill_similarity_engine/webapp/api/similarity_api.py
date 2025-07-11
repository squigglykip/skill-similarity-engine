"""
Similarity API Module for NAB Skills Intelligence Platform
=========================================================

This module contains similarity and skills analysis endpoints:
- /api/skills-gap/<source_job_id>/<target_job_id>
- /api/skills-analysis/<from_job_id>/<to_job_id>
- /api/career-pathways-distribution/<job_id>

These endpoints provide sophisticated skills analysis, gap identification,
and career pathway distribution intelligence.
"""

from flask import Blueprint, request, jsonify, g
from ..sql import queries

# Create blueprint for similarity API
similarity_bp = Blueprint('similarity_api', __name__, url_prefix='/api')

def get_db():
    """Get database connection from Flask g object."""
    from flask import current_app
    import sqlite3
    if 'db' not in g:
        g.db = sqlite3.connect(str(current_app.config['DATABASE_PATH']))
        g.db.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return g.db

def get_webapp_config():
    """Get webapp configuration manager."""
    try:
        from ...config.webapp_config_manager import get_webapp_config_manager
        return get_webapp_config_manager()
    except ImportError:
        # Fallback for testing or if config manager is not available
        class MockConfig:
            def get_similarity_threshold(self, key): return 0.5
            def get_core_performance_config(self): return {'max_depth_default': 3, 'max_results_default': 10}
        return MockConfig()

@similarity_bp.route('/skills-gap/<source_job_id>/<target_job_id>')
def api_skills_gap(source_job_id, target_job_id):
    """API endpoint for skills gap analysis between two jobs."""
    try:
        db = get_db()
        
        # Get skills gap analysis using available query
        gap_query = queries.get('skills', 'get_skill_gaps_between_jobs')
        skills_gap = db.execute(gap_query, (source_job_id, target_job_id)).fetchall()
        
        # Organise skills by status - mapping gap_type to user-friendly categories
        skills_by_status = {
            'Skills in Job 1 Only': [],
            'Skills in Job 2 Only': [],
            'Shared Skills': []
        }
        
        for skill in skills_gap:
            gap_type = skill['gap_type']
            skill_data = {
                'name': skill['skill_name'],
                'category': skill['skill_category'],
                'subcategory': skill['skill_subcategory'],
                'job1_proficiency': skill['job1_proficiency'],
                'job2_proficiency': skill['job2_proficiency']
            }
            
            # Map SQL gap_type to user-friendly categories
            if gap_type == 'Missing in Job 1':
                skills_by_status['Skills in Job 2 Only'].append(skill_data)
            elif gap_type == 'Missing in Job 2':
                skills_by_status['Skills in Job 1 Only'].append(skill_data)
            elif gap_type == 'Same Requirement':
                skills_by_status['Shared Skills'].append(skill_data)
        
        return jsonify({
            'source_job_id': source_job_id,
            'target_job_id': target_job_id,
            'skills_gap': skills_by_status,
            'summary': {
                'skills_in_job1_only': len(skills_by_status['Skills in Job 1 Only']),
                'skills_in_job2_only': len(skills_by_status['Skills in Job 2 Only']),
                'shared_skills': len(skills_by_status['Shared Skills']),
                'total_skills_analyzed': sum(len(skills) for skills in skills_by_status.values())
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@similarity_bp.route('/skills-analysis/<from_job_id>/<to_job_id>')
def api_skills_analysis(from_job_id, to_job_id):
    """API endpoint for skills transition analysis between two jobs."""
    try:
        db = get_db()
        
        # Get skills for both jobs with skill metadata
        skills_query = """
        WITH job1_skills AS (
            SELECT js.Skill_ID, s.Skill_Name, s.Category, s.Subcategory, s.SkillType
            FROM job_skills js
            JOIN skills s ON js.Skill_ID = s.Skill_ID
            WHERE js.JobProfileID = ?
        ),
        job2_skills AS (
            SELECT js.Skill_ID, s.Skill_Name, s.Category, s.Subcategory, s.SkillType
            FROM job_skills js
            JOIN skills s ON js.Skill_ID = s.Skill_ID
            WHERE js.JobProfileID = ?
        ),
        skills_matched AS (
            SELECT j1.Skill_ID, j1.Skill_Name, j1.Category, j1.Subcategory, j1.SkillType
            FROM job1_skills j1
            INNER JOIN job2_skills j2 ON j1.Skill_ID = j2.Skill_ID
        ),
        skills_to_develop AS (
            SELECT j2.Skill_ID, j2.Skill_Name, j2.Category, j2.Subcategory, j2.SkillType
            FROM job2_skills j2
            LEFT JOIN job1_skills j1 ON j2.Skill_ID = j1.Skill_ID
            WHERE j1.Skill_ID IS NULL
        )
        SELECT 
            'matched' as skill_status,
            COUNT(*) as skill_count,
            SkillType,
            Category
        FROM skills_matched
        GROUP BY SkillType, Category
        UNION ALL
        SELECT 
            'develop' as skill_status,
            COUNT(*) as skill_count,
            SkillType,
            Category
        FROM skills_to_develop
        GROUP BY SkillType, Category
        """
        
        skills_analysis = db.execute(skills_query, (from_job_id, to_job_id)).fetchall()
        
        # Calculate summary metrics
        skills_matched = sum(row['skill_count'] for row in skills_analysis if row['skill_status'] == 'matched')
        skills_to_develop = sum(row['skill_count'] for row in skills_analysis if row['skill_status'] == 'develop')
        
        # Calculate difficulty based on skills overlap
        total_required_skills = skills_matched + skills_to_develop
        difficulty = 'Low' if total_required_skills == 0 else (
            'Low' if skills_to_develop / total_required_skills <= 0.3 else
            'Medium' if skills_to_develop / total_required_skills <= 0.6 else 'High'
        )
        
        # Get detailed skills for each category (SQLite compatible)
        detailed_skills_query = """
        WITH job1_skills AS (
            SELECT js.Skill_ID, s.Skill_Name, s.Category, s.SkillType, s.Info_URL
            FROM job_skills js
            JOIN skills s ON js.Skill_ID = s.Skill_ID
            WHERE js.JobProfileID = ?
        ),
        job2_skills AS (
            SELECT js.Skill_ID, s.Skill_Name, s.Category, s.SkillType, s.Info_URL
            FROM job_skills js
            JOIN skills s ON js.Skill_ID = s.Skill_ID
            WHERE js.JobProfileID = ?
        )
        SELECT 
            'matched' as status,
            j1.Skill_Name as skill_name,
            j1.Category as category,
            j1.SkillType as skill_type,
            j1.Info_URL as info_url
        FROM job1_skills j1
        INNER JOIN job2_skills j2 ON j1.Skill_ID = j2.Skill_ID
        UNION ALL
        SELECT 
            'develop' as status,
            j2.Skill_Name as skill_name,
            j2.Category as category,
            j2.SkillType as skill_type,
            j2.Info_URL as info_url
        FROM job2_skills j2
        LEFT JOIN job1_skills j1 ON j2.Skill_ID = j1.Skill_ID
        WHERE j1.Skill_ID IS NULL

        ORDER BY status, category, skill_name
        """
        
        detailed_skills = db.execute(detailed_skills_query, (from_job_id, to_job_id)).fetchall()
        
        # Handle ID mapping for backward compatibility
        # If job IDs look like node_X, they should be mapped to actual JobProfileIDs
        # but for now, log the issue and continue
        if from_job_id.startswith('node_') or to_job_id.startswith('node_'):
            print(f"⚠️ Received D3 node IDs instead of JobProfileIDs: {from_job_id} → {to_job_id}")
            print(f"   This suggests the JavaScript extractJobId function needs adjustment")
        
        # Calculate SkillType breakdown for skills to develop
        skilltype_to_develop = {}
        skilltype_matched = {}
        
        for row in skills_analysis:
            skill_type = row['SkillType'] or 'Unspecified'
            if row['skill_status'] == 'develop':
                skilltype_to_develop[skill_type] = skilltype_to_develop.get(skill_type, 0) + row['skill_count']
            elif row['skill_status'] == 'matched':
                skilltype_matched[skill_type] = skilltype_matched.get(skill_type, 0) + row['skill_count']
        
        return jsonify({
            'success': True,
            'skills_matched': skills_matched,
            'skills_to_develop': skills_to_develop,
            'transition_difficulty': difficulty,
            'skilltype_to_develop': skilltype_to_develop,
            'skilltype_matched': skilltype_matched,
            'skill_type_distribution': {
                (row['SkillType'] or 'Unspecified'): row['skill_count'] 
                for row in skills_analysis 
                if row['skill_status'] == 'matched'
            },
            'detailed_skills': [
                {
                    'name': row['skill_name'],
                    'category': row['category'] or 'General',
                    'skill_type': row['skill_type'] or 'Skill',
                    'status': row['status'],
                    'info_url': row['info_url']
                }
                for row in detailed_skills
            ]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500 