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
**Branch: `feature/poc-memory-management`**

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
**Branch: `feature/poc-performance-optimization`**

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

#### 6.13 Error Handling and Logging Improvements
**Branch: `feature/poc-error-handling`**

> **Implementation Context**: The pre-computation phase involves long-running, resource-intensive processes that require robust error handling and detailed logging. When processing tens of thousands of jobs over hours, errors must be properly captured, contextualized, and where possible, recovered from without losing progress. Similarly, data quality issues must be detected and reported clearly to ensure the validity of results.
> 
> A key requirement is the ability to identify exactly where and why an error occurred in a large dataset, so the system can be restarted from that point rather than beginning again. The logging system must balance verbosity with performance impact, as excessive logging can slow down computation. The validation reporting will be critical for ensuring that the precomputed data meets quality standards before being used for analysis.

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

#### 6.4 Core Data Loading Enhancements
**Branch: `feature/poc-data-loading`**

> **Implementation Context**: Efficient data loading is crucial for our system, as it processes large datasets with complex relationships between skills, jobs, and job-skill mappings. The current implementation loads all data into memory at once, which doesn't scale to our full dataset of 35,000+ jobs and their associated skills. This section implements streaming and chunked loading capabilities that reduce memory pressure while maintaining data integrity.
> 
> A particular challenge is handling the many-to-many relationship between jobs and skills, where a single job may have hundreds of skills, and common skills appear in thousands of jobs. The composite key generation system is essential for addressing issues with duplicate job IDs across different organizational contexts. The enhanced loaders must maintain referential integrity across chunked loads while providing progress feedback for long-running operations.

- [ ] Update `SkillTaxonomyLoader` class
  - [ ] Add chunked loading support
      - [ ] Implement streaming CSV parser
      - [ ] Create progress tracking during load
      - [ ] Build partial taxonomy construction
      - [ ] Add incremental taxonomy updates
  - [ ] Implement memory-efficient processing
      - [ ] Create generator-based loading
      - [ ] Implement deferred object construction
      - [ ] Build dictionary sharing for common values
      - [ ] Add automatic string interning
  - [ ] Enhance validation for HRIS formats
      - [ ] Create comprehensive schema validation
      - [ ] Implement data quality checks
      - [ ] Build error recovery options
      - [ ] Add detailed validation reporting
- [ ] Update `JobArchitectureLoader` class
  - [ ] Add chunked loading support
      - [ ] Implement streaming job loading
      - [ ] Create job batching by department
      - [ ] Build partial architecture construction
      - [ ] Add job dependencies handling
  - [ ] Implement unique job ID creation
      - [ ] Create composite key generation system
      - [ ] Implement sanitization for key components
      - [ ] Build collision detection and resolution
      - [ ] Add compatibility with existing systems
  - [ ] Add flexible column mapping
      - [ ] Create configuration-driven column mapping
      - [ ] Implement auto-detection of column formats
      - [ ] Build translation layer for different HRIS exports
      - [ ] Add column validation and type checking
- [ ] Create utility for data validation and error reporting
  - [ ] Implement comprehensive validation rules
      - [ ] Create rule engine for data validation
      - [ ] Implement field-level validation rules
      - [ ] Build cross-field validation
      - [ ] Add business rule validation
  - [ ] Add detailed error reporting
      - [ ] Create structured error format
      - [ ] Implement error categorization
      - [ ] Build error location tracking
      - [ ] Add error severity classification
  - [ ] Create data quality metrics
      - [ ] Implement completeness metrics
      - [ ] Create consistency metrics
      - [ ] Build accuracy scoring
      - [ ] Add data quality dashboard

#### 6.5 TF-IDF and Skill Processing Improvements
**Branch: `feature/poc-skill-processing`**

> **Implementation Context**: Accurate similarity calculations depend on properly processing skills, particularly multi-word skills that make up a significant portion of our taxonomy. The current implementation treats each skill as an atomic unit, but doesn't handle skill phrases optimally, leading to potential inaccuracies in similarity scores. This section enhances our TF-IDF vectorization system to properly handle multi-word skills and maintain consistent mapping between original and processed skill names.
> 
> A key challenge is maintaining a bidirectional mapping between the original skill names (which may contain spaces, punctuation, and inconsistent formatting) and the normalized versions used in vector calculations. This mapping must persist across preprocessing and similarity calculations, ensuring that all outputs reference the original, human-readable skill names. The token preservation system for phrases is critical for maintaining semantic meaning that would otherwise be lost when treating words individually.
>
> **Memory-Efficient TF-IDF**: When processing large datasets (35,000+ jobs) using chunked processing, we must ensure that TF-IDF calculations maintain global corpus statistics. Our approach separates TF-IDF calculation into two phases: (1) a global statistics collection phase that computes document frequencies across the entire corpus, and (2) a chunked vector generation phase that applies these global statistics during similarity calculations. This ensures consistent TF-IDF weighting regardless of which chunk a job appears in.

