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
        
        # Get unique divisions
        divisions_query = """
        SELECT DISTINCT Division 
        FROM positions 
        WHERE Division IS NOT NULL AND Division != ''
        ORDER BY Division
        """
        divisions = [row['Division'] for row in db.execute(divisions_query).fetchall()]
        
        # Get unique business units
        business_units_query = """
        SELECT DISTINCT Business_Unit 
        FROM positions 
        WHERE Business_Unit IS NOT NULL AND Business_Unit != ''
        ORDER BY Business_Unit
        """
        business_units = [row['Business_Unit'] for row in db.execute(business_units_query).fetchall()]
        
        # Get unique locations
        locations_query = """
        SELECT DISTINCT Location 
        FROM positions 
        WHERE Location IS NOT NULL AND Location != ''
        ORDER BY Location
        """
        locations = [row['Location'] for row in db.execute(locations_query).fetchall()]
        
        # Get unique regions
        regions_query = """
        SELECT DISTINCT Rg 
        FROM positions 
        WHERE Rg IS NOT NULL AND Rg != ''
        ORDER BY Rg
        """
        regions = [row['Rg'] for row in db.execute(regions_query).fetchall()]
        
        return jsonify({
            'divisions': divisions,
            'business_units': business_units,
            'locations': locations,
            'regions': regions
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 