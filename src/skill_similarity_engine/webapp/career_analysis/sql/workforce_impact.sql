-- Workforce impact analysis queries
-- Get position counts by job profile
SELECT 
    JobProfileID,
    COUNT(*) as position_count,
    Division,
    Business_Unit,
    Location
FROM positions 
WHERE JobProfileID = ?
GROUP BY JobProfileID, Division, Business_Unit, Location;
