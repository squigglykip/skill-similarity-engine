-- =================================================================
-- SKILLS QUERIES - V2 SCHEMA
-- Queries for skills analysis, proficiency levels, and skill relationships
-- Updated for core_skills_taxonomy and core_job_skill_requirements tables
-- =================================================================

-- query_name: get_skills_by_category
-- Get all skills grouped by category and subcategory with V2 analytics
SELECT 
    st.primary_category as skill_category,
    st.secondary_category as skill_subcategory,
    COUNT(*) as skill_count,
    COUNT(DISTINCT jsr.job_profile_id) as jobs_using_skills
FROM core_skills_taxonomy st
LEFT JOIN core_job_skill_requirements jsr ON st.Skill_ID = jsr.skill_id
WHERE st.skill_name IS NOT NULL  -- FAIL-FAST validation
GROUP BY st.primary_category, st.secondary_category
ORDER BY st.primary_category, st.secondary_category;

-- query_name: get_top_skills_in_family
-- Get most common skills within a specific job family with V2 enhancements
SELECT 
    st.skill_name,
    st.primary_category as skill_category,
    st.secondary_category as skill_subcategory,
    COUNT(DISTINCT jsr.job_profile_id) as jobs_count,
    COUNT(DISTINCT jsr.job_profile_id) * 100.0 / family_jobs.total_jobs as percentage_of_family,
    AVG(jsr.proficiency_requirement) as avg_proficiency_score,
    SUM(CASE WHEN jsr.is_defining_skill = 1 THEN 1 ELSE 0 END) as defining_skill_instances
FROM core_skills_taxonomy st
INNER JOIN core_job_skill_requirements jsr ON st.Skill_ID = jsr.skill_id
INNER JOIN core_job_architecture ja ON jsr.job_profile_id = ja.JobProfileID
CROSS JOIN (
    SELECT COUNT(*) as total_jobs 
    FROM core_job_architecture 
    WHERE job_function = ?
) family_jobs
WHERE ja.job_function = ?
    AND st.skill_name IS NOT NULL  -- FAIL-FAST validation
    AND ja.job_title IS NOT NULL
GROUP BY st.Skill_ID, st.skill_name, st.primary_category, st.secondary_category, family_jobs.total_jobs
ORDER BY jobs_count DESC, avg_proficiency_score DESC
LIMIT ?;

-- query_name: get_skill_proficiency_distribution
-- Get distribution of proficiency levels for a specific skill
SELECT 
    st.skill_name,
    st.primary_category as skill_category,
    jsr.proficiency_requirement,
    COUNT(*) as job_count,
    COUNT(*) * 100.0 / skill_total.total as percentage
FROM core_skills_taxonomy st
INNER JOIN core_job_skill_requirements jsr ON st.Skill_ID = jsr.skill_id
CROSS JOIN (
    SELECT COUNT(*) as total
    FROM core_job_skill_requirements jsr2
    WHERE jsr2.skill_id = ?
) skill_total
WHERE st.Skill_ID = ?
    AND st.skill_name IS NOT NULL  -- FAIL-FAST validation
GROUP BY st.Skill_ID, st.skill_name, st.primary_category, jsr.proficiency_requirement, skill_total.total
ORDER BY jsr.proficiency_requirement;

-- query_name: get_skill_gaps_between_jobs
-- Find skill gaps between two specific jobs with V2 enhancements
SELECT 
    st.skill_name,
    st.primary_category as skill_category,
    st.secondary_category as skill_subcategory,
    job1_skills.proficiency_requirement as job1_proficiency,
    job2_skills.proficiency_requirement as job2_proficiency,
    job1_skills.is_defining_skill as job1_defining,
    job2_skills.is_defining_skill as job2_defining,
    CASE 
        WHEN job1_skills.skill_id IS NULL THEN 'Missing in Job 1'
        WHEN job2_skills.skill_id IS NULL THEN 'Missing in Job 2'
        WHEN job1_skills.proficiency_requirement != job2_skills.proficiency_requirement THEN 'Different Proficiency'
        ELSE 'Same Requirement'
    END as gap_type
