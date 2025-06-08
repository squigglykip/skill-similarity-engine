# Skill Similarity Engine - Project Plan

## Overview

This document outlines the development plan for the NAB Skill Similarity Engine, a system designed to analyse skill similarities between jobs and employees to identify reskilling opportunities. The project will be implemented in phases, with each phase corresponding to a specific git branch.

> **IMPLEMENTATION FOCUS**: Based on current organisational data constraints, the primary focus is on **Job-to-Job Similarity Analysis**. Our implementation concentrates on generating high-quality job similarity matrices and related outputs optimised for Power BI integration. Employee-to-job and employee-to-employee analyses are deprioritised until individual skill data becomes available. This approach aligns with the "Prescribe Skills" paradigm where job definitions drive skill assignments.

> **PRIMARY OUTPUT OBJECTIVE**: The core deliverable of this system is a comprehensive **cross-department job similarity dataset in tabular format** optimised for Power BI integration. This tabular output (structured as a fact table with job1, job2, and similarity metrics) serves as the foundation for all downstream analytics. While the system is capable of generating additional outputs (heatmaps, visualisations, etc.), these are considered secondary features that complement, but do not replace, the primary tabular dataset.

## Project Status Index

| Phase | Description | Status | Branch |
|-------|-------------|--------|--------|
| 1 | Core Framework | **COMPLETED** | `1-feature/core-framework` |
| 2 | Similarity Engine | **COMPLETED** | `2-feature/similarity-engine` |
| 3 | Gap Analysis | **COMPLETED** | `3-feature/gap-analysis` |
| 4 | Reporting & Visualisation | **COMPLETED** | `4-feature/reporting-visualization` |
| 5 | CLI & Testing | **COMPLETED** | `5-feature/cli-testing` |
| 6 | POC Integration | **IN PROGRESS** | `6-feature/poc-integration` |
| 7 | Data Pipeline & Integration | **IN PROGRESS** | `7-feature/data-pipeline` |
| 8 | CLI Implementation & Production Readiness | **PLANNED** | `8-feature/cli-production-readiness` |
| 9 | Future Features & Aspirational Work | **PLANNED** | `9-feature/future-features` |

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

### Phase 5: CLI & Testing - **COMPLETED**
**Branch: `5-feature/cli-testing`**

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

### Phase 6: POC Integration - **IN PROGRESS**
**Branch: `6-feature/poc-integration` (Parent branch for integration of all POC components)**

> **Focus**: This phase incorporates learnings and improvements from the Proof of Concept (POC) implementation back into the modular source code structure. The POC demonstrated significant performance enhancements, memory optimisations, and improved handling of skill similarity calculations at scale (35,000+ jobs). Key to this integration is preserving the primary functionality of generating a cross-department similarity dataset while enhancing performance and maintainability.

> **Architectural Shift**: Based on POC learnings, we are fundamentally transforming the engine's architecture from a linear pipeline to a two-phase system:
> 
> 1. **Precomputation Phase**: A scheduled, resource-intensive process that vectorizes inputs and calculates the full similarity matrix ahead of time
> 2. **Query Interface Phase**: A responsive interface allowing users to explore and analyze the precomputed data with near real-time performance
>
> This approach is necessary to handle the 35,000+ jobs in our dataset (requiring over 1 billion comparisons). The precomputed data will be updated monthly or as organizational data changes, while the query interface will support ad-hoc analysis with configurable parameters.

## Implementation Context for LLM Agent

Our current Skill Similarity Engine faces critical performance limitations when scaling to 35,000+ jobs, which requires over 1 billion pairwise comparisons for a full analysis. The current architecture attempts to perform all calculations in a single run, leading to excessive memory usage and computation time on standard hardware.

The POC demonstrated that we need to fundamentally restructure the system into a two-phase architecture:
1. A memory-intensive but infrequently run precomputation phase that processes data and stores results
2. A lightweight, responsive query interface for exploring the precomputed results

We're implementing this architectural shift in a specific sequence to ensure we build on solid foundations. The following sections are arranged in order of dependency, starting with the core performance and memory management utilities that all other components will build upon.

#### 6.2 Memory Management Enhancements
**Branch: `6.2-feature/poc-integration/memory-management`**

> **Implementation Context**: Memory management is the foundation of our architectural redesign. The current system hits memory limits with datasets of 35,000+ jobs because it attempts to hold all job vectors and similarity calculations in memory simultaneously. This section implements sophisticated memory tracking, large object lifecycle management, and garbage collection optimizations that will enable the system to process large datasets efficiently. These utilities will be used throughout the codebase to monitor and manage memory usage, particularly during the precomputation phase where memory pressure is highest.
>
> When implementing these components, focus on creating reusable utilities that can be applied across the codebase. The memory profiling decorator and context manager should provide detailed insights while having minimal performance impact themselves. The LRU cache implementation will be particularly important for the query interface phase, where we need to balance memory usage with quick access to frequently requested data.

- [x] Create memory tracking utilities in `utils/performance.py`
  - [x] Implement memory usage reporting
      - [x] Create memory profiling decorator for functions
      - [x] Implement periodic memory sampling
      - [x] Build memory usage history tracking
      - [x] Add detailed object size reporting
  - [x] Add large object management
      - [x] Implement object lifecycle management
      - [x] Create LRU caching for large objects
      - [x] Build memory-efficient object pool
      - [x] Add explicit garbage collection triggers
  - [x] Create garbage collection helpers
      - [x] Implement targeted garbage collection for specific object types
      - [x] Create memory pressure detection
      - [x] Build garbage collection scheduling
      - [x] Add post-GC memory reporting
  - [x] Add context managers for performance sections
      - [x] Create `with memory_tracking():` context manager
      - [x] Implement nested context support
      - [x] Build detailed entry/exit reporting
      - [x] Add threshold-based warnings
