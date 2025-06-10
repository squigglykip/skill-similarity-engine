# Skill Similarity Engine - Project Plan

## Overview

This document outlines the development plan for the NAB Skill Similarity Engine, a system designed to analyse skill similarities between jobs to identify reskilling opportunities. The project implements a two-phase architecture optimised for JobProfile-level analysis.

> **ARCHITECTURAL FOCUS**: The system operates on **JobProfile similarity** (architectural blueprints with prescribed skills) rather than complex individual position analysis. This aligns with current business priorities and data availability, delivering core value through pure skill-based similarity calculations.

> **PRIMARY OUTPUT OBJECTIVE**: The core deliverable is a comprehensive **JobProfile similarity dataset in tabular format** optimised for Power BI integration. This tabular output (structured as a fact table with job1, job2, and similarity metrics) serves as the foundation for all downstream analytics.

> **TWO-PHASE ARCHITECTURE**: 
> 1. **Pre-computation Phase**: Generates pure JobProfileID-to-JobProfileID skill similarity matrices (production-ready)
> 2. **Query Phase**: Applies contextual weightings when needed (future enhancement)

## Project Status Index

| Phase | Description | Status | Branch |
|-------|-------------|--------|--------|
| 1 | Core Framework | **COMPLETED** | `1-feature/core-framework` |
| 2 | Similarity Engine | **COMPLETED** | `2-feature/similarity-engine` |
| 3 | Gap Analysis | **COMPLETED** | `3-feature/gap-analysis` |
| 4 | Reporting & Visualisation | **COMPLETED** | `4-feature/reporting-visualization` |
| 5 | CLI & Testing | **COMPLETED** | `5-feature/cli-testing` |
| 6 | POC Integration & Production Foundation | **COMPLETED** | `6-feature/poc-integration` |
| 7 | Data Pipeline & Integration | **IN PROGRESS** | `7-feature/data-pipeline` |
| 8 | Future Features & Aspirational Work | **PLANNED** | `8-feature/future-features` |

### Key Components Status

| Component | Status | Notes |
|-----------|--------|-------|
| Command Line Interface | **COMPLETED** | Working via main.py with menu-driven interface |
| Memory Management | **COMPLETED** | Handles large datasets (35,000+ jobs) efficiently |
| Configuration System | **COMPLETED** | Comprehensive YAML-based configuration |
| Pre-computation Infrastructure | **COMPLETED** | Production-ready with quarterly versioning |
| Asymmetric Similarity Calculation | **COMPLETED** | Pure skill-based similarity without complex weighting |
| Model Governance & Versioning | **COMPLETED** | Quarterly versioning with audit trails |
| JobProfile Similarity Export | **COMPLETED** | Primary tabular output for Power BI |
| Field Mapping System | **COMPLETED** | Configuration-driven data loading |
| Error Handling & Logging | **COMPLETED** | Comprehensive error tracking and reporting |

## Completed Phases

### Phase 1: Core Framework - **COMPLETED**
**Branch: `1-feature/core-framework`**

#### 1.1 Project Setup
- [x] Create project structure
- [x] Set up development environment
- [x] Define initial dependencies in requirements.txt
- [x] Configure pyproject.toml

#### 1.2 Data Models
- [x] Implement `models/skills.py` for skill taxonomy representation
- [x] Implement `models/jobs.py` for job architecture representation
- [x] Implement `models/employees.py` for employee data representation
- [x] Add type annotations and proper documentation

#### 1.3 Configuration System
- [x] Implement `config/settings.py` for application configuration
- [x] Create YAML/JSON configuration parsers
- [x] Implement configuration validation
- [x] Add support for environment-specific configurations

#### 1.4 Data Normalisation
- [x] Implement min-max scaling in `data/normalisers.py`
- [x] Implement boolean normalisation
- [x] Implement TF-IDF style weighting for rare vs. common skills
- [x] Implement configurable importance weights

#### 1.5 Data Loaders
- [x] Implement CSV data loaders in `data/loaders.py`
- [x] Implement Excel data loaders
- [x] Add data validation and error handling
- [x] Create sample data files for testing

### Phase 2: Similarity Engine - **COMPLETED**
**Branch: `2-feature/similarity-engine`**

#### 2.1 Vector Representation
- [x] Implement vector representation for skills in `similarity/cosine.py`
- [x] Add support for different vectorisation strategies
- [x] Implement dimensionality reduction techniques
- [x] Create utility functions for vector manipulation

#### 2.2 Similarity Calculation
- [x] Implement cosine similarity in `similarity/cosine.py`
- [x] Add threshold configuration options
- [x] Implement Pay Scale Area-adjusted similarity calculator

##### Pay Scale Area Methodology
- [x] Develop adjustment methodology to account for seniority in similarity calculations
- [x] Implement `PSAAdjustedSimilarityCalculator` wrapper for base calculator
- [x] Create configurable adjustment factors for different PSA level gaps
- [x] Test impact on career progression analysis and pathway identification

This enhancement addresses the real-world scenario where explicit proficiency levels are not available in HRIS data. Instead, we use Pay Scale Area (job seniority) as a proxy for skill proficiency, ensuring that:
- Jobs with similar skill sets but vastly different seniority levels receive appropriately reduced similarity scores
- Career progression pathways favor appropriate level jumps (1-2 levels) over extreme jumps
- Similarity scores reflect organisational reality where skills at different seniority levels represent different proficiency

#### 2.3 Similarity Matrix Generation
- [x] Implement job-to-job similarity matrix generation
- [x] Add performance optimisations for large datasets

### Phase 3: Gap Analysis - **COMPLETED**
**Branch: `3-feature/gap-analysis`**

#### 3.1 Skill Gap Identification
- [x] Implement skill gap identification in `analysis/gap.py`
- [x] Identify present skills vs. needed skills
- [x] Identify excess skills (skills not needed in target role)
- [x] Create comprehensive gap reports

#### 3.2 Development Effort Calculation
- [x] Implement development effort scoring
- [x] Factor in skill difficulty levels
- [x] Add configurable weighting for different skill categories
- [x] Create prioritised development plans

#### 3.3 Reskilling Pathway Generation
- [x] Implement reskilling pathway algorithms
- [x] Add support for multi-step career transitions
- [x] Implement optimal path finding for skill development
- [x] Create pathway visualisation data structures

### Phase 4: Reporting & Visualisation - **COMPLETED**
**Branch: `4-feature/reporting-visualization`**

#### 4.1 Basic Reporting
- [x] Implement DataFrame export functionality
- [x] Add CSV export capabilities
- [x] Add JSON export capabilities
- [x] Implement report configuration options

#### 4.2 Primary Output: Tabular Job Similarity Data
- [x] Design standardised fact table format for job similarity data
- [x] Implement JobProfile similarity export
- [x] Create metadata-enriched tabular format
- [x] Add opportunity flags for filtering in Power BI
- [x] Optimise exports for large datasets
- [x] Ensure consistency in data structure across runs

#### 4.3 Secondary Outputs: Heatmap Visualisation 
- [x] Implement heatmap generation in `visualization/heatmaps.py`
- [x] Add customisation options for heatmap appearance
- [x] Add clustering options for better visualisation

#### 4.4 Workforce Planning Reports
- [x] Implement aggregate reporting functionality
- [x] Create skills gap analysis at organisational level

#### 4.5 Large-Scale Visualisation
- [x] Implement hexbin visualisation for dimensionality reduction in `visualization/hexbin.py`
- [x] Add support for different dimensionality reduction methods (PCA, t-SNE, UMAP)
- [x] Implement efficient data export for Power BI integration
- [x] Add opportunity flags for filtering in Power BI

