-- =================================================================
-- MOVEMENT ANALYTICS QUERIES - V2 ANALYTICS SCHEMA
-- Advanced career movement analysis using analytics_movement_patterns
-- and related analytics tables for career pathway intelligence
-- =================================================================

-- query_name: get_movement_patterns_for_job
-- Get movement patterns for a specific job (both inbound and outbound)
SELECT 
    mp.movement_pattern_id,
    mp.movement_month,
    mp.from_job_profile_id,
    mp.to_job_profile_id,
    from_job.JobProfile as from_job_title,
    to_job.JobProfile as to_job_title,
    from_job.JobFunction as from_function,
    to_job.JobFunction as to_function,
    mp.movement_count,
    mp.unique_employees,
    mp.avg_days_between,
    mp.movement_type,
    mp.skill_similarity_score,
    mp.difficulty_score,
    mp.success_rate,
    
    -- Enhanced similarity from job similarities table
    js.enhanced_similarity_score,
    js.shared_defining_skills_count,
    js.rarity_weighted_score,
    
    -- Direction indicator
    CASE 
        WHEN mp.from_job_profile_id = ? THEN 'outbound'
        WHEN mp.to_job_profile_id = ? THEN 'inbound'
        ELSE 'unrelated'
    END as movement_direction

FROM analytics_movement_patterns mp
LEFT JOIN core_job_architecture from_job ON mp.from_job_profile_id = from_job.JobProfileID
LEFT JOIN core_job_architecture to_job ON mp.to_job_profile_id = to_job.JobProfileID
LEFT JOIN analytics_job_similarities js 
    ON mp.from_job_profile_id = js.job_from AND mp.to_job_profile_id = js.job_to
WHERE (mp.from_job_profile_id = ? OR mp.to_job_profile_id = ?)
  AND mp.movement_count > 0
  AND from_job.JobProfile IS NOT NULL
  AND to_job.JobProfile IS NOT NULL
ORDER BY mp.movement_count DESC, mp.avg_days_between ASC;

-- query_name: get_top_career_transitions
-- Get most common career transitions across the organization
SELECT 
    mp.from_job_profile_id,
    mp.to_job_profile_id,
    from_job.JobProfile as from_job_title,
    to_job.JobProfile as to_job_title,
    from_job.JobFunction as from_function,
    to_job.JobFunction as to_function,
    from_job.ManagementLevel as from_level,
    to_job.ManagementLevel as to_level,
    SUM(mp.movement_count) as total_movements,
    COUNT(DISTINCT mp.movement_month) as months_active,
    AVG(mp.avg_days_between) as avg_transition_days,
    AVG(mp.success_rate) as avg_success_rate,
    
    -- Enhanced Analytics
    js.enhanced_similarity_score,
    js.shared_defining_skills_count,
    js.skill_overlap_percentage,
    
    -- Movement Classification
    CASE 
        WHEN from_job.JobFunction = to_job.JobFunction AND from_job.ManagementLevel = to_job.ManagementLevel THEN 'lateral_same_function'
        WHEN from_job.JobFunction = to_job.JobFunction AND from_job.ManagementLevel != to_job.ManagementLevel THEN 'vertical_same_function'
        WHEN from_job.JobFunction != to_job.JobFunction AND from_job.ManagementLevel = to_job.ManagementLevel THEN 'lateral_cross_function'
        WHEN from_job.JobFunction != to_job.JobFunction AND from_job.ManagementLevel != to_job.ManagementLevel THEN 'diagonal_cross_function'
        ELSE 'unknown'
    END as transition_type

FROM analytics_movement_patterns mp
JOIN core_job_architecture from_job ON mp.from_job_profile_id = from_job.JobProfileID
JOIN core_job_architecture to_job ON mp.to_job_profile_id = to_job.JobProfileID
LEFT JOIN analytics_job_similarities js 
    ON mp.from_job_profile_id = js.job_from AND mp.to_job_profile_id = js.job_to
WHERE mp.movement_count > 0
  AND from_job.JobProfile IS NOT NULL
  AND to_job.JobProfile IS NOT NULL
GROUP BY mp.from_job_profile_id, mp.to_job_profile_id, from_job.JobProfile, to_job.JobProfile,
         from_job.JobFunction, to_job.JobFunction, from_job.ManagementLevel, to_job.ManagementLevel,
         js.enhanced_similarity_score, js.shared_defining_skills_count, js.skill_overlap_percentage
