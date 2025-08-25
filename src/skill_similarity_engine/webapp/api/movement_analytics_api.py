"""
Movement Analytics API Module for NAB Skills Intelligence Platform
================================================================

This module contains V2 movement analytics endpoints:
- /api/v2/movement-patterns/<job_id>
- /api/v2/top-career-transitions
- /api/v2/movement-by-function
- /api/v2/movement-timeline
- /api/v2/high-mobility-jobs
- /api/v2/movement-success-factors
- /api/v2/movement-network-analysis
- /api/v2/career-pathway-recommendations/<job_id>

These endpoints provide sophisticated career movement analysis using
analytics_movement_patterns and related V2 analytics tables.
"""

from flask import Blueprint, request, jsonify, g

# Create blueprint for movement analytics API
movement_analytics_bp = Blueprint('movement_analytics_api', __name__, url_prefix='/api/v2')

def get_db():
    """Get database connection from Flask g object."""
    from flask import current_app
    import sqlite3
    if 'db' not in g:
        g.db = sqlite3.connect(str(current_app.config['DATABASE_PATH']))
        g.db.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return g.db

@movement_analytics_bp.route('/movement-patterns/<job_id>')
def api_movement_patterns(job_id):
    """API endpoint for movement patterns for a specific job."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get movement patterns (both inbound and outbound)
        patterns_query = queries.get('movement_analytics', 'get_movement_patterns_for_job')
        movement_patterns = [dict(row) for row in db.execute(patterns_query, (job_id, job_id, job_id, job_id)).fetchall()]
        
        if not movement_patterns:
            return jsonify({
                'success': True,
                'data': {
                    'job_id': job_id,
                    'movement_patterns': [],
                    'message': 'No movement patterns found for this job'
                }
            })
        
        # Separate inbound and outbound movements
        inbound_movements = [p for p in movement_patterns if p.get('movement_direction') == 'inbound']
        outbound_movements = [p for p in movement_patterns if p.get('movement_direction') == 'outbound']
        
        # Calculate summary metrics
        total_inbound_count = sum(p.get('movement_count', 0) for p in inbound_movements)
        total_outbound_count = sum(p.get('movement_count', 0) for p in outbound_movements)
        avg_success_rate = sum(p.get('success_rate', 0) for p in movement_patterns if p.get('success_rate')) / len([p for p in movement_patterns if p.get('success_rate')]) if movement_patterns else 0
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job_id,
                'movement_patterns': movement_patterns,
                'pattern_analysis': {
                    'total_patterns': len(movement_patterns),
                    'inbound_patterns': len(inbound_movements),
                    'outbound_patterns': len(outbound_movements),
                    'total_inbound_movements': total_inbound_count,
                    'total_outbound_movements': total_outbound_count,
                    'average_success_rate': round(avg_success_rate, 3)
                },
                'inbound_movements': inbound_movements,
                'outbound_movements': outbound_movements,
                'mobility_insights': self._generate_mobility_insights(inbound_movements, outbound_movements)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@movement_analytics_bp.route('/top-career-transitions')
def api_top_career_transitions():
    """API endpoint for most common career transitions."""
    try:
        min_movements = int(request.args.get('min_movements', 5))
        
        db = get_db()
        
        from ..sql import queries
        
        # Get top transitions
        transitions_query = queries.get('movement_analytics', 'get_top_career_transitions')
        transitions = [dict(row) for row in db.execute(transitions_query, (min_movements,)).fetchall()]
        
        # Analyze transition patterns
        transition_types = {}
        for transition in transitions:
            t_type = transition.get('transition_type', 'unknown')
            if t_type not in transition_types:
                transition_types[t_type] = []
            transition_types[t_type].append(transition)
        
        # Get top performers by type
        top_by_type = {}
        for t_type, transitions_list in transition_types.items():
            top_by_type[t_type] = sorted(transitions_list, key=lambda x: x.get('total_movements', 0), reverse=True)[:5]
        
        return jsonify({
            'success': True,
            'data': {
                'career_transitions': transitions,
                'transition_analysis': {
                    'total_transition_patterns': len(transitions),
                    'transition_types': list(transition_types.keys()),
                    'avg_transition_days': sum(t.get('avg_transition_days', 0) for t in transitions) / len(transitions) if transitions else 0,
                    'avg_success_rate': sum(t.get('avg_success_rate', 0) for t in transitions if t.get('avg_success_rate')) / len([t for t in transitions if t.get('avg_success_rate')]) if transitions else 0
                },
                'transitions_by_type': transition_types,
                'top_transitions_by_type': top_by_type,
                'transition_insights': self._generate_transition_insights(transitions)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@movement_analytics_bp.route('/movement-by-function')
def api_movement_by_function():
    """API endpoint for movement analytics grouped by job function."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get function-level movement analytics
        function_query = queries.get('movement_analytics', 'get_movement_analytics_by_function')
        function_movements = [dict(row) for row in db.execute(function_query).fetchall()]
        
        # Separate internal vs cross-function movements
        internal_movements = [f for f in function_movements if f.get('relationship_type') == 'internal']
        cross_function_movements = [f for f in function_movements if f.get('relationship_type') == 'cross_function']
        
        # Calculate mobility scores for functions
        function_mobility = {}
        for movement in function_movements:
            source_func = movement.get('source_function')
            if source_func not in function_mobility:
                function_mobility[source_func] = {
                    'outbound_movements': 0,
                    'outbound_patterns': 0,
                    'avg_success_rate': 0,
                    'functions_reached': set()
                }
            
            function_mobility[source_func]['outbound_movements'] += movement.get('total_movements', 0)
            function_mobility[source_func]['outbound_patterns'] += 1
            function_mobility[source_func]['functions_reached'].add(movement.get('target_function'))
            
        # Convert sets to counts for JSON serialization
        for func_data in function_mobility.values():
            func_data['functions_reached'] = len(func_data['functions_reached'])
        
        return jsonify({
            'success': True,
            'data': {
                'function_movements': function_movements,
                'movement_analysis': {
                    'total_function_pairs': len(function_movements),
                    'internal_movement_pairs': len(internal_movements),
                    'cross_function_pairs': len(cross_function_movements),
                    'total_movements': sum(f.get('total_movements', 0) for f in function_movements)
                },
                'internal_movements': internal_movements,
                'cross_function_movements': cross_function_movements,
                'function_mobility_scores': function_mobility,
                'function_insights': self._generate_function_insights(function_movements)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@movement_analytics_bp.route('/movement-timeline')
def api_movement_timeline():
    """API endpoint for movement patterns over time."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get timeline analysis
        timeline_query = queries.get('movement_analytics', 'get_movement_timeline_analysis')
        timeline_data = [dict(row) for row in db.execute(timeline_query).fetchall()]
        
        # Group by year for trend analysis
        yearly_data = {}
        for month_data in timeline_data:
            year = month_data.get('year')
            if year not in yearly_data:
                yearly_data[year] = {
                    'total_movements': 0,
                    'promotions': 0,
                    'laterals': 0,
                    'demotions': 0,
                    'months_count': 0,
                    'avg_success_rate': []
                }
            
            yearly_data[year]['total_movements'] += month_data.get('total_movements', 0)
            yearly_data[year]['promotions'] += month_data.get('promotions', 0)
            yearly_data[year]['laterals'] += month_data.get('laterals', 0)
            yearly_data[year]['demotions'] += month_data.get('demotions', 0)
            yearly_data[year]['months_count'] += 1
            if month_data.get('avg_success_rate'):
                yearly_data[year]['avg_success_rate'].append(month_data.get('avg_success_rate'))
        
        # Calculate yearly averages
        for year_data in yearly_data.values():
            if year_data['avg_success_rate']:
                year_data['avg_success_rate'] = sum(year_data['avg_success_rate']) / len(year_data['avg_success_rate'])
            else:
                year_data['avg_success_rate'] = 0
        
        return jsonify({
            'success': True,
            'data': {
                'monthly_timeline': timeline_data,
                'yearly_summary': yearly_data,
                'timeline_insights': self._generate_timeline_insights(timeline_data, yearly_data)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@movement_analytics_bp.route('/high-mobility-jobs')
def api_high_mobility_jobs():
    """API endpoint for jobs with high mobility (high movement activity)."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get high mobility jobs
        mobility_query = queries.get('movement_analytics', 'get_high_mobility_jobs')
        mobility_jobs = [dict(row) for row in db.execute(mobility_query).fetchall()]
        
        # Categorize by mobility type
        high_inbound = [j for j in mobility_jobs if j.get('total_inbound_movements', 0) > j.get('total_outbound_movements', 0)]
        high_outbound = [j for j in mobility_jobs if j.get('total_outbound_movements', 0) > j.get('total_inbound_movements', 0)]
        balanced_mobility = [j for j in mobility_jobs if abs(j.get('total_inbound_movements', 0) - j.get('total_outbound_movements', 0)) <= 5]
        
        return jsonify({
            'success': True,
            'data': {
                'high_mobility_jobs': mobility_jobs,
                'mobility_analysis': {
                    'total_mobile_jobs': len(mobility_jobs),
                    'high_inbound_jobs': len(high_inbound),
                    'high_outbound_jobs': len(high_outbound),
                    'balanced_mobility_jobs': len(balanced_mobility),
                    'avg_total_mobility': sum(j.get('total_mobility', 0) for j in mobility_jobs) / len(mobility_jobs) if mobility_jobs else 0
                },
                'mobility_categories': {
                    'destination_roles': high_inbound[:10],  # Top 10 destination roles
                    'springboard_roles': high_outbound[:10],  # Top 10 springboard roles
                    'transit_hubs': balanced_mobility[:10]  # Top 10 transit hub roles
                },
                'mobility_insights': self._generate_mobility_job_insights(mobility_jobs)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@movement_analytics_bp.route('/movement-success-factors')
def api_movement_success_factors():
    """API endpoint for analyzing factors that contribute to successful transitions."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get success factors analysis
        success_query = queries.get('movement_analytics', 'get_movement_success_factors')
        success_factors = [dict(row) for row in db.execute(success_query).fetchall()]
        
        # Analyze success patterns
        success_by_similarity = {}
        success_by_function = {}
        success_by_level = {}
        
        for factor in success_factors:
            # Group by similarity level
            sim_level = factor.get('similarity_level', 'unknown')
            if sim_level not in success_by_similarity:
                success_by_similarity[sim_level] = []
            success_by_similarity[sim_level].append(factor)
            
            # Group by function relationship
            func_rel = factor.get('function_relationship', 'unknown')
            if func_rel not in success_by_function:
                success_by_function[func_rel] = []
            success_by_function[func_rel].append(factor)
            
            # Group by level change
            level_change = factor.get('level_change', 'unknown')
            if level_change not in success_by_level:
                success_by_level[level_change] = []
            success_by_level[level_change].append(factor)
        
        return jsonify({
            'success': True,
            'data': {
                'success_factors': success_factors,
                'success_analysis': {
                    'by_similarity_level': success_by_similarity,
                    'by_function_relationship': success_by_function,
                    'by_level_change': success_by_level
                },
                'success_insights': self._generate_success_insights(success_factors)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@movement_analytics_bp.route('/movement-network-analysis')
def api_movement_network_analysis():
    """API endpoint for network analysis of job movements."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get network data
        network_query = queries.get('movement_analytics', 'get_movement_network_analysis')
        network_data = [dict(row) for row in db.execute(network_query).fetchall()]
        
        # Calculate network metrics
        nodes = set()
        for edge in network_data:
            nodes.add(edge.get('source_function'))
            nodes.add(edge.get('target_function'))
        
        # Create adjacency information for network analysis
        adjacency = {}
        for node in nodes:
            adjacency[node] = {
                'outbound_connections': [],
                'inbound_connections': [],
                'total_outbound_weight': 0,
                'total_inbound_weight': 0
            }
        
        for edge in network_data:
            source = edge.get('source_function')
            target = edge.get('target_function')
            weight = edge.get('edge_weight', 0)
            
            adjacency[source]['outbound_connections'].append({
                'target': target,
                'weight': weight,
                'strength': edge.get('pathway_strength')
            })
            adjacency[source]['total_outbound_weight'] += weight
            
            adjacency[target]['inbound_connections'].append({
                'source': source,
                'weight': weight,
                'strength': edge.get('pathway_strength')
            })
            adjacency[target]['total_inbound_weight'] += weight
        
        # Identify network hubs (high connectivity)
        network_hubs = []
        for node, connections in adjacency.items():
            total_weight = connections['total_outbound_weight'] + connections['total_inbound_weight']
            total_connections = len(connections['outbound_connections']) + len(connections['inbound_connections'])
            
            if total_connections > 0:
                network_hubs.append({
                    'function': node,
                    'total_weight': total_weight,
                    'total_connections': total_connections,
                    'outbound_weight': connections['total_outbound_weight'],
                    'inbound_weight': connections['total_inbound_weight']
                })
        
        network_hubs.sort(key=lambda x: x['total_weight'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'network_edges': network_data,
                'network_nodes': list(nodes),
                'adjacency_matrix': adjacency,
                'network_metrics': {
                    'total_functions': len(nodes),
                    'total_pathways': len(network_data),
                    'total_movement_weight': sum(e.get('edge_weight', 0) for e in network_data),
                    'avg_pathway_strength': sum(e.get('avg_similarity', 0) for e in network_data) / len(network_data) if network_data else 0
                },
                'network_hubs': network_hubs[:10],  # Top 10 hubs
                'network_insights': self._generate_network_insights(network_data, network_hubs)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@movement_analytics_bp.route('/career-pathway-recommendations/<job_id>')
def api_career_pathway_recommendations(job_id):
    """API endpoint for intelligent career pathway recommendations."""
    try:
        db = get_db()
        
        from ..sql import queries
        
        # Get pathway recommendations
        recommendations_query = queries.get('movement_analytics', 'get_career_pathway_recommendations')
        recommendations = [dict(row) for row in db.execute(recommendations_query, (job_id,)).fetchall()]
        
        if not recommendations:
            return jsonify({
                'success': True,
                'data': {
                    'job_id': job_id,
                    'recommendations': [],
                    'message': 'No career pathway recommendations found based on movement analytics'
                }
            })
        
        # Categorize by recommendation score
        excellent_matches = [r for r in recommendations if r.get('recommendation_score', 0) > 0.8]
        good_matches = [r for r in recommendations if 0.6 <= r.get('recommendation_score', 0) <= 0.8]
        potential_matches = [r for r in recommendations if 0.4 <= r.get('recommendation_score', 0) < 0.6]
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job_id,
                'pathway_recommendations': recommendations,
                'recommendation_analysis': {
                    'total_recommendations': len(recommendations),
                    'excellent_matches': len(excellent_matches),
                    'good_matches': len(good_matches),
                    'potential_matches': len(potential_matches),
                    'avg_recommendation_score': sum(r.get('recommendation_score', 0) for r in recommendations) / len(recommendations) if recommendations else 0
                },
                'categorized_recommendations': {
                    'excellent_matches': excellent_matches,
                    'good_matches': good_matches,
                    'potential_matches': potential_matches
                },
                'pathway_insights': self._generate_pathway_insights(recommendations)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _generate_mobility_insights(inbound_movements, outbound_movements):
    """Generate insights about job mobility patterns."""
    insights = []
    
    inbound_count = sum(m.get('movement_count', 0) for m in inbound_movements)
    outbound_count = sum(m.get('movement_count', 0) for m in outbound_movements)
    
    if inbound_count > outbound_count * 2:
        insights.append({
            'type': 'destination_role',
            'message': 'Strong destination role - high inbound career interest',
            'ratio': f'{inbound_count}:{outbound_count}'
        })
    elif outbound_count > inbound_count * 2:
        insights.append({
            'type': 'springboard_role',
            'message': 'Springboard role - high outbound career progression',
            'ratio': f'{inbound_count}:{outbound_count}'
        })
    else:
        insights.append({
            'type': 'transit_hub',
            'message': 'Career transit hub - balanced bidirectional movement',
            'ratio': f'{inbound_count}:{outbound_count}'
        })
    
    return insights

def _generate_transition_insights(transitions):
    """Generate insights about career transition patterns."""
    insights = []
    
    # Analyze transition types
    type_counts = {}
    for transition in transitions:
        t_type = transition.get('transition_type', 'unknown')
        type_counts[t_type] = type_counts.get(t_type, 0) + transition.get('total_movements', 0)
    
    most_common_type = max(type_counts, key=type_counts.get) if type_counts else None
    if most_common_type:
        insights.append({
            'type': 'pattern',
            'message': f'Most common transition type: {most_common_type}',
            'percentage': round(type_counts[most_common_type] / sum(type_counts.values()) * 100, 1)
        })
    
    # High similarity transitions
    high_sim = [t for t in transitions if t.get('enhanced_similarity_score', 0) > 0.7]
    if high_sim:
        insights.append({
            'type': 'similarity',
            'message': f'{len(high_sim)} transitions have high skill similarity (>0.7)',
            'avg_success': round(sum(t.get('avg_success_rate', 0) for t in high_sim) / len(high_sim), 3)
        })
    
    return insights

def _generate_function_insights(function_movements):
    """Generate insights about function-level movement patterns."""
    insights = []
    
    # Most mobile functions (sources)
    source_mobility = {}
    for movement in function_movements:
        source = movement.get('source_function')
        source_mobility[source] = source_mobility.get(source, 0) + movement.get('total_movements', 0)
    
    most_mobile_source = max(source_mobility, key=source_mobility.get) if source_mobility else None
    if most_mobile_source:
        insights.append({
            'type': 'mobility_source',
            'message': f'Most mobile source function: {most_mobile_source}',
            'total_movements': source_mobility[most_mobile_source]
        })
    
    # Cross-function vs internal movement
    cross_function = [f for f in function_movements if f.get('relationship_type') == 'cross_function']
    internal = [f for f in function_movements if f.get('relationship_type') == 'internal']
    
    if cross_function and internal:
        cross_total = sum(f.get('total_movements', 0) for f in cross_function)
        internal_total = sum(f.get('total_movements', 0) for f in internal)
        
        insights.append({
            'type': 'movement_balance',
            'message': f'Cross-function vs internal movement ratio: {cross_total}:{internal_total}',
            'cross_function_percentage': round(cross_total / (cross_total + internal_total) * 100, 1)
        })
    
    return insights

def _generate_timeline_insights(timeline_data, yearly_data):
    """Generate insights about movement timeline trends."""
    insights = []
    
    if len(yearly_data) >= 2:
        years = sorted(yearly_data.keys())
        recent_year = years[-1]
        previous_year = years[-2]
        
        recent_movements = yearly_data[recent_year]['total_movements']
        previous_movements = yearly_data[previous_year]['total_movements']
        
        if recent_movements > previous_movements:
            growth_rate = ((recent_movements - previous_movements) / previous_movements) * 100
            insights.append({
                'type': 'growth_trend',
                'message': f'Career movement activity increased {growth_rate:.1f}% from {previous_year} to {recent_year}',
                'current_year_movements': recent_movements
            })
        elif recent_movements < previous_movements:
            decline_rate = ((previous_movements - recent_movements) / previous_movements) * 100
            insights.append({
                'type': 'decline_trend',
                'message': f'Career movement activity decreased {decline_rate:.1f}% from {previous_year} to {recent_year}',
                'current_year_movements': recent_movements
            })
    
    # Promotion vs lateral movement trends
    total_promotions = sum(data.get('promotions', 0) for data in timeline_data)
    total_laterals = sum(data.get('laterals', 0) for data in timeline_data)
    
    if total_promotions and total_laterals:
        promotion_percentage = (total_promotions / (total_promotions + total_laterals)) * 100
        insights.append({
            'type': 'movement_composition',
            'message': f'Promotions represent {promotion_percentage:.1f}% of total movements',
            'promotion_ratio': f'{total_promotions}:{total_laterals}'
        })
    
    return insights

def _generate_mobility_job_insights(mobility_jobs):
    """Generate insights about high-mobility jobs."""
    insights = []
    
    # Job families with high mobility
    family_mobility = {}
    for job in mobility_jobs:
        family = job.get('job_family', 'Unknown')
        if family not in family_mobility:
            family_mobility[family] = []
        family_mobility[family].append(job)
    
    if family_mobility:
        most_mobile_family = max(family_mobility, key=lambda x: len(family_mobility[x]))
        insights.append({
            'type': 'family_mobility',
            'message': f'Most mobile job family: {most_mobile_family}',
            'jobs_count': len(family_mobility[most_mobile_family])
        })
    
    # High career pathway potential correlation
    high_career_potential = [j for j in mobility_jobs if j.get('career_pathway_potential') == 'high']
    if high_career_potential:
        avg_mobility = sum(j.get('total_mobility', 0) for j in high_career_potential) / len(high_career_potential)
        insights.append({
            'type': 'career_potential_correlation',
            'message': f'{len(high_career_potential)} jobs with high career pathway potential',
            'avg_mobility_score': round(avg_mobility, 1)
        })
    
    return insights

def _generate_success_insights(success_factors):
    """Generate insights about movement success factors."""
    insights = []
    
    # Best performing similarity level
    similarity_success = {}
    for factor in success_factors:
        sim_level = factor.get('similarity_level', 'unknown')
        if sim_level not in similarity_success:
            similarity_success[sim_level] = []
        similarity_success[sim_level].append(factor.get('avg_success_rate', 0))
    
    for level, rates in similarity_success.items():
        avg_rate = sum(rates) / len(rates) if rates else 0
        similarity_success[level] = avg_rate
    
    best_similarity_level = max(similarity_success, key=similarity_success.get) if similarity_success else None
    if best_similarity_level:
        insights.append({
            'type': 'similarity_success',
            'message': f'Highest success rate for {best_similarity_level} similarity transitions',
            'success_rate': round(similarity_success[best_similarity_level], 3)
        })
    
    # Same function vs cross-function success
    same_function_success = []
    cross_function_success = []
    
    for factor in success_factors:
        func_rel = factor.get('function_relationship', 'unknown')
        success_rate = factor.get('avg_success_rate', 0)
        
        if func_rel == 'same_function':
            same_function_success.append(success_rate)
        elif func_rel == 'cross_function':
            cross_function_success.append(success_rate)
    
    if same_function_success and cross_function_success:
        same_avg = sum(same_function_success) / len(same_function_success)
        cross_avg = sum(cross_function_success) / len(cross_function_success)
        
        if same_avg > cross_avg:
            insights.append({
                'type': 'function_relationship',
                'message': f'Same-function transitions more successful ({same_avg:.3f} vs {cross_avg:.3f})',
                'difference': round(same_avg - cross_avg, 3)
            })
        else:
            insights.append({
                'type': 'function_relationship',
                'message': f'Cross-function transitions more successful ({cross_avg:.3f} vs {same_avg:.3f})',
                'difference': round(cross_avg - same_avg, 3)
            })
    
    return insights

def _generate_network_insights(network_data, network_hubs):
    """Generate insights about movement network."""
    insights = []
    
    # Most connected hub
    if network_hubs:
        top_hub = network_hubs[0]
        insights.append({
            'type': 'connectivity_hub',
            'message': f'Most connected function: {top_hub["function"]}',
            'total_weight': top_hub['total_weight'],
            'connections': top_hub['total_connections']
        })
    
    # Network density
    total_possible_connections = len(set([e.get('source_function') for e in network_data] + [e.get('target_function') for e in network_data])) ** 2
    actual_connections = len(network_data)
    network_density = actual_connections / total_possible_connections if total_possible_connections > 0 else 0
    
    insights.append({
        'type': 'network_density',
        'message': f'Network density: {network_density:.3f}',
        'interpretation': 'high' if network_density > 0.3 else 'medium' if network_density > 0.1 else 'low'
    })
    
    # Major vs minor pathways
    major_pathways = [e for e in network_data if e.get('pathway_strength') == 'major_pathway']
    if major_pathways:
        insights.append({
            'type': 'pathway_strength',
            'message': f'{len(major_pathways)} major career pathways identified',
            'total_major_weight': sum(e.get('edge_weight', 0) for e in major_pathways)
        })
    
    return insights

def _generate_pathway_insights(recommendations):
    """Generate insights about career pathway recommendations."""
    insights = []
    
    # Function diversity
    target_functions = set(r.get('target_function') for r in recommendations)
    insights.append({
        'type': 'function_diversity',
        'message': f'Pathways span {len(target_functions)} different job functions',
        'functions': list(target_functions)
    })
    
    # Historical movement backing
    with_history = [r for r in recommendations if r.get('historical_movements', 0) > 0]
    insights.append({
        'type': 'historical_validation',
        'message': f'{len(with_history)} recommendations backed by historical movement data',
        'percentage': round(len(with_history) / len(recommendations) * 100, 1) if recommendations else 0
    })
    
    # High availability opportunities
    high_availability = [r for r in recommendations if r.get('available_positions', 0) > 5]
    if high_availability:
        insights.append({
            'type': 'opportunity_availability',
            'message': f'{len(high_availability)} recommendations with 5+ available positions',
            'total_positions': sum(r.get('available_positions', 0) for r in high_availability)
        })
    
    return insights
