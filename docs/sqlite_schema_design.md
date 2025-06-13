# SQLite Schema Design for NAB Skill Similarity Engine
## Business Context Database

**Generated**: 2025-01-08  
**Version**: 1.1 (Updated from actual schema analysis)  
**Target**: Flask Webapp Data Layer

---

## Overview

This schema integrates 7 key datasets into a cohesive SQLite database that supports:
- **Career pathway exploration** (job similarity + business context)
- **White paper generation** (employee context + job progression)  
- **Team transition planning** (org hierarchy + workforce distribution)
- **Skills analysis** (comprehensive skills taxonomy + job mappings)

## Design Principles

1. **Simplicity over optimisation**: Readable joins, minimal denormalisation
2. **Logical relationships**: Clear foreign keys matching business understanding
3. **Query-friendly**: Support webapp filtering without complex indexing strategies
4. **Future-proof**: Schema can evolve with additional datasets

---

## Core Entity Relationships

```mermaid
erDiagram
    JOBS {
        string JobProfileID PK
        string JobProfile
        string JobID  
        string Job
        string JobFamily
        string JobFamilyGroup
    }
    
    JOB_SIMILARITIES {
        string job_from FK
        string job_to FK
        decimal similarity_score
        decimal skill_overlap_score
        integer shared_skills_count
        integer total_skills_from
        integer total_skills_to
    }
    
    POSITIONS {
        string Position_Number PK
        string JobProfileID FK
        string Employee_Number
        string Division
        string Business_Unit
        string Team
        string SubTeam
        string Function
        string SubFunction
        string Org_Level_8
        string Org_Level_9
        string Org_Level_10
        string Location
        string Rg
        string Cty
        string Employee_Group
        string Salary_Group
        string Employee_Subgroup
    }
    
    SCHEMA_METADATA {
        string key PK
        string value
        string created_at
    }
    
    SKILLS {
        string Skill_ID PK
        string Skill_Name
        string Category
        string Subcategory
        string SkillType
        string Latest_Version
    }
    
    JOB_SKILLS {
        string JobProfileID FK
        string Skill_ID FK
        string Skill_Name
        decimal Skill_Weight
    }
    
    JOBS ||--o{ JOB_SIMILARITIES : "job_from"
    JOBS ||--o{ JOB_SIMILARITIES : "job_to"
    JOBS ||--o{ POSITIONS : "JobProfileID"
    JOBS ||--o{ JOB_SKILLS : "JobProfileID"
    SKILLS ||--o{ JOB_SKILLS : "Skill_ID"
```

---

## Table Definitions

### 1. **jobs** - Job Architecture Master Data
*Source: `data/job_architecture/dummy_job_architecture.csv`*

```sql
CREATE TABLE jobs (
    JobProfileID TEXT PRIMARY KEY,           -- R0001.5 format
    JobProfile TEXT NOT NULL,               -- "Analyst - Risk Management"
    JobID TEXT,                             -- Hierarchical job code
    Job TEXT,                               -- Job title
    JobFamily TEXT,                         -- "Technology", "Risk", "Finance"
    JobFamilyGroup TEXT                     -- Higher-level grouping
);
```

**Key Insights**: 715 unique jobs, JobProfileID is our central linking key across all systems.

### 2. **job_similarities** - Pre-computed Job-to-Job Similarities
*Source: `models/2025-Q2/precompute_*/job_similarity_matrix.parquet`*

```sql
CREATE TABLE job_similarities (
    job_from TEXT NOT NULL,                 -- Source JobProfileID
    job_to TEXT NOT NULL,                   -- Target JobProfileID  
    similarity_score REAL NOT NULL,        -- Overall similarity (0-1)
    skill_overlap_score REAL,              -- Skills-specific similarity
    shared_skills_count INTEGER,           -- Number of overlapping skills
    total_skills_from INTEGER,             -- Total skills for source job
    total_skills_to INTEGER,               -- Total skills for target job
    
    PRIMARY KEY (job_from, job_to),
    FOREIGN KEY (job_from) REFERENCES jobs(JobProfileID),
    FOREIGN KEY (job_to) REFERENCES jobs(JobProfileID)
);
```

**Key Insights**: 510,510 similarity pairs with 100% coverage of all JobProfileIDs.

### 3. **positions** - Workforce Context with Full Organizational Hierarchy
*Source: `data/workforce_context/dummy_workforce_context.csv`*