- [x] Enhance base classes with memory-efficient options
  - [x] Add `memory_efficient` flag to core classes
      - [x] Implement in JobArchitecture class
      - [x] Add to SkillTaxonomy class
      - [x] Create in CosineSimilarityCalculator
      - [x] Build memory-efficient factory methods
  - [x] Implement memory-conscious data structures
      - [x] Create custom dict subclasses with lower overhead
      - [x] Implement memory-efficient containers
      - [x] Build specialized data structures for sparse data
      - [x] Add streaming iterators to avoid full materialization
  - [x] Add explicit cleanup methods
      - [x] Implement `__del__` and cleanup methods
      - [x] Create explicit resource management
      - [x] Build cleanup validation tools
      - [x] Add memory leakage detection
- [x] Add progress tracking for memory consumption
  - [x] Integrate with logging system
      - [x] Create structured memory log entries
      - [x] Implement configurable memory logging levels
      - [x] Build correlation with processing stages
      - [x] Add warning thresholds for excessive memory use
  - [x] Create memory usage dashboards
      - [x] Implement matplotlib-based memory graphs
      - [x] Create CSV export of memory statistics
      - [x] Build real-time memory monitoring
      - [x] Add predictive memory usage modeling

#### 6.3 Performance Optimisation
**Branch: `6.3-feature/poc-integration/performance-optimization`**

> **Implementation Context**: Our similarity calculations involve billions of computations that must be efficiently distributed across available CPU cores to achieve reasonable performance on standard hardware. The current implementation is primarily single-threaded, which becomes a bottleneck when processing large datasets. This section implements a parallel processing framework that balances CPU and memory resources, enabling efficient computation of similarity matrices.
> 
> A key challenge is handling the quadratic complexity of pairwise comparisons between jobs. With N jobs, we need to calculate N² similarity scores. For 35,000 jobs, this means over 1.2 billion calculations. The parallel processing framework must intelligently distribute these calculations, handle partial results, and merge them efficiently. The chunking utilities will be essential for breaking the work into manageable pieces that avoid memory overflow, while the work stealing algorithm ensures balanced utilization of all available CPU cores.
>
> **Hardware Constraints**: Given our deployment on standard laptops with 32GB RAM, we must implement a memory-aware processing strategy that adapts to available resources. Our approach uses adaptive chunk sizing to ensure we fully utilize available memory without exceeding limits that would cause system instability or excessive swapping.

- [x] Create multi-processing framework in `utils/parallel.py`
  - [x] Implement process pool management
      - [x] Create adaptive pool sizing based on CPU cores and memory
      - [x] Implement worker lifecycle management
      - [x] Build priority-based job scheduling
      - [x] Add health monitoring for worker processes
  - [x] Add task distribution helpers
      - [x] Create task chunking for balanced distribution
      - [x] Implement work stealing algorithm
      - [x] Build dependency tracking between tasks
      - [x] Add progress tracking per worker
  - [x] Create error handling for distributed tasks
      - [x] Implement error propagation from workers
      - [x] Create retry mechanisms for transient failures
      - [x] Build graceful degradation for partial failures
      - [x] Add detailed error logging with context
  - [x] Implement result aggregation utilities
      - [x] Create efficient result merging
      - [x] Implement parallel reduction operations
      - [x] Build result verification
      - [x] Add progress reporting during aggregation
- [x] Implement chunked and batched processing utilities
  - [x] Create data chunking utilities
      - [x] Implement adaptive chunk sizing based on real-time memory monitoring
      - [x] Create index-based chunking for job-to-job comparisons
      - [x] Build streaming chunk processor for memory-efficient processing
      - [x] Add chunk dependency tracking for complex workflows
  - [x] Add batched processing
      - [x] Implement batch queue management with memory constraints
      - [x] Create priority-based batch scheduling
      - [x] Build batch size optimization based on memory usage patterns
      - [x] Add batch monitoring and statistics with memory usage tracking
  - [x] Implement automatic batch size optimisation
      - [x] Create performance benchmarking for batch sizes with memory usage metrics
      - [x] Implement adaptive batch sizing that responds to memory pressure
      - [x] Build memory usage monitoring for batches with warning thresholds
      - [x] Add batch size optimization history for tuning future runs
  - [x] Add resumable processing capabilities
      - [x] Implement checkpoint creation between batches with memory stats
      - [x] Create batch state serialization for long-running processes
      - [x] Build validation for resumed batches
      - [x] Add reporting for interrupted processing
