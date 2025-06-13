-- =====================================================================
-- Career Pathway Visualization Queries for D3.js Collapsible Tree
-- =====================================================================
-- These queries generate hierarchical data for career pathway exploration
-- Structure: Job Family → Source Job → Similar Jobs → Skills Gap Analysis

-- ===================
-- 1. Job Family Overview
-- ===================
-- Get all job families with job counts for tree root nodes
SELECT 
    JobFamily as family_name,
    COUNT(*) as job_count,
    JobFamilyGroup as family_group
FROM jobs 
WHERE JobFamily IS NOT NULL
GROUP BY JobFamily, JobFamilyGroup
ORDER BY job_count DESC;

-- ===================
-- 2. Jobs within Family  
-- ===================
-- Get all jobs within a specific family (for tree level 1)
SELECT 
    JobProfileID,
    JobProfile as job_title,
    JobFamily,
    JobID,
    Job as job_name
FROM jobs 
WHERE JobFamily = :family_name
ORDER BY JobProfile;

-- ===================
-- 3. Career Pathway Tree Data
-- ===================
-- Generate hierarchical career pathway data for a specific job family
-- This creates the main tree structure: Source Job → Target Jobs → Skills
WITH job_pathways AS (
    SELECT DISTINCT
        j1.JobFamily as source_family,
        j1.JobProfileID as source_job_id,
        j1.JobProfile as source_job_title,
        j2.JobFamily as target_family,
        j2.JobProfileID as target_job_id, 
        j2.JobProfile as target_job_title,
        js.similarity_score,
        CASE 
            WHEN js.similarity_score >= 0.8 THEN 'High'
            WHEN js.similarity_score >= 0.6 THEN 'Medium' 
            WHEN js.similarity_score >= 0.4 THEN 'Low'
            ELSE 'Very Low'
        END as similarity_level
    FROM job_similarities js
    JOIN jobs j1 ON js.job_from = j1.JobProfileID
    JOIN jobs j2 ON js.job_to = j2.JobProfileID  
    WHERE j1.JobFamily = :source_family
      AND js.similarity_score >= 0.4  -- Filter for meaningful similarities
      AND j1.JobProfileID != j2.JobProfileID  -- Exclude self-matches
)
SELECT 
    source_family,
    source_job_id,
    source_job_title,
    target_family,
    target_job_id,
    target_job_title,
    similarity_score,
    similarity_level,
    COUNT(*) OVER (PARTITION BY source_job_id) as pathway_count
FROM job_pathways
ORDER BY source_job_title, similarity_score DESC;

-- ===================
-- 4. Skills Gap Analysis for Career Transition
-- ===================
-- Compare skills between source and target jobs for transition planning
WITH source_skills AS (
    SELECT js.Skill_ID, s.Skill_Name, s.Category
    FROM job_skills js
    JOIN skills s ON js.Skill_ID = s.Skill_ID
    WHERE js.JobProfileID = :source_job_id
),
target_skills AS (
    SELECT js.Skill_ID, s.Skill_Name, s.Category  
    FROM job_skills js
    JOIN skills s ON js.Skill_ID = s.Skill_ID
    WHERE js.JobProfileID = :target_job_id
)
SELECT 
    COALESCE(ts.Skill_Name, ss.Skill_Name) as skill_name,
    COALESCE(ts.Category, ss.Category) as skill_category,
    CASE 
        WHEN ss.Skill_ID IS NOT NULL AND ts.Skill_ID IS NOT NULL THEN 'Transferable'
        WHEN ss.Skill_ID IS NOT NULL AND ts.Skill_ID IS NULL THEN 'Source Only'
        WHEN ss.Skill_ID IS NULL AND ts.Skill_ID IS NOT NULL THEN 'Target Required'
    END as skill_status,
    COALESCE(ts.Skill_ID, ss.Skill_ID) as skill_id
FROM target_skills ts
FULL OUTER JOIN source_skills ss ON ts.Skill_ID = ss.Skill_ID
ORDER BY skill_status, skill_category, skill_name;

-- ===================
-- 5. Position Context for Career Pathways
-- ===================
-- Show available positions and organizational context for target jobs
SELECT DISTINCT
    p."Position Number",
    p.JobProfileID,
    j.JobProfile,
    p.Division,
    p.Business_Unit,
    p.Team,
    p.Location,
    p."Employee Number",
    CASE WHEN p."Employee Number" IS NULL THEN 'Vacant' ELSE 'Occupied' END as position_status
