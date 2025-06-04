"""
logging.config

Configuration management for the centralised logging framework.
This module will provide functions and classes to configure log levels, targets, rotation, and formatters.
"""

import logging
import os
from .formatters import get_console_formatter, get_json_formatter
from .paths import get_run_log_dir

def setup_logging(
    level=None,
    log_to_file=False,
    log_file_path=None,
    formatter="console",
    run_dir=None
):
    """
    Set up the centralised logging configuration.
    Args:
        level: Log level (e.g., 'DEBUG', 'INFO').
        log_to_file: Whether to log to a file.
        log_file_path: Path to the log file. If None and log_to_file is True, defaults to logs/engine.log in the run dir.
        formatter: 'console' or 'json'.
        run_dir: The run directory to use for log file output. If None, a new run dir is created.
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("skill_similarity_engine")
    logger.setLevel(level or os.getenv("LOG_LEVEL", "INFO"))

    # Remove existing handlers
    logger.handlers = []

    # Console handler
    ch = logging.StreamHandler()
    if formatter == "json":
        ch.setFormatter(get_json_formatter())
    else:
        ch.setFormatter(get_console_formatter())
    logger.addHandler(ch)

    # File handler (optional)
    if log_to_file:
        if log_file_path is None:
            # Use run_dir if provided, else create a new one
            if run_dir is None:
                paths = get_run_log_dir()
                run_dir = paths['run']
                logs_dir = paths['logs']
            else:
                logs_dir = os.path.join(run_dir, 'logs')
                os.makedirs(logs_dir, exist_ok=True)
            log_file_path = os.path.join(logs_dir, 'engine.log')
        fh = logging.FileHandler(log_file_path)
        if formatter == "json":
            fh.setFormatter(get_json_formatter())
        else:
            fh.setFormatter(get_console_formatter())
        logger.addHandler(fh)

    return logger 