```sql
CREATE TABLE positions (
    "Position Number" TEXT PRIMARY KEY,     -- Unique position identifier  
    JobProfileID TEXT,                      -- Direct link to jobs table
    "Employee Number" TEXT,                 -- Current employee (if filled)
    
    -- Organizational Hierarchy
    Division TEXT,                          -- Business division
    Business_Unit TEXT,                     -- Business unit
    Team TEXT,                              -- Team level
    SubTeam TEXT,                           -- Sub-team level
    Function TEXT,                          -- Function level
    SubFunction TEXT,                       -- Sub-function level
    Org_Level_8 TEXT,                       -- Org level 8
    Org_Level_9 TEXT,                       -- Org level 9
    Org_Level_10 TEXT,                      -- Org level 10
    
    -- Geographic Context
    Location TEXT,                          -- Location
    Rg TEXT,                               -- Region
    Cty TEXT,                              -- Country
    
    -- Employment Details
    "Employee Group" TEXT,                  -- Employee group
    "Salary Group" TEXT,                    -- Salary group
    "Employee Subgroup" TEXT,               -- Employee subgroup
    
    FOREIGN KEY (JobProfileID) REFERENCES jobs(JobProfileID)
);
```

**Design Decision**: Direct JobProfileID foreign key eliminates need for separate mapping table. Maintains full organizational hierarchy for comprehensive business context analysis.

### 4. **schema_metadata** - Database Versioning and Metadata
*Auto-generated during database creation*

```sql
CREATE TABLE schema_metadata (
    key TEXT PRIMARY KEY,                   -- Metadata key
    value TEXT NOT NULL,                    -- Metadata value
    created_at TEXT NOT NULL                -- Creation timestamp
);
```

**Key Insights**: Contains schema version (1.0), creation date, and source document reference for tracking database provenance.

### 5. **skills** - Comprehensive Skills Library
*Source: `data/skills_library/lightcast_skills_comprehensive.csv`*

```sql
CREATE TABLE skills (
    Skill_ID TEXT PRIMARY KEY,              -- Lightcast skill identifier
    Skill_Name TEXT NOT NULL,               -- "Python Programming"
    Category TEXT,                          -- "Information Technology"
    Subcategory TEXT,                       -- "Programming Languages"
    SkillType TEXT,                         -- "Specialized Skill", etc.
    Latest_Version TEXT,                    -- Version tracking
    Description TEXT,                       -- Skill description
    Info_URL TEXT,                          -- Additional information URL
    Is_Language BOOLEAN,                    -- Language skill flag
    Category_ID INTEGER,                    -- Category identifier
    Subcategory_ID INTEGER,                 -- Subcategory identifier
    Type_ID TEXT,                          -- Type identifier
    Market_Demand TEXT,                     -- Market demand indicator
    Rarity_Score REAL                       -- 0-1 scale for skill uniqueness
);
```

**Key Insights**: 38,395 skills from Lightcast API with rich taxonomy structure. Note: Most skills (37,995) have empty category, with 168 in Information Technology being the largest categorized group.

### 6. **job_skills** - Job-to-Skills Mapping
*Source: `data/input_data/job_skill_mapping.csv`*

```sql
CREATE TABLE job_skills (
    JobProfileID TEXT NOT NULL,             -- Link to jobs table
    Skill_ID TEXT NOT NULL,                 -- Link to skills table
    Skill_Weight REAL DEFAULT 1.0,         -- Importance weight (0-1)
    
    PRIMARY KEY (JobProfileID, Skill_ID),
    FOREIGN KEY (JobProfileID) REFERENCES jobs(JobProfileID),
    FOREIGN KEY (Skill_ID) REFERENCES skills(Skill_ID)
);
```

**Design Decision**: Use Skill_ID as primary relationship key. Skill_Name can be derived through JOIN with skills table, avoiding data duplication and ensuring consistency.

---

## Indexes for Webapp Performance

```sql
-- Job exploration queries
CREATE INDEX idx_jobs_family ON jobs(JobFamily);
CREATE INDEX idx_jobs_family_group ON jobs(JobFamilyGroup);

-- Similarity queries (most important)
CREATE INDEX idx_similarities_from ON job_similarities(job_from, similarity_score DESC);
CREATE INDEX idx_similarities_to ON job_similarities(job_to, similarity_score DESC);
CREATE INDEX idx_similarities_score ON job_similarities(similarity_score DESC);

-- Position filtering 
CREATE INDEX idx_position_job_mapping ON position_job_mapping(JobProfileID);
CREATE INDEX idx_positions_business_unit ON positions(Business_Unit);
CREATE INDEX idx_positions_division ON positions(Division);
CREATE INDEX idx_positions_team ON positions(Team);
CREATE INDEX idx_positions_function ON positions(Function);
CREATE INDEX idx_positions_location ON positions(Location, Rg);


-- Skills analysis
CREATE INDEX idx_job_skills_job ON job_skills(JobProfileID);
CREATE INDEX idx_job_skills_skill ON job_skills(Skill_ID);
CREATE INDEX idx_skills_category ON skills(Category, Subcategory);
```

