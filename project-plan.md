# Skill Similarity Engine - Project Plan

## Overview

This document outlines the development plan for the NAB Skill Similarity Engine, a system designed to analyse skill similarities between jobs and employees to identify reskilling opportunities. The project will be implemented in phases, with each phase corresponding to a specific git branch.

> **IMPLEMENTATION FOCUS**: Based on current organisational data constraints, the primary focus is on **Job-to-Job Similarity Analysis**. Our implementation concentrates on generating high-quality job similarity matrices and related outputs optimised for Power BI integration. Employee-to-job and employee-to-employee analyses are deprioritised until individual skill data becomes available. This approach aligns with the "Prescribe Skills" paradigm where job definitions drive skill assignments.

> **PRIMARY OUTPUT OBJECTIVE**: The core deliverable of this system is a comprehensive **cross-department job similarity dataset in tabular format** optimised for Power BI integration. This tabular output (structured as a fact table with job1, job2, and similarity metrics) serves as the foundation for all downstream analytics. While the system is capable of generating additional outputs (heatmaps, visualisations, etc.), these are considered secondary features that complement, but do not replace, the primary tabular dataset.

## Project Status Index

| Phase | Description | Status | Branch |
|-------|-------------|--------|--------|
| 1 | Core Framework | **COMPLETED** | `feature/core-framework` |
| 2 | Similarity Engine | **COMPLETED** | `feature/similarity-engine` |
| 3 | Gap Analysis | **COMPLETED** | `feature/gap-analysis` |
| 4 | Reporting & Visualisation | **COMPLETED** | `feature/reporting-visualization` |
| 5 | CLI & Testing | **IN PROGRESS** | `feature/cli-testing` |
| 6 | POC Integration | **PLANNED** | `feature/poc-integration` |
| 7 | Data Pipeline & Integration | **IN PROGRESS** | `feature/data-pipeline` |
| 8 | CLI Implementation & Production Readiness | **PLANNED** | `feature/cli-production-readiness` |

### Key Components Status

| Component | Status | Notes |
|-----------|--------|-------|
| Command Line Interface | **COMPLETED** | Basic functionality implemented |
| Memory Management | **PLANNED** | Critical for large datasets (35,000+ jobs) |
| Job Context & Metadata | **PLANNED** | Enhanced job identification system |
| Configuration System | **COMPLETED** | Comprehensive YAML-based configuration |
| Similarity Calculation | **COMPLETED** | Basic implementation; enhancements planned |
| TF-IDF & Skill Processing | **PLANNED** | Improvements for multi-word skills |
| Seniority Implementation | **COMPLETED** | Pay Scale Area-adjusted similarity |
| Role Track Implementation | **COMPLETED** | IC vs. Leadership path handling |
| Location Implementation | **IN PROGRESS** | Geographic proximity for job transitions |
| Power BI Integration | **PLANNED** | Optimized data exports for visualization |
| Cross-Department Similarity Export | **COMPLETED** | Primary tabular output for Power BI |
| Department Visualisations | **SECONDARY** | Additional visual outputs as complementary features |

## Development Branches

We will use the following branch structure:
- `main` - Production-ready code
- `develop` - Integration branch for feature branches
- Feature branches - Named according to the feature being implemented

## Completed Phases

### Phase 1: Core Framework - **COMPLETED**
**Branch: `feature/core-framework`**

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
**Branch: `feature/similarity-engine`**

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
**Branch: `feature/gap-analysis`**

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
**Branch: `feature/reporting-visualization`**

#### 4.1 Basic Reporting
- [x] Implement DataFrame export functionality
- [x] Add CSV export capabilities
- [x] Add JSON export capabilities
- [x] Implement report configuration options

#### 4.2 Primary Output: Tabular Job Similarity Data
- [x] Design standardised fact table format for job similarity data
- [x] Implement cross-department similarity export
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

### Phase 5: CLI & Testing - **IN PROGRESS**
**Branch: `feature/cli-testing`**

#### 5.1 Command Line Interface - **COMPLETED**
- [x] Create CLI framework in `scripts/`
- [x] Implement commands for most important functionalities:
  - [x] Data loading and transformation
  - [x] Similarity calculation
  - [x] Gap analysis 
  - [x] Generating reports and exports
- [x] Add configuration options via CLI
- [x] Create comprehensive help documentation

#### 5.2 Testing Strategy

> **Testing Approach**: Given the scale and complexity of the data this system handles (47,000 employees, 35,000 jobs, 35,000 skills), we adopt a pragmatic testing approach focusing on the Job-to-Job Similarity Analysis functionality. We follow a staged deployment pipeline with quality gates between environments (Development → Testing → Staging → Production).

##### 5.2.1 Completed Testing
- [x] Test CLI scripts with sample data
- [x] Verify data loading and validation
- [x] Test similarity calculations with small datasets
- [x] Test export functionality and file generation
- [x] Validate job similarity scores against manually calculated examples
- [x] Test filtering of job similarity results by department/job family
- [x] Verify opportunity flags are correctly applied to job pairs
- [x] Test end-to-end workflows with realistic data volumes
- [x] Verify department filtering functionality
- [x] Test configuration overrides and custom settings
- [x] Validate CSV export format standards for Power BI integration
- [x] Test performance with realistic job volumes (35,000+ jobs)
- [x] Validate memory usage during large-scale similarity calculations
- [x] Test Pay Scale Area-adjusted similarity calculations
- [x] Test with jobs having extremely sparse or dense skill sets
- [x] Validate behavior with unusual skill taxonomy structures
- [x] Test handling of jobs with missing or incomplete data
- [x] Create deployment documentation
- [x] Set up basic logging for critical operations
- [x] Document configuration settings for production environment

##### 5.2.2 Priority Testing Tasks
- [x] Test incremental updates to job architecture data
- [x] Test refresh cycles with incremental job updates
- [x] Document integration patterns for future reference
- [x] Complete remaining unit tests for models and data components
- [x] Create test workflows for the full job-to-job similarity pipeline
- [x] Implement tests for validating input data quality
- [x] Create tests for verifying output data consistency
- [x] Add tests for error handling with malformed input data

##### 5.2.3 Testing Infrastructure - Future Development
- [ ] Set up automated test runs as part of continuous integration
- [ ] Implement code coverage reporting
- [ ] Add linting checks to enforce code quality standards
- [ ] Set up dedicated testing environment with larger datasets
- [ ] Implement automated test pipelines for all test categories
- [ ] Configure staging environment mirroring production
- [ ] Create validation workflow with domain experts
- [ ] Implement user acceptance testing process
- [ ] Define code coverage targets (aim for >80% for core functionality)
- [ ] Create data quality validation framework

