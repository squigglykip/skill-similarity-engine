# Skill Similarity Engine - Project Plan

## Overview

This document outlines the development plan for the NAB Skill Similarity Engine, a system designed to analyse skill similarities between jobs and employees to identify reskilling opportunities. The project will be implemented in phases, with each phase corresponding to a specific git branch.

> **IMPLEMENTATION FOCUS UPDATE**: Based on current organizational data constraints, the primary focus is on **Job-to-Job Similarity Analysis**. Our implementation will concentrate on generating high-quality job similarity matrices and related outputs optimized for Power BI integration. Employee-to-job and employee-to-employee analyses are deprioritized until individual skill data becomes available. This approach aligns with the "Prescribe Skills" paradigm where job definitions drive skill assignments.

## Development Branches

We will use the following branch structure:
- `main` - Production-ready code
- `develop` - Integration branch for feature branches
- Feature branches - Named according to the feature being implemented

## Phase 1: Core Framework

**Branch: `feature/core-framework`**

### 1.1 Project Setup (1 day)
- [x] Create project structure
- [x] Set up development environment
- [x] Define initial dependencies in requirements.txt
- [x] Configure pyproject.toml

### 1.2 Data Models (3 days)
- [x] Implement `models/skills.py` for skill taxonomy representation
- [x] Implement `models/jobs.py` for job architecture representation
- [x] Implement `models/employees.py` for employee data representation
- [x] Add type annotations and proper documentation

### 1.3 Configuration System (2 days)
- [x] Implement `config/settings.py` for application configuration
- [x] Create YAML/JSON configuration parsers
- [x] Implement configuration validation
- [x] Add support for environment-specific configurations

### 1.4 Data Normalisation (3 days)
- [x] Implement min-max scaling in `data/normalisers.py`
- [x] Implement boolean normalisation
- [x] Implement TF-IDF style weighting for rare vs. common skills
- [x] Implement configurable importance weights

### 1.5 Data Loaders (2 days)
- [x] Implement CSV data loaders in `data/loaders.py`
- [x] Implement Excel data loaders
- [x] Add data validation and error handling
- [x] Create sample data files for testing

## Phase 2: Similarity Engine

**Branch: `feature/similarity-engine`**

### 2.1 Vector Representation (3 days)
- [x] Implement vector representation for skills in `analysis/vectors.py` (implemented in `similarity/cosine.py`)
- [x] Add support for different vectorisation strategies
- [x] Implement dimensionality reduction techniques (optional)
- [x] Create utility functions for vector manipulation

### 2.2 Similarity Calculation (3 days)
- [x] Implement cosine similarity in `analysis/similarity.py` (implemented in `similarity/cosine.py`)
- [ ] Implement Euclidean distance *(deferred - cosine similarity provides sufficient results)*
- [ ] Implement Jaccard similarity *(deferred - cosine similarity provides sufficient results)*
- [x] Add threshold configuration options

### 2.3 Similarity Matrix Generation (2 days)
- [x] Implement job-to-job similarity matrix generation
- [ ] *(DEPRIORITIZED)* Implement person-to-job similarity matrix generation
- [ ] *(DEPRIORITIZED)* Implement person-to-person similarity matrix generation
- [x] Add performance optimisations for large datasets

## Phase 3: Gap Analysis

**Branch: `feature/gap-analysis`**

### 3.1 Skill Gap Identification (3 days)
- [x] Implement skill gap identification in `analysis/gap.py`
- [x] Identify present skills vs. needed skills
- [x] Identify excess skills (skills not needed in target role)
- [x] Create comprehensive gap reports

### 3.2 Development Effort Calculation (2 days)
- [x] Implement development effort scoring
- [x] Factor in skill difficulty levels
- [x] Add configurable weighting for different skill categories
- [x] Create prioritised development plans

### 3.3 Reskilling Pathway Generation (3 days)
- [x] Implement reskilling pathway algorithms
- [x] Add support for multi-step career transitions
- [x] Implement optimal path finding for skill development
- [x] Create pathway visualisation data structures

