-- Executive Summary SQL Queries
-- References (1) through (16) from whitepaper_example_gold_standard.md

-- Reference (1): Total job profiles in database
-- SELECT COUNT(*) FROM jobs
CREATE VIEW ref_01_total_job_profiles AS
SELECT COUNT(*) as total_job_count
FROM jobs;

-- Reference (2): Top 3 similarities range calculation
-- SELECT similarity_score FROM job_similarities WHERE job_from = ? ORDER BY similarity_score DESC LIMIT 3
CREATE VIEW ref_02_top_similarities_template AS
SELECT 
    MIN(similarity_score) as min_similarity,
    MAX(similarity_score) as max_similarity,
    COUNT(*) as pathway_count
FROM (
    SELECT similarity_score 
    FROM job_similarities 
    WHERE job_from = ? 
      AND similarity_score < 1.0  -- Exclude 100% matches
    ORDER BY similarity_score DESC 
    LIMIT 3
);

-- Reference (3): Outstanding opportunities assessment (percentile-based)
-- Qualitative assessment derived from similarity scores >78% (top quartile performance)
CREATE VIEW ref_03_similarity_distribution AS
SELECT 
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY similarity_score) as p95_threshold,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY similarity_score) as p90_threshold,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY similarity_score) as p75_threshold,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY similarity_score) as p50_threshold
FROM job_similarities 
WHERE similarity_score > 0.0 AND similarity_score < 1.0;

-- Reference (4): Percentile ranking calculation
-- SELECT PERCENTILE_RANK() WITHIN GROUP (ORDER BY similarity_score) FROM job_similarities WHERE similarity_score < 1.0
CREATE VIEW ref_04_percentile_ranking_template AS
SELECT 
    similarity_score,
    PERCENT_RANK() OVER (ORDER BY similarity_score) * 100 as percentile_rank
FROM job_similarities 
WHERE similarity_score > 0.0 AND similarity_score < 1.0;

-- Reference (5): Senior Risk Analyst similarity
-- SELECT similarity_score FROM job_similarities WHERE job_from = ? AND job_to = 'R0156.2'
-- (Template - requires job_from parameter)

-- Reference (6): Move type classification for Senior Risk Analyst
-- Management level progression analysis (Group 1 → Group 2, same function)
CREATE VIEW ref_06_move_type_classification AS
SELECT 
    source.JobProfileID as source_job_id,
    target.JobProfileID as target_job_id,
    source.ManagementLevel as source_level,
    target.ManagementLevel as target_level,
    source.JobFunction as source_function,
    target.JobFunction as target_function,
    CASE 
        WHEN source.JobFunction = target.JobFunction AND 
             CAST(SUBSTR(target.ManagementLevel, -1) AS INTEGER) > CAST(SUBSTR(source.ManagementLevel, -1) AS INTEGER)
        THEN 'Progression - Functional_Advancement'
        WHEN source.JobFunction != target.JobFunction AND 
             CAST(SUBSTR(target.ManagementLevel, -1) AS INTEGER) >= CAST(SUBSTR(source.ManagementLevel, -1) AS INTEGER)
        THEN 'Progression - Cross_Functional_Advancement'
        WHEN CAST(SUBSTR(target.ManagementLevel, -1) AS INTEGER) = CAST(SUBSTR(source.ManagementLevel, -1) AS INTEGER)
        THEN 'Lateral - Same_Level'
        ELSE 'Other'
    END as move_type
FROM jobs source
CROSS JOIN jobs target
WHERE source.JobProfileID != target.JobProfileID;

-- Reference (7): Business Intelligence Specialist similarity
-- (Template - requires job_from parameter)

-- Reference (8): Move type for BI Specialist
-- (Uses same view as ref_06)

-- Reference (9): Technology Solutions Architect similarity
-- (Template - requires job_from parameter)

-- Reference (10): Move type for Solutions Architect
-- (Uses same view as ref_06)

