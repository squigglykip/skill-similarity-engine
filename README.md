# Skill Similarity Engine

## Overview

The Skill Similarity Engine is a scalable analytics system designed to analyse and compare job roles based on their skill requirements. Its primary goal is to identify reskilling and mobility opportunities within large organisations, with outputs optimised for integration with Power BI and other analytics tools.

## Main Deliverables
- **Job-to-Job Similarity Analysis**: Generates a comprehensive, cross-department similarity dataset for all jobs, enabling data-driven workforce planning and career mobility insights.
- **Power BI Integration**: Outputs are structured for easy import and analysis in Power BI, supporting interactive dashboards and reporting.

## Current Focus
- **Precompute Architecture**: The engine is being re-architected to precompute all job-to-job similarities, enabling fast, scalable analysis even for very large datasets (35,000+ jobs).
- **Memory & Performance Optimisation**: Special attention is given to efficient memory usage and parallel processing, so the system can run on standard laptops and workstations.

## Future Direction
The project will expand to include:
- Interactive career pathway exploration
- Advanced skill gap analysis and personalised development plans
- Scenario-based organisational planning
- Advanced visualisation and user-facing tools

For a detailed roadmap and feature breakdown, see [`project-plan.md`](./project-plan.md).

## Technical Approach
- **Precompute, then Query**: All heavy similarity calculations are performed in advance, with results stored for fast lookup and analysis.
- **Configurable & Cross-Platform**: Uses YAML-based configuration, supports environment-specific settings, and runs on Windows and macOS.
- **Optimised for Large Data**: Designed to handle tens of thousands of jobs and skills efficiently.

## Configuration & Usage

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

## More Information
- **Detailed plans and status**: [`project-plan.md`](./project-plan.md)
- **Branching strategy**: [`BRANCHING.md`](./BRANCHING.md)
- **Practical applications and visualisation examples**: [`docs/practical_applications.md`](./docs/practical_applications.md)

For questions or contributions, please refer to the project plan or contact the maintainers. 