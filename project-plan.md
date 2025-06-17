# Skill Similarity Engine - Project Plan

## Overview

This document outlines the development plan for the NAB Skill Similarity Engine, a system designed to analyse skill similarities between jobs to identify reskilling opportunities. The project implements a two-phase architecture optimised for JobProfile-level analysis.

> **📋 WEBAPP SITEMAP**: Detailed user stories, feature specifications, and development roadmap for the Flask webapp are documented in [`docs/webapp-sitemap-user-stories.md`](docs/webapp-sitemap-user-stories.md)

> **ARCHITECTURAL FOCUS**: The system operates on **JobProfile similarity** (architectural blueprints with prescribed skills) rather than complex individual position analysis. This aligns with current business priorities and data availability, delivering core value through pure skill-based similarity calculations.

> **PRIMARY OUTPUT OBJECTIVE**: The core deliverable is a comprehensive **JobProfile similarity dataset in tabular format** optimised for Power BI integration. This tabular output (structured as a fact table with job1, job2, and similarity metrics) serves as the foundation for all downstream analytics.

> **TWO-PHASE ARCHITECTURE**: 
> 1. **Pre-computation Phase**: Generates pure JobProfileID-to-JobProfileID skill similarity matrices (production-ready)
> 2. **Query Phase**: Applies contextual weightings when needed (Flask webapp implementation)

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

## Current Priority: Real Data Integration for Career Pathways

> **IMMEDIATE FOCUS**: Phase 8.2.4 Career Pathway Explorer is functionally complete but requires real data integration to replace mock data in Skills Transition Analysis and Workforce Intelligence sections. This is the **highest priority** before moving to Phase 8.2.5.

**🎯 NEXT IMMEDIATE TASKS (8.2.4 Real Data Integration):**
1. **Skills Analysis Real Data** - Connect to job_skills table for real skill overlap calculations
2. **Workforce Intelligence Real Data** - Connect to positions table for real position counts and geographic distribution  
3. **Database Query Optimization** - Ensure sub-2-second performance with real data queries
4. **Data Validation & Error Handling** - Graceful handling of incomplete real data
5. **User Interface Updates** - Update JavaScript to handle real data structures and edge cases

**📊 SUCCESS CRITERIA**: 100% real data across all three sections (Career Progression Journey ✅, Skills Transition Analysis 📋, Workforce Intelligence 📋)

## Next Phase: Query Layer Implementation

> **CLI Implementation Note**: The CLI interface is fully functional in `main.py` with menu-driven data loading, similarity matrix generation, model versioning, and export capabilities. This completes the **pre-computation phase** of our two-phase architecture.

### Phase 8: Query Layer & Flask Webapp - **IN PROGRESS** 🚧
**Branch: `8-feature/query-layer-webapp`**

> **Business Priority**: Urgent need for career pathway exploration and white paper generation for colleagues facing role transitions. This phase delivers the query layer of our two-phase architecture, making the pre-computed similarity data accessible to non-technical business users.

#### 8.1 Business Context Database Foundation - **COMPLETED** ✅
**Branch: `8.1-feature/business-context-foundation`**

Successfully created the comprehensive business context database that powers the Flask webapp, integrating job similarities, skills taxonomy, workforce positions, and job architecture into a single optimised SQLite database for fast querying.

**Core Tasks:**

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
- [x] **Cross-Dataset Key Analysis**
  - [x] Create exploration script: `scripts/explore_data_relationships.py`
  - [x] Analyze primary keys, foreign keys, and relationship cardinalities
  - [x] Document data quality: completeness, consistency, duplicates
  - [x] Identify optimal join strategies and performance considerations

- [x] **Schema Design & Documentation**
  - [x] Design SQLite schema with proper normalization
  - [x] Define table relationships and foreign key constraints  
  - [x] Plan indexes for fast webapp queries (by job family, location, etc.)
  - [x] Document schema in `docs/sqlite_schema_design.md`
  - [x] Create entity-relationship diagram for schema visualization

- [x] **Data Integration Strategy**
  - [x] Plan JOIN operations between datasets
  - [x] Handle missing data and data quality issues
  - [x] Design aggregation tables for performance (if needed)
  - [x] Validate relationship integrity across all datasets

**8.1.3 CLI Enhancement for Business Context Database** ✅ **COMPLETED** (schema design ✅, data pipeline ✅)
- [x] **Extend main.py menu system** to include business context processing
  - [x] Add new menu option: "2. Generate Business Context Database"  
  - [x] Create sub-menu for business context configuration options
  - [x] Integrate with existing model versioning system (output to `models/2025-Q2/`)

- [x] **Create new src modules for relational data processing**:
  - [x] `src/skill_similarity_engine/business_context/` directory structure ✅ **COMPLETED**
  - [x] `src/skill_similarity_engine/business_context/schema_builder.py` - SQLite schema with 2-table architecture ✅ **COMPLETED**
  - [x] `src/skill_similarity_engine/business_context/data_loader.py` - Enhanced data loading with position enrichment ✅ **COMPLETED**
  - [x] `src/skill_similarity_engine/business_context/validator.py` - Data validation and relationship integrity ✅ **COMPLETED**

- [x] **Enhanced data loaders for new folders**:
  - [x] Extend existing loaders to read from `data/job_architecture/`, `data/skills_library/`, `data/workforce_context/` ✅ **COMPLETED**
  - [x] Create validation and quality checks for relational data integrity ✅ **COMPLETED**
  - [x] Handle missing data and provide fallback strategies ✅ **COMPLETED**

- [x] **SQLite database design and creation**:
  - [x] Design optimised schema for webapp queries (jobs, skills, positions, job_similarities tables) ✅ **COMPLETED**
  - [x] Implement 2-table architecture (simplified from original 3-table design) ✅ **COMPLETED**
  - [x] Create indexes for fast filtering (by JobProfileID, business unit, job family, etc.) ✅ **COMPLETED**
  - [x] Position enrichment: 100% JobProfileID population via position_job_mapping integration ✅ **COMPLETED**
  - [x] Skills enhancement: 14 columns including Category, Subcategory, Description, Info_URL, Is_Language ✅ **COMPLETED**
  - [x] Output: `models/2025-Q2/business_context.sqlite` (alongside existing similarity matrices) ✅ **COMPLETED**

