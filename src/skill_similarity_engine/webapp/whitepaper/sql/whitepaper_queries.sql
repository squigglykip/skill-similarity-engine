-- Core white paper data queries
-- Skills gap analysis between two jobs
SELECT 
    js1.Skill_Name as shared_skill
FROM job_skills js1
INNER JOIN job_skills js2 ON js1.Skill_ID = js2.Skill_ID
WHERE js1.JobProfileID = ? AND js2.JobProfileID = ?;
