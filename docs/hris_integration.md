# HRIS Integration Guide

This guide explains how to integrate your organisation's Human Resource Information System (HRIS) data with the Skill Similarity Engine. The integration process involves mapping your HRIS data schema to the engine's required format and running a transformation script to convert the data.

## Table of Contents

- [HRIS Integration Guide](#hris-integration-guide)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Data Requirements](#data-requirements)
    - [1. Job Architecture Data](#1-job-architecture-data)
    - [2. Skills Data](#2-skills-data)
    - [3. Job-Skills Mapping Data](#3-job-skills-mapping-data)
  - [Schema Mapping Configuration](#schema-mapping-configuration)
  - [Transformation Process](#transformation-process)
  - [Running the Transformation](#running-the-transformation)
  - [Schema Separation Principles](#schema-separation-principles)
    - [Key Separation Points](#key-separation-points)
    - [Maintaining Separation](#maintaining-separation)
  - [Testing the Integration](#testing-the-integration)
    - [Unit Testing](#unit-testing)
    - [Integration Testing](#integration-testing)
  - [Validating Results](#validating-results)
    - [Schema Validation](#schema-validation)
  - [Advanced Configuration](#advanced-configuration)
    - [Value Mappings](#value-mappings)
    - [Text Processing](#text-processing)
    - [Binary Skills Representation](#binary-skills-representation)
  - [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
    - [Logging](#logging)
    - [Getting Help](#getting-help)

## Overview

The Skill Similarity Engine requires specific data formats to perform its analysis. This guide helps you transform your organisation's HRIS data into these required formats. The core components involved in this process are:

1. **HRIS Schema Mapping Configuration**: A YAML file that defines how your HRIS data maps to the engine's required format
2. **Transformation Script**: A Python script that reads your HRIS data and the mapping configuration to produce the required files
3. **Example Data**: Sample files demonstrating the expected format for both input and output

The transformation process maintains a strict separation between your HRIS naming conventions and the engine's internal schema, ensuring that engine functions only work with standardized field names and value formats regardless of the source HRIS system.

## Data Requirements

The Skill Similarity Engine requires two main data components:

### 1. Job Architecture Data

This data describes job roles within your organisation and requires at minimum:

- **Job ID**: A unique identifier for each job role
- **Job Title**: The title or name of the job role
- **Department**: The department or function the job belongs to
- **Level**: The seniority level of the job (mapped to engine's JobLevel enum)

Optional but valuable fields include:

- **Pay Scale Area**: Salary band or remuneration category
- **Role Track**: Career track (e.g., Technical, Management, Individual Contributor)
- **Location**: Geographic location of the job
- **Active Status**: Whether the job is currently active

### 2. Skills Data

This data describes the skills used within your organisation and requires at minimum:

- **Skill ID**: A unique identifier for each skill
- **Skill Name**: The name or description of the skill

Optional but valuable fields include:

- **Category**: Broad category the skill belongs to (e.g., Technical, Business)
- **Subcategory**: More specific categorisation within the parent category
- **Difficulty**: Rating of skill complexity (1-5 scale)

### 3. Job-Skills Mapping Data

This data maps which skills are required for which jobs and requires at minimum:

- **Job ID**: Reference to the job
- **Skill ID**: Reference to the skill

Optional but valuable fields include:

- **Proficiency Level**: Required proficiency level for the skill (1-5 scale)

## Schema Mapping Configuration

The schema mapping is defined in a YAML configuration file that specifies:

1. **File Paths**: Locations of source HRIS data files and destination output files
2. **Column Mappings**: How column names in your HRIS data map to required fields
3. **Value Mappings**: How values in your HRIS data map to required values (e.g., job levels)
4. **Transformation Options**: Settings to control the transformation process

Here's an example snippet of a mapping configuration:

```yaml
jobs_mapping:
  # Required fields
  job_id: "position_id"
  title: "job_name"
  department: "business_unit"
  level: "job_grade"
  
  # Optional fields
  pay_scale_area: "salary_band"
  role_track: "career_stream"
  location: "office_location"
  active: "is_current"

job_level_mapping:
  "Grade 1": "ENTRY"
  "Grade 2": "ASSOCIATE"
  "Grade 3": "PROFESSIONAL"
  "Grade 4": "SENIOR"
  "Grade 5": "PRINCIPAL"
  "Grade 6": "EXECUTIVE"
```

A complete example configuration file is provided at `examples/hris_example/hris_schema_mapping.yaml`.

## Transformation Process

The transformation process consists of these steps:

1. **Load Configuration**: Read the mapping configuration
2. **Transform Jobs**: Convert HRIS job data to engine's format
3. **Transform Skills**: Convert HRIS skill data to engine's format
4. **Assign Skills to Jobs**: Link skills to jobs based on the mapping data
5. **Generate Reports**: Create logs and reports of the transformation

During transformation, the script performs these key tasks:

- Maps column names from HRIS format to engine format
- Converts value representations (e.g., job levels, proficiency ratings)
- Validates data integrity and relationships
- Applies default values for missing data
- Creates properly formatted output files

## Running the Transformation

To transform your HRIS data, use the `hris_transform.py` script:

```bash
# Navigate to the project root
cd skill-similarity-engine

# Transform all data using default configuration
python scripts/hris_transform.py transform-all

# Transform all data with a specific configuration file
python scripts/hris_transform.py --config-file path/to/my_config.yaml transform-all

# Transform only job data
python scripts/hris_transform.py transform-jobs

# Transform only skill data
python scripts/hris_transform.py transform-skills

# Assign skills to jobs after jobs and skills are transformed
python scripts/hris_transform.py assign-skills
```

## Schema Separation Principles

A key design principle of the HRIS integration is maintaining a clear separation between your HRIS schema and the engine's internal schema. This separation provides several benefits:

1. **Adaptability**: The engine can work with data from any HRIS system without code changes
2. **Stability**: Changes to the HRIS data format don't affect the engine's core functionality
3. **Maintainability**: Each component has a clear responsibility with well-defined interfaces
4. **Testability**: Components can be tested in isolation with mock data

### Key Separation Points

1. **Configuration-Driven Mapping**: All schema transformations are defined in configuration, not code
2. **Complete Transformation Before Processing**: HRIS data is fully transformed before reaching engine components
3. **Validation at Boundaries**: Data is validated when it crosses from HRIS format to engine format
4. **No HRIS Schema Dependencies**: Engine code never has direct dependencies on HRIS field names or values

### Maintaining Separation

When working with the HRIS adapter, observe these guidelines:

1. **Never modify engine code to accommodate HRIS formats** - Update the mapping configuration instead
2. **Don't leak HRIS naming conventions into the engine** - Complete all transformations before passing data
3. **Keep transformation logic in the adapter** - Don't duplicate it in engine components
4. **Use the adapter's API, not its implementation** - Interact through documented interfaces

## Testing the Integration

Testing the HRIS integration consists of two main aspects:

1. **Unit Testing**: Verifying that the transformation components work correctly
2. **Integration Testing**: Ensuring transformed data works with the engine

### Unit Testing

Run unit tests specifically for the HRIS adapter:

```bash
# Run all HRIS adapter unit tests
python -m pytest tests/unit/hris_adapter -v

# Run specific test categories
python -m pytest tests/unit/hris_adapter/test_config.py -v
python -m pytest tests/unit/hris_adapter/test_transformer.py -v
python -m pytest tests/unit/hris_adapter/test_workflow.py -v
```

These tests verify that:
- Configuration loading works correctly
- Transformation rules are applied as expected
- Edge cases are handled properly
- Value mappings produce the correct results

### Integration Testing

Test the complete integration workflow:

```bash
# Run full integration tests
python -m pytest tests/integration/test_hris_integration.py -v

# Test with sample data
python -m pytest tests/integration/test_hris_sample_data.py -v
```

These tests verify that:
- Transformed data can be loaded by engine components
- Engine functions produce correct results with transformed data
- End-to-end workflows complete successfully

## Validating Results

After transformation, you should verify that:

1. The output files exist at the specified locations
2. The output files contain the expected number of records
3. Sample records have been transformed correctly
4. Any mapping reports show expected transformations
5. Schema has been properly standardized to the engine's format

Use these commands to check the output files:

```bash
# View transformed jobs
head data/jobs.csv

# View transformed skills
head data/skills.csv

# Check record counts
wc -l data/jobs.csv
wc -l data/skills.csv

# Check mapping report if enabled
head logs/hris_mapping_report.csv

# Run schema validation
python scripts/validate_schema.py data/jobs.csv jobs
python scripts/validate_schema.py data/skills.csv skills
```

### Schema Validation

The schema validation tool checks that transformed data adheres to the engine's schema requirements:

- Field names follow the standard convention
- Required fields are present
- Field formats are correct (e.g., job levels use the correct enum values)
- Relationships between records are valid

## Advanced Configuration

### Value Mappings

The configuration supports complex value mappings for various fields:

- **Job Level Mapping**: Maps HRIS job grades to engine's JobLevel enum
- **Pay Scale Mapping**: Maps HRIS pay scales to engine's categorisation
- **Role Track Mapping**: Maps HRIS tracks to engine's RoleTrack enum
- **Proficiency Mapping**: Maps HRIS proficiency descriptions to 1-5 numeric scale

### Text Processing

The engine can extract skills from text descriptions (experimental feature):

```yaml
text_processing:
  extract_skills_from_text: true
  extract_from_fields: ["job_description", "responsibilities"]
  min_confidence: 0.7
```

### Binary Skills Representation

If your HRIS doesn't include proficiency levels, you can use binary skill representation:

```yaml
transformation_options:
  use_binary_skills: true
```

## Troubleshooting

### Common Issues

1. **File Not Found Errors**
   - Verify that the input file paths in the configuration are correct
   - Ensure the directories exist and have appropriate permissions

2. **Mapping Errors**
   - Check that column names in the configuration match your HRIS data
   - Verify that the value mappings cover all possible values in your data

3. **Missing Required Fields**
   - Ensure all required fields have mappings in the configuration
   - Check if default values are properly defined for missing data

4. **Transformation Errors**
   - Enable detailed logging: `logging.level: "DEBUG"`
   - Check the mapping report for unexpected transformations

5. **Schema Validation Failures**
   - Verify that your value mappings produce valid enum values
   - Check that field types are consistent with engine expectations
   - Ensure that relationship fields (IDs) are consistent across datasets

### Logging

Detailed logs can help diagnose issues:

```yaml
logging:
  level: "DEBUG"
  log_details: true
  save_mapping_report: true
  mapping_report_path: "logs/hris_mapping_report.csv"
```

### Getting Help

If you encounter persistent issues:

1. Check the example files to understand the expected format
2. Review the transformation script for implementation details
3. Run the unit tests to verify adapter functionality
4. Contact support with your configuration file and error logs 