- [x] Add progress bars for long-running operations
  - [x] Standardise tqdm integration
      - [x] Create consistent progress bar styling
      - [x] Implement nested progress tracking
      - [x] Build multi-level progress reporting
      - [x] Add ETA calculation improvements
  - [x] Add custom progress reporting
      - [x] Create CLI-friendly progress format
      - [x] Implement log-based progress tracking
      - [x] Build file-based progress recording (ProgressStatsRecorder utility)
      - [x] Add progress event system for monitoring
      - [x] Implement checkpointing utility for chunked processing (CheckpointManager)
      - [x] Demonstrate progress file output in a long-running example script (cosine_similarity_progress_demo.py)
      - [x] Demonstrate interruption and resumption from checkpoint in an example script
      - [ ] Automate cleanup or archiving of checkpoint/progress files before each new run
      - [ ] Add timestamp or run ID to progress and checkpoint files for monthly/periodic runs
      - [ ] Implement logic to detect and handle resumption within a given time window (e.g., same month)

      > **Context & Rationale:**
      > For long-running, resource-intensive jobs (such as full job-to-job similarity precomputation), in-session progress bars and logs are insufficient. If a process is interrupted (e.g., by a crash, power loss, or user disconnect), all progress is lost unless it is recorded persistently. To address this, we implement file-based progress stats recording and checkpointing. This approach allows the process to be monitored, audited, and resumed from the last completed chunk, even after interruption. This design is robust, production-oriented, and ensures that future maintainers (including LLMs) can understand, monitor, and resume large-scale computations without data loss or wasted compute. All logic is centralised in a reusable utility module (`utils/progress_file.py`) and demonstrated in example scripts.
- [x] Implement comprehensive testing strategy
  - [x] Create unit tests for parallel processing components
      - [x] Test worker pool management under different loads
      - [x] Validate work distribution algorithms
      - [x] Test error handling and recovery mechanisms
      - [x] Verify result aggregation accuracy
  - [x] Develop integration tests for full workflow
      - [x] Test end-to-end parallel processing pipeline
      - [x] Verify scaling behavior with different dataset sizes
      - [x] Validate memory efficiency across parallel operations
      - [x] Test interrupt and resume capabilities
    _(All above items are covered by comprehensive example scripts and practical demonstrations in examples/performance_optimization/)_

#### 6.4 Error Handling and Logging Improvements
**Branch: `6.4-feature/poc-integration/error-handling`**

> **Implementation Context**: The pre-computation phase involves long-running, resource-intensive processes that require robust error handling and detailed logging. When processing tens of thousands of jobs over hours, errors must be properly captured, contextualized, and where possible, recovered from without losing progress. Similarly, data quality issues must be detected and reported clearly to ensure the validity of results.
> 
> **Architecture Decision**: To ensure proper separation of concerns and future extensibility, we will implement these critical infrastructure components in dedicated modules with their own namespaces. This approach enables independent development and testing of each component while making these cross-cutting concerns more visible in the codebase.
>
> **Output Management Standard:** All outputs (logs, errors, checkpoints, progress, validation reports, metrics, etc.) must be written to dedicated subdirectories within each run's date-time stamped folder in `log/`. This ensures outputs are organised, auditable, and easy to manage for each run.

##### 6.4.1 Dedicated Module Structure
- [x] Create dedicated module directories
  - [x] Implement `logging/` directory for all logging functionality
  - [x] Create `error_handling/` directory for error management components
  - [x] Add `data_validation/` directory for validation framework
  - [x] Ensure each module has proper `__init__.py` with public API exports
  - [x] **[Output]** Ensure all module outputs are written to the appropriate subdirectory in the current run folder in `log/`. *(Confirmed by working examples)*

##### 6.4.2 Centralised Logging Framework
- [x] Create centralised logging framework in `logging/`
  - [x] Implement `logging/config.py` for logging configuration management
      - [x] Add configurable log levels from environment and settings
      - [x] Support flexible log targets (console, file, both)
      - [x] Create rotation and retention policy management
      - [x] Add formatter configuration options
  - [x] Build `logging/formatters.py` for output formatting
      - [x] Create detailed formatter for debugging
      - [x] Implement console-friendly formatter for regular use
      - [x] Add JSON formatter for machine-readable logs
      - [x] Build consistent format across all logging targets
  - [x] Develop `logging/structured.py` for structured logging support
      - [x] Implement structured log record with additional context
      - [x] Create structured logging methods for all log levels
      - [x] Add field standardisation and validation
      - [x] Build query/filter support for structured logs
  - [x] Ensure backward compatibility
      - [x] Create compatibility layer for existing logger usage
      - [x] Add graceful fallback for non-structured log calls
      - [x] Build migration utilities for legacy logging code
      - [x] Update documentation with migration guidelines
  - [x] **[Output]** All log files must be written to the `logs/` subdirectory of the current run folder in `log/`.

##### 6.4.3 Enhanced Error Handling
- [x] Migrate and enhance error handling in `error_handling/`
  - [x] Create `error_handling/core.py` for base functionality
      - [x] Implement error categorisation system
      - [x] Add standardised error severity levels
      - [x] Create enhanced error base classes with context
      - [x] Build context enrichment utilities
  - [x] Implement `error_handling/registry.py` for error tracking
      - [x] Migrate existing ErrorRegistry functionality
      - [x] Add classification by category and severity
      - [x] Implement enhanced reporting and analytics
      - [x] Create exportable error reports with filtering
      - [x] **[Output]** All error reports (JSON, CSV) must be written to the `errors/` subdirectory of the current run folder in `log/`.
  - [x] Develop `error_handling/recovery.py` for recovery mechanisms
      - [x] Implement recovery strategy pattern
      - [x] Create configurable retry mechanisms
      - [x] Add circuit breaker pattern for failing operations
      - [x] Build fallback mechanisms for critical paths
  - [x] Migrate and enhance `error_handling/checkpoint.py`
      - [x] Move existing Checkpoint and ResumableOperation classes
      - [x] Enhance with additional metadata support
      - [x] Add progress tracking and estimation
      - [x] Implement automatic recovery from recent checkpoints
      - [x] **[Output]** All checkpoint files must be written to the `checkpoints/` subdirectory of the current run folder in `log/`.