## In-Progress and Future Phases

### Phase 5: CLI & Testing - **COMPLETED**
**Branch: `5-feature/cli-testing`**

- [x] Menu-driven CLI interface in `main.py`
- [x] Data loading and validation commands
- [x] Similarity calculation and export functionality
- [x] Comprehensive testing with realistic data volumes
- [x] End-to-end workflow validation

### Phase 6: POC Integration & Production Foundation - **COMPLETED**
**Branch: `6-feature/poc-integration`**

#### 6.1 Two-Phase Architecture Implementation - **COMPLETED**
- [x] **Pre-computation Phase**: Pure JobProfileID-to-JobProfileID similarity matrix generation
- [x] **Query Interface Design**: Framework for applying context modifiers at query time
- [x] **Architectural Separation**: Clean distinction between base similarity and contextual weighting

#### 6.2 Memory Management & Performance - **COMPLETED**
- [x] Memory tracking utilities and large object management
- [x] Multi-processing framework with adaptive pool sizing
- [x] Chunked and batched processing for large datasets
- [x] Progress tracking with file-based checkpointing

#### 6.3 Core Data Loading Enhancements - **COMPLETED**
- [x] Field mapping system with YAML configuration
- [x] Streaming/chunked data loading for scalability
- [x] JobProfileID-based architecture with canonical field names
- [x] Comprehensive validation and error handling

#### 6.4 Asymmetric Similarity Implementation - **COMPLETED**
- [x] Direct, literal skill mapping without complex vectorisation
- [x] AsymmetricCoverageCalculator for pure skill overlap calculation
- [x] Configuration-driven skill weighting (optional, not applied in pre-computation)
- [x] Production testing: 715 jobs → 510,510 comparisons in ~3 seconds

#### 6.5 Model Governance & Versioning - **COMPLETED**
- [x] Quarterly versioning with intelligent time detection
- [x] Dual-format outputs: CSV (Power BI) + Parquet (efficiency)
- [x] ModelVersionManager class with comprehensive audit trails
- [x] Production-ready directory structure and metadata management

#### 6.6 Error Handling & Logging Framework - **COMPLETED**
- [x] Centralised logging with structured output
- [x] Enhanced error categorisation and reporting
- [x] Checkpointing and recovery mechanisms
- [x] Data validation with schema-driven configuration

## Completed Phase

### Phase 7: Data Pipeline & Integration - **COMPLETED** ✅
**Branch: `7-feature/data-pipeline`**

#### 7.1 Data Export Optimisation - **COMPLETED** ✅
- [x] Standardised export formats optimised for Power BI
- [x] Efficient serialisation and metadata descriptions  
- [x] JobProfile similarity exports (primary tabular output)

#### 7.2 Configuration Management System - **COMPLETED** ✅
- [x] Comprehensive YAML-based configuration with hierarchical structure
- [x] Type-safe dataclasses for strongly-typed configuration handling
- [x] Configuration validation and error reporting with helpful messages
- [x] CLI support for configuration management and overrides
- [x] Environment-specific settings (dev, test, production)
- [x] Similarity thresholds, skill weightings, visualisation preferences, export specifications
- [x] Extension points for future features (disabled by default)

#### 7.3 Enhanced Configuration Framework - **COMPLETED** ✅
- [x] Variable weight configuration system with toggle capability (0 = disabled)
- [x] Extensible structure for future similarity variables
- [x] Clean separation between skills-based core and optional weighting variables
- [x] Configuration versioning and backward compatibility
- [x] Well-structured sections with comprehensive documentation

#### 7.4 HRIS Data Integration - **COMPLETED** ✅
- [x] Schema separation strategy with `hris_schema_mapping.yaml`
- [x] Field mapping system between HRIS job codes and internal architecture
- [x] Data validation framework with error reporting and quality metrics
- [x] End-to-end transformation pipeline with comprehensive unit tests
- [x] Clean separation between external HRIS formats and internal engine schemas

#### 7.5 Power BI Integration - **PLANNED** 📋
- [ ] Data schema documentation for Power BI developers
- [ ] Reference relationship models and DAX measures for common analyses
- [ ] User guide and best practices for working with similarity data exports
- [ ] Performance optimisations for large similarity datasets

#### 7.6 Output Delivery Strategy - **PLANNED** 📋
- [ ] Clear primary output focus: JobProfile similarity CSV for Power BI
- [ ] Secondary output controls: heatmaps and visualisations as optional features
- [ ] CLI flags for output selection (`--primary-only`, `--visualizations`)
- [ ] Documentation for recommended usage patterns

#### 7.7 Production Testing - **PLANNED** 📋
- [ ] End-to-end testing with real HRIS data
- [ ] Performance validation with full-scale datasets
- [ ] User feedback integration and refinements

## Next Phase: Query Layer Implementation

> **CLI Implementation Note**: The CLI interface is fully functional in `main.py` with menu-driven data loading, similarity matrix generation, model versioning, and export capabilities. This completes the **pre-computation phase** of our two-phase architecture.

### Phase 8: Query Layer & Flask Webapp - **IN PROGRESS** 🚧
**Branch: `8-feature/query-layer-webapp`**

> **Business Priority**: Urgent need for career pathway exploration and white paper generation for colleagues facing role transitions. This phase delivers the query layer of our two-phase architecture, making the pre-computed similarity data accessible to non-technical business users.

#### 8.1 Web Application Foundation - **PLANNED** 📋
**Branch: `8.1-feature/query-layer-webapp/foundation`**

**8.1.0 Skills Library API Foundation** ✅ **COMPLETED**
- [x] **Create Skills Library API Module** (`src/skill_similarity_engine/api/`)
  - [x] `SkillsLibraryAPI` class with Lightcast OAuth 2.0 authentication
  - [x] Version tracking and incremental update logic  
  - [x] CSV generation for downstream business context integration
  - [x] Comprehensive logging and error handling

- [x] **API Integration & Testing**:
  - [x] Test API authentication with provided Lightcast credentials ✅ **COMPLETED**
  - [x] Validate incremental update logic (fetch only new versions) ✅ **COMPLETED** 
  - [x] Generate initial `skills_library.csv` from all historical versions ✅ **COMPLETED**
  - [x] Performance testing for full vs incremental updates ✅ **COMPLETED**

**8.1.1 Dummy Data Structure Completion** ✅ **COMPLETED**
- [x] **Skills Library Data** ✅ **COMPLETED**
  - [x] `data/skills_library/lightcast_skills_comprehensive.csv` (5.1MB, 38,395 skills) 
  - [x] Generated via Lightcast API integration with incremental updates
  - [x] Includes skill taxonomy with categories, subcategories, types, and latest versions

- [x] **Workforce Context Data** ✅ **COMPLETED** 
  - [x] `data/workforce_context/dummy_workforce_context.csv` (2.2MB)
  - [x] SAP/HRIS-style employee and position data for business context

- [x] **Job Architecture Data** ✅ **COMPLETED**
  - [x] `data/job_architecture/dummy_job_architecture.csv` (74KB, 717 records) ✅ **COMPLETED**
  - [x] Matches real schema: JobProfileID, JobProfile, JobID, Job, JobFamily, JobFamilyGroup
  - [x] Uses real JobProfileIDs from user's data (R0001.5 format)
  - [x] NAB-realistic job families and organizational structure
  - [x] Generated via `scripts/generate_dummy_job_architecture.py`

