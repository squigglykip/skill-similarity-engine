-- =================================================================
-- D3.JS VISUALIZATION QUERIES - V2 SCHEMA MIGRATION
-- Queries for generating data structures for D3.js visualizations
-- Migrated from V1 tables to V2 analytics schema
-- =================================================================

-- query_name: get_tree_data_for_family
-- Generate hierarchical tree data for D3.js collapsible tree visualization
-- MIGRATED: jobs → core_job_architecture, job_similarities → analytics_job_similarities
SELECT 
    'function' as node_type,
    j.job_function as id,
    j.job_function as name,
    NULL as parent_id,
    COUNT(*) as children_count,
    0 as similarity_score,
    'Job Function' as category
FROM core_job_architecture j
WHERE j.job_function = ?
  AND j.job_title IS NOT NULL  -- FAIL-FAST validation
GROUP BY j.job_function

UNION ALL

SELECT 
    'job' as node_type,
    j.JobProfileID as id,
    j.job_title as name,
    j.job_function as parent_id,
    COUNT(DISTINCT js.job_to) as children_count,
    0 as similarity_score,
    COALESCE(j.job_sub_function, 'Unknown') as category
FROM core_job_architecture j
LEFT JOIN analytics_job_similarities js 
    ON j.JobProfileID = js.job_from 
    AND js.enhanced_similarity_score >= 0.7
    AND js.enhanced_similarity_score IS NOT NULL
WHERE j.job_function = ?
  AND j.job_title IS NOT NULL
GROUP BY j.JobProfileID, j.job_title, j.job_function, j.job_sub_function

UNION ALL

SELECT 
    'similar_job' as node_type,
    'sim_' || ranked_similarities.job_from || '_' || ranked_similarities.job_to as id,
    similar_job.job_title as name,
    ranked_similarities.job_from as parent_id,
    0 as children_count,
    ranked_similarities.enhanced_similarity_score as similarity_score,
    CASE 
        WHEN ranked_similarities.enhanced_similarity_score >= 0.8 THEN 'High'
        WHEN ranked_similarities.enhanced_similarity_score >= 0.7 THEN 'Medium'
        ELSE 'Low'
    END as category
FROM (
    SELECT 
        js.job_from,
        js.job_to,
        js.enhanced_similarity_score,
        ROW_NUMBER() OVER (PARTITION BY js.job_from ORDER BY js.enhanced_similarity_score DESC) as rank
    FROM analytics_job_similarities js
    JOIN core_job_architecture source_job ON js.job_from = source_job.JobProfileID
    WHERE source_job.job_function = ?
        AND js.enhanced_similarity_score >= 0.7
        AND js.enhanced_similarity_score IS NOT NULL
) ranked_similarities
JOIN core_job_architecture similar_job ON ranked_similarities.job_to = similar_job.JobProfileID
WHERE ranked_similarities.rank <= 5  -- Limit to top 5 similar jobs per job
ORDER BY node_type, similarity_score DESC, name;

-- query_name: get_network_data_for_similarities
-- Generate network data for D3.js force-directed graph of job similarities
-- MIGRATED: jobs → core_job_architecture, job_similarities → analytics_job_similarities
SELECT 
    'nodes' as data_type,
    j.JobProfileID as id,
    j.job_title as name,
    j.job_function as group,
    j.management_level as level,
    COUNT(DISTINCT js.job_to) as degree
FROM core_job_architecture j
LEFT JOIN analytics_job_similarities js 
    ON j.JobProfileID = js.job_from 
    AND js.enhanced_similarity_score >= ?
    AND js.enhanced_similarity_score IS NOT NULL
WHERE j.job_function = ?
  AND j.job_title IS NOT NULL
GROUP BY j.JobProfileID, j.job_title, j.job_function, j.management_level

UNION ALL

SELECT 
    'links' as data_type,
    js.job_from as source,
    js.job_to as target,
    js.enhanced_similarity_score as value,
    CASE 
        WHEN js.enhanced_similarity_score >= 0.8 THEN 'high'
        WHEN js.enhanced_similarity_score >= 0.6 THEN 'medium'
        ELSE 'low'
    END as type,
    NULL as degree
