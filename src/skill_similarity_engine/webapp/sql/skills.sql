-- =================================================================
-- SKILLS QUERIES
-- Queries for skills analysis, proficiency levels, and skill relationships
-- =================================================================

-- query_name: get_skills_by_category
-- Get all skills grouped by category and subcategory
SELECT 
    Category as skill_category,
    Subcategory as skill_subcategory,
    COUNT(*) as skill_count,
    COUNT(DISTINCT js.JobProfileID) as jobs_using_skills
FROM skills s
LEFT JOIN job_skills js ON s.Skill_ID = js.Skill_ID
GROUP BY Category, Subcategory
ORDER BY Category, Subcategory;

-- query_name: get_top_skills_in_family
-- Get most common skills within a specific job family
SELECT 
    s.skill_name,
    s.skill_category,
    s.skill_subcategory,
    COUNT(DISTINCT js.job_id) as jobs_count,
    COUNT(DISTINCT js.job_id) * 100.0 / family_jobs.total_jobs as percentage_of_family,
    AVG(CASE 
        WHEN js.proficiency_level = 'Beginner' THEN 1
        WHEN js.proficiency_level = 'Intermediate' THEN 2
        WHEN js.proficiency_level = 'Advanced' THEN 3
        WHEN js.proficiency_level = 'Expert' THEN 4
        ELSE 2
    END) as avg_proficiency_score
FROM skills s
JOIN job_skills js ON s.id = js.skills_skill_id
JOIN jobs j ON js.job_id = j.id
CROSS JOIN (
    SELECT COUNT(*) as total_jobs 
    FROM jobs 
    WHERE job_family = ?
) family_jobs
WHERE j.job_family = ?
GROUP BY s.id, s.skill_name, s.skill_category, s.skill_subcategory, family_jobs.total_jobs
ORDER BY jobs_count DESC, avg_proficiency_score DESC
LIMIT ?;

-- query_name: get_skill_proficiency_distribution
-- Get distribution of proficiency levels for a specific skill
SELECT 
    s.skill_name,
    s.skill_category,
    js.proficiency_level,
    COUNT(*) as job_count,
    COUNT(*) * 100.0 / skill_total.total as percentage
FROM skills s
JOIN job_skills js ON s.id = js.skills_skill_id
CROSS JOIN (
    SELECT COUNT(*) as total
    FROM job_skills js2
    WHERE js2.skills_skill_id = ?
) skill_total
WHERE s.id = ?
GROUP BY s.id, s.skill_name, s.skill_category, js.proficiency_level, skill_total.total
ORDER BY 
    CASE js.proficiency_level
        WHEN 'Beginner' THEN 1
        WHEN 'Intermediate' THEN 2
        WHEN 'Advanced' THEN 3
        WHEN 'Expert' THEN 4
        ELSE 5
    END;

-- query_name: get_skill_gaps_between_jobs
-- Find skill gaps between two specific jobs
SELECT 
    s.skill_name,
    s.skill_category,
    s.skill_subcategory,
    job1_skills.proficiency_level as job1_proficiency,
    job2_skills.proficiency_level as job2_proficiency,
    CASE 
        WHEN job1_skills.skills_skill_id IS NULL THEN 'Missing in Job 1'
        WHEN job2_skills.skills_skill_id IS NULL THEN 'Missing in Job 2'
        WHEN job1_skills.proficiency_level != job2_skills.proficiency_level THEN 'Different Proficiency'
        ELSE 'Same Requirement'
    END as gap_type
FROM skills s
LEFT JOIN job_skills job1_skills ON s.id = job1_skills.skills_skill_id AND job1_skills.job_id = ?
LEFT JOIN job_skills job2_skills ON s.id = job2_skills.skills_skill_id AND job2_skills.job_id = ?
WHERE job1_skills.skills_skill_id IS NOT NULL OR job2_skills.skills_skill_id IS NOT NULL
ORDER BY s.skill_category, gap_type, s.skill_name;

-- query_name: get_transferable_skills
-- Find skills that are common across multiple job families
SELECT 
    s.skill_name,
    s.skill_category,
    s.skill_subcategory,
    COUNT(DISTINCT j.job_family) as families_count,
    COUNT(DISTINCT js.job_id) as jobs_count,
    GROUP_CONCAT(DISTINCT j.job_family) as families,
    AVG(CASE 
        WHEN js.proficiency_level = 'Beginner' THEN 1
        WHEN js.proficiency_level = 'Intermediate' THEN 2
        WHEN js.proficiency_level = 'Advanced' THEN 3
        WHEN js.proficiency_level = 'Expert' THEN 4
        ELSE 2
    END) as avg_proficiency_score
FROM skills s
JOIN job_skills js ON s.id = js.skills_skill_id
JOIN jobs j ON js.job_id = j.id
GROUP BY s.id, s.skill_name, s.skill_category, s.skill_subcategory
HAVING families_count >= ?
ORDER BY families_count DESC, jobs_count DESC;

