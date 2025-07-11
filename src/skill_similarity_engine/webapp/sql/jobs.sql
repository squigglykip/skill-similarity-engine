-- =================================================================
-- JOB QUERIES
-- Queries for job information, job families, and job relationships
-- =================================================================

-- query_name: get_sample_jobs
-- Get a sample of jobs for display
SELECT 
    JobProfileID as id,
    JobProfile as job_title,
    JobFunction as job_function,
    JobFunctionID as job_function_id,
    ManagementLevel as management_level
FROM jobs
ORDER BY JobProfile
LIMIT ?;

-- query_name: get_job_functions
-- Get all job functions with job counts
SELECT 
    JobFunctionID,
    JobFunction,
    COUNT(*) as job_count
FROM jobs j
GROUP BY JobFunctionID, JobFunction
ORDER BY job_count DESC;

-- query_name: get_jobs_in_function
-- Get all jobs within a specific job function
SELECT 
    JobProfileID as id,
    JobProfile as job_title,
    JobFunction as job_function,
    JobFunctionID as job_function_id
FROM jobs
WHERE JobFunction = ?
ORDER BY JobProfile;

-- query_name: get_job_details
-- Get detailed information about a specific job
SELECT 
    j.JobProfileID as id,
    j.JobProfile as job_title,
    j.JobFunction as job_function,
    j.JobFunctionID as job_function_id,
    j.ManagementLevel as management_level,
    COUNT(DISTINCT js.Skill_ID) as total_skills,
    COUNT(DISTINCT cp.target_job_id) as similar_jobs_count,
    AVG(cp.similarity_score) as avg_similarity_score
FROM jobs j
LEFT JOIN job_skills js ON j.JobProfileID = js.JobProfileID
LEFT JOIN career_pathways cp ON j.JobProfileID = cp.source_job_id
WHERE j.JobProfileID = ?
GROUP BY j.JobProfileID, j.JobProfile, j.JobFunction, j.JobFunctionID, j.ManagementLevel;

-- query_name: search_jobs
-- Search jobs by title with optional function filter
SELECT 
    JobProfileID as id,
    JobProfile as job_title,
    JobFunction as job_function,
    JobFunctionID as job_function_id,
    ManagementLevel as management_level
FROM jobs
WHERE JobProfile LIKE ?
    AND (? IS NULL OR JobFunction = ?)
ORDER BY JobProfile
LIMIT 50;

-- query_name: get_job_skills
-- Get all skills for a specific job
SELECT 
    s.Skill_Name as skill_name,
    s.Category as skill_category,
    s.Subcategory as skill_subcategory,
    s.SkillType as skill_type,
    s.Skill_ID as skill_id
FROM job_skills js
JOIN skills s ON js.Skill_ID = s.Skill_ID
WHERE js.JobProfileID = ?
ORDER BY s.Category, s.Skill_Name;

-- query_name: get_jobs_by_level
-- Get jobs filtered by management level
SELECT 
    JobProfileID as id,
    JobProfile as job_title,
    JobFunction as job_function,
    JobFunctionID as job_function_id,
    ManagementLevel as management_level
FROM jobs
WHERE ManagementLevel = ?
ORDER BY JobFunction, JobProfile;

-- query_name: get_jobs_by_category
-- Get jobs filtered by job category
SELECT 
    JobProfileID as id,
    JobProfile as job_title,
    JobFunction as job_function,
    JobFunctionID as job_function_id,
    JobCategory as job_category
FROM jobs
WHERE JobCategory = ?
ORDER BY JobProfile;

-- query_name: get_job_summary_stats
-- Get summary statistics for jobs
SELECT 
    COUNT(*) as total_jobs,
    COUNT(DISTINCT JobFunction) as total_functions,
    COUNT(DISTINCT ManagementLevel) as total_levels,
    COUNT(DISTINCT JobCategory) as total_categories,
    AVG(skill_count) as avg_skills_per_job
FROM (
    SELECT 
        j.JobProfileID,
        j.JobFunction,
        j.ManagementLevel,
        j.JobCategory,
        COUNT(js.Skill_ID) as skill_count
    FROM jobs j
    LEFT JOIN job_skills js ON j.JobProfileID = js.JobProfileID
    GROUP BY j.JobProfileID, j.JobFunction, j.ManagementLevel, j.JobCategory
) job_stats; 