- [x] **Job Architecture to Positions Mapping** ✅ **COMPLETED**
  - [x] `data/job_architecture_to_positions_mapping/position_job_mapping.csv` ✅ **COMPLETED** 
  - [x] Simple one-to-one mapping: Position_Number → JobProfileID
  - [x] Bridge between workforce positions and job architecture
  - [x] Links job architecture data to workforce context for comprehensive analysis
  - [x] Enables filtering and contextual queries in the webapp
  - [x] Generated via `scripts/generate_position_job_mapping.py`

**8.1.2 Data Exploration & Schema Design** ⚡ **NEXT PRIORITY** (dummy data completion ✅)
- [ ] **Cross-Dataset Key Analysis**
  - [ ] Create exploration script: `scripts/explore_data_relationships.py`
  - [ ] Analyze primary keys, foreign keys, and relationship cardinalities
  - [ ] Document data quality: completeness, consistency, duplicates
  - [ ] Identify optimal join strategies and performance considerations

- [ ] **Schema Design & Documentation**
  - [ ] Design SQLite schema with proper normalization
  - [ ] Define table relationships and foreign key constraints  
  - [ ] Plan indexes for fast webapp queries (by job family, location, etc.)
  - [ ] Document schema in `docs/sqlite_schema_design.md`
  - [ ] Create entity-relationship diagram for schema visualization

- [ ] **Data Integration Strategy**
  - [ ] Plan JOIN operations between datasets
  - [ ] Handle missing data and data quality issues
  - [ ] Design aggregation tables for performance (if needed)
  - [ ] Validate relationship integrity across all datasets

**8.1.3 CLI Enhancement for Business Context Database** 📋 **PLANNED** (after schema design)
- [ ] **Extend main.py menu system** to include business context processing
  - [ ] Add new menu option: "2. Generate Business Context Database"  
  - [ ] Create sub-menu for business context configuration options
  - [ ] Integrate with existing model versioning system (output to `models/2025-Q2/`)

- [ ] **Create new src modules for relational data processing**:
  - [ ] `src/skill_similarity_engine/business_context/` directory structure
  - [ ] `src/skill_similarity_engine/business_context/data_integrator.py` - Join JobProfiles → Positions → SAP data
  - [ ] `src/skill_similarity_engine/business_context/sqlite_builder.py` - Create optimised SQLite schema and indexes
  - [ ] `src/skill_similarity_engine/business_context/orchestrator.py` - Main CLI integration module

- [ ] **Enhanced data loaders for new folders**:
  - [ ] Extend existing loaders to read from `data/job_architecture/`, `data/skills_library/`, `data/workforce_context/`
  - [ ] Create validation and quality checks for relational data integrity
  - [ ] Handle missing data and provide fallback strategies

- [ ] **SQLite database design and creation**:
  - [ ] Design optimised schema for webapp queries (JobProfiles, Positions, BusinessContext tables)
  - [ ] Create indexes for fast filtering (by business_unit, job_family, location, etc.)
  - [ ] Build aggregation tables for performance (position counts by role/location)
  - [ ] Output: `models/2025-Q2/business_context.sqlite` (alongside existing similarity matrices)

- [ ] **CLI integration and user experience**:
  - [ ] Progress tracking and logging for large dataset processing
  - [ ] Validation reports (data quality, coverage, relationship integrity)
  - [ ] Option to regenerate only business context without re-running similarity computation
  - [ ] Error handling and recovery for partial processing

**Updated CLI Menu Structure:**
```
Main Menu:
1. Precompute Skill Similarities
2. Generate Business Context Database     # NEW
3. Query Skill Similarities (coming soon)
0. Exit

Business Context Menu:
1. Update Skills Library (API)            # NEW - Fetch from Lightcast API
2. Load and validate enhanced data        # NEW - Load from job_architecture/, workforce_context/
3. Generate business context database     # NEW - Create SQLite with relational joins
4. Validate business context integrity    # NEW - Data quality reports
0. Back to main menu
```

**Updated Development Workflow:**
```
Phase 1: Complete Dummy Data Structure ✅ **COMPLETED**
1. ✅ Create job_architecture/*.csv files with realistic NAB structure
2. ✅ Create job_architecture_to_positions_mapping/ bridge data  
3. ✅ Validate all data relationships and integrity

Phase 2: Data Exploration & Schema Design ⚡ **CURRENT PRIORITY**
1. Explore relationships between all datasets using analysis scripts
2. Document data quality, completeness, and key relationships
3. Design optimal SQLite schema with proper normalization and indexes
4. Create entity-relationship diagram and schema documentation

Phase 3: CLI Integration 📋 **NEXT**
1. Extend main.py with business context menu
2. Build data integration modules in business_context/
3. Create SQLite generation with optimised schema
4. Test end-to-end with complete dummy data

Phase 3: Quarterly Production Workflow (FINAL STATE)
1. Data Scientist runs: "1. Precompute Skill Similarities" → generates similarity matrices
2. Data Scientist runs: "2. Generate Business Context Database" → 
   a. Updates skills library via Lightcast API (incremental)
   b. Loads job architecture & workforce context from CSVs  
   c. Creates business_context.sqlite with all combined data
3. Output to OneDrive: models/2025-Q2/ contains both similarity data + business context
4. Users double-click .bat file → webapp loads from models/2025-Q2/

Result: Fast webapp with pre-computed similarities + optimised relational queries
```

**Immediate Dummy Data Requirements:**

**Priority 1: Job Architecture Data**
```
data/job_architecture/job_families.csv:
- Job_Family (Technology, Risk, Finance, Operations, etc.)
- Job_Subfamily (Data & Analytics, Cyber Security, Personal Banking, etc.)  
- Business_Domain (Corporate, Retail Banking, Business Banking, etc.)
- Function_Category (Technology, Finance, Risk & Compliance, etc.)

data/job_architecture/career_levels.csv:  
- Career_Level (1-8 scale matching NAB structure)
- Level_Name (Graduate, Analyst, Senior Analyst, Manager, etc.)
- Salary_Grade_Mapping (External, Group 1-7 from existing data)
- Leadership_Track (Individual Contributor, People Leader)

data/job_architecture/business_units.csv:
- Business_Unit (Personal Banking, Business Banking, Corporate & Investment Banking, etc.)
- Division (Technology, Finance, Risk, Operations, etc.)  
- Region (Australia, New Zealand, Asia)
- Location_Hub (Melbourne, Sydney, Brisbane, Perth, Auckland, etc.)

data/job_architecture/job_progressions.csv:
- From_JobProfile, To_JobProfile (career pathway mappings)
- Progression_Type (promotion, lateral, function_change)
- Typical_Timeline (1-2 years, 2-3 years, etc.)
- Success_Rate (estimated % of successful transitions)
```

**Priority 2: Architecture to Positions Mapping**  
```
data/job_architecture_to_positions_mapping/position_mappings.csv:
- JobProfileID (from existing job_data.csv)
- Position_Count (how many actual positions exist)
- Current_Headcount (filled positions)
- Geographic_Distribution (by location)
- Team_Assignment (specific team/department mappings)
```

**Data Exploration Checklist:**

**Dataset Analysis Required:**
```
1. Skills Library (lightcast_skills_comprehensive.csv):
   - Primary Key: Skill_ID? 
   - Columns: Skill_Name, Category, Subcategory, SkillType, Latest_Version
   - Cardinality: ~38,395 skills
   - Question: How does this relate to job_skill_mapping.csv?

2. Job Architecture (dummy_job_architecture.csv):  
   - Primary Key: JobProfileID ✅ CONFIRMED
   - Columns: JobProfile, JobID, Job, JobFamily, JobFamilyGroup  
   - Cardinality: 717 job profiles
   - Foreign Keys: None currently

3. Workforce Context (dummy_workforce_context.csv):
   - Primary Key: Position_Number ✅ CONFIRMED  
   - Columns: Employee data + 10-level org hierarchy + location + salary
   - Cardinality: ~5,000 positions  
   - Foreign Keys: People_Leader_Number → Position_Number

4. Position Mapping (position_job_mapping.csv):
   - Bridge Table: Position_Number → JobProfileID ✅ CONFIRMED
   - Cardinality: 1:1 mapping, 5,000 records
   - Critical for joining workforce context to job architecture

5. Existing Engine Data (job_data.csv, skill_data.csv, job_skill_mapping.csv):
   - How do these relate to the new enhanced datasets?
   - Do we need to maintain backward compatibility?
   - Are there conflicting JobProfileIDs or skill definitions?
```