-- query_name: get_emerging_skills
-- Find skills that appear in high-level jobs but not in entry-level positions
SELECT 
    s.skill_name,
    s.skill_category,
    s.skill_subcategory,
    COUNT(DISTINCT CASE WHEN j.job_level IN ('Senior', 'Lead', 'Principal', 'Executive') THEN js.job_id END) as senior_jobs,
    COUNT(DISTINCT CASE WHEN j.job_level IN ('Entry', 'Junior', 'Associate') THEN js.job_id END) as junior_jobs,
    COUNT(DISTINCT js.job_id) as total_jobs,
    (COUNT(DISTINCT CASE WHEN j.job_level IN ('Senior', 'Lead', 'Principal', 'Executive') THEN js.job_id END) * 100.0 / 
     NULLIF(COUNT(DISTINCT js.job_id), 0)) as senior_percentage
FROM skills s
JOIN job_skills js ON s.id = js.skills_skill_id
JOIN jobs j ON js.job_id = j.id
GROUP BY s.id, s.skill_name, s.skill_category, s.skill_subcategory
HAVING senior_jobs > 0 AND senior_percentage >= ?
ORDER BY senior_percentage DESC, senior_jobs DESC;

-- query_name: get_skill_combinations
-- Find common skill combinations that appear together in jobs
SELECT 
    s1.skill_name as skill_1,
    s2.skill_name as skill_2,
    s1.skill_category as category_1,
    s2.skill_category as category_2,
    COUNT(DISTINCT js1.job_id) as jobs_with_both,
    COUNT(DISTINCT js1.job_id) * 100.0 / skill1_total.total as percentage_of_skill1_jobs
FROM skills s1
JOIN job_skills js1 ON s1.id = js1.skills_skill_id
JOIN job_skills js2 ON js1.job_id = js2.job_id AND js2.skills_skill_id != js1.skills_skill_id
JOIN skills s2 ON js2.skills_skill_id = s2.id
CROSS JOIN (
    SELECT COUNT(DISTINCT job_id) as total
    FROM job_skills
    WHERE skills_skill_id = ?
) skill1_total
WHERE s1.id = ?
    AND s1.id < s2.id  -- Avoid duplicate pairs
GROUP BY s1.id, s1.skill_name, s1.skill_category, s2.id, s2.skill_name, s2.skill_category, skill1_total.total
HAVING jobs_with_both >= ?
ORDER BY jobs_with_both DESC, percentage_of_skill1_jobs DESC;

-- query_name: get_skills_by_proficiency_requirement
-- Get skills filtered by minimum proficiency level requirement
SELECT 
    s.skill_name,
    s.skill_category,
    s.skill_subcategory,
    js.proficiency_level,
    COUNT(DISTINCT js.job_id) as jobs_requiring_level,
    GROUP_CONCAT(DISTINCT j.job_title, '; ') as example_jobs
FROM skills s
JOIN job_skills js ON s.id = js.skills_skill_id
JOIN jobs j ON js.job_id = j.id
WHERE js.proficiency_level = ?
GROUP BY s.id, s.skill_name, s.skill_category, s.skill_subcategory, js.proficiency_level
ORDER BY jobs_requiring_level DESC;

-- query_name: get_skill_trends_by_level
-- Analyse how skill requirements change across job levels
SELECT 
    s.skill_name,
    s.skill_category,
    j.job_level,
    COUNT(*) as frequency,
    AVG(CASE 
        WHEN js.proficiency_level = 'Beginner' THEN 1
        WHEN js.proficiency_level = 'Intermediate' THEN 2
        WHEN js.proficiency_level = 'Advanced' THEN 3
        WHEN js.proficiency_level = 'Expert' THEN 4
        ELSE 2
    END) as avg_proficiency_score,
    MODE() WITHIN GROUP (ORDER BY js.proficiency_level) as most_common_proficiency
FROM skills s
JOIN job_skills js ON s.id = js.skills_skill_id
JOIN jobs j ON js.job_id = j.id
WHERE s.skill_category = ?
GROUP BY s.id, s.skill_name, s.skill_category, j.job_level
ORDER BY s.skill_name, 
    CASE j.job_level
        WHEN 'Entry' THEN 1
        WHEN 'Junior' THEN 2
        WHEN 'Associate' THEN 3
        WHEN 'Mid' THEN 4
        WHEN 'Senior' THEN 5
        WHEN 'Lead' THEN 6
        WHEN 'Principal' THEN 7
        WHEN 'Executive' THEN 8
        ELSE 9
    END;

