# V1 → V2 Schema Migration Guide ("Rosetta Stone")

**Purpose**: Comprehensive mapping guide for updating all SQL queries from V1 to V2 database schema.

**Critical**: ALL existing SQL queries in `@webapp/sql/` must be updated to work with V2 schema before webapp can function.

---

## 🔄 **Table Mappings**

### **1. Jobs Table**
```sql
-- V1 Schema
jobs
├── JobProfileID (PRIMARY KEY)     → JobProfileID (same)
├── JobProfile                     → job_title  
├── JobFunction                    → job_function
├── JobFunctionID                  → job_function_id
├── ManagementLevel                → management_level
├── JobCategory                    → job_category
├── JobSubFunction                 → job_sub_function
└── JobCluster                     → (REMOVED - use analytics_job_families)

-- V2 Schema  
core_job_architecture
├── JobProfileID (PRIMARY KEY)     
├── job_title                      
├── job_function                   
├── job_function_id                
├── management_level               
├── job_category                   
├── job_sub_function               
├── job_description                (NEW)
├── job_level                      (NEW)
├── reports_to_job_id              (NEW)
├── created_date                   (NEW)
└── last_updated                   (NEW)
```

### **2. Skills Table**
```sql
-- V1 Schema
skills
├── Skill_ID (PRIMARY KEY)         → Skill_ID (same)
├── Skill_Name                     → skill_name
├── Category                       → primary_category  
├── Subcategory                    → secondary_category
├── SkillType                      → skill_type
└── Description                    → skill_description

-- V2 Schema
core_skills_taxonomy  
├── Skill_ID (PRIMARY KEY)         
├── skill_name                     
├── primary_category               
├── secondary_category             
├── tertiary_category              (NEW)
├── skill_type                     
├── skill_description              
├── skill_level                    (NEW)
├── industry_relevance             (NEW)
├── technology_stack               (NEW)
├── certification_available        (NEW)
├── created_date                   (NEW)
└── last_updated                   (NEW)
```

### **3. Job-Skills Relationship**
```sql
-- V1 Schema
job_skills
├── JobProfileID (FOREIGN KEY)     → job_profile_id
├── Skill_ID (FOREIGN KEY)         → skill_id  
├── Skill_Weight                   → proficiency_requirement
└── [Composite Primary Key]        → [Composite Primary Key]

-- V2 Schema  
core_job_skill_requirements
├── job_profile_id (FOREIGN KEY)   
├── skill_id (FOREIGN KEY)         
├── proficiency_requirement        
├── is_defining_skill              (NEW)
├── skill_category                 (NEW)
├── importance_score               (NEW)
├── created_date                   (NEW)
└── last_updated                   (NEW)
```

### **4. Positions/Workforce**
```sql
-- V1 Schema
positions
├── PositionID (PRIMARY KEY)       → position_id
├── JobProfileID (FOREIGN KEY)     → job_profile_id
├── CompanyOrganisationID          → organisation_id
├── CompanyDivisionID              → division_id  
├── CompanyBusinessUnitID          → business_unit_id
├── CompanyLocationID              → location_id
├── Position Number                → position_number
├── Division                       → division_name
├── Business_Unit                  → business_unit_name
├── Location                       → location_name
└── Rg                             → region

-- V2 Schema
core_workforce_current
├── position_id (PRIMARY KEY)      
├── job_profile_id (FOREIGN KEY)   
├── organisation_id                
├── division_id                    
├── business_unit_id               
├── location_id                    
├── position_number                
├── division_name                  
├── business_unit_name             
├── location_name                  
├── region                         
├── employee_level                 (NEW)
├── employment_type                (NEW)
├── start_date                     (NEW)
├── end_date                       (NEW)
├── is_active                      (NEW)
├── created_date                   (NEW)
└── last_updated                   (NEW)
```

### **5. Job Similarities (MAJOR CHANGE)**
```sql
-- V1 Schema
job_similarities
├── job_from (FOREIGN KEY)         → job_from (same)
├── job_to (FOREIGN KEY)           → job_to (same)
├── similarity_score               → enhanced_similarity_score
└── [Composite Primary Key]        → [Composite Primary Key]

-- V2 Schema (ENHANCED)
analytics_job_similarities
├── job_from (FOREIGN KEY)         
├── job_to (FOREIGN KEY)           
├── enhanced_similarity_score      (REPLACES similarity_score)
├── rarity_weighted_score          (NEW)
├── shared_defining_skills_count   (NEW)
├── total_skills_compared          (NEW)
├── similarity_rank                (NEW)
├── skill_gap_analysis             (NEW)
├── transferability_score          (NEW)
├── created_date                   (NEW)
└── last_updated                   (NEW)
```