- [ ] Enhance TF-IDF vectoriser in `similarity/cosine.py`
  - [ ] Add preprocessing for multi-word skills (spaces to underscores)
      - [ ] Implement configurable token transformation
      - [ ] Create bidirectional mapping storage
      - [ ] Build token normalization pipeline
      - [ ] Add compatibility with existing skill IDs
  - [ ] Implement token preservation for skill phrases
      - [ ] Create phrase detection system
      - [ ] Implement custom tokenizer for skill phrases
      - [ ] Build n-gram preservation
      - [ ] Add domain-specific stop words
  - [ ] Create configuration options for tokenisation strategies
      - [ ] Implement YAML-based tokenizer configuration
      - [ ] Create pluggable tokenizer system
      - [ ] Build domain-specific tokenizers
      - [ ] Add token filtering options
  - [ ] Implement two-phase TF-IDF for memory-efficient processing
      - [ ] Create global statistics collector for document frequencies
          - [ ] Implement streaming corpus analysis that minimizes memory usage
          - [ ] Create efficient document frequency counter with progress reporting
          - [ ] Build memory-efficient vocabulary builder
          - [ ] Add incremental statistics updates for new data
      - [ ] Implement persistent storage of IDF values
          - [ ] Create compressed binary format for IDF dictionary
          - [ ] Implement metadata storage with corpus statistics
          - [ ] Build versioning system for IDF values
          - [ ] Add compatibility checks between IDF files and job data
      - [ ] Build efficient IDF loader for chunked processing
          - [ ] Create memory-mapped IDF dictionary access
          - [ ] Implement lazy loading of IDF values
          - [ ] Build caching system for frequently accessed values
          - [ ] Add thread-safe access for parallel processing
      - [ ] Add validation to ensure consistent TF-IDF across chunks
          - [ ] Implement verification of IDF application consistency
          - [ ] Create test utilities to compare chunked vs. full calculation
          - [ ] Build diagnostic tools for identifying TF-IDF discrepancies
          - [ ] Add logging of TF-IDF statistics for verification
- [ ] Implement skill name mapping system
  - [ ] Add bidirectional mapping between original and transformed names
      - [ ] Create JSON mapping file format
      - [ ] Implement in-memory bidirectional lookup
      - [ ] Build persistence of mappings across runs
      - [ ] Add version tracking for mappings
  - [ ] Ensure consistency in all outputs
      - [ ] Implement mapping application in all exports
      - [ ] Create name resolution middleware
      - [ ] Build validation for mapping consistency
      - [ ] Add automatic detection of inconsistencies
  - [ ] Create utility methods for conversion
      - [ ] Implement transformation API
      - [ ] Create batch conversion utilities
      - [ ] Build streaming conversion
      - [ ] Add context-aware transformation
- [ ] Update skill taxonomy handling
  - [ ] Add validation for skill uniqueness post-transformation
      - [ ] Create collision detection for transformed names
      - [ ] Implement automatic disambiguation
      - [ ] Build validation reporting
      - [ ] Add manual override capability
  - [ ] Implement improved normalisation in SkillTaxonomyLoader
      - [ ] Create comprehensive normalization pipeline
      - [ ] Implement case normalization
      - [ ] Build punctuation handling
      - [ ] Add domain-specific normalization rules
  - [ ] Add configurability for normalisation strategies
      - [ ] Create YAML configuration for normalization
      - [ ] Implement strategy pattern for normalizers
      - [ ] Build pluggable normalizer system
      - [ ] Add normalization rule testing

#### 6.1 Pre-computation Strategy for Local Performance
**Branch: `feature/poc-precomputation`**

> **Implementation Context**: This section represents the core of our architectural redesign - transforming from on-demand calculation to a precomputation-based approach. The current system calculates similarities directly when requested, which doesn't scale to tens of thousands of jobs. The precomputation strategy introduces a "database-like" structure that stores vectorized job data and similarity matrices for rapid retrieval.
> 
> This approach addresses the quadratic complexity problem by performing the intensive calculations infrequently and storing the results in an optimized format. The system must efficiently store sparse vectors and matrices (most jobs have only a small subset of all possible skills, and most job pairs have very low similarity scores that can be filtered out). The versioning system ensures that precomputed data remains compatible with the job architecture as it evolves, while the incremental update capability avoids recalculating the entire matrix when only a small portion of the data changes.