-- query_name: get_transferable_skills_analysis
-- Advanced transferable skills analysis based on category relationships and co-occurrence patterns
WITH source_skills AS (
    SELECT js.Skill_ID, s.Skill_Name, s.Category, s.Subcategory, s.SkillType
    FROM job_skills js
    JOIN skills s ON js.Skill_ID = s.Skill_ID
    WHERE js.JobProfileID = ?
),
target_skills AS (
    SELECT js.Skill_ID, s.Skill_Name, s.Category, s.Subcategory, s.SkillType
    FROM job_skills js
    JOIN skills s ON js.Skill_ID = s.Skill_ID
    WHERE js.JobProfileID = ?
),
skills_matched AS (
    SELECT ss.Skill_ID, ss.Skill_Name, ss.Category, ss.Subcategory, ss.SkillType
    FROM source_skills ss
    INNER JOIN target_skills ts ON ss.Skill_ID = ts.Skill_ID
),
skills_to_develop AS (
    SELECT ts.Skill_ID, ts.Skill_Name, ts.Category, ts.Subcategory, ts.SkillType
    FROM target_skills ts
    LEFT JOIN source_skills ss ON ts.Skill_ID = ss.Skill_ID
    WHERE ss.Skill_ID IS NULL
),
skills_only_in_source AS (
    SELECT ss.Skill_ID, ss.Skill_Name, ss.Category, ss.Subcategory, ss.SkillType
    FROM source_skills ss
    LEFT JOIN target_skills ts ON ss.Skill_ID = ts.Skill_ID
    WHERE ts.Skill_ID IS NULL
),
-- Calculate skill co-occurrence patterns with target job skills
skill_cooccurrence AS (
    SELECT 
        sos.Skill_ID as source_skill_id,
        sos.Skill_Name as source_skill_name,
        sos.Category as source_category,
        sos.SkillType as source_skill_type,
        COUNT(DISTINCT js2.JobProfileID) as jobs_with_target_category,
        CAST(COUNT(DISTINCT js2.JobProfileID) AS REAL) / 
            (SELECT COUNT(DISTINCT JobProfileID) FROM job_skills) as cooccurrence_score
    FROM skills_only_in_source sos
    JOIN job_skills js1 ON sos.Skill_ID = js1.Skill_ID
    -- Find jobs that have this source skill AND skills from target categories
    JOIN job_skills js2 ON js1.JobProfileID = js2.JobProfileID
    JOIN skills s2 ON js2.Skill_ID = s2.Skill_ID
    -- Match with categories present in target job
    WHERE s2.Category IN (SELECT DISTINCT Category FROM target_skills)
        AND js1.Skill_ID != js2.Skill_ID
    GROUP BY sos.Skill_ID, sos.Skill_Name, sos.Category, sos.SkillType
),
-- Classify transferability based on multiple criteria
transferable_skills AS (
    SELECT 
        sos.Skill_ID,
        sos.Skill_Name,
        sos.Category,
        sos.Subcategory,
        sos.SkillType,
        COALESCE(sc.cooccurrence_score, 0) as cooccurrence_score,
        CASE 
            -- High transferability: Same category as target skills
            WHEN sos.Category IN (SELECT DISTINCT Category FROM target_skills) THEN 'High'
            -- Medium transferability: High co-occurrence with target skill categories
            WHEN COALESCE(sc.cooccurrence_score, 0) >= 0.3 THEN 'Medium'
            -- Low transferability: Common skills (communication, leadership, etc.)
            WHEN sos.SkillType = 'Common Skill' THEN 'Low'
            -- Minimal transferability: Specialized skills with no category overlap
            ELSE 'Minimal'
        END as transferability_level,
        CASE 
            WHEN sos.Category IN (SELECT DISTINCT Category FROM target_skills) THEN 'Same category as target role'
            WHEN COALESCE(sc.cooccurrence_score, 0) >= 0.3 THEN 'Frequently paired with target skills'
            WHEN sos.SkillType = 'Common Skill' THEN 'Foundational transferable skill'
            ELSE 'Limited direct relevance'
        END as transferability_reason
    FROM skills_only_in_source sos
    LEFT JOIN skill_cooccurrence sc ON sos.Skill_ID = sc.source_skill_id
    WHERE CASE 
        WHEN sos.Category IN (SELECT DISTINCT Category FROM target_skills) THEN 1
        WHEN COALESCE(sc.cooccurrence_score, 0) >= 0.2 THEN 1
        WHEN sos.SkillType = 'Common Skill' THEN 1
        ELSE 0
    END = 1
)
-- Return comprehensive analysis
SELECT 
    'matched' as skill_status,
    COUNT(*) as skill_count,
    SkillType,
    Category,
    '' as transferability_level,
    '' as transferability_reason
FROM skills_matched
GROUP BY SkillType, Category
UNION ALL
SELECT 
    'develop' as skill_status,
    COUNT(*) as skill_count,
    SkillType,
    Category,
    '' as transferability_level,
    '' as transferability_reason
FROM skills_to_develop
GROUP BY SkillType, Category
UNION ALL
SELECT 
    'transferable' as skill_status,
    COUNT(*) as skill_count,
    SkillType,
    Category,
    transferability_level,
    MAX(transferability_reason) as transferability_reason
FROM transferable_skills
GROUP BY SkillType, Category, transferability_level
ORDER BY skill_status, transferability_level DESC, skill_count DESC; 