- [x] **CLI integration and user experience**:
  - [x] Progress tracking and logging for large dataset processing ✅ **COMPLETED**
  - [x] Validation reports (data quality, coverage, relationship integrity) ✅ **COMPLETED**
  - [x] Option to regenerate only business context without re-running similarity computation ✅ **COMPLETED**
  - [x] Error handling and recovery for partial processing ✅ **COMPLETED**
  - [x] Configuration-driven data loading with `data_sources.yaml` ✅ **COMPLETED**

**8.1.1 Enhanced Data Pipeline - Analysis & Requirements**

> **Current State Analysis**: The existing system processes basic job similarity using minimal fields (`JobProfileID`, `RoleSet`, `Salary Group`, basic skills). This enables pure skill-based similarity but lacks contextual richness for career pathway exploration and business filtering.

#### 8.2 Flask Webapp Development - **IN PROGRESS** 🚧
**Branch: `8.2-feature/webapp-foundation`**

> **📋 STRATEGIC REFERENCE**: Detailed sitemap, user stories, and feature specifications are documented in [`docs/webapp-sitemap-user-stories.md`](docs/webapp-sitemap-user-stories.md)

This phase builds a **restricted-access strategic intelligence platform** exclusively for the Future Skills team to support data-driven workforce planning and capability analysis. The webapp queries the SQLite business context database to provide sensitive workforce intelligence for strategic decision-making.

> ⚠️ **RESTRICTED ACCESS TOOL**: This platform contains highly sensitive workforce intelligence that informs strategic organizational decisions. Access is strictly limited to authorized Future Skills team members and selected strategic partners.

**Primary User Personas** (RESTRICTED ACCESS ONLY):
- **Future Skills Team Members** - Strategic workforce analysts conducting capability assessments
- **Future Skills Team Leaders** - Senior strategists making workforce transformation recommendations  
- **Authorized Strategic Partners** - Selected HR and business leaders with specific project access

**Strategic Platform Features:**
1. **🔍 Workforce Intelligence** - Job similarity analysis and skills capability mapping
2. **📋 Strategic Reports** - Professional transition impact analysis and capability assessment reports
3. **🎯 Transition Pathways** - Role transition analysis and redeployment opportunity identification
4. **📊 Advanced Analytics** - Skills drift analysis and workforce planning insights
5. **📚 Comprehensive Documentation** - Methodology documentation and calculation transparency

**Technical Foundation** (✅ Already Built):
- Flask app architecture with SQLite integration
- Organised SQL queries (`similarities.sql`, `jobs.sql`, etc.)
- Professional NAB-styled UI components
- D3.js visualisation foundation (career pathways)
- Business context database with comprehensive job/skills/position data

**Current Implementation Status:**
- ✅ UI Framework & Component Library (8.2.2) - **COMPLETED**
- ✅ Workforce Intelligence Core (8.2.3) - **COMPLETED**
- ✅ Career Pathway Explorer (8.2.4) - **COMPLETED** (Real Data Integration Required)
- ✅ Executive Dashboard Enhancement (8.2.5) - **95% COMPLETED** (Cross-Family Analysis Remaining)
- 📋 Strategic Reports Generator (8.2.6) - **NEXT PRIORITY** *(Renumbered from 8.2.5)*
- 📋 Documentation & Methodology Transparency (8.2.7) - **PLANNED** *(Renumbered from 8.2.6)*

**8.2.2 User Interface Foundation** ✅ **COMPLETED**  
**Branch: `8.2.2-feature/webapp-foundation/ui-framework`**

- [x] **HTML Template System**
  - [x] Create base template with NAB-inspired styling ✅ **COMPLETED**
  - [x] Implement responsive navigation header and footer ✅ **COMPLETED**
  - [x] Set up Jinja2 macro library for reusable components ✅ **COMPLETED**
  - [x] Create page layout templates (single-column, dashboard) ✅ **COMPLETED**
  - [x] Add breadcrumb navigation system ✅ **COMPLETED**

- [x] **CSS Framework & Styling**
  - [x] Choose CSS framework (Tailwind CSS selected) ✅ **COMPLETED**
  - [x] Create professional colour scheme inspired by NAB branding ✅ **COMPLETED**
  - [x] Implement responsive design system (mobile-first) ✅ **COMPLETED**
  - [x] Align with comprehensive NAB design system (fonts, colours, components) ✅ **COMPLETED**
  - [x] Create component library following NAB style guide patterns ✅ **COMPLETED**

- [x] **JavaScript Architecture**
  - [x] Set up modern JavaScript (ES6+) with module system ✅ **COMPLETED**
  - [x] Implement AJAX patterns for dynamic content loading ✅ **COMPLETED**
  - [x] Create utility functions for API communication ✅ **COMPLETED**
  - [x] Add loading states and user feedback mechanisms ✅ **COMPLETED**
  - [x] Set up event handling for interactive components ✅ **COMPLETED**

- [x] **Component Library**
  - [x] Build form components (inputs, selects, checkboxes) ✅ **COMPLETED**
  - [x] Create data table components for similarity results ✅ **COMPLETED**
  - [x] Implement modal dialogs for detailed views ✅ **COMPLETED**
  - [x] Add button components with consistent styling ✅ **COMPLETED**
  - [x] Create loading spinners and progress indicators ✅ **COMPLETED**

**8.2.3 Workforce Intelligence Core** ✅ **COMPLETED**
**Branch: `8.2.3-feature/webapp-foundation/workforce-intelligence`**

> **Strategic Focus**: *"As a Future Skills analyst, I need comprehensive workforce intelligence tools to assess role transitions and support strategic workforce planning decisions."*

**Successfully Implemented Components** (in `components.html`):

- [x] **Job Search & Discovery Interface** ✅ **COMPLETED**
  - [x] Searchable multi-select dropdown for JobProfile selection with real-time filtering
  - [x] Advanced filtering by Job Family, Division, Business Unit, Career Level, Location
  - [x] Visual tag system for selected profiles with removal capability
  - [x] Prevention of duplicates and validation requiring selections
  - [x] 20 demo job profiles with realistic NAB data structure
  - [x] Export functionality for search results