#### 5.3 Documentation & Examples - **COMPLETED**
- [x] Complete all docstrings and type annotations
- [x] Update README with comprehensive usage instructions
- [x] Create Jupyter notebook examples
- [x] Create sample configuration templates for different use cases

### Phase 6: POC Integration - **PLANNED**
**Branch: `feature/poc-integration` (Parent branch for integration of all POC components)**

> **Focus**: This phase incorporates learnings and improvements from the Proof of Concept (POC) implementation back into the modular source code structure. The POC demonstrated significant performance enhancements, memory optimisations, and improved handling of skill similarity calculations at scale (35,000+ jobs). Key to this integration is preserving the primary functionality of generating a cross-department similarity dataset while enhancing performance and maintainability.

#### 6.1 Memory Management Enhancements
**Branch: `feature/poc-memory-management`**
- [ ] Create memory tracking utilities in `utils/performance.py`
  - [ ] Implement memory usage reporting
  - [ ] Add large object management
  - [ ] Create garbage collection helpers
  - [ ] Add context managers for performance sections
- [ ] Enhance base classes with memory-efficient options
  - [ ] Add `memory_efficient` flag to core classes
  - [ ] Implement memory-conscious data structures
  - [ ] Add explicit cleanup methods
- [ ] Add progress tracking for memory consumption
  - [ ] Integrate with logging system
  - [ ] Create memory usage dashboards

#### 6.2 Performance Optimisation
**Branch: `feature/poc-performance-optimization`**
- [ ] Create multi-processing framework in `utils/parallel.py`
  - [ ] Implement process pool management
  - [ ] Add task distribution helpers
  - [ ] Create error handling for distributed tasks
  - [ ] Implement result aggregation utilities
- [ ] Implement chunked and batched processing utilities
  - [ ] Create data chunking utilities
  - [ ] Add batched processing
  - [ ] Implement automatic batch size optimisation
  - [ ] Add resumable processing capabilities
- [ ] Add progress bars for long-running operations
  - [ ] Standardise tqdm integration
  - [ ] Add custom progress reporting

#### 6.3 TF-IDF and Skill Processing Improvements
**Branch: `feature/poc-skill-processing`**
- [ ] Enhance TF-IDF vectoriser in `similarity/cosine.py`
  - [ ] Add preprocessing for multi-word skills (spaces to underscores)
  - [ ] Implement token preservation for skill phrases
  - [ ] Create configuration options for tokenisation strategies
- [ ] Implement skill name mapping system
  - [ ] Add bidirectional mapping between original and transformed names
  - [ ] Ensure consistency in all outputs
  - [ ] Create utility methods for conversion
- [ ] Update skill taxonomy handling
  - [ ] Add validation for skill uniqueness post-transformation
  - [ ] Implement improved normalisation in SkillTaxonomyLoader
  - [ ] Add configurability for normalisation strategies

#### 6.4 Configuration Transparency System
**Branch: `feature/poc-configuration-transparency`**
- [ ] Create configuration tracking framework in `config/tracking.py`
  - [ ] Implement configuration versioning
  - [ ] Create serialisation of active configuration
  - [ ] Add configuration context management
  - [ ] Implement configuration diffing capabilities
- [ ] Develop configuration embedding mechanism
  - [ ] Create metadata enrichment for output data frames
  - [ ] Implement factor contribution analysis
  - [ ] Add configuration impact calculation
  - [ ] Build configuration documentation generator
- [ ] Implement configuration scenario management
  - [ ] Add scenario definition capabilities
  - [ ] Create scenario comparison reports
  - [ ] Implement run history tracking
  - [ ] Build configuration validation engine

#### 6.5 Core Data Loading Enhancements
**Branch: `feature/poc-data-loading`**
- [ ] Update `SkillTaxonomyLoader` class
  - [ ] Add chunked loading support
  - [ ] Implement memory-efficient processing
  - [ ] Enhance validation for HRIS formats
- [ ] Update `JobArchitectureLoader` class
  - [ ] Add chunked loading support
  - [ ] Implement unique job ID creation
  - [ ] Add flexible column mapping
- [ ] Create utility for data validation and error reporting
  - [ ] Implement comprehensive validation rules
  - [ ] Add detailed error reporting
  - [ ] Create data quality metrics

#### 6.6 Job Context and Metadata Handling
**Branch: `feature/poc-job-context`**
- [ ] Enhance `Job` model in `models/jobs.py`
  - [ ] Add rich contextual metadata support
  - [ ] Implement organisation unit information
  - [ ] Add salary group and people leader flag as standard attributes
  - [ ] Support location-based data
  - [ ] Add standardised attribute sanitisation
- [ ] Implement robust job identifier system
  - [ ] Create a `generate_unique_id()` method that produces a composite key
  - [ ] Include all differentiating factors in composite key (job_id, org_unit, location, seniority, role_track)
  - [ ] Implement sanitisation of key components for consistent formatting
  - [ ] Add storage of original "simple" job ID alongside composite ID
  - [ ] Create documentation of composite key structure and components
- [ ] Develop context-aware utilities
  - [ ] Implement job filtering by any context dimension
  - [ ] Create grouping and aggregation helpers for multi-dimensional analysis
  - [ ] Add duplicate context detection and handling
  - [ ] Add utility methods to extract business context from composite IDs

#### 6.7 Similarity Calculation Enhancements
**Branch: `feature/poc-similarity-enhancements`**
- [ ] Enhance `CosineSimilarityCalculator`
  - [ ] Add parallel processing support
  - [ ] Implement batched processing
  - [ ] Optimise vector computation
- [ ] Add department filtering capability
  - [ ] Pre-filtering for better performance
  - [ ] Optimised subset processing
- [ ] Implement memory-efficient similarity matrix generation
  - [ ] Add sparse matrix support
  - [ ] Create incremental matrix building
  - [ ] Add memory-mapped storage for large matrices
- [ ] Add similarity enhancement factor tracking
  - [ ] Track which factors influenced each similarity score
  - [ ] Record threshold application effects
  - [ ] Add configuration parameterisation to similarity scores
  - [ ] Create factor breakdown views

