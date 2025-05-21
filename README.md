# Skill Similarity Engine

## Overview

This document outlines the development plan for the NAB Skill Similarity Engine, a system designed to analyse skill similarities between jobs and employees to identify reskilling opportunities. The project is implemented in phases, with each phase corresponding to a specific git branch.

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

We use the following branch structure:
- `main` - Production-ready code
- `develop` - Integration branch for feature branches
- Feature branches - Named according to the feature being implemented

## Phases

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

#### 2.3 Similarity Matrix Generation
- [x] Implement job-to-job similarity matrix generation
- [x] *(FUTURE DEVELOPMENT)* Implement person-to-job similarity matrix generation
- [x] *(FUTURE DEVELOPMENT)* Implement person-to-person similarity matrix generation
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
- [ ] *(FUTURE DEVELOPMENT)* Add department/team level reporting
- [ ] *(FUTURE DEVELOPMENT)* Implement future state modelling

### Phase 5: CLI & Testing - **IN PROGRESS**
**Branch: `feature/cli-testing`**

#### 5.1 Command Line Interface - **COMPLETED**
- [x] Create CLI framework in `scripts/`
- [x] Implement commands for most important functionalities
- [x] Add configuration options via CLI
- [x] Create comprehensive help documentation

#### 5.2 Unit Testing
- [x] Test CLI scripts with sample data
- [x] Verify data loading and validation
- [x] Test similarity calculations with small datasets
- [x] Test export functionality and file generation
- [x] Validate job similarity scores against manually calculated examples
- [ ] Implement unit tests for data models
- [ ] Create data quality validation framework

#### 5.3 Integration Testing
- [x] Test end-to-end workflows with realistic data volumes
- [x] Verify department filtering functionality
- [x] Test configuration overrides and custom settings
- [x] Validate CSV export format standards for Power BI integration
- [ ] Create integration tests for end-to-end workflows
- [ ] Test with various data volumes and structures
- [ ] Implement performance testing
- [ ] Create CI/CD pipeline (if applicable)

#### 5.4 Documentation & Examples
- [x] Complete all docstrings and type annotations
- [x] Update README with comprehensive usage instructions
- [x] Create Jupyter notebook examples
- [x] Add sample data and configuration files

## Dependencies

The following dependencies are used:
- pandas (data manipulation)
- numpy (numerical operations)
- scikit-learn (similarity metrics, dimensionality reduction)
- matplotlib/seaborn (visualisation)
- pyyaml (configuration)
- pytest (testing)
- click (CLI interface)

## Technical Constraints

- Python 3.8+ compatibility
- Minimal external dependencies
- No sensitive data in codebase
- Cross-platform compatibility (Windows/macOS)
- Comprehensive documentation
- Optimised data exports for Power BI consumption 
- Support for "Prescribe Skills" model with job-to-job analysis as primary focus 

# Configuration

The Skill Similarity Engine uses a flexible configuration system that supports different environments:

- **Development**: Default development settings
- **Testing**: Settings optimized for testing
- **Production**: Settings optimized for production use

## Using Configuration

To use the configuration system in your code:

```python
from skill_similarity_engine.config.settings import load_config_for_environment, get_config

# Load configuration (defaults to the environment in default.yaml)
load_config_for_environment("path/to/config/dir")

# Or for a specific environment
load_config_for_environment("path/to/config/dir", "production")

# Access configuration
config = get_config()
threshold = config.similarity.threshold
```

## Environment Variables

You can override any configuration setting using environment variables:

```bash
# Override data directory
export SSE_DATA_DIR="/custom/data/path"

# Override similarity threshold
export SSE_SIMILARITY_THRESHOLD="0.75"
```

## Configuration Files

The configuration is stored in YAML files with a hierarchy:

1. `default.yaml` - Default values for all settings
2. `[environment].yaml` - Environment-specific overrides
3. `local.yaml` - Local overrides (not checked into git)

See the `config/README.md` file for details on the configuration structure. 