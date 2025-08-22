-- =================================================================
-- METADATA QUERIES - V2 SCHEMA MIGRATION
-- Database statistics, health checks, and system information
-- Migrated from V1 tables to V2 analytics schema
-- =================================================================

-- query_name: get_database_stats
-- Get comprehensive database statistics using V2 schema
SELECT 
    'Total Records' as metric,
    (SELECT COUNT(*) FROM core_job_architecture) +
    (SELECT COUNT(*) FROM core_job_skill_requirements) +
    (SELECT COUNT(*) FROM analytics_job_similarities) +
    (SELECT COUNT(*) FROM core_skills_taxonomy) +
    (SELECT COUNT(*) FROM core_workforce_current) as value
UNION ALL
SELECT 'Jobs', COUNT(*) FROM core_job_architecture
UNION ALL
SELECT 'Job Skills Relationships', COUNT(*) FROM core_job_skill_requirements
UNION ALL
SELECT 'Job Similarities', COUNT(*) FROM analytics_job_similarities
UNION ALL
SELECT 'Skills', COUNT(*) FROM core_skills_taxonomy
UNION ALL
SELECT 'Current Workforce', COUNT(*) FROM core_workforce_current
UNION ALL
SELECT 'Schema Metadata', COUNT(*) FROM sys_schema_metadata;

-- query_name: get_table_sizes
-- Get size information for each V2 table
SELECT 
    'core_job_architecture' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT job_function) as distinct_functions,
    MIN(JobProfileID) as min_id,
    MAX(JobProfileID) as max_id
FROM core_job_architecture
WHERE job_title IS NOT NULL
UNION ALL
SELECT 
    'core_skills_taxonomy',
    COUNT(*),
    COUNT(DISTINCT Category),
    MIN(Skill_ID),
    MAX(Skill_ID)
FROM core_skills_taxonomy
WHERE Skill_Name IS NOT NULL
UNION ALL
SELECT 
    'core_job_skill_requirements',
    COUNT(*),
    COUNT(DISTINCT JobProfileID),
    MIN(JobProfileID),
    MAX(JobProfileID)
FROM core_job_skill_requirements
UNION ALL
SELECT 
    'analytics_job_similarities',
    COUNT(*),
    COUNT(DISTINCT job_from),
    MIN(job_from),
    MAX(job_from)
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL
UNION ALL
SELECT 
    'core_workforce_current',
    COUNT(*),
    COUNT(DISTINCT JobProfileID),
    MIN(position_number),
    MAX(position_number)
FROM core_workforce_current;

-- query_name: get_data_quality_metrics
-- Check V2 data quality and completeness
SELECT 
    'Job Completeness' as metric,
    ROUND(
        (COUNT(CASE WHEN job_title IS NOT NULL AND job_function IS NOT NULL THEN 1 END) * 100.0) / COUNT(*), 
        2
    ) as percentage
FROM core_job_architecture
UNION ALL
SELECT 
    'Skills Completeness',
    ROUND(
        (COUNT(CASE WHEN Skill_Name IS NOT NULL AND Category IS NOT NULL THEN 1 END) * 100.0) / COUNT(*), 
        2
    )
FROM core_skills_taxonomy
UNION ALL
SELECT 
    'Jobs with Skills',
    ROUND(
        (COUNT(DISTINCT JobProfileID) * 100.0) / (SELECT COUNT(*) FROM core_job_architecture), 
        2
    )
FROM core_job_skill_requirements
UNION ALL
SELECT 
    'Jobs with Similarities',
    ROUND(
        (COUNT(DISTINCT job_from) * 100.0) / (SELECT COUNT(*) FROM core_job_architecture), 
        2
    )
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL;

