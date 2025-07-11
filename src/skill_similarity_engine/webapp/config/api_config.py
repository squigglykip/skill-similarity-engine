"""
ApiConfig - API Endpoint Configuration
======================================

Configuration class for API endpoints following PTH OOP/Config-driven 
architectural philosophy. Eliminates hardcoded values from API blueprints
and provides centralized endpoint configuration.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ApiDefaults:
    """Default values for API configuration."""
    # General API defaults
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100
    DEFAULT_TIMEOUT: int = 30
    
    # Search API defaults
    SEARCH_MIN_QUERY_LENGTH: int = 2
    SEARCH_MAX_RESULTS: int = 50
    SEARCH_DEFAULT_LIMIT: int = 10
    
    # Jobs API defaults
    JOBS_DEFAULT_LIMIT: int = 20
    JOBS_MAX_LIMIT: int = 100
    SIMILARITY_DEFAULT_LIMIT: int = 10
    SIMILARITY_MAX_LIMIT: int = 50
    
    # Career Analysis API defaults
    ANALYSIS_DEFAULT_TOP_N: int = 3
    ANALYSIS_MAX_TOP_N: int = 10
    ANALYSIS_DEFAULT_SIMILARITY_MIN: float = 0.4
    ANALYSIS_DEFAULT_SIMILARITY_MAX: float = 0.9
    
    # Export API defaults
    EXPORT_MAX_RECORDS: int = 1000
    EXPORT_TIMEOUT: int = 60
    EXPORT_FORMATS: Optional[list] = None  # Will be set in __post_init__
    
    # Performance defaults
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TTL: int = 300  # 5 minutes
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60
    
    def __post_init__(self):
        if self.EXPORT_FORMATS is None:
            self.EXPORT_FORMATS = ['csv', 'json', 'xlsx']

class ApiConfig:
    """API configuration following PTH patterns."""
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """Initialize API configuration with optional overrides."""
        self.config_override = config_override or {}
        self.defaults = ApiDefaults()
    
    def get_search_api_config(self) -> Dict[str, Any]:
        """Get Search API configuration."""
        search_config = self.config_override.get('search_api', {})
        return {
            'min_query_length': search_config.get('min_query_length', self.defaults.SEARCH_MIN_QUERY_LENGTH),
            'max_results': search_config.get('max_results', self.defaults.SEARCH_MAX_RESULTS),
            'default_limit': search_config.get('default_limit', self.defaults.SEARCH_DEFAULT_LIMIT),
            'timeout': search_config.get('timeout', self.defaults.DEFAULT_TIMEOUT),
            'cache_enabled': search_config.get('cache_enabled', self.defaults.CACHE_ENABLED),
            'cache_ttl': search_config.get('cache_ttl', self.defaults.CACHE_DEFAULT_TTL),
        }
    
    def get_jobs_api_config(self) -> Dict[str, Any]:
        """Get Jobs API configuration."""
        jobs_config = self.config_override.get('jobs_api', {})
        return {
            'default_limit': jobs_config.get('default_limit', self.defaults.JOBS_DEFAULT_LIMIT),
            'max_limit': jobs_config.get('max_limit', self.defaults.JOBS_MAX_LIMIT),
            'similarity_default_limit': jobs_config.get('similarity_default_limit', self.defaults.SIMILARITY_DEFAULT_LIMIT),
            'similarity_max_limit': jobs_config.get('similarity_max_limit', self.defaults.SIMILARITY_MAX_LIMIT),
            'timeout': jobs_config.get('timeout', self.defaults.DEFAULT_TIMEOUT),
            'cache_enabled': jobs_config.get('cache_enabled', self.defaults.CACHE_ENABLED),
            'cache_ttl': jobs_config.get('cache_ttl', self.defaults.CACHE_DEFAULT_TTL),
        }
    
    def get_career_analysis_api_config(self) -> Dict[str, Any]:
        """Get Career Analysis API configuration."""
        analysis_config = self.config_override.get('career_analysis_api', {})
        return {
            'default_top_n': analysis_config.get('default_top_n', self.defaults.ANALYSIS_DEFAULT_TOP_N),
            'max_top_n': analysis_config.get('max_top_n', self.defaults.ANALYSIS_MAX_TOP_N),
            'default_similarity_min': analysis_config.get('default_similarity_min', self.defaults.ANALYSIS_DEFAULT_SIMILARITY_MIN),
            'default_similarity_max': analysis_config.get('default_similarity_max', self.defaults.ANALYSIS_DEFAULT_SIMILARITY_MAX),
            'timeout': analysis_config.get('timeout', self.defaults.DEFAULT_TIMEOUT),
            'cache_enabled': analysis_config.get('cache_enabled', self.defaults.CACHE_ENABLED),
            'cache_ttl': analysis_config.get('cache_ttl', self.defaults.CACHE_DEFAULT_TTL),
        }
    
    def get_export_api_config(self) -> Dict[str, Any]:
        """Get Export API configuration."""
        export_config = self.config_override.get('export_api', {})
        return {
            'max_records': export_config.get('max_records', self.defaults.EXPORT_MAX_RECORDS),
            'timeout': export_config.get('timeout', self.defaults.EXPORT_TIMEOUT),
            'supported_formats': export_config.get('supported_formats', self.defaults.EXPORT_FORMATS),
            'cache_enabled': export_config.get('cache_enabled', self.defaults.CACHE_ENABLED),
            'cache_ttl': export_config.get('cache_ttl', self.defaults.CACHE_DEFAULT_TTL),
        }
    
    def get_pathways_api_config(self) -> Dict[str, Any]:
        """Get Pathways API configuration."""
        pathways_config = self.config_override.get('pathways_api', {})
        return {
            'default_limit': pathways_config.get('default_limit', self.defaults.DEFAULT_PAGE_SIZE),
            'max_limit': pathways_config.get('max_limit', self.defaults.MAX_PAGE_SIZE),
            'timeout': pathways_config.get('timeout', self.defaults.DEFAULT_TIMEOUT),
            'cache_enabled': pathways_config.get('cache_enabled', self.defaults.CACHE_ENABLED),
            'cache_ttl': pathways_config.get('cache_ttl', self.defaults.CACHE_DEFAULT_TTL),
        }
    
    def get_similarity_api_config(self) -> Dict[str, Any]:
        """Get Similarity API configuration."""
        similarity_config = self.config_override.get('similarity_api', {})
        return {
            'default_limit': similarity_config.get('default_limit', self.defaults.SIMILARITY_DEFAULT_LIMIT),
            'max_limit': similarity_config.get('max_limit', self.defaults.SIMILARITY_MAX_LIMIT),
            'timeout': similarity_config.get('timeout', self.defaults.DEFAULT_TIMEOUT),
            'cache_enabled': similarity_config.get('cache_enabled', self.defaults.CACHE_ENABLED),
            'cache_ttl': similarity_config.get('cache_ttl', self.defaults.CACHE_DEFAULT_TTL),
        }
    
    def get_metadata_api_config(self) -> Dict[str, Any]:
        """Get Metadata API configuration."""
        metadata_config = self.config_override.get('metadata_api', {})
        return {
            'timeout': metadata_config.get('timeout', self.defaults.DEFAULT_TIMEOUT),
            'cache_enabled': metadata_config.get('cache_enabled', self.defaults.CACHE_ENABLED),
            'cache_ttl': metadata_config.get('cache_ttl', self.defaults.CACHE_DEFAULT_TTL),
        }
    
    def get_general_api_config(self) -> Dict[str, Any]:
        """Get general API configuration."""
        general_config = self.config_override.get('general', {})
        return {
            'default_page_size': general_config.get('default_page_size', self.defaults.DEFAULT_PAGE_SIZE),
            'max_page_size': general_config.get('max_page_size', self.defaults.MAX_PAGE_SIZE),
            'default_timeout': general_config.get('default_timeout', self.defaults.DEFAULT_TIMEOUT),
            'cache_enabled': general_config.get('cache_enabled', self.defaults.CACHE_ENABLED),
            'cache_default_ttl': general_config.get('cache_default_ttl', self.defaults.CACHE_DEFAULT_TTL),
            'rate_limit_enabled': general_config.get('rate_limit_enabled', self.defaults.RATE_LIMIT_ENABLED),
            'rate_limit_per_minute': general_config.get('rate_limit_per_minute', self.defaults.RATE_LIMIT_PER_MINUTE),
        }
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration for APIs."""
        cors_config = self.config_override.get('cors', {})
        return {
            'enabled': cors_config.get('enabled', False),
            'origins': cors_config.get('origins', ['http://localhost:5000']),
            'methods': cors_config.get('methods', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']),
            'headers': cors_config.get('headers', ['Content-Type', 'Authorization']),
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate API configuration."""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate search configuration
        search_config = self.get_search_api_config()
        if search_config['min_query_length'] <= 0:
            validation_results['errors'].append("Search min query length must be positive")
            validation_results['valid'] = False
        
        if search_config['max_results'] <= 0:
            validation_results['errors'].append("Search max results must be positive")
            validation_results['valid'] = False
        
        # Validate jobs configuration
        jobs_config = self.get_jobs_api_config()
        if jobs_config['default_limit'] > jobs_config['max_limit']:
            validation_results['errors'].append("Jobs default limit cannot exceed max limit")
            validation_results['valid'] = False
        
        # Validate career analysis configuration
        analysis_config = self.get_career_analysis_api_config()
        if analysis_config['default_top_n'] > analysis_config['max_top_n']:
            validation_results['errors'].append("Analysis default top_n cannot exceed max top_n")
            validation_results['valid'] = False
        
        if not (0.0 <= analysis_config['default_similarity_min'] <= 1.0):
            validation_results['errors'].append("Analysis similarity min must be between 0.0 and 1.0")
            validation_results['valid'] = False
        
        if not (0.0 <= analysis_config['default_similarity_max'] <= 1.0):
            validation_results['errors'].append("Analysis similarity max must be between 0.0 and 1.0")
            validation_results['valid'] = False
        
        if analysis_config['default_similarity_min'] >= analysis_config['default_similarity_max']:
            validation_results['errors'].append("Analysis similarity min must be less than max")
            validation_results['valid'] = False
        
        # Validate export configuration
        export_config = self.get_export_api_config()
        if export_config['max_records'] <= 0:
            validation_results['errors'].append("Export max records must be positive")
            validation_results['valid'] = False
        
        if not export_config['supported_formats']:
            validation_results['warnings'].append("No export formats configured")
        
        return validation_results
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get comprehensive API configuration summary."""
        return {
            'search_api': self.get_search_api_config(),
            'jobs_api': self.get_jobs_api_config(),
            'career_analysis_api': self.get_career_analysis_api_config(),
            'export_api': self.get_export_api_config(),
            'pathways_api': self.get_pathways_api_config(),
            'similarity_api': self.get_similarity_api_config(),
            'metadata_api': self.get_metadata_api_config(),
            'general': self.get_general_api_config(),
            'cors': self.get_cors_config(),
        } 