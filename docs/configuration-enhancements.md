# Configuration System Enhancements

## Overview

This document outlines proposed enhancements to the configuration system, particularly focusing on making declarative parameters like thresholds, weights, and other settings configurable through YAML files.

## Current State

The system currently has a basic configuration structure that handles essential settings like file paths and output directories. However, many operational parameters such as similarity thresholds, opportunity flags, and weighting factors are hardcoded within the implementation classes.

## Proposed Enhancements

### 1. Comprehensive Configuration Schema

Create a comprehensive configuration schema that encompasses all configurable aspects of the system:

```yaml
# Sample enhanced configuration.yaml
---
# General settings
general:
  output_dir: "./output"
  data_dir: "./data"
  log_level: "INFO"
  log_file: "./logs/skill_similarity.log"

# Similarity settings
similarity:
  algorithm: "cosine"  # Options: cosine, euclidean, jaccard
  min_threshold: 0.3   # Minimum similarity threshold for inclusion in results
  opportunity_threshold: 0.7  # Threshold for flagging high-similarity opportunities
  
  # Skill type weights for vectorization
  skill_weights:
    technical: 1.0
    soft: 1.0
    domain: 1.0
    methodology: 1.0
    tool: 0.8
    certification: 0.6
    other: 0.5

# Gap analysis settings
gap_analysis:
  min_proficiency_ratio: 0.8  # Minimum proficiency ratio for skill matching
  max_development_effort: 10  # Maximum development effort to consider viable
  
  # Weights for different skill types in development effort calculation
  effort_weights:
    technical: 1.2
    soft: 1.5
    domain: 1.0
    methodology: 1.1
    tool: 0.8
    certification: 2.0
    other: 1.0

# Export settings
export:
  include_metadata: true
  include_names: true
  include_descriptions: false
  add_opportunity_flags: true
  default_format: "csv"  # Options: csv, json, excel

# Opportunity flags settings
opportunity_flags:
  high_similarity_threshold: 0.7
  internal_mobility_threshold: 0.6
  cross_departmental_threshold: 0.5

# Power BI integration settings
power_bi:
  relationship_model: "star"  # Options: star, snowflake
  dimension_tables:
    - jobs
    - departments
    - skills
  fact_tables:
    - similarity
    - gap
```

### 2. Configuration Object Hierarchy

Implement a hierarchical configuration object structure that mirrors the YAML schema:

```python
@dataclass
class SimilarityConfig:
    algorithm: str = "cosine"
    min_threshold: float = 0.3
    opportunity_threshold: float = 0.7
    skill_weights: Dict[str, float] = field(default_factory=lambda: {
        "technical": 1.0,
        "soft": 1.0,
        "domain": 1.0,
        "methodology": 1.0,
        "tool": 0.8,
        "certification": 0.6,
        "other": 0.5
    })

@dataclass
class GapAnalysisConfig:
    min_proficiency_ratio: float = 0.8
    max_development_effort: int = 10
    effort_weights: Dict[str, float] = field(default_factory=lambda: {
        "technical": 1.2,
        "soft": 1.5,
        "domain": 1.0,
        "methodology": 1.1,
        "tool": 0.8,
        "certification": 2.0,
        "other": 1.0
    })

@dataclass
class ExportConfig:
    include_metadata: bool = True
    include_names: bool = True
    include_descriptions: bool = False
    add_opportunity_flags: bool = True
    default_format: str = "csv"

@dataclass
class OpportunityFlagsConfig:
    high_similarity_threshold: float = 0.7
    internal_mobility_threshold: float = 0.6
    cross_departmental_threshold: float = 0.5

@dataclass
class PowerBIConfig:
    relationship_model: str = "star"
    dimension_tables: List[str] = field(default_factory=lambda: ["jobs", "departments", "skills"])
    fact_tables: List[str] = field(default_factory=lambda: ["similarity", "gap"])

@dataclass
class AppConfig:
    general: GeneralConfig = field(default_factory=GeneralConfig)
    similarity: SimilarityConfig = field(default_factory=SimilarityConfig)
    gap_analysis: GapAnalysisConfig = field(default_factory=GapAnalysisConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    opportunity_flags: OpportunityFlagsConfig = field(default_factory=OpportunityFlagsConfig)
    power_bi: PowerBIConfig = field(default_factory=PowerBIConfig)
```

### 3. Configuration Access Layer

Enhance the configuration system to provide easy access to the configuration values throughout the application:

```python
class ConfigManager:
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._config = AppConfig()
        return cls._instance
    
    @classmethod
    def load_config(cls, config_path: str) -> None:
        """Load configuration from a YAML file."""
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        cls._instance._config = AppConfig.from_dict(config_dict)
    
    @classmethod
    def get_config(cls) -> AppConfig:
        """Get the application configuration."""
        return cls._instance._config
    
    @classmethod
    def get_similarity_config(cls) -> SimilarityConfig:
        """Get the similarity configuration."""
        return cls._instance._config.similarity
    
    @classmethod
    def get_gap_analysis_config(cls) -> GapAnalysisConfig:
        """Get the gap analysis configuration."""
        return cls._instance._config.gap_analysis
    
    # Additional getter methods for other config sections
```

### 4. Implementation Plan

1. **Framework Updates**: Enhance the configuration framework in `config/settings.py`
   - Implement the hierarchical configuration classes
   - Create loading and saving methods for YAML/JSON files
   - Implement validation for configuration values

2. **Component Updates**: Update system components to use the configuration
   - Modify the similarity calculator to use thresholds from config
   - Update the gap analyzer to use effort weights from config
   - Adjust exporters to use export settings from config

3. **CLI Integration**: Update CLI commands to support configuration
   - Add commands for generating/viewing configuration
   - Support overriding config values via command line arguments
   - Implement configuration validation before operations

4. **Documentation**: Update documentation to reflect new configuration options
   - Create a configuration reference guide
   - Document all available settings and their default values
   - Provide example configuration files for common use cases

## Benefits

1. **Flexibility**: Easy adaptation to different use cases and environments
2. **Maintainability**: Centralized management of operational parameters
3. **Transparency**: Clear documentation of all system parameters
4. **Testability**: Easier testing with different parameter sets
5. **Reproducibility**: Consistent results when using the same configuration

## Timeline

Estimated implementation time: 3-4 days

- Day 1: Design and implement the configuration class hierarchy
- Day 2: Update system components to use configuration values
- Day 3: Implement CLI integration and validation
- Day 4: Create documentation and example configurations 