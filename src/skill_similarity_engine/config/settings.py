"""
Configuration settings for the skill similarity engine.

This module provides a centralized configuration management system using a single YAML file.
Configuration values can be accessed via the get_config() function.
"""

import os
from pathlib import Path
import yaml
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Any, Optional, List, Tuple
import json


# Environment variable prefix for overriding settings
ENV_PREFIX = "SSE_"


class ConfigFormat(Enum):
    """Format of configuration files."""
    YAML = auto()
    JSON = auto()
    
    @classmethod
    def from_file_extension(cls, file_path: str) -> "ConfigFormat":
        """
        Determine config format from file extension.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Determined ConfigFormat
            
        Raises:
            ValueError: If the file extension is not supported
        """
        extension = os.path.splitext(file_path)[1].lower()
        if extension in (".yaml", ".yml"):
            return cls.YAML
        elif extension == ".json":
            return cls.JSON
        else:
            raise ValueError(f"Unsupported file extension: {extension}")


@dataclass
class LoggingConfig:
    """Configuration for application logging."""
    level: str = "INFO"
    log_dir: str = "logs"
    log_file: str = "skill_similarity_engine.log"
    console_output: bool = True
    file_output: bool = True
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass
class NormalisationConfig:
    """Configuration for data normalisation."""
    use_min_max_scaling: bool = True
    use_boolean_normalisation: bool = False
    use_tfidf_weighting: bool = True
    importance_weights: Dict[str, float] = field(default_factory=lambda: {
        "Technical": 1.0,
        "Soft": 1.0,
        "Domain": 1.0,
        "Methodology": 1.0,
        "Tool": 1.0,
        "Certification": 1.0,
        "Other": 1.0
    })


@dataclass
class SimilarityConfig:
    """Configuration for similarity calculations."""
    method: str = "cosine"
    threshold: float = 0.5
    top_n_results: int = 5


@dataclass
class GapAnalysisConfig:
    """Configuration settings for skill gap analysis."""
    
    def __init__(self):
        """Initialize with default gap analysis settings."""
        # Minimum ratio of employee's proficiency to be considered adequate
        self.min_proficiency_ratio = 0.8
        
        # Difficulty factor for skill development effort calculation
        self.skill_difficulty_factor = 1.0
        
        # Minimum threshold for considering a gap significant
        self.min_gap_threshold = 0.2
        
        # Category weights for development effort calculation
        # Default values in case the external config isn't available
        self.category_weights = {
            "CERTIFICATION": 0.8,
            "COMMON": 1.0,
            "SPECIALIZED": 1.2,
            # Legacy category names for backward compatibility with tests
            "Technical": 1.0,
            "Soft": 1.0,
            "Domain": 1.2,
            "Methodology": 1.2,
            "Tool": 1.2,
            "Certification": 0.8,
            # Removed "Other" as it's not in the SkillType enum
            "Unknown": 1.0  # Added "Unknown" as a fallback for missing categories
        }


@dataclass
class OpportunityConfig:
    """Configuration for opportunity identification."""
    high_similarity_threshold: float = 0.8
    low_gap_threshold: float = 20.0
    high_match_percentage: float = 80.0
    critical_gap_percentage: float = 50.0
    critical_skill_gap_threshold: float = 0.4


@dataclass
class ReportingConfig:
    """Configuration for report generation."""
    include_headers: bool = True
    date_format: str = "%Y-%m-%d"
    float_format: str = "%.2f"
    include_index: bool = False
    encoding: str = "utf-8"
    json_indent: int = 2


@dataclass
class HeatmapConfig:
    """Configuration for heatmap visualizations."""
    default_colormap: str = "viridis"
    default_figsize: Tuple[int, int] = (10, 8)
    show_annotations: bool = True
    annotation_format: str = ".2f"
    line_width: float = 0.5
    show_colorbar: bool = True
    mask_diagonal: bool = False
    cluster_by_default: bool = False
    dpi: int = 300


@dataclass
class TeamAnalysisConfig:
    """Configuration for team gap analysis."""
    fully_covered_weight: float = 1.0
    partially_covered_weight: float = 0.5
    reskilling_difficulty_levels: Dict[int, str] = field(default_factory=lambda: {
        1: "Very Easy",
        2: "Easy",
        3: "Moderate", 
        4: "Difficult",
        5: "Very Difficult"
    })


