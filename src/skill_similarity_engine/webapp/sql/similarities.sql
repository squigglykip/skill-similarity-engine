-- =================================================================
-- SIMILARITY QUERIES
-- Queries for job similarities, matching, and relationship analysis
-- =================================================================

-- query_name: get_similar_jobs
-- Get similar jobs for a specific job with similarity scores
SELECT 
    j.JobProfileID as id,
    j.JobProfile as job_title,
    j.JobFamily as job_family,
    j.JobFamilyGroup as job_level,
    js.similarity_score,
    CASE 
        WHEN js.similarity_score >= 0.8 THEN 'High'
        WHEN js.similarity_score >= 0.6 THEN 'Medium'
        ELSE 'Low'
    END as similarity_category
FROM job_similarities js
JOIN jobs j ON js.job_to = j.JobProfileID
WHERE js.job_from = ?
    AND js.similarity_score >= ?
ORDER BY js.similarity_score DESC
LIMIT ?;

-- query_name: get_similar_jobs_with_threshold
-- Get similar jobs for a specific job with a custom similarity threshold
SELECT 
    j.JobProfileID as id,
    j.JobProfile as job_title,
    j.JobFamily as job_family,
    j.JobFamilyGroup as job_level,
    js.similarity_score,
    CASE 
        WHEN js.similarity_score >= 0.8 THEN 'High'
        WHEN js.similarity_score >= 0.6 THEN 'Medium'
        ELSE 'Low'
    END as similarity_category
FROM job_similarities js
JOIN jobs j ON js.job_to = j.JobProfileID
WHERE js.job_from = ?
    AND js.similarity_score >= ?
ORDER BY js.similarity_score DESC
LIMIT ?;

-- query_name: get_top_similar_jobs
-- Get top N most similar jobs for a specific job
SELECT 
    j.JobProfileID as id,
    j.JobProfile as job_title,
    j.JobFamily as job_family,
    j.JobFamilyGroup as job_family_group,
    js.similarity_score,
    CASE 
        WHEN js.similarity_score >= 0.8 THEN 'High'
        WHEN js.similarity_score >= 0.6 THEN 'Medium'
        ELSE 'Low'
    END as similarity_category
FROM job_similarities js
JOIN jobs j ON js.job_to = j.JobProfileID
WHERE js.job_from = ?
ORDER BY js.similarity_score DESC
LIMIT ?;

-- query_name: get_similarity_distribution
-- Get distribution of similarity scores
SELECT 
    CASE 
        WHEN similarity_score >= 0.8 THEN 'High'
        WHEN similarity_score >= 0.6 THEN 'Medium'
        WHEN similarity_score >= 0.4 THEN 'Low'
        ELSE 'Very Low'
    END as similarity_category,
    COUNT(*) as count,
    AVG(similarity_score) as avg_score,
    MIN(similarity_score) as min_score,
    MAX(similarity_score) as max_score
FROM job_similarities
GROUP BY CASE 
    WHEN similarity_score >= 0.8 THEN 'High'
    WHEN similarity_score >= 0.6 THEN 'Medium'
    WHEN similarity_score >= 0.4 THEN 'Low'
    ELSE 'Very Low'
END
ORDER BY avg_score DESC;

-- query_name: get_mutual_similarities
-- Find jobs that are mutually similar (bidirectional high similarity)
SELECT 
    j1.JobProfile as job_1,
    j2.JobProfile as job_2,
    js1.similarity_score as score_1_to_2,
    js2.similarity_score as score_2_to_1,
    (js1.similarity_score + js2.similarity_score) / 2 as avg_similarity
FROM job_similarities js1
JOIN job_similarities js2 ON js1.job_from = js2.job_to 
    AND js1.job_to = js2.job_from
JOIN jobs j1 ON js1.job_from = j1.JobProfileID
JOIN jobs j2 ON js1.job_to = j2.JobProfileID
WHERE js1.similarity_score >= ?
    AND js2.similarity_score >= ?
ORDER BY avg_similarity DESC
LIMIT ?;

