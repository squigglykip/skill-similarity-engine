# Skill Similarity Engine - Configuration Reference

This document provides a complete reference for configuring the Skill Similarity Engine for production use, with a focus on Job-to-Job Similarity Analysis.

## Configuration File

The system uses a YAML configuration file (`config.yaml`) to customize behavior. Below is a complete reference of all available settings:

```yaml
# Application settings
app:
  # Directory where output files will be saved
  output_directory: "./outputs"
  
  # Directory where input data files are located
  data_directory: "./data"
  
  # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_level: "INFO"
  
  # Maximum number of threads to use for parallel processing
  max_threads: 4
  
  # Whether to add metadata to exports (titles, descriptions, etc.)
  add_metadata_to_exports: true
  
  # Default file format for exports (csv, json, excel)
  default_export_format: "csv"

# Job matching settings
job_matching:
  # Minimum similarity threshold for job matching
  similarity_threshold: 0.7
  
  # Maximum number of similar jobs to recommend
  max_recommendations: 10
  
  # Whether to filter out jobs from different departments by default
  filter_by_department: false
  
  # Similarity metric to use (cosine, jaccard, euclidean)
  similarity_metric: "cosine"
  
  # Whether to normalize skill proficiency levels
  normalize_proficiency: true

# Opportunity flags thresholds
opportunity:
  # Threshold for high similarity flag (0.0 to 1.0)
  high_similarity_threshold: 0.8
  
  # Threshold for low skill gap flag (percentage, 0 to 100)
  low_gap_threshold: 20.0
  
  # Threshold for high match percentage flag (percentage, 0 to 100)
  high_match_percentage: 80.0
  
  # Threshold for critical gap flag (percentage, 0 to 100)
  critical_gap_percentage: 50.0
  
  # Threshold for considering something a career advancement
  career_advancement_level_delta: 1

# Visualization settings
visualization:
  # Default colormap for heatmaps
  colormap: "viridis"
  
  # Whether to apply clustering to job similarity heatmaps
  apply_clustering: true
  
  # Clustering method (hierarchical, kmeans)
  clustering_method: "hierarchical"
  
  # Number of clusters for job grouping
  cluster_count: 10
  
  # Default figure size in inches (width, height)
  figure_size: [12, 10]
  
  # Resolution (DPI) for saved figures
  dpi: 300

# Data loading settings
data_loading:
  # Whether to validate all input data before processing
  validate_inputs: true
  
  # Maximum number of rows to process in one batch
  batch_size: 10000
  
  # Whether to cache processed data
  enable_caching: true
  
  # Directory for cached data
  cache_directory: "./cache"
  
  # Maximum cache file age in hours
  max_cache_age: 24

# Logging settings
logging:
  # Whether to log to file
  file_output: true
  
  # Log file location
  log_directory: "./logs"
  
  # Log file name
  log_filename: "skill_similarity_engine.log"
  
  # Whether to log to console
  console_output: true
  
  # Maximum log file size in MB before rotation
  max_log_file_size: 10
  
  # Number of backup log files to keep
  log_backup_count: 5
```

## Environment Variables

Configuration can also be provided via environment variables, which will override the values in the config file:

| Environment Variable | Description | Example |
|----------------------|-------------|---------|
| `SSE_OUTPUT_DIR` | Output directory | `/path/to/outputs` |
| `SSE_DATA_DIR` | Data directory | `/path/to/data` |
| `SSE_LOG_LEVEL` | Logging level | `INFO` |
| `SSE_SIMILARITY_THRESHOLD` | Job similarity threshold | `0.7` |
| `SSE_HIGH_SIMILARITY` | High similarity threshold | `0.8` |
| `SSE_MAX_THREADS` | Maximum number of threads | `4` |

## Production Settings Recommendations

For production environments, the following settings are recommended:

### Performance Settings

```yaml
app:
  max_threads: 8  # Adjust based on CPU cores

job_matching:
  similarity_metric: "cosine"  # Best balance of performance and accuracy

data_loading:
  batch_size: 5000  # Adjust based on available memory
  enable_caching: true
```

### Large Dataset Settings

For very large datasets (35,000+ jobs):

```yaml
job_matching:
  filter_by_department: true  # Process by department to reduce memory usage

data_loading:
  batch_size: 1000  # Smaller batches to conserve memory
```

### Security Settings

```yaml
app:
  output_directory: "/secure/path/to/outputs"  # Use controlled access path
  
logging:
  log_directory: "/var/log/skill-similarity-engine"  # Standard log location
  console_output: false  # Disable for services/background jobs
```

## Configuration in Code

You can override configuration programmatically:

```python
from skill_similarity_engine.config.settings import get_config, update_config

# Get the current configuration
config = get_config()

# Update specific settings
update_config({
    "app": {
        "max_threads": 8
    },
    "job_matching": {
        "similarity_threshold": 0.75
    }
})
```

## Validation

The system validates configuration against a schema to ensure all values are within acceptable ranges. Invalid configuration will cause warnings or errors depending on the severity.

## Common Configurations

### Basic Analysis

```yaml
app:
  output_directory: "./outputs"

job_matching:
  similarity_threshold: 0.7
  max_recommendations: 10
```

### Department-Focused Analysis

```yaml
job_matching:
  filter_by_department: true
  similarity_threshold: 0.6  # Lower threshold for intra-department matching
```

### Career Pathway Analysis

```yaml
opportunity:
  high_similarity_threshold: 0.7  # Lower to identify more potential pathways
  low_gap_threshold: 30.0  # Higher to allow for more transition opportunities
  career_advancement_level_delta: 1
```

## Configuration for Specific Use Cases

### Power BI Integration

```yaml
app:
  add_metadata_to_exports: true
  default_export_format: "csv"

opportunity:
  high_similarity_threshold: 0.8
```

### Batch Processing

```yaml
app:
  max_threads: 8
  
data_loading:
  batch_size: 5000
  enable_caching: true
```

## Testing Your Configuration

Run the following command to validate your configuration without processing data:

```bash
skill-similarity-engine validate-config --config-file your-config.yaml
``` 