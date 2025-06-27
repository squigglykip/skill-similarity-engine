-- Skills gap calculation queries
-- Get skills for source job
SELECT Skill_ID, Skill_Name 
FROM job_skills js
INNER JOIN skills s ON js.Skill_ID = s.Skill_ID
WHERE js.JobProfileID = ?;
