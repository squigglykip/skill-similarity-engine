"""
V2 Dashboard API Module for NAB Skills Intelligence Platform
==========================================================

This module contains V2 dashboard endpoints for fast analytics widgets:
- /api/v2/dashboard/job-families-summary
- /api/v2/dashboard/movement-patterns-summary  
- /api/v2/dashboard/skill-intelligence-summary
- /api/v2/dashboard/overview

These endpoints provide fast, focused metrics for dashboard widgets
using pre-computed V2 analytics tables.
"""

from flask import Blueprint, jsonify, g

# Create blueprint for V2 dashboard API
v2_dashboard_bp = Blueprint('v2_dashboard_api', __name__, url_prefix='/api/v2/dashboard')

def get_db():
    """Get database connection from Flask g object."""
    from flask import current_app
    import sqlite3
    if 'db' not in g:
        g.db = sqlite3.connect(str(current_app.config['DATABASE_PATH']))
        g.db.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return g.db

@v2_dashboard_bp.route('/job-families-summary')
def api_job_families_summary():
    """Fast job families overview for dashboard widget."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get job families summary
        summary_query = queries.get('v2_dashboard', 'get_job_families_summary')
        summary = db.execute(summary_query).fetchone()
        
        # Get top families
        top_families_query = queries.get('v2_dashboard', 'get_top_job_families')
        top_families = [dict(row) for row in db.execute(top_families_query).fetchall()]
        
        if not summary:
            return jsonify({
                'success': False,
                'error': 'No job families data available'
            }), 404
        
        summary_data = dict(summary)
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_families': summary_data.get('total_families', 0),
                    'jobs_in_families': summary_data.get('jobs_in_families', 0),
                    'avg_quality_score': round(summary_data.get('avg_quality_score', 0), 3),
                    'high_quality_families': summary_data.get('high_quality_families', 0),
                    'largest_family_size': summary_data.get('largest_family_size', 0),
                    'quality_percentage': round((summary_data.get('high_quality_families', 0) / summary_data.get('total_families', 1)) * 100, 1)
                },
                'top_families': top_families,
                'data_source': 'analytics_job_families + analytics_job_family_characteristics'
            }
        })
        
    except Exception as e:
        import traceback
        error_details = {
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }
        print(f"ERROR in job_families_summary: {error_details}")
        return jsonify({
            'success': False,
            'error': str(e),
            'debug': error_details
        }), 500

@v2_dashboard_bp.route('/movement-patterns-summary')
def api_movement_patterns_summary():
    """Fast movement patterns overview for dashboard widget."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get movement summary
        summary_query = queries.get('v2_dashboard', 'get_movement_patterns_summary')
        summary = db.execute(summary_query).fetchone()
        
        # Get hot movement paths
        hot_paths_query = queries.get('v2_dashboard', 'get_movement_hot_paths')
        hot_paths = [dict(row) for row in db.execute(hot_paths_query).fetchall()]
        
        if not summary:
            return jsonify({
                'success': False,
                'error': 'No movement patterns data available'
            }), 404
        
        summary_data = dict(summary)
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_patterns': summary_data.get('total_patterns', 0),
                    'source_jobs': summary_data.get('source_jobs', 0),
                    'target_jobs': summary_data.get('target_jobs', 0),
                    'total_movements': summary_data.get('total_movements', 0),
                    'avg_success_rate': round(summary_data.get('avg_success_rate', 0), 3) if summary_data.get('avg_success_rate') else 0,
                    'connectivity_ratio': round((summary_data.get('total_patterns', 0) / max(summary_data.get('source_jobs', 1), 1)), 2)
                },
                'hot_paths': hot_paths,
                'data_source': 'analytics_movement_patterns'
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@v2_dashboard_bp.route('/skill-intelligence-summary')
def api_skill_intelligence_summary():
    """Fast skill intelligence overview for dashboard widget."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get skill rarity summary
        rarity_query = queries.get('v2_dashboard', 'get_skill_intelligence_summary')
        rarity_summary = db.execute(rarity_query).fetchone()
        
        # Get skill bundles count
        bundles_count_query = queries.get('v2_dashboard', 'get_skill_bundles_summary')
        bundles_count = db.execute(bundles_count_query).fetchone()
        
        # Get skill trends summary
        trends_query = queries.get('v2_dashboard', 'get_skill_trends_summary')
        trends_summary = db.execute(trends_query).fetchone()
        
        # Get defining skills summary
        defining_query = queries.get('v2_dashboard', 'get_defining_skills_summary')
        defining_summary = db.execute(defining_query).fetchone()
        
        # Get specialized skills summary
        specialized_query = queries.get('v2_dashboard', 'get_specialized_skills_summary')
        specialized_summary = db.execute(specialized_query).fetchone()
        
        # Get top skill bundles
        bundles_query = queries.get('v2_dashboard', 'get_top_skill_bundles')
        top_bundles = [dict(row) for row in db.execute(bundles_query).fetchall()]
        
        # Get rare skills by category
        rare_by_category_query = queries.get('v2_dashboard', 'get_rare_skills_by_category')
        rare_by_category = [dict(row) for row in db.execute(rare_by_category_query).fetchall()]
        
        # Combine rarity analysis with bundles count
        rarity_data = dict(rarity_summary) if rarity_summary else {}
        if bundles_count:
            rarity_data['skill_bundles'] = dict(bundles_count).get('skill_bundles_count', 0)

        return jsonify({
            'success': True,
            'data': {
                'rarity_analysis': rarity_data,
                'trends_analysis': dict(trends_summary) if trends_summary else {},
                'defining_skills': dict(defining_summary) if defining_summary else {},
                'specialized_skills': dict(specialized_summary) if specialized_summary else {},
                'top_bundles': top_bundles,
                'rare_by_category': rare_by_category,
                'data_source': 'analytics_skill_rarity + analytics_skill_bundles + analytics_skill_demand_trends + analytics_job_defining_skills + analytics_specialized_skills'
            }
        })
        
    except Exception as e:
        import traceback
        error_details = {
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }
        print(f"ERROR in skill_intelligence_summary: {error_details}")
        return jsonify({
            'success': False,
            'error': str(e),
            'debug': error_details
        }), 500

@v2_dashboard_bp.route('/architecture-health-summary')
def api_architecture_health_summary():
    """Fast architecture health overview for dashboard widget."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get architecture health summary
        health_query = queries.get('v2_dashboard', 'get_architecture_health_summary')
        health_summary = db.execute(health_query).fetchone()
        
        if not health_summary:
            return jsonify({
                'success': False,
                'error': 'No architecture health data available'
            }), 404
        
        health_data = dict(health_summary)
        
        # Calculate health indicators
        total_clusters = health_data.get('total_clusters', 1)
        healthy_clusters = health_data.get('healthy_clusters', 0)
        poor_clusters = health_data.get('poor_quality_clusters', 0)
        
        health_percentage = round((healthy_clusters / total_clusters) * 100, 1)
        poor_percentage = round((poor_clusters / total_clusters) * 100, 1)
        
        # Determine overall health status
        if health_percentage >= 80:
            health_status = 'excellent'
            health_color = 'green'
        elif health_percentage >= 60:
            health_status = 'good'
            health_color = 'blue'
        elif health_percentage >= 40:
            health_status = 'fair'
            health_color = 'yellow'
        else:
            health_status = 'poor'
            health_color = 'red'
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_clusters': total_clusters,
                    'avg_silhouette_score': round(health_data.get('avg_silhouette_score', 0), 3),
                    'healthy_clusters': healthy_clusters,
                    'poor_quality_clusters': poor_clusters,
                    'total_jobs_clustered': health_data.get('total_jobs_clustered', 0),
                    'avg_business_value': round(health_data.get('avg_business_value', 0), 3),
                    'health_percentage': health_percentage,
                    'poor_percentage': poor_percentage,
                    'health_status': health_status,
                    'health_color': health_color
                },
                'data_source': 'analytics_job_families + analytics_job_family_characteristics'
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@v2_dashboard_bp.route('/overview')
def api_dashboard_overview():
    """Complete dashboard overview combining all V2 analytics."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get all summary data in parallel
        job_families_query = queries.get('v2_dashboard', 'get_job_families_summary')
        movement_query = queries.get('v2_dashboard', 'get_movement_patterns_summary')
        rarity_query = queries.get('v2_dashboard', 'get_skill_intelligence_summary')
        trends_query = queries.get('v2_dashboard', 'get_skill_trends_summary')
        health_query = queries.get('v2_dashboard', 'get_architecture_health_summary')
        
        job_families_data = db.execute(job_families_query).fetchone()
        movement_data = db.execute(movement_query).fetchone()
        rarity_data = db.execute(rarity_query).fetchone()
        trends_data = db.execute(trends_query).fetchone()
        health_data = db.execute(health_query).fetchone()
        
        return jsonify({
            'success': True,
            'data': {
                'job_families': dict(job_families_data) if job_families_data else {},
                'movement_patterns': dict(movement_data) if movement_data else {},
                'skill_rarity': dict(rarity_data) if rarity_data else {},
                'skill_trends': dict(trends_data) if trends_data else {},
                'architecture_health': dict(health_data) if health_data else {},
                'data_timestamp': 'real_time',
                'data_source': 'v2_analytics_complete'
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