#### 6.8 Advanced Optimisation Strategies
**Branch: `feature/poc-advanced-optimization`**
- [ ] Implement sparse matrix support
  - [ ] Integrate scipy.sparse or similar libraries
  - [ ] Add compression options for large datasets
  - [ ] Create memory-efficient matrix operations
- [ ] Develop IDF precomputation system
  - [ ] Implement caching for IDF values
  - [ ] Add cache update mechanisms
  - [ ] Create configuration for calculation strategies
- [ ] Create advanced filtering framework
  - [ ] Implement pre-filtering by multiple dimensions
  - [ ] Develop filter pipeline architecture
  - [ ] Add similarity threshold filters for early stopping
- [ ] Build incremental processing system
  - [ ] Support for segmented matrix generation
  - [ ] Add resumable calculation capabilities
  - [ ] Implement result merging for distributed processing

#### 6.9 Pre-processing Implementation
**Branch: `feature/poc-preprocessing`**
- [ ] Create vectorisation system in `preprocessing/vectorisation.py`
  - [ ] Implement one-time corpus vectorisation
  - [ ] Add vector storage and retrieval
  - [ ] Create memory-efficient vector management
- [ ] Develop vector management utilities
  - [ ] Implement efficient vector storage format
  - [ ] Add partial loading capabilities
  - [ ] Create vector versioning system
- [ ] Build context-aware analysis framework
  - [ ] Implement holistic comparison support
  - [ ] Add department-specific analysis
  - [ ] Create efficient vector filtering
- [ ] Add vector update mechanisms
  - [ ] Implement incremental updates
  - [ ] Add batch update support
  - [ ] Create version control for vectors

#### 6.10 Focused Data Export and Insight-Driven Visualisation
**Branch: `feature/poc-exports`**
- [ ] Create Power BI optimised exporters in `visualization/power_bi.py`
  - [ ] Implement standardised tabular "fact table" format for comprehensive data
  - [ ] Add relationship-friendly data structures
  - [ ] Create metadata generation
  - [ ] Implement configuration factor inclusion in exports
- [ ] Implement departmental batching for exports
  - [ ] Add configurable batch sizes
  - [ ] Create memory-efficient batch processing
  - [ ] Add resume capability for interrupted exports
- [ ] Add statistics generation utilities
  - [ ] Create summary statistics
  - [ ] Implement department-specific metrics
  - [ ] Add opportunity flag generation
  - [ ] Create configuration impact metrics
- [ ] Design focused visualisation approach
  - [ ] Create "highlights" mode showing only most significant findings
  - [ ] Implement significance thresholds to limit output volume
  - [ ] Develop aggregated visualisation methods to replace unit-by-unit comparisons
  - [ ] Create executive summary visualisations for key insights
- [ ] Enhance cross-department similarity exports
  - [ ] Optimize the primary tabular output format
  - [ ] Add configurable options for controlling the level of detail
  - [ ] Create efficient processing for full cross-department comparisons
  - [ ] Implement memory-efficient design for large job datasets

#### 6.11 High Performance Computing Strategy
**Branch: `feature/poc-high-performance`**
- [ ] Implement vector preprocessing pipeline
  - [ ] Create preprocessing workflow for raw input data
  - [ ] Develop optimised vector storage formats
  - [ ] Add incremental update capability for new/changed data
- [ ] Create matrix computation framework
  - [ ] Implement chunked processing for full matrix calculation
  - [ ] Add within-department prioritisation logic
  - [ ] Create checkpoint saving and resumability
  - [ ] Implement sparse matrix storage for efficient representation
- [ ] Add performance acceleration components
  - [ ] Implement Numba-accelerated similarity functions
  - [ ] Add symmetry optimisations (compute half the matrix)
  - [ ] Create early termination for low-similarity pairs
  - [ ] Implement smart chunking strategies
- [ ] Develop hybrid computation system
  - [ ] Implement combined precomputed/on-demand calculation
  - [ ] Add caching for frequently accessed results
  - [ ] Create background processing for low-priority calculations

#### 6.12 Error Handling and Logging Improvements
**Branch: `feature/poc-error-handling`**
- [ ] Create centralised logging framework
  - [ ] Add configurable log levels
  - [ ] Implement file and console logging
  - [ ] Add structured logging support
- [ ] Implement enhanced error handling
  - [ ] Create contextual error messages
  - [ ] Add error categorisation
  - [ ] Implement recovery mechanisms
- [ ] Add data validation reporting
  - [ ] Create validation summary reports
  - [ ] Implement data quality metrics
  - [ ] Add warning thresholds

#### 6.13 CLI Enhancements
**Branch: `feature/poc-cli-enhancements`**
- [ ] Update CLI with new options
  - [ ] Add performance tuning parameters
  - [ ] Implement memory optimisation flags
  - [ ] Create output format selection
  - [ ] Add configuration scenario options
- [ ] Add filtering capabilities
  - [ ] Implement department filtering
  - [ ] Add job level filtering
  - [ ] Create custom filter expressions
- [ ] Enhance help documentation
  - [ ] Add comprehensive option descriptions
  - [ ] Create usage examples
  - [ ] Implement configuration templates
  - [ ] Add troubleshooting section

#### 6.14 Implementation Plan

The POC integration will be structured as a 4-sprint project, with a total timeline of 8 weeks:

- **Sprint 1 (Weeks 1-2):** Foundation Improvements
  - Memory Management
  - TF-IDF and Skill Processing
  - Configuration Transparency
  - Performance Optimisation  
  - Core Data Loading
  
- **Sprint 2 (Weeks 3-4):** Job Metadata and Similarity Enhancements
  - Job Context and Metadata
  - Similarity Calculation
  - HRIS Specific Adaptations

- **Sprint 3 (Weeks 5-6):** Advanced Optimisation and Reporting
  - Advanced Optimisation Strategies
  - Pre-processing Implementation
  - Focused Data Export and Visualisation
  - Error Handling and Logging

- **Sprint 4 (Weeks 7-8):** User Interface and Testing
  - CLI Enhancements
  - Integration Testing
  - Documentation Updates
  - Final Integration and Validation

##### Dependencies and Risks
- Access to real-world HRIS data for testing
- Stakeholder availability for UAT
- Sufficient computational resources for large-scale testing
- Access to representative multi-word skill samples
- Sample configuration scenarios for testing transparency features