- [x] **Strategic Job Analysis Results Display** ✅ **COMPLETED**
  - [x] Aggregated position deployment view by Division + Business Unit combination
  - [x] Position counts showing actual workforce deployment (e.g., "8 positions")
  - [x] Location spread with geographic codes (e.g., "MEL(5), SYD(2), BNE(1)")
  - [x] Strategic organizational deployment context for workforce planning
  - [x] "View Positions" action for detailed drill-down capability
  - [x] "Find Similar" action for similarity analysis integration

- [x] **Enhanced Filtering & Business Intelligence** ✅ **COMPLETED**
  - [x] Separate Division filter (Business & Private Banking, Corporate & Institutional Banking, etc.)
  - [x] Separate Business Unit filter (Group Technology, Business Banking, etc.)
  - [x] Hierarchical filtering allowing Division→Business Unit drill-down
  - [x] Min similarity threshold controls for analysis precision
  - [x] Maximum results limiting for focused analysis

- [x] **Methodology Transparency & Strategic Context** ✅ **COMPLETED**
  - [x] Info icon tooltips explaining calculation methodologies
  - [x] Strategic language appropriate for Future Skills team
  - [x] Professional NAB-styled interface with consistent branding
  - [x] Clear data source indicators and methodology transparency
  - [x] Export capabilities for further strategic analysis

**Strategic Value Delivered**: 
The implementation transforms the tool from a job catalogue to genuine strategic workforce intelligence, answering real business questions like "If we sunset this role, how many people are affected and where?" The aggregated position data shows actual organizational deployment patterns, enabling informed workforce planning decisions about capability concentration, redeployment opportunities, and impact assessment for organizational changes.

**8.2.4 Career Pathway Explorer** ✅ **COMPLETED** 
**Branch: `8.2.4-feature/webapp-foundation/career-pathways`**

> **User Story Focus**: *"As a Risk Analyst, I want to see visual career pathways showing how I can progress to different roles over time, with clear skills development requirements."*

**🚀 MAJOR BREAKTHROUGH**: Replaced on-the-fly computation with **pre-computed career pathways** (8,580 relationships), solving the 714→3→2→1 performance limitation and enabling deep pathway exploration with real-time responsiveness.

**Architectural Achievement**: Complete pipeline from similarity matrix generation → career pathway pre-computation → SQLite database integration, ready for webapp consumption.

**✅ COMPLETED ACHIEVEMENTS:**

- [x] **Pre-Computed Career Pathway Engine** 
  - [x] Fixed similarity calculation algorithm (eliminated all-zero similarity bug)
  - [x] Integrated job-skill mapping data (40,170 relationships) for accurate similarities
  - [x] Generated 8,580 pre-computed career pathway relationships (avg 12 per job)
  - [x] Career move type classification: 74.4% progression, 25.6% lateral moves
  - [x] Difficulty scoring and similarity ranking for all pathways
  - **Performance Impact**: From on-the-fly limited computation → instant access to full relationship matrix

- [x] **Complete Data Pipeline Infrastructure**
  - [x] Chunked similarity matrix pre-computation with progress tracking
  - [x] Career pathways generation with adaptive chunking and memory management
  - [x] Parquet + CSV dual-format output for performance and compatibility
  - [x] Date-based versioning system (models/2025-Q2/precompute_YYYYMMDD/)
  - [x] SQLite database integration with 510,510 similarity pairs + 8,580 career pathways

- [x] **Enhanced CLI User Experience**
  - [x] Clean visual sections with emojis and progress indicators
  - [x] Structured information display with thousands separators
  - [x] Reduced log noise (WARNING level default) with meaningful user updates
  - [x] Smart file path validation with automatic data/ prefix detection
  - [x] Runtime estimation and memory usage monitoring

- [x] **D3.js Tree Visualization Foundation**
  - [x] Basic D3.js collapsible tree implementation with career pathway data
  - [x] Tree expansion/collapse functionality with depth controls
  - [x] Node filtering by similarity threshold and organizational context
  - [x] Professional NAB-styled tree visualization with consistent branding
  - [x] Integration with pre-computed career_pathways table (8,580 relationships)
  - [x] Tree state analysis and adaptive behavior (COLLAPSED/MEDIUM/LARGE detection)
  - [x] Comprehensive debug logging and performance monitoring

- [x] **D3.js Tree Spacing & Text Layout Solution** ✅ **COMPLETED**
  - [x] **BREAKTHROUGH**: Implemented nodeSize() approach instead of size() for fixed node spacing
  - [x] Resolved text overlap issue completely with guaranteed space allocation per node
  - [x] Optimized node dimensions: 50px width × 300px height for perfect spacing balance
  - [x] Added expand/collapse indicators (► ▼) to show node states clearly
  - [x] Set initial tree load to show only root + first level children for clean UX
  - [x] Eliminated complex spacing calculations - D3 nodeSize() handles everything automatically
  - **Impact**: Text overlap completely resolved, tree is readable and professional at all levels

- [x] **Organizational Filtering System** ✅ **COMPLETED**
  - [x] **CRITICAL FIX**: Resolved additive filter behavior that was incorrectly expanding results
  - [x] Implemented restrictive filtering logic ensuring all criteria apply to SAME position record
  - [x] Fixed SQL query logic from separate IN clauses to single unified WHERE clause
  - [x] Comprehensive testing with all filter combinations (Division, Business Unit, Location, Region)
  - [x] Progressive filtering validation: 10→7→3→5→1→0 jobs (properly restrictive)
  - [x] Production-ready organizational context filtering for career pathway exploration
  - **Impact**: Organizational filters now work as intended - restrictive, not additive

- [x] **Interactive Career Pathway Analysis System** ✅ **COMPLETED**
  - [x] **Tree Node Selection & Highlighting**: Golden glow highlighting for selected nodes with enhanced visual feedback
  - [x] **Dynamic Career Progression Journey**: Breadcrumb trail automatically generated from tree selections showing full pathway
  - [x] **Interactive Breadcrumb Selection**: Click any step in the journey to analyze that specific transition
  - [x] **Context-Aware Analysis Sections**: Skills Transition Analysis and Workforce Intelligence update based on selected breadcrumb
  - [x] **Real-Time Pathway Updates**: All three analysis sections (Journey, Skills, Workforce) update dynamically with tree selections
  - [x] **Professional UI Polish**: Smooth transitions, loading indicators, and error handling for production use
  - **User Experience**: Click tree node → see pathway → click any breadcrumb → analyze that transition step

