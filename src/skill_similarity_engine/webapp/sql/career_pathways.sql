-- =================================================================
-- CAREER PATHWAY QUERIES - V2 SCHEMA MIGRATION
-- Simple migration from deprecated career_pathways table to analytics_job_similarities
-- Uses enhanced_similarity_score for improved pathway recommendations
-- =================================================================

-- query_name: get_career_tree_fast
-- Generate D3.js tree data using analytics_job_similarities (replaces deprecated career_pathways)
-- REBUILT: Uses analytics tables with enhanced similarity scoring
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
    FROM core_job_architecture j
    WHERE j.JobProfileID IN ({job_placeholders})
    
    UNION ALL
    
    -- Recursive expansion: Get direct pathways from each node using analytics_job_similarities
    -- APPLY ORGANIZATIONAL FILTERS HERE to restrict which jobs can appear in the tree
    SELECT 
        'similar_job' as node_type,
        js.job_to as id,
        ja.JobProfile as name,
        js.job_from as parent_id,
        tb.level + 1 as level,
        ja.JobFunction as category,
        js.enhanced_similarity_score as similarity_score,
        COALESCE(mp.movement_type, 'lateral') as career_move_type,
        COALESCE(mp.avg_days_between, 365.0) / 365.0 as difficulty_score,
        js.shared_defining_skills_count as shared_skills_count,
        0 as children_count,  -- Will be calculated post-query
        tb.root_job_id
    FROM tree_builder tb
    JOIN analytics_job_similarities js ON tb.id = js.job_from
    JOIN core_job_architecture ja ON js.job_to = ja.JobProfileID
    JOIN core_job_architecture source_ja ON js.job_from = source_ja.JobProfileID
    LEFT JOIN analytics_movement_patterns mp 
        ON js.job_from = mp.from_job_profile_id 
        AND js.job_to = mp.to_job_profile_id
    WHERE js.enhanced_similarity_score >= ?  -- similarity_threshold (param 2)
      AND tb.level < ?  -- max_depth (param 3) 
      AND js.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
      AND js.job_to != tb.root_job_id  -- Don't go back to root
      AND js.job_to != tb.id  -- Don't self-reference
      -- 🎯 CAREER EXPLORATION FILTERS: Simple field-based filtering
      -- Exclude same JobID if filter enabled (exclude_same_job_id=1)
      AND (? = 0 OR ja.JobID != source_ja.JobID)
      -- Exclude same JobFunction if filter enabled (exclude_same_job_function=1)  
      AND (? = 0 OR ja.JobFunction != source_ja.JobFunction)
    -- Limit pathways per node to prevent explosion - use ROW_NUMBER for exact counts
    AND js.job_to IN (
        SELECT job_to
        FROM (
            SELECT job_to, 
                   ROW_NUMBER() OVER (PARTITION BY job_from ORDER BY enhanced_similarity_score DESC) as rn
            FROM analytics_job_similarities js2 
            WHERE js2.job_from = js.job_from 
              AND js2.enhanced_similarity_score IS NOT NULL
              AND js2.enhanced_similarity_score >= ?  -- similarity_threshold
        ) ranked
        WHERE rn <= ?  -- max_results - guarantees exactly N rows per parent
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

-- query_name: get_career_tree_with_job_filters
-- Generate D3.js tree data with job filtering options (exclude same JobID/JobFunction)
-- Enhanced version with cross-functional and cross-job exploration capabilities
WITH RECURSIVE tree_builder AS (
    -- Level 0: Root nodes (selected starting jobs) - ALWAYS included regardless of filters
    SELECT 
        'root' as node_type,
        j.JobProfileID as id,
        j.JobProfile as name,
        NULL as parent_id,
        0 as level,
        j.JobFunction as category,
        j.JobID as job_id,
        1.0 as similarity_score,
        'starting_role' as career_move_type,
        0.0 as difficulty_score,
        0 as shared_skills_count,
        0 as children_count,
        j.JobProfileID as root_job_id
    FROM core_job_architecture j
    WHERE j.JobProfileID IN ({job_placeholders})
    
    UNION ALL
    
    -- Recursive expansion: Get pathways with job filtering applied
    SELECT 
        'similar_job' as node_type,
        js.job_to as id,
        ja.JobProfile as name,
        js.job_from as parent_id,
        tb.level + 1 as level,
        ja.JobFunction as category,
        ja.JobID as job_id,
        js.enhanced_similarity_score as similarity_score,
        COALESCE(mp.movement_type, 'lateral') as career_move_type,
        COALESCE(mp.avg_days_between, 365.0) / 365.0 as difficulty_score,
        js.shared_defining_skills_count as shared_skills_count,
        0 as children_count,
        tb.root_job_id
    FROM tree_builder tb
    JOIN analytics_job_similarities js ON tb.id = js.job_from
    JOIN core_job_architecture ja ON js.job_to = ja.JobProfileID
    JOIN core_job_architecture source_ja ON js.job_from = source_ja.JobProfileID
    LEFT JOIN analytics_movement_patterns mp 
        ON js.job_from = mp.from_job_profile_id 
        AND js.job_to = mp.to_job_profile_id
    WHERE js.enhanced_similarity_score >= ?  -- similarity_threshold
      AND tb.level < ?  -- max_depth
      AND js.enhanced_similarity_score IS NOT NULL
      AND js.job_to != tb.root_job_id  -- Don't go back to root
      AND js.job_to != tb.id  -- Don't self-reference
      -- NEW: Job filtering logic - exclude same JobID if filter enabled
      AND (? = 0 OR ja.JobID != source_ja.JobID)
      -- NEW: Job function filtering logic - exclude same JobFunction if filter enabled
      AND (? = 0 OR ja.JobFunction != source_ja.JobFunction)
      -- Organizational filters (optional)
      AND (
          -- Level 1: Apply org filters if specified
          (tb.level = 0 AND (
              ? = '' OR js.job_to IN (
                  SELECT JobProfileID FROM core_workforce_current 
                  WHERE (? = '' OR ORG_UNIT_NAME_2 = ?)  -- Division filter
                    AND (? = '' OR ORG_UNIT_NAME_3 = ?)  -- Business Unit filter
                    AND (? = '' OR Location = ?)         -- Location filter
                    AND (? = '' OR Rg = ?)               -- Region filter
              )
          ))
          OR
          -- Level 2+: Allow any job that passes job filters
          (tb.level > 0)
      )
    -- Limit pathways per node to prevent explosion
    AND js.job_to IN (
        SELECT job_to
        FROM (
            SELECT job_to, 
                   ROW_NUMBER() OVER (PARTITION BY job_from ORDER BY enhanced_similarity_score DESC) as rn
            FROM analytics_job_similarities js2 
            WHERE js2.job_from = js.job_from 
              AND js2.enhanced_similarity_score IS NOT NULL
              -- Apply same job filters to ranking
              AND EXISTS (
                  SELECT 1 FROM core_job_architecture ja2, core_job_architecture source_ja2
                  WHERE ja2.JobProfileID = js2.job_to 
                    AND source_ja2.JobProfileID = js2.job_from
                    AND (? = 0 OR ja2.JobID != source_ja2.JobID)
                    AND (? = 0 OR ja2.JobFunction != source_ja2.JobFunction)
              )
        ) ranked
        WHERE rn <= ?  -- max_results
    )
)
SELECT DISTINCT
    node_type,
    id,
    name,
    parent_id,
    level,
    category,
    job_id,
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
    FROM core_job_architecture j
    WHERE j.JobProfileID IN ({job_placeholders})
    
    UNION ALL
    
    -- Level 1: Direct pathways from roots using analytics_job_similarities
    SELECT 
        'similar_job' as node_type,
        js.job_to as id,
        ja.JobProfile as name,
        js.job_from as parent_id,
        1 as level,
        ja.JobFunction as category,
        js.enhanced_similarity_score as similarity_score,
        COALESCE(mp.movement_type, 'lateral') as career_move_type,
        COALESCE(mp.avg_days_between, 365.0) / 365.0 as difficulty_score,
        js.shared_defining_skills_count as shared_skills_count,
        0 as children_count
    FROM analytics_job_similarities js
    JOIN core_job_architecture ja ON js.job_to = ja.JobProfileID
    LEFT JOIN analytics_movement_patterns mp 
        ON js.job_from = mp.from_job_profile_id 
        AND js.job_to = mp.to_job_profile_id
    WHERE js.job_from IN ({job_placeholders})
      AND js.enhanced_similarity_score >= ?
      AND js.enhanced_similarity_score IS NOT NULL
      AND ? >= 1  -- max_depth allows level 1
      AND js.job_to IN (
          SELECT job_to
          FROM (
              SELECT job_to, 
                     ROW_NUMBER() OVER (PARTITION BY job_from ORDER BY enhanced_similarity_score DESC) as rn
              FROM analytics_job_similarities js2 
              WHERE js2.job_from = js.job_from 
                AND js2.enhanced_similarity_score IS NOT NULL
          ) ranked
          WHERE rn <= ?  -- max_results - guarantees exactly N rows per parent
      )
    
    UNION ALL
    
    -- Level 2: Pathways from level 1 nodes
    SELECT 
        'similar_job' as node_type,
        js2.job_to as id,
        ja.JobProfile as name,
        js2.job_from as parent_id,
        2 as level,
        ja.JobFunction as category,
        js2.enhanced_similarity_score as similarity_score,
        COALESCE(mp.movement_type, 'lateral') as career_move_type,
        COALESCE(mp.avg_days_between, 365.0) / 365.0 as difficulty_score,
        js2.shared_defining_skills_count as shared_skills_count,
        0 as children_count
    FROM analytics_job_similarities js1
    JOIN analytics_job_similarities js2 ON js1.job_to = js2.job_from
    JOIN core_job_architecture ja ON js2.job_to = ja.JobProfileID
    LEFT JOIN analytics_movement_patterns mp 
        ON js2.job_from = mp.from_job_profile_id 
        AND js2.job_to = mp.to_job_profile_id
    WHERE js1.job_from IN ({job_placeholders})
      AND js1.enhanced_similarity_score >= ?
      AND js1.enhanced_similarity_score IS NOT NULL
      AND js2.enhanced_similarity_score >= ?
      AND js2.enhanced_similarity_score IS NOT NULL
      AND js2.job_to NOT IN ({job_placeholders})  -- Don't return to starting jobs
      AND ? >= 2  -- max_depth allows level 2
      AND js1.job_to IN (
          SELECT job_to
          FROM (
              SELECT job_to, 
                     ROW_NUMBER() OVER (PARTITION BY job_from ORDER BY enhanced_similarity_score DESC) as rn
              FROM analytics_job_similarities js_sub1 
              WHERE js_sub1.job_from = js1.job_from 
                AND js_sub1.enhanced_similarity_score IS NOT NULL
          ) ranked1
          WHERE rn <= ?  -- max_results for level 1
      )
      AND js2.job_to IN (
          SELECT job_to
          FROM (
              SELECT job_to, 
                     ROW_NUMBER() OVER (PARTITION BY job_from ORDER BY enhanced_similarity_score DESC) as rn
              FROM analytics_job_similarities js_sub2 
              WHERE js_sub2.job_from = js2.job_from 
                AND js_sub2.enhanced_similarity_score IS NOT NULL
          ) ranked2
          WHERE rn <= ?  -- max_results for level 2
      )
      
    UNION ALL
    
    -- Level 3: Pathways from level 2 nodes
    SELECT 
        'similar_job' as node_type,
        js3.job_to as id,
        ja.JobProfile as name,
        js3.job_from as parent_id,
        3 as level,
        ja.JobFunction as category,
        js3.enhanced_similarity_score as similarity_score,
        COALESCE(mp.movement_type, 'lateral') as career_move_type,
        COALESCE(mp.avg_days_between, 365.0) / 365.0 as difficulty_score,
        js3.shared_defining_skills_count as shared_skills_count,
        0 as children_count
    FROM analytics_job_similarities js1
    JOIN analytics_job_similarities js2 ON js1.job_to = js2.job_from
    JOIN analytics_job_similarities js3 ON js2.job_to = js3.job_from
    JOIN core_job_architecture ja ON js3.job_to = ja.JobProfileID
    LEFT JOIN analytics_movement_patterns mp 
        ON js3.job_from = mp.from_job_profile_id 
        AND js3.job_to = mp.to_job_profile_id
    WHERE js1.job_from IN ({job_placeholders})
      AND js1.enhanced_similarity_score >= ?
      AND js1.enhanced_similarity_score IS NOT NULL
      AND js2.enhanced_similarity_score >= ?
      AND js2.enhanced_similarity_score IS NOT NULL
      AND js3.enhanced_similarity_score >= ?
      AND js3.enhanced_similarity_score IS NOT NULL
      AND js3.job_to NOT IN ({job_placeholders})  -- Don't return to starting jobs
      AND ? >= 3  -- max_depth allows level 3
      AND js1.job_to IN (
          SELECT job_to
          FROM (
              SELECT job_to, 
                     ROW_NUMBER() OVER (PARTITION BY job_from ORDER BY enhanced_similarity_score DESC) as rn
              FROM analytics_job_similarities js_sub1 
              WHERE js_sub1.job_from = js1.job_from 
                AND js_sub1.enhanced_similarity_score IS NOT NULL
          ) ranked1
          WHERE rn <= ?  -- max_results for level 1
      )
      AND js2.job_to IN (
          SELECT job_to
          FROM (
              SELECT job_to, 
                     ROW_NUMBER() OVER (PARTITION BY job_from ORDER BY enhanced_similarity_score DESC) as rn
              FROM analytics_job_similarities js_sub2 
              WHERE js_sub2.job_from = js2.job_from 
                AND js_sub2.enhanced_similarity_score IS NOT NULL
          ) ranked2
          WHERE rn <= ?  -- max_results for level 2
      )
      AND js3.job_to IN (
          SELECT job_to
          FROM (
              SELECT job_to, 
                     ROW_NUMBER() OVER (PARTITION BY job_from ORDER BY enhanced_similarity_score DESC) as rn
              FROM analytics_job_similarities js_sub3 
              WHERE js_sub3.job_from = js3.job_from 
                AND js_sub3.enhanced_similarity_score IS NOT NULL
          ) ranked3
          WHERE rn <= ?  -- max_results for level 3
      )
) base_tree
WHERE (
    -- Always include root nodes (starting jobs)
    (base_tree.level = 0)
) OR (
    -- For career pathway results (levels 1+), apply organizational filters as RESTRICTIONS
    (base_tree.level > 0) 
    AND (? = '' OR base_tree.id IN (SELECT JobProfileID FROM core_workforce_current WHERE ORG_UNIT_NAME_2 = ?))  -- Division
    AND (? = '' OR base_tree.id IN (SELECT JobProfileID FROM core_workforce_current WHERE ORG_UNIT_NAME_3 = ?))  -- Business Unit
    AND (? = '' OR base_tree.id IN (SELECT JobProfileID FROM core_workforce_current WHERE Location = ?))         -- Location
    AND (? = '' OR base_tree.id IN (SELECT JobProfileID FROM core_workforce_current WHERE Rg = ?))               -- Region
)
ORDER BY level, similarity_score DESC, name;

