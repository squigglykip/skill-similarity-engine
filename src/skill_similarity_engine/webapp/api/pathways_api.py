"""
Pathways API Module for NAB Skills Intelligence Platform
=======================================================

This module contains career pathways and visualization endpoints:
- /api/career-pathway/<start_job_id>
- /api/career-pathways-distribution/<job_id>
- /api/d3-tree-data
- /api/d3-tree-filtered
- /api/pathway-visualization-data

These endpoints provide sophisticated career pathway analysis, job progression trees,
and visualization data for D3.js-based interactive charts.
"""

from flask import Blueprint, request, jsonify, redirect, g
from ..sql import queries
from ...utils.display import DisplayFormat

# Create blueprint for pathways API
pathways_bp = Blueprint('pathways_api', __name__, url_prefix='/api')

def get_db():
    """Get database connection from Flask g object."""
    from flask import current_app
    import sqlite3
    if 'db' not in g:
        g.db = sqlite3.connect(str(current_app.config['DATABASE_PATH']))
        g.db.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return g.db

def get_display_manager():
    """Get display manager from Flask g object."""
    return g.get('display_manager')

def get_webapp_config():
    """Get webapp configuration manager."""
    try:
        from ...config.webapp_config_manager import get_webapp_config_manager
        return get_webapp_config_manager()
    except ImportError:
        # Fallback for testing or if config manager is not available
        class MockConfig:
            def get_similarity_threshold(self, key): return 0.6 if key == 'pathway' else 0.5
            def get_core_performance_config(self): return {'max_depth_default': 3, 'max_results_default': 10}
        return MockConfig()

