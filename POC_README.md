# Skill Similarity Engine POC

This document provides instructions for running the Skill Similarity Engine POC (Proof of Concept) using synthetic data.

## Overview

The POC demonstrates the complete pipeline for job similarity analysis using the Skill Similarity Engine with synthetic HRIS data. The synthetic data matches the schema of real HRIS data but contains randomly generated content.

The POC consists of:
1. A command-line tool (`main.py`) for running the analysis and generating tabular outputs
2. Comprehensive tabular outputs for Power BI analysis

## Prerequisites

- Python 3.8 or later
- PowerShell (for Windows) or bash (for Linux/macOS)
- Synthetic data files in `data/poc/` directory:
  - `HRIS_jobs.csv`
  - `HRIS_skills.csv`
  - `HRIS_job_skills.csv`

Required Python packages (installed automatically by the scripts):
- pandas
- numpy
- matplotlib
- tqdm
- multiprocessing

## Quick Start

### Using PowerShell (Windows)

The easiest way to run the POC is using PowerShell:

```powershell
# Run the analysis with default options
python main.py --skills-file data/poc/input/HRIS_skills.csv --jobs-file data/poc/input/HRIS_jobs.csv --job-skills-file data/poc/input/HRIS_job_skills.csv

# With all options
python main.py --skills-file data/poc/input/HRIS_skills.csv `
               --jobs-file data/poc/input/HRIS_jobs.csv `
               --job-skills-file data/poc/input/HRIS_job_skills.csv `
               --department "Technology" `
               --output-dir data/poc/output `
               --output-format csv `
               --tabular-only `
               --verbose
```

### Command-Line Execution

```bash
# Basic usage
python main.py --skills-file data/poc/input/HRIS_skills.csv --jobs-file data/poc/input/HRIS_jobs.csv --job-skills-file data/poc/input/HRIS_job_skills.csv

# With additional options
python main.py --skills-file data/poc/input/HRIS_skills.csv \
               --jobs-file data/poc/input/HRIS_jobs.csv \
               --job-skills-file data/poc/input/HRIS_job_skills.csv \
               --department "Technology" \
               --output-dir data/poc/output \
               --verbose
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
| `--no-visualizations` | Skip generating visualizations (default: True) |
| `--tabular-only` | Generate only tabular data for Power BI (default: True) |
| `--batch-size` | Batch size for processing departments (default: 5) |
| `--memory-efficient` | Use memory-efficient mode for large datasets (default: False) |
| `--chunk-size` | Chunk size for reading large files (default: 100000) |
| `--verbose` | Enable verbose logging (optional) |

## Performance Options

For large datasets, consider these performance options:

| Argument | Description |
|----------|-------------|
| `--num-processes` | Number of processes to use for parallel processing (default: number of CPU cores) |
| `--memory-efficient` | Reduce memory usage at the cost of processing speed |
| `--chunk-size` | Size of chunks when reading large CSV files |
| `--batch-size` | Number of departments to process in each batch |

## Output Files

After running the analysis, the following files will be created in a timestamped output directory (e.g., `poc_run_20250404_134436`):

### Similarity Matrices
- `job_similarity_all_departments.csv`: Complete similarity matrix in tabular format for all jobs
- `job_similarity_{department}.csv`: Similarity matrix for each department (with sanitized department names)

### Job Skills Data
- `job_skills/{department}/skills_{job_id}.csv`: Individual job skills for each job, organized by department

### Statistics
- `summary_statistics.csv`: Statistical summary of all similarity scores and opportunities
- `department_statistics.csv`: Department-specific statistics

## Using the Results with Power BI

The tabular outputs are designed for seamless import into Power BI for analysis:

1. **Job similarity analysis**: Connect to the `job_similarity_all_departments.csv` file in Power BI
2. **Department filtering**: Use Power BI's filtering to focus on specific departments
3. **Job skills exploration**: Import the job skills CSVs to examine individual job skill profiles
4. **Career opportunity identification**: Use the opportunity flags to identify potential career paths

These results can be used to inform talent mobility, career pathing, and workforce planning initiatives.

## Troubleshooting

Common issues:
- **Memory errors**: Use the `--memory-efficient` flag for large datasets
- **Slow processing**: Adjust `--batch-size` and `--chunk-size` to optimize performance
- **Department name errors**: The script automatically sanitizes department names with special characters 