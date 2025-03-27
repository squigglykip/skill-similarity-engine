# Synthetic Data Generation for Skill Similarity Engine

This directory contains scripts to generate and analyze synthetic data for large-scale testing of the skill similarity engine.

## Overview

The synthetic data generator creates realistic datasets with configurable numbers of:
- Skills (default: 2,500)
- Jobs (default: 32,000)
- Employees (default: 39,000)

The data is designed to have realistic distributions and relationships:
- Departments have imbalanced sizes (like real organisations)
- Job levels follow a hierarchical distribution (more junior roles than senior)
- Skills are distributed across categories with realistic patterns
- Job requirements match department and level expectations
- Employee skills correlate with job requirements with appropriate variation

### Pay Scale Area and Similarity Calculation

The synthetic data uses **Pay Scale Area** (PSA) instead of individual skill proficiency levels, matching NAB's HRIS data structure. This approach:

- Assigns each job a Pay Scale Area (PSA1-PSA6) based on seniority
- Employees inherit the Pay Scale Area from their job
- Skills are stored as binary attributes (present/absent) rather than with proficiency levels
- Similarity calculations are adjusted based on Pay Scale Area differences:
  - Jobs with similar PSA levels maintain their calculated similarity
  - Jobs with distant PSA levels (e.g., PSA1 vs PSA6) have reduced similarity scores
  - This prevents suggesting high similarity between junior and senior roles even if skill lists match

This approach ensures that career progression paths make sense hierarchically and that similarity scores reflect not just skill overlap but also appropriate seniority levels.

## Generating Synthetic Data

To generate synthetic data with default settings:
W
```bash
python generate_synthetic_data.py
```

By default, this will:
1. Use the sample data in `../data/sample` as a template
2. Generate the synthetic dataset matching NAB's scale
3. Save the data to `../data/synthetic`

### Customizing Data Generation

You can customize the data generation with these parameters:

```bash
python generate_synthetic_data.py --skills 1000 --jobs 5000 --employees 10000 --output ../data/custom
```

Parameters:
- `--skills`: Number of skills to generate
- `--jobs`: Number of jobs to generate
- `--employees`: Number of employees to generate
- `--output`: Directory to save the generated data
- `--sample-data`: Directory containing sample data templates

## Analyzing Synthetic Data

After generating the data, you can analyze it with the analysis script:

```bash
python run_synthetic_analysis.py --data-dir ../data/synthetic
```

This will:
1. Load the synthetic data
2. Run performance tests and similarity calculations
3. Generate visualizations for the largest departments
4. Save analysis results to `../data/synthetic/analysis`

### Performance Testing with Subsets

For initial testing, you can sample a subset of the data:

```bash
python run_synthetic_analysis.py --data-dir ../data/synthetic --sample-jobs 1000 --sample-employees 5000
```

Parameters:
- `--data-dir`: Directory containing the synthetic data
- `--output-dir`: Directory to save analysis results
- `--sample-jobs`: Analyze only a subset of jobs
- `--sample-employees`: Include only a subset of employees

## Using With Existing Functional Tests

The synthetic data can also be used with the functional tests:

```bash
cd ..
python -m tests.functional.test_large_scale_performance --data-dir ./data/synthetic
```

## Data Format

The generated data follows the same format as the sample data:

- `skills.csv` and `skills.json`: Skill definitions
- `jobs.csv` and `jobs.json`: Job definitions with skill requirements
- `employees.csv` and `employees.json`: Employee data with skills and job assignments
- `stats.json`: Statistics about the generated dataset

## Performance Considerations

The full 39,000 employee dataset is large and may require significant memory and processing time. Start with smaller samples when testing, especially on machines with limited resources. 