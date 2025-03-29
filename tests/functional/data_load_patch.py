"""
Data loading utilities for functional tests.

This module provides patches and helper functions for loading test data
in a way that's compatible with both unit tests and functional tests.
"""

import os
from pathlib import Path

def get_test_data_path(data_type='sample'):
    """
    Get the path to test data directory.
    
    Args:
        data_type: Type of data to load ('sample', 'synthetic', or 'real')
        
    Returns:
        Path: Path to the data directory
    """
    # Find the project root by looking for the src directory
    current_dir = Path(__file__).parent
    project_root = current_dir
    
    # Walk up until we find the src directory
    while not (project_root / 'src').exists() and project_root != project_root.parent:
        project_root = project_root.parent
    
    # Check if we're using real data from environment variable
    use_real_data = os.environ.get("USE_REAL_DATA", "False").lower() == "true"
    
    if use_real_data and data_type == 'real':
        # Look for real data in environment variable or default location
        real_data_dir = os.environ.get("REAL_DATA_DIR", project_root / 'data' / 'real')
        if Path(real_data_dir).exists():
            return Path(real_data_dir)
    
    # Use requested data type or fall back to sample
    data_dir = project_root / 'data' / data_type
    
    # Fall back to sample if the requested directory doesn't exist
    if not data_dir.exists():
        data_dir = project_root / 'data' / 'sample'
    
    return data_dir 