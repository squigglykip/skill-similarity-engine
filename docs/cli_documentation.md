# Skill Similarity Engine CLI Documentation

This document provides comprehensive documentation for the command-line interface of the Skill Similarity Engine.

## Main Command

```
Usage: skillsim [OPTIONS] COMMAND [ARGS]...

  Skill Similarity Engine - Workforce Analytics Tool.

  This tool provides functionality for analyzing skill similarities between
  jobs and employees, identifying reskilling opportunities, and generating
  reports for workforce planning.

Options:
  -c, --config PATH      Path to configuration file (YAML or JSON)
  -o, --output-dir PATH  Directory for output files
  --verbose / --quiet    Enable/disable verbose output
  --help                 Show this message and exit.

Commands:
  config                      Configuration management commands.
  employee-job-similarity     Calculate employee-to-job similarity scores.
  employee-similarity         Calculate employee-to-employee similarity...
  employee-similarity-export  Export employee similarity data for Power...
  generate-config             Generate a configuration file template.
  job-similarity              Calculate job-to-job similarity scores.
  job-similarity-export       Export job similarity data for Power BI...
  skill-gap-analysis          Generate skill gap analysis reports.
  version                     Display the version information for the...
  workforce-planning-export   Export workforce planning data for Power BI...

```

# Commands

## skillsim job-similarity

```
Usage: skillsim job-similarity [OPTIONS] SKILL_TAXONOMY_FILE
                               JOB_ARCHITECTURE_FILE

  Calculate job-to-job similarity scores.

  This command loads the skill taxonomy and job architecture data, and
  calculates similarity scores between pairs of jobs based on their skill
  profiles.

Options:
  --department TEXT           Filter jobs by department
  --top-n INTEGER             Number of top similar jobs to return
  --threshold FLOAT           Similarity threshold (0.0-1.0)
  --cluster / --no-cluster    Whether to cluster similar jobs together
  --output-format [csv|json]  Output file format
  --output-dir PATH           Directory for output files
  --help                      Show this message and exit.

```

### Options

- `--department`: Filter jobs by department
- `--top-n`: Number of top similar jobs to return
- `--threshold`: Similarity threshold (0.0-1.0)
- `--cluster`: Whether to cluster similar jobs together
- `--output-format`: Output file format
- `--output-dir`: Directory for output files

## skillsim employee-job-similarity

```
Usage: skillsim employee-job-similarity [OPTIONS] SKILL_TAXONOMY_FILE
                                        JOB_ARCHITECTURE_FILE
                                        EMPLOYEE_DATABASE_FILE

  Calculate employee-to-job similarity scores.

  This command loads the skill taxonomy, job architecture, and employee data,
  and calculates how well each employee matches with different jobs based on
  their skill profiles.

Options:
  --department TEXT           Filter by department
  --top-n INTEGER             Number of top similar matches to return
  --threshold FLOAT           Similarity threshold (0.0-1.0)
  --output-format [csv|json]  Output file format
  --output-dir PATH           Directory for output files
  --help                      Show this message and exit.

```

### Options

- `--department`: Filter by department
- `--top-n`: Number of top similar matches to return
- `--threshold`: Similarity threshold (0.0-1.0)
- `--output-format`: Output file format
- `--output-dir`: Directory for output files

## skillsim employee-similarity

```
Usage: skillsim employee-similarity [OPTIONS] SKILL_TAXONOMY_FILE
                                    EMPLOYEE_DATABASE_FILE

  Calculate employee-to-employee similarity scores.

  This command loads the skill taxonomy and employee data, and calculates
  similarity scores between pairs of employees based on their skill profiles.

Options:
  --department TEXT           Filter employees by department
  --top-n INTEGER             Number of top similar employees to return
  --threshold FLOAT           Similarity threshold (0.0-1.0)
  --output-format [csv|json]  Output file format
  --output-dir PATH           Directory for output files
  --help                      Show this message and exit.

```

### Options

- `--department`: Filter employees by department
- `--top-n`: Number of top similar employees to return
- `--threshold`: Similarity threshold (0.0-1.0)
- `--output-format`: Output file format
- `--output-dir`: Directory for output files

## skillsim skill-gap-analysis

