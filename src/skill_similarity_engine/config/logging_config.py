"""
Logging configuration for the skill similarity engine.

This module provides a central configuration for logging throughout the application.
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from .settings import get_config

def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_dir: Optional[str] = None,
    console_output: Optional[bool] = None,
    file_output: Optional[bool] = None,
) -> logging.Logger:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Name of the log file
        log_dir: Directory to store log files
        console_output: Whether to output logs to console
        file_output: Whether to output logs to file
        
    Returns:
        Configured logger instance
    """
    # Get logging configuration from config
    config = get_config().logging
    
    # Use provided values or defaults from config
    log_level = log_level or config.level
    log_file = log_file or config.log_file
    log_dir = log_dir or config.log_dir
    console_output = console_output if console_output is not None else config.console_output
    file_output = file_output if file_output is not None else config.file_output
    
    # Create logger
    logger = logging.getLogger("skill_similarity_engine")
    
    # Set the logging level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    
    console_formatter = logging.Formatter(
        "%(levelname)s - %(message)s"
    )
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if requested
    if file_output:
        # Determine log directory and file
        log_directory = Path(log_dir)
        
        # Create directory if it doesn't exist
        log_directory.mkdir(parents=True, exist_ok=True)
        
        # Full path to log file
        log_path = log_directory / log_file
        
        # Create file handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=config.max_file_size_mb * 1024 * 1024,  # Convert to bytes
            backupCount=config.backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    # Don't propagate to root logger
    logger.propagate = False
    
    logger.info(f"Logging configured with level {log_level}")
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name, creating it if it doesn't exist.
    
    Args:
        name: Name of the logger (typically __name__ in the calling module)
        
    Returns:
        Logger instance
    """
    root_logger = logging.getLogger("skill_similarity_engine")
    
    # If the root logger has no handlers, set up logging with defaults
    if not root_logger.handlers:
        setup_logging()
    
    # Return the requested logger
    if name.startswith("skill_similarity_engine"):
        return logging.getLogger(name)
    else:
        return logging.getLogger(f"skill_similarity_engine.{name}") 