### **6. Career Pathways (REPLACED WITH ANALYTICS)**
```sql
-- V1 Schema (PRE-COMPUTED TABLE - DEPRECATED)
career_pathways
├── source_job_id                  → analytics_job_similarities.job_from
├── target_job_id                  → analytics_job_similarities.job_to  
├── similarity_score               → analytics_job_similarities.enhanced_similarity_score
├── career_move_type               → analytics_movement_patterns.movement_type
├── difficulty_score               → analytics_movement_patterns.transition_difficulty
└── shared_skills_count            → analytics_job_similarities.shared_defining_skills_count

-- V2 Schema (DYNAMIC QUERIES FROM ANALYTICS TABLES)
analytics_job_similarities        (For similarity-based pathways)
analytics_movement_patterns       (For historical movement data)
analytics_pathway_predictions     (For ML-predicted pathways)
```

---

## 🔧 **Query Pattern Changes**

### **1. Basic Job Queries**
```sql
-- BEFORE (V1)
SELECT JobProfileID, JobProfile, JobFunction 
FROM jobs 
WHERE JobFunction = ?;

-- AFTER (V2) - Database-First, Fail-Fast
SELECT JobProfileID, job_title, job_function 
FROM core_job_architecture 
WHERE job_function = ? 
  AND job_title IS NOT NULL;  -- FAIL-FAST validation
```

### **2. Skills Queries**
```sql
-- BEFORE (V1)
SELECT Skill_Name, Category, Subcategory 
FROM skills 
WHERE Category = ?;

-- AFTER (V2) - Enhanced with new fields
SELECT skill_name, primary_category, secondary_category, tertiary_category
FROM core_skills_taxonomy 
WHERE primary_category = ? 
  AND skill_name IS NOT NULL;  -- FAIL-FAST validation
```

### **3. Job-Skills Relationships**
```sql
-- BEFORE (V1)  
SELECT s.Skill_Name, js.Skill_Weight
FROM job_skills js
JOIN skills s ON js.Skill_ID = s.Skill_ID
WHERE js.JobProfileID = ?;

-- AFTER (V2) - Enhanced with defining skills
SELECT st.skill_name, jsr.proficiency_requirement, jsr.is_defining_skill
FROM core_job_skill_requirements jsr
INNER JOIN core_skills_taxonomy st ON jsr.skill_id = st.Skill_ID
WHERE jsr.job_profile_id = ? 
  AND st.skill_name IS NOT NULL;  -- FAIL-FAST validation
```

### **4. Similarity Queries (MAJOR ENHANCEMENT)**
```sql
-- BEFORE (V1) - Basic similarity
SELECT j.JobProfile, js.similarity_score
FROM job_similarities js
JOIN jobs j ON js.job_to = j.JobProfileID  
WHERE js.job_from = ?
ORDER BY js.similarity_score DESC;

-- AFTER (V2) - Enhanced analytics  
SELECT ja.job_title, 
       js.enhanced_similarity_score,
       js.rarity_weighted_score,
       js.shared_defining_skills_count,
       js.total_skills_compared
FROM analytics_job_similarities js
INNER JOIN core_job_architecture ja ON js.job_to = ja.JobProfileID
WHERE js.job_from = ?
  AND js.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
ORDER BY js.enhanced_similarity_score DESC;
```

### **5. Career Pathways (COMPLETELY NEW APPROACH)**
```sql
-- BEFORE (V1) - Pre-computed table
SELECT target_job_id, similarity_score, career_move_type
FROM career_pathways  
WHERE source_job_id = ?
ORDER BY similarity_score DESC;

-- AFTER (V2) - Dynamic analytics queries
SELECT js.job_to,
       js.enhanced_similarity_score,
       mp.movement_type,
       mp.transition_difficulty,
       pp.model_agreement_fraction
FROM analytics_job_similarities js
LEFT JOIN analytics_movement_patterns mp 
    ON js.job_from = mp.from_job_profile_id 
    AND js.job_to = mp.to_job_profile_id
LEFT JOIN analytics_pathway_predictions pp
    ON js.job_from = pp.from_job_profile_id
    AND js.job_to = pp.to_job_profile_id  
WHERE js.job_from = ?
  AND js.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST validation
ORDER BY js.enhanced_similarity_score DESC;
```

---

## 🆕 **New V2-Only Analytics Capabilities**

