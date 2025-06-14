# SQLite Schema Design for NAB Skill Similarity Engine
## Business Context Database

**Generated**: 2025-06-14 10:45:50
**Database File**: `C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\models\2025-Q2\business_context.sqlite`
**Database Size**: 80.89 MB
**Last Modified**: 2025-06-13T18:36:22.382150

---

## Overview

This document provides comprehensive schema documentation for the NAB Skill Similarity Engine SQLite database.
The database integrates job architecture, skill taxonomies, workforce context, and pre-computed similarities
to support career pathway analysis and workforce planning.

## Quick Reference for LLMs

**Core Tables for Query Development:**

- **`career_pathways`** (8,580 records) - source_job_id, target_job_id, similarity_rank, similarity_score, career_move_type
- **`job_similarities`** (510,510 records) - job_from, job_to, similarity_score
- **`job_skills`** (40,170 records) - JobProfileID, Skill_ID, Skill_Weight
- **`jobs`** (715 records) - JobProfileID, JobProfile, JobFamily, JobFamilyGroup
- **`positions`** (5,000 records) - JobProfileID, Division, Business_Unit, Location, Team
- **`skills`** (38,395 records) - Skill_ID, Skill_Name, Category, SkillType

**Key Relationships:**
- `jobs.JobProfileID` → `career_pathways.source_job_id/target_job_id`
- `jobs.JobProfileID` → `job_similarities.job_from/job_to`
- `jobs.JobProfileID` → `positions.JobProfileID`
- `jobs.JobProfileID` → `job_skills.JobProfileID`
- `skills.Skill_ID` → `job_skills.Skill_ID`

**Critical for D3 Tree Queries:**
- Use `career_pathways` table for pre-computed relationships (fast!)
- `similarity_rank` 1-12 gives top pathways per job
- `career_move_type`: 'lateral', 'progression', 'cross_family'
- Handle quoted column names: `"Position Number"`, `"Business_Unit"`

---

## Database Statistics

- **Total Tables**: 7
- **Total Records**: 603,374
- **Total Indexes**: 18
- **Database Size**: 80.89 MB

## Entity Relationship Diagram

```mermaid
erDiagram
    CAREER_PATHWAYS {
        text source_job_id PK FK
        text target_job_id PK FK
        integer similarity_rank
        real similarity_score
        real skill_overlap_score
        integer shared_skills_count
        text career_move_type
        real difficulty_score
    }

    JOB_SIMILARITIES {
        text job_from PK FK
        text job_to PK FK
        real similarity_score
        real skill_overlap_score
        integer shared_skills_count
        integer total_skills_from
        integer total_skills_to
    }

    JOB_SKILLS {
        text JobProfileID PK FK
        text Skill_ID PK FK
        real Skill_Weight
    }

    JOBS {
        text JobProfileID PK
        text JobProfile
        text JobID
        text Job
        text JobFamily
        text JobFamilyGroup
    }

    POSITIONS {
        text Position Number PK
        text JobProfileID FK
        text Employee Number
        text Division
        text Business_Unit
        text Team
        text SubTeam
        text Function
        text SubFunction
        text Org_Level_8
        text Org_Level_9
        text Org_Level_10
        text Location
        text Rg
        text Cty
        text Employee Group
        text Salary Group
        text Employee Subgroup
    }

    SCHEMA_METADATA {
        text key PK
        text value
        text created_at
    }

    SKILLS {
        text Skill_ID PK
        text Skill_Name
        text Category
        text Subcategory
        text SkillType
        text Latest_Version
        text Description
        text Info_URL
        boolean Is_Language
        integer Category_ID
        integer Subcategory_ID
        text Type_ID
        text Market_Demand
        real Rarity_Score
    }

    JOBS ||--o{ CAREER_PATHWAYS : "target_job_id"
    JOBS ||--o{ CAREER_PATHWAYS : "source_job_id"
    JOBS ||--o{ JOB_SIMILARITIES : "job_to"
    JOBS ||--o{ JOB_SIMILARITIES : "job_from"
    SKILLS ||--o{ JOB_SKILLS : "Skill_ID"
    JOBS ||--o{ JOB_SKILLS : "JobProfileID"
    JOBS ||--o{ POSITIONS : "JobProfileID"
```