-- query_name: get_similarity_by_family
-- Get similarity statistics between job families
SELECT 
    j1.JobFamily as source_family,
    j2.JobFamily as target_family,
    COUNT(*) as relationship_count,
    AVG(js.similarity_score) as avg_similarity,
    MAX(js.similarity_score) as max_similarity,
    COUNT(CASE WHEN js.similarity_score >= 0.8 THEN 1 END) as high_similarity_count
FROM job_similarities js
JOIN jobs j1 ON js.job_from = j1.JobProfileID
JOIN jobs j2 ON js.job_to = j2.JobProfileID
GROUP BY j1.JobFamily, j2.JobFamily
HAVING COUNT(*) >= ?
ORDER BY avg_similarity DESC;

-- query_name: find_career_clusters
-- Find clusters of highly similar jobs (potential career groups)
SELECT 
    j.JobFamily,
    j.JobFamilyGroup as job_level,
    COUNT(DISTINCT js.job_to) as similar_jobs_count,
    AVG(js.similarity_score) as avg_similarity,
    GROUP_CONCAT(DISTINCT j2.JobProfile, '; ') as similar_job_titles
FROM jobs j
JOIN job_similarities js ON j.JobProfileID = js.job_from
JOIN jobs j2 ON js.job_to = j2.JobProfileID
WHERE js.similarity_score >= ?
GROUP BY j.JobProfileID, j.JobFamily, j.JobFamilyGroup
HAVING similar_jobs_count >= ?
ORDER BY similar_jobs_count DESC, avg_similarity DESC;

-- query_name: get_similarity_gaps
-- Find jobs with low similarity to others (potential specialised roles)
SELECT 
    j.JobProfileID as id,
    j.JobProfile as job_title,
    j.JobFamily as job_family,
    j.JobFamilyGroup as job_level,
    COUNT(js.job_to) as total_similarities,
    COUNT(CASE WHEN js.similarity_score >= 0.6 THEN 1 END) as moderate_similarities,
    COUNT(CASE WHEN js.similarity_score >= 0.8 THEN 1 END) as high_similarities,
    AVG(js.similarity_score) as avg_similarity
FROM jobs j
LEFT JOIN job_similarities js ON j.JobProfileID = js.job_from
GROUP BY j.JobProfileID, j.JobProfile, j.JobFamily, j.JobFamilyGroup
HAVING high_similarities < ?
ORDER BY avg_similarity ASC, total_similarities ASC;

-- query_name: get_cross_family_similarities
-- Find highest similarities between different job families
SELECT 
    j1.JobFamily as source_family,
    j1.JobProfile as source_job,
    j2.JobFamily as target_family,
    j2.JobProfile as target_job,
    js.similarity_score
FROM job_similarities js
JOIN jobs j1 ON js.job_from = j1.JobProfileID
JOIN jobs j2 ON js.job_to = j2.JobProfileID
WHERE j1.JobFamily != j2.JobFamily
    AND js.similarity_score >= ?
ORDER BY js.similarity_score DESC
LIMIT ?;

-- query_name: get_cross_family_stats
-- Get statistics for cross-family mobility analysis  
SELECT 
    j1.JobFamily as source_family,
    j2.JobFamily as target_family,
    COUNT(*) as total_pairs,
    ROUND(AVG(js.similarity_score), 3) as avg_similarity,
    ROUND(MIN(js.similarity_score), 3) as min_similarity,
    ROUND(MAX(js.similarity_score), 3) as max_similarity,
    COUNT(CASE WHEN js.similarity_score >= 0.4 THEN 1 END) as viable_transitions
FROM job_similarities js
JOIN jobs j1 ON js.job_from = j1.JobProfileID
JOIN jobs j2 ON js.job_to = j2.JobProfileID
WHERE j1.JobFamily != j2.JobFamily
    AND js.similarity_score >= 0.2
GROUP BY j1.JobFamily, j2.JobFamily
HAVING COUNT(*) >= 5
ORDER BY avg_similarity DESC
LIMIT 10; 