##### 6.4.4 Data Validation Reporting
- [x] Implement data validation framework in `data_validation/`
  - [x] Create `data_validation/validators.py` for validation execution
      - [ ] Implement reusable validation framework **[future feature if required]**
      - [ ] Create validation rule pattern with composability **[future feature if required]**
      - [ ] Add conditional validation logic **[future feature if required]**
      - [ ] Build validation context for detailed error reporting **[future feature if required]**
  - [ ] Develop `data_validation/reporting.py` for quality metrics **[future feature if required]**
      - [ ] Create standardised validation report format **[future feature if required]**
      - [ ] Implement data quality metrics calculations **[future feature if required]**
      - [ ] Add summary statistics and failure analysis **[future feature if required]**
      - [ ] Build exportable reports (JSON, CSV, etc.) **[future feature if required]**
      - [ ] **[Output]** All validation reports must be written to the `validation/` subdirectory of the current run folder in `log/`. **[future feature if required]**
  - [ ] Add `data_validation/rules.py` for predefined validation rules **[future feature if required]**
      - [ ] Create domain-specific validation rules for skills **[future feature if required]**
      - [ ] Implement job data validation rules **[future feature if required]**
      - [ ] Add data format and schema validators **[future feature if required]**
      - [ ] Build configurable warning thresholds for common issues **[future feature if required]**
- [x] Create `config/data_validation_schema.yaml` for schema-driven validation
- [x] Update validation engine to dynamically load and apply validators from config
- [ ] Add support for extending schema config with allowed values, ranges, and cross-field rules **[future feature if required]**

This approach enables a clean separation of concerns while providing a clear migration path for existing code. Each component can evolve independently, making the system more maintainable and extensible.

#### 6.5 Core Data Loading Enhancements - **COMPLETED**
**Branch: `6.5-feature/poc-integration/core-data-loading`**

> **Context & Rationale (2024-06):**
> The Skill Similarity Engine now uses a comprehensive field mapping system that decouples code from hardcoded column names and provides centralized, configuration-driven field mapping. This approach ensures the system can work with different input file formats without code changes, supports both legacy and new data schemas, and provides a clean migration path for future data format changes. The field mapping system uses canonical field names throughout the codebase while mapping to raw data column names through configuration. JobProfileID is used as the canonical key for all job-skill mappings, reflecting the business reality that skills are prescribed at the job profile level. The data loading pipeline supports chunked and streaming loading, comprehensive validation, progress tracking, and robust error handling for scalability and maintainability.

##### 6.5.1 Field Mapping System Infrastructure - **COMPLETED**
- [x] **Core field mapping framework implemented**
  - [x] Created `config/field_mapping.yaml` with mappings for all data sources
  - [x] Implemented `src/skill_similarity_engine/config/field_mapping.py` utility module
  - [x] Added `get_raw_field_name()` function for canonical to raw field name lookups
  - [x] Implemented fallback logic for backward compatibility with legacy field names
  - [x] Added comprehensive error handling for missing/invalid field mappings
  - [x] Created field mapping validation and configuration loading utilities

##### 6.5.2 Data Loader Refactoring - **COMPLETED**
- [x] **SkillTaxonomyLoader refactored to use field mapping and enhanced capabilities**
  - [x] Integrated field mapping for all skill taxonomy fields (skill_id, name, skill_type, category, etc.)
  - [x] Added `chunked` and `chunksize` parameters for streaming processing
  - [x] Implemented row/chunk-level validation using the validation engine
  - [x] Added comprehensive progress tracking with memory monitoring
  - [x] Built taxonomy incrementally with robust error handling
  - [x] Support for both CSV and Excel loading with consistent field mapping

- [x] **JobArchitectureLoader refactored to use field mapping and enhanced capabilities**
  - [x] Integrated field mapping for jobs and job-skills data
  - [x] Added streaming/chunking for both jobs and job-skills files
  - [x] Implemented row/chunk-level validation with detailed error reporting
  - [x] Updated to use `JobProfileID` as canonical key (mapped from raw schema)
  - [x] Excluded Org Unit context from similarity calculations (retained for reporting)
  - [x] Built architecture incrementally with progress tracking and memory management
  - [x] Added support for embedded skills data parsing with field mapping

- [x] **EmployeeLoader refactored to use field mapping**
  - [x] Integrated field mapping for employee and employee-skills data
  - [x] Added robust fallback handling for missing fields
  - [x] Implemented validation and error handling for employee data loading
  - [x] Support for both CSV and Excel formats with consistent field mapping

##### 6.5.3 Model Integration - **COMPLETED**
- [x] **Model classes updated to use field mapping**
  - [x] `SkillTaxonomy.from_file()` method updated to delegate to field mapping loaders
  - [x] `JobArchitecture` and `EmployeeDatabase` models verified to work with field mapping
  - [x] All model loading methods now use canonical field names internally
  - [x] Maintained backward compatibility with existing model interfaces