FROM analytics_job_similarities js
JOIN core_job_architecture j1 ON js.job_from = j1.JobProfileID
JOIN core_job_architecture j2 ON js.job_to = j2.JobProfileID
WHERE js.enhanced_similarity_score >= ?
    AND js.enhanced_similarity_score IS NOT NULL
    AND (j1.job_function = ? OR j2.job_function = ?)
ORDER BY data_type, value DESC;

-- query_name: get_sunburst_data
-- Generate hierarchical data for D3.js sunburst visualization of skills by category
-- MIGRATED: skills → core_skills_taxonomy, job_skills → core_job_skill_requirements, jobs → core_job_architecture
SELECT 
    'root' as level,
    'Skills' as id,
    'Skills' as name,
    NULL as parent,
    COUNT(DISTINCT s.Skill_ID) as value,
    'skills' as category
FROM core_skills_taxonomy s
JOIN core_job_skill_requirements jsr ON s.Skill_ID = jsr.Skill_ID
JOIN core_job_architecture j ON jsr.JobProfileID = j.JobProfileID
WHERE j.job_function = ?
  AND j.job_title IS NOT NULL

UNION ALL

SELECT 
    'category' as level,
    s.Category as id,
    s.Category as name,
    'Skills' as parent,
    COUNT(DISTINCT s.Skill_ID) as value,
    'category' as category
FROM core_skills_taxonomy s
JOIN core_job_skill_requirements jsr ON s.Skill_ID = jsr.Skill_ID
JOIN core_job_architecture j ON jsr.JobProfileID = j.JobProfileID
WHERE j.job_function = ?
  AND j.job_title IS NOT NULL
  AND s.Category IS NOT NULL
GROUP BY s.Category

UNION ALL

SELECT 
    'subcategory' as level,
    s.Category || ' - ' || s.Subcategory as id,
    s.Subcategory as name,
    s.Category as parent,
    COUNT(DISTINCT s.Skill_ID) as value,
    'subcategory' as category
FROM core_skills_taxonomy s
JOIN core_job_skill_requirements jsr ON s.Skill_ID = jsr.Skill_ID
JOIN core_job_architecture j ON jsr.JobProfileID = j.JobProfileID
WHERE j.job_function = ?
    AND j.job_title IS NOT NULL
    AND s.Subcategory IS NOT NULL
    AND s.Category IS NOT NULL
GROUP BY s.Category, s.Subcategory

UNION ALL

SELECT 
    'skill' as level,
    s.Skill_ID as id,
    s.Skill_Name as name,
    COALESCE(s.Category || ' - ' || s.Subcategory, s.Category) as parent,
    COUNT(DISTINCT jsr.JobProfileID) as value,
    'skill' as category
FROM core_skills_taxonomy s
JOIN core_job_skill_requirements jsr ON s.Skill_ID = jsr.Skill_ID
JOIN core_job_architecture j ON jsr.JobProfileID = j.JobProfileID
WHERE j.job_function = ?
  AND j.job_title IS NOT NULL
  AND s.Skill_Name IS NOT NULL
GROUP BY s.Skill_ID, s.Skill_Name, s.Category, s.Subcategory
ORDER BY level, value DESC;

-- query_name: get_chord_diagram_data
-- Generate data for D3.js chord diagram showing skill relationships between job functions
-- MIGRATED: V1 tables → V2 schema with enhanced similarity scoring
SELECT 
    source_function.job_function as source,
    target_function.job_function as target,
    COUNT(DISTINCT common_skills.Skill_ID) as shared_skills,
    AVG(js.enhanced_similarity_score) as avg_similarity
FROM core_job_architecture source_job
JOIN core_job_skill_requirements source_skills ON source_job.JobProfileID = source_skills.JobProfileID
JOIN core_job_skill_requirements target_skills ON source_skills.Skill_ID = target_skills.Skill_ID
JOIN core_job_architecture target_job ON target_skills.JobProfileID = target_job.JobProfileID
JOIN analytics_job_similarities js 
    ON source_job.JobProfileID = js.job_from 
    AND target_job.JobProfileID = js.job_to
JOIN (SELECT DISTINCT job_function FROM core_job_architecture WHERE job_function IS NOT NULL) source_function 
    ON source_job.job_function = source_function.job_function
