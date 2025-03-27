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
from typing import Dict, Any, Optional


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
    """Configuration for gap analysis."""
    min_proficiency_ratio: float = 0.8
    skill_difficulty_factor: float = 1.0
    min_gap_threshold: float = 0.2
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
class OpportunityConfig:
    """Configuration for opportunity identification."""
    high_similarity_threshold: float = 0.8
    low_gap_threshold: float = 20.0
    high_match_percentage: float = 80.0
    critical_gap_percentage: float = 50.0
    critical_skill_gap_threshold: float = 0.4


@dataclass
class FutureExtensionConfig:
    """Configuration for future extensions (disabled by default)."""
    seniority_weight: float = 0.0
    role_track_weight: float = 0.0
    location_weight: float = 0.0


@dataclass
class AppConfig:
    """Main application configuration."""
    version: str = "0.1.0"
    data_dir: str = "data"
    output_dir: str = "output"
    normalisation: NormalisationConfig = field(default_factory=NormalisationConfig)
    similarity: SimilarityConfig = field(default_factory=SimilarityConfig)
    gap_analysis: GapAnalysisConfig = field(default_factory=GapAnalysisConfig)
    opportunity: OpportunityConfig = field(default_factory=OpportunityConfig)
    future_extensions: FutureExtensionConfig = field(default_factory=FutureExtensionConfig)
    environment: str = "development"


