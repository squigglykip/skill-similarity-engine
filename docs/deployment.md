# Skill Similarity Engine - Deployment Guide

This document provides instructions for deploying the Skill Similarity Engine in a production environment, with a focus on the Job-to-Job Similarity Analysis functionality.

## Requirements

- Python 3.8+ 
- Required packages:
  - pandas
  - numpy
  - scikit-learn
  - matplotlib/seaborn (for visualizations)
  - pyyaml (for configuration)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-organization/skill-similarity-engine.git
   cd skill-similarity-engine
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package:
   ```
   pip install -e .
   ```

## Configuration

The system uses a configuration file to customize behavior. Create a `config.yaml` file in your working directory:

```yaml
# Sample configuration
app:
  output_directory: "./outputs"
  data_directory: "./data"
  log_level: "INFO"

job_matching:
  similarity_threshold: 0.7
  max_recommendations: 10

opportunity:
  high_similarity_threshold: 0.8
  low_gap_threshold: 20.0
  high_match_percentage: 80.0
  critical_gap_percentage: 50.0
```

## Usage for Job-to-Job Similarity Analysis

The primary functionality of the Skill Similarity Engine is to analyze job similarities. Here's how to use it:

### Command Line Interface

The simplest way to run the job similarity analysis is through the CLI:

```bash
# Generate a job similarity matrix
skill-similarity-engine job-similarity --job-file jobs.csv --skill-file skills.csv --output similarity_matrix.csv

# Generate job similarity with opportunity flags
skill-similarity-engine job-similarity --job-file jobs.csv --skill-file skills.csv --output similarity_matrix.csv --add-opportunity-flags
```

### Input Data Format

**Skills CSV:**
```
skill_id,skill_name,skill_category,skill_level
S001,Python,Technical,3
S002,Data Analysis,Technical,3
```

**Jobs CSV:**
```
job_id,title,department,level,skills
J001,Data Scientist,Data,Senior,"S001:3,S002:3,S003:3"
J002,Data Analyst,Data,Mid-level,"S001:2,S002:3"
```

### Using the API

For more control, you can use the API directly:

```python
from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture
from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator
import pandas as pd

# Load skills and jobs
skill_taxonomy = SkillTaxonomy()
skill_df = pd.read_csv("skills.csv")
for _, row in skill_df.iterrows():
    skill_taxonomy.add_skill(Skill(skill_id=row['skill_id'], name=row['skill_name']))

job_arch = JobArchitecture()
job_df = pd.read_csv("jobs.csv")
for _, row in job_df.iterrows():
    job = Job(job_id=row['job_id'], title=row['title'], 
              department=row['department'], level=row['level'])
    
    # Parse skills in format "S001:3,S002:4"
    if 'skills' in row and row['skills']:
        for skill_entry in row['skills'].split(','):
            if ":" in skill_entry:
                skill_id, prof = skill_entry.split(":")
                job.add_skill(skill_id, int(prof))
    
    job_arch.add_job(job)

# Calculate similarities
vectorizer = TfidfVectorizer(skill_taxonomy)
calculator = CosineSimilarityCalculator(
    vectorizer=vectorizer,
    skill_taxonomy=skill_taxonomy,
    job_architecture=job_arch
)

# Get similarity between two specific jobs
similarity = calculator.calculate_job_similarity('J001', 'J002')
print(f"Similarity between jobs: {similarity:.2f}")
```

## Integration with Power BI

To integrate with Power BI, export the similarity data:

```bash
skill-similarity-engine export-job-similarity --job-file jobs.csv --skill-file skills.csv --output similarity_data.csv --add-opportunity-flags
```

Then, in Power BI:

1. Import the exported CSV file
2. Create relationships between the job similarity data and your other job/skill tables
3. Use the opportunity flags for filtering and highlighting
4. Create visualizations using the similarity scores

## Logging

The system logs information to help with troubleshooting:

- Log files are written to the `logs` directory by default
- The log level can be configured in `config.yaml`
- For production, consider setting up log rotation

## Performance Considerations

- The system uses TF-IDF vectorization which is lightweight and performs well even with large datasets
- Memory usage scales with the number of skills and jobs
- For very large datasets (over 35,000 jobs), consider:
  - Running the analysis in batches by department/job family
  - Using a machine with more RAM for the analysis
  - Using the department filtering options to reduce the size of the matrices

## Troubleshooting

Common issues:

1. **Memory errors**: Reduce the size of the dataset or increase available memory
2. **Missing skills**: Check that all skill IDs referenced in jobs exist in the skill taxonomy
3. **Output format issues**: Verify input data formats match the expected format

## Security Considerations

- Ensure that sensitive data (like employee IDs) is anonymized or properly secured
- Restrict access to the output files containing similarity data
- Consider encrypting data if it contains sensitive information

## Updates and Maintenance

To update the system:

1. Pull the latest changes from the repository
2. Update dependencies: `pip install -e .`
3. Run tests to ensure everything works: `python -m unittest discover tests`

For any issues or feature requests, please contact the development team. 