-- query_name: get_direct_career_options
-- Simple query for direct career pathways from a single job using analytics_job_similarities
SELECT 
    js.job_to as target_job_id,
    ja.JobProfile as target_job_name,
    ja.JobFunction as target_function,
    js.enhanced_similarity_score as similarity_score,
    js.rarity_weighted_score,
    js.shared_defining_skills_count,
    js.shared_skills_count,
    js.total_skills_from,
    js.total_skills_to,
    js.skill_overlap_percentage,
    COALESCE(mp.movement_type, 'lateral') as career_move_type,
    COALESCE(mp.avg_days_between, 365.0) as avg_transition_days,
    COALESCE(mp.movement_count, 0) as historical_movements,
    -- Add position context from workforce data
    COUNT(cw.employee_number) as position_count,
    GROUP_CONCAT(DISTINCT cw.ORG_UNIT_NAME_2) as divisions,
    GROUP_CONCAT(DISTINCT cw.ORG_UNIT_NAME_3) as business_units,
    GROUP_CONCAT(DISTINCT cw.Location) as locations
FROM analytics_job_similarities js
JOIN core_job_architecture ja ON js.job_to = ja.JobProfileID
LEFT JOIN analytics_movement_patterns mp 
    ON js.job_from = mp.from_job_profile_id 
    AND js.job_to = mp.to_job_profile_id
