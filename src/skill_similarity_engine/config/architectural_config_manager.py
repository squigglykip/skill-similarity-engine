"""
Enterprise Configuration Manager - Skill Similarity Engine

This module implements PTH's configuration-driven architecture philosophy:
- NO hardcoded values in any src/ module
- Complete externalization of configuration
- Enterprise design patterns (Strategy, Factory, Singleton)
- Domain-driven design with proper abstraction layers

Architecture: Configuration-Driven Design Pattern following PTH's enterprise patterns

ENHANCED: Phase 4 - Modular Configuration Support
- Hybrid loading: Support both monolithic and modular structures
- Backward compatibility: All existing APIs continue to work
- Performance optimization: Lazy loading of module configurations
- Enhanced discoverability: Module-specific configuration access
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass


class ConfigurationStrategy(ABC):
    """Strategy pattern for different configuration loading approaches."""
    
    @abstractmethod
    def load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from specified path."""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration structure and content."""
        pass


class YAMLConfigurationStrategy(ConfigurationStrategy):
    """YAML configuration loading strategy."""
    
    def load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.debug(f"Loaded YAML configuration from {config_path}")
            return config
        except Exception as e:
            raise ConfigurationError(f"Failed to load YAML configuration from {config_path}: {e}")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate YAML configuration structure."""
        required_sections = ['directories', 'files', 'processing', 'datetime']
        return all(section in config for section in required_sections)


class ModularConfigurationStrategy(ConfigurationStrategy):
    """Strategy for loading modular configuration structure."""
    
    def load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configurations from modular structure."""
        config = {}
        
        try:
            # Load core configurations
            core_config = self._load_core_configs(config_path / "core")
            config.update(core_config)
            
            # Load module configurations (structured by src modules)
            module_config = self._load_module_configs(config_path / "modules")
            config.update(module_config)
            
            # Load data configurations
            data_config = self._load_data_configs(config_path / "data")
            config.update(data_config)
            
            # Load integration configurations
            integration_config = self._load_integration_configs(config_path / "integration")
            config.update(integration_config)
            
            logger.info(f"✅ Loaded modular configuration from {config_path}")
            return config
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load modular configuration: {e}")
    
    def _load_core_configs(self, core_path: Path) -> Dict[str, Any]:
        """Load core infrastructure configurations."""
        config = {}
        
        if not core_path.exists():
            return config
            
        # Load directories configuration - special handling for top-level keys
        directories_file = core_path / 'directories.yaml'
        if directories_file.exists():
            directories_config = self._load_yaml_safe(directories_file)
            # Map directories directly to top-level + create directories section
            config['directories'] = {}
            config['files'] = {}
            
            for key, value in directories_config.items():
                if key == 'files':
                    config['files'].update(value)
                elif key not in ['files']:  # All other keys are directory configs
                    config['directories'][key] = value
        
        # Load other core files normally
        core_files = {
            'processing.yaml': ('processing',),
            'datetime.yaml': ('core',),  # SURGICAL FIX: Load datetime under core for core.datetime.* access
            'configuration_management.yaml': ('configuration_management',),
            'similarity_parameters.yaml': ('core',),
            'clustering_analysis.yaml': ('core',),
            'skills_clustering.yaml': ('core',),
            'file_patterns.yaml': ('workforce_data_patterns', 'skills_data_patterns', 'position_mapping_patterns', 'output_patterns', 'database_patterns')
        }
        
        for filename, sections in core_files.items():
            file_path = core_path / filename
            if file_path.exists():
                file_config = self._load_yaml_safe(file_path)
                
                # Special handling for similarity_parameters.yaml and clustering_analysis.yaml
                if filename == 'similarity_parameters.yaml':
                    # Create core section if it doesn't exist
                    if 'core' not in config:
                        config['core'] = {}
                    # Load the entire file content under core.similarity_parameters
                    config['core']['similarity_parameters'] = file_config
                elif filename == 'clustering_analysis.yaml':
                    # Create core section if it doesn't exist
                    if 'core' not in config:
                        config['core'] = {}
                    # Load the entire file content under core.clustering_analysis
                    config['core']['clustering_analysis'] = file_config
                elif filename == 'skills_clustering.yaml':
                    # Create core section if it doesn't exist
                    if 'core' not in config:
                        config['core'] = {}
                    # Load the entire file content under core.skills_clustering
                    config['core']['skills_clustering'] = file_config
                elif filename == 'datetime.yaml':
                    # SURGICAL FIX: Create core section if it doesn't exist
                    if 'core' not in config:
                        config['core'] = {}
                    # Load the entire file content under core.datetime for core.datetime.* access
                    config['core']['datetime'] = file_config
                else:
                    # Normal section-based loading for other files
                    for section in sections:
                        if section in file_config:
                            config[section] = file_config[section]
        
        return config
    
    def _load_module_configs(self, modules_path: Path) -> Dict[str, Any]:
        """Load module-specific configurations."""
        config = {}
        
        if not modules_path.exists():
            return config
        
        # Module mappings: directory -> config sections
        module_mappings = {
            'utils': 'utils',
            'similarity': ['similarity_module', 'similarity'],  # Map to both sections
            'models': 'models',
            'analysis': ['gap_analysis', 'team_analysis', 'workforce_analysis'],
            'api': 'api',
            'business_context': 'business_context',
            'error_handling': 'error_handling',
            'cli': 'cli',
            'data': 'data',
            'data_validation': 'data_validation',
            'logging': 'logging'
        }
        
        for module_dir in modules_path.iterdir():
            if module_dir.is_dir() and module_dir.name in module_mappings:
                module_config = self._load_module_directory(module_dir)
                
                # Map to expected configuration sections
                mapping = module_mappings[module_dir.name]
                if isinstance(mapping, str):
                    config[mapping] = module_config
                elif isinstance(mapping, list):
                    # Special handling for similarity module
                    if module_dir.name == 'similarity':
                        config['similarity_module'] = module_config
                        # Map legacy 'similarity' section to algorithms config with correct structure
                        if 'algorithms' in module_config:
                            config['similarity'] = module_config['algorithms']
                        else:
                            config['similarity'] = module_config  # Fallback to whole module
                    else:
                        # Handle analysis module (multiple sections)
                        for section_name in mapping:
                            section_key = section_name.split('_')[-1]  # e.g., 'gap_analysis' -> 'analysis'
                            if section_key in module_config:
                                config[section_name] = module_config[section_key]
        
        return config
    
    def _load_module_directory(self, module_path: Path) -> Dict[str, Any]:
        """Load all configuration files in a module directory."""
        module_config = {}
        
        for config_file in module_path.glob("*.yaml"):
            file_config = self._load_yaml_safe(config_file)
            # Use filename (without extension) as the key
            key = config_file.stem
            module_config[key] = file_config
        
        return module_config
    
    def _load_data_configs(self, data_path: Path) -> Dict[str, Any]:
        """Load data-specific configurations.""" 
        config = {}
        
        if not data_path.exists():
            return config
            
        data_files = {
            'field_mappings.yaml': 'field_mappings',
            'sources.yaml': 'data_sources', 
            'validation_schema.yaml': 'validation_schema'
        }
        
        for filename, section in data_files.items():
            file_path = data_path / filename
            if file_path.exists():
                config[section] = self._load_yaml_safe(file_path)
        
        return config
    
    def _load_integration_configs(self, integration_path: Path) -> Dict[str, Any]:
        """Load integration configurations."""
        config = {}
        
        if not integration_path.exists():
            return config
            
        for config_file in integration_path.glob("*.yaml"):
            file_config = self._load_yaml_safe(config_file)
            config[config_file.stem] = file_config
        
        return config
    
    def _load_yaml_safe(self, file_path: Path) -> Dict[str, Any]:
        """Safely load YAML file with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
            return {}
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate modular configuration structure."""
        # More lenient validation for modular structure
        essential_sections = ['directories', 'processing']
        return any(section in config for section in essential_sections)


class EnvironmentConfigurationStrategy(ConfigurationStrategy):
    """Environment variable configuration loading strategy."""
    
    def load_config(self, config_path: Path = None) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        
        # Map environment variables to configuration structure
        env_mappings = {
            'SSE_DATA_ROOT': ('directories', 'data_root'),
            'SSE_CONFIG_ROOT': ('directories', 'config_root'),
            'SSE_CHUNK_SIZE': ('processing', 'default_chunk_size'),
            'SSE_DATE_FORMAT': ('datetime', 'input_date_format'),
            'SSE_LOG_LEVEL': ('logging', 'default_level'),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                if section not in config:
                    config[section] = {}
                config[section][key] = value
        
        return config
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Environment configuration is always valid (optional override)."""
        return True