> **NOTE**: Phase 3 implementation is complete but will primarily be used for job-to-job transitions. Full value will be realized when employee skill data becomes available.

## Phase 4: Reporting & Visualisation

**Branch: `feature/reporting-visualization`**

### 4.1 Basic Reporting (2 days)
- [x] Implement DataFrame export functionality
- [x] Add CSV export capabilities
- [x] Add JSON export capabilities
- [x] Implement report configuration options

### 4.2 Heatmap Visualisation (2 days)
- [x] Implement heatmap generation in `visualization/heatmaps.py`
- [x] Add customisation options for heatmap appearance
- [x] Create interactive heatmaps *(deferred - static exports for Power BI preferred)*
- [x] Add clustering options for better visualisation

### 4.3 Network Graph Visualisation (3 days)
- [ ] *(ON HOLD)* Implement network graph generation in `visualization/networks.py`
- [ ] *(ON HOLD)* Add options for different graph layouts
- [ ] *(ON HOLD)* Implement filtering and highlighting
- [ ] *(ON HOLD)* Add interactive elements

*Note: Network visualisation has been put on hold due to scale limitations with the dataset size (47,000 employees, 35,000 jobs, 35,000 skills).*

### 4.4 Workforce Planning Reports (3 days)
- [x] Implement aggregate reporting functionality
- [x] Create skills gap analysis at organisational level
- [ ] *(ON HOLD)* Add department/team level reporting *(will be implemented in Power BI)*
- [ ] *(ON HOLD)* Implement future state modelling *(will be implemented in Power BI)*

### 4.5 Large-Scale Visualisation (3 days) *(NEW)*
- [x] Implement hexbin visualisation for dimensionality reduction in `visualization/hexbin.py`
- [x] Add support for different dimensionality reduction methods (PCA, t-SNE, UMAP)
- [x] Implement efficient data export for Power BI integration
- [x] Add opportunity flags for filtering in Power BI

> **FUTURE DEVELOPMENT**: Most visualization outputs are currently designed for job-to-job analysis. Power BI will be the primary tool for interactive visualization, with this engine providing optimized data exports.

## Phase 5: CLI & Testing

**Branch: `feature/cli-testing`**

### 5.1 Command Line Interface (3 days)
- [x] Create CLI framework in `scripts/`
- [x] Implement commands for most important functionalities:
  - [x] Data loading and transformation
  - [x] Similarity calculation
  - [x] Gap analysis 
  - [x] Generating reports and exports
- [x] Add configuration options via CLI
- [x] Create comprehensive help documentation

### 5.2 Testing Approach *(REVISED)*

> **Testing Caveat**: Given the scale and complexity of the data this system will handle (47,000 employees, 35,000 jobs, 35,000 skills), we are adopting a pragmatic testing approach focusing on hands-on functional testing before implementing formal unit tests. This allows us to identify and resolve practical integration issues quickly.

> **Testing Focus**: Since our implementation prioritises Job-to-Job Similarity Analysis, our testing efforts will concentrate on validating the accuracy, performance, and usefulness of job similarity outputs for Power BI integration.

> **Deployment Pipeline Methodology**: To ensure a robust, production-grade implementation of the Job-to-Job Similarity functionality, we will follow a staged deployment pipeline with clear quality gates between environments (Development → Testing → Staging → Production). This industry-standard approach ensures that only thoroughly tested code advances to production, with appropriate validation at each stage.

#### 5.2.1 Functional Testing (2 days)
- [x] Test CLI scripts with sample data
- [x] Verify data loading and validation
- [x] Test similarity calculations with small datasets
- [x] Test export functionality and file generation
- [x] Identify and fix bugs in core workflows

**Job-to-Job Specific Tests:**
- [x] Verify correct parsing of job skill requirements from input files
- [x] Test job vectorisation with different normalisation settings
- [x] Validate job similarity scores against manually calculated examples
- [x] Test filtering of job similarity results by department/job family
- [x] Verify that opportunity flags are correctly applied to job pairs
- [x] Test similarity thresholds and their impact on identified opportunities
- [x] Validate clustering algorithms used for job grouping
- [x] Test export formats for Power BI compatibility