> **Strategy Overview**: Transform the engine from a calculation-heavy system to a query-based system through intelligent pre-computation and storage of both input vectors and similarity matrices. This approach dramatically improves performance on standard laptops while maintaining accuracy and enabling interactive analysis.

##### 6.1.1 Input Data Vectorization Framework

> **Implementation Context**: The vectorization framework transforms raw job and skill data into mathematical representations (vectors) that can be efficiently compared. These vectors must be stored in a compact format that preserves the sparse nature of skill distributions across jobs. The metadata system must maintain a complete record of how vectors were generated to ensure reproducibility and proper interpretation of results.
> 
> A key challenge is maintaining the relationship between the original job data (with all its contextual attributes) and the mathematical vectors used for similarity calculations. The bidirectional mapping system ensures that we can always connect vector indices back to the original job IDs, which may be composite keys incorporating department, location, and other contextual elements. The storage system must balance compression for space efficiency with quick access for the query interface.

- [ ] Implement vector preprocessing framework
  - [ ] Create vector computation pipeline for skills, jobs, and job-skills mappings
      - [ ] Implement data extraction stage that preserves all metadata attributes
      - [ ] Develop preprocessing hooks for each data type (skills, jobs, mappings)
      - [ ] Create configurable TF-IDF parameters via YAML configuration
      - [ ] Build logging system that captures all preprocessing decisions
  - [ ] Implement optimized TF-IDF vector storage format
      - [ ] Use compressed numpy arrays (.npz format) with sparse matrix support
      - [ ] Implement binary serialization for faster loading
      - [ ] Create index mapping between job IDs and vector positions
      - [ ] Support for partial vector loading based on department
  - [ ] Add metadata storage alongside vectors (computation parameters, timestamps)
      - [ ] Create JSON manifest files containing vectorization parameters
      - [ ] Store all job attributes in a queryable metadata store
      - [ ] Implement bidirectional mapping between original and composite job IDs
      - [ ] Add provenance tracking for data sources and version information
  - [ ] Create validation utilities for vector integrity
      - [ ] Implement checksum verification for vector files
      - [ ] Add consistency checking between vectors and metadata
      - [ ] Create self-test functionality to verify vector quality
      - [ ] Build diagnostic tools for identifying corrupted or outdated vectors
- [ ] Design efficient storage strategy
  - [ ] Implement compressed numpy array storage for vectors
      - [ ] Use scipy.sparse CSR format for skill vectors
      - [ ] Implement automatic precision selection (float32 vs float64)
      - [ ] Create custom serialization for minimal file size
      - [ ] Add compression level configuration based on speed vs size tradeoff
  - [ ] Create directory structure to organize vectors by department and date
      - [ ] Implement standardized directory layout:
        ```
        precomputed_data/
        ├── vectors/
        │   ├── by_date/
        │   │   ├── YYYYMMDD/
        │   │   │   ├── all_vectors.npz
        │   │   │   └── metadata.json
        │   ├── by_department/
        │   │   ├── dept_name/
        │   │   │   ├── vectors.npz
        │   │   │   └── metadata.json
        │   └── latest/ (symlinks to most recent)
        ```
      - [ ] Add automatic cleanup of old vector files based on configurable retention
      - [ ] Create departmental subdirectories with standalone vector files
      - [ ] Implement date-based versioning for historical tracking
  - [ ] Add indexing for quick vector lookup by job ID
      - [ ] Create JSON index files mapping job IDs to vector indices
      - [ ] Implement multiple index types (by department, by original ID, by composite ID)
      - [ ] Build indexing system supporting O(1) lookups
      - [ ] Add search functionality for finding jobs by partial ID match
  - [ ] Implement versioning to track vector changes
      - [ ] Add automatic version incrementation in metadata
      - [ ] Create vector differencing tool to identify changes between versions
      - [ ] Store version history in metadata for audit purposes
      - [ ] Implement version compatibility checking for matrices
