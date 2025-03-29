# Skill Similarity Engine - Project Plan

## Overview

This document outlines the development plan for the NAB Skill Similarity Engine, a system designed to analyse skill similarities between jobs and employees to identify reskilling opportunities. The project will be implemented in phases, with each phase corresponding to a specific git branch.

> **IMPLEMENTATION FOCUS**: Based on current organisational data constraints, the primary focus is on **Job-to-Job Similarity Analysis**. Our implementation concentrates on generating high-quality job similarity matrices and related outputs optimised for Power BI integration. Employee-to-job and employee-to-employee analyses are deprioritised until individual skill data becomes available. This approach aligns with the "Prescribe Skills" paradigm where job definitions drive skill assignments.

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

#### 4.2 Heatmap Visualisation
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
- [ ] Test incremental updates to job architecture data
- [ ] Test refresh cycles with incremental job updates
- [ ] Document integration patterns for future reference
- [ ] Complete remaining unit tests for models and data components
- [ ] Create test workflows for the full job-to-job similarity pipeline
- [ ] Implement tests for validating input data quality
- [ ] Create tests for verifying output data consistency
- [ ] Add tests for error handling with malformed input data

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

### Phase 6: Data Pipeline & Integration - **IN PROGRESS**
**Branch: `feature/data-pipeline`**

#### 6.1 Data Export Optimisation - **COMPLETED**
- [x] Create standardised data export formats
- [x] Implement efficient data serialisation
- [x] Add metadata and schema descriptions in exports
- [x] Ensure exports are optimised for downstream consumption
- [x] Validate CSV formats meet Power BI integration requirements

#### 6.2 Configuration Management System - **COMPLETED**
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

#### 6.3 Skill Affinity Analyzer Enhancement - **IN PROGRESS**
**Branch: `feature/similarity-enhancements`**

> **Enhancement Focus**: Implement additional variables beyond skills that affect job similarity: seniority, role track (IC vs. Leadership), and location. These enhancements will provide more nuanced similarity calculations for improved job matching and career pathway recommendations.

##### 6.3.1 Enhanced Configuration System - **COMPLETED**
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

##### 6.3.2 Project Rationale and Benefits

The inclusion of these additional variables goes beyond a simplistic skills-only approach to job similarity calculations, delivering several key benefits:

1. **More Realistic Career Pathways**: By factoring in seniority levels, we can avoid suggesting unrealistic jumps from junior to senior positions, creating more achievable career progression options.

2. **Role-Appropriate Transitions**: Distinguishing between Individual Contributor (IC) and Leadership roles allows identification of natural progression paths (IC → Senior IC → Leadership) while avoiding less common regressions (Leadership → IC).

3. **Geographic Practicality**: By considering location in similarity scores, we can prioritize transitions that don't require relocation, making recommendations more practical for employees.

4. **Flexible Implementation**: The weighted approach allows organizations to tune the importance of each variable based on their specific needs and priorities.

5. **Incremental Adoption**: Variables can be initially disabled (weight=0) and gradually introduced as the organization becomes comfortable with the enhanced model.

##### 6.3.3 Test-Driven Development Approach
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

##### 6.3.4 Seniority Implementation
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

##### 6.3.5 Role Track Implementation
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
- [ ] Develop unit and integration tests
  - [ ] Test transitions within same track
  - [ ] Test transitions across tracks
  - [ ] Test compatibility with seniority calculations

The role track implementation acknowledges that career progression typically follows patterns where Individual Contributors may progress to Leadership roles, but transitions in the opposite direction are less common. All role track similarity thresholds are now configurable, allowing organisations to adjust the system to their specific career paths and progression policies.

##### 6.3.6 Location Implementation
- [x] Add location attributes to job data model
  - [x] Create flexible schema supporting different location specificity (suburb/city/state/country)
  - [x] Implement geocoding capabilities (optional enhancement)
  - [x] Design normalisation for inconsistent address formats
- [x] Develop location similarity algorithm
  - [x] Implement exact matching for same location
  - [x] Create proximity scoring for nearby locations
  - [x] Add distance-based scoring for remote locations
  - [x] Handle special cases like remote work and multiple locations
- [x] Make location comparison fully configurable
  - [x] Move location similarity thresholds to configuration system
  - [x] Allow adjustment of same-location vs different-location similarities
- [ ] Implement test suite
  - [ ] Test exact location matches
  - [ ] Test proximity-based matching
  - [ ] Test handling of incomplete or missing location data

The location implementation recognizes that geographic proximity significantly affects job transition practicality. By incorporating configurable location similarity thresholds, we can prioritize transitions that don't require relocation while still showing non-local opportunities at lower similarity scores when appropriate. The configuration system enables fine-tuning of these parameters without code changes.

##### 6.3.7 Variable Integration Framework
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

##### 6.3.8 CLI Integration and User Experience
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