**Key Relationship Questions to Explore:**
```
1. Skills Integration:
   - How do skills in lightcast_skills_comprehensive.csv map to skill_data.csv?
   - Can we join on Skill_Name or do we need new mapping tables?
   - Are there skill ID conflicts between datasets?

2. Job Profile Consistency:
   - Do JobProfileIDs in dummy_job_architecture.csv match job_data.csv?
   - How many job profiles exist vs actual positions vs similarity engine data?
   - What happens if a position references a JobProfileID not in job architecture?

3. Organizational Hierarchy:
   - How deep should we normalize the 10-level org structure?
   - Which levels are most important for webapp filtering?
   - Should we create separate tables for business units, locations, cost centers?

4. Data Quality & Completeness:
   - What percentage of positions have assigned employees?
   - Are there orphaned records (positions without job profiles, etc.)?
   - How should we handle missing data in joins?
```

**Data Flow Strategy:**
```
Skills Data Flow: ✅ COMPLETE
Lightcast API → skills_library.csv → business_context.sqlite → webapp

Job Architecture Flow: ✅ COMPLETE  
job_architecture/*.csv → business_context.sqlite → webapp

Workforce Context Flow: ✅ COMPLETE
workforce_context/*.csv → business_context.sqlite → webapp

Integration Point: All three sources combined in SQLite with optimised schema
NEXT: Explore relationships and design optimal schema
```

**Benefits of CLI-based Business Context Generation:**
- ✅ **Leverages existing infrastructure**: Model versioning, logging, error handling
- ✅ **Separation of concerns**: Heavy processing in CLI, fast queries in webapp  
- ✅ **Performance optimisation**: Pre-computed joins and indexes for webapp speed
- ✅ **Data governance**: Business context processing in controlled CLI environment
- ✅ **Deployment simplicity**: Webapp receives pre-optimised SQLite file
- ✅ **Incremental updates**: Can regenerate business context without re-running similarity computation
- ✅ **API-first skills management**: Consistent access to Lightcast data alongside CSV sources
- ✅ **Unified data versioning**: Skills library updates tied to quarterly model releases
- ✅ **Incremental API efficiency**: Only fetch new versions, 2-5 minute updates vs 60+ minute full refresh

**8.1.1 Enhanced Data Pipeline - Analysis & Requirements**

> **Current State Analysis**: The existing system processes basic job similarity using minimal fields (`JobProfileID`, `RoleSet`, `Salary Group`, basic skills). This enables pure skill-based similarity but lacks contextual richness for career pathway exploration and business filtering.

**Data Enhancement Priority Analysis:**

**Priority 1: Essential for MVP Webapp (Implement First)**
- [ ] **Job Family Context**: `Job_Family`, `Job_Subfamily` for grouping related roles
  - *Enables*: "Show me similar roles within Technology" filtering
  - *User Value*: Contextual similarity within business domains
  - *Data Source*: Job architecture master data (likely available)

- [ ] **Career Level Progression**: `Career_Level`, `Career_Track` for hierarchy
  - *Enables*: "What's the next level up?" pathway analysis
  - *User Value*: Natural career progression recommendations
  - *Data Source*: HR level/grade mappings (likely available)

- [ ] **Business Unit Context**: `Business_Unit`, `Function` for organisational filtering
  - *Enables*: "Show pathways within Personal Banking" scope filtering
  - *User Value*: Relevant opportunities within user's business area
  - *Data Source*: Organisational structure data (likely available)

**Priority 2: Enhanced User Experience (Second Phase)**
- [ ] **Skills Taxonomy Hierarchy**: `Parent_Skill_ID`, `Related_Skills`, `Prerequisites`
  - *Enables*: "What skills lead to this capability?" pathway visualisation
  - *User Value*: Skill development roadmaps with logical progression
  - *Data Source*: Skills framework (may need curation)

- [ ] **Geographic Context**: `Region`, `Country`, `City`, `Remote_Eligible`
  - *Enables*: Location-aware opportunity filtering
  - *User Value*: Practical mobility options based on location preferences
  - *Data Source*: Job posting/office location data (likely available)

**Priority 3: Advanced Features (Future Enhancement)**
- [ ] **Workforce Analytics**: Current headcount, team sizes, demand signals
  - *Enables*: "Where are the actual opportunities?" capacity planning
  - *User Value*: Market reality vs theoretical similarities
  - *Data Source*: HRIS employment data (privacy/aggregation considerations)

- [ ] **Career Pathway History**: `Progression_From`, `Progression_To`, success rates
  - *Enables*: Evidence-based pathway recommendations
  - *User Value*: "What do successful transitions actually look like?"
  - *Data Source*: Historical movement data (complex data governance)

**Data Feasibility Assessment:**

| Data Category | Availability | Complexity | Business Value | Implementation Priority |
|---------------|--------------|------------|----------------|------------------------|
| Job Families | High | Low | High | Priority 1 |
| Career Levels | High | Low | High | Priority 1 |
| Business Units | High | Low | High | Priority 1 |
| Skills Hierarchy | Medium | Medium | High | Priority 2 |
| Geographic Data | High | Low | Medium | Priority 2 |
| Workforce Counts | Medium | High | Medium | Priority 3 |
| Career History | Low | Very High | High | Priority 3 |

**Enhanced Data Pipeline Implementation Strategy:**

**Data Organization Tasks:**
- [ ] **Create Enhanced Data Structure**:
  - [ ] Populate `data/job_architecture/` with job family, career level, and business unit mappings
  - [ ] Populate `data/skills_library/` with skills hierarchy, prerequisites, and competency frameworks  
  - [ ] Populate `data/workforce_context/` with aggregated SAP/HRIS team and department data
  - [ ] Update `config/field_mapping.yaml` to include mappings for enhanced fields
  - [ ] Create enhanced field derivation rules in `config/enhanced_field_mapping.yaml`

**Data Pipeline Extensions:**
- [ ] **Phase A**: Extend existing CSV loaders to handle Priority 1 fields from new data folders
- [ ] **Phase B**: Create new data models for hierarchical skills (Priority 2) 
- [ ] **Phase C**: Integrate HRIS/SAP extracts for workforce context (Priority 3)
- [ ] **Phase D**: Build pathway history analysis from HR movement data (Priority 3)

**Data Flow Integration:**
- [ ] **CLI Enhancement**: Extend CLI to read from `data/job_architecture/`, `data/skills_library/`, `data/workforce_context/`
- [ ] **Output Integration**: Enhanced pre-computed data outputs to existing `models/2025-Q2/` structure
- [ ] **WebApp Data Loading**: Create webapp data loader to read from `models/` quarterly outputs
- [ ] **Configuration Management**: Extend `config/` files to support webapp-specific settings

**Data-to-Feature Mapping Analysis:**

> This section maps specific enhanced data fields to webapp features, showing how data investments translate to user value.