JOIN (SELECT DISTINCT job_function FROM core_job_architecture WHERE job_function IS NOT NULL) target_function 
    ON target_job.job_function = target_function.job_function
JOIN core_skills_taxonomy common_skills ON source_skills.Skill_ID = common_skills.Skill_ID
WHERE source_job.job_function != target_job.job_function
    AND js.enhanced_similarity_score >= ?
    AND js.enhanced_similarity_score IS NOT NULL
    AND source_job.job_title IS NOT NULL
    AND target_job.job_title IS NOT NULL
GROUP BY source_function.job_function, target_function.job_function
HAVING shared_skills >= ?
ORDER BY shared_skills DESC, avg_similarity DESC;

-- query_name: get_tree_map_data
-- Generate data for D3.js treemap showing job distribution by function and level
-- MIGRATED: jobs → core_job_architecture, job_skills → core_job_skill_requirements, job_similarities → analytics_job_similarities
SELECT 
    j.job_function as family,
    COALESCE(j.management_level, 'Unknown') as level,
    COUNT(*) as job_count,
    AVG(skill_counts.skill_count) as avg_skills_per_job,
    COUNT(DISTINCT js.job_to) as total_similarities
FROM core_job_architecture j
LEFT JOIN (
    SELECT JobProfileID, COUNT(*) as skill_count
    FROM core_job_skill_requirements
    GROUP BY JobProfileID
) skill_counts ON j.JobProfileID = skill_counts.JobProfileID
LEFT JOIN analytics_job_similarities js 
    ON j.JobProfileID = js.job_from 
    AND js.enhanced_similarity_score >= 0.7
    AND js.enhanced_similarity_score IS NOT NULL
WHERE j.job_title IS NOT NULL
  AND j.job_function IS NOT NULL
GROUP BY j.job_function, j.management_level
ORDER BY j.job_function, j.management_level;

-- query_name: get_career_pathway_tree
-- Generate tree structure for career pathway visualization using analytics_job_similarities
-- MIGRATED: Completely rebuilt for V2 schema using enhanced similarity scoring
WITH RECURSIVE career_tree AS (
    -- Start with the specified job
    SELECT 
        j.JobProfileID as id,
        j.job_title,
        j.job_function as job_family,
        j.management_level as job_level,
        CAST(j.JobProfileID AS TEXT) as path,
        0 as depth,
        j.JobProfileID as root_id
    FROM core_job_architecture j
    WHERE j.JobProfileID = ?
      AND j.job_title IS NOT NULL
    
    UNION ALL
    
    -- Add similar jobs as potential career moves using analytics_job_similarities
    SELECT 
        similar_job.JobProfileID as id,
        similar_job.job_title,
        similar_job.job_function as job_family,
        similar_job.management_level as job_level,
        ct.path || ' -> ' || CAST(similar_job.JobProfileID AS TEXT) as path,
        ct.depth + 1,
        ct.root_id
    FROM career_tree ct
    JOIN analytics_job_similarities js ON ct.id = js.job_from
    JOIN core_job_architecture similar_job ON js.job_to = similar_job.JobProfileID
    WHERE ct.depth < ?  -- Limit recursion depth
        AND js.enhanced_similarity_score >= ?
        AND js.enhanced_similarity_score IS NOT NULL
        AND similar_job.job_title IS NOT NULL
        AND similar_job.JobProfileID NOT IN (
            -- Prevent cycles: check if job already appears in the path
            SELECT DISTINCT 
                TRIM(value) as job_id
            FROM (
                WITH RECURSIVE path_split(job_id, remaining_path) AS (
                    SELECT 
                        CASE 
                            WHEN INSTR(ct.path, ' -> ') > 0 
                            THEN SUBSTR(ct.path, 1, INSTR(ct.path, ' -> ') - 1)
                            ELSE ct.path
                        END as job_id,
                        CASE 
                            WHEN INSTR(ct.path, ' -> ') > 0 
                            THEN SUBSTR(ct.path, INSTR(ct.path, ' -> ') + 4)
                            ELSE ''
                        END as remaining_path
                    
                    UNION ALL
                    
                    SELECT 
                        CASE 
                            WHEN INSTR(remaining_path, ' -> ') > 0 
                            THEN SUBSTR(remaining_path, 1, INSTR(remaining_path, ' -> ') - 1)
                            ELSE remaining_path
                        END as job_id,
                        CASE 
                            WHEN INSTR(remaining_path, ' -> ') > 0 
                            THEN SUBSTR(remaining_path, INSTR(remaining_path, ' -> ') + 4)
                            ELSE ''
                        END as remaining_path
                    FROM path_split
                    WHERE remaining_path != ''
                )
                SELECT job_id as value FROM path_split WHERE job_id != ''
            )
            WHERE TRIM(value) = similar_job.JobProfileID
        )
)
SELECT 
    id,
    job_title,
    job_family,
    job_level,
    depth,
    path,
    CASE 
        WHEN depth = 0 THEN 'root'
        WHEN depth = 1 THEN 'direct'
        ELSE 'extended'
    END as relationship_type