FROM core_skills_taxonomy st
LEFT JOIN core_job_skill_requirements job1_skills ON st.Skill_ID = job1_skills.skill_id AND job1_skills.job_profile_id = ?
LEFT JOIN core_job_skill_requirements job2_skills ON st.Skill_ID = job2_skills.skill_id AND job2_skills.job_profile_id = ?
WHERE (job1_skills.skill_id IS NOT NULL OR job2_skills.skill_id IS NOT NULL)
    AND st.skill_name IS NOT NULL  -- FAIL-FAST validation
ORDER BY st.primary_category, gap_type, st.skill_name;

-- query_name: get_transferable_skills
-- Find skills that are common across multiple job families
SELECT 
    st.skill_name,
    st.primary_category as skill_category,
    st.secondary_category as skill_subcategory,
    COUNT(DISTINCT ja.job_function) as functions_count,
    COUNT(DISTINCT jsr.job_profile_id) as jobs_count,
    GROUP_CONCAT(DISTINCT ja.job_function) as functions,
    AVG(jsr.proficiency_requirement) as avg_proficiency_score,
    SUM(CASE WHEN jsr.is_defining_skill = 1 THEN 1 ELSE 0 END) as defining_instances
FROM core_skills_taxonomy st
INNER JOIN core_job_skill_requirements jsr ON st.Skill_ID = jsr.skill_id
INNER JOIN core_job_architecture ja ON jsr.job_profile_id = ja.JobProfileID
WHERE st.skill_name IS NOT NULL  -- FAIL-FAST validation
    AND ja.job_title IS NOT NULL
GROUP BY st.Skill_ID, st.skill_name, st.primary_category, st.secondary_category
HAVING functions_count >= ?
ORDER BY functions_count DESC, jobs_count DESC;

-- query_name: get_emerging_skills
-- Find skills that appear in high-level jobs but not in entry-level positions
SELECT 
    st.skill_name,
    st.primary_category as skill_category,
    st.secondary_category as skill_subcategory,
    COUNT(DISTINCT CASE WHEN ja.management_level IN ('Senior', 'Lead', 'Principal', 'Executive') THEN jsr.job_profile_id END) as senior_jobs,
    COUNT(DISTINCT CASE WHEN ja.management_level IN ('Entry', 'Junior', 'Associate') THEN jsr.job_profile_id END) as junior_jobs,
    COUNT(DISTINCT jsr.job_profile_id) as total_jobs,
    (COUNT(DISTINCT CASE WHEN ja.management_level IN ('Senior', 'Lead', 'Principal', 'Executive') THEN jsr.job_profile_id END) * 100.0 / 
     NULLIF(COUNT(DISTINCT jsr.job_profile_id), 0)) as senior_percentage
FROM core_skills_taxonomy st
INNER JOIN core_job_skill_requirements jsr ON st.Skill_ID = jsr.skill_id
INNER JOIN core_job_architecture ja ON jsr.job_profile_id = ja.JobProfileID
WHERE st.skill_name IS NOT NULL  -- FAIL-FAST validation
    AND ja.job_title IS NOT NULL
GROUP BY st.Skill_ID, st.skill_name, st.primary_category, st.secondary_category
HAVING senior_jobs > 0 AND senior_percentage >= ?
ORDER BY senior_percentage DESC, senior_jobs DESC;

-- query_name: get_skill_combinations
-- Find common skill combinations that appear together in jobs
SELECT 
    s1.skill_name as skill_1,
    s2.skill_name as skill_2,
    s1.primary_category as category_1,
    s2.primary_category as category_2,
    COUNT(DISTINCT js1.job_profile_id) as jobs_with_both,
    COUNT(DISTINCT js1.job_profile_id) * 100.0 / skill1_total.total as percentage_of_skill1_jobs
FROM core_skills_taxonomy s1
INNER JOIN core_job_skill_requirements js1 ON s1.Skill_ID = js1.skill_id
INNER JOIN core_job_skill_requirements js2 ON js1.job_profile_id = js2.job_profile_id AND js2.skill_id != js1.skill_id
INNER JOIN core_skills_taxonomy s2 ON js2.skill_id = s2.Skill_ID
CROSS JOIN (
    SELECT COUNT(DISTINCT job_profile_id) as total
    FROM core_job_skill_requirements
    WHERE skill_id = ?
) skill1_total
WHERE s1.Skill_ID = ?
    AND s1.Skill_ID < s2.Skill_ID  -- Avoid duplicate pairs
    AND s1.skill_name IS NOT NULL  -- FAIL-FAST validation
    AND s2.skill_name IS NOT NULL