FROM positions p
JOIN jobs j ON p.JobProfileID = j.JobProfileID
WHERE j.JobProfileID = :target_job_id
ORDER BY p.Division, p.Business_Unit, p.Team;

-- ===================
-- 6. D3.js Tree Data Structure Query
-- ===================
-- Generate properly formatted hierarchical data for D3.js collapsible tree
-- This query creates the nested JSON structure that D3.js expects
WITH RECURSIVE career_tree AS (
    -- Root level: Job Families
    SELECT 
        1 as level,
        JobFamily as id,
        JobFamily as name,
        'family' as type,
        NULL as parent_id,
        COUNT(*) as size,
        JobFamily as path
    FROM jobs 
    WHERE JobFamily IS NOT NULL
    GROUP BY JobFamily
    
    UNION ALL
    
    -- Level 2: Jobs within families  
    SELECT
        2 as level,
        j.JobProfileID as id,
        j.JobProfile as name,
        'job' as type, 
        j.JobFamily as parent_id,
        1 as size,
        j.JobFamily || '/' || j.JobProfileID as path
    FROM jobs j
    WHERE j.JobFamily IS NOT NULL
    
    UNION ALL
    
    -- Level 3: Similar jobs (career pathway targets)
    SELECT
        3 as level,
        js.job_to as id,
        j2.JobProfile as name,
        'target_job' as type,
        js.job_from as parent_id,
        ROUND(js.similarity_score * 100) as size,
        j1.JobFamily || '/' || js.job_from || '/' || js.job_to as path
    FROM job_similarities js
    JOIN jobs j1 ON js.job_from = j1.JobProfileID
    JOIN jobs j2 ON js.job_to = j2.JobProfileID
    WHERE js.similarity_score >= 0.4
      AND js.job_from != js.job_to
)
SELECT 
    level,
    id,
    name,
    type,
    parent_id,
    size,
    path
FROM career_tree
ORDER BY level, parent_id, size DESC;

-- ===================
-- 7. Interactive Tree Data (Family-Specific)
-- ===================
-- Generate tree data for a specific job family (used by API endpoint)
SELECT json_group_array(
    json_object(
        'id', JobProfileID,
        'name', JobProfile,
        'family', JobFamily,
        'similarity_targets', (
            SELECT json_group_array(
                json_object(
                    'id', j2.JobProfileID,
                    'name', j2.JobProfile, 
                    'family', j2.JobFamily,
                    'similarity', js.similarity_score,
                    'skills_gap', (
                        SELECT COUNT(*)
                        FROM job_skills js_target
                        LEFT JOIN job_skills js_source ON js_source.Skill_ID = js_target.Skill_ID 
                            AND js_source.JobProfileID = j1.JobProfileID
                        WHERE js_target.JobProfileID = j2.JobProfileID
                          AND js_source.Skill_ID IS NULL
                    )
                )
            )
            FROM job_similarities js
            JOIN jobs j2 ON js.job_to = j2.JobProfileID
            WHERE js.job_from = j1.JobProfileID 
              AND js.similarity_score >= 0.5
              AND js.job_from != js.job_to
            ORDER BY js.similarity_score DESC
            LIMIT 10
        )
    )
) as tree_data
FROM jobs j1
WHERE j1.JobFamily = :family_name
ORDER BY j1.JobProfile;

-- ===================
-- 8. Skills Sunburst Data (Alternative Visualization)
-- ===================
-- Generate data for a skills-focused sunburst chart (bonus visualization)
SELECT 
    s.Category as category,
    s.Subcategory as subcategory,
    s.Skill_Name as skill_name,
    COUNT(DISTINCT js.JobProfileID) as job_count,
    AVG(js.Skill_Weight) as avg_importance
FROM skills s
JOIN job_skills js ON s.Skill_ID = js.Skill_ID
JOIN jobs j ON js.JobProfileID = j.JobProfileID
WHERE j.JobFamily = :family_name
  AND s.Category IS NOT NULL
  AND s.Category != ''
GROUP BY s.Category, s.Subcategory, s.Skill_Name
HAVING job_count >= 2  -- Only skills used by multiple jobs
ORDER BY category, subcategory, job_count DESC;

-- ===================
-- Sample Parameter Values for Testing
-- ===================
-- Use these parameter values when testing queries:
-- :family_name = 'Data & Analytics'
-- :source_job_id = 'R0001.5' 
-- :target_job_id = 'R0001.6' 