FROM career_tree
ORDER BY depth, job_family, job_title;

-- query_name: get_recursive_job_tree
-- Generate recursive hierarchical tree data starting from selected jobs with configurable depth and similarity
-- Supports organizational filtering using core_workforce_current
-- MIGRATED: Complete V2 schema migration with enhanced similarity scoring
WITH RECURSIVE job_tree AS (
    -- Level 0: Root selected jobs
    SELECT 
        'job' as node_type,
        j.JobProfileID as id,
        j.job_title as name,
        NULL as parent_id,
        0 as level,
        j.job_function as category,
        0.0 as similarity_score,
        CAST(j.JobProfileID AS TEXT) as path,
        j.JobProfileID as unique_id  -- Same as ID for root nodes
    FROM core_job_architecture j
    WHERE j.JobProfileID IN ({job_placeholders})
      AND j.job_title IS NOT NULL
    
    UNION ALL
    
    -- Recursive: Similar jobs at each level with organizational filtering
    SELECT 
        'similar_job' as node_type,
        js.job_to as id,
        similar_job.job_title as name,
        jt.unique_id as parent_id,  -- Use unique parent ID
        jt.level + 1 as level,
        similar_job.job_function as category,
        js.enhanced_similarity_score as similarity_score,
        jt.path || ' -> ' || js.job_to as path,
        jt.unique_id || '_' || js.job_to as unique_id  -- Create unique ID for each occurrence
    FROM job_tree jt
    JOIN (
        SELECT 
            job_from,
            job_to,
            enhanced_similarity_score,
            ROW_NUMBER() OVER (PARTITION BY job_from ORDER BY enhanced_similarity_score DESC) as rank
        FROM analytics_job_similarities
        WHERE enhanced_similarity_score >= ? 
            AND enhanced_similarity_score IS NOT NULL
            AND enhanced_similarity_score < 0.99  -- More permissive than 1.0
    ) js ON jt.id = js.job_from AND js.rank <= ?  -- Configurable via max_results parameter
    JOIN core_job_architecture similar_job ON js.job_to = similar_job.JobProfileID
    LEFT JOIN core_workforce_current cw ON similar_job.JobProfileID = cw.JobProfileID
    WHERE jt.level < ?
        AND js.job_to != jt.id  -- Prevent immediate self-reference
        AND similar_job.job_title IS NOT NULL
        AND (
            jt.path NOT LIKE '%' || js.job_to || ' -> %'  -- job_to not in middle of path
            AND jt.path NOT LIKE js.job_to || ' -> %'     -- job_to not at start of path  
            AND jt.path != js.job_to                      -- job_to not the entire path
        )  -- More precise cycle detection: only prevent if job appears in current ancestor path
        -- Organizational filters (optional - empty string means no filter)
        AND (? = '' OR cw.ORG_UNIT_NAME_2 = ?)  -- Division
        AND (? = '' OR cw.ORG_UNIT_NAME_3 = ?)  -- Business Unit
        AND (? = '' OR cw.Location = ?)         -- Location
        AND (? = '' OR cw.Rg = ?)               -- Region
)
SELECT 
    node_type,
    unique_id as id,  -- Use unique ID instead of job ID
    name,
    parent_id,
    level,
    similarity_score,
    category,
    0 as children_count  -- Simplified - will be calculated in application if needed
FROM job_tree
ORDER BY level, similarity_score DESC, name;