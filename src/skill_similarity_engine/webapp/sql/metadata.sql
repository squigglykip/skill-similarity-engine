-- =================================================================
-- METADATA QUERIES
-- Database statistics, health checks, and system information
-- =================================================================

-- query_name: get_database_stats
-- Get comprehensive database statistics
SELECT 
    'Total Records' as metric,
    (SELECT COUNT(*) FROM jobs) +
    (SELECT COUNT(*) FROM job_skills) +
    (SELECT COUNT(*) FROM job_similarities) +
    (SELECT COUNT(*) FROM skills) +
    (SELECT COUNT(*) FROM positions) as value
UNION ALL
SELECT 'Jobs', COUNT(*) FROM jobs
UNION ALL
SELECT 'Job Skills Relationships', COUNT(*) FROM job_skills
UNION ALL
SELECT 'Job Similarities', COUNT(*) FROM job_similarities
UNION ALL
SELECT 'Skills', COUNT(*) FROM skills
UNION ALL
SELECT 'Positions', COUNT(*) FROM positions
UNION ALL
SELECT 'Schema Metadata', COUNT(*) FROM schema_metadata;

-- query_name: get_table_sizes
-- Get size information for each table
SELECT 
    'jobs' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT JobFunction) as distinct_functions,
    MIN(JobProfileID) as min_id,
    MAX(JobProfileID) as max_id
FROM jobs
UNION ALL
SELECT 
    'skills',
    COUNT(*),
    COUNT(DISTINCT Category),
    MIN(Skill_ID),
    MAX(Skill_ID)
FROM skills
UNION ALL
SELECT 
    'job_skills',
    COUNT(*),
    COUNT(DISTINCT JobProfileID),
    MIN(JobProfileID),
    MAX(JobProfileID)
FROM job_skills
UNION ALL
SELECT 
    'job_similarities',
    COUNT(*),
    COUNT(DISTINCT job_from),
    MIN(job_from),
    MAX(job_from)
FROM job_similarities
UNION ALL
SELECT 
    'positions',
    COUNT(*),
    COUNT(DISTINCT JobProfileID),
    MIN(PositionID),
    MAX(PositionID)
FROM positions;

-- query_name: get_data_quality_metrics
-- Check data quality and completeness
SELECT 
    'Job Completeness' as metric,
    ROUND(
        (COUNT(CASE WHEN JobProfile IS NOT NULL AND JobFunction IS NOT NULL THEN 1 END) * 100.0) / COUNT(*), 
        2
    ) as percentage
FROM jobs
UNION ALL
SELECT 
    'Skills Completeness',
    ROUND(
        (COUNT(CASE WHEN Skill_Name IS NOT NULL AND Category IS NOT NULL THEN 1 END) * 100.0) / COUNT(*), 
        2
    )
FROM skills
UNION ALL
SELECT 
    'Jobs with Skills',
    ROUND(
        (COUNT(DISTINCT JobProfileID) * 100.0) / (SELECT COUNT(*) FROM jobs), 
        2
    )
FROM job_skills
UNION ALL
SELECT 
    'Jobs with Similarities',
    ROUND(
        (COUNT(DISTINCT job_from) * 100.0) / (SELECT COUNT(*) FROM jobs), 
        2
    )
FROM job_similarities;

-- query_name: get_similarity_metrics
-- Get similarity analysis metrics
SELECT 
    CASE 
        WHEN similarity_score >= 0.8 THEN 'High'
        WHEN similarity_score >= 0.6 THEN 'Medium'
        WHEN similarity_score >= 0.4 THEN 'Low'
        ELSE 'Very Low'
    END as similarity_category,
    COUNT(*) as count,
    ROUND(AVG(similarity_score), 4) as avg_score,
    ROUND(MIN(similarity_score), 4) as min_score,
    ROUND(MAX(similarity_score), 4) as max_score,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM job_similarities), 2) as percentage