HAVING total_movements >= ?  -- Minimum movement threshold
ORDER BY total_movements DESC, avg_success_rate DESC
LIMIT 50;

-- query_name: get_movement_analytics_by_function
-- Get movement analytics grouped by job function
SELECT 
    from_job.JobFunction as source_function,
    to_job.JobFunction as target_function,
    COUNT(DISTINCT mp.movement_pattern_id) as unique_patterns,
    SUM(mp.movement_count) as total_movements,
    COUNT(DISTINCT mp.from_job_profile_id) as source_jobs_count,
    COUNT(DISTINCT mp.to_job_profile_id) as target_jobs_count,
    AVG(mp.avg_days_between) as avg_transition_days,
    AVG(mp.success_rate) as avg_success_rate,
    AVG(js.enhanced_similarity_score) as avg_similarity_score,
    AVG(js.shared_defining_skills_count) as avg_shared_defining_skills,
    
    -- Movement Type Distribution
    SUM(CASE WHEN mp.movement_type = 'promotion' THEN mp.movement_count ELSE 0 END) as promotions,
    SUM(CASE WHEN mp.movement_type = 'lateral' THEN mp.movement_count ELSE 0 END) as lateral_moves,
    SUM(CASE WHEN mp.movement_type = 'demotion' THEN mp.movement_count ELSE 0 END) as demotions,
    
    -- Difficulty Analysis
    AVG(mp.difficulty_score) as avg_difficulty_score,
    
    -- Function Relationship
    CASE 
        WHEN from_job.JobFunction = to_job.JobFunction THEN 'internal'
        ELSE 'cross_function'
    END as relationship_type

FROM analytics_movement_patterns mp
JOIN core_job_architecture from_job ON mp.from_job_profile_id = from_job.JobProfileID
JOIN core_job_architecture to_job ON mp.to_job_profile_id = to_job.JobProfileID
LEFT JOIN analytics_job_similarities js 
    ON mp.from_job_profile_id = js.job_from AND mp.to_job_profile_id = js.job_to
WHERE mp.movement_count > 0
  AND from_job.JobFunction IS NOT NULL
  AND to_job.JobFunction IS NOT NULL
GROUP BY from_job.JobFunction, to_job.JobFunction
HAVING total_movements >= 10  -- Statistical significance threshold
ORDER BY total_movements DESC, avg_success_rate DESC;

-- query_name: get_movement_timeline_analysis
-- Get movement patterns over time to identify trends
SELECT 
    mp.movement_month,
    SUBSTR(mp.movement_month, 1, 4) as year,
    COUNT(DISTINCT mp.movement_pattern_id) as pattern_count,
    SUM(mp.movement_count) as total_movements,
    COUNT(DISTINCT mp.from_job_profile_id) as source_jobs,
    COUNT(DISTINCT mp.to_job_profile_id) as target_jobs,
    AVG(mp.avg_days_between) as avg_transition_time,
    
    -- Movement Type Breakdown
    SUM(CASE WHEN mp.movement_type = 'promotion' THEN mp.movement_count ELSE 0 END) as promotions,
    SUM(CASE WHEN mp.movement_type = 'lateral' THEN mp.movement_count ELSE 0 END) as laterals,
    SUM(CASE WHEN mp.movement_type = 'demotion' THEN mp.movement_count ELSE 0 END) as demotions,
    
    -- Success Metrics
    AVG(mp.success_rate) as avg_success_rate,
    AVG(mp.difficulty_score) as avg_difficulty,
    
    -- Function Mobility
    COUNT(DISTINCT from_job.JobFunction || '->' || to_job.JobFunction) as unique_function_pairs

FROM analytics_movement_patterns mp
JOIN core_job_architecture from_job ON mp.from_job_profile_id = from_job.JobProfileID
JOIN core_job_architecture to_job ON mp.to_job_profile_id = to_job.JobProfileID
WHERE mp.movement_count > 0
  AND mp.movement_month IS NOT NULL
  AND from_job.JobFunction IS NOT NULL
  AND to_job.JobFunction IS NOT NULL
GROUP BY mp.movement_month
ORDER BY mp.movement_month DESC;

