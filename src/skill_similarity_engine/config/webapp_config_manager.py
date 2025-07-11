"""
Webapp Configuration Manager

This module provides specialized configuration management for the webapp module,
following the hybrid configuration architecture approach that maintains
architectural consistency while respecting webapp domain boundaries.

Created: Phase 1.4.8 - Webapp Module Refactoring
Author: Workforce Intelligence Migration System
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import yaml
from .architectural_config_manager import ConfigurationAdapter


class WebappConfigManager:
    """
    Manages webapp-specific configuration with type-safe access methods.
    
    This class provides domain-specific configuration management for the webapp
    module while maintaining consistency with the enterprise architectural patterns.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize webapp configuration manager.
        
        Args:
            config_path: Path to webapp_config.yaml file. Defaults to standard location.
        """
        if config_path is None:
            # Standard location relative to this file
            config_path = Path(__file__).parent.parent.parent.parent / 'config' / 'webapp_config.yaml'
        
        self.config_path = config_path
        self._config = None
        self._adapter = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._config = yaml.safe_load(file)
            
            # Create adapter for nested value access
            self._adapter = ConfigurationAdapter(self._config)
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Webapp configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in webapp configuration: {e}")
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self._load_config()
    
    # ==========================================================================
    # Core Application Configuration
    # ==========================================================================
    
    def get_core_database_config(self) -> Dict[str, Any]:
        """
        Get core database configuration.
        
        Returns:
            Dictionary containing database connection and setup parameters
        """
        return self._adapter.get_nested_value('webapp', 'core', 'database', default={
            'default_model_version': '2025-Q2',
            'business_context_filename': 'business_context.sqlite',
            'connection_timeout_seconds': 30,
            'retry_attempts': 3
        })
    
    def get_core_api_config(self) -> Dict[str, Any]:
        """
        Get core API configuration.
        
        Returns:
            Dictionary containing API defaults and thresholds
        """
        return self._adapter.get_nested_value('webapp', 'core', 'api', default={
            'default_job_limit': 20,
            'default_search_limit': 10,
            'default_similarity_threshold': 0.5,
            'max_similarity_threshold': 0.99,
            'min_similarity_threshold': 0.1,
            'pathway_similarity_threshold': 0.6,
            'cross_family_similarity_threshold': 0.4,
            'max_pathways_display': 12
        })
    
    def get_core_performance_config(self) -> Dict[str, Any]:
        """
        Get core performance configuration.
        
        Returns:
            Dictionary containing performance and caching settings
        """
        return self._adapter.get_nested_value('webapp', 'core', 'performance', default={
            'max_depth_default': 3,
            'max_results_default': 10,
            'cache_timeout_seconds': 3600,
            'pagination_size': 50,
            'query_timeout_seconds': 30
        })
    
    def get_core_routes_config(self) -> Dict[str, Any]:
        """
        Get core routes configuration.
        
        Returns:
            Dictionary containing route and response settings
        """
        return self._adapter.get_nested_value('webapp', 'core', 'routes', default={
            'error_response_format': 'json',
            'cors_enabled': False,
            'debug_mode': False
        })
    
    # ==========================================================================
    # Career Analysis Configuration
    # ==========================================================================
    
    def get_career_analysis_config(self) -> Dict[str, Any]:
        """
        Get complete career analysis configuration.
        
        Returns:
            Dictionary containing all career analysis settings
        """
        return self._adapter.get_nested_value('webapp', 'career_analysis', default={})
    
    def get_career_analysis_analysis_config(self) -> Dict[str, Any]:
        """
        Get career analysis parameters and limits.
        
        Returns:
            Dictionary containing analysis parameters and thresholds
        """
        return self._adapter.get_nested_value('webapp', 'career_analysis', 'analysis', default={
            'max_pathways_analysis': 5,
            'default_pathways_analysis': 3,
            'min_similarity_threshold': 0.1,
            'max_similarity_threshold': 0.99,
            'confidence_high_threshold': 0.8,
            'confidence_medium_threshold': 0.6
        })
    
    def get_career_analysis_content_generation_config(self) -> Dict[str, Any]:
        """
        Get content generation configuration.
        
        Returns:
            Dictionary containing content generation settings
        """
        return self._adapter.get_nested_value('webapp', 'career_analysis', 'content_generation', default={
            'reference_numbering_start': 1,
            'max_reference_number': 999,
            'cache_timeout_seconds': 3600,
            'template_cache_enabled': True
        })
    
    def get_career_analysis_document_styling_config(self) -> Dict[str, Any]:
        """
        Get document styling configuration.
        
        Returns:
            Dictionary containing fonts, colors, spacing, and sizing
        """
        return self._adapter.get_nested_value('webapp', 'career_analysis', 'document_styling', default={})
    
    def get_career_analysis_fonts_config(self) -> Dict[str, str]:
        """
        Get font family configuration.
        
        Returns:
            Dictionary containing font family mappings
        """
        return self._adapter.get_nested_value('webapp', 'career_analysis', 'document_styling', 'fonts', default={
            'heading': 'Epilogue',
            'primary': 'Source Sans Pro',
            'mono': 'Monaco'
        })
    
    def get_career_analysis_font_sizes_config(self) -> Dict[str, int]:
        """
        Get font sizes configuration.
        
        Returns:
            Dictionary containing font size mappings
        """
        return self._adapter.get_nested_value('webapp', 'career_analysis', 'document_styling', 'font_sizes', default={
            'cover_title': 42,
            'cover_subtitle': 28,
            'h1': 22,
            'h2': 14,
            'h3': 13,
            'body': 11,
            'table_header': 9,
            'table_body': 9,
            'caption': 9
        })
    
    def get_career_analysis_colors_config(self) -> Dict[str, List[int]]:
        """
        Get color palette configuration.
        
        Returns:
            Dictionary containing RGB color values
        """
        return self._adapter.get_nested_value('webapp', 'career_analysis', 'document_styling', 'colors', default={
            'nab_black': [0, 0, 0],
            'nab_red': [220, 38, 38],
            'blue_600': [37, 99, 235],
            'white': [255, 255, 255]
        })
    
    def get_career_analysis_spacing_config(self) -> Dict[str, int]:
        """
        Get spacing configuration.
        
        Returns:
            Dictionary containing spacing values in points
        """
        return self._adapter.get_nested_value('webapp', 'career_analysis', 'document_styling', 'spacing', default={
            'spacing_1': 4,
            'spacing_2': 8,
            'spacing_3': 12,
            'spacing_4': 16,
            'spacing_5': 20,
            'spacing_6': 24,
            'spacing_8': 32
        })
    
    def get_career_analysis_paths_config(self) -> Dict[str, str]:
        """
        Get file and directory paths configuration.
        
        Returns:
            Dictionary containing path configurations
        """
        return self._adapter.get_nested_value('webapp', 'career_analysis', 'paths', default={
            'templates_dir': 'templates',
            'sections_templates_dir': 'templates/sections',
            'output_dir': 'output'
        })
    
    def get_career_analysis_output_config(self) -> Dict[str, Any]:
        """
        Get output format configuration.
        
        Returns:
            Dictionary containing output format settings and patterns
        """
        return self._adapter.get_nested_value('webapp', 'career_analysis', 'output', default={
            'supported_formats': ['word', 'pdf', 'powerpoint', 'html', 'markdown'],
            'default_format': 'word',
            'default_audience': 'business_leaders',
            'default_scenario': 'skills_gap_analysis'
        })
    
    def get_career_analysis_sections_config(self) -> Dict[str, Any]:
        """
        Get sections configuration.
        
        Returns:
            Dictionary containing section order and titles
        """
        return self._adapter.get_nested_value('webapp', 'career_analysis', 'sections', default={
            'order': ['executive_summary', 'current_role_context', 'pathway_analysis', 'strategic_recommendations', 'conclusion'],
            'titles': {
                'executive_summary': 'Executive Summary',
                'current_role_context': 'Current Role Context',
                'pathway_analysis': 'Pathway Analysis: Top 3 Strategic Opportunities',
                'strategic_recommendations': 'Strategic Recommendations',
                'conclusion': 'Conclusion'
            }
        })
    
    def get_career_analysis_validation_config(self) -> Dict[str, Any]:
        """
        Get validation configuration.
        
        Returns:
            Dictionary containing validation rules and limits
        """
        return self._adapter.get_nested_value('webapp', 'career_analysis', 'validation', default={
            'min_job_id_length': 1,
            'max_job_id_length': 50,
            'similarity_range_min': 0,
            'similarity_range_max': 100,
            'top_n_min': 1,
            'top_n_max': 10
        })
    
    # ==========================================================================
    # Frontend Configuration
    # ==========================================================================
    
    def get_frontend_javascript_config(self) -> Dict[str, Any]:
        """
        Get JavaScript configuration.
        
        Returns:
            Dictionary containing JavaScript settings and defaults
        """
        return self._adapter.get_nested_value('webapp', 'frontend', 'javascript', default={
            'api_timeout_ms': 10000,
            'cache_duration_ms': 300000,
            'default_similarity_threshold': 0.5,
            'max_results_per_page': 50,
            'animation_duration_ms': 300
        })
    
    def get_frontend_css_config(self) -> Dict[str, Any]:
        """
        Get CSS configuration.
        
        Returns:
            Dictionary containing CSS variables and component settings
        """
        return self._adapter.get_nested_value('webapp', 'frontend', 'css', default={})
    
    def get_frontend_css_variables_config(self) -> Dict[str, str]:
        """
        Get CSS variables configuration.
        
        Returns:
            Dictionary containing CSS custom property values
        """
        return self._adapter.get_nested_value('webapp', 'frontend', 'css', 'variables', default={
            'primary_color': '#dc2626',
            'font_heading': 'Epilogue',
            'font_primary': 'Source Sans Pro',
            'spacing_base': '1rem'
        })
    
    # ==========================================================================
    # Database Configuration
    # ==========================================================================
    
    def get_database_query_limits_config(self) -> Dict[str, int]:
        """
        Get database query limits configuration.
        
        Returns:
            Dictionary containing query result limits
        """
        return self._adapter.get_nested_value('webapp', 'database', 'query_limits', default={
            'default_limit': 50,
            'search_limit': 10,
            'pathways_limit': 12,
            'workforce_limit': 15,
            'export_limit': 6
        })
    
    def get_database_similarity_config(self) -> Dict[str, float]:
        """
        Get database similarity configuration.
        
        Returns:
            Dictionary containing similarity thresholds for queries
        """
        return self._adapter.get_nested_value('webapp', 'database', 'similarity_config', default={
            'default_threshold': 0.5,
            'pathway_threshold': 0.6,
            'high_similarity': 0.8,
            'cross_family_threshold': 0.4
        })
    
    def get_database_performance_config(self) -> Dict[str, int]:
        """
        Get database performance configuration.
        
        Returns:
            Dictionary containing performance settings
        """
        return self._adapter.get_nested_value('webapp', 'database', 'performance', default={
            'max_depth': 3,
            'max_results': 10,
            'timeout_seconds': 30,
            'connection_pool_size': 5
        })
    
    # ==========================================================================
    # Development Configuration
    # ==========================================================================
    
    def get_development_debug_config(self) -> Dict[str, bool]:
        """
        Get development debug configuration.
        
        Returns:
            Dictionary containing debug settings
        """
        return self._adapter.get_nested_value('webapp', 'development', 'debug', default={
            'enabled': False,
            'log_sql_queries': False,
            'show_template_errors': True
        })
    
    def get_development_testing_config(self) -> Dict[str, bool]:
        """
        Get development testing configuration.
        
        Returns:
            Dictionary containing testing settings
        """
        return self._adapter.get_nested_value('webapp', 'development', 'testing', default={
            'mock_data_enabled': False,
            'performance_monitoring': False
        })
    
    # ==========================================================================
    # Convenience Methods for Common Patterns
    # ==========================================================================
    
    def get_database_path(self, model_version: Optional[str] = None) -> Path:
        """
        Get the complete database path using dynamic quarterly version resolution.
        
        Args:
            model_version: Optional specific model version. If None, uses ModelVersionManager 
                          to find the latest quarterly version.
            
        Returns:
            Path object pointing to the business context database
        """
        if model_version is not None:
            # Specific version requested - use hardcoded path
            db_config = self.get_core_database_config()
            filename = db_config.get('business_context_filename', 'business_context.sqlite')
            
            # Construct path relative to skill-similarity-engine project root
            config_dir = Path(__file__).parent  # /skill-similarity-engine/src/skill_similarity_engine/config/
            project_root = config_dir.parent.parent.parent  # /skill-similarity-engine/
            return project_root / 'models' / model_version / filename
        else:
            # Use dynamic versioning system to find latest quarterly database
            try:
                from ..webapp.config.database_config import DatabaseConfig
                database_config = DatabaseConfig()
                return database_config.get_database_path()
            except Exception as e:
                # Fallback to hardcoded default if dynamic resolution fails
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Dynamic database path resolution failed: {e}")
                
                db_config = self.get_core_database_config()
                model_version = db_config.get('default_model_version', '2025-Q2')
                filename = db_config.get('business_context_filename', 'business_context.sqlite')
                
                config_dir = Path(__file__).parent
                project_root = config_dir.parent.parent.parent
                fallback_path = project_root / 'models' / model_version / filename
                logger.warning(f"Using fallback database path: {fallback_path}")
                return fallback_path
    
    def get_similarity_threshold(self, threshold_type: str = 'default') -> float:
        """
        Get similarity threshold for the specified type.
        
        Args:
            threshold_type: Type of threshold ('default', 'pathway', 'high', 'cross_family')
            
        Returns:
            Similarity threshold value
        """
        if threshold_type == 'default':
            return self.get_core_api_config().get('default_similarity_threshold', 0.5)
        elif threshold_type == 'pathway':
            return self.get_core_api_config().get('pathway_similarity_threshold', 0.6)
        elif threshold_type == 'high':
            return self.get_database_similarity_config().get('high_similarity', 0.8)
        elif threshold_type == 'cross_family':
            return self.get_core_api_config().get('cross_family_similarity_threshold', 0.4)
        else:
            raise ValueError(f"Unknown threshold type: {threshold_type}")
    
    def get_result_limit(self, limit_type: str = 'default') -> int:
        """
        Get result limit for the specified type.
        
        Args:
            limit_type: Type of limit ('default', 'search', 'pathways', 'export')
            
        Returns:
            Result limit value
        """
        if limit_type == 'default':
            return self.get_database_query_limits_config().get('default_limit', 50)
        elif limit_type == 'search':
            return self.get_core_api_config().get('default_search_limit', 10)
        elif limit_type == 'pathways':
            return self.get_core_api_config().get('max_pathways_display', 12)
        elif limit_type == 'export':
            return self.get_database_query_limits_config().get('export_limit', 6)
        else:
            raise ValueError(f"Unknown limit type: {limit_type}")


# =============================================================================
# Module-Level Factory Functions
# =============================================================================

_webapp_config_manager = None

def get_webapp_config_manager(config_path: Optional[Path] = None) -> WebappConfigManager:
    """
    Get the global webapp configuration manager instance.
    
    Args:
        config_path: Optional path to webapp configuration file
        
    Returns:
        WebappConfigManager instance
    """
    global _webapp_config_manager
    
    if _webapp_config_manager is None or config_path is not None:
        _webapp_config_manager = WebappConfigManager(config_path)
    
    return _webapp_config_manager

def reload_webapp_config() -> None:
    """Reload webapp configuration from file."""
    global _webapp_config_manager
    
    if _webapp_config_manager is not None:
        _webapp_config_manager.reload_config() 