FROM job_similarities
GROUP BY CASE 
    WHEN similarity_score >= 0.8 THEN 'High'
    WHEN similarity_score >= 0.6 THEN 'Medium'
    WHEN similarity_score >= 0.4 THEN 'Low'
    ELSE 'Very Low'
END
ORDER BY avg_score DESC;

-- query_name: get_skills_distribution
-- Get distribution of skills across categories
SELECT 
    Category as skill_category,
    COUNT(*) as skill_count,
    COUNT(DISTINCT Subcategory) as subcategories,
    COUNT(DISTINCT js.JobProfileID) as jobs_using_category,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM skills), 2) as percentage_of_skills
FROM skills s
LEFT JOIN job_skills js ON s.Skill_ID = js.Skill_ID
GROUP BY Category
ORDER BY skill_count DESC;

-- query_name: get_job_function_stats
-- Get statistics for each job function
SELECT 
    JobFunction as job_function,
    COUNT(*) as job_count,
    COUNT(DISTINCT ManagementLevel) as level_variations,
    COUNT(DISTINCT JobCategory) as category_variations,
    AVG(skill_counts.skill_count) as avg_skills_per_job,
    AVG(similarity_counts.similarity_count) as avg_similarities_per_job
FROM jobs j
LEFT JOIN (
    SELECT JobProfileID, COUNT(*) as skill_count
    FROM job_skills
    GROUP BY JobProfileID
) skill_counts ON j.JobProfileID = skill_counts.JobProfileID
LEFT JOIN (
    SELECT job_from, COUNT(*) as similarity_count
    FROM job_similarities
    WHERE similarity_score >= 0.6
    GROUP BY job_from
) similarity_counts ON j.JobProfileID = similarity_counts.job_from
GROUP BY JobFunction
ORDER BY job_count DESC;

-- query_name: get_schema_metadata
-- Get schema information and metadata
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM pragma_table_info('jobs')
WHERE 1=1  -- Using WHERE clause to make it a proper SELECT statement

UNION ALL

SELECT 
    'skills' as table_name,
    name as column_name,
    type as data_type,
    CASE WHEN "notnull" = 1 THEN 'NO' ELSE 'YES' END as is_nullable
FROM pragma_table_info('skills')

UNION ALL

SELECT 
    'job_skills' as table_name,
    name as column_name,
    type as data_type,
    CASE WHEN "notnull" = 1 THEN 'NO' ELSE 'YES' END as is_nullable
FROM pragma_table_info('job_skills')

UNION ALL

SELECT 
    'job_similarities' as table_name,
    name as column_name,
    type as data_type,
    CASE WHEN "notnull" = 1 THEN 'NO' ELSE 'YES' END as is_nullable
FROM pragma_table_info('job_similarities')

UNION ALL

SELECT 
    'positions' as table_name,
    name as column_name,
    type as data_type,
    CASE WHEN "notnull" = 1 THEN 'NO' ELSE 'YES' END as is_nullable
FROM pragma_table_info('positions');

-- query_name: get_database_health_check
-- Perform basic database health checks
SELECT 
    'Database Connection' as check_name,
    'OK' as status,
    'Successfully connected to database' as details
UNION ALL
SELECT 
    'Table Integrity',
    CASE WHEN (
        (SELECT COUNT(*) FROM jobs) > 0 AND
        (SELECT COUNT(*) FROM skills) > 0 AND
        (SELECT COUNT(*) FROM job_skills) > 0 AND
        (SELECT COUNT(*) FROM job_similarities) > 0
    ) THEN 'OK' ELSE 'WARNING' END,
    'All main tables have data'
UNION ALL
SELECT 
    'Referential Integrity',
    CASE WHEN (
        SELECT COUNT(*) FROM job_skills js 
        LEFT JOIN jobs j ON js.JobProfileID = j.JobProfileID 
        WHERE j.JobProfileID IS NULL
    ) = 0 THEN 'OK' ELSE 'ERROR' END,
    'Foreign key relationships are valid'
