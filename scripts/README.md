# Skill Similarity Engine Scripts

This directory contains scripts for running the Skill Similarity Engine.

## Available Scripts

- **skillsim.py**: Main CLI interface for the Skill Similarity Engine
- **run_similarity.py**: Run various similarity analyses (job-to-job, employee-to-job, etc.)
- **visualize.py**: Create visualizations of similarity results
- **generate_reports.py**: Generate reports and summaries from similarity results
- **hris_transform.py**: Transform HRIS data into formats compatible with the Skill Similarity Engine

## Usage

### Main CLI Interface

```bash
python skillsim.py --help
```

See the [CLI Documentation](../docs/user_guide.md) for more details.

### Similarity Analysis

```bash
python run_similarity.py jobs-to-jobs --config-file path/to/config.yaml
```

See the [Similarity Analysis Documentation](../docs/practical_applications.md) for more details.

### Visualization

```bash
python visualize.py heatmap --similarity-matrix path/to/matrix.csv --output path/to/output.png
```

### HRIS Data Transformation

Transform your organisation's HRIS data into formats compatible with the Skill Similarity Engine:

```bash
# Transform all data
python hris_transform.py transform-all

# Transform with a custom configuration
python hris_transform.py --config-file path/to/custom_mapping.yaml transform-all

# Transform just jobs
python hris_transform.py transform-jobs

# Transform just skills
python hris_transform.py transform-skills

# Assign skills to jobs
python hris_transform.py assign-skills
```

For detailed information about HRIS integration, see the [HRIS Integration Guide](../docs/hris_integration.md).

## Examples

Example command sequences for common use cases:

### Full Workflow

```bash
# Transform HRIS data
python hris_transform.py transform-all

# Run job-to-job similarity analysis
python run_similarity.py jobs-to-jobs

# Generate reports
python generate_reports.py job-similarity-report

# Visualize results
python visualize.py heatmap --similarity-matrix outputs/job_similarity_matrix.csv
```

### Department-Specific Analysis

```bash
# Run analysis for a specific department
python run_similarity.py jobs-to-jobs --department "Technology"

# Visualize department-specific results
python visualize.py heatmap --similarity-matrix outputs/Technology_similarity_matrix.csv
```

## Development

To add a new script:

1. Create a new Python file in this directory
2. Follow the pattern of existing scripts, using Click for CLI interfaces
3. Update this README to document the new script 