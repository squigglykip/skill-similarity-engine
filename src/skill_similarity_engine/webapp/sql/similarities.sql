-- =================================================================
-- SIMILARITY QUERIES - V2 SCHEMA
-- Queries for job similarity analysis and cross-family exploration  
-- Updated for analytics_job_similarities table with enhanced scoring
-- =================================================================

-- query_name: get_similar_jobs
-- Get jobs similar to a given job with enhanced V2 similarity scores
SELECT 
    ja.JobProfileID as id,
    ja.JobProfile as job_title,
    ja.JobFunction as job_function,
    ja.JobFunctionID as job_function_id,
    js.enhanced_similarity_score as similarity_score,
    js.rarity_weighted_score,
    js.shared_defining_skills_count,
    js.total_skills_compared,
    CASE 
        WHEN js.enhanced_similarity_score >= 0.8 THEN 'High'
        WHEN js.enhanced_similarity_score >= 0.6 THEN 'Medium'
        ELSE 'Low'
    END as similarity_category
FROM analytics_job_similarities js
INNER JOIN core_job_architecture ja ON js.job_to = ja.JobProfileID
WHERE js.job_from = ?
    AND js.enhanced_similarity_score >= ?
    AND js.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
ORDER BY js.enhanced_similarity_score DESC
LIMIT ?;

-- query_name: get_similar_jobs_with_threshold  
-- Get jobs similar to a given job with enhanced similarity threshold
SELECT 
    ja.JobProfileID as id,
    ja.JobProfile as job_title,
    ja.JobFunction as job_function,
    ja.JobFunctionID as job_function_id,
    js.enhanced_similarity_score as similarity_score,
    js.rarity_weighted_score,
    js.shared_defining_skills_count,
    js.total_skills_compared,
    CASE 
        WHEN js.enhanced_similarity_score >= 0.8 THEN 'High'
        WHEN js.enhanced_similarity_score >= 0.6 THEN 'Medium'
        ELSE 'Low'
    END as similarity_category
FROM analytics_job_similarities js
INNER JOIN core_job_architecture ja ON js.job_to = ja.JobProfileID
WHERE js.job_from = ?
    AND js.enhanced_similarity_score >= ?
    AND js.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
ORDER BY js.enhanced_similarity_score DESC
LIMIT ?;

-- query_name: get_job_similarity_stats
-- Get enhanced similarity statistics for a specific job
SELECT 
    COUNT(*) as total_similar_jobs,
    AVG(js.enhanced_similarity_score) as avg_similarity,
    MAX(js.enhanced_similarity_score) as max_similarity,
    AVG(js.rarity_weighted_score) as avg_rarity_weighted_score,
    SUM(js.shared_defining_skills_count) as total_shared_defining_skills,
    ja.JobProfileID as id,
    ja.JobProfile as job_title,
    ja.JobFunction as job_function,
    ja.JobFunctionID as job_function_id
FROM analytics_job_similarities js
INNER JOIN core_job_architecture ja ON js.job_from = ja.JobProfileID
WHERE js.job_from = ?
    AND js.enhanced_similarity_score >= 0.5
    AND js.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
GROUP BY ja.JobProfileID, ja.JobProfile, ja.JobFunction, ja.JobFunctionID;

-- query_name: get_cross_function_similarities
-- Get enhanced similarities between jobs from different functions
SELECT 
    ja1.JobFunction as source_function,
    ja2.JobFunction as target_function,
    AVG(js.enhanced_similarity_score) as avg_similarity,
    AVG(js.rarity_weighted_score) as avg_rarity_weighted_score,
    COUNT(*) as pathway_count,
    SUM(js.shared_defining_skills_count) as total_shared_defining_skills
FROM analytics_job_similarities js
INNER JOIN core_job_architecture ja1 ON js.job_from = ja1.JobProfileID
INNER JOIN core_job_architecture ja2 ON js.job_to = ja2.JobProfileID
WHERE ja1.JobFunction != ja2.JobFunction
    AND js.enhanced_similarity_score >= ?
    AND js.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
GROUP BY ja1.JobFunction, ja2.JobFunction
ORDER BY avg_similarity DESC
LIMIT ?;

-- query_name: get_function_mobility_matrix
-- Generate enhanced mobility matrix showing average similarities between functions
SELECT 
    ja.JobProfileID,
    ja.JobFunction as job_function,
    ja.JobFunctionID as job_function_id,
    COUNT(DISTINCT js.job_to) as similar_jobs_count,
    AVG(js.enhanced_similarity_score) as avg_similarity,
    AVG(js.rarity_weighted_score) as avg_rarity_weighted_score,
    SUM(js.shared_defining_skills_count) as total_shared_defining_skills
FROM core_job_architecture ja
LEFT JOIN analytics_job_similarities js ON ja.JobProfileID = js.job_from 
    AND js.enhanced_similarity_score >= 0.6
    AND js.enhanced_similarity_score IS NOT NULL
