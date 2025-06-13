-- =================================================================
-- CAREER PATHWAY QUERIES (OPTIMIZED PRE-COMPUTED VERSION)
-- Queries for career pathway exploration using pre-computed relationships
-- =================================================================

-- query_name: get_career_tree_fast
-- Generate hierarchical tree data for D3.js using pre-computed career pathways
-- Much faster than on-the-fly computation
SELECT 
    'job' as node_type,
    j.JobProfileID as id,
    j.JobProfile as name,
    NULL as parent_id,
    0 as level,
    j.JobFamily as category,
    0.0 as similarity_score,
    j.JobProfileID as path,
    j.JobProfileID as unique_id
FROM jobs j
WHERE j.JobProfileID IN ({job_placeholders})

UNION ALL

-- Recursive levels using pre-computed career pathways
WITH RECURSIVE pathway_tree AS (
    -- Level 0: Starting jobs
    SELECT 
        cp.source_job_id as current_job_id,
        cp.target_job_id as next_job_id,
        1 as level,
        cp.similarity_rank,
        cp.similarity_score,
        cp.career_move_type,
        CAST(cp.source_job_id || '->' || cp.target_job_id AS TEXT) as path
    FROM career_pathways cp
    WHERE cp.source_job_id IN ({job_placeholders})
      AND cp.similarity_score >= ?
      AND cp.similarity_rank <= ?
    
    UNION ALL
    
    -- Recursive levels: Continue building tree
    SELECT 
        cp.source_job_id as current_job_id,
        cp.target_job_id as next_job_id,
        pt.level + 1,
        cp.similarity_rank,
        cp.similarity_score,
        cp.career_move_type,
        pt.path || '->' || cp.target_job_id as path
    FROM pathway_tree pt
    JOIN career_pathways cp ON pt.next_job_id = cp.source_job_id
    WHERE pt.level < ?  -- max_depth parameter
      AND cp.similarity_score >= ?
      AND cp.similarity_rank <= ?
      AND cp.target_job_id NOT IN (
          SELECT DISTINCT job_id 
          FROM (
              SELECT cp.source_job_id as job_id FROM career_pathways cp WHERE cp.source_job_id IN ({job_placeholders})
              UNION 
              SELECT value as job_id FROM (
                  SELECT TRIM(value) as value
                  FROM (
                      SELECT SUBSTR(pt.path || '->', start_pos, end_pos - start_pos) as value
                      FROM (
                          SELECT pt.path, 
                                 INSTR(pt.path || '->', cp.target_job_id || '->') as start_pos,
                                 INSTR(pt.path || '->', '->') as end_pos
                          FROM (SELECT pt.path) pt
                      ) positions
                      WHERE start_pos > 0
                  )
              )
              WHERE LENGTH(value) > 0
          )
      )  -- Prevent cycles
)
SELECT 
    'similar_job' as node_type,
    pt.next_job_id as id,
    j.JobProfile as name,
    pt.current_job_id as parent_id,
    pt.level,
    j.JobFamily as category,
    pt.similarity_score,
    pt.path,
    pt.current_job_id || '_' || pt.next_job_id as unique_id
FROM pathway_tree pt
JOIN jobs j ON pt.next_job_id = j.JobProfileID
LEFT JOIN positions p ON j.JobProfileID = p.JobProfileID
WHERE (? = '' OR ? = '' OR p.Division = ? OR p.Division = ?)
  AND (? = '' OR ? = '' OR p.Business_Unit = ? OR p.Business_Unit = ?)
  AND (? = '' OR ? = '' OR p.Location = ? OR p.Location = ?)
  AND (? = '' OR ? = '' OR p.Rg = ? OR p.Rg = ?)
ORDER BY level, similarity_score DESC;

-- query_name: get_top_career_pathways
-- Get top N career pathways for a specific job (simple version)
SELECT 
    cp.target_job_id,
    j.JobProfile as target_job_name,
    j.JobFamily as target_family,
    cp.similarity_score,
    cp.similarity_rank,
    cp.career_move_type,
    cp.difficulty_score,
    cp.shared_skills_count
FROM career_pathways cp
JOIN jobs j ON cp.target_job_id = j.JobProfileID
WHERE cp.source_job_id = ?
  AND cp.similarity_score >= ?
ORDER BY cp.similarity_rank
LIMIT ?;

-- query_name: get_career_pathways_by_move_type
-- Get career pathways filtered by move type
SELECT 
    cp.source_job_id,
    j1.JobProfile as source_job_name,
    cp.target_job_id,
    j2.JobProfile as target_job_name,
    cp.similarity_score,
    cp.career_move_type,
    cp.difficulty_score
