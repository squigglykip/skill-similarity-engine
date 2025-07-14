"""
DatabaseConfig - Database Configuration
=======================================

Configuration class for database operations following PTH OOP/Config-driven 
architectural philosophy. Eliminates hardcoded database paths and settings.

Uses ModelVersionManager to dynamically find the latest quarterly database version.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import sqlite3
import logging

logger = logging.getLogger(__name__)

@dataclass
class DatabaseDefaults:
    """Default values for database configuration."""
    # Database path defaults
    DATABASE_NAME: str = 'workforce_intelligence.sqlite'
    MODELS_BASE_DIR: str = 'models'  # Base directory for model versions
    
    # Connection defaults
    CONNECTION_TIMEOUT: int = 30
    QUERY_TIMEOUT: int = 10
    MAX_CONNECTIONS: int = 10
    
    # Performance defaults
    ENABLE_WAL_MODE: bool = True
    ENABLE_FOREIGN_KEYS: bool = True
    CACHE_SIZE: int = 2000  # SQLite cache pages
    
    # Backup defaults
    BACKUP_ENABLED: bool = False
    BACKUP_RETENTION_DAYS: int = 7


class DatabaseConfig:
    """Database configuration with dynamic quarterly version resolution."""
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        self.defaults = DatabaseDefaults()
        self.config_override = config_override or {}
    
    def get_database_path(self) -> Path:
        """
        Get database path using ModelVersionManager for dynamic quarterly version resolution.
        
        Returns:
            Path to the business_context.sqlite database in the latest quarterly version
        """
        try:
            # Import here to avoid circular imports
            from ...models.versioning import ModelVersionManager
            
            # Use ModelVersionManager to find the latest quarterly version
            version_manager = ModelVersionManager()
            current_version_path = version_manager.get_current_version_path()
            
            if current_version_path and current_version_path.exists():
                db_path = current_version_path / self.defaults.DATABASE_NAME
                
                if db_path.exists():
                    logger.info(f"Found database in latest quarterly version: {db_path}")
                    return db_path
                else:
                    logger.warning(f"Database file not found in latest version directory: {db_path}")
            
            # Fallback: search all quarterly directories for the most recent database
            fallback_path = self._find_most_recent_database()
            if fallback_path:
                logger.info(f"Found database in quarterly fallback search: {fallback_path}")
                return fallback_path
            
            # Emergency fallback: search any models directory for any database
            emergency_path = self._find_any_available_database()
            if emergency_path:
                logger.warning(f"Using emergency database found at: {emergency_path}")
                return emergency_path
            
            # Final fallback: return a path that will trigger proper error handling
            missing_path = Path(self.defaults.MODELS_BASE_DIR) / "business_context.sqlite"
            logger.error(f"No database found anywhere - returning non-existent path: {missing_path}")
            return missing_path
            
        except Exception as e:
            # If anything fails, try to find any available database
            logger.error(f"Error in primary database path resolution: {e}")
            try:
                emergency_path = self._find_any_available_database()
                if emergency_path:
                    logger.warning(f"Using emergency fallback due to error: {emergency_path}")
                    return emergency_path
            except Exception as emergency_error:
                logger.error(f"Emergency fallback also failed: {emergency_error}")
            
            # Absolute last resort
            missing_path = Path(self.defaults.MODELS_BASE_DIR) / "business_context.sqlite"
            logger.error(f"All database resolution methods failed - returning: {missing_path}")
            return missing_path
    
    def _find_most_recent_database(self) -> Optional[Path]:
        """
        Find the most recent quarterly database following YYYY-QN pattern.
        
        Returns:
            Path to the most recent quarterly database, or None if not found
        """
        models_dir = Path(self.defaults.MODELS_BASE_DIR)
        if not models_dir.exists():
            return None
        
        quarterly_dirs = []
        for item in models_dir.iterdir():
            if item.is_dir() and self._is_quarterly_version(item.name):
                db_file = item / self.defaults.DATABASE_NAME
                if db_file.exists():
                    quarterly_dirs.append((item, db_file))
        
        if quarterly_dirs:
            # Sort by directory name (YYYY-QN format sorts naturally)
            _, latest_db = max(quarterly_dirs, key=lambda x: x[0].name)
            return latest_db
        
        return None
    
    def _find_any_available_database(self) -> Optional[Path]:
        """
        Emergency method to find ANY business_context.sqlite file in the models directory tree.
        
        Returns:
            Path to any available database file, or None if not found
        """
        models_dir = Path(self.defaults.MODELS_BASE_DIR)
        if not models_dir.exists():
            return None
        
        # Search recursively for any business_context.sqlite file
        for db_file in models_dir.rglob(self.defaults.DATABASE_NAME):
            if db_file.is_file():
                logger.info(f"Found database file during emergency search: {db_file}")
                return db_file
        
        return None
    
    def _is_quarterly_version(self, version_name: str) -> bool:
        """
        Check if a version name follows the quarterly pattern (YYYY-QN).
        
        Args:
            version_name: Name to check
            
        Returns:
            True if it's a quarterly version
        """
        try:
            parts = version_name.split('-')
            if len(parts) != 2:
                return False
            
            year = int(parts[0])
            quarter_part = parts[1]
            
            if not quarter_part.startswith('Q'):
                return False
                
            quarter = int(quarter_part[1:])
            return 1900 <= year <= 2100 and quarter in [1, 2, 3, 4]
            
        except (ValueError, IndexError):
            return False

    def get_connection_config(self) -> Dict[str, Any]:
        """Get database connection configuration."""
        return {
            'timeout': self.config_override.get('connection_timeout', self.defaults.CONNECTION_TIMEOUT),
            'max_connections': self.config_override.get('max_connections', self.defaults.MAX_CONNECTIONS),
            'check_same_thread': False  # Allow multi-threading
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get database performance configuration."""
        return {
            'cache_size': self.config_override.get('cache_size', self.defaults.CACHE_SIZE),
            'enable_wal_mode': self.config_override.get('enable_wal_mode', self.defaults.ENABLE_WAL_MODE),
            'enable_foreign_keys': self.config_override.get('enable_foreign_keys', self.defaults.ENABLE_FOREIGN_KEYS)
        }
    
    def get_backup_config(self) -> Dict[str, Any]:
        """Get database backup configuration."""
        return {
            'backup_enabled': self.config_override.get('backup_enabled', self.defaults.BACKUP_ENABLED),
            'backup_retention_days': self.config_override.get('backup_retention_days', self.defaults.BACKUP_RETENTION_DAYS)
        }
    
    def get_sqlite_pragma_config(self) -> Dict[str, Any]:
        """Get SQLite PRAGMA configuration."""
        config = {}
        
        perf_config = self.get_performance_config()
        
        if perf_config['enable_wal_mode']:
            config['journal_mode'] = 'WAL'
        
        if perf_config['enable_foreign_keys']:
            config['foreign_keys'] = 'ON'
            
        config['cache_size'] = perf_config['cache_size']
        config['temp_store'] = 'MEMORY'
        config['synchronous'] = 'NORMAL'
        
        return config
    
    def get_connection_string(self) -> str:
        """
        Get SQLite connection string.
        
        Returns:
            SQLite connection string with parameters
        """
        db_path = self.get_database_path()
        conn_config = self.get_connection_config()
        
        # Basic SQLite connection string
        connection_string = f"sqlite:///{db_path}"
        
        # Add timeout parameter
        connection_string += f"?timeout={conn_config['timeout']}"
        
        return connection_string
    
    def validate_database_access(self) -> Dict[str, Any]:
        """
        Validate database accessibility and structure.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'database_exists': False,
            'database_accessible': False,
            'database_path': None,
            'database_size_mb': 0,
            'table_count': 0,
            'error_message': None,
            'resolution_method': None
        }
        
        try:
            db_path = self.get_database_path()
            results['database_path'] = str(db_path)
            
            # Determine how the path was resolved
            if 'business_context.sqlite' == db_path.name and db_path.parent.name == self.defaults.MODELS_BASE_DIR:
                results['resolution_method'] = 'emergency_fallback_failed'
            elif self._is_quarterly_version(db_path.parent.name):
                results['resolution_method'] = 'quarterly_version'
            else:
                results['resolution_method'] = 'recursive_search'
            
            # Check if file exists
            if not db_path.exists():
                results['error_message'] = f"Database file does not exist: {db_path}"
                return results
            
            results['database_exists'] = True
            results['database_size_mb'] = round(db_path.stat().st_size / (1024 * 1024), 2)
            
            # Try to connect and get table count
            with sqlite3.connect(str(db_path), timeout=10) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                results['table_count'] = cursor.fetchone()[0]
                results['database_accessible'] = True
                
        except Exception as e:
            results['error_message'] = str(e)
            logger.error(f"Database validation failed: {e}")
        
        return results
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of the database configuration."""
        db_path = self.get_database_path()
        validation = self.validate_database_access()
        
        return {
            'database_path': str(db_path),
            'database_exists': validation['database_exists'],
            'database_accessible': validation['database_accessible'],
            'database_size_mb': validation['database_size_mb'],
            'table_count': validation['table_count'],
            'resolution_method': validation['resolution_method'],
            'connection_config': self.get_connection_config(),
            'performance_config': self.get_performance_config(),
            'backup_config': self.get_backup_config(),
            'uses_dynamic_versioning': True,
            'architecture_compliant': True,  # No hardcoded paths
            'error_message': validation.get('error_message')
        } 