**Feature: Career Pathway Explorer**
```
Required Data: Job_Family + Career_Level + Business_Unit
Current Limitation: Can only show "similar jobs" without context
Enhanced Capability: "Show me Data Science roles in Technology at Senior level"
User Journey: Risk Analyst → filters by (Function=Technology, Level=Senior) → sees Data Scientist, Solutions Architect, Tech Lead options
```

**Feature: Skills Gap Analysis**  
```
Required Data: Skills_Hierarchy + Prerequisites + Related_Skills
Current Limitation: Shows skill differences but no learning pathway
Enhanced Capability: "You need Python → suggests JavaScript first (related), then Python (builds on JS)"
User Journey: Business Analyst → wants Machine Learning Engineer → sees prerequisite chain: Statistics → Python → ML
```

**Feature: Geographic Mobility Filter**
```
Required Data: Region + Country + City + Remote_Eligible  
Current Limitation: Location-blind recommendations
Enhanced Capability: "Show Sydney opportunities" or "Remote-eligible roles only"
User Journey: Melbourne employee → filters Sydney opportunities → sees realistic relocation options
```

**Feature: Team Transition Planning**
```
Required Data: Business_Unit + Function + Current_Headcount (aggregated)
Current Limitation: Theoretical similarities without business context
Enhanced Capability: "Personal Banking has 15 similar roles with capacity for 3 more"
User Journey: Manager planning team restructure → sees absorption capacity by business unit
```

**Minimum Viable Enhancement (Priority 1 Only):**

With just `Job_Family`, `Career_Level`, and `Business_Unit`, the webapp could deliver:
- **Contextual Filtering**: "Technology roles only" or "Senior level opportunities"  
- **Progressive Pathways**: "Next level up in your function"
- **Business-Relevant Results**: "Opportunities within Personal Banking"
- **White Paper Generation**: Context-aware role transitions with business unit considerations

**Data Quality & Validation Requirements:**

| Field | Validation Rule | Data Quality Check | Fallback Strategy |
|-------|----------------|-------------------|------------------|
| Job_Family | Must be from controlled list | Cross-reference with org chart | Default to "General" |
| Career_Level | Sequential hierarchy (1-8) | No gaps in progression | Map to salary grade |
| Business_Unit | Must exist in current structure | Validate against HRIS | Use "Corporate" default |
| Skills_Hierarchy | No circular references | Tree structure validation | Flatten to categories |

**Success Metrics for Enhanced Data:**
- **User Engagement**: % of queries using filters (target: >60%)
- **Relevance**: User ratings of pathway suggestions (target: >4.0/5)
- **Business Value**: White papers generated vs manual analysis time saved
- **Data Quality**: % of records with complete Priority 1 fields (target: >95%)

**Current Data State Analysis:**

> Based on examination of existing data files in `data/input_data/`, here's what we have vs what we need:

**Job Data - Current State (`job_data.csv`, 717 records):**
```
HAVE: JobProfileID, RoleSet, Salary Group, People Leader Flag, Street, Suburb, Location, Cty
MISSING: Job_Family, Job_Subfamily, Career_Level, Business_Unit, Function, Career_Track
```

**Sample Current Data Patterns:**
- ✅ **Location Data**: Good geographic detail (`VIC`, `NSW`, `QLD`, `WA` + cities)
- ✅ **Role Hierarchy**: Salary Groups (`External`, `Group 1-7`) suggest career levels  
- ✅ **Leadership Context**: `People Leader Flag` provides management track info
- ❌ **Business Context**: No job families, business units, or functions
- ❌ **Career Progression**: No explicit career level or advancement pathways

**Skills Data - Current State (`skill_data.csv`, 2,070 records):**
```
HAVE: Skill_ID, Skill_Name, SkillType, Category, Subcategory  
MISSING: Parent_Skill_ID, Prerequisites, Related_Skills, Difficulty_Rating, Learning_Time
```

**Sample Current Skills Analysis:**
- ✅ **Rich Taxonomy**: 2,070 skills with detailed categories (Finance, IT, Marketing, etc.)
- ✅ **Skill Types**: `Common Skill`, `Specialized Skill`, `Certification` distinctions
- ✅ **Categorisation**: Business domains well-represented
- ❌ **Hierarchy**: No parent-child relationships or prerequisites
- ❌ **Learning Context**: No difficulty ratings or time estimates

**Data Enhancement Opportunity Analysis:**

**Quick Wins (Can be derived from existing data):**
1. **Career Level Mapping**: `Salary Group` → Career levels (External=0, Group1=Junior, Group7=Executive)
2. **Leadership Track**: `People Leader Flag` → Career track classification  
3. **Business Unit Inference**: Role patterns suggest business domains (e.g., "Data Engineer" → Technology)
4. **Geographic Clustering**: Existing location data can enable geographic filtering

**Medium Enhancement (Requires external data):**
1. **Job Family Classification**: Manual mapping of `RoleSet` to business functions
2. **Skills Hierarchy**: SME input to define prerequisite relationships
3. **Business Unit Assignment**: Mapping roles to NAB's organisational structure

**Complex Enhancement (Requires HRIS integration):**
1. **Workforce Distribution**: Current headcount by role/location
2. **Career Movement History**: Historical transition success rates

**Immediate Implementation Strategy:**

**Phase A (Leverage Existing Data - 2 weeks):**
- Create mapping tables to derive Priority 1 fields from existing data
- Map `Salary Group` to `Career_Level` (1-7 scale)
- Map `People Leader Flag` to `Career_Track` (IC vs Leadership)
- Group similar roles into job families using keyword analysis
- Enhance location context with region mapping

**Phase B (External Classification - 4 weeks):**
- Business SME sessions to classify roles into job families
- Map job families to NAB business units and functions
- Create skills hierarchy through workshop sessions
- Define skill prerequisites and related skill relationships

**Data Quality Assessment:**
- **Completeness**: 100% for basic fields, 0% for enhanced fields
- **Consistency**: High (clean JobProfileID format, standardised salary groups)
- **Accuracy**: Good location data, reasonable role titles
- **Opportunity**: Strong foundation that can be enhanced systematically

**Actual Data Structure (Updated):**

```
data/
├── input_data/                    # Current CLI input (EXISTING - NO CHANGES)
│   ├── job_data.csv              # Basic job profiles for similarity computation
│   ├── skill_data.csv            # Core skills taxonomy
│   └── job_skill_mapping.csv     # Job-skill relationships
│
├── job_architecture/              # NEW - Rich job context data
│   ├── job_families.csv          # Job family classifications
│   ├── career_levels.csv         # Career progression framework
│   ├── business_units.csv        # Organisational structure
│   └── job_progressions.csv      # Career pathway mappings
│
├── skills_library/                # NEW - Enhanced skills taxonomy
│   ├── skills_hierarchy.csv      # Parent-child skill relationships
│   ├── skill_prerequisites.csv   # Learning pathway dependencies
│   ├── skill_adjacencies.csv     # Related/transferable skills
│   └── competency_frameworks.csv # Skill groupings and domains
│
└── workforce_context/             # NEW - SAP/HRIS derived data
    ├── team_structure.csv        # Current team assignments
    ├── department_hierarchy.csv  # Organisational structure
    ├── workforce_distribution.csv # Aggregated headcount by role/location
    └── role_demand_signals.csv   # Hiring/growth patterns

config/                            # EXISTING - Enhanced for webapp
├── field_mapping.yaml            # EXISTING - Extend for enhanced fields
├── enhanced_field_mapping.yaml   # NEW - Webapp-specific field mappings
├── webapp_config.yaml            # NEW - Webapp configuration
└── [existing config files...]    # EXISTING - No changes

models/                            # EXISTING - Enhanced outputs
├── 2025-Q2/                      # EXISTING - Current quarterly model
│   ├── precompute_*/             # EXISTING - Base similarity matrices
│   ├── enhanced_job_metadata.parquet      # NEW - Rich job context
│   ├── enhanced_skills_metadata.parquet   # NEW - Skills hierarchy
│   └── webapp_filters.json       # NEW - UI dropdown options
└── [previous quarters...]        # EXISTING - Historical models
```