- [ ] Build incremental update capability
  - [ ] Create utilities to identify changed data since last vectorization
      - [ ] Implement file-based change detection system
      - [ ] Build data comparison tool to identify modified job/skill records
      - [ ] Create change detection hooks for HRIS-integrated workflows
      - [ ] Add configurable change sensitivity thresholds
  - [ ] Implement targeted recalculation for only affected vectors
      - [ ] Identify dependency graph of affected vectors when a skill changes
      - [ ] Create efficient selective recalculation algorithm
      - [ ] Implement change propagation to dependent matrices
      - [ ] Add "changed vectors only" processing mode
  - [ ] Add vector merging to maintain complete dataset
      - [ ] Create vector merge operation that preserves existing vectors
      - [ ] Build conflict resolution for overlapping vector changes
      - [ ] Implement transactional vector updates (all succeed or all fail)
      - [ ] Add verification of merged vector integrity
  - [ ] Create change logs for vector updates
      - [ ] Implement structured logging of all vector changes
      - [ ] Create human-readable change summaries
      - [ ] Store change history in metadata for auditing
      - [ ] Add reporting tool for summarizing update scope

##### 6.1.2 Similarity Matrix Pre-computation

> **Implementation Context**: Computing similarity matrices for 35,000+ jobs requires over 1.2 billion pairwise comparisons, which cannot be performed in a single pass on standard hardware with 32GB RAM. Our approach divides this massive computation into manageable chunks with adaptive sizing based on real-time memory monitoring. This ensures we maximize hardware utilization while preventing out-of-memory errors.
>
> The memory-adaptive chunking strategy dynamically adjusts processing batch sizes based on observed memory usage patterns, allowing the system to find the optimal balance between processing speed and memory consumption. For a typical laptop with 32GB RAM, we target keeping memory usage below 28GB to leave room for the operating system and other processes.

- [ ] Create similarity matrix computation framework
  - [ ] Implement batch processing for manageable chunks
      - [ ] Create adaptive chunking based on available memory and usage patterns
      - [ ] Implement sliding window matrix computation with memory monitoring
      - [ ] Build matrix reassembly from computed chunks with verification
      - [ ] Add progress tracking per chunk with ETA and memory predictions
  - [ ] Create department-based matrix segmentation
      - [ ] Implement storage of matrices by department pairs for memory efficiency
      - [ ] Create cross-department matrix calculation strategy with priority queuing
      - [ ] Build index system for department-specific lookups
      - [ ] Add metadata about department relationships
  - [ ] Add configurable priority for in-department vs cross-department calculations
      - [ ] Implement priority queue for matrix computation based on business value
      - [ ] Create configuration for department importance weighting
      - [ ] Build adaptive scheduling based on prior query patterns
      - [ ] Develop interrupt/resume capability for long computations
  - [ ] Implement checkpoint saving for long-running processes
      - [ ] Create standardized checkpoint file format with memory statistics
      - [ ] Add automatic checkpoint creation at configurable intervals or memory thresholds
      - [ ] Implement recovery from checkpoint after interruption
      - [ ] Build checkpoint verification system
- [ ] Develop sparse matrix storage
  - [ ] Implement threshold-based filtering (only store similarities above threshold)
      - [ ] Create configurable similarity threshold system
      - [ ] Implement matrix filtering pipeline
      - [ ] Add metadata tracking of applied thresholds
      - [ ] Build automatic threshold optimization based on density
  - [ ] Create efficient compressed sparse format
      - [ ] Use scipy.sparse.csr_matrix for storage
      - [ ] Implement custom serialization for better compression
      - [ ] Create memory-mapped sparse matrix loading
      - [ ] Add specialized sparse matrix operations
  - [ ] Add row/column indexing for fast lookup
      - [ ] Create JSON index files mapping job IDs to matrix indices
      - [ ] Implement bidirectional lookup (ID to index and index to ID)
      - [ ] Build indexing system supporting O(1) lookups
      - [ ] Add search functionality for finding related jobs
  - [ ] Implement block-based storage for department pairs
      - [ ] Create matrix blocks organized by department pairs
      - [ ] Implement standardized block naming convention:
        ```
        matrices/
        ├── dept_pairs/
        │   ├── dept1_dept2.npz
        │   ├── dept1_dept3.npz
        │   └── ...
        ├── within_dept/
        │   ├── dept1.npz
        │   ├── dept2.npz
        │   └── ...
        └── full_matrix.npz (optional)
        ```
      - [ ] Create "matrix map" for locating specific job pairs
      - [ ] Add lazy loading capabilities for matrix blocks
