-- =================================================================
-- SKILL INTELLIGENCE QUERIES - V2 ANALYTICS SCHEMA
-- Advanced skill intelligence using analytics tables for rarity,
-- bundles, demand trends, and specialization analysis
-- =================================================================

-- query_name: get_skill_comprehensive_analysis
-- Get comprehensive analysis for a specific skill including all analytics
SELECT 
    st.Skill_ID,
    st.Skill_Name,
    st.Category,
    st.Subcategory,
    st.SkillType,
    
    -- Rarity Analysis
    sr.prevalence_percentage,
    sr.rarity_category,
    sr.rarity_score,
    sr.total_profiles_with_skill,
    sr.is_defining_skill,
    sr.defining_for_jobs_count,
    
    -- Demand Trends
    sdt.velocity_category,
    sdt.trend_direction,
    sdt.trend_strength,
    sdt.current_prevalence_percent,
    sdt.short_term_cagr,
    sdt.medium_term_cagr,
    sdt.long_term_cagr,
    
    -- Bundle Information
    sb.bundle_name,
    sb.bundle_description,
    sb.bundle_size,
    sb.bundle_confidence,
    bc.specialization_area,
    bc.business_value_score as bundle_business_value,
    bc.training_feasibility,
    bc.market_demand_level as bundle_market_demand,
    
    -- Specialization Analysis
    ss.specialization_score,
    ss.specialization_category,
    ss.strategic_importance,
    ss.skill_lifecycle_stage,
    ss.investment_recommendation,
    ss.external_market_demand

FROM core_skills_taxonomy st
LEFT JOIN analytics_skill_rarity sr ON st.Skill_ID = sr.skill_id
LEFT JOIN analytics_skill_demand_trends sdt ON st.Skill_ID = sdt.skill_id
LEFT JOIN analytics_skill_bundles sb ON st.Skill_ID = sb.skill_id
LEFT JOIN analytics_bundle_characteristics bc ON sb.cluster_id = bc.cluster_id
LEFT JOIN analytics_specialized_skills ss ON st.Skill_ID = ss.skill_id
WHERE st.Skill_ID = ?
  AND st.Skill_Name IS NOT NULL;  -- FAIL-FAST validation

-- query_name: get_skill_bundle_analysis
-- Get detailed analysis of a specific skill bundle
SELECT 
    bc.cluster_id,
    bc.bundle_name,
    bc.bundle_description,
    bc.bundle_rationale,
    bc.bundle_size,
    bc.dominant_category,
    bc.category_purity,
    bc.application_level,
    bc.specialization_area,
    bc.business_value_score,
    bc.training_feasibility,
    bc.skill_complementarity,
    bc.market_demand_level,
    bc.typical_career_stage,
    bc.skill_acquisition_difficulty,
    COUNT(DISTINCT sb.skill_id) as actual_skills_count,
    COUNT(DISTINCT jsr.JobProfileID) as jobs_using_bundle_skills,
    AVG(sr.rarity_score) as avg_skill_rarity,
    COUNT(DISTINCT CASE WHEN sr.rarity_category = 'Rare' THEN sb.skill_id END) as rare_skills_in_bundle
FROM analytics_bundle_characteristics bc
LEFT JOIN analytics_skill_bundles sb ON bc.cluster_id = sb.cluster_id
LEFT JOIN core_job_skill_requirements jsr ON sb.skill_id = jsr.Skill_ID
LEFT JOIN analytics_skill_rarity sr ON sb.skill_id = sr.skill_id
WHERE bc.cluster_id = ?
  AND bc.bundle_name IS NOT NULL
GROUP BY bc.cluster_id, bc.bundle_name, bc.bundle_description, bc.bundle_rationale,
         bc.bundle_size, bc.dominant_category, bc.category_purity, bc.application_level,
         bc.specialization_area, bc.business_value_score, bc.training_feasibility,
         bc.skill_complementarity, bc.market_demand_level, bc.typical_career_stage,
         bc.skill_acquisition_difficulty;

-- query_name: get_skills_in_bundle
-- Get all skills within a specific bundle with their individual analytics
SELECT 
    sb.skill_id,
    sb.skill_name,
    sb.category,
    sb.subcategory,
    sb.skill_type,
    sb.prevalence_percent,
    sr.rarity_score,
    sr.rarity_category,
    sdt.velocity_category,
    sdt.trend_direction,
    COUNT(DISTINCT jsr.JobProfileID) as jobs_requiring_skill,
    COUNT(DISTINCT jds.job_profile_id) as jobs_where_defining,
    AVG(CASE WHEN jds.defining_skill_rank IS NOT NULL THEN jds.defining_skill_rank END) as avg_defining_rank