WHERE ja.JobProfile IS NOT NULL  -- FAIL-FAST validation
GROUP BY ja.JobProfileID, ja.JobFunction, ja.JobFunctionID
ORDER BY similar_jobs_count DESC;

-- query_name: get_highest_similarity_jobs
-- Get pairs of jobs with highest enhanced similarity scores across all functions
SELECT 
    ja1.job_title as source_job,
    ja1.job_function as source_function,
    ja2.job_title as target_job,
    ja2.job_function as target_function,
    js.enhanced_similarity_score as similarity_score,
    js.rarity_weighted_score,
    js.shared_defining_skills_count
FROM analytics_job_similarities js
INNER JOIN core_job_architecture ja1 ON js.job_from = ja1.JobProfileID
INNER JOIN core_job_architecture ja2 ON js.job_to = ja2.JobProfileID
WHERE js.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
ORDER BY js.enhanced_similarity_score DESC
LIMIT ?;

-- query_name: get_cross_function_stats
-- Get enhanced statistics about cross-function job similarities
SELECT 
    ja1.JobFunction as source_function,
    ja2.JobFunction as target_function,
    COUNT(*) as total_pathways,
    AVG(js.enhanced_similarity_score) as avg_similarity,
    MAX(js.enhanced_similarity_score) as max_similarity,
    MIN(js.enhanced_similarity_score) as min_similarity,
    AVG(js.rarity_weighted_score) as avg_rarity_weighted_score,
    SUM(js.shared_defining_skills_count) as total_shared_defining_skills
FROM analytics_job_similarities js
INNER JOIN core_job_architecture ja1 ON js.job_from = ja1.JobProfileID
INNER JOIN core_job_architecture ja2 ON js.job_to = ja2.JobProfileID
WHERE ja1.JobFunction != ja2.JobFunction
    AND js.enhanced_similarity_score >= 0.4
    AND js.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
GROUP BY ja1.JobFunction, ja2.JobFunction
ORDER BY avg_similarity DESC;

-- query_name: get_similarity_distribution
-- Get distribution of enhanced similarity scores
SELECT 
    CASE 
        WHEN enhanced_similarity_score >= 0.8 THEN 'High'
        WHEN enhanced_similarity_score >= 0.6 THEN 'Medium'
        WHEN enhanced_similarity_score >= 0.4 THEN 'Low'
        ELSE 'Very Low'
    END as similarity_category,
    COUNT(*) as count,
    AVG(enhanced_similarity_score) as avg_score,
    MIN(enhanced_similarity_score) as min_score,
    MAX(enhanced_similarity_score) as max_score,
    AVG(rarity_weighted_score) as avg_rarity_weighted_score
FROM analytics_job_similarities
WHERE enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
GROUP BY CASE 
    WHEN enhanced_similarity_score >= 0.8 THEN 'High'
    WHEN enhanced_similarity_score >= 0.6 THEN 'Medium'
    WHEN enhanced_similarity_score >= 0.4 THEN 'Low'
    ELSE 'Very Low'
END
ORDER BY avg_score DESC;

-- query_name: get_mutual_similarities
-- Find jobs that are mutually similar (bidirectional high enhanced similarity)
SELECT 
    ja1.job_title as job_1,
    ja2.job_title as job_2,
    js1.enhanced_similarity_score as score_1_to_2,
    js2.enhanced_similarity_score as score_2_to_1,
    (js1.enhanced_similarity_score + js2.enhanced_similarity_score) / 2 as avg_similarity,
    (js1.rarity_weighted_score + js2.rarity_weighted_score) / 2 as avg_rarity_weighted_score,
    js1.shared_defining_skills_count + js2.shared_defining_skills_count as total_shared_defining_skills
FROM analytics_job_similarities js1
INNER JOIN analytics_job_similarities js2 ON js1.job_from = js2.job_to 
    AND js1.job_to = js2.job_from
INNER JOIN core_job_architecture ja1 ON js1.job_from = ja1.JobProfileID
INNER JOIN core_job_architecture ja2 ON js1.job_to = ja2.JobProfileID
WHERE js1.enhanced_similarity_score >= ?
    AND js2.enhanced_similarity_score >= ?
    AND js1.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
    AND js2.enhanced_similarity_score IS NOT NULL
ORDER BY avg_similarity DESC
LIMIT ?;

-- query_name: get_similarity_by_function
-- Get enhanced similarity statistics between job functions
SELECT 
    ja1.job_function as source_function,
    ja2.job_function as target_function,
    COUNT(*) as relationship_count,
    AVG(js.enhanced_similarity_score) as avg_similarity,
    MAX(js.enhanced_similarity_score) as max_similarity,
    COUNT(CASE WHEN js.enhanced_similarity_score >= 0.8 THEN 1 END) as high_similarity_count,
    AVG(js.rarity_weighted_score) as avg_rarity_weighted_score,
    SUM(js.shared_defining_skills_count) as total_shared_defining_skills
