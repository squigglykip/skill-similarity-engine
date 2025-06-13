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
    j.job_title,
    j.job_family,
    j.job_level
FROM positions p
JOIN jobs j ON p.JobProfileID = j.id
WHERE p.JobProfileID = ?
ORDER BY p.CompanyOrganisationID, p.CompanyDivisionID;

-- query_name: get_positions_by_organisation
-- Get positions within a specific organisation or division
SELECT 
    p.PositionID,
    p.JobProfileID,
    j.job_title,
    j.job_family,
    j.job_level,
    COUNT(*) OVER (PARTITION BY j.job_family) as family_positions_count,
    COUNT(*) OVER (PARTITION BY p.CompanyDivisionID) as division_positions_count
FROM positions p
JOIN jobs j ON p.JobProfileID = j.id
WHERE (? IS NULL OR p.CompanyOrganisationID = ?)
    AND (? IS NULL OR p.CompanyDivisionID = ?)
ORDER BY j.job_family, j.job_title;

-- query_name: get_organisation_structure
-- Get organisational structure showing hierarchy of positions
SELECT 
    p.CompanyOrganisationID,
    p.CompanyDivisionID,
    p.CompanyBusinessUnitID,
    COUNT(DISTINCT p.PositionID) as total_positions,
    COUNT(DISTINCT j.job_family) as job_families_count,
    COUNT(DISTINCT j.id) as unique_jobs_count,
    GROUP_CONCAT(DISTINCT j.job_family) as job_families
FROM positions p
JOIN jobs j ON p.JobProfileID = j.id
GROUP BY p.CompanyOrganisationID, p.CompanyDivisionID, p.CompanyBusinessUnitID
ORDER BY p.CompanyOrganisationID, p.CompanyDivisionID, p.CompanyBusinessUnitID;

-- query_name: get_position_distribution_by_location
-- Get distribution of positions across different locations
SELECT 
    p.CompanyLocationID,
    COUNT(DISTINCT p.PositionID) as position_count,
    COUNT(DISTINCT j.job_family) as job_families,
    COUNT(DISTINCT j.id) as unique_jobs,
    GROUP_CONCAT(DISTINCT j.job_family) as families_present
FROM positions p
JOIN jobs j ON p.JobProfileID = j.id
WHERE p.CompanyLocationID IS NOT NULL
GROUP BY p.CompanyLocationID
ORDER BY position_count DESC;

-- query_name: get_job_family_distribution
-- Get distribution of job families across the organisation
SELECT 
    j.job_family,
    COUNT(DISTINCT p.PositionID) as position_count,
    COUNT(DISTINCT p.CompanyOrganisationID) as organisations,
    COUNT(DISTINCT p.CompanyDivisionID) as divisions,
    COUNT(DISTINCT p.CompanyLocationID) as locations,
    COUNT(DISTINCT j.id) as unique_job_profiles
FROM positions p
JOIN jobs j ON p.JobProfileID = j.id
GROUP BY j.job_family
ORDER BY position_count DESC;

-- query_name: get_positions_needing_skills
-- Find positions that require specific skills (for talent management)
SELECT 
    p.PositionID,
    p.JobProfileID,
    j.job_title,
    j.job_family,
    p.CompanyOrganisationID,
    p.CompanyDivisionID,
    p.CompanyLocationID,
    s.skill_name,
    js.proficiency_level
FROM positions p
JOIN jobs j ON p.JobProfileID = j.id
JOIN job_skills js ON j.id = js.job_id
JOIN skills s ON js.skills_skill_id = s.id
WHERE s.skill_name LIKE ?
    OR s.skill_category = ?
ORDER BY p.CompanyOrganisationID, j.job_family, js.proficiency_level DESC;

-- query_name: get_career_opportunities_by_location
-- Find career progression opportunities within specific locations
SELECT 
    current_pos.CompanyLocationID,
    current_jobs.job_family as current_family,
    current_jobs.job_level as current_level,
    target_jobs.job_family as target_family,
    target_jobs.job_level as target_level,
    COUNT(DISTINCT target_pos.PositionID) as available_positions,
    AVG(js.similarity_score) as avg_similarity
FROM positions current_pos
JOIN jobs current_jobs ON current_pos.JobProfileID = current_jobs.id
JOIN job_similarities js ON current_jobs.id = js.job_id
JOIN jobs target_jobs ON js.similar_job_id = target_jobs.id
JOIN positions target_pos ON target_jobs.id = target_pos.JobProfileID
WHERE current_pos.CompanyLocationID = target_pos.CompanyLocationID
    AND current_pos.JobProfileID = ?
    AND js.similarity_score >= ?
GROUP BY current_pos.CompanyLocationID, current_jobs.job_family, current_jobs.job_level, 
         target_jobs.job_family, target_jobs.job_level
ORDER BY avg_similarity DESC, available_positions DESC;

-- query_name: get_skills_demand_by_division
-- Analyse skills demand across different divisions
SELECT 
    p.CompanyDivisionID,
    s.skill_category,
    s.skill_name,
    COUNT(DISTINCT p.PositionID) as positions_requiring,
    COUNT(DISTINCT j.id) as jobs_requiring,
    AVG(CASE 
        WHEN js.proficiency_level = 'Beginner' THEN 1
        WHEN js.proficiency_level = 'Intermediate' THEN 2
        WHEN js.proficiency_level = 'Advanced' THEN 3
        WHEN js.proficiency_level = 'Expert' THEN 4
        ELSE 2
    END) as avg_proficiency_required
FROM positions p
JOIN jobs j ON p.JobProfileID = j.id
JOIN job_skills js ON j.id = js.job_id
JOIN skills s ON js.skills_skill_id = s.id
WHERE p.CompanyDivisionID IS NOT NULL
GROUP BY p.CompanyDivisionID, s.skill_category, s.skill_name
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
    COUNT(DISTINCT j.job_family) as job_families,
    AVG(position_counts.positions_per_job) as avg_positions_per_job
FROM positions p
JOIN jobs j ON p.JobProfileID = j.id
CROSS JOIN (
    SELECT AVG(job_position_count) as positions_per_job
    FROM (
        SELECT JobProfileID, COUNT(*) as job_position_count
        FROM positions
        GROUP BY JobProfileID
    )
) position_counts; 