GROUP BY s1.Skill_ID, s1.skill_name, s1.primary_category, s2.Skill_ID, s2.skill_name, s2.primary_category, skill1_total.total
HAVING jobs_with_both >= ?
ORDER BY jobs_with_both DESC, percentage_of_skill1_jobs DESC;

-- query_name: get_skills_by_proficiency_requirement
-- Get skills filtered by minimum proficiency level requirement
SELECT 
    st.skill_name,
    st.primary_category as skill_category,
    st.secondary_category as skill_subcategory,
    jsr.proficiency_requirement,
    COUNT(DISTINCT jsr.job_profile_id) as jobs_requiring_level,
    GROUP_CONCAT(DISTINCT ja.job_title, '; ') as example_jobs
FROM core_skills_taxonomy st
INNER JOIN core_job_skill_requirements jsr ON st.Skill_ID = jsr.skill_id
INNER JOIN core_job_architecture ja ON jsr.job_profile_id = ja.JobProfileID
WHERE jsr.proficiency_requirement >= ?
    AND st.skill_name IS NOT NULL  -- FAIL-FAST validation
    AND ja.job_title IS NOT NULL
GROUP BY st.Skill_ID, st.skill_name, st.primary_category, st.secondary_category, jsr.proficiency_requirement
ORDER BY jobs_requiring_level DESC;

-- query_name: get_skill_trends_by_level
-- Analyse how skill requirements change across job levels
SELECT 
    st.skill_name,
    st.primary_category as skill_category,
    ja.management_level,
    COUNT(*) as frequency,
    AVG(jsr.proficiency_requirement) as avg_proficiency_score,
    SUM(CASE WHEN jsr.is_defining_skill = 1 THEN 1 ELSE 0 END) as defining_instances
FROM core_skills_taxonomy st
INNER JOIN core_job_skill_requirements jsr ON st.Skill_ID = jsr.skill_id
INNER JOIN core_job_architecture ja ON jsr.job_profile_id = ja.JobProfileID
WHERE st.primary_category = ?
    AND st.skill_name IS NOT NULL  -- FAIL-FAST validation
    AND ja.job_title IS NOT NULL
GROUP BY st.Skill_ID, st.skill_name, st.primary_category, ja.management_level
ORDER BY st.skill_name, ja.management_level;

-- query_name: get_defining_skills_analysis
-- Simplified defining skills analysis for job transitions
SELECT 
    st.skill_name,
    st.primary_category as skill_category,
    st.secondary_category as skill_subcategory,
    jsr1.proficiency_requirement as source_proficiency,
    jsr2.proficiency_requirement as target_proficiency,
    jsr1.is_defining_skill as source_defining,
    jsr2.is_defining_skill as target_defining,
    CASE 
        WHEN jsr1.skill_id IS NULL THEN 'Need to Develop'
        WHEN jsr2.skill_id IS NULL THEN 'Transferable Skill'
        WHEN jsr1.proficiency_requirement < jsr2.proficiency_requirement THEN 'Need to Upskill'
        WHEN jsr1.proficiency_requirement > jsr2.proficiency_requirement THEN 'Overqualified'
        ELSE 'Direct Match'
    END as skill_gap_type
FROM core_skills_taxonomy st
LEFT JOIN core_job_skill_requirements jsr1 ON st.Skill_ID = jsr1.skill_id AND jsr1.job_profile_id = ?
LEFT JOIN core_job_skill_requirements jsr2 ON st.Skill_ID = jsr2.skill_id AND jsr2.job_profile_id = ?
WHERE (jsr1.skill_id IS NOT NULL OR jsr2.skill_id IS NOT NULL)
    AND st.skill_name IS NOT NULL  -- FAIL-FAST validation
