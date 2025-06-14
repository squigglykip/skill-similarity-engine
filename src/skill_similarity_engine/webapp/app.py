"""
Flask Application for NAB Skills Intelligence Platform
======================================================

Modern Flask application using organised SQL queries and proper database schema.
Includes D3.js visualizations, career pathway analysis, and skills intelligence.

Features:
- Component library showcase with D3.js tree visualization
- Job search and similarity analysis
- Career pathway exploration with skills gap analysis
- Organised SQL query structure for maintainability
- NAB-style design system implementation
"""

import sqlite3
import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify, g, redirect

def create_app(config=None):
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'dev-key-change-in-production'
    if config:
        app.config.update(config)
    
    # Database configuration
    database_path = Path(__file__).parent.parent.parent.parent / 'models' / '2025-Q2' / 'business_context.sqlite'
    app.config['DATABASE_PATH'] = database_path
    
    def get_db():
        """Get database connection."""
        if 'db' not in g:
            g.db = sqlite3.connect(str(app.config['DATABASE_PATH']))
            g.db.row_factory = sqlite3.Row  # Enable dict-like access to rows
        return g.db

    def close_db(e=None):
        """Close database connection."""
        db = g.pop('db', None)
        if db is not None:
            db.close()

    @app.teardown_appcontext
    def close_db_handler(error):
        close_db()

    # Helper functions using organised SQL queries
    def get_sample_jobs(limit=20):
        """Get sample jobs for testing using organised SQL."""
        from .sql import queries
        db = get_db()
        
        # Use a simplified version for samples with correct column names
        cursor = db.execute("""
            SELECT JobProfileID as id, JobProfile as job_title, JobFamily as job_family, JobFamilyGroup as job_level 
            FROM jobs 
            ORDER BY JobProfile 
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()

    def search_jobs(query, limit=10):
        """Search jobs by name using organised SQL."""
        from .sql import queries
        db = get_db()
        
        search_query = queries.get('jobs', 'search_jobs')
        cursor = db.execute(search_query, (f'%{query}%', None, None))
        return cursor.fetchmany(limit)

    def get_job_similarities(job_id, limit=10):
        """Get similar jobs using organised SQL."""
        from .sql import queries
        db = get_db()
        
        similarities_query = queries.get('similarities', 'get_similar_jobs')
        cursor = db.execute(similarities_query, (job_id, 0.5, limit))
        return cursor.fetchall()

    # Routes
    @app.route('/')
    def index():
        """Homepage with overview and navigation."""
        from .sql import queries
        
        try:
            db = get_db()
            
            # Get basic stats for homepage
            stats_query = queries.get('metadata', 'get_database_stats')
            stats = db.execute(stats_query).fetchall()
            
            # Get job families overview
            families_query = queries.get('jobs', 'get_job_families')
            families = db.execute(families_query).fetchall()
            
            sample_jobs = get_sample_jobs(10)
            
            return render_template('index.html', 
                                 sample_jobs=sample_jobs,
                                 database_stats=stats, 
                                 job_families=families[:5])  # Top 5 families
        except Exception as e:
            print(f"Error loading homepage: {e}")
            sample_jobs = get_sample_jobs(10)
            return render_template('index.html', 
                                 sample_jobs=sample_jobs,
                                 database_stats=[], 
                                 job_families=[])

    @app.route('/components')
    def components():
        """Component library showcase page."""
        return render_template('components.html')

    @app.route('/job-search')
    def job_search():
        """Job search and exploration interface."""
        from .sql import queries
        
        try:
            db = get_db()
            
            # Get job families for filter dropdown
            families_query = queries.get('jobs', 'get_job_families')
            families = db.execute(families_query).fetchall()
            
            # Get sample jobs for initial display
            sample_jobs = get_sample_jobs(20)
            
            return render_template('job_search.html', 
                                 job_families=families,
                                 jobs=sample_jobs)
        except Exception as e:
            print(f"Error loading job search: {e}")
            sample_jobs = get_sample_jobs(20)
            return render_template('job_search.html', 
                                 job_families=[], 
                                 jobs=sample_jobs)

    @app.route('/similarity-results')
    def similarity_results():
        """Similarity results page."""
        job_id = request.args.get('job_id')
        
        if job_id:
            # Get specific job details
            from .sql import queries
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

    @app.route('/career-pathways')
    def career_pathways():
        """Career pathway exploration interface."""
        from .sql import queries
        
        try:
            db = get_db()
            
            # Get job families for starting point selection
            families_query = queries.get('jobs', 'get_job_families')
            families = db.execute(families_query).fetchall()
            
            sample_jobs = get_sample_jobs(10)
            
            return render_template('career_pathways.html', 
                                 job_families=families,
                                 jobs=sample_jobs)
        except Exception as e:
            print(f"Error loading career pathways: {e}")
            sample_jobs = get_sample_jobs(10)
            return render_template('career_pathways.html', 
                                 job_families=[],
                                 jobs=sample_jobs)

    # API endpoints for AJAX functionality
    @app.route('/api/search-jobs')
    def api_search_jobs():
        """API endpoint for job search autocomplete."""
        query = request.args.get('q', '')
        if not query:
            return jsonify([])
        
        jobs = search_jobs(query, 10)
        return jsonify([{
            'id': job['id'],
            'title': job['job_title'],
            'family': job['job_family'],
            'level': job['job_level']
        } for job in jobs])

    @app.route('/api/job-similarities/<job_id>')
    def api_job_similarities(job_id):
        """API endpoint for getting job similarities."""
        similarities = get_job_similarities(job_id, 15)
        return jsonify([{
            'job_id': sim['id'],
            'job_title': sim['job_title'],
            'job_family': sim['job_family'],
            'job_level': sim['job_level'],
            'similarity_score': round(sim['similarity_score'], 3),
            'similarity_category': sim['similarity_category']
        } for sim in similarities])

    @app.route('/api/career-pathway/<int:start_job_id>')
    def api_career_pathway(start_job_id):
        """API endpoint for career pathway analysis using organised SQL."""
        from .sql import queries
        
        min_similarity = float(request.args.get('min_similarity', 0.6))
        limit = int(request.args.get('limit', 10))
        
        try:
            db = get_db()
            
            # Get career progression options
            pathway_query = queries.get('career_pathways', 'get_career_progression_options')
            pathways = db.execute(pathway_query, (start_job_id, start_job_id, start_job_id, min_similarity, limit)).fetchall()
            
            return jsonify([{
                'target_job_id': pathway['target_job_id'],
                'target_job_title': pathway['target_job_title'],
                'target_family': pathway['target_family'],
                'target_level': pathway['target_level'],
                'similarity_score': round(pathway['similarity_score'], 3),
                'move_type': pathway['move_type'],
                'skills_to_develop': pathway['skills_to_develop'],
                'common_skills_count': pathway['common_skills_count']
            } for pathway in pathways])
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/skills-gap/<int:source_job_id>/<int:target_job_id>')
    def api_skills_gap(source_job_id, target_job_id):
        """API endpoint for skills gap analysis between two jobs."""
        from .sql import queries
        
        try:
            db = get_db()
            
            # Get skills gap analysis
            gap_query = queries.get('career_pathways', 'get_skills_gap_analysis')
            skills_gap = db.execute(gap_query, (source_job_id, target_job_id)).fetchall()
            
            # Organise skills by status
            skills_by_status = {
                'New Skill Required': [],
                'Transferable Skill': [],
                'Skill Development Required': [],
                'Skill Match': []
            }
            
            for skill in skills_gap:
                status = skill['skill_status']
                skills_by_status[status].append({
                    'name': skill['skill_name'],
                    'category': skill['skill_category'],
                    'subcategory': skill['skill_subcategory'],
                    'current_proficiency': skill['current_proficiency'],
                    'required_proficiency': skill['required_proficiency']
                })
            
            return jsonify({
                'source_job_id': source_job_id,
                'target_job_id': target_job_id,
                'skills_gap': skills_by_status,
                'summary': {
                    'new_skills_needed': len(skills_by_status['New Skill Required']),
                    'skills_to_develop': len(skills_by_status['Skill Development Required']),
                    'transferable_skills': len(skills_by_status['Transferable Skill']),
                    'matching_skills': len(skills_by_status['Skill Match'])
                }
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/d3-tree-data')
    def api_d3_tree_data():
        """API endpoint for job-centric D3.js tree using optimized pre-computed career pathways."""
        from .sql import queries
        
        # Get parameters
        job_ids = request.args.get('jobs', '').split(',') if request.args.get('jobs') else []
        job_ids = [job.strip() for job in job_ids if job.strip()]
        similarity_threshold = float(request.args.get('similarity', 0.2))  # Lower default since pre-computed
        max_depth = int(request.args.get('depth', 3))
        max_results = int(request.args.get('max_results', 10))  # Higher default - no performance penalty
        
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
            
            print(f"🌳 Building tree with {len(nodes)} nodes")
            
            for node in node_dict.values():
                parent_id = node.get('parent')
                if parent_id and parent_id in node_dict:
                    node_dict[parent_id]['children'].append(node)
                    print(f"   Added {node['id']} as child of {parent_id}")
                else:
                    roots.append(node)  # Root level nodes
                    print(f"   Added {node['id']} as root (parent: {parent_id})")
            
            # Debug: Count children per level
            def count_tree_levels(node, level=0):
                counts = {level: 1}
                for child in node.get('children', []):
                    child_counts = count_tree_levels(child, level + 1)
                    for l, c in child_counts.items():
                        counts[l] = counts.get(l, 0) + c
                return counts
            
            print(f"🌳 Found {len(roots)} root nodes")
            
            # If multiple roots, create a virtual root
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
                print(f"🌳 Virtual root tree levels: {tree_counts}")
                return virtual_root
            elif len(roots) == 1:
                tree_counts = count_tree_levels(roots[0])
                print(f"🌳 Single root tree levels: {tree_counts}")
                return roots[0]
            else:
                print("🌳 No valid root nodes found!")
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
            
            # Use optimized pre-computed career pathways query
            job_placeholders = ','.join(['?' for _ in job_ids])
            tree_query = queries.get('career_pathways', 'get_career_tree_fast')
            
            if not tree_query:
                # Fallback to original recursive query if career pathways not available
                tree_query = queries.get('d3_visualization', 'get_recursive_job_tree')
                if not tree_query:
                    raise ValueError("No tree query available")
            
            # Replace placeholder in query
            tree_query = tree_query.replace('{job_placeholders}', job_placeholders)
            
            # Execute with job IDs, similarity threshold, max depth, max results, and organizational filters
            params = job_ids + [similarity_threshold, max_depth, max_results,
                               division_filter, division_filter,  # Division filter (twice for SQL OR logic)
                               business_unit_filter, business_unit_filter,  # Business Unit filter
                               location_filter, location_filter,  # Location filter
                               region_filter, region_filter]  # Region filter
            
            # Build filter description for logging
            filters = []
            if division_filter: filters.append(f"division={division_filter}")
            if business_unit_filter: filters.append(f"business_unit={business_unit_filter}")
            if location_filter: filters.append(f"location={location_filter}")
            if region_filter: filters.append(f"region={region_filter}")
            filter_desc = f", filters=[{', '.join(filters)}]" if filters else ""
            
            print(f"🔍 SQL Parameters: jobs={job_ids}, similarity>={similarity_threshold}, max_depth<{max_depth}, max_results<={max_results}{filter_desc}")
            
            tree_data = db.execute(tree_query, params).fetchall()
            print(f"🗄️ SQL returned {len(tree_data)} rows")
            
            # Debug: Group by level to see distribution
            level_counts = {}
            for row in tree_data:
                level = row['level']
                level_counts[level] = level_counts.get(level, 0) + 1
            print(f"📊 SQL result levels: {level_counts}")
            
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
            
            # Debug: Show ALL nodes and their parent relationships
            print(f"🔍 ALL nodes from SQL:")
            for i, node in enumerate(nodes):
                print(f"   Node {i+1}: ID={node['id']}, Name={node['name'][:30]}..., Parent={node['parent']}, Level={node['level']}")
            
            # Debug: Check for orphaned nodes (parents that don't exist)
            all_ids = {node['id'] for node in nodes}
            orphaned = [node for node in nodes if node['parent'] and node['parent'] not in all_ids]
            if orphaned:
                print(f"⚠️  Found {len(orphaned)} orphaned nodes (parent doesn't exist):")
                for node in orphaned:
                    print(f"   Orphan: ID={node['id']}, Parent={node['parent']}, Name={node['name']}")
            else:
                print("✅ No orphaned nodes found")
            
            tree_root = build_tree(nodes)
            
            return jsonify({
                'success': True,
                'selected_jobs': job_ids,
                'similarity_threshold': similarity_threshold,
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

    @app.route('/api/search-all-jobs')
    def api_search_all_jobs():
        """API endpoint to search all jobs across families for multi-select dropdown."""
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 50))
        
        try:
            db = get_db()
            
            if query:
                # Search jobs by title or family
                search_query = """
                SELECT JobProfileID, JobProfile, JobFamily, JobFamilyGroup
                FROM jobs 
                WHERE JobProfile LIKE ? OR JobFamily LIKE ?
                ORDER BY 
                    CASE WHEN JobProfile LIKE ? THEN 1 ELSE 2 END,
                    JobProfile
                LIMIT ?
                """
                search_pattern = f'%{query}%'
                exact_pattern = f'{query}%'
                jobs = db.execute(search_query, (search_pattern, search_pattern, exact_pattern, limit)).fetchall()
            else:
                # Return popular/sample jobs when no query
                sample_query = """
                SELECT j.JobProfileID, j.JobProfile, j.JobFamily, j.JobFamilyGroup,
                       COUNT(js.job_to) as similarity_count
                FROM jobs j
                LEFT JOIN job_similarities js ON j.JobProfileID = js.job_from
                GROUP BY j.JobProfileID, j.JobProfile, j.JobFamily, j.JobFamilyGroup
                ORDER BY similarity_count DESC, j.JobProfile
                LIMIT ?
                """
                jobs = db.execute(sample_query, (limit,)).fetchall()
            
            return jsonify([{
                'id': job['JobProfileID'],
                'title': job['JobProfile'],
                'family': job['JobFamily'],
                'group': job['JobFamilyGroup'],
                'label': f"{job['JobProfile']} ({job['JobFamily']})"
            } for job in jobs])
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/d3-tree-filtered')
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

    @app.route('/api/jobs-in-family/<family>')
    def api_jobs_in_family(family):
        """API endpoint to get all jobs in a specific family for selection."""
        try:
            db = get_db()
            jobs_query = """
            SELECT JobProfileID, JobProfile, JobFamilyGroup 
            FROM jobs 
            WHERE JobFamily = ? 
            ORDER BY JobProfile
            """
            jobs = db.execute(jobs_query, (family,)).fetchall()
            
            return jsonify([{
                'id': job['JobProfileID'],
                'title': job['JobProfile'],
                'group': job['JobFamilyGroup']
            } for job in jobs])
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/job-families')
    def api_job_families():
        """API endpoint to get all job families using organised SQL."""
        from .sql import queries
        
        try:
            db = get_db()
            families_query = queries.get('jobs', 'get_job_families')
            families = db.execute(families_query).fetchall()
            
            return jsonify([{
                'name': family['job_family'],
                'job_count': family['job_count'],
                'high_similarity_jobs': family['high_similarity_jobs']
            } for family in families])
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/database-health')
    def api_database_health():
        """API endpoint for database health check and statistics."""
        from .sql import queries
        
        try:
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

    @app.route('/api/pathway-visualization-data')
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

    @app.route('/api/organizational-data')
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

    return app

if __name__ == '__main__':
    # Development server for direct running
    app = create_app()
    
    # Check if database exists
    if not app.config['DATABASE_PATH'].exists():
        print(f"⚠️  Database not found at: {app.config['DATABASE_PATH']}")
        print("   Run the CLI to generate business context database first.")
        exit(1)
    
    print(f"✅ Database found at: {app.config['DATABASE_PATH']}")
    print("🚀 Starting Flask development server...")
    print("   Available routes:")
    print("   - http://localhost:5000/ (Homepage)")
    print("   - http://localhost:5000/components (Component Library)")
    print("   - http://localhost:5000/job-search (Job Search)")
    print("   - http://localhost:5000/similarity-results (Similarity Results)")
    print("   - http://localhost:5000/career-pathways (Career Pathways)")
    
    app.run(debug=True, port=5000) 