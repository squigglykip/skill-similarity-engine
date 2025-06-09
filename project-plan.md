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

**8.1.1 Enhanced Data Pipeline**
- [ ] Expand CLI to ingest full job architecture (including job families)
- [ ] Integrate complete skills taxonomy with hierarchical relationships
- [ ] Include full SAP/HRIS data for comprehensive role information
- [ ] Create rich metadata for enhanced query capabilities

**8.1.2 Flask Application Setup**
- [ ] Flask application setup and project structure
- [ ] .bat file launcher for seamless user deployment
- [ ] Configuration management for webapp settings
- [ ] Data loading pipeline for all pre-computed datasets
- [ ] Basic routing structure and API endpoints
- [ ] Error handling and logging for web requests
- [ ] Local development environment setup

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