##### Success Criteria
1. Integrated source code performs as well as or better than the POC implementation
2. Memory usage is optimised for large datasets (35,000+ jobs)
3. Processing time is improved through parallel execution
4. Multi-word skills are correctly handled in similarity calculations
5. Job context information is properly captured and utilised
6. Configuration transparency enables tracking how factors affect each similarity score
7. Multiple similarity calculation scenarios can be run and compared
8. Documentation is updated to reflect all changes
9. Command line interface provides all functionality from the POC
10. Visualisation outputs are focused on key insights rather than overwhelming with exhaustive outputs

### Phase 7: Data Pipeline & Integration - **IN PROGRESS**
**Branch: `feature/data-pipeline`**

#### 7.1 Data Export Optimisation - **COMPLETED**
- [x] Create standardised data export formats
- [x] Implement efficient data serialisation
- [x] Add metadata and schema descriptions in exports
- [x] Ensure exports are optimised for downstream consumption
- [x] Validate CSV formats meet Power BI integration requirements
- [x] Optimize cross-department similarity exports (primary output)
- [x] Ensure department-specific exports are available as needed (secondary outputs)

#### 7.2 Configuration Management System - **COMPLETED**
- [x] Design comprehensive configuration schema for all configurable parameters
- [x] Implement YAML-based configuration with hierarchical structure
- [x] Move hardcoded thresholds, weights, and flags to configuration
- [x] Create configuration validation and error reporting
- [x] Add CLI support for configuration management
- [x] Develop sample configuration files for different use cases
- [x] Update components to use centralised configuration
- [x] Implement version control for configurations
- [x] Support environment-specific settings (dev, test, production)
- [x] Create user-specific overrides
- [x] Implement configuration categories:
  - [x] Similarity thresholds for opportunity identification
  - [x] Skill importance weightings by category
  - [x] Visualisation preferences and colour schemes
  - [x] Export format specifications
  - [x] Performance tuning parameters
- [x] Add configuration override capabilities via CLI arguments
- [x] Create user-friendly documentation for all configuration options

The configuration system now features:
- A well-structured `config.yaml` file with clear sections and comments
- Type-safe dataclasses for strongly-typed configuration handling
- Proper validation of configuration values with helpful error messages
- Comprehensive settings for all system modules (normalisation, similarity, gap analysis, reporting, visualisation)
- Logging configuration with customisable outputs
- Team analysis and workforce planning parameters
- Extension points for future features like seniority and location weighting

#### 7.3 Skill Affinity Analyzer Enhancement - **COMPLETED**
**Branch: `feature/similarity-enhancements`**

> **Enhancement Focus**: Implement additional variables beyond skills that affect job similarity: seniority, role track (IC vs. Leadership), and location. These enhancements will provide more nuanced similarity calculations for improved job matching and career pathway recommendations.

##### 7.3.1 Enhanced Configuration System - **COMPLETED**
- [x] Implement variable weight configuration system
- [x] Support toggling variables on/off via weight settings (0 = disabled)
- [x] Implement basic versioning to track configuration changes
- [x] Create extensible structure for future variables
- [x] Add validation for configuration options
- [x] Design for backward compatibility with existing configurations

The configuration now includes a `future_extensions` section that allows for easy activation of new similarity variables:

```yaml
# Future extensions (all disabled by default)
future_extensions:
  seniority_weight: 0.0
  role_track_weight: 0.0
  location_weight: 0.0
```

These variables can be toggled on by setting their weights to non-zero values, providing a smooth path for gradually introducing new features.

##### 7.3.2 Project Rationale and Benefits

The inclusion of these additional variables goes beyond a simplistic skills-only approach to job similarity calculations, delivering several key benefits:

1. **More Realistic Career Pathways**: By factoring in seniority levels, we can avoid suggesting unrealistic jumps from junior to senior positions, creating more achievable career progression options.

2. **Role-Appropriate Transitions**: Distinguishing between Individual Contributor (IC) and Leadership roles allows identification of natural progression paths (IC → Senior IC → Leadership) while avoiding less common regressions (Leadership → IC).

3. **Geographic Practicality**: By considering location in similarity scores, we can prioritize transitions that don't require relocation, making recommendations more practical for employees.

4. **Flexible Implementation**: The weighted approach allows organizations to tune the importance of each variable based on their specific needs and priorities.

5. **Incremental Adoption**: Variables can be initially disabled (weight=0) and gradually introduced as the organization becomes comfortable with the enhanced model.

##### 7.3.3 Test-Driven Development Approach
- [ ] Create comprehensive test framework for each new variable
  - [ ] Develop test fixtures with representative role data containing seniority, track, and location information
  - [ ] Design test cases that cover standard scenarios, edge cases, and boundary conditions
  - [ ] Create tests that verify variable toggling through weight configuration
  - [ ] Implement CI-ready test commands and fixtures
  - [ ] Set up test coverage monitoring for new code

Testing will follow a multi-layer approach:
1. **Unit tests** to verify individual variable calculation correctness
2. **Integration tests** to validate interactions between variables
3. **Functional tests** using realistic data scenarios to ensure overall behavior matches expectations

This test-driven approach will ensure high quality and reliability while facilitating future maintenance.

##### 7.3.4 Seniority Implementation - **COMPLETED**
- [x] Enhance job data model to include standardised seniority information
  - [x] Define a formal seniority level schema (Junior, Mid-level, Senior, Lead, etc.)
  - [x] Create normalisation utilities to map organisation-specific levels to standard scale
  - [x] Implement migration tools to enrich existing data
- [x] Design seniority comparison algorithm
  - [x] Implement level "distance" calculation (e.g., Junior → Senior = 2 levels)
  - [x] Create weighted scoring that prioritizes level-by-level progression
  - [x] Develop configurable penalties for skipping multiple levels
  - [x] Create seniority similarity score in range [0.0-1.0]
- [x] Implement nuanced career progression model
  - [x] Same level matches receive highest similarity (configurable, default 1.0)
  - [x] One step up career progression receives high similarity (configurable, default 0.7)
  - [x] Multiple steps up receive decreasing similarity based on configurable step penalty
  - [x] Steps down receive severe penalties to discourage demotions
  - [x] Multiple steps down receive near-zero similarity to eliminate from recommendations
- [x] Move all seniority similarity thresholds to configuration system
  - [x] Make career progression parameters fully configurable
  - [x] Document all configurable parameters with clear descriptions
- [x] Implement comprehensive test suite
  - [x] Test progression calculations (adjacent levels, skipped levels)
  - [x] Test handling of missing seniority information
  - [x] Test sensitivity to weight configuration

