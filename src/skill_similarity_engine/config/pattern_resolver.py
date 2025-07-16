"""
Configuration Pattern Resolver

Utility module for resolving file patterns and names from centralized configuration.
This eliminates hardcoded values from source files and provides a single point of configuration.
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PatternResolver:
    """Resolves file patterns from centralized configuration."""
    
    def __init__(self):
        """Initialize the pattern resolver."""
        self._config_manager = None
    
    def _get_config_manager(self):
        """Get the configuration manager instance."""
        if self._config_manager is None:
            try:
                from .architectural_config_manager import get_config_manager
                self._config_manager = get_config_manager()
            except ImportError as e:
                logger.warning(f"Could not import configuration manager: {e}")
                self._config_manager = None
        return self._config_manager
    
    def get_workforce_pattern(self, pattern_name: str, default: Optional[str] = None) -> str:
        """
        Get a workforce data pattern from configuration.
        
        Args:
            pattern_name: Name of the pattern (e.g., 'colleague_positions', 'positions_history')
            default: Default value if pattern not found
            
        Returns:
            File pattern string
        """
        config_manager = self._get_config_manager()
        
        if config_manager:
            try:
                return config_manager.get_nested_value(
                    'workforce_data_patterns', pattern_name,
                    default=default
                )
            except Exception as e:
                logger.debug(f"Could not get workforce pattern '{pattern_name}': {e}")
        
        # Fallback defaults
        fallback_patterns = {
            'colleague_positions': 'd_colleague_position_fy*.csv',
            'positions_history': 'd_positions_fy*.csv',
            'colleague_positions_dev': 'd_colleague_positions_fy*.csv',
            'positions_history_dev': 'd_positions_fy*.csv'
        }
        
        return default or fallback_patterns.get(pattern_name, pattern_name)
    
    def get_skills_pattern(self, pattern_name: str, default: Optional[str] = None) -> str:
        """
        Get a skills data pattern from configuration.
        
        Args:
            pattern_name: Name of the pattern (e.g., 'skills_comprehensive', 'job_skill_mapping')
            default: Default value if pattern not found
            
        Returns:
            File pattern string
        """
        config_manager = self._get_config_manager()
        
        if config_manager:
            try:
                return config_manager.get_nested_value(
                    'skills_data_patterns', pattern_name,
                    default=default
                )
            except Exception as e:
                logger.debug(f"Could not get skills pattern '{pattern_name}': {e}")
        
        # Fallback defaults
        fallback_patterns = {
            'skills_comprehensive': 'skills_comprehensive_all_versions.csv',
            'job_skill_mapping': 'job_skill_mapping.csv',
            'job_architecture': 'dummy_job_architecture.csv',
            'workforce_context': 'dummy_workforce_context.csv'
        }
        
        return default or fallback_patterns.get(pattern_name, pattern_name)
    
    def get_output_pattern(self, pattern_name: str, default: Optional[str] = None) -> str:
        """
        Get an output file pattern from configuration.
        
        Args:
            pattern_name: Name of the pattern (e.g., 'employee_movements_csv', 'job_similarity_matrix_parquet')
            default: Default value if pattern not found
            
        Returns:
            File pattern string
        """
        config_manager = self._get_config_manager()
        
        if config_manager:
            try:
                return config_manager.get_nested_value(
                    'output_patterns', pattern_name,
                    default=default
                )
            except Exception as e:
                logger.debug(f"Could not get output pattern '{pattern_name}': {e}")
        
        # Fallback defaults
        fallback_patterns = {
            'employee_movements_csv': 'employee_movements.csv',
            'employee_movements_parquet': 'employee_movements.parquet',
            'movement_summary_csv': 'movement_summary.csv',
            'movement_summary_parquet': 'movement_summary.parquet',
            'job_similarity_matrix_csv': 'job_similarity_matrix.csv',
            'job_similarity_matrix_parquet': 'job_similarity_matrix.parquet',
            'career_pathways_csv': 'career_pathways.csv',
            'career_pathways_parquet': 'career_pathways.parquet',
            'metadata_json': 'metadata.json',
            'progress_json': 'progress.json',
            'checkpoint_json': 'checkpoint.json'
        }
        
        return default or fallback_patterns.get(pattern_name, pattern_name)
    
    def get_database_pattern(self, pattern_name: str, default: Optional[str] = None) -> str:
        """
        Get a database file pattern from configuration.
        
        Args:
            pattern_name: Name of the pattern (e.g., 'business_context_db', 'workforce_intelligence_db')
            default: Default value if pattern not found
            
        Returns:
            File pattern string
        """
        config_manager = self._get_config_manager()
        
        if config_manager:
            try:
                return config_manager.get_nested_value(
                    'database_patterns', pattern_name,
                    default=default
                )
            except Exception as e:
                logger.debug(f"Could not get database pattern '{pattern_name}': {e}")
        
        # Fallback defaults
        fallback_patterns = {
            'business_context_db': 'business_context.sqlite',
            'workforce_intelligence_db': 'workforce_intelligence.sqlite'
        }
        
        return default or fallback_patterns.get(pattern_name, pattern_name)
    
    def get_position_mapping_pattern(self, pattern_name: str, default: Optional[str] = None) -> str:
        """
        Get a position mapping pattern from configuration.
        
        Args:
            pattern_name: Name of the pattern (e.g., 'position_job_mapping', 'position_id_mapping')
            default: Default value if pattern not found
            
        Returns:
            File pattern string
        """
        config_manager = self._get_config_manager()
        
        if config_manager:
            try:
                return config_manager.get_nested_value(
                    'position_mapping_patterns', pattern_name,
                    default=default
                )
            except Exception as e:
                logger.debug(f"Could not get position mapping pattern '{pattern_name}': {e}")
        
        # Fallback defaults
        fallback_patterns = {
            'position_job_mapping': 'position_job_mapping.csv',
            'position_id_mapping': 'position_id_to_job_profile.csv'
        }
        
        return default or fallback_patterns.get(pattern_name, pattern_name)


# Global instance
_pattern_resolver = PatternResolver()


def get_workforce_pattern(pattern_name: str, default: Optional[str] = None) -> str:
    """Get a workforce data pattern from configuration."""
    return _pattern_resolver.get_workforce_pattern(pattern_name, default)


def get_skills_pattern(pattern_name: str, default: Optional[str] = None) -> str:
    """Get a skills data pattern from configuration."""
    return _pattern_resolver.get_skills_pattern(pattern_name, default)


def get_output_pattern(pattern_name: str, default: Optional[str] = None) -> str:
    """Get an output file pattern from configuration."""
    return _pattern_resolver.get_output_pattern(pattern_name, default)


def get_database_pattern(pattern_name: str, default: Optional[str] = None) -> str:
    """Get a database file pattern from configuration."""
    return _pattern_resolver.get_database_pattern(pattern_name, default)


def get_position_mapping_pattern(pattern_name: str, default: Optional[str] = None) -> str:
    """Get a position mapping pattern from configuration."""
    return _pattern_resolver.get_position_mapping_pattern(pattern_name, default) 