LEFT JOIN core_workforce_current cw ON ja.JobProfileID = cw.JobProfileID
WHERE js.job_from = ?
  AND js.enhanced_similarity_score >= ?
  AND js.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
GROUP BY js.job_to, ja.job_title, ja.job_function, 
         js.enhanced_similarity_score, js.rarity_weighted_score, js.shared_defining_skills_count,
         js.shared_skills_count, js.total_skills_from, js.total_skills_to, js.skill_overlap_percentage,
         mp.movement_type, mp.avg_days_between, mp.movement_count
ORDER BY js.enhanced_similarity_score DESC
LIMIT ?;

-- query_name: get_career_pathways_by_move_type
-- Get career pathways filtered by move type using analytics_movement_patterns
SELECT 
    js.job_from as source_job_id,
    ja1.JobProfile as source_job_name,
    ja1.JobFunction as source_function,
    js.job_to as target_job_id,
    ja2.JobProfile as target_job_name,
    ja2.JobFunction as target_function,
    js.enhanced_similarity_score as similarity_score,
    js.rarity_weighted_score,
    js.shared_defining_skills_count,
    mp.movement_type as career_move_type,
    mp.avg_days_between as avg_transition_days,
    mp.movement_count as historical_movements,
    mp.success_rate
FROM analytics_job_similarities js
JOIN core_job_architecture ja1 ON js.job_from = ja1.JobProfileID
JOIN core_job_architecture ja2 ON js.job_to = ja2.JobProfileID
INNER JOIN analytics_movement_patterns mp 
    ON js.job_from = mp.from_job_profile_id 
    AND js.job_to = mp.to_job_profile_id