**🎯 REMAINING WEBAPP INTEGRATION:**

- [x] **Interactive Career Tree Visualization** (`/career-pathways`) ✅ **COMPLETED**
  - [x] ~~Multi-hop pathway discovery~~ → **Pre-computed with 8,580 relationships**
  - [x] ~~Pathway ranking algorithm~~ → **Completed: similarity_rank, difficulty_score**
  - [x] ~~Basic D3.js tree implementation~~ → **Completed with nodeSize() spacing solution**
  - [x] ~~**CRITICAL**: Solve text overlap issue~~ → **RESOLVED with nodeSize() approach**
  - [x] Colour-coded similarity strength using similarity scores (green/yellow/orange/red)
  - [x] Click-to-expand using career_pathways table with ► ▼ indicators
  - [x] Initial load shows root + first level only for clean user experience
  - **Database Ready**: `career_pathways` table with 8,580 relationships ✅ **IN USE**

- [x] **Webapp Query Integration** ✅ **COMPLETED** (Data Layer Complete)
  - [x] ~~Create pathway ranking algorithm~~ → **Complete: ranking + move types**
  - [x] ~~Career progression logic~~ → **Complete: lateral vs. progression classification**
  - [x] Connect webapp queries to pre-computed career_pathways table
  - [x] **Implement organizational filtering using positions table** ✅ **COMPLETED**
  - [x] Add real-time pathway exploration (data pre-computed, just need UI)

- [x] **Filter Panel UI Improvements** ✅ **COMPLETED**
  - [x] **Restructure filter panel with 3-column layout for sliders** ✅ **COMPLETED**
  - [x] **Make filter panel collapsible for better screen real estate** ✅ **COMPLETED**
  - [x] **Remove Job Families dropdown (simplify interface)** ✅ **COMPLETED**
  - [x] **Enhanced loading indicators with spinner animation** ✅ **COMPLETED**
  - [x] **Improved button structure and state management** ✅ **COMPLETED**
  - [x] **Arrange similarity, depth, and [third slider] side by side** ✅ **COMPLETED**
  - [x] **Add expand/collapse animation for smooth user experience** ✅ **COMPLETED**

- [x] **Advanced Pathway Intelligence Features** ✅ **PARTIALLY COMPLETED**
  - [ ] Alternative vs. recommended pathway highlighting in tree visualization
  - [x] **Geographic mobility filtering using positions table (Location, Division)** ✅ **COMPLETED**
  - [ ] Career progression detection (junior → senior role logic using job levels)
  - [ ] Pathway categorization (direct, bridge roles, long-term progression)
  - [ ] Click-to-expand pathway exploration with detailed transition info

- [ ] **Skills Development Roadmaps** (`/career-pathways/roadmap`)
  - [x] ~~Calculate skills gaps~~ → **Pre-computed: shared_skills_count per pathway**
  - [x] ~~Skills importance analysis~~ → **Complete: 40,170 job-skill mappings integrated**
  - [ ] Connect webapp to job_skills table for gap visualization  
  - [ ] Create timeline view using pre-computed difficulty_score progression
  - [ ] Add milestone markers based on similarity_rank thresholds
  - [ ] Show skill adjacencies and prerequisites using skill category data
  - [ ] Create learning pathway recommendations based on skill gaps
  - [ ] Progress tracking interface for skill development journey
  - [ ] Achievement badges for pathway progression milestones
  - **Database Ready**: Job-skill mappings + career pathways + skills categories

- [x] **Enhanced Pathway Visualisation** ✅ **COMPLETED** (Foundation Complete)
  - [x] ~~Pathway data preparation~~ → **Complete: 8,580 relationships with similarity scores**
  - [x] ~~Similarity strength calculation~~ → **Complete: similarity_score + difficulty_score**
  - [x] **Update D3.js visualization to consume pre-computed data** ✅ **COMPLETED**
  - [x] **Add pathway strength color-coding using existing similarity_score** ✅ **COMPLETED**
  - [x] **Implement collapsible tree nodes for better navigation** ✅ **COMPLETED**
  - [x] **Add hover tooltips showing transition details (similarity, skills overlap)** ✅ **COMPLETED**
  - [x] **Visual node highlighting for last selected node** ✅ **COMPLETED**
  - [x] **Enhanced tooltip positioning and content** ✅ **COMPLETED**
  - [ ] Export pathway diagrams for presentations
  - [ ] Integration with job comparison tool from 8.2.3

- [x] **User Experience & Interface Polish** ✅ **PARTIALLY COMPLETED**
  - [x] **Add loading indicators for tree generation and data fetching** ✅ **COMPLETED**
  - [x] **Enhanced click behavior with dual-action functionality** ✅ **COMPLETED**
  - [x] **Improved tooltip positioning and user guidance** ✅ **COMPLETED**
  - [x] **Visual feedback for node selection (golden ring highlighting)** ✅ **COMPLETED**
  - [x] **Non-intrusive Section 3 integration (no auto-scroll)** ✅ **COMPLETED**
  - [x] Implement smooth animations for tree expansion/collapse
  - [x] Create breadcrumb navigation for deep pathway exploration
  - [x] Add pathway saving/bookmarking functionality for strategic analysis
  - [x] Mobile-responsive design for tablet access

- [x] **Context-Aware Selection Details Table** ✅ **COMPLETED**
  - [x] **Create table component showing details of clicked nodes from tree diagram** ✅ **COMPLETED**
  - [x] **Display job information (title, family, division, position counts) for selected pathways** ✅ **COMPLETED**
  - [x] **Show transition details (similarity score, shared skills, difficulty score, move type)** ✅ **COMPLETED**
  - [x] **Use similar styling to existing 'Strategic Job Analysis Results' component** ✅ **COMPLETED**
  - [x] **Update table content dynamically based on tree diagram selections** ✅ **COMPLETED**
  - [x] **Include export functionality for selected pathway details** ✅ **COMPLETED**

**🎯 STRATEGIC IMPACT**: This breakthrough eliminates the fundamental scalability constraint that limited career pathway exploration to 3→2→1 relationships. The system now provides instant access to comprehensive career intelligence with 8,580 pre-computed relationships, enabling real strategic workforce planning conversations about redeployment, capability development, and organizational resilience.