##### 6.3.9 Integration Tests & Documentation
- [ ] Test combined operation of all three variables
  - [ ] Create comprehensive test scenarios
  - [ ] Develop test data with complete variable coverage
  - [ ] Implement performance testing for enhanced calculations
- [ ] Update documentation
  - [ ] Create detailed reference for each variable
  - [ ] Document integration patterns and best practices
  - [ ] Provide configuration templates for common scenarios
- [ ] Develop validation framework
  - [ ] Create tools to measure improvement in similarity accuracy
  - [ ] Implement A/B comparison with skills-only approach
  - [ ] Design metrics for evaluating enhancement impacts

#### 6.4 HRIS Data Integration
- [ ] Develop HRIS data translation layer to standardise naming conventions
- [ ] Create mapping dictionaries between HRIS job codes and internal architecture
- [ ] Implement field normalisation for inconsistent data formats
- [ ] Build data validation to catch anomalies in HRIS exports
- [ ] Create detailed documentation of all HRIS-to-internal mappings
- [ ] Develop incremental update workflow for job architecture changes
- [ ] Implement configurable refresh schedules for HRIS data synchronisation
- [ ] Design error handling and notification process for translation failures
- [ ] Implement mapping from raw HRIS data to the required skills structure
- [ ] Focus on scalability for large dataset processing

#### 6.5 Power BI Integration
- [ ] Finalise data schema documentation for Power BI developers
- [ ] Create reference relationship models for Power BI implementation
- [ ] Develop sample DAX measures for common analyses
- [ ] Document refresh and update procedures
- [ ] Create user guide for working with exported data in Power BI

#### 6.6 Production Deployment Preparation
- [ ] Create deployment documentation
- [ ] Implement logging for production environments
- [ ] Add configuration templates for different environments
- [ ] Create backup and recovery procedures
- [ ] Establish workflow for environment promotion
- [ ] Develop version tagging and release notes process
- [ ] Create user feedback collection mechanism
- [ ] Implement rollback mechanisms for failed deployments

#### 6.7 Real-World Data Testing
- [ ] Perform complete end-to-end testing with real HRIS data
- [ ] Create validation reports comparing outputs with expected results
- [ ] Validate memory usage and performance with full-scale data
- [ ] Conduct usability testing with intended end users
- [ ] Gather feedback and implement necessary refinements
- [ ] Document any remaining data quality issues or constraints
- [ ] Finalise implementation recommendations based on testing results

### Phase 7: Interactive CLI Implementation - **PLANNED**
**Branch: `feature/interactive-cli`**

#### 7.1 Interactive CLI Framework
- [ ] Create interactive CLI module structure
- [ ] Implement welcome screen and main flow sequence
- [ ] Add styled console output with rich library
- [ ] Set up questionary/PyInquirer for interactive prompts

#### 7.2 User Flow Implementation
- [ ] Build analysis type selection interface
- [ ] Implement input file selection with validation
- [ ] Create output preferences configuration flow
- [ ] Develop analysis parameters selection screens
- [ ] Add summary confirmation before proceeding with analysis

#### 7.3 Progress Tracking
- [ ] Implement progress bars for time-consuming operations
- [ ] Add spinners for operations without percentage completion
- [ ] Include elapsed time indicators for long-running processes
- [ ] Create step-by-step progress indicators

#### 7.4 Integration with Core Analysis
- [ ] Connect interactive CLI to existing analysis functions
- [ ] Ensure proper data flow between CLI and core functionality
- [ ] Implement progress tracking hooks in core analysis code
- [ ] Add thorough error handling and validation

#### 7.5 Testing and Polish
- [ ] Create test cases for interactive CLI
- [ ] Test with various input conditions and edge cases
- [ ] Polish user experience and refine error messages
- [ ] Add comprehensive help documentation

#### 7.6 Documentation and Examples
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
- Phase 5: 11 days - **IN PROGRESS** (CLI completed, core testing completed, documentation in progress)
- Phase 6: 15 days - **IN PROGRESS** (unified configuration, HRIS integration, similarity enhancements, and Power BI support)
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
2. Vectorises job skill profiles using TF-IDF 
3. Calculates cosine similarity between job pairs with high performance
4. Handles realistic job volumes and skill taxonomies
5. Produces clean outputs ready for Power BI integration

Remaining work is primarily focused on:
1. **Testing** - Completing additional test cases to ensure robustness and reliability
2. **Production Readiness** - Implementing logging, error handling, and deployment documentation
3. **Integration** - Finalising HRIS data mappings and Power BI integration patterns
4. **Data Quality** - Implementing data validation and quality checks
5. **Similarity Enhancements** - Adding seniority, role track, and location variables to improve similarity calculations
6. **Documentation** - Completing comprehensive guides for system usage and integration

With these final pieces in place, the system will be fully production-ready and positioned to deliver significant value through job similarity analysis and skill gap identification. The focus on Job-to-Job similarity provides immediate value while establishing a foundation for future employee-centric analyses once individual skill data becomes available.