- [ ] Build department-prioritized computation
  - [ ] Create priority queue for department-pair processing
      - [ ] Implement priority scoring for department pairs
      - [ ] Create configuration for business-driven priorities
      - [ ] Build adaptive priority adjustment based on usage patterns
      - [ ] Develop APIs for priority management
  - [ ] Implement background processing for lower-priority pairs
      - [ ] Create worker pool for background processing
      - [ ] Implement priority-based task scheduler
      - [ ] Add resource monitoring to adapt worker count
      - [ ] Build pausable background processing system
  - [ ] Add resume capability for interrupted computation
      - [ ] Implement computation state serialization
      - [ ] Create resume flags and state tracking
      - [ ] Build verification of resumed computation
      - [ ] Add diagnostic tools for interrupted computations
  - [ ] Create usage-based prioritization (recently viewed departments get priority)
      - [ ] Implement query logging to track department access
      - [ ] Create heat map of department access patterns
      - [ ] Build adaptive priority system based on recent queries
      - [ ] Develop cache warming for frequently accessed departments

#### 6.7 Job Context and Metadata Handling
**Branch: `feature/poc-job-context`**

> **Implementation Context**: Our system needs to handle complex organizational contexts where the same job title may appear multiple times with different attributes (department, location, seniority level, etc.). The current implementation uses simple job IDs that don't capture this complexity, leading to potential inconsistencies and confusion in the similarity results.
> 
> This section implements a robust composite key system that ensures each job is uniquely identified with its full organizational context. The enhanced Job model will maintain rich metadata that can be used for filtering and analysis beyond simple similarity scores. The context-aware utilities enable powerful multi-dimensional analysis that considers organizational structure alongside skill similarity.

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

#### 6.8 Similarity Calculation Enhancements
**Branch: `feature/poc-similarity-enhancements`**

> **Implementation Context**: While our core similarity calculation uses cosine similarity between skill vectors, real-world job similarity involves additional factors like seniority level, role type, and location. The current implementation has basic support for these factors, but they need to be enhanced and optimized for the two-phase architecture.
> 
> The similarity calculator must be updated to leverage our parallel processing framework for better performance with large datasets. The factor tracking system is important for transparency, allowing users to understand which aspects of similarity (skills, seniority, role track, location) contributed most to a given similarity score. This transparency is crucial for business users to trust and effectively use the system's recommendations.

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

#### 6.9 Advanced Optimisation Strategies
**Branch: `feature/poc-advanced-optimization`**

> **Implementation Context**: This section focuses on specialized optimizations that can dramatically improve performance for our specific use case. The sparse matrix support is critical since most job pairs have very low similarity scores that can be filtered out, potentially reducing storage requirements by 90%+ without losing significant information.
> 
> The pre-filtering framework can avoid unnecessary calculations by quickly identifying job pairs that are unlikely to have high similarity based on metadata (e.g., jobs from completely different departments or with very different seniority levels). This approach can reduce the computation load by orders of magnitude. The incremental processing system ensures that we don't recalculate the entire similarity matrix when only a small portion of the data changes.

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

#### 6.6 Query Interface for Pre-computed Data
**Branch: `feature/poc-query-interface`**

> **Implementation Context**: The query interface is the user-facing component of our two-phase architecture, providing rapid access to the precomputed similarity data. Unlike the current approach which calculates similarities on demand, this interface primarily retrieves and filters precomputed results, delivering near-instantaneous responses even for complex queries across large datasets.
> 
> This interface must balance performance with flexibility, allowing users to explore similarity data with various filters and thresholds without requiring recalculation. The memory-efficient loading is crucial for keeping the interface responsive on standard hardware, loading only the relevant portions of the precomputed matrices. The hybrid execution model handles cases where the exact precomputed data isn't available, falling back to targeted on-demand calculation when necessary.

- [ ] Create high-performance query API
  - [ ] Implement job-to-job similarity lookups
  - [ ] Add similar-jobs-by-department queries
  - [ ] Create top-K similar jobs functionality
  - [ ] Implement composite queries (similar jobs with filters)
- [ ] Develop memory-efficient data loading
  - [ ] Implement on-demand loading of relevant matrix blocks
  - [ ] Create memory mapping for large matrices
  - [ ] Add caching for frequently accessed data
  - [ ] Implement data eviction strategies for memory management
- [ ] Build hybrid query execution
  - [ ] Create query planning to utilize pre-computed data when available
  - [ ] Implement fallback to on-demand calculation for missing data
  - [ ] Add query results caching
  - [ ] Create asynchronous background computation for frequently accessed missing data

#### 6.10 Configuration Transparency System
**Branch: `feature/poc-configuration-transparency`**