ORDER BY 
    CASE 
        WHEN jsr2.is_defining_skill = 1 AND jsr1.skill_id IS NULL THEN 1  -- Critical gaps first
        WHEN jsr2.is_defining_skill = 1 THEN 2  -- Other defining skills
        ELSE 3  -- Non-defining skills
    END,
    st.primary_category, st.skill_name;

-- query_name: get_skills_analysis_summary_for_api
-- Enhanced skills analysis summary with defining skills, rarity, and velocity intelligence
WITH job1_skills AS (
    SELECT jsr.Skill_ID, st.Skill_Name, st.Category, st.Subcategory, st.SkillType
    FROM core_job_skill_requirements jsr
    JOIN core_skills_taxonomy st ON jsr.Skill_ID = st.Skill_ID
    WHERE jsr.JobProfileID = ?
      AND st.Skill_Name IS NOT NULL
),
job2_skills AS (
    SELECT jsr.Skill_ID, st.Skill_Name, st.Category, st.Subcategory, st.SkillType
    FROM core_job_skill_requirements jsr
    JOIN core_skills_taxonomy st ON jsr.Skill_ID = st.Skill_ID
    WHERE jsr.JobProfileID = ?
      AND st.Skill_Name IS NOT NULL
),
skills_matched AS (
    SELECT j1.Skill_ID, j1.Skill_Name, j1.Category, j1.Subcategory, j1.SkillType
    FROM job1_skills j1
    INNER JOIN job2_skills j2 ON j1.Skill_ID = j2.Skill_ID
),
skills_to_develop AS (
    SELECT j2.Skill_ID, j2.Skill_Name, j2.Category, j2.Subcategory, j2.SkillType
    FROM job2_skills j2
    LEFT JOIN job1_skills j1 ON j2.Skill_ID = j1.Skill_ID
    WHERE j1.Skill_ID IS NULL
),
skills_transferable AS (
    SELECT j1.Skill_ID, j1.Skill_Name, j1.Category, j1.Subcategory, j1.SkillType
    FROM job1_skills j1
    LEFT JOIN job2_skills j2 ON j1.Skill_ID = j2.Skill_ID
    WHERE j2.Skill_ID IS NULL
),
enhanced_matched AS (
    SELECT 
        sm.*,
        COALESCE(ajds.defining_skill_rank, 999) as defining_rank,
        COALESCE(asr.rarity_score, 50.0) as rarity_score,
        COALESCE(asr.rarity_category, 'Common') as rarity_category,
        COALESCE(asdt.velocity_category, 'stable') as velocity_category,
        COALESCE(asdt.trend_direction, 'stable') as trend_direction,
        CASE WHEN ajds.defining_skill_rank IS NOT NULL THEN 1 ELSE 0 END as is_defining
    FROM skills_matched sm
    LEFT JOIN analytics_job_defining_skills ajds ON sm.Skill_ID = ajds.skill_id AND ajds.job_profile_id = ?
    LEFT JOIN analytics_skill_rarity asr ON sm.Skill_ID = asr.skill_id
    LEFT JOIN analytics_skill_demand_trends asdt ON sm.Skill_ID = asdt.skill_id
),
enhanced_to_develop AS (
    SELECT 
        std.*,
        COALESCE(ajds.defining_skill_rank, 999) as defining_rank,
        COALESCE(asr.rarity_score, 50.0) as rarity_score,
        COALESCE(asr.rarity_category, 'Common') as rarity_category,
        COALESCE(asdt.velocity_category, 'stable') as velocity_category,
        COALESCE(asdt.trend_direction, 'stable') as trend_direction,
        CASE WHEN ajds.defining_skill_rank IS NOT NULL THEN 1 ELSE 0 END as is_defining
    FROM skills_to_develop std
    LEFT JOIN analytics_job_defining_skills ajds ON std.Skill_ID = ajds.skill_id AND ajds.job_profile_id = ?
    LEFT JOIN analytics_skill_rarity asr ON std.Skill_ID = asr.skill_id
    LEFT JOIN analytics_skill_demand_trends asdt ON std.Skill_ID = asdt.skill_id
),
enhanced_transferable AS (
    SELECT 
        st.*,
        COALESCE(ajds.defining_skill_rank, 999) as defining_rank,
        COALESCE(asr.rarity_score, 50.0) as rarity_score,
        COALESCE(asr.rarity_category, 'Common') as rarity_category,
        COALESCE(asdt.velocity_category, 'stable') as velocity_category,
        COALESCE(asdt.trend_direction, 'stable') as trend_direction,
        CASE WHEN ajds.defining_skill_rank IS NOT NULL THEN 1 ELSE 0 END as is_defining
    FROM skills_transferable st
    LEFT JOIN analytics_job_defining_skills ajds ON st.Skill_ID = ajds.skill_id AND ajds.job_profile_id = ?
    LEFT JOIN analytics_skill_rarity asr ON st.Skill_ID = asr.skill_id
    LEFT JOIN analytics_skill_demand_trends asdt ON st.Skill_ID = asdt.skill_id
)
SELECT 
    'matched' as skill_status,
    COUNT(*) as skill_count,
    em.SkillType,
    em.Category,
    SUM(CASE WHEN em.is_defining = 1 THEN 1 ELSE 0 END) as defining_skills_count,
    SUM(CASE WHEN em.rarity_category = 'Rare' THEN 1 ELSE 0 END) as rare_skills_count,
    SUM(CASE WHEN em.velocity_category = 'emerging' THEN 1 ELSE 0 END) as emerging_skills_count,
    SUM(CASE WHEN em.velocity_category = 'declining' THEN 1 ELSE 0 END) as declining_skills_count,
    ROUND(AVG(em.rarity_score), 1) as avg_rarity_score
