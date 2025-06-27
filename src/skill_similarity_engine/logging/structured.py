"""
logging.structured

Structured/contextual logging support for the centralised logging framework.
This module will provide structured log records, field validation, and filtering utilities.
"""

import logging

def log_structured(logger, level, msg, **context):
    """
    Log a structured message with additional context fields.
    Args:
        logger: Logger instance.
        level: Log level as string (e.g., 'info', 'warning', 'error', 'debug').
        msg: Log message.
        **context: Additional context fields to include in the log.
    """
    record = {
        "message": msg,
        **context
    }
    if level == "info":
        logger.info(record)
    elif level == "warning":
        logger.warning(record)
    elif level == "error":
        logger.error(record)
    elif level == "debug":
        logger.debug(record)
    else:
        logger.log(level, record)
