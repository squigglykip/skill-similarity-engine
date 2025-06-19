-- =================================================================
-- CAREER PATHWAY QUERIES (REBUILT FOR MAXIMUM PERFORMANCE)
-- Simple, fast queries leveraging the pre-computed career_pathways table
-- Uses direct lookups instead of complex multi-level JOINs
-- =================================================================

-- query_name: get_career_tree_fast
-- Generate D3.js tree data using optimized recursive approach for pre-computed career pathways
-- FIXED: Organizational filters are now properly restrictive, not additive
WITH RECURSIVE tree_builder AS (
    -- Level 0: Root nodes (selected starting jobs) - ALWAYS included regardless of org filters
    SELECT 
        'root' as node_type,
        j.JobProfileID as id,
        j.JobProfile as name,
        NULL as parent_id,
        0 as level,
        j.JobFunction as category,
        1.0 as similarity_score,
        'starting_role' as career_move_type,
        0.0 as difficulty_score,
        0 as shared_skills_count,
        0 as children_count,
        j.JobProfileID as root_job_id
    FROM jobs j
    WHERE j.JobProfileID IN ({job_placeholders})
    
    UNION ALL
    
    -- Recursive expansion: Get direct pathways from each node
    -- APPLY ORGANIZATIONAL FILTERS HERE to restrict which jobs can appear in the tree
    SELECT 
        'similar_job' as node_type,
        cp.target_job_id as id,
        j.JobProfile as name,
        cp.source_job_id as parent_id,
        tb.level + 1 as level,
        j.JobFunction as category,
        cp.similarity_score,
        cp.career_move_type,
        cp.difficulty_score,
        cp.shared_skills_count,
        0 as children_count,  -- Will be calculated post-query
        tb.root_job_id
    FROM tree_builder tb
    JOIN career_pathways cp ON tb.id = cp.source_job_id
    JOIN jobs j ON cp.target_job_id = j.JobProfileID
    WHERE cp.similarity_score >= ?  -- similarity_threshold (param 2)
      AND tb.level < ?  -- max_depth (param 3) 
      AND cp.similarity_rank <= ?   -- max_results (param 4)
      AND cp.target_job_id != tb.root_job_id  -- Don't go back to root
      AND cp.target_job_id != tb.id  -- Don't self-reference
      -- 🎯 ORGANIZATIONAL FILTERS: Applied at Level 1+ to restrict tree expansion
      AND (
          -- Level 1: Strict filtering - these jobs MUST match org filters if specified
          -- FIXED: Use single query to ensure all filters apply to the SAME position record
          (tb.level = 0 AND (
              cp.target_job_id IN (
                  SELECT JobProfileID FROM positions 
                  WHERE (? = '' OR Division = ?)
                    AND (? = '' OR "Business_Unit" = ?)
                    AND (? = '' OR Location = ?)
                    AND (? = '' OR Rg = ?)
              )
          ))
          OR
          -- Level 2+: Allow any job (they're reachable through filtered Level 1 jobs)
          (tb.level > 0)
      )
)
SELECT DISTINCT
    node_type,
    id,
    name,
    parent_id,
    level,
    category,
    similarity_score,
    career_move_type,
    difficulty_score,
    shared_skills_count,
    children_count
FROM tree_builder
ORDER BY level, similarity_score DESC, name;

-- query_name: get_career_tree_fast_simple
-- Non-recursive fallback version for better performance with large datasets
-- Build tree level by level using simple UNIONs (same interface as recursive version)
SELECT 
    node_type,
    id,
    name,
    parent_id,
    level,
    category,
    similarity_score,
    career_move_type,
    difficulty_score,
    shared_skills_count,
    children_count
FROM (
    -- Level 0: Root nodes
    SELECT 
        'root' as node_type,
        j.JobProfileID as id,
        j.JobProfile as name,
        NULL as parent_id,
        0 as level,
        j.JobFunction as category,
        1.0 as similarity_score,
        'starting_role' as career_move_type,
        0.0 as difficulty_score,
        0 as shared_skills_count,
        0 as children_count
    FROM jobs j
    WHERE j.JobProfileID IN ({job_placeholders})
    
    UNION ALL
    
    -- Level 1: Direct pathways from roots
    SELECT 
        'similar_job' as node_type,
        cp.target_job_id as id,
        j.JobProfile as name,
        cp.source_job_id as parent_id,
        1 as level,
        j.JobFunction as category,
        cp.similarity_score,
        cp.career_move_type,
        cp.difficulty_score,
        cp.shared_skills_count,
        0 as children_count
    FROM career_pathways cp
    JOIN jobs j ON cp.target_job_id = j.JobProfileID
    WHERE cp.source_job_id IN ({job_placeholders})
      AND cp.similarity_score >= ?
      AND cp.similarity_rank <= ?
      AND ? >= 1  -- max_depth allows level 1
    
    UNION ALL
    
    -- Level 2: Pathways from level 1 nodes
    SELECT 
        'similar_job' as node_type,
        cp2.target_job_id as id,
        j.JobProfile as name,
        cp2.source_job_id as parent_id,
        2 as level,
        j.JobFunction as category,
        cp2.similarity_score,
        cp2.career_move_type,
        cp2.difficulty_score,
        cp2.shared_skills_count,
        0 as children_count
    FROM career_pathways cp1
    JOIN career_pathways cp2 ON cp1.target_job_id = cp2.source_job_id
    JOIN jobs j ON cp2.target_job_id = j.JobProfileID
    WHERE cp1.source_job_id IN ({job_placeholders})
      AND cp1.similarity_score >= ?
      AND cp1.similarity_rank <= ?
      AND cp2.similarity_score >= ?
      AND cp2.similarity_rank <= ?
      AND cp2.target_job_id NOT IN ({job_placeholders})
      AND ? >= 2  -- max_depth allows level 2
      
    UNION ALL
    
    -- Level 3: Pathways from level 2 nodes
    SELECT 
        'similar_job' as node_type,
        cp3.target_job_id as id,
        j.JobProfile as name,
        cp3.source_job_id as parent_id,
        3 as level,
        j.JobFunction as category,
        cp3.similarity_score,
        cp3.career_move_type,
        cp3.difficulty_score,
        cp3.shared_skills_count,
        0 as children_count
    FROM career_pathways cp1
    JOIN career_pathways cp2 ON cp1.target_job_id = cp2.source_job_id
    JOIN career_pathways cp3 ON cp2.target_job_id = cp3.source_job_id
    JOIN jobs j ON cp3.target_job_id = j.JobProfileID
    WHERE cp1.source_job_id IN ({job_placeholders})
      AND cp1.similarity_score >= ?
      AND cp1.similarity_rank <= ?
      AND cp2.similarity_score >= ?
      AND cp2.similarity_rank <= ?
      AND cp3.similarity_score >= ?
      AND cp3.similarity_rank <= ?
      AND cp3.target_job_id NOT IN ({job_placeholders})
      AND ? >= 3  -- max_depth allows level 3
) 
SELECT DISTINCT
    node_type,
    id,
    name,
    parent_id,
    level,
    category,
    similarity_score,
    career_move_type,
    difficulty_score,
    shared_skills_count,
    children_count
FROM base_tree
WHERE (
    -- Always include root nodes (starting jobs)
    (base_tree.level = 0)
) OR (
    -- For career pathway results (levels 1+), apply organizational filters as RESTRICTIONS
    (base_tree.level > 0) 
    AND (? = '' OR base_tree.id IN (SELECT JobProfileID FROM positions WHERE Division = ?))
    AND (? = '' OR base_tree.id IN (SELECT JobProfileID FROM positions WHERE "Business_Unit" = ?))
    AND (? = '' OR base_tree.id IN (SELECT JobProfileID FROM positions WHERE Location = ?))
    AND (? = '' OR base_tree.id IN (SELECT JobProfileID FROM positions WHERE Rg = ?))
)
ORDER BY level, similarity_score DESC, name;

-- query_name: get_direct_career_options
-- Simple query for direct career pathways from a single job
SELECT 
    cp.target_job_id,
    j.JobProfile as target_job_name,
    j.JobFunction as target_function,
    cp.similarity_score,
    cp.similarity_rank,
    cp.career_move_type,
    cp.difficulty_score,
    cp.shared_skills_count,
    -- Add position context
    COUNT(p."Position Number") as position_count,
    GROUP_CONCAT(DISTINCT p.Division) as divisions,
    GROUP_CONCAT(DISTINCT p."Business_Unit") as business_units
FROM career_pathways cp
JOIN jobs j ON cp.target_job_id = j.JobProfileID
LEFT JOIN positions p ON j.JobProfileID = p.JobProfileID
WHERE cp.source_job_id = ?
  AND cp.similarity_score >= ?
  AND cp.similarity_rank <= ?
GROUP BY cp.target_job_id, j.JobProfile, j.JobFunction, 
         cp.similarity_score, cp.similarity_rank, cp.career_move_type,
         cp.difficulty_score, cp.shared_skills_count
ORDER BY cp.similarity_rank;

-- query_name: get_career_pathways_by_move_type
-- Get career pathways filtered by move type (lateral, progression)
SELECT 
    cp.source_job_id,
    j1.JobProfile as source_job_name,
    j1.JobFunction as source_function,
    cp.target_job_id,
    j2.JobProfile as target_job_name,
    j2.JobFunction as target_function,
    cp.similarity_score,
    cp.career_move_type,
    cp.difficulty_score,
    cp.shared_skills_count,
    cp.similarity_rank
FROM career_pathways cp
JOIN jobs j1 ON cp.source_job_id = j1.JobProfileID
JOIN jobs j2 ON cp.target_job_id = j2.JobProfileID
WHERE cp.career_move_type = ?
  AND cp.similarity_score >= ?
  AND cp.similarity_rank <= ?
ORDER BY cp.similarity_score DESC
LIMIT ?;

-- query_name: get_pathway_statistics
-- Get statistics about career pathways for analysis
SELECT 
    career_move_type,
    COUNT(*) as pathway_count,
    ROUND(AVG(similarity_score), 3) as avg_similarity,
    ROUND(AVG(difficulty_score), 3) as avg_difficulty,
    ROUND(AVG(shared_skills_count), 1) as avg_shared_skills,
    ROUND(MIN(similarity_score), 3) as min_similarity,
    ROUND(MAX(similarity_score), 3) as max_similarity,
    COUNT(DISTINCT source_job_id) as unique_source_jobs,
    COUNT(DISTINCT target_job_id) as unique_target_jobs
FROM career_pathways
WHERE similarity_score >= ?
  AND similarity_rank <= ?
GROUP BY career_move_type
ORDER BY avg_similarity DESC;

-- query_name: get_most_connected_jobs
-- Find jobs with the most career pathway options
SELECT 
    cp.source_job_id,
    j.JobProfile as job_name,
    j.JobFunction,
    COUNT(*) as pathway_count,
    ROUND(AVG(cp.similarity_score), 3) as avg_similarity,
    COUNT(CASE WHEN cp.career_move_type = 'lateral' THEN 1 END) as lateral_moves,
    COUNT(CASE WHEN cp.career_move_type = 'progression' THEN 1 END) as progression_moves,
    -- Add position deployment context
    COUNT(DISTINCT p."Position Number") as position_count,
    GROUP_CONCAT(DISTINCT p.Division) as present_divisions,
    GROUP_CONCAT(DISTINCT p.Location) as present_locations
FROM career_pathways cp
JOIN jobs j ON cp.source_job_id = j.JobProfileID
LEFT JOIN positions p ON j.JobProfileID = p.JobProfileID
WHERE cp.similarity_score >= ?
  AND cp.similarity_rank <= ?
GROUP BY cp.source_job_id, j.JobProfile, j.JobFunction
HAVING pathway_count >= ?  -- Minimum pathways to be considered "well-connected"
ORDER BY pathway_count DESC, avg_similarity DESC
LIMIT ?;

-- query_name: get_skills_comparison
-- Compare skills between two jobs for career pathway analysis
SELECT 
    s.Skill_Name as skill_name,
    s.Skill_ID as skill_id,
    s.Category as skill_category,
    s.Subcategory as skill_subcategory,
    CASE 
        WHEN js_source.Skill_ID IS NOT NULL AND js_target.Skill_ID IS NOT NULL THEN 'Transferable'
        WHEN js_source.Skill_ID IS NOT NULL AND js_target.Skill_ID IS NULL THEN 'Current Only'
        WHEN js_source.Skill_ID IS NULL AND js_target.Skill_ID IS NOT NULL THEN 'New Required'
        ELSE 'Unknown'
    END as skill_status,
    js_source.Skill_Weight as current_weight,
    js_target.Skill_Weight as target_weight
FROM skills s
LEFT JOIN job_skills js_source ON s.Skill_ID = js_source.Skill_ID AND js_source.JobProfileID = ?
LEFT JOIN job_skills js_target ON s.Skill_ID = js_target.Skill_ID AND js_target.JobProfileID = ?
WHERE js_source.Skill_ID IS NOT NULL OR js_target.Skill_ID IS NOT NULL
ORDER BY 
    CASE skill_status 
        WHEN 'Transferable' THEN 1 
        WHEN 'New Required' THEN 2 
        WHEN 'Current Only' THEN 3 
        ELSE 4 
    END,
    s.Category, 
    s.Skill_Name;

-- query_name: get_job_function_mobility
-- Analyze mobility patterns between job functions
SELECT 
    j1.JobFunction as source_function,
    j2.JobFunction as target_function,
    COUNT(*) as pathway_count,
    ROUND(AVG(cp.similarity_score), 3) as avg_similarity,
    ROUND(AVG(cp.difficulty_score), 3) as avg_difficulty,
    COUNT(CASE WHEN cp.career_move_type = 'lateral' THEN 1 END) as lateral_count,
    COUNT(CASE WHEN cp.career_move_type = 'progression' THEN 1 END) as progression_count
FROM career_pathways cp
JOIN jobs j1 ON cp.source_job_id = j1.JobProfileID
JOIN jobs j2 ON cp.target_job_id = j2.JobProfileID
WHERE cp.similarity_score >= ?
  AND cp.similarity_rank <= ?
GROUP BY j1.JobFunction, j2.JobFunction
HAVING pathway_count >= ?  -- Minimum pathways for statistical relevance
ORDER BY pathway_count DESC, avg_similarity DESC; 