@dataclass
class WorkforceConfig:
    """Configuration for workforce planning."""
    critical_skill_threshold: float = 3.0
    max_skills_in_report: int = 20
    department_skill_coverage_threshold: float = 75.0


class HRISAdapterConfig:
    """Configuration settings for the HRIS adapter."""
    
    def __init__(self):
        """Initialize with default HRIS adapter settings."""
        # Default configuration file path (can be overridden)
        self.default_config_path = "config/hris_config.yaml"
        
        # Default file format settings
        self.file_format = "csv"
        self.encoding = "utf-8"
        self.delimiter = ","
        self.has_header = True
        
        # Transformation options
        self.use_binary_skills = False
        self.default_proficiency = 3
        
        # Output directory for transformed files
        self.output_dir = "data/transformed"


@dataclass
class FutureExtensionConfig:
    """Configuration for future extensions (disabled by default)."""
    # Enhancement component weights
    seniority_weight: float = 0.0
    role_track_weight: float = 0.0
    location_weight: float = 0.0
    skill_type_weight: float = 0.0
    
    # Seniority similarity thresholds
    seniority_same_level_similarity: float = 1.0     # Similarity when seniority levels are the same
    seniority_one_up_similarity: float = 0.9         # Similarity when target job is one level higher
    seniority_up_step_penalty: float = 0.1           # Penalty per level for multiple levels up
    seniority_one_down_similarity: float = 0.1       # Similarity when target job is one level lower
    seniority_down_similarity: float = 0.0           # Similarity when target job is multiple levels lower
    
    # Role track similarity thresholds
    role_track_same_similarity: float = 1.0          # Similarity when role tracks are the same
    role_track_different_similarity: float = 0.5     # Similarity when target is leadership (from IC)
    role_track_regression_similarity: float = 0.1    # Similarity when target is IC (from leadership)
    
    # Location similarity thresholds
    location_same_similarity: float = 1.0            # Similarity when locations are the same
    location_different_similarity: float = 0.3       # Similarity when locations are different
    
    # Skill type similarity weights
    skill_type_similarity_weights: Dict[str, float] = field(default_factory=lambda: {
        "CERTIFICATION": 1.0,
        "COMMON": 0.7,
        "SPECIALIZED": 1.8
    })
    
    # Skill type mapping from HRIS to engine categories
    skill_type_mapping: Dict[str, str] = field(default_factory=lambda: {
        "Certification": "CERTIFICATION",
        "Common Skill": "COMMON",
        "Specialized Skill": "SPECIALIZED"
    })


class GeneralConfig:
    """General configuration settings for the skill similarity engine."""
    
    def __init__(self):
        """Initialize with default general settings."""
        # Version information
        self.version = "0.1.0"
        
        # Directory paths
        self.data_dir = "data"
        self.output_dir = "output"
        
        # External configuration files
        self.similarity_enhancement_factors_file = "config/similarity_enhancement_factors.yaml"


class DataSourceConfig:
    """Configuration settings for data sources."""
    
    def __init__(self):
        """Initialize with default data source settings."""
        # Data source paths
        self.jobs_file = "data/jobs.csv"
        self.skills_file = "data/skills.csv"
        self.employees_file = "data/employees.csv"
        
        # Data source options
        self.encoding = "utf-8"
        self.delimiter = ","
        self.has_header = True


class ModelConfig:
    """Configuration settings for model parameters."""
    
    def __init__(self):
        """Initialize with default model settings."""
        # Vectorization parameters
        self.vector_size = 100
        self.min_count = 1
        self.window = 5
        self.workers = 4
        
        # Similarity parameters
        self.similarity_threshold = 0.7
        self.top_n_results = 5


