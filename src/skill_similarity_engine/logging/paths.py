import os
from datetime import datetime
from typing import Dict, List, Optional

# Import architectural configuration manager
try:
    from ..config.architectural_config_manager import get_config_manager
except ImportError:
    # Fallback if architectural config unavailable
    get_config_manager = None


def _get_logging_config():
    """Get logging configuration from architectural config manager."""
    if get_config_manager is None:
        # Fallback configuration
        return {
            'directories': {
                'log_root': 'log',
                'relative_path_from_logging_module': '../../../log',
                'run_directory_format': 'run_{timestamp}',
                'timestamp_format': '%Y%m%d_%H%M%S',
                'run_subdirectories': ['logs', 'errors', 'checkpoints', 'progress', 'validation', 'metrics'],
                'create_run_subdirs': True,
                'make_dirs_exist_ok': True
            }
        }
    
    try:
        config_manager = get_config_manager()
        return config_manager.get_nested_value('logging', default={
            'directories': {
                'log_root': 'log',
                'relative_path_from_logging_module': '../../../log',
                'run_directory_format': 'run_{timestamp}',
                'timestamp_format': '%Y%m%d_%H%M%S',
                'run_subdirectories': ['logs', 'errors', 'checkpoints', 'progress', 'validation', 'metrics'],
                'create_run_subdirs': True,
                'make_dirs_exist_ok': True
            }
        })
    except Exception:
        # Fallback if configuration loading fails
        return {
            'directories': {
                'log_root': 'log',
                'relative_path_from_logging_module': '../../../log',
                'run_directory_format': 'run_{timestamp}',
                'timestamp_format': '%Y%m%d_%H%M%S',
                'run_subdirectories': ['logs', 'errors', 'checkpoints', 'progress', 'validation', 'metrics'],
                'create_run_subdirs': True,
                'make_dirs_exist_ok': True
            }
        }


def _get_log_root_directory():
    """Get the root log directory based on configuration."""
    config = _get_logging_config()
    dirs_config = config.get('directories', {})
    
    # Use relative path from logging module as configured
    relative_path = dirs_config.get('relative_path_from_logging_module', '../../../log')
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))
    
    # Create directory if configured to do so
    if dirs_config.get('make_dirs_exist_ok', True):
        os.makedirs(log_dir, exist_ok=True)
    
    return log_dir


def _get_run_subdirs():
    """Get the list of run subdirectories from configuration."""
    config = _get_logging_config()
    dirs_config = config.get('directories', {})
    return dirs_config.get('run_subdirectories', ['logs', 'errors', 'checkpoints', 'progress', 'validation', 'metrics'])


# Module-level variables using configuration
LOG_DIR = _get_log_root_directory()
RUN_SUBDIRS = _get_run_subdirs()

def get_run_log_dir() -> Dict[str, str]:
    """
    Create and return a new per-run log directory with a timestamp, including standard subdirectories.
    Returns a dict with the run directory and all subdirectory paths.
    Usage:
        paths = get_run_log_dir()
        run_log_dir = paths['run']
        logs_dir = paths['logs']
    """
    # Load configuration
    config = _get_logging_config()
    dirs_config = config.get('directories', {})
    
    # Generate run ID using configured timestamp format
    timestamp_format = dirs_config.get('timestamp_format', '%Y%m%d_%H%M%S')
    run_id = datetime.now().strftime(timestamp_format)
    
    # Generate run directory name using configured format
    run_format = dirs_config.get('run_directory_format', 'run_{timestamp}')
    run_dir_name = run_format.format(timestamp=run_id)
    
    # Create run directory
    run_log_dir = os.path.join(LOG_DIR, run_dir_name)
    make_dirs_exist_ok = dirs_config.get('make_dirs_exist_ok', True)
    os.makedirs(run_log_dir, exist_ok=make_dirs_exist_ok)
    
    # Create subdirectories if configured
    subdirs = {}
    if dirs_config.get('create_run_subdirs', True):
        run_subdirs = dirs_config.get('run_subdirectories', RUN_SUBDIRS)
        for sub in run_subdirs:
            sub_path = os.path.join(run_log_dir, sub)
            os.makedirs(sub_path, exist_ok=make_dirs_exist_ok)
            subdirs[sub] = sub_path
    
    subdirs['run'] = run_log_dir
    return subdirs
