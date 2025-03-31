# HRIS Integration and Job Similarity Analysis Guide

This guide provides step-by-step instructions for integrating HRIS data with the Skill Similarity Engine and running a job-to-job similarity analysis for leadership presentation.

## Table of Contents

1. [Branch Strategy](#branch-strategy)
2. [Setting Up HRIS Data Pipeline](#setting-up-hris-data-pipeline)
3. [Running the Job Similarity Analysis](#running-the-job-similarity-analysis)
4. [Preparing Results for Leadership](#preparing-results-for-leadership)
5. [Appendix: Data Field Requirements](#appendix-data-field-requirements)

## Branch Strategy

Use the following branch structure for this work:

```
main
└── feature/hris-data-pipeline  (HRIS integration)
    └── feature/poc-similarity-run  (Proof of concept run with real data)
```

Create branches with:

```bash
# Start with HRIS integration branch
git checkout -b feature/hris-data-pipeline

# Once data pipeline is ready, create branch for POC run
git checkout -b feature/poc-similarity-run
```

## Setting Up HRIS Data Pipeline

### Step 1: Analyze HRIS Data Structure

- [x] **Analyze existing HRIS exports**
   - [x] Review column headers and data formats
   - [x] Identify key fields for job data
   - [x] Document data quality issues or gaps
   - Note: Identified three main data files: jobs_data.csv, skills_data.csv, and job_skills_mapping.csv

- [x] **Create a mapping document**
   - [x] Map HRIS fields to engine's required fields
   - [x] Define transformation rules
   - [x] Document any assumptions being made
   - Note: Created hris_schema_mapping.yaml with detailed field mappings

### Step 2: Create Data Transformation Script

- [x] **Create a new Python script for transforming HRIS data**
   ```bash
   touch skill-similarity-engine/scripts/hris_transform.py
   ```

- [x] **Implement the following functionality:**
   - Note: Created script with CLI structure and basic functionality
   - Note: Implemented data loading and transformation logic
   - Note: Added support for CSV and Excel formats

### Step 3: Create a Skills Taxonomy

- [x] **Extract unique skills from HRIS data**
   - [x] Identify all skills mentioned in job descriptions or skill requirements
   - [x] Remove duplicates and standardize terminology
   - Note: Identified 30,000 unique skills with clear categorization

- [x] **Build skills CSV file**
   ```
   skill_id,name,category,subcategory,difficulty
   S001,Python Programming,Technical,Programming Languages,3
   S002,SQL,Technical,Database,3
   ...
   ```
   - Note: Using SkillType as primary category, with Category and Subcategory for hierarchy

- [x] **Validate the taxonomy**
   - [x] Ensure all required skills are included
   - [x] Check that categorizations are consistent
   - Note: Validated against HRIS data structure

### Step 4: Map Jobs to Skills

- [x] **Create job-skill mapping logic**
   - [x] If explicit mapping exists in HRIS, use it directly
   - [x] Otherwise, develop rule-based mapping or extract from job descriptions
   - Note: Using binary skill representation (has/doesn't have)

- [x] **Update jobs with skills**
   ```python
   # Example logic for updating Job objects with skills
   for job_id, skill_list in job_skills_mapping.items():
       if job_id in job_arch.jobs:
           for skill_id in skill_list:
               job_arch.jobs[job_id].skills[skill_id] = 1  # Binary skill assignment
   ```
   - Note: Implemented binary skill assignment based on job_skills_mapping.csv

### Step 5: Test the Pipeline

- [x] **Generate synthetic data for testing**
   ```bash
   python scripts/generate_hris_synthetic_data.py
   ```
   - Note: Creates 40,000 jobs, 30,000 skills, and job-skill mappings
   - Note: Matches actual HRIS schema and data formats
   - Note: Outputs files to data/poc/ with timestamps

- [ ] **Run pipeline with sample HRIS data**
   ```bash
   python scripts/hris_transform.py transform_jobs /path/to/hris_jobs.csv data/real/
   python scripts/hris_transform.py transform_skills /path/to/hris_skills.csv data/real/
   python scripts/hris_transform.py assign_skills_to_jobs /path/to/hris_job_skills.csv data/real/jobs.csv data/real/
   ```
   - Note: Ready for testing with actual data

- [ ] **Validate outputs**
   - [ ] Check that `data/real/skills.csv` and `data/real/jobs.csv` have correct formats
   - [ ] Verify a sample of transformed records for accuracy
   - Note: Need to run with actual data to validate

## Running the Job Similarity Analysis

### Step 1: Generate Configuration

- [x] **Create a configuration file for the analysis**
   ```bash
   python -m scripts.skillsim.py config generate --output-path data/real/config.yaml
   ```
   - Note: Created and configured hris_schema_mapping.yaml

- [x] **Edit the configuration file to set appropriate values**
   ```yaml
   # Similarity settings
   similarity:
     threshold: 0.5  # Minimum similarity score to include in results
     top_n_results: 10  # Number of top matches to show for each job

   # Enhancement factors
   future_extensions:
     seniority_weight: 0.3  # Weight for seniority similarity (0.0 = disabled)
     role_track_weight: 0.1  # Weight for role track similarity (0.0 = disabled)
     location_weight: 0.0  # Weight for location similarity (0.0 = disabled)
   ```
   - Note: Configured based on HRIS data structure

### Step 2: Run Test Analysis with Department Filter

- [x] **Run analysis on synthetic data**
   ```bash
   python scripts/run_hris_synthetic_analysis.py \
       data/poc/jobs_data_YYYYMMDD_HHMMSS.csv \
       data/poc/skills_data_YYYYMMDD_HHMMSS.csv \
       data/poc/job_skills_mapping_YYYYMMDD_HHMMSS.csv \
       data/poc/output
   ```
   - Note: Generates similarity matrix and top similar jobs
   - Note: Outputs results with timestamps

- [ ] **Start with a single department to test the process**
   ```bash
   python -m scripts.run_similarity.py job_similarity \
       data/real/skills.csv \
       data/real/jobs.csv \
       --department "Technology" \
       --config-file data/real/config.yaml \
       --output-dir data/real/output
   ```
   - Note: Ready for testing with actual data

- [ ] **Examine the results and adjust parameters if needed**
   - Note: Need to run with actual data to validate

### Step 3: Run Full Analysis

- [ ] **Once satisfied with the test, run the full job similarity analysis**
   ```bash
   python -m scripts.run_similarity.py job_similarity \
       data/real/skills.csv \
       data/real/jobs.csv \
       --config-file data/real/config.yaml \
       --output-dir data/real/output
   ```
   - Note: Ready for full analysis once testing is complete

- [ ] **Or use the main CLI entry point**
   ```bash
   python -m scripts.skillsim.py run similarity \
       --skills data/real/skills.csv \
       --jobs data/real/jobs.csv \
       --config-file data/real/config.yaml \
       --output-dir data/real/output
   ```
   - Note: Ready for use once testing is complete

### Step 4: Analyze and Visualize Results

- [x] **Load similarity matrix into pandas**
   ```python
   import pandas as pd
   
   # Load the similarity matrix
   similarity_df = pd.read_csv('data/poc/output/similarity_matrix_YYYYMMDD_HHMMSS.csv', index_col=0)
   
   # View the top similar jobs for a specific job
   job_id = 'R0001'  # Replace with actual job ID
   similar_jobs = similarity_df.loc[job_id].sort_values(ascending=False)[1:11]  # Top 10 excluding self
   print(f"Top 10 similar jobs to {job_id}:")
   print(similar_jobs)
   ```
   - Note: Implemented in run_hris_synthetic_analysis.py

- [ ] **Generate basic visualizations**
   ```python
   import matplotlib.pyplot as plt
   import seaborn as sns
   
   # Create a heatmap of similarity for top jobs in a department
   dept_jobs = job_arch.filter_by_department('Technology').jobs.keys()
   dept_similarity = similarity_df.loc[dept_jobs, dept_jobs]
   
   plt.figure(figsize=(12, 10))
   sns.heatmap(dept_similarity, cmap='viridis', vmin=0, vmax=1)
   plt.title('Job Similarity Heatmap - Technology Department')
   plt.tight_layout()
   plt.savefig('data/real/output/technology_similarity_heatmap.png')
   ```
   - Note: Ready for implementation once data is available

## Preparing Results for Leadership

### Step 1: Create Summary Statistics

- [x] **Calculate summary statistics about the job similarity analysis**
   - [x] Number of jobs analyzed
   - [x] Distribution of similarity scores
   - [x] Top 10 most similar job pairs
   - [x] Potential career pathways
   - Note: Implemented in run_hris_synthetic_analysis.py

### Step 2: Prepare Visual Materials

- [ ] **Create heatmaps of job similarity by department**
- [ ] **Generate network diagrams of related jobs**
- [ ] **Produce department-level similarity summaries**
- Note: Ready for implementation once data is available

### Step 3: Document Findings and Recommendations

- [ ] **Prepare a brief document highlighting**
   - [ ] Key insights from the analysis
   - [ ] Potential applications of the results
   - [ ] Recommendations for further development
   - [ ] Technical notes on the implementation
   - Note: Ready for documentation once analysis is complete

## Appendix: Data Field Requirements

### Required Fields for Job Data

| Engine Field      | Description                              | Example HRIS Fields      | Status |
|-------------------|------------------------------------------|--------------------------|---------|
| job_id            | Unique job identifier                    | JobID                    | ✓ Mapped |
| title             | Job title                                | RoleSet                  | ✓ Mapped |
| department        | Department or business unit              | Org Unit Name            | ✓ Mapped |
| level             | Job level                                | Salary Group             | ✓ Mapped |
| pay_scale_area    | Seniority level (mapped to PSA)          | Salary Group             | ✓ Mapped |
| skills            | List of required skills                  | job_skills_mapping.csv   | ✓ Mapped |
| role_track        | IC or leadership track                   | People Leader Flag       | ✓ Mapped |
| location          | Job location (if using location factor)  | Street, Suburb, Location, Cty | ✓ Mapped |

### Required Fields for Skills Taxonomy

| Engine Field     | Description                            | Example HRIS Fields       | Status |
|------------------|----------------------------------------|---------------------------|---------|
| skill_id         | Unique skill identifier                | Skill_ID                  | ✓ Mapped |
| name             | Skill name                             | Skill_Name                | ✓ Mapped |
| category         | High-level skill category              | SkillType                 | ✓ Mapped |
| subcategory      | More specific categorization           | Category                  | ✓ Mapped |
| difficulty       | Skill difficulty rating (1-5)          | Not in scope              | ✓ Excluded | 