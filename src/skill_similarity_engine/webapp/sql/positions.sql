-- =================================================================
-- POSITIONS QUERIES
-- Queries for position information and organisational context
-- =================================================================

-- query_name: get_positions_for_job
-- Get all positions/instances of a specific job profile
SELECT 
    p.PositionID,
    p.JobProfileID,
    p.CompanyOrganisationID,
    p.CompanyDivisionID,
    p.CompanyBusinessUnitID,
    p.CompanyLocationID,
    j.JobProfile as job_title,
    j.JobFunction as job_function,
    j.ManagementLevel as management_level
FROM positions p
JOIN jobs j ON p.JobProfileID = j.JobProfileID
WHERE p.JobProfileID = ?
ORDER BY p.CompanyOrganisationID, p.CompanyDivisionID;

-- query_name: get_positions_by_organisation
-- Get positions within a specific organisation or division
SELECT 
    p.PositionID,
    p.JobProfileID,
    j.JobProfile as job_title,
    j.JobFunction as job_function,
    j.ManagementLevel as management_level,
    COUNT(*) OVER (PARTITION BY j.JobFunction) as function_positions_count,
    COUNT(*) OVER (PARTITION BY p.CompanyDivisionID) as division_positions_count
FROM positions p
JOIN jobs j ON p.JobProfileID = j.JobProfileID
WHERE (? IS NULL OR p.CompanyOrganisationID = ?)
    AND (? IS NULL OR p.CompanyDivisionID = ?)
ORDER BY j.JobFunction, j.JobProfile;

-- query_name: get_organisation_structure
-- Get organisational structure showing hierarchy of positions
SELECT 
    p.CompanyOrganisationID,
    p.CompanyDivisionID,
    p.CompanyBusinessUnitID,
    COUNT(DISTINCT p.PositionID) as total_positions,
    COUNT(DISTINCT j.JobFunction) as job_functions_count,
    COUNT(DISTINCT j.JobProfileID) as unique_jobs_count,
    GROUP_CONCAT(DISTINCT j.JobFunction) as job_functions
FROM positions p
JOIN jobs j ON p.JobProfileID = j.JobProfileID
GROUP BY p.CompanyOrganisationID, p.CompanyDivisionID, p.CompanyBusinessUnitID
ORDER BY p.CompanyOrganisationID, p.CompanyDivisionID, p.CompanyBusinessUnitID;

-- query_name: get_position_distribution_by_location
-- Get distribution of positions across different locations
SELECT 
    p.CompanyLocationID,
    COUNT(DISTINCT p.PositionID) as position_count,
    COUNT(DISTINCT j.JobFunction) as job_functions,
    COUNT(DISTINCT j.JobProfileID) as unique_jobs,
    GROUP_CONCAT(DISTINCT j.JobFunction) as functions_present
FROM positions p
JOIN jobs j ON p.JobProfileID = j.JobProfileID
WHERE p.CompanyLocationID IS NOT NULL
GROUP BY p.CompanyLocationID
ORDER BY position_count DESC;

-- query_name: get_job_function_distribution
-- Get distribution of job functions across the organisation
SELECT 
    j.JobFunction as job_function,
    COUNT(DISTINCT p.PositionID) as position_count,
    COUNT(DISTINCT p.CompanyOrganisationID) as organisations,
    COUNT(DISTINCT p.CompanyDivisionID) as divisions,
    COUNT(DISTINCT p.CompanyLocationID) as locations,
    COUNT(DISTINCT j.JobProfileID) as unique_job_profiles
FROM positions p
JOIN jobs j ON p.JobProfileID = j.JobProfileID
GROUP BY j.JobFunction
ORDER BY position_count DESC;

-- query_name: get_positions_needing_skills
-- Find positions that require specific skills (for talent management)
SELECT 
    p.PositionID,
    p.JobProfileID,
    j.JobProfile as job_title,
    j.JobFunction as job_function,
    p.CompanyOrganisationID,
    p.CompanyDivisionID,
    p.CompanyLocationID,
    s.Skill_Name as skill_name,
    s.Category as skill_category
FROM positions p
JOIN jobs j ON p.JobProfileID = j.JobProfileID
JOIN job_skills js ON j.JobProfileID = js.JobProfileID
JOIN skills s ON js.Skill_ID = s.Skill_ID
WHERE s.Skill_Name LIKE ?
    OR s.Category = ?
ORDER BY p.CompanyOrganisationID, j.JobFunction, s.Skill_Name;

-- query_name: get_career_opportunities_by_location
-- Find career progression opportunities within specific locations
SELECT 
    current_pos.CompanyLocationID,
    current_jobs.JobFunction as current_function,
    current_jobs.ManagementLevel as current_level,
    target_jobs.JobFunction as target_function,
    target_jobs.ManagementLevel as target_level,
    COUNT(DISTINCT target_pos.PositionID) as available_positions,
    AVG(cp.similarity_score) as avg_similarity
FROM positions current_pos
JOIN jobs current_jobs ON current_pos.JobProfileID = current_jobs.JobProfileID
JOIN career_pathways cp ON current_jobs.JobProfileID = cp.source_job_id
JOIN jobs target_jobs ON cp.target_job_id = target_jobs.JobProfileID
JOIN positions target_pos ON target_jobs.JobProfileID = target_pos.JobProfileID
WHERE current_pos.CompanyLocationID = target_pos.CompanyLocationID
    AND current_pos.JobProfileID = ?
    AND cp.similarity_score >= ?
GROUP BY current_pos.CompanyLocationID, current_jobs.JobFunction, current_jobs.ManagementLevel,
         target_jobs.JobFunction, target_jobs.ManagementLevel
ORDER BY avg_similarity DESC, available_positions DESC;

-- query_name: get_skills_demand_by_division
-- Analyse skills demand across different divisions
SELECT 
    p.CompanyDivisionID,
    s.Category as skill_category,
    s.Skill_Name as skill_name,
    COUNT(DISTINCT p.PositionID) as positions_requiring,
    COUNT(DISTINCT j.JobProfileID) as jobs_requiring,
    s.SkillType as skill_type
FROM positions p
JOIN jobs j ON p.JobProfileID = j.JobProfileID
JOIN job_skills js ON j.JobProfileID = js.JobProfileID
JOIN skills s ON js.Skill_ID = s.Skill_ID
WHERE p.CompanyDivisionID IS NOT NULL
GROUP BY p.CompanyDivisionID, s.Category, s.Skill_Name, s.SkillType
HAVING positions_requiring >= ?
ORDER BY p.CompanyDivisionID, positions_requiring DESC;

-- query_name: get_position_summary_stats
-- Get summary statistics for positions and organisational structure
SELECT 
    COUNT(DISTINCT p.PositionID) as total_positions,
    COUNT(DISTINCT p.JobProfileID) as unique_job_profiles,
    COUNT(DISTINCT p.CompanyOrganisationID) as organisations,
    COUNT(DISTINCT p.CompanyDivisionID) as divisions,
    COUNT(DISTINCT p.CompanyBusinessUnitID) as business_units,
    COUNT(DISTINCT p.CompanyLocationID) as locations,
    COUNT(DISTINCT j.JobFunction) as job_functions,
    AVG(position_counts.positions_per_job) as avg_positions_per_job
FROM positions p
JOIN jobs j ON p.JobProfileID = j.JobProfileID
CROSS JOIN (
    SELECT AVG(job_position_count) as positions_per_job
    FROM (
        SELECT JobProfileID, COUNT(*) as job_position_count
        FROM positions
        GROUP BY JobProfileID
    )
) position_counts; 