class Config:
    """Global configuration settings for the skill similarity engine."""
    
    def __init__(self):
        """Initialize with default configuration settings."""
        # Initialize configuration sections
        self.general = GeneralConfig()
        self.data_sources = DataSourceConfig()
        self.model = ModelConfig()
        self.gap_analysis = GapAnalysisConfig()
        self.team_analysis = TeamAnalysisConfig()
        self.hris_adapter = HRISAdapterConfig()
        self.future_extensions = FutureExtensionConfig()
        # Add workforce configuration
        self.workforce = WorkforceConfig()
        # Add additional config sections for backward compatibility with tests
        self.normalisation = NormalisationConfig()
        self.similarity = SimilarityConfig()
        self.opportunity = OpportunityConfig()
    
    @property
    def data_dir(self):
        """Get data directory from general config."""
        return self.general.data_dir
    
    @data_dir.setter
    def data_dir(self, value):
        """Set data directory in general config."""
        self.general.data_dir = value
    
    @property
    def output_dir(self):
        """Get output directory from general config."""
        return self.general.output_dir
    
    @output_dir.setter
    def output_dir(self, value):
        """Set output directory in general config."""
        self.general.output_dir = value
    
    @property
    def version(self):
        """Get version from general config."""
        return self.general.version
    
    @version.setter
    def version(self, value):
        """Set version in general config."""
        self.general.version = value
    
    @property
    def environment(self):
        """Get environment setting (for backward compatibility)."""
        return getattr(self.general, "environment", "development")


