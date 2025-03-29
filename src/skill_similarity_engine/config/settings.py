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
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    normalisation: NormalisationConfig = field(default_factory=NormalisationConfig)
    similarity: SimilarityConfig = field(default_factory=SimilarityConfig)
    gap_analysis: GapAnalysisConfig = field(default_factory=GapAnalysisConfig)
    opportunity: OpportunityConfig = field(default_factory=OpportunityConfig)
    reporting: ReportingConfig = field(default_factory=ReportingConfig)
    heatmaps: HeatmapConfig = field(default_factory=HeatmapConfig)
    team_analysis: TeamAnalysisConfig = field(default_factory=TeamAnalysisConfig)
    workforce: WorkforceConfig = field(default_factory=WorkforceConfig)
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
        
        # Set logging config
        if 'logging' in config_data:
            log_config = config_data['logging']
            if 'level' in log_config:
                self._config.logging.level = log_config['level']
            if 'log_dir' in log_config:
                self._config.logging.log_dir = log_config['log_dir']
            if 'log_file' in log_config:
                self._config.logging.log_file = log_config['log_file']
            if 'console_output' in log_config:
                self._config.logging.console_output = log_config['console_output']
            if 'file_output' in log_config:
                self._config.logging.file_output = log_config['file_output']
            if 'max_file_size_mb' in log_config:
                self._config.logging.max_file_size_mb = log_config['max_file_size_mb']
            if 'backup_count' in log_config:
                self._config.logging.backup_count = log_config['backup_count']
                
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
        
        # Set reporting config
        if 'reporting' in config_data:
            rep_config = config_data['reporting']
            if 'include_headers' in rep_config:
                self._config.reporting.include_headers = rep_config['include_headers']
            if 'date_format' in rep_config:
                self._config.reporting.date_format = rep_config['date_format']
            if 'float_format' in rep_config:
                self._config.reporting.float_format = rep_config['float_format']
            if 'include_index' in rep_config:
                self._config.reporting.include_index = rep_config['include_index']
            if 'encoding' in rep_config:
                self._config.reporting.encoding = rep_config['encoding']
            if 'json_indent' in rep_config:
                self._config.reporting.json_indent = rep_config['json_indent']
                
        # Set heatmap config
        if 'heatmaps' in config_data:
            hm_config = config_data['heatmaps']
            if 'default_colormap' in hm_config:
                self._config.heatmaps.default_colormap = hm_config['default_colormap']
            if 'default_figsize' in hm_config:
                self._config.heatmaps.default_figsize = tuple(hm_config['default_figsize'])
            if 'show_annotations' in hm_config:
                self._config.heatmaps.show_annotations = hm_config['show_annotations']
            if 'annotation_format' in hm_config:
                self._config.heatmaps.annotation_format = hm_config['annotation_format']
            if 'line_width' in hm_config:
                self._config.heatmaps.line_width = hm_config['line_width']
            if 'show_colorbar' in hm_config:
                self._config.heatmaps.show_colorbar = hm_config['show_colorbar']
            if 'mask_diagonal' in hm_config:
                self._config.heatmaps.mask_diagonal = hm_config['mask_diagonal']
            if 'cluster_by_default' in hm_config:
                self._config.heatmaps.cluster_by_default = hm_config['cluster_by_default']
            if 'dpi' in hm_config:
                self._config.heatmaps.dpi = hm_config['dpi']
                
        # Set team analysis config
        if 'team_analysis' in config_data:
            team_config = config_data['team_analysis']
            if 'fully_covered_weight' in team_config:
                self._config.team_analysis.fully_covered_weight = team_config['fully_covered_weight']
            if 'partially_covered_weight' in team_config:
                self._config.team_analysis.partially_covered_weight = team_config['partially_covered_weight']
            if 'reskilling_difficulty_levels' in team_config:
                self._config.team_analysis.reskilling_difficulty_levels = team_config['reskilling_difficulty_levels']
                
        # Set workforce config
        if 'workforce' in config_data:
            wf_config = config_data['workforce']
            if 'critical_skill_threshold' in wf_config:
                self._config.workforce.critical_skill_threshold = wf_config['critical_skill_threshold']
            if 'max_skills_in_report' in wf_config:
                self._config.workforce.max_skills_in_report = wf_config['max_skills_in_report']
            if 'department_skill_coverage_threshold' in wf_config:
                self._config.workforce.department_skill_coverage_threshold = wf_config['department_skill_coverage_threshold']
        
        # Set future extensions config
        if 'future_extensions' in config_data:
            ext_config = config_data['future_extensions']
            if 'seniority_weight' in ext_config:
                self._config.future_extensions.seniority_weight = ext_config['seniority_weight']
            if 'role_track_weight' in ext_config:
                self._config.future_extensions.role_track_weight = ext_config['role_track_weight']
            if 'location_weight' in ext_config:
                self._config.future_extensions.location_weight = ext_config['location_weight']
                
        # Validate the config
        self._validate_config()
        
    def _validate_config(self):
        """
        Validate the configuration.
        
        Raises:
            ValueError: If validation fails
        """
        # Ensure data_dir and output_dir are valid
        data_dir = Path(self._config.data_dir)
        output_dir = Path(self._config.output_dir)
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_data_path(self, relative_path=""):
        """
        Get the absolute path to a data file or directory.
        
        Args:
            relative_path: Relative path within the data directory
            
        Returns:
            Absolute path
        """
        # Convert to Path objects to handle path concatenation properly
        data_dir = Path(self._config.data_dir)
        
        # Handle absolute and relative paths
        if os.path.isabs(self._config.data_dir):
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
        output_dir = Path(self._config.output_dir)
        
        # Handle absolute and relative paths
        if os.path.isabs(self._config.output_dir):
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
    return _config_manager.get_config()


def get_data_path(relative_path=""):
    """
    Get the absolute path to a data file or directory.
    
    Args:
        relative_path: Relative path within the data directory
        
    Returns:
        Absolute path
    """
    return _config_manager.get_data_path(relative_path)


def get_output_path(relative_path=""):
    """
    Get the absolute path to an output file or directory.
    
    Args:
        relative_path: Relative path within the output directory
        
    Returns:
        Absolute path
    """
    return _config_manager.get_output_path(relative_path)
