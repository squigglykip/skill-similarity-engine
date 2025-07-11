"""
ServiceConfig - Service Layer Configuration
==========================================

Configuration class for the service layer following PTH OOP/Config-driven 
architectural philosophy. Eliminates hardcoded values from DatabaseService,
JobService, and other service classes.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ServiceDefaults:
    """Default values for service layer configuration."""
    # DatabaseService defaults
    DEFAULT_JOB_LIMIT: int = 20
    DEFAULT_SEARCH_LIMIT: int = 10
    DEFAULT_SIMILARITY_LIMIT: int = 10
    DEFAULT_SIMILARITY_THRESHOLD: float = 0.5
    MIN_SIMILARITY_THRESHOLD: float = 0.1
    MAX_SIMILARITY_THRESHOLD: float = 0.99
    
    # JobService defaults
    DEFAULT_DISPLAY_FORMAT: str = 'standard'
    DISPLAY_NAME_FORMATS: Optional[list] = None  # Will be set in __post_init__
    
    # Performance defaults
    SERVICE_TIMEOUT: int = 30
    MAX_BATCH_SIZE: int = 100
    CACHE_ENABLED: bool = True
    CACHE_TIMEOUT: int = 300  # 5 minutes
    
    # Error handling defaults
    RETRY_ATTEMPTS: int = 3
    RETRY_DELAY: float = 1.0
    FALLBACK_ENABLED: bool = True
    
    def __post_init__(self):
        if self.DISPLAY_NAME_FORMATS is None:
            self.DISPLAY_NAME_FORMATS = ['standard', 'search', 'dropdown', 'compact']

class ServiceConfig:
    """Service layer configuration following PTH patterns."""
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """Initialize service configuration with optional overrides."""
        self.config_override = config_override or {}
        self.defaults = ServiceDefaults()
    
    def get_database_service_config(self) -> Dict[str, Any]:
        """Get DatabaseService configuration."""
        db_config = self.config_override.get('database_service', {})
        return {
            'default_job_limit': db_config.get('default_job_limit', self.defaults.DEFAULT_JOB_LIMIT),
            'default_search_limit': db_config.get('default_search_limit', self.defaults.DEFAULT_SEARCH_LIMIT),
            'default_similarity_limit': db_config.get('default_similarity_limit', self.defaults.DEFAULT_SIMILARITY_LIMIT),
            'default_similarity_threshold': db_config.get('default_similarity_threshold', self.defaults.DEFAULT_SIMILARITY_THRESHOLD),
            'min_similarity_threshold': db_config.get('min_similarity_threshold', self.defaults.MIN_SIMILARITY_THRESHOLD),
            'max_similarity_threshold': db_config.get('max_similarity_threshold', self.defaults.MAX_SIMILARITY_THRESHOLD),
            'timeout': db_config.get('timeout', self.defaults.SERVICE_TIMEOUT),
            'max_batch_size': db_config.get('max_batch_size', self.defaults.MAX_BATCH_SIZE),
            'cache_enabled': db_config.get('cache_enabled', self.defaults.CACHE_ENABLED),
            'cache_timeout': db_config.get('cache_timeout', self.defaults.CACHE_TIMEOUT),
            'retry_attempts': db_config.get('retry_attempts', self.defaults.RETRY_ATTEMPTS),
            'retry_delay': db_config.get('retry_delay', self.defaults.RETRY_DELAY),
            'fallback_enabled': db_config.get('fallback_enabled', self.defaults.FALLBACK_ENABLED),
        }
    
    def get_job_service_config(self) -> Dict[str, Any]:
        """Get JobService configuration."""
        job_config = self.config_override.get('job_service', {})
        return {
            'default_display_format': job_config.get('default_display_format', self.defaults.DEFAULT_DISPLAY_FORMAT),
            'display_name_formats': job_config.get('display_name_formats', self.defaults.DISPLAY_NAME_FORMATS),
            'timeout': job_config.get('timeout', self.defaults.SERVICE_TIMEOUT),
            'max_batch_size': job_config.get('max_batch_size', self.defaults.MAX_BATCH_SIZE),
            'cache_enabled': job_config.get('cache_enabled', self.defaults.CACHE_ENABLED),
            'cache_timeout': job_config.get('cache_timeout', self.defaults.CACHE_TIMEOUT),
            'fallback_enabled': job_config.get('fallback_enabled', self.defaults.FALLBACK_ENABLED),
        }
    
    def get_similarity_thresholds(self) -> Dict[str, float]:
        """Get similarity threshold configuration."""
        similarity_config = self.config_override.get('similarity_thresholds', {})
        return {
            'excellent_min': similarity_config.get('excellent_min', 0.8),
            'excellent_max': similarity_config.get('excellent_max', 1.0),
            'good_min': similarity_config.get('good_min', 0.6),
            'good_max': similarity_config.get('good_max', 0.8),
            'moderate_min': similarity_config.get('moderate_min', 0.4),
            'moderate_max': similarity_config.get('moderate_max', 0.6),
            'default_threshold': similarity_config.get('default_threshold', self.defaults.DEFAULT_SIMILARITY_THRESHOLD),
            'min_threshold': similarity_config.get('min_threshold', self.defaults.MIN_SIMILARITY_THRESHOLD),
            'max_threshold': similarity_config.get('max_threshold', self.defaults.MAX_SIMILARITY_THRESHOLD),
        }
    
    def get_timeline_config(self) -> Dict[str, str]:
        """Get timeline estimation configuration."""
        timeline_config = self.config_override.get('timeline_estimates', {})
        return {
            'excellent_timeline': timeline_config.get('excellent_timeline', '8-12'),
            'good_timeline': timeline_config.get('good_timeline', '12-16'),
            'moderate_timeline': timeline_config.get('moderate_timeline', '16-24'),
            'default_timeline': timeline_config.get('default_timeline', '12-16'),
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration for services."""
        perf_config = self.config_override.get('performance', {})
        return {
            'timeout': perf_config.get('timeout', self.defaults.SERVICE_TIMEOUT),
            'max_batch_size': perf_config.get('max_batch_size', self.defaults.MAX_BATCH_SIZE),
            'cache_enabled': perf_config.get('cache_enabled', self.defaults.CACHE_ENABLED),
            'cache_timeout': perf_config.get('cache_timeout', self.defaults.CACHE_TIMEOUT),
            'retry_attempts': perf_config.get('retry_attempts', self.defaults.RETRY_ATTEMPTS),
            'retry_delay': perf_config.get('retry_delay', self.defaults.RETRY_DELAY),
        }
    
    def get_error_handling_config(self) -> Dict[str, Any]:
        """Get error handling configuration for services."""
        error_config = self.config_override.get('error_handling', {})
        return {
            'retry_attempts': error_config.get('retry_attempts', self.defaults.RETRY_ATTEMPTS),
            'retry_delay': error_config.get('retry_delay', self.defaults.RETRY_DELAY),
            'fallback_enabled': error_config.get('fallback_enabled', self.defaults.FALLBACK_ENABLED),
            'timeout': error_config.get('timeout', self.defaults.SERVICE_TIMEOUT),
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate service configuration."""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate similarity thresholds
        thresholds = self.get_similarity_thresholds()
        if thresholds['min_threshold'] >= thresholds['max_threshold']:
            validation_results['errors'].append("Min similarity threshold must be less than max threshold")
            validation_results['valid'] = False
        
        # Validate performance settings
        perf_config = self.get_performance_config()
        if perf_config['timeout'] <= 0:
            validation_results['errors'].append("Service timeout must be positive")
            validation_results['valid'] = False
        
        if perf_config['max_batch_size'] <= 0:
            validation_results['errors'].append("Max batch size must be positive")
            validation_results['valid'] = False
        
        # Validate retry settings
        error_config = self.get_error_handling_config()
        if error_config['retry_attempts'] < 0:
            validation_results['errors'].append("Retry attempts cannot be negative")
            validation_results['valid'] = False
        
        if error_config['retry_delay'] < 0:
            validation_results['errors'].append("Retry delay cannot be negative")
            validation_results['valid'] = False
        
        return validation_results
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get comprehensive service configuration summary."""
        return {
            'database_service': self.get_database_service_config(),
            'job_service': self.get_job_service_config(),
            'similarity_thresholds': self.get_similarity_thresholds(),
            'timeline_config': self.get_timeline_config(),
            'performance': self.get_performance_config(),
            'error_handling': self.get_error_handling_config(),
        } 