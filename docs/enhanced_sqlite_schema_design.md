# Enhanced SQLite Schema Design for Phase 2

This document describes the enhanced SQLite schema that supports 14-column job architecture and 18-column skills library.

## Enhanced Table Schemas

### 1. jobs Table (Enhanced from 6 to 14 columns)

The jobs table now includes 8 additional columns for rich organisational metadata:
- ProfileTitleSuffix, ManagementLevel, JobSubFunctionID, JobSubFunction
- JobCategoryID, JobCategory, Customer_Facing, is_Banker
- Executive_Leadership_Group, Accountability_Scope

### 2. skills Table (Enhanced from 6 to 18 columns)  

The skills table now includes 12 additional columns for comprehensive Lightcast integration:
- category_id, description, descriptionSource, infoUrl
- isLanguage, isSoftware, subcategory_id
- tag_wikipediaExtract, tag_wikipediaUrl, tags, type_id, type_name

## Backward Compatibility

All existing webapp queries will continue to work unchanged. The enhanced schema only adds new columns and capabilities.

## New Query Capabilities

The enhanced schema enables new filtering and analysis capabilities:
- Management level progression analysis
- Customer-facing role identification
- Software vs language skills categorisation
- Job category-based career pathways

# Business Context Database with 14-Column Job Architecture and 18-Column Skills Library

**Created**: 2025-01-18  
**Updated**: 2025-01-18  
**Version**: 2.0 (Phase 2 Enhanced Schema)  
**Purpose**: Document enhanced database schema for business context queries and webapp integration

---

## 🎯 **Schema Overview**

This document describes the enhanced SQLite schema that supports:
- **14-column job architecture** with rich organisational metadata
- **18-column skills library** with JSON fields and comprehensive Lightcast integration
- **Backward compatibility** with existing webapp queries
- **New query capabilities** leveraging enhanced categorical fields

---

## 📋 **Enhanced Table Schemas**

### **1. jobs Table (Enhanced from 6 to 14 columns)**

```sql
CREATE TABLE jobs (
    -- Core 6 columns (backward compatible)
    JobProfileID TEXT PRIMARY KEY,           -- R0001.5 format
    JobProfile TEXT NOT NULL,               -- "Analyst - Risk Management"
    JobID TEXT,                             -- Hierarchical job code (R0001)
    Job TEXT,                               -- Job title ("Analyst")
    JobFamily TEXT,                         -- "Technology", "Risk", "Finance"
    JobFamilyGroup TEXT,                    -- Higher-level grouping
    
    -- Enhanced 8 columns (Phase 2 additions)
    ProfileTitleSuffix TEXT,                -- "Analyst", "Manager", "Consultant", etc. (16 categories)
    ManagementLevel TEXT,                   -- "Group 1", "Group 2", ..., "Group 7", "Group NA" (8 categories)
    JobSubFunctionID TEXT,                  -- "JF0001", "JF0002", ..., "JF0834" (105 unique values)
    JobSubFunction TEXT,                    -- "Corporate Finance", "Executive", etc. (105 categories)
    JobCategoryID TEXT,                     -- "JC1", "JC2", "JC3", "JC10" (4 categories)
    JobCategory TEXT,                       -- "Support", "Revenue Generating", "Enabling", "Executive"
    Customer_Facing TEXT,                   -- "Customer Facing", "Non-Customer Facing" (nullable, 24 nulls)
    is_Banker TEXT,                         -- "Banker", "Non-Banker" (nullable, 24 nulls)
    Executive_Leadership_Group TEXT,        -- "Executive Leadership Group" (nullable, 2903 nulls)
    Accountability_Scope TEXT               -- "Direct", "Supports" (nullable)
);
```

**Data Quality Notes**:
- **3,098 job profiles** total (vs 715 in similarity calculations)
- **24 null values** in Customer_Facing and is_Banker fields
- **2,903 null values** in Executive_Leadership_Group (rare designation)
- **Hierarchical relationship**: 384 JobIDs → 3,098 JobProfileIDs

### **2. skills Table (Enhanced from 6 to 18 columns)**