WHERE mp.movement_type = ?
  AND js.enhanced_similarity_score >= ?
  AND js.enhanced_similarity_score IS NOT NULL
  AND mp.movement_count > 0  -- Must have actual historical movements
ORDER BY js.enhanced_similarity_score DESC, mp.movement_count DESC
LIMIT ?;

-- query_name: get_pathway_statistics
-- Get statistics about career pathways for analysis using analytics tables
SELECT 
    mp.movement_type as career_move_type,
    COUNT(*) as pathway_count,
    ROUND(AVG(js.enhanced_similarity_score), 3) as avg_similarity,
    ROUND(AVG(mp.avg_days_between), 1) as avg_transition_days,
    ROUND(AVG(js.shared_defining_skills_count), 1) as avg_shared_defining_skills,
    ROUND(MIN(js.enhanced_similarity_score), 3) as min_similarity,
    ROUND(MAX(js.enhanced_similarity_score), 3) as max_similarity,
    COUNT(DISTINCT js.job_from) as unique_source_jobs,
    COUNT(DISTINCT js.job_to) as unique_target_jobs,
    SUM(mp.movement_count) as total_historical_movements
FROM analytics_job_similarities js
INNER JOIN analytics_movement_patterns mp 
    ON js.job_from = mp.from_job_profile_id 
    AND js.job_to = mp.to_job_profile_id
