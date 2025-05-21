# Test Data

This directory contains synthetic test data for unit, integration, and functional tests.

## Data Files

### HRIS Schema (Input Format)

These files follow the external HRIS schema format as defined in the schema reference:

- `hris_jobs.csv`: Contains 9 jobs across 3 departments (Engineering, Data, Marketing) with different levels and roles.
- `hris_skills.csv`: Contains 18 skills of different types (Specialized, Common, Certification) across various categories.
- `hris_job_skills.csv`: Maps jobs to skills with intentional overlaps for similarity testing.
- `hris_employees.csv`: Contains 6 employees with assigned jobs and skill proficiency levels.

### Engine Schema (Transformed Format)

These files follow the internal engine schema format:

- `jobs.csv`: Jobs data in the engine's schema format.
- `skills.csv`: Skills data in the engine's schema format (CSV version).
- `skills.json`: Skills data in the engine's schema format (JSON version).
- `employees.csv`: Employee data in the engine's schema format.

### Configuration

- `test_hris_config.yaml`: Sample HRIS adapter configuration for transforming the test data.

## Test Data Design

The test data was designed with the following considerations:

1. **Shared Skills**: Jobs within the same department have overlapping skills to ensure valid similarity calculations.
   - Engineering jobs share Python, Communication skills
   - Data jobs share SQL, Data Analysis skills
   - Marketing jobs share Communication, Digital Marketing skills

2. **Skill Type Coverage**: All skill types are included:
   - `SPECIALIZED`: Various programming and domain skills
   - `COMMON`: Soft skills like communication, leadership
   - `CERTIFICATION`: Professional certifications

3. **Hierarchy Representation**: Each department has a career progression:
   - Junior/Mid-level individual contributors
   - Senior individual contributors
   - Management roles

## Usage in Tests

### In Unit Tests

For unit tests that only test a specific component without transformation:

```python
from skill_similarity_engine.models.jobs import JobArchitecture
from skill_similarity_engine.models.skills import SkillTaxonomy

# Use the engine schema files directly
taxonomy = SkillTaxonomy.from_file("tests/test_data/skills.csv")
job_arch = JobArchitecture.from_file("tests/test_data/jobs.csv")
```

### In Integration Tests

For integration tests that verify transformation:

```python
from skill_similarity_engine.hris_adapter.transformer import HRISTransformer

# Use the HRIS schema files and transform them
transformer = HRISTransformer(config_path="tests/test_data/test_hris_config.yaml")
jobs_path, skills_path = transformer.transform()

# Then use the transformed files
taxonomy = SkillTaxonomy.from_file(skills_path)
job_arch = JobArchitecture.from_file(jobs_path)
```

## Extending the Test Data

When adding new test cases:

1. Keep ID patterns consistent (e.g., J### for jobs, S### for skills)
2. Ensure new jobs in the same department share some skills with existing jobs
3. Update both HRIS schema and engine schema files to stay in sync 