-- Reference (11): Management level hierarchy mapping
-- Group NA=0, Group 1=1, Group 2=2, etc.
CREATE VIEW ref_11_management_hierarchy AS
SELECT DISTINCT
    ManagementLevel,
    CASE 
        WHEN ManagementLevel LIKE '%NA%' THEN 0
        WHEN ManagementLevel LIKE '%1%' THEN 1
        WHEN ManagementLevel LIKE '%2%' THEN 2
        WHEN ManagementLevel LIKE '%3%' THEN 3
        WHEN ManagementLevel LIKE '%4%' THEN 4
        WHEN ManagementLevel LIKE '%5%' THEN 5
        WHEN ManagementLevel LIKE '%6%' THEN 6
        WHEN ManagementLevel LIKE '%7%' THEN 7
        ELSE 1
    END as level_numeric
FROM jobs
WHERE ManagementLevel IS NOT NULL;

-- Reference (12): Objective categorisation methodology
-- (Methodological reference - no SQL needed)

-- Reference (13): Confidence level assessment
-- Based on data volume assessment (references 14-16)
CREATE VIEW ref_13_confidence_factors AS
SELECT 
    (SELECT COUNT(DISTINCT Skill_ID) FROM job_skills) as active_competencies,
    (SELECT COUNT(*) FROM career_pathways) as precomputed_pathways,
    (SELECT COUNT(DISTINCT Division) FROM positions) as division_count,
    CASE 
        WHEN (SELECT COUNT(DISTINCT Skill_ID) FROM job_skills) > 2000 AND
             (SELECT COUNT(*) FROM career_pathways) > 8000 AND
             (SELECT COUNT(DISTINCT Division) FROM positions) >= 6
        THEN 'HIGH'
        WHEN (SELECT COUNT(DISTINCT Skill_ID) FROM job_skills) > 1000 AND
             (SELECT COUNT(*) FROM career_pathways) > 5000 AND
             (SELECT COUNT(DISTINCT Division) FROM positions) >= 4
        THEN 'MEDIUM-HIGH'
        ELSE 'MEDIUM'
    END as confidence_level;

-- Reference (14): Active competencies count
-- SELECT COUNT(DISTINCT Skill_ID) FROM job_skills
CREATE VIEW ref_14_active_competencies AS
SELECT COUNT(DISTINCT Skill_ID) as active_competencies_count
FROM job_skills;

-- Reference (15): Pre-computed pathways count
-- SELECT COUNT(*) FROM career_pathways
CREATE VIEW ref_15_precomputed_pathways AS
SELECT COUNT(*) as pathways_count
FROM career_pathways;

-- Reference (16): Divisional structure count
-- SELECT COUNT(DISTINCT Division) FROM positions
CREATE VIEW ref_16_divisional_structure AS
SELECT COUNT(DISTINCT Division) as division_count
FROM positions;

-- Helper queries for dynamic threshold calculation

-- NAB-specific similarity distribution (excluding 100% matches)
CREATE VIEW nab_similarity_distribution AS
SELECT 
    similarity_score,
    PERCENT_RANK() OVER (ORDER BY similarity_score) * 100 as percentile_rank
FROM job_similarities 
WHERE similarity_score > 0.0 AND similarity_score < 1.0
ORDER BY similarity_score;

-- Top 3 pathways for any source job (using optimized career_pathways table)
CREATE VIEW top_pathways_template AS
SELECT 
    cp.source_job_id,
    cp.target_job_id,
    cp.similarity_score,
    j.JobProfile as target_job_title,
    j.JobFunction as target_job_function,
    cp.similarity_rank as rank,
    cp.career_move_type,
    cp.difficulty_score
FROM career_pathways cp
JOIN jobs j ON cp.target_job_id = j.JobProfileID
WHERE cp.similarity_rank <= 12  -- Top 12 pathways per job
ORDER BY cp.source_job_id, cp.similarity_rank; 