> **Implementation Context**: Our similarity calculations involve numerous configurable parameters that significantly impact the results, but the current implementation doesn't track or expose these parameters adequately. This section creates a comprehensive system for tracking, versioning, and exposing the configuration values that influence similarity scores.
> 
> This transparency is crucial for reproducibility and auditability - we need to know exactly what configuration produced a given set of results. The configuration embedding mechanism ensures that outputs always include the configuration that generated them, while the scenario management system enables users to compare different configuration approaches to find the optimal settings for their specific needs.

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

#### 6.11 CLI Commands for Pre-computation and Query
**Branch: `feature/poc-cli-enhancements`**

> **Implementation Context**: The command-line interface is the primary way users will interact with our system, particularly for triggering the resource-intensive precomputation phase and managing precomputed data. The current CLI is basic and doesn't support the two-phase architecture or provide adequate feedback for long-running operations.
> 
> The enhanced CLI must provide comprehensive commands for both phases of our system, with appropriate progress tracking and error handling for precomputation, and flexible query options for the interactive phase. The management commands are essential for maintaining the precomputed data over time, cleaning up outdated files and verifying the integrity of the data store.
>
> **Memory Management Context**: Given our deployment on standard laptops with 32GB RAM, the CLI must expose memory management options that allow users to control resource utilization. These options enable processing of large datasets (35,000+ jobs) by adapting chunk sizes and processing strategies based on available memory.

- [ ] Implement vector pre-computation command
  - [ ] Add `precompute-vectors` command with input source options
  - [ ] Create progress tracking and error handling
  - [ ] Add incremental update mode
  - [ ] Implement verification and validation options
  - [ ] Add memory management flags:
      - [ ] `--memory-limit` to set maximum memory usage (default: 28GB)
      - [ ] `--adaptive-chunks` to enable memory-based chunk sizing
      - [ ] `--min-chunk-size` and `--max-chunk-size` to set boundaries
- [ ] Create similarity matrix computation command
  - [ ] Add `precompute-similarity` command with department prioritization
  - [ ] Create options for chunk size and memory limits
  - [ ] Implement threading and parallel processing options
  - [ ] Add resumable execution with checkpoints
  - [ ] Implement memory-aware processing options:
      - [ ] `--memory-strategy` with options (conservative, balanced, aggressive)
      - [ ] `--memory-monitor-interval` to control sampling frequency
      - [ ] `--memory-threshold-warning` and `--memory-threshold-critical`
- [ ] Develop management commands
  - [ ] Create `list-precomputed` to show available pre-computed data
  - [ ] Add `verify-integrity` to validate pre-computed files
  - [ ] Implement `clean-outdated` to remove stale pre-computed data
  - [ ] Add `repair-precomputed` to fix corrupted data
  - [ ] Create `memory-estimate` to predict memory needs for a given dataset
- [ ] Update query interface CLI
  - [ ] Add performance tuning parameters
  - [ ] Implement memory optimisation flags
  - [ ] Create output format selection
  - [ ] Add configuration scenario options
  - [ ] Add department filtering
  - [ ] Add job level filtering
  - [ ] Create custom filter expressions
- [ ] Enhance help documentation
  - [ ] Add comprehensive option descriptions
  - [ ] Create usage examples
  - [ ] Implement configuration templates
  - [ ] Add troubleshooting section
  - [ ] Create memory management guide with hardware recommendations

#### 6.12 Focused Data Export and Insight-Driven Visualisation
**Branch: `feature/poc-exports`**

> **Implementation Context**: The ultimate goal of our system is to provide actionable insights through easily consumable outputs. The current implementation generates excessive data with limited prioritization, overwhelming users with raw similarity scores instead of focusing on the most relevant insights. This section implements a more focused approach to data export and visualization.
> 
> The primary output remains a comprehensive cross-department similarity dataset optimized for Power BI, but with enhanced metadata and configurability. The "highlights" mode addresses information overload by surfacing only the most significant findings. The departmental batching ensures that exports remain manageable even for the full dataset of 35,000+ jobs.

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

#### 6.14 Implementation Plan

> **Implementation Approach**: This implementation plan follows a logical dependency structure, starting with foundational utilities that all other components will build upon. Each sprint focuses on a specific layer of the architecture, ensuring that we build from the ground up with proper foundations. The memory management and performance optimization components come first as they provide essential infrastructure for all subsequent development. The core processing and vectorization framework follows, then the precomputation engine, and finally the query interface and outputs.
>
> This approach allows for incremental testing and validation, with each layer building on stable components from previous sprints. The sequencing also mirrors the data flow through the system: first we optimize how data is loaded and processed, then how it's stored and analyzed, and finally how it's queried and visualized.
>
> **Memory Management Focus**: Based on our testing with 35,000+ jobs on standard laptops with 32GB RAM, we've identified memory management as a critical success factor. We've prioritized the memory-aware processing framework early in the implementation plan to ensure all subsequent components can leverage these capabilities.

