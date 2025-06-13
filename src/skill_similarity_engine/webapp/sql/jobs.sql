-- =================================================================
-- JOB QUERIES
-- Queries for job information, job families, and job relationships
-- =================================================================

-- query_name: get_job_families
-- Get all job families with job counts
SELECT 
    JobFamily as job_family,
    COUNT(*) as job_count,
    COUNT(DISTINCT CASE WHEN similarity_score >= 0.8 THEN job_to END) as high_similarity_jobs
FROM jobs j
LEFT JOIN job_similarities js ON j.JobProfileID = js.job_from
GROUP BY JobFamily
ORDER BY job_count DESC;

-- query_name: get_jobs_in_family
-- Get all jobs within a specific job family
SELECT 
    JobProfileID as id,
    JobProfile as job_title,
    JobFamily as job_family,
    JobFamilyGroup as job_family_group
FROM jobs
WHERE JobFamily = ?
ORDER BY JobProfile;

-- query_name: get_job_details
-- Get detailed information about a specific job
SELECT 
    j.id,
    j.job_title,
    j.job_family,
    j.job_level,
    j.job_cluster,
    COUNT(DISTINCT js.skills_skill_id) as total_skills,
    COUNT(DISTINCT jss.similar_job_id) as similar_jobs_count,
    AVG(jss.similarity_score) as avg_similarity_score
FROM jobs j
LEFT JOIN job_skills js ON j.id = js.job_id
LEFT JOIN job_similarities jss ON j.id = jss.job_id
WHERE j.id = ?
GROUP BY j.id, j.job_title, j.job_family, j.job_level, j.job_cluster;

-- query_name: search_jobs
-- Search jobs by title with optional family filter
SELECT 
    id,
    job_title,
    job_family,
    job_level,
    job_cluster
FROM jobs
WHERE job_title LIKE ?
    AND (? IS NULL OR job_family = ?)
ORDER BY job_title
LIMIT 50;

-- query_name: get_job_skills
-- Get all skills for a specific job with proficiency levels
SELECT 
    s.skill_name,
    s.skill_category,
    s.skill_subcategory,
    js.proficiency_level,
    s.id as skill_id
FROM job_skills js
JOIN skills s ON js.skills_skill_id = s.id
WHERE js.job_id = ?
ORDER BY s.skill_category, s.skill_name;

-- query_name: get_jobs_by_level
-- Get jobs filtered by job level
SELECT 
    id,
    job_title,
    job_family,
    job_level,
    job_cluster
FROM jobs
WHERE job_level = ?
ORDER BY job_family, job_title;

-- query_name: get_jobs_by_cluster
-- Get jobs filtered by job cluster
SELECT 
    id,
    job_title,
    job_family,
    job_level,
    job_cluster
FROM jobs
WHERE job_cluster = ?
ORDER BY job_title;

-- query_name: get_job_summary_stats
-- Get summary statistics for jobs
SELECT 
    COUNT(*) as total_jobs,
    COUNT(DISTINCT job_family) as total_families,
    COUNT(DISTINCT job_level) as total_levels,
    COUNT(DISTINCT job_cluster) as total_clusters,
    AVG(skill_count) as avg_skills_per_job
FROM (
    SELECT 
        j.id,
        j.job_family,
        j.job_level,
        j.job_cluster,
        COUNT(js.skills_skill_id) as skill_count
    FROM jobs j
    LEFT JOIN job_skills js ON j.id = js.job_id
    GROUP BY j.id, j.job_family, j.job_level, j.job_cluster
) job_stats; 