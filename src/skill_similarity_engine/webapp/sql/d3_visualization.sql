-- =================================================================
-- D3.JS VISUALIZATION QUERIES
-- Queries for generating data structures for D3.js visualizations
-- =================================================================

-- query_name: get_tree_data_for_family
-- Generate hierarchical tree data for D3.js collapsible tree visualization
SELECT 
    'function' as node_type,
    j.JobFunction as id,
    j.JobFunction as name,
    NULL as parent_id,
    COUNT(*) as children_count,
    0 as similarity_score,
    'Job Function' as category
FROM jobs j
WHERE j.JobFunction = ?
GROUP BY j.JobFunction

UNION ALL

SELECT 
    'job' as node_type,
    j.JobProfileID as id,
    j.JobProfile as name,
    j.JobFunction as parent_id,
    COUNT(DISTINCT js.job_to) as children_count,
    0 as similarity_score,
    COALESCE(j.JobSubFunction, 'Unknown') as category
FROM jobs j
LEFT JOIN job_similarities js ON j.JobProfileID = js.job_from AND js.similarity_score >= 0.7
WHERE j.JobFunction = ?
GROUP BY j.JobProfileID, j.JobProfile, j.JobFunction, j.JobSubFunction

UNION ALL

SELECT 
    'similar_job' as node_type,
    'sim_' || ranked_similarities.job_from || '_' || ranked_similarities.job_to as id,
    similar_job.JobProfile as name,
    ranked_similarities.job_from as parent_id,
    0 as children_count,
    ranked_similarities.similarity_score,
    CASE 
        WHEN ranked_similarities.similarity_score >= 0.8 THEN 'High'
        WHEN ranked_similarities.similarity_score >= 0.7 THEN 'Medium'
        ELSE 'Low'
    END as category
FROM (
    SELECT 
        js.job_from,
        js.job_to,
        js.similarity_score,
        ROW_NUMBER() OVER (PARTITION BY js.job_from ORDER BY js.similarity_score DESC) as rank
    FROM job_similarities js
    JOIN jobs source_job ON js.job_from = source_job.JobProfileID
    WHERE source_job.JobFunction = ?
        AND js.similarity_score >= 0.7
) ranked_similarities
JOIN jobs similar_job ON ranked_similarities.job_to = similar_job.JobProfileID
WHERE ranked_similarities.rank <= 5  -- Limit to top 5 similar jobs per job
ORDER BY node_type, similarity_score DESC, name;

-- query_name: get_network_data_for_similarities
-- Generate network data for D3.js force-directed graph of job similarities
SELECT 
    'nodes' as data_type,
    j.JobProfileID as id,
    j.JobProfile as name,
    j.JobFunction as group,
    j.ManagementLevel as level,
    COUNT(DISTINCT js.job_to) as degree
FROM jobs j
LEFT JOIN job_similarities js ON j.JobProfileID = js.job_from AND js.similarity_score >= ?
WHERE j.JobFunction = ?
GROUP BY j.JobProfileID, j.JobProfile, j.JobFunction, j.ManagementLevel

UNION ALL

SELECT 
    'links' as data_type,
    js.job_from as source,
    js.job_to as target,
    js.similarity_score as value,
    CASE 
        WHEN js.similarity_score >= 0.8 THEN 'high'
        WHEN js.similarity_score >= 0.6 THEN 'medium'
        ELSE 'low'
    END as type,
    NULL as degree
FROM job_similarities js
JOIN jobs j1 ON js.job_from = j1.JobProfileID
JOIN jobs j2 ON js.job_to = j2.JobProfileID
WHERE js.similarity_score >= ?
    AND (j1.JobFunction = ? OR j2.JobFunction = ?)
ORDER BY data_type, value DESC;

-- query_name: get_sunburst_data
-- Generate hierarchical data for D3.js sunburst visualization of skills by category
SELECT 
    'root' as level,
    'Skills' as id,
    'Skills' as name,
    NULL as parent,
    COUNT(DISTINCT s.Skill_ID) as value,
    'skills' as category