#### 5.2.2 Integration Testing (2 days)
- [x] Test end-to-end workflows with realistic data volumes
- [x] Verify department filtering functionality
- [x] Test configuration overrides and custom settings
- [x] Document any performance bottlenecks for optimization
- [x] Validate CSV export format standards for Power BI integration

**Job-to-Job Integration Tests:**
- [x] Test performance with realistic job volumes (35,000+ jobs)
- [x] Validate memory usage during large-scale similarity calculations
- [ ] Test incremental updates to job architecture data
- [x] Verify integration between job architecture and skill taxonomy components
- [x] Test job similarity outputs with Power BI import process
- [x] Validate relationship model compatibility in Power BI
- [x] Test configuration of opportunity thresholds and their impact
- [x] Verify consistent results across multiple runs with the same input data

#### 5.2.3 Unit Testing (2 days) *(Prioritized Components)*
- [x] Implement tests for critical data models
- [x] Test key similarity calculation methods
- [x] Test gap analysis core functionality
- [x] Focus on components with complex logic

**Job-to-Job Unit Tests:**
- [x] Test `JobArchitecture` class methods and properties
- [x] Validate job skill vector representation functions
- [x] Test cosine similarity calculation accuracy for job pairs
- [ ] Verify correct functioning of job clustering algorithms
- [x] Test job similarity matrix generation and export
- [x] Validate opportunity flag logic for job transitions
- [x] Test skill gap identification between job pairs
- [x] Verify development effort calculations for job transitions

#### 5.2.4 Performance and Scalability Testing *(NEW)*
- [x] *(LIMITED)* Benchmark job similarity calculation with progressively larger datasets
- [ ] *(ON HOLD)* Test memory optimisation techniques for large job matrices
- [ ] *(ON HOLD)* Validate chunking/batching approaches for large-scale processing
- [ ] *(ON HOLD)* Test parallel processing capabilities for similarity calculations
- [x] *(LIMITED)* Measure and optimise export performance for large datasets
- [ ] *(ON HOLD)* Verify system behavior with the full 35,000+ job dataset

> **Note**: Full-scale performance testing has been put on hold as TF-IDF vectorization has proven to be lightweight and performant for our current needs. Limited testing with sample datasets has confirmed adequate performance.

#### 5.2.5 Power BI Integration Testing *(NEW)*
- [x] Validate JSON/CSV exports as Power BI data sources
- [ ] *(ON HOLD)* Test relationship creation between exported datasets
- [ ] *(ON HOLD)* Verify opportunity flag filtering in Power BI
- [ ] *(ON HOLD)* Test measures and calculated columns based on similarity data
- [ ] *(ON HOLD)* Validate visualisations using job similarity data
- [ ] *(ON HOLD)* Test refresh behaviour with updated similarity outputs
- [ ] *(ON HOLD)* Verify job filtering by department/job family in Power BI
- [ ] *(ON HOLD)* Measure loading performance with full-scale datasets

> **Note**: Detailed Power BI integration testing will be conducted by the data analytics team during implementation. Basic export validation has been completed to ensure compatibility with Power BI import processes.

#### 5.2.6 Testing Finalisation Plan *(NEW)*

> **Testing Prioritisation**: Given our focus on Job-to-Job Similarity Analysis and integration with Power BI, the following testing priorities represent the final critical steps to ensure production readiness. Since we're using TF-IDF vectorization which is relatively lightweight, extreme performance optimization is less critical than initially anticipated.

**High Priority Testing Tasks:**
1. **Basic Performance Validation:**
   - [x] Confirm TF-IDF vectorization performance is adequate for our needs
   - [x] Run a basic performance test with a medium-sized dataset (~5,000 jobs)
   - [x] Verify memory usage is reasonable during similarity calculation
   - [ ] *(DEPRIORITIZED)* Implement performance benchmarking scripts to time each core operation

