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
    j1.job_title as job_1,
    j2.job_title as job_2,
    js1.similarity_score as score_1_to_2,
    js2.similarity_score as score_2_to_1,
    (js1.similarity_score + js2.similarity_score) / 2 as avg_similarity
FROM job_similarities js1
JOIN job_similarities js2 ON js1.job_id = js2.similar_job_id 
    AND js1.similar_job_id = js2.job_id
JOIN jobs j1 ON js1.job_id = j1.id
JOIN jobs j2 ON js1.similar_job_id = j2.id
WHERE js1.similarity_score >= ?
    AND js2.similarity_score >= ?
ORDER BY avg_similarity DESC
LIMIT ?;

-- query_name: get_similarity_by_family
-- Get similarity statistics between job families
SELECT 
    j1.job_family as source_family,
    j2.job_family as target_family,
    COUNT(*) as relationship_count,
    AVG(js.similarity_score) as avg_similarity,
    MAX(js.similarity_score) as max_similarity,
    COUNT(CASE WHEN js.similarity_score >= 0.8 THEN 1 END) as high_similarity_count
FROM job_similarities js
JOIN jobs j1 ON js.job_id = j1.id
JOIN jobs j2 ON js.similar_job_id = j2.id
GROUP BY j1.job_family, j2.job_family
HAVING COUNT(*) >= ?
ORDER BY avg_similarity DESC;

-- query_name: find_career_clusters
-- Find clusters of highly similar jobs (potential career groups)
SELECT 
    j.job_family,
    j.job_level,
    COUNT(DISTINCT js.similar_job_id) as similar_jobs_count,
    AVG(js.similarity_score) as avg_similarity,
    GROUP_CONCAT(DISTINCT j2.job_title, '; ') as similar_job_titles
FROM jobs j
JOIN job_similarities js ON j.id = js.job_id
JOIN jobs j2 ON js.similar_job_id = j2.id
WHERE js.similarity_score >= ?
GROUP BY j.id, j.job_family, j.job_level
HAVING similar_jobs_count >= ?
ORDER BY similar_jobs_count DESC, avg_similarity DESC;

-- query_name: get_similarity_gaps
-- Find jobs with low similarity to others (potential specialised roles)
SELECT 
    j.id,
    j.job_title,
    j.job_family,
    j.job_level,
    COUNT(js.similar_job_id) as total_similarities,
    COUNT(CASE WHEN js.similarity_score >= 0.6 THEN 1 END) as moderate_similarities,
    COUNT(CASE WHEN js.similarity_score >= 0.8 THEN 1 END) as high_similarities,
    AVG(js.similarity_score) as avg_similarity
FROM jobs j
LEFT JOIN job_similarities js ON j.id = js.job_id
GROUP BY j.id, j.job_title, j.job_family, j.job_level
HAVING high_similarities < ?
ORDER BY avg_similarity ASC, total_similarities ASC;

-- query_name: get_cross_family_similarities
-- Find highest similarities between different job families
SELECT 
    j1.job_family as source_family,
    j1.job_title as source_job,
    j2.job_family as target_family,
    j2.job_title as target_job,
    js.similarity_score
FROM job_similarities js
JOIN jobs j1 ON js.job_id = j1.id
JOIN jobs j2 ON js.similar_job_id = j2.id
WHERE j1.job_family != j2.job_family
    AND js.similarity_score >= ?
ORDER BY js.similarity_score DESC
LIMIT ?; 