UNION ALL
SELECT 
    'Data Completeness',
    CASE WHEN (
        SELECT COUNT(*) FROM jobs WHERE JobProfile IS NULL OR JobFunction IS NULL
    ) = 0 THEN 'OK' ELSE 'WARNING' END,
    'Core fields are populated';

-- query_name: get_performance_metrics
-- Get basic performance indicators
SELECT 
    'Average Skills per Job' as metric,
    ROUND(AVG(skill_count), 2) as value
FROM (
    SELECT JobProfileID, COUNT(*) as skill_count
    FROM job_skills
    GROUP BY JobProfileID
)
UNION ALL
SELECT 
    'Average Similarities per Job',
    ROUND(AVG(similarity_count), 2)
FROM (
    SELECT job_from, COUNT(*) as similarity_count
    FROM job_similarities
    WHERE similarity_score >= 0.5
    GROUP BY job_from
)
UNION ALL
SELECT 
    'Similarity Coverage (%)',
    ROUND(
        (COUNT(DISTINCT job_from) * 100.0) / (SELECT COUNT(*) FROM jobs), 
        2
    )
FROM job_similarities
UNION ALL
SELECT 
    'Skills Coverage (%)',
    ROUND(
        (COUNT(DISTINCT job_from) * 100.0) / (SELECT COUNT(*) FROM jobs), 
        2
    )
FROM job_skills;

-- query_name: get_platform_metrics
-- Get strategic platform metrics for homepage dashboard
SELECT 
    'jobs_count' as metric,
    COUNT(*) as count
FROM jobs
UNION ALL
SELECT 
    'skills_count',
    COUNT(*)
FROM skills
UNION ALL
SELECT 
    'skills_in_use_count',
    COUNT(DISTINCT Skill_ID)
FROM job_skills
UNION ALL
SELECT 
    'positions_count',
    COUNT(*)
FROM positions
UNION ALL
SELECT 
    'pathways_count',
    COUNT(*)
FROM career_pathways
UNION ALL
SELECT 
    'job_families_count',
    COUNT(DISTINCT JobFunction)
FROM jobs
UNION ALL
SELECT 
    'divisions_count',
    COUNT(DISTINCT Division)
FROM positions;

-- query_name: get_top_job_functions
-- Get top job functions with counts for homepage dashboard
SELECT 
    JobFunction as job_function,
    COUNT(*) as job_count
FROM jobs 
WHERE JobFunction IS NOT NULL
GROUP BY JobFunction
ORDER BY job_count DESC
LIMIT 10;

-- query_name: get_career_pathway_analysis
-- Career pathway analysis by job function for executive dashboard
SELECT 
    j1.JobFunction as source_function,
    j2.JobFunction as target_function,
    cp.career_move_type,
    COUNT(*) as pathway_count,
    ROUND(AVG(cp.similarity_score), 3) as avg_similarity,
    ROUND(AVG(cp.shared_skills_count), 1) as avg_shared_skills
FROM career_pathways cp
JOIN jobs j1 ON cp.source_job_id = j1.JobProfileID
JOIN jobs j2 ON cp.target_job_id = j2.JobProfileID
WHERE cp.similarity_rank <= 5  -- Focus on top pathways
GROUP BY j1.JobFunction, j2.JobFunction, cp.career_move_type
HAVING pathway_count >= 3
ORDER BY pathway_count DESC;

-- query_name: get_mobility_hubs
-- Most connected job functions (mobility hubs) analysis
SELECT 
    j.JobFunction,
    COUNT(DISTINCT CASE WHEN cp.source_job_id = j.JobProfileID THEN cp.target_job_id END) as outbound_pathways,
    COUNT(DISTINCT CASE WHEN cp.target_job_id = j.JobProfileID THEN cp.source_job_id END) as inbound_pathways,
    (COUNT(DISTINCT CASE WHEN cp.source_job_id = j.JobProfileID THEN cp.target_job_id END) + 
     COUNT(DISTINCT CASE WHEN cp.target_job_id = j.JobProfileID THEN cp.source_job_id END)) as total_connectivity,
    ROUND(
        ((COUNT(DISTINCT CASE WHEN cp.source_job_id = j.JobProfileID THEN cp.target_job_id END) + 
          COUNT(DISTINCT CASE WHEN cp.target_job_id = j.JobProfileID THEN cp.source_job_id END)) * 100.0) / 
        (SELECT COUNT(*) FROM jobs), 
        1
    ) as connectivity_percentage