### **Analytics Tables (No V1 Equivalent)**
```sql
-- Job Intelligence
analytics_job_defining_skills      -- Skills that define each job role
analytics_skill_rarity             -- Market rarity and demand analysis

-- Movement Intelligence  
analytics_movement_patterns        -- Historical workforce movements
analytics_pathway_predictions      -- ML-predicted career transitions

-- Clustering Intelligence
analytics_job_families             -- DBSCAN job clustering (20 families)
analytics_skill_bundles            -- Skills clustering (27 bundles)

-- Trend Intelligence
analytics_skill_demand_trends      -- Skill velocity and CAGR analysis
analytics_specialized_skills       -- Emerging/specialized skills

-- Quality Metrics
analytics_bundle_characteristics   -- Bundle silhouette scores
analytics_job_family_characteristics -- Family quality metrics
```

### **New Query Patterns**
```sql
-- Defining Skills for Job (NEW)
SELECT skill_name, defining_score, rarity_percentile
FROM analytics_job_defining_skills jds
INNER JOIN core_skills_taxonomy st ON jds.skill_id = st.Skill_ID
WHERE jds.job_profile_id = ?
ORDER BY jds.defining_score DESC;

-- Skill Rarity Analysis (NEW)
SELECT skill_name, rarity_score, market_demand_score, percentile_rank
FROM analytics_skill_rarity sr
INNER JOIN core_skills_taxonomy st ON sr.skill_id = st.Skill_ID
WHERE sr.rarity_score >= ?
ORDER BY sr.rarity_score DESC;

-- Job Family Clustering (NEW)
SELECT cluster_id, cluster_label, silhouette_score
FROM analytics_job_families jf
INNER JOIN analytics_job_family_characteristics jfc ON jf.cluster_id = jfc.cluster_id
WHERE jf.job_profile_id = ?;
```

---

## ⚠️ **Breaking Changes**

### **1. Removed Tables/Columns**
- ❌ `career_pathways` table (replaced with dynamic analytics queries)
- ❌ `jobs.JobCluster` (replaced with `analytics_job_families`)
- ❌ Direct similarity lookups (enhanced with rarity weighting)

### **2. Renamed Fields**
- `JobProfile` → `job_title`
- `Skill_Name` → `skill_name` 
- `Category` → `primary_category`
- `Subcategory` → `secondary_category`
- `similarity_score` → `enhanced_similarity_score`

### **3. New Required Joins**
- All queries must use V2 table names (`core_*`, `analytics_*`)
- Skills queries should leverage rarity analysis where applicable
- Job similarities must use enhanced scores, not basic similarity

### **4. Performance Changes**
- V2 has 45+ strategic indexes for sub-100ms performance
- Analytics tables enable complex queries without performance degradation
- Some V1 direct lookups now require joins (but are indexed)

---

## ✅ **Migration Checklist**

### **Phase 0.1: Table Name Updates**
- [ ] Replace `jobs` → `core_job_architecture`
- [ ] Replace `skills` → `core_skills_taxonomy`
- [ ] Replace `job_skills` → `core_job_skill_requirements`
- [ ] Replace `positions` → `core_workforce_current`
- [ ] Replace `job_similarities` → `analytics_job_similarities`
- [ ] Remove `career_pathways` references

### **Phase 0.2: Column Name Updates** 
- [ ] Update all `JobProfile` → `job_title`
- [ ] Update all `Skill_Name` → `skill_name`
- [ ] Update all `Category` → `primary_category`
- [ ] Update all `Subcategory` → `secondary_category` 
- [ ] Update all `similarity_score` → `enhanced_similarity_score`

### **Phase 0.3: Query Enhancement**
- [ ] Add FAIL-FAST validation (`WHERE field IS NOT NULL`)
- [ ] Use enhanced similarity scores instead of basic
- [ ] Leverage defining skills where applicable
- [ ] Add rarity analysis to skills queries

### **Phase 0.4: Validation Testing**
- [ ] Test all existing webapp pages load correctly
- [ ] Verify all metrics pull from V2 database 
- [ ] Confirm no placeholder/hardcoded values
- [ ] Validate query performance (<500ms)
- [ ] Check API endpoints return valid data

---

## 🎯 **Success Criteria**

**Phase 0 Complete When:**
- ✅ All 7 SQL files updated to V2 schema
- ✅ V1 webapp loads successfully with V2 database
- ✅ All existing functionality preserved
- ✅ Zero placeholder data or fallback values  
- ✅ Query performance maintained or improved
- ✅ All APIs return real V2 analytics data

**This document serves as the authoritative guide for the critical Phase 0 SQL reconciliation task.**
