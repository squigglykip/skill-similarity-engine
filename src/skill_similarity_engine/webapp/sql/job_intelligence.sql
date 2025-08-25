-- =================================================================
-- JOB INTELLIGENCE QUERIES - V2 ANALYTICS SCHEMA
-- Advanced job intelligence using analytics tables for defining skills,
-- job families, and skill bundle analysis
-- =================================================================

-- query_name: get_job_defining_skills
-- Get defining skills for a specific job with rarity and analytics data
SELECT 
    jds.job_profile_id,
    jds.skill_id,
    jds.skill_name,
    jds.category,
    jds.subcategory,
    jds.skill_type,
    jds.defining_skill_rank,
    jds.defining_skill_score,
    jds.prevalence_percentage,
    jds.rarity_category,
    sr.rarity_score,
    CASE 
        WHEN jds.defining_skill_rank <= 3 THEN 'Critical'
        WHEN jds.defining_skill_rank <= 8 THEN 'Important' 
        ELSE 'Supplementary'
    END as skill_importance,
    COALESCE(sdt.velocity_category, 'stable') as skill_trend,
    COALESCE(sdt.trend_direction, 'stable') as trend_direction
FROM analytics_job_defining_skills jds
LEFT JOIN analytics_skill_rarity sr ON jds.skill_id = sr.skill_id
LEFT JOIN analytics_skill_demand_trends sdt ON jds.skill_id = sdt.skill_id
WHERE jds.job_profile_id = ?
  AND jds.skill_name IS NOT NULL  -- FAIL-FAST validation
ORDER BY jds.defining_skill_rank ASC;

-- query_name: get_job_family_info
-- Get comprehensive job family information including cluster analysis
SELECT 
    jf.job_profile_id,
    jf.job_profile,
    jf.job_function,
    jf.cluster_id,
    jf.cluster_name,
    jf.cluster_description,
    jf.cluster_size,
    jf.cluster_confidence,
    jf.silhouette_score,
    jfc.family_name,
    jfc.family_description,
    jfc.dominant_function,
    jfc.function_purity,
    jfc.business_value_score,
    jfc.career_pathway_potential,
    jfc.skill_transferability,
    jfc.market_demand_level
FROM analytics_job_families jf
LEFT JOIN analytics_job_family_characteristics jfc ON jf.cluster_id = jfc.cluster_id
WHERE jf.job_profile_id = ?
  AND jf.job_profile IS NOT NULL;  -- FAIL-FAST validation

-- query_name: get_job_skill_bundles
-- Get skill bundles associated with a job's skills
SELECT 
    sb.skill_id,
    sb.skill_name,
    sb.category,
    sb.cluster_id,
    sb.bundle_name,
    sb.bundle_description,
    sb.bundle_size,
    sb.bundle_confidence,
    sb.silhouette_score,
    bc.specialization_area,
    bc.business_value_score,
    bc.training_feasibility,
    bc.market_demand_level,
    bc.typical_career_stage,
    CASE WHEN jsr.JobProfileID IS NOT NULL THEN 1 ELSE 0 END as job_has_skill
FROM analytics_skill_bundles sb
LEFT JOIN analytics_bundle_characteristics bc ON sb.cluster_id = bc.cluster_id
LEFT JOIN core_job_skill_requirements jsr 
    ON sb.skill_id = jsr.Skill_ID AND jsr.JobProfileID = ?
WHERE sb.skill_name IS NOT NULL
  AND (jsr.JobProfileID IS NOT NULL OR sb.bundle_name IN (
    -- Include bundles that contain at least one skill from this job
    SELECT DISTINCT sb2.bundle_name 
    FROM analytics_skill_bundles sb2
    JOIN core_job_skill_requirements jsr2 ON sb2.skill_id = jsr2.Skill_ID
    WHERE jsr2.JobProfileID = ?
  ))
ORDER BY bc.business_value_score DESC, sb.bundle_confidence DESC;

-- query_name: get_job_specialization_analysis
-- Get specialization analysis for a job based on its skills
SELECT 
    ss.skill_id,
    ss.skill_name,
    ss.category,
    ss.subcategory,
    ss.specialization_score,
    ss.specialization_category,
    ss.rarity_rank,
    ss.strategic_importance,
    ss.skill_lifecycle_stage,
    ss.investment_recommendation,
    ss.market_context,
    ss.training_availability,
    ss.external_market_demand,
    CASE WHEN jsr.JobProfileID IS NOT NULL THEN 1 ELSE 0 END as job_has_skill
FROM analytics_specialized_skills ss
LEFT JOIN core_job_skill_requirements jsr 
    ON ss.skill_id = jsr.Skill_ID AND jsr.JobProfileID = ?
WHERE ss.skill_name IS NOT NULL
  AND jsr.JobProfileID IS NOT NULL  -- Only skills this job actually has
ORDER BY ss.specialization_score DESC, ss.strategic_importance DESC;