WHERE js.enhanced_similarity_score >= ?
  AND js.enhanced_similarity_score IS NOT NULL
  AND mp.movement_count > 0
GROUP BY mp.movement_type
ORDER BY avg_similarity DESC;

-- query_name: get_most_connected_jobs
-- Find jobs with the most career pathway options using analytics_job_similarities
SELECT 
    js.job_from as source_job_id,
    ja.JobProfile as job_name,
    ja.JobFunction as job_function,
    ja.JobCategory as job_category,
    ja.ManagementLevel as management_level,
    COUNT(*) as pathway_count,
    ROUND(AVG(js.enhanced_similarity_score), 3) as avg_similarity,
    ROUND(AVG(js.rarity_weighted_score), 3) as avg_rarity_weighted_score,
    COUNT(CASE WHEN mp.movement_type = 'lateral' THEN 1 END) as lateral_moves,
    COUNT(CASE WHEN mp.movement_type = 'promotion' THEN 1 END) as promotion_moves,
    COUNT(CASE WHEN mp.movement_type = 'demotion' THEN 1 END) as demotion_moves,
    -- Add position deployment context
    COUNT(DISTINCT cw.employee_number) as position_count,
    GROUP_CONCAT(DISTINCT cw.ORG_UNIT_NAME_2) as present_divisions,
    GROUP_CONCAT(DISTINCT cw.Location) as present_locations
FROM analytics_job_similarities js
JOIN core_job_architecture ja ON js.job_from = ja.JobProfileID
LEFT JOIN analytics_movement_patterns mp 
    ON js.job_from = mp.from_job_profile_id 
    AND js.job_to = mp.to_job_profile_id
LEFT JOIN core_workforce_current cw ON ja.JobProfileID = cw.JobProfileID
WHERE js.enhanced_similarity_score >= ?
  AND js.enhanced_similarity_score IS NOT NULL
