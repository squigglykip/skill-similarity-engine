"""
Metadata API Module for NAB Skills Intelligence Platform
=======================================================

This module contains metadata and system information endpoints:
- /api/database-health
- /api/organizational-data

These endpoints provide system health information, database statistics,
and organizational hierarchy data for filter components.
"""

from flask import Blueprint, jsonify, g

# Create blueprint for metadata API
metadata_bp = Blueprint('metadata_api', __name__, url_prefix='/api')

def get_db():
    """Get database connection from Flask g object."""
    from flask import current_app
    import sqlite3
    if 'db' not in g:
        g.db = sqlite3.connect(str(current_app.config['DATABASE_PATH']))
        g.db.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return g.db

@metadata_bp.route('/database-health')
def api_database_health():
    """API endpoint for database health check and statistics."""
    try:
        # Import queries locally to avoid circular imports
        from ..sql import queries
        
        db = get_db()
        
        # Get health check
        health_query = queries.get('metadata', 'get_database_health_check')
        health_checks = db.execute(health_query).fetchall()
        
        # Get basic stats
        stats_query = queries.get('metadata', 'get_database_stats')
        stats = db.execute(stats_query).fetchall()
        
        return jsonify({
            'health_checks': [{
                'check_name': check['check_name'],
                'status': check['status'],
                'details': check['details']
            } for check in health_checks],
            'database_stats': [{
                'metric': stat['metric'],
                'value': stat['value']
            } for stat in stats],
            'timestamp': db.execute('SELECT datetime("now")').fetchone()[0]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@metadata_bp.route('/organizational-data')
def api_organizational_data():
    """API endpoint to get organizational hierarchy data for filters."""
    try:
        db = get_db()
        
        # Import queries locally to avoid circular imports
        from ..sql import queries
        
        # Get unique divisions using organized SQL
        divisions_query = queries.get('metadata', 'get_organizational_divisions')
        divisions = [row['Division'] for row in db.execute(divisions_query).fetchall()]
        
        # Get unique business units using organized SQL
        business_units_query = queries.get('metadata', 'get_organizational_business_units')
        business_units = [row['Business_Unit'] for row in db.execute(business_units_query).fetchall()]
        
        # Get unique locations using organized SQL
        locations_query = queries.get('metadata', 'get_organizational_locations')
        locations = [row['Location'] for row in db.execute(locations_query).fetchall()]
        
        # Get unique regions using organized SQL
        regions_query = queries.get('metadata', 'get_organizational_regions')
        regions = [row['Rg'] for row in db.execute(regions_query).fetchall()]
        
        return jsonify({
            'success': True,
            'data': {
                'divisions': divisions,
                'business_units': business_units,
                'locations': locations,
                'regions': regions
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 