-- query_name: get_similarity_metrics
-- Get similarity analysis metrics using enhanced similarity scores
SELECT 
    CASE 
        WHEN enhanced_similarity_score >= 0.8 THEN 'High'
        WHEN enhanced_similarity_score >= 0.6 THEN 'Medium'
        WHEN enhanced_similarity_score >= 0.4 THEN 'Low'
        ELSE 'Very Low'
    END as similarity_category,
    COUNT(*) as count,
    ROUND(AVG(enhanced_similarity_score), 4) as avg_score,
    ROUND(MIN(enhanced_similarity_score), 4) as min_score,
    ROUND(MAX(enhanced_similarity_score), 4) as max_score,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM analytics_job_similarities WHERE enhanced_similarity_score IS NOT NULL), 2) as percentage
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL
GROUP BY CASE 
    WHEN enhanced_similarity_score >= 0.8 THEN 'High'
    WHEN enhanced_similarity_score >= 0.6 THEN 'Medium'
    WHEN enhanced_similarity_score >= 0.4 THEN 'Low'
    ELSE 'Very Low'
END
ORDER BY avg_score DESC;

-- query_name: get_skills_distribution
-- Get distribution of skills across categories using V2 schema
SELECT 
    Category as skill_category,
    COUNT(*) as skill_count,
    COUNT(DISTINCT Subcategory) as subcategories,
    COUNT(DISTINCT jsr.JobProfileID) as jobs_using_category,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM core_skills_taxonomy), 2) as percentage_of_skills
FROM core_skills_taxonomy s
LEFT JOIN core_job_skill_requirements jsr ON s.Skill_ID = jsr.Skill_ID
WHERE s.Category IS NOT NULL
GROUP BY Category
ORDER BY skill_count DESC;

-- query_name: get_job_function_stats
-- Get statistics for each job function using V2 schema
SELECT 
    JobFunction as job_function,
    COUNT(*) as job_count,
    COUNT(DISTINCT ManagementLevel) as level_variations,
    COUNT(DISTINCT JobCategory) as category_variations,
    AVG(skill_counts.skill_count) as avg_skills_per_job,
    AVG(similarity_counts.similarity_count) as avg_similarities_per_job
FROM core_job_architecture j
LEFT JOIN (
    SELECT JobProfileID, COUNT(*) as skill_count
    FROM core_job_skill_requirements
    GROUP BY JobProfileID
) skill_counts ON j.JobProfileID = skill_counts.JobProfileID
LEFT JOIN (
    SELECT job_from, COUNT(*) as similarity_count
    FROM analytics_job_similarities
    WHERE enhanced_similarity_score >= 0.6
      AND enhanced_similarity_score IS NOT NULL
    GROUP BY job_from
) similarity_counts ON j.JobProfileID = similarity_counts.job_from
WHERE j.JobFunction IS NOT NULL
  AND j.JobProfile IS NOT NULL
GROUP BY JobFunction
ORDER BY job_count DESC;

-- query_name: get_schema_metadata
-- Get V2 schema information and metadata
SELECT 
    'core_job_architecture' as table_name,
    name as column_name,
    type as data_type,
    CASE WHEN "notnull" = 1 THEN 'NO' ELSE 'YES' END as is_nullable
FROM pragma_table_info('core_job_architecture')

UNION ALL

SELECT 
    'core_skills_taxonomy' as table_name,
    name as column_name,
    type as data_type,
    CASE WHEN "notnull" = 1 THEN 'NO' ELSE 'YES' END as is_nullable
FROM pragma_table_info('core_skills_taxonomy')

UNION ALL

SELECT 
    'core_job_skill_requirements' as table_name,
    name as column_name,
    type as data_type,
    CASE WHEN "notnull" = 1 THEN 'NO' ELSE 'YES' END as is_nullable
FROM pragma_table_info('core_job_skill_requirements')

UNION ALL

SELECT 
    'analytics_job_similarities' as table_name,
    name as column_name,
    type as data_type,
    CASE WHEN "notnull" = 1 THEN 'NO' ELSE 'YES' END as is_nullable
FROM pragma_table_info('analytics_job_similarities')

UNION ALL

SELECT 
    'core_workforce_current' as table_name,
    name as column_name,
    type as data_type,
    CASE WHEN "notnull" = 1 THEN 'NO' ELSE 'YES' END as is_nullable