---

## Table Definitions

### 1. **career_pathways** - 8,580 records

```sql
CREATE TABLE career_pathways (
    source_job_id TEXT NOT NULL PRIMARY KEY,
    target_job_id TEXT NOT NULL PRIMARY KEY,
    similarity_rank INTEGER NOT NULL,
    similarity_score REAL NOT NULL,
    skill_overlap_score REAL,
    shared_skills_count INTEGER,
    career_move_type TEXT,
    difficulty_score REAL
);
```

**Foreign Key Relationships:**

- `target_job_id` → `jobs.JobProfileID`
- `source_job_id` → `jobs.JobProfileID`

**Key Column Statistics:**

- **source_job_id**: 715 unique values, avg length 7.0
- **target_job_id**: 699 unique values, avg length 7.0
- **similarity_rank**: 12 unique values, range 1 - 12
- **similarity_score**: Range 0.1389 - 1.0000, avg 0.6641
- **skill_overlap_score**: Range 0.1389 - 1.0000, avg 0.6641
- **shared_skills_count**: 17 unique values, range 2 - 20
- **career_move_type**: 2 unique values, avg length 9.98
- **difficulty_score**: Range 0.0000 - 0.8611, avg 0.3359

**Sample Records:**

- `source_job_id`: R0001.5
- `target_job_id`: R0001.6
- `similarity_rank`: 1
- `similarity_score`: 1.0
- `skill_overlap_score`: 1.0
- `shared_skills_count`: 20
- `career_move_type`: lateral
- `difficulty_score`: 0.0

---

### 2. **job_similarities** - 510,510 records

```sql
CREATE TABLE job_similarities (
    job_from TEXT NOT NULL PRIMARY KEY,
    job_to TEXT NOT NULL PRIMARY KEY,
    similarity_score REAL NOT NULL,
    skill_overlap_score REAL,
    shared_skills_count INTEGER,
    total_skills_from INTEGER,
    total_skills_to INTEGER
);
```

**Foreign Key Relationships:**

- `job_to` → `jobs.JobProfileID`
- `job_from` → `jobs.JobProfileID`

**Key Column Statistics:**

- **job_from**: 715 unique values, avg length 7.0
- **job_to**: 715 unique values, avg length 7.0
- **similarity_score**: Range 0.0000 - 1.0000, avg 0.3419
- **skill_overlap_score**: Range 0.0000 - 0.0000, avg 0.0000
- **shared_skills_count**: 0 unique values, range 0 - 0
- **total_skills_from**: 0 unique values, range 0 - 0
- **total_skills_to**: 0 unique values, range 0 - 0

**Sample Records:**

- `job_from`: R0001.5
- `job_to`: R0001.6
- `similarity_score`: 1.0

---

### 3. **job_skills** - 40,170 records

```sql
CREATE TABLE job_skills (
    JobProfileID TEXT NOT NULL PRIMARY KEY,
    Skill_ID TEXT NOT NULL PRIMARY KEY,
    Skill_Weight REAL DEFAULT 1.0
);
```

**Foreign Key Relationships:**

- `Skill_ID` → `skills.Skill_ID`
- `JobProfileID` → `jobs.JobProfileID`

**Key Column Statistics:**

- **JobProfileID**: 715 unique values, avg length 7.0
- **Skill_ID**: 2,091 unique values, avg length 20.0
- **Skill_Weight**: Range 1.0000 - 1.0000, avg 1.0000

**Sample Records:**

- `JobProfileID`: R0001.5
- `Skill_ID`: BGSD16A8EEF4F5775E15
- `Skill_Weight`: 1.0

---

### 4. **jobs** - 715 records

```sql
CREATE TABLE jobs (
    JobProfileID TEXT PRIMARY KEY,
    JobProfile TEXT NOT NULL,
    JobID TEXT,
    Job TEXT,
    JobFamily TEXT,
    JobFamilyGroup TEXT
);
```

**Key Column Statistics:**

- **JobProfileID**: 715 unique values, avg length 7.0
- **JobProfile**: 336 unique values, avg length 33.44
- **JobID**: 240 unique values, avg length 5.0
- **Job**: 53 unique values, avg length 19.98
- **JobFamily**: 8 unique values, avg length 19.06
- **JobFamilyGroup**: 7 unique values, avg length 14.76