The POC integration will be structured as a 4-sprint project, with a total timeline of 8 weeks, aligned with our new two-phase architecture:

- **Sprint 1 (Weeks 1-2):** Foundation Layer 
  - Memory Management Enhancements (6.2)
  - Performance Optimisation (6.3)
  - Memory-Aware Processing Framework (6.16) [NEW]
  - Error Handling and Logging Improvements (6.13)
  
- **Sprint 2 (Weeks 3-4):** Core Processing Layer
  - Core Data Loading Enhancements (6.4)
  - TF-IDF and Skill Processing Improvements (6.5)
  - Input Data Vectorization Framework (6.1.1)

- **Sprint 3 (Weeks 5-6):** Pre-computation and Analysis
  - Similarity Matrix Pre-computation (6.1.2)
  - Job Context and Metadata Handling (6.7)
  - Similarity Calculation Enhancements (6.8)
  - Advanced Optimisation Strategies (6.9)

- **Sprint 4 (Weeks 7-8):** User Interface and Outputs
  - Query Interface for Pre-computed Data (6.6)
  - Configuration Transparency System (6.10)
  - CLI Commands for Pre-computation and Query (6.11)
  - Focused Data Export and Insight-Driven Visualisation (6.12)

##### Dependencies and Risks
- Access to real-world HRIS data for testing
- Stakeholder availability for UAT
- Sufficient computational resources for large-scale testing
- Access to representative multi-word skill samples for testing
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

#### 6.15 Examples and Practical Testing

> **Implementation Context**: While our test suite (unit, integration, functional) verifies that components work correctly in isolation and together, we need practical examples that demonstrate real-world usage patterns. These examples serve multiple purposes: they document how to use the components, validate that our APIs are intuitive, and provide a way to visually inspect memory behavior during actual operations rather than just in test scenarios. This practical testing is essential for memory management features where the proof is in the actual usage with real-scale data.
>
> A key difference between formal tests and these practical examples is that examples focus on demonstrating usage patterns and producing tangible outputs (like memory graphs) that developers can review, while formal tests focus on automated verification of correctness. Both are necessary for a complete quality assurance strategy.

- [x] Create example scripts to demonstrate memory management utilities
  - [x] Develop dashboard demonstration example
      - [x] Create script that tracks memory during a realistic workflow
      - [x] Generate visualizations showing memory usage patterns
      - [x] Add annotations for different processing stages
      - [x] Include prediction visualization for memory growth
  - [x] Implement memory-efficient comparison demo
      - [x] Create side-by-side comparison between standard and memory-efficient implementations
      - [x] Measure and display memory savings from optimizations
      - [x] Plot memory usage differences as operations scale
      - [x] Add commentary on memory pattern differences
  - [x] Create function-level profiling example
      - [x] Demonstrate profiling decorator on key functions
      - [x] Show relationship between input size and memory usage
      - [x] Implement reporting of per-function memory statistics
      - [x] Include visualization of memory footprint by function
  - [x] Build memory leakage detection example
      - [x] Create demonstration of leak detection utilities
      - [x] Show how to identify problematic object types
      - [x] Implement reference tracking for common leak patterns
      - [x] Include remediation examples for typical memory leaks
- [x] Create practical examples of memory optimization approaches
  - [x] Develop context manager usage examples
      - [x] Show how to identify memory-intensive code blocks
      - [x] Create nested context examples for detailed memory tracking
      - [x] Implement combined CPU and memory profiling
      - [x] Show real-time decision making based on memory metrics
  - [x] Implement CLI tool monitoring examples
      - [x] Create example of integrating memory monitoring into CLI
      - [x] Show configuration options for memory optimization
      - [x] Implement adaptive behavior based on available memory
      - [x] Demonstrate reporting options for memory usage
  - [x] Create real-world batch processing example
      - [x] Implement chunk size optimization based on memory constraints
      - [x] Show memory-aware parallel processing
      - [x] Create adaptive resource utilization example
      - [x] Implement checkpoint and resume capabilities