@dataclass
class ConfigurationPaths:
    """Enhanced configuration file paths with modular structure support."""
    
    # Legacy paths (for backward compatibility)
    architectural_config: Path
    data_sources: Path
    field_mappings: Path
    operational_config: Path
    
    # New modular structure paths
    core_config_dir: Optional[Path] = None
    modules_config_dir: Optional[Path] = None
    data_config_dir: Optional[Path] = None
    integration_config_dir: Optional[Path] = None
    
    @classmethod
    def discover(cls, base_path: Optional[Path] = None) -> 'ConfigurationPaths':
        """Discover both legacy and modular configuration paths."""
        if base_path is None:
            # Search upwards for config directory (like PTH pattern)
            current = Path.cwd()
            config_dir = None
            
            for _ in range(5):  # Search up to 5 levels
                candidate = current / "config"
                if candidate.is_dir():
                    config_dir = candidate
                    break
                current = current.parent
            
            if config_dir is None:
                raise ConfigurationError("Could not find 'config' directory in any parent directory")
        else:
            config_dir = base_path / "config"
        
        # Check for modular structure
        core_dir = config_dir / "core"
        modules_dir = config_dir / "modules"
        data_dir = config_dir / "data"
        integration_dir = config_dir / "integration"
        
        return cls(
            # Legacy paths
            architectural_config=config_dir / "architectural_config.yaml",
            data_sources=config_dir / "data_sources.yaml",
            field_mappings=config_dir / "data" / "field_mappings.yaml", 
            operational_config=config_dir / "operational_config.yaml",
            
            # Modular structure paths (may not exist)
            core_config_dir=core_dir if core_dir.exists() else None,
            modules_config_dir=modules_dir if modules_dir.exists() else None,
            data_config_dir=data_dir if data_dir.exists() else None,
            integration_config_dir=integration_dir if integration_dir.exists() else None
        )
    
    def has_modular_structure(self) -> bool:
        """Check if modular configuration structure exists."""
        return (self.modules_config_dir is not None and 
                self.modules_config_dir.exists() and
                any(self.modules_config_dir.iterdir()))