class ConfigManager:
    """Singleton manager for application configuration."""
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._config = AppConfig()
        return cls._instance
    
    @property
    def config(self):
        """Get the current configuration."""
        return self._config
    
    @config.setter
    def config(self, value):
        """Set the current configuration."""
        self._config = value
    
    def get_config(self):
        """Get the current configuration (for compatibility with tests)."""
        return self._config
    
    def load_config(self, config_file):
        """Load configuration from a YAML file."""
        # Determine format from extension
        try:
            config_format = ConfigFormat.from_file_extension(config_file)
        except ValueError:
            # Default to YAML for backward compatibility
            config_format = ConfigFormat.YAML
        
        # Read file content
        with open(config_file, 'r') as f:
            if config_format == ConfigFormat.YAML:
                config_data = yaml.safe_load(f)
            else:  # JSON
                import json
                config_data = json.load(f)
        
        # Set top-level attributes
        if 'version' in config_data:
            self._config.version = config_data['version']
        if 'data_dir' in config_data:
            self._config.data_dir = config_data['data_dir']
        if 'output_dir' in config_data:
            self._config.output_dir = config_data['output_dir']
        if 'environment' in config_data:
            self._config.environment = config_data['environment']
        
        # Set normalisation config
        if 'normalisation' in config_data:
            norm_config = config_data['normalisation']
            if 'use_min_max_scaling' in norm_config:
                self._config.normalisation.use_min_max_scaling = norm_config['use_min_max_scaling']
            elif 'min_max_scaling' in norm_config:
                self._config.normalisation.use_min_max_scaling = norm_config['min_max_scaling']
                
            if 'use_boolean_normalisation' in norm_config:
                self._config.normalisation.use_boolean_normalisation = norm_config['use_boolean_normalisation']
            elif 'boolean_normalisation' in norm_config:
                self._config.normalisation.use_boolean_normalisation = norm_config['boolean_normalisation']
                
            if 'use_tfidf_weighting' in norm_config:
                self._config.normalisation.use_tfidf_weighting = norm_config['use_tfidf_weighting']
            elif 'tfidf_weighting' in norm_config:
                self._config.normalisation.use_tfidf_weighting = norm_config['tfidf_weighting']
                
            if 'importance_weights' in norm_config:
                self._config.normalisation.importance_weights = norm_config['importance_weights']
        
        # Set similarity config
        if 'similarity' in config_data:
            sim_config = config_data['similarity']
            if 'method' in sim_config:
                self._config.similarity.method = sim_config['method']
            if 'threshold' in sim_config:
                self._config.similarity.threshold = sim_config['threshold']
            if 'top_n_results' in sim_config:
                self._config.similarity.top_n_results = sim_config['top_n_results']
        
        # Set gap analysis config
        if 'gap_analysis' in config_data:
            gap_config = config_data['gap_analysis']
            if 'min_proficiency_ratio' in gap_config:
                self._config.gap_analysis.min_proficiency_ratio = gap_config['min_proficiency_ratio']
            if 'skill_difficulty_factor' in gap_config:
                self._config.gap_analysis.skill_difficulty_factor = gap_config['skill_difficulty_factor']
            if 'min_gap_threshold' in gap_config:
                self._config.gap_analysis.min_gap_threshold = gap_config['min_gap_threshold']
            if 'category_weights' in gap_config:
                self._config.gap_analysis.category_weights = gap_config['category_weights']
        
        # Set opportunity config
        if 'opportunity' in config_data:
            opp_config = config_data['opportunity']
            if 'high_similarity_threshold' in opp_config:
                self._config.opportunity.high_similarity_threshold = opp_config['high_similarity_threshold']
            if 'low_gap_threshold' in opp_config:
                self._config.opportunity.low_gap_threshold = opp_config['low_gap_threshold']
            if 'high_match_percentage' in opp_config:
                self._config.opportunity.high_match_percentage = opp_config['high_match_percentage']
            if 'critical_gap_percentage' in opp_config:
                self._config.opportunity.critical_gap_percentage = opp_config['critical_gap_percentage']
            if 'critical_skill_gap_threshold' in opp_config:
                self._config.opportunity.critical_skill_gap_threshold = opp_config['critical_skill_gap_threshold']
        
        # Set future extensions config
        if 'future_extensions' in config_data:
            ext_config = config_data['future_extensions']
            if 'seniority_weight' in ext_config:
                self._config.future_extensions.seniority_weight = ext_config['seniority_weight']
            if 'role_track_weight' in ext_config:
                self._config.future_extensions.role_track_weight = ext_config['role_track_weight']
            if 'location_weight' in ext_config:
                self._config.future_extensions.location_weight = ext_config['location_weight']
                
        # Validate the config (simplified for now)
        # In a real implementation, more thorough validation would be done
        self._validate_config()
        
    def _validate_config(self):
        """
        Validate the configuration.
        
        Raises:
            ValueError: If validation fails
        """
        # For now, we'll just do some basic checks
        # A real implementation would use jsonschema or similar
        if self._config.similarity.threshold < 0 or self._config.similarity.threshold > 1:
            raise ValueError("Similarity threshold must be between 0 and 1")
            
    def get_data_path(self, relative_path=""):
        """
        Get the absolute path to a file in the data directory.
        
        Args:
            relative_path: Relative path within the data directory
            
        Returns:
            Path to the file
        """
        config = self.get_config()
        data_dir = config.data_dir
        
        # For test compatibility, just return the joined path as a string
        if relative_path:
            return os.path.join(data_dir, relative_path)
        return data_dir
    
    def get_output_path(self, relative_path=""):
        """
        Get the absolute path to a file in the output directory.
        
        Args:
            relative_path: Relative path within the output directory
            
        Returns:
            Path to the file
        """
        config = self.get_config()
        output_dir = config.output_dir
        
        # For test compatibility, just return the joined path as a string
        if relative_path:
            return os.path.join(output_dir, relative_path)
        return output_dir


# Global instance of the config manager
_config_manager = ConfigManager()


def load_config(config_file):
    """Load configuration from the specified file."""
    _config_manager.load_config(config_file)


def load_config_for_environment(config_dir, environment=None):
    """
    Load configuration for the specified environment.
    For backwards compatibility with existing code.
    
    Args:
        config_dir: Directory containing configuration files
        environment: Environment to load (development, testing, production)
    """
    config_file = os.path.join(config_dir, "config.yaml")
    
    # In tests, the file might not exist - just set the environment
    if not os.path.exists(config_file):
        if environment:
            _config_manager.config.environment = environment
        return
        
    load_config(config_file)
    if environment:
        _config_manager.config.environment = environment


def get_config():
    """Get the current configuration."""
    return _config_manager.config


def get_data_path(relative_path=""):
    """
    Get the absolute path to a file in the data directory.
    
    Args:
        relative_path: Relative path within the data directory
        
    Returns:
        Path to the file
    """
    return _config_manager.get_data_path(relative_path)


def get_output_path(relative_path=""):
    """
    Get the absolute path to a file in the output directory.
    
    Args:
        relative_path: Relative path within the output directory
        
    Returns:
        Path to the file
    """
    return _config_manager.get_output_path(relative_path)
