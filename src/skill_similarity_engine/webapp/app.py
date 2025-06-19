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
import csv
import io
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, g, redirect, Response

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
            SELECT JobProfileID as id, JobProfile as job_title, JobFunction as job_function, JobFunctionID as job_function_id 
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

    def get_job_similarities_with_threshold(job_id, min_similarity, limit):
        """Get similar jobs using organised SQL with a specified similarity threshold."""
        from .sql import queries
        db = get_db()
        
        similarities_query = queries.get('similarities', 'get_similar_jobs_with_threshold')
        cursor = db.execute(similarities_query, (job_id, min_similarity, limit))
        return cursor.fetchall()

    # Routes
    @app.route('/')
    def index():
        """Homepage with overview and navigation."""
        from .sql import queries
        
        try:
            db = get_db()
            
            # Get platform metrics for dashboard
            platform_metrics_query = queries.get('metadata', 'get_platform_metrics')
            platform_metrics_raw = db.execute(platform_metrics_query).fetchall()
            
            # Convert platform metrics to dictionary for easier template access
            platform_metrics = {}
            for row in platform_metrics_raw:
                platform_metrics[row['metric']] = row['count']
            
            # Get top job families
            top_families_query = queries.get('metadata', 'get_top_job_families')
            top_families = db.execute(top_families_query).fetchall()
            
            # Get career pathway insights
            career_insights_query = queries.get('metadata', 'get_career_insights_summary')
            career_insights_raw = db.execute(career_insights_query).fetchall()
            
            # Convert career insights to dictionary
            career_insights = {}
            for row in career_insights_raw:
                career_insights[row['metric']] = row['value']
            
            # Get mobility hubs
            mobility_hubs_query = queries.get('metadata', 'get_mobility_hubs')
            mobility_hubs = db.execute(mobility_hubs_query).fetchall()
            
            # Get similarity distribution for mobility readiness analysis
            similarity_dist_query = queries.get('metadata', 'get_similarity_distribution')
            similarity_distribution = db.execute(similarity_dist_query).fetchall()
            
            # Get similarity statistics
            similarity_stats_query = queries.get('metadata', 'get_similarity_statistics')
            similarity_stats_raw = db.execute(similarity_stats_query).fetchall()
            
            # Convert similarity stats to dictionary
            similarity_stats = {}
            for row in similarity_stats_raw:
                similarity_stats[row['metric']] = row['value']
            
            # Get strategic recommendations for executive dashboard (lightweight queries)
            try:
                strategic_recs_query = queries.get('metadata', 'get_strategic_recommendations')
                strategic_recommendations = db.execute(strategic_recs_query).fetchall()
                
                cross_family_query = queries.get('metadata', 'get_cross_family_mobility_opportunities')
                cross_family_opportunities = db.execute(cross_family_query).fetchall()
                
                # Get cross-family similarity analysis
                cross_family_similarities_query = queries.get('similarities', 'get_cross_family_similarities')
                cross_family_similarities = db.execute(cross_family_similarities_query, (0.4, 12)).fetchall()
                
                cross_family_stats_query = queries.get('similarities', 'get_cross_family_stats')
                cross_family_stats_raw = db.execute(cross_family_stats_query).fetchall()
                
                skills_concentration_query = queries.get('metadata', 'get_skills_concentration_analysis')
                skills_concentration = db.execute(skills_concentration_query).fetchall()
            except Exception as e:
                print(f"Warning: Strategic recommendations query failed: {e}")
                strategic_recommendations = []
                skills_concentration = []
                cross_family_opportunities = []
                cross_family_similarities = []
                cross_family_stats_raw = None
            
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
            
            # Get job functions for filter dropdown
            functions_query = queries.get('jobs', 'get_job_functions')
            functions = db.execute(functions_query).fetchall()
            
            # Get sample jobs for initial display
            sample_jobs = get_sample_jobs(20)
            
            return render_template('job_explorer.html', 
                                 job_functions=functions,
                                 jobs=sample_jobs)
        except Exception as e:
            print(f"Error loading job search: {e}")
            sample_jobs = get_sample_jobs(20)
            return render_template('job_explorer.html', 
                                 job_functions=[], 
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
            'function': job['job_function'],
            'function_id': job['job_function_id']
        } for job in jobs])

    @app.route('/api/job-details/<job_id>')
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
            
            # Get position count for this job
            positions_query = """
            SELECT COUNT(*) as position_count
            FROM positions p
            WHERE p.JobProfileID = ?
            """
            position_count = db.execute(positions_query, (job_id,)).fetchone()
            
            # Get similarity count (career pathways)
            pathways_query = """
            SELECT COUNT(*) as pathway_count
            FROM career_pathways cp
            WHERE cp.source_job_id = ?
            """
            pathway_count = db.execute(pathways_query, (job_id,)).fetchone()
            
            return jsonify({
                'job': {
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
                },
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
                    'positions_count': position_count['position_count'] if position_count else 0,
                    'pathways_count': pathway_count['pathway_count'] if pathway_count else 0
                }
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/job-workforce/<job_id>')
    def api_job_workforce(job_id):
        """API endpoint for getting workforce context for a specific job."""
        try:
            db = get_db()
            
            # Get workforce distribution by division, business unit, and location
            workforce_query = """
            SELECT 
                p.Division,
                p.Business_Unit,
                p.Location,
                COUNT(*) as position_count
            FROM positions p
            WHERE p.JobProfileID = ?
            GROUP BY p.Division, p.Business_Unit, p.Location
            ORDER BY position_count DESC
            """
            workforce_data = db.execute(workforce_query, (job_id,)).fetchall()
            
            # Aggregate by division
            by_division = {}
            by_business_unit = {}
            by_location = {}
            total_positions = 0
            
            for row in workforce_data:
                total_positions += row['position_count']
                
                # By division
                div = row['Division'] or 'Other'
                by_division[div] = by_division.get(div, 0) + row['position_count']
                
                # By business unit
                bu = row['Business_Unit'] or 'Other'
                by_business_unit[bu] = by_business_unit.get(bu, 0) + row['position_count']
                
                # By location
                loc = row['Location'] or 'Other'
                by_location[loc] = by_location.get(loc, 0) + row['position_count']
            
            return jsonify({
                'total_positions': total_positions,
                'by_division': [{'division': k, 'count': v} for k, v in sorted(by_division.items(), key=lambda x: x[1], reverse=True)],
                'by_business_unit': [{'business_unit': k, 'count': v} for k, v in sorted(by_business_unit.items(), key=lambda x: x[1], reverse=True)],
                'by_location': [{'location': k, 'count': v} for k, v in sorted(by_location.items(), key=lambda x: x[1], reverse=True)]
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/job-similarities/<job_id>')
    def api_job_similarities(job_id):
        """API endpoint for getting job similarities."""
        min_similarity = float(request.args.get('min_similarity', 0.5))  # Default threshold
        limit = int(request.args.get('limit', 15))  # Default limit
        
        similarities = get_job_similarities_with_threshold(job_id, min_similarity, limit)
        return jsonify([{
            'job_id': sim['id'],
            'job_title': sim['job_title'],
            'job_function': sim['job_function'],
            'job_function_id': sim['job_function_id'],
            'similarity_score': round(sim['similarity_score'], 3),
            'similarity_category': sim['similarity_category']
        } for sim in similarities])

    @app.route('/api/career-pathways-distribution/<job_id>')
    def api_career_pathways_distribution(job_id):
        """API endpoint for getting the distribution of career pathway similarities from career_pathways table."""
        try:
            db = get_db()
            
            # Get all 12 career pathways for this job from the career_pathways table
            pathways_query = """
            SELECT cp.similarity_score, j.JobProfile as job_title, j.JobFunction as job_function
            FROM career_pathways cp
            JOIN jobs j ON cp.target_job_id = j.JobProfileID
            WHERE cp.source_job_id = ?
            ORDER BY cp.similarity_rank
            """
            pathways = db.execute(pathways_query, (job_id,)).fetchall()
            
            # Return the raw data - exactly 12 pathways for distribution analysis
            return jsonify([{
                'similarity_score': round(pathway['similarity_score'], 3),
                'job_title': pathway['job_title'],
                'job_function': pathway['job_function']
            } for pathway in pathways])
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

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
            
            # Build tree structure
            for node in node_dict.values():
                parent_id = node.get('parent')
                if parent_id and parent_id in node_dict:
                    node_dict[parent_id]['children'].append(node)
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
            # Updated parameter order for new SQL logic (filters applied at Level 1 only)
            params = job_ids + [similarity_threshold, max_depth, max_results,
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
            
            print(f"🔍 Query: jobs={job_ids}, similarity>={similarity_threshold}, depth<={max_depth}, max_results<={max_results}{filter_desc}")
            
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
                    print(f"⚠️  FILTER BUG DETECTED: Found {len(unexpected_roots)} unexpected root jobs:")
                    for job in unexpected_roots[:5]:  # Show first 5
                        print(f"   - {job}")
                    if len(unexpected_roots) > 5:
                        print(f"   ... and {len(unexpected_roots) - 5} more")
                    print("   🔧 This suggests organizational filters are being additive instead of restrictive")
                else:
                    print("✅ Organizational filters working correctly - no unexpected root jobs")
                
                # Additional validation: Check if Level 1 jobs match the organizational filter
                if division_filter:
                    level_1_jobs = [row for row in tree_data if row['level'] == 1]
                    print(f"🔍 Checking Level 1 jobs against Division filter '{division_filter}':")
                    for job in level_1_jobs[:5]:  # Show first 5
                        job_id = str(job['id'])
                        # Check if this job exists in the specified division
                        division_check = db.execute("SELECT Division FROM positions WHERE JobProfileID = ?", (job_id,)).fetchall()
                        divisions = [d['Division'] for d in division_check] if division_check else ['No positions found']
                        matches_filter = division_filter in divisions
                        status = "✅" if matches_filter else "❌"
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
                print(f"⚠️  Found {len(orphaned)} orphaned nodes - tree structure may be broken")
            
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
                # Search jobs by JobProfileID, title, or function
                search_query = """
                SELECT JobProfileID, JobProfile, JobFunctionID, JobFunction
                FROM jobs 
                WHERE JobProfileID LIKE ? OR JobProfile LIKE ? OR JobFunction LIKE ?
                ORDER BY 
                    CASE 
                        WHEN JobProfileID LIKE ? THEN 1 
                        WHEN JobProfile LIKE ? THEN 2 
                        ELSE 3 
                    END,
                    JobProfile
                LIMIT ?
                """
                search_pattern = f'%{query}%'
                exact_pattern = f'{query}%'
                jobs = db.execute(search_query, (search_pattern, search_pattern, search_pattern, exact_pattern, exact_pattern, limit)).fetchall()
            else:
                # Return popular/sample jobs when no query
                sample_query = """
                SELECT j.JobProfileID, j.JobProfile, j.JobFunctionID, j.JobFunction,
                       COUNT(js.job_to) as similarity_count
                FROM jobs j
                LEFT JOIN job_similarities js ON j.JobProfileID = js.job_from
                GROUP BY j.JobProfileID, j.JobProfile, j.JobFunctionID, j.JobFunction
                ORDER BY similarity_count DESC, j.JobProfile
                LIMIT ?
                """
                jobs = db.execute(sample_query, (limit,)).fetchall()
            
            return jsonify([{
                'id': job['JobProfileID'],
                'title': job['JobProfile'],
                'function': job['JobFunction'],
                'function_id': job['JobFunctionID'],
                'label': f"{job['JobProfile']} ({job['JobProfileID']})"
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

    @app.route('/api/jobs-in-function/<function>')
    def api_jobs_in_function(function):
        """API endpoint to get all jobs in a specific function for selection."""
        try:
            db = get_db()
            jobs_query = """
            SELECT JobProfileID, JobProfile, JobFunctionID 
            FROM jobs 
            WHERE JobFunction = ? 
            ORDER BY JobProfile
            """
            jobs = db.execute(jobs_query, (function,)).fetchall()
            
            return jsonify([{
                'id': job['JobProfileID'],
                'title': job['JobProfile'],
                'function_id': job['JobFunctionID']
            } for job in jobs])
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/job-functions')
    def api_job_functions():
        """API endpoint to get all job functions using organised SQL."""
        from .sql import queries
        
        try:
            db = get_db()
            functions_query = queries.get('jobs', 'get_job_functions')
            functions = db.execute(functions_query).fetchall()
            
            return jsonify([{
                'name': function['job_function'],
                'job_count': function['job_count'],
                'high_similarity_jobs': function['high_similarity_jobs']
            } for function in functions])
            
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

    @app.route('/api/skills-analysis/<from_job_id>/<to_job_id>')
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
                print(f"⚠️  Received D3 node IDs instead of JobProfileIDs: {from_job_id} → {to_job_id}")
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

    @app.route('/api/workforce-analysis/<job_ids>')
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
                print(f"⚠️  Filtering out D3 node IDs from workforce analysis: {node_ids}")
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
                COUNT(p."Position Number") as position_count,
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
                        'job_family': row['JobFamily'],
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

    # CSV Export Endpoints
    @app.route('/api/export/career-tree/<job_ids>')
    def export_career_tree_csv(job_ids):
        """Export comprehensive career tree data as CSV report."""
        try:
            db = get_db()
            
            # Parse job IDs
            job_id_list = [job_id.strip() for job_id in job_ids.split(',') if job_id.strip()]
            
            # Get tree data using the same logic as the API
            similarity_threshold = float(request.args.get('similarity', 0.2))
            max_depth = int(request.args.get('depth', 3))
            max_results = int(request.args.get('max_results', 6))
            
            placeholders = ','.join(['?' for _ in job_id_list])
            
            # Get comprehensive tree data
            tree_query = f"""
            WITH RECURSIVE tree_builder AS (
                -- Level 0: Root nodes (selected starting jobs)
                SELECT 
                    'root' as node_type,
                    j.JobProfileID as id,
                    j.JobProfile as name,
                    NULL as parent_id,
                    0 as level,
                    j.JobFamily as category,
                    1.0 as similarity_score,
                    'starting_role' as career_move_type,
                    0.0 as difficulty_score,
                    0 as shared_skills_count,
                    j.JobProfileID as root_job_id
                FROM jobs j
                WHERE j.JobProfileID IN ({placeholders})
                
                UNION ALL
                
                -- Recursive expansion: Get direct pathways from each node
                SELECT 
                    'similar_job' as node_type,
                    cp.target_job_id as id,
                    j.JobProfile as name,
                    cp.source_job_id as parent_id,
                    tb.level + 1 as level,
                    j.JobFamily as category,
                    cp.similarity_score,
                    cp.career_move_type,
                    cp.difficulty_score,
                    cp.shared_skills_count,
                    tb.root_job_id
                FROM tree_builder tb
                JOIN career_pathways cp ON tb.id = cp.source_job_id
                JOIN jobs j ON cp.target_job_id = j.JobProfileID
                WHERE tb.level < ? 
                  AND cp.similarity_score >= ?
                  AND cp.similarity_rank <= ?
            )
            SELECT 
                tb.*,
                j.JobFamilyGroup,
                CASE 
                    WHEN tb.similarity_score >= 0.8 THEN 'High Similarity'
                    WHEN tb.similarity_score >= 0.6 THEN 'Medium Similarity'
                    ELSE 'Lower Similarity'
                END as similarity_category
            FROM tree_builder tb
            LEFT JOIN jobs j ON tb.id = j.JobProfileID
            ORDER BY tb.root_job_id, tb.level, tb.similarity_score DESC
            """
            
            tree_data = db.execute(tree_query, job_id_list + [max_depth, similarity_threshold, max_results]).fetchall()
            
            # Create CSV output
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header information
            writer.writerow(['NAB Career Pathways Export'])
            writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow(['Starting Jobs:', ', '.join(job_id_list)])
            writer.writerow(['Similarity Threshold:', f'{similarity_threshold:.1%}'])
            writer.writerow(['Max Depth:', max_depth])
            writer.writerow(['Max Results per Level:', max_results])
            writer.writerow([])
            
            # Write summary statistics
            total_nodes = len(tree_data)
            levels = set(row['level'] for row in tree_data)
            families = set(row['category'] for row in tree_data if row['category'])
            
            writer.writerow(['SUMMARY STATISTICS'])
            writer.writerow(['Total Career Opportunities:', total_nodes])
            writer.writerow(['Career Levels Explored:', len(levels)])
            writer.writerow(['Job Families Represented:', len(families)])
            writer.writerow(['Job Families:', ', '.join(sorted(families))])
            writer.writerow([])
            
            # Write detailed tree data
            writer.writerow(['DETAILED CAREER PATHWAY DATA'])
            writer.writerow([
                'Root Job ID', 'Level', 'Job ID', 'Job Title', 'Job Family', 'Job Family Group',
                'Parent Job ID', 'Similarity Score', 'Similarity Category',
                'Career Move Type', 'Difficulty Score', 'Shared Skills Count', 'Node Type'
            ])
            
            for row in tree_data:
                writer.writerow([
                    row['root_job_id'],
                    row['level'],
                    row['id'],
                    row['name'],
                    row['category'],
                    row['JobFamilyGroup'] or 'N/A',
                    row['parent_id'] or 'N/A',
                    f"{row['similarity_score']:.3f}",
                    row['similarity_category'],
                    row['career_move_type'],
                    f"{row['difficulty_score']:.3f}",
                    row['shared_skills_count'],
                    row['node_type']
                ])
            
            # Group by level for level analysis
            writer.writerow([])
            writer.writerow(['LEVEL-BY-LEVEL ANALYSIS'])
            
            for level in sorted(levels):
                level_data = [row for row in tree_data if row['level'] == level]
                writer.writerow([])
                writer.writerow([f'LEVEL {level}', f'({len(level_data)} opportunities)'])
                writer.writerow(['Job ID', 'Job Title', 'Job Family', 'Similarity Score', 'Career Move Type'])
                
                for row in level_data:
                    writer.writerow([
                        row['id'],
                        row['name'],
                        row['category'],
                        f"{row['similarity_score']:.3f}",
                        row['career_move_type']
                    ])
            
            # Create response
            output.seek(0)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'NAB_Career_Pathways_{timestamp}.csv'
            
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename={filename}'}
            )
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/export/skills-analysis/<from_job_id>/<to_job_id>')
    def export_skills_analysis_csv(from_job_id, to_job_id):
        """Export comprehensive skills analysis as CSV report."""
        try:
            db = get_db()
            
            # Get job details
            job_query = "SELECT JobProfileID, JobProfile, JobFunctionID, JobFunction FROM jobs WHERE JobProfileID = ?"
            from_job = db.execute(job_query, (from_job_id,)).fetchone()
            to_job = db.execute(job_query, (to_job_id,)).fetchone()
            
            if not from_job or not to_job:
                return jsonify({'error': 'One or both jobs not found'}), 404
            
            # Get detailed skills analysis
            skills_query = """
            WITH job1_skills AS (
                SELECT js.Skill_ID, s.Skill_Name, s.Category, s.SkillType
                FROM job_skills js
                JOIN skills s ON js.Skill_ID = s.Skill_ID
                WHERE js.JobProfileID = ?
            ),
            job2_skills AS (
                SELECT js.Skill_ID, s.Skill_Name, s.Category, s.SkillType
                FROM job_skills js
                JOIN skills s ON js.Skill_ID = s.Skill_ID
                WHERE js.JobProfileID = ?
            )
            SELECT 
                'matched' as status,
                j1.Skill_ID,
                j1.Skill_Name,
                j1.Category,
                j1.SkillType
            FROM job1_skills j1
            INNER JOIN job2_skills j2 ON j1.Skill_ID = j2.Skill_ID
            
            UNION ALL
            
            SELECT 
                'develop' as status,
                j2.Skill_ID,
                j2.Skill_Name,
                j2.Category,
                j2.SkillType
            FROM job2_skills j2
            LEFT JOIN job1_skills j1 ON j2.Skill_ID = j1.Skill_ID
            WHERE j1.Skill_ID IS NULL
            
            ORDER BY 1, 5, 4, 3
            """
            
            skills_data = db.execute(skills_query, (from_job_id, to_job_id)).fetchall()
            
            # Calculate statistics
            matched_skills = [row for row in skills_data if row['status'] == 'matched']
            develop_skills = [row for row in skills_data if row['status'] == 'develop']
            
            # Group by skill type
            skilltype_matched = {}
            skilltype_develop = {}
            
            for skill in matched_skills:
                skilltype = skill['SkillType'] or 'Unspecified'
                skilltype_matched[skilltype] = skilltype_matched.get(skilltype, 0) + 1
            
            for skill in develop_skills:
                skilltype = skill['SkillType'] or 'Unspecified'
                skilltype_develop[skilltype] = skilltype_develop.get(skilltype, 0) + 1
            
            # Calculate transition difficulty
            total_target_skills = len(matched_skills) + len(develop_skills)
            if total_target_skills > 0:
                skill_overlap = len(matched_skills) / total_target_skills
                if skill_overlap >= 0.8:
                    difficulty = 'Easy'
                elif skill_overlap >= 0.6:
                    difficulty = 'Medium'
                else:
                    difficulty = 'Hard'
            else:
                difficulty = 'Unknown'
            
            # Create CSV output
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header information
            writer.writerow(['NAB Skills Transition Analysis Export'])
            writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])
            
            # Write transition summary
            writer.writerow(['TRANSITION SUMMARY'])
            writer.writerow(['From Job ID:', from_job_id])
            writer.writerow(['From Job Title:', from_job['JobProfile']])
            writer.writerow(['From Job Function:', from_job['JobFunction']])
            writer.writerow(['To Job ID:', to_job_id])
            writer.writerow(['To Job Title:', to_job['JobProfile']])
            writer.writerow(['To Job Function:', to_job['JobFunction']])
            writer.writerow([])
            
            # Write key metrics
            writer.writerow(['KEY METRICS'])
            writer.writerow(['Skills Already Matched:', len(matched_skills)])
            writer.writerow(['Skills to Develop:', len(develop_skills)])
            writer.writerow(['Total Target Skills:', total_target_skills])
            writer.writerow(['Skill Overlap Percentage:', f'{skill_overlap:.1%}' if total_target_skills > 0 else 'N/A'])
            writer.writerow(['Transition Difficulty:', difficulty])
            writer.writerow([])
            
            # Write skill type breakdown
            writer.writerow(['SKILL TYPE BREAKDOWN'])
            writer.writerow(['Skill Type', 'Matched', 'To Develop', 'Total Needed', 'Gap Percentage'])
            
            all_skilltypes = set(list(skilltype_matched.keys()) + list(skilltype_develop.keys()))
            for skilltype in sorted(all_skilltypes):
                matched_count = skilltype_matched.get(skilltype, 0)
                develop_count = skilltype_develop.get(skilltype, 0)
                total_needed = matched_count + develop_count
                gap_percentage = (develop_count / total_needed * 100) if total_needed > 0 else 0
                
                writer.writerow([
                    skilltype,
                    matched_count,
                    develop_count,
                    total_needed,
                    f'{gap_percentage:.1f}%'
                ])
            
            writer.writerow([])
            
            # Write detailed skills matched
            writer.writerow(['SKILLS ALREADY MATCHED'])
            writer.writerow(['Skill ID', 'Skill Name', 'Category', 'Skill Type'])
            
            for skill in matched_skills:
                writer.writerow([
                    skill['Skill_ID'],
                    skill['Skill_Name'],
                    skill['Category'],
                    skill['SkillType'] or 'Unspecified'
                ])
            
            writer.writerow([])
            
            # Write detailed skills to develop
            writer.writerow(['SKILLS TO DEVELOP'])
            writer.writerow(['Skill ID', 'Skill Name', 'Category', 'Skill Type'])
            
            for skill in develop_skills:
                writer.writerow([
                    skill['Skill_ID'],
                    skill['Skill_Name'],
                    skill['Category'],
                    skill['SkillType'] or 'Unspecified'
                ])
            
            # Group by category for category analysis
            writer.writerow([])
            writer.writerow(['SKILLS BY CATEGORY'])
            
            categories = set(skill['Category'] for skill in skills_data if skill['Category'])
            for category in sorted(categories):
                category_matched = [s for s in matched_skills if s['Category'] == category]
                category_develop = [s for s in develop_skills if s['Category'] == category]
                
                if category_matched or category_develop:
                    writer.writerow([])
                    writer.writerow([f'CATEGORY: {category}'])
                    writer.writerow(['Status', 'Skill Name', 'Skill Type'])
                    
                    for skill in category_matched:
                        writer.writerow(['Matched', skill['Skill_Name'], skill['SkillType'] or 'Unspecified'])
                    
                    for skill in category_develop:
                        writer.writerow(['To Develop', skill['Skill_Name'], skill['SkillType'] or 'Unspecified'])
            
            # Create response
            output.seek(0)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'NAB_Skills_Analysis_{from_job_id}_to_{to_job_id}_{timestamp}.csv'
            
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename={filename}'}
            )
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/export/workforce-analysis/<job_ids>')
    def export_workforce_analysis_csv(job_ids):
        """Export comprehensive workforce analysis as CSV report."""
        try:
            db = get_db()
            
            # Parse job IDs and filter out D3 node IDs
            job_id_list = job_ids.split(',')
            actual_job_ids = [job_id.strip() for job_id in job_id_list if job_id.strip() and not job_id.startswith('node_')]
            
            if not actual_job_ids:
                return jsonify({'error': 'No valid JobProfileIDs provided'}), 400
            
            placeholders = ','.join(['?' for _ in actual_job_ids])
            
            # Get comprehensive workforce data
            workforce_query = f"""
            SELECT 
                j.JobProfileID,
                j.JobProfile,
                j.JobFamily,
                j.JobFamilyGroup,
                p."Position Number",
                p."Position Name",
                p."Employee Number",
                p.Division,
                p.Business_Unit,
                p.Team,
                p."Salary Group",
                p."Employee Group",
                p.Location,
                p.Rg as Region
            FROM jobs j
            LEFT JOIN positions p ON j.JobProfileID = p.JobProfileID
            WHERE j.JobProfileID IN ({placeholders})
            ORDER BY j.JobProfile, p.Division, p.Business_Unit, p.Team, p."Position Name"
            """
            
            workforce_data = db.execute(workforce_query, actual_job_ids).fetchall()
            
            # Get job details
            jobs_query = f"""
            SELECT JobProfileID, JobProfile, JobFunctionID, JobFunction
            FROM jobs 
            WHERE JobProfileID IN ({placeholders})
            ORDER BY JobProfile
            """
            
            jobs_data = db.execute(jobs_query, actual_job_ids).fetchall()
            
            # Calculate summary statistics
            total_positions = len([row for row in workforce_data if row['Position Number']])
            total_employees = len([row for row in workforce_data if row['Employee Number']])
            unique_divisions = len(set(row['Division'] for row in workforce_data if row['Division']))
            unique_locations = len(set(row['Location'] for row in workforce_data if row['Location']))
            unique_business_units = len(set(row['Business_Unit'] for row in workforce_data if row['Business_Unit']))
            
            # Create CSV output
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header information
            writer.writerow(['NAB Workforce Intelligence Export'])
            writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow(['Job IDs Analyzed:', ', '.join(actual_job_ids)])
            writer.writerow([])
            
            # Write summary statistics
            writer.writerow(['WORKFORCE SUMMARY'])
            writer.writerow(['Total Positions:', total_positions])
            writer.writerow(['Total Employees:', total_employees])
            writer.writerow(['Divisions Represented:', unique_divisions])
            writer.writerow(['Business Units Represented:', unique_business_units])
            writer.writerow(['Locations Represented:', unique_locations])
            writer.writerow([])
            
            # Write job profiles summary
            writer.writerow(['JOB PROFILES ANALYZED'])
            writer.writerow(['Job ID', 'Job Title', 'Job Function ID', 'Job Function'])
            
            for job in jobs_data:
                writer.writerow([
                    job['JobProfileID'],
                    job['JobProfile'],
                    job['JobFunctionID'],
                    job['JobFunction'] or 'N/A'
                ])
            
            writer.writerow([])
            
            # Write detailed position data
            writer.writerow(['DETAILED POSITION DATA'])
            writer.writerow([
                'Job ID', 'Job Title', 'Job Function', 'Position Number', 'Position Name',
                'Employee Number', 'Division', 'Business Unit', 'Team', 'Salary Group',
                'Employee Group', 'Location', 'Region'
            ])
            
            for row in workforce_data:
                writer.writerow([
                    row['JobProfileID'],
                    row['JobProfile'],
                    row['JobFunction'],
                    row['Position Number'] or 'N/A',
                    row['Position Name'] or 'N/A',
                    row['Employee Number'] or 'N/A',
                    row['Division'] or 'N/A',
                    row['Business_Unit'] or 'N/A',
                    row['Team'] or 'N/A',
                    row['Salary Group'] or 'N/A',
                    row['Employee Group'] or 'N/A',
                    row['Location'] or 'N/A',
                    row['Region'] or 'N/A'
                ])
            
            # Write division analysis
            writer.writerow([])
            writer.writerow(['DIVISION ANALYSIS'])
            
            divisions = {}
            for row in workforce_data:
                if row['Division']:
                    if row['Division'] not in divisions:
                        divisions[row['Division']] = {
                            'positions': 0,
                            'employees': 0,
                            'business_units': set(),
                            'locations': set(),
                            'jobs': set()
                        }
                    
                    if row['Position Number']:
                        divisions[row['Division']]['positions'] += 1
                    if row['Employee Number']:
                        divisions[row['Division']]['employees'] += 1
                    if row['Business_Unit']:
                        divisions[row['Division']]['business_units'].add(row['Business_Unit'])
                    if row['Location']:
                        divisions[row['Division']]['locations'].add(row['Location'])
                    divisions[row['Division']]['jobs'].add(row['JobProfile'])
            
            writer.writerow(['Division', 'Positions', 'Employees', 'Business Units', 'Locations', 'Job Profiles'])
            
            for division, data in sorted(divisions.items()):
                writer.writerow([
                    division,
                    data['positions'],
                    data['employees'],
                    len(data['business_units']),
                    len(data['locations']),
                    len(data['jobs'])
                ])
            
            # Write location analysis
            writer.writerow([])
            writer.writerow(['LOCATION ANALYSIS'])
            
            locations = {}
            for row in workforce_data:
                if row['Location']:
                    if row['Location'] not in locations:
                        locations[row['Location']] = {
                            'positions': 0,
                            'employees': 0,
                            'divisions': set(),
                            'jobs': set()
                        }
                    
                    if row['Position Number']:
                        locations[row['Location']]['positions'] += 1
                    if row['Employee Number']:
                        locations[row['Location']]['employees'] += 1
                    if row['Division']:
                        locations[row['Location']]['divisions'].add(row['Division'])
                    locations[row['Location']]['jobs'].add(row['JobProfile'])
            
            writer.writerow(['Location', 'Positions', 'Employees', 'Divisions', 'Job Profiles'])
            
            for location, data in sorted(locations.items()):
                writer.writerow([
                    location,
                    data['positions'],
                    data['employees'],
                    len(data['divisions']),
                    len(data['jobs'])
                ])
            
            # Write business unit analysis
            writer.writerow([])
            writer.writerow(['BUSINESS UNIT ANALYSIS'])
            
            business_units = {}
            for row in workforce_data:
                if row['Business_Unit']:
                    if row['Business_Unit'] not in business_units:
                        business_units[row['Business_Unit']] = {
                            'positions': 0,
                            'employees': 0,
                            'divisions': set(),
                            'locations': set(),
                            'jobs': set()
                        }
                    
                    if row['Position Number']:
                        business_units[row['Business_Unit']]['positions'] += 1
                    if row['Employee Number']:
                        business_units[row['Business_Unit']]['employees'] += 1
                    if row['Division']:
                        business_units[row['Business_Unit']]['divisions'].add(row['Division'])
                    if row['Location']:
                        business_units[row['Business_Unit']]['locations'].add(row['Location'])
                    business_units[row['Business_Unit']]['jobs'].add(row['JobProfile'])
            
            writer.writerow(['Business Unit', 'Positions', 'Employees', 'Divisions', 'Locations', 'Job Profiles'])
            
            for bu, data in sorted(business_units.items()):
                writer.writerow([
                    bu,
                    data['positions'],
                    data['employees'],
                    len(data['divisions']),
                    len(data['locations']),
                    len(data['jobs'])
                ])
            
            # Create response
            output.seek(0)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'NAB_Workforce_Analysis_{timestamp}.csv'
            
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename={filename}'}
            )
            
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