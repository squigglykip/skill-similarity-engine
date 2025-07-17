# SQLite Schema Design for NAB Skill Similarity Engine
## Workforce Intelligence Database

**Generated**: 2025-07-17 14:45:38
**Database File**: `c:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\models\2025-Q3\workforce_intelligence.sqlite`
**Database Size**: 211.6 MB
**SQLite Version**: 3.45.3
**Page Size**: 4096 bytes
**Total Pages**: 54,170
**Foreign Keys**: Disabled
**Last Modified**: 2025-07-17T14:42:49.919399

---

## Overview

This document provides comprehensive schema documentation for the NAB Skill Similarity Engine SQLite database.
The database integrates job architecture, skill taxonomies, workforce context, movement analysis, and pre-computed similarities
to support career pathway analysis, workforce planning, and strategic workforce intelligence.

## Quick Reference for LLMs

**Core Tables for Query Development:**

- **`career_pathways`** (8,580 records) - source_job_id, target_job_id, similarity_rank, similarity_score, career_move_type
- **`colleague_movements`** (162,954 records) - employee_number, jobprofile_id, movement_type, movement_date
- **`job_similarities`** (510,510 records) - job_from, job_to, similarity_score
- **`job_skills`** (40,170 records) - JobProfileID, Skill_ID, Skill_Weight
- **`jobs`** (715 records) - JobProfileID, JobProfile, JobFamily, JobFamilyGroup
- **`movement_fact`** (162,941 records) - movement_pattern, movement_count, month, avg_days_in_position
- **`positions`** (35,000 records) - JobProfileID, Division, Business_Unit, Location, Team
- **`skills`** (38,430 records) - Skill_ID, Skill_Name, Category, SkillType

**Key Relationships:**
- `jobs.JobProfileID` â†’ `career_pathways.source_job_id/target_job_id`
- `jobs.JobProfileID` â†’ `job_similarities.job_from/job_to`
- `jobs.JobProfileID` â†’ `positions.JobProfileID`
- `jobs.JobProfileID` â†’ `job_skills.JobProfileID`
- `skills.Skill_ID` â†’ `job_skills.Skill_ID`

**Critical for D3 Tree Queries:**
- Use `career_pathways` table for pre-computed relationships (fast!)
- `similarity_rank` 1-12 gives top pathways per job
- `career_move_type`: 'lateral', 'progression', 'cross_family'
- Handle quoted column names: `"Position Number"`, `"Business_Unit"`

---

## Database Statistics

- **Total Tables**: 11
- **Total Records**: 1,594,304
- **Total Indexes**: 21
- **Database Size**: 211.6 MB

### Key Business Metrics


### Movement Analysis Summary

- **Total Movements Tracked**: 162,954
- **Movement Types**:
  - lateral: 162,954

### Career Pathways Summary

- **Total Career Pathways**: 8,580
- **Pathway Types**:
  - progression: 6,382 pathways (avg similarity: 0.5489)
  - lateral: 2,198 pathways (avg similarity: 0.9987)

## Relationship Analysis

### Foreign Key Relationships (9)

- `career_pathways.target_job_id` → `jobs.JobProfileID`
- `career_pathways.source_job_id` → `jobs.JobProfileID`
- `colleague_movements.jobprofile_id` → `jobs.JobProfileID`
- `colleague_movements.employee_number` → `positions.Employee Number`
- `job_similarities.job_to` → `jobs.JobProfileID`
- `job_similarities.job_from` → `jobs.JobProfileID`
- `job_skills.Skill_ID` → `skills.Skill_ID`
- `job_skills.JobProfileID` → `jobs.JobProfileID`
- `positions.JobProfileID` → `jobs.JobProfileID`

### Referential Integrity Check

- ✅ **career_pathways.target_job_id**: No orphaned records
- ✅ **career_pathways.source_job_id**: No orphaned records
- ⚠️ **colleague_movements.jobprofile_id**: 162954 orphaned records
- ⚠️ **colleague_movements.employee_number**: 162954 orphaned records
- ✅ **job_similarities.job_to**: No orphaned records
- ✅ **job_similarities.job_from**: No orphaned records
- ⚠️ **job_skills.Skill_ID**: 125 orphaned records
- ✅ **job_skills.JobProfileID**: No orphaned records
- ⚠️ **positions.JobProfileID**: 35000 orphaned records

## Performance Analysis

### Table Size Categories

**Small Tables:**
- jobs: 715 rows
- schema_metadata: 4 rows

**Medium Tables:**
- career_pathways: 8,580 rows
- job_skills: 40,170 rows
- positions: 35,000 rows
- skills: 38,430 rows
- workforce_context: 35,000 rows

**Large Tables:**
- colleague_movements: 162,954 rows
- job_similarities: 510,510 rows
- movement_fact: 162,941 rows
- position_history: 600,000 rows

### Query Optimization Recommendations

- **indexing**: Large table (162,941 rows) with minimal indexing
  - Recommendation: Consider adding indexes on frequently queried columns
- **indexing**: Large table (600,000 rows) with minimal indexing
  - Recommendation: Consider adding indexes on frequently queried columns
- **indexing**: Large table (38,430 rows) with minimal indexing
  - Recommendation: Consider adding indexes on frequently queried columns
