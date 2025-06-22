# SQLite Schema Design for NAB Skill Similarity Engine
## Business Context Database

**Generated**: 2025-06-21 16:33:12
**Database File**: `C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\models\2025-Q2\business_context.sqlite`
**Database Size**: 118.95 MB
**Last Modified**: 2025-06-21T12:32:16.231553

---

## Overview

This document provides comprehensive schema documentation for the NAB Skill Similarity Engine SQLite database.
The database integrates job architecture, skill taxonomies, workforce context, and pre-computed similarities
to support career pathway analysis and workforce planning.

## Quick Reference for LLMs

**Core Tables for Query Development:**

- **`career_pathways`** (17,160 records) - source_job_id, target_job_id, similarity_rank, similarity_score, career_move_type
- **`job_similarities`** (510,510 records) - job_from, job_to, similarity_score
- **`job_skills`** (40,170 records) - JobProfileID, Skill_ID, Skill_Weight
- **`jobs`** (715 records) - JobProfileID, JobProfile, JobFamily, JobFamilyGroup
- **`positions`** (35,000 records) - JobProfileID, Division, Business_Unit, Location, Team
- **`skills`** (38,430 records) - Skill_ID, Skill_Name, Category, SkillType

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
- **Total Records**: 641,989
- **Total Indexes**: 18
- **Database Size**: 118.95 MB

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

    POSITIONS {
        text Employee Number PK
        text Position Number
        text Position Name
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

### 1. **career_pathways** - 17,160 records

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

- **source_job_id**: 715 unique values (17,160 non-null), avg length 7.0
- **target_job_id**: 707 unique values (17,160 non-null), avg length 7.0
- **similarity_rank**: 24 unique values (17,160 non-null), range 1 - 24
- **similarity_score**: 427 unique values (17,160 non-null), range 0.0882 - 1.0000, avg 0.5848
- **skill_overlap_score**: 427 unique values (17,160 non-null), range 0.0882 - 1.0000, avg 0.5848
- **shared_skills_count**: 18 unique values (17,160 non-null), range 1 - 20
- **career_move_type**: 2 unique values (17,160 non-null), avg length 10.49
- **difficulty_score**: 427 unique values (17,160 non-null), range 0.0000 - 0.9118, avg 0.4152

**Sample Data by Column:**

- **source_job_id**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **target_job_id**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **similarity_rank**: `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`
- **similarity_score**: `1.0`, `0.813953488372093`, `0.8`, `0.7954545454545454`, `0.7708333333333334`, `0.7692307692307693`, `0.7543859649122807`, `0.75`, `0.7446808510638298`, `0.7413793103448276`
- **skill_overlap_score**: `1.0`, `0.4567901234567901`, `0.4444444444444444`, `0.3950617283950617`, `0.382716049382716`, `0.7543859649122807`, `0.6491228070175439`, `0.631578947368421`, `0.6140350877192983`, `0.5964912280701754`
- **shared_skills_count**: `20`, `9`, `8`, `7`, `15`, `12`, `11`, `14`, `13`, `10`
- **career_move_type**: `lateral`, `progression`
- **difficulty_score**: `0.0`, `0.5432098765432098`, `0.5555555555555556`, `0.6049382716049383`, `0.617283950617284`, `0.24561403508771928`, `0.3508771929824561`, `0.368421052631579`, `0.38596491228070173`, `0.4035087719298246`

**Sample Complete Records:**

**Record 1:**
  - `source_job_id`: R0333.4
  - `target_job_id`: R0333.5
  - `similarity_rank`: 1
  - `similarity_score`: 1.0
  - `skill_overlap_score`: 1.0
  - `shared_skills_count`: 20
  - `career_move_type`: lateral
  - `difficulty_score`: 0.0

**Record 2:**
  - `source_job_id`: R0333.4
  - `target_job_id`: R0333.3
  - `similarity_rank`: 2
  - `similarity_score`: 1.0
  - `skill_overlap_score`: 1.0
  - `shared_skills_count`: 20
  - `career_move_type`: lateral
  - `difficulty_score`: 0.0

**Record 3:**
  - `source_job_id`: R0333.4
  - `target_job_id`: R0333.2
  - `similarity_rank`: 3
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

**Sample Data by Column:**

- **JobProfileID**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **JobProfile**: `Payment Systems Analyst - 5`, `Settlement Officer - 6`, `Sales Manager - II`, `Sales Manager - 1`, `Relationship Manager - 2`, `Customer Service Representa...`, `Customer Service Representa...`, `Cloud Architect - 0`, `Digital Product Manager - III`, `Business Banker - 1`
- **JobID**: `R0001`, `R0002`, `R0003`, `R0005`, `R0007`, `R0009`, `R0010`, `R0022`, `R0023`, `R0025`
- **Job**: `Payment Systems Analyst`, `Settlement Officer`, `Sales Manager`, `Relationship Manager`, `Customer Service Representa...`, `Cloud Architect`, `Digital Product Manager`, `Business Banker`, `Chief Officer`, `Data Scientist`
- **ProfileTitleSuffix**: `Senior Manager`, `Associate`, `II`, `Team Lead`, `Senior Consultant`, `Manager`, `III`, `Consultant`, `Head of`, `Lead Consultant`
- **ManagementLevel**: `Group 2`, `Group 1`, `Group 4`, `Group 3`, `Group 6`, `Group 5`, `Group 7`, `Group NA`
- **JobSubFunctionID**: `JF0655`, `JF0559`, `JF0204`, `JF0778`, `JF0095`, `JF0128`, `JF0592`, `JF0888`, `JF0274`, `JF0474`
- **JobSubFunction**: `Data Governance`, `Machine Learning`, `Investment Banking`, `Cybersecurity`, `Portfolio Management`, `Business Continuity`, `Data Management`, `Risk Management`, `Sales`, `Software Engineering`
- **JobFunctionID**: `JF001`, `JF002`, `JF003`, `JF004`, `JF005`, `JF006`, `JF007`, `JF008`, `JF009`, `JF010`
- **JobFunction**: `Audit & Assurance`, `Banking Services`, `Business Development`, `Customer Relations`, `Data & Analytics`, `Executive Leadership`, `Facilities & Administration`, `Finance & Treasury`, `Human Resources`, `Investment Management`
- **JobCategoryID**: `JC2`, `JC1`, `JC3`, `JC10`
- **JobCategory**: `Support`, `Enabling`, `Revenue Generating`, `Executive & General Management`
- **Customer_Facing**: `Customer Facing`, `Non-Customer Facing`, ``
- **is_Banker**: `Non-Banker`, `Banker`, ``
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

### 5. **positions** - 35,000 records

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

- `JobProfileID` → `jobs.JobProfileID`

**Column Statistics:**

- **Employee Number**: 35,000 unique values (35,000 non-null), avg length 6.0
- **Position Number**: 4,997 unique values (35,000 non-null), avg length 8.0
- **Position Name**: 580 unique values (35,000 non-null), avg length 21.98
- **JobProfileID**: 628 unique values (35,000 non-null), avg length 7.0
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

**Sample Data by Column:**

- **Employee Number**: `100000`, `100001`, `100002`, `100003`, `100004`, `100005`, `100006`, `100007`, `100008`, `100009`
- **Position Number**: `50003311`, `50003667`, `50000226`, `50004844`, `50003090`, `50002029`, `50001106`, `50000237`, `50002938`, `50001289`
- **Position Name**: `Investment Principal Specia...`, `Operations Vice President`, `Audit General Manager`, `Strategy Executive Manager`, `Customer Principal Developer`, `Product Consultant`, `Markets Lead Engineer`, `Legal Executive Advisor`, `Customer Senior Engineer`, `Technology Manager`
- **JobProfileID**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0003.0`, `R0003.2`, `R0005.1`, `R0009.0`, `R0009.1`
- **Division**: `Business & Private Banking`, `Corporate & Institutional B...`, `Customer Banking & Wealth`, `Group Functions`, `NAB Ventures`, `Technology`
- **Business_Unit**: `Business Banking`, `Corporate Banking`, `Finance`, `Human Resources`, `Legal & Compliance`, `NAB Ventures`, `Personal Banking`, `Risk Management`, `Technology`, `Wealth Management`
- **Team**: `Business Banking Operations`, `Corporate Banking Operations`, `Finance Strategy`, `Human Resources Strategy`, `Legal & Compliance Strategy`, `NAB Ventures Operations`, `Personal Banking Operations`, `Risk Management Strategy`, `Technology Operations`, `Wealth Management Operations`
- **SubTeam**: `Team 15`, `Team 05`, `Team 27`, `Team 04`, `Team 17`, `Team 18`, `Team 06`, `Team 25`, `Team 20`, `Team 30`
- **Function**: `Squad A`, `Squad B`, `Squad C`, `Squad D`, `Squad E`, `Squad F`, `Squad G`, `Squad H`, `Squad I`, `Squad J`
- **SubFunction**: `Pod 15`, `Pod 19`, `Pod 9`, `Pod 17`, `Pod 18`, `Pod 1`, `Pod 13`, `Pod 5`, `Pod 8`, `Pod 11`
- **Org_Level_8**: `Unit 038`, `Unit 003`, `Unit 030`, `Unit 025`, `Unit 028`, `Unit 039`, `Unit 026`, `Unit 036`, `Unit 006`, `Unit 009`
- **Org_Level_9**: `Cell 11`, `Cell 30`, `Cell 22`, `Cell 13`, `Cell 25`, `Cell 17`, `Cell 09`, `Cell 01`, `Cell 18`, `Cell 28`
- **Org_Level_10**: `Node 024`, `Node 037`, `Node 092`, `Node 077`, `Node 023`, `Node 034`, `Node 010`, `Node 084`, `Node 098`, `Node 032`
- **Location**: `Adelaide`, `Brisbane City`, `Docklands`, `Parramatta`, `Perth`, `Sydney`
- **Rg**: `SA`, `QLD`, `VIC`, `NSW`, `WA`
- **Cty**: `AU`
- **Employee Group**: `Fixed Term`, `Permanent`, `Casual`, `Contractor`
- **Salary Group**: `Group 7`, `Group 2`, `Group 5`, `External`, `Group 1`, `Group 4`, `Group 6`, `Group 3`, `Casual`
- **Employee Subgroup**: `Full Time`, `Casual`, `Part Time`

**Sample Complete Records:**

**Record 1:**
  - `Employee Number`: 100000
  - `Position Number`: 50003311
  - `Position Name`: Investment Principal Specialist
  - `JobProfileID`: R0242.3
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
  - `JobProfileID`: R0306.0
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
  - `JobProfileID`: R0304.2
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
- **value**: `1.0`, `2025-06-21T12:31:51.523720`, `docs/sqlite_schema_design.md`, `NAB Skill Similarity Engine...`
- **created_at**: `2025-06-21T12:31:51.523720`

**Sample Complete Records:**

**Record 1:**
  - `key`: schema_version
  - `value`: 1.0
  - `created_at`: 2025-06-21T12:31:51.523720

**Record 2:**
  - `key`: created_date
  - `value`: 2025-06-21T12:31:51.523720
  - `created_at`: 2025-06-21T12:31:51.523720

**Record 3:**
  - `key`: source_document
  - `value`: docs/sqlite_schema_design.md
  - `created_at`: 2025-06-21T12:31:51.523720

---

### 7. **skills** - 38,430 records

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

**Sample Data by Column:**

- **Skill_ID**: `BGS1024316C916ACCFA3`, `BGS105C99F084505B956`, `BGS1080D1F8CED414379`, `BGS10AB6DEBB81A2E88C`, `BGS10B5E145CA48862FC`, `BGS10CBE4935DDCAE5AD`, `BGS10EE289B9FDE2C4B1`, `BGS10F3F05054C5731C2`, `BGS10F94E4049444B523`, `BGS110587665F051DF29`
- **Skill_Name**: `DX Spectrum`, `Microsoft Sysprep`, `Application Remediation`, `Clinical Assay`, `Welding Tips`, `Apoptosis`, `Investment Account Management`, `GPS Data`, `Bill Of Materials`, `Video Remote Interpreting (...`
- **Category**: ``, `Administration`, `Agriculture, Horticulture, ...`, `Analysis`, `Architecture and Construction`, `Business`, `Customer and Client Support`, `Design`, `Economics, Policy, and Soci...`, `Education and Training`
- **Subcategory**: ``, `Administrative Support and ...`, `Dictation`, `Document Management`, `Office Management`, `Office and Productivity Equ...`, `Office and Productivity Sof...`, `Scheduling`, `Agricultural Management and...`, `Agricultural Research and A...`
- **SkillType**: `Specialized Skill`, `Common Skill`, `Certification`
- **Latest_Version**: `8.5`, `9.31`, `8.4`, `8.2`, `8.6`, `8.11`, `8.27`, `8.3`, `8.8`, `8.9`
- **category_id**: `17`, `30`, `21`, `13`, `32`, `14`, `12`, `4`, `16`, `23`
- **description**: ``, `Microsoft Sysprep is a util...`, `Application Remediation ref...`, `Clinical Assay refers to a ...`, `Welding Tips refers to the ...`, `Apoptosis is a process of p...`, `Investment Account Manageme...`, `GPS Data refers to informat...`, `A Bill of Materials (BOM) i...`, `Video Remote Interpreting (...`
- **Info_URL**: `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`
- **Is_Language**: `0`, `1`
- **subcategory_id**: `411`, `476`, `477`, `621`, `542`, `622`, `281`, `422`, `633`, `487`
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

### skills.SkillType

- **Specialized Skill**: 34,406 records
- **Certification**: 3,525 records
- **Common Skill**: 499 records

### career_pathways.career_move_type

- **progression**: 14,962 records
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

This schema documentation should be used to:
1. **Inform LLMs** about database structure and relationships
2. **Guide query development** for webapp endpoints
3. **Validate data integrity** during pipeline updates
4. **Plan schema evolution** for future requirements

**Last Updated**: 2025-06-21 16:33:12