FROM analytics_skill_bundles sb
LEFT JOIN analytics_skill_rarity sr ON sb.skill_id = sr.skill_id
LEFT JOIN analytics_skill_demand_trends sdt ON sb.skill_id = sdt.skill_id
LEFT JOIN core_job_skill_requirements jsr ON sb.skill_id = jsr.Skill_ID
LEFT JOIN analytics_job_defining_skills jds ON sb.skill_id = jds.skill_id
WHERE sb.cluster_id = ?
  AND sb.skill_name IS NOT NULL
GROUP BY sb.skill_id, sb.skill_name, sb.category, sb.subcategory, sb.skill_type,
         sb.prevalence_percent, sr.rarity_score, sr.rarity_category,
         sdt.velocity_category, sdt.trend_direction
ORDER BY sr.rarity_score DESC, sb.prevalence_percent DESC;

-- query_name: get_rare_skills_analysis
-- Get comprehensive analysis of rare and specialized skills
SELECT 
    sr.skill_id,
    sr.skill_name,
    sr.category,
    sr.subcategory,
    sr.skill_type,
    sr.prevalence_percentage,
    sr.rarity_score,
    sr.rarity_category,
    sr.defining_for_jobs_count,
    
    -- Specialization Metrics
    ss.specialization_score,
    ss.specialization_category,
    ss.strategic_importance,
    ss.skill_lifecycle_stage,
    ss.investment_recommendation,
    
    -- Demand Trends
    sdt.velocity_category,
    sdt.trend_direction,
    sdt.trend_strength,
    
    -- Bundle Context
    sb.bundle_name,
    bc.business_value_score as bundle_value,
    
    -- Current Usage
    COUNT(DISTINCT jsr.JobProfileID) as current_jobs_count,
    COUNT(DISTINCT cwc.ORG_UNIT_NAME_2) as divisions_using

FROM analytics_skill_rarity sr
LEFT JOIN analytics_specialized_skills ss ON sr.skill_id = ss.skill_id
LEFT JOIN analytics_skill_demand_trends sdt ON sr.skill_id = sdt.skill_id
LEFT JOIN analytics_skill_bundles sb ON sr.skill_id = sb.skill_id
LEFT JOIN analytics_bundle_characteristics bc ON sb.cluster_id = bc.cluster_id
LEFT JOIN core_job_skill_requirements jsr ON sr.skill_id = jsr.Skill_ID
LEFT JOIN core_workforce_current cwc ON jsr.JobProfileID = cwc.JobProfileID
WHERE sr.rarity_category IN ('Rare', 'Very Rare') 
  OR ss.specialization_category IN ('Ultra-Rare', 'Rare')
  AND sr.skill_name IS NOT NULL
GROUP BY sr.skill_id, sr.skill_name, sr.category, sr.subcategory, sr.skill_type,
         sr.prevalence_percentage, sr.rarity_score, sr.rarity_category,
         sr.defining_for_jobs_count, ss.specialization_score, ss.specialization_category,
         ss.strategic_importance, ss.skill_lifecycle_stage, ss.investment_recommendation,
         sdt.velocity_category, sdt.trend_direction, sdt.trend_strength,
         sb.bundle_name, bc.business_value_score
ORDER BY sr.rarity_score DESC, ss.specialization_score DESC;

-- query_name: get_skill_demand_trends_analysis
-- Get trending skills analysis with growth metrics
SELECT 
    sdt.skill_id,
    sdt.skill_name,
    sdt.category,
    sdt.skill_type,
    sdt.jobs_requiring_skill,
    sdt.current_prevalence_percent,
    sdt.velocity_category,
    sdt.trend_direction,
    sdt.trend_strength,
    sdt.short_term_cagr,
    sdt.medium_term_cagr,
    sdt.long_term_cagr,
    sdt.total_movements,
    sdt.projected_demand_1yr,
    sdt.projected_demand_2yr,
    sdt.projected_demand_3yr,
    
    -- Rarity Context
    sr.rarity_category,
    sr.rarity_score,
    
    -- Bundle Context
    sb.bundle_name,
    bc.market_demand_level as bundle_market_demand,
    
    -- Specialization Context
    ss.strategic_importance,
    ss.investment_recommendation

FROM analytics_skill_demand_trends sdt
LEFT JOIN analytics_skill_rarity sr ON sdt.skill_id = sr.skill_id
LEFT JOIN analytics_skill_bundles sb ON sdt.skill_id = sb.skill_id
LEFT JOIN analytics_bundle_characteristics bc ON sb.cluster_id = bc.cluster_id
LEFT JOIN analytics_specialized_skills ss ON sdt.skill_id = ss.skill_id
WHERE sdt.velocity_category = ?  -- 'growing', 'declining', 'stable', etc.
  AND sdt.skill_name IS NOT NULL
ORDER BY sdt.short_term_cagr DESC, sdt.jobs_requiring_skill DESC
LIMIT 50;

