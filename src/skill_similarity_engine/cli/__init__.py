"""
CLI Module for Skill Similarity Engine

This module provides command-line interface utilities and commands.
"""

# Import CLI utilities for easy access
from .utilities import (
    prompt_bool,
    prompt_int,
    prompt_float,
    prompt_choice,
    prompt_file_path,
    prompt_directory_path,
    get_configured_file_path,
    get_configured_directory_path,
    print_banner,
    print_success,
    print_error,
    confirm_operation,
)

# Import main CLI entry point
from .main import cli, main

__all__ = [
    # CLI utilities
    'prompt_bool',
    'prompt_int', 
    'prompt_float',
    'prompt_choice',
    'prompt_file_path',
    'prompt_directory_path',
    'get_configured_file_path',
    'get_configured_directory_path',
    'print_banner',
    'print_success',
    'print_error',
    'confirm_operation',
    
    # Main CLI
    'cli',
    'main',
] 