GROUP BY js.job_from, ja.job_title, ja.job_function, ja.job_category, ja.management_level
HAVING pathway_count >= ?  -- Minimum pathways to be considered "well-connected"
ORDER BY pathway_count DESC, avg_similarity DESC
LIMIT ?;

-- query_name: get_skills_comparison
-- Compare skills between two jobs for career pathway analysis using V2 schema
SELECT 
    st.skill_name,
    st.Skill_ID as skill_id,
    st.Category as skill_category,
    st.Subcategory as skill_subcategory,
    st.SkillType as skill_type,
    CASE 
        WHEN jsr_source.Skill_ID IS NOT NULL AND jsr_target.Skill_ID IS NOT NULL THEN 'Transferable'
        WHEN jsr_source.Skill_ID IS NOT NULL AND jsr_target.Skill_ID IS NULL THEN 'Current Only'
        WHEN jsr_source.Skill_ID IS NULL AND jsr_target.Skill_ID IS NOT NULL THEN 'New Required'
        ELSE 'Unknown'
    END as skill_status,
    -- Add defining skills analysis
    ds_source.defining_skill_score as current_defining_score,
    ds_target.defining_skill_score as target_defining_score,
    sr.rarity_score,
    sr.rarity_category
FROM core_skills_taxonomy st
LEFT JOIN core_job_skill_requirements jsr_source 
    ON st.Skill_ID = jsr_source.Skill_ID AND jsr_source.JobProfileID = ?
LEFT JOIN core_job_skill_requirements jsr_target 
    ON st.Skill_ID = jsr_target.Skill_ID AND jsr_target.JobProfileID = ?
LEFT JOIN analytics_job_defining_skills ds_source 
    ON st.Skill_ID = ds_source.skill_id AND ds_source.job_profile_id = ?
LEFT JOIN analytics_job_defining_skills ds_target 
    ON st.Skill_ID = ds_target.skill_id AND ds_target.job_profile_id = ?
LEFT JOIN analytics_skill_rarity sr ON st.Skill_ID = sr.skill_id
WHERE jsr_source.Skill_ID IS NOT NULL OR jsr_target.Skill_ID IS NOT NULL
ORDER BY 
    CASE skill_status 
        WHEN 'Transferable' THEN 1 
        WHEN 'New Required' THEN 2 
        WHEN 'Current Only' THEN 3 
        ELSE 4 
    END,
    COALESCE(ds_source.defining_skill_score, ds_target.defining_skill_score, 0) DESC,
    st.Category, 
    st.skill_name;

-- query_name: get_job_function_mobility
-- Analyze mobility patterns between job functions using analytics_movement_patterns
SELECT 
    ja1.job_function as source_function,
    ja2.job_function as target_function,
    COUNT(DISTINCT js.similarity_id) as pathway_count,
    ROUND(AVG(js.enhanced_similarity_score), 3) as avg_similarity,
    ROUND(AVG(mp.avg_days_between), 1) as avg_transition_days,
    COUNT(CASE WHEN mp.movement_type = 'lateral' THEN 1 END) as lateral_count,
    COUNT(CASE WHEN mp.movement_type = 'promotion' THEN 1 END) as promotion_count,
    COUNT(CASE WHEN mp.movement_type = 'demotion' THEN 1 END) as demotion_count,
    SUM(mp.movement_count) as total_historical_movements
FROM analytics_job_similarities js
JOIN core_job_architecture ja1 ON js.job_from = ja1.JobProfileID
JOIN core_job_architecture ja2 ON js.job_to = ja2.JobProfileID
INNER JOIN analytics_movement_patterns mp 
    ON js.job_from = mp.from_job_profile_id 
    AND js.job_to = mp.to_job_profile_id
WHERE js.enhanced_similarity_score >= ?
  AND js.enhanced_similarity_score IS NOT NULL
  AND mp.movement_count > 0
GROUP BY ja1.job_function, ja2.job_function
HAVING pathway_count >= ?  -- Minimum pathways for statistical relevance
ORDER BY total_historical_movements DESC, avg_similarity DESC;

-- query_name: get_career_pathways_distribution_for_api
-- Get career pathway similarities distribution for a specific job using V2 analytics
-- Enhanced version with configurable parameters for job explorer
SELECT 
    js.similarity_score,
    js.enhanced_similarity_score,
    ja.JobProfile as job_title,
    ja.JobFunction as job_function,
    js.job_to as job_id