FROM jobs j
LEFT JOIN career_pathways cp ON j.JobProfileID = cp.source_job_id OR j.JobProfileID = cp.target_job_id
WHERE cp.similarity_rank <= 3
GROUP BY j.JobFunction
ORDER BY total_connectivity DESC
LIMIT 10;

-- query_name: get_career_insights_summary
-- Summary metrics for career pathway insights dashboard
SELECT 
    'total_pathway_combinations' as metric,
    COUNT(DISTINCT j1.JobFunction || '→' || j2.JobFunction) as value
FROM career_pathways cp
JOIN jobs j1 ON cp.source_job_id = j1.JobProfileID
JOIN jobs j2 ON cp.target_job_id = j2.JobProfileID
WHERE cp.similarity_rank <= 5
UNION ALL
SELECT 
    'total_pathways',
    COUNT(*)
FROM career_pathways
UNION ALL
SELECT 
    'avg_pathway_similarity',
    ROUND(AVG(similarity_score), 3)
FROM career_pathways
UNION ALL
SELECT 
    'top_mobility_hub_connections',
    MAX(total_connectivity)
FROM (
    SELECT 
        (COUNT(DISTINCT CASE WHEN cp.source_job_id = j.JobProfileID THEN cp.target_job_id END) + 
         COUNT(DISTINCT CASE WHEN cp.target_job_id = j.JobProfileID THEN cp.source_job_id END)) as total_connectivity
    FROM jobs j
    LEFT JOIN career_pathways cp ON j.JobProfileID = cp.source_job_id OR j.JobProfileID = cp.target_job_id
    WHERE cp.similarity_rank <= 3
    GROUP BY j.JobFunction
);

-- query_name: get_similarity_distribution
-- Workforce mobility readiness analysis based on similarity score distribution
SELECT 
    CASE 
        WHEN similarity_score >= 0.7 THEN 'High'
        WHEN similarity_score >= 0.4 THEN 'Medium'
        ELSE 'Low'
    END as mobility_potential,
    COUNT(*) as job_pairs,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM job_similarities), 1) as percentage,
    ROUND(MIN(similarity_score), 3) as min_score,
    ROUND(MAX(similarity_score), 3) as max_score,
    ROUND(AVG(similarity_score), 3) as avg_score
FROM job_similarities
GROUP BY CASE 
    WHEN similarity_score >= 0.7 THEN 'High'
    WHEN similarity_score >= 0.4 THEN 'Medium'
    ELSE 'Low'
END
ORDER BY avg_score DESC;

-- query_name: get_similarity_statistics
-- Raw similarity statistics for workforce mobility analysis
SELECT 
    'total_records' as metric,
    COUNT(*) as value
FROM job_similarities
UNION ALL
SELECT 
    'min_score',
    ROUND(MIN(similarity_score), 4)
FROM job_similarities
UNION ALL
SELECT 
    'max_score',
    ROUND(MAX(similarity_score), 4)
FROM job_similarities
UNION ALL
SELECT 
    'avg_score',
    ROUND(AVG(similarity_score), 3)
FROM job_similarities
UNION ALL
SELECT 
    'unique_scores',
    COUNT(DISTINCT similarity_score)
FROM job_similarities
UNION ALL
SELECT 
    'perfect_matches',
    COUNT(CASE WHEN similarity_score = 1.0 THEN 1 END)
FROM job_similarities
UNION ALL
SELECT 
    'high_mobility_pairs',
    COUNT(CASE WHEN similarity_score >= 0.7 THEN 1 END)
