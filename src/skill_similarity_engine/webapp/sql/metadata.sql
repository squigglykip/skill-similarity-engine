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
    COUNT(DISTINCT job_family) as distinct_families,
    MIN(id) as min_id,
    MAX(id) as max_id
FROM jobs
UNION ALL
SELECT 
    'skills',
    COUNT(*),
    COUNT(DISTINCT skill_category),
    MIN(id),
    MAX(id)
FROM skills
UNION ALL
SELECT 
    'job_skills',
    COUNT(*),
    COUNT(DISTINCT job_id),
    MIN(job_id),
    MAX(job_id)
FROM job_skills
UNION ALL
SELECT 
    'job_similarities',
    COUNT(*),
    COUNT(DISTINCT job_id),
    MIN(job_id),
    MAX(job_id)
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
        (COUNT(CASE WHEN job_title IS NOT NULL AND job_family IS NOT NULL THEN 1 END) * 100.0) / COUNT(*), 
        2
    ) as percentage
FROM jobs
UNION ALL
SELECT 
    'Skills Completeness',
    ROUND(
        (COUNT(CASE WHEN skill_name IS NOT NULL AND skill_category IS NOT NULL THEN 1 END) * 100.0) / COUNT(*), 
        2
    )
FROM skills
UNION ALL
SELECT 
    'Jobs with Skills',
    ROUND(
        (COUNT(DISTINCT job_id) * 100.0) / (SELECT COUNT(*) FROM jobs), 
        2
    )
FROM job_skills
UNION ALL
SELECT 
    'Jobs with Similarities',
    ROUND(
        (COUNT(DISTINCT job_id) * 100.0) / (SELECT COUNT(*) FROM jobs), 
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
    skill_category,
    COUNT(*) as skill_count,
    COUNT(DISTINCT skill_subcategory) as subcategories,
    COUNT(DISTINCT js.job_id) as jobs_using_category,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM skills), 2) as percentage_of_skills
FROM skills s
LEFT JOIN job_skills js ON s.id = js.skills_skill_id
GROUP BY skill_category
ORDER BY skill_count DESC;

-- query_name: get_job_family_stats
-- Get statistics for each job family
SELECT 
    job_family,
    COUNT(*) as job_count,
    COUNT(DISTINCT job_level) as level_variations,
    COUNT(DISTINCT job_cluster) as cluster_variations,
    AVG(skill_counts.skill_count) as avg_skills_per_job,
    AVG(similarity_counts.similarity_count) as avg_similarities_per_job
FROM jobs j
LEFT JOIN (
    SELECT job_id, COUNT(*) as skill_count
    FROM job_skills
    GROUP BY job_id
) skill_counts ON j.id = skill_counts.job_id
LEFT JOIN (
    SELECT job_id, COUNT(*) as similarity_count
    FROM job_similarities
    WHERE similarity_score >= 0.6
    GROUP BY job_id
) similarity_counts ON j.id = similarity_counts.job_id
GROUP BY job_family
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
        LEFT JOIN jobs j ON js.job_id = j.id 
        WHERE j.id IS NULL
    ) = 0 THEN 'OK' ELSE 'ERROR' END,
    'Foreign key relationships are valid'
UNION ALL
SELECT 
    'Data Completeness',
    CASE WHEN (
        SELECT COUNT(*) FROM jobs WHERE job_title IS NULL OR job_family IS NULL
    ) = 0 THEN 'OK' ELSE 'WARNING' END,
    'Core fields are populated';

-- query_name: get_performance_metrics
-- Get basic performance indicators
SELECT 
    'Average Skills per Job' as metric,
    ROUND(AVG(skill_count), 2) as value
FROM (
    SELECT job_id, COUNT(*) as skill_count
    FROM job_skills
    GROUP BY job_id
)
UNION ALL
SELECT 
    'Average Similarities per Job',
    ROUND(AVG(similarity_count), 2)
FROM (
    SELECT job_id, COUNT(*) as similarity_count
    FROM job_similarities
    WHERE similarity_score >= 0.5
    GROUP BY job_id
)
UNION ALL
SELECT 
    'Similarity Coverage (%)',
    ROUND(
        (COUNT(DISTINCT job_id) * 100.0) / (SELECT COUNT(*) FROM jobs), 
        2
    )
FROM job_similarities
UNION ALL
SELECT 
    'Skills Coverage (%)',
    ROUND(
        (COUNT(DISTINCT job_id) * 100.0) / (SELECT COUNT(*) FROM jobs), 
        2
    )
FROM job_skills; 