FROM pragma_table_info('core_workforce_current')

UNION ALL

SELECT 
    'analytics_job_defining_skills' as table_name,
    name as column_name,
    type as data_type,
    CASE WHEN "notnull" = 1 THEN 'NO' ELSE 'YES' END as is_nullable
FROM pragma_table_info('analytics_job_defining_skills')

UNION ALL

SELECT 
    'analytics_skill_rarity' as table_name,
    name as column_name,
    type as data_type,
    CASE WHEN "notnull" = 1 THEN 'NO' ELSE 'YES' END as is_nullable
FROM pragma_table_info('analytics_skill_rarity')

UNION ALL

SELECT 
    'analytics_movement_patterns' as table_name,
    name as column_name,
    type as data_type,
    CASE WHEN "notnull" = 1 THEN 'NO' ELSE 'YES' END as is_nullable
FROM pragma_table_info('analytics_movement_patterns')

UNION ALL

SELECT 
    'analytics_job_families' as table_name,
    name as column_name,
    type as data_type,
    CASE WHEN "notnull" = 1 THEN 'NO' ELSE 'YES' END as is_nullable
FROM pragma_table_info('analytics_job_families')

UNION ALL

SELECT 
    'analytics_skill_bundles' as table_name,
    name as column_name,
    type as data_type,
    CASE WHEN "notnull" = 1 THEN 'NO' ELSE 'YES' END as is_nullable
FROM pragma_table_info('analytics_skill_bundles');

-- query_name: get_database_health_check
-- Perform basic V2 database health checks
SELECT 
    'Database Connection' as check_name,
    'OK' as status,
    'Successfully connected to V2 database' as details
UNION ALL
SELECT 
    'V2 Table Integrity',
    CASE WHEN (
        (SELECT COUNT(*) FROM core_job_architecture) > 0 AND
        (SELECT COUNT(*) FROM core_skills_taxonomy) > 0 AND
        (SELECT COUNT(*) FROM core_job_skill_requirements) > 0 AND
        (SELECT COUNT(*) FROM analytics_job_similarities) > 0
    ) THEN 'OK' ELSE 'WARNING' END,
    'All main V2 tables have data'
UNION ALL
SELECT 
    'V2 Referential Integrity',
    CASE WHEN (
        SELECT COUNT(*) FROM core_job_skill_requirements jsr 
        LEFT JOIN core_job_architecture ja ON jsr.JobProfileID = ja.JobProfileID 
        WHERE ja.JobProfileID IS NULL
    ) = 0 THEN 'OK' ELSE 'ERROR' END,
    'V2 foreign key relationships are valid'
UNION ALL
SELECT 
    'V2 Data Completeness',
    CASE WHEN (
        SELECT COUNT(*) FROM core_job_architecture WHERE JobProfile IS NULL OR JobFunction IS NULL
    ) = 0 THEN 'OK' ELSE 'WARNING' END,
    'V2 core fields are populated'
UNION ALL
SELECT 
    'Analytics Tables Health',
    CASE WHEN (
        (SELECT COUNT(*) FROM analytics_job_similarities WHERE enhanced_similarity_score IS NOT NULL) > 0 AND
        (SELECT COUNT(*) FROM analytics_job_defining_skills) > 0 AND
        (SELECT COUNT(*) FROM analytics_skill_rarity) > 0
    ) THEN 'OK' ELSE 'WARNING' END,
    'V2 analytics tables are populated'
UNION ALL
SELECT 
    'Enhanced Similarity Scores',
    CASE WHEN (
        SELECT COUNT(*) FROM analytics_job_similarities 
        WHERE enhanced_similarity_score IS NOT NULL 
        AND enhanced_similarity_score > 0
    ) > 1000 THEN 'OK' ELSE 'WARNING' END,
    'Enhanced similarity scores are calculated';

-- query_name: get_performance_metrics
-- Get V2 performance indicators
SELECT 
    'Average Skills per Job' as metric,
    ROUND(AVG(skill_count), 2) as value
