"""
Data loading utilities for functional tests.

This module provides patches and helper functions for loading test data
in a way that's compatible with both unit tests and functional tests.
It integrates with the centralized test_data module to ensure consistent
data usage across all test types.
"""

import os
from pathlib import Path
import sys

# Add the parent test directory to the Python path for test_data access
parent_test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_test_dir not in sys.path:
    sys.path.insert(0, parent_test_dir)

# Import the centralized test data functions
from test_data import (
    ENGINE_JOBS_CSV, 
    ENGINE_SKILLS_CSV,
    ENGINE_SKILLS_JSON,
    ENGINE_EMPLOYEES_CSV,
    HRIS_JOBS_CSV,
    HRIS_SKILLS_CSV,
    HRIS_JOB_SKILLS_CSV,
    HRIS_EMPLOYEES_CSV,
    TEST_HRIS_CONFIG,
    load_skill_taxonomy,
    load_job_architecture,
    load_employee_database
)

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
    
    # If test_data is requested, use the centralized test_data directory
    if data_type == 'test_data':
        return Path(os.path.dirname(ENGINE_JOBS_CSV))
    
    # Use requested data type or fall back to sample
    data_dir = project_root / 'data' / data_type
    
    # Fall back to sample if the requested directory doesn't exist
    if not data_dir.exists():
        data_dir = project_root / 'data' / 'sample'
    
    return data_dir

def get_test_hris_config():
    """Return the path to the test HRIS configuration file."""
    return TEST_HRIS_CONFIG

def get_test_data_files():
    """
    Get paths to all test data files.
    
    Returns:
        dict: A dictionary with keys for all test data file paths
    """
    return {
        'engine_jobs': ENGINE_JOBS_CSV,
        'engine_skills': ENGINE_SKILLS_CSV,
        'engine_skills_json': ENGINE_SKILLS_JSON,
        'engine_employees': ENGINE_EMPLOYEES_CSV,
        'hris_jobs': HRIS_JOBS_CSV,
        'hris_skills': HRIS_SKILLS_CSV,
        'hris_job_skills': HRIS_JOB_SKILLS_CSV,
        'hris_employees': HRIS_EMPLOYEES_CSV,
        'hris_config': TEST_HRIS_CONFIG
    } 