**Sample Records:**

- `JobProfileID`: R0001.5
- `JobProfile`: Analyst - Data Governance Specialist
- `JobID`: J0001
- `Job`: Data Governance Specialist
- `JobFamily`: Data & Analytics
- `JobFamilyGroup`: Technology

---

### 5. **positions** - 5,000 records

```sql
CREATE TABLE positions (
    Position Number TEXT PRIMARY KEY,
    JobProfileID TEXT,
    Employee Number TEXT,
    Division TEXT,
    Business_Unit TEXT,
    Team TEXT,
    SubTeam TEXT,
    Function TEXT,
    SubFunction TEXT,
    Org_Level_8 TEXT,
    Org_Level_9 TEXT,
    Org_Level_10 TEXT,
    Location TEXT,
    Rg TEXT,
    Cty TEXT,
    Employee Group TEXT,
    Salary Group TEXT,
    Employee Subgroup TEXT
);
```

**Foreign Key Relationships:**

- `JobProfileID` → `jobs.JobProfileID`

**Key Column Statistics:**

- **Position Number**: 5,000 unique values, avg length 8.0
- **JobProfileID**: 628 unique values, avg length 7.0
- **Employee Number**: 3,501 unique values, avg length 5.6
- **Division**: 6 unique values, avg length 20.27
- **Business_Unit**: 10 unique values, avg length 14.4
- **Team**: 10 unique values, avg length 24.52
- **SubTeam**: 30 unique values, avg length 7.0
- **Function**: 26 unique values, avg length 7.0
- **SubFunction**: 20 unique values, avg length 5.54
- **Org_Level_8**: 50 unique values, avg length 8.0
- **Org_Level_9**: 30 unique values, avg length 7.0
- **Org_Level_10**: 100 unique values, avg length 8.0
- **Location**: 6 unique values, avg length 8.51
- **Rg**: 5 unique values, avg length 2.66
- **Cty**: 1 unique values, avg length 2.0
- **Employee Group**: 5 unique values, avg length 6.15
- **Salary Group**: 9 unique values, avg length 7.0
- **Employee Subgroup**: 4 unique values, avg length 5.6

**Sample Records:**

- `Position Number`: 50000000
- `JobProfileID`: R0453.0
- `Employee Number`: 102031.0
- `Division`: Technology
- `Business_Unit`: Corporate Banking
- `Team`: Wealth Management Operations
- `SubTeam`: Team 20
- `Function`: Squad D
- `SubFunction`: Pod 18
- `Org_Level_8`: Unit 047
- `Org_Level_9`: Cell 12
- `Org_Level_10`: Node 060
- `Location`: Adelaide
- `Rg`: SA
- `Cty`: AU
- `Employee Group`: Casual
- `Salary Group`: Group 7
- `Employee Subgroup`: Part Time

---

### 6. **schema_metadata** - 4 records

