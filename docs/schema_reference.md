# Schema Reference Guide

This document provides a comprehensive reference for the data schemas used in the Skill Similarity Engine, including both the external HRIS schemas and the internal engine schemas.

## Overview

The Skill Similarity Engine transforms data from Human Resource Information Systems (HRIS) into a standardised internal schema. This document details both schemas and explains the transformation process.

## HRIS Schema (External)

This section outlines the expected schema for input data from HRIS systems.

### Jobs Data

| HRIS Column Name    | Data Type | Description                                       | Required |
|---------------------|-----------|---------------------------------------------------|----------|
| JobID               | String    | Unique identifier for the job                     | Yes      |
| RoleSet             | String    | Job title or role name                            | Yes      |
| Org Unit Number     | String    | Numerical identifier for the organisational unit  | No       |
| Org Unit Name       | String    | Name of the department or organisational unit     | Yes      |
| Salary Group        | String    | Salary band, level or grade (e.g., "Group 3")     | Yes      |
| People Leader Flag  | String    | Indicates if role involves people management      | No       |
| Street              | String    | Street address for job location                   | No       |
| Suburb              | String    | Suburb/district for job location                  | No       |
| Location            | String    | Office location name                              | No       |
| Cty                 | String    | City location                                     | No       |

### Skills Data

| HRIS Column Name | Data Type | Description                                       | Required |
|------------------|-----------|---------------------------------------------------|----------|
| Skill_ID         | String    | Unique identifier for the skill                   | Yes      |
| Skill_Name       | String    | Name of the skill                                 | Yes      |
| SkillType        | String    | Type of skill (e.g., "Specialized Skill")         | Yes      |
| Category         | String    | Primary category of the skill                     | No       |
| Subcategory      | String    | Subcategory for additional classification         | No       |

### Job-Skills Mapping Data

| HRIS Column Name | Data Type | Description                                       | Required |
|------------------|-----------|---------------------------------------------------|----------|
| JobID            | String    | Identifier for the job                            | Yes      |
| Skill_ID         | String    | Identifier for the skill                          | Yes      |

## Internal Engine Schema

This section details the standardised internal schema used by the Skill Similarity Engine.

### Jobs Schema

| Engine Column Name | Data Type   | Description                                   | Transformed From      |
|--------------------|-------------|-----------------------------------------------|----------------------|
| job_id             | String      | Unique identifier for the job                 | JobID                |
| title              | String      | Job title                                     | RoleSet              |
| department         | String      | Department or organisational unit             | Org Unit Name        |
| level              | Enum        | Standardised job level (e.g., "MID_LEVEL")    | Salary Group         |
| role_track         | Enum        | Track type (e.g., "INDIVIDUAL_CONTRIBUTOR")   | People Leader Flag   |
| location           | String      | Combined location information                 | Multiple fields      |
| skills             | String      | Semicolon-separated list of skills            | Job-Skills mapping   |

The `level` field uses the following enum values:
- ENTRY
- ASSOCIATE
- MID_LEVEL
- SENIOR
- LEAD
- MANAGER
- DIRECTOR
- EXECUTIVE

The `role_track` field uses the following enum values:
- INDIVIDUAL_CONTRIBUTOR
- MANAGEMENT

### Skills Schema

| Engine Column Name | Data Type | Description                                     | Transformed From |
|--------------------|-----------|------------------------------------------------|-----------------|
| skill_id           | String    | Unique identifier for the skill                 | Skill_ID        |
| name               | String    | Name of the skill                               | Skill_Name      |
| category           | Enum      | Standardised category (e.g., "SPECIALIZED")     | SkillType       |
| description        | String    | Description of the skill                        | Subcategory     |
| subcategory        | String    | Subcategory information                         | Category        |

The `category` field uses the following enum values:
- COMMON
- SPECIALIZED
- CERTIFICATION
- TECHNICAL
- SOFT

## Schema Mapping Configuration

The transformation between HRIS schema and internal schema is controlled by the `hris_schema_mapping.yaml` configuration file. This file defines:

1. **Column mappings**: Which HRIS columns map to which internal fields
2. **Value mappings**: How specific values should be transformed (e.g., "Group 3" → "MID_LEVEL")
3. **File paths**: Where input and output files are located
4. **Format options**: File format details like encoding and delimiter

Example column mapping:
```yaml
jobs_mapping:
  job_id: "JobID"
  title: "RoleSet"
  department: "Org Unit Name"
  level: "Salary Group"
```

Example value mapping:
```yaml
salary_group_mapping:
  "Group 1": 
    level: "ENTRY"
    psa: "ENTRY"
  "Group 3":
    level: "MID_LEVEL"
    psa: "MIDRANGE"
```

## Schema Transformation Process

The transformation process:

1. Loads HRIS data from configured input files
2. Maps each column from HRIS schema to internal schema 
3. Transforms values using configured mappings
4. Applies job-skills relationships
5. Saves the transformed data to output files

During this process, strict schema separation is maintained to ensure HRIS vendor-specific schemas do not leak into the Skill Similarity Engine's standardised internal schema.

## Common Issues and Troubleshooting

When integrating with a new HRIS system, common schema-related issues include:

1. **Missing required columns**: Ensure all required HRIS columns are present
2. **Unexpected data types**: Validate data types match expectations
3. **Missing mappings**: Verify all required mappings are defined in the configuration
4. **Value transformation errors**: Check that all possible values in categorised fields have mappings

## Extending the Schema

To extend the schema for additional HRIS systems:

1. Update the `hris_schema_mapping.yaml` with new column mappings
2. Add any additional value mappings required
3. Test the transformation with sample data
4. Update transformation functions if custom logic is needed 