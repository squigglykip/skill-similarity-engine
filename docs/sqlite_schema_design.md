# SQLite Schema Design for NAB Skill Similarity Engine
## Business Context Database

**Generated**: 2025-06-15 13:21:03
**Database File**: `c:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\models\2025-Q2\business_context.sqlite`
**Database Size**: 80.89 MB
**Last Modified**: 2025-06-14T14:45:23.063359

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

**Column Statistics:**

- **source_job_id**: 715 unique values (8,580 non-null), avg length 7.0
- **target_job_id**: 699 unique values (8,580 non-null), avg length 7.0
- **similarity_rank**: 12 unique values (8,580 non-null), range 1 - 12
- **similarity_score**: 325 unique values (8,580 non-null), range 0.1389 - 1.0000, avg 0.6641
- **skill_overlap_score**: 325 unique values (8,580 non-null), range 0.1389 - 1.0000, avg 0.6641
- **shared_skills_count**: 17 unique values (8,580 non-null), range 2 - 20
- **career_move_type**: 2 unique values (8,580 non-null), avg length 9.98
- **difficulty_score**: 325 unique values (8,580 non-null), range 0.0000 - 0.8611, avg 0.3359

**Sample Data by Column:**

- **source_job_id**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **target_job_id**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **similarity_rank**: `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`
- **similarity_score**: `1.0`, `0.813953488372093`, `0.8`, `0.7954545454545454`, `0.7708333333333334`, `0.7692307692307693`, `0.7543859649122807`, `0.75`, `0.7446808510638298`, `0.7413793103448276`
- **skill_overlap_score**: `1.0`, `0.5294117647058824`, `0.4264705882352941`, `0.4117647058823529`, `0.673469387755102`, `0.5510204081632653`, `0.3823529411764705`, `0.3235294117647059`, `0.2352941176470588`, `0.2058823529411764`
- **shared_skills_count**: `20`, `10`, `8`, `13`, `11`, `7`, `6`, `4`, `5`, `3`
- **career_move_type**: `lateral`, `progression`
- **difficulty_score**: `0.0`, `0.47058823529411764`, `0.5735294117647058`, `0.5882352941176471`, `0.326530612244898`, `0.44897959183673475`, `0.6176470588235294`, `0.6764705882352942`, `0.7647058823529412`, `0.7941176470588236`

**Sample Complete Records:**

**Record 1:**
  - `source_job_id`: R0001.5
  - `target_job_id`: R0001.6
  - `similarity_rank`: 1
  - `similarity_score`: 1.0
  - `skill_overlap_score`: 1.0
  - `shared_skills_count`: 20
  - `career_move_type`: lateral
  - `difficulty_score`: 0.0

**Record 2:**
  - `source_job_id`: R0001.5
  - `target_job_id`: R0053.0
  - `similarity_rank`: 2
  - `similarity_score`: 0.5294117647058824
  - `skill_overlap_score`: 0.5294117647058824
  - `shared_skills_count`: 10
  - `career_move_type`: progression
  - `difficulty_score`: 0.47058823529411764

**Record 3:**
  - `source_job_id`: R0001.5
  - `target_job_id`: R0053.1
  - `similarity_rank`: 3
  - `similarity_score`: 0.5294117647058824
  - `skill_overlap_score`: 0.5294117647058824
  - `shared_skills_count`: 10
  - `career_move_type`: progression
  - `difficulty_score`: 0.47058823529411764

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

**Column Statistics:**

- **job_from**: 715 unique values (510,510 non-null), avg length 7.0
- **job_to**: 715 unique values (510,510 non-null), avg length 7.0
- **similarity_score**: 1,106 unique values (510,510 non-null), range 0.0000 - 1.0000, avg 0.3419
- **skill_overlap_score**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **shared_skills_count**: 0 unique values (0 non-null), range 0 - 0
- **total_skills_from**: 0 unique values (0 non-null), range 0 - 0
- **total_skills_to**: 0 unique values (0 non-null), range 0 - 0

**Sample Data by Column:**

- **job_from**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **job_to**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **similarity_score**: `1.0`, `0.8604651162790697`, `0.813953488372093`, `0.8048780487804879`, `0.8`, `0.7959183673469388`, `0.7954545454545454`, `0.7906976744186046`, `0.7843137254901961`, `0.78`

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

**Column Statistics:**

- **JobProfileID**: 715 unique values (40,170 non-null), avg length 7.0
- **Skill_ID**: 2,091 unique values (40,170 non-null), avg length 20.0
- **Skill_Weight**: 1 unique values (40,170 non-null), range 1.0000 - 1.0000, avg 1.0000

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

**Column Statistics:**