FROM analytics_job_similarities js
JOIN core_job_architecture ja ON js.job_to = ja.JobProfileID
WHERE js.job_from = ?
  AND js.enhanced_similarity_score >= ?  -- min_similarity threshold
  AND js.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
  AND ja.JobProfile IS NOT NULL
ORDER BY js.enhanced_similarity_score DESC
LIMIT ?;

-- query_name: check_job_division_filter
-- Check if a job exists in the specified division (for organizational filter validation)
SELECT DISTINCT cwc.ORG_UNIT_NAME_2 as Division
FROM core_workforce_current cwc
WHERE cwc.JobProfileID = ?
  AND cwc.ORG_UNIT_NAME_2 IS NOT NULL;

-- query_name: get_career_tree_recursive
-- Multi-level recursive tree query that builds proper career pathway trees
-- Supports dynamic expansion and cycle prevention like V1 system
WITH RECURSIVE career_tree AS (
    -- Level 0: Root nodes (selected starting jobs)
    SELECT 
        'root' as node_type,
        ja.JobProfileID as id,
        ja.JobProfile as name,
        NULL as parent_id,
        0 as level,
        ja.JobFunction as category,
        1.0 as similarity_score,
        'starting_role' as career_move_type,
        0.0 as difficulty_score,
        0 as shared_skills_count,
        0 as children_count,
        ja.JobProfileID as root_job_id,
        ja.JobProfileID as path  -- Track path to prevent cycles
    FROM core_job_architecture ja
    WHERE ja.JobProfileID = ?  -- single job parameter
    
    UNION ALL
    
    -- Recursive levels: Expand each node with its top similar jobs
    SELECT 
        'similar_job' as node_type,
        js.job_to as id,
        ja.JobProfile as name,
        js.job_from as parent_id,
        ct.level + 1 as level,
        ja.JobFunction as category,
        js.enhanced_similarity_score as similarity_score,
        COALESCE(mp.movement_type, 'lateral') as career_move_type,
        COALESCE(mp.avg_days_between, 365.0) / 365.0 as difficulty_score,
        js.shared_defining_skills_count as shared_skills_count,
        0 as children_count,
        ct.root_job_id,
        ct.path || '→' || js.job_to as path  -- Extend path for cycle detection
    FROM career_tree ct
    JOIN analytics_job_similarities js ON ct.id = js.job_from
    JOIN core_job_architecture ja ON js.job_to = ja.JobProfileID
    LEFT JOIN analytics_movement_patterns mp ON js.job_from = mp.from_job_profile_id AND js.job_to = mp.to_job_profile_id
    WHERE ct.level < ?  -- max_depth limit
      AND js.enhanced_similarity_score >= ?  -- similarity_threshold
      AND js.enhanced_similarity_score IS NOT NULL
      -- Cycle prevention: don't return to any job already in the path
      AND ct.path NOT LIKE '%' || js.job_to || '%'
      -- Limit results per parent to prevent explosion - use ROW_NUMBER for exact counts - FIXED_VERSION_2024
      AND js.job_to IN (
          SELECT job_to
          FROM (
              SELECT job_to, 
                     ROW_NUMBER() OVER (PARTITION BY job_from ORDER BY enhanced_similarity_score DESC) as rn
              FROM analytics_job_similarities js2 
              WHERE js2.job_from = js.job_from 
                AND js2.enhanced_similarity_score IS NOT NULL
          ) ranked
          WHERE rn <= ?  -- max_results per parent - guarantees exactly N rows per parent
      )
      -- Apply organizational filters to restrict expansion
      AND (? = '' OR js.job_to IN (SELECT JobProfileID FROM core_workforce_current WHERE ORG_UNIT_NAME_2 = ?))  -- Division
      AND (? = '' OR js.job_to IN (SELECT JobProfileID FROM core_workforce_current WHERE ORG_UNIT_NAME_3 = ?))  -- Business Unit  
      AND (? = '' OR js.job_to IN (SELECT JobProfileID FROM core_workforce_current WHERE Location = ?))         -- Location
      AND (? = '' OR js.job_to IN (SELECT JobProfileID FROM core_workforce_current WHERE Rg = ?))               -- Region
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
FROM career_tree
ORDER BY level, similarity_score DESC, name;