- [x] Set up example data and configuration
  - [x] Create realistic sample datasets for memory testing
      - [x] Generate scalable synthetic job and skill data
      - [x] Implement configuration templates for memory testing
      - [x] Create data generation scripts with controllable complexity
      - [x] Add documentation on data characteristics
  - [x] Implement configuration examples
      - [x] Create optimized configurations for different memory constraints
      - [x] Document memory-critical configuration parameters
      - [x] Implement templates for various hardware profiles
      - [x] Create configuration impact analysis examples

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
- [ ] Implement comprehensive testing strategy
  - [ ] Create unit tests for address standardisation functions
  - [ ] Build integration tests for full location comparison workflow
  - [ ] Develop functional tests for location-based similarity adjustments
  - [ ] Add examples demonstrating real-world location impacts on job matches

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
- [ ] Develop testing and validation approach
  - [ ] Create unit tests for distance calculation accuracy
  - [ ] Build integration tests with known location pairs
  - [ ] Develop example scripts to visualize distance-similarity relationship
  - [ ] Implement benchmarks for geocoding performance

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

#### 6.16 Memory-Aware Processing Framework
**Branch: `feature/memory-aware-processing`**

> **Implementation Context**: Processing 35,000+ jobs with over 1.2 billion comparisons on standard laptops with 32GB RAM requires sophisticated memory management. Our testing has shown that neither a fully memory-efficient approach nor a standard implementation alone can solve this challenge. Instead, we need a hybrid approach that continuously monitors memory usage and adapts processing strategies in real-time.
>
> This section implements a comprehensive memory-aware processing framework that integrates with the chunking and parallel processing components to ensure optimal resource utilization while preventing out-of-memory conditions. The framework provides both low-level utilities for fine-grained memory control and high-level abstractions that make memory-aware processing accessible throughout the codebase.

- [ ] Implement memory-aware processing controller
  - [ ] Create `MemoryAwareProcessor` class in `utils/memory_aware.py`
      - [ ] Implement continuous memory monitoring with configurable sampling rate
      - [ ] Create adaptive chunk size calculation based on memory trends
      - [ ] Build memory pressure detection with multiple warning levels
      - [ ] Add automatic garbage collection triggering based on thresholds
  - [ ] Develop memory-based execution strategies
      - [ ] Implement progressive chunk sizing that starts conservative and scales up
      - [ ] Create fallback mechanisms for when memory pressure is detected
      - [ ] Build emergency cleanup protocols for critical memory situations
      - [ ] Add memory reservation system for critical operations
  - [ ] Add configuration options for memory-aware processing
      - [ ] Create YAML configuration section for memory thresholds and strategies
      - [ ] Implement runtime adjustment of memory parameters
      - [ ] Build memory strategy profiles for different hardware configurations
      - [ ] Add documentation of memory parameters and their impacts
- [ ] Create memory-efficient data structures for similarity calculations
  - [ ] Implement sparse vector representation for job skills
      - [ ] Create compressed skill vector format using scipy.sparse
      - [ ] Implement memory-mapped vector storage for large datasets
      - [ ] Build vector slicing for partial loading
      - [ ] Add vector compression with configurable precision (float32/float16)
  - [ ] Develop incremental similarity matrix builder
      - [ ] Create block-based matrix construction that processes and saves in chunks
      - [ ] Implement threshold-based filtering to only store significant similarities
      - [ ] Build memory-mapped matrix access for efficient queries
      - [ ] Add matrix compression techniques for storage efficiency
  - [ ] Add memory usage analytics
      - [ ] Create detailed memory profiling for similarity calculations
      - [ ] Implement memory usage prediction based on job counts
      - [ ] Build visualization of memory usage patterns during processing
      - [ ] Add memory efficiency scoring for different implementation approaches
- [ ] Integrate with existing components
  - [ ] Update similarity calculator to use memory-aware processing
      - [ ] Implement memory-efficient cosine similarity calculation
      - [ ] Create chunked matrix operations that respect memory limits
      - [ ] Build adaptive precision control based on memory availability
      - [ ] Add fallback to disk-based processing for extreme cases
  - [ ] Enhance job architecture loading with memory awareness
      - [ ] Implement progressive loading of job data based on memory availability
      - [ ] Create memory-efficient job representation with shared attributes
      - [ ] Build lazy loading of job details
      - [ ] Add memory impact estimates for job loading operations
  - [ ] Update CLI with memory management options
      - [ ] Add `--memory-limit` flag to control maximum memory usage
      - [ ] Implement `--adaptive-chunks` option for memory-based chunking
      - [ ] Create `--memory-profile` option to output detailed memory analytics
      - [ ] Build memory strategy selection through configuration