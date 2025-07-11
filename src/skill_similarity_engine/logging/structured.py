"""
logging.structured

Structured/contextual logging support for the centralised logging framework.
This module will provide structured log records, field validation, and filtering utilities.
"""

import logging
from typing import Dict, Any, Optional

# Import architectural configuration manager
try:
    from ..config.architectural_config_manager import get_config_manager
except ImportError:
    # Fallback if architectural config unavailable
    get_config_manager = None


def _get_structured_config():
    """Get structured logging configuration from architectural config manager."""
    if get_config_manager is None:
        # Fallback configuration
        return {
            'valid_levels': ['debug', 'info', 'warning', 'error', 'critical'],
            'default_structured_level': 'info',
            'max_context_fields': 20,
            'max_field_length': 1000
        }
    
    try:
        config_manager = get_config_manager()
        return config_manager.get_nested_value('logging', 'structured', default={
            'valid_levels': ['debug', 'info', 'warning', 'error', 'critical'],
            'default_structured_level': 'info',
            'max_context_fields': 20,
            'max_field_length': 1000
        })
    except Exception:
        # Fallback if configuration loading fails
        return {
            'valid_levels': ['debug', 'info', 'warning', 'error', 'critical'],
            'default_structured_level': 'info',
            'max_context_fields': 20,
            'max_field_length': 1000
        }

def log_structured(logger: logging.Logger, level: Optional[str] = None, msg: Optional[str] = None, **context) -> None:
    """
    Log a structured message with additional context fields.
    Args:
        logger: Logger instance.
        level: Log level as string (e.g., 'info', 'warning', 'error', 'debug'). Uses configuration default if None.
        msg: Log message.
        **context: Additional context fields to include in the log.
    """
    # Load configuration
    config = _get_structured_config()
    
    # Validate and set level
    valid_levels = config.get('valid_levels', ['debug', 'info', 'warning', 'error', 'critical'])
    actual_level = level or config.get('default_structured_level', 'info')
    
    if actual_level not in valid_levels:
        # Fallback to default level if invalid level provided
        actual_level = config.get('default_structured_level', 'info')
    
    # Validate context fields (limit number and length)
    max_fields = config.get('max_context_fields', 20)
    max_length = config.get('max_field_length', 1000)
    
    # Limit number of context fields
    if len(context) > max_fields:
        # Keep only the first max_fields items
        context = dict(list(context.items())[:max_fields])
    
    # Limit field value lengths
    truncated_context = {}
    for key, value in context.items():
        if isinstance(value, str) and len(value) > max_length:
            truncated_context[key] = value[:max_length] + '...[truncated]'
        else:
            truncated_context[key] = value
    
    # Build log record
    record = {
        "message": msg or "",
        **truncated_context
    }
    
    # Log with appropriate level
    if actual_level == "info":
        logger.info(record)
    elif actual_level == "warning":
        logger.warning(record)
    elif actual_level == "error":
        logger.error(record)
    elif actual_level == "debug":
        logger.debug(record)
    elif actual_level == "critical":
        logger.critical(record)
    else:
        # For numeric levels or custom levels
        try:
            numeric_level = getattr(logging, actual_level.upper(), logging.INFO)
            logger.log(numeric_level, record)
        except (AttributeError, ValueError):
            # Fallback to INFO level
            logger.info(record)