The seniority implementation now recognizes that career progression typically occurs in incremental steps, with moves between adjacent levels more common and realistic than skipping multiple levels. By incorporating this domain knowledge through configurable thresholds, we provide more practical career progression suggestions while heavily discouraging unrealistic demotions.

##### 7.3.5 Role Track Implementation - **COMPLETED**
- [x] Extend job data model to include role track categorisation
  - [x] Create enumeration for track types (IC, Leadership)
  - [x] Define subcategories within tracks (e.g., Leadership: Team Lead, Manager, Director, etc.)
  - [x] Develop data schema for track information
- [x] Design track comparison algorithm
  - [x] Implement different scoring for IC→IC, Leadership→Leadership, IC→Leadership, and Leadership→IC transitions
  - [x] Create configurable preference weighting for "natural progressions" (IC→Leadership)
  - [x] Add penalties for uncommon regressions (Leadership→IC)
  - [x] Map scores to [0.0-1.0] range for consistency
- [x] Make role track comparison fully configurable
  - [x] Move role track similarity thresholds to configuration system
  - [x] Allow fine-tuning of same-track vs different-track similarities
- [x] Develop unit and integration tests
  - [x] Test transitions within same track
  - [x] Test transitions across tracks
  - [x] Test compatibility with seniority calculations

The role track implementation acknowledges that career progression typically follows patterns where Individual Contributors may progress to Leadership roles, but transitions in the opposite direction are less common. All role track similarity thresholds are now configurable, allowing organisations to adjust the system to their specific career paths and progression policies.

##### 7.3.6 Location Implementation - **IN PROGRESS** (Branch: feature/similiarity-enhancement-location)

###### Overview
The location implementation recognises that geographic proximity significantly affects job transition practicality. Our enhanced approach focuses on "displacement" rather than binary location matching, acknowledging that most employees are unwilling to relocate between cities for internal roles unless for exceptional career opportunities.

###### 7.3.6.1 Location Data Model Enhancement - **COMPLETED**
- [x] Add location attributes to job data model
  - [x] Create flexible schema supporting different location specificity (suburb/city/state/country)
  - [x] Design normalisation for inconsistent address formats

###### 7.3.6.2 Basic Location Similarity - **COMPLETED**
- [x] Implement exact matching for same location
- [x] Make location comparison configurable
  - [x] Move location similarity thresholds to configuration system
  - [x] Allow adjustment of same-location vs different-location similarities

###### 7.3.6.3 Global Geo-Context Implementation - **IN PROGRESS**
- [ ] Develop region-specific address parsing and standardisation
  - [ ] Create utility for standardising street addresses across multiple countries
  - [ ] Implement postcode/ZIP validation for key countries (Australia, India, Vietnam, UK, etc.)
  - [ ] Handle common address abbreviations across different contexts
  - [ ] Support different address formats (e.g., UK, India, Vietnam, Singapore formats)
- [ ] Implement international proximity rules
  - [ ] Define similarity thresholds for cross-country job comparisons
  - [ ] Prioritise domestic relocations over international
  - [ ] Create regional clusters (APAC, Europe, Americas) for similarity scoring
- [ ] Create NAB-specific global location mapping
  - [ ] Map all NAB office locations globally to standardised addresses
  - [ ] Identify primary business hubs across countries (Melbourne, Sydney, London, Bengaluru, etc.)
  - [ ] Categorise international locations by business function and importance

###### 7.3.6.4 Geocoding and Distance Calculation - **IN PROGRESS**
- [ ] Implement geocoding capability
  - [ ] Create address-to-coordinates conversion utility
  - [ ] Handle partial location information (missing street number, etc.)
  - [ ] Implement geocoding service fallback options
  - [ ] Support international address formats and locales
- [ ] Build Haversine distance calculation module
  - [ ] Implement pure Python Haversine formula calculation
  - [ ] Add caching for common location pairs
  - [ ] Create distance matrix generation for batch processing
  - [ ] Handle international dateline and Earth curvature for global distances
- [ ] Develop distance-to-similarity conversion
  - [ ] Create exponential decay function based on commute realities
  - [ ] Implement configurable distance thresholds (e.g., 5km, 10km, 25km)
  - [ ] Tune similarity scores to match practical commute preferences
  - [ ] Add special handling for cross-country distances

###### 7.3.6.5 Commute-Based Similarity Model - **PLANNED**
- [ ] Develop realistic commute-based similarity scoring
  - [ ] Create distance bands with corresponding similarity scores
    - [ ] Same building/campus: 1.0
    - [ ] Walking distance (<2km): 0.9
    - [ ] Short commute (2-10km): 0.7-0.8
    - [ ] Medium commute (10-25km): 0.4-0.6
    - [ ] Long commute (25-50km): 0.2-0.3
    - [ ] Different city/same country: 0.1
    - [ ] Different country/same region: 0.05
    - [ ] Different global region: 0.0
  - [ ] Adjust scores based on public transport accessibility in different cities
  - [ ] Consider typical traffic patterns for major global cities
  - [ ] Account for international relocation practicality by job level

###### 7.3.6.6 Address Validation and Experimentation - **PLANNED**
- [ ] Create test framework for address validation
  - [ ] Implement unit tests with sample addresses from multiple countries
  - [ ] Test address normalisation with variations across different formats
  - [ ] Validate postal code systems across different countries
- [ ] Build experimentation module for Haversine accuracy
  - [ ] Create comparison between Haversine and real-world commute times
  - [ ] Test with known location pairs across different countries
  - [ ] Validate against Google Maps API data for international routes
- [ ] Develop visualization tools for distance-based similarity
  - [ ] Create heatmap visualization of location similarities
  - [ ] Build distance matrix reports for NAB's global locations
  - [ ] Generate CSV exports for Power BI integration with country filters

###### 7.3.6.7 Edge Case Handling - **PLANNED**
- [ ] Implement handling for special location types
  - [ ] Manage "Remote" or "Work from home" locations with country context
  - [ ] Handle multiple work locations across countries (e.g., split time between India and Australia)
  - [ ] Manage temporary assignments, secondments and international rotations
  - [ ] Account for visa/work permit constraints in similarity calculations
- [ ] Create fallback mechanisms for missing location data
  - [ ] Implement city-level matching when street address is unavailable
  - [ ] Use postal code proximity when geocoding fails
  - [ ] Default to country-level comparison for unfamiliar international locations
  - [ ] Handle transliteration issues in non-Latin address formats