```
Usage: skillsim skill-gap-analysis [OPTIONS] SKILL_TAXONOMY_FILE
                                   JOB_ARCHITECTURE_FILE
                                   EMPLOYEE_DATABASE_FILE

  Generate skill gap analysis reports.

  This command analyzes the gap between current employee skills and target job
  requirements. It can analyze a specific employee against a specific job, or
  generate a comprehensive report of employees against potential target roles.

Options:
  --employee-id TEXT              ID of the employee to analyze
  --target-job-id TEXT            ID of the target job to analyze
  --department TEXT               Filter by department
  --add-opportunity-flags / --no-opportunity-flags
                                  Whether to add opportunity flags to the
                                  output
  --output-format [csv|json|excel]
                                  Output file format
  --help                          Show this message and exit.

```

### Options

- `--employee-id`: ID of the employee to analyze
- `--target-job-id`: ID of the target job to analyze
- `--department`: Filter by department
- `--add-opportunity-flags`: Whether to add opportunity flags to the output
- `--output-format`: Output file format

## skillsim job-similarity-export

```
Usage: skillsim job-similarity-export [OPTIONS] SKILL_TAXONOMY_FILE
                                      JOB_ARCHITECTURE_FILE

  Export job similarity data for Power BI integration.

  This command generates a structured export of job similarity data optimised
  for Power BI consumption, including metadata and opportunity flags.

Options:
  --department TEXT               Filter by department
  --add-opportunity-flags / --no-opportunity-flags
                                  Whether to add opportunity flags to the
                                  output
  --output-format [csv|json|excel]
                                  Output file format
  --help                          Show this message and exit.

```

### Options

- `--department`: Filter by department
- `--add-opportunity-flags`: Whether to add opportunity flags to the output
- `--output-format`: Output file format

## skillsim employee-similarity-export

```
Usage: skillsim employee-similarity-export [OPTIONS] SKILL_TAXONOMY_FILE
                                           JOB_ARCHITECTURE_FILE
                                           EMPLOYEE_DATABASE_FILE

  Export employee similarity data for Power BI integration.

  This command generates a structured export of employee similarity data
  optimised for Power BI consumption, including metadata and opportunity
  flags.

Options:
  --department TEXT               Filter by department
  --add-opportunity-flags / --no-opportunity-flags
                                  Whether to add opportunity flags to the
                                  output
  --output-format [csv|json|excel]
                                  Output file format
  --help                          Show this message and exit.

```

### Options

- `--department`: Filter by department
- `--add-opportunity-flags`: Whether to add opportunity flags to the output
- `--output-format`: Output file format

## skillsim workforce-planning-export

```
Usage: skillsim workforce-planning-export [OPTIONS] SKILL_TAXONOMY_FILE
                                          JOB_ARCHITECTURE_FILE

  Export workforce planning data for Power BI integration.

  This command generates a structured export of workforce planning data,
  including skill demand across jobs, optimised for Power BI consumption.

Options:
  --department TEXT               Filter jobs by department
  --add-opportunity-flags / --no-opportunity-flags
                                  Whether to add opportunity flags to the
                                  output
  --output-format [csv|json|excel]
                                  Output file format
  --help                          Show this message and exit.

```

### Options

- `--department`: Filter jobs by department
- `--add-opportunity-flags`: Whether to add opportunity flags to the output
- `--output-format`: Output file format

## skillsim config

```
Usage: skillsim config [OPTIONS] COMMAND [ARGS]...

  Configuration management commands.

Options:
  --help  Show this message and exit.

Commands:
  init  Initialize a configuration file at the specified path.
  view  View the current configuration.

```

### Options


## skillsim generate-config

```
Usage: skillsim generate-config [OPTIONS] [OUTPUT_FILE]

  Generate a configuration file template.

  This command creates a template configuration file with default settings
  that can be customized for specific use cases.

Options:
  --output-format [yaml|json]  Output format for the configuration template
  --help                       Show this message and exit.

```

### Options

- `--output-format`: Output format for the configuration template

## skillsim version

```
Usage: skillsim version [OPTIONS]

  Display the version information for the Skill Similarity Engine.

Options:
  --help  Show this message and exit.

```

### Options