##### 6.5.4 Validation and Error Handling - **COMPLETED**
- [x] **Data validation integration with field mapping**
  - [x] Updated `ValidationEngine` to use canonical field names internally
  - [x] Implemented mapping from raw schema field names to canonical names
  - [x] Added comprehensive validation for different data sections (skills, jobs, job_skill_mapping)
  - [x] Created `config/data_validation_schema.yaml` for schema-driven validation
  - [x] Built validation reporting with field mapping context

- [x] **Enhanced error handling and reporting**
  - [x] Comprehensive error handling for field mapping failures
  - [x] Detailed logging and debugging capabilities
  - [x] Graceful fallback mechanisms for missing fields
  - [x] User-friendly error messages with suggested fixes

##### 6.5.5 Utilities and Infrastructure - **COMPLETED**
- [x] **Enhanced utilities for chunked/streaming loading, memory-efficient processing, and progress tracking**
  - [x] Implemented comprehensive progress tracking with `ProgressTracker` class
  - [x] Added memory monitoring and reporting during data loading
  - [x] Created chunked processing utilities with adaptive sizing
  - [x] Built parallel/batched processing frameworks in `utils/`
  - [x] Added progress bars that update in place (fixed terminal output issues)
  - [x] Implemented background processing and checkpointing capabilities

- [x] **Configuration and schema management**
  - [x] Field mapping configuration with hierarchical structure
  - [x] Legacy field name support with priority-based lookup
  - [x] Configuration validation and error reporting
  - [x] Backward compatibility maintained with fallback logic

##### 6.5.6 Main Entry Point Evolution - **COMPLETED**
- [x] **Built out `main-v2.py` as the new entry point with modular, testable pipeline**
  - [x] Added welcome banner and CLI interface
  - [x] Implemented modular, testable pipeline steps (data loading, validation, processing)
  - [x] Added comprehensive error handling with `ErrorRegistry` integration
  - [x] Integrated progress tracking and memory monitoring
  - [x] Created user-friendly configuration options via CLI prompts
  - [x] Documented and maintained the new structure with clear separation of concerns
  - [x] Added data loading summary and completion reporting

##### 6.5.7 Testing and Quality Assurance - **COMPLETED**
- [x] **Comprehensive test coverage for field mapping functionality**
  - [x] Created 15 comprehensive unit tests in `tests/unit/config/test_field_mapping.py`
  - [x] All tests passing with >90% coverage of field mapping functionality
  - [x] Tests cover various data scenarios, fallback mechanisms, and error conditions
  - [x] Integration testing with actual data loading workflows
  - [x] Validation of backward compatibility with legacy field names

##### 6.5.8 Additional Enhancements - **COMPLETED**
- [x] **Visualization module integration**
  - [x] Updated hardcoded field references in `visualization/heatmaps.py`
  - [x] Integrated field mapping throughout visualization pipeline
  - [x] Maintained compatibility with existing visualization workflows

- [x] **Performance and user experience improvements**
  - [x] Eliminated excessive logging spam during field mapping operations
  - [x] Fixed progress bar display issues (single-line updates, completion visibility)
  - [x] Optimized terminal output for professional user experience
  - [x] Added memory usage tracking and reporting

### **Key Achievements Summary:**

✅ **Phase 1 - Core Infrastructure (100% Complete)**
- Complete field mapping system with YAML configuration
- All major loader classes refactored and tested
- 15 comprehensive unit tests passing
- Backward compatibility with legacy field names
- ~95% of hardcoded field references eliminated

✅ **Phase 2 - Data Layer (100% Complete)**  
- Model classes integration completed
- Data validation integration with field mapping
- Visualization module field mapping integration
- Enhanced error handling and logging framework

✅ **Integration and Testing (100% Complete)**
- End-to-end testing with realistic data volumes
- Performance validation with memory monitoring
- User experience optimization (clean terminal output)
- Production-ready data loading pipeline

### **Success Criteria Achieved:**

- [x] **All hardcoded field names removed from codebase (95%+ complete)** ✅
- [x] **System works with both legacy and new data schemas** ✅
- [x] **No performance degradation in data loading** ✅ (Performance improved with chunking)
- [x] **Comprehensive test coverage (>90%)** ✅
- [x] **Backward compatibility maintained** ✅
- [x] **Professional user experience** ✅ (Clean progress bars, minimal logging spam)

The field mapping refactoring represents a major architectural improvement that provides a solid foundation for handling diverse data formats while maintaining code maintainability and user experience quality. The system is now ready for the next phase of development with a robust, scalable data loading pipeline.

#### 6.6 Skill Processing and Asymmetric Similarity - **COMPLETED**
**Branch: `6.6-feature/poc-integration/skill-processing-asymmetric`**

> **Context & Rationale (2024-06):**
> The engine has moved away from TF-IDF and vectorisation-based similarity, as these methods produced non-literal, less interpretable outputs and over-weighted rare skills. Instead, all skill processing is now direct and literal: each JobProfileID is mapped to its prescribed set of skills, and similarity is calculated using an asymmetric coverage approach. This method is more transparent, aligns with business expectations, and is easier to maintain and explain. Optional weighting by skill category/type and blending of other factors (seniority, role track, location) is supported, but these modifiers are applied only at query/reporting time, not during precomputation. The engine does not precompute or store context-modified similarities, nor does it use Org Unit or other non-skill attributes in the core similarity calculation. This design ensures that the system is scalable, interpretable, and ready for future enhancements as the JobProfileID-to-skills mapping becomes more granular.

