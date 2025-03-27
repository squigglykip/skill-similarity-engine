# Skill Similarity Engine Data Model

This directory contains data for the skill similarity engine. The system uses a structured approach to model skills, jobs, and employees while appropriately representing career progression through Pay Scale Areas.

## Data Structure Overview

### Core Data Files

- **skills.csv** - The skill taxonomy defining all skills in the system
- **jobs.csv** - The job architecture defining all job roles and their required skills
- **employees.csv** - Employee data including current jobs and skills

### Data Directories

- **sample/** - Small example dataset for testing and development
- **synthetic/** - Larger generated dataset simulating the full scale of NAB data
- **real/** - *(Optional)* Directory for real HRIS data (not included in repository)

## Pay Scale Area Methodology

In our NAB implementation, we don't have explicit proficiency levels for skills in the HRIS data. Instead, we use the Pay Scale Area (PSA) as a proxy for seniority and implicit skill proficiency.

### Pay Scale Areas

Jobs are categorized into Pay Scale Areas representing seniority levels:

- **PSA1** - Entry level roles
- **PSA2** - Associate level roles
- **PSA3** - Mid-level roles
- **PSA4** - Senior level roles
- **PSA5** - Lead and Manager roles
- **PSA6** - Director and Executive roles

### Similarity Adjustment

When calculating similarity between jobs, we adjust scores based on PSA differences:

- Same PSA: No adjustment (100% of base similarity)
- 1 level difference: Minor adjustment (90% of base similarity)
- 2 level difference: Moderate adjustment (70% of base similarity)
- 3 level difference: Significant adjustment (50% of base similarity)
- 4+ level difference: Major adjustment (30% or less of base similarity)

This ensures that even with binary skill relationships (has/doesn't have), we account for the reality that skills at different seniority levels represent different proficiency levels.

### Career Progression Implications

This methodology produces more realistic career pathways by:

1. Favoring progression to roles 1-2 levels higher (realistic career steps)
2. Reducing similarity scores for inappropriate jumps (entry to executive)
3. Better representing the organizational structure in similarity metrics
4. Accounting for implicit proficiency without requiring explicit skill proficiency data

## Data Format Details

### skills.csv

```
skill_id,name,category,subcategory,difficulty
S001,Python Programming,Technical,Programming Languages,3
S002,SQL,Technical,Database,3
```

### jobs.csv

```
job_id,title,department,level,pay_scale_area,skills
J001,Data Analyst,Analytics,Associate,PSA2,S001,S002,S003
J002,Senior Data Analyst,Analytics,Senior,PSA4,S001,S002,S003,S004
```

### employees.csv

```
employee_id,name,current_job,pay_scale_area,skills
E001,James Smith,J001,PSA2,S001,S002,S003,S006
E002,Emily Johnson,J001,PSA2,S001,S002,S003,S005
```

## Synthetic Data Generation

For testing and development, we provide scripts to generate synthetic data matching the scale of NAB's workforce (39,000 employees, 32,000 jobs, 2,500 skills). See the [synthetic data documentation](../scripts/README_synthetic_data.md) for details on the generation process. 