```sql
CREATE TABLE skills (
    -- Core fields (backward compatible)
    Skill_ID TEXT PRIMARY KEY,              -- Lightcast skill identifier (id field from CSV)
    Skill_Name TEXT NOT NULL,               -- "Python Programming" (name field from CSV)
    Category TEXT,                          -- "Information Technology" (category_name field)
    Subcategory TEXT,                       -- "Enterprise Information Management" (subcategory_name field)
    SkillType TEXT,                         -- "Specialized Skill", "Hard Skill", "Soft Skill" (type field)
    Latest_Version TEXT,                    -- Version tracking (source_version field)
    
    -- Enhanced 18-column schema (Phase 2 additions)
    category_id INTEGER,                    -- Lightcast category ID
    description TEXT,                       -- Detailed skill description
    descriptionSource TEXT,                 -- Source of description
    infoUrl TEXT,                          -- Lightcast skill URL (infoUrl field)
    isLanguage BOOLEAN,                    -- Whether skill is a language (0.77% true)
    isSoftware BOOLEAN,                    -- Whether skill is software (28.35% true)
    subcategory_id INTEGER,               -- Lightcast subcategory ID
    tag_wikipediaExtract TEXT,            -- Wikipedia integration (68% coverage)
    tag_wikipediaUrl TEXT,                -- Wikipedia URL
    tags TEXT,                            -- JSON field: nested structures
    type_id TEXT,                         -- Lightcast type ID (ST1, etc.)
    type_name TEXT,                       -- Human-readable type name
    
    -- Legacy compatibility fields (maintained for backward compatibility)
    Market_Demand TEXT DEFAULT '',         -- "High", "Medium", "Low" (placeholder)
    Rarity_Score REAL DEFAULT NULL        -- 0-1 scale for skill uniqueness (placeholder)
);
```

**Data Quality Notes**:
- **38,430 skills** total (vs 2,068 previously)
- **31 main categories**, **450+ subcategories**
- **JSON fields**: `tags` contains nested structures
- **Boolean flags**: 77 language skills (0.77%), 2,835 software skills (28.35%)
- **Wikipedia integration**: 68% coverage with extracts and URLs

### **3. Other Tables (Unchanged)**

The following tables maintain their existing schema:
- `job_similarities` - Pre-computed job-to-job similarities
- `job_skills` - Job-to-skills mapping with weights
- `positions` - Workforce context with organisational hierarchy
- `career_pathways` - Pre-computed career progression data

---

## 🔍 **New Query Capabilities**

### **Enhanced Job Filtering**

```sql
-- Filter by management level
SELECT * FROM jobs WHERE ManagementLevel = 'Group 4';

-- Filter by job category
SELECT * FROM jobs WHERE JobCategory = 'Revenue Generating';

-- Filter by customer-facing roles
SELECT * FROM jobs WHERE Customer_Facing = 'Customer Facing';

-- Filter by banker vs non-banker
SELECT * FROM jobs WHERE is_Banker = 'Banker';

-- Executive leadership analysis
SELECT * FROM jobs WHERE Executive_Leadership_Group IS NOT NULL;

-- Management hierarchy analysis
SELECT ManagementLevel, COUNT(*) as job_count 
FROM jobs 
GROUP BY ManagementLevel 
ORDER BY ManagementLevel;
```

### **Enhanced Skills Analysis**

```sql
-- Software skills identification
SELECT * FROM skills WHERE isSoftware = 1;

-- Language skills identification
SELECT * FROM skills WHERE isLanguage = 1;

-- Skills with Wikipedia coverage
SELECT * FROM skills WHERE tag_wikipediaUrl IS NOT NULL;

-- Skills by Lightcast category
SELECT category_id, Category, COUNT(*) as skill_count
FROM skills 
GROUP BY category_id, Category
ORDER BY skill_count DESC;

-- JSON tag analysis (requires JSON functions)
SELECT Skill_Name, tags FROM skills WHERE tags != '' AND tags != 'nan';
```

### **Cross-Table Enhanced Queries**

```sql
-- Customer-facing jobs and their skills
SELECT j.JobProfile, j.Customer_Facing, s.Skill_Name, s.isSoftware
FROM jobs j
JOIN job_skills js ON j.JobProfileID = js.JobProfileID
JOIN skills s ON js.Skill_ID = s.Skill_ID
WHERE j.Customer_Facing = 'Customer Facing'
ORDER BY j.JobProfile, s.Skill_Name;

-- Management level progression analysis
SELECT 
    j1.ManagementLevel as current_level,
    j2.ManagementLevel as target_level,
    COUNT(*) as pathway_count,
    AVG(sim.similarity_score) as avg_similarity
FROM job_similarities sim
JOIN jobs j1 ON sim.job_from = j1.JobProfileID
JOIN jobs j2 ON sim.job_to = j2.JobProfileID
WHERE sim.similarity_score >= 0.7
GROUP BY j1.ManagementLevel, j2.ManagementLevel
ORDER BY pathway_count DESC;
```