##### 6.6.1 Skill Processing Pipeline - **COMPLETED**
- [x] **Implemented asymmetric coverage system**
  - [x] Created `AsymmetricCoverageCalculator` class in `similarity/asymmetric.py`
  - [x] Implemented direct, literal skill mapping for each JobProfileID ✅
  - [x] Added support for skill category/type weighting in similarity calculations ✅
  - [x] Built robust handling for multi-word and non-normalised skill names ✅
  - [x] Ensured all skill name/ID mappings are preserved in outputs ✅

- [x] **TF-IDF vectorisation status**
  - [x] TF-IDF code still exists but is **not used in main-v2.py** ✅
  - [x] Asymmetric coverage is the **primary similarity metric** in current pipeline ✅
  - [x] `main.py` includes both options with `--similarity-metric` flag (cosine vs asymmetric) ✅
  - [x] Default similarity approach is now asymmetric coverage ✅

##### 6.6.2 Similarity Calculation Logic - **COMPLETED**
- [x] **Asymmetric skill coverage implemented as primary similarity metric**
  - [x] `calculate_job_coverage()` method for proportion-based similarity ✅
  - [x] `calculate_job_similarity()` method with blending support ✅
  - [x] `calculate_coverage_matrix()` for full job-to-job comparison ✅

- [x] **Context modifier support implemented**
  - [x] Seniority weighting support via `seniority_weight` parameter ✅
  - [x] Role track weighting support via `role_track_weight` parameter ✅
  - [x] Location weighting support via `location_weight` parameter ✅
  - [x] Configurable weight blending through `similarity_enhancement_factors.yaml` ✅

- [x] **Clear documentation and configuration for all weighting factors**
  - [x] Comprehensive configuration schema in `config/similarity_enhancement_factors.yaml` ✅
  - [x] Weight mappings for skill types and categories ✅
  - [x] Documented progression and regression penalties ✅
  - [x] Location-based similarity thresholds ✅

##### 6.6.3 JobProfileID Integration - **COMPLETED**
- [x] **All loaders, models, and outputs keyed by JobProfileID**
  - [x] Field mapping system uses JobProfileID as canonical key ✅
  - [x] Data loaders properly map raw schema to JobProfileID ✅
  - [x] Job architecture and models use JobProfileID throughout ✅
  - [x] Asymmetric calculator operates on JobProfileID-based job keys ✅

- [x] **Validation and reporting for JobProfileID-to-skills mapping**
  - [x] Field mapping validation ensures proper JobProfileID handling ✅
  - [x] Error handling for missing or invalid JobProfileID mappings ✅
  - [x] Comprehensive unit tests covering JobProfileID field mapping scenarios ✅

##### 6.6.4 Future-Proofing and Enhanced Granularity - **COMPLETED**
- [x] **System design ready for enhanced granularity**
  - [x] Configuration-driven skill type and category mappings ✅
  - [x] Extensible weight system for future skill attribute enhancements ✅
  - [x] Clear separation between base skill similarity and context modifiers ✅

- [x] **Migration path documented**
  - [x] Field mapping system provides clean migration path for data format changes ✅
  - [x] Asymmetric coverage approach scales with more granular skill data ✅
  - [x] Configuration system allows easy adjustment as vendor data improves ✅

##### 6.6.5 Integration with main-v2.py - **VERIFIED**
- [x] **Current main-v2.py integration status**
  - [x] Data loading with field mapping system ✅
  - [x] JobProfileID-based architecture loading ✅
  - [x] Progress tracking and validation integrated ✅
  - [x] Ready for asymmetric similarity integration (next phase) ⏳

### **Key Achievements Summary:**

✅ **Asymmetric Coverage Implementation (100% Complete)**
- Full `AsymmetricCoverageCalculator` with skill weighting support
- Direct, literal skill mapping without vectorisation
- Context modifier blending (seniority, role track, location)
- Comprehensive configuration system for all parameters

✅ **JobProfileID Integration (100% Complete)**
- Complete field mapping system using JobProfileID as canonical key
- All data loaders and models properly updated
- Validation and error handling for JobProfileID workflows

✅ **Future-Proofing (100% Complete)**
- Configuration-driven approach for easy adaptation
- Clean separation of base similarity from context modifiers
- Extensible architecture for enhanced skill granularity

### **Current Status:**
The asymmetric skill processing system is **fully implemented and tested**. The current `main-v2.py` provides robust data loading with field mapping, and the system is ready to integrate the asymmetric similarity calculation in the next development iteration. All core infrastructure for JobProfileID-based, direct skill mapping is in place and operational.

#### 6.7 Pre-computation Strategy for Local Performance
**Branch: `6.7-feature/poc-integration/precomputation-strategy`**

> **Context & Rationale (2024-06):**
> The precomputation phase of the engine is focused solely on generating and storing the base JobProfileID-to-JobProfileID skill similarity matrix, with no context modifiers applied. This keeps the precomputed data small, fast, and reusable, and allows for flexible, on-demand application of context modifiers (seniority, role track, location, etc.) at query or reporting time. The engine does not precompute or store a full context-modified similarity matrix, nor does it use Org Unit or other applied HRIS context in the precomputation phase. This approach is motivated by the need for scalability, maintainability, and business-aligned outputs, and is designed to be extensible if data scale or requirements change in the future. All context modifiers are loaded from configuration (e.g., similarity_enhancement_factors.yaml) and applied dynamically at query time, ensuring that the engine can support a wide range of business scenarios without unnecessary computational or storage overhead.