FROM career_pathways cp
JOIN jobs j1 ON cp.source_job_id = j1.JobProfileID
JOIN jobs j2 ON cp.target_job_id = j2.JobProfileID
WHERE cp.career_move_type = ?
  AND cp.similarity_score >= ?
ORDER BY cp.similarity_score DESC
LIMIT ?;

-- query_name: get_pathway_statistics
-- Get statistics about career pathways
SELECT 
    career_move_type,
    COUNT(*) as pathway_count,
    AVG(similarity_score) as avg_similarity,
    AVG(difficulty_score) as avg_difficulty,
    MIN(similarity_score) as min_similarity,
    MAX(similarity_score) as max_similarity
FROM career_pathways
WHERE similarity_score >= ?
GROUP BY career_move_type
ORDER BY avg_similarity DESC;

-- query_name: get_most_connected_jobs
-- Find jobs with the most career pathway options
SELECT 
    cp.source_job_id,
    j.JobProfile as job_name,
    j.JobFamily,
    COUNT(*) as pathway_count,
    AVG(cp.similarity_score) as avg_similarity,
    COUNT(CASE WHEN cp.career_move_type = 'lateral' THEN 1 END) as lateral_moves,
    COUNT(CASE WHEN cp.career_move_type = 'progression' THEN 1 END) as progression_moves,
    COUNT(CASE WHEN cp.career_move_type = 'cross_family' THEN 1 END) as cross_family_moves
FROM career_pathways cp
JOIN jobs j ON cp.source_job_id = j.JobProfileID
WHERE cp.similarity_score >= ?
GROUP BY cp.source_job_id, j.JobProfile, j.JobFamily
ORDER BY pathway_count DESC
LIMIT ?;

-- query_name: get_pathway_skills_analysis
-- Get skills analysis for a specific career pathway
SELECT 
    js_source.Skill_Name as skill_name,
    js_source.Skill_ID as skill_id,
    s.Category as skill_category,
    CASE 
        WHEN js_target.Skill_ID IS NOT NULL THEN 'Transferable'
        ELSE 'Source Only'
    END as skill_status,
    js_source.Skill_Weight as source_weight,
    js_target.Skill_Weight as target_weight
FROM job_skills js_source
JOIN skills s ON js_source.Skill_ID = s.Skill_ID
LEFT JOIN job_skills js_target ON js_source.Skill_ID = js_target.Skill_ID 
    AND js_target.JobProfileID = ?
WHERE js_source.JobProfileID = ?

UNION

SELECT 
    js_target.Skill_Name as skill_name,
    js_target.Skill_ID as skill_id,
    s.Category as skill_category,
    'Target Required' as skill_status,
    NULL as source_weight,
    js_target.Skill_Weight as target_weight
FROM job_skills js_target
JOIN skills s ON js_target.Skill_ID = s.Skill_ID
LEFT JOIN job_skills js_source ON js_target.Skill_ID = js_source.Skill_ID 
    AND js_source.JobProfileID = ?
WHERE js_target.JobProfileID = ?
  AND js_source.Skill_ID IS NULL

ORDER BY skill_status, skill_category, skill_name;

-- query_name: get_career_pathway_recommendations
-- Get personalized career pathway recommendations with ranking
SELECT 
    cp.target_job_id,
    j.JobProfile as target_job_name,
    j.JobFamily as target_family,
    cp.similarity_score,
    cp.career_move_type,
    cp.difficulty_score,
    cp.shared_skills_count,
    -- Position availability context
    COUNT(DISTINCT p.JobProfileID) as available_positions,
    COUNT(DISTINCT CASE WHEN p."Employee Number" IS NULL THEN p.JobProfileID END) as vacant_positions,
    -- Recommendation score (combines similarity, difficulty, and availability)
    (cp.similarity_score * 0.5 + 
     (1.0 - cp.difficulty_score) * 0.3 + 
     CASE WHEN COUNT(DISTINCT p.JobProfileID) > 0 THEN 0.2 ELSE 0.0 END) as recommendation_score
FROM career_pathways cp
JOIN jobs j ON cp.target_job_id = j.JobProfileID
LEFT JOIN positions p ON j.JobProfileID = p.JobProfileID
WHERE cp.source_job_id = ?
  AND cp.similarity_score >= ?
GROUP BY cp.target_job_id, j.JobProfile, j.JobFamily, 
         cp.similarity_score, cp.career_move_type, cp.difficulty_score, cp.shared_skills_count
ORDER BY recommendation_score DESC
LIMIT ?; 