FROM enhanced_matched em
GROUP BY em.SkillType, em.Category
UNION ALL
SELECT 
    'develop' as skill_status,
    COUNT(*) as skill_count,
    etd.SkillType,
    etd.Category,
    SUM(CASE WHEN etd.is_defining = 1 THEN 1 ELSE 0 END) as defining_skills_count,
    SUM(CASE WHEN etd.rarity_category = 'Rare' THEN 1 ELSE 0 END) as rare_skills_count,
    SUM(CASE WHEN etd.velocity_category = 'emerging' THEN 1 ELSE 0 END) as emerging_skills_count,
    SUM(CASE WHEN etd.velocity_category = 'declining' THEN 1 ELSE 0 END) as declining_skills_count,
    ROUND(AVG(etd.rarity_score), 1) as avg_rarity_score
FROM enhanced_to_develop etd
GROUP BY etd.SkillType, etd.Category
UNION ALL
SELECT 
    'transferable' as skill_status,
    COUNT(*) as skill_count,
    et.SkillType,
    et.Category,
    SUM(CASE WHEN et.is_defining = 1 THEN 1 ELSE 0 END) as defining_skills_count,
    SUM(CASE WHEN et.rarity_category = 'Rare' THEN 1 ELSE 0 END) as rare_skills_count,
    SUM(CASE WHEN et.velocity_category = 'emerging' THEN 1 ELSE 0 END) as emerging_skills_count,
    SUM(CASE WHEN et.velocity_category = 'declining' THEN 1 ELSE 0 END) as declining_skills_count,
    ROUND(AVG(et.rarity_score), 1) as avg_rarity_score
FROM enhanced_transferable et
GROUP BY et.SkillType, et.Category;

-- query_name: get_detailed_skills_analysis_for_api
-- Enhanced detailed skills analysis with defining skills, rarity, and velocity data
WITH job1_skills AS (
    SELECT jsr.Skill_ID, st.Skill_Name, st.Category, st.SkillType
    FROM core_job_skill_requirements jsr
    JOIN core_skills_taxonomy st ON jsr.Skill_ID = st.Skill_ID
    WHERE jsr.JobProfileID = ?
      AND st.Skill_Name IS NOT NULL
),
job2_skills AS (
    SELECT jsr.Skill_ID, st.Skill_Name, st.Category, st.SkillType
    FROM core_job_skill_requirements jsr
    JOIN core_skills_taxonomy st ON jsr.Skill_ID = st.Skill_ID
    WHERE jsr.JobProfileID = ?
      AND st.Skill_Name IS NOT NULL
)
SELECT 
    'matched' as status,
    j1.Skill_Name as skill_name,
    j1.Category as category,
    j1.SkillType as skill_type,
    COALESCE(ajds.defining_skill_rank, 999) as defining_rank,
    CASE WHEN ajds.defining_skill_rank IS NOT NULL THEN 1 ELSE 0 END as is_defining,
    COALESCE(asr.rarity_score, 50.0) as rarity_score,
    COALESCE(asr.rarity_category, 'Common') as rarity_category,
    COALESCE(asdt.velocity_category, 'stable') as velocity_category,
    COALESCE(asdt.trend_direction, 'stable') as trend_direction,
    COALESCE(asdt.trend_strength, 'stable') as trend_strength,
    COALESCE(st.infoUrl, '') as info_url
