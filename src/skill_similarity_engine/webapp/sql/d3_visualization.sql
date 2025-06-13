-- =================================================================
-- D3.JS VISUALIZATION QUERIES
-- Queries for generating data structures for D3.js visualizations
-- =================================================================

-- query_name: get_tree_data_for_family
-- Generate hierarchical tree data for D3.js collapsible tree visualization
SELECT 
    'family' as node_type,
    j.JobFamily as id,
    j.JobFamily as name,
    NULL as parent_id,
    COUNT(*) as children_count,
    0 as similarity_score,
    'Job Family' as category
FROM jobs j
WHERE j.JobFamily = ?
GROUP BY j.JobFamily

UNION ALL

SELECT 
    'job' as node_type,
    j.JobProfileID as id,
    j.JobProfile as name,
    j.JobFamily as parent_id,
    COUNT(DISTINCT js.job_to) as children_count,
    0 as similarity_score,
    COALESCE(j.JobFamilyGroup, 'Unknown') as category
FROM jobs j
LEFT JOIN job_similarities js ON j.JobProfileID = js.job_from AND js.similarity_score >= 0.7
WHERE j.JobFamily = ?
GROUP BY j.JobProfileID, j.JobProfile, j.JobFamily, j.JobFamilyGroup

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
    WHERE source_job.JobFamily = ?
        AND js.similarity_score >= 0.7
) ranked_similarities
JOIN jobs similar_job ON ranked_similarities.job_to = similar_job.JobProfileID
WHERE ranked_similarities.rank <= 5  -- Limit to top 5 similar jobs per job
ORDER BY node_type, similarity_score DESC, name;

-- query_name: get_network_data_for_similarities
-- Generate network data for D3.js force-directed graph of job similarities
SELECT 
    'nodes' as data_type,
    j.id as id,
    j.job_title as name,
    j.job_family as group,
    j.job_level as level,
    COUNT(DISTINCT js.similar_job_id) as degree
FROM jobs j
LEFT JOIN job_similarities js ON j.id = js.job_id AND js.similarity_score >= ?
WHERE j.job_family = ?
GROUP BY j.id, j.job_title, j.job_family, j.job_level

UNION ALL

SELECT 
    'links' as data_type,
    js.job_id as source,
    js.similar_job_id as target,
    js.similarity_score as value,
    js.similarity_category as type,
    NULL as degree
FROM job_similarities js
JOIN jobs j1 ON js.job_id = j1.id
JOIN jobs j2 ON js.similar_job_id = j2.id
WHERE js.similarity_score >= ?
    AND (j1.job_family = ? OR j2.job_family = ?)
ORDER BY data_type, value DESC;

-- query_name: get_sunburst_data
-- Generate hierarchical data for D3.js sunburst visualization of skills by category
SELECT 
    'root' as level,
    'Skills' as id,
    'Skills' as name,
    NULL as parent,
    COUNT(DISTINCT s.id) as value,
    'skills' as category
FROM skills s
JOIN job_skills js ON s.id = js.skills_skill_id
JOIN jobs j ON js.job_id = j.id
WHERE j.job_family = ?

UNION ALL

SELECT 
    'category' as level,
    s.skill_category as id,
    s.skill_category as name,
    'Skills' as parent,
    COUNT(DISTINCT s.id) as value,
    'category' as category
FROM skills s
JOIN job_skills js ON s.id = js.skills_skill_id
JOIN jobs j ON js.job_id = j.id
WHERE j.job_family = ?
GROUP BY s.skill_category

UNION ALL

SELECT 
    'subcategory' as level,
    s.skill_category || ' - ' || s.skill_subcategory as id,
    s.skill_subcategory as name,
    s.skill_category as parent,
    COUNT(DISTINCT s.id) as value,
    'subcategory' as category
FROM skills s
JOIN job_skills js ON s.id = js.skills_skill_id
JOIN jobs j ON js.job_id = j.id
WHERE j.job_family = ?
    AND s.skill_subcategory IS NOT NULL
GROUP BY s.skill_category, s.skill_subcategory

UNION ALL

SELECT 
    'skill' as level,
    CAST(s.id AS TEXT) as id,
    s.skill_name as name,
    COALESCE(s.skill_category || ' - ' || s.skill_subcategory, s.skill_category) as parent,
    COUNT(DISTINCT js.job_id) as value,
    'skill' as category
FROM skills s
JOIN job_skills js ON s.id = js.skills_skill_id
JOIN jobs j ON js.job_id = j.id
WHERE j.job_family = ?
GROUP BY s.id, s.skill_name, s.skill_category, s.skill_subcategory
ORDER BY level, value DESC;

-- query_name: get_chord_diagram_data
-- Generate data for D3.js chord diagram showing skill relationships between job families
SELECT 
    source_family.job_family as source,
    target_family.job_family as target,
    COUNT(DISTINCT common_skills.skills_skill_id) as shared_skills,
    AVG(js.similarity_score) as avg_similarity
FROM jobs source_job
JOIN job_skills source_skills ON source_job.id = source_skills.job_id
JOIN job_skills target_skills ON source_skills.skills_skill_id = target_skills.skills_skill_id
JOIN jobs target_job ON target_skills.job_id = target_job.id
JOIN job_similarities js ON source_job.id = js.job_id AND target_job.id = js.similar_job_id
JOIN (SELECT DISTINCT job_family FROM jobs) source_family ON source_job.job_family = source_family.job_family
JOIN (SELECT DISTINCT job_family FROM jobs) target_family ON target_job.job_family = target_family.job_family
JOIN skills common_skills ON source_skills.skills_skill_id = common_skills.id
WHERE source_job.job_family != target_job.job_family
    AND js.similarity_score >= ?
GROUP BY source_family.job_family, target_family.job_family
HAVING shared_skills >= ?
ORDER BY shared_skills DESC, avg_similarity DESC;

-- query_name: get_tree_map_data
-- Generate data for D3.js treemap showing job distribution by family and level
SELECT 
    j.job_family as family,
    COALESCE(j.job_level, 'Unknown') as level,
    COUNT(*) as job_count,
    AVG(skill_counts.skill_count) as avg_skills_per_job,
    COUNT(DISTINCT js.similar_job_id) as total_similarities
FROM jobs j
LEFT JOIN (
    SELECT job_id, COUNT(*) as skill_count
    FROM job_skills
    GROUP BY job_id
) skill_counts ON j.id = skill_counts.job_id
LEFT JOIN job_similarities js ON j.id = js.job_id AND js.similarity_score >= 0.7
GROUP BY j.job_family, j.job_level
ORDER BY j.job_family, j.job_level;

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
        j.JobFamily as category,
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
        similar_job.JobFamily as category,
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
    ) js ON jt.id = js.job_from AND js.rank <= 3  -- Reduced for performance
    JOIN jobs similar_job ON js.job_to = similar_job.JobProfileID
    LEFT JOIN positions p ON similar_job.JobProfileID = p.JobProfileID
    WHERE jt.level < ?
        AND jt.path NOT LIKE '%' || js.job_to || '%'
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