FROM (
    SELECT JobProfileID, COUNT(*) as skill_count
    FROM core_job_skill_requirements
    GROUP BY JobProfileID
)
UNION ALL
SELECT 
    'Average Similarities per Job',
    ROUND(AVG(similarity_count), 2)
FROM (
    SELECT job_from, COUNT(*) as similarity_count
    FROM analytics_job_similarities
    WHERE enhanced_similarity_score >= 0.5
      AND enhanced_similarity_score IS NOT NULL
    GROUP BY job_from
)
UNION ALL
SELECT 
    'Enhanced Similarity Coverage (%)',
    ROUND(
        (COUNT(DISTINCT job_from) * 100.0) / (SELECT COUNT(*) FROM core_job_architecture), 
        2
    )
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL
UNION ALL
SELECT 
    'Skills Coverage (%)',
    ROUND(
        (COUNT(DISTINCT JobProfileID) * 100.0) / (SELECT COUNT(*) FROM core_job_architecture), 
        2
    )
FROM core_job_skill_requirements;

-- query_name: get_platform_metrics
-- Get strategic platform metrics for homepage dashboard using V2 schema
SELECT 
    'jobs_count' as metric,
    COUNT(*) as count
FROM core_job_architecture
WHERE JobProfile IS NOT NULL
UNION ALL
SELECT 
    'skills_count',
    COUNT(*)
FROM core_skills_taxonomy
WHERE Skill_Name IS NOT NULL
UNION ALL
SELECT 
    'skills_in_use_count',
    COUNT(DISTINCT Skill_ID)
FROM core_job_skill_requirements
UNION ALL
SELECT 
    'positions_count',
    COUNT(DISTINCT position_number)
FROM core_workforce_current
WHERE position_number IS NOT NULL
UNION ALL
SELECT 
    'pathways_count',
    COUNT(*)
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL
UNION ALL
SELECT 
    'job_families_count',
    COUNT(DISTINCT cluster_id)
FROM analytics_job_families
UNION ALL
SELECT 
    'job_functions_count',
    COUNT(DISTINCT JobFunction)
FROM core_job_architecture
WHERE JobFunction IS NOT NULL
UNION ALL
SELECT 
    'divisions_count',
    COUNT(DISTINCT ORG_UNIT_NAME_2)
FROM core_workforce_current
WHERE ORG_UNIT_NAME_2 IS NOT NULL AND ORG_UNIT_NAME_2 != ''
UNION ALL
SELECT 
    'defining_skills_count',
    COUNT(*)
FROM analytics_job_defining_skills
UNION ALL
SELECT 
    'skill_bundles_count',
    COUNT(DISTINCT cluster_id)
FROM analytics_skill_bundles
UNION ALL
SELECT 
    'movement_patterns_count',
    COUNT(*)
FROM analytics_movement_patterns
WHERE movement_count > 0;

-- query_name: get_top_job_functions
-- Get top job functions with counts for homepage dashboard
SELECT 
    JobFunction as job_function,
    COUNT(*) as job_count
FROM core_job_architecture 
WHERE JobFunction IS NOT NULL
  AND JobProfile IS NOT NULL
GROUP BY JobFunction
ORDER BY job_count DESC
LIMIT 10;

-- query_name: get_career_pathway_analysis
-- Career pathway analysis by job function using analytics_job_similarities
SELECT 
    ja1.JobFunction as source_function,
    ja2.JobFunction as target_function,
    COALESCE(mp.movement_type, 'lateral') as career_move_type,
    COUNT(*) as pathway_count,
    ROUND(AVG(js.enhanced_similarity_score), 3) as avg_similarity,
    ROUND(AVG(js.shared_defining_skills_count), 1) as avg_shared_defining_skills,
    ROUND(AVG(js.rarity_weighted_score), 3) as avg_rarity_weighted_score
FROM analytics_job_similarities js
JOIN core_job_architecture ja1 ON js.job_from = ja1.JobProfileID
JOIN core_job_architecture ja2 ON js.job_to = ja2.JobProfileID
LEFT JOIN analytics_movement_patterns mp 
    ON js.job_from = mp.from_job_profile_id 
    AND js.job_to = mp.to_job_profile_id
