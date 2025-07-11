"""
WebappConfig - Main Configuration Orchestrator
==============================================

Main configuration class for the webapp module following PTH OOP/Config-driven 
architectural philosophy. Eliminates hardcoded values and provides centralized
configuration injection for all webapp components.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from .service_config import ServiceConfig
from .api_config import ApiConfig
from .database_config import DatabaseConfig
from .blueprint_config import BlueprintConfig

@dataclass
class WebappDefaults:
    """Default values for webapp configuration."""
    # Flask application defaults
    SECRET_KEY: str = 'dev-key-change-in-production'
    DEBUG: bool = True
    HOST: str = 'localhost'
    PORT: int = 5000
    
    # Database defaults
    DATABASE_NAME: str = 'business_context.sqlite'
    DATABASE_PATH_FALLBACK: str = 'models/2025-Q2/business_context.sqlite'
    
    # Display defaults
    DISPLAY_MANAGER_ENABLED: bool = True
    FALLBACK_JOB_TITLES: bool = True
    
    # Performance defaults
    REQUEST_TIMEOUT: int = 30
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    
    # Logging defaults
    LOG_LEVEL: str = 'INFO'
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

class WebappConfig:
    """Main webapp configuration orchestrator following PTH patterns."""
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """Initialize webapp configuration with optional overrides."""
        self.config_override = config_override or {}
        self.defaults = WebappDefaults()
        
        # Initialize sub-configurations
        self.service_config = ServiceConfig(self.config_override.get('services', {}))
        self.api_config = ApiConfig(self.config_override.get('api', {}))
        self.database_config = DatabaseConfig(self.config_override.get('database', {}))
        self.blueprint_config = BlueprintConfig(self.config_override.get('blueprints', {}))
    
    def get_flask_config(self) -> Dict[str, Any]:
        """Get Flask application configuration."""
        return {
            'SECRET_KEY': self.config_override.get('SECRET_KEY', self.defaults.SECRET_KEY),
            'DEBUG': self.config_override.get('DEBUG', self.defaults.DEBUG),
            'MAX_CONTENT_LENGTH': self.config_override.get('MAX_CONTENT_LENGTH', self.defaults.MAX_CONTENT_LENGTH),
            'DATABASE_PATH': self.database_config.get_database_path(),
        }
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get development server configuration."""
        return {
            'host': self.config_override.get('HOST', self.defaults.HOST),
            'port': self.config_override.get('PORT', self.defaults.PORT),
            'debug': self.config_override.get('DEBUG', self.defaults.DEBUG),
        }
    
    def get_display_config(self) -> Dict[str, Any]:
        """Get display manager configuration."""
        return {
            'enabled': self.config_override.get('DISPLAY_MANAGER_ENABLED', self.defaults.DISPLAY_MANAGER_ENABLED),
            'fallback_titles': self.config_override.get('FALLBACK_JOB_TITLES', self.defaults.FALLBACK_JOB_TITLES),
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration."""
        return {
            'request_timeout': self.config_override.get('REQUEST_TIMEOUT', self.defaults.REQUEST_TIMEOUT),
            'max_content_length': self.config_override.get('MAX_CONTENT_LENGTH', self.defaults.MAX_CONTENT_LENGTH),
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            'level': self.config_override.get('LOG_LEVEL', self.defaults.LOG_LEVEL),
            'format': self.config_override.get('LOG_FORMAT', self.defaults.LOG_FORMAT),
        }
    
    def get_service_config(self) -> ServiceConfig:
        """Get service layer configuration."""
        return self.service_config
    
    def get_api_config(self) -> ApiConfig:
        """Get API configuration."""
        return self.api_config
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration."""
        return self.database_config
    
    def get_blueprint_config(self) -> BlueprintConfig:
        """Get blueprint configuration."""
        return self.blueprint_config
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate entire webapp configuration."""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate database path
        db_path = self.database_config.get_database_path()
        if not db_path.exists():
            validation_results['errors'].append(f"Database not found at: {db_path}")
            validation_results['valid'] = False
        
        # Validate service configurations
        service_validation = self.service_config.validate_configuration()
        if not service_validation['valid']:
            validation_results['errors'].extend(service_validation['errors'])
            validation_results['valid'] = False
        
        # Validate API configurations
        api_validation = self.api_config.validate_configuration()
        if not api_validation['valid']:
            validation_results['errors'].extend(api_validation['errors'])
            validation_results['valid'] = False
        
        return validation_results
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get comprehensive configuration summary for debugging."""
        return {
            'webapp': {
                'flask_config': self.get_flask_config(),
                'server_config': self.get_server_config(),
                'display_config': self.get_display_config(),
                'performance_config': self.get_performance_config(),
                'logging_config': self.get_logging_config(),
            },
            'services': self.service_config.get_configuration_summary(),
            'api': self.api_config.get_configuration_summary(),
            'database': self.database_config.get_configuration_summary(),
            'blueprints': self.blueprint_config.get_configuration_summary(),
        } 