-- query_name: get_high_mobility_jobs
-- Identify jobs with high mobility (high inbound and outbound movement)
SELECT 
    ja.JobProfileID,
    ja.JobProfile,
    ja.JobFunction,
    ja.ManagementLevel,
    
    -- Inbound Movement Metrics
    COUNT(DISTINCT mp_in.movement_pattern_id) as inbound_patterns,
    SUM(COALESCE(mp_in.movement_count, 0)) as total_inbound_movements,
    AVG(mp_in.success_rate) as avg_inbound_success,
    
    -- Outbound Movement Metrics  
    COUNT(DISTINCT mp_out.movement_pattern_id) as outbound_patterns,
    SUM(COALESCE(mp_out.movement_count, 0)) as total_outbound_movements,
    AVG(mp_out.success_rate) as avg_outbound_success,
    
    -- Total Mobility Score
    (SUM(COALESCE(mp_in.movement_count, 0)) + SUM(COALESCE(mp_out.movement_count, 0))) as total_mobility,
    
    -- Job Family Context
    jf.cluster_name as job_family,
    jfc.career_pathway_potential,
    jfc.skill_transferability,
    
    -- Current Workforce
    COUNT(DISTINCT cwc.position_number) as current_positions

FROM core_job_architecture ja
LEFT JOIN analytics_movement_patterns mp_in ON ja.JobProfileID = mp_in.to_job_profile_id
LEFT JOIN analytics_movement_patterns mp_out ON ja.JobProfileID = mp_out.from_job_profile_id
LEFT JOIN analytics_job_families jf ON ja.JobProfileID = jf.job_profile_id
LEFT JOIN analytics_job_family_characteristics jfc ON jf.cluster_id = jfc.cluster_id
LEFT JOIN core_workforce_current cwc ON ja.JobProfileID = cwc.JobProfileID
WHERE ja.JobProfile IS NOT NULL
GROUP BY ja.JobProfileID, ja.JobProfile, ja.JobFunction, ja.ManagementLevel,
         jf.cluster_name, jfc.career_pathway_potential, jfc.skill_transferability
HAVING total_mobility > 0
ORDER BY total_mobility DESC, (inbound_patterns + outbound_patterns) DESC
LIMIT 30;

-- query_name: get_movement_success_factors
-- Analyze factors that contribute to successful career transitions
SELECT 
    mp.movement_type,
    
    -- Similarity Score Impact
    CASE 
        WHEN js.enhanced_similarity_score >= 0.7 THEN 'high_similarity'
        WHEN js.enhanced_similarity_score >= 0.4 THEN 'medium_similarity'  
        ELSE 'low_similarity'
    END as similarity_level,
    
    -- Defining Skills Impact
    CASE 
        WHEN js.shared_defining_skills_count >= 3 THEN 'many_shared_defining'
        WHEN js.shared_defining_skills_count >= 1 THEN 'some_shared_defining'
        ELSE 'no_shared_defining'
    END as defining_skills_level,
    
    -- Function Relationship
    CASE 
        WHEN from_job.JobFunction = to_job.JobFunction THEN 'same_function'
        ELSE 'cross_function'
    END as function_relationship,
    
    -- Management Level Change
    CASE 
        WHEN from_job.ManagementLevel = to_job.ManagementLevel THEN 'same_level'
        ELSE 'level_change'
    END as level_change,
    
    -- Aggregated Metrics
    COUNT(*) as movement_instances,
    SUM(mp.movement_count) as total_movements,
    AVG(mp.success_rate) as avg_success_rate,
    AVG(mp.avg_days_between) as avg_transition_days,
    AVG(mp.difficulty_score) as avg_difficulty_score,
    AVG(js.enhanced_similarity_score) as avg_similarity_score

FROM analytics_movement_patterns mp
JOIN core_job_architecture from_job ON mp.from_job_profile_id = from_job.JobProfileID
JOIN core_job_architecture to_job ON mp.to_job_profile_id = to_job.JobProfileID
LEFT JOIN analytics_job_similarities js 
    ON mp.from_job_profile_id = js.job_from AND mp.to_job_profile_id = js.job_to
WHERE mp.movement_count > 0
  AND mp.success_rate IS NOT NULL
  AND from_job.JobProfile IS NOT NULL
  AND to_job.JobProfile IS NOT NULL
GROUP BY mp.movement_type, similarity_level, defining_skills_level, 
         function_relationship, level_change