FROM skills s
JOIN job_skills js ON s.Skill_ID = js.Skill_ID
JOIN jobs j ON js.JobProfileID = j.JobProfileID
WHERE j.JobFunction = ?

UNION ALL

SELECT 
    'category' as level,
    s.Category as id,
    s.Category as name,
    'Skills' as parent,
    COUNT(DISTINCT s.Skill_ID) as value,
    'category' as category
FROM skills s
JOIN job_skills js ON s.Skill_ID = js.Skill_ID
JOIN jobs j ON js.JobProfileID = j.JobProfileID
WHERE j.JobFunction = ?
GROUP BY s.Category

UNION ALL

SELECT 
    'subcategory' as level,
    s.Category || ' - ' || s.Subcategory as id,
    s.Subcategory as name,
    s.Category as parent,
    COUNT(DISTINCT s.Skill_ID) as value,
    'subcategory' as category
FROM skills s
JOIN job_skills js ON s.Skill_ID = js.Skill_ID
JOIN jobs j ON js.JobProfileID = j.JobProfileID
WHERE j.JobFunction = ?
    AND s.Subcategory IS NOT NULL
GROUP BY s.Category, s.Subcategory

UNION ALL

SELECT 
    'skill' as level,
    s.Skill_ID as id,
    s.Skill_Name as name,
    COALESCE(s.Category || ' - ' || s.Subcategory, s.Category) as parent,
    COUNT(DISTINCT js.JobProfileID) as value,
    'skill' as category
FROM skills s
JOIN job_skills js ON s.Skill_ID = js.Skill_ID
JOIN jobs j ON js.JobProfileID = j.JobProfileID
WHERE j.JobFunction = ?
GROUP BY s.Skill_ID, s.Skill_Name, s.Category, s.Subcategory
ORDER BY level, value DESC;

-- query_name: get_chord_diagram_data
-- Generate data for D3.js chord diagram showing skill relationships between job functions
SELECT 
    source_function.JobFunction as source,
    target_function.JobFunction as target,
    COUNT(DISTINCT common_skills.Skill_ID) as shared_skills,
    AVG(js.similarity_score) as avg_similarity
FROM jobs source_job
JOIN job_skills source_skills ON source_job.JobProfileID = source_skills.JobProfileID
JOIN job_skills target_skills ON source_skills.Skill_ID = target_skills.Skill_ID
JOIN jobs target_job ON target_skills.JobProfileID = target_job.JobProfileID
JOIN job_similarities js ON source_job.JobProfileID = js.job_from AND target_job.JobProfileID = js.job_to
JOIN (SELECT DISTINCT JobFunction FROM jobs) source_function ON source_job.JobFunction = source_function.JobFunction
JOIN (SELECT DISTINCT JobFunction FROM jobs) target_function ON target_job.JobFunction = target_function.JobFunction
JOIN skills common_skills ON source_skills.Skill_ID = common_skills.Skill_ID
WHERE source_job.JobFunction != target_job.JobFunction
    AND js.similarity_score >= ?
GROUP BY source_function.JobFunction, target_function.JobFunction
HAVING shared_skills >= ?
ORDER BY shared_skills DESC, avg_similarity DESC;

-- query_name: get_tree_map_data
-- Generate data for D3.js treemap showing job distribution by function and level
SELECT 
    j.JobFunction as family,
    COALESCE(j.ManagementLevel, 'Unknown') as level,
    COUNT(*) as job_count,
    AVG(skill_counts.skill_count) as avg_skills_per_job,
    COUNT(DISTINCT js.job_to) as total_similarities
FROM jobs j
LEFT JOIN (
    SELECT JobProfileID, COUNT(*) as skill_count
    FROM job_skills
    GROUP BY JobProfileID
) skill_counts ON j.JobProfileID = skill_counts.JobProfileID
LEFT JOIN job_similarities js ON j.JobProfileID = js.job_from AND js.similarity_score >= 0.7
GROUP BY j.JobFunction, j.ManagementLevel
ORDER BY j.JobFunction, j.ManagementLevel;

