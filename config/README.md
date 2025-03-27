# Skill Similarity Engine - Configuration System

This directory contains configuration files for the Skill Similarity Engine.

## Configuration Files

The configuration system supports multiple configuration files in a hierarchical structure:

1. **default.yaml** - Default configuration with all settings and their default values
2. **testing.yaml** - Testing environment configuration (overrides default)
3. **production.yaml** - Production environment configuration (overrides default)
4. **local.yaml** - Local overrides (not checked into git, overrides all others)

## Using the Configuration System

### From Python Code

```python
from skill_similarity_engine.config.settings import load_config_for_environment, get_config

# Load configuration for the current environment
load_config_for_environment("path/to/config/dir")

# Or for a specific environment
load_config_for_environment("path/to/config/dir", "production")

# Access configuration values
config = get_config()
threshold = config.similarity.threshold
```

### From Command Line

The configuration system includes CLI commands for viewing and managing configuration:

```bash
# View current configuration
python -m skill_similarity_engine config view

# View configuration for a specific environment
python -m skill_similarity_engine config view --environment production

# Initialize configuration files in a directory
python -m skill_similarity_engine config init --output-dir /path/to/config

# Create a local configuration file
python -m skill_similarity_engine config create-local --config-dir /path/to/config
```

## Environment Variables

You can override any configuration setting using environment variables with the prefix `SSE_`:

```bash
# Override data directory
export SSE_DATA_DIR="/custom/data/path"

# Override similarity threshold
export SSE_SIMILARITY_THRESHOLD="0.75"

# Override nested settings
export SSE_GAP_ANALYSIS_MIN_PROFICIENCY_RATIO="0.9"
```

## Configuration Structure

The configuration is structured hierarchically with the following sections:

- **version** - Configuration version string
- **environment** - Current environment (development, testing, production)
- **data_dir** - Directory for data files
- **output_dir** - Directory for output files
- **normalisation** - Settings for data normalisation
  - **use_min_max_scaling** - Whether to use min-max scaling
  - **use_boolean_normalisation** - Whether to use boolean normalisation
  - **use_tfidf_weighting** - Whether to use TF-IDF weighting
  - **importance_weights** - Weights for different skill categories
- **similarity** - Settings for similarity calculations
  - **method** - Similarity calculation method
  - **threshold** - Minimum similarity threshold
  - **top_n_results** - Number of top results to return
- **gap_analysis** - Settings for gap analysis
  - **min_proficiency_ratio** - Minimum ratio for proficiency matching
  - **skill_difficulty_factor** - Weight for skill difficulty
  - **min_gap_threshold** - Minimum gap threshold for critical gaps
  - **category_weights** - Weights for different skill categories
- **opportunity** - Settings for opportunity identification
  - **high_similarity_threshold** - Threshold for high similarity
  - **low_gap_threshold** - Threshold for low gap
  - **high_match_percentage** - Threshold for high match percentage
  - **critical_gap_percentage** - Threshold for critical gap percentage

## Future Extensions

The configuration system includes placeholder sections for future extensions:

- **seniority** - Settings for seniority-based similarity
- **role_track** - Settings for role track-based similarity
- **location** - Settings for location-based similarity

These sections are currently disabled (weight=0) but can be enabled in future versions. 