- **indexing**: Large table (35,000 rows) with minimal indexing
  - Recommendation: Consider adding indexes on frequently queried columns

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

    COLLEAGUE_MOVEMENTS {
        integer movement_id PK
        text employee_number FK
        text jobprofile_id FK
        text movement_type
        date movement_date
        date effective_date
        date end_date
        text change_reason
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
        text ProfileTitleSuffix
        text ManagementLevel
        text JobSubFunctionID
        text JobSubFunction
        text JobFunctionID
        text JobFunction
        text JobCategoryID
        text JobCategory
        text Customer_Facing
        text is_Banker
        text Executive_Leadership_Group
        text Accountability_Scope
    }

    MOVEMENT_FACT {
        integer fact_id PK
        text movement_month
        integer movement_year
        text from_position
        text to_position
        text movement_pattern
        integer movement_count
        real pct_total_movements
        integer unique_employees
        real avg_days_between
        integer monthly_total_movements
        text predominant_movement_type
    }

    POSITION_HISTORY {
        date week_ending
        text position_number
        text position_id_lookup_key
        text organisational_unit
        text cost_centre_number
        text position_title
        text people_leader
        text operational
        text org_unit_id_lookup_key
    }

    POSITIONS {
        text Employee_Number PK
        text Position_Number
        text Position_Name
        text JobProfileID FK
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
        text Employee_Group
        text Salary_Group
        text Employee_Subgroup
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
        integer category_id
        text description
        text descriptionSource
        text Info_URL
        boolean Is_Language
        boolean isSoftware
        integer subcategory_id
        text tag_wikipediaExtract
        text tag_wikipediaUrl
        text tags
        text type_id
        text type_name
        text Market_Demand
        real Rarity_Score
    }

    WORKFORCE_CONTEXT {
        date week_ending
        text position_number
        text position_name
        text employee_number
        text employee_name
        text location
        text region
        text country
        text employee_group
        text salary_group
        text division
        text business_unit
        text team
        text sub_team
        text function
        text sub_function
        text org_level_8
        text org_level_9
        text org_level_10
    }

    JOBS ||--o{ CAREER_PATHWAYS : "target_job_id"
    JOBS ||--o{ CAREER_PATHWAYS : "source_job_id"
    JOBS ||--o{ COLLEAGUE_MOVEMENTS : "jobprofile_id"
    POSITIONS ||--o{ COLLEAGUE_MOVEMENTS : "employee_number"
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

- `target_job_id` â†’ `jobs.JobProfileID`
- `source_job_id` â†’ `jobs.JobProfileID`

**Column Statistics:**

- **source_job_id**: 715 unique values (8,580 non-null), avg length 7.0
- **target_job_id**: 699 unique values (8,580 non-null), avg length 7.0
- **similarity_rank**: 12 unique values (8,580 non-null), range 1 - 12
- **similarity_score**: 325 unique values (8,580 non-null), range 0.1389 - 1.0000, avg 0.6641
- **skill_overlap_score**: 325 unique values (8,580 non-null), range 0.1389 - 1.0000, avg 0.6641
- **shared_skills_count**: 17 unique values (8,580 non-null), range 2 - 20
- **career_move_type**: 2 unique values (8,580 non-null), avg length 9.98
- **difficulty_score**: 325 unique values (8,580 non-null), range 0.0000 - 0.8611, avg 0.3359

**Data Quality - Completeness:**

- **source_job_id**: 100% complete
- **target_job_id**: 100% complete
- **similarity_rank**: 100% complete
- **similarity_score**: 100% complete
- **skill_overlap_score**: 100% complete
- **shared_skills_count**: 100% complete
- **career_move_type**: 100% complete
- **difficulty_score**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **source_job_id**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **target_job_id**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **similarity_rank**: `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`
- **similarity_score**: `0.1388888888888889`, `0.1666666666666666`, `0.1875`, `0.2058823529411764`, `0.21875`, `0.2195121951219512`, `0.2222222222222222`, `0.2307692307692307`, `0.2352941176470588`, `0.2368421052631578`
- **skill_overlap_score**: `0.1388888888888889`, `0.1666666666666666`, `0.1875`, `0.2058823529411764`, `0.21875`, `0.2195121951219512`, `0.2222222222222222`, `0.2307692307692307`, `0.2352941176470588`, `0.2368421052631578`
- **shared_skills_count**: `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `11`
- **career_move_type**: `lateral`, `progression`
- **difficulty_score**: `0.0`, `0.13953488372093026`, `0.18604651162790697`, `0.19512195121951215`, `0.19999999999999996`, `0.20408163265306123`, `0.20454545454545459`, `0.2093023255813954`, `0.21568627450980393`, `0.21999999999999997`

**Sample Complete Records:**

**Record 1:**
  - `source_job_id`: R0181.3
  - `target_job_id`: R0181.2
  - `similarity_rank`: 1
  - `similarity_score`: 1.0
  - `skill_overlap_score`: 1.0
  - `shared_skills_count`: 20
  - `career_move_type`: lateral
  - `difficulty_score`: 0.0

**Record 2:**
  - `source_job_id`: R0181.3
  - `target_job_id`: R0116.4
  - `similarity_rank`: 2
  - `similarity_score`: 0.5084745762711864
  - `skill_overlap_score`: 0.5084745762711864
  - `shared_skills_count`: 10
  - `career_move_type`: progression
  - `difficulty_score`: 0.4915254237288136

**Record 3:**
  - `source_job_id`: R0181.3
  - `target_job_id`: R0116.3
  - `similarity_rank`: 3
  - `similarity_score`: 0.5084745762711864
  - `skill_overlap_score`: 0.5084745762711864
  - `shared_skills_count`: 10
  - `career_move_type`: progression
  - `difficulty_score`: 0.4915254237288136

---

### 2. **colleague_movements** - 162,954 records

```sql
CREATE TABLE colleague_movements (
    movement_id INTEGER PRIMARY KEY,
    employee_number TEXT NOT NULL,
    jobprofile_id TEXT NOT NULL,
    movement_type TEXT NOT NULL,
    movement_date DATE NOT NULL,
    effective_date DATE NOT NULL,
    end_date DATE,
    change_reason TEXT
);
```

**Foreign Key Relationships:**

- `jobprofile_id` â†’ `jobs.JobProfileID`
- `employee_number` â†’ `positions.Employee Number`

**Column Statistics:**

- **movement_id**: 162,954 unique values (162,954 non-null), range 1 - 162954
- **employee_number**: 118,248 unique values (162,954 non-null), avg length 8.58
- **jobprofile_id**: 4,996 unique values (162,954 non-null), avg length 8.0
- **movement_type**: 1 unique values (162,954 non-null), avg length 7.0
- **change_reason**: 1 unique values (162,954 non-null), avg length 18.0

**Data Quality - Completeness:**

- **movement_id**: 100% complete
- **employee_number**: 100% complete
- **jobprofile_id**: 100% complete
- **movement_type**: 100% complete
- **movement_date**: 100% complete
- **effective_date**: 100% complete
- **end_date**: 100% complete
- **change_reason**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **movement_id**: `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`
- **employee_number**: `100000040`, `100000636`, `100001456`, `100002973`, `100003410`, `100004179`, `100004925`, `100005439`, `100005557`, `100006134`
- **jobprofile_id**: `50000000`, `50000001`, `50000002`, `50000003`, `50000004`, `50000005`, `50000006`, `50000007`, `50000008`, `50000009`
- **movement_type**: `lateral`
- **movement_date**: `2021-07-08`, `2021-07-15`, `2021-07-22`, `2021-07-29`, `2021-08-05`, `2021-08-12`, `2021-08-19`, `2021-08-26`, `2021-09-02`, `2021-09-09`
- **effective_date**: `2021-07-08`, `2021-07-15`, `2021-07-22`, `2021-07-29`, `2021-08-05`, `2021-08-12`, `2021-08-19`, `2021-08-26`, `2021-09-02`, `2021-09-09`
- **end_date**: `2021-07-01`, `2021-07-08`, `2021-07-15`, `2021-07-22`, `2021-07-29`, `2021-08-05`, `2021-08-12`, `2021-08-19`, `2021-08-26`, `2021-09-02`
- **change_reason**: `Career Progression`

**Sample Complete Records:**

**Record 1:**
  - `movement_id`: 1
  - `employee_number`: 56458214
  - `jobprofile_id`: 50000271
  - `movement_type`: lateral
  - `movement_date`: 2022-06-02
  - `effective_date`: 2022-06-02
  - `end_date`: 2022-05-05
  - `change_reason`: Career Progression

**Record 2:**
  - `movement_id`: 2
  - `employee_number`: 56459636
  - `jobprofile_id`: 50003458
  - `movement_type`: lateral
  - `movement_date`: 2021-08-19
  - `effective_date`: 2021-08-19
  - `end_date`: 2021-07-08
  - `change_reason`: Career Progression

**Record 3:**
  - `movement_id`: 3
  - `employee_number`: 56461657
  - `jobprofile_id`: 50001953
  - `movement_type`: lateral
  - `movement_date`: 2021-11-18
  - `effective_date`: 2021-11-18
  - `end_date`: 2021-09-02
  - `change_reason`: Career Progression

---

### 3. **job_similarities** - 510,510 records

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

- `job_to` â†’ `jobs.JobProfileID`
- `job_from` â†’ `jobs.JobProfileID`

**Column Statistics:**

- **job_from**: 715 unique values (510,510 non-null), avg length 7.0
- **job_to**: 715 unique values (510,510 non-null), avg length 7.0
- **similarity_score**: 1,106 unique values (510,510 non-null), range 0.0000 - 1.0000, avg 0.3419
- **skill_overlap_score**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **shared_skills_count**: 0 unique values (0 non-null), range 0 - 0
- **total_skills_from**: 0 unique values (0 non-null), range 0 - 0
- **total_skills_to**: 0 unique values (0 non-null), range 0 - 0

**Data Quality - Completeness:**

- **job_from**: 100% complete
- **job_to**: 100% complete
- **similarity_score**: 100% complete
- **skill_overlap_score**: 0.0% complete (510,510 null values)
- **shared_skills_count**: 0.0% complete (510,510 null values)
- **total_skills_from**: 0.0% complete (510,510 null values)
- **total_skills_to**: 0.0% complete (510,510 null values)

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **job_from**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **job_to**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **similarity_score**: `0.0`, `0.0104166666666666`, `0.0106382978723404`, `0.0123456790123456`, `0.0125`, `0.0129870129870129`, `0.0131578947368421`, `0.0133333333333333`, `0.0136986301369863`, `0.0140845070422535`

**Sample Complete Records:**

**Record 1:**
  - `job_from`: R0001.5
  - `job_to`: R0001.6
  - `similarity_score`: 1.0

**Record 2:**
  - `job_from`: R0001.5
  - `job_to`: R0002.0
  - `similarity_score`: 0.3529411764705882

**Record 3:**
  - `job_from`: R0001.5
  - `job_to`: R0002.1
  - `similarity_score`: 0.3529411764705882

---

### 4. **job_skills** - 40,170 records

```sql
CREATE TABLE job_skills (
    JobProfileID TEXT NOT NULL PRIMARY KEY,
    Skill_ID TEXT NOT NULL PRIMARY KEY,
    Skill_Weight REAL DEFAULT 1.0
);
```

**Foreign Key Relationships:**

- `Skill_ID` â†’ `skills.Skill_ID`
- `JobProfileID` â†’ `jobs.JobProfileID`

**Column Statistics:**

- **JobProfileID**: 715 unique values (40,170 non-null), avg length 7.0
- **Skill_ID**: 2,091 unique values (40,170 non-null), avg length 20.0
- **Skill_Weight**: 1 unique values (40,170 non-null), range 1.0000 - 1.0000, avg 1.0000

**Data Quality - Completeness:**

- **JobProfileID**: 100% complete
- **Skill_ID**: 100% complete
- **Skill_Weight**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **JobProfileID**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **Skill_ID**: `BGS10EE289B9FDE2C4B1`, `BGS11665AC6BD06C5EBD`, `BGS117E3FE9519A5B542`, `BGS1241B6719A7FE041D`, `BGS1250D82C4B027A171`, `BGS147DBB4CF132F0523`, `BGS152BE1A314EFF3FE3`, `BGS166A638195D1E2BAE`, `BGS16C952D775A16E650`, `BGS1737E89A3E6B7A57C`
- **Skill_Weight**: `1.0`

**Sample Complete Records:**

**Record 1:**
  - `JobProfileID`: R0001.5
  - `Skill_ID`: BGSD16A8EEF4F5775E15
  - `Skill_Weight`: 1.0

**Record 2:**
  - `JobProfileID`: R0001.5
  - `Skill_ID`: ES147CB8BEA5CF1AF1F6
  - `Skill_Weight`: 1.0

**Record 3:**
  - `JobProfileID`: R0001.5
  - `Skill_ID`: ES203B9B0426DA590EDF
  - `Skill_Weight`: 1.0

---

### 5. **jobs** - 715 records

```sql
CREATE TABLE jobs (
    JobProfileID TEXT PRIMARY KEY,
    JobProfile TEXT NOT NULL,
    JobID TEXT,
    Job TEXT,
    ProfileTitleSuffix TEXT,
    ManagementLevel TEXT,
    JobSubFunctionID TEXT,
    JobSubFunction TEXT,
    JobFunctionID TEXT,
    JobFunction TEXT,
    JobCategoryID TEXT,
    JobCategory TEXT,
    Customer_Facing TEXT,
    is_Banker TEXT,
    Executive_Leadership_Group TEXT,
    Accountability_Scope TEXT
);
```

**Column Statistics:**

- **JobProfileID**: 715 unique values (715 non-null), avg length 7.0
- **JobProfile**: 309 unique values (715 non-null), avg length 22.48
- **JobID**: 240 unique values (715 non-null), avg length 5.0
- **Job**: 35 unique values (715 non-null), avg length 17.92
- **ProfileTitleSuffix**: 16 unique values (715 non-null), avg length 8.92
- **ManagementLevel**: 8 unique values (715 non-null), avg length 7.02
- **JobSubFunctionID**: 526 unique values (715 non-null), avg length 6.0
- **JobSubFunction**: 110 unique values (715 non-null), avg length 17.58
- **JobFunctionID**: 22 unique values (715 non-null), avg length 5.0
- **JobFunction**: 22 unique values (715 non-null), avg length 19.57
- **JobCategoryID**: 4 unique values (715 non-null), avg length 3.06
- **JobCategory**: 4 unique values (715 non-null), avg length 10.87
- **Customer_Facing**: 3 unique values (715 non-null), avg length 17.64
- **is_Banker**: 3 unique values (715 non-null), avg length 8.38
- **Executive_Leadership_Group**: 2 unique values (715 non-null), avg length 1.24
- **Accountability_Scope**: 3 unique values (715 non-null), avg length 0.72

**Data Quality - Completeness:**

- **JobProfileID**: 100% complete
- **JobProfile**: 100% complete
- **JobID**: 100% complete
- **Job**: 100% complete
- **ProfileTitleSuffix**: 100% complete
- **ManagementLevel**: 100% complete
- **JobSubFunctionID**: 100% complete
- **JobSubFunction**: 100% complete
- **JobFunctionID**: 100% complete
- **JobFunction**: 100% complete
- **JobCategoryID**: 100% complete
- **JobCategory**: 100% complete
- **Customer_Facing**: 100% complete
- **is_Banker**: 100% complete
- **Executive_Leadership_Group**: 100% complete
- **Accountability_Scope**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **JobProfileID**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **JobProfile**: `Budget Manager (Ungraded)`, `Budget Manager - 0`, `Budget Manager - 2`, `Budget Manager - 3`, `Budget Manager - 4`, `Budget Manager - 5`, `Budget Manager - 6`, `Budget Manager - 7`, `Budget Manager - II`, `Business Analyst - 0`
- **JobID**: `R0001`, `R0002`, `R0003`, `R0005`, `R0007`, `R0009`, `R0010`, `R0022`, `R0023`, `R0025`
- **Job**: `Budget Manager`, `Business Analyst`, `Business Banker`, `Chief Officer`, `Cloud Architect`, `Compliance Officer`, `Credit Risk Manager`, `Customer Service Representa...`, `Cybersecurity Analyst`, `Data Scientist`
- **ProfileTitleSuffix**: `Advisor`, `Analyst`, `Associate`, `Consultant`, `Group Executive`, `Head of`, `I`, `II`, `III`, `Lead Consultant`
- **ManagementLevel**: `Group 1`, `Group 2`, `Group 3`, `Group 4`, `Group 5`, `Group 6`, `Group 7`, `Group NA`
- **JobSubFunctionID**: `JF0002`, `JF0003`, `JF0004`, `JF0005`, `JF0007`, `JF0009`, `JF0011`, `JF0013`, `JF0020`, `JF0021`
- **JobSubFunction**: `Account Management`, `Actuarial Services`, `Anti-Money Laundering`, `Application Support`, `Artificial Intelligence`, `Asset Management`, `Audit & Assurance`, `Basel Compliance`, `Brand Management`, `Budgeting & Forecasting`
- **JobFunctionID**: `JF001`, `JF002`, `JF003`, `JF004`, `JF005`, `JF006`, `JF007`, `JF008`, `JF009`, `JF010`
- **JobFunction**: `Audit & Assurance`, `Banking Services`, `Business Development`, `Customer Relations`, `Data & Analytics`, `Executive Leadership`, `Facilities & Administration`, `Finance & Treasury`, `Human Resources`, `Investment Management`
- **JobCategoryID**: `JC1`, `JC10`, `JC2`, `JC3`
- **JobCategory**: `Enabling`, `Executive & General Management`, `Revenue Generating`, `Support`
- **Customer_Facing**: ``, `Customer Facing`, `Non-Customer Facing`
- **is_Banker**: ``, `Banker`, `Non-Banker`
- **Executive_Leadership_Group**: ``, `Executive Leadership Group`
- **Accountability_Scope**: ``, `Direct`, `Supports`

**Sample Complete Records:**

**Record 1:**
  - `JobProfileID`: R0001.5
  - `JobProfile`: Payment Systems Analyst - 5
  - `JobID`: R0001
  - `Job`: Payment Systems Analyst
  - `ProfileTitleSuffix`: Senior Manager
  - `ManagementLevel`: Group 2
  - `JobSubFunctionID`: JF0655
  - `JobSubFunction`: Data Governance
  - `JobFunctionID`: JF016
  - `JobFunction`: Data & Analytics
  - `JobCategoryID`: JC2
  - `JobCategory`: Support
  - `Customer_Facing`: Customer Facing
  - `is_Banker`: Non-Banker
  - `Executive_Leadership_Group`: 
  - `Accountability_Scope`: 

**Record 2:**
  - `JobProfileID`: R0001.6
  - `JobProfile`: Settlement Officer - 6
  - `JobID`: R0001
  - `Job`: Settlement Officer
  - `ProfileTitleSuffix`: Associate
  - `ManagementLevel`: Group 1
  - `JobSubFunctionID`: JF0559
  - `JobSubFunction`: Machine Learning
  - `JobFunctionID`: JF016
  - `JobFunction`: Data & Analytics
  - `JobCategoryID`: JC2
  - `JobCategory`: Support
  - `Customer_Facing`: Customer Facing
  - `is_Banker`: Banker
  - `Executive_Leadership_Group`: Executive Leadership Group
  - `Accountability_Scope`: 

**Record 3:**
  - `JobProfileID`: R0002.0
  - `JobProfile`: Sales Manager - II
  - `JobID`: R0002
  - `Job`: Sales Manager
  - `ProfileTitleSuffix`: II
  - `ManagementLevel`: Group 4
  - `JobSubFunctionID`: JF0204
  - `JobSubFunction`: Investment Banking
  - `JobFunctionID`: JF012
  - `JobFunction`: Banking Services
  - `JobCategoryID`: JC1
  - `JobCategory`: Enabling
  - `Customer_Facing`: Customer Facing
  - `is_Banker`: Banker
  - `Executive_Leadership_Group`: 
  - `Accountability_Scope`: 

---

### 6. **movement_fact** - 162,941 records

```sql
CREATE TABLE movement_fact (
    fact_id INTEGER PRIMARY KEY,
    movement_month TEXT NOT NULL,
    movement_year INTEGER NOT NULL,
    from_position TEXT NOT NULL,
    to_position TEXT NOT NULL,
    movement_pattern TEXT NOT NULL,
    movement_count INTEGER NOT NULL,
    pct_total_movements REAL,
    unique_employees INTEGER NOT NULL,
    avg_days_between REAL,
    monthly_total_movements INTEGER NOT NULL,
    predominant_movement_type TEXT
);
```

**Column Statistics:**

- **fact_id**: 162,941 unique values (162,941 non-null), range 1 - 162941
- **movement_month**: 48 unique values (162,941 non-null), avg length 7.0
- **movement_year**: 5 unique values (162,941 non-null), range 2021 - 2025
- **from_position**: 4,997 unique values (162,941 non-null), avg length 8.0
- **to_position**: 4,996 unique values (162,941 non-null), avg length 8.0
- **movement_pattern**: 162,297 unique values (162,941 non-null), avg length 19.0
- **movement_count**: 2 unique values (162,941 non-null), range 1 - 2
- **pct_total_movements**: 8 unique values (162,941 non-null), range 0.0200 - 0.2100, avg 0.0298
- **unique_employees**: 2 unique values (162,941 non-null), range 1 - 2
- **avg_days_between**: 56 unique values (162,941 non-null), range 7.0000 - 357.0000, avg 58.9805
- **monthly_total_movements**: 48 unique values (162,941 non-null), range 472 - 4828
- **predominant_movement_type**: 1 unique values (162,941 non-null), avg length 7.0

**Data Quality - Completeness:**

- **fact_id**: 100% complete
- **movement_month**: 100% complete
- **movement_year**: 100% complete
- **from_position**: 100% complete
- **to_position**: 100% complete
- **movement_pattern**: 100% complete
- **movement_count**: 100% complete
- **pct_total_movements**: 100% complete
- **unique_employees**: 100% complete
- **avg_days_between**: 100% complete
- **monthly_total_movements**: 100% complete
- **predominant_movement_type**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **fact_id**: `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`
- **movement_month**: `2021-07`, `2021-08`, `2021-09`, `2021-10`, `2021-11`, `2021-12`, `2022-01`, `2022-02`, `2022-03`, `2022-04`
- **movement_year**: `2021`, `2022`, `2023`, `2024`, `2025`
- **from_position**: `50000000`, `50000001`, `50000002`, `50000003`, `50000004`, `50000005`, `50000006`, `50000007`, `50000008`, `50000009`
- **to_position**: `50000000`, `50000001`, `50000002`, `50000003`, `50000004`, `50000005`, `50000006`, `50000007`, `50000008`, `50000009`
- **movement_pattern**: `50000000 → 50000072`, `50000000 → 50000119`, `50000000 → 50000142`, `50000000 → 50000149`, `50000000 → 50000384`, `50000000 → 50000385`, `50000000 → 50000433`, `50000000 → 50000660`, `50000000 → 50000734`, `50000000 → 50000739`
- **movement_count**: `1`, `2`
- **pct_total_movements**: `0.02`, `0.03`, `0.04`, `0.05`, `0.06`, `0.12`, `0.2`, `0.21`
- **unique_employees**: `1`, `2`
- **avg_days_between**: `7.0`, `10.5`, `14.0`, `21.0`, `24.5`, `28.0`, `31.5`, `35.0`, `38.5`, `42.0`
- **monthly_total_movements**: `472`, `490`, `495`, `503`, `1555`, `1580`, `1585`, `1604`, `3065`, `3109`
- **predominant_movement_type**: `lateral`

**Sample Complete Records:**

**Record 1:**
  - `fact_id`: 1
  - `movement_month`: 2021-07
  - `movement_year`: 2021
  - `from_position`: 50004608
  - `to_position`: 50002964
  - `movement_pattern`: 50004608 → 50002964
  - `movement_count`: 1
  - `pct_total_movements`: 0.2
  - `unique_employees`: 1
  - `avg_days_between`: 28.0
  - `monthly_total_movements`: 495
  - `predominant_movement_type`: lateral

**Record 2:**
  - `fact_id`: 2
  - `movement_month`: 2021-07
  - `movement_year`: 2021
  - `from_position`: 50003207
  - `to_position`: 50000638
  - `movement_pattern`: 50003207 → 50000638
  - `movement_count`: 1
  - `pct_total_movements`: 0.2
  - `unique_employees`: 1
  - `avg_days_between`: 21.0
  - `monthly_total_movements`: 495
  - `predominant_movement_type`: lateral

**Record 3:**
  - `fact_id`: 3
  - `movement_month`: 2021-07
  - `movement_year`: 2021
  - `from_position`: 50002733
  - `to_position`: 50001177
  - `movement_pattern`: 50002733 → 50001177
  - `movement_count`: 1
  - `pct_total_movements`: 0.2
  - `unique_employees`: 1
  - `avg_days_between`: 14.0
  - `monthly_total_movements`: 495
  - `predominant_movement_type`: lateral

---

### 7. **position_history** - 600,000 records

```sql
CREATE TABLE position_history (
    week_ending DATE,
    position_number TEXT NOT NULL,
    position_id_lookup_key TEXT,
    organisational_unit TEXT,
    cost_centre_number TEXT,
    position_title TEXT,
    people_leader TEXT,
    operational TEXT,
    org_unit_id_lookup_key TEXT
);
```

**Column Statistics:**

- **position_number**: 4,997 unique values (600,000 non-null), avg length 8.0
- **position_id_lookup_key**: 600,000 unique values (600,000 non-null), avg length 15.89
- **organisational_unit**: 11 unique values (600,000 non-null), avg length 13.99
- **cost_centre_number**: 90 unique values (600,000 non-null), avg length 4.0
- **position_title**: 1 unique values (600,000 non-null), avg length 0
- **people_leader**: 117,288 unique values (600,000 non-null), avg length 6.97
- **operational**: 2 unique values (600,000 non-null), avg length 1.0
- **org_unit_id_lookup_key**: 580,257 unique values (600,000 non-null), avg length 7.0

**Data Quality - Completeness:**

- **week_ending**: 100% complete
- **position_number**: 100% complete
- **position_id_lookup_key**: 100% complete
- **organisational_unit**: 100% complete
- **cost_centre_number**: 100% complete
- **position_title**: 100% complete
- **people_leader**: 100% complete
- **operational**: 100% complete
- **org_unit_id_lookup_key**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **week_ending**: `01/06/2024`, `01/07/2020`, `01/07/2021`, `01/07/2022`, `01/07/2023`, `01/07/2024`, `02/03/2024`, `02/06/2021`, `02/06/2022`, `02/06/2023`
- **position_number**: `50000000`, `50000001`, `50000002`, `50000003`, `50000004`, `50000005`, `50000006`, `50000007`, `50000008`, `50000009`
- **position_id_lookup_key**: `100000404561.949`, `100000482476.752`, `100000490281.261`, `100001048729.251`, `100001257854.242`, `100001742750.32`, `100002088367.031`, `100002093222.153`, `100003533132.812`, `100006060675.268`
- **organisational_unit**: `Business Banking`, `Corporate Affairs`, `Customer Banking`, `Finance`, `Human Resources`, `Institutional Banking`, `Legal & Compliance`, `Marketing`, `Operations`, `Risk Management`
- **cost_centre_number**: `1000`, `1100`, `1200`, `1300`, `1400`, `1500`, `1600`, `1700`, `1800`, `1900`
- **position_title**: ``
- **people_leader**: ``, `20000096.0`, `20000338.0`, `20000462.0`, `20000658.0`, `20000664.0`, `20000681.0`, `20000815.0`, `20001248.0`, `20001309.0`
- **operational**: `0`, `1`
- **org_unit_id_lookup_key**: `1000052`, `1000088`, `1000099`, `1000111`, `1000120`, `1000132`, `1000159`, `1000177`, `1000181`, `1000182`

**Sample Complete Records:**

**Record 1:**
  - `week_ending`: 01/07/2020
  - `position_number`: 50000000
  - `position_id_lookup_key`: 173270485187.612
  - `organisational_unit`: Risk Management
  - `cost_centre_number`: 2800
  - `position_title`: 
  - `people_leader`: 22615063.0
  - `operational`: 1
  - `org_unit_id_lookup_key`: 7379873

**Record 2:**
  - `week_ending`: 02/06/2021
  - `position_number`: 50000000
  - `position_id_lookup_key`: 133027629035.626
  - `organisational_unit`: Technology
  - `cost_centre_number`: 6100
  - `position_title`: 
  - `people_leader`: 20703164.0
  - `operational`: 1
  - `org_unit_id_lookup_key`: 5035291

**Record 3:**
  - `week_ending`: 02/12/2020
  - `position_number`: 50000000
  - `position_id_lookup_key`: 225280122312.613
  - `organisational_unit`: Technology
  - `cost_centre_number`: 6100
  - `position_title`: 
  - `people_leader`: 20703164.0
  - `operational`: 1
  - `org_unit_id_lookup_key`: 7975908

---

### 8. **positions** - 35,000 records

```sql
CREATE TABLE positions (
    Employee Number TEXT PRIMARY KEY,
    Position Number TEXT NOT NULL,
    Position Name TEXT,
    JobProfileID TEXT,
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

- `JobProfileID` â†’ `jobs.JobProfileID`

**Column Statistics:**

- **Employee Number**: 35,000 unique values (35,000 non-null), avg length 6.0
- **Position Number**: 4,997 unique values (35,000 non-null), avg length 8.0
- **Position Name**: 580 unique values (35,000 non-null), avg length 21.98
- **JobProfileID**: 1 unique values (35,000 non-null), avg length 0
- **Division**: 6 unique values (35,000 non-null), avg length 20.1
- **Business_Unit**: 10 unique values (35,000 non-null), avg length 14.34
- **Team**: 10 unique values (35,000 non-null), avg length 24.53
- **SubTeam**: 30 unique values (35,000 non-null), avg length 7.0
- **Function**: 26 unique values (35,000 non-null), avg length 7.0
- **SubFunction**: 20 unique values (35,000 non-null), avg length 5.55
- **Org_Level_8**: 50 unique values (35,000 non-null), avg length 8.0
- **Org_Level_9**: 30 unique values (35,000 non-null), avg length 7.0
- **Org_Level_10**: 100 unique values (35,000 non-null), avg length 8.0
- **Location**: 6 unique values (35,000 non-null), avg length 8.6
- **Rg**: 5 unique values (35,000 non-null), avg length 2.67
- **Cty**: 1 unique values (35,000 non-null), avg length 2.0
- **Employee Group**: 4 unique values (35,000 non-null), avg length 8.77
- **Salary Group**: 9 unique values (35,000 non-null), avg length 7.0
- **Employee Subgroup**: 3 unique values (35,000 non-null), avg length 8.01

**Data Quality - Completeness:**

- **Employee Number**: 100% complete
- **Position Number**: 100% complete
- **Position Name**: 100% complete
- **JobProfileID**: 100% complete
- **Division**: 100% complete
- **Business_Unit**: 100% complete
- **Team**: 100% complete
- **SubTeam**: 100% complete
- **Function**: 100% complete
- **SubFunction**: 100% complete
- **Org_Level_8**: 100% complete
- **Org_Level_9**: 100% complete
- **Org_Level_10**: 100% complete
- **Location**: 100% complete
- **Rg**: 100% complete
- **Cty**: 100% complete
- **Employee Group**: 100% complete
- **Salary Group**: 100% complete
- **Employee Subgroup**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **Employee Number**: `100000`, `100001`, `100002`, `100003`, `100004`, `100005`, `100006`, `100007`, `100008`, `100009`
- **Position Number**: `50000000`, `50000001`, `50000002`, `50000003`, `50000004`, `50000005`, `50000006`, `50000007`, `50000008`, `50000009`
- **Position Name**: `Analytics Advisor`, `Analytics Analyst`, `Analytics Associate`, `Analytics Consultant`, `Analytics Developer`, `Analytics Director`, `Analytics Engineer`, `Analytics Executive Advisor`, `Analytics Executive Director`, `Analytics Executive Manager`
- **JobProfileID**: ``
- **Division**: `Business & Private Banking`, `Corporate & Institutional B...`, `Customer Banking & Wealth`, `Group Functions`, `NAB Ventures`, `Technology`
- **Business_Unit**: `Business Banking`, `Corporate Banking`, `Finance`, `Human Resources`, `Legal & Compliance`, `NAB Ventures`, `Personal Banking`, `Risk Management`, `Technology`, `Wealth Management`
- **Team**: `Business Banking Operations`, `Corporate Banking Operations`, `Finance Strategy`, `Human Resources Strategy`, `Legal & Compliance Strategy`, `NAB Ventures Operations`, `Personal Banking Operations`, `Risk Management Strategy`, `Technology Operations`, `Wealth Management Operations`
- **SubTeam**: `Team 01`, `Team 02`, `Team 03`, `Team 04`, `Team 05`, `Team 06`, `Team 07`, `Team 08`, `Team 09`, `Team 10`
- **Function**: `Squad A`, `Squad B`, `Squad C`, `Squad D`, `Squad E`, `Squad F`, `Squad G`, `Squad H`, `Squad I`, `Squad J`
- **SubFunction**: `Pod 1`, `Pod 10`, `Pod 11`, `Pod 12`, `Pod 13`, `Pod 14`, `Pod 15`, `Pod 16`, `Pod 17`, `Pod 18`
- **Org_Level_8**: `Unit 001`, `Unit 002`, `Unit 003`, `Unit 004`, `Unit 005`, `Unit 006`, `Unit 007`, `Unit 008`, `Unit 009`, `Unit 010`
- **Org_Level_9**: `Cell 01`, `Cell 02`, `Cell 03`, `Cell 04`, `Cell 05`, `Cell 06`, `Cell 07`, `Cell 08`, `Cell 09`, `Cell 10`
- **Org_Level_10**: `Node 001`, `Node 002`, `Node 003`, `Node 004`, `Node 005`, `Node 006`, `Node 007`, `Node 008`, `Node 009`, `Node 010`
- **Location**: `Adelaide`, `Brisbane City`, `Docklands`, `Parramatta`, `Perth`, `Sydney`
- **Rg**: `NSW`, `QLD`, `SA`, `VIC`, `WA`
- **Cty**: `AU`
- **Employee Group**: `Casual`, `Contractor`, `Fixed Term`, `Permanent`
- **Salary Group**: `Casual`, `External`, `Group 1`, `Group 2`, `Group 3`, `Group 4`, `Group 5`, `Group 6`, `Group 7`
- **Employee Subgroup**: `Casual`, `Full Time`, `Part Time`

**Sample Complete Records:**

**Record 1:**
  - `Employee Number`: 100000
  - `Position Number`: 50003311
  - `Position Name`: Investment Principal Specialist
  - `JobProfileID`: 
  - `Division`: Corporate & Institutional Banking
  - `Business_Unit`: Technology
  - `Team`: Business Banking Operations
  - `SubTeam`: Team 15
  - `Function`: Squad H
  - `SubFunction`: Pod 15
  - `Org_Level_8`: Unit 038
  - `Org_Level_9`: Cell 11
  - `Org_Level_10`: Node 024
  - `Location`: Brisbane City
  - `Rg`: QLD
  - `Cty`: AU
  - `Employee Group`: Fixed Term
  - `Salary Group`: Group 7
  - `Employee Subgroup`: Full Time

**Record 2:**
  - `Employee Number`: 100001
  - `Position Number`: 50003667
  - `Position Name`: Operations Vice President
  - `JobProfileID`: 
  - `Division`: Corporate & Institutional Banking
  - `Business_Unit`: Human Resources
  - `Team`: Human Resources Strategy
  - `SubTeam`: Team 05
  - `Function`: Squad D
  - `SubFunction`: Pod 19
  - `Org_Level_8`: Unit 003
  - `Org_Level_9`: Cell 30
  - `Org_Level_10`: Node 037
  - `Location`: Adelaide
  - `Rg`: SA
  - `Cty`: AU
  - `Employee Group`: Permanent
  - `Salary Group`: Group 7
  - `Employee Subgroup`: Full Time

**Record 3:**
  - `Employee Number`: 100002
  - `Position Number`: 50000226
  - `Position Name`: Audit General Manager
  - `JobProfileID`: 
  - `Division`: Technology
  - `Business_Unit`: Human Resources
  - `Team`: Finance Strategy
  - `SubTeam`: Team 27
  - `Function`: Squad H
  - `SubFunction`: Pod 9
  - `Org_Level_8`: Unit 030
  - `Org_Level_9`: Cell 22
  - `Org_Level_10`: Node 092
  - `Location`: Sydney
  - `Rg`: NSW
  - `Cty`: AU
  - `Employee Group`: Fixed Term
  - `Salary Group`: Group 2
  - `Employee Subgroup`: Casual

---

### 9. **schema_metadata** - 4 records

```sql
CREATE TABLE schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

**Column Statistics:**

- **key**: 4 unique values (4 non-null), avg length 12.0
- **value**: 4 unique values (4 non-null), avg length 27.5
- **created_at**: 1 unique values (4 non-null), avg length 26.0

**Data Quality - Completeness:**

- **key**: 100% complete
- **value**: 100% complete
- **created_at**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **key**: `created_date`, `purpose`, `schema_version`, `source_document`
- **value**: `1.0`, `2025-07-17T14:42:29.174221`, `NAB Skill Similarity Engine...`, `docs/sqlite_schema_design.md`
- **created_at**: `2025-07-17T14:42:29.174221`

**Sample Complete Records:**

**Record 1:**
  - `key`: schema_version
  - `value`: 1.0
  - `created_at`: 2025-07-17T14:42:29.174221

**Record 2:**
  - `key`: created_date
  - `value`: 2025-07-17T14:42:29.174221
  - `created_at`: 2025-07-17T14:42:29.174221

**Record 3:**
  - `key`: source_document
  - `value`: docs/sqlite_schema_design.md
  - `created_at`: 2025-07-17T14:42:29.174221

---

### 10. **skills** - 38,430 records

```sql
CREATE TABLE skills (
    Skill_ID TEXT PRIMARY KEY,
    Skill_Name TEXT NOT NULL,
    Category TEXT,
    Subcategory TEXT,
    SkillType TEXT,
    Latest_Version TEXT,
    category_id INTEGER,
    description TEXT,
    descriptionSource TEXT,
    Info_URL TEXT,
    Is_Language BOOLEAN,
    isSoftware BOOLEAN,
    subcategory_id INTEGER,
    tag_wikipediaExtract TEXT,
    tag_wikipediaUrl TEXT,
    tags TEXT,
    type_id TEXT,
    type_name TEXT,
    Market_Demand TEXT DEFAULT '',
    Rarity_Score REAL DEFAULT NULL
);
```

**Column Statistics:**

- **Skill_ID**: 38,430 unique values (38,430 non-null), avg length 20.0
- **Skill_Name**: 38,430 unique values (38,430 non-null), avg length 19.68
- **Category**: 34 unique values (38,430 non-null), avg length 17.96
- **Subcategory**: 460 unique values (38,430 non-null), avg length 20.29
- **SkillType**: 3 unique values (38,430 non-null), avg length 16.57
- **Latest_Version**: 51 unique values (38,430 non-null), avg length 3.98
- **category_id**: 34 unique values (38,430 non-null), range 0 - 0
- **description**: 36,922 unique values (38,430 non-null), avg length 483.26
- **descriptionSource**: 0 unique values (0 non-null), avg length 0
- **Info_URL**: 38,430 unique values (38,430 non-null), avg length 60.0
- **subcategory_id**: 453 unique values (38,430 non-null), range 100 - 0
- **tag_wikipediaExtract**: 0 unique values (0 non-null), avg length 0
- **tag_wikipediaUrl**: 0 unique values (0 non-null), avg length 0
- **tags**: 0 unique values (0 non-null), avg length 0
- **type_id**: 3 unique values (38,430 non-null), avg length 3.0
- **type_name**: 0 unique values (0 non-null), avg length 0
- **Market_Demand**: 1 unique values (38,430 non-null), avg length 0
- **Rarity_Score**: 1 unique values (38,430 non-null), range 0.0000 - 0.0000, avg 0.0000

**Data Quality - Completeness:**

- **Skill_ID**: 100% complete
- **Skill_Name**: 100% complete
- **Category**: 100% complete
- **Subcategory**: 100% complete
- **SkillType**: 100% complete
- **Latest_Version**: 100% complete
- **category_id**: 100% complete
- **description**: 100% complete
- **descriptionSource**: 0.0% complete (38,430 null values)
- **Info_URL**: 100% complete
- **Is_Language**: 100% complete
- **isSoftware**: 0.0% complete (38,430 null values)
- **subcategory_id**: 100% complete
- **tag_wikipediaExtract**: 0.0% complete (38,430 null values)
- **tag_wikipediaUrl**: 0.0% complete (38,430 null values)
- **tags**: 0.0% complete (38,430 null values)
- **type_id**: 100% complete
- **type_name**: 0.0% complete (38,430 null values)
- **Market_Demand**: 100% complete
- **Rarity_Score**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **Skill_ID**: `BGS1024316C916ACCFA3`, `BGS105C99F084505B956`, `BGS1080D1F8CED414379`, `BGS10AB6DEBB81A2E88C`, `BGS10B5E145CA48862FC`, `BGS10CBE4935DDCAE5AD`, `BGS10EE289B9FDE2C4B1`, `BGS10F3F05054C5731C2`, `BGS10F94E4049444B523`, `BGS110587665F051DF29`
- **Skill_Name**: `.NET Assemblies`, `.NET Development`, `.NET Framework`, `.NET Framework 1`, `.NET Framework 3`, `.NET Framework 4`, `.NET MAUI (Multi-Platform A...`, `.NET Reflector`, `.NET Remoting`, `.htaccess Files`
- **Category**: ``, `Administration`, `Agriculture, Horticulture, ...`, `Analysis`, `Architecture and Construction`, `Business`, `Customer and Client Support`, `Design`, `Economics, Policy, and Soci...`, `Education and Training`
- **Subcategory**: ``, `Account Management`, `Accounting and Finance Soft...`, `Accounts Payable and Receiv...`, `Administrative Support and ...`, `Advanced Customer Service`, `Advanced Patient Care`, `Advertising`, `Aerospace Engineering`, `Agile Software Development`
- **SkillType**: `Certification`, `Common Skill`, `Specialized Skill`
- **Latest_Version**: `8.0`, `8.1`, `8.11`, `8.12`, `8.13`, `8.14`, `8.15`, `8.16`, `8.17`, `8.18`
- **category_id**: `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`
- **description**: ``, `'Autoroll' refers to TV-sig...`, `'National Lifeguard’ is a l...`, `.NET Assemblies refer to th...`, `.NET Development refers to ...`, `.NET Framework 1 is a softw...`, `.NET Framework 3 is a softw...`, `.NET Framework 4 is a softw...`, `.NET Framework is a softwar...`, `.NET MAUI is a modern, cros...`
- **Info_URL**: `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`
- **Is_Language**: `0`, `1`
- **subcategory_id**: `100`, `101`, `102`, `105`, `106`, `107`, `108`, `109`, `110`, `111`
- **type_id**: `ST1`, `ST2`, `ST3`
- **Market_Demand**: ``
- **Rarity_Score**: ``

**Sample Complete Records:**

**Record 1:**
  - `Skill_ID`: BGS1024316C916ACCFA3
  - `Skill_Name`: DX Spectrum
  - `Category`: Information Technology
  - `Subcategory`: Enterprise Information Management
  - `SkillType`: Specialized Skill
  - `Latest_Version`: 8.5
  - `category_id`: 17
  - `description`: 
  - `Info_URL`: https://lightcast.io/open-skills/skills/BGS1024...
  - `Is_Language`: 0
  - `subcategory_id`: 411
  - `type_id`: ST1
  - `Market_Demand`: 
  - `Rarity_Score`: 

**Record 2:**
  - `Skill_ID`: BGS105C99F084505B956
  - `Skill_Name`: Microsoft Sysprep
  - `Category`: Information Technology
  - `Subcategory`: Software Development Tools
  - `SkillType`: Specialized Skill
  - `Latest_Version`: 9.31
  - `category_id`: 17
  - `description`: Microsoft Sysprep is a utility tool used to pre...
  - `Info_URL`: https://lightcast.io/open-skills/skills/BGS105C...
  - `Is_Language`: 0
  - `subcategory_id`: 476
  - `type_id`: ST1
  - `Market_Demand`: 
  - `Rarity_Score`: 

**Record 3:**
  - `Skill_ID`: BGS1080D1F8CED414379
  - `Skill_Name`: Application Remediation
  - `Category`: Information Technology
  - `Subcategory`: Software Quality Assurance
  - `SkillType`: Specialized Skill
  - `Latest_Version`: 9.31
  - `category_id`: 17
  - `description`: Application Remediation refers to the process o...
  - `Info_URL`: https://lightcast.io/open-skills/skills/BGS1080...
  - `Is_Language`: 0
  - `subcategory_id`: 477
  - `type_id`: ST1
  - `Market_Demand`: 
  - `Rarity_Score`: 

---

### 11. **workforce_context** - 35,000 records

```sql
CREATE TABLE workforce_context (
    week_ending DATE,
    position_number TEXT NOT NULL,
    position_name TEXT,
    employee_number TEXT,
    employee_name TEXT,
    location TEXT,
    region TEXT,
    country TEXT,
    employee_group TEXT,
    salary_group TEXT,
    division TEXT,
    business_unit TEXT,
    team TEXT,
    sub_team TEXT,
    function TEXT,
    sub_function TEXT,
    org_level_8 TEXT,
    org_level_9 TEXT,
    org_level_10 TEXT
);
```

**Column Statistics:**

- **position_number**: 4,997 unique values (35,000 non-null), avg length 8.0
- **position_name**: 580 unique values (35,000 non-null), avg length 21.98
- **employee_number**: 35,000 unique values (35,000 non-null), avg length 6.0
- **employee_name**: 224 unique values (35,000 non-null), avg length 13.08
- **location**: 6 unique values (35,000 non-null), avg length 8.6
- **region**: 5 unique values (35,000 non-null), avg length 2.67
- **country**: 1 unique values (35,000 non-null), avg length 2.0
- **employee_group**: 4 unique values (35,000 non-null), avg length 8.77
- **salary_group**: 9 unique values (35,000 non-null), avg length 7.0
- **division**: 6 unique values (35,000 non-null), avg length 20.1
- **business_unit**: 10 unique values (35,000 non-null), avg length 14.34
- **team**: 10 unique values (35,000 non-null), avg length 24.53
- **sub_team**: 30 unique values (35,000 non-null), avg length 7.0
- **function**: 26 unique values (35,000 non-null), avg length 7.0
- **sub_function**: 20 unique values (35,000 non-null), avg length 5.55
- **org_level_8**: 50 unique values (35,000 non-null), avg length 8.0
- **org_level_9**: 30 unique values (35,000 non-null), avg length 7.0
- **org_level_10**: 100 unique values (35,000 non-null), avg length 8.0

**Data Quality - Completeness:**

- **week_ending**: 100% complete
- **position_number**: 100% complete
- **position_name**: 100% complete
- **employee_number**: 100% complete
- **employee_name**: 100% complete
- **location**: 100% complete
- **region**: 100% complete
- **country**: 100% complete
- **employee_group**: 100% complete
- **salary_group**: 100% complete
- **division**: 100% complete
- **business_unit**: 100% complete
- **team**: 100% complete
- **sub_team**: 100% complete
- **function**: 100% complete
- **sub_function**: 100% complete
- **org_level_8**: 100% complete
- **org_level_9**: 100% complete
- **org_level_10**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **week_ending**: `2025-06-21`
- **position_number**: `50000000`, `50000001`, `50000002`, `50000003`, `50000004`, `50000005`, `50000006`, `50000007`, `50000008`, `50000009`
- **position_name**: `Analytics Advisor`, `Analytics Analyst`, `Analytics Associate`, `Analytics Consultant`, `Analytics Developer`, `Analytics Director`, `Analytics Engineer`, `Analytics Executive Advisor`, `Analytics Executive Director`, `Analytics Executive Manager`
- **employee_number**: `100000`, `100001`, `100002`, `100003`, `100004`, `100005`, `100006`, `100007`, `100008`, `100009`
- **employee_name**: `Amanda Brown`, `Amanda Davis`, `Amanda Garcia`, `Amanda Gonzalez`, `Amanda Hernandez`, `Amanda Johnson`, `Amanda Jones`, `Amanda Lopez`, `Amanda Martinez`, `Amanda Miller`
- **location**: `Adelaide`, `Brisbane City`, `Docklands`, `Parramatta`, `Perth`, `Sydney`
- **region**: `NSW`, `QLD`, `SA`, `VIC`, `WA`
- **country**: `AU`
- **employee_group**: `Casual`, `Contractor`, `Fixed Term`, `Permanent`
- **salary_group**: `Casual`, `External`, `Group 1`, `Group 2`, `Group 3`, `Group 4`, `Group 5`, `Group 6`, `Group 7`
- **division**: `Business & Private Banking`, `Corporate & Institutional B...`, `Customer Banking & Wealth`, `Group Functions`, `NAB Ventures`, `Technology`
- **business_unit**: `Business Banking`, `Corporate Banking`, `Finance`, `Human Resources`, `Legal & Compliance`, `NAB Ventures`, `Personal Banking`, `Risk Management`, `Technology`, `Wealth Management`
- **team**: `Business Banking Operations`, `Corporate Banking Operations`, `Finance Strategy`, `Human Resources Strategy`, `Legal & Compliance Strategy`, `NAB Ventures Operations`, `Personal Banking Operations`, `Risk Management Strategy`, `Technology Operations`, `Wealth Management Operations`
- **sub_team**: `Team 01`, `Team 02`, `Team 03`, `Team 04`, `Team 05`, `Team 06`, `Team 07`, `Team 08`, `Team 09`, `Team 10`
- **function**: `Squad A`, `Squad B`, `Squad C`, `Squad D`, `Squad E`, `Squad F`, `Squad G`, `Squad H`, `Squad I`, `Squad J`
- **sub_function**: `Pod 1`, `Pod 10`, `Pod 11`, `Pod 12`, `Pod 13`, `Pod 14`, `Pod 15`, `Pod 16`, `Pod 17`, `Pod 18`
- **org_level_8**: `Unit 001`, `Unit 002`, `Unit 003`, `Unit 004`, `Unit 005`, `Unit 006`, `Unit 007`, `Unit 008`, `Unit 009`, `Unit 010`
- **org_level_9**: `Cell 01`, `Cell 02`, `Cell 03`, `Cell 04`, `Cell 05`, `Cell 06`, `Cell 07`, `Cell 08`, `Cell 09`, `Cell 10`
- **org_level_10**: `Node 001`, `Node 002`, `Node 003`, `Node 004`, `Node 005`, `Node 006`, `Node 007`, `Node 008`, `Node 009`, `Node 010`

**Sample Complete Records:**

**Record 1:**
  - `week_ending`: 2025-06-21
  - `position_number`: 50003311
  - `position_name`: Investment Principal Specialist
  - `employee_number`: 100000
  - `employee_name`: Emma Smith
  - `location`: Brisbane City
  - `region`: QLD
  - `country`: AU
  - `employee_group`: Fixed Term
  - `salary_group`: Group 7
  - `division`: Corporate & Institutional Banking
  - `business_unit`: Technology
  - `team`: Business Banking Operations
  - `sub_team`: Team 15
  - `function`: Squad H
  - `sub_function`: Pod 15
  - `org_level_8`: Unit 038
  - `org_level_9`: Cell 11
  - `org_level_10`: Node 024

**Record 2:**
  - `week_ending`: 2025-06-21
  - `position_number`: 50003667
  - `position_name`: Operations Vice President
  - `employee_number`: 100001
  - `employee_name`: Emma Hernandez
  - `location`: Adelaide
  - `region`: SA
  - `country`: AU
  - `employee_group`: Permanent
  - `salary_group`: Group 7
  - `division`: Corporate & Institutional Banking
  - `business_unit`: Human Resources
  - `team`: Human Resources Strategy
  - `sub_team`: Team 05
  - `function`: Squad D
  - `sub_function`: Pod 19
  - `org_level_8`: Unit 003
  - `org_level_9`: Cell 30
  - `org_level_10`: Node 037

**Record 3:**
  - `week_ending`: 2025-06-21
  - `position_number`: 50000226
  - `position_name`: Audit General Manager
  - `employee_number`: 100002
  - `employee_name`: Michael Brown
  - `location`: Sydney
  - `region`: NSW
  - `country`: AU
  - `employee_group`: Fixed Term
  - `salary_group`: Group 2
  - `division`: Technology
  - `business_unit`: Human Resources
  - `team`: Finance Strategy
  - `sub_team`: Team 27
  - `function`: Squad H
  - `sub_function`: Pod 9
  - `org_level_8`: Unit 030
  - `org_level_9`: Cell 22
  - `org_level_10`: Node 092

---

## Key Data Distributions

Top values for important categorical columns:

### positions.Division

- **Technology**: 6,144 records
- **Customer Banking & Wealth**: 5,913 records
- **Corporate & Institutional Banking**: 5,835 records
- **Group Functions**: 5,798 records
- **NAB Ventures**: 5,677 records
- **Business & Private Banking**: 5,633 records

### positions.Business_Unit

- **Personal Banking**: 3,724 records
- **Corporate Banking**: 3,645 records
- **NAB Ventures**: 3,597 records
- **Technology**: 3,553 records
- **Legal & Compliance**: 3,531 records
- **Wealth Management**: 3,528 records
- **Human Resources**: 3,508 records
- **Business Banking**: 3,322 records
- **Finance**: 3,322 records
- **Risk Management**: 3,270 records

### positions.Location

- **Brisbane City**: 6,261 records
- **Adelaide**: 6,115 records
- **Parramatta**: 5,942 records
- **Docklands**: 5,608 records
- **Sydney**: 5,542 records
- **Perth**: 5,532 records

### skills.Category

- **Information Technology**: 10,628 records
- **Health Care**: 3,737 records
- **Engineering**: 2,202 records
- **Science and Research**: 1,833 records
- **Finance**: 1,621 records
- **Business**: 1,538 records
- **Media and Communications**: 1,432 records
- **Analysis**: 1,262 records
- **Law, Regulation, and Compliance**: 1,134 records
- **Manufacturing and Production**: 1,111 records
- **Design**: 873 records
- **Marketing and Public Relations**: 714 records
- **Transportation, Supply Chain, and Logistics**: 698 records
- **Maintenance, Repair, and Facility Services**: 678 records
- **Architecture and Construction**: 590 records

### skills.SkillType

- **Specialized Skill**: 34,406 records
- **Certification**: 3,525 records
- **Common Skill**: 499 records

### career_pathways.career_move_type

- **progression**: 6,382 records
- **lateral**: 2,198 records

### colleague_movements.movement_type

- **lateral**: 162,954 records

### movement_fact.movement_pattern

- **50002797 → 50004078**: 3 records
- **50002343 → 50002456**: 3 records
- **50001493 → 50003144**: 3 records
- **50000958 → 50000033**: 3 records
- **50004995 → 50001479**: 2 records
- **50004993 → 50003949**: 2 records
- **50004993 → 50001713**: 2 records
- **50004983 → 50002848**: 2 records
- **50004968 → 50004778**: 2 records
- **50004966 → 50002736**: 2 records
- **50004963 → 50004233**: 2 records
- **50004963 → 50003986**: 2 records
- **50004961 → 50002968**: 2 records
- **50004960 → 50004037**: 2 records
- **50004954 → 50003293**: 2 records

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

### colleague_movements table indexes

**idx_colleague_movements_employee**
```sql
CREATE INDEX idx_colleague_movements_employee ON colleague_movements(employee_number)
```

**idx_colleague_movements_job**
```sql
CREATE INDEX idx_colleague_movements_job ON colleague_movements(jobprofile_id)
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

**idx_jobs_function**
```sql
CREATE INDEX idx_jobs_function ON jobs(JobFunction)
```

**idx_jobs_function_id**
```sql
CREATE INDEX idx_jobs_function_id ON jobs(JobFunctionID)
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

### workforce_context table indexes

**idx_workforce_context_employee**
```sql
CREATE INDEX idx_workforce_context_employee ON workforce_context(employee_number)
```

## Data Distribution Analysis

Key data patterns and distributions across business tables:

### jobs Distribution

**JobProfile** (20 unique values):

- Cloud Architect - 4: 9 (7.6%)
- Financial Controller - 3: 8 (6.7%)
- Digital Product Manager - 3: 7 (5.9%)
- Payment Systems Analyst - 0: 6 (5.0%)
- Operations Analyst - 5: 6 (5.0%)
- Legal Counsel - 4: 6 (5.0%)
- HR Business Partner - 3: 6 (5.0%)
- Financial Analyst - 0: 6 (5.0%)
- Cybersecurity Analyst - 3: 6 (5.0%)
- Credit Risk Manager - 3: 6 (5.0%)


### skills Distribution

**Skill_Name** (20 unique values):

- z/OS: 1 (5.0%)
- xVal: 1 (5.0%)
- watchOS: 1 (5.0%)
- vMix (Software): 1 (5.0%)
- tvOS: 1 (5.0%)
- t-SNE (t-distributed Stochastic Neighbor Embedding): 1 (5.0%)
- spatialNET: 1 (5.0%)
- shRNA: 1 (5.0%)
- qTest: 1 (5.0%)
- phpList: 1 (5.0%)

**Category** (20 unique values):

- Information Technology: 10,628 (29.8%)
- Health Care: 3,737 (10.5%)
- : 3,377 (9.5%)
- Engineering: 2,202 (6.2%)
- Science and Research: 1,833 (5.1%)
- Finance: 1,621 (4.5%)
- Business: 1,538 (4.3%)
- Media and Communications: 1,432 (4.0%)
- Analysis: 1,262 (3.5%)
- Law, Regulation, and Compliance: 1,134 (3.2%)

**SkillType** (3 unique values):

- Specialized Skill: 34,406 (89.5%)
- Certification: 3,525 (9.2%)
- Common Skill: 499 (1.3%)


### positions Distribution

**Division** (6 unique values):

- Technology: 6,144 (17.6%)
- Customer Banking & Wealth: 5,913 (16.9%)
- Corporate & Institutional Banking: 5,835 (16.7%)
- Group Functions: 5,798 (16.6%)
- NAB Ventures: 5,677 (16.2%)
- Business & Private Banking: 5,633 (16.1%)

**Business_Unit** (10 unique values):

- Personal Banking: 3,724 (10.6%)
- Corporate Banking: 3,645 (10.4%)
- NAB Ventures: 3,597 (10.3%)
- Technology: 3,553 (10.2%)
- Legal & Compliance: 3,531 (10.1%)
- Wealth Management: 3,528 (10.1%)
- Human Resources: 3,508 (10.0%)
- Business Banking: 3,322 (9.5%)
- Finance: 3,322 (9.5%)
- Risk Management: 3,270 (9.3%)

**Location** (6 unique values):

- Brisbane City: 6,261 (17.9%)
- Adelaide: 6,115 (17.5%)
- Parramatta: 5,942 (17.0%)
- Docklands: 5,608 (16.0%)
- Sydney: 5,542 (15.8%)
- Perth: 5,532 (15.8%)


### career_pathways Distribution

**career_move_type** (2 unique values):

- progression: 6,382 (74.4%)
- lateral: 2,198 (25.6%)

**similarity_score** (20 unique values):

- 1.0: 2,182 (57.5%)
- 0.5: 405 (10.7%)
- 0.6666666666666666: 113 (3.0%)
- 0.5172413793103449: 102 (2.7%)
- 0.5769230769230769: 93 (2.5%)
- 0.6428571428571429: 91 (2.4%)
- 0.625: 66 (1.7%)
- 0.62: 66 (1.7%)
- 0.6481481481481481: 64 (1.7%)
- 0.6: 64 (1.7%)


### job_similarities Distribution

**similarity_score** (20 unique values):

- 0.4: 10,572 (8.0%)
- 0.0: 9,896 (7.5%)
- 0.3333333333333333: 9,790 (7.4%)
- 0.3448275862068966: 8,623 (6.5%)
- 0.3793103448275862: 8,297 (6.3%)
- 0.3636363636363636: 7,276 (5.5%)
- 0.4081632653061224: 7,030 (5.3%)
- 0.4285714285714285: 6,923 (5.3%)
- 0.3620689655172414: 6,867 (5.2%)
- 0.396551724137931: 6,398 (4.9%)


### colleague_movements Distribution

**movement_type** (1 unique values):

- lateral: 162,954 (100.0%)


### movement_fact Distribution

**movement_pattern** (20 unique values):

- 50002797 → 50004078: 3 (6.8%)
- 50002343 → 50002456: 3 (6.8%)
- 50001493 → 50003144: 3 (6.8%)
- 50000958 → 50000033: 3 (6.8%)
- 50004995 → 50001479: 2 (4.5%)
- 50004993 → 50003949: 2 (4.5%)
- 50004993 → 50001713: 2 (4.5%)
- 50004983 → 50002848: 2 (4.5%)
- 50004968 → 50004778: 2 (4.5%)
- 50004966 → 50002736: 2 (4.5%)

**movement_count** (2 unique values):

- 1: 162,928 (100.0%)
- 2: 13 (0.0%)


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
SELECT DISTINCT j.JobProfile, j.JobFamily, COUNT(DISTINCT p."Position Number") as position_count
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

This comprehensive schema documentation should be used to:
1. **Inform LLMs** about database structure, relationships, and data patterns
2. **Guide query development** for webapp endpoints with performance considerations
3. **Validate data integrity** during pipeline updates and data quality checks
4. **Plan schema evolution** for future requirements and optimizations
5. **Understand business context** through movement analysis and career pathways
6. **Optimize performance** using the query recommendations and size analysis

## Analysis Summary

- **Database Analysis Date**: 2025-07-17 14:45:38
- **Tables Analyzed**: 11
- **Relationships Mapped**: 9
- **Performance Recommendations**: 4
- **Data Quality Checks**: Completeness, duplicates, referential integrity
- **Business Insights**: Movement patterns, career pathways, skill distributions