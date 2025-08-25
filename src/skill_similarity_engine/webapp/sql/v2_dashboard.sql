-- =================================================================
-- V2 DASHBOARD QUERIES - FAST ANALYTICS WIDGETS
-- Focused, fast queries for dashboard V2 analytics widgets
-- All queries optimized for <500ms response times
-- =================================================================

-- query_name: get_job_families_summary
-- Get job families overview for dashboard widget
SELECT 
    COUNT(DISTINCT cluster_id) as total_families,
    COUNT(DISTINCT job_profile_id) as jobs_in_families,
    AVG(silhouette_score) as avg_quality_score,
    COUNT(DISTINCT CASE WHEN silhouette_score > 0.5 THEN cluster_id END) as high_quality_families,
    MAX(cluster_size) as largest_family_size
FROM analytics_job_families
WHERE cluster_id IS NOT NULL;

-- query_name: get_movement_patterns_summary
-- Get movement patterns overview for dashboard widget
SELECT 
    COUNT(DISTINCT movement_pattern_id) as total_patterns,
    COUNT(DISTINCT from_job_profile_id) as source_jobs,
    COUNT(DISTINCT to_job_profile_id) as target_jobs,
    SUM(movement_count) as total_movements,
    AVG(CASE WHEN success_rate IS NOT NULL THEN success_rate END) as avg_success_rate
FROM analytics_movement_patterns
WHERE movement_count > 0;

-- query_name: get_skill_intelligence_summary
-- Get skill intelligence overview for dashboard widget
SELECT 
    COUNT(DISTINCT skill_id) as total_skills_analyzed,
    COUNT(DISTINCT CASE WHEN rarity_category = 'Rare' THEN skill_id END) as rare_skills,
    COUNT(DISTINCT CASE WHEN rarity_category = 'Very Rare' THEN skill_id END) as very_rare_skills,
    AVG(rarity_score) as avg_rarity_score
FROM analytics_skill_rarity
WHERE skill_id IS NOT NULL;

-- query_name: get_skill_bundles_summary
-- Get skill bundles count for dashboard widget
SELECT 
    COUNT(DISTINCT cluster_id) as skill_bundles_count
FROM analytics_skill_bundles
WHERE cluster_id IS NOT NULL;

-- query_name: get_skill_trends_summary  
-- Get skill demand trends overview for dashboard widget
SELECT 
    COUNT(DISTINCT skill_id) as skills_with_trends,
    COUNT(DISTINCT CASE WHEN velocity_category = 'growing' THEN skill_id END) as growing_skills,
    COUNT(DISTINCT CASE WHEN velocity_category = 'declining' THEN skill_id END) as declining_skills,
    COUNT(DISTINCT CASE WHEN velocity_category = 'stable' THEN skill_id END) as stable_skills,
    AVG(CASE WHEN short_term_cagr IS NOT NULL THEN short_term_cagr END) as avg_growth_rate
FROM analytics_skill_demand_trends
WHERE skill_id IS NOT NULL;

-- query_name: get_defining_skills_summary
-- Get defining skills analysis summary for dashboard widget
SELECT 
    COUNT(DISTINCT job_profile_id) as jobs_with_defining_skills,
    COUNT(DISTINCT skill_id) as total_defining_skills,
    AVG(defining_skill_score) as avg_defining_score,
    COUNT(DISTINCT CASE WHEN rarity_category = 'Rare' THEN skill_id END) as rare_defining_skills,
    COUNT(DISTINCT CASE WHEN defining_skill_rank <= 3 THEN job_profile_id END) as jobs_with_critical_skills
FROM analytics_job_defining_skills
WHERE defining_skill_score IS NOT NULL;

-- query_name: get_specialized_skills_summary
-- Get specialized skills overview for dashboard widget  
SELECT 
    COUNT(DISTINCT skill_id) as total_specialized_skills,
    COUNT(DISTINCT CASE WHEN specialization_category = 'Ultra-Rare' THEN skill_id END) as ultra_rare_specialized,
    COUNT(DISTINCT CASE WHEN strategic_importance = 'High' THEN skill_id END) as high_strategic_importance,
    COUNT(DISTINCT CASE WHEN investment_recommendation = 'Invest' THEN skill_id END) as investment_recommended,
    AVG(specialization_score) as avg_specialization_score
FROM analytics_specialized_skills
WHERE skill_id IS NOT NULL;

-- query_name: get_top_job_families
-- Get top 5 job families for dashboard widget
SELECT 
    cluster_id,
    cluster_name,
    cluster_size,
    silhouette_score
FROM analytics_job_families
WHERE cluster_name IS NOT NULL
GROUP BY cluster_id, cluster_name, cluster_size, silhouette_score
ORDER BY cluster_size DESC, silhouette_score DESC
LIMIT 5;

-- query_name: get_top_skill_bundles
-- Get top 5 skill bundles for dashboard widget
SELECT 
    cluster_id,
    bundle_name,
    bundle_size,
    business_value_score,
    training_feasibility,
    market_demand_level
FROM analytics_bundle_characteristics
WHERE bundle_name IS NOT NULL
ORDER BY business_value_score DESC, bundle_size DESC
LIMIT 5;

-- query_name: get_movement_hot_paths
-- Get top movement patterns for dashboard widget
SELECT 
    from_job_title.JobProfile as from_job,
    to_job_title.JobProfile as to_job,
    SUM(mp.movement_count) as total_movements,
    AVG(mp.success_rate) as avg_success_rate,
    mp.movement_type
FROM analytics_movement_patterns mp
LEFT JOIN core_job_architecture from_job_title ON mp.from_job_profile_id = from_job_title.JobProfileID
LEFT JOIN core_job_architecture to_job_title ON mp.to_job_profile_id = to_job_title.JobProfileID
WHERE mp.movement_count > 0
  AND from_job_title.JobProfile IS NOT NULL
  AND to_job_title.JobProfile IS NOT NULL
GROUP BY mp.from_job_profile_id, mp.to_job_profile_id, from_job_title.JobProfile, to_job_title.JobProfile, mp.movement_type
ORDER BY total_movements DESC, avg_success_rate DESC
LIMIT 5;

-- query_name: get_rare_skills_by_category
-- Get rare skills distribution by category for dashboard widget
SELECT 
    sr.category,
    COUNT(DISTINCT sr.skill_id) as rare_skills_count,
    AVG(sr.rarity_score) as avg_rarity_score,
    COUNT(DISTINCT CASE WHEN sr.rarity_category = 'Very Rare' THEN sr.skill_id END) as very_rare_count
FROM analytics_skill_rarity sr
WHERE sr.rarity_category IN ('Rare', 'Very Rare')
  AND sr.category IS NOT NULL
GROUP BY sr.category
ORDER BY rare_skills_count DESC
LIMIT 5;

-- query_name: get_architecture_health_summary
-- Get overall architecture health for dashboard widget
SELECT 
    COUNT(DISTINCT jf.cluster_id) as total_clusters,
    AVG(jfc.silhouette_score) as avg_silhouette_score,
    COUNT(DISTINCT CASE WHEN jfc.silhouette_score > 0.5 THEN jf.cluster_id END) as healthy_clusters,
    COUNT(DISTINCT CASE WHEN jfc.silhouette_score <= 0.3 THEN jf.cluster_id END) as poor_quality_clusters,
    SUM(jf.cluster_size) as total_jobs_clustered,
    AVG(jfc.business_value_score) as avg_business_value
FROM analytics_job_families jf
LEFT JOIN analytics_job_family_characteristics jfc ON jf.cluster_id = jfc.cluster_id
WHERE jf.cluster_id IS NOT NULL;
