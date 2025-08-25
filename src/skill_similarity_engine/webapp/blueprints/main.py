"""
Main Routes Blueprint
====================

Homepage and basic navigation routes for the SSE webapp.
Extracted from app.py as part of Phase 2b webapp modularization.

Routes:
- /: Homepage with platform overview and dashboard
- /components: Component library showcase
"""

from flask import Blueprint, render_template, g
import time

# Create blueprint
main_bp = Blueprint('main', __name__)

# Configuration access
def get_config():
    """Get webapp configuration with fallback."""
    try:
        from ...config.webapp_config_manager import WebappConfigManager
        return WebappConfigManager()
    except Exception:
        # Fallback for testing
        class MockConfig:
            def get_api_defaults(self):
                return {'default_limit': 20}
        return MockConfig()

def get_db():
    """Get database connection from Flask g object."""
    from flask import current_app
    import sqlite3
    if 'db' not in g:
        g.db = sqlite3.connect(str(current_app.config['DATABASE_PATH']))
        g.db.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return g.db

def get_display_manager():
    """Get job display manager from Flask g object."""
    if 'display_manager' not in g:
        try:
            from ...utils.display import JobDisplayManager
            db = get_db()
            g.display_manager = JobDisplayManager(db)
        except ImportError:
            g.display_manager = None
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
            if display_manager and job_dict.get('JobProfileID'):
                from ...utils.display import DisplayFormat
                job_dict['display_name'] = display_manager.get_display_name(
                    job_dict['JobProfileID'], DisplayFormat.STANDARD
                )
            else:
                job_dict['display_name'] = job_dict.get('job_title', job_dict.get('JobProfile', 'Unknown Job'))
            jobs_with_display_names.append(job_dict)
        
        return jobs_with_display_names
        
    except Exception as e:
        print(f"Error getting sample jobs: {e}")
        return []

@main_bp.route('/')
def index():
    """Homepage with overview and navigation."""
    from ..sql import queries
    
    try:
        db = get_db()
        start_time = time.time()
        
        print("🔍 PERFORMANCE DEBUG: Starting dashboard data loading...")
        
        # Get platform metrics for dashboard - TIMING THIS
        print("📊 Loading platform metrics...")
        query_start = time.time()
        platform_metrics_query = queries.get('metadata', 'get_platform_metrics')
        platform_metrics_raw = db.execute(platform_metrics_query).fetchall()
        print(f"  ✅ Platform metrics: {(time.time() - query_start)*1000:.2f}ms")
        
        # Convert platform metrics to dictionary for easier template access
        platform_metrics = {}
        for row in platform_metrics_raw:
            platform_metrics[row['metric']] = row['count']
        
        # TEMPORARILY DISABLE SLOW QUERIES FOR PERFORMANCE TESTING
        print("⚠️  PERFORMANCE TEST: Skipping slow queries...")
        
        # Get top job functions (formerly job families) - DISABLED
        # top_families_query = queries.get('metadata', 'get_top_job_functions')
        # top_families = db.execute(top_families_query).fetchall()
        top_families = []
        
        # Get career pathway insights - DISABLED
        # career_insights_query = queries.get('metadata', 'get_career_insights_summary')
        # career_insights_raw = db.execute(career_insights_query).fetchall()
        career_insights = {}
        
        # Get mobility hubs - DISABLED
        # mobility_hubs_query = queries.get('metadata', 'get_mobility_hubs')
        # mobility_hubs = db.execute(mobility_hubs_query).fetchall()
        mobility_hubs = []
        
        # Get similarity distribution - DISABLED
        # similarity_dist_query = queries.get('metadata', 'get_similarity_distribution')
        # similarity_distribution = db.execute(similarity_dist_query).fetchall()
        similarity_distribution = []
        
        # Get similarity statistics - DISABLED
        # similarity_stats_query = queries.get('metadata', 'get_similarity_statistics')
        # similarity_stats_raw = db.execute(similarity_stats_query).fetchall()
        similarity_stats = {}
        
        # Strategic recommendations - DISABLED
        strategic_recommendations = []
        skills_concentration = []
        cross_family_opportunities = []
        cross_family_similarities = []
        cross_family_stats_raw = None
        
        total_time = (time.time() - start_time) * 1000
        print(f"🚀 PERFORMANCE DEBUG: Dashboard data loading completed in {total_time:.2f}ms")
        
        sample_jobs = get_sample_jobs(6)  # Reduced for cleaner display
        
        return render_template('index.html', 
                             sample_jobs=sample_jobs,
                             platform_metrics=platform_metrics,
                             top_families=top_families[:3],
                             career_insights=career_insights,
                             mobility_hubs=mobility_hubs[:3],
                             similarity_distribution=similarity_distribution,
                             similarity_stats=similarity_stats,
                             strategic_recommendations=strategic_recommendations[:5],
                             skills_concentration=skills_concentration[:5],
                             cross_family_opportunities=cross_family_opportunities[:3],
                             cross_family_similarities=cross_family_similarities[:3],
                             cross_family_stats=cross_family_stats_raw)  # Top recommendations and insights
    except Exception as e:
        print(f"Error loading homepage: {e}")
        sample_jobs = get_sample_jobs(6)
        # Fallback with empty metrics
        platform_metrics = {
            'jobs_count': 0,
            'skills_count': 0,
            'skills_in_use_count': 0,
            'positions_count': 0,
            'pathways_count': 0,
            'job_families_count': 0,
            'divisions_count': 0
        }
        return render_template('index.html', 
                             sample_jobs=sample_jobs,
                             platform_metrics=platform_metrics,
                             top_families=[],
                             career_insights={},
                             mobility_hubs=[],
                             similarity_distribution=[],
                             similarity_stats={},
                             strategic_recommendations=[],
                             skills_concentration=[],
                             cross_family_opportunities=[],
                             cross_family_similarities=[],
                             cross_family_stats=None)

@main_bp.route('/components')
def components():
    """Component library showcase page."""
    return render_template('components.html') 