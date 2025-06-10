# LLM Handover Prompt: Data Exploration & SQLite Schema Design

## Project Context: NAB Skill Similarity Engine - Business Context Database

You are taking over development of a **data exploration and SQLite schema design phase** for the NAB Skill Similarity Engine project. This system analyzes job-to-job skill similarities to identify reskilling opportunities and career pathways.

## Current Project Status

### ✅ **Completed Work**
1. **Core Similarity Engine**: Functional CLI that computes job-to-job similarity matrices (717 jobs in dev subset, ~2,000 in full corpus)
2. **Skills Library API**: Integration with Lightcast API for skills taxonomy data (38,395 skills)
3. **Complete Dummy Data Structure**: All synthetic datasets created and ready for integration

### 🎯 **Development Context**
- **Data Scale**: Working with 717 job subset for development; full production scale ~2,000 job profiles
- **Synthetic Data**: Most data is dummy/synthetic for development purposes - **data completeness is not a concern**
- **Focus**: Schema design and integration patterns, not data quality analysis

### 🎯 **Your Mission: Phase 8.1.2 - Data Exploration & Schema Design**

**Objective**: Analyze relationships across 5+ datasets and design an optimal SQLite schema for a Flask webapp that will provide career pathway exploration and white paper generation.

## Available Datasets & Key Files

### **Primary Data Files** (all in `data/` directory):
```
data/skills_library/lightcast_skills_comprehensive.csv (5.1MB, 38,395 skills)
- Lightcast API skills taxonomy
- Columns: Skill_ID, Skill_Name, Category, Subcategory, SkillType, Latest_Version

data/job_architecture/dummy_job_architecture.csv (74KB, 717 records)  
- Job profile master data
- Columns: JobProfileID, JobProfile, JobID, Job, JobFamily, JobFamilyGroup
- Uses real JobProfileIDs in R0001.5 format

data/workforce_context/dummy_workforce_context.csv (2.2MB, ~5,000 positions)
- SAP/HRIS-style employee and position data  
- 48 columns including 10-level org hierarchy, geography, salary groups
- Schema documented in docs/workforce_context_schema.md

data/job_architecture_to_positions_mapping/position_job_mapping.csv
- Bridge table: Position_Number → JobProfileID (one-to-one mapping)
- Critical for connecting workforce context to job architecture

data/input_data/ (existing similarity engine data):
- job_data.csv (717 jobs) - basic job profiles for similarity computation
- skill_data.csv (2,070 skills) - core skills taxonomy  
- job_skill_mapping.csv (40,170 mappings) - job-to-skill relationships
```

### **Key Reference Files**:
```
project-plan.md - Complete project context and current status
docs/job_arch_schema.md - Real job architecture schema (6 columns)
docs/workforce_context_schema.md - Real workforce schema (48 columns)  
scripts/generate_dummy_*.py - Data generation scripts for understanding structure
main.py - Existing CLI interface (reference for integration patterns)
```

## Specific Tasks to Complete

### **1. Cross-Dataset Key Analysis**
Create `scripts/explore_data_relationships.py` to analyze:

**Critical Relationship Questions:**
- **Skills Integration**: How do lightcast_skills_comprehensive.csv and skill_data.csv relate? Can we join on Skill_Name or need mapping tables?
- **Job Profile Consistency**: Do JobProfileIDs match between dummy_job_architecture.csv and job_data.csv? 
- **Schema Structure**: How to optimally structure relationships for webapp performance?
- **Organizational Hierarchy**: Which of the 10 org levels are most important for webapp filtering?

**Note**: Since this is synthetic dummy data, focus on **schema design and integration patterns** rather than data quality analysis.

**Required Analysis:**
```python
# Analyze each dataset:
- Primary keys and uniqueness
- Foreign key relationships  
- Data completeness rates
- Value distributions and cardinalities
- Potential join strategies and performance implications
```

### **2. Schema Design & Documentation**  
Design SQLite schema optimized for webapp queries:

**Webapp Use Cases to Support:**
- "Show me Technology roles in Melbourne" (job family + location filtering)
- "Find similar roles to Data Scientist" (job similarity + metadata)  
- "Generate career pathway white paper" (employee context + job progression)
- "Team transition planning" (org hierarchy + workforce distribution)

**Schema Considerations:**
- Normalize 10-level org hierarchy appropriately
- Index for fast filtering (job_family, location, business_unit)
- Handle People Leader relationships (manager → employee hierarchies)
- Support for aggregation queries (headcount by role/location)