-- query_name: get_career_pathway_tree
-- Generate tree structure for career pathway visualization
WITH RECURSIVE career_tree AS (
    -- Start with the specified job
    SELECT 
        j.id,
        j.job_title,
        j.job_family,
        j.job_level,
        CAST(j.id AS TEXT) as path,
        0 as depth,
        j.id as root_id
    FROM jobs j
    WHERE j.id = ?
    
    UNION ALL
    
    -- Add similar jobs as potential career moves
    SELECT 
        similar_job.id,
        similar_job.job_title,
        similar_job.job_family,
        similar_job.job_level,
        ct.path || ' -> ' || CAST(similar_job.id AS TEXT) as path,
        ct.depth + 1,
        ct.root_id
    FROM career_tree ct
    JOIN job_similarities js ON ct.id = js.job_id
    JOIN jobs similar_job ON js.similar_job_id = similar_job.id
    WHERE ct.depth < ?  -- Limit recursion depth
        AND js.similarity_score >= ?
        AND similar_job.id NOT IN (
            SELECT CAST(
                SUBSTR(ct.path, 
                       INSTR(ct.path || ' -> ', CAST(similar_job.id AS TEXT) || ' -> '), 
                       LENGTH(CAST(similar_job.id AS TEXT))
                ) AS INTEGER
            )
        ) -- Prevent cycles
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
-- Supports organizational filtering by Division, Business Unit, Location, etc.
WITH RECURSIVE job_tree AS (
    -- Level 0: Root selected jobs
    SELECT 
        'job' as node_type,
        j.JobProfileID as id,
        j.JobProfile as name,
        NULL as parent_id,
        0 as level,
        j.JobFunction as category,
        0.0 as similarity_score,
        CAST(j.JobProfileID AS TEXT) as path,
        j.JobProfileID as unique_id  -- Same as ID for root nodes
    FROM jobs j
    WHERE j.JobProfileID IN ({job_placeholders})
    
    UNION ALL
    
    -- Recursive: Similar jobs at each level with organizational filtering
    SELECT 
        'similar_job' as node_type,
        js.job_to as id,
        similar_job.JobProfile as name,
        jt.unique_id as parent_id,  -- Use unique parent ID
        jt.level + 1 as level,
        similar_job.JobFunction as category,
        js.similarity_score,
        jt.path || ' -> ' || js.job_to as path,
        jt.unique_id || '_' || js.job_to as unique_id  -- Create unique ID for each occurrence
    FROM job_tree jt
    JOIN (
        SELECT 
            job_from,
            job_to,
            similarity_score,
            ROW_NUMBER() OVER (PARTITION BY job_from ORDER BY similarity_score DESC) as rank
        FROM job_similarities
        WHERE similarity_score >= ? 
            AND similarity_score < 0.99  -- More permissive than 1.0
    ) js ON jt.id = js.job_from AND js.rank <= ?  -- Now configurable via max_results parameter
    JOIN jobs similar_job ON js.job_to = similar_job.JobProfileID
    LEFT JOIN positions p ON similar_job.JobProfileID = p.JobProfileID
    WHERE jt.level < ?
        AND js.job_to != jt.id  -- Prevent immediate self-reference
        AND (
            jt.path NOT LIKE '%' || js.job_to || ' -> %'  -- job_to not in middle of path
            AND jt.path NOT LIKE js.job_to || ' -> %'     -- job_to not at start of path  
            AND jt.path != js.job_to                      -- job_to not the entire path
        )  -- More precise cycle detection: only prevent if job appears in current ancestor path
        -- Organizational filters (optional - empty string means no filter)
        AND (? = '' OR p.Division = ?)
        AND (? = '' OR p.Business_Unit = ?)
        AND (? = '' OR p.Location = ?)
        AND (? = '' OR p.Rg = ?)
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