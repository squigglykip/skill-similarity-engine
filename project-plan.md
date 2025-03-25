# Skill Similarity Engine - Project Plan

## Overview

This document outlines the development plan for the NAB Skill Similarity Engine, a system designed to analyse skill similarities between jobs and employees to identify reskilling opportunities. The project will be implemented in phases, with each phase corresponding to a specific git branch.

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
- [x] Implement person-to-job similarity matrix generation
- [x] Implement person-to-person similarity matrix generation
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

#### 5.2.1 Functional Testing (2 days)
- [ ] Test CLI scripts with sample data
- [ ] Verify data loading and validation
- [ ] Test similarity calculations with small datasets
- [ ] Test export functionality and file generation
- [ ] Identify and fix bugs in core workflows

#### 5.2.2 Integration Testing (2 days)
- [ ] Test end-to-end workflows with realistic data volumes
- [ ] Verify department filtering functionality
- [ ] Test configuration overrides and custom settings
- [ ] Document any performance bottlenecks for optimization

#### 5.2.3 Unit Testing (2 days) *(Prioritized Components)*
- [ ] Implement tests for critical data models
- [ ] Test key similarity calculation methods
- [ ] Test gap analysis core functionality
- [ ] Focus on components with complex logic

### 5.3 Performance Optimisation (3 days) *(REVISED)*
- [ ] Address performance bottlenecks identified during testing
- [ ] Implement chunking/batching for large matrix calculations
- [ ] Add caching mechanisms for frequently accessed data
- [ ] Optimise memory usage for large-scale operations

### 5.4 Documentation & Examples (2 days)
- [x] Complete all docstrings and type annotations
- [x] Update README with comprehensive usage instructions
- [x] Create Jupyter notebook examples
- [x] Create sample configuration templates for different use cases

## Phase 6: Data Pipeline & Integration

**Branch: `feature/data-pipeline`** *(RENAMED from data-transformation)*

### 6.1 Data Export Optimisation (2 days) *(REVISED)*
- [ ] Create standardised data export formats
- [ ] Implement efficient data serialisation
- [ ] Add metadata and schema descriptions in exports
- [ ] Ensure exports are optimised for downstream consumption

### 6.2 Data Transformation Scripts (2 days) *(REVISED)*
- [ ] Create transformation scripts for converting tabular skill data to required format
- [ ] Implement mapping from raw HRIS data to the required skills structure
- [ ] Add validation and error reporting for data transformation
- [ ] Focus on scalability for large dataset processing

### 6.3 Production Deployment Preparation (1 day) *(NEW)*
- [ ] Create deployment documentation
- [ ] Implement logging for production environments
- [ ] Add configuration templates for different environments (dev, test, prod)
- [ ] Create backup and recovery procedures

### 6.4 Data Quality Checks (1 day)
- [ ] Create data quality verification tools
- [ ] Implement consistency checks across different data sources
- [ ] Add reporting for missing or anomalous data
- [ ] Create audit trails for data transformations

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

Total estimated time: 57 working days (~11-12 weeks)
- Phase 1: 11 days - **COMPLETED**
- Phase 2: 8 days - **COMPLETED** (with some deferred items)
- Phase 3: 8 days - **COMPLETED**
- Phase 4: 13 days - **COMPLETED**
- Phase 5: 11 days - **IN PROGRESS** (CLI completed, testing approach revised)
- Phase 6: 6 days - **PENDING**

## Technical Constraints

- Python 3.8+ compatibility
- Minimal external dependencies
- No sensitive data in codebase
- Cross-platform compatibility (Windows/macOS)
- Comprehensive documentation
- Clean data exports for Power BI integration
- Scalability for datasets with 40,000+ employees and 35,000+ jobs 