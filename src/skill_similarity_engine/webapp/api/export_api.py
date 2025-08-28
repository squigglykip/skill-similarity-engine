"""
Export API Module for NAB Skills Intelligence Platform
====================================================

This module contains CSV export endpoints:
- /api/export/career-tree/<job_ids>
- /api/export/skills-analysis/<from_job_id>/<to_job_id>
- /api/export/workforce-analysis/<job_ids>

These endpoints provide comprehensive CSV exports for career tree data,
skills analysis reports, and workforce intelligence analysis.
"""

import io
import csv
from datetime import datetime
from flask import Blueprint, request, jsonify, url_for, g

# Create blueprint for export API
export_bp = Blueprint('export_api', __name__, url_prefix='/api/export')

def get_db():
    """Get database connection from Flask g object."""
    from flask import current_app
    import sqlite3
    if 'db' not in g:
        g.db = sqlite3.connect(str(current_app.config['DATABASE_PATH']))
        g.db.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return g.db

@export_bp.route('/career-tree/<job_ids>')
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
                j.JobFunction as category,
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
                j.JobFunction as category,
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
            j.JobSubFunction,
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
                row['JobSubFunction'] or 'N/A',
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
        
        return url_for('static', filename=filename, _external=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/skills-analysis/<from_job_id>/<to_job_id>')
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
        
        return url_for('static', filename=filename, _external=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/workforce-analysis/<job_ids>')
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
            j.JobFunction,
            j.JobSubFunction,
            p.position_number,
            p.position_name,
            p.employee_number,
            p.ORG_UNIT_NAME_2,
            p.ORG_UNIT_NAME_3,
            p.ORG_UNIT_NAME_4,
            p.Salary_Group,
            p.Employee_Group,
            p.Location,
            p.Rg as Region
        FROM core_job_architecture j
        LEFT JOIN core_workforce_current p ON j.JobProfileID = p.JobProfileID
        WHERE j.JobProfileID IN ({placeholders})
        ORDER BY j.JobProfile, p.ORG_UNIT_NAME_2, p.ORG_UNIT_NAME_3, p.ORG_UNIT_NAME_4, p.position_name
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
        unique_divisions = len(set(row['Division'] for row in workforce_data if row['Division']))
        unique_locations = len(set(row['Location'] for row in workforce_data if row['Location']))
        unique_business_units = len(set(row['Business_Unit'] for row in workforce_data if row['Business_Unit']))
        
        # Create CSV output
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header information
        writer.writerow(['NAB Workforce Intelligence Analysis Export'])
        writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['Job Profile IDs:', ', '.join(actual_job_ids)])
        writer.writerow([])
        
        # Write summary statistics
        writer.writerow(['SUMMARY STATISTICS'])
        writer.writerow(['Total Positions:', total_positions])
        writer.writerow(['Unique Divisions:', unique_divisions])
        writer.writerow(['Unique Locations:', unique_locations])
        writer.writerow(['Unique Business Units:', unique_business_units])
        writer.writerow(['Job Profiles Analyzed:', len(jobs_data)])
        writer.writerow([])
        
        # Write job profiles summary
        writer.writerow(['JOB PROFILES ANALYZED'])
        writer.writerow(['Job ID', 'Job Title', 'Function ID', 'Job Function'])
        
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
                        'positions': set(),
                        'employees': 0,
                        'business_units': set(),
                        'locations': set(),
                        'jobs': set()
                    }
                
                if row['Position Number']:
                    divisions[row['Division']]['positions'].add(row['Position Number'])
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
                len(data['positions']),
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
                        'positions': set(),
                        'employees': 0,
                        'divisions': set(),
                        'jobs': set()
                    }
                
                if row['Position Number']:
                    locations[row['Location']]['positions'].add(row['Position Number'])
                if row['Employee Number']:
                    locations[row['Location']]['employees'] += 1
                if row['Division']:
                    locations[row['Location']]['divisions'].add(row['Division'])
                locations[row['Location']]['jobs'].add(row['JobProfile'])
        
        writer.writerow(['Location', 'Positions', 'Employees', 'Divisions', 'Job Profiles'])
        
        for location, data in sorted(locations.items()):
            writer.writerow([
                location,
                len(data['positions']),
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
                        'positions': set(),
                        'employees': 0,
                        'divisions': set(),
                        'locations': set(),
                        'jobs': set()
                    }
                
                if row['Position Number']:
                    business_units[row['Business_Unit']]['positions'].add(row['Position Number'])
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
                len(data['positions']),
                data['employees'],
                len(data['divisions']),
                len(data['locations']),
                len(data['jobs'])
            ])
        
        # Create response
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'NAB_Workforce_Analysis_{timestamp}.csv'
        
        return url_for('static', filename=filename, _external=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 