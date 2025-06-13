-- =================================================================
-- CAREER PATHWAY QUERIES
-- Queries for career progression analysis and pathway discovery
-- =================================================================

-- query_name: get_career_progression_options
-- Find potential career progression paths from a starting job
SELECT 
    target.id as target_job_id,
    target.job_title as target_job_title,
    target.job_family as target_family,
    target.job_level as target_level,
    js.similarity_score,
    CASE 
        WHEN target.job_level > source.job_level THEN 'Promotion'
        WHEN target.job_level = source.job_level THEN 'Lateral Move'
        ELSE 'Role Change'
    END as move_type,
    skills_gap.skills_to_develop,
    skills_gap.common_skills_count
FROM jobs source
JOIN job_similarities js ON source.id = js.job_id
JOIN jobs target ON js.similar_job_id = target.id
LEFT JOIN (
    -- Calculate skills gap between source and target jobs
    SELECT 
        source_skills.job_id as source_job_id,
        target_skills.job_id as target_job_id,
        COUNT(CASE WHEN target_skills.skills_skill_id IS NULL THEN 1 END) as skills_to_develop,
        COUNT(CASE WHEN source_skills.skills_skill_id IS NOT NULL THEN 1 END) as common_skills_count
    FROM job_skills source_skills
    FULL OUTER JOIN job_skills target_skills 
        ON source_skills.skills_skill_id = target_skills.skills_skill_id
        AND target_skills.job_id = ?
    WHERE source_skills.job_id = ?
    GROUP BY source_skills.job_id, target_skills.job_id
) skills_gap ON skills_gap.source_job_id = source.id AND skills_gap.target_job_id = target.id
WHERE source.id = ?
    AND js.similarity_score >= ?
    AND target.id != source.id
ORDER BY js.similarity_score DESC, move_type
LIMIT ?;

-- query_name: get_skills_gap_analysis
-- Analyse skills gap between two specific jobs
SELECT 
    s.skill_name,
    s.skill_category,
    s.skill_subcategory,
    source_skills.proficiency_level as current_proficiency,
    target_skills.proficiency_level as required_proficiency,
    CASE 
        WHEN source_skills.skills_skill_id IS NULL THEN 'New Skill Required'
        WHEN target_skills.skills_skill_id IS NULL THEN 'Transferable Skill'
        WHEN source_skills.proficiency_level < target_skills.proficiency_level THEN 'Skill Development Required'
        ELSE 'Skill Match'
    END as skill_status
FROM skills s
LEFT JOIN job_skills source_skills ON s.id = source_skills.skills_skill_id AND source_skills.job_id = ?
LEFT JOIN job_skills target_skills ON s.id = target_skills.skills_skill_id AND target_skills.job_id = ?
WHERE source_skills.skills_skill_id IS NOT NULL OR target_skills.skills_skill_id IS NOT NULL
ORDER BY s.skill_category, skill_status, s.skill_name;

-- query_name: get_pathway_by_level_progression
-- Find career pathways by job level progression within job families
SELECT 
    family_progression.job_family,
    family_progression.current_level,
    family_progression.next_level,
    COUNT(*) as available_positions,
    AVG(js.similarity_score) as avg_similarity,
    GROUP_CONCAT(DISTINCT next_jobs.job_title, '; ') as available_roles
FROM (
    SELECT DISTINCT 
        j1.job_family,
        j1.job_level as current_level,
        j2.job_level as next_level
    FROM jobs j1
    CROSS JOIN jobs j2
    WHERE j1.job_family = j2.job_family
        AND j2.job_level > j1.job_level
        AND j1.id = ?
) family_progression
JOIN jobs current_jobs ON family_progression.job_family = current_jobs.job_family 
    AND family_progression.current_level = current_jobs.job_level
JOIN jobs next_jobs ON family_progression.job_family = next_jobs.job_family 
    AND family_progression.next_level = next_jobs.job_level
JOIN job_similarities js ON current_jobs.id = js.job_id AND next_jobs.id = js.similar_job_id
WHERE current_jobs.id = ?
GROUP BY family_progression.job_family, family_progression.current_level, family_progression.next_level
ORDER BY avg_similarity DESC;

