"""
Job Intelligence API Module for NAB Skills Intelligence Platform
==============================================================

This module contains V2 job intelligence endpoints:
- /api/v2/job-defining-skills/<job_id>
- /api/v2/job-family-info/<job_id>
- /api/v2/job-skill-bundles/<job_id>
- /api/v2/job-intelligence-summary/<job_id>
- /api/v2/job-transition-recommendations/<job_id>
- /api/v2/job-families-overview
- /api/v2/job-market-intelligence/<job_id>

These endpoints provide sophisticated job intelligence analysis using
V2 analytics tables for defining skills, job families, and strategic insights.
"""

from flask import Blueprint, request, jsonify, g

# Create blueprint for job intelligence API
job_intelligence_bp = Blueprint('job_intelligence_api', __name__, url_prefix='/api/v2')

def get_db():
    """Get database connection from Flask g object."""
    from flask import current_app
    import sqlite3
    if 'db' not in g:
        g.db = sqlite3.connect(str(current_app.config['DATABASE_PATH']))
        g.db.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return g.db

@job_intelligence_bp.route('/job-defining-skills/<job_id>')
def api_job_defining_skills(job_id):
    """API endpoint for job defining skills analysis using V2 analytics."""
    try:
        db = get_db()
        
        # Import queries locally to avoid circular imports
        from ..sql import queries
        
        # Get defining skills analysis
        defining_skills_query = queries.get('job_intelligence', 'get_job_defining_skills')
        defining_skills = [dict(row) for row in db.execute(defining_skills_query, (job_id,)).fetchall()]
        
        if not defining_skills:
            return jsonify({
                'success': False,
                'error': f'No defining skills found for job {job_id}'
            }), 404
        
        # Categorize skills by importance
        critical_skills = [skill for skill in defining_skills if skill['skill_importance'] == 'Critical']
        important_skills = [skill for skill in defining_skills if skill['skill_importance'] == 'Important']
        supplementary_skills = [skill for skill in defining_skills if skill['skill_importance'] == 'Supplementary']
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job_id,
                'total_defining_skills': len(defining_skills),
                'critical_skills': critical_skills,
                'important_skills': important_skills,
                'supplementary_skills': supplementary_skills,
                'skills_by_category': {
                    'critical': len(critical_skills),
                    'important': len(important_skills),
                    'supplementary': len(supplementary_skills)
                },
                'all_defining_skills': defining_skills
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@job_intelligence_bp.route('/job-family-info/<job_id>')
def api_job_family_info(job_id):
    """API endpoint for job family information using DBSCAN clustering analysis."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get job family information
        family_query = queries.get('job_intelligence', 'get_job_family_info')
        family_info = db.execute(family_query, (job_id,)).fetchone()
        
        if not family_info:
            return jsonify({
                'success': False,
                'error': f'No job family information found for job {job_id}'
            }), 404
        
        family_data = dict(family_info)
        
        # Get similar jobs in the same family
        similar_jobs_query = queries.get('job_intelligence', 'get_similar_jobs_by_family')
        similar_jobs = [dict(row) for row in db.execute(similar_jobs_query, (job_id,)).fetchall()]
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job_id,
                'family_info': family_data,
                'similar_jobs_in_family': similar_jobs,
                'family_metrics': {
                    'cluster_size': family_data.get('cluster_size', 0),
                    'confidence': family_data.get('cluster_confidence', 0),
                    'business_value': family_data.get('business_value_score', 0),
                    'career_potential': family_data.get('career_pathway_potential', 'unknown'),
                    'skill_transferability': family_data.get('skill_transferability', 0)
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@job_intelligence_bp.route('/job-skill-bundles/<job_id>')
def api_job_skill_bundles(job_id):
    """API endpoint for skill bundles associated with a job."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get skill bundles analysis
        bundles_query = queries.get('job_intelligence', 'get_job_skill_bundles')
        skill_bundles = [dict(row) for row in db.execute(bundles_query, (job_id, job_id)).fetchall()]
        
        # Get specialization analysis
        specialization_query = queries.get('job_intelligence', 'get_job_specialization_analysis')
        specialized_skills = [dict(row) for row in db.execute(specialization_query, (job_id,)).fetchall()]
        
        # Group bundles by business value
        high_value_bundles = [bundle for bundle in skill_bundles if bundle.get('business_value_score', 0) > 0.7]
        medium_value_bundles = [bundle for bundle in skill_bundles if 0.4 <= bundle.get('business_value_score', 0) <= 0.7]
        low_value_bundles = [bundle for bundle in skill_bundles if bundle.get('business_value_score', 0) < 0.4]
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job_id,
                'skill_bundles': skill_bundles,
                'specialized_skills': specialized_skills,
                'bundle_analysis': {
                    'total_bundles': len(skill_bundles),
                    'high_value_bundles': len(high_value_bundles),
                    'medium_value_bundles': len(medium_value_bundles),
                    'low_value_bundles': len(low_value_bundles)
                },
                'specialization_analysis': {
                    'total_specialized': len(specialized_skills),
                    'ultra_rare': len([s for s in specialized_skills if s.get('specialization_category') == 'Ultra-Rare']),
                    'strategic_skills': len([s for s in specialized_skills if s.get('strategic_importance') == 'High'])
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@job_intelligence_bp.route('/job-intelligence-summary/<job_id>')
def api_job_intelligence_summary(job_id):
    """API endpoint for comprehensive job intelligence summary."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get comprehensive summary
        summary_query = queries.get('job_intelligence', 'get_job_intelligence_summary')
        summary = db.execute(summary_query, (job_id,)).fetchone()
        
        if not summary:
            return jsonify({
                'success': False,
                'error': f'No intelligence summary found for job {job_id}'
            }), 404
        
        summary_data = dict(summary)
        
        # Get market intelligence
        market_query = queries.get('job_intelligence', 'get_job_market_intelligence')
        market_data = db.execute(market_query, (job_id,)).fetchone()
        market_info = dict(market_data) if market_data else {}
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job_id,
                'job_profile': summary_data.get('JobProfile'),
                'job_function': summary_data.get('JobFunction'),
                'management_level': summary_data.get('ManagementLevel'),
                'intelligence_metrics': {
                    'defining_skills_count': summary_data.get('defining_skills_count', 0),
                    'rare_defining_skills': summary_data.get('rare_defining_skills', 0),
                    'skill_bundles_count': summary_data.get('skill_bundles_count', 0),
                    'specialized_skills_count': summary_data.get('specialized_skills_count', 0),
                    'ultra_rare_skills': summary_data.get('ultra_rare_skills', 0),
                    'total_skills_count': summary_data.get('total_skills_count', 0)
                },
                'family_context': {
                    'job_family': summary_data.get('job_family'),
                    'family_size': summary_data.get('family_size', 0),
                    'family_business_value': summary_data.get('family_business_value', 0),
                    'career_pathway_potential': summary_data.get('career_pathway_potential')
                },
                'market_intelligence': market_info,
                'strategic_insights': self._generate_strategic_insights(summary_data, market_info)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@job_intelligence_bp.route('/job-transition-recommendations/<job_id>')
def api_job_transition_recommendations(job_id):
    """API endpoint for intelligent job transition recommendations."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get transition recommendations
        recommendations_query = queries.get('job_intelligence', 'get_job_transition_recommendations')
        recommendations = [dict(row) for row in db.execute(recommendations_query, (job_id,)).fetchall()]
        
        if not recommendations:
            return jsonify({
                'success': True,
                'data': {
                    'job_id': job_id,
                    'recommendations': [],
                    'message': 'No transition recommendations found based on current analytics'
                }
            })
        
        # Categorize recommendations by score
        high_potential = [rec for rec in recommendations if rec.get('recommendation_score', 0) > 0.7]
        medium_potential = [rec for rec in recommendations if 0.4 <= rec.get('recommendation_score', 0) <= 0.7]
        low_potential = [rec for rec in recommendations if rec.get('recommendation_score', 0) < 0.4]
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job_id,
                'recommendations': recommendations,
                'recommendation_analysis': {
                    'total_recommendations': len(recommendations),
                    'high_potential': len(high_potential),
                    'medium_potential': len(medium_potential),
                    'low_potential': len(low_potential)
                },
                'top_recommendations': recommendations[:5],  # Top 5
                'categorized_recommendations': {
                    'high_potential': high_potential,
                    'medium_potential': medium_potential,
                    'low_potential': low_potential
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@job_intelligence_bp.route('/job-families-overview')
def api_job_families_overview():
    """API endpoint for overview of all job families with analytics."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get job families overview
        families_query = queries.get('job_intelligence', 'get_top_job_families')
        job_families = [dict(row) for row in db.execute(families_query).fetchall()]
        
        # Calculate summary statistics
        total_families = len(job_families)
        total_cluster_size = sum(family.get('cluster_size', 0) for family in job_families)
        avg_business_value = sum(family.get('business_value_score', 0) for family in job_families) / total_families if total_families > 0 else 0
        
        # Categorize by business value
        high_value_families = [f for f in job_families if f.get('business_value_score', 0) > 0.7]
        medium_value_families = [f for f in job_families if 0.4 <= f.get('business_value_score', 0) <= 0.7]
        
        return jsonify({
            'success': True,
            'data': {
                'job_families': job_families,
                'summary_statistics': {
                    'total_families': total_families,
                    'total_jobs_clustered': total_cluster_size,
                    'avg_business_value': round(avg_business_value, 3),
                    'high_value_families': len(high_value_families),
                    'medium_value_families': len(medium_value_families)
                },
                'high_value_families': high_value_families[:10],  # Top 10
                'family_insights': self._generate_family_insights(job_families)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _generate_strategic_insights(summary_data, market_data):
    """Generate strategic insights based on job intelligence data."""
    insights = []
    
    # Defining skills insight
    rare_defining = summary_data.get('rare_defining_skills', 0)
    total_defining = summary_data.get('defining_skills_count', 1)
    if rare_defining / total_defining > 0.3:
        insights.append({
            'type': 'risk',
            'category': 'Skills Concentration',
            'message': f'High concentration of rare defining skills ({rare_defining}/{total_defining}). Consider cross-training initiatives.',
            'priority': 'high'
        })
    
    # Family value insight
    family_value = summary_data.get('family_business_value', 0)
    if family_value > 0.8:
        insights.append({
            'type': 'opportunity',
            'category': 'Strategic Value',
            'message': 'Job belongs to high-value family cluster with strong business impact.',
            'priority': 'medium'
        })
    
    # Market movement insight
    inbound_movements = market_data.get('inbound_movements', 0)
    outbound_movements = market_data.get('outbound_movements', 0)
    if inbound_movements > outbound_movements * 2:
        insights.append({
            'type': 'trend',
            'category': 'Career Attractiveness',
            'message': 'Strong inbound career interest - consider as destination role for development programs.',
            'priority': 'medium'
        })
    
    return insights

def _generate_family_insights(job_families):
    """Generate insights about job family landscape."""
    insights = []
    
    # High business value families
    high_value_count = len([f for f in job_families if f.get('business_value_score', 0) > 0.8])
    if high_value_count > 0:
        insights.append({
            'type': 'strategic',
            'message': f'{high_value_count} job families identified with exceptional business value (>0.8)',
            'recommendation': 'Prioritize these families for talent development and retention programs'
        })
    
    # Large family clusters
    large_families = [f for f in job_families if f.get('cluster_size', 0) > 100]
    if large_families:
        insights.append({
            'type': 'scale',
            'message': f'{len(large_families)} large job families (>100 jobs) provide significant mobility opportunities',
            'recommendation': 'Leverage these families for cross-functional skill development'
        })
    
    return insights

@job_intelligence_bp.route('/job-family/<job_id>')
def api_job_family(job_id):
    """API endpoint for job family information."""
    try:
        db = get_db()
        
        # Get job family information
        query = """
        SELECT 
            job_profile_id,
            cluster_id,
            cluster_name,
            cluster_description,
            cluster_rationale,
            cluster_size,
            sample_jobs,
            sample_skills,
            cluster_confidence,
            silhouette_score,
            intra_cluster_similarity,
            inter_cluster_distance
        FROM analytics_job_families 
        WHERE job_profile_id = ?
        """
        
        result = db.execute(query, (job_id,)).fetchone()
        
        if not result:
            return jsonify({
                'success': False,
                'error': f'No job family found for job {job_id}'
            }), 404
        
        return jsonify(dict(result))
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@job_intelligence_bp.route('/skill-rarity-analysis/<job_id>')
def api_skill_rarity_analysis(job_id):
    """API endpoint for skill rarity analysis for a job."""
    try:
        db = get_db()
        
        # Get skills for the job and their rarity information
        query = """
        SELECT 
            sr.skill_id,
            sr.skill_name,
            sr.category,
            sr.subcategory,
            sr.skill_type,
            sr.prevalence_percentage,
            sr.rarity_category,
            sr.rarity_score
        FROM analytics_skill_rarity sr
        INNER JOIN core_job_skill_requirements jr ON sr.skill_id = jr.Skill_ID
        WHERE jr.JobProfileID = ?
        ORDER BY sr.rarity_score DESC
        """
        
        results = db.execute(query, (job_id,)).fetchall()
        skills = [dict(row) for row in results]
        
        # Categorize by rarity
        rare_skills = [s for s in skills if s['rarity_category'] == 'Rare']
        uncommon_skills = [s for s in skills if s['rarity_category'] == 'Uncommon']
        common_skills = [s for s in skills if s['rarity_category'] == 'Common']
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job_id,
                'total_skills': len(skills),
                'rare_skills': rare_skills,
                'uncommon_skills': uncommon_skills,
                'common_skills': common_skills,
                'rarity_distribution': {
                    'rare': len(rare_skills),
                    'uncommon': len(uncommon_skills),
                    'common': len(common_skills)
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@job_intelligence_bp.route('/specialized-skills/<job_id>')
def api_specialized_skills(job_id):
    """API endpoint for specialized skills analysis for a job."""
    try:
        db = get_db()
        
        # Get specialized skills for the job
        query = """
        SELECT 
            ss.skill_id,
            ss.skill_name,
            ss.category,
            ss.subcategory,
            ss.skill_type,
            ss.jobs_count,
            ss.prevalence_percent,
            ss.specialization_score,
            ss.specialization_reason,
            ss.specialization_category,
            ss.strategic_importance,
            ss.investment_recommendation
        FROM analytics_specialized_skills ss
        INNER JOIN core_job_skill_requirements jr ON ss.skill_id = jr.Skill_ID
        WHERE jr.JobProfileID = ?
        ORDER BY ss.specialization_score DESC
        """
        
        results = db.execute(query, (job_id,)).fetchall()
        specialized_skills = [dict(row) for row in results]
        
        return jsonify(specialized_skills)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500