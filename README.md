# Skill Similarity Engine - Project Plan

## Overview

This document outlines the development plan for the NAB Skill Similarity Engine, a system designed to analyse skill similarities between jobs and employees to identify reskilling opportunities. The project will be implemented in phases, with each phase corresponding to a specific git branch.

> **IMPLEMENTATION FOCUS**: The current implementation focuses primarily on **Job-to-Job Similarity Analysis**. This approach aligns with our available data and integration with Power BI for visualisation and reporting. The system generates standardised outputs that feed into relationship models in Power BI, enabling job similarity analysis, career pathway identification, and skill gap analysis between roles.

> **Power BI Integration**: Rather than developing extensive built-in reporting and visualisation capabilities, we've designed the system to output optimised data formats that integrate seamlessly with Power BI's relationship models. This gives analysts maximum flexibility while maintaining a focused codebase.

## Development Branches

We will use the following branch structure:
- `main` - Production-ready code
- `develop` - Integration branch for feature branches
- Feature branches - Named according to the feature being implemented

## Phase 1: Core Framework

**Branch: `feature/core-framework`**

### 1.1 Project Setup (1 day)
- [x] Create project structure
- [ ] Set up development environment
- [ ] Define initial dependencies in requirements.txt
- [ ] Configure pyproject.toml

### 1.2 Data Models (3 days)
- [ ] Implement `models/skills.py` for skill taxonomy representation
- [ ] Implement `models/jobs.py` for job architecture representation
- [ ] Implement `models/employees.py` for employee data representation
- [ ] Add type annotations and proper documentation

### 1.3 Configuration System (2 days)
- [ ] Implement `config/settings.py` for application configuration
- [ ] Create YAML/JSON configuration parsers
- [ ] Implement configuration validation
- [ ] Add support for environment-specific configurations

### 1.4 Data Normalisation (3 days)
- [ ] Implement min-max scaling in `data/normalisers.py`
- [ ] Implement boolean normalisation
- [ ] Implement TF-IDF style weighting for rare vs. common skills
- [ ] Implement configurable importance weights

### 1.5 Data Loaders (2 days)
- [ ] Implement CSV data loaders in `data/loaders.py`
- [ ] Implement Excel data loaders
- [ ] Add data validation and error handling
- [ ] Create sample data files for testing

## Phase 2: Similarity Engine

**Branch: `feature/similarity-engine`**

### 2.1 Vector Representation (3 days)
- [ ] Implement vector representation for skills in `analysis/vectors.py`
- [ ] Add support for different vectorisation strategies
- [ ] Implement dimensionality reduction techniques (optional)
- [ ] Create utility functions for vector manipulation

### 2.2 Similarity Calculation (3 days)
- [ ] Implement cosine similarity in `analysis/similarity.py`
- [ ] Implement Euclidean distance
- [ ] Implement Jaccard similarity
- [ ] Add threshold configuration options

### 2.3 Similarity Matrix Generation (2 days)
- [ ] Implement job-to-job similarity matrix generation
- [ ] *(FUTURE DEVELOPMENT)* Implement person-to-job similarity matrix generation
- [ ] *(FUTURE DEVELOPMENT)* Implement person-to-person similarity matrix generation
- [ ] Add performance optimisations for large datasets

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
- [ ] *(FUTURE DEVELOPMENT)* Implement network graph generation in `visualization/networks.py`
- [ ] *(FUTURE DEVELOPMENT)* Add options for different graph layouts
- [ ] *(FUTURE DEVELOPMENT)* Implement filtering and highlighting
- [ ] *(FUTURE DEVELOPMENT)* Add interactive elements (if applicable)

### 4.4 Workforce Planning Reports (3 days)
- [ ] Implement aggregate reporting functionality
- [ ] Create skills gap analysis at organisational level
- [ ] *(FUTURE DEVELOPMENT)* Add department/team level reporting
- [ ] *(FUTURE DEVELOPMENT)* Implement future state modelling

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

Total estimated time: 49 working days (~10 weeks)
- Phase 1: 11 days
- Phase 2: 8 days
- Phase 3: 8 days
- Phase 4: 10 days
- Phase 5: 12 days

## Technical Constraints

- Python 3.8+ compatibility
- Minimal external dependencies
- No sensitive data in codebase
- Cross-platform compatibility (Windows/macOS)
- Comprehensive documentation
- Optimised data exports for Power BI consumption 
- Support for "Prescribe Skills" model with job-to-job analysis as primary focus 