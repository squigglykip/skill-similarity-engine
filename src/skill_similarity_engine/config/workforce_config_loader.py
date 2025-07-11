#!/usr/bin/env python3
"""
Workforce Configuration Loader

Integrates Position Transition History's configuration-driven architecture 
into Skill Similarity Engine. Provides centralized configuration management
for workforce intelligence data sources and processing parameters.

Based on PTH's ConfigLoader patterns with enhancements for SSE integration.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class WorkforceConfigurationError(Exception):
    """Raised when configuration loading or validation fails."""
    pass


@dataclass
class DatasetConfig:
    """Configuration for a specific dataset."""
    name: str
    field_mappings: Dict[str, str]
    data_types: Dict[str, str]
    validation_rules: Dict[str, Any]
    source_file_pattern: str
    description: str


class WorkforceConfigLoader:
    """
    Centralized configuration loader for workforce intelligence data.
    
    Implements PTH's Configuration-Driven Architecture pattern within SSE,
    enabling clean separation between configuration and processing logic.
    """
    
    def __init__(self, config_directory: Optional[str] = None):
        """
        Initialize workforce configuration loader.
        
        Args:
            config_directory: Path to config directory (defaults to SSE's config/)
        """
        if config_directory:
            self.config_dir = Path(config_directory)
        else:
            # Default to SSE's config directory
            current_file = Path(__file__)
            sse_root = current_file.parent.parent.parent.parent  # Navigate to SSE root
            self.config_dir = sse_root / "config"
        
        # Configuration file paths
        self.field_mappings_path = self.config_dir / "data" / "field_mappings.yaml"
        self.operational_config_path = self.config_dir / "operational_config.yaml"
        
        # Configuration cache
        self._field_mappings_config: Optional[Dict[str, Any]] = None
        self._operational_config: Optional[Dict[str, Any]] = None
        self._legacy_data_sources: Optional[Dict[str, Any]] = None
        
        if not self.config_dir.exists():
            raise WorkforceConfigurationError(f"Configuration directory not found: {self.config_dir}")
        
        logger.info(f"🔧 Initialized WorkforceConfigLoader with config dir: {self.config_dir}")
    
    def load_field_mappings_config(self) -> Dict[str, Any]:
        """
        Load the data field mappings configuration.
        
        Returns:
            Dictionary containing field mappings and data schemas
        """
        if self._field_mappings_config is None:
            self._field_mappings_config = self._load_yaml_file(self.field_mappings_path)
            logger.info(f"✅ Loaded field mappings from {self.field_mappings_path}")
        
        return self._field_mappings_config
    
    def load_operational_config(self) -> Dict[str, Any]:
        """
        Load the operational configuration.
        
        Returns:
            Dictionary containing operational settings and performance parameters
        """
        if self._operational_config is None:
            self._operational_config = self._load_yaml_file(self.operational_config_path)
            logger.info(f"✅ Loaded operational config from {self.operational_config_path}")
        
        return self._operational_config
    
    def load_workforce_data_schema(self) -> Dict[str, Any]:
        """
        Load the complete workforce configuration (backward compatibility).
        
        Returns:
            Dictionary containing complete workforce data schema (merged from both files)
        """
        field_mappings = self.load_field_mappings_config()
        operational = self.load_operational_config()
        
        # Merge configurations for backward compatibility
        merged_config = field_mappings.copy()
        merged_config['global_settings'] = operational
        
        return merged_config
    
    def load_legacy_data_sources(self) -> Dict[str, Any]:
        """
        Load legacy data sources configuration for backward compatibility.
        
        Returns:
            Dictionary containing legacy data sources configuration
        """
        if self._legacy_data_sources is None:
            legacy_path = self.config_dir / "data_sources_legacy.yaml"
            if legacy_path.exists():
                self._legacy_data_sources = self._load_yaml_file(legacy_path)
                logger.info(f"📜 Loaded legacy data sources from {legacy_path}")
            else:
                logger.warning(f"⚠️ Legacy data sources file not found: {legacy_path}")
                self._legacy_data_sources = {}
        
        return self._legacy_data_sources
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse YAML configuration file with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                if config is None:
                    raise WorkforceConfigurationError(f"Empty configuration file: {file_path}")
                return config
        except FileNotFoundError:
            raise WorkforceConfigurationError(f"Configuration file not found: {file_path}")
        except yaml.YAMLError as e:
            raise WorkforceConfigurationError(f"Invalid YAML in {file_path}: {e}")
        except Exception as e:
            raise WorkforceConfigurationError(f"Error loading {file_path}: {e}")
    
    # === DATASET CONFIGURATION ACCESS METHODS ===
    
    def get_dataset_config(self, dataset_name: str) -> DatasetConfig:
        """
        Get configuration for a specific dataset.
        
        Args:
            dataset_name: Name of dataset (e.g., 'colleague_positions', 'positions')
            
        Returns:
            DatasetConfig object with all dataset configuration
        """
        field_mappings_config = self.load_field_mappings_config()
        
        # Check if dataset exists in configuration
        if dataset_name not in field_mappings_config:
            available = [key for key in field_mappings_config.keys()]
            raise WorkforceConfigurationError(
                f"Dataset '{dataset_name}' not found in field mappings. "
                f"Available datasets: {available}"
            )
        
        dataset_config = field_mappings_config[dataset_name]
        
        return DatasetConfig(
            name=dataset_name,
            field_mappings=dataset_config.get('field_mappings', {}),
            data_types=dataset_config.get('data_types', {}),
            validation_rules=dataset_config.get('validation', {}),
            source_file_pattern=dataset_config.get('source_file_pattern', '*.csv'),
            description=dataset_config.get('description', f'Configuration for {dataset_name}')
        )
    
    def get_field_mappings(self, dataset_name: str) -> Dict[str, str]:
        """
        Get field mappings for external -> internal field names.
        
        Args:
            dataset_name: Name of dataset
            
        Returns:
            Dictionary mapping external field names to internal standardised names
        """
        dataset_config = self.get_dataset_config(dataset_name)
        return dataset_config.field_mappings
    
    def get_data_types(self, dataset_name: str) -> Dict[str, str]:
        """
        Get data type specifications for a dataset.
        
        Args:
            dataset_name: Name of dataset
            
        Returns:
            Dictionary mapping internal field names to data types
        """
        dataset_config = self.get_dataset_config(dataset_name)
        return dataset_config.data_types
    
    def get_validation_rules(self, dataset_name: str) -> Dict[str, Any]:
        """
        Get validation rules for a dataset.
        
        Args:
            dataset_name: Name of dataset
            
        Returns:
            Dictionary containing validation rules (required fields, constraints, etc.)
        """
        dataset_config = self.get_dataset_config(dataset_name)
        return dataset_config.validation_rules
    
    def get_source_file_pattern(self, dataset_name: str) -> str:
        """
        Get file pattern for loading dataset files.
        
        Args:
            dataset_name: Name of dataset
            
        Returns:
            Glob pattern for matching dataset files
        """
        dataset_config = self.get_dataset_config(dataset_name)
        return dataset_config.source_file_pattern
    
    # === GLOBAL SETTINGS ACCESS METHODS ===
    
    def get_global_settings(self) -> Dict[str, Any]:
        """
        Get global configuration settings.
        
        Returns:
            Dictionary containing global settings (date formats, performance, etc.)
        """
        operational_config = self.load_operational_config()
        return operational_config
    
    def get_performance_settings(self) -> Dict[str, Any]:
        """
        Get performance optimization settings.
        
        Returns:
            Dictionary containing performance settings (chunk sizes, parallel workers, etc.)
        """
        global_settings = self.get_global_settings()
        return global_settings.get('performance', {})
    
    def get_date_format(self, dataset_name: Optional[str] = None) -> str:
        """
        Get date format for a dataset or global default.
        
        Args:
            dataset_name: Optional dataset name for dataset-specific format
            
        Returns:
            Date format string (e.g., '%d/%m/%Y')
        """
        if dataset_name:
            validation_rules = self.get_validation_rules(dataset_name)
            if 'date_format' in validation_rules:
                return validation_rules['date_format']
        
        # Fallback to global default
        global_settings = self.get_global_settings()
        return global_settings.get('default_date_format', '%Y-%m-%d')
    
    def get_boolean_mappings(self) -> Dict[str, List[str]]:
        """
        Get boolean value mappings from global settings.
        
        Returns:
            Dictionary with 'true' and 'false' value lists
        """
        global_settings = self.get_global_settings()
        return {
            'true': global_settings.get('boolean_true_values', ['TRUE', 'True', '1', 'YES', 'Y']),
            'false': global_settings.get('boolean_false_values', ['FALSE', 'False', '0', 'NO', 'N'])
        }
    
    def get_null_representations(self) -> List[str]:
        """
        Get list of strings that represent null/missing values.
        
        Returns:
            List of null representation strings
        """
        global_settings = self.get_global_settings()
        return global_settings.get('null_representations', ['', 'nan', 'null', 'NULL', 'None'])
    
    # === PERFORMANCE OPTIMIZATION ACCESS METHODS ===
    
    def get_default_chunk_size(self, operation_type: str = 'default') -> int:
        """
        Get default chunk size for specific operations.
        
        Args:
            operation_type: Type of operation (e.g., 'movement_analysis', 'similarity_calc')
            
        Returns:
            Recommended chunk size
        """
        performance = self.get_performance_settings()
        chunk_sizes = performance.get('chunk_sizes', {})
        
        # Load fallback from architectural config manager
        try:
            from .architectural_config_manager import get_config_manager
            config_manager = get_config_manager()
            fallback_chunk_size = config_manager.get_nested_value(
                'configuration_management', 'performance', 'chunk_size_default', default=10000
            )
        except Exception:
            fallback_chunk_size = 10000
        
        return chunk_sizes.get(operation_type, chunk_sizes.get('default', fallback_chunk_size))
    
    def get_parallel_workers(self, operation_type: str = 'default') -> Optional[int]:
        """
        Get recommended number of parallel workers.
        
        Args:
            operation_type: Type of operation
            
        Returns:
            Number of workers or None for auto-detection
        """
        performance = self.get_performance_settings()
        workers = performance.get('parallel_workers', {})
        return workers.get(operation_type, workers.get('default'))
    
    def get_memory_limits(self) -> Dict[str, int]:
        """
        Get memory limits for different operations.
        
        Returns:
            Dictionary with memory limits in MB
        """
        performance = self.get_performance_settings()
        return performance.get('memory_limits', {
            'movement_analysis': 8000,  # 8GB default
            'similarity_calculation': 12000,  # 12GB default
            'default': 4000  # 4GB default
        })
    
    # === DATASET LISTING AND DISCOVERY ===
    
    def list_available_datasets(self) -> List[str]:
        """
        Get list of all available datasets in configuration.
        
        Returns:
            List of dataset names
        """
        config = self.load_workforce_data_schema()
        return [key for key in config.keys() if not key.startswith('global_')]
    
    def get_movement_analysis_datasets(self) -> List[str]:
        """
        Get list of datasets required for movement analysis.
        
        Returns:
            List of dataset names required for movement analysis
        """
        datasets = self.list_available_datasets()
        # Filter for movement analysis specific datasets
        movement_datasets = [
            name for name in datasets 
            if any(keyword in name.lower() for keyword in ['colleague', 'position', 'movement'])
        ]
        return movement_datasets
    
    def get_similarity_calculation_datasets(self) -> List[str]:
        """
        Get list of datasets required for similarity calculations.
        
        Returns:
            List of dataset names required for similarity calculations
        """
        datasets = self.list_available_datasets()
        # Filter for similarity calculation specific datasets
        similarity_datasets = [
            name for name in datasets 
            if any(keyword in name.lower() for keyword in ['skill', 'job', 'architecture'])
        ]
        return similarity_datasets
    
    # === VALIDATION AND DIAGNOSTICS ===
    
    def validate_configuration(self) -> bool:
        """
        Validate the loaded configuration for completeness and consistency.
        
        Returns:
            True if configuration is valid
            
        Raises:
            WorkforceConfigurationError: If configuration is invalid
        """
        try:
            config = self.load_workforce_data_schema()
            
            # Check for required global settings
            if 'global_settings' not in config:
                raise WorkforceConfigurationError("Missing 'global_settings' section")
            
            # Validate each dataset configuration
            datasets = self.list_available_datasets()
            if not datasets:
                raise WorkforceConfigurationError("No datasets found in configuration")
            
            for dataset_name in datasets:
                dataset_config = self.get_dataset_config(dataset_name)
                
                # Check for required fields
                if not dataset_config.field_mappings:
                    logger.warning(f"⚠️ Dataset '{dataset_name}' has no field mappings")
                
                if not dataset_config.data_types:
                    logger.warning(f"⚠️ Dataset '{dataset_name}' has no data types specified")
            
            logger.info("✅ Configuration validation completed successfully")
            return True
            
        except Exception as e:
            raise WorkforceConfigurationError(f"Configuration validation failed: {e}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get summary of loaded configuration.
        
        Returns:
            Dictionary with configuration summary statistics
        """
        try:
            datasets = self.list_available_datasets()
            total_field_mappings = sum(
                len(self.get_field_mappings(dataset)) for dataset in datasets
            )
            
            return {
                'config_directory': str(self.config_dir),
                'total_datasets': len(datasets),
                'available_datasets': datasets,
                'total_field_mappings': total_field_mappings,
                'movement_analysis_datasets': self.get_movement_analysis_datasets(),
                'similarity_calculation_datasets': self.get_similarity_calculation_datasets(),
                'global_settings_loaded': 'global_settings' in self.load_workforce_data_schema(),
                'performance_settings_available': bool(self.get_performance_settings())
            }
        except Exception as e:
            return {'error': str(e)}


# === MODULE SINGLETON PATTERN ===

_workforce_config_loader: Optional[WorkforceConfigLoader] = None


def get_workforce_config_loader(config_directory: Optional[str] = None) -> WorkforceConfigLoader:
    """
    Get singleton instance of WorkforceConfigLoader.
    
    Args:
        config_directory: Optional config directory path
        
    Returns:
        WorkforceConfigLoader instance
    """
    global _workforce_config_loader
    
    if _workforce_config_loader is None:
        _workforce_config_loader = WorkforceConfigLoader(config_directory)
    
    return _workforce_config_loader


def reset_workforce_config_loader() -> None:
    """Reset the singleton instance (useful for testing)."""
    global _workforce_config_loader
    _workforce_config_loader = None


# === UTILITY FUNCTIONS ===

def validate_workforce_field_mapping(external_data: Dict[str, Any], 
                                    dataset_name: str,
                                    config_loader: Optional[WorkforceConfigLoader] = None) -> Dict[str, Any]:
    """
    Map external field names to internal field names using configuration.
    
    Args:
        external_data: Dictionary with external field names
        dataset_name: Name of dataset for field mapping
        config_loader: Optional config loader instance
        
    Returns:
        Dictionary with internal field names
    """
    if config_loader is None:
        config_loader = get_workforce_config_loader()
    
    field_mappings = config_loader.get_field_mappings(dataset_name)
    mapped_data = {}
    
    for external_field, internal_field in field_mappings.items():
        if external_field in external_data:
            mapped_data[internal_field] = external_data[external_field]
    
    return mapped_data


def get_workforce_dataset_file_paths(dataset_name: str, 
                                   data_directory: str,
                                   config_loader: Optional[WorkforceConfigLoader] = None) -> List[Path]:
    """
    Get file paths for a dataset using configuration-defined patterns.
    
    Args:
        dataset_name: Name of dataset
        data_directory: Directory containing data files
        config_loader: Optional config loader instance
        
    Returns:
        List of file paths matching the dataset pattern
    """
    if config_loader is None:
        config_loader = get_workforce_config_loader()
    
    pattern = config_loader.get_source_file_pattern(dataset_name)
    data_dir = Path(data_directory)
    
    # Use glob to find matching files
    return list(data_dir.glob(pattern)) 