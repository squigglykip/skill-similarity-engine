"""
BlueprintConfig - Blueprint Configuration
========================================

Configuration class for Flask blueprints following PTH OOP/Config-driven 
architectural philosophy. Eliminates hardcoded values from blueprint handlers.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class BlueprintDefaults:
    """Default values for blueprint configuration."""
    # General blueprint defaults
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Main blueprint defaults
    MAIN_SAMPLE_JOBS_LIMIT: int = 20
    MAIN_WELCOME_MESSAGE: str = "Welcome to NAB Skills Intelligence Platform"
    
    # Job Explorer blueprint defaults
    JOB_EXPLORER_DEFAULT_LIMIT: int = 20
    JOB_EXPLORER_SIMILARITY_LIMIT: int = 10
    JOB_EXPLORER_SIMILARITY_THRESHOLD: float = 0.5
    
    # Career Analysis blueprint defaults
    CAREER_ANALYSIS_SAMPLE_LIMIT: int = 20
    CAREER_ANALYSIS_DEFAULT_SCENARIO: str = 'skills_gap_analysis'
    CAREER_ANALYSIS_DEFAULT_AUDIENCE: str = 'business_leaders'
    
    # Career Pathways blueprint defaults
    CAREER_PATHWAYS_SAMPLE_LIMIT: int = 20
    CAREER_PATHWAYS_MAX_DEPTH: int = 5
    CAREER_PATHWAYS_DEFAULT_FILTERS: Optional[dict] = None  # Will be set in __post_init__
    
    # Performance defaults
    BLUEPRINT_CACHE_ENABLED: bool = True
    BLUEPRINT_CACHE_TIMEOUT: int = 300  # 5 minutes
    
    def __post_init__(self):
        if self.CAREER_PATHWAYS_DEFAULT_FILTERS is None:
            self.CAREER_PATHWAYS_DEFAULT_FILTERS = {
                'include_lateral': True,
                'include_promotion': True,
                'include_cross_functional': True,
            }

class BlueprintConfig:
    """Blueprint configuration following PTH patterns."""
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """Initialize blueprint configuration with optional overrides."""
        self.config_override = config_override or {}
        self.defaults = BlueprintDefaults()
    
    def get_main_blueprint_config(self) -> Dict[str, Any]:
        """Get main blueprint configuration."""
        main_config = self.config_override.get('main', {})
        return {
            'sample_jobs_limit': main_config.get('sample_jobs_limit', self.defaults.MAIN_SAMPLE_JOBS_LIMIT),
            'welcome_message': main_config.get('welcome_message', self.defaults.MAIN_WELCOME_MESSAGE),
            'page_size': main_config.get('page_size', self.defaults.DEFAULT_PAGE_SIZE),
            'max_page_size': main_config.get('max_page_size', self.defaults.MAX_PAGE_SIZE),
            'cache_enabled': main_config.get('cache_enabled', self.defaults.BLUEPRINT_CACHE_ENABLED),
            'cache_timeout': main_config.get('cache_timeout', self.defaults.BLUEPRINT_CACHE_TIMEOUT),
        }
    
    def get_job_explorer_config(self) -> Dict[str, Any]:
        """Get job explorer blueprint configuration."""
        job_explorer_config = self.config_override.get('job_explorer', {})
        return {
            'default_limit': job_explorer_config.get('default_limit', self.defaults.JOB_EXPLORER_DEFAULT_LIMIT),
            'similarity_limit': job_explorer_config.get('similarity_limit', self.defaults.JOB_EXPLORER_SIMILARITY_LIMIT),
            'similarity_threshold': job_explorer_config.get('similarity_threshold', self.defaults.JOB_EXPLORER_SIMILARITY_THRESHOLD),
            'page_size': job_explorer_config.get('page_size', self.defaults.DEFAULT_PAGE_SIZE),
            'max_page_size': job_explorer_config.get('max_page_size', self.defaults.MAX_PAGE_SIZE),
            'cache_enabled': job_explorer_config.get('cache_enabled', self.defaults.BLUEPRINT_CACHE_ENABLED),
            'cache_timeout': job_explorer_config.get('cache_timeout', self.defaults.BLUEPRINT_CACHE_TIMEOUT),
        }
    
    def get_career_analysis_config(self) -> Dict[str, Any]:
        """Get career analysis blueprint configuration."""
        career_analysis_config = self.config_override.get('career_analysis', {})
        return {
            'sample_limit': career_analysis_config.get('sample_limit', self.defaults.CAREER_ANALYSIS_SAMPLE_LIMIT),
            'default_scenario': career_analysis_config.get('default_scenario', self.defaults.CAREER_ANALYSIS_DEFAULT_SCENARIO),
            'default_audience': career_analysis_config.get('default_audience', self.defaults.CAREER_ANALYSIS_DEFAULT_AUDIENCE),
            'page_size': career_analysis_config.get('page_size', self.defaults.DEFAULT_PAGE_SIZE),
            'max_page_size': career_analysis_config.get('max_page_size', self.defaults.MAX_PAGE_SIZE),
            'cache_enabled': career_analysis_config.get('cache_enabled', self.defaults.BLUEPRINT_CACHE_ENABLED),
            'cache_timeout': career_analysis_config.get('cache_timeout', self.defaults.BLUEPRINT_CACHE_TIMEOUT),
        }
    
    def get_career_pathways_config(self) -> Dict[str, Any]:
        """Get career pathways blueprint configuration."""
        career_pathways_config = self.config_override.get('career_pathways', {})
        return {
            'sample_limit': career_pathways_config.get('sample_limit', self.defaults.CAREER_PATHWAYS_SAMPLE_LIMIT),
            'max_depth': career_pathways_config.get('max_depth', self.defaults.CAREER_PATHWAYS_MAX_DEPTH),
            'default_filters': career_pathways_config.get('default_filters', self.defaults.CAREER_PATHWAYS_DEFAULT_FILTERS),
            'page_size': career_pathways_config.get('page_size', self.defaults.DEFAULT_PAGE_SIZE),
            'max_page_size': career_pathways_config.get('max_page_size', self.defaults.MAX_PAGE_SIZE),
            'cache_enabled': career_pathways_config.get('cache_enabled', self.defaults.BLUEPRINT_CACHE_ENABLED),
            'cache_timeout': career_pathways_config.get('cache_timeout', self.defaults.BLUEPRINT_CACHE_TIMEOUT),
        }
    
    def get_general_blueprint_config(self) -> Dict[str, Any]:
        """Get general blueprint configuration."""
        general_config = self.config_override.get('general', {})
        return {
            'default_page_size': general_config.get('default_page_size', self.defaults.DEFAULT_PAGE_SIZE),
            'max_page_size': general_config.get('max_page_size', self.defaults.MAX_PAGE_SIZE),
            'cache_enabled': general_config.get('cache_enabled', self.defaults.BLUEPRINT_CACHE_ENABLED),
            'cache_timeout': general_config.get('cache_timeout', self.defaults.BLUEPRINT_CACHE_TIMEOUT),
        }
    
    def get_template_config(self) -> Dict[str, Any]:
        """Get template configuration for blueprints."""
        template_config = self.config_override.get('templates', {})
        return {
            'auto_reload': template_config.get('auto_reload', True),
            'cache_templates': template_config.get('cache_templates', False),
            'template_folder': template_config.get('template_folder', 'templates'),
            'static_folder': template_config.get('static_folder', 'static'),
        }
    
    def get_error_handling_config(self) -> Dict[str, Any]:
        """Get error handling configuration for blueprints."""
        error_config = self.config_override.get('error_handling', {})
        return {
            'show_debug_info': error_config.get('show_debug_info', False),
            'custom_error_pages': error_config.get('custom_error_pages', True),
            'log_errors': error_config.get('log_errors', True),
            'fallback_templates': error_config.get('fallback_templates', True),
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate blueprint configuration."""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate main blueprint configuration
        main_config = self.get_main_blueprint_config()
        if main_config['sample_jobs_limit'] <= 0:
            validation_results['errors'].append("Main blueprint sample jobs limit must be positive")
            validation_results['valid'] = False
        
        # Validate job explorer configuration
        job_explorer_config = self.get_job_explorer_config()
        if job_explorer_config['default_limit'] <= 0:
            validation_results['errors'].append("Job explorer default limit must be positive")
            validation_results['valid'] = False
        
        if not (0.0 <= job_explorer_config['similarity_threshold'] <= 1.0):
            validation_results['errors'].append("Job explorer similarity threshold must be between 0.0 and 1.0")
            validation_results['valid'] = False
        
        # Validate career analysis configuration
        career_analysis_config = self.get_career_analysis_config()
        if career_analysis_config['sample_limit'] <= 0:
            validation_results['errors'].append("Career analysis sample limit must be positive")
            validation_results['valid'] = False
        
        # Validate career pathways configuration
        career_pathways_config = self.get_career_pathways_config()
        if career_pathways_config['max_depth'] <= 0:
            validation_results['errors'].append("Career pathways max depth must be positive")
            validation_results['valid'] = False
        
        # Validate general configuration
        general_config = self.get_general_blueprint_config()
        if general_config['default_page_size'] > general_config['max_page_size']:
            validation_results['errors'].append("Default page size cannot exceed max page size")
            validation_results['valid'] = False
        
        return validation_results
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get comprehensive blueprint configuration summary."""
        return {
            'main': self.get_main_blueprint_config(),
            'job_explorer': self.get_job_explorer_config(),
            'career_analysis': self.get_career_analysis_config(),
            'career_pathways': self.get_career_pathways_config(),
            'general': self.get_general_blueprint_config(),
            'templates': self.get_template_config(),
            'error_handling': self.get_error_handling_config(),
        } 