```sql
CREATE TABLE schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

**Key Column Statistics:**

- **key**: 4 unique values, avg length 12.0
- **value**: 4 unique values, avg length 27.5
- **created_at**: 1 unique values, avg length 26.0

**Sample Records:**

- `key`: schema_version
- `value`: 1.0
- `created_at`: 2025-06-13T18:36:07.482003

---

### 7. **skills** - 38,395 records

```sql
CREATE TABLE skills (
    Skill_ID TEXT PRIMARY KEY,
    Skill_Name TEXT NOT NULL,
    Category TEXT,
    Subcategory TEXT,
    SkillType TEXT,
    Latest_Version TEXT,
    Description TEXT,
    Info_URL TEXT,
    Is_Language BOOLEAN,
    Category_ID INTEGER,
    Subcategory_ID INTEGER,
    Type_ID TEXT,
    Market_Demand TEXT,
    Rarity_Score REAL
);
```

**Key Column Statistics:**

- **Skill_ID**: 38,395 unique values, avg length 20.0
- **Skill_Name**: 38,395 unique values, avg length 19.68
- **Category**: 29 unique values, avg length 0.2
- **Subcategory**: 191 unique values, avg length 0.23
- **SkillType**: 4 unique values, avg length 1.64
- **Latest_Version**: 48 unique values, avg length 3.98
- **Description**: 2,422 unique values, avg length 24.08
- **Info_URL**: 3,731 unique values, avg length 5.83
- **Category_ID**: 29 unique values, range 0 - 0
- **Subcategory_ID**: 187 unique values, range 100 - 0
- **Type_ID**: 4 unique values, avg length 0.29
- **Market_Demand**: 1 unique values, avg length 0
- **Rarity_Score**: Range 0.0000 - 0.0000, avg 0.0000

**Sample Records:**

- `Skill_ID`: BGS1024316C916ACCFA3
- `Skill_Name`: DX Spectrum
- `Category`: Information Technology
- `Subcategory`: Enterprise Information Management
- `SkillType`: Specialized Skill
- `Latest_Version`: 8.5
- `Description`: 
- `Info_URL`: https://lightcast.io/open-skills/skills/BGS1024...
- `Is_Language`: 0
- `Category_ID`: 17
- `Subcategory_ID`: 411
- `Type_ID`: ST1
- `Market_Demand`: 
- `Rarity_Score`: 

---

## Key Data Distributions

Top values for important categorical columns:

### jobs.JobFamily

- **Banking Operations**: 101 records
- **Data & Analytics**: 99 records
- **Finance & Accounting**: 98 records
- **Human Resources**: 94 records
- **Executive Leadership**: 88 records
- **Customer Service & Sales**: 81 records
- **Risk & Compliance**: 78 records
- **Technology & Engineering**: 76 records

### jobs.JobFamilyGroup

- **Technology**: 175 records
- **Operations**: 101 records
- **Finance**: 98 records
- **Support Functions**: 94 records
- **Executive & Leadership**: 88 records
- **Customer & Commercial**: 81 records
- **Risk & Control Functions**: 78 records

### positions.Division

- **Business & Private Banking**: 876 records
- **Group Functions**: 854 records
- **Customer Banking & Wealth**: 832 records
- **Corporate & Institutional Banking**: 825 records
- **NAB Ventures**: 813 records
- **Technology**: 800 records

### positions.Business_Unit

- **Legal & Compliance**: 536 records
- **Human Resources**: 521 records
- **NAB Ventures**: 512 records
- **Business Banking**: 506 records
- **Corporate Banking**: 505 records
- **Personal Banking**: 499 records
- **Risk Management**: 496 records
- **Wealth Management**: 489 records
- **Technology**: 474 records
- **Finance**: 462 records

### positions.Location

- **Perth**: 896 records
- **Brisbane City**: 863 records
- **Parramatta**: 826 records
- **Docklands**: 819 records
- **Adelaide**: 811 records
- **Sydney**: 785 records

### skills.Category

- **Information Technology**: 168 records
- **Health Care**: 57 records
- **Business**: 15 records
- **Administration**: 14 records
- **Engineering**: 14 records
- **Physical and Inherent Abilities**: 13 records
- **Analysis**: 12 records
- **Customer and Client Support**: 12 records
- **Design**: 12 records
- **Marketing and Public Relations**: 11 records

### skills.SkillType

- **Specialized Skill**: 3,639 records
- **Certification**: 66 records
- **Common Skill**: 25 records

### career_pathways.career_move_type

- **progression**: 6,382 records
- **lateral**: 2,198 records

## Database Indexes

Performance indexes for optimized queries:

### career_pathways table indexes

**idx_career_pathways_move_type**
```sql
CREATE INDEX idx_career_pathways_move_type ON career_pathways(career_move_type, similarity_score DESC)
```

**idx_career_pathways_rank**
```sql
CREATE INDEX idx_career_pathways_rank ON career_pathways(similarity_rank, similarity_score DESC)
```

**idx_career_pathways_source**
```sql
CREATE INDEX idx_career_pathways_source ON career_pathways(source_job_id, similarity_rank)
```

**idx_career_pathways_target**
```sql
CREATE INDEX idx_career_pathways_target ON career_pathways(target_job_id, similarity_rank)
```

### job_similarities table indexes

**idx_similarities_from**
```sql
CREATE INDEX idx_similarities_from ON job_similarities(job_from, similarity_score DESC)
```

**idx_similarities_score**
```sql
CREATE INDEX idx_similarities_score ON job_similarities(similarity_score DESC)
```

**idx_similarities_to**
```sql
CREATE INDEX idx_similarities_to ON job_similarities(job_to, similarity_score DESC)
```

### job_skills table indexes

**idx_job_skills_job**
```sql
CREATE INDEX idx_job_skills_job ON job_skills(JobProfileID)
```

**idx_job_skills_skill**
```sql
CREATE INDEX idx_job_skills_skill ON job_skills(Skill_ID)
```

### jobs table indexes

**idx_jobs_family**
```sql
CREATE INDEX idx_jobs_family ON jobs(JobFamily)
```

**idx_jobs_family_group**
```sql
CREATE INDEX idx_jobs_family_group ON jobs(JobFamilyGroup)
```

### positions table indexes

**idx_positions_business_unit**
```sql
CREATE INDEX idx_positions_business_unit ON positions(Business_Unit)
```

**idx_positions_division**
```sql
CREATE INDEX idx_positions_division ON positions(Division)
```

**idx_positions_function**
```sql
CREATE INDEX idx_positions_function ON positions(Function)
```

**idx_positions_job_profile**
```sql
CREATE INDEX idx_positions_job_profile ON positions(JobProfileID)
```

**idx_positions_location**
```sql
CREATE INDEX idx_positions_location ON positions(Location, Rg)
```

**idx_positions_team**
```sql
CREATE INDEX idx_positions_team ON positions(Team)
```

### skills table indexes

**idx_skills_category**
```sql
CREATE INDEX idx_skills_category ON skills(Category, Subcategory)
```

## Common Query Patterns

### 1. Career Pathway Exploration
```sql
-- Find similar roles with high similarity scores
SELECT j2.JobProfile, js.similarity_score, j2.JobFamily
FROM job_similarities js
JOIN jobs j1 ON js.job_from = j1.JobProfileID
JOIN jobs j2 ON js.job_to = j2.JobProfileID
WHERE j1.JobProfileID = 'R0001.1'
  AND js.similarity_score > 0.7