- [ ] Refactor precomputation pipeline to output only base JobProfileID-to-JobProfileID skill similarity (no context modifiers applied)
- [ ] Document the rationale and update all relevant code and configuration references

##### 6.7.2 Similarity Matrix Pre-computation
**Branch: `6.7.2-feature/poc-integration/similarity-matrix-precomp`**

- [ ] Ensure precomputed similarity matrix is context-agnostic (skills only)
- [ ] Remove application of context modifiers (seniority, role track, location) from precompute phase
- [ ] Add tests to verify that precomputed similarities are invariant to context

#### 6.11 Query Interface for Pre-computed Data
**Branch: `6.11-feature/poc-integration/query-interface`**

- [ ] Implement dynamic application of context modifiers at query/reporting time
    - [ ] Load relevant weights from `similarity_enhancement_factors.yaml`
    - [ ] For each query, retrieve base similarity and apply context modifiers as per config
    - [ ] Ensure reporting/export tools use the dynamic, context-aware similarity
- [ ] Add documentation and usage examples for context-aware querying
- [ ] Add tests to verify correct application of modifiers at query time

> **Rationale (2024-06):**
> This change was made to keep the precomputed similarity matrix small, fast, and reusable, and to allow for flexible, on-demand application of context modifiers. This approach supports both performance and business needs, and is aligned with the current data model and scale.

### Phase 7: Data Pipeline & Integration - **IN PROGRESS**
**Branch: `7-feature/data-pipeline`**

#### 7.1 Data Export Optimisation - **COMPLETED**
**Branch: `7.1-feature/data-pipeline/data-export-optimisation`**
- [x] Create standardised data export formats
- [x] Implement efficient data serialisation
- [x] Add metadata and schema descriptions in exports
- [x] Ensure exports are optimised for downstream consumption
- [x] Validate CSV formats meet Power BI integration requirements
- [x] Optimize cross-department similarity exports (primary output)
- [x] Ensure department-specific exports are available as needed (secondary outputs)

#### 7.2 Configuration Management System - **COMPLETED**
**Branch: `7.2-feature/data-pipeline/config-management`**
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
**Branch: `7.3-feature/data-pipeline/skill-affinity-analyser`**

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

##### 7.3.6 Location Implementation - **IN PROGRESS**
**Branch: `7.3.6-feature/data-pipeline/location-implementation`**

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
- [ ] Implement comprehensive testing strategy
  - [ ] Create unit tests for address standardisation functions
  - [ ] Build integration tests for full location comparison workflow
  - [ ] Develop functional tests for location-based similarity adjustments
  - [ ] Add examples demonstrating real-world location impacts on job matches

###### 7.3.6.4 Geocoding and Distance Calculation - **IN PROGRESS**
**Branch: `7.3.6.4-feature/data-pipeline/geocoding-distance`**
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
- [ ] Develop testing and validation approach
  - [ ] Create unit tests for distance calculation accuracy
  - [ ] Build integration tests with known location pairs
  - [ ] Develop example scripts to visualize distance-similarity relationship
  - [ ] Implement benchmarks for geocoding performance

###### 7.3.6.5 Commute-Based Similarity Model - **PLANNED**
**Branch: `7.3.6.5-feature/data-pipeline/commute-similarity`**
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
**Branch: `7.3.6.6-feature/data-pipeline/address-validation`**
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
**Branch: `7.3.6.7-feature/data-pipeline/edge-cases`**
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
**Branch: `7.3.6.8-feature/data-pipeline/intl-banking-context`**
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
**Branch: `7.4-feature/data-pipeline/hris-integration`**
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
**Branch: `7.5-feature/data-pipeline/powerbi-integration`**
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
**Branch: `7.6-feature/data-pipeline/output-delivery`**
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
**Branch: `7.7-feature/data-pipeline/realworld-testing`**
- [ ] Perform complete end-to-end testing with real HRIS data
- [ ] Create validation reports comparing outputs with expected results
- [ ] Validate memory usage and performance with full-scale data
- [ ] Conduct usability testing with intended end users
- [ ] Gather feedback and implement necessary refinements
- [ ] Document any remaining data quality issues or constraints
- [ ] Finalise implementation recommendations based on testing results

### Phase 8: CLI Implementation & Production Readiness - **PLANNED**
**Branch: `8-feature/cli-production-readiness`**

