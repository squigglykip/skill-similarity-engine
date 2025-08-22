-- =================================================================
-- POSITIONS QUERIES - V2 SCHEMA
-- Queries for position information and organisational context
-- Updated for core_workforce_current table and V2 analytics
-- =================================================================

-- query_name: get_positions_for_job
-- Get all positions/instances of a specific job profile
SELECT 
    cwc.position_id,
    cwc.job_profile_id,
    cwc.organisation_id,
    cwc.division_id,
    cwc.business_unit_id,
    cwc.location_id,
    ja.job_title,
    ja.job_function,
    ja.management_level
FROM core_workforce_current cwc
INNER JOIN core_job_architecture ja ON cwc.job_profile_id = ja.JobProfileID
WHERE cwc.job_profile_id = ?
  AND ja.job_title IS NOT NULL  -- FAIL-FAST validation
ORDER BY cwc.organisation_id, cwc.division_id;

-- query_name: get_positions_by_organisation
-- Get positions within a specific organisation or division
SELECT 
    cwc.position_id,
    cwc.job_profile_id,
    ja.job_title,
    ja.job_function,
    ja.management_level,
    COUNT(*) OVER (PARTITION BY ja.job_function) as function_positions_count,
    COUNT(*) OVER (PARTITION BY cwc.division_id) as division_positions_count
FROM core_workforce_current cwc
INNER JOIN core_job_architecture ja ON cwc.job_profile_id = ja.JobProfileID
WHERE (? IS NULL OR cwc.organisation_id = ?)
    AND (? IS NULL OR cwc.division_id = ?)
    AND ja.job_title IS NOT NULL  -- FAIL-FAST validation
ORDER BY ja.job_function, ja.job_title;

-- query_name: get_organisation_structure
-- Get organisational structure showing hierarchy of positions
SELECT 
    cwc.organisation_id,
    cwc.division_id,
    cwc.business_unit_id,
    COUNT(DISTINCT cwc.position_id) as total_positions,
    COUNT(DISTINCT ja.job_function) as job_functions_count,
    COUNT(DISTINCT ja.JobProfileID) as unique_jobs_count,
    GROUP_CONCAT(DISTINCT ja.job_function) as job_functions
FROM core_workforce_current cwc
INNER JOIN core_job_architecture ja ON cwc.job_profile_id = ja.JobProfileID
WHERE ja.job_title IS NOT NULL  -- FAIL-FAST validation
GROUP BY cwc.organisation_id, cwc.division_id, cwc.business_unit_id
ORDER BY cwc.organisation_id, cwc.division_id, cwc.business_unit_id;

-- query_name: get_position_distribution_by_location
-- Get distribution of positions across different locations
SELECT 
    cwc.location_id,
    COUNT(DISTINCT cwc.position_id) as position_count,
    COUNT(DISTINCT ja.job_function) as job_functions,
    COUNT(DISTINCT ja.JobProfileID) as unique_jobs,
    GROUP_CONCAT(DISTINCT ja.job_function) as functions_present
FROM core_workforce_current cwc
INNER JOIN core_job_architecture ja ON cwc.job_profile_id = ja.JobProfileID
WHERE cwc.location_id IS NOT NULL
    AND ja.job_title IS NOT NULL  -- FAIL-FAST validation
GROUP BY cwc.location_id
ORDER BY position_count DESC;

-- query_name: get_job_function_distribution
-- Get distribution of job functions across the organisation
SELECT 
    ja.job_function,
    COUNT(DISTINCT cwc.position_id) as position_count,
    COUNT(DISTINCT cwc.organisation_id) as organisations,
    COUNT(DISTINCT cwc.division_id) as divisions,
    COUNT(DISTINCT cwc.location_id) as locations,
    COUNT(DISTINCT ja.JobProfileID) as unique_job_profiles
FROM core_workforce_current cwc
INNER JOIN core_job_architecture ja ON cwc.job_profile_id = ja.JobProfileID
WHERE ja.job_title IS NOT NULL  -- FAIL-FAST validation
GROUP BY ja.job_function
ORDER BY position_count DESC;

-- query_name: get_positions_needing_skills
-- Find positions that require specific skills (for talent management) with V2 enhancements
SELECT 
    cwc.position_id,
    cwc.job_profile_id,
    ja.job_title,
    ja.job_function,
    cwc.organisation_id,
    cwc.division_id,
    cwc.location_id,
    st.skill_name,
    st.primary_category as skill_category,
    jsr.proficiency_requirement,
    jsr.is_defining_skill
FROM core_workforce_current cwc
INNER JOIN core_job_architecture ja ON cwc.job_profile_id = ja.JobProfileID
INNER JOIN core_job_skill_requirements jsr ON ja.JobProfileID = jsr.job_profile_id
INNER JOIN core_skills_taxonomy st ON jsr.skill_id = st.Skill_ID
WHERE (st.skill_name LIKE ? OR st.primary_category = ?)
    AND ja.job_title IS NOT NULL  -- FAIL-FAST validation
    AND st.skill_name IS NOT NULL
ORDER BY cwc.organisation_id, ja.job_function, st.skill_name;

-- query_name: get_career_opportunities_by_location
-- Find career progression opportunities within specific locations using V2 analytics
SELECT 
    current_cwc.location_id,
    current_ja.job_function as current_function,
    current_ja.management_level as current_level,
    target_ja.job_function as target_function,
    target_ja.management_level as target_level,
    COUNT(DISTINCT target_cwc.position_id) as available_positions,
    AVG(ajs.enhanced_similarity_score) as avg_similarity,
    AVG(ajs.rarity_weighted_score) as avg_rarity_weighted_score