**Data Pipeline Integration Points:**
1. **CLI reads**: `data/input_data/` + new enhancement folders → outputs to `models/2025-Q2/`
2. **WebApp reads**: `models/2025-Q2/` (pre-computed + enhanced metadata)
3. **Configuration**: `config/` files drive both CLI enhancement and webapp behavior

**8.1.2 Flask Application Setup**
- [ ] Flask application setup and project structure
- [ ] .bat file launcher for seamless user deployment
- [ ] Configuration management for webapp settings
- [ ] Data loading pipeline for all pre-computed datasets
- [ ] Basic routing structure and API endpoints
- [ ] Error handling and logging for web requests
- [ ] Local development environment setup

**8.1.3 CSS Architecture & Design System**
- [ ] Select CSS framework (Bootstrap 5 or Tailwind CSS for rapid development)
- [ ] Establish CSS architecture methodology (BEM naming convention)
- [ ] Create modular SCSS/CSS structure with variables and mixins
- [ ] Define responsive breakpoint system (mobile-first approach)
- [ ] Set up CSS build pipeline with autoprefixer and minification
- [ ] Implement CSS custom properties for dynamic theming

**8.1.4 NAB Brand Style Guide Implementation**
- [ ] Research and implement NAB colour palette and brand guidelines
- [ ] Define typography scale (headings, body text, captions) with web-safe fonts
- [ ] Create NAB-compliant component library (buttons, forms, cards, tables)
- [ ] Establish spacing and layout grid system aligned with corporate standards
- [ ] Design icon system and illustration guidelines
- [ ] Define interaction states (hover, focus, active, disabled) for all components

**8.1.5 Component System Architecture**
- [ ] Create reusable Jinja2 macro library for UI components
- [ ] Implement component documentation with usage examples
- [ ] Build form component system (inputs, selects, checkboxes, validation)
- [ ] Design data visualisation component templates (tables, charts, graphs)
- [ ] Create layout components (headers, navigation, sidebars, footers)
- [ ] Establish loading and error state component patterns

**8.1.6 Frontend Architecture & JavaScript Structure**
- [ ] Set up modern JavaScript architecture (ES6+ with Babel if needed)
- [ ] Implement module system for JavaScript components
- [ ] Create utility functions library for common webapp interactions
- [ ] Set up event handling patterns for dynamic content
- [ ] Implement AJAX/fetch patterns for API communication
- [ ] Create JavaScript build pipeline with bundling and minification

**8.1.7 Template & Layout System**
- [ ] Design master template hierarchy with inheritance structure
- [ ] Create page layout templates (single-column, two-column, dashboard)
- [ ] Implement navigation template with active state management
- [ ] Build breadcrumb and page header template system
- [ ] Create responsive table templates for similarity data display
- [ ] Design form layout templates with validation display

**8.1.8 Asset Management & Performance**
- [ ] Set up static asset organisation (CSS, JS, images, fonts)
- [ ] Implement asset versioning and cache busting strategy
- [ ] Optimise images and create responsive image system
- [ ] Set up font loading strategy for performance
- [ ] Implement CSS and JavaScript minification pipeline
- [ ] Create development vs production asset handling

**8.1.9 Accessibility & User Experience Foundation**
- [ ] Implement WCAG 2.1 AA compliance baseline
- [ ] Create semantic HTML structure templates
- [ ] Establish keyboard navigation patterns
- [ ] Implement screen reader compatibility
- [ ] Design focus management and skip link system
- [ ] Create accessible form validation and error messaging

**8.1.10 Responsive Design System**
- [ ] Define mobile-first responsive strategy
- [ ] Create tablet and desktop layout variations
- [ ] Implement touch-friendly interactions for mobile
- [ ] Design responsive navigation patterns (hamburger menu, etc.)
- [ ] Create responsive table solutions for large datasets
- [ ] Test cross-device compatibility and performance

#### 8.2 Career Pathway Engine - **PLANNED** 📋
**Branch: `8.2-feature/query-layer-webapp/career-pathways`**

> **Technical Challenge**: With 510K+ job comparisons, multi-hop career pathway queries could explode to millions of combinations. Pre-computing pathways to depth 4 provides optimal performance for interactive exploration.

**8.2.1 Pathway Pre-Computation Strategy**
- [ ] Design efficient pathway graph algorithms
- [ ] Implement depth-limited pathway discovery (max 4 progressions)
- [ ] Create pathway ranking based on similarity scores and skill gaps
- [ ] Build pathway caching system for frequently accessed routes
- [ ] Optimise memory usage for large pathway networks

**8.2.2 Interactive Pathway Queries**
- [ ] Real-time pathway search and filtering
- [ ] Similarity threshold adjustment for pathway discovery
- [ ] Multi-destination pathway exploration ("show paths to role A, B, C")
- [ ] Skill gap analysis for each pathway step
- [ ] Geographic and business unit filtering for pathways

**8.2.3 Pathway Visualisation**
- [ ] Network graph rendering for pathway relationships
- [ ] Interactive pathway exploration interface
- [ ] Similarity strength visualisation (edge weights)
- [ ] Skill overlap heatmaps for pathway steps
- [ ] Export pathway diagrams for presentations

#### 8.3 White Paper Generation System - **PLANNED** 📋
**Branch: `8.3-feature/query-layer-webapp/white-papers`**

> **Business Goal**: Generate professional, standardised reports for colleagues facing role transitions, highlighting opportunities and skill development pathways.

**8.3.1 Template Engine**
- [ ] Jinja2 template system for report generation
- [ ] Multiple white paper formats (transition opportunities, skill gaps, career roadmaps)
- [ ] NAB branding and professional styling
- [ ] Configurable report sections and content blocks
- [ ] Dynamic data population from similarity analysis

**8.3.2 Report Content Generation**
- [ ] Automated job similarity analysis and ranking
- [ ] Skill gap identification and prioritisation
- [ ] Career pathway recommendations with rationale
- [ ] Market context and opportunity scoring
- [ ] Personalised transition timeline suggestions

**8.3.3 Output Formats**
- [ ] PDF generation for professional distribution
- [ ] HTML reports for web viewing and email
- [ ] Word document export for collaborative editing
- [ ] Summary slides for presentation purposes
- [ ] Bulk report generation for multiple roles

#### 8.4 User Interface & Experience - **PLANNED** 📋
**Branch: `8.4-feature/query-layer-webapp/user-experience`**

**8.4.1 User Stories & Requirements**
- [ ] Business user journey mapping for career exploration
- [ ] HR professional workflow for white paper generation
- [ ] Manager use cases for team transition planning
- [ ] Self-service employee exploration scenarios
- [ ] Admin interface for system configuration

**8.4.2 Frontend Development**
- [ ] Responsive HTML/CSS design for professional appearance
- [ ] JavaScript interactivity for dynamic filtering and exploration
- [ ] Bootstrap or similar framework for consistent styling
- [ ] Progressive enhancement for complex visualisations
- [ ] Accessibility compliance for corporate environment

**8.4.3 User Experience Design**
- [ ] Intuitive navigation for non-technical users
- [ ] Context-sensitive help and guidance
- [ ] Error messages and validation feedback
- [ ] Loading indicators for complex queries
- [ ] Keyboard shortcuts for power users

