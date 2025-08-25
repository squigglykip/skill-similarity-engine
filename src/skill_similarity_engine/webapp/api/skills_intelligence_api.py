"""
Skills Intelligence API Module for NAB Skills Intelligence Platform
==================================================================

This module contains V2 skills intelligence endpoints:
- /api/v2/skill-analysis/<skill_id>
- /api/v2/skill-bundle-analysis/<bundle_id>
- /api/v2/skills-in-bundle/<bundle_id>
- /api/v2/rare-skills-analysis
- /api/v2/skill-trends-analysis
- /api/v2/skill-bundles-overview
- /api/v2/skills-by-category
- /api/v2/skill-investment-recommendations
- /api/v2/skills-search

These endpoints provide sophisticated skills intelligence analysis using
V2 analytics tables for rarity, demand trends, bundles, and specialization.
"""

from flask import Blueprint, request, jsonify, g

# Create blueprint for skills intelligence API
skills_intelligence_bp = Blueprint('skills_intelligence_api', __name__, url_prefix='/api/v2')

def get_db():
    """Get database connection from Flask g object."""
    from flask import current_app
    import sqlite3
    if 'db' not in g:
        g.db = sqlite3.connect(str(current_app.config['DATABASE_PATH']))
        g.db.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return g.db

@skills_intelligence_bp.route('/skill-analysis/<skill_id>')
def api_skill_analysis(skill_id):
    """API endpoint for comprehensive skill analysis using V2 analytics."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get comprehensive skill analysis
        analysis_query = queries.get('skill_intelligence', 'get_skill_comprehensive_analysis')
        skill_analysis = db.execute(analysis_query, (skill_id,)).fetchone()
        
        if not skill_analysis:
            return jsonify({
                'success': False,
                'error': f'No analysis found for skill {skill_id}'
            }), 404
        
        skill_data = dict(skill_analysis)
        
        return jsonify({
            'success': True,
            'data': {
                'skill_id': skill_id,
                'skill_info': {
                    'skill_name': skill_data.get('Skill_Name'),
                    'category': skill_data.get('Category'),
                    'subcategory': skill_data.get('Subcategory'),
                    'skill_type': skill_data.get('SkillType')
                },
                'rarity_analysis': {
                    'prevalence_percentage': skill_data.get('prevalence_percentage'),
                    'rarity_category': skill_data.get('rarity_category'),
                    'rarity_score': skill_data.get('rarity_score'),
                    'total_profiles_with_skill': skill_data.get('total_profiles_with_skill'),
                    'is_defining_skill': bool(skill_data.get('is_defining_skill')),
                    'defining_for_jobs_count': skill_data.get('defining_for_jobs_count', 0)
                },
                'demand_trends': {
                    'velocity_category': skill_data.get('velocity_category'),
                    'trend_direction': skill_data.get('trend_direction'),
                    'trend_strength': skill_data.get('trend_strength'),
                    'current_prevalence_percent': skill_data.get('current_prevalence_percent'),
                    'short_term_cagr': skill_data.get('short_term_cagr'),
                    'medium_term_cagr': skill_data.get('medium_term_cagr'),
                    'long_term_cagr': skill_data.get('long_term_cagr')
                },
                'bundle_context': {
                    'bundle_name': skill_data.get('bundle_name'),
                    'bundle_description': skill_data.get('bundle_description'),
                    'bundle_size': skill_data.get('bundle_size'),
                    'specialization_area': skill_data.get('specialization_area'),
                    'bundle_business_value': skill_data.get('bundle_business_value'),
                    'training_feasibility': skill_data.get('training_feasibility'),
                    'bundle_market_demand': skill_data.get('bundle_market_demand')
                },
                'specialization_analysis': {
                    'specialization_score': skill_data.get('specialization_score'),
                    'specialization_category': skill_data.get('specialization_category'),
                    'strategic_importance': skill_data.get('strategic_importance'),
                    'skill_lifecycle_stage': skill_data.get('skill_lifecycle_stage'),
                    'investment_recommendation': skill_data.get('investment_recommendation'),
                    'external_market_demand': skill_data.get('external_market_demand')
                },
                'strategic_insights': self._generate_skill_insights(skill_data)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@skills_intelligence_bp.route('/skill-bundle-analysis/<int:bundle_id>')
def api_skill_bundle_analysis(bundle_id):
    """API endpoint for detailed skill bundle analysis."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get bundle analysis
        bundle_query = queries.get('skill_intelligence', 'get_skill_bundle_analysis')
        bundle_analysis = db.execute(bundle_query, (bundle_id,)).fetchone()
        
        if not bundle_analysis:
            return jsonify({
                'success': False,
                'error': f'No bundle analysis found for bundle {bundle_id}'
            }), 404
        
        bundle_data = dict(bundle_analysis)
        
        return jsonify({
            'success': True,
            'data': {
                'bundle_id': bundle_id,
                'bundle_info': {
                    'bundle_name': bundle_data.get('bundle_name'),
                    'bundle_description': bundle_data.get('bundle_description'),
                    'bundle_rationale': bundle_data.get('bundle_rationale'),
                    'bundle_size': bundle_data.get('bundle_size'),
                    'dominant_category': bundle_data.get('dominant_category'),
                    'specialization_area': bundle_data.get('specialization_area')
                },
                'quality_metrics': {
                    'category_purity': bundle_data.get('category_purity'),
                    'business_value_score': bundle_data.get('business_value_score'),
                    'skill_complementarity': bundle_data.get('skill_complementarity'),
                    'actual_skills_count': bundle_data.get('actual_skills_count'),
                    'avg_skill_rarity': bundle_data.get('avg_skill_rarity'),
                    'rare_skills_in_bundle': bundle_data.get('rare_skills_in_bundle')
                },
                'application_context': {
                    'application_level': bundle_data.get('application_level'),
                    'training_feasibility': bundle_data.get('training_feasibility'),
                    'market_demand_level': bundle_data.get('market_demand_level'),
                    'typical_career_stage': bundle_data.get('typical_career_stage'),
                    'skill_acquisition_difficulty': bundle_data.get('skill_acquisition_difficulty')
                },
                'usage_metrics': {
                    'jobs_using_bundle_skills': bundle_data.get('jobs_using_bundle_skills', 0)
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@skills_intelligence_bp.route('/skills-in-bundle/<int:bundle_id>')
def api_skills_in_bundle(bundle_id):
    """API endpoint for skills within a specific bundle."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get skills in bundle
        skills_query = queries.get('skill_intelligence', 'get_skills_in_bundle')
        skills = [dict(row) for row in db.execute(skills_query, (bundle_id,)).fetchall()]
        
        if not skills:
            return jsonify({
                'success': False,
                'error': f'No skills found for bundle {bundle_id}'
            }), 404
        
        # Analyze skills distribution
        rare_skills = [s for s in skills if s.get('rarity_category') in ['Rare', 'Very Rare']]
        defining_skills = [s for s in skills if s.get('jobs_where_defining', 0) > 0]
        trending_skills = [s for s in skills if s.get('velocity_category') == 'growing']
        
        return jsonify({
            'success': True,
            'data': {
                'bundle_id': bundle_id,
                'skills': skills,
                'skills_analysis': {
                    'total_skills': len(skills),
                    'rare_skills_count': len(rare_skills),
                    'defining_skills_count': len(defining_skills),
                    'trending_skills_count': len(trending_skills),
                    'avg_jobs_per_skill': sum(s.get('jobs_requiring_skill', 0) for s in skills) / len(skills) if skills else 0
                },
                'skill_categories': {
                    'rare_skills': rare_skills,
                    'defining_skills': defining_skills,
                    'trending_skills': trending_skills
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@skills_intelligence_bp.route('/rare-skills-analysis')
def api_rare_skills_analysis():
    """API endpoint for rare and specialized skills analysis."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get rare skills analysis
        rare_skills_query = queries.get('skill_intelligence', 'get_rare_skills_analysis')
        rare_skills = [dict(row) for row in db.execute(rare_skills_query).fetchall()]
        
        # Categorize by specialization
        ultra_rare = [s for s in rare_skills if s.get('specialization_category') == 'Ultra-Rare']
        rare = [s for s in rare_skills if s.get('rarity_category') == 'Rare']
        very_rare = [s for s in rare_skills if s.get('rarity_category') == 'Very Rare']
        
        # Strategic importance analysis
        high_strategic = [s for s in rare_skills if s.get('strategic_importance') == 'High']
        growing_rare = [s for s in rare_skills if s.get('velocity_category') == 'growing']
        declining_rare = [s for s in rare_skills if s.get('velocity_category') == 'declining']
        
        return jsonify({
            'success': True,
            'data': {
                'rare_skills': rare_skills,
                'rarity_distribution': {
                    'ultra_rare': len(ultra_rare),
                    'rare': len(rare),
                    'very_rare': len(very_rare),
                    'total_rare_skills': len(rare_skills)
                },
                'strategic_analysis': {
                    'high_strategic_importance': len(high_strategic),
                    'growing_rare_skills': len(growing_rare),
                    'declining_rare_skills': len(declining_rare)
                },
                'top_strategic_rare_skills': [s for s in rare_skills if s.get('strategic_importance') == 'High'][:10],
                'concentration_risks': self._analyze_concentration_risks(rare_skills)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@skills_intelligence_bp.route('/skill-trends-analysis')
def api_skill_trends_analysis():
    """API endpoint for skill demand trends analysis."""
    try:
        velocity_category = request.args.get('velocity', 'growing')  # growing, declining, stable
        
        db = get_db()
        
        from ..sql import queries
        
        # Get trending skills
        trends_query = queries.get('skill_intelligence', 'get_skill_demand_trends_analysis')
        trending_skills = [dict(row) for row in db.execute(trends_query, (velocity_category,)).fetchall()]
        
        # Calculate trend metrics
        total_skills = len(trending_skills)
        avg_cagr = sum(s.get('short_term_cagr', 0) for s in trending_skills) / total_skills if total_skills > 0 else 0
        rare_trending = [s for s in trending_skills if s.get('rarity_category') in ['Rare', 'Very Rare']]
        strategic_trending = [s for s in trending_skills if s.get('strategic_importance') == 'High']
        
        return jsonify({
            'success': True,
            'data': {
                'velocity_category': velocity_category,
                'trending_skills': trending_skills,
                'trend_metrics': {
                    'total_skills': total_skills,
                    'average_short_term_cagr': round(avg_cagr, 3),
                    'rare_skills_trending': len(rare_trending),
                    'strategic_skills_trending': len(strategic_trending)
                },
                'top_performers': trending_skills[:15] if trending_skills else [],
                'rare_trending_skills': rare_trending,
                'strategic_trending_skills': strategic_trending,
                'trend_insights': self._generate_trend_insights(trending_skills, velocity_category)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@skills_intelligence_bp.route('/skill-bundles-overview')
def api_skill_bundles_overview():
    """API endpoint for overview of all skill bundles."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get bundles overview
        bundles_query = queries.get('skill_intelligence', 'get_skill_bundles_overview')
        bundles = [dict(row) for row in db.execute(bundles_query).fetchall()]
        
        # Analyze bundle landscape
        high_value_bundles = [b for b in bundles if b.get('business_value_score', 0) > 0.7]
        large_bundles = [b for b in bundles if b.get('actual_skills_count', 0) > 50]
        growing_bundles = [b for b in bundles if b.get('growing_skills', 0) > b.get('declining_skills', 0)]
        
        return jsonify({
            'success': True,
            'data': {
                'skill_bundles': bundles,
                'bundle_landscape': {
                    'total_bundles': len(bundles),
                    'high_value_bundles': len(high_value_bundles),
                    'large_bundles': len(large_bundles),
                    'growing_bundles': len(growing_bundles),
                    'avg_bundle_size': sum(b.get('actual_skills_count', 0) for b in bundles) / len(bundles) if bundles else 0
                },
                'strategic_bundles': high_value_bundles[:10],
                'bundle_insights': self._generate_bundle_insights(bundles)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@skills_intelligence_bp.route('/skills-by-category')
def api_skills_by_category():
    """API endpoint for skills analysis grouped by category."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get category analysis
        category_query = queries.get('skill_intelligence', 'get_skills_by_category_analysis')
        categories = [dict(row) for row in db.execute(category_query).fetchall()]
        
        # Calculate category insights
        top_categories = sorted(categories, key=lambda x: x.get('jobs_using_category', 0), reverse=True)[:10]
        rarest_categories = sorted(categories, key=lambda x: x.get('avg_rarity_score', 0), reverse=True)[:5]
        growing_categories = [c for c in categories if c.get('growing_skills', 0) > c.get('declining_skills', 0)]
        
        return jsonify({
            'success': True,
            'data': {
                'skill_categories': categories,
                'category_insights': {
                    'total_categories': len(categories),
                    'top_categories_by_usage': top_categories,
                    'rarest_categories': rarest_categories,
                    'growing_categories': len(growing_categories)
                },
                'category_analysis': {
                    'most_specialized': [c for c in categories if c.get('specialized_skills_count', 0) > 10],
                    'highest_defining_skills': sorted(categories, key=lambda x: x.get('defining_skills_count', 0), reverse=True)[:5]
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@skills_intelligence_bp.route('/skill-investment-recommendations')
def api_skill_investment_recommendations():
    """API endpoint for strategic skill investment recommendations."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get investment recommendations
        investment_query = queries.get('skill_intelligence', 'get_skill_investment_recommendations')
        recommendations = [dict(row) for row in db.execute(investment_query).fetchall()]
        
        # Categorize by priority score
        high_priority = [r for r in recommendations if r.get('investment_priority_score', 0) >= 85]
        medium_priority = [r for r in recommendations if 70 <= r.get('investment_priority_score', 0) < 85]
        low_priority = [r for r in recommendations if r.get('investment_priority_score', 0) < 70]
        
        return jsonify({
            'success': True,
            'data': {
                'investment_recommendations': recommendations,
                'priority_analysis': {
                    'high_priority_count': len(high_priority),
                    'medium_priority_count': len(medium_priority),
                    'low_priority_count': len(low_priority),
                    'total_recommendations': len(recommendations)
                },
                'strategic_investments': high_priority,
                'tactical_investments': medium_priority,
                'investment_insights': self._generate_investment_insights(recommendations)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@skills_intelligence_bp.route('/skills-search')
def api_skills_search():
    """API endpoint for intelligent skills search with filtering."""
    try:
        # Get search parameters
        search_term = request.args.get('q', '')
        category_filter = request.args.get('category', '')
        rarity_filter = request.args.get('rarity', '')
        trend_filter = request.args.get('trend', '')
        
        db = get_db()
        
        from ..sql import queries
        
        # Prepare search parameters with LIKE pattern
        search_pattern = f'%{search_term}%' if search_term else ''
        
        # Execute search
        search_query = queries.get('skill_intelligence', 'search_skills_intelligence')
        search_results = [dict(row) for row in db.execute(search_query, (
            search_pattern, search_pattern, search_pattern,  # Search term (3 uses)
            category_filter, category_filter,  # Category filter (2 uses)
            rarity_filter, rarity_filter,  # Rarity filter (2 uses)
            trend_filter, trend_filter  # Trend filter (2 uses)
        )).fetchall()]
        
        return jsonify({
            'success': True,
            'data': {
                'search_term': search_term,
                'filters': {
                    'category': category_filter,
                    'rarity': rarity_filter,
                    'trend': trend_filter
                },
                'results': search_results,
                'result_summary': {
                    'total_results': len(search_results),
                    'rare_skills_found': len([s for s in search_results if s.get('rarity_category') in ['Rare', 'Very Rare']]),
                    'trending_skills_found': len([s for s in search_results if s.get('velocity_category') == 'growing'])
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _generate_skill_insights(skill_data):
    """Generate strategic insights for a skill."""
    insights = []
    
    rarity_score = skill_data.get('rarity_score', 0)
    velocity = skill_data.get('velocity_category', '')
    strategic_importance = skill_data.get('strategic_importance', '')
    
    if rarity_score > 90:
        insights.append({
            'type': 'risk',
            'message': 'Ultra-rare skill with potential talent pipeline risk',
            'recommendation': 'Consider targeted acquisition or intensive development programs'
        })
    
    if velocity == 'growing' and strategic_importance == 'High':
        insights.append({
            'type': 'opportunity',
            'message': 'High-growth, strategically important skill',
            'recommendation': 'Priority investment target for competitive advantage'
        })
    
    if velocity == 'declining' and rarity_score > 80:
        insights.append({
            'type': 'warning',
            'message': 'Rare skill in decline - potential knowledge loss risk',
            'recommendation': 'Document expertise and consider transition strategies'
        })
    
    return insights

def _analyze_concentration_risks(rare_skills):
    """Analyze concentration risks in rare skills."""
    risks = []
    
    # Skills with very few practitioners
    ultra_concentrated = [s for s in rare_skills if s.get('current_jobs_count', 0) <= 3]
    if ultra_concentrated:
        risks.append({
            'type': 'Ultra-Concentration',
            'count': len(ultra_concentrated),
            'description': 'Skills with ≤3 practitioners - extreme succession risk'
        })
    
    # Geographic concentration
    single_division = [s for s in rare_skills if s.get('divisions_using', 0) == 1]
    if single_division:
        risks.append({
            'type': 'Geographic Concentration',
            'count': len(single_division),
            'description': 'Rare skills concentrated in single division'
        })
    
    return risks

def _generate_trend_insights(trending_skills, velocity_category):
    """Generate insights about skill trends."""
    insights = []
    
    if velocity_category == 'growing':
        high_growth = [s for s in trending_skills if s.get('short_term_cagr', 0) > 0.5]
        if high_growth:
            insights.append({
                'type': 'opportunity',
                'message': f'{len(high_growth)} skills showing exceptional growth (>50% CAGR)',
                'skills': [s['skill_name'] for s in high_growth[:5]]
            })
    
    elif velocity_category == 'declining':
        rapid_decline = [s for s in trending_skills if s.get('short_term_cagr', 0) < -0.3]
        if rapid_decline:
            insights.append({
                'type': 'risk',
                'message': f'{len(rapid_decline)} skills in rapid decline (>30% negative CAGR)',
                'recommendation': 'Consider transition strategies or technology alternatives'
            })
    
    return insights

def _generate_bundle_insights(bundles):
    """Generate insights about skill bundle landscape."""
    insights = []
    
    # High-value bundles
    exceptional_value = [b for b in bundles if b.get('business_value_score', 0) > 0.9]
    if exceptional_value:
        insights.append({
            'type': 'strategic',
            'message': f'{len(exceptional_value)} bundles with exceptional business value (>0.9)',
            'recommendation': 'Prioritize for enterprise-wide development programs'
        })
    
    # Large, diverse bundles
    mega_bundles = [b for b in bundles if b.get('actual_skills_count', 0) > 100]
    if mega_bundles:
        insights.append({
            'type': 'complexity',
            'message': f'{len(mega_bundles)} mega-bundles (>100 skills) identified',
            'recommendation': 'Consider breaking into focused sub-bundles for training efficiency'
        })
    
    return insights

def _generate_investment_insights(recommendations):
    """Generate insights about skill investment recommendations."""
    insights = []
    
    # High ROI opportunities
    high_roi = [r for r in recommendations if r.get('investment_priority_score', 0) > 90]
    if high_roi:
        insights.append({
            'type': 'high_roi',
            'message': f'{len(high_roi)} skills identified as exceptional investment opportunities',
            'total_potential_reach': sum(r.get('current_jobs_using', 0) for r in high_roi)
        })
    
    # Rare but growing skills
    rare_growing = [r for r in recommendations 
                   if r.get('rarity_category') == 'Rare' and r.get('velocity_category') == 'growing']
    if rare_growing:
        insights.append({
            'type': 'strategic_rare',
            'message': f'{len(rare_growing)} rare skills showing growth trends - early investment opportunity',
            'recommendation': 'First-mover advantage potential in emerging skill areas'
        })
    
    return insights