###### 7.3.6.8 International Banking Context - **PLANNED**
- [ ] Implement NAB-specific global location considerations
  - [ ] Identify key NAB business hubs and locations across all countries
  - [ ] Create special handling for locations with specific financial services capabilities
  - [ ] Add weightings for global function concentration by location
  - [ ] Recognise regional centres of excellence (e.g., technology in India, trading in London)
- [ ] Develop global business context understanding
  - [ ] Define similarity for roles across international boundaries
  - [ ] Implement special rules for global roles vs regional roles
  - [ ] Create handling for headquarters vs satellite office transitions
  - [ ] Factor in international career path expectations at different career levels
- [ ] Create international mobility context
  - [ ] Develop tiered scoring for roles typically offering international mobility
  - [ ] Adjust similarity based on historical relocation patterns
  - [ ] Map executive and senior leadership roles with higher international mobility expectations

##### 7.3.7 Variable Integration Framework - **COMPLETED**
- [x] Create weighted variable integration system
- [x] Design extensible pattern for adding future variables
- [x] Implement normalized score combination algorithm
- [x] Create comprehensive logging of factor contributions
- [x] Implement adjustment controls
- [x] Create configurable weighting system
- [x] Add minimum threshold options
- [x] Develop variable-specific tuning parameters
- [x] Test combined operation
- [x] Verify correct weighting application
- [x] Test boundary cases (all variables at max/min)
- [x] Validate stability with different weight combinations

This framework provides a flexible, configuration-driven foundation not only for the three immediate variables but also for future extensions, ensuring the system can evolve with organisational needs. All aspects of the similarity calculations are now configurable through the configuration system, allowing for detailed tuning without code changes.

##### 7.3.8 CLI Integration and User Experience
- [ ] Enhance CLI to support new variables
- [ ] Add commands to toggle variables on/off
- [ ] Implement options to adjust weights interactively
- [ ] Create commands to display relative impact of variables
- [ ] Develop visualization enhancements
- [ ] Add visualization of variable contributions to similarity scores
- [ ] Create specialized views for each variable
- [ ] Implement interactive exploration of variable effects
- [ ] Update documentation
- [ ] Create comprehensive guide to variable configuration
- [ ] Document expected effects of each variable
- [ ] Provide example configurations for different use cases

User-friendly tools will make these complex enhancements accessible to business users, enabling them to explore and optimize the similarity model for their organization's specific needs.

##### 7.3.9 Integration Tests & Documentation - **COMPLETED**
- [x] Test combined operation of all three variables
- [x] Create comprehensive test scenarios
- [x] Develop test data with complete variable coverage
- [x] Implement performance testing for enhanced calculations
- [x] Update documentation
- [x] Create detailed reference for each variable
- [x] Document integration patterns and best practices
- [x] Provide configuration templates for common scenarios
- [x] Develop validation framework
- [x] Create tools to measure improvement in similarity accuracy
- [x] Implement A/B comparison with skills-only approach
- [x] Design metrics for evaluating enhancement impacts

##### 7.3.10 Enhanced Configuration Structure - **COMPLETED**
- [x] Redesign configuration file structure with clear sections and comprehensive documentation
- [x] Implement structured headings with descriptive separators
- [x] Add detailed explanations for each configuration parameter
- [x] Group related parameters into logical sections
- [x] Enhance configuration documentation
- [x] Add detailed parameter descriptions and rationale
- [x] Include example values and valid ranges
- [x] Provide real-world impact explanations for different settings
- [x] Improve YAML readability and maintainability
- [x] Use consistent formatting and indentation
- [x] Implement clear separation between configuration sections
- [x] Add comprehensive comments explaining parameter purposes
- [x] Create versioning system for tracking configuration changes
- [x] Add explicit configuration version identifiers
- [x] Document backward compatibility considerations
- [x] Create upgrade path for existing configurations

The enhancement to the configuration structure has delivered several benefits:
1. **Improved readability** - Clear section headers and descriptive comments make the configuration easier to understand
2. **Better documentation** - Each parameter now has detailed explanations of its purpose and impact
3. **More maintainable** - Logical grouping and consistent formatting make updates simpler
4. **Self-explanatory** - New users can understand the configuration without extensive external documentation
5. **Future-proof** - The structure allows for easy addition of new parameters and sections

#### 7.4 HRIS Data Integration
- [x] Develop HRIS data translation layer to standardise naming conventions
- [x] Create mapping dictionaries between HRIS job codes and internal architecture
- [x] Implement field normalisation for inconsistent data formats
- [x] Build data validation to catch anomalies in HRIS exports
- [x] Create detailed documentation of all HRIS-to-internal mappings
- [x] Develop incremental update workflow for job architecture changes
- [x] Implement configurable refresh schedules for HRIS data synchronisation
- [x] Design error handling and notification process for translation failures
- [x] Implement mapping from raw HRIS data to the required skills structure
- [x] Focus on scalability for large dataset processing

##### 7.4.1 Schema Separation Strategy - **COMPLETED**
- [x] Review and finalize the HRIS schema mapping configuration
  - [x] Ensure the configuration file (`hris_schema_mapping.yaml`) is complete and accurate
  - [x] Document each mapping field with examples and rationale
  - [x] Validate all value mappings (salary groups, role tracks, etc.)
  - [x] Create configuration templates for different HRIS systems
- [x] Create comprehensive unit tests for HRIS adapter components
  - [x] Test `HRISConfigLoader` with different configuration scenarios
  - [x] Test `HRISTransformer` with sample HRIS data
  - [x] Test `HRISWorkflow` integration with the engine's components
  - [x] Test end-to-end transformation pipeline with realistic data
  - [x] Validate output data against expected schema
- [x] Verify schema isolation within the engine
  - [x] Ensure all core engine components use internal schema only
  - [x] Confirm that transformation is complete before data reaches engine
  - [x] Add validation checks for schema compliance at engine boundaries
  - [x] Create clear error messages for schema inconsistencies
- [x] Implement integration testing workflow
  - [x] Run unit tests for HRIS adapter components (`pytest tests/unit/hris_adapter`)
  - [x] Run end-to-end tests with sample HRIS data sets
  - [x] Validate output formats and compatibility
  - [x] Create regression tests to prevent schema leakage

