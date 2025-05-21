#!/usr/bin/env python3
"""
Basic functional tests for the Skill Similarity Engine CLI.

This script tests the basic functionality of the CLI commands using centralized test data
to ensure that the commands can be executed without errors.
"""

import sys
import os
import subprocess
import tempfile
import shutil
import pytest
from pathlib import Path

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Define project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Import centralized test data
from tests.functional.data_load_patch import get_test_data_files
from tests.test_data import (
    ENGINE_JOBS_CSV,
    ENGINE_SKILLS_CSV,
    ENGINE_EMPLOYEES_CSV
)

@pytest.fixture
def sample_data():
    """Get centralized test data files for testing."""
    # Get data from the centralized test data module
    return {
        "skills_csv": ENGINE_SKILLS_CSV,
        "jobs_csv": ENGINE_JOBS_CSV, 
        "job_skills_csv": None,  # No separate job skills file in centralized data
        "employees_csv": ENGINE_EMPLOYEES_CSV
    }

def run_command(command):
    """Run a command and return the result."""
    print(f"Running: {command}")
    result = subprocess.run(
        command, 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True
    )
    
    print(f"Exit code: {result.returncode}")
    if result.stdout:
        print(f"Standard output:\n{result.stdout[:500]}...")
    if result.stderr:
        print(f"Standard error:\n{result.stderr}")
    
    return result

def test_version_command():
    """Test the version command."""
    print("\n--- Testing version command ---")
    command = f"python {PROJECT_ROOT}/scripts/skillsim.py version"
    result = run_command(command)
    assert result.returncode == 0, "Version command failed"

def test_generate_config_command():
    """Test the generate-config command."""
    print("\n--- Testing generate-config command ---")
    output_file = Path(tempfile.mkdtemp()) / "test_config.yaml"
    command = f"python {PROJECT_ROOT}/scripts/skillsim.py generate-config {output_file}"
    result = run_command(command)
    assert result.returncode == 0, "Generate config command failed"
    assert output_file.exists(), "Config file was not created"

def test_job_similarity_command(sample_data):
    """Test the job-similarity command."""
    print("\n--- Testing job-similarity command ---")
    
    command = (
        f"python {PROJECT_ROOT}/scripts/skillsim.py job-similarity "
        f"{sample_data['skills_csv']} {sample_data['jobs_csv']}"
    )
    result = run_command(command)
    assert result.returncode == 0, "Job similarity command failed"

def test_employee_job_similarity_command(sample_data):
    """Test the employee-job-similarity command."""
    print("\n--- Testing employee-job-similarity command ---")
    
    command = (
        f"python {PROJECT_ROOT}/scripts/skillsim.py employee-job-similarity "
        f"{sample_data['skills_csv']} {sample_data['jobs_csv']} {sample_data['employees_csv']}"
    )
    result = run_command(command)
    assert result.returncode == 0, "Employee-job similarity command failed"

def test_skill_gap_analysis_command(sample_data):
    """Test the skill-gap-analysis command."""
    print("\n--- Testing skill-gap-analysis command ---")
    
    command = (
        f"python {PROJECT_ROOT}/scripts/skillsim.py skill-gap-analysis "
        f"{sample_data['skills_csv']} {sample_data['jobs_csv']} {sample_data['employees_csv']} "
        f"--employee-id E001 --target-job-id J001"
    )
    result = run_command(command)
    assert result.returncode == 0, "Skill gap analysis command failed"

def test_department_filtering(sample_data):
    """Test filtering by department."""
    print("\n--- Testing department filtering ---")
    
    command = (
        f"python {PROJECT_ROOT}/scripts/skillsim.py job-similarity "
        f"{sample_data['skills_csv']} {sample_data['jobs_csv']} "
        f"--department Data"
    )
    result = run_command(command)
    assert result.returncode == 0, "Department filtering failed"

def cleanup():
    """Clean up test files."""
    print(f"\nCleaning up temporary files in {SAMPLE_DATA_DIR}")
    shutil.rmtree(SAMPLE_DATA_DIR)

def main():
    """Run all tests."""
    try:
        print(f"Creating sample data in {SAMPLE_DATA_DIR}")
        sample_data = sample_data()
        
        # Run the tests
        test_version_command()
        test_generate_config_command()
        test_job_similarity_command(sample_data)
        test_employee_job_similarity_command(sample_data)
        test_skill_gap_analysis_command(sample_data)
        test_department_filtering(sample_data)
        
        print("\nAll tests passed successfully!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1
    finally:
        cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 