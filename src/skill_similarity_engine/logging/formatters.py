"""
logging.formatters

Defines log formatters for the centralised logging framework.
This module will provide detailed, console-friendly, and JSON formatters for log output.
"""

import logging
import json
from typing import Dict, Any, Optional

# Import architectural configuration manager
try:
    from ..config.architectural_config_manager import get_config_manager
except ImportError:
    # Fallback if architectural config unavailable
    get_config_manager = None


def _get_formatter_config():
    """Get formatter configuration from architectural config manager."""
    if get_config_manager is None:
        # Fallback configuration
        return {
            'console': {
                'format_string': '%(asctime)s - %(levelname)s - %(message)s',
                'date_format': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format_string': '%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s',
                'date_format': '%Y-%m-%d %H:%M:%S'
            },
            'json': {
                'include_fields': ['time', 'level', 'name', 'message', 'module', 'line'],
                'date_format': '%Y-%m-%d %H:%M:%S',
                'ensure_ascii': False,
                'indent': None
            }
        }
    
    try:
        config_manager = get_config_manager()
        return config_manager.get_nested_value('logging', 'formatters', default={
            'console': {
                'format_string': '%(asctime)s - %(levelname)s - %(message)s',
                'date_format': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format_string': '%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s',
                'date_format': '%Y-%m-%d %H:%M:%S'
            },
            'json': {
                'include_fields': ['time', 'level', 'name', 'message', 'module', 'line'],
                'date_format': '%Y-%m-%d %H:%M:%S',
                'ensure_ascii': False,
                'indent': None
            }
        })
    except Exception:
        # Fallback if configuration loading fails
        return {
            'console': {
                'format_string': '%(asctime)s - %(levelname)s - %(message)s',
                'date_format': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format_string': '%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s',
                'date_format': '%Y-%m-%d %H:%M:%S'
            },
            'json': {
                'include_fields': ['time', 'level', 'name', 'message', 'module', 'line'],
                'date_format': '%Y-%m-%d %H:%M:%S',
                'ensure_ascii': False,
                'indent': None
            }
        }

class ConsoleFormatter(logging.Formatter):
    def __init__(self, format_string: Optional[str] = None, date_format: Optional[str] = None):
        # Load configuration
        config = _get_formatter_config()
        console_config = config.get('console', {})
        
        fmt = format_string or console_config.get('format_string', '%(asctime)s - %(levelname)s - %(message)s')
        datefmt = date_format or console_config.get('date_format', '%Y-%m-%d %H:%M:%S')
        
        super().__init__(fmt, datefmt=datefmt)

class DetailedFormatter(logging.Formatter):
    def __init__(self, format_string: Optional[str] = None, date_format: Optional[str] = None):
        # Load configuration
        config = _get_formatter_config()
        detailed_config = config.get('detailed', {})
        
        fmt = format_string or detailed_config.get('format_string', '%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s')
        datefmt = date_format or detailed_config.get('date_format', '%Y-%m-%d %H:%M:%S')
        
        super().__init__(fmt, datefmt=datefmt)

class JSONFormatter(logging.Formatter):
    def __init__(self, include_fields: Optional[list] = None, date_format: Optional[str] = None, **json_kwargs):
        # Load configuration
        config = _get_formatter_config()
        json_config = config.get('json', {})
        
        self.include_fields = include_fields or json_config.get('include_fields', ['time', 'level', 'name', 'message', 'module', 'line'])
        self.json_kwargs = {
            'ensure_ascii': json_config.get('ensure_ascii', False),
            'indent': json_config.get('indent', None),
            **json_kwargs
        }
        
        datefmt = date_format or json_config.get('date_format', '%Y-%m-%d %H:%M:%S')
        super().__init__(datefmt=datefmt)
    
    def format(self, record):
        log_record = {}
        
        # Build log record based on configured fields
        if 'time' in self.include_fields:
            log_record['time'] = self.formatTime(record, self.datefmt)
        if 'level' in self.include_fields:
            log_record['level'] = record.levelname
        if 'name' in self.include_fields:
            log_record['name'] = record.name
        if 'message' in self.include_fields:
            log_record['message'] = record.getMessage()
        if 'module' in self.include_fields:
            log_record['module'] = record.module
        if 'line' in self.include_fields:
            log_record['line'] = record.lineno
            
        return json.dumps(log_record, **self.json_kwargs)

def get_console_formatter():
    return ConsoleFormatter()

def get_detailed_formatter():
    return DetailedFormatter()

def get_json_formatter():
    return JSONFormatter()