#### 8.5 Skills & Gap Analysis Module - **PLANNED** 📋
**Branch: `8.5-feature/query-layer-webapp/skills-analysis`**

> **User Journey**: "I'm a Risk Analyst, what skills do I need to become a Data Scientist?" → Interactive skill comparison with learning pathway recommendations.

**8.5.1 CLI Pre-Computation Support**
- [ ] Extend CLI to pre-compute skill gap matrices for all job pairs
- [ ] Generate skill overlap/difference summaries for fast webapp queries
- [ ] Create skill frequency and rarity statistics (if job family data available)
- [ ] Pre-compute transferable skills identification and skill adjacency mappings

**8.5.2 Skills Comparison Interface**
- [ ] Interactive job-to-job skill comparison visualisation
- [ ] Skill gap analysis with transferable skills highlighting
- [ ] Skill adjacency and transferability insights
- [ ] Gap prioritisation based on skill rarity/importance (no time estimates)

**8.5.3 Bulk Skills Analysis**
- [ ] Multi-select job comparison interface (dropdown selections, no uploads)
- [ ] Department-wide skill assessment via job selection interface
- [ ] Skills inventory reporting for workforce planning

#### 8.6 Team & Department Analysis Module - **PLANNED** 📋
**Branch: `8.6-feature/query-layer-webapp/team-analysis`**

> **User Journey**: Future Skills team selects roles/departments → see skill overlaps, internal mobility options, and workforce transition scenarios.
> 
> **Access Control**: This module is restricted to Future Skills team only and not shared widely across the business.

**8.6.1 CLI Pre-Computation Support**
- [ ] Generate aggregated role similarity clusters for team analysis
- [ ] Pre-compute department mobility matrices
- [ ] Create skill coverage heatmaps by business unit/geography

**8.6.2 Team Analysis Interface**
- [ ] Role/department selection interface (dropdown-based, no uploads)
- [ ] Internal mobility opportunities analysis for selected roles
- [ ] Skill redundancy and gap analysis across departments/functions
- [ ] Workforce transition scenario planning

**8.6.3 Department Analytics**
- [ ] Cross-department mobility analysis
- [ ] Skill concentration and risk assessment
- [ ] Workforce planning scenario modelling

#### 8.7 Scenario Planning Module - **PLANNED** 📋
**Branch: `8.7-feature/query-layer-webapp/scenario-planning`**

> **User Journey**: "If we sunset this role, where could these 50 people go?" → Migration heatmap with absorption capacity analysis.

**8.7.1 CLI Pre-Computation Support**
- [ ] Generate role absorption capacity matrices
- [ ] Pre-compute workforce migration scenarios for common role changes
- [ ] Create supply/demand models for internal job markets

**8.7.2 Scenario Planning Interface**
- [ ] "What-if" role sunsetting analysis
- [ ] Workforce migration scenario modelling
- [ ] Capacity planning for role expansion/contraction
- [ ] Geographic workforce redeployment analysis

#### 8.8 Advanced Visualisation & Reporting - **PLANNED** 📋
**Branch: `8.8-feature/query-layer-webapp/advanced-viz`**

**8.8.1 Enhanced Visual Components**
- [ ] Interactive network graphs for career pathway exploration
- [ ] Skill heatmaps and similarity matrices
- [ ] Career progression trees and branching visualisations
- [ ] Geographic mobility and opportunity mapping

**8.8.2 Extended White Paper Types**
- [ ] Team transition planning reports
- [ ] Department restructure impact analysis
- [ ] Skill development roadmaps with market context
- [ ] Executive workforce planning summaries

#### 8.9 Deployment & Versioning Strategy - **PLANNED** 📋
**Branch: `8.9-feature/query-layer-webapp/deployment`**

> **Seamless User Experience**: Data scientist runs quarterly CLI pre-computation → outputs to OneDrive → non-technical users double-click .bat file → webapp loads with latest data.

**8.9.1 CLI Pre-Computation Workflow**
- [ ] Quarterly pre-computation command that generates all webapp data
- [ ] Automated output packaging for shared deployment location
- [ ] Version stamping and metadata generation
- [ ] Data validation and quality checks before deployment

**8.9.2 OneDrive Deployment Strategy**
- [ ] Standardised output directory structure for shared location
- [ ] Version-aware .bat launcher that checks for latest data
- [ ] User-friendly version display in webapp header
- [ ] Automatic data refresh detection and notification

**8.9.3 User Experience Optimisation**
- [ ] One-click deployment for non-technical users
- [ ] Clear version and last-updated information in webapp
- [ ] Graceful handling of missing or outdated data
- [ ] User guidance for accessing latest versions

#### 8.10 Integration & Performance - **PLANNED** 📋
**Branch: `8.10-feature/query-layer-webapp/integration`**

**8.10.1 Data Integration**
- [ ] Efficient loading of all pre-computed datasets
- [ ] Version compatibility checks between CLI outputs and webapp
- [ ] Memory management for large pre-computed matrices
- [ ] Background data refresh capabilities

**8.10.2 Performance Optimization**
- [ ] Query response time optimization (target <2 seconds)
- [ ] Smart caching of pre-computed results
- [ ] Lazy loading for complex visualisations
- [ ] Resource monitoring and performance metrics

**8.10.3 Testing & Validation**
- [ ] User acceptance testing with business colleagues
- [ ] Performance testing with full pre-computed datasets
- [ ] Cross-browser compatibility testing
- [ ] End-to-end deployment workflow testing
- [ ] Security review for corporate OneDrive environment

### Phase 9: Enterprise Integration & Advanced Intelligence - **ASPIRATIONAL** 🔮

> **Future Scope**: These features require external integrations, enterprise licenses, or advanced AI capabilities beyond the current local webapp scope. They represent the evolution toward enterprise-grade talent intelligence platforms.

### 9.1 External Market Intelligence Integration
**Branch:** 9.1-feature/enterprise-integration/market-intelligence
**Goal:** Integrate external market data to enhance internal career pathway recommendations.
- **Lightcast Skills Taxonomy** integration for market demand signals
- **Labour market analytics** for role growth/decline predictions  
- **Cross-industry mobility** benchmarking against external datasets
- **Real-time job market** demand integration for pathway prioritisation
- ✅ Inspiration: LinkedIn Talent Insights, Lightcast Analytics

### 9.2 AI-Powered Career Coaching
**Branch:** 9.2-feature/enterprise-integration/ai-coaching
**Goal:** Advanced AI recommendations that go beyond skill similarity to include market trends and personalized guidance.
- **Predictive analytics** for role evolution and skill obsolescence
- **AI-powered coaching** recommendations based on career progression patterns
- **Natural language** career pathway explanations and guidance
- **Machine learning** for improving pathway recommendations over time
- ✅ Inspiration: Gloat Intelligence, Eightfold AI Career Coaching

### 9.3 Enterprise Workforce Intelligence Platform
**Branch:** 9.3-feature/enterprise-integration/workforce-platform
**Goal:** Full enterprise integration with HRIS, learning systems, and strategic workforce planning platforms.
- **Real-time HRIS integration** for live workforce analytics
- **Learning Management System** integration for skill development tracking
- **Strategic workforce planning** integration with enterprise tools (Workday, SAP SuccessFactors)
- **Multi-tenant deployment** for different business units and geographies
- **API ecosystem** for integration with other enterprise talent tools
- ✅ Inspiration: Workday Skills Cloud, SAP People Analytics, Oracle HCM

### 🧠 Optional New Feature Proposals