-- query_name: get_job_intelligence_summary
-- Get comprehensive job intelligence summary combining all analytics
SELECT 
    ja.JobProfileID,
    ja.JobProfile,
    ja.JobFunction,
    ja.ManagementLevel,
    ja.JobCategory,
    
    -- Defining Skills Metrics
    COUNT(DISTINCT jds.skill_id) as defining_skills_count,
    COUNT(DISTINCT CASE WHEN jds.rarity_category = 'Rare' THEN jds.skill_id END) as rare_defining_skills,
    
    -- Job Family Metrics  
    jf.cluster_name as job_family,
    jf.cluster_size as family_size,
    jfc.business_value_score as family_business_value,
    jfc.career_pathway_potential,
    
    -- Skill Bundle Metrics
    COUNT(DISTINCT sb.cluster_id) as skill_bundles_count,
    AVG(bc.business_value_score) as avg_bundle_value,
    
    -- Specialization Metrics
    COUNT(DISTINCT ss.skill_id) as specialized_skills_count,
    COUNT(DISTINCT CASE WHEN ss.specialization_category = 'Ultra-Rare' THEN ss.skill_id END) as ultra_rare_skills,
    
    -- Total Skills
    COUNT(DISTINCT jsr.Skill_ID) as total_skills_count

FROM core_job_architecture ja
LEFT JOIN analytics_job_defining_skills jds ON ja.JobProfileID = jds.job_profile_id
LEFT JOIN analytics_job_families jf ON ja.JobProfileID = jf.job_profile_id
LEFT JOIN analytics_job_family_characteristics jfc ON jf.cluster_id = jfc.cluster_id
LEFT JOIN core_job_skill_requirements jsr ON ja.JobProfileID = jsr.JobProfileID
LEFT JOIN analytics_skill_bundles sb ON jsr.Skill_ID = sb.skill_id
LEFT JOIN analytics_bundle_characteristics bc ON sb.cluster_id = bc.cluster_id
LEFT JOIN analytics_specialized_skills ss ON jsr.Skill_ID = ss.skill_id
WHERE ja.JobProfileID = ?
  AND ja.JobProfile IS NOT NULL  -- FAIL-FAST validation
GROUP BY ja.JobProfileID, ja.JobProfile, ja.JobFunction, ja.ManagementLevel, ja.JobCategory,
         jf.cluster_name, jf.cluster_size, jfc.business_value_score, jfc.career_pathway_potential;

-- query_name: get_similar_jobs_by_family
-- Get similar jobs within the same job family cluster
SELECT 
    jf2.job_profile_id,
    jf2.job_profile,
    jf2.job_function,
    jf2.management_level,
    js.enhanced_similarity_score,
    js.shared_defining_skills_count,
    js.rarity_weighted_score,
    COUNT(DISTINCT cwc.position_number) as current_positions
FROM analytics_job_families jf1
JOIN analytics_job_families jf2 ON jf1.cluster_id = jf2.cluster_id
LEFT JOIN analytics_job_similarities js 
    ON jf1.job_profile_id = js.job_from AND jf2.job_profile_id = js.job_to
LEFT JOIN core_workforce_current cwc ON jf2.job_profile_id = cwc.JobProfileID
WHERE jf1.job_profile_id = ?
  AND jf2.job_profile_id != jf1.job_profile_id  -- Exclude self
  AND jf2.job_profile IS NOT NULL
GROUP BY jf2.job_profile_id, jf2.job_profile, jf2.job_function, jf2.management_level,
         js.enhanced_similarity_score, js.shared_defining_skills_count, js.rarity_weighted_score
ORDER BY js.enhanced_similarity_score DESC, js.shared_defining_skills_count DESC
LIMIT 20;

-- query_name: get_job_market_intelligence
-- Get market intelligence for a job including demand trends and movement patterns
SELECT 
    ja.JobProfileID,
    ja.JobProfile,
    ja.JobFunction,
    
    -- Current Workforce Metrics
    COUNT(DISTINCT cwc.position_number) as current_positions,
    COUNT(DISTINCT cwc.ORG_UNIT_NAME_2) as divisions_present,
    COUNT(DISTINCT cwc.Location) as locations_present,
    
    -- Movement Pattern Metrics
    COUNT(DISTINCT mp_in.movement_pattern_id) as inbound_movements,
    COUNT(DISTINCT mp_out.movement_pattern_id) as outbound_movements,
    AVG(mp_in.skill_similarity_score) as avg_inbound_similarity,
    AVG(mp_out.skill_similarity_score) as avg_outbound_similarity,
    
    -- Skill Demand Trends
    COUNT(DISTINCT sdt.skill_id) as skills_with_trends,
    COUNT(DISTINCT CASE WHEN sdt.velocity_category = 'growing' THEN sdt.skill_id END) as growing_skills,
    COUNT(DISTINCT CASE WHEN sdt.velocity_category = 'declining' THEN sdt.skill_id END) as declining_skills,
    
    -- Family Business Value
    jfc.business_value_score as family_business_value,
    jfc.market_demand_level as family_market_demand

