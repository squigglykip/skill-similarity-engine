# Skill Similarity Engine CLI Scripts

This directory contains command-line interface (CLI) scripts for the Skill Similarity Engine.

## Overview

- `skillsim.py`: Main entry point that provides access to all commands
- `run_similarity.py`: Commands for calculating similarity between jobs and employees
- `generate_reports.py`: Commands for generating reports and data exports
- `help_docs.py`: Script to generate comprehensive CLI documentation

## Installation

When the package is installed, these scripts are available as the following commands:

- `skillsim`: Main command with all functionality
- `skill-similarity`: Focused on similarity calculations
- `skill-reports`: Focused on report generation

## Usage

### Quick Start

To get started with the CLI, run:

```bash
# Display help information
python scripts/skillsim.py --help

# Generate a configuration template
python scripts/skillsim.py generate-config config.yaml

# Calculate job similarities
python scripts/skillsim.py job-similarity data/skill_taxonomy.csv data/job_architecture.csv

# Generate skill gap analysis
python scripts/skillsim.py skill-gap-analysis data/skill_taxonomy.csv data/job_architecture.csv data/employee_database.csv
```

### Working with Large Datasets

For large datasets, we recommend filtering by department and using appropriate thresholds:

```bash
python scripts/skillsim.py job-similarity-export data/skill_taxonomy.csv data/job_architecture.csv --department "Finance"
```

### Documentation

To generate comprehensive CLI documentation, run:

```bash
python scripts/help_docs.py
```

This will create a markdown file `docs/cli_documentation.md` with detailed usage instructions.

## Examples

For detailed examples, see the [CLI Examples](../docs/cli_examples.md) documentation. 