class ConfigurationAdapter:
    """Adapter pattern for configuration data access."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize configuration adapter."""
        self._config = config
    
    def get_path(self, path_key: str, section: str = 'directories') -> Path:
        """Get path configuration as Path object."""
        try:
            path_str = self._config[section][path_key]
            return Path(path_str)
        except KeyError:
            raise ConfigurationError(f"Path configuration not found: {section}.{path_key}")
    
    def get_file(self, file_key: str, section: str = 'files') -> Path:
        """Get file configuration as Path object."""
        try:
            file_str = self._config[section][file_key]
            return Path(file_str)
        except KeyError:
            raise ConfigurationError(f"File configuration not found: {section}.{file_key}")
    
    def get_value(self, key: str, section: str, default: Any = None) -> Any:
        """Get configuration value with optional default and variable substitution."""
        try:
            value = self._config[section][key]
            # Apply variable substitution if value is a string
            if isinstance(value, str):
                return self._substitute_variables(value)
            return value
        except KeyError:
            if default is not None:
                return default
            raise ConfigurationError(f"Configuration value not found: {section}.{key}")
    
    def _substitute_variables(self, value: str) -> str:
        """
        Substitute configuration variables in the format ${section.key}.
        
        Args:
            value: String that may contain variable references
            
        Returns:
            String with variables substituted from configuration
        """
        import re
        
        # Pattern to match ${section.key} or ${section.subsection.key}
        pattern = r'\$\{([^}]+)\}'
        
        def replace_var(match):
            var_path = match.group(1)
            path_parts = var_path.split('.')
            
            try:
                # Navigate through configuration using path parts
                current = self._config
                for part in path_parts:
                    current = current[part]
                
                # If the resolved value is also a string with variables, substitute recursively
                if isinstance(current, str) and '${' in current:
                    return self._substitute_variables(current)
                
                return str(current)
            except (KeyError, TypeError):
                logger.warning(f"Configuration variable not found: {var_path}")
                return match.group(0)  # Return original if not found
        
        return re.sub(pattern, replace_var, value)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section with variable substitution."""
        try:
            section_data = self._config[section]
            if isinstance(section_data, dict):
                return self._substitute_dict_variables(section_data)
            return section_data
        except KeyError:
            raise ConfigurationError(f"Configuration section not found: {section}")
    
    def get_nested_value(self, *keys, default: Any = None) -> Any:
        """Get nested configuration value using dot notation with variable substitution."""
        try:
            current = self._config
            for key in keys:
                current = current[key]
            
            # Apply variable substitution if value is a string
            if isinstance(current, str):
                return self._substitute_variables(current)
            elif isinstance(current, dict):
                # Recursively substitute variables in dictionary values
                return self._substitute_dict_variables(current)
            elif isinstance(current, list):
                # Recursively substitute variables in list items
                return self._substitute_list_variables(current)
            
            return current
        except (KeyError, TypeError):
            if default is not None:
                return default
            raise ConfigurationError(f"Configuration path not found: {'.'.join(keys)}")
    
    def _substitute_dict_variables(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively substitute variables in dictionary values."""
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._substitute_variables(value)
            elif isinstance(value, dict):
                result[key] = self._substitute_dict_variables(value)
            elif isinstance(value, list):
                result[key] = self._substitute_list_variables(value)
            else:
                result[key] = value
        return result
    
    def _substitute_list_variables(self, data: List[Any]) -> List[Any]:
        """Recursively substitute variables in list items."""
        result = []
        for item in data:
            if isinstance(item, str):
                result.append(self._substitute_variables(item))
            elif isinstance(item, dict):
                result.append(self._substitute_dict_variables(item))
            elif isinstance(item, list):
                result.append(self._substitute_list_variables(item))
            else:
                result.append(item)
        return result
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        try:
            return self._config[section]
        except KeyError:
            raise ConfigurationError(f"Configuration section not found: {section}")


