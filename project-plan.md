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
- [ ] Implement Euclidean distance
- [ ] Implement Jaccard similarity
- [x] Add threshold configuration options

### 2.3 Similarity Matrix Generation (2 days)
- [x] Implement job-to-job similarity matrix generation
- [x] Implement person-to-job similarity matrix generation
- [x] Implement person-to-person similarity matrix generation
- [x] Add performance optimisations for large datasets

## Phase 3: Gap Analysis

**Branch: `feature/gap-analysis`**

### 3.1 Skill Gap Identification (3 days)
- [ ] Implement skill gap identification in `analysis/gap.py`
- [ ] Identify present skills vs. needed skills
- [ ] Identify excess skills (skills not needed in target role)
- [ ] Create comprehensive gap reports

### 3.2 Development Effort Calculation (2 days)
- [ ] Implement development effort scoring
- [ ] Factor in skill difficulty levels
- [ ] Add configurable weighting for different skill categories
- [ ] Create prioritised development plans

### 3.3 Reskilling Pathway Generation (3 days)
- [ ] Implement reskilling pathway algorithms
- [ ] Add support for multi-step career transitions
- [ ] Implement optimal path finding for skill development
- [ ] Create pathway visualisation data structures

## Phase 4: Reporting & Visualisation

**Branch: `feature/reporting-visualization`**

### 4.1 Basic Reporting (2 days)
- [ ] Implement DataFrame export functionality
- [ ] Add CSV export capabilities
- [ ] Add JSON export capabilities
- [ ] Implement report configuration options

### 4.2 Heatmap Visualisation (2 days)
- [ ] Implement heatmap generation in `visualization/heatmaps.py`
- [ ] Add customisation options for heatmap appearance
- [ ] Create interactive heatmaps (if applicable)
- [ ] Add clustering options for better visualisation

### 4.3 Network Graph Visualisation (3 days)
- [ ] Implement network graph generation in `visualization/networks.py`
- [ ] Add options for different graph layouts
- [ ] Implement filtering and highlighting
- [ ] Add interactive elements (if applicable)

### 4.4 Workforce Planning Reports (3 days)
- [ ] Implement aggregate reporting functionality
- [ ] Create skills gap analysis at organisational level
- [ ] Add department/team level reporting
- [ ] Implement future state modelling

## Phase 5: CLI & Testing

**Branch: `feature/cli-testing`**

### 5.1 Command Line Interface (3 days)
- [ ] Create CLI framework in `scripts/`
- [ ] Implement commands for all major functionalities
- [ ] Add configuration options via CLI
- [ ] Create comprehensive help documentation

### 5.2 Unit Testing (4 days)
- [ ] Implement unit tests for data models
- [ ] Implement unit tests for similarity calculations
- [ ] Implement unit tests for gap analysis
- [ ] Implement unit tests for visualisation components

### 5.3 Integration Testing (3 days)
- [ ] Create integration tests for end-to-end workflows
- [ ] Test with various data volumes and structures
- [ ] Implement performance testing
- [ ] Create CI/CD pipeline (if applicable)

### 5.4 Documentation & Examples (2 days)
- [ ] Complete all docstrings and type annotations
- [ ] Update README with comprehensive usage instructions
- [ ] Create Jupyter notebook examples
- [ ] Add sample data and configuration files

## Phase 6: Data Transformation Scripts

**Branch: `feature/data-transformation`**

### 6.1 Input Data Transformation (2 days)
- [ ] Create transformation scripts for converting tabular skill data to condensed format
- [ ] Implement mapping from raw HRIS data to the required skills structure
- [ ] Add validation and error reporting for data transformation
- [ ] Create logging and monitoring for transformation processes

### 6.2 Batch Processing Tools (2 days)
- [ ] Implement batch processing for large datasets
- [ ] Add support for incremental updates
- [ ] Create backup/restore functionality
- [ ] Implement scheduling options for regular data refreshes

### 6.3 Data Quality Checks (1 day)
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
- pyyaml (configuration)
- pytest (testing)
- click (CLI interface)

## Timeline

Total estimated time: 54 working days (~11 weeks)
- Phase 1: 11 days
- Phase 2: 8 days
- Phase 3: 8 days
- Phase 4: 10 days
- Phase 5: 12 days
- Phase 6: 5 days

## Technical Constraints

- Python 3.8+ compatibility
- Minimal external dependencies
- No sensitive data in codebase
- Cross-platform compatibility (Windows/macOS)
- Comprehensive documentation 