- **JobProfileID**: 715 unique values (715 non-null), avg length 7.0
- **JobProfile**: 336 unique values (715 non-null), avg length 33.44
- **JobID**: 240 unique values (715 non-null), avg length 5.0
- **Job**: 53 unique values (715 non-null), avg length 19.98
- **JobFamily**: 8 unique values (715 non-null), avg length 19.06
- **JobFamilyGroup**: 7 unique values (715 non-null), avg length 14.76

**Sample Data by Column:**

- **JobProfileID**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **JobProfile**: `Analyst - Data Governance S...`, `Data Scientist - Manager`, `Senior Associate Executive ...`, `Analyst - Executive Director`, `Systems Analyst - Director`, `Graduate - Financial Analyst`, `Senior Associate Operations...`, `Graduate - Executive Director`, `Senior Associate Budget Ana...`, `Employee Relations Speciali...`
- **JobID**: `J0001`, `J0002`, `J0003`, `J0005`, `J0007`, `J0009`, `J0010`, `J0022`, `J0023`, `J0025`
- **Job**: `Data Governance Specialist`, `Data Scientist`, `Executive Director`, `Systems Analyst`, `Financial Analyst`, `Operations Analyst`, `Budget Analyst`, `Employee Relations Specialist`, `Organisational Development ...`, `General Manager`
- **JobFamily**: `Banking Operations`, `Customer Service & Sales`, `Data & Analytics`, `Executive Leadership`, `Finance & Accounting`, `Human Resources`, `Risk & Compliance`, `Technology & Engineering`
- **JobFamilyGroup**: `Customer & Commercial`, `Executive & Leadership`, `Finance`, `Operations`, `Risk & Control Functions`, `Support Functions`, `Technology`

**Sample Complete Records:**

**Record 1:**
  - `JobProfileID`: R0001.5
  - `JobProfile`: Analyst - Data Governance Specialist
  - `JobID`: J0001
  - `Job`: Data Governance Specialist
  - `JobFamily`: Data & Analytics
  - `JobFamilyGroup`: Technology

**Record 2:**
  - `JobProfileID`: R0001.6
  - `JobProfile`: Data Scientist - Manager
  - `JobID`: J0001
  - `Job`: Data Scientist
  - `JobFamily`: Data & Analytics
  - `JobFamilyGroup`: Technology

**Record 3:**
  - `JobProfileID`: R0002.0
  - `JobProfile`: Senior Associate Executive Director
  - `JobID`: J0002
  - `Job`: Executive Director
  - `JobFamily`: Executive Leadership
  - `JobFamilyGroup`: Executive & Leadership

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

**Column Statistics:**

- **Position Number**: 5,000 unique values (5,000 non-null), avg length 8.0
- **JobProfileID**: 628 unique values (5,000 non-null), avg length 7.0
- **Employee Number**: 3,501 unique values (5,000 non-null), avg length 5.6
- **Division**: 6 unique values (5,000 non-null), avg length 20.27
- **Business_Unit**: 10 unique values (5,000 non-null), avg length 14.4
- **Team**: 10 unique values (5,000 non-null), avg length 24.52
- **SubTeam**: 30 unique values (5,000 non-null), avg length 7.0
- **Function**: 26 unique values (5,000 non-null), avg length 7.0
- **SubFunction**: 20 unique values (5,000 non-null), avg length 5.54
- **Org_Level_8**: 50 unique values (5,000 non-null), avg length 8.0
- **Org_Level_9**: 30 unique values (5,000 non-null), avg length 7.0
- **Org_Level_10**: 100 unique values (5,000 non-null), avg length 8.0
- **Location**: 6 unique values (5,000 non-null), avg length 8.51
- **Rg**: 5 unique values (5,000 non-null), avg length 2.66
- **Cty**: 1 unique values (5,000 non-null), avg length 2.0
- **Employee Group**: 5 unique values (5,000 non-null), avg length 6.15
- **Salary Group**: 9 unique values (5,000 non-null), avg length 7.0
- **Employee Subgroup**: 4 unique values (5,000 non-null), avg length 5.6

**Sample Data by Column:**

