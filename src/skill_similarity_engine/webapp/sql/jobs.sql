-- =================================================================
-- JOB QUERIES - V2 SCHEMA
-- Queries for job information, job families, and job relationships
-- Updated for core_job_architecture table and V2 analytics
-- =================================================================

-- query_name: get_sample_jobs
-- Get a sample of jobs for display
SELECT 
    JobProfileID as id,
    JobProfile as job_title,
    JobFunction as job_function,
    JobFunctionID as job_function_id,
    ManagementLevel as management_level
FROM core_job_architecture
WHERE JobProfile IS NOT NULL  -- FAIL-FAST: Must have valid data
ORDER BY JobProfile
LIMIT ?;

-- query_name: get_job_functions
-- Get all job functions with job counts
SELECT 
    JobFunctionID as job_function_id,
    JobFunction as job_function,
    COUNT(*) as job_count
FROM core_job_architecture j
WHERE JobFunction IS NOT NULL  -- FAIL-FAST: Must have valid function
GROUP BY JobFunctionID, JobFunction
ORDER BY job_count DESC;

-- query_name: get_jobs_in_function
-- Get all jobs within a specific job function
SELECT 
    JobProfileID as id,
    JobProfile as job_title,
    JobFunction as job_function,
    JobFunctionID as job_function_id,
    ManagementLevel as management_level
FROM core_job_architecture
WHERE JobFunction = ?
  AND JobProfile IS NOT NULL  -- FAIL-FAST validation
ORDER BY JobProfile;

-- query_name: get_job_details
-- Get detailed information about a specific job with V2 analytics
SELECT 
    j.JobProfileID as id,
    j.JobProfile as job_title,
    j.JobFunction as job_function,
    j.JobFunctionID as job_function_id,
    j.ManagementLevel as management_level,
    j.JobCategory as job_category,
    NULL as job_description,  -- No description field in V2 schema
    COUNT(DISTINCT jsr.Skill_ID) as total_skills,
    COUNT(DISTINCT ajs.job_to) as similar_jobs_count,
    AVG(ajs.enhanced_similarity_score) as avg_similarity_score
FROM core_job_architecture j
LEFT JOIN core_job_skill_requirements jsr ON j.JobProfileID = jsr.JobProfileID
LEFT JOIN analytics_job_similarities ajs ON j.JobProfileID = ajs.job_from
WHERE j.JobProfileID = ?
  AND j.JobProfile IS NOT NULL  -- FAIL-FAST validation
GROUP BY j.JobProfileID, j.JobProfile, j.JobFunction, j.JobFunctionID, j.ManagementLevel, j.JobCategory;

-- query_name: search_jobs
-- Search jobs by title with optional function filter
SELECT 
    JobProfileID as id,
    JobProfile as job_title,
    JobFunction as job_function,
    JobFunctionID as job_function_id,
    ManagementLevel as management_level
FROM core_job_architecture
WHERE JobProfile LIKE ?
    AND (? IS NULL OR JobFunction = ?)
    AND JobProfile IS NOT NULL  -- FAIL-FAST validation
ORDER BY JobProfile
LIMIT 50;

-- query_name: get_job_skills
-- Get all skills for a specific job with V2 enhancements
SELECT 
    st.Skill_Name as skill_name,
    st.Category as skill_category,
    st.Subcategory as skill_subcategory,
    st.SkillType as skill_type,
    st.Skill_ID as skill_id,
    NULL as proficiency_requirement,  -- Not in V2 schema
    NULL as is_defining_skill,       -- Not in V2 schema
    NULL as importance_score         -- Not in V2 schema
FROM core_job_skill_requirements jsr
INNER JOIN core_skills_taxonomy st ON jsr.Skill_ID = st.Skill_ID
WHERE jsr.JobProfileID = ?
  AND st.Skill_Name IS NOT NULL  -- FAIL-FAST validation
ORDER BY st.Category, st.Skill_Name;

-- query_name: get_jobs_by_level
-- Get jobs filtered by management level
SELECT 
    JobProfileID as id,
    JobProfile as job_title,
    JobFunction as job_function,
    JobFunctionID as job_function_id,
    ManagementLevel as management_level
FROM core_job_architecture
WHERE ManagementLevel = ?
  AND JobProfile IS NOT NULL  -- FAIL-FAST validation
ORDER BY JobFunction, JobProfile;

-- query_name: get_jobs_by_category
-- Get jobs filtered by job category
SELECT 
    JobProfileID as id,
    JobProfile as job_title,
    JobFunction as job_function,
    JobFunctionID as job_function_id,
    JobCategory as job_category
FROM core_job_architecture
WHERE JobCategory = ?
  AND JobProfile IS NOT NULL  -- FAIL-FAST validation
ORDER BY JobProfile;

-- query_name: get_job_summary_stats
-- Get summary statistics for jobs with V2 analytics
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
        COUNT(jsr.Skill_ID) as skill_count
    FROM core_job_architecture j
    LEFT JOIN core_job_skill_requirements jsr ON j.JobProfileID = jsr.JobProfileID
    WHERE j.JobProfile IS NOT NULL  -- FAIL-FAST validation
    GROUP BY j.JobProfileID, j.JobFunction, j.ManagementLevel, j.JobCategory
) job_stats;

-- query_name: get_job_complete_details
-- Get complete job information with all available columns for API endpoints
SELECT 
    JobProfileID,
    JobProfile,
    JobFunctionID,
    JobFunction,
    Job,
    ProfileTitleSuffix,
    ManagementLevel,
    JobSubFunction,
    JobCategory,
    Customer_Facing,
    is_Banker
FROM core_job_architecture
WHERE JobProfileID = ?
  AND JobProfile IS NOT NULL;  -- FAIL-FAST validation

-- query_name: get_job_skills_for_api
-- Get all skills for a specific job for API endpoints
SELECT 
    st.Skill_ID,
    st.Skill_Name,
    st.Category,
    st.Subcategory,
    st.SkillType,
    '' as Info_URL  -- Not available in V2 schema
FROM core_job_skill_requirements jsr
INNER JOIN core_skills_taxonomy st ON jsr.Skill_ID = st.Skill_ID
WHERE jsr.JobProfileID = ?
  AND st.Skill_Name IS NOT NULL  -- FAIL-FAST validation
ORDER BY st.Category, st.Skill_Name;

-- query_name: get_job_workforce_stats
-- Get position and employee counts for a specific job
SELECT 
    COUNT(DISTINCT position_number) as position_count,
    COUNT(DISTINCT employee_number) as employee_count
FROM core_workforce_current
WHERE JobProfileID = ?;

-- query_name: get_job_pathway_count
-- Get count of career pathways available for a job using V2 analytics
SELECT COUNT(*) as pathway_count
FROM analytics_job_similarities
WHERE job_from = ?
  AND enhanced_similarity_score IS NOT NULL;

-- query_name: get_job_families
-- Get all job families/functions for dropdowns and navigation
SELECT DISTINCT 
    ja.JobFunction as job_family,
    COUNT(*) as job_count
FROM core_job_architecture ja
WHERE ja.JobFunction IS NOT NULL  -- FAIL-FAST validation
GROUP BY ja.JobFunction
ORDER BY COUNT(*) DESC, ja.JobFunction;

-- query_name: get_all_jobs_for_selection
-- Get all jobs for career analysis and pathway selection dropdowns
SELECT 
    JobProfileID,
    JobProfile,
    JobFunction,
    JobFunctionID,
    ManagementLevel
FROM core_job_architecture
WHERE JobProfile IS NOT NULL  -- FAIL-FAST validation
ORDER BY JobProfile; 