FROM job1_skills j1
INNER JOIN job2_skills j2 ON j1.Skill_ID = j2.Skill_ID
LEFT JOIN analytics_job_defining_skills ajds ON j1.Skill_ID = ajds.skill_id AND ajds.job_profile_id = ?
LEFT JOIN analytics_skill_rarity asr ON j1.Skill_ID = asr.skill_id
LEFT JOIN analytics_skill_demand_trends asdt ON j1.Skill_ID = asdt.skill_id
LEFT JOIN core_skills_taxonomy st ON j1.Skill_ID = st.Skill_ID
UNION ALL
SELECT 
    'develop' as status,
    st2.Skill_Name as skill_name,
    st2.Category as category,
    st2.SkillType as skill_type,
    COALESCE(ajds.defining_skill_rank, 999) as defining_rank,
    CASE WHEN ajds.defining_skill_rank IS NOT NULL THEN 1 ELSE 0 END as is_defining,
    COALESCE(asr.rarity_score, 50.0) as rarity_score,
    COALESCE(asr.rarity_category, 'Common') as rarity_category,
    COALESCE(asdt.velocity_category, 'stable') as velocity_category,
    COALESCE(asdt.trend_direction, 'stable') as trend_direction,
    COALESCE(asdt.trend_strength, 'stable') as trend_strength,
    COALESCE(st2.infoUrl, '') as info_url
FROM job2_skills j2
LEFT JOIN job1_skills j1 ON j2.Skill_ID = j1.Skill_ID
LEFT JOIN analytics_job_defining_skills ajds ON j2.Skill_ID = ajds.skill_id AND ajds.job_profile_id = ?
LEFT JOIN analytics_skill_rarity asr ON j2.Skill_ID = asr.skill_id
LEFT JOIN analytics_skill_demand_trends asdt ON j2.Skill_ID = asdt.skill_id
LEFT JOIN core_skills_taxonomy st2 ON j2.Skill_ID = st2.Skill_ID
WHERE j1.Skill_ID IS NULL
UNION ALL
SELECT 
    'transferable' as status,
    st3.Skill_Name as skill_name,
    st3.Category as category,
    st3.SkillType as skill_type,
    COALESCE(ajds.defining_skill_rank, 999) as defining_rank,
    CASE WHEN ajds.defining_skill_rank IS NOT NULL THEN 1 ELSE 0 END as is_defining,
    COALESCE(asr.rarity_score, 50.0) as rarity_score,
    COALESCE(asr.rarity_category, 'Common') as rarity_category,
    COALESCE(asdt.velocity_category, 'stable') as velocity_category,
    COALESCE(asdt.trend_direction, 'stable') as trend_direction,
    COALESCE(asdt.trend_strength, 'stable') as trend_strength,
    COALESCE(st3.infoUrl, '') as info_url
FROM job1_skills j1
LEFT JOIN job2_skills j2 ON j1.Skill_ID = j2.Skill_ID
LEFT JOIN analytics_job_defining_skills ajds ON j1.Skill_ID = ajds.skill_id AND ajds.job_profile_id = ?
LEFT JOIN analytics_skill_rarity asr ON j1.Skill_ID = asr.skill_id
LEFT JOIN analytics_skill_demand_trends asdt ON j1.Skill_ID = asdt.skill_id
LEFT JOIN core_skills_taxonomy st3 ON j1.Skill_ID = st3.Skill_ID
WHERE j2.Skill_ID IS NULL
ORDER BY status, 
         defining_rank ASC,  -- Defining skills first (lower rank = more important)
         rarity_score DESC,  -- Rare skills first within each group
         category, skill_name;