-- query_name: get_skill_bundles_overview
-- Get overview of all skill bundles with key metrics
SELECT 
    bc.cluster_id,
    bc.bundle_name,
    bc.bundle_description,
    bc.bundle_size,
    bc.dominant_category,
    bc.specialization_area,
    bc.business_value_score,
    bc.training_feasibility,
    bc.market_demand_level,
    bc.typical_career_stage,
    COUNT(DISTINCT sb.skill_id) as actual_skills_count,
    COUNT(DISTINCT jsr.JobProfileID) as jobs_using_bundle,
    AVG(sr.rarity_score) as avg_rarity_score,
    COUNT(DISTINCT CASE WHEN sdt.velocity_category = 'growing' THEN sb.skill_id END) as growing_skills,
    COUNT(DISTINCT CASE WHEN sdt.velocity_category = 'declining' THEN sb.skill_id END) as declining_skills
FROM analytics_bundle_characteristics bc
LEFT JOIN analytics_skill_bundles sb ON bc.cluster_id = sb.cluster_id
LEFT JOIN core_job_skill_requirements jsr ON sb.skill_id = jsr.Skill_ID
LEFT JOIN analytics_skill_rarity sr ON sb.skill_id = sr.skill_id
LEFT JOIN analytics_skill_demand_trends sdt ON sb.skill_id = sdt.skill_id
WHERE bc.bundle_name IS NOT NULL
GROUP BY bc.cluster_id, bc.bundle_name, bc.bundle_description, bc.bundle_size,
         bc.dominant_category, bc.specialization_area, bc.business_value_score,
         bc.training_feasibility, bc.market_demand_level, bc.typical_career_stage
ORDER BY bc.business_value_score DESC, bc.bundle_size DESC;

-- query_name: get_skills_by_category_analysis
-- Get skill analysis grouped by category with analytics
SELECT 
    st.Category as skill_category,
    COUNT(DISTINCT st.Skill_ID) as total_skills,
    COUNT(DISTINCT jsr.JobProfileID) as jobs_using_category,
    
    -- Rarity Distribution
    COUNT(DISTINCT CASE WHEN sr.rarity_category = 'Common' THEN st.Skill_ID END) as common_skills,
    COUNT(DISTINCT CASE WHEN sr.rarity_category = 'Rare' THEN st.Skill_ID END) as rare_skills,
    COUNT(DISTINCT CASE WHEN sr.rarity_category = 'Very Rare' THEN st.Skill_ID END) as very_rare_skills,
    AVG(sr.rarity_score) as avg_rarity_score,
    
    -- Demand Trends
    COUNT(DISTINCT CASE WHEN sdt.velocity_category = 'growing' THEN st.Skill_ID END) as growing_skills,
    COUNT(DISTINCT CASE WHEN sdt.velocity_category = 'declining' THEN st.Skill_ID END) as declining_skills,
    COUNT(DISTINCT CASE WHEN sdt.velocity_category = 'stable' THEN st.Skill_ID END) as stable_skills,
    
    -- Bundle Presence
    COUNT(DISTINCT sb.cluster_id) as skill_bundles_count,
    AVG(bc.business_value_score) as avg_bundle_value,
    
    -- Specialization
    COUNT(DISTINCT ss.skill_id) as specialized_skills_count,
    COUNT(DISTINCT CASE WHEN ss.specialization_category = 'Ultra-Rare' THEN ss.skill_id END) as ultra_rare_specialized,
    
    -- Defining Skills
    COUNT(DISTINCT jds.skill_id) as defining_skills_count

FROM core_skills_taxonomy st
LEFT JOIN core_job_skill_requirements jsr ON st.Skill_ID = jsr.Skill_ID
LEFT JOIN analytics_skill_rarity sr ON st.Skill_ID = sr.skill_id
LEFT JOIN analytics_skill_demand_trends sdt ON st.Skill_ID = sdt.skill_id
LEFT JOIN analytics_skill_bundles sb ON st.Skill_ID = sb.skill_id
LEFT JOIN analytics_bundle_characteristics bc ON sb.cluster_id = bc.cluster_id
LEFT JOIN analytics_specialized_skills ss ON st.Skill_ID = ss.skill_id
LEFT JOIN analytics_job_defining_skills jds ON st.Skill_ID = jds.skill_id
WHERE st.Category IS NOT NULL
  AND st.Skill_Name IS NOT NULL
GROUP BY st.Category
ORDER BY jobs_using_category DESC, avg_rarity_score DESC;