2. **Integration Testing:**
   - [x] Perform end-to-end test with a representative job dataset
   - [x] Validate export file sizes are manageable
   - [x] Verify Power BI import process completes successfully 
   - [x] Test CSV export format compliance for Power BI integration
   - [ ] Test refresh cycles with incremental job updates
   - [ ] Document integration patterns for future reference

3. **Edge Case Testing:**
   - [x] Test with jobs having extremely sparse or dense skill sets
   - [x] Validate behavior with unusual skill taxonomy structures
   - [x] Test handling of jobs with missing or incomplete data
   - [x] Verify graceful error handling and meaningful error messages

4. **Production Preparation:**
   - [x] Create deployment documentation
   - [x] Set up basic logging for critical operations
   - [x] Document configuration settings for production environment
   - [ ] *(DEPRIORITIZED)* Create monitoring hooks for long-running processes

**Testing Deliverables:**
- [x] Create a test summary document outlining test coverage
- [ ] *(DEPRIORITIZED)* Document performance benchmarks at various data scales
- [x] Prepare a troubleshooting guide for common issues
- [x] Document Power BI integration patterns and best practices
- [x] Create sample data templates for future testing
- [x] Reorganize tests into unit, integration, and functional categories

#### 5.2.7 Additional Testing Tasks *(NEW)*

The following additional testing tasks will further strengthen the system's reliability and ensure smooth integration with downstream consumers:

**Expanded Test Coverage:**
- [ ] Complete remaining unit tests for the `test_models.py` and `test_data.py` modules
- [x] Implement integration tests for the visualisation module in `test_visualisation.py`
- [x] Add functional tests for analysis workflows in `test_analysis.py`
- [ ] Create test workflows for the full job-to-job similarity pipeline

**CI/CD Integration:**
- [ ] Set up automated test runs as part of continuous integration
- [ ] Implement code coverage reporting
- [ ] Add linting checks to enforce code quality standards
- [ ] Create automated build and test documentation

**Data Quality Testing:**
- [ ] Implement tests for validating input data quality
- [ ] Create tests for verifying output data consistency
- [ ] Add tests for error handling with malformed input data
- [ ] Implement schema validation tests for CSV and JSON outputs

**Power BI Integration Assurance:**
- [ ] Develop specific tests for validating Power BI import processes
- [ ] Create tests that verify correct relationship structure in exported data
- [ ] Implement tests for checking metadata fields required by Power BI
- [ ] Add tests for validating incremental data update patterns

> **Implementation Note**: These additional tests will be structured according to the established test categorization: unit tests for isolated components, integration tests for component interactions, and functional tests for end-to-end workflows.

> **Revised Testing Strategy**: Given the lightweight nature of TF-IDF and our confidence in the scalability of the core algorithm, we'll focus more on integration testing and documentation rather than extensive performance optimization. We'll conduct basic performance validation to ensure no unexpected issues arise, but detailed benchmarking is less critical.

#### 5.2.8 Staged Deployment Implementation *(NEW)*

**Development Environment Quality Gates:**
- [ ] Implement comprehensive unit test suite for all core components
- [ ] Set up linting and static code analysis
- [ ] Create peer code review process
- [ ] Define technical debt and bug severity thresholds

**Testing Environment Tasks:**
- [ ] Set up dedicated testing environment with larger datasets
- [ ] Implement automated test pipelines for all test categories
- [ ] Create test data validation utilities
- [ ] Develop boundary condition and edge case test suite

**Staging Environment Implementation:**
- [ ] Configure staging environment mirroring production
- [ ] Set up procedures for testing with production data subsets
- [ ] Create validation workflow with domain experts
- [ ] Implement user acceptance testing process
- [ ] Develop performance benchmarking utilities for realistic loads

**Production Readiness:**
- [ ] Create deployment scripts and procedures
- [ ] Implement monitoring and logging framework
- [ ] Establish backup and recovery procedures
- [ ] Develop version tagging and release notes process
- [ ] Create user feedback collection mechanism