WHERE js.enhanced_similarity_score >= 0.6  -- Focus on meaningful similarities
  AND js.enhanced_similarity_score IS NOT NULL
  AND ja1.JobFunction IS NOT NULL
  AND ja2.JobFunction IS NOT NULL
GROUP BY ja1.JobFunction, ja2.JobFunction, mp.movement_type
HAVING pathway_count >= 5  -- Statistical significance
ORDER BY avg_similarity DESC, pathway_count DESC;

-- query_name: get_mobility_hubs
-- Most connected job functions (mobility hubs) analysis using V2 analytics
SELECT 
    ja.JobFunction as job_function,
    COUNT(DISTINCT CASE WHEN js.job_from = ja.JobProfileID THEN js.job_to END) as outbound_pathways,
    COUNT(DISTINCT CASE WHEN js.job_to = ja.JobProfileID THEN js.job_from END) as inbound_pathways,
    (COUNT(DISTINCT CASE WHEN js.job_from = ja.JobProfileID THEN js.job_to END) + 
     COUNT(DISTINCT CASE WHEN js.job_to = ja.JobProfileID THEN js.job_from END)) as total_connectivity,
    ROUND(
        ((COUNT(DISTINCT CASE WHEN js.job_from = ja.JobProfileID THEN js.job_to END) + 
          COUNT(DISTINCT CASE WHEN js.job_to = ja.JobProfileID THEN js.job_from END)) * 100.0) / 
        (SELECT COUNT(*) FROM core_job_architecture WHERE JobProfile IS NOT NULL), 
        1
    ) as connectivity_percentage,
    ROUND(AVG(js.enhanced_similarity_score), 3) as avg_similarity_score
FROM core_job_architecture ja
LEFT JOIN analytics_job_similarities js 
    ON (ja.JobProfileID = js.job_from OR ja.JobProfileID = js.job_to)
    AND js.enhanced_similarity_score >= 0.6
    AND js.enhanced_similarity_score IS NOT NULL
WHERE ja.JobFunction IS NOT NULL
  AND ja.JobProfile IS NOT NULL
GROUP BY ja.JobFunction
ORDER BY total_connectivity DESC
LIMIT 10;

-- query_name: get_career_insights_summary
-- Summary metrics for career pathway insights dashboard using V2 analytics
SELECT 
    'total_pathway_combinations' as metric,
    COUNT(DISTINCT ja1.JobFunction || '→' || ja2.JobFunction) as value
FROM analytics_job_similarities js
JOIN core_job_architecture ja1 ON js.job_from = ja1.JobProfileID
JOIN core_job_architecture ja2 ON js.job_to = ja2.JobProfileID
WHERE js.enhanced_similarity_score >= 0.5
  AND js.enhanced_similarity_score IS NOT NULL
  AND ja1.JobFunction IS NOT NULL
  AND ja2.JobFunction IS NOT NULL
UNION ALL
SELECT 
    'total_enhanced_pathways',
    COUNT(*)
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL
UNION ALL
SELECT 
    'avg_enhanced_similarity',
    ROUND(AVG(enhanced_similarity_score), 3)
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL
UNION ALL
SELECT 
    'defining_skills_pairs',
    COUNT(*)
FROM analytics_job_similarities
WHERE shared_defining_skills_count > 0
UNION ALL
SELECT 
    'job_families_discovered',
    COUNT(DISTINCT cluster_id)
FROM analytics_job_families
UNION ALL
SELECT 
    'skill_bundles_identified',
    COUNT(DISTINCT cluster_id)
FROM analytics_skill_bundles
UNION ALL
SELECT 
    'movement_patterns_analyzed',
    COUNT(DISTINCT from_job_profile_id || '->' || to_job_profile_id)
FROM analytics_movement_patterns
WHERE movement_count > 0;