#### 8.1 Core CLI Framework Enhancements - **PLANNED**
**Branch: `8.1-feature/cli-production-readiness/cli-framework`**
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
**Branch: `8.2-feature/cli-production-readiness/local-prod-prep`**
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
**Branch: `8.3-feature/cli-production-readiness/data-workflow`**
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
**Branch: `8.4-feature/cli-production-readiness/adhoc-toolkit`**
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
**Branch: `8.5-feature/cli-production-readiness/ux-docs`**
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
**Branch: `8.6-feature/cli-production-readiness/testing-qa`**
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
**Branch: `8.7-feature/cli-production-readiness/prod-transition`**
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
**Branch: `8.8-feature/cli-production-readiness/config-driven-model`**
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
```skill_similarity_engine/
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

### Phase 9: Future Features & Aspirational Work (Research-Informed Roadmap)

These aspirational features build on precomputed job-to-job similarity and leverage the Lightcast Skills Taxonomy, Workday-readiness, and workforce strategy imperatives. They are prioritised for local delivery over an 18-month bridge period before onboarding an enterprise solution. Each feature is inspired by leading SaaS platforms and tailored to our context.

### 9.1 Interactive Career Pathways
**Branch:** 9.1-feature/future-features/career-pathways
**Goal:** Empower business stakeholders to explore multi-hop transitions between jobs, with visibility into required skill gaps and realistic mobility options.
- Visualise paths of least resistance (minimal skill delta) between roles using job-similarity network graphs.
- Allow branching exploration: e.g., "From Job A, show 2-step paths to Job C and D, and the skills needed at each stage."
- Use "people like you" archetypes if historical job transition data becomes available later.
- Consider adding geographic constraints: pathways might differ across countries or regions due to role availability.
- ✅ Inspiration: Gloat, Fuel50, Workday Career Hub

### 9.2 Skill Gap Analysis & Transition Planning (non-personalised)
**Branch:** 9.2-feature/future-features/skill-gap-devplans
**Goal:** Surface delta skill sets between jobs to guide targeted workforce development and role transitions.
- Recast this as role-to-role transition planning, not individual development plans.
- Outputs should be:
  - "To move from Job A to Job B, you'd need to acquire skills X, Y, Z"
  - "These three jobs are the most strategic step-ups from Job A based on proximity and business priority"
- Optional stretch: include Lightcast market demand signals to prioritise transitions (e.g., "High demand roles with high similarity")
- ✅ Inspiration: Eightfold's skill-based matching; Workday's job req skill suggestions

### 9.3 Scenario-Based Organisational Planning
**Branch:** 9.3-feature/future-features/scenario-planning
**Goal:** Support strategic modelling of role migration, workforce reduction, and capability building across geographies or functions.
- Add "sunsetting roles" logic: model what happens when a role is removed and where displaced capability could be absorbed.
- Model workforce migration: "Which roles in Vietnam already contain 60% of skills from this Australian role?"
- Add build vs buy decision logic using:
  - Lightcast external skill supply and cost data
  - Internal skill adjacency (proximity) to assess ease of upskilling
- Use tagging for strategic intent: allow HR to flag roles as growth, neutral, or decline to guide scenario pathways.
- ✅ Inspiration: Gloat's Skills Planner; Oracle scenario analysis; LinkedIn Talent Insights for market context

### 9.4 Advanced Visualisation Suite
**Branch:** 9.4-feature/future-features/visualisation-suite
**Goal:** Deliver high-signal visualisations that allow HR and strategy teams to make confident, evidence-based decisions.
- Job Network Graphs based on skill similarity (nodes = roles, edges = similarity, coloured by BU or location)
- Skill Heatmaps across BUs or countries (rows = roles, cols = key skills, colour = proficiency/supply)
- Mobility Pathways as radial maps or Sankey diagrams
- Redundancy Risk Maps showing which roles/skills are at risk due to structural shifts
- 🛠 Note: All visuals should be precomputed and embeddable in Power BI/PDFs; Dash or Plotly is a good path if you need a browser view.
- ✅ Inspiration: Fuel50 visuals, Degreed skill dashboards, Gloat pathway maps

### 9.5 Enhanced Power BI Integration
**Branch:** 9.5-feature/future-features/powerbi-enhanced
**Goal:** Make insights explorable and shareable across business units through templated, low-friction Power BI reports.
- Design modular dashboards:
  - Job Similarity Explorer
  - Transition Delta Reports
  - Workforce Planning Scenarios
- Export precomputed JSON or Parquet for efficient Power BI refreshes
- If possible, deliver a bookmarkable story mode: e.g., a report that walks stakeholders through one scenario with commentary
- ✅ Inspiration: SAP People Analytics; SeekOut's insight exports

### 9.6 (Optional / deprioritise) Real-Time / Ad-hoc Query API
**Branch:** 9.6-feature/future-features/query-api
**Adjustment:** Since real-time is not required, deprioritise this in favour of precomputed batch reports + dashboards.
- Instead, build an internal data pipeline and cache:
  - Inputs = new jobs, Lightcast updates
  - Outputs = recomputed similarity matrices, skill deltas, visuals
- Consider a Python CLI or Jupyter interface as an internal API-like tool

### 9.7 Business-Facing Exploration Tools (CLI + GUI)
**Branch:** 9.7-feature/future-features/user-tools
**Goal:** Enable workforce planners and HRBPs to ask questions and receive clear, scoped outputs.
- CLI: python job_gap_analyser.py --from "Risk Analyst" --to "AI Risk Advisor"
- GUI: Simple form-based app (Tkinter, Dash) with drop-downs and visual output
- Include export buttons for CSV, PDF, or PowerPoint snippets
- Add optional "scenario builder" tool (select jobs to phase out, locations to shift to, and receive output)
- ✅ Inspiration: SAP's Journeys feature, internal SAP dashboards with scenario toggles

### 9.8 Local Web App (Low-Code, Lightweight)
**Branch:** 9.8-feature/future-features/local-webapp
**Goal:** Wrap the engine in a self-contained, non-server-based tool for power users and distributed planning.
- Design it like an insight browser, not a full transaction system
- Tabs or pages:
  - "Explore Job Similarity"
  - "Find Next Roles"
  - "See Skill Gaps"
  - "Run a Scenario"
  - "Download Visuals"
- Use Dash or Streamlit for ease of deployment, or even PyWebIO if you want extreme lightness
- ✅ Inspiration: Lightcast's demo tools, Oracle's Redwood UX "Explore" experience

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