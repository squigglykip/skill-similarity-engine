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

def safe_row_get(row, key, default=None):
    """Safely get value from sqlite3.Row object with fallback to default."""
    try:
        return row[key] if key in row.keys() else default
    except (KeyError, IndexError):
        return default

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
        
        # Get enhanced skills analysis using organized SQL (now requires 5 parameters)
        skills_query = queries.get('skills', 'get_skills_analysis_summary_for_api')
        skills_analysis = db.execute(skills_query, (from_job_id, to_job_id, to_job_id, to_job_id, from_job_id)).fetchall()
        
        # Calculate summary metrics
        skills_matched = sum(row['skill_count'] for row in skills_analysis if row['skill_status'] == 'matched')
        skills_to_develop = sum(row['skill_count'] for row in skills_analysis if row['skill_status'] == 'develop')
        skills_transferable = sum(row['skill_count'] for row in skills_analysis if row['skill_status'] == 'transferable')
        
        # Calculate difficulty based on skills overlap
        total_required_skills = skills_matched + skills_to_develop
        difficulty = 'Low' if total_required_skills == 0 else (
            'Low' if skills_to_develop / total_required_skills <= 0.3 else
            'Medium' if skills_to_develop / total_required_skills <= 0.6 else 'High'
        )
        
        # Get detailed skills using organized SQL (now requires 5 parameters)
        detailed_skills_query = queries.get('skills', 'get_detailed_skills_analysis_for_api')
        detailed_skills = db.execute(detailed_skills_query, (from_job_id, to_job_id, to_job_id, to_job_id, from_job_id)).fetchall()
        
        # Handle ID mapping for backward compatibility
        # If job IDs look like node_X, they should be mapped to actual JobProfileIDs
        # but for now, log the issue and continue
        if from_job_id.startswith('node_') or to_job_id.startswith('node_'):
            print(f"⚠️ Received D3 node IDs instead of JobProfileIDs: {from_job_id} → {to_job_id}")
            print(f"   This suggests the JavaScript extractJobId function needs adjustment")
        
        # Calculate enhanced metrics from V2 data
        skilltype_to_develop = {}
        skilltype_matched = {}
        
        # Enhanced intelligence metrics
        total_defining_matched = 0
        total_defining_to_develop = 0
        total_defining_transferable = 0
        total_rare_matched = 0
        total_rare_to_develop = 0
        total_emerging_matched = 0
        total_emerging_to_develop = 0
        total_declining_matched = 0
        total_declining_to_develop = 0
        
        for row in skills_analysis:
            skill_type = safe_row_get(row, 'SkillType') or 'Unspecified'
            if row['skill_status'] == 'develop':
                skilltype_to_develop[skill_type] = skilltype_to_develop.get(skill_type, 0) + row['skill_count']
                total_defining_to_develop += safe_row_get(row, 'defining_skills_count', 0)
                total_rare_to_develop += safe_row_get(row, 'rare_skills_count', 0)
                total_emerging_to_develop += safe_row_get(row, 'emerging_skills_count', 0)
                total_declining_to_develop += safe_row_get(row, 'declining_skills_count', 0)
            elif row['skill_status'] == 'matched':
                skilltype_matched[skill_type] = skilltype_matched.get(skill_type, 0) + row['skill_count']
                total_defining_matched += safe_row_get(row, 'defining_skills_count', 0)
                total_rare_matched += safe_row_get(row, 'rare_skills_count', 0)
                total_emerging_matched += safe_row_get(row, 'emerging_skills_count', 0)
                total_declining_matched += safe_row_get(row, 'declining_skills_count', 0)
            elif row['skill_status'] == 'transferable':
                total_defining_transferable += safe_row_get(row, 'defining_skills_count', 0)
        
        return jsonify({
            'success': True,
            'skills_matched': skills_matched,
            'skills_to_develop': skills_to_develop,
            'skills_transferable': skills_transferable,
            'transition_difficulty': difficulty,
            'skilltype_to_develop': skilltype_to_develop,
            'skilltype_matched': skilltype_matched,
            'skill_type_distribution': {
                (safe_row_get(row, 'SkillType') or 'Unspecified'): row['skill_count'] 
                for row in skills_analysis 
                if row['skill_status'] == 'matched'
            },
            # Enhanced V2 intelligence metrics
            'enhanced_insights': {
                'defining_skills_matched': total_defining_matched,
                'defining_skills_to_develop': total_defining_to_develop,
                'defining_skills_transferable': total_defining_transferable,
                'rare_skills_matched': total_rare_matched,
                'rare_skills_to_develop': total_rare_to_develop,
                'emerging_skills_matched': total_emerging_matched,
                'emerging_skills_to_develop': total_emerging_to_develop,
                'declining_skills_matched': total_declining_matched,
                'declining_skills_to_develop': total_declining_to_develop
            },
            'detailed_skills': [
                {
                    'name': row['skill_name'],
                    'category': safe_row_get(row, 'category') or 'General',
                    'skill_type': safe_row_get(row, 'skill_type') or 'Skill',
                    'status': row['status'],
                    'is_defining': bool(safe_row_get(row, 'is_defining', 0)),
                    'defining_rank': safe_row_get(row, 'defining_rank', 999),
                    'rarity_score': safe_row_get(row, 'rarity_score', 50.0),
                    'rarity_category': safe_row_get(row, 'rarity_category', 'Common'),
                    'velocity_category': safe_row_get(row, 'velocity_category', 'stable'),
                    'trend_direction': safe_row_get(row, 'trend_direction', 'stable'),
                    'trend_strength': safe_row_get(row, 'trend_strength', 'stable'),
                    'info_url': safe_row_get(row, 'info_url', '')
                }
                for row in detailed_skills
            ]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500 