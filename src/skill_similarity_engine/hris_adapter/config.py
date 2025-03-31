"""
HRIS Configuration Module.

This module provides functionality to load and manage HRIS schema mapping configuration.
"""

import os
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path


class HRISConfigError(Exception):
    """Exception raised for errors in the HRIS configuration."""
    pass


class HRISConfigLoader:
    """
    Loader for HRIS configuration from YAML files.
    
    Attributes:
        config (dict): The loaded configuration
        config_path (str): Path to the configuration file
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the HRIS configuration loader.
        
        Args:
            config_path: Path to the configuration file (default: use default path)
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """
        Get the default configuration path.
        
        Returns:
            Default path to the configuration file
        """
        # Try several possible locations
        possible_paths = [
            # Current directory
            os.path.join(os.getcwd(), "hris_schema_mapping.yaml"),
            # Config directory
            os.path.join(os.getcwd(), "config", "hris_schema_mapping.yaml"),
            # Project root config directory
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                        "config", "hris_schema_mapping.yaml"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        raise HRISConfigError("Could not find HRIS schema mapping configuration file")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load the configuration from the file.
        
        Returns:
            Loaded configuration as a dictionary
        
        Raises:
            HRISConfigError: If the configuration file cannot be loaded
        """
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
            
            self._validate_config(config)
            return config
        except Exception as e:
            raise HRISConfigError(f"Failed to load HRIS configuration: {e}")
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate the configuration structure.
        
        Args:
            config: Configuration to validate
        
        Raises:
            HRISConfigError: If the configuration is invalid
        """
        # Check required sections
        required_sections = ["hris_data", "output_data", "jobs_mapping", "skills_mapping"]
        for section in required_sections:
            if section not in config:
                raise HRISConfigError(f"Missing required configuration section: {section}")
        
        # Check required job mapping fields
        required_job_fields = ["job_id", "title", "department", "level"]
        for field in required_job_fields:
            if field not in config["jobs_mapping"]:
                raise HRISConfigError(f"Missing required job mapping field: {field}")
        
        # Check required skill mapping fields
        required_skill_fields = ["skill_id", "name"]
        for field in required_skill_fields:
            if field not in config["skills_mapping"]:
                raise HRISConfigError(f"Missing required skill mapping field: {field}")
    
    def get_hris_data_paths(self) -> Dict[str, str]:
        """
        Get the paths to HRIS data files.
        
        Returns:
            Dictionary of HRIS data file paths
        """
        return {
            "jobs_file": self.config["hris_data"]["jobs_file"],
            "skills_file": self.config["hris_data"]["skills_file"],
            "job_skills_file": self.config.get("hris_data", {}).get("job_skills_file")
        }
    
    def get_output_data_paths(self) -> Dict[str, str]:
        """
        Get the paths to output data files.
        
        Returns:
            Dictionary of output data file paths
        """
        return {
            "jobs_file": self.config["output_data"]["jobs_file"],
            "skills_file": self.config["output_data"]["skills_file"]
        }
    
    def get_jobs_mapping(self) -> Dict[str, str]:
        """
        Get the job field mappings.
        
        Returns:
            Dictionary mapping engine fields to HRIS columns
        """
        return self.config["jobs_mapping"]
    
    def get_skills_mapping(self) -> Dict[str, str]:
        """
        Get the skill field mappings.
        
        Returns:
            Dictionary mapping engine fields to HRIS columns
        """
        return self.config["skills_mapping"]
    
    def get_job_skills_mapping(self) -> Dict[str, str]:
        """
        Get the job-skills mapping.
        
        Returns:
            Dictionary mapping engine fields to HRIS columns for job-skills relationship
        """
        return self.config.get("job_skills_mapping", {})
    
    def get_value_mappings(self) -> Dict[str, Dict]:
        """
        Get all value mapping dictionaries.
        
        Returns:
            Dictionary of value mapping dictionaries
        """
        return {
            "salary_group": self.config.get("salary_group_mapping", {}),
            "role_track": self.config.get("role_track_mapping", {}),
            "skill_type": self.config.get("skill_type_mapping", {})
        }
    
    def get_transformation_options(self) -> Dict[str, Any]:
        """
        Get transformation options.
        
        Returns:
            Dictionary of transformation options
        """
        return self.config.get("transformation_options", {})
    
    def get_file_format_options(self) -> Dict[str, Any]:
        """
        Get file format options.
        
        Returns:
            Dictionary of file format options
        """
        return {
            "file_format": self.config["hris_data"].get("file_format", "csv"),
            "encoding": self.config["hris_data"].get("encoding", "utf-8"),
            "delimiter": self.config["hris_data"].get("delimiter", ","),
            "has_header": self.config["hris_data"].get("has_header", True),
            "sheet_name": self.config["hris_data"].get("sheet_name", "Sheet1")
        }
    
    def get_logging_options(self) -> Dict[str, Any]:
        """
        Get logging options.
        
        Returns:
            Dictionary of logging options
        """
        return self.config.get("logging", {}) 