##### 7.4.2 Data Validation Framework - **COMPLETED**
- [x] Design validation rules for HRIS data transformation
  - [x] Implement field type validation (string, numeric, dates)
  - [x] Create format validation for standard fields (email, IDs, codes)
  - [x] Build range validation for numeric fields (salary bands, levels)
  - [x] Implement cross-field validation for logical constraints
- [x] Develop validation reporting
  - [x] Create detailed validation error reports with row numbers and values
  - [x] Implement warning levels for non-critical issues
  - [x] Design flexible validation thresholds (strict vs. permissive modes)
  - [x] Create suggestions for fixing common validation issues
- [x] Build data quality metrics
  - [x] Implement completeness checking (% of fields populated)
  - [x] Create consistency validation across related fields
  - [x] Design domain checking for categorical fields
  - [x] Implement referential integrity checking for related data

This approach ensures a clean separation between external (HRIS) data formats and internal engine schemas, making the system more maintainable and adaptable to different HRIS systems while preserving the stability of core engine functionality.

#### 7.5 Power BI Integration
- [ ] Finalise data schema documentation for Power BI developers
- [ ] Create reference relationship models for Power BI implementation
- [ ] Develop sample DAX measures for common analyses
- [ ] Document refresh and update procedures
- [ ] Create user guide for working with exported data in Power BI
- [ ] Define fact table relationships and hierarchies
- [ ] Create standardized calculated measures for similarity analysis
- [ ] Develop templated visualizations for common job similarity views
- [ ] Document best practices for filtering and slicing the similarity data
- [ ] Implement performance optimizations for large similarity datasets

#### 7.6 Output Delivery Strategy
- [ ] Define clear primary and secondary output priorities
  - [ ] Document the cross-department similarity CSV as the primary output
  - [ ] Categorize other outputs (heatmaps, visualizations) as secondary features
  - [ ] Create configuration options for enabling/disabling secondary outputs
  - [ ] Implement memory-efficient processing when only primary output is needed
- [ ] Design CLI flags for output selection
  - [ ] Add `--primary-only` flag to generate only the cross-department tabular data
  - [ ] Create `--visualizations` flag to explicitly request secondary outputs
  - [ ] Implement `--report-type` option for selecting specific output formats
  - [ ] Add documentation for all output control options
- [ ] Develop output delivery documentation
  - [ ] Create clear workflow diagrams showing primary and secondary outputs
  - [ ] Document recommended usage patterns for different scenarios
  - [ ] Provide examples of integrating outputs with downstream systems
  - [ ] Create troubleshooting guide for common output issues

#### 7.7 Real-World Data Testing
- [ ] Perform complete end-to-end testing with real HRIS data
- [ ] Create validation reports comparing outputs with expected results
- [ ] Validate memory usage and performance with full-scale data
- [ ] Conduct usability testing with intended end users
- [ ] Gather feedback and implement necessary refinements
- [ ] Document any remaining data quality issues or constraints
- [ ] Finalise implementation recommendations based on testing results

### Phase 8: CLI Implementation & Production Readiness - **PLANNED**
**Branch: `feature/cli-production-readiness`**

#### 8.1 Core CLI Framework Enhancements - **PLANNED**
- [ ] Expand current CLI functionality
  - [ ] Ensure consistent interface across all commands
  - [ ] Add comprehensive error handling and user feedback
  - [ ] Implement progress tracking for long-running operations
  - [ ] Add logging with configurable verbosity levels
  - [ ] Create unified entry point for all operations
- [ ] Create "quick start" convenience commands
  - [ ] Implement shortcuts for common operation combinations
  - [ ] Add preset configuration profiles for different analysis types
  - [ ] Create wizards for first-time users to generate configurations
- [ ] Implement clear output control options
  - [ ] Add flags for controlling primary vs. secondary outputs
  - [ ] Create options for output directory and naming conventions
  - [ ] Implement batch processing for multiple departments
  - [ ] Add memory optimization flags for large datasets

#### 8.2 Local Production Usage Preparation - **PLANNED**
- [ ] Create workspace structure for NAB local usage
  - [ ] Design standard directory structure for inputs and outputs
  - [ ] Develop workspace initialization and validation commands
  - [ ] Create templates for NAB-specific data formats
  - [ ] Build safeguards to prevent accidental data corruption
- [ ] Implement batch processing for large NAB datasets
  - [ ] Add incremental processing capability for large job datasets
  - [ ] Create checkpointing for long-running analyses
  - [ ] Implement memory-efficient processing for constrained environments
  - [ ] Add retry mechanisms for handling transient failures
- [ ] Design Windows-specific deployment considerations
  - [ ] Create batch files (.bat) for common operations
  - [ ] Implement Windows-friendly path handling
  - [ ] Add Windows Task Scheduler templates for regular execution
  - [ ] Ensure compatibility with corporate Windows security policies

#### 8.3 Data Workflow Integration - **PLANNED**
- [ ] Develop data input/output pipeline
  - [ ] Create standardized input data validators
  - [ ] Add support for Excel files (common in NAB business environment)
  - [ ] Implement CSV with headers format for Power BI compatibility
  - [ ] Add data transformation utilities for various NAB input formats
- [ ] Build Power BI integration utilities
  - [ ] Create output formats optimized for Power BI consumption
  - [ ] Develop Power BI templates for common visualizations
  - [ ] Add metadata to outputs for improved Power BI discoverability
  - [ ] Create refresh sequence documentation for Power BI datasets
- [ ] Design data versioning and archiving system
  - [ ] Implement output naming conventions with timestamps
  - [ ] Create utilities for comparing results across multiple runs
  - [ ] Add automated archiving of previous analysis results
  - [ ] Build data provenance tracking to maintain audit trail

#### 8.4 Ad-hoc Analysis Toolkit - **PLANNED**
- [ ] Create specialized commands for one-off analyses
  - [ ] Implement targeted department analysis
  - [ ] Add job family comparison tools
  - [ ] Build role progression path analysis
  - [ ] Develop skill gap identification for targeted roles
- [ ] Develop analysis customization options
  - [ ] Add runtime parameter overrides for quick experimentation
  - [ ] Create temporary configuration modification commands
  - [ ] Implement "what-if" simulation capabilities
  - [ ] Build comparison mode between different parameter sets
- [ ] Implement ad-hoc reporting
  - [ ] Create executive summary generation for key findings
  - [ ] Add visualization generation for common metrics
  - [ ] Build export to presentation formats (e.g., PowerPoint)
  - [ ] Implement customizable report templates