class ArchitecturalConfigManager:
    """
    Enhanced Singleton configuration manager implementing PTH's enterprise patterns.
    
    ENHANCED for Modular Configuration Support:
    - Hybrid loading: Support both monolithic and modular structures
    - Backward compatibility: All existing APIs continue to work unchanged
    - Performance optimization: Lazy loading of module configurations
    - Enhanced discoverability: Module-specific configuration access
    
    This class eliminates ALL hardcoded values from SSE source code by:
    1. Loading comprehensive configuration from YAML files (monolithic or modular)
    2. Providing type-safe configuration access
    3. Supporting environment variable overrides
    4. Implementing fallback strategies for missing configurations
    5. Enforcing configuration validation
    """
    
    _instance: Optional['ArchitecturalConfigManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'ArchitecturalConfigManager':
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_base_path: Optional[Path] = None):
        """Initialize configuration manager (singleton pattern)."""
        if self._initialized:
            return
        
        self._config_base_path = config_base_path
        self._strategies = {
            'yaml': YAMLConfigurationStrategy(),
            'modular': ModularConfigurationStrategy(),
            'env': EnvironmentConfigurationStrategy()
        }
        self._config = {}
        self._adapter = None
        
        # Modular configuration support
        self._is_modular = False
        self._module_configs = {}
        self._configuration_metadata = {
            'structure_type': 'unknown',
            'files_loaded': [],
            'modules': [],
            'load_time': None
        }
        
        self._load_configuration()
        self._initialized = True
    
    def _load_configuration(self):
        """Enhanced configuration loading with modular support."""
        import time
        start_time = time.time()
        
        try:
            # Discover configuration file paths
            paths = ConfigurationPaths.discover(self._config_base_path)
            
            # Check if modular structure exists and prefer it
            if paths.has_modular_structure():
                self._load_modular_configuration(paths)
            else:
                self._load_legacy_configuration(paths)
            
            # Apply environment variable overrides
            env_overrides = self._strategies['env'].load_config()
            if env_overrides:
                self._merge_config(env_overrides, 'environment_overrides')
                logger.info("Applied environment variable overrides")
            
            # Create configuration adapter
            self._adapter = ConfigurationAdapter(self._config)
            
            # Update metadata
            self._configuration_metadata['load_time'] = time.time() - start_time
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._load_fallback_configuration()
            self._configuration_metadata['structure_type'] = 'fallback'
    
    def _load_modular_configuration(self, paths: ConfigurationPaths):
        """Load from new modular structure."""
        self._is_modular = True
        
        try:
            # Load modular configurations
            if paths.core_config_dir is None:
                raise ConfigurationError("Core config directory not found")
            config_root = paths.core_config_dir.parent
            modular_config = self._strategies['modular'].load_config(config_root)
            self._config.update(modular_config)
            
            # Cache module-specific configurations for performance
            self._cache_module_configs(paths.modules_config_dir)
            
            # Update metadata
            self._configuration_metadata.update({
                'structure_type': 'modular',
                'files_loaded': self._count_modular_files(config_root),
                'modules': list(self._module_configs.keys())
            })
            
            logger.info("✅ Loaded modular configuration structure")
            
        except Exception as e:
            logger.error(f"Failed to load modular configuration: {e}")
            # Fall back to legacy loading
            self._load_legacy_configuration(paths)
    
    def _load_legacy_configuration(self, paths: ConfigurationPaths):
        """Load from legacy monolithic structure."""
        self._is_modular = False
        
        # Load primary architectural configuration
        if paths.architectural_config.exists():
            primary_config = self._strategies['yaml'].load_config(paths.architectural_config)
            
            # Validate configuration
            if not self._strategies['yaml'].validate_config(primary_config):
                logger.warning("Primary configuration validation failed")
            
            self._config.update(primary_config)
            logger.info(f"Loaded architectural configuration from {paths.architectural_config}")
            
            # Update metadata
            self._configuration_metadata.update({
                'structure_type': 'legacy',
                'files_loaded': [str(paths.architectural_config)]
            })
        else:
            logger.warning(f"Architectural configuration not found: {paths.architectural_config}")
            self._load_fallback_configuration()
            return
        
        # Load additional configuration files if they exist (legacy behavior)
        additional_configs = [
            ('data_sources', paths.data_sources),
            ('field_mappings', paths.field_mappings),
            ('operational', paths.operational_config)
        ]
        
        for config_name, config_path in additional_configs:
            if config_path.exists():
                additional_config = self._strategies['yaml'].load_config(config_path)
                # Merge additional configurations into main config
                self._merge_config(additional_config, config_name)
                logger.debug(f"Loaded additional configuration: {config_name}")
                self._configuration_metadata['files_loaded'].append(str(config_path))
        
        logger.info("📋 Loaded legacy configuration structure")
    
    def _load_fallback_configuration(self):
        """Load fallback configuration when other methods fail."""
        self._config = self._get_fallback_config()
        self._adapter = ConfigurationAdapter(self._config)
        self._configuration_metadata['structure_type'] = 'fallback'
        logger.warning("⚠️ Using fallback configuration - functionality may be limited")
    
    def _cache_module_configs(self, modules_dir: Optional[Path]):
        """Cache module-specific configurations for performance."""
        if not modules_dir or not modules_dir.exists():
            return
        
        for module_dir in modules_dir.iterdir():
            if module_dir.is_dir():
                module_config = {}
                for config_file in module_dir.glob("*.yaml"):
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            file_config = yaml.safe_load(f) or {}
                        module_config[config_file.stem] = file_config
                    except Exception as e:
                        logger.warning(f"Failed to cache module config {config_file}: {e}")
                
                if module_config:
                    self._module_configs[module_dir.name] = module_config
    
    def _count_modular_files(self, config_root: Path) -> List[str]:
        """Count and list modular configuration files."""
        files = []
        for subdir in ['core', 'modules', 'data', 'integration']:
            subdir_path = config_root / subdir
            if subdir_path.exists():
                for yaml_file in subdir_path.rglob("*.yaml"):
                    files.append(str(yaml_file.relative_to(config_root)))
        return files
    
    def _merge_config(self, additional_config: Dict[str, Any], source_name: str):
        """Merge additional configuration into main configuration."""
        for section, values in additional_config.items():
            if section not in self._config:
                self._config[section] = {}
            
            if isinstance(values, dict):
                self._config[section].update(values)
            else:
                self._config[section] = values
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Get fallback configuration when primary configuration is unavailable."""
        logger.warning("Using fallback configuration - functionality may be limited")
        
        return {
            'directories': {
                'data_root': 'data',
                'config_root': 'config',
                'output_root': 'output',
                'models_root': 'models',
                'logs_root': 'logs',
                'colleague_positions': 'data/colleague_positions_history',
                'positions_history': 'data/positions_history',
                'skills_library': 'data/skills_library',
                'input_data': 'data/input_data',
                'precomputed': 'data/precomputed',
            },
            'files': {
                'skills_comprehensive': 'skills_library/skills_comprehensive_all_versions.csv',
                'job_skill_mapping': 'input_data/job_skill_mapping.csv',
                'data_sources': 'config/data_sources.yaml',
            },
            'processing': {
                'default_chunk_size': 10000,
                'default_encoding': 'utf-8',
                'default_delimiter': ',',
            },
            'datetime': {
                'input_date_format': '%d/%m/%Y',
                'output_date_format': '%Y-%m-%d',
                'timestamp_format': '%Y%m%d_%H%M%S',
            },
            'logging': {
                'default_level': 'INFO',
                'console_output': True,
                'file_output': True,
            }
        }
    
    # =========================================================================
    # ENHANCED API: Modular Configuration Access
    # =========================================================================
    
    def is_modular_structure(self) -> bool:
        """Check if using modular configuration structure."""
        return self._is_modular
    
    def get_configuration_metadata(self) -> Dict[str, Any]:
        """Get configuration loading metadata."""
        return self._configuration_metadata.copy()
    
    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get configuration for specific module."""
        if self._is_modular:
            return self._module_configs.get(module_name, {})
        else:
            # Map legacy sections to modules
            return self._map_legacy_to_module(module_name)
    
    def _map_legacy_to_module(self, module_name: str) -> Dict[str, Any]:
        """Map legacy configuration sections to module structure."""
        legacy_mappings = {
            'utils': 'utils',
            'similarity': 'similarity_module',
            'models': 'models',
            'analysis': ['gap_analysis', 'team_analysis', 'workforce_analysis'],
            'api': 'api',
            'business_context': 'business_context',
            'error_handling': 'error_handling',
            'cli': 'cli',
            'data': 'data',
            'data_validation': 'data_validation',
            'logging': 'logging'
        }
        
        mapping = legacy_mappings.get(module_name)
        if isinstance(mapping, str):
            return self._config.get(mapping, {})
        elif isinstance(mapping, list):
            # Combine multiple sections
            combined = {}
            for section in mapping:
                combined.update(self._config.get(section, {}))
            return combined
        else:
            return {}
    
    def get_nested_module_value(self, module_name: str, *keys, default: Any = None) -> Any:
        """Get nested value from module configuration."""
        try:
            module_config = self.get_module_config(module_name)
            result = module_config
            for key in keys:
                result = result[key]
            return result
        except (KeyError, TypeError):
            if default is not None:
                return default
            raise ConfigurationError(f"Module config value not found: {module_name}.{'.'.join(keys)}")
    
    def validate_module_config(self, module_name: str) -> bool:
        """Validate configuration for specific module."""
        module_config = self.get_module_config(module_name)
        return len(module_config) > 0
    
    def reload_module_configuration(self, module_name: str = None):
        """Reload configuration for specific module or all modules."""
        if module_name and self._is_modular:
            # Reload specific module only
            modules_dir = self._config_base_path / "config" / "modules" if self._config_base_path else Path("config/modules")
            module_dir = modules_dir / module_name
            if module_dir.exists():
                self._cache_single_module(module_dir, module_name)
                logger.info(f"Reloaded module configuration: {module_name}")
        else:
            # Reload all configurations
            self.reload_configuration()
    
    def _cache_single_module(self, module_dir: Path, module_name: str):
        """Cache configuration for a single module."""
        module_config = {}
        for config_file in module_dir.glob("*.yaml"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}
                module_config[config_file.stem] = file_config
            except Exception as e:
                logger.warning(f"Failed to reload module config {config_file}: {e}")
        
        if module_config:
            self._module_configs[module_name] = module_config
    
    # =========================================================================
    # ENHANCED CORE CONFIGURATION ACCESS (Phase 1 Implementation)
    # =========================================================================
    
    def get_core_datetime_config(self) -> Optional[Dict[str, Any]]:
        """
        Get core datetime configuration with enhanced structure.
        
        This method supports the new enhanced datetime configuration format
        with absolute authority and flexible parsing.
        
        Returns:
            Core datetime configuration dict or None if not available
        """
        try:
            # Try to get enhanced core configuration first from _config['core'] (surgical fix)
            if 'core' in self._config and 'datetime' in self._config['core']:
                datetime_config = self._config['core']['datetime']
                
                # Check if it's the enhanced format with primary_formats
                if isinstance(datetime_config, dict) and 'primary_formats' in datetime_config:
                    logger.debug("Using enhanced core datetime configuration")
                    return datetime_config
            
            # Fallback: Try to get enhanced core configuration from _module_configs (original)
            if self._is_modular and 'core' in self._module_configs:
                core_config = self._module_configs['core']
                if 'datetime' in core_config:
                    datetime_config = core_config['datetime']
                    
                    # Check if it's the enhanced format with primary_formats
                    if isinstance(datetime_config, dict) and 'primary_formats' in datetime_config:
                        logger.debug("Using enhanced core datetime configuration from module configs")
                        return datetime_config
            
            # Fallback to architectural config datetime section
            if 'datetime' in self._config:
                datetime_config = self._config['datetime']
                if isinstance(datetime_config, dict):
                    # Convert legacy format to enhanced format for compatibility
                    enhanced_config = {
                        'primary_formats': {
                            'input_date': datetime_config.get('input_date_format', '%d/%m/%Y'),
                            'output_date': datetime_config.get('output_date_format', '%Y-%m-%d'),
                            'timestamp': datetime_config.get('timestamp_format', '%Y%m%d_%H%M%S'),
                            'logging': '%Y-%m-%d %H:%M:%S'
                        },
                        'parsing_tolerance': datetime_config.get('alternative_date_formats', [
                            '%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d'
                        ])
                    }
                    logger.debug("Using legacy datetime configuration with enhanced compatibility wrapper")
                    return enhanced_config
                    
        except Exception as e:
            logger.warning(f"Failed to load core datetime configuration: {e}")
        
        return None
    
    def get_core_datetime_formats(self) -> Dict[str, Any]:
        """
        Get core datetime formats for backward compatibility.
        
        Returns primary date formats in the expected legacy format.
        """
        core_datetime = self.get_core_datetime_config()
        if core_datetime and 'primary_formats' in core_datetime:
            primary_formats = core_datetime['primary_formats']
            return {
                'input_date_format': primary_formats.get('input_date', '%d/%m/%Y'),
                'output_date_format': primary_formats.get('output_date', '%Y-%m-%d'),
                'movement_date_format': primary_formats.get('input_date', '%d/%m/%Y'),  # Movement uses input format
                'timestamp_format': primary_formats.get('timestamp', '%Y%m%d_%H%M%S'),
                'parsing_tolerance': core_datetime.get('parsing_tolerance', ['%d/%m/%Y', '%Y-%m-%d'])
            }
        
        # Legacy fallback
        return {
            'input_date_format': '%d/%m/%Y',
            'output_date_format': '%Y-%m-%d', 
            'movement_date_format': '%d/%m/%Y',
            'timestamp_format': '%Y%m%d_%H%M%S',
            'parsing_tolerance': ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y']
        }

    # =========================================================================
    # EXISTING API: Backward Compatible Configuration Access
    # =========================================================================
    # All existing methods remain unchanged to ensure backward compatibility
    
    def get_directory(self, dir_key: str) -> Path:
        """Get directory path - replaces hardcoded directory strings."""
        if self._adapter is None:
            raise ConfigurationError("Configuration adapter not initialized")
        return self._adapter.get_path(dir_key, 'directories')
    
    def get_file_path(self, file_key: str) -> Path:
        """Get file path - replaces hardcoded file strings."""
        if self._adapter is None:
            raise ConfigurationError("Configuration adapter not initialized")
        return self._adapter.get_file(file_key, 'files')
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration - replaces hardcoded processing parameters."""
        if self._adapter is None:
            raise ConfigurationError("Configuration adapter not initialized")
        return self._adapter.get_section('processing')
    
    def get_datetime_config(self) -> Dict[str, Any]:
        """Get datetime configuration - replaces hardcoded date formats."""
        if self._adapter is None:
            raise ConfigurationError("Configuration adapter not initialized")
        return self._adapter.get_section('datetime')
    
    def get_similarity_config(self) -> Dict[str, Any]:
        """Get similarity engine configuration - replaces hardcoded similarity parameters."""
        if self._adapter is None:
            raise ConfigurationError("Configuration adapter not initialized")
        return self._adapter.get_section('similarity')
    
    def get_movement_analysis_config(self) -> Dict[str, Any]:
        """Get movement analysis configuration - replaces hardcoded movement parameters."""
        if self._adapter is None:
            raise ConfigurationError("Configuration adapter not initialized")
        return self._adapter.get_section('movement_analysis')
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration - replaces hardcoded logging parameters."""
        if self._adapter is None:
            raise ConfigurationError("Configuration adapter not initialized")
        return self._adapter.get_section('logging')
    
    def get_validation_config(self) -> Dict[str, Any]:
        """Get validation configuration - replaces hardcoded validation parameters."""
        if self._adapter is None:
            raise ConfigurationError("Configuration adapter not initialized")
        return self._adapter.get_section('validation')
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration - replaces hardcoded database parameters."""
        if self._adapter is None:
            raise ConfigurationError("Configuration adapter not initialized")
        return self._adapter.get_section('database')
    
    def get_versioning_config(self) -> Dict[str, Any]:
        """Get versioning configuration - replaces hardcoded versioning parameters."""
        if self._adapter is None:
            raise ConfigurationError("Configuration adapter not initialized")
        return self._adapter.get_section('versioning')
    
    def get_models_config(self) -> Dict[str, Any]:
        """Get models configuration section - replaces hardcoded model parameters."""
        if self._adapter is None:
            raise ConfigurationError("Configuration adapter not initialized")
        return self._adapter.get_section('models')
    
    def get_models_directories_config(self) -> Dict[str, Any]:
        """Get models directories configuration - replaces hardcoded directory names."""
        if self._adapter is None:
            raise ConfigurationError("Configuration adapter not initialized")
        return self._adapter.get_nested_value('models', 'directories', default={})
    
    def get_models_export_settings(self) -> Dict[str, Any]:
        """Get models export settings configuration - replaces hardcoded export parameters."""
        if self._adapter is None:
            raise ConfigurationError("Configuration adapter not initialized")
        return self._adapter.get_nested_value('models', 'export_settings', default={})
    
    def get_skill_types_config(self) -> Dict[str, Any]:
        """Get skill types configuration - replaces hardcoded skill type mappings."""
        if self._adapter is None:
            raise ConfigurationError("Configuration adapter not initialized")
        return self._adapter.get_nested_value('models', 'skill_types', default={})
    
    def get_models_date_formats(self) -> Dict[str, Any]:
        """Get models date formats configuration - replaces hardcoded date format strings."""
        if self._adapter is None:
            raise ConfigurationError("Configuration adapter not initialized")
        return self._adapter.get_nested_value('models', 'date_formats', default={})

    def get_models_boolean_mappings(self) -> Dict[str, Any]:
        """Get models boolean mappings configuration - replaces hardcoded boolean value mappings."""
        return self._adapter.get_nested_value('models', 'boolean_mappings', default={})

    def get_models_movement_analysis_config(self) -> Dict[str, Any]:
        """Get models movement analysis configuration - replaces hardcoded movement analysis parameters."""
        return self._adapter.get_nested_value('models', 'movement_analysis', default={})

    def get_models_precompute_config(self) -> Dict[str, Any]:
        """Get models precompute configuration - replaces hardcoded precompute parameters."""
        return self._adapter.get_nested_value('models', 'precompute', default={})

    def get_models_validation_config(self) -> Dict[str, Any]:
        """Get models validation configuration - replaces hardcoded validation parameters."""
        return self._adapter.get_nested_value('models', 'validation', default={})

    def get_models_skills_taxonomy_config(self) -> Dict[str, Any]:
        """Get models skills taxonomy configuration - replaces hardcoded skills taxonomy parameters."""
        return self._adapter.get_nested_value('models', 'skills_taxonomy', default={})

    def get_models_job_architecture_config(self) -> Dict[str, Any]:
        """Get models job architecture configuration - replaces hardcoded job architecture parameters."""
        return self._adapter.get_nested_value('models', 'job_architecture', default={})

    def get_models_employee_config(self) -> Dict[str, Any]:
        """Get models employee configuration - replaces hardcoded employee model parameters."""
        return self._adapter.get_nested_value('models', 'employee_model', default={})

    def get_models_position_history_config(self) -> Dict[str, Any]:
        """Get models position history configuration - replaces hardcoded position history parameters."""
        return self._adapter.get_nested_value('models', 'position_history', default={
            'aggregation_method': 'monthly',
            'include_current_positions': True,
            'organizational_context_fields': [
                'division', 'business_unit', 'team', 'location', 
                'region', 'employee_group', 'salary_group'
            ]
        })

    def get_models_movement_fact_config(self) -> Dict[str, Any]:
        """Get movement fact table builder configuration."""
        return self._adapter.get_nested_value('models', 'movement_fact', default={})
    
    def get_models_position_enrichment_config(self) -> Dict[str, Any]:
        """Get position enrichment pipeline configuration."""
        # Position enrichment config is in models module (modular config)
        return self._adapter.get_nested_value('models', 'position_enrichment', default={})

    # Similarity module configurations

    def get_similarity_module_config(self) -> Dict[str, Any]:
        """Get similarity module configuration - replaces hardcoded similarity module parameters."""
        return self._adapter.get_section('similarity_module')

    def get_similarity_algorithms_config(self) -> Dict[str, Any]:
        """Get similarity algorithms configuration - replaces hardcoded algorithm parameters."""
        return self._adapter.get_nested_value('similarity_module', 'algorithms', default={})

    def get_similarity_asymmetric_config(self) -> Dict[str, Any]:
        """Get similarity asymmetric configuration - replaces hardcoded asymmetric parameters."""
        return self._adapter.get_nested_value('similarity_module', 'asymmetric', default={})

    def get_similarity_cosine_config(self) -> Dict[str, Any]:
        """Get similarity cosine configuration - replaces hardcoded cosine parameters."""
        return self._adapter.get_nested_value('similarity_module', 'cosine', default={})

    def get_similarity_precompute_config(self) -> Dict[str, Any]:
        """Get similarity precompute configuration - replaces hardcoded precompute parameters."""
        return self._adapter.get_nested_value('similarity_module', 'precompute', default={})

    def get_similarity_logging_config(self) -> Dict[str, Any]:
        """Get similarity logging configuration - replaces hardcoded logging parameters."""
        return self._adapter.get_nested_value('similarity_module', 'logging', default={})

    def get_similarity_validation_config(self) -> Dict[str, Any]:
        """Get similarity validation configuration - replaces hardcoded validation parameters."""
        return self._adapter.get_nested_value('similarity_module', 'validation', default={})

    def get_career_pathways_config(self) -> Dict[str, Any]:
        """Get career pathways configuration - replaces hardcoded career pathway parameters."""
        return self._adapter.get_nested_value('similarity_module', 'precompute', 'career_pathways', default={})

    def get_runtime_estimation_config(self) -> Dict[str, Any]:
        """Get runtime estimation configuration - replaces hardcoded runtime estimation parameters."""
        return self._adapter.get_nested_value('similarity_module', 'precompute', 'estimation', default={})

    def get_move_classification_config(self) -> Dict[str, Any]:
        """Get career move classification configuration - replaces hardcoded classification thresholds."""
        return self._adapter.get_nested_value('similarity_module', 'precompute', 'move_classification', default={})

    def get_nested_value(self, *keys, default: Any = None) -> Any:
        """Get nested configuration value - provides flexible configuration access."""
        if self._adapter is None:
            raise ConfigurationError("Configuration adapter not initialized")
        return self._adapter.get_nested_value(*keys, default=default)

    # Utility Methods

    def reload_configuration(self):
        """Reload configuration from files."""
        logger.info("Reloading configuration...")
        self._config.clear()
        self._module_configs.clear()
        self._load_configuration()

    def get_full_config(self) -> Dict[str, Any]:
        """Get complete configuration dictionary (for debugging/inspection)."""
        return self._config.copy()

    def validate_configuration(self) -> bool:
        """Validate loaded configuration."""
        try:
            # Check essential sections exist
            essential_sections = ['directories', 'processing']
            for section in essential_sections:
                if section not in self._config:
                    logger.error(f"Essential configuration section missing: {section}")
                    return False

            # Validate directory paths exist or can be created
            try:
                data_root = self.get_directory('data_root')
                if not data_root.exists():
                    logger.warning(f"Data root directory does not exist: {data_root}")
            except Exception as e:
                logger.error(f"Failed to validate data directory: {e}")
                return False

            logger.info("✅ Configuration validation passed")
            return True

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    def get_similarity_matrix_operations_config(self) -> Dict[str, Any]:
        """Get similarity matrix operations configuration."""
        return self._adapter.get_nested_value('similarity_module', 'matrix_operations', default={
            'batch_size': 1000,
            'use_sparse_matrices': False,
            'cache_intermediate_results': True,
            'symmetric_matrix': False,
            'enable_checkpointing': True,
            'checkpoint_interval': 1000
        })

    # Utils module configurations (extensive backward compatibility)

    def get_utils_memory_config(self) -> Dict[str, Any]:
        """Get utils memory configuration - replaces hardcoded memory parameters."""
        return self._adapter.get_nested_value('utils', 'memory', default={
            'system_reserve_mb': 2000.0,
            'default_memory_limit_mb': None,
            'memory_threshold_percent': 80.0,
            'target_memory_percent': 70.0,
            'critical_memory_percent': 85.0,
            'emergency_memory_percent': 95.0,
            'check_interval_seconds': 1.0,
            'averaging_window_samples': 5,
            'gc_at_warning': False,
            'gc_at_critical': True,
            'gc_full_at_emergency': True,
            'pressure_threshold_percent': 80.0
        })

    def get_utils_chunking_config(self) -> Dict[str, Any]:
        """Get utils chunking configuration - replaces hardcoded chunking parameters."""
        return self._adapter.get_nested_value('utils', 'chunking', default={
            'initial_chunk_size': 1000,
            'min_chunk_size': 100,
            'max_chunk_size': 10000,
            'growth_factor': 1.5,
            'shrink_factor': 0.5,
            'target_chunk_memory_mb': 500.0,
            'matrix': {
                'initial_chunk_size': 1000,
                'min_chunk_size': 100,
                'max_chunk_size': 5000,
                'memory_threshold_percent': 80.0,
                'target_memory_percent': 70.0
            }
        })

    def get_utils_parallel_config(self) -> Dict[str, Any]:
        """Get utils parallel configuration - replaces hardcoded parallel parameters."""
        return self._adapter.get_nested_value('utils', 'parallel', default={
            'max_workers': None,
            'memory_per_worker_mb': 1000,
            'system_memory_usage_percent': 80.0,
            'work_stealing_enabled': True,
            'task_timeout_seconds': 300
        })

    def get_utils_progress_config(self) -> Dict[str, Any]:
        """Get utils progress configuration - replaces hardcoded progress parameters."""
        return self._adapter.get_nested_value('utils', 'progress', default={
            'default_log_interval': 100,
            'simple_log_interval': 10,
            'bar_width': 50,
            'progress_bar_char': "█",
            'empty_bar_char': " ",
            'memory_tracking_enabled': True,
            'memory_check_interval': 1.0,
            'time_format': {
                'show_hours': True,
                'show_minutes': True,
                'show_seconds': True,
                'decimal_places': 2
            }
        })

    def get_utils_performance_config(self) -> Dict[str, Any]:
        """Get utils performance configuration - replaces hardcoded performance parameters."""
        return self._adapter.get_nested_value('utils', 'performance', default={
            'track_memory_usage': True,
            'memory_snapshot_interval': 5.0,
            'track_largest_objects': True,
            'largest_objects_count': 10,
            'object_tracking_enabled': False,
            'bytes_to_mb_divisor': 1048576,
            'slow_operation_threshold_seconds': 5.0,
            'memory_leak_threshold_mb': 100.0
        })

    def get_utils_dashboard_config(self) -> Dict[str, Any]:
        """Get utils dashboard configuration - replaces hardcoded dashboard parameters."""
        return self._adapter.get_nested_value('utils', 'dashboard', default={
            'max_history_snapshots': 1000,
            'chart_width': 12,
            'chart_height': 4,
            'chart_dpi': 300,
            'plot_generation_interval': 10,
            'csv_export_interval': 50,
            'default_prediction_window': 20,
            'min_samples_for_prediction': 5,
            'polynomial_degree_max': 3,
            'prediction_sample_threshold': 10,
            'memory_alert_thresholds': [8192, 16384, 32768]
        })

    def get_utils_display_config(self) -> Dict[str, Any]:
        """Get utils display configuration - replaces hardcoded display parameters."""
        return self._adapter.get_nested_value('utils', 'display', default={
            'max_parameter_string_length': 50,
            'truncation_suffix': "...",
            'default_separator_char': "=",
            'default_separator_length': 80,
            'progress_update_interval': 1.0,
            'clear_line_width': 80
        })


# Factory pattern for creating configuration manager
class ConfigManagerFactory:
    """Factory for creating configuration manager instances."""
    
    @staticmethod
    def create_manager(config_base_path: Optional[Path] = None) -> ArchitecturalConfigManager:
        """Create configuration manager with specified base path."""
        return ArchitecturalConfigManager(config_base_path)
    
    @staticmethod
    def create_test_manager(test_config: Dict[str, Any]) -> ArchitecturalConfigManager:
        """Create configuration manager for testing with mock configuration."""
        manager = ArchitecturalConfigManager()
        manager._config = test_config
        manager._adapter = ConfigurationAdapter(test_config)
        return manager


# Convenience functions for direct access (following SSE patterns)
_global_manager: Optional[ArchitecturalConfigManager] = None


def get_config_manager() -> ArchitecturalConfigManager:
    """Get global configuration manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = ArchitecturalConfigManager()
    return _global_manager


def get_directory(dir_key: str) -> Path:
    """Get directory path from global configuration manager."""
    return get_config_manager().get_directory(dir_key)


def get_file_path(file_key: str) -> Path:
    """Get file path from global configuration manager."""
    return get_config_manager().get_file_path(file_key)


def get_config_value(*keys, default: Any = None) -> Any:
    """Get configuration value from global configuration manager."""
    return get_config_manager().get_nested_value(*keys, default=default) 