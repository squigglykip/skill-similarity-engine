"""
logging.config

Configuration management for the centralised logging framework.
This module will provide functions and classes to configure log levels, targets, rotation, and formatters.
"""

import logging
import os
from typing import Optional, Dict, Any
from .formatters import get_console_formatter, get_json_formatter
from .paths import get_run_log_dir

# Import architectural configuration manager
try:
    from ..config.architectural_config_manager import get_config_manager
except ImportError:
    # Fallback if architectural config unavailable
    get_config_manager = None


def _get_logging_core_config():
    """Get core logging configuration from architectural config manager."""
    if get_config_manager is None:
        # Fallback configuration
        return {
            'default_logger_name': 'skill_similarity_engine',
            'default_log_level': 'INFO',
            'environment_variable': 'LOG_LEVEL',
            'default_log_filename': 'engine.log',
            'create_dirs_if_missing': True
        }
    
    try:
        config_manager = get_config_manager()
        return config_manager.get_nested_value('logging', 'core', default={
            'default_logger_name': 'skill_similarity_engine',
            'default_log_level': 'INFO',
            'environment_variable': 'LOG_LEVEL',
            'default_log_filename': 'engine.log',
            'create_dirs_if_missing': True
        })
    except Exception:
        # Fallback if configuration loading fails
        return {
            'default_logger_name': 'skill_similarity_engine',
            'default_log_level': 'INFO',
            'environment_variable': 'LOG_LEVEL',
            'default_log_filename': 'engine.log',
            'create_dirs_if_missing': True
        }


def _get_logging_formatters_config():
    """Get formatter configuration from architectural config manager."""
    if get_config_manager is None:
        # Fallback configuration
        return {
            'default_formatter': 'console',
            'available_types': ['console', 'detailed', 'json']
        }
    
    try:
        config_manager = get_config_manager()
        return config_manager.get_nested_value('logging', 'formatters', default={
            'default_formatter': 'console',
            'available_types': ['console', 'detailed', 'json']
        })
    except Exception:
        # Fallback if configuration loading fails
        return {
            'default_formatter': 'console',
            'available_types': ['console', 'detailed', 'json']
        }

def setup_logging(
    level: Optional[str] = None,
    log_to_file: Optional[bool] = None,
    log_file_path: Optional[str] = None,
    formatter: Optional[str] = None,
    run_dir: Optional[str] = None
) -> logging.Logger:
    """
    Set up the centralised logging configuration.
    Args:
        level: Log level (e.g., 'DEBUG', 'INFO'). Uses configuration default if None.
        log_to_file: Whether to log to a file. Uses configuration default if None.
        log_file_path: Path to the log file. If None and log_to_file is True, defaults to configured filename in the run dir.
        formatter: Formatter type. Uses configuration default if None.
        run_dir: The run directory to use for log file output. If None, a new run dir is created.
    Returns:
        Configured logger instance.
    """
    # Load configuration
    core_config = _get_logging_core_config()
    formatters_config = _get_logging_formatters_config()
    
    # Get logger with configured name
    logger_name = core_config.get('default_logger_name', 'skill_similarity_engine')
    logger = logging.getLogger(logger_name)
    
    # Set log level with configuration fallback
    env_var = core_config.get('environment_variable', 'LOG_LEVEL')
    default_level = core_config.get('default_log_level', 'INFO')
    logger.setLevel(level or os.getenv(env_var, default_level))

    # Remove existing handlers
    logger.handlers = []

    # Console handler
    ch = logging.StreamHandler()
    
    # Use configured default formatter if not specified
    actual_formatter = formatter or formatters_config.get('default_formatter', 'console')
    if actual_formatter == "json":
        ch.setFormatter(get_json_formatter())
    else:
        ch.setFormatter(get_console_formatter())
    logger.addHandler(ch)

    # File handler (optional) - use configuration default if not specified
    handlers_config = {}
    try:
        config_manager = get_config_manager()
        if config_manager:
            handlers_config = config_manager.get_nested_value('logging', 'handlers', 'file', default={})
    except Exception:
        pass
    
    actual_log_to_file = log_to_file if log_to_file is not None else handlers_config.get('enabled_by_default', False)
    
    if actual_log_to_file:
        if log_file_path is None:
            # Use run_dir if provided, else create a new one
            if run_dir is None:
                paths = get_run_log_dir()
                run_dir = paths['run']
                logs_dir = paths['logs']
            else:
                logs_dir = os.path.join(run_dir, 'logs')
                create_dirs = core_config.get('create_dirs_if_missing', True)
                if create_dirs:
                    os.makedirs(logs_dir, exist_ok=True)
            
            # Use configured log filename
            log_filename = core_config.get('default_log_filename', 'engine.log')
            log_file_path = os.path.join(logs_dir, log_filename)
        
        # Create file handler with configured settings
        file_mode = handlers_config.get('mode', 'a')
        file_encoding = handlers_config.get('encoding', 'utf-8')
        fh = logging.FileHandler(log_file_path, mode=file_mode, encoding=file_encoding)
        
        if actual_formatter == "json":
            fh.setFormatter(get_json_formatter())
        else:
            fh.setFormatter(get_console_formatter())
        logger.addHandler(fh)

    return logger 