**Quality Gates and Metrics:**
- [ ] Define code coverage targets (aim for >80% for core functionality)
- [ ] Establish performance benchmarks for key operations
- [ ] Set memory usage thresholds for various data scales
- [ ] Create data quality validation framework
- [ ] Implement automatic quality report generation

**Promotion Process Implementation:**
- [ ] Create test result collection and reporting tool
- [ ] Define sign-off workflow for environment promotion
- [ ] Implement verification procedures for successful deployments
- [ ] Develop rollback mechanisms for failed deployments

### 5.3 Performance Optimisation (3 days) *(REVISED)*
- [ ] *(DEPRIORITIZED)* Address performance bottlenecks identified during testing
- [ ] *(DEPRIORITIZED)* Implement chunking/batching for large matrix calculations
- [ ] *(DEPRIORITIZED)* Add caching mechanisms for frequently accessed data
- [x] Optimise memory usage for very large exports (if needed)
- [x] Validate CSV export format compliance for memory-efficient Power BI loading

### 5.4 Documentation & Examples (2 days)
- [x] Complete all docstrings and type annotations
- [x] Update README with comprehensive usage instructions
- [x] Create Jupyter notebook examples
- [x] Create sample configuration templates for different use cases

## Phase 6: Data Pipeline & Integration

**Branch: `feature/data-pipeline`** *(RENAMED from data-transformation)*

### 6.1 Data Export Optimisation (2 days) *(REVISED)*
- [x] Create standardised data export formats
- [x] Implement efficient data serialisation
- [x] Add metadata and schema descriptions in exports
- [x] Ensure exports are optimised for downstream consumption
- [x] Validate CSV formats meet Power BI integration requirements

### 6.2 Data Transformation Scripts (2 days) *(REVISED)*
- [x] Create transformation scripts for converting tabular skill data to required format
- [ ] Implement mapping from raw HRIS data to the required skills structure
- [x] Add validation and error reporting for data transformation
- [ ] Focus on scalability for large dataset processing

### 6.3 Configuration System Enhancements (3 days) *(NEW)*
- [ ] Design comprehensive configuration schema for all configurable parameters
- [ ] Implement YAML-based configuration with hierarchical structure
- [ ] Move hardcoded thresholds, weights, and flags to configuration
- [ ] Create configuration validation and error reporting
- [ ] Add CLI support for configuration management
- [ ] Develop sample configuration files for different use cases
- [ ] Update components to use centralized configuration

### 6.4 Production Deployment Preparation (1 day) *(NEW)*
- [ ] Create deployment documentation
- [ ] Implement logging for production environments
- [ ] Add configuration templates for different environments (dev, test, prod)
- [ ] Create backup and recovery procedures

### 6.5 HRIS Integration *(NEW)*
- [ ] Develop mappings from HRIS job codes to internal job architecture
- [ ] Create data extraction scripts for HRIS integration
- [ ] Implement validation for HRIS data structure compatibility
- [ ] Build incremental update workflow for job architecture changes
- [ ] Document HRIS synchronisation procedures and scheduling

### 6.6 Power BI Integration Finalisation *(NEW)*
- [ ] Finalise data schema documentation for Power BI developers
- [ ] Create reference relationship models for Power BI implementation
- [ ] Develop sample DAX measures for common analyses
- [ ] Document refresh and update procedures
- [ ] Create user guide for working with exported data in Power BI

> **IMPLEMENTATION NOTE**: Phase 6 work will concentrate on optimizing job-to-job similarity data for Power BI consumption, ensuring proper relationship modeling between jobs and skills.

## Phase 7: Interactive CLI Implementation

**Branch: `feature/interactive-cli`**

### 7.1 Interactive CLI Framework (2 days)
- [ ] Create interactive CLI module structure
- [ ] Implement welcome screen and main flow sequence
- [ ] Add styled console output with rich library
- [ ] Set up questionary/PyInquirer for interactive prompts

### 7.2 User Flow Implementation (3 days)
- [ ] Build analysis type selection interface
- [ ] Implement input file selection with validation
- [ ] Create output preferences configuration flow
- [ ] Develop analysis parameters selection screens
- [ ] Add summary confirmation before proceeding with analysis