- **Position Number**: `50000000`, `50000001`, `50000002`, `50000003`, `50000004`, `50000005`, `50000006`, `50000007`, `50000008`, `50000009`
- **JobProfileID**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0003.0`, `R0003.2`, `R0005.1`, `R0009.0`, `R0009.1`
- **Employee Number**: `102031.0`, `100121.0`, `100644.0`, `102831.0`, `101745.0`, `102052.0`, `101642.0`, `103249.0`, `102673.0`, `102992.0`
- **Division**: `Business & Private Banking`, `Corporate & Institutional B...`, `Customer Banking & Wealth`, `Group Functions`, `NAB Ventures`, `Technology`
- **Business_Unit**: `Business Banking`, `Corporate Banking`, `Finance`, `Human Resources`, `Legal & Compliance`, `NAB Ventures`, `Personal Banking`, `Risk Management`, `Technology`, `Wealth Management`
- **Team**: `Business Banking Operations`, `Corporate Banking Operations`, `Finance Strategy`, `Human Resources Strategy`, `Legal & Compliance Strategy`, `NAB Ventures Operations`, `Personal Banking Operations`, `Risk Management Strategy`, `Technology Operations`, `Wealth Management Operations`
- **SubTeam**: `Team 20`, `Team 02`, `Team 19`, `Team 27`, `Team 15`, `Team 22`, `Team 13`, `Team 12`, `Team 25`, `Team 05`
- **Function**: `Squad A`, `Squad B`, `Squad C`, `Squad D`, `Squad E`, `Squad F`, `Squad G`, `Squad H`, `Squad I`, `Squad J`
- **SubFunction**: `Pod 18`, `Pod 12`, `Pod 15`, `Pod 5`, `Pod 13`, `Pod 2`, `Pod 20`, `Pod 1`, `Pod 9`, `Pod 4`
- **Org_Level_8**: `Unit 047`, `Unit 011`, `Unit 020`, `Unit 040`, `Unit 005`, `Unit 017`, `Unit 035`, `Unit 048`, `Unit 038`, `Unit 008`
- **Org_Level_9**: `Cell 12`, `Cell 21`, `Cell 22`, `Cell 17`, `Cell 14`, `Cell 07`, `Cell 11`, `Cell 09`, `Cell 16`, `Cell 18`
- **Org_Level_10**: `Node 060`, `Node 067`, `Node 023`, `Node 073`, `Node 039`, `Node 065`, `Node 078`, `Node 033`, `Node 014`, `Node 027`
- **Location**: `Adelaide`, `Brisbane City`, `Docklands`, `Parramatta`, `Perth`, `Sydney`
- **Rg**: `SA`, `QLD`, `VIC`, `NSW`, `WA`
- **Cty**: `AU`
- **Employee Group**: `Casual`, `Contractor`, `Permanent`, `Fixed Term`, ``
- **Salary Group**: `Group 7`, `Group 1`, `Group 5`, `Group 6`, `Group 3`, `External`, `Group 4`, `Group 2`, `Casual`
- **Employee Subgroup**: `Part Time`, `Full Time`, `Casual`, ``

**Sample Complete Records:**

**Record 1:**
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

**Record 2:**
  - `Position Number`: 50000001
  - `JobProfileID`: R0400.6
  - `Employee Number`: 100121.0
  - `Division`: NAB Ventures
  - `Business_Unit`: Finance
  - `Team`: Business Banking Operations
  - `SubTeam`: Team 02
  - `Function`: Squad Y
  - `SubFunction`: Pod 12
  - `Org_Level_8`: Unit 011
  - `Org_Level_9`: Cell 21
  - `Org_Level_10`: Node 067
  - `Location`: Parramatta
  - `Rg`: NSW
  - `Cty`: AU
  - `Employee Group`: Contractor
  - `Salary Group`: Group 1
  - `Employee Subgroup`: Part Time

**Record 3:**
  - `Position Number`: 50000002
  - `JobProfileID`: R0465.3
  - `Employee Number`: 100644.0
  - `Division`: NAB Ventures
  - `Business_Unit`: Business Banking
  - `Team`: Legal & Compliance Strategy
  - `SubTeam`: Team 19
  - `Function`: Squad U
  - `SubFunction`: Pod 18
  - `Org_Level_8`: Unit 020
  - `Org_Level_9`: Cell 22
  - `Org_Level_10`: Node 023
  - `Location`: Parramatta
  - `Rg`: NSW
  - `Cty`: AU
  - `Employee Group`: Contractor
  - `Salary Group`: Group 5
  - `Employee Subgroup`: Full Time

---

### 6. **schema_metadata** - 4 records

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

**Sample Data by Column:**

- **key**: `created_date`, `purpose`, `schema_version`, `source_document`
- **value**: `1.0`, `2025-06-13T18:36:07.482003`, `docs/sqlite_schema_design.md`, `NAB Skill Similarity Engine...`
- **created_at**: `2025-06-13T18:36:07.482003`

**Sample Complete Records:**

**Record 1:**
  - `key`: schema_version
  - `value`: 1.0
  - `created_at`: 2025-06-13T18:36:07.482003

**Record 2:**
  - `key`: created_date
  - `value`: 2025-06-13T18:36:07.482003
  - `created_at`: 2025-06-13T18:36:07.482003

**Record 3:**
  - `key`: source_document
  - `value`: docs/sqlite_schema_design.md
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

**Column Statistics:**

- **Skill_ID**: 38,395 unique values (38,395 non-null), avg length 20.0
- **Skill_Name**: 38,395 unique values (38,395 non-null), avg length 19.68
- **Category**: 29 unique values (38,395 non-null), avg length 0.2
- **Subcategory**: 191 unique values (38,395 non-null), avg length 0.23
- **SkillType**: 4 unique values (38,395 non-null), avg length 1.64
- **Latest_Version**: 48 unique values (38,395 non-null), avg length 3.98
- **Description**: 2,422 unique values (38,395 non-null), avg length 24.08
- **Info_URL**: 3,731 unique values (38,395 non-null), avg length 5.83
- **Category_ID**: 29 unique values (38,395 non-null), range 0 - 0
- **Subcategory_ID**: 187 unique values (38,395 non-null), range 100 - 0
- **Type_ID**: 4 unique values (38,395 non-null), avg length 0.29
- **Market_Demand**: 1 unique values (38,395 non-null), avg length 0
- **Rarity_Score**: 1 unique values (38,395 non-null), range 0.0000 - 0.0000, avg 0.0000

**Sample Data by Column:**

- **Skill_ID**: `BGS1024316C916ACCFA3`, `BGS105C99F084505B956`, `BGS1080D1F8CED414379`, `BGS10AB6DEBB81A2E88C`, `BGS10B5E145CA48862FC`, `BGS10CBE4935DDCAE5AD`, `BGS10EE289B9FDE2C4B1`, `BGS10F3F05054C5731C2`, `BGS10F94E4049444B523`, `BGS110587665F051DF29`
- **Skill_Name**: `DX Spectrum`, `Microsoft Sysprep`, `Application Remediation`, `Clinical Assay`, `Welding Tips`, `Apoptosis`, `Investment Account Management`, `GPS Data`, `Bill Of Materials`, `Video Remote Interpreting (...`
- **Category**: ``, `Administration`, `Analysis`, `Architecture and Construction`, `Business`, `Customer and Client Support`, `Design`, `Education and Training`, `Energy and Utilities`, `Engineering`
- **Subcategory**: ``, `Administrative Support and ...`, `Document Management`, `Office Management`, `Office and Productivity Equ...`, `Office and Productivity Sof...`, `Scheduling`, `Data Analysis`, `Data Science`, `Data Visualization`
- **SkillType**: `Specialized Skill`, ``, `Certification`, `Common Skill`
- **Latest_Version**: `8.5`, `9.31`, `8.4`, `8.2`, `8.6`, `8.11`, `8.27`, `8.3`, `8.8`, `8.9`
- **Description**: ``, `Respiratory diseases, or lu...`, `In law as practiced in coun...`, `A presentation conveys info...`, `A fuel is any material that...`, `A cardiac stress test is a ...`, `Micromachines are mechanica...`, `Phlebotomy is the process o...`, `A topical medication is a m...`, `A complication in medicine,...`
- **Info_URL**: `https://lightcast.io/open-s...`, ``, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`
- **Is_Language**: `0`, ``, `1`
- **Category_ID**: `17`, ``, `14`, `7`, `19`, `0`, `21`, `6`, `11`, `1`
- **Subcategory_ID**: `411`, ``, `491`, `289`, `175`, `494`, `345`, `507`, `177`, `447`
- **Type_ID**: `ST1`, ``, `ST3`, `ST2`
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
  - `Description`: 
  - `Info_URL`: https://lightcast.io/open-skills/skills/BGS1024...
  - `Is_Language`: 0
  - `Category_ID`: 17
  - `Subcategory_ID`: 411
  - `Type_ID`: ST1
  - `Market_Demand`: 
  - `Rarity_Score`: 

**Record 2:**
  - `Skill_ID`: BGS105C99F084505B956
  - `Skill_Name`: Microsoft Sysprep
  - `Category`: 
  - `Subcategory`: 
  - `SkillType`: 
  - `Latest_Version`: 9.31
  - `Description`: 
  - `Info_URL`: 
  - `Is_Language`: 
  - `Category_ID`: 
  - `Subcategory_ID`: 
  - `Type_ID`: 
  - `Market_Demand`: 
  - `Rarity_Score`: 

**Record 3:**
  - `Skill_ID`: BGS1080D1F8CED414379
  - `Skill_Name`: Application Remediation
  - `Category`: 
  - `Subcategory`: 
  - `SkillType`: 
  - `Latest_Version`: 9.31
  - `Description`: 
  - `Info_URL`: 
  - `Is_Language`: 
  - `Category_ID`: 
  - `Subcategory_ID`: 
  - `Type_ID`: 
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

**Last Updated**: 2025-06-15 13:21:03