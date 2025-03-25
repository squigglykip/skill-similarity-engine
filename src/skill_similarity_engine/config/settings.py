"""
Configuration system for the skill similarity engine.

This module provides functionality for loading, validating, and accessing
configuration settings from YAML or JSON files.
"""

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import jsonschema
import yaml


class ConfigFormat(Enum):
    """Supported configuration file formats."""
    YAML = "yaml"
    JSON = "json"
    
    @classmethod
    def from_file_extension(cls, file_path: str) -> "ConfigFormat":
        """
        Determine config format from file extension.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Corresponding ConfigFormat enum value
            
        Raises:
            ValueError: If the file extension is not supported
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in (".yaml", ".yml"):
            return cls.YAML
        elif ext == ".json":
            return cls.JSON
        else:
            raise ValueError(f"Unsupported config file extension: {ext}")


@dataclass
class NormalisationConfig:
    """
    Configuration for data normalisation.
    
    Attributes:
        use_min_max_scaling: Whether to use min-max scaling for proficiency levels
        use_boolean_normalisation: Whether to use boolean normalisation (has/doesn't have skill)
        use_tfidf_weighting: Whether to use TF-IDF style weighting
        importance_weights: Dictionary mapping skill categories to importance weights
    """
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
    """
    Configuration for similarity calculations.
    
    Attributes:
        method: Similarity calculation method to use (cosine, euclidean, or jaccard)
        threshold: Minimum similarity threshold for considering matches
        top_n_results: Number of top similarity results to return
    """
    method: str = "cosine"
    threshold: float = 0.5
    top_n_results: int = 5


@dataclass
class GapAnalysisConfig:
    """
    Configuration for gap analysis.
    
    Attributes:
        min_proficiency_ratio: Minimum ratio of employee's proficiency to required proficiency
        skill_difficulty_factor: Weight given to skill difficulty in development effort
        category_weights: Weights for different skill categories in development effort
    """
    min_proficiency_ratio: float = 0.8
    skill_difficulty_factor: float = 1.0
    category_weights: Dict[str, float] = field(default_factory=lambda: {
        "Technical": 1.0,
        "Soft": 0.8,
        "Domain": 0.7,
        "Methodology": 0.9,
        "Tool": 0.6,
        "Certification": 0.5,
        "Other": 0.5
    })


@dataclass
class AppConfig:
    """
    Main application configuration.
    
    Attributes:
        environment: Current environment (development, testing, or production)
        data_dir: Directory for data files
        output_dir: Directory for output files
        normalisation: Normalisation configuration
        similarity: Similarity calculation configuration
        gap_analysis: Gap analysis configuration
    """
    environment: str = "development"
    data_dir: str = "data"
    output_dir: str = "output"
    normalisation: NormalisationConfig = field(default_factory=NormalisationConfig)
    similarity: SimilarityConfig = field(default_factory=SimilarityConfig)
    gap_analysis: GapAnalysisConfig = field(default_factory=GapAnalysisConfig)


# Configuration schema for validation
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "environment": {"type": "string", "enum": ["development", "testing", "production"]},
        "data_dir": {"type": "string"},
        "output_dir": {"type": "string"},
        "normalisation": {
            "type": "object",
            "properties": {
                "use_min_max_scaling": {"type": "boolean"},
                "use_boolean_normalisation": {"type": "boolean"},
                "use_tfidf_weighting": {"type": "boolean"},
                "importance_weights": {
                    "type": "object",
                    "additionalProperties": {"type": "number"}
                }
            }
        },
        "similarity": {
            "type": "object",
            "properties": {
                "method": {"type": "string", "enum": ["cosine", "euclidean", "jaccard"]},
                "threshold": {"type": "number", "minimum": 0, "maximum": 1},
                "top_n_results": {"type": "integer", "minimum": 1}
            }
        },
        "gap_analysis": {
            "type": "object",
            "properties": {
                "min_proficiency_ratio": {"type": "number", "minimum": 0, "maximum": 1},
                "skill_difficulty_factor": {"type": "number", "minimum": 0},
                "category_weights": {
                    "type": "object",
                    "additionalProperties": {"type": "number"}
                }
            }
        }
    }
}


class ConfigManager:
    """
    Manager for loading and accessing application configuration.
    
    Attributes:
        config: The loaded application configuration
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern for ConfigManager."""
        if not cls._instance:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config = AppConfig()
        return cls._instance
    
    def load_config(self, config_path: str) -> None:
        """
        Load configuration from a file.
        
        Args:
            config_path: Path to the configuration file
            
        Raises:
            FileNotFoundError: If the config file doesn't exist
            ValueError: If the config file format is invalid
            jsonschema.exceptions.ValidationError: If the config is invalid
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Determine format from file extension
        config_format = ConfigFormat.from_file_extension(config_path)
        
        # Load configuration data
        with open(config_path, "r") as f:
            if config_format == ConfigFormat.YAML:
                config_data = yaml.safe_load(f)
            elif config_format == ConfigFormat.JSON:
                config_data = json.load(f)
        
        # Validate configuration
        jsonschema.validate(config_data, CONFIG_SCHEMA)
        
        # Update configuration
        self._update_config(config_data)
    
    def _update_config(self, config_data: Dict[str, Any]) -> None:
        """
        Update configuration with data from a loaded config file.
        
        Args:
            config_data: Configuration data dictionary
        """
        # Update top-level attributes
        if "environment" in config_data:
            self.config.environment = config_data["environment"]
        
        if "data_dir" in config_data:
            self.config.data_dir = config_data["data_dir"]
        
        if "output_dir" in config_data:
            self.config.output_dir = config_data["output_dir"]
        
        # Update normalisation config
        if "normalisation" in config_data:
            norm_data = config_data["normalisation"]
            
            if "use_min_max_scaling" in norm_data:
                self.config.normalisation.use_min_max_scaling = norm_data["use_min_max_scaling"]
            
            if "use_boolean_normalisation" in norm_data:
                self.config.normalisation.use_boolean_normalisation = norm_data["use_boolean_normalisation"]
            
            if "use_tfidf_weighting" in norm_data:
                self.config.normalisation.use_tfidf_weighting = norm_data["use_tfidf_weighting"]
            
            if "importance_weights" in norm_data:
                self.config.normalisation.importance_weights.update(norm_data["importance_weights"])
        
        # Update similarity config
        if "similarity" in config_data:
            sim_data = config_data["similarity"]
            
            if "method" in sim_data:
                self.config.similarity.method = sim_data["method"]
            
            if "threshold" in sim_data:
                self.config.similarity.threshold = sim_data["threshold"]
            
            if "top_n_results" in sim_data:
                self.config.similarity.top_n_results = sim_data["top_n_results"]
        
        # Update gap analysis config
        if "gap_analysis" in config_data:
            gap_data = config_data["gap_analysis"]
            
            if "min_proficiency_ratio" in gap_data:
                self.config.gap_analysis.min_proficiency_ratio = gap_data["min_proficiency_ratio"]
            
            if "skill_difficulty_factor" in gap_data:
                self.config.gap_analysis.skill_difficulty_factor = gap_data["skill_difficulty_factor"]
            
            if "category_weights" in gap_data:
                self.config.gap_analysis.category_weights.update(gap_data["category_weights"])
    
    def get_config(self) -> AppConfig:
        """
        Get the current application configuration.
        
        Returns:
            The current application configuration
        """
        return self.config
    
    def get_data_path(self, filename: str) -> str:
        """
        Get the full path to a data file.
        
        Args:
            filename: Name of the data file
            
        Returns:
            Full path to the data file
        """
        return os.path.join(self.config.data_dir, filename)
    
    def get_output_path(self, filename: str) -> str:
        """
        Get the full path to an output file.
        
        Args:
            filename: Name of the output file
            
        Returns:
            Full path to the output file
        """
        return os.path.join(self.config.output_dir, filename)


# Singleton instance
config_manager = ConfigManager()


def load_config(config_path: str) -> None:
    """
    Load configuration from a file.
    
    Args:
        config_path: Path to the configuration file
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
        ValueError: If the config file format is invalid
        jsonschema.exceptions.ValidationError: If the config is invalid
    """
    config_manager.load_config(config_path)


def get_config() -> AppConfig:
    """
    Get the current application configuration.
    
    Returns:
        The current application configuration
    """
    return config_manager.get_config()


def get_data_path(filename: str) -> str:
    """
    Get the full path to a data file.
    
    Args:
        filename: Name of the data file
        
    Returns:
        Full path to the data file
    """
    return config_manager.get_data_path(filename)


def get_output_path(filename: str) -> str:
    """
    Get the full path to an output file.
    
    Args:
        filename: Name of the output file
        
    Returns:
        Full path to the output file
    """
    return config_manager.get_output_path(filename)