-- query_name: get_similarity_distribution
-- Workforce mobility readiness analysis using enhanced similarity scores
SELECT 
    CASE 
        WHEN enhanced_similarity_score >= 0.7 THEN 'High'
        WHEN enhanced_similarity_score >= 0.4 THEN 'Medium'
        ELSE 'Low'
    END as mobility_potential,
    COUNT(*) as job_pairs,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM analytics_job_similarities WHERE enhanced_similarity_score IS NOT NULL), 1) as percentage,
    ROUND(MIN(enhanced_similarity_score), 3) as min_score,
    ROUND(MAX(enhanced_similarity_score), 3) as max_score,
    ROUND(AVG(enhanced_similarity_score), 3) as avg_score,
    ROUND(AVG(rarity_weighted_score), 3) as avg_rarity_weighted_score
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL
GROUP BY CASE 
    WHEN enhanced_similarity_score >= 0.7 THEN 'High'
    WHEN enhanced_similarity_score >= 0.4 THEN 'Medium'
    ELSE 'Low'
END
ORDER BY avg_score DESC;

-- query_name: get_similarity_statistics
-- Raw enhanced similarity statistics for workforce mobility analysis
SELECT 
    'total_records' as metric,
    COUNT(*) as value
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL
UNION ALL
SELECT 
    'min_enhanced_score',
    ROUND(MIN(enhanced_similarity_score), 4)
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL
UNION ALL
SELECT 
    'max_enhanced_score',
    ROUND(MAX(enhanced_similarity_score), 4)
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL
UNION ALL
SELECT 
    'avg_enhanced_score',
    ROUND(AVG(enhanced_similarity_score), 3)
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL
UNION ALL
SELECT 
    'unique_enhanced_scores',
    COUNT(DISTINCT enhanced_similarity_score)
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL
UNION ALL
SELECT 
    'perfect_matches',
    COUNT(CASE WHEN enhanced_similarity_score >= 0.99 THEN 1 END)
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL
UNION ALL
SELECT 
    'high_mobility_pairs',
    COUNT(CASE WHEN enhanced_similarity_score >= 0.7 THEN 1 END)
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL
UNION ALL
SELECT 
    'defining_skills_enhanced_pairs',
    COUNT(CASE WHEN shared_defining_skills_count > 0 THEN 1 END)
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL;

-- query_name: get_strategic_recommendations
-- Strategic recommendations using V2 analytics data
SELECT 
    'workforce_resilience' as category,
    'Skills Concentration Risk Analysis' as title,
    'HIGH' as priority,
    'V2 analytics identified rare skills concentrated in specific job families. Recommend cross-training programs and geographic skill distribution using the defining skills analysis.' as recommendation,
    (SELECT COUNT(*) FROM analytics_skill_rarity WHERE rarity_category = 'Rare') as metric_count,
    'rare skills identified' as metric_label
UNION ALL
SELECT 
    'career_mobility',
    'Enhanced Mobility Hub Optimization',
    'MEDIUM',
    'V2 similarity analysis with rarity weighting identified key mobility hubs. Leverage enhanced scoring for strategic workforce transitions and career pathway planning.',
    (SELECT COUNT(DISTINCT JobFunction) FROM (
        SELECT ja.JobFunction, COUNT(*) as connections
        FROM core_job_architecture ja
        JOIN analytics_job_similarities js ON ja.JobProfileID = js.job_from
        WHERE js.enhanced_similarity_score >= 0.7
        GROUP BY ja.JobFunction
        HAVING connections > 50
    )) as metric_count,
    'high-connectivity functions'
UNION ALL
SELECT 
    'workforce_readiness',
    'Defining Skills Transition Analysis',
    'MEDIUM',
    'Analysis shows significant opportunities for skills-based transitions. Focus development on roles with high defining skills overlap for optimal deployment flexibility.',
    (SELECT ROUND(AVG(shared_defining_skills_count)) FROM analytics_job_similarities WHERE enhanced_similarity_score >= 0.6) as metric_count,
    'avg defining skills overlap'