HAVING movement_instances >= 5  -- Statistical significance
ORDER BY avg_success_rate DESC, total_movements DESC;

-- query_name: get_movement_network_analysis
-- Get network analysis of job movements for visualization
SELECT 
    from_job.JobFunction as source_function,
    to_job.JobFunction as target_function,
    SUM(mp.movement_count) as edge_weight,
    COUNT(DISTINCT mp.movement_pattern_id) as pattern_count,
    AVG(js.enhanced_similarity_score) as avg_similarity,
    AVG(mp.success_rate) as avg_success_rate,
    
    -- Network Metrics
    CASE 
        WHEN SUM(mp.movement_count) >= 100 THEN 'major_pathway'
        WHEN SUM(mp.movement_count) >= 50 THEN 'moderate_pathway'
        WHEN SUM(mp.movement_count) >= 20 THEN 'minor_pathway'
        ELSE 'rare_pathway'
    END as pathway_strength,
    
    -- Directionality (for network visualization)
    'directed' as edge_type

FROM analytics_movement_patterns mp
JOIN core_job_architecture from_job ON mp.from_job_profile_id = from_job.JobProfileID
JOIN core_job_architecture to_job ON mp.to_job_profile_id = to_job.JobProfileID
LEFT JOIN analytics_job_similarities js 
    ON mp.from_job_profile_id = js.job_from AND mp.to_job_profile_id = js.job_to
WHERE mp.movement_count > 0
  AND from_job.JobFunction IS NOT NULL
  AND to_job.JobFunction IS NOT NULL
  AND from_job.JobFunction != to_job.JobFunction  -- Cross-function only
GROUP BY from_job.JobFunction, to_job.JobFunction
HAVING edge_weight >= 10  -- Minimum movement threshold
ORDER BY edge_weight DESC;

-- query_name: get_career_pathway_recommendations
-- Get intelligent career pathway recommendations based on movement analytics
SELECT 
    mp.to_job_profile_id as recommended_job_id,
    to_job.JobProfile as recommended_job_title,
    to_job.JobFunction as target_function,
    to_job.ManagementLevel as target_level,
    
    -- Movement History Evidence
    SUM(mp.movement_count) as historical_movements,
    AVG(mp.success_rate) as historical_success_rate,
    AVG(mp.avg_days_between) as avg_transition_time,
    
    -- Similarity Analysis
    js.enhanced_similarity_score,
    js.shared_defining_skills_count,
    js.rarity_weighted_score,
    js.skill_overlap_percentage,
    
    -- Current Opportunities
    COUNT(DISTINCT cwc.position_number) as available_positions,
    
    -- Job Family Context
    target_jf.cluster_name as target_family,
    target_jfc.career_pathway_potential,
    target_jfc.business_value_score,
    
    -- Recommendation Score (composite)
    (AVG(mp.success_rate) * 0.3 + 
     js.enhanced_similarity_score * 0.4 + 
     (SUM(mp.movement_count) / 100.0) * 0.2 + 
     COALESCE(target_jfc.business_value_score, 0.5) * 0.1) as recommendation_score

FROM analytics_movement_patterns mp
JOIN core_job_architecture to_job ON mp.to_job_profile_id = to_job.JobProfileID
LEFT JOIN analytics_job_similarities js 
    ON mp.from_job_profile_id = js.job_from AND mp.to_job_profile_id = js.job_to
LEFT JOIN analytics_job_families target_jf ON to_job.JobProfileID = target_jf.job_profile_id
LEFT JOIN analytics_job_family_characteristics target_jfc ON target_jf.cluster_id = target_jfc.cluster_id
LEFT JOIN core_workforce_current cwc ON to_job.JobProfileID = cwc.JobProfileID
WHERE mp.from_job_profile_id = ?
  AND mp.movement_count > 0
  AND to_job.JobProfile IS NOT NULL
GROUP BY mp.to_job_profile_id, to_job.JobProfile, to_job.JobFunction, to_job.ManagementLevel,
         js.enhanced_similarity_score, js.shared_defining_skills_count, js.rarity_weighted_score,
         js.skill_overlap_percentage, target_jf.cluster_name, target_jfc.career_pathway_potential,
         target_jfc.business_value_score
ORDER BY recommendation_score DESC, historical_movements DESC
LIMIT 15;