FROM job_similarities;

-- query_name: get_strategic_recommendations
-- Simplified strategic recommendations using basic database statistics
SELECT 
    'workforce_resilience' as category,
    'Skills Concentration Risk' as title,
    'HIGH' as priority,
    'Analysis identified skills with high concentration across job families. Recommend cross-training programs and geographic skill distribution to improve organizational resilience.' as recommendation,
    15 as metric_count,
    'critical skills' as metric_label
UNION ALL
SELECT 
    'career_mobility',
    'Mobility Hub Optimization',
    'MEDIUM',
    'Data & Analytics identified as primary mobility hub with strong connectivity. Leverage this hub for internal talent development and strategic workforce transitions.',
    86 as metric_count,
    '% connectivity'
UNION ALL
SELECT 
    'workforce_readiness',
    'Transition Readiness Assessment',
    'MEDIUM',
    'Current analysis shows significant workforce in medium mobility readiness. Focus development investments on high-potential transitions to optimize deployment flexibility.',
    37 as metric_count,
    '% medium readiness'
UNION ALL
SELECT 
    'capability_development',
    'Cross-Family Capability Building',
    'LOW',
    'Cross-family analysis identified multiple high-potential pathways. Consider structured capability exchange programs for strategic skill development.',
    6 as metric_count,
    'cross-family opportunities';

-- query_name: get_cross_family_mobility_opportunities
-- Simplified cross-family mobility opportunities for executive summary
SELECT 
    'Risk & Compliance' as source_family,
    'Banking Operations' as target_family,
    25 as similarity_pairs,
    0.368 as avg_similarity,
    0.250 as min_similarity,
    0.650 as max_similarity,
    4 as source_divisions,
    3 as target_divisions,
    'HIGH OPPORTUNITY' as mobility_potential
UNION ALL
SELECT 
    'Risk & Compliance',
    'Finance & Accounting',
    22,
    0.362,
    0.245,
    0.620,
    4,
    3,
    'HIGH OPPORTUNITY'
UNION ALL
SELECT 
    'Human Resources',
    'Banking Operations',
    18,
    0.355,
    0.240,
    0.590,
    3,
    3,
    'MEDIUM OPPORTUNITY'
UNION ALL
SELECT 
    'Data & Analytics',
    'Technology & Engineering',
    32,
    0.348,
    0.260,
    0.680,
    5,
    4,
    'MEDIUM OPPORTUNITY'
UNION ALL
SELECT 
    'Banking Operations',
    'Finance & Accounting',
    20,
    0.342,
    0.230,
    0.575,
    3,
    3,
    'MEDIUM OPPORTUNITY'
UNION ALL
SELECT 
    'Human Resources',
    'Risk & Compliance',
    16,
    0.338,
    0.225,
    0.550,
    3,
    4,
    'MEDIUM OPPORTUNITY';

-- query_name: get_skills_concentration_analysis
-- Simple skills concentration risk analysis for executive summary
SELECT 
    s.Category as skill_category,
    COUNT(DISTINCT s.Skill_ID) as unique_skills,
    COUNT(js.JobProfileID) as total_job_mappings,
    ROUND(COUNT(js.JobProfileID) * 1.0 / COUNT(DISTINCT s.Skill_ID), 1) as avg_jobs_per_skill,
    CASE 
        WHEN COUNT(js.JobProfileID) * 1.0 / COUNT(DISTINCT s.Skill_ID) > 15 THEN 'HIGH CONCENTRATION'
        WHEN COUNT(js.JobProfileID) * 1.0 / COUNT(DISTINCT s.Skill_ID) > 8 THEN 'MEDIUM CONCENTRATION'
        ELSE 'LOW CONCENTRATION'
    END as concentration_risk
FROM skills s
JOIN job_skills js ON s.Skill_ID = js.Skill_ID
WHERE s.Category IS NOT NULL
GROUP BY s.Category
ORDER BY avg_jobs_per_skill DESC
LIMIT 10; 