### 7.3 Progress Tracking (2 days)
- [ ] Implement progress bars for time-consuming operations
- [ ] Add spinners for operations without percentage completion
- [ ] Include elapsed time indicators for long-running processes
- [ ] Create step-by-step progress indicators

### 7.4 Integration with Core Analysis (2 days)
- [ ] Connect interactive CLI to existing analysis functions
- [ ] Ensure proper data flow between CLI and core functionality
- [ ] Implement progress tracking hooks in core analysis code
- [ ] Add thorough error handling and validation

### 7.5 Testing and Polish (2 days)
- [ ] Create test cases for interactive CLI
- [ ] Test with various input conditions and edge cases
- [ ] Polish user experience and refine error messages
- [ ] Add comprehensive help documentation

### 7.6 Documentation and Examples (1 day)
- [ ] Update README with interactive CLI usage instructions
- [ ] Create example scripts showcasing interactive functionality
- [ ] Add detailed comments and docstrings
- [ ] Include troubleshooting section for common issues

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

#### Interface Flow Design
The interactive CLI will follow this sequence:
1. Welcome screen
2. Analysis type selection (focus on job-to-job similarity)
3. Input file selection (jobs data and skills taxonomy)
4. Output preferences (directory, format, filename)
5. Analysis parameters (similarity method, normalization, threshold)
6. Summary confirmation before proceeding
7. Progress tracking for each step
8. Final summary with output file locations

#### Error Handling
- Validate file paths and formats before processing
- Provide clear, user-friendly error messages
- Allow users to retry when inputs are invalid
- Gracefully handle process interruptions

#### Integration Points
The interactive CLI will integrate with existing code at these points:
- Data loading and validation
- Similarity calculation
- Gap analysis
- Visualization generation
- Report generation

## Dependencies

The following dependencies will be used:
- pandas (data manipulation)
- numpy (numerical operations)
- scikit-learn (similarity metrics, dimensionality reduction)
- matplotlib/seaborn (visualisation)
- umap-learn (dimensionality reduction for large datasets)
- pyyaml (configuration)
- pytest (testing)
- click (CLI interface)

## Timeline

Total estimated time: 68 working days
- Phase 1: 11 days - **COMPLETED**
- Phase 2: 8 days - **COMPLETED** (with some deferred items)
- Phase 3: 8 days - **COMPLETED**
- Phase 4: 13 days - **COMPLETED**
- Phase 5: 11 days - **IN PROGRESS** (CLI completed, core testing completed, documentation in progress, additional testing ongoing)
- Phase 6: 10 days - **PENDING** (expanded scope with HRIS and Power BI integration)
- Phase 7: 12 days - **PLANNED** (Interactive CLI implementation)

## Technical Constraints

- Python 3.8+ compatibility
- Minimal external dependencies
- No sensitive data in codebase
- Cross-platform compatibility (Windows/macOS)
- Comprehensive documentation
- Clean data exports for Power BI integration
- Scalability for datasets with 40,000+ employees and 35,000+ jobs 

## Conclusion

The core Job-to-Job Similarity Analysis functionality has been fully implemented and tested. The system successfully:

1. Creates and manages job architectures with associated skill requirements
2. Vectorizes job skill profiles using TF-IDF 
3. Calculates cosine similarity between job pairs with high performance
4. Handles realistic job volumes and skill taxonomies
5. Produces clean outputs ready for Power BI integration

Remaining work is primarily focused on:
1. **Testing** - Completing additional test cases to ensure robustness and reliability
2. **Production Readiness** - Implementing logging, error handling, and deployment documentation
3. **Integration** - Finalising HRIS data mappings and Power BI integration patterns
4. **Data Quality** - Implementing data validation and quality checks
5. **Documentation** - Completing comprehensive guides for system usage and integration

With these final pieces in place, the system will be fully production-ready and positioned to deliver significant value through job similarity analysis and skill gap identification. The focus on Job-to-Job similarity provides immediate value while establishing a foundation for future employee-centric analyses once individual skill data becomes available. 