"""
CLI Utilities for Skill Similarity Engine

This module provides interactive prompt utilities for command-line interfaces,
extracted and enhanced from the main.py cottage industry code.
"""

import sys
from pathlib import Path
from typing import Optional, Union, List, Any

from ..config.architectural_config_manager import get_config_manager


def prompt_bool(prompt: str, default: bool = False) -> bool:
    """
    Prompt user for a boolean (yes/no) response.
    
    Args:
        prompt: The question to ask the user
        default: Default value if user just presses Enter
        
    Returns:
        bool: True for yes, False for no
        
    Example:
        >>> enable_logging = prompt_bool("Enable logging?", default=True)
        Enable logging? [Y/n]: 
    """
    default_text = 'Y/n' if default else 'y/N'
    
    while True:
        response = input(f"{prompt} [{default_text}]: ").strip().lower()
        
        if not response:
            return default
            
        if response in ('y', 'yes', 'true', '1'):
            return True
        elif response in ('n', 'no', 'false', '0'):
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")


def prompt_int(prompt: str, default: Optional[int] = None, 
               min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
    """
    Prompt user for an integer value with validation.
    
    Args:
        prompt: The question to ask the user
        default: Default value if user just presses Enter
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)
        
    Returns:
        int: The validated integer value
        
    Raises:
        KeyboardInterrupt: If user cancels with Ctrl+C
        
    Example:
        >>> chunk_size = prompt_int("Chunk size", default=1000, min_value=100)
        Chunk size [default: 1000]: 
    """
    default_text = f"default: {default}" if default is not None else "no default"
    
    while True:
        try:
            response = input(f"{prompt} [{default_text}]: ").strip()
            
            if not response:
                if default is not None:
                    return default
                else:
                    print("No default value available. Please enter a number.")
                    continue
            
            value = int(response)
            
            # Validate range if specified
            if min_value is not None and value < min_value:
                print(f"Value must be at least {min_value}.")
                continue
                
            if max_value is not None and value > max_value:
                print(f"Value must be at most {max_value}.")
                continue
            
            return value
            
        except ValueError:
            print("Please enter a valid integer.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(1)


def prompt_float(prompt: str, default: Optional[float] = None,
                min_value: Optional[float] = None, max_value: Optional[float] = None) -> float:
    """
    Prompt user for a float value with validation.
    
    Args:
        prompt: The question to ask the user
        default: Default value if user just presses Enter
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)
        
    Returns:
        float: The validated float value
        
    Example:
        >>> threshold = prompt_float("Similarity threshold", default=0.5, min_value=0.0, max_value=1.0)
    """
    default_text = f"default: {default}" if default is not None else "no default"
    
    while True:
        try:
            response = input(f"{prompt} [{default_text}]: ").strip()
            
            if not response:
                if default is not None:
                    return default
                else:
                    print("No default value available. Please enter a number.")
                    continue
            
            value = float(response)
            
            # Validate range if specified
            if min_value is not None and value < min_value:
                print(f"Value must be at least {min_value}.")
                continue
                
            if max_value is not None and value > max_value:
                print(f"Value must be at most {max_value}.")
                continue
            
            return value
            
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(1)


def prompt_choice(prompt: str, choices: List[str], default: Optional[str] = None) -> str:
    """
    Prompt user to select from a list of choices.
    
    Args:
        prompt: The question to ask the user
        choices: List of valid choices
        default: Default choice if user just presses Enter
        
    Returns:
        str: The selected choice
        
    Example:
        >>> format_choice = prompt_choice("Output format", ["csv", "parquet", "both"], default="both")
    """
    choices_lower = [choice.lower() for choice in choices]
    choices_display = "/".join(choices)
    default_text = f"default: {default}" if default else "no default"
    
    while True:
        response = input(f"{prompt} [{choices_display}] [{default_text}]: ").strip().lower()
        
        if not response:
            if default is not None:
                return default
            else:
                print(f"No default value available. Please choose from: {choices_display}")
                continue
        
        if response in choices_lower:
            # Return the original case version
            return choices[choices_lower.index(response)]
        else:
            print(f"Please choose from: {choices_display}")


def prompt_file_path(prompt: str, default_path: Optional[str] = None, 
                     must_exist: bool = True, create_dirs: bool = False) -> Path:
    """
    Prompt user for a file path with validation and configuration integration.
    
    Args:
        prompt: The question to ask the user
        default_path: Default path if user just presses Enter
        must_exist: Whether the file must already exist
        create_dirs: Whether to create parent directories if they don't exist
        
    Returns:
        Path: The validated file path
        
    Example:
        >>> skills_file = prompt_file_path("Skills CSV file", "data/skills.csv", must_exist=True)
    """
    default_text = f"default: {default_path}" if default_path else "no default"
    
    while True:
        try:
            response = input(f"{prompt} [{default_text}]: ").strip()
            
            if not response:
                if default_path is not None:
                    file_path = Path(default_path)
                else:
                    print("No default path available. Please enter a file path.")
                    continue
            else:
                file_path = Path(response)
            
            # Check if file exists when required
            if must_exist:
                # Try the path as-is first
                if file_path.exists():
                    return file_path
                
                # Try with data/ prefix for relative paths
                data_path = Path("data") / file_path
                if data_path.exists():
                    return data_path
                
                print(f"File not found at either:")
                print(f"  • {file_path}")
                print(f"  • {data_path}")
                continue
            else:
                # For output files, optionally create directories
                if create_dirs and file_path.parent != Path("."):
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    print(f"Created directory: {file_path.parent}")
                
                return file_path
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(1)


def prompt_directory_path(prompt: str, default_path: Optional[str] = None,
                         must_exist: bool = True, create_if_missing: bool = False) -> Path:
    """
    Prompt user for a directory path with validation.
    
    Args:
        prompt: The question to ask the user
        default_path: Default path if user just presses Enter
        must_exist: Whether the directory must already exist
        create_if_missing: Whether to create the directory if it doesn't exist
        
    Returns:
        Path: The validated directory path
    """
    default_text = f"default: {default_path}" if default_path else "no default"
    
    while True:
        try:
            response = input(f"{prompt} [{default_text}]: ").strip()
            
            if not response:
                if default_path is not None:
                    dir_path = Path(default_path)
                else:
                    print("No default path available. Please enter a directory path.")
                    continue
            else:
                dir_path = Path(response)
            
            if must_exist and not dir_path.exists():
                if create_if_missing:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    print(f"Created directory: {dir_path}")
                    return dir_path
                else:
                    print(f"Directory not found: {dir_path}")
                    continue
            elif not must_exist and create_if_missing:
                dir_path.mkdir(parents=True, exist_ok=True)
                
            return dir_path
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(1)


def get_configured_file_path(config_key: str, prompt_text: Optional[str] = None, 
                           must_exist: bool = True) -> Path:
    """
    Get a file path from configuration with optional user override.
    
    Args:
        config_key: Configuration key to look up default path
        prompt_text: Optional prompt text (if None, uses config_key)
        must_exist: Whether the file must exist
        
    Returns:
        Path: The file path from config or user input
        
    Example:
        >>> skills_file = get_configured_file_path('skills_comprehensive', 
        ...                                       "Skills library file")
    """
    try:
        config_manager = get_config_manager()
        default_path = str(config_manager.get_file_path(config_key))
        
        if prompt_text is None:
            prompt_text = f"Path for {config_key.replace('_', ' ')}"
            
        return prompt_file_path(prompt_text, default_path, must_exist=must_exist)
        
    except Exception as e:
        print(f"⚠️  Could not load default path for {config_key}: {e}")
        
        if prompt_text is None:
            prompt_text = f"Path for {config_key.replace('_', ' ')}"
            
        return prompt_file_path(prompt_text, must_exist=must_exist)


def get_configured_directory_path(config_key: str, prompt_text: Optional[str] = None,
                                must_exist: bool = True) -> Path:
    """
    Get a directory path from configuration with optional user override.
    
    Args:
        config_key: Configuration key to look up default path
        prompt_text: Optional prompt text (if None, uses config_key)
        must_exist: Whether the directory must exist
        
    Returns:
        Path: The directory path from config or user input
    """
    try:
        config_manager = get_config_manager()
        default_path = str(config_manager.get_directory(config_key))
        
        if prompt_text is None:
            prompt_text = f"Directory for {config_key.replace('_', ' ')}"
            
        return prompt_directory_path(prompt_text, default_path, must_exist=must_exist)
        
    except Exception as e:
        print(f"⚠️  Could not load default directory for {config_key}: {e}")
        
        if prompt_text is None:
            prompt_text = f"Directory for {config_key.replace('_', ' ')}"
            
        return prompt_directory_path(prompt_text, must_exist=must_exist)


def print_banner(title: str, width: int = 60, char: str = "=") -> None:
    """
    Print a formatted banner for CLI sections.
    
    Args:
        title: The title to display
        width: Width of the banner
        char: Character to use for the banner
        
    Example:
        >>> print_banner("DATA LOADING & VALIDATION")
        ============================================================
        DATA LOADING & VALIDATION
        ============================================================
    """
    border = char * width
    print(f"\n{border}")
    print(title)
    print(border)


def print_success(message: str, details: Optional[List[str]] = None) -> None:
    """
    Print a success message with optional details.
    
    Args:
        message: Main success message
        details: Optional list of detail lines
    """
    print(f"\n{'='*60}")
    print(f"✅ {message}")
    print('='*60)
    
    if details:
        for detail in details:
            print(f"📁 {detail}")
        print('='*60)


def print_error(message: str, details: Optional[List[str]] = None) -> None:
    """
    Print an error message with optional details.
    
    Args:
        message: Main error message
        details: Optional list of detail lines
    """
    print(f"\n❌ ERROR: {message}")
    
    if details:
        for detail in details:
            print(f"   • {detail}")


def confirm_operation(operation: str, details: Optional[List[str]] = None) -> bool:
    """
    Ask user to confirm a potentially destructive operation.
    
    Args:
        operation: Description of the operation
        details: Optional list of details about what will happen
        
    Returns:
        bool: True if user confirms, False otherwise
    """
    print(f"\n⚠️  You are about to: {operation}")
    
    if details:
        print("\nThis will:")
        for detail in details:
            print(f"  • {detail}")
    
    return prompt_bool("\nDo you want to continue?", default=False) 