---

## ⚠️ **Webapp Query Migration Guide**

### **Backward Compatibility**

✅ **These existing queries will continue to work unchanged**:
- Basic job searches by `JobProfileID`, `JobProfile`, `JobFamily`
- Skills queries using `Skill_ID`, `Skill_Name`, `Category`, `Subcategory`
- Job-skill mapping queries
- Similarity queries

### **Queries Requiring Updates**

🔄 **Optional enhancements** (existing functionality + new features):

1. **Job Family Statistics** - Can now include management level breakdown
2. **Skills Categorisation** - Can leverage `isSoftware`, `isLanguage` flags
3. **Filtering Options** - Can add filters for `Customer_Facing`, `ManagementLevel`, etc.

### **New Query Opportunities**

🆕 **New webapp features enabled by enhanced schema**:

1. **Management Level Filters**
   ```sql
   -- Add to job search filters
   WHERE ManagementLevel IN ('Group 1', 'Group 2', 'Group 3')
   ```

2. **Job Category Analysis**
   ```sql
   -- Career pathway analysis by category
   SELECT JobCategory, COUNT(*) FROM jobs GROUP BY JobCategory;
   ```

3. **Customer-Facing Role Analysis**
   ```sql
   -- Identify customer-facing career paths
   WHERE Customer_Facing = 'Customer Facing'
   ```

4. **Software vs Non-Software Skills**
   ```sql
   -- Skills breakdown by type
   SELECT isSoftware, COUNT(*) FROM skills GROUP BY isSoftware;
   ```

---

## 🚀 **Implementation Strategy**

### **Phase 2: Core Schema Enhancement** ✅
- [x] Update `SchemaBuilder._create_jobs_table()` for 14-column schema
- [x] Update `SchemaBuilder._create_skills_table()` for 18-column schema
- [x] Update `DataLoader._load_job_architecture()` for enhanced data loading
- [x] Update `DataLoader._load_skills_library()` for comprehensive skills

### **Phase 3: Webapp Query Updates** 🔄
- [ ] Audit existing SQL queries for compatibility
- [ ] Add optional filters for new categorical fields
- [ ] Enhance job search with management level and category filters
- [ ] Add skills analysis features (software/language identification)
- [ ] Update API endpoints to support new filtering options

### **Validation & Testing**
- [ ] Test database generation with enhanced schema
- [ ] Verify foreign key relationships with 3,098 job profiles
- [ ] Validate JSON field handling in skills table
- [ ] Test webapp functionality with new database structure

---

## 📊 **Schema Statistics**

| Table | Current Rows | New Columns | Key Enhancement |
|-------|-------------|-------------|-----------------|
| jobs | 3,098 | +8 (14 total) | Management levels, job categories, customer-facing flags |
| skills | 38,430 | +12 (18 total) | JSON fields, boolean flags, Wikipedia integration |
| job_skills | ~300K | 0 | No changes |
| job_similarities | 510,510 | 0 | No changes |
| positions | ~50K | 0 | No changes |

---

## 🔧 **Developer Notes**

### **Handling Nullable Fields**
- `Customer_Facing`, `is_Banker`: 24 null values (handle gracefully in queries)
- `Executive_Leadership_Group`: 2,903 null values (rare designation)
- `Accountability_Scope`: Nullable field

### **JSON Field Processing**
- `tags` field contains nested JSON structures
- Use SQLite JSON functions for advanced queries
- Fallback to string matching for basic searches

### **Boolean Field Handling**
- `isLanguage`: 77 true values (0.77% of skills)
- `isSoftware`: 2,835 true values (28.35% of skills)
- Use `= 1` or `= 0` for boolean queries in SQLite

### **Performance Considerations**
- Index new categorical fields for filtering: `ManagementLevel`, `JobCategory`, `Customer_Facing`
- Consider partial indexes for non-null nullable fields
- JSON field queries may require special indexing

This enhanced schema provides a solid foundation for advanced workforce analytics while maintaining full backward compatibility with existing webapp functionality. 