**Deliverables:**
- `docs/sqlite_schema_design.md` - Complete schema documentation
- Entity-relationship diagram (ASCII or Mermaid format)
- Index strategy for performance
- Data migration plan from CSVs to SQLite

### **3. Data Integration Strategy**
Plan the JOIN operations and data quality handling:

**Integration Challenges:**
- **Skills**: Lightcast (38K) vs existing (2K) - overlap analysis and integration strategy
- **Jobs**: Enhanced architecture vs similarity engine data - consistency and mapping strategy
- **Hierarchy**: 10-level org structure - normalization vs denormalization tradeoffs for performance
- **Scale**: Development (717 jobs) vs production (~2K jobs) - scalable schema design

**Note**: Focus on schema structure and integration patterns rather than data quality since we're using synthetic data.

## Technical Context

### **Architecture**: Two-Phase System
1. **Pre-computation Phase** (CLI): Generates similarity matrices and business context database
2. **Query Phase** (Flask webapp): Fast queries against pre-computed data

### **Data Flow**:
```
Lightcast API → skills_library.csv → business_context.sqlite → webapp
job_architecture/*.csv → business_context.sqlite → webapp  
workforce_context/*.csv → business_context.sqlite → webapp
```

### **Performance Requirements**:
- SQLite database for 5K+ positions, ~2K job profiles (717 in dev), 38K+ skills
- Webapp queries must respond in <2 seconds
- Support for filtering by multiple dimensions simultaneously
- Schema must scale from development (717 jobs) to production (~2K jobs)

### **Existing Patterns** (from main.py):
- Chunked data loading with progress tracking
- Configuration-driven field mapping (config/field_mapping.yaml)
- Error handling and logging frameworks
- Model versioning (quarterly outputs to models/2025-Q2/)

## Expected Outputs

### **1. Analysis Script** (`scripts/explore_data_relationships.py`):
```python
# Generate comprehensive analysis report covering:
- Dataset summaries (rows, columns, key fields)
- Relationship analysis (primary/foreign keys, cardinalities)  
- Data quality metrics (completeness, duplicates, consistency)
- Join strategy recommendations
- Performance considerations for different schema designs
```

### **2. Schema Documentation** (`docs/sqlite_schema_design.md`):
```sql
-- Complete SQLite schema with:
- Table definitions with proper data types
- Primary key and foreign key constraints
- Index definitions for performance
- View definitions for common queries
-- Rationale for design decisions
-- Migration strategy from CSV to SQLite
```

### **3. Integration Plan**:
- Detailed steps for CSV → SQLite migration
- Data quality validation checkpoints
- Handling strategy for missing/inconsistent data
- Performance testing approach

## Key Success Criteria

1. **Comprehensive Understanding**: Demonstrate deep understanding of all dataset relationships
2. **Optimal Schema**: Design that supports fast webapp queries while maintaining data integrity
3. **Production-Ready**: Schema that can handle real-world data quality issues
4. **Clear Documentation**: Another developer can implement your schema design
5. **Performance-Focused**: Indexes and structure optimized for webapp use cases

## Next Phase Context

After your work, the next developer will:
1. Implement your schema in `src/skill_similarity_engine/business_context/sqlite_builder.py`
2. Extend `main.py` with "Generate Business Context Database" menu option
3. Build data integration modules using your JOIN strategies
4. Test end-to-end with your schema design

Your exploration and schema design work is **critical** for the success of the webapp phase. Take time to thoroughly understand the data relationships before designing the schema.

## Questions to Address in Your Analysis

1. **Skills Mapping**: Can we unify Lightcast and existing skills, or need separate tables?
2. **Job Hierarchy**: Should JobFamily/JobFamilyGroup be normalized into separate tables?
3. **Org Structure**: Which org levels matter most for filtering? Flatten or normalize?
4. **Performance vs Simplicity**: Denormalized for speed or normalized for maintainability?
5. **Development vs Production Scale**: Schema that works efficiently from 717 to ~2K job profiles?
6. **Future Scalability**: Schema that can eventually scale beyond production requirements?

**Development Focus**: Since we're using synthetic dummy data, prioritize schema design and integration patterns over data quality concerns.

Your thorough analysis will determine the success of the entire webapp phase. Focus on understanding the data first, then designing for the specific webapp use cases. 