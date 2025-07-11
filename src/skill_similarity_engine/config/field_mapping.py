"""
Field mapping utility for the Skill Similarity Engine.

This module provides functionality for loading and accessing field mappings 
that decouple canonical variable names used in code from raw data column names.

Architecture: Configuration-Driven Design Pattern following PTH's enterprise patterns
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from functools import lru_cache

from .architectural_config_manager import get_config_manager

logger = logging.getLogger(__name__)


class FieldMappingError(Exception):
    """Exception raised when field mapping operations fail."""
    pass


class FieldMapper:
    """
    Provides field mapping functionality to translate between canonical field names
    used in code and actual column names in raw data files.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the field mapper.
        
        Args:
            config_path: Path to the field mapping YAML file. If None, will search
                        for it relative to the current module.
        """
        self.config_path = config_path or self._find_config_path()
        self.config = self._load_config()
        
        # Load configuration settings from architectural config manager
        config_manager = get_config_manager()
        fallback_config = config_manager.get_nested_value(
            'configuration_management', 'fallback_handling', default={}
        )
        logging_config = config_manager.get_nested_value(
            'configuration_management', 'logging', default={}
        )
        
        # Configuration-driven settings (no hardcoded defaults)
        self.case_sensitive = fallback_config.get('case_sensitive', 
                                                self.config.get('field_name_alternatives', {}).get('case_sensitive', False))
        self.enable_fallback = fallback_config.get('enable_fallback',
                                                 self.config.get('field_name_alternatives', {}).get('enable_fallback', True))
        self.log_fallback_usage = logging_config.get('log_fallback_usage',
                                                    self.config.get('field_name_alternatives', {}).get('log_fallback_usage', True))
        
    def _find_config_path(self) -> str:
        """
        Find the field mapping config file using architectural configuration manager.
        
        Returns:
            Path to the field mapping configuration file
            
        Raises:
            FieldMappingError: If the config file cannot be found
        """
        try:
            # Use architectural config manager for path discovery
            config_manager = get_config_manager()
            search_paths = config_manager.get_nested_value(
                'configuration_management', 'file_discovery', 'config_search_paths',
                default=['config', '../config', '../../config']
            )
            
            field_mapping_filename = config_manager.get_nested_value(
                'configuration_management', 'file_discovery', 'default_filenames', 'field_mapping',
                default='field_mapping.yaml'
            )
            
            # Search in configured paths (relative to project root)
            # Navigate from src/skill_similarity_engine/config/ back to project root
            project_root = Path(__file__).parent.parent.parent.parent
            for search_path in search_paths:
                config_path = project_root / search_path / field_mapping_filename
                if config_path.exists():
                    return str(config_path)
            
            # Fallback to legacy settings if available
            try:
                from .settings import get_config
                main_config = get_config()
                if hasattr(main_config, 'field_mapping_file'):
                    legacy_path = Path(main_config.field_mapping_file)
                    if legacy_path.exists():
                        return str(legacy_path)
            except ImportError:
                pass
            
            raise FieldMappingError(f"Could not find {field_mapping_filename} in any configured search path")
            
        except Exception as e:
            logger.error(f"Error finding config path: {e}")
            raise FieldMappingError(f"Configuration path discovery failed: {e}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load the field mapping configuration from YAML file.
        
        Returns:
            Dictionary containing the field mapping configuration
            
        Raises:
            FieldMappingError: If the config file cannot be loaded
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not isinstance(config, dict):
                raise FieldMappingError("Field mapping config must be a dictionary")
            
            logger.info(f"Loaded field mapping configuration from {self.config_path}")
            return config
            
        except FileNotFoundError:
            raise FieldMappingError(f"Field mapping config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise FieldMappingError(f"Error parsing field mapping config: {e}")
        except Exception as e:
            raise FieldMappingError(f"Error loading field mapping config: {e}")
    
    def get_raw_field_name(self, 
                          canonical_name: str, 
                          section: str = 'skills',
                          fallback_sections: Optional[List[str]] = None) -> str:
        """
        Get the raw data field name for a canonical field name.
        
        Args:
            canonical_name: The canonical field name used in code
            section: The configuration section to look in (e.g., 'skills', 'jobs')
            fallback_sections: Additional sections to try if not found in main section
            
        Returns:
            The raw data column name to use
            
        Raises:
            FieldMappingError: If the field mapping cannot be found
        """
        # Try the main section first
        raw_name = self._get_field_from_section(canonical_name, section)
        if raw_name:
            return raw_name
        
        # Try fallback sections if enabled
        if self.enable_fallback and fallback_sections:
            for fallback_section in fallback_sections:
                raw_name = self._get_field_from_section(canonical_name, fallback_section)
                if raw_name:
                    if self.log_fallback_usage:
                        logger.debug(f"Using fallback mapping for '{canonical_name}': "
                                   f"section '{fallback_section}' -> '{raw_name}'")
                    return raw_name
        
        # Try legacy section if it exists
        if self.enable_fallback and 'legacy' in self.config:
            raw_name = self._get_field_from_section(canonical_name, 'legacy', search_subsections=True)
            if raw_name:
                if self.log_fallback_usage:
                    logger.debug(f"Using legacy mapping for '{canonical_name}': '{raw_name}'")
                return raw_name
        
        # If all else fails, return the canonical name as-is
        logger.warning(f"No field mapping found for '{canonical_name}' in section '{section}', "
                      f"using canonical name as raw field name")
        return canonical_name
    
    def _get_field_from_section(self, 
                               canonical_name: str, 
                               section: str,
                               search_subsections: bool = False) -> Optional[str]:
        """
        Get a field mapping from a specific configuration section.
        
        Args:
            canonical_name: The canonical field name to look up
            section: The configuration section to search in
            search_subsections: Whether to search in subsections of the section
            
        Returns:
            The raw field name if found, None otherwise
        """
        section_config = self.config.get(section, {})
        
        if search_subsections:
            # Search in all subsections (for legacy mappings)
            for subsection_name, subsection in section_config.items():
                if isinstance(subsection, dict) and canonical_name in subsection:
                    mapping = subsection[canonical_name]
                    return self._resolve_field_mapping(mapping)
        else:
            # Direct lookup in section
            if canonical_name in section_config:
                mapping = section_config[canonical_name]
                return self._resolve_field_mapping(mapping)
        
        return None
    
    def _resolve_field_mapping(self, mapping: Union[str, List[str]]) -> Optional[str]:
        """
        Resolve a field mapping that might be a string or list of alternatives.
        
        Args:
            mapping: The field mapping (string or list of strings)
            
        Returns:
            The first available field name
        """
        if isinstance(mapping, str):
            return mapping
        elif isinstance(mapping, list) and mapping:
            # Return the first option for now
            # In a more sophisticated implementation, you might check which
            # columns actually exist in the data
            return mapping[0]
        
        return None
    
    def get_field_mapping_dict(self, section: str) -> Dict[str, str]:
        """
        Get all field mappings for a section as a dictionary.
        
        Args:
            section: The configuration section to get mappings for
            
        Returns:
            Dictionary mapping canonical names to raw field names
        """
        section_config = self.config.get(section, {})
        result = {}
        
        for canonical_name, mapping in section_config.items():
            raw_name = self._resolve_field_mapping(mapping)
            if raw_name:
                result[canonical_name] = raw_name
        
        return result
    
    def map_row_fields(self, 
                      row: Dict[str, Any], 
                      section: str,
                      reverse: bool = False) -> Dict[str, Any]:
        """
        Map field names in a data row using the field mapping.
        
        Args:
            row: Dictionary representing a data row
            section: The configuration section to use for mapping
            reverse: If True, map from raw names to canonical names
            
        Returns:
            New dictionary with mapped field names
        """
        field_mappings = self.get_field_mapping_dict(section)
        mapped_row = {}
        
        if reverse:
            # Map from raw names to canonical names
            reverse_mappings = {v: k for k, v in field_mappings.items()}
            for raw_name, value in row.items():
                canonical_name = reverse_mappings.get(raw_name, raw_name)
                if not self.case_sensitive:
                    # Try case-insensitive lookup
                    for raw_key, canonical_key in reverse_mappings.items():
                        if raw_key.lower() == raw_name.lower():
                            canonical_name = canonical_key
                            break
                mapped_row[canonical_name] = value
        else:
            # Map from canonical names to raw names
            for canonical_name, value in row.items():
                raw_name = field_mappings.get(canonical_name, canonical_name)
                mapped_row[raw_name] = value
        
        return mapped_row
    
    def get_available_sections(self) -> List[str]:
        """
        Get all available configuration sections.
        
        Returns:
            List of section names
        """
        return [key for key in self.config.keys() 
                if isinstance(self.config[key], dict) and key not in ['field_name_alternatives', 'data_source_priority']]


@lru_cache(maxsize=1)
def get_field_mapper() -> FieldMapper:
    """
    Get a cached instance of the FieldMapper.
    
    Returns:
        Singleton FieldMapper instance
    """
    return FieldMapper()


def get_raw_field_name(canonical_name: str, 
                      section: str = 'skills',
                      fallback_sections: Optional[List[str]] = None) -> str:
    """
    Convenience function to get a raw field name for a canonical name.
    
    Args:
        canonical_name: The canonical field name used in code
        section: The configuration section to look in
        fallback_sections: Additional sections to try if not found
        
    Returns:
        The raw data column name to use
    """
    mapper = get_field_mapper()
    return mapper.get_raw_field_name(canonical_name, section, fallback_sections)


def map_row_fields(row: Dict[str, Any], 
                  section: str,
                  reverse: bool = False) -> Dict[str, Any]:
    """
    Convenience function to map field names in a data row.
    
    Args:
        row: Dictionary representing a data row
        section: The configuration section to use for mapping
        reverse: If True, map from raw names to canonical names
        
    Returns:
        New dictionary with mapped field names
    """
    mapper = get_field_mapper()
    return mapper.map_row_fields(row, section, reverse) 
