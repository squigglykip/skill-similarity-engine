# Skill Similarity Engine

## Overview

The Skill Similarity Engine is a scalable analytics system for analysing and comparing job roles based on their skill requirements. Its primary goal is to identify reskilling and mobility opportunities within large organisations, with outputs optimised for integration with Power BI and other analytics tools.

## Main Features

- **Job-to-Job Similarity Analysis:** Generates a comprehensive, cross-department similarity dataset for all jobs, supporting data-driven workforce planning and career mobility insights.
- **Skill Gap Analysis:** Identifies missing and surplus skills between roles, supporting targeted development planning.
- **Power BI Integration:** Outputs are structured for easy import and analysis in Power BI, supporting interactive dashboards and reporting.
- **Configurable Processing:** YAML-based configuration system supports environment-specific settings and local overrides.
- **Memory and Performance Optimisation:** Designed to handle tens of thousands of jobs and skills efficiently, with precomputation, chunking, and parallel processing for large-scale data.

## Current Focus

- **Precompute Architecture:** The engine precomputes all job-to-job similarities, enabling fast, scalable analysis even for very large datasets (35,000+ jobs).
- **CLI and Testing:** A command-line interface is available for all major operations, with ongoing improvements to usability and test coverage.
- **Memory Management:** Ongoing enhancements to support large datasets on standard hardware.

## Roadmap and Future Direction

Planned and in-progress features include:
- Interactive career pathway exploration
- Advanced skill gap analysis and personalised development plans
- Scenario-based organisational planning
- Enhanced visualisation and user-facing tools (CLI, Power BI templates, web app)
- Employee-level analytics (when data is available)

For a detailed roadmap and feature breakdown, see [`project-plan.md`](./project-plan.md).

## Technical Approach

- **Precompute, then Query:** All heavy similarity calculations are performed in advance, with results stored for fast lookup and analysis.
- **Modular Codebase:** The engine is organised into modules for data loading, similarity calculation, analysis, visualisation, and CLI.
- **Cross-Platform:** Runs on Windows and macOS; all commands and paths are Windows-friendly.
- **Extensible:** Designed for easy integration of new features, data sources, and analytics.

## Configuration

The engine uses a flexible configuration system supporting different environments (development, testing, production):

```python
from skill_similarity_engine.config.settings import load_config_for_environment, get_config

# Load configuration (defaults to the environment in default.yaml)
load_config_for_environment("path/to/config/dir")

# Or for a specific environment
load_config_for_environment("path/to/config/dir", "production")

# Access configuration
config = get_config()
threshold = config.similarity.threshold
```

You can override any configuration setting using environment variables:

```powershell
# Override data directory
$env:SSE_DATA_DIR = "C:\custom\data\path"

# Override similarity threshold
$env:SSE_SIMILARITY_THRESHOLD = "0.75"
```

Configuration files are stored in YAML format with a hierarchy:
1. `default.yaml` – Default values for all settings
2. `[environment].yaml` – Environment-specific overrides
3. `local.yaml` – Local overrides (not checked into git)

See [`config/README.md`](./config/README.md) for details on configuration structure.

## Code Structure

The main codebase is under `src/skill_similarity_engine/` and is organised as follows:
- `cli/` – Command-line interface and utilities
- `config/` – Configuration management
- `data/` – Data loaders and normalisation
- `models/` – Data models for jobs, skills, etc.
- `similarity/` – Similarity calculation logic
- `analysis/` – Gap analysis and reporting
- `visualization/` – Visualisation and export tools
- `utils/` – Utilities for performance, memory management, and parallel processing
- `hris_adapter/` – HRIS data integration

## Practical Applications

- **Workforce Planning:** Identify similar roles and potential mobility pathways across departments.
- **Reskilling Programmes:** Pinpoint skill gaps and development needs for targeted upskilling.
- **Reporting:** Generate Power BI-ready datasets and visualisations for business analysis.
- **Scenario Analysis:** Model the impact of organisational changes on skill supply and demand.

See [`docs/practical_applications.md`](./docs/practical_applications.md) for more examples and visualisations.

## Requirements

Core dependencies include:
- numpy, pandas, scikit-learn (core analytics)
- matplotlib (visualisation)
- pyyaml, jsonschema (configuration)
- click (CLI)
- pytest (testing)
- mypy, black, isort, flake8 (development tools)

See [`requirements.txt`](./requirements.txt) for the full list.

## Contributing

- Please follow the [branching strategy](./BRANCHING.md) for feature development and pull requests.
- All changes to `main` and `develop` branches require a pull request and review.
- Reference issues in branch names or pull requests when possible.
- See the project plan for commit and PR guidelines.

## More Information

- **Detailed plans and status:** [`project-plan.md`](./project-plan.md)
- **Branching strategy:** [`BRANCHING.md`](./BRANCHING.md)
- **Practical applications and visualisation examples:** [`docs/practical_applications.md`](./docs/practical_applications.md)

For questions or contributions, please refer to the project plan or contact the maintainers. 