@pathways_bp.route('/career-pathways-distribution/<job_id>')
def api_career_pathways_distribution(job_id):
    """API endpoint for getting the distribution of career pathway similarities from career_pathways table."""
    try:
        db = get_db()
        
        # Get career pathways using organized SQL
        pathways_query = queries.get('career_pathways', 'get_career_pathways_distribution_for_api')
        pathways = db.execute(pathways_query, (job_id,)).fetchall()
        
        # Return the raw data - exactly 12 pathways for distribution analysis
        display_manager = get_display_manager()
        result = []
        for pathway in pathways:
            pathway_data = {
                'similarity_score': round(pathway['similarity_score'], 3),
                'job_title': pathway['job_title'],
                'job_function': pathway['job_function']
            }
            # Add standardised display names (use job_title as id source)
            if display_manager:
                # We need to find the job_id for this job_title to get display names
                # For now, we'll add a simple display name that matches the job_title
                pathway_data['display_name_standard'] = pathway['job_title']
                pathway_data['display_name_search'] = pathway['job_title']
                pathway_data['display_name_dropdown'] = pathway['job_title']
                pathway_data['display_name_compact'] = pathway['job_title']
            result.append(pathway_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pathways_bp.route('/career-pathway/<start_job_id>')
def api_career_pathway(start_job_id):
    """API endpoint for career pathway analysis using organised SQL."""
    webapp_config = get_webapp_config()
    min_similarity = float(request.args.get('min_similarity', 0.6))
    limit = int(request.args.get('limit', 10))
    
    try:
        db = get_db()
        
        # Get career progression options using available query
        pathway_query = queries.get('career_pathways', 'get_direct_career_options')
        pathways = db.execute(pathway_query, (start_job_id, min_similarity, limit)).fetchall()
        
        # Add display names to pathway results
        display_manager = get_display_manager()
        result = []
        
        for pathway in pathways:
            pathway_data = {
                'target_job_id': pathway['target_job_id'],
                'target_job_title': pathway['target_job_name'],  # SQL returns target_job_name
                'target_function': pathway['target_function'],
                'similarity_score': round(pathway['similarity_score'], 3),
                'similarity_rank': pathway['similarity_rank'],
                'move_type': pathway['career_move_type'],  # SQL returns career_move_type
                'difficulty_score': pathway['difficulty_score'],
                'common_skills_count': pathway['shared_skills_count'],  # SQL returns shared_skills_count
                'position_count': pathway['position_count'],
                'divisions': pathway['divisions'],
                'business_units': pathway['business_units']
            }
            # Add standardised display names using target_job_id
            if display_manager:
                pathway_data['target_display_name_standard'] = display_manager.get_display_name(pathway['target_job_id'], DisplayFormat.STANDARD)
                pathway_data['target_display_name_search'] = display_manager.get_display_name(pathway['target_job_id'], DisplayFormat.SEARCH)
                pathway_data['target_display_name_dropdown'] = display_manager.get_display_name(pathway['target_job_id'], DisplayFormat.DROPDOWN)
                pathway_data['target_display_name_compact'] = display_manager.get_display_name(pathway['target_job_id'], DisplayFormat.COMPACT)
            
            result.append(pathway_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pathways_bp.route('/d3-tree-data')
def api_d3_tree_data():
    """API endpoint for job-centric D3.js tree using optimized pre-computed career pathways."""
    webapp_config = get_webapp_config()
    
    # Get parameters
    job_ids = request.args.get('jobs', '').split(',') if request.args.get('jobs') else []
    job_ids = [job.strip() for job in job_ids if job.strip()]
    similarity_threshold = float(request.args.get('similarity', webapp_config.get_similarity_threshold('pathway')))  # Configurable default 
    max_depth = int(request.args.get('depth', webapp_config.get_core_performance_config().get('max_depth_default', 3)))
    max_results = int(request.args.get('max_results', webapp_config.get_core_performance_config().get('max_results_default', 10)))  # Configurable default
    similarity_method = request.args.get('similarity_method', 'enhanced')  # 'enhanced' or 'literal'
    
    # Organizational filters (optional)
    division_filter = request.args.get('division', '').strip()
    business_unit_filter = request.args.get('business_unit', '').strip()
    location_filter = request.args.get('location', '').strip()
    region_filter = request.args.get('region', '').strip()
    
    def build_tree(nodes):
        if not nodes:
            return None
            
        node_dict = {node['id']: dict(node, children=[]) for node in nodes}
        roots = []
        
        # Build tree structure
        for node in node_dict.values():
            parent_id = node.get('parent')
            if parent_id and parent_id in node_dict:
                # Only add if not already in children (deduplicate multiple parent paths)
                parent_children = node_dict[parent_id]['children']
                if not any(child['id'] == node['id'] for child in parent_children):
                    parent_children.append(node)
            else:
                roots.append(node)  # Root level nodes
        
        # Count children per level for summary
        def count_tree_levels(node, level=0):
            counts = {level: 1}
            for child in node.get('children', []):
                child_counts = count_tree_levels(child, level + 1)
                for l, c in child_counts.items():
                    counts[l] = counts.get(l, 0) + c
            return counts
        
        # Create appropriate root structure
        if len(roots) > 1:
            virtual_root = {
                'id': 'root',
                'name': f'{len(roots)} Selected Jobs',
                'type': 'root',
                'parent': None,
                'level': -1,
                'similarity_score': 1.0,
                'category': 'Selected Jobs',
                'children': roots
            }
            tree_counts = count_tree_levels(virtual_root)
            print(f"🌳 Tree built: {len(nodes)} total nodes, levels: {tree_counts}")
            return virtual_root
        elif len(roots) == 1:
            tree_counts = count_tree_levels(roots[0])
            print(f"🌳 Tree built: {len(nodes)} total nodes, levels: {tree_counts}")
            return roots[0]
        else:
            print("❌ No valid root nodes found!")
            return None
    
    try:
        if not job_ids:
            return jsonify({
                'success': False,
                'error': 'No jobs selected',
                'tree': None,
                'total_nodes': 0
            })
        
        db = get_db()
        
        # Use recursive career pathways query that builds proper multi-level trees
        # Get the base recursive tree query
        tree_query = queries.get('career_pathways', 'get_career_tree_recursive')
        # Modify query based on similarity method
        if tree_query and similarity_method == 'literal':
            # Replace enhanced_similarity_score with similarity_score for literal comparison
            tree_query = tree_query.replace('enhanced_similarity_score', 'similarity_score')
        
        if not tree_query:
            # Fallback to older queries if recursive query not available
            tree_query = queries.get('career_pathways', 'get_career_tree_fast')
            if not tree_query:
                tree_query = queries.get('d3_visualization', 'get_recursive_job_tree')
                if not tree_query:
                    return jsonify({
                        'success': False,
                        'error': 'No tree query available - check SQL file structure',
                        'tree': None,
                        'total_nodes': 0
                    }), 500
        
        # For the simple query, we support single job only for now
        if len(job_ids) != 1:
            return jsonify({
                'success': False,
                'error': f'Simple tree query supports single job only, got {len(job_ids)} jobs',
                'tree': None,
                'total_nodes': 0
            }), 400
            
        job_id = job_ids[0]
        
        # Parameters: job_id (root), max_depth, similarity_threshold, max_results, + 8 org filters  
        params = [job_id, max_depth, similarity_threshold, max_results,
                  division_filter, division_filter,  # Division filter (check + value)
                  business_unit_filter, business_unit_filter,  # Business Unit filter (check + value)
                  location_filter, location_filter,  # Location filter (check + value)  
                  region_filter, region_filter]  # Region filter (check + value)
        
        # Build filter description for logging
        filters = []
        if division_filter: filters.append(f"division={division_filter}")
        if business_unit_filter: filters.append(f"business_unit={business_unit_filter}")
        if location_filter: filters.append(f"location={location_filter}")
        if region_filter: filters.append(f"region={region_filter}")
        filter_desc = f", filters=[{', '.join(filters)}]" if filters else ""
        
        print(f"📊 Query: jobs={job_ids}, similarity>={similarity_threshold}, depth<={max_depth}, max_results<={max_results}, method={similarity_method}{filter_desc}")
        
        tree_data = db.execute(tree_query, params).fetchall()
        
        # 🎯 ORGANIZATIONAL FILTER DEBUGGING
        if filters:
            # Count results by level to detect additive behavior
            level_counts = {}
            root_jobs = set(job_ids)
            unexpected_roots = []
            
            for row in tree_data:
                level = row['level']
                level_counts[level] = level_counts.get(level, 0) + 1
                
                # Check for unexpected root-level jobs (level 0 but not in our selected jobs)
                if level == 0 and str(row['id']) not in root_jobs:
                    unexpected_roots.append(f"{row['id']}:{row['name'][:30]}")
            
            print(f"📊 Results by level: {level_counts}")
            
            if unexpected_roots:
                print(f"⚠️ Found {len(unexpected_roots)} unexpected root jobs:")
                for job in unexpected_roots[:5]:  # Show first 5
                    print(f"   - {job}")
                if len(unexpected_roots) > 5:
                    print(f"   ... and {len(unexpected_roots) - 5} more")
                print("   📊 This suggests organizational filters are being additive instead of restrictive")
            else:
                print("[OK] Organizational filters working correctly - no unexpected root jobs")
            
                            # Additional validation: Check if Level 1 jobs match the organizational filter
            if division_filter:
                level_1_jobs = [row for row in tree_data if row['level'] == 1]
                print(f"📊 Checking Level 1 jobs against Division filter '{division_filter}':")
                division_check_query = queries.get('career_pathways', 'check_job_division_filter')
                for job in level_1_jobs[:5]:  # Show first 5
                    job_id = str(job['id'])
                    # Check if this job exists in the specified division using organized SQL
                    division_check = db.execute(division_check_query, (job_id,)).fetchall()
                    divisions = [d['Division'] for d in division_check] if division_check else ['No positions found']
                    matches_filter = division_filter in divisions
                    status = "[OK]" if matches_filter else "[X]"
                    print(f"   {status} {job_id}: {job['name'][:40]} -> Divisions: {divisions}")
                if len(level_1_jobs) > 5:
                    print(f"   ... and {len(level_1_jobs) - 5} more Level 1 jobs")
        else:
            # Simple count when no filters
            level_counts = {}
            for row in tree_data:
                level = row['level']
                level_counts[level] = level_counts.get(level, 0) + 1
            print(f"📊 Results by level: {level_counts}")
        
        # Convert to D3.js hierarchical format - use row index for unique IDs
        nodes = []
        for i, row in enumerate(tree_data):
            node = {
                'id': f"node_{i}",  # Simple unique identifier using row index
                'job_id': str(row['id']),  # Original job ID for display
                'name': row['name'],
                'parent': None,  # Will be set below based on parent relationships
                'type': row['node_type'],
                'level': row['level'],
                'children_count': row['children_count'],
                'similarity_score': float(row['similarity_score']) if row['similarity_score'] else 0,
                'category': row['category']
            }
            nodes.append(node)
        
        # Now set parent relationships based on the actual data structure
        for i, node in enumerate(nodes):
            row = tree_data[i]
            if row['parent_id'] and row['level'] > 0:
                # Find the parent node - look for a node at level-1 with matching job_id
                for j, potential_parent in enumerate(nodes):
                    if (potential_parent['job_id'] == str(row['parent_id']) and 
                        potential_parent['level'] == row['level'] - 1):
                        node['parent'] = potential_parent['id']
                        break
        
        # Quick validation: Check for orphaned nodes (parents that don't exist)
        all_ids = {node['id'] for node in nodes}
        orphaned = [node for node in nodes if node['parent'] and node['parent'] not in all_ids]
        
        # Simple validation: Remove any orphaned nodes (those without valid parents)
        # With the new SQL logic, this should be rare since filtering happens at SQL level
        nodes_without_parents = [node for node in nodes if node['level'] > 0 and not node['parent']]
        
        if orphaned:
            print(f"⚠️ Found {len(orphaned)} orphaned nodes - tree structure may be broken")
        
        if nodes_without_parents:
            # Clean approach: Simply remove orphaned nodes instead of trying to reconnect them
            # This ensures organizational filters work as intended (restrictive, not additive)
            orphaned_job_ids = {node['job_id'] for node in nodes_without_parents}
            nodes_before = len(nodes)
            nodes = [node for node in nodes if node['job_id'] not in orphaned_job_ids]
            nodes_after = len(nodes)
            
            print(f"🧹 Cleaned up: Removed {nodes_before - nodes_after} orphaned nodes")
            print(f"   Final result: {nodes_after} nodes (organizational filters applied cleanly)")
        
        tree_root = build_tree(nodes)
        
        return jsonify({
            'success': True,
            'selected_jobs': job_ids,
            'similarity_threshold': similarity_threshold,
            'similarity_method': similarity_method,
            'max_depth': max_depth,
            'max_results': max_results,
            'tree': tree_root,
            'total_nodes': len(nodes)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'selected_jobs': job_ids,
            'tree': None,
            'total_nodes': 0
        }), 500

@pathways_bp.route('/d3-tree-filtered')
def api_d3_tree_filtered():
    """Legacy endpoint - redirect to new job-centric API."""
    family = request.args.get('family', '')
    selected_jobs = request.args.get('jobs', '').split(',') if request.args.get('jobs') else []
    
    # Redirect to new API
    if selected_jobs:
        return redirect(f'/api/d3-tree-data?jobs={",".join(selected_jobs)}&similarity=0.7&depth=3')
    else:
        return jsonify({
            'success': False,
            'error': 'No jobs selected',
            'tree': None
        })

@pathways_bp.route('/pathway-visualization-data')
def api_pathway_visualization_data():
    """API endpoint for getting sample data for pathway visualizations."""
    return jsonify({
        'sample_pathways': [
            {
                'id': 'ra_to_ds',
                'name': 'Risk Analyst → Data Scientist',
                'steps': [
                    {'job': 'Risk Analyst', 'family': 'Risk & Compliance', 'similarity': 100, 'timeframe': 'Current'},
                    {'job': 'Business Analyst', 'family': 'Customer Service & Sales', 'similarity': 78, 'timeframe': '6-12 months'},
                    {'job': 'Data Analyst', 'family': 'Technology', 'similarity': 85, 'timeframe': '12-18 months'},
                    {'job': 'Data Scientist', 'family': 'Technology', 'similarity': 92, 'timeframe': 'Target'}
                ],
                'skills': {
                    'transferable': ['Statistical Analysis', 'Risk Assessment', 'Excel', 'Problem Solving'],
                    'develop': ['Python', 'Machine Learning', 'SQL', 'Data Visualization'],
                    'advanced': ['Deep Learning', 'Cloud Platforms', 'AI Ethics']
                }
            }
        ],
        'network_data': {
            'nodes': [
                {'id': 'RA', 'label': 'Risk Analyst', 'family': 'Risk & Compliance', 'type': 'current'},
                {'id': 'BA', 'label': 'Business Analyst', 'family': 'Customer Service & Sales', 'type': 'similar'},
                {'id': 'CO', 'label': 'Compliance Officer', 'family': 'Risk & Compliance', 'type': 'similar'},
                {'id': 'DA', 'label': 'Data Analyst', 'family': 'Technology', 'type': 'similar'},
                {'id': 'DS', 'label': 'Data Scientist', 'family': 'Technology', 'type': 'target'}
            ],
            'edges': [
                {'from': 'RA', 'to': 'BA', 'similarity': 0.78},
                {'from': 'RA', 'to': 'CO', 'similarity': 0.65},
                {'from': 'RA', 'to': 'DA', 'similarity': 0.71},
                {'from': 'RA', 'to': 'DS', 'similarity': 0.54},
                {'from': 'BA', 'to': 'DA', 'similarity': 0.82},
                {'from': 'DA', 'to': 'DS', 'similarity': 0.92}
            ]
        }
    })