#### 9.9 Skill Adjacency Explorer
**Branch:** 9.9-feature/future-features/skill-adjacency-explorer
- Let users input a skill and get:
  - Nearby related skills (based on co-occurrence in jobs or Lightcast graph)
  - Jobs that heavily use this skill
  - Suggested upskilling paths from this skill
- 🎯 This could help HR craft upskilling programs and shows off skill-level granularity

#### 9.10 Capability Impact Modeller
**Branch:** 9.10-feature/future-features/capability-impact-modeller
- Allow "what-if" analysis for capabilities (groups of skills)
- Example: "What roles rely on Cloud Infrastructure skills? What happens if we lose this capability?"
- 🎯 This connects to strategic capability frameworks and allows higher-level planning above roles

## 10. New Functionality Enabled by Employee-Level Skills Data

*Note: The following features are not currently planned or in scope, but are listed to illustrate the future potential of the Skill Similarity Engine if employee-level skill data becomes available. These capabilities would build on the job-to-job similarity and prescribed skills work, enabling a new class of workforce analytics and talent management tools.*

### 🔁 1. Job Matching & Career Navigation
**Branch:** 10.1-feature/employee-insights/job-matching
**What it does:**
Match employees to potential internal roles based on their current skillset (vs. prescribed skills for the role).

**Features you can deliver:**
- Personalised internal job recommendations
- Skill delta display: "You're 85% ready for Job X"
- Visual role pathways: "Shortest path to move from Job A to Job Z"
- Alerts for "roles you're nearly ready for" or "roles in high demand you could upskill into"

*Precedent: Gloat, Eightfold, Workday Career Hub*
*Internal Use Only: This could be a "silent" advisory tool for workforce planning without publishing scores to employees.*

### 🔗 2. Internal Coaching / Mentoring Marketplace
**Branch:** 10.2-feature/employee-insights/coaching-marketplace
**What it does:**
Identify employees with skills others are missing and recommend them as mentors, SMEs, or informal coaches.

**Features you can deliver:**
- "Who in the org has skills in X?"
- "Which team could support upskilling in Y?"
- Skill supply heatmaps per BU/location
- Match people with complementary skills for coaching/mobility pilots

*Precedent: Gloat's "Projects & Mentors", Degreed SkillShare*
*Internal Use Only: Use these insights to support talent mobility programs or identify internal champions, not to publish open marketplaces (unless culturally appropriate).*

### 📈 3. Upskilling & Workforce Readiness Analysis
**Branch:** 10.3-feature/employee-insights/workforce-readiness
**What it does:**
Track readiness at the individual, team, or cohort level for critical roles or future-state workforce needs.

**Features you can deliver:**
- "How ready is Team A to support transition to Capability X?"
- "Which employees are 70%+ ready for AI/ML-related roles?"
- "What's the average skill gap for Role X across the current workforce?"

*Precedent: Eightfold Workforce Insights, Workday's Future-Ready Workforce dashboards*

### 🧬 4. Skill Adjacency-Based Recommendations
**Branch:** 10.4-feature/employee-insights/skill-adjacency-recs
**What it does:**
Suggest upskilling opportunities for employees based on skills they already have and jobs they're close to.

**Features you can deliver:**
- "Based on your skills, here are 3 adjacent capabilities to grow"
- Pathways for high-leverage skills (e.g., "You're 1 course away from cloud proficiency")
- Predictive growth mapping: "Most likely roles for this person in 12 months"

*Precedent: Lightcast adjacencies + internal journey builders*
*Benefit: Helps frame talent transformation as opportunity-led, not deficit-led.*

### 🎯 5. Strategic Talent Pooling
**Branch:** 10.5-feature/employee-insights/talent-pooling
**What it does:**
Segment the workforce by capability, readiness, risk, or growth potential.

**Features you can deliver:**
- Create "talent pools" for critical capabilities (e.g., AI fluency, regulatory compliance)
- Build internal pipelines: "Who could be the next cohort of Risk Advisors?"
- Inform succession planning with bottom-up insights

*Precedent: SAP SuccessFactors, Oracle HCM succession tools*
*Benefit: Allows for proactive reskilling and retention in key areas*

### 🧠 6. Organisational Intelligence & Capability Mapping
**Branch:** 10.6-feature/employee-insights/org-intelligence
**What it does:**
Zoom out to see capabilities at scale, role duplication, and skill redundancy.

**Features you can deliver:**
- "Where does this capability live in the organisation?"
- "Which BUs have similar skill profiles?"
- "Which locations have overlapping capabilities?"
- "Where are our single points of failure?"

*Precedent: Gloat's org capability graphs*
*Strategic Value: Informs restructure decisions, talent movement, and role aggregation*

### 🛑 Caveats and Guardrails
Because you mentioned this would be internal only, here's how to manage the risks:

| Risk                   | Mitigation                                                                                 |
|------------------------|------------------------------------------------------------------------------------------|
| Perceived surveillance | Keep insights team-facing only; don't score or rank individuals publicly                  |
| Skill data quality     | Introduce confidence scores or tags like "self-assessed", "validated by manager", "inferred from project history" |
| Equity & transparency  | Be intentional with fairness—e.g., don't let lack of visibility penalise someone with strong but undocumented skills |
| Overreach risk         | Keep role recommendations as nudges or planning tools, not mandates                      |

### 🚀 Combined Use Case Example
Say you want to build an internal data science capability in Vietnam. With employee-level skills, you could:
- Identify current Vietnamese employees with Python, SQL, and analytics
- Compare them to prescribed skills for 'Data Scientist' roles
- Run a skill delta analysis and propose upskilling programs
- Identify internal SMEs across the business who could coach
- Model potential internal transitions into those roles
- Track readiness over time

You're suddenly doing build vs. buy at the capability level—powered by actual employee data.

**Key Achievement**: Section 6.7.5 successfully implemented and validated. Model governance framework provides professional quarterly versioning with complete audit trails, dual-format outputs, and clean separation of concerns. The system is production-ready for large-scale datasets with intelligent hardware optimisation and comprehensive error handling.

**End-to-End Testing Results**:
- **Data Loading**: 2,068 skills, 715 jobs, 40,170 job-skill mappings processed with chunked loading
- **Similarity Generation**: 510,510 job pair comparisons completed in ~3 seconds  
- **Output Generation**: Both CSV (17.5MB) and Parquet files created successfully
- **Versioning**: Created `models/2025-Q2/precompute_20250608_132404/` structure correctly
- **Multi-format Success**: CSV for Power BI cloud compatibility, Parquet for efficient local analysis
- **Performance**: Stable memory usage (~84MB), excellent processing speed
- **User Confirmation**: "healthy results" validated by user testing

**Architecture Benefits Achieved**:
- Clean modularisation with `ModelVersionManager` class
- Time intelligence with accurate quarterly detection (Q2, not Q8)
- Dual format support for both efficiency (Parquet) and compatibility (CSV)
- Production-ready governance with comprehensive audit trails

**Benefits**: This governance framework ensures that quarterly similarity matrix updates are managed professionally with full audit trails, quality assurance, and rollback capabilities. It provides confidence for business users and maintains data integrity across model evolution cycles.

**Section 6.7.5 Achievement Summary**: Model governance framework successfully implemented and validated with professional quarterly versioning, complete audit trails, dual-format outputs, and clean separation of concerns. End-to-end testing confirmed production readiness: 510,510 job pair comparisons completed in ~3 seconds, both CSV (17.5MB) and Parquet files generated successfully, and intelligent quarterly versioning working correctly with `models/2025-Q2/precompute_20250608_132404/` structure. The `ModelVersionManager` class provides clean modularisation with time intelligence and production-ready governance capabilities.

#### 6.11 Query Interface for Pre-computed Data - **PLANNED**