-- query_name: get_cross_family_pathways
-- Find pathways to other job families with high skill overlap
SELECT 
    target_family.job_family as target_family,
    COUNT(DISTINCT target_jobs.id) as available_positions,
    AVG(js.similarity_score) as avg_similarity,
    MAX(js.similarity_score) as best_similarity,
    skill_overlap.common_skills_percentage,
    GROUP_CONCAT(DISTINCT target_jobs.job_title, '; ') as example_roles
FROM jobs source_job
JOIN job_similarities js ON source_job.id = js.job_id
JOIN jobs target_jobs ON js.similar_job_id = target_jobs.id
JOIN (
    SELECT DISTINCT job_family 
    FROM jobs 
    WHERE job_family != (SELECT job_family FROM jobs WHERE id = ?)
) target_family ON target_jobs.job_family = target_family.job_family
LEFT JOIN (
    -- Calculate skill overlap percentage
    SELECT 
        target_jobs.job_family,
        (COUNT(DISTINCT common_skills.skills_skill_id) * 100.0 / 
         COUNT(DISTINCT all_source_skills.skills_skill_id)) as common_skills_percentage
    FROM job_skills all_source_skills
    LEFT JOIN job_skills common_skills ON all_source_skills.skills_skill_id = common_skills.skills_skill_id
    LEFT JOIN jobs target_jobs ON common_skills.job_id = target_jobs.id
    WHERE all_source_skills.job_id = ?
        AND (common_skills.job_id IS NULL OR target_jobs.job_family != (SELECT job_family FROM jobs WHERE id = ?))
    GROUP BY target_jobs.job_family
) skill_overlap ON skill_overlap.job_family = target_family.job_family
WHERE source_job.id = ?
    AND js.similarity_score >= ?
    AND target_jobs.job_family != source_job.job_family
GROUP BY target_family.job_family, skill_overlap.common_skills_percentage
HAVING COUNT(DISTINCT target_jobs.id) >= 1
ORDER BY avg_similarity DESC, common_skills_percentage DESC
LIMIT ?;

-- query_name: get_common_career_transitions
-- Find most common career transitions across the organisation
SELECT 
    source.job_family as from_family,
    target.job_family as to_family,
    source.job_level as from_level,
    target.job_level as to_level,
    COUNT(*) as transition_frequency,
    AVG(js.similarity_score) as avg_similarity,
    CASE 
        WHEN target.job_level > source.job_level THEN 'Promotion'
        WHEN target.job_level = source.job_level AND source.job_family != target.job_family THEN 'Cross-Family Move'
        WHEN target.job_level = source.job_level THEN 'Lateral Move'
        ELSE 'Level Change'
    END as transition_type
FROM job_similarities js
JOIN jobs source ON js.job_id = source.id
JOIN jobs target ON js.similar_job_id = target.id
WHERE js.similarity_score >= ?
GROUP BY source.job_family, target.job_family, source.job_level, target.job_level
HAVING transition_frequency >= ?
ORDER BY transition_frequency DESC, avg_similarity DESC;

-- query_name: get_skill_development_recommendations
-- Get skill development recommendations for a career target
SELECT 
    s.skill_name,
    s.skill_category,
    s.skill_subcategory,
    target_skills.proficiency_level as required_level,
    COUNT(similar_jobs.id) as jobs_requiring_skill,
    AVG(similar_js.similarity_score) as avg_job_similarity
FROM skills s
JOIN job_skills target_skills ON s.id = target_skills.skills_skill_id
LEFT JOIN job_skills source_skills ON s.id = source_skills.skills_skill_id AND source_skills.job_id = ?
JOIN jobs similar_jobs ON target_skills.job_id = similar_jobs.id
JOIN job_similarities similar_js ON similar_jobs.id = similar_js.similar_job_id
WHERE target_skills.job_id = ?
    AND source_skills.skills_skill_id IS NULL  -- Skills not currently possessed
    AND similar_js.job_id = ?  -- Similar to current job
    AND similar_js.similarity_score >= ?
GROUP BY s.id, s.skill_name, s.skill_category, s.skill_subcategory, target_skills.proficiency_level
ORDER BY jobs_requiring_skill DESC, avg_job_similarity DESC; 