#### 8.5 User Experience & Documentation - **PLANNED**
- [ ] Enhance user feedback and assistance
  - [ ] Create comprehensive inline help for all commands
  - [ ] Add contextual hints for common errors
  - [ ] Implement interactive examples for first-time users
  - [ ] Build configuration validation with helpful error messages
- [ ] Develop comprehensive user documentation
  - [ ] Create step-by-step workflow guides for common NAB use cases
  - [ ] Add troubleshooting section with solutions to common issues
  - [ ] Develop reference documentation for all parameters
  - [ ] Build documentation for output file formats
- [ ] Create NAB-specific usage guides
  - [ ] Document recommended practices for NAB environment
  - [ ] Add examples using realistic NAB data patterns (anonymized)
  - [ ] Create departmental guides for different NAB business units
  - [ ] Build integration guides for NAB's existing analytics tools

#### 8.6 Testing & Quality Assurance - **PLANNED**
- [ ] Implement comprehensive CLI testing
  - [ ] Create end-to-end test workflows with realistic data volumes
  - [ ] Add validation tests for all output formats
  - [ ] Implement boundary testing for edge cases
  - [ ] Build performance benchmarks for laptop environments
- [ ] Create user acceptance testing plan
  - [ ] Develop test scenarios for NAB business users
  - [ ] Build feedback collection mechanism
  - [ ] Create validation checklist for outputs
  - [ ] Design test data representative of NAB's environment
- [ ] Implement system verification utilities
  - [ ] Create diagnostic commands for environment validation
  - [ ] Add dependency checks for required libraries
  - [ ] Build self-test capabilities to verify installation
  - [ ] Implement system resource requirement verification

#### 8.7 Transition from Testing to Production - **PLANNED**
- [ ] Create transition workflow
  - [ ] Design process for moving from test data to production data
  - [ ] Build validation steps for ensuring quality with real data
  - [ ] Create rollback procedures for problematic analyses
  - [ ] Develop controlled deployment process for new functionality
- [ ] Implement phased rollout approach
  - [ ] Create limited scope initial deployment plan
  - [ ] Design expansion strategy for adding departments incrementally
  - [ ] Build metrics for tracking adoption and usage
  - [ ] Develop success criteria for each deployment phase
- [ ] Establish ongoing maintenance procedures
  - [ ] Create process for configuration updates
  - [ ] Design approach for incorporating user feedback
  - [ ] Build strategy for periodic retraining/recalibration
  - [ ] Develop documentation for regular maintenance tasks

#### 8.8 Configuration-Driven Data Model Enhancement - **PLANNED**
- [ ] Implement configuration-driven taxonomy management
  - [ ] Move hardcoded enumerations (like SkillType) to configuration files
  - [ ] Create dynamic loading system for taxonomies and classifications
  - [ ] Build schema validation for custom taxonomies
  - [ ] Implement backward compatibility for existing enum references
- [ ] Design flexible configuration schema
  - [ ] Create validation rules for custom classifications
  - [ ] Implement runtime registration of new types
  - [ ] Add user-friendly documentation for taxonomy extensions
  - [ ] Design migration tools for taxonomy changes
- [ ] Develop integration with external taxonomy providers
  - [ ] Create adapter framework for Skills Taxonomy Service providers
  - [ ] Implement mapping between provider schemas and internal models
  - [ ] Build automated sync process for taxonomy updates
  - [ ] Add audit trails for taxonomy modifications
- [ ] Create migration tooling
  - [ ] Design versioned taxonomy schemas
  - [ ] Implement automated migration between versions
  - [ ] Create data validation for taxonomy-dependent fields
  - [ ] Build reporting for taxonomy evolution
- [ ] Enhance test coverage
  - [ ] Create tests for custom taxonomy validation
  - [ ] Implement compatibility tests for taxonomy versions
  - [ ] Test runtime extension of classification systems
  - [ ] Verify backward compatibility with existing data

This enhancement will replace hardcoded enumerations throughout the codebase with a flexible, configuration-driven approach. By moving taxonomies like skill types to configuration, we gain several advantages:

1. **Future-proof adaptability** - New types can be added without code changes
2. **External integration** - Easy adaptation to external taxonomy providers 
3. **Organisational alignment** - Taxonomies can be tailored to match organisational structures
4. **Versioned evolution** - Changes can be tracked and migrations managed systematically

The implementation will ensure that all data models and processing logic adapt to taxonomy changes defined in configuration, reducing maintenance overhead and enabling the system to evolve alongside changing organisational needs.

### Implementation Details & Timeline

The CLI implementation will focus on creating a robust, user-friendly interface that can be reliably run on standard NAB laptops without requiring cloud infrastructure. The design will prioritize:

1. **Reliability**: Ensuring consistent results with appropriate error handling
2. **Usability**: Making the tool accessible to non-technical users
3. **Performance**: Optimizing for reasonable performance on standard hardware
4. **Integration**: Seamless connection to existing NAB tools like Power BI
5. **Maintainability**: Easy to update and extend as requirements evolve

**Timeline**: 15 working days
- Core CLI Enhancements: 3 days
- Local Production Preparation: 3 days
- Data Workflow Integration: 3 days
- Ad-hoc Analysis Toolkit: 2 days
- User Experience & Documentation: 2 days
- Testing & Quality Assurance: 1 day
- Transition Planning: 1 day

This phase will establish the skill similarity engine as a practical, production-ready tool that can be used on an ad-hoc basis by NAB P&C to generate valuable insights without requiring complex infrastructure or cloud deployment.

### Technical Implementation Details

#### Code Structure
```
skill_similarity_engine/
├── cli/
│   ├── __init__.py
│   ├── interactive.py    <- New file for interactive CLI
│   └── utils.py          <- CLI utilities
├── visualization/        <- Existing visualization code
├── models/               <- Existing data models
├── analysis/             <- Existing analysis code
├── similarity/           <- Existing similarity calculation
└── __main__.py           <- Updated entry point
```

#### Interactive CLI Flow Design
The interactive CLI will follow this sequence:
1. Welcome screen
2. Analysis type selection (focus on job-to-job similarity)
3. Input file selection (jobs data and skills taxonomy)
4. Output preferences (directory, format, filename)
5. Analysis parameters (similarity method, normalization, threshold)
6. Summary confirmation before proceeding
7. Progress tracking for each step
8. Final summary with output file locations
```