**✅ CRITICAL BLOCKER RESOLVED**: The **text overlap in D3.js tree visualization** has been completely resolved using the **nodeSize() approach**. The 6 previous spacing approaches (size() with separation functions, manual level spacing, etc.) were replaced with D3's nodeSize() method, which guarantees fixed space allocation per node and eliminates all text overlap issues.

**🎉 DEPLOYMENT READY**: The career pathway explorer is now fully functional with:
- ✅ **Zero text overlap** at all tree levels
- ✅ **Professional visual indicators** (► ▼) for expand/collapse states  
- ✅ **Clean initial UX** showing root + first level only
- ✅ **Color-coded similarity** scoring with excellent readability
- ✅ **Production-ready performance** with 8,580 pre-computed relationships

**Next Phase Focus**: With the core visualization challenges solved, future work can focus on **feature enhancement and user experience polish** as outlined in the remaining webapp integration tasks below.

**🔗 SKILLS HYPERLINKS IMPLEMENTATION** ✅ **COMPLETED** *(NEW ACHIEVEMENT)*

**8.2.4.7 Skills URL Integration Across Platform** ✅ **COMPLETED**
- [x] **Job Explorer Skills Hyperlinks** ✅ **COMPLETED**
  - [x] Updated backend API to include `Info_URL` field from skills table
  - [x] Enhanced `/api/job-details/<job_id>` endpoint with skills URL data
  - [x] Modified frontend JavaScript to create conditional hyperlinks
  - [x] Skills by category section: clickable skill badges when URLs available
  - [x] All skills list section: clickable skill names with external link indicators
  - [x] **Data Reality**: Only 9.7% of skills have URLs (3,730 of 38,395), but infrastructure ready

- [x] **Career Pathways Skills Hyperlinks** ✅ **COMPLETED**
  - [x] Updated skills-analysis API to include `info_url` field in detailed_skills response
  - [x] Enhanced SQL queries in both job1_skills and job2_skills CTEs
  - [x] Modified "Skills Shared Between Job Profiles" section with conditional hyperlinks
  - [x] Updated "Skills to Develop" section with conditional hyperlinks
  - [x] Consistent styling: `text-blue-600 hover:text-blue-800 hover:underline`
  - [x] Graceful fallback: plain text display when URLs not available

- [x] **Technical Implementation Details**
  - [x] Backend: Added `s.Info_URL` to all relevant SQL queries
  - [x] API Response: Included `info_url` field in JSON responses
  - [x] Frontend: Conditional rendering `${skill.info_url ? '<a href="..." target="_blank">' : ''}${skill.name}${skill.info_url ? '</a>' : ''}`
  - [x] User Experience: External links open in new tabs with visual indicators
  - [x] **Future Ready**: Infrastructure supports 100% URL coverage when data improves

**🎯 REAL DATA INTEGRATION REQUIREMENTS** 📋 **IN PROGRESS**

Based on the conversation summary, the current implementation uses a mix of real and mock data. Significant progress has been made on UI integration and breadcrumb functionality:

**✅ COMPLETED UI ENHANCEMENTS**

**8.2.4.0 JavaScript Modularization & Error Resolution** ✅ **COMPLETED**
- [x] **Resolved critical DOM errors** that were preventing breadcrumb selection from updating analysis sections
- [x] **Disabled problematic embedded functions** (`buildTransitionAnalysisForStep`, `buildStartingRoleAnalysis`) that caused null pointer exceptions
- [x] **Enhanced modular JavaScript integration** with proper fallback handling and state synchronization
- [x] **Fixed breadcrumb click handlers** to properly call API endpoints and update Skills/Workforce sections
- [x] **Improved error handling** with graceful fallbacks when modular system isn't available
- [x] **Added job ID extraction utilities** to handle different node data formats from tree and database
- [x] **Synchronized visual feedback** between embedded and modular JavaScript systems

**Console Log Evidence**: 
```
✅ Real skills analysis populated for step 3
✅ Real workforce analysis populated for step 2  
🔍 Fetching skills analysis: node_17 → node_81
🔍 Fetching workforce analysis for jobs: node_0, node_5, node_17, node_81
```

**Impact**: Breadcrumb selection now works flawlessly - clicking any breadcrumb triggers the correct API calls and updates both Skills Transition Analysis and Workforce Intelligence sections with contextually appropriate data.

**8.2.4.1 Career Breadcrumb Real Data Integration** 📋 **REQUIRED**
- [x] **Career breadcrumbs already use real data** ✅ **COMPLETED**
  - [x] Job titles from SQLite database (real JobProfile names)
  - [x] Similarity scores from pre-computed career_pathways table
  - [x] Pathway structure from actual database relationships
  - [x] Color-coded similarity matching using real similarity_score values

**📋 REMAINING DATA INTEGRATION TASKS**

**8.2.4.1 Skills Transition Analysis Real Data Integration** 📋 **NEXT PRIORITY**
- [ ] **Replace mock skills data with real skills from database**
  - [x] **API endpoint structure working** - `/api/skills-analysis/<from_job_id>/<to_job_id>` calls successful
  - [x] **JavaScript integration complete** - `populateSkillsTransitionAnalysisForStep()` calls API correctly
  - [x] **Breadcrumb context handling** - API calls update based on selected transition
  - [x] **Fix SQL queries** - Current API returns data but calculations need database integration
  - [x] **Connect to `job_skills` table** (40,170 real job-skill mappings) for accurate counts
  - [x] **Use real skill names** from `skills` table instead of hardcoded examples
  - [x] **Implement skill category grouping** and SkillType distribution

- [x] **Enhance skills analysis calculations**
  - [x] Calculate real "Skills Matched" count from shared skills between jobs
  - [x] Calculate real "Skills to Develop" from target job skills not in source job
  - [x] Calculate real "Transferable Skills" from source job skills applicable to target
  - [x] Use real skill categories (Technical, Leadership, etc.) from skills taxonomy
  - [x] Generate real transition difficulty scores based on actual skill gaps

**8.2.4.2 Workforce Intelligence Real Data Integration** 📋 **NEXT PRIORITY**
- [ ] **Replace mock workforce data with real position data**
  - [x] **API endpoint structure working** - `/api/workforce-analysis/<job_ids>` calls successful
  - [x] **JavaScript integration complete** - `populateWorkforceIntelligenceForStep()` calls API correctly
  - [x] **Breadcrumb context handling** - API calls update based on selected pathway
  - [x] **Fix SQL queries** - Current API returns data but calculations need database integration
  - [x] **Connect to `positions` table** for real position counts by job
  - [x] **Use real Division and Business Unit** data from positions table
  - [x] **Calculate actual geographic distribution** from real Location data