class ConfigManager:
    """
    Singleton manager for configuration settings.
    
    This class manages the global configuration for the skill similarity engine.
    It ensures that configuration is loaded only once and provides access to
    configuration values and utility functions.
    """
    
    # Singleton instance
    _instance = None
    
    def __new__(cls):
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config = Config()
            cls._instance.load_config()
        return cls._instance
    
    def get_config(self):
        """
        Get the current configuration.
        
        Returns:
            Current Config instance
        """
        return self.config
    
    def load_config(self, config_path: Optional[str] = None):
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file (default: use environment variable or default path)
        """
        # Flag to track if we're loading a specific config file
        is_explicit_config = config_path is not None
        
        # Get config path from environment variable or use default
        if config_path is None:
            config_path = os.environ.get("SKILL_ENGINE_CONFIG", "config/config.yaml")
        
        # Load yaml config if it exists
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                yaml_config = yaml.safe_load(f)
            
            # Update configuration values
            if yaml_config:
                self._update_config_from_dict(yaml_config)
        elif is_explicit_config:
            # If a specific config file was requested but not found, raise an error
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Load enhancement factors if specified in the main config
        self._load_enhancement_factors(is_explicit_config)
        
        # Also look for environment variables that override config
        self._update_config_from_env()
    
    def _load_enhancement_factors(self, is_explicit_config=False):
        """Load similarity enhancement factors from external file."""
        # Check for both new and old file path attributes
        enhancement_file = getattr(self.config.general, "similarity_enhancement_factors_file", 
                                "config/similarity_enhancement_factors.yaml")
        
        # Check for the backward compatibility with future_extensions_file
        future_extensions_file = getattr(self.config.general, "future_extensions_file", None)
        if future_extensions_file:
            enhancement_file = future_extensions_file
        
        # If we're loading a specific config and the enhancement file is the default, skip loading
        if is_explicit_config and enhancement_file == "config/similarity_enhancement_factors.yaml":
            print("Skipping loading default enhancement factors when using explicit config")
            return
        
        # Print debug information
        print(f"Loading enhancement factors from file: {enhancement_file}")
        print(f"File exists: {os.path.exists(enhancement_file)}")
        
        # Load if the file exists
        if os.path.exists(enhancement_file):
            try:
                with open(enhancement_file, "r") as f:
                    enhancement_config = yaml.safe_load(f)
                
                print(f"Loaded enhancement config: {enhancement_config}")
                
                # Update specific settings from enhancement factors
                if enhancement_config:
                    # Update skill category weights for gap analysis if available
                    if "skill_category_weights" in enhancement_config:
                        self.config.gap_analysis.category_weights = enhancement_config["skill_category_weights"]
                    
                    # Update extension attributes directly
                    for key, value in enhancement_config.items():
                        if hasattr(self.config.future_extensions, key):
                            setattr(self.config.future_extensions, key, value)
                            print(f"Updated future_extensions.{key} to {value}")
                    
                    # Update skill type similarity weights if available
                    if "skill_type_similarity_weights" in enhancement_config:
                        self.config.future_extensions.skill_type_similarity_weights = enhancement_config["skill_type_similarity_weights"]
                    
                    # Update skill type mapping if available
                    if "skill_type_mapping" in enhancement_config:
                        self.config.future_extensions.skill_type_mapping = enhancement_config["skill_type_mapping"]
            except Exception as e:
                # Log the error but continue with default values
                print(f"Error loading enhancement factors: {e}")
    
    def _update_config_attr(self, config_dict, attr_name, config_obj):
        """Helper method to update a config attribute if it exists in the dict."""
        if attr_name in config_dict:
            setattr(config_obj, attr_name, config_dict[attr_name])
    
    def _update_config_from_dict(self, config_dict: Dict[str, Any]):
        """
        Update configuration from dictionary.
        
        Args:
            config_dict: Dictionary with configuration values
        """
        # Handle top-level attributes first
        if "data_dir" in config_dict:
            self.config.data_dir = config_dict["data_dir"]
        if "output_dir" in config_dict:
            self.config.output_dir = config_dict["output_dir"]
        if "version" in config_dict:
            self.config.version = config_dict["version"]
        if "future_extensions_file" in config_dict:
            self.config.general.future_extensions_file = config_dict["future_extensions_file"]
        if "similarity_enhancement_factors_file" in config_dict:
            self.config.general.similarity_enhancement_factors_file = config_dict["similarity_enhancement_factors_file"]
        
        # Update general config
        if "general" in config_dict:
            for key, value in config_dict["general"].items():
                if hasattr(self.config.general, key):
                    setattr(self.config.general, key, value)
        
        # Update data sources config
        if "data_sources" in config_dict:
            for key, value in config_dict["data_sources"].items():
                if hasattr(self.config.data_sources, key):
                    setattr(self.config.data_sources, key, value)
        
        # Update model config
        if "model" in config_dict:
            for key, value in config_dict["model"].items():
                if hasattr(self.config.model, key):
                    setattr(self.config.model, key, value)
        
        # Update gap analysis config
        if "gap_analysis" in config_dict:
            for key, value in config_dict["gap_analysis"].items():
                if hasattr(self.config.gap_analysis, key):
                    setattr(self.config.gap_analysis, key, value)
        
        # Update team analysis config
        if "team_analysis" in config_dict:
            for key, value in config_dict["team_analysis"].items():
                if hasattr(self.config.team_analysis, key):
                    setattr(self.config.team_analysis, key, value)
                    
        # Update HRIS adapter config
        if "hris_adapter" in config_dict:
            for key, value in config_dict["hris_adapter"].items():
                if hasattr(self.config.hris_adapter, key):
                    setattr(self.config.hris_adapter, key, value)
        
        # Update similarity config
        if "similarity" in config_dict:
            for key, value in config_dict["similarity"].items():
                if hasattr(self.config.similarity, key):
                    setattr(self.config.similarity, key, value)
        
        # Update future extensions config
        if "future_extensions" in config_dict:
            for key, value in config_dict["future_extensions"].items():
                if hasattr(self.config.future_extensions, key):
                    setattr(self.config.future_extensions, key, value)
    
    def _update_config_from_env(self):
        """Update configuration from environment variables."""
        # Example format: SKILL_ENGINE_GENERAL_LOG_LEVEL
        env_prefix = "SKILL_ENGINE_"
        
        for env_var, env_value in os.environ.items():
            if env_var.startswith(env_prefix):
                # Remove prefix and split by underscore
                config_path = env_var[len(env_prefix):].lower().split("_")
                
                if len(config_path) >= 2:
                    # First part is the config section, rest is the attribute path
                    section = config_path[0]
                    attr_path = "_".join(config_path[1:])
                    
                    # Get the section object
                    section_obj = None
                    if section == "general":
                        section_obj = self.config.general
                    elif section == "data_sources":
                        section_obj = self.config.data_sources
                    elif section == "model":
                        section_obj = self.config.model
                    elif section == "gap_analysis":
                        section_obj = self.config.gap_analysis
                    elif section == "team_analysis":
                        section_obj = self.config.team_analysis
                    elif section == "hris_adapter":
                        section_obj = self.config.hris_adapter
                    
                    # Set the attribute if it exists
                    if section_obj is not None and hasattr(section_obj, attr_path):
                        attr = getattr(section_obj, attr_path)
                        
                        # Convert value to the same type as the attribute
                        if isinstance(attr, bool):
                            converted_value = env_value.lower() in ("true", "1", "yes", "y")
                        elif isinstance(attr, int):
                            converted_value = int(env_value)
                        elif isinstance(attr, float):
                            converted_value = float(env_value)
                        elif isinstance(attr, list):
                            converted_value = env_value.split(",")
                        elif isinstance(attr, dict):
                            # Parse JSON string
                            try:
                                converted_value = json.loads(env_value)
                            except json.JSONDecodeError:
                                # If not valid JSON, keep as string
                                converted_value = env_value
                        else:
                            converted_value = env_value
                        
                        setattr(section_obj, attr_path, converted_value)

    def get_data_path(self, relative_path=""):
        """
        Get the absolute path to a data file or directory.
        
        Args:
            relative_path: Relative path within the data directory
            
        Returns:
            Absolute path
        """
        # Convert to Path objects to handle path concatenation properly
        data_dir = Path(self.config.data_dir)
        
        # Handle absolute and relative paths
        if os.path.isabs(self.config.data_dir):
            # If data_dir is absolute, use it directly
            full_path = data_dir / relative_path
        else:
            # If data_dir is relative, resolve it relative to the current working directory
            full_path = Path.cwd() / data_dir / relative_path
        
        return str(full_path)
    
    def get_output_path(self, relative_path=""):
        """
        Get the absolute path to an output file or directory.
        
        Args:
            relative_path: Relative path within the output directory
            
        Returns:
            Absolute path
        """
        # Convert to Path objects to handle path concatenation properly
        output_dir = Path(self.config.output_dir)
        
        # Handle absolute and relative paths
        if os.path.isabs(self.config.output_dir):
            # If output_dir is absolute, use it directly
            full_path = output_dir / relative_path
        else:
            # If output_dir is relative, resolve it relative to the current working directory
            full_path = Path.cwd() / output_dir / relative_path
        
        # Create directory if it doesn't exist
        if relative_path and not os.path.splitext(relative_path)[1]:  # No extension, assume it's a directory
            full_path.mkdir(parents=True, exist_ok=True)
        else:
            full_path.parent.mkdir(parents=True, exist_ok=True)
        
        return str(full_path)


# Global ConfigManager instance
_config_manager = ConfigManager()


def load_config(config_file):
    """
    Load configuration from a file.
    
    Args:
        config_file: Path to the configuration file
    """
    _config_manager.load_config(config_file)


def get_config():
    """
    Get the current configuration.
    
    Returns:
        Current AppConfig instance
    """
    return _config_manager.config


def get_data_path(relative_path=""):
    """
    Get the absolute path to a data file or directory.
    
    Args:
        relative_path: Relative path within the data directory
        
    Returns:
        Absolute path
    """
    # Convert to Path objects to handle path concatenation properly
    data_dir = Path(get_config().data_dir)
    
    # Handle absolute and relative paths
    if os.path.isabs(get_config().data_dir):
        # If data_dir is absolute, use it directly
        full_path = data_dir / relative_path
    else:
        # If data_dir is relative, resolve it relative to the current working directory
        full_path = Path.cwd() / data_dir / relative_path
    
    return str(full_path)


def get_output_path(relative_path=""):
    """
    Get the absolute path to an output file or directory.
    
    Args:
        relative_path: Relative path within the output directory
        
    Returns:
        Absolute path
    """
    # Convert to Path objects to handle path concatenation properly
    output_dir = Path(get_config().output_dir)
    
    # Handle absolute and relative paths
    if os.path.isabs(get_config().output_dir):
        # If output_dir is absolute, use it directly
        full_path = output_dir / relative_path
    else:
        # If output_dir is relative, resolve it relative to the current working directory
        full_path = Path.cwd() / output_dir / relative_path
    
    # Create directory if it doesn't exist
    if relative_path and not os.path.splitext(relative_path)[1]:  # No extension, assume it's a directory
        full_path.mkdir(parents=True, exist_ok=True)
    else:
        full_path.parent.mkdir(parents=True, exist_ok=True)
    
    return str(full_path)

# Create an alias for backward compatibility with tests
AppConfig = Config
