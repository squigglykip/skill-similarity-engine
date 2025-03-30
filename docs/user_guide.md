# Skill Similarity Engine: User Guide

> **Note on Flowcharts**: If this document contains Mermaid flowcharts which may not render correctly in all markdown viewers. To view any diagrams:
> 1. Use a Mermaid-compatible markdown viewer (VS Code with Markdown Preview Mermaid extension, GitHub, GitLab, etc.)
> 2. Or paste the Mermaid code into the [Mermaid Live Editor](https://mermaid.live)
> 3. Or convert the markdown to HTML/PDF with a tool that supports Mermaid

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation & Setup](#installation--setup)
3. [Data Preparation](#data-preparation)
4. [Configuration](#configuration)
5. [Common Workflows](#common-workflows)
6. [CLI Reference](#cli-reference)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Usage](#advanced-usage)

## Getting Started

The Skill Similarity Engine is a command-line tool that analyzes job roles based on their skill requirements. This guide will help you set up and use the engine effectively for your talent management needs.

### Prerequisites

- Python 3.8 or higher
- Pip package manager
- Minimum 8GB RAM (16GB recommended for large datasets)
- Windows, macOS, or Linux operating system

### Quick Start

For those familiar with Python applications, here's a quick start guide:

```bash
# Clone the repository (if not already done)
git clone https://github.com/your-org/skill-similarity-engine.git
cd skill-similarity-engine

# Install dependencies
pip install -r requirements.txt

# Generate a configuration file
python scripts/skillsim.py generate-config config.yaml

# Run basic similarity analysis
python scripts/skillsim.py -c config.yaml job-similarity data/skills.csv data/jobs.csv
```

## Installation & Setup

### Standard Installation

1. **Clone or download the repository**:
   ```bash
   git clone https://github.com/your-org/skill-similarity-engine.git
   cd skill-similarity-engine
   ```

2. **Create a virtual environment** (optional but recommended):
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**:
   ```bash
   python scripts/skillsim.py version
   ```

### NAB Internal Setup

For NAB employees, an alternative setup process is available:

1. **Request access** to the NAB GitHub repository
2. **Clone the repository** to your local machine:
   ```bash
   git clone https://github.nab.com.au/P&C/skill-similarity-engine.git
   cd skill-similarity-engine
   ```
3. **Follow the same steps** for virtual environment and dependency installation

### Project Structure Setup

For regular usage, we recommend creating a dedicated project structure:

```
nab-skill-analysis/
├── config/
│   └── config.yaml        # Your configuration
├── data/
│   ├── skills.csv         # Skill taxonomy
│   └── jobs.csv           # Job architecture
├── output/                # Analysis results
└── scripts/               # Copy or symlink from repository
```

## Data Preparation

The engine requires two main data inputs:

### 1. Skill Taxonomy

A taxonomy of skills with their properties:

#### CSV Format:
```csv
skill_id,name,category,difficulty
S001,Python,Technical,3
S002,Data Analysis,Technical,4
S003,Project Management,Methodology,3
```

#### Required Fields:
- `skill_id`: Unique identifier for each skill
- `name`: Skill name
- `category`: Categorization (Technical, Soft, Domain, etc.)

#### Optional Fields:
- `difficulty`: Numeric rating of skill acquisition difficulty (1-5)
- `description`: Text description of the skill
- `aliases`: Alternative names for the same skill

### 2. Job Architecture

A collection of job roles with their required skills:

#### CSV Format:
```csv
job_id,title,department,level,skills,location,role_track
J001,Data Analyst,Analytics,Mid-Level,"S001:4;S002:5;S006:3",Melbourne,IC
J002,Data Scientist,Analytics,Senior,"S001:5;S002:5;S004:4",Sydney,IC
J003,Analytics Manager,Analytics,Manager,"S002:4;S003:5;S007:4",Melbourne,Leadership
```

#### Required Fields:
- `job_id`: Unique identifier for each job
- `title`: Job title
- `skills`: List of required skills with proficiency levels (format: `skill_id:proficiency;skill_id:proficiency`)

#### Optional Fields:
- `department`: Business unit or department
- `level`: Seniority level (used for enhancement)
- `location`: Geographic location (used for enhancement)
- `role_track`: IC or Leadership (used for enhancement)

### Data Conversion

If your data is in a different format (Excel, JSON, etc.), you may need to convert it:

```bash
# Convert Excel to CSV
python scripts/convert_data.py --input data/skills.xlsx --output data/skills.csv --type skills

# Convert JSON to CSV
python scripts/convert_data.py --input data/jobs.json --output data/jobs.csv --type jobs
```

## Configuration

The engine uses a YAML configuration file to control its behavior. Generate a default configuration with:

```bash
python scripts/skillsim.py generate-config config.yaml
```

### Core Configuration Areas

```yaml
# Main configuration settings
version: "0.1.0"
data_dir: "./data"
output_dir: "./output"

# Normalization settings
normalisation:
  min_max_scaling: true
  boolean_normalisation: false
  tfidf_weighting: true

# Similarity calculation settings
similarity:
  method: "cosine"
  threshold: 0.7
  top_n_results: 10

# Enhancement factors
future_extensions:
  seniority_weight: 0.5
  role_track_weight: 0.3
  location_weight: 0.7
```

### Enhancement Factor Configuration

The `future_extensions` section controls the additional factors beyond skills:

```yaml
future_extensions:
  # Weight factors (0.0 = disabled, 1.0 = maximum influence)
  seniority_weight: 0.5
  role_track_weight: 0.3
  location_weight: 0.7
  
  # Seniority similarity settings
  seniority_same_level_similarity: 1.0
  seniority_one_up_similarity: 0.7
  seniority_one_down_similarity: 0.1
  
  # Role track settings
  role_track_same_similarity: 1.0
  role_track_different_similarity: 0.5
  
  # Location settings
  location_same_similarity: 1.0
  location_different_similarity: 0.3
```

### NAB-Recommended Settings

For NAB-specific usage, we recommend these initial settings:

```yaml
future_extensions:
  # Enable all enhancements
  seniority_weight: 0.8
  role_track_weight: 0.4
  location_weight: 0.6
  
  # Seniority: favor upward progression
  seniority_one_up_similarity: 0.8
  seniority_up_step_penalty: 0.15
  
  # Location: strict for Melbourne/Sydney separation
  location_different_similarity: 0.1
```

## Common Workflows

### 1. Basic Job Similarity Analysis

Calculate similarity between all jobs:

```bash
python scripts/skillsim.py -c config.yaml job-similarity data/skills.csv data/jobs.csv
```

This produces:
- `output/job_similarity_matrix.csv`: Complete similarity matrix
- `output/job_similarity_pairs.csv`: Pairwise similarities above threshold

### 2. Department-Specific Analysis

Focus on a specific department:

```bash
python scripts/skillsim.py -c config.yaml job-similarity data/skills.csv data/jobs.csv --department "Technology"
```

### 3. Enhanced Similarity with Location

Activate location-based similarity:

```bash
python scripts/skillsim.py -c config.yaml job-similarity data/skills.csv data/jobs.csv --location-weight 0.7
```

### 4. Career Pathways Analysis

Generate potential career progression paths:

```bash
python scripts/skillsim.py -c config.yaml career-paths data/skills.csv data/jobs.csv --reference-job "J001" --max-steps 3
```

This creates a visualization of possible career paths from the specified job.

### 5. Skill Gap Analysis

Analyze skill gaps between specific jobs:

```bash
python scripts/skillsim.py -c config.yaml skill-gap data/skills.csv data/jobs.csv --source-job "J001" --target-job "J008"
```

### 6. Export for Power BI

Generate files optimized for Power BI:

```bash
python scripts/skillsim.py -c config.yaml export-for-powerbi data/skills.csv data/jobs.csv --output-dir "powerbi_data"
```

## CLI Reference

### Main Commands

- `version`: Display version information
- `generate-config`: Create a configuration template
- `job-similarity`: Calculate job-to-job similarities
- `skill-gap`: Analyze skill differences between jobs
- `career-paths`: Generate career progression options
- `export-for-powerbi`: Create Power BI-compatible outputs

### Common Options

Options available for most commands:

- `-c, --config`: Path to configuration file
- `-o, --output-dir`: Directory for output files
- `--verbose/--quiet`: Control output verbosity
- `--department`: Filter jobs by department
- `--threshold`: Minimum similarity threshold (0.0-1.0)

### Enhancement Options

Options for controlling enhancement factors:

- `--seniority-weight`: Weight for seniority (0.0-1.0)
- `--role-track-weight`: Weight for role track (0.0-1.0)
- `--location-weight`: Weight for location (0.0-1.0)

## Troubleshooting

### Common Issues

#### "File not found" errors

**Problem**: The engine can't find your data files.
**Solution**: Check file paths and use absolute paths if necessary:

```bash
python scripts/skillsim.py -c config.yaml job-similarity "C:/Path/To/skills.csv" "C:/Path/To/jobs.csv"
```

#### Memory errors

**Problem**: The engine runs out of memory with large datasets.
**Solution**: Filter by department or use batch processing:

```bash
python scripts/skillsim.py -c config.yaml job-similarity data/skills.csv data/jobs.csv --department "Technology" --batch-size 1000
```

#### Unexpected similarity scores

**Problem**: Similarity scores are higher or lower than expected.
**Solution**: Check enhancement weights and adjust configuration:

```bash
python scripts/skillsim.py -c config.yaml job-similarity data/skills.csv data/jobs.csv --seniority-weight 0.3 --location-weight 0.0
```

### Getting Help

For detailed help on any command:

```bash
python scripts/skillsim.py <command> --help
```

## Advanced Usage

### Batch Processing

For very large datasets, use batch processing:

```bash
python scripts/skillsim.py -c config.yaml batch-process data/skills.csv data/jobs.csv --departments "Technology,Finance,Marketing"
```

### Custom Enhancement Factors

Create a specialized configuration file for custom enhancement factors:

```yaml
# custom_factors.yaml
future_extensions:
  # Custom weights
  seniority_weight: 0.7
  role_track_weight: 0.4
  location_weight: 0.8
  
  # Custom seniority model
  seniority_same_level_similarity: 1.0
  seniority_one_up_similarity: 0.9
  seniority_two_up_similarity: 0.5
  seniority_three_plus_up_similarity: 0.1
  seniority_down_similarity: 0.0
  
  # Custom location model for NAB offices
  location_same_building_similarity: 1.0
  location_same_city_similarity: 0.8
  location_different_city_similarity: 0.1
```

Use it with:

```bash
python scripts/skillsim.py -c custom_factors.yaml job-similarity data/skills.csv data/jobs.csv
```

### Scheduling Regular Runs

Create a batch file for regular execution:

```batch
@echo off
REM skill_analysis.bat
cd C:\Path\To\skill-similarity-engine
call venv\Scripts\activate
python scripts/skillsim.py -c config.yaml job-similarity data/skills.csv data/jobs.csv --output-dir "output_%date:~-4,4%%date:~-7,2%%date:~-10,2%"
```

Schedule this with Windows Task Scheduler for regular updates.

---

*For more detailed information about the engine's architecture and methodology, refer to the Technical Overview document.* 