---

## Key Webapp Query Patterns

### **1. Career Pathway Exploration**
```sql
-- "Find similar roles to Data Scientist in Technology"
SELECT j2.JobProfile, js.similarity_score, j2.JobFamily
FROM job_similarities js
JOIN jobs j1 ON js.job_from = j1.JobProfileID  
JOIN jobs j2 ON js.job_to = j2.JobProfileID
WHERE j1.JobProfile LIKE '%Data Scientist%'
  AND j2.JobFamily = 'Technology'
  AND js.similarity_score > 0.5
ORDER BY js.similarity_score DESC;
```

### **2. Geographic Opportunity Filtering**
```sql
-- "Show Melbourne Technology roles similar to my current role"
SELECT DISTINCT j.JobProfile, js.similarity_score, COUNT(p.Position_Number) as available_positions
FROM job_similarities js
JOIN jobs j ON js.job_to = j.JobProfileID
JOIN position_job_mapping pjm ON j.JobProfileID = pjm.JobProfileID
JOIN positions p ON pjm.Position_Number = p.Position_Number
WHERE js.job_from = 'R0123.4'  -- Current role
  AND j.JobFamily = 'Technology'
  AND p.Location = 'Melbourne'
  AND p.Employee_Number IS NULL  -- Vacant positions
GROUP BY j.JobProfileID, js.similarity_score
ORDER BY js.similarity_score DESC;
```

### **3. Skills Gap Analysis**
```sql
-- "What skills do I need for target role?"
SELECT s.Skill_Name, s.Category,
       CASE WHEN current_skills.Skill_ID IS NULL THEN 'MISSING' ELSE 'HAVE' END as status
FROM job_skills target_skills
JOIN skills s ON target_skills.Skill_ID = s.Skill_ID
LEFT JOIN job_skills current_skills ON current_skills.Skill_ID = target_skills.Skill_ID 
  AND current_skills.JobProfileID = 'R0123.4'  -- Current role
WHERE target_skills.JobProfileID = 'R0567.8'   -- Target role
ORDER BY status, s.Category;
```

### **4. Team Context Analysis**
```sql
-- "Who in my division has done this role?"
SELECT p.Employee_Number, p.Division, p.Business_Unit, p.Team, j.JobProfile
FROM positions p
JOIN position_job_mapping pjm ON p.Position_Number = pjm.Position_Number
JOIN jobs j ON pjm.JobProfileID = j.JobProfileID
WHERE p.Division = 'Technology'
  AND j.JobProfile LIKE '%Data%'
  AND p.Employee_Number IS NOT NULL;
```

---

## Data Integration Strategy

### **Phase 1: Core Schema Creation**
1. Create empty SQLite database with schema
2. Load job architecture data (717 records)
3. Load skills library (38K records) 
4. Load job-skill mappings (40K relationships)

### **Phase 2: Similarity Data Integration**
1. Load pre-computed job similarities (510K pairs)
2. Validate 100% JobProfileID coverage
3. Add similarity metadata and scoring

### **Phase 3: Workforce Context**
1. Load position data (5K records)
2. Create position-to-job mappings
3. Validate organisational hierarchy integrity

### **Validation Checkpoints**
- All JobProfileIDs in similarities exist in jobs table
- All Position JobProfileIDs exist in jobs table  
- No orphaned skills in job_skills table
- Org hierarchy integrity (leaders exist as positions)

---

## CLI Integration Plan

### **New Menu Structure** (extends existing `main.py`)
```
Main Menu:
1. Precompute Skill Similarities     # EXISTING
2. Generate Business Context Database # NEW  
3. Query Skill Similarities          # FUTURE
0. Exit

Business Context Menu:
1. Create SQLite schema
2. Load job architecture data
3. Load skills library data  
4. Load workforce context data
5. Load similarity matrices
6. Validate database integrity
7. Generate complete database
0. Back to main menu
```

### **Implementation Modules**
```
src/skill_similarity_engine/business_context/
├── __init__.py
├── schema_builder.py       # SQLite schema creation
├── data_loader.py          # CSV → SQLite loaders  
├── similarity_integrator.py # Parquet → SQLite
├── validator.py            # Data integrity checks
└── orchestrator.py         # CLI menu integration
```

---

## Output Location & Versioning

### **Database Output**
```
models/2025-Q2/precompute_20250608/
├── job_similarity_matrix.parquet    # EXISTING similarity data
├── job_similarity_matrix.csv        # EXISTING Power BI export
└── business_context.sqlite           # NEW comprehensive database
```

