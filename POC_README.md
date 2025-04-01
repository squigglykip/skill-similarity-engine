# Skill Similarity Engine POC

This document provides instructions for running the Skill Similarity Engine POC (Proof of Concept) using synthetic data.

## Overview

The POC demonstrates the complete pipeline for job similarity analysis using the Skill Similarity Engine with synthetic HRIS data. The synthetic data matches the schema of real HRIS data but contains randomly generated content.

The POC consists of:
1. A command-line tool (`main.py`) for running the analysis
2. A web interface (`webapp.py`) for exploring the results
3. A PowerShell helper script (`run_poc.ps1`) for easy execution

## Prerequisites

- Python 3.8 or later
- PowerShell (for Windows) or bash (for Linux/macOS)
- Synthetic data files in `data/poc/` directory:
  - `jobs_data_YYYYMMDD_HHMMSS.csv`
  - `skills_data_YYYYMMDD_HHMMSS.csv`
  - `job_skills_mapping_YYYYMMDD_HHMMSS.csv`

Required Python packages (installed automatically by the scripts):
- pandas
- numpy
- matplotlib
- seaborn
- streamlit (for the web interface)

## Quick Start

### Using the PowerShell Script (Recommended)

The easiest way to run the POC is using the PowerShell script:

```powershell
# Run the analysis
./run_poc.ps1 -Mode analysis -SkillsFile "data/poc/skills_data_20250331_175651.csv" -JobsFile "data/poc/jobs_data_20250331_175651.csv"

# Launch the web interface
./run_poc.ps1 -Mode webapp
```

Note: Replace the filenames with your actual data file paths.

### Manual Execution

#### Running the Analysis Directly

```bash
# Basic usage
python main.py --skills-file data/poc/skills_data_20250331_175651.csv --jobs-file data/poc/jobs_data_20250331_175651.csv

# With additional options
python main.py --skills-file data/poc/skills_data_20250331_175651.csv \
               --jobs-file data/poc/jobs_data_20250331_175651.csv \
               --job-skills-file data/poc/job_skills_mapping_20250331_175651.csv \
               --department "Technology" \
               --output-dir data/poc/output \
               --verbose
```

#### Starting the Web Interface

```bash
# Install Streamlit if not already installed
pip install streamlit

# Run the web app
python -m streamlit run webapp.py
```

## Command-Line Options

The `main.py` script accepts the following arguments:

| Argument | Description |
|----------|-------------|
| `--skills-file` | Path to skills data CSV (required if not using HRIS adapter) |
| `--jobs-file` | Path to jobs data CSV (required if not using HRIS adapter) |
| `--job-skills-file` | Path to job-skills mapping CSV (optional) |
| `--use-hris-adapter` | Use the HRIS adapter to transform data (optional) |
| `--config` | Path to HRIS configuration file (used if --use-hris-adapter is specified) |
| `--department` | Filter analysis by department (optional) |
| `--output-dir` | Directory for output files (default: "./data/poc/output") |
| `--output-format` | Output file format: csv, json, or excel (default: "csv") |
| `--no-visualizations` | Skip generating visualizations (optional) |
| `--verbose` | Enable verbose logging (optional) |

## Web Interface Features

The web interface provides:

1. **Overview dashboard** with key metrics and similarity distribution
2. **Job similarity heatmaps** for each department
3. **Top similar job pairs** based on similarity scores
4. **Job similarity search** to find jobs similar to a specific job
5. **Interactive filters** for departments and similarity thresholds

## Output Files

After running the analysis, the following files will be created in the output directory:

- `job_similarity_all_departments.csv`: Complete similarity matrix for all jobs
- `similarity_matrix_DEPARTMENT.csv`: Similarity matrix for each department
- `heatmap_DEPARTMENT.png`: Heatmap visualization for each department
- `summary_statistics.csv`: Statistical summary of the similarity scores

## Using the Results

The POC results demonstrate how the Skill Similarity Engine can:

1. Identify similar jobs across the organization
2. Group jobs by skill similarity
3. Calculate similarity scores between any two jobs
4. Generate visualizations for leadership presentations

These results can be used to inform talent mobility, career pathing, and workforce planning initiatives. 