FROM core_job_architecture ja
LEFT JOIN core_workforce_current cwc ON ja.JobProfileID = cwc.JobProfileID
LEFT JOIN analytics_movement_patterns mp_in ON ja.JobProfileID = mp_in.to_job_profile_id
LEFT JOIN analytics_movement_patterns mp_out ON ja.JobProfileID = mp_out.from_job_profile_id
LEFT JOIN core_job_skill_requirements jsr ON ja.JobProfileID = jsr.JobProfileID
LEFT JOIN analytics_skill_demand_trends sdt ON jsr.Skill_ID = sdt.skill_id
LEFT JOIN analytics_job_families jf ON ja.JobProfileID = jf.job_profile_id
LEFT JOIN analytics_job_family_characteristics jfc ON jf.cluster_id = jfc.cluster_id
WHERE ja.JobProfileID = ?
  AND ja.JobProfile IS NOT NULL
GROUP BY ja.JobProfileID, ja.JobProfile, ja.JobFunction, 
         jfc.business_value_score, jfc.market_demand_level;

-- query_name: get_top_job_families
-- Get all job families with their characteristics for family analysis
SELECT 
    jfc.cluster_id,
    jfc.family_name,
    jfc.family_description,
    jfc.cluster_size,
    jfc.dominant_function,
    jfc.function_purity,
    jfc.business_value_score,
    jfc.career_pathway_potential,
    jfc.skill_transferability,
    jfc.market_demand_level,
    jfc.specialization_depth,
    COUNT(DISTINCT cwc.position_number) as current_workforce_count,
    AVG(js.enhanced_similarity_score) as avg_internal_similarity
FROM analytics_job_family_characteristics jfc
LEFT JOIN analytics_job_families jf ON jfc.cluster_id = jf.cluster_id
LEFT JOIN core_workforce_current cwc ON jf.job_profile_id = cwc.JobProfileID
LEFT JOIN analytics_job_similarities js 
    ON jf.job_profile_id = js.job_from 
    AND js.job_to IN (
        SELECT jf2.job_profile_id 
        FROM analytics_job_families jf2 
        WHERE jf2.cluster_id = jfc.cluster_id
    )
WHERE jfc.family_name IS NOT NULL
GROUP BY jfc.cluster_id, jfc.family_name, jfc.family_description, jfc.cluster_size,
         jfc.dominant_function, jfc.function_purity, jfc.business_value_score,
         jfc.career_pathway_potential, jfc.skill_transferability, jfc.market_demand_level,
         jfc.specialization_depth
ORDER BY jfc.business_value_score DESC, jfc.cluster_size DESC;

-- query_name: get_job_transition_recommendations
-- Get intelligent job transition recommendations based on analytics
SELECT 
    target_ja.JobProfileID as target_job_id,
    target_ja.JobProfile as target_job_title,
    target_ja.JobFunction as target_function,
    target_ja.ManagementLevel as target_level,
    
    -- Similarity Metrics
    js.enhanced_similarity_score,
    js.shared_defining_skills_count,
    js.rarity_weighted_score,
    js.skill_overlap_percentage,
    
    -- Movement History
    mp.movement_count,
    mp.success_rate,
    mp.avg_days_between,
    mp.movement_type,
    
    -- Family Compatibility
    CASE WHEN source_jf.cluster_id = target_jf.cluster_id THEN 1 ELSE 0 END as same_family,
    target_jfc.career_pathway_potential as target_career_potential,
    target_jfc.business_value_score as target_business_value,
    
    -- Current Opportunities
    COUNT(DISTINCT cwc.position_number) as available_positions,
    
    -- Recommendation Score (weighted combination)
    (js.enhanced_similarity_score * 0.4 + 
     COALESCE(mp.success_rate, 0.5) * 0.3 + 
     COALESCE(target_jfc.business_value_score, 0.5) * 0.3) as recommendation_score

FROM analytics_job_similarities js
JOIN core_job_architecture target_ja ON js.job_to = target_ja.JobProfileID
LEFT JOIN analytics_movement_patterns mp 
    ON js.job_from = mp.from_job_profile_id AND js.job_to = mp.to_job_profile_id
LEFT JOIN analytics_job_families source_jf ON js.job_from = source_jf.job_profile_id
LEFT JOIN analytics_job_families target_jf ON js.job_to = target_jf.job_profile_id
LEFT JOIN analytics_job_family_characteristics target_jfc ON target_jf.cluster_id = target_jfc.cluster_id
LEFT JOIN core_workforce_current cwc ON target_ja.JobProfileID = cwc.JobProfileID
WHERE js.job_from = ?
  AND js.enhanced_similarity_score >= 0.3  -- Minimum viability threshold
  AND target_ja.JobProfile IS NOT NULL
GROUP BY target_ja.JobProfileID, target_ja.JobProfile, target_ja.JobFunction, target_ja.ManagementLevel,
         js.enhanced_similarity_score, js.shared_defining_skills_count, js.rarity_weighted_score,
         js.skill_overlap_percentage, mp.movement_count, mp.success_rate, mp.avg_days_between,
         mp.movement_type, source_jf.cluster_id, target_jf.cluster_id, 
         target_jfc.career_pathway_potential, target_jfc.business_value_score
ORDER BY recommendation_score DESC, js.enhanced_similarity_score DESC
LIMIT 15;