FROM analytics_job_similarities js
INNER JOIN core_job_architecture ja1 ON js.job_from = ja1.JobProfileID
INNER JOIN core_job_architecture ja2 ON js.job_to = ja2.JobProfileID
WHERE js.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
GROUP BY ja1.job_function, ja2.job_function
HAVING COUNT(*) >= ?
ORDER BY avg_similarity DESC;

-- query_name: find_career_clusters
-- Find clusters of highly similar jobs (potential career groups) with V2 analytics
SELECT 
    ja.JobFunction as job_function,
    ja.ManagementLevel as management_level,
    COUNT(DISTINCT js.job_to) as similar_jobs_count,
    AVG(js.enhanced_similarity_score) as avg_similarity,
    AVG(js.rarity_weighted_score) as avg_rarity_weighted_score,
    SUM(js.shared_defining_skills_count) as total_shared_defining_skills,
    GROUP_CONCAT(DISTINCT ja2.job_title, '; ') as similar_job_titles
FROM core_job_architecture ja
INNER JOIN analytics_job_similarities js ON ja.JobProfileID = js.job_from
INNER JOIN core_job_architecture ja2 ON js.job_to = ja2.JobProfileID
WHERE js.enhanced_similarity_score >= ?
    AND js.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
    AND ja.JobProfile as job_title IS NOT NULL
GROUP BY ja.JobProfileID, ja.JobFunction as job_function, ja.ManagementLevel as management_level
HAVING similar_jobs_count >= ?
ORDER BY similar_jobs_count DESC, avg_similarity DESC;

-- query_name: get_similarity_gaps
-- Find jobs with low enhanced similarity to others (potential specialised roles)
SELECT 
    ja.JobProfileID as id,
    ja.JobProfile as job_title,
    ja.JobFunction as job_function,
    ja.ManagementLevel as management_level,
    COUNT(js.job_to) as total_similarities,
    COUNT(CASE WHEN js.enhanced_similarity_score >= 0.6 THEN 1 END) as moderate_similarities,
    COUNT(CASE WHEN js.enhanced_similarity_score >= 0.8 THEN 1 END) as high_similarities,
    AVG(js.enhanced_similarity_score) as avg_similarity,
    AVG(js.rarity_weighted_score) as avg_rarity_weighted_score
FROM core_job_architecture ja
LEFT JOIN analytics_job_similarities js ON ja.JobProfileID = js.job_from
    AND js.enhanced_similarity_score IS NOT NULL
WHERE ja.JobProfile IS NOT NULL  -- FAIL-FAST validation
GROUP BY ja.JobProfileID, ja.JobProfile as job_title, ja.JobFunction as job_function, ja.ManagementLevel as management_level
HAVING high_similarities < ?
ORDER BY avg_similarity ASC, total_similarities ASC;

-- query_name: get_cross_function_similarities_detail
-- Find highest enhanced similarities between different job functions
SELECT 
    ja1.job_function as source_function,
    ja1.job_title as source_job,
    ja2.job_function as target_function,
    ja2.job_title as target_job,
    js.enhanced_similarity_score as similarity_score,
    js.rarity_weighted_score,
    js.shared_defining_skills_count
FROM analytics_job_similarities js
INNER JOIN core_job_architecture ja1 ON js.job_from = ja1.JobProfileID
INNER JOIN core_job_architecture ja2 ON js.job_to = ja2.JobProfileID
WHERE ja1.job_function != ja2.job_function
    AND js.enhanced_similarity_score >= ?
    AND js.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
ORDER BY js.enhanced_similarity_score DESC
LIMIT ?;

-- query_name: get_cross_function_stats_detail
-- Get enhanced statistics for cross-function mobility analysis  
SELECT 
    ja1.job_function as source_function,
    ja2.job_function as target_function,
    COUNT(*) as total_pairs,
    ROUND(AVG(js.enhanced_similarity_score), 3) as avg_similarity,
    ROUND(MIN(js.enhanced_similarity_score), 3) as min_similarity,
    ROUND(MAX(js.enhanced_similarity_score), 3) as max_similarity,
    ROUND(AVG(js.rarity_weighted_score), 3) as avg_rarity_weighted_score,
    COUNT(CASE WHEN js.enhanced_similarity_score >= 0.4 THEN 1 END) as viable_transitions,
    SUM(js.shared_defining_skills_count) as total_shared_defining_skills
FROM analytics_job_similarities js
INNER JOIN core_job_architecture ja1 ON js.job_from = ja1.JobProfileID
INNER JOIN core_job_architecture ja2 ON js.job_to = ja2.JobProfileID
WHERE ja1.job_function != ja2.job_function
    AND js.enhanced_similarity_score >= 0.2
    AND js.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
GROUP BY ja1.job_function, ja2.job_function
HAVING COUNT(*) >= 5
ORDER BY avg_similarity DESC
LIMIT 10; 