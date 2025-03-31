# HRIS Integration Example

This directory contains example files demonstrating how to transform data from a Human Resource Information System (HRIS) into the format required by the Skill Similarity Engine.

## Example Files

### HRIS Source Data

- **job_data.csv**: Example job data from an HRIS system
  - Contains 15 sample job records with fields like job code, title, department, level, pay band, track, location, and active status
  - Represents a cross-section of different departments and seniority levels

- **skills_data.csv**: Example skill data from an HRIS system
  - Contains 20 sample skills across technical, business, design, and soft skill categories
  - Includes skill difficulty levels and categorisation

- **job_skills_mapping.csv**: Example job-to-skill mapping data
  - Maps which skills are required for which jobs
  - Includes proficiency levels on a 1-5 scale

### Configuration

- **hris_schema_mapping.yaml**: Example configuration file for transforming the HRIS data
  - Defines the mapping between HRIS data fields and engine required fields
  - Contains value mappings for job levels, pay scales, role tracks, and proficiency levels
  - Includes transformation options and logging settings

## Using the Example

This example demonstrates a typical HRIS integration workflow.

### 1. Copy the Configuration

```bash
mkdir -p config
cp examples/hris_example/hris_schema_mapping.yaml config/
```

### 2. Update the Configuration (if needed)

Edit the configuration file to match your actual environment:

```bash
# Open the configuration file in your text editor
nano config/hris_schema_mapping.yaml

# Adjust file paths, column mappings, and value mappings as needed
```

### 3. Run the Transformation

```bash
# Transform all data (jobs, skills, and job-skill mappings)
python scripts/hris_transform.py --config-file config/hris_schema_mapping.yaml transform-all

# Or transform specific components
python scripts/hris_transform.py --config-file config/hris_schema_mapping.yaml transform-jobs
python scripts/hris_transform.py --config-file config/hris_schema_mapping.yaml transform-skills
python scripts/hris_transform.py --config-file config/hris_schema_mapping.yaml assign-skills
```

### 4. Verify the Results

Check that the transformation created the expected output files:

```bash
# View the transformed job data
head data/jobs.csv

# View the transformed skill data
head data/skills.csv

# Check the mapping report
head logs/hris_mapping_report.csv
```

## Customising for Your HRIS

To adapt this example for your own HRIS data:

1. **Understand Your HRIS Data Structure**:
   - Identify which tables/exports contain job information
   - Identify which tables/exports contain skill information
   - Identify how jobs and skills are connected in your HRIS

2. **Map Your HRIS Fields**:
   - Update the column mappings in the configuration file
   - Create value mappings for your HRIS-specific values

3. **Configure File Paths**:
   - Update the input file paths to point to your HRIS data exports
   - Set appropriate output paths for the transformed data

4. **Test and Iterate**:
   - Run the transformation with a small subset of data
   - Verify the output accuracy
   - Refine the configuration as needed

For complete documentation on HRIS integration, see the [HRIS Integration Guide](../../docs/hris_integration.md). 