UNION ALL
SELECT 
    'capability_development',
    'Job Family Cross-Pollination',
    'LOW',
    'DBSCAN clustering identified ' || (SELECT COUNT(DISTINCT cluster_id) FROM analytics_job_families) || ' distinct job families. Consider structured capability exchange programs leveraging family insights.',
    (SELECT COUNT(DISTINCT cluster_id) FROM analytics_job_families) as metric_count,
    'job families identified'
UNION ALL
SELECT 
    'skills_intelligence',
    'Skill Bundle Development Strategy',
    'MEDIUM',
    'V2 skill bundling analysis identified complementary skill clusters. Leverage ' || (SELECT COUNT(DISTINCT cluster_id) FROM analytics_skill_bundles) || ' skill bundles for targeted development programs.',
    (SELECT COUNT(DISTINCT cluster_id) FROM analytics_skill_bundles) as metric_count,
    'skill bundles available';

-- query_name: get_cross_family_mobility_opportunities
-- Cross-family mobility opportunities using V2 analytics data
SELECT 
    ja1.JobFunction as source_family,
    ja2.JobFunction as target_family,
    COUNT(*) as similarity_pairs,
    ROUND(AVG(js.enhanced_similarity_score), 3) as avg_similarity,
    ROUND(MIN(js.enhanced_similarity_score), 3) as min_similarity,
    ROUND(MAX(js.enhanced_similarity_score), 3) as max_similarity,
    COUNT(DISTINCT cw1.ORG_UNIT_NAME_2) as source_divisions,
    COUNT(DISTINCT cw2.ORG_UNIT_NAME_2) as target_divisions,
    CASE 
        WHEN AVG(js.enhanced_similarity_score) >= 0.6 THEN 'HIGH OPPORTUNITY'
        WHEN AVG(js.enhanced_similarity_score) >= 0.4 THEN 'MEDIUM OPPORTUNITY'
        ELSE 'LOW OPPORTUNITY'
    END as mobility_potential,
    ROUND(AVG(js.shared_defining_skills_count), 1) as avg_shared_defining_skills
FROM analytics_job_similarities js
JOIN core_job_architecture ja1 ON js.job_from = ja1.JobProfileID
JOIN core_job_architecture ja2 ON js.job_to = ja2.JobProfileID
LEFT JOIN core_workforce_current cw1 ON ja1.JobProfileID = cw1.JobProfileID
LEFT JOIN core_workforce_current cw2 ON ja2.JobProfileID = cw2.JobProfileID
WHERE js.enhanced_similarity_score >= 0.3  -- Minimum threshold for analysis
  AND js.enhanced_similarity_score IS NOT NULL
  AND ja1.JobFunction != ja2.JobFunction  -- Cross-family only
  AND ja1.JobFunction IS NOT NULL
  AND ja2.JobFunction IS NOT NULL
GROUP BY ja1.JobFunction, ja2.JobFunction
HAVING similarity_pairs >= 10  -- Statistical significance
ORDER BY avg_similarity DESC, similarity_pairs DESC
LIMIT 20;

-- query_name: get_skills_concentration_analysis
-- Skills concentration risk analysis using V2 analytics and rarity data
SELECT 
    st.Category as skill_category,
    COUNT(DISTINCT st.Skill_ID) as unique_skills,
    COUNT(jsr.JobProfileID) as total_job_mappings,
    ROUND(COUNT(jsr.JobProfileID) * 1.0 / COUNT(DISTINCT st.Skill_ID), 1) as avg_jobs_per_skill,
    COUNT(CASE WHEN sr.rarity_category = 'Rare' THEN 1 END) as rare_skills_count,
    COUNT(CASE WHEN ds.job_profile_id IS NOT NULL THEN 1 END) as defining_skills_count,
    CASE 
        WHEN COUNT(jsr.JobProfileID) * 1.0 / COUNT(DISTINCT st.Skill_ID) > 15 THEN 'HIGH CONCENTRATION'
        WHEN COUNT(jsr.JobProfileID) * 1.0 / COUNT(DISTINCT st.Skill_ID) > 8 THEN 'MEDIUM CONCENTRATION'
        ELSE 'LOW CONCENTRATION'
    END as concentration_risk