-- query_name: get_skill_investment_recommendations
-- Get strategic skill investment recommendations based on analytics
SELECT 
    sr.skill_id,
    sr.skill_name,
    sr.category,
    sr.rarity_category,
    sr.rarity_score,
    
    -- Investment Factors
    ss.strategic_importance,
    ss.investment_recommendation,
    ss.skill_lifecycle_stage,
    
    -- Market Dynamics
    sdt.velocity_category,
    sdt.trend_direction,
    sdt.short_term_cagr,
    sdt.projected_demand_1yr,
    
    -- Business Context
    bc.business_value_score,
    bc.training_feasibility,
    bc.market_demand_level,
    
    -- Current State
    COUNT(DISTINCT jsr.JobProfileID) as current_jobs_using,
    COUNT(DISTINCT jds.job_profile_id) as jobs_where_defining,
    COUNT(DISTINCT cwc.ORG_UNIT_NAME_2) as divisions_present,
    
    -- Investment Priority Score (calculated)
    CASE 
        WHEN ss.strategic_importance = 'High' AND sdt.velocity_category = 'growing' THEN 95
        WHEN ss.strategic_importance = 'High' AND sr.rarity_category = 'Rare' THEN 90
        WHEN sdt.velocity_category = 'growing' AND bc.business_value_score > 0.7 THEN 85
        WHEN ss.strategic_importance = 'Medium' AND sdt.trend_direction = 'up' THEN 80
        WHEN sr.rarity_category = 'Rare' AND bc.training_feasibility = 'high' THEN 75
        WHEN bc.business_value_score > 0.6 AND bc.training_feasibility = 'medium' THEN 70
        ELSE 50
    END as investment_priority_score

FROM analytics_skill_rarity sr
LEFT JOIN analytics_specialized_skills ss ON sr.skill_id = ss.skill_id
LEFT JOIN analytics_skill_demand_trends sdt ON sr.skill_id = sdt.skill_id
LEFT JOIN analytics_skill_bundles sb ON sr.skill_id = sb.skill_id
LEFT JOIN analytics_bundle_characteristics bc ON sb.cluster_id = bc.cluster_id
LEFT JOIN core_job_skill_requirements jsr ON sr.skill_id = jsr.Skill_ID
LEFT JOIN analytics_job_defining_skills jds ON sr.skill_id = jds.skill_id
LEFT JOIN core_workforce_current cwc ON jsr.JobProfileID = cwc.JobProfileID
WHERE sr.skill_name IS NOT NULL
  AND (ss.strategic_importance IN ('High', 'Medium') 
       OR sdt.velocity_category = 'growing'
       OR sr.rarity_category IN ('Rare', 'Very Rare'))
GROUP BY sr.skill_id, sr.skill_name, sr.category, sr.rarity_category, sr.rarity_score,
         ss.strategic_importance, ss.investment_recommendation, ss.skill_lifecycle_stage,
         sdt.velocity_category, sdt.trend_direction, sdt.short_term_cagr, sdt.projected_demand_1yr,
         bc.business_value_score, bc.training_feasibility, bc.market_demand_level
ORDER BY investment_priority_score DESC, sr.rarity_score DESC
LIMIT 30;

-- query_name: search_skills_intelligence
-- Search skills with intelligent filtering and analytics
SELECT 
    st.Skill_ID,
    st.Skill_Name,
    st.Category,
    st.Subcategory,
    st.SkillType,
    sr.rarity_category,
    sr.rarity_score,
    sr.prevalence_percentage,
    sdt.velocity_category,
    sdt.trend_direction,
    sb.bundle_name,
    bc.business_value_score,
    ss.specialization_category,
    COUNT(DISTINCT jsr.JobProfileID) as jobs_count
FROM core_skills_taxonomy st
LEFT JOIN analytics_skill_rarity sr ON st.Skill_ID = sr.skill_id
LEFT JOIN analytics_skill_demand_trends sdt ON st.Skill_ID = sdt.skill_id
LEFT JOIN analytics_skill_bundles sb ON st.Skill_ID = sb.skill_id
LEFT JOIN analytics_bundle_characteristics bc ON sb.cluster_id = bc.cluster_id
LEFT JOIN analytics_specialized_skills ss ON st.Skill_ID = ss.skill_id
LEFT JOIN core_job_skill_requirements jsr ON st.Skill_ID = jsr.Skill_ID
WHERE st.Skill_Name IS NOT NULL
  AND (? = '' OR st.Skill_Name LIKE ? OR st.Category LIKE ?)  -- Search term
  AND (? = '' OR st.Category = ?)  -- Category filter
  AND (? = '' OR sr.rarity_category = ?)  -- Rarity filter
  AND (? = '' OR sdt.velocity_category = ?)  -- Trend filter
GROUP BY st.Skill_ID, st.Skill_Name, st.Category, st.Subcategory, st.SkillType,
         sr.rarity_category, sr.rarity_score, sr.prevalence_percentage,
         sdt.velocity_category, sdt.trend_direction, sb.bundle_name,
         bc.business_value_score, ss.specialization_category
ORDER BY sr.rarity_score DESC, jobs_count DESC
LIMIT 100;