### **Benefits of CLI Generation**
- **Version consistency**: Database tied to similarity computation quarter
- **Data governance**: Controlled processing environment
- **Performance**: Pre-computed joins for fast webapp queries
- **Deployment**: Single SQLite file for webapp distribution
- **Validation**: Built-in data integrity checking

---

## Schema Evolution Strategy

### **Current Schema (v1.0)**
- Core job similarities with business context
- Basic skills taxonomy integration
- Simplified org hierarchy (3-4 levels)

### **Future Extensions (v2.0+)**
- Skills prerequisite relationships
- Career pathway history tracking  
- Workforce demand signals
- Enhanced geographic context

### **Backwards Compatibility**
- Additive schema changes only
- Version metadata in database
- Migration scripts for schema updates

---

## Performance Expectations

### **Actual Database Size**
- **jobs**: 715 records
- **job_similarities**: 510,510 records 
- **positions**: 5,000 records
- **skills**: 38,395 records
- **job_skills**: 40,170 records
- **schema_metadata**: 4 records
- **Total**: 79.5 MB SQLite database

### **Query Performance**
- **Simple filters**: <100ms (job family, location)
- **Similarity queries**: <500ms (with proper indexes)
- **Complex joins**: <2 seconds (acceptable for webapp)
- **Skills analysis**: <1 second (pre-indexed)

### **Scalability Notes**
- Current scale well within SQLite limits
- Production scale (2K jobs) → ~200MB database
- No complex optimisation needed at this scale

---

## Summary

This schema design prioritises:
✅ **Simplicity**: Clear relationships, readable queries  
✅ **Functionality**: Supports all key webapp use cases
✅ **Integration**: Clean CLI-based generation process
✅ **Performance**: Adequate speed without over-engineering
✅ **Evolution**: Can grow with additional datasets

The design directly implements your domain insights:
- Job similarities as central hub connecting to all context
- Position-workforce bridge via job mappings
- Skills library integration with job-skill relationships  
- Simplified org hierarchy without unnecessary normalisation

**Next Step**: ✅ **COMPLETED** - CLI business context generation modules created this schema successfully.

---

## Actual Implementation Analysis

**Database Generated**: 2025-06-11  
**Analysis Date**: 2025-01-08  
**Source**: `python scripts/examine_sqlite_schema.py`

### Key Findings

✅ **Schema Implementation**: All major tables implemented successfully  
✅ **Data Volume**: 79.5 MB database with 594,794 total records  
✅ **Relationships**: Foreign key constraints properly implemented  
✅ **D3.js Integration**: Successfully integrated with Flask API for real-time visualization  

### Actual Business Context
- **Top Job Families**: Banking Operations (101), Data & Analytics (99), Finance & Accounting (98)
- **Similarity Coverage**: 510,510 job-to-job similarity pairs with 100% JobProfileID coverage
- **Organizational Depth**: Full 10-level hierarchy maintained in positions table  
- **Skills Taxonomy**: 38,395 skills with rich metadata (168 in Information Technology category)

### Schema Variations from Design
1. **No separate position_job_mapping**: JobProfileID directly in positions table
2. **Enhanced skills metadata**: Additional columns for descriptions, URLs, and categorization
3. **Schema versioning**: Added schema_metadata table for database provenance
4. **Column naming**: Some columns use quoted names with spaces (e.g., "Position Number") 

erDiagram
    JOBS {
        string JobProfileID PK
        string JobProfile
        string JobID  
        string Job
        string JobFamily
        string JobFamilyGroup
    }
    
    JOB_SIMILARITIES {
        string job_from FK
        string job_to FK
        decimal similarity_score
        decimal skill_overlap_score
        integer shared_skills_count
        integer total_skills_from
        integer total_skills_to
    }
    
    POSITIONS {
        string Position_Number PK
        string JobProfileID FK
        string Employee_Number
        string Business_Unit
        string ORG_UNIT_NAME_1
        string ORG_UNIT_NAME_2
        string Location
        decimal Salary_Grade
    }
    
    SKILLS {
        string Skill_ID PK
        string Skill_Name
        string Category
        string Subcategory
        string SkillType
        string Latest_Version
    }
    
    JOB_SKILLS {
        string JobProfileID FK
        string Skill_ID FK
        string Skill_Name
        decimal Skill_Weight
    }
    
    JOBS ||--o{ JOB_SIMILARITIES : "job_from"
    JOBS ||--o{ JOB_SIMILARITIES : "job_to"
    JOBS ||--o{ POSITIONS : "JobProfileID"
    JOBS ||--o{ JOB_SKILLS : "JobProfileID"
    SKILLS ||--o{ JOB_SKILLS : "Skill_ID"