ORDER BY js.similarity_score DESC
LIMIT 10;
```

### 2. Skills Gap Analysis
```sql
-- Compare skills between two jobs
SELECT s.Skill_Name, s.Category,
       source_skills.Skill_Weight as current_weight,
       target_skills.Skill_Weight as target_weight
FROM skills s
LEFT JOIN job_skills source_skills ON s.Skill_ID = source_skills.Skill_ID
  AND source_skills.JobProfileID = 'R0001.1'
LEFT JOIN job_skills target_skills ON s.Skill_ID = target_skills.Skill_ID
  AND target_skills.JobProfileID = 'R0002.1'
WHERE source_skills.Skill_ID IS NOT NULL
   OR target_skills.Skill_ID IS NOT NULL
ORDER BY s.Category, s.Skill_Name;
```

### 3. Organizational Context
```sql
-- Find roles in specific business units
SELECT DISTINCT j.JobProfile, j.JobFamily, COUNT(p."Position Number") as position_count
FROM jobs j
JOIN positions p ON j.JobProfileID = p.JobProfileID
WHERE p.Business_Unit = 'Technology'
GROUP BY j.JobProfileID, j.JobProfile, j.JobFamily
ORDER BY position_count DESC;
```

### 4. Career Pathways (Pre-computed)
```sql
-- Get career pathway options using pre-computed table
SELECT j.JobProfile, cp.similarity_score, cp.career_move_type, cp.difficulty_score
FROM career_pathways cp
JOIN jobs j ON cp.target_job_id = j.JobProfileID
WHERE cp.source_job_id = 'R0001.1'
  AND cp.similarity_score > 0.6
ORDER BY cp.similarity_rank
LIMIT 12;
```

---

## Schema Evolution Notes

- **Version**: Current schema represents production-ready structure
- **Performance**: Optimized for webapp queries with appropriate indexes
- **Scalability**: Handles current data volumes efficiently
- **Future Extensions**: Schema designed for additive changes

## Usage in Development

This schema documentation should be used to:
1. **Inform LLMs** about database structure and relationships
2. **Guide query development** for webapp endpoints
3. **Validate data integrity** during pipeline updates
4. **Plan schema evolution** for future requirements

**Last Updated**: 2025-06-14 10:45:50