FROM core_workforce_current current_cwc
INNER JOIN core_job_architecture current_ja ON current_cwc.job_profile_id = current_ja.JobProfileID
INNER JOIN analytics_job_similarities ajs ON current_ja.JobProfileID = ajs.job_from
INNER JOIN core_job_architecture target_ja ON ajs.job_to = target_ja.JobProfileID
INNER JOIN core_workforce_current target_cwc ON target_ja.JobProfileID = target_cwc.job_profile_id
WHERE current_cwc.location_id = target_cwc.location_id
    AND current_cwc.job_profile_id = ?
    AND ajs.enhanced_similarity_score >= ?
    AND ajs.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
    AND current_ja.job_title IS NOT NULL
    AND target_ja.job_title IS NOT NULL
GROUP BY current_cwc.location_id, current_ja.job_function, current_ja.management_level,
         target_ja.job_function, target_ja.management_level
ORDER BY avg_similarity DESC, available_positions DESC;

-- query_name: get_skills_demand_by_division
-- Analyse skills demand across different divisions with V2 enhancements
SELECT 
    cwc.division_id,
    st.primary_category as skill_category,
    st.skill_name,
    COUNT(DISTINCT cwc.position_id) as positions_requiring,
    COUNT(DISTINCT ja.JobProfileID) as jobs_requiring,
    st.skill_type,
    AVG(jsr.proficiency_requirement) as avg_proficiency_required,
    SUM(CASE WHEN jsr.is_defining_skill = 1 THEN 1 ELSE 0 END) as defining_skill_instances
FROM core_workforce_current cwc
INNER JOIN core_job_architecture ja ON cwc.job_profile_id = ja.JobProfileID
INNER JOIN core_job_skill_requirements jsr ON ja.JobProfileID = jsr.job_profile_id
INNER JOIN core_skills_taxonomy st ON jsr.skill_id = st.Skill_ID
WHERE cwc.division_id IS NOT NULL
    AND ja.job_title IS NOT NULL  -- FAIL-FAST validation
    AND st.skill_name IS NOT NULL
GROUP BY cwc.division_id, st.primary_category, st.skill_name, st.skill_type
HAVING positions_requiring >= ?
ORDER BY cwc.division_id, positions_requiring DESC;

-- query_name: get_position_summary_stats
-- Get summary statistics for positions and organisational structure with V2 analytics
SELECT 
    COUNT(DISTINCT cwc.position_id) as total_positions,
    COUNT(DISTINCT cwc.job_profile_id) as unique_job_profiles,
    COUNT(DISTINCT cwc.organisation_id) as organisations,
    COUNT(DISTINCT cwc.division_id) as divisions,
    COUNT(DISTINCT cwc.business_unit_id) as business_units,
    COUNT(DISTINCT cwc.location_id) as locations,
    COUNT(DISTINCT ja.job_function) as job_functions,
    AVG(position_counts.positions_per_job) as avg_positions_per_job
FROM core_workforce_current cwc
INNER JOIN core_job_architecture ja ON cwc.job_profile_id = ja.JobProfileID
CROSS JOIN (
    SELECT AVG(job_position_count) as positions_per_job
    FROM (
        SELECT job_profile_id, COUNT(*) as job_position_count
        FROM core_workforce_current
        GROUP BY job_profile_id
    )
) position_counts
WHERE ja.job_title IS NOT NULL;  -- FAIL-FAST validation

-- query_name: get_job_workforce_distribution
-- Get workforce distribution by division, business unit, and location for a specific job
SELECT 
    cwc.ORG_UNIT_NAME_2 as Division,
    cwc.ORG_UNIT_NAME_3 as Business_Unit,
    cwc.Location,
    COUNT(DISTINCT cwc.employee_number) as employee_count
FROM core_workforce_current cwc
WHERE cwc.JobProfileID = ?
  AND cwc.employee_number IS NOT NULL  -- FAIL-FAST validation
GROUP BY cwc.ORG_UNIT_NAME_2, cwc.ORG_UNIT_NAME_3, cwc.Location
ORDER BY employee_count DESC;

-- query_name: get_detailed_workforce_analysis
-- Get detailed workforce analysis for multiple jobs (dynamic placeholders)
-- Note: This query template needs placeholders to be replaced dynamically
SELECT 
    ja.JobProfileID,
    ja.JobProfile,
    ja.JobFunction,
    (ja.JobProfile || ' (' || ja.JobProfileID || ')') as job_profile,
    cwc.position_name,
    cwc.ORG_UNIT_NAME_2 as Division,
    cwc.ORG_UNIT_NAME_3 as Business_Unit,
    cwc.ORG_UNIT_NAME_4 as Team,
    cwc.Salary_Group as salary_group,
    cwc.Employee_Group as employee_group,
    cwc.Location,
    cwc.Rg,
    COUNT(DISTINCT cwc.position_number) as position_count,
    COUNT(DISTINCT cwc.employee_number) as headcount
FROM core_job_architecture ja
LEFT JOIN core_workforce_current cwc ON ja.JobProfileID = cwc.JobProfileID
WHERE ja.JobProfileID IN ({placeholders})
  AND ja.JobProfile IS NOT NULL  -- FAIL-FAST validation
GROUP BY ja.JobProfileID, ja.JobProfile, ja.JobFunction, cwc.position_name, 
         cwc.ORG_UNIT_NAME_2, cwc.ORG_UNIT_NAME_3, cwc.ORG_UNIT_NAME_4, 
         cwc.Salary_Group, cwc.Employee_Group, cwc.Location, cwc.Rg
ORDER BY ja.JobProfile, cwc.ORG_UNIT_NAME_2, cwc.ORG_UNIT_NAME_3, position_count DESC; 