FROM core_skills_taxonomy st
JOIN core_job_skill_requirements jsr ON st.Skill_ID = jsr.Skill_ID
LEFT JOIN analytics_skill_rarity sr ON st.Skill_ID = sr.skill_id
LEFT JOIN analytics_job_defining_skills ds ON st.Skill_ID = ds.skill_id
WHERE st.Category IS NOT NULL
GROUP BY st.Category
ORDER BY avg_jobs_per_skill DESC;

-- query_name: get_v2_analytics_health
-- V2 Analytics-specific health check for new tables
SELECT 
    'Job Defining Skills Coverage' as check_name,
    CASE WHEN (
        SELECT COUNT(DISTINCT job_profile_id) FROM analytics_job_defining_skills
    ) > (
        SELECT COUNT(*) FROM core_job_architecture WHERE job_title IS NOT NULL
    ) * 0.5 THEN 'OK' ELSE 'WARNING' END as status,
    'Defining skills analysis covers majority of jobs' as details
UNION ALL
SELECT 
    'Skill Rarity Analysis',
    CASE WHEN (
        SELECT COUNT(*) FROM analytics_skill_rarity WHERE rarity_score IS NOT NULL
    ) > 1000 THEN 'OK' ELSE 'WARNING' END,
    'Skill rarity scores calculated'
UNION ALL
SELECT 
    'Job Families Clustering',
    CASE WHEN (
        SELECT COUNT(DISTINCT cluster_id) FROM analytics_job_families
    ) > 5 THEN 'OK' ELSE 'WARNING' END,
    'Job families identified through clustering'
UNION ALL
SELECT 
    'Skill Bundles Analysis',
    CASE WHEN (
        SELECT COUNT(DISTINCT cluster_id) FROM analytics_skill_bundles
    ) > 10 THEN 'OK' ELSE 'WARNING' END,
    'Skill bundles created from clustering'
UNION ALL
SELECT 
    'Movement Patterns Data',
    CASE WHEN (
        SELECT COUNT(*) FROM analytics_movement_patterns WHERE movement_count > 0
    ) > 1000 THEN 'OK' ELSE 'WARNING' END,
    'Historical movement patterns analyzed'
UNION ALL
SELECT 
    'Enhanced Similarity Quality',
    CASE WHEN (
        SELECT COUNT(*) FROM analytics_job_similarities 
        WHERE enhanced_similarity_score != similarity_score
        AND enhanced_similarity_score IS NOT NULL
        AND similarity_score IS NOT NULL
    ) > 100 THEN 'OK' ELSE 'WARNING' END,
    'Enhanced similarity differs from basic similarity';

-- query_name: get_organizational_divisions
-- Get unique divisions for organizational filters using V2 schema
SELECT DISTINCT ORG_UNIT_NAME_2 as Division
FROM core_workforce_current 
WHERE ORG_UNIT_NAME_2 IS NOT NULL AND ORG_UNIT_NAME_2 != ''
ORDER BY ORG_UNIT_NAME_2;

-- query_name: get_organizational_business_units
-- Get unique business units for organizational filters using V2 schema
SELECT DISTINCT ORG_UNIT_NAME_3 as Business_Unit
FROM core_workforce_current 
WHERE ORG_UNIT_NAME_3 IS NOT NULL AND ORG_UNIT_NAME_3 != ''
ORDER BY ORG_UNIT_NAME_3;

-- query_name: get_organizational_locations
-- Get unique locations for organizational filters using V2 schema
SELECT DISTINCT Location
FROM core_workforce_current 
WHERE Location IS NOT NULL AND Location != ''
ORDER BY Location;

-- query_name: get_organizational_regions
-- Get unique regions for organizational filters using V2 schema
SELECT DISTINCT Rg
FROM core_workforce_current 
WHERE Rg IS NOT NULL AND Rg != ''
ORDER BY Rg;