- [x] **Enhance workforce intelligence calculations**
  - [x] Calculate real position counts for each job in pathway
  - [x] Show real geographic spread (MEL, SYD, BNE counts) from positions data
  - [x] Display real organizational context (Division + Business Unit combinations)
  - [x] Generate real workforce impact analysis for pathway transitions
  - [x] Create real redeployment opportunity assessments

**8.2.4.4 Database Query Optimization for Real Data** 📋 **REQUIRED**
- [x] **Optimize SQL queries for real-time performance**
  - [x] Create efficient JOIN queries across jobs, skills, positions, career_pathways tables
  - [x] Add database indexes for fast pathway + skills + workforce queries
  - [x] Implement query caching for frequently accessed pathway combinations
  - [x] Optimize for sub-2-second response times with full real dataset

- [x] **Create comprehensive data validation**
  - [x] Validate data completeness across all integrated tables
  - [x] Handle missing skills data gracefully (some jobs may have incomplete skill mappings)
  - [x] Handle missing position data gracefully (some jobs may not have current positions)
  - [x] Provide fallback displays when real data is incomplete

**8.2.4.5 User Interface Updates for Real Data Display** 📋 **REQUIRED**
- [x] **Update JavaScript functions to handle real data structures**
  - [x] Modify `populateSkillsTransitionAnalysis()` to use real database queries
  - [x] Update `populateWorkforceIntelligence()` to display real position data
  - [x] Enhance error handling for real data edge cases
  - [x] Add loading indicators for real database queries

- [x] **Enhance data presentation for real complexity**
  - [x] Handle variable numbers of skills (some jobs have 5 skills, others have 50)
  - [x] Display skill categories and subcategories from real taxonomy
  - [x] Show confidence indicators for calculated metrics
  - [x] Add data quality indicators (e.g., "Based on X positions" disclaimers)

**🎯 INTEGRATION SUCCESS CRITERIA:**
1. **Skills Analysis**: Shows real skill names, real overlap counts, real development requirements
2. **Workforce Intelligence**: Shows real position counts, real geographic distribution, real organizational deployment
3. **Performance**: All real data queries complete in <2 seconds
4. **Data Quality**: Graceful handling of incomplete data with appropriate user messaging
5. **Accuracy**: All calculated metrics (similarity, skills gaps, position counts) reflect actual database values

**📊 CURRENT DATA STATUS SUMMARY:**
- ✅ **Real Data**: Career breadcrumbs, tree visualization, similarity scores, job titles, pathway structure
- ✅ **API Integration**: Skills and workforce analysis endpoints working with proper breadcrumb context
- ✅ **JavaScript Integration**: Breadcrumb selection triggers correct API calls and UI updates
- 📋 **SQL Query Integration**: API endpoints need database query fixes for real data calculations
- 🎯 **Integration Target**: Fix SQL queries to return real database calculations instead of mock data

**8.2.5 Executive Dashboard Enhancement** 📋 **NEXT PRIORITY**
**Branch: `8.2.5-feature/webapp-foundation/executive-dashboard`**

> **Strategic Focus**: *"Transform the homepage into a comprehensive executive intelligence platform showcasing high-level workforce insights derived from the comprehensive analysis in `executive_insights.json`."*

This phase elevates the homepage from a basic landing page to a strategic workforce intelligence dashboard that provides executives with immediate access to key insights about organizational capability, mobility potential, and strategic workforce planning opportunities.

**🎯 NAVIGATION ENHANCEMENT**

**8.2.5.1 Strategic Navigation Structure** 📋 **REQUIRED**
- [ ] **Executive Dashboard Section Navigation**
  - [ ] Platform Overview (key metrics and data version)
  - [ ] Career Pathway Intelligence (mobility hubs and connectivity infsights)
  - [ ] Workforce Mobility Analysis (similarity distribution and readiness scores)
  - [ ] Strategic Recommendations (executive-level actionable insights)
  - [ ] Cross-Family Analysis (inter-departmental mobility patterns)
  - [ ] Geographic Intelligence (location-based capability distribution)

- [ ] **Enhanced Navigation UX**
  - [ ] Smooth scroll navigation between dashboard sections
  - [ ] Collapsible section headers for executive briefing mode
  - [ ] Quick jump navigation sidebar for rapid insight access
  - [ ] Export capabilities for executive presentation materials
  - [ ] Print-friendly layout for board meeting materials

**📊 DASHBOARD CONTENT IMPLEMENTATION**

**8.2.5.2 Platform Overview Enhancement** ✅ **COMPLETED**
- [x] **Strategic Platform Metrics** (from `executive_insights.json`)
  ```
  🎯 PLATFORM OVERVIEW:
     • 715 job profiles across 8 job families
     • 38,395 skills in comprehensive taxonomy  
     • 2,091 skills actively in use (NEW: Skills In Use card)
     • 8,580 pre-computed career pathways
     • 5,000 active positions across 6 divisions
  ```
- [x] **Platform Metrics SQL Queries**: Complete with real-time database integration
- [x] **Enhanced Executive Context**: Added explanatory text describing foundation datasets
- [x] **Enhanced Metrics Display**: Add visual indicators and professional styling
- [x] **Contextual Tooltips**: Methodology explanations for executive understanding
- [x] **Skills In Use Card Implementation** ✅ **NEW ACHIEVEMENT**
  - [x] Added 5th metric card showing actual skills utilisation vs total library
  - [x] Updated SQL query: `COUNT(DISTINCT Skill_ID) FROM job_skills`
  - [x] Changed grid layout from 4 to 5 columns with orange colour scheme
  - [x] Professional tooltips explaining active skills vs comprehensive taxonomy
  - [x] **Impact**: Shows 2,091 skills actively mapped vs 38,395 total (5.4% utilisation)

**8.2.5.3 + 8.2.5.4 Workforce Mobility Intelligence Dashboard** ✅ **COMPLETED** *(Combined sections 8.2.5.3 + 8.2.5.4)*
- [x] **Unified Section Structure** with comprehensive explanatory text
- [x] **Pathway Connectivity Overview** 
  ```
  🚀 CAREER PATHWAY INSIGHTS:
     • 128 job family pathway combinations identified
     • Top mobility hub: Data & Analytics (618 connections)
     • Average pathway similarity: 0.78
  ```
- [x] **Workforce Mobility Readiness Analysis**
  ```
  🎯 WORKFORCE MOBILITY READINESS:
     • High mobility potential: 0.6% (executive-focused percentage display)
     • Medium mobility potential: 36.8% (strategic workforce flexibility)
     • Low mobility potential: 62.6% (requires significant development)
  ```
- [x] **Executive Narrative Structure**: Clear progression from connectivity → readiness → strategic insights
- [x] **Comprehensive SQL Queries**: Career pathway analysis + similarity distribution queries
- [x] **Strategic Context Enhancement**: Added explanatory paragraphs explaining practical applications
- [x] **Consistent Terminology**: "Job Profiles" throughout instead of mixed "jobs/roles" terminology
- [x] **Executive Storytelling**: Percentage-first display for better strategic impact

**8.2.5.5 Strategic Recommendations Panel** ✅ **COMPLETED**
- [x] **Executive Strategic Insights** with priority-based recommendations (HIGH/MEDIUM/LOW)
  ```
  🎯 STRATEGIC RECOMMENDATIONS IMPLEMENTED:
  
  1. 🛡️ WORKFORCE RESILIENCE (HIGH PRIORITY):
     • Skills Concentration Risk analysis with critical skills identification
     • Strategic cross-training and geographic distribution recommendations
  
  2. 🚀 CAREER MOBILITY OPTIMIZATION (MEDIUM PRIORITY):
     • Data & Analytics mobility hub optimization strategies
     • Internal talent development pathway leveraging
  
  3. 📊 TRANSITION READINESS ASSESSMENT (MEDIUM PRIORITY):
     • 36.8% workforce in medium mobility readiness analysis
     • Development investment focus recommendations
  
  4. 🔄 CROSS-FAMILY CAPABILITY BUILDING (LOW PRIORITY):
     • Risk & Compliance cross-functional opportunities
     • Structured capability exchange program recommendations
  ```
- [x] **Actionable Recommendations Display**: Executive-ready strategic insights with color-coded priority indicators
- [x] **Priority Indicators**: HIGH (red), MEDIUM (yellow), LOW (blue) priority visual system
- [x] **Implementation Roadmap**: Q1-Q4 2025 timeline with specific quarterly initiatives
- [x] **Cross-Family Mobility Intelligence**: Strategic inter-departmental transition analysis
- [x] **Strategic SQL Queries**: get_strategic_recommendations, get_skills_concentration_analysis, get_cross_family_mobility_opportunities
- [x] **Professional UI Design**: Priority badges, metric displays, and implementation timeline
~~**8.2.5.6 Cross-Family Similarity Intelligence**~~ 🚫 **DEFERRED** *(Future iteration enhancement)*
- ~~**Inter-Departmental Mobility Analysis**~~
  ```
  📈 TOP CROSS-FAMILY SIMILARITIES (FUTURE ENHANCEMENT):
     • Risk & Compliance ↔ Banking Operations (0.368 similarity)
     • Risk & Compliance ↔ Finance & Accounting (0.362 similarity)
     • Risk & Compliance ↔ Data & Analytics (0.360 similarity)
     • Human Resources ↔ Banking Operations (0.360 similarity)
  ```
- ~~**Cross-Family Analysis SQL Queries**~~:
  ```sql
  -- Job family similarity matrix analysis (FUTURE IMPLEMENTATION)
  SELECT 
      j1.JobFamily as family1,
      j2.JobFamily as family2,
      AVG(js.similarity_score) as avg_similarity,
      COUNT(js.similarity_score) as pair_count
  FROM job_similarities js
  LEFT JOIN jobs j1 ON js.job_from = j1.JobProfileID
  LEFT JOIN jobs j2 ON js.job_to = j2.JobProfileID
  WHERE j1.JobFamily IS NOT NULL AND j2.JobFamily IS NOT NULL
  GROUP BY j1.JobFamily, j2.JobFamily
  HAVING COUNT(js.similarity_score) >= 5
  ORDER BY avg_similarity DESC;
  ```
- ~~**Cross-Family Mobility Matrix**: Visual heatmap of inter-departmental connections~~
- ~~**Strategic Mobility Insights**: Executive interpretation of cross-functional opportunities~~
- ~~**Redeployment Intelligence**: Organisational restructure and capability reallocation insights~~

~~**8.2.5.7 Geographic Intelligence Dashboard**~~ 🚫 **REMOVED** *(Not prioritised for current implementation)*

~~**🔧 TECHNICAL IMPLEMENTATION**~~ 🚫 **DEFERRED** *(Technical implementation covered in existing sections)*

**🎯 STRATEGIC IMPACT OBJECTIVES:**
1. **Executive Briefing Ready**: Homepage serves as comprehensive workforce intelligence briefing
2. **Strategic Decision Support**: Key insights readily available for executive conversations
3. **Workforce Planning Intelligence**: Data-driven insights for organisational development
4. **Cross-Functional Understanding**: Clear visibility of inter-departmental mobility opportunities
5. **Geographic Strategy Support**: Location-based capability intelligence for strategic planning

**📊 SUCCESS METRICS:**
- **Dashboard Load Performance**: <2 seconds for all executive insights
- **Data Accuracy**: 100% alignment with `executive_insights.json` comprehensive analysis
- **Executive Usability**: Intuitive navigation and clear strategic context
- **Mobile Compatibility**: Full functionality on executive mobile devices
- **Export Capability**: Professional presentation materials generation

**🎯 SECTION 8.2.5 ACHIEVEMENT SUMMARY:**
- **Overall Progress**: 4/5 sections completed (80%)
- **Platform Overview**: ✅ Enhanced with 5th "Skills In Use" card showing 2,091 active skills
- **Workforce Mobility Intelligence**: ✅ Complete with pathway connectivity and readiness analysis
- **Strategic Recommendations**: ✅ Complete with priority-based recommendations and implementation roadmap
- **Skills Hyperlinks**: ✅ Complete across Job Explorer and Career Pathways (NEW ACHIEVEMENT)
- **Cross-Family Analysis**: 📋 Remaining task - inter-departmental mobility intelligence
- **Next Priority**: Complete Cross-Family Similarity Intelligence to achieve 100% section completion

---

**8.2.6 White Paper Generation System** 📋 **PLANNED**
**Branch: `8.2.6-feature/webapp-foundation/white-papers`**

> **🎯 DYNAMIC SIMILARITY FRAMEWORK**: Implement intelligent percentile-based story classification that adapts to actual data distribution rather than hardcoded thresholds. With similarity bell curve around 35%, a 68% similarity represents 94th percentile performance and should be classified as "Excellent Opportunities" rather than "Good". The system should dynamically calculate percentiles from the dataset and classify stories accordingly:
> - **Top 5%**: Outstanding Opportunities (immediate transition ready)
> - **Top 10%**: Excellent Opportunities (smooth transition prospects) 
> - **Top 25%**: Good Opportunities (manageable development required)
> - **Median**: Development Opportunities (significant upskilling needed)
> - **Below Median**: Transformation Required (major career pivot required)

> **🏢 BUSINESS COMMUNICATION FRAMEWORK**: Refined communication structure balancing technical accuracy with business context:
> - **Lead with JobProfile**: Start with HR architectural precision - "Analyst - Data Governance Specialist job architecture"
> - **Translate to Positions**: Follow with business-recognisable language - "which encompasses positions including Data Manager (5), Risk Senior Developer (8), Technology Principal Specialist (10)"
> - **Complete Structure**: "The [JobProfile] job architecture, which encompasses positions including [Position Names with counts]"
> - **Technical Foundation**: One JobProfile → Many Positions (1:many relationship)
> - **Database Strategy**: Query positions table for counts/geography, map through jobs table for similarity calculations
> - **Business Value**: Maintains technical traceability while providing immediate operational context

- [ ] **Template Engine & Content Generation**
  - [ ] Create Word document templates for different white paper types
  - [ ] Implement automated content generation from similarity data using python-docx
  - [ ] **Implement dynamic percentile-based similarity classification system**
  - [ ] Add career transition opportunity analysis
  - [ ] Generate skill gap assessments and recommendations
  - [ ] Create market context and opportunity scoring

- [ ] **Professional Document Formatting**
  - [ ] Design professional Word templates with NAB-inspired branding
  - [ ] Implement multi-page documents with consistent styling and headers
  - [ ] Add executive summary and detailed analysis sections
  - [ ] Include data visualisations (charts, tables, diagrams) embedded in Word
  - [ ] Create appendices with supporting data

- [ ] **Document Customisation**
  - [ ] Allow customisation of document sections and focus areas
  - [ ] Implement different document types (individual vs team analysis)
  - [ ] Add personalisation options (recipient name, current role)
  - [ ] Create bulk document generation for multiple roles
  - [ ] Allow custom branding and messaging

- [ ] **Output Formats & Distribution**
  - [ ] Generate editable Word documents (.docx) as primary output
  - [ ] Create HTML versions for web viewing and email
  - [ ] Allow users to edit Word documents before converting to PDF
  - [ ] Generate PowerPoint slides for presentations
  - [ ] Add email integration for automatic document distribution

**8.2.7 Documentation & Methodology Transparency** 📋 **PLANNED**
**Branch: `8.2.7-feature/webapp-foundation/documentation`**

> **Strategic Imperative**: *"As a Future Skills strategist, I need complete transparency of methodology and data sources behind every analysis to ensure informed strategic decision-making and accountability."*

- [ ] **Comprehensive Documentation Portal** (`/documentation`)
  - [ ] Complete methodology documentation for all similarity calculations
  - [ ] Data source descriptions and quality assessments  
  - [ ] Algorithm explanations with confidence measures and limitations
  - [ ] System capabilities and recommended usage guidelines
  - [ ] Version history and change logs for full transparency

- [ ] **Universal Info Icon & Tooltip System**
  - [ ] Info icon tooltips on every chart, graph, and data visualization
  - [ ] Hover tooltips explaining calculation methodologies in plain language
  - [ ] Quick methodology summaries for complex strategic analyses
  - [ ] Direct links to detailed documentation sections from tooltips
  - [ ] Data quality and confidence indicators on all outputs

- [ ] **Strategic Decision Support Documentation**
  - [ ] Interpretation guidelines for similarity scores and strategic recommendations
  - [ ] Recommended confidence thresholds for different workforce decisions
  - [ ] Case studies and example strategic applications
  - [ ] Risk assessment frameworks for workforce transitions
  - [ ] Best practices for communicating insights to leadership

- [ ] **Calculation Audit Trails & Transparency**
  - [ ] Detailed logs of all calculation inputs and parameters
  - [ ] Reproducibility documentation for all strategic analyses  
  - [ ] Version tracking for data sources and algorithm changes
  - [ ] Change impact assessments when methodologies evolve
  - [ ] Export capabilities for external validation and review

**8.2.8 Deployment & User Experience** 📋 **PLANNED**
**Branch: `8.2.8-feature/webapp-foundation/deployment`**

- [ ] **Local Deployment System**
  - [ ] Create `.bat` file launcher for seamless Windows deployment
  - [ ] Implement automatic dependency checking and installation
  - [ ] Add data version detection and compatibility checking
  - [ ] Create user-friendly startup and shutdown procedures
  - [ ] Add desktop shortcut creation and browser launching

- [ ] **User Experience Optimisation**
  - [ ] Implement responsive design for tablet and mobile access
  - [ ] Add keyboard shortcuts for power users
  - [ ] Create context-sensitive help and tooltips
  - [ ] Implement progressive loading for large datasets
  - [ ] Add accessibility features (WCAG compliance)

- [ ] **Performance & Reliability**
  - [ ] Optimise database queries for sub-2-second response times
  - [ ] Implement smart caching for frequently accessed data
  - [ ] Add graceful error handling and recovery
  - [ ] Create system health monitoring and diagnostics
  - [ ] Test with full production dataset sizes

- [ ] **Documentation & Training**
  - [ ] Create user guide with screenshots and tutorials
  - [ ] Write technical documentation for maintenance
  - [ ] Develop video tutorials for key workflows
  - [ ] Create troubleshooting guide for common issues
  - [ ] Add in-app onboarding and feature discovery

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