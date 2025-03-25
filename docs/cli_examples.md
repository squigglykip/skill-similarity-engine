# Skill Similarity Engine CLI Examples

This document provides examples of common usage patterns for the Skill Similarity Engine CLI.

## Setup and Configuration

### Generating a Default Configuration

To generate a default configuration file in YAML format:

```bash
skillsim generate-config config.yaml
```

For JSON format:

```bash
skillsim generate-config --output-format json config.json
```

### Checking Version

To check the version of the installed package:

```bash
skillsim version
```

## Basic Similarity Calculations

### Job-to-Job Similarity

Calculate similarity between jobs in the job architecture:

```bash
skillsim job-similarity data/skill_taxonomy.csv data/job_architecture.csv
```

Filter by department:

```bash
skillsim job-similarity data/skill_taxonomy.csv data/job_architecture.csv --department "Finance"
```

Specify similarity threshold and top N results:

```bash
skillsim job-similarity data/skill_taxonomy.csv data/job_architecture.csv --threshold 0.7 --top-n 10
```

### Employee-to-Job Similarity

Calculate similarity between employees and jobs:

```bash
skillsim employee-job-similarity data/skill_taxonomy.csv data/job_architecture.csv data/employee_database.csv
```

Filter by department:

```bash
skillsim employee-job-similarity data/skill_taxonomy.csv data/job_architecture.csv data/employee_database.csv --department "IT"
```

### Employee-to-Employee Similarity

Calculate similarity between employees:

```bash
skillsim employee-similarity data/skill_taxonomy.csv data/employee_database.csv
```

Output in JSON format:

```bash
skillsim employee-similarity data/skill_taxonomy.csv data/employee_database.csv --output-format json
```

## Advanced Reporting

### Skill Gap Analysis

Generate comprehensive skill gap analysis:

```bash
skillsim skill-gap-analysis data/skill_taxonomy.csv data/job_architecture.csv data/employee_database.csv
```

Analyze specific employee against specific job:

```bash
skillsim skill-gap-analysis data/skill_taxonomy.csv data/job_architecture.csv data/employee_database.csv --employee-id "E12345" --target-job-id "J67890"
```

Output in Excel format:

```bash
skillsim skill-gap-analysis data/skill_taxonomy.csv data/job_architecture.csv data/employee_database.csv --output-format excel
```

### Workforce Planning

Generate workforce planning data for Power BI:

```bash
skillsim workforce-planning-export data/skill_taxonomy.csv data/job_architecture.csv
```

### Optimised Exports for Power BI

Export job similarity data with opportunity flags:

```bash
skillsim job-similarity-export data/skill_taxonomy.csv data/job_architecture.csv
```

Export employee similarity data:

```bash
skillsim employee-similarity-export data/skill_taxonomy.csv data/job_architecture.csv data/employee_database.csv
```

Disable opportunity flags:

```bash
skillsim job-similarity-export data/skill_taxonomy.csv data/job_architecture.csv --no-opportunity-flags
```

## Processing Large Datasets

For large datasets, it's recommended to filter by department or other criteria:

```bash
skillsim job-similarity-export data/skill_taxonomy.csv data/job_architecture.csv --department "Finance" --output-dir "output/finance_analysis"
```

## Scripting and Batch Processing

The CLI is designed to be used in scripts. Here's an example bash script to process multiple departments:

```bash
#!/bin/bash

DEPARTMENTS=("Finance" "IT" "HR" "Marketing" "Operations")
OUTPUT_BASE="output/department_analysis"

for dept in "${DEPARTMENTS[@]}"; do
  echo "Processing $dept department..."
  
  # Create department-specific output directory
  mkdir -p "$OUTPUT_BASE/$dept"
  
  # Run similarity and gap analysis
  skillsim job-similarity-export data/skill_taxonomy.csv data/job_architecture.csv \
    --department "$dept" \
    --output-dir "$OUTPUT_BASE/$dept"
    
  skillsim skill-gap-analysis data/skill_taxonomy.csv data/job_architecture.csv data/employee_database.csv \
    --department "$dept" \
    --output-dir "$OUTPUT_BASE/$dept" \
    --output-format excel
    
  echo "Completed processing for $dept"
done

echo "All departments processed successfully"
```

## Using Configuration Files

Create a configuration file `config.yaml`:

```yaml
environment: production
data_dir: /path/to/data
output_dir: /path/to/output
similarity:
  method: cosine
  threshold: 0.75
  top_n_results: 10
gap_analysis:
  min_proficiency_ratio: 0.7
  skill_difficulty_factor: 1.2
opportunity:
  high_similarity_threshold: 0.85
  low_gap_threshold: 15.0
```

Then use it with any command:

```bash
skillsim job-similarity data/skill_taxonomy.csv data/job_architecture.csv --config-file config.yaml
``` 