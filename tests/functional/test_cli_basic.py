#!/usr/bin/env python3
"""
Basic functional tests for the Skill Similarity Engine CLI.

This script tests the basic functionality of the CLI commands using small sample data
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

# Create a small sample data directory
SAMPLE_DATA_DIR = Path(tempfile.mkdtemp())

@pytest.fixture
def sample_data():
    """Create sample data files for testing."""
    # Create sample skill taxonomy CSV
    skills_csv = SAMPLE_DATA_DIR / "skill_taxonomy.csv"
    with open(skills_csv, "w") as f:
        f.write("skill_id,skill_name,category,difficulty\n")
        f.write("S001,Python Programming,Technical,3\n")
        f.write("S002,Data Analysis,Technical,4\n")
        f.write("S003,Project Management,Soft,2\n")
        f.write("S004,Communication,Soft,1\n")
        f.write("S005,Machine Learning,Technical,5\n")
    
    # Create sample job architecture CSV
    jobs_csv = SAMPLE_DATA_DIR / "job_architecture.csv"
    with open(jobs_csv, "w") as f:
        f.write("job_id,job_title,department,level,skill_id,required_proficiency\n")
        f.write("J001,Data Scientist,Data Science,4,S001,4\n")
        f.write("J001,Data Scientist,Data Science,4,S002,5\n")
        f.write("J001,Data Scientist,Data Science,4,S005,3\n")
        f.write("J002,Software Engineer,Engineering,3,S001,5\n")
        f.write("J002,Software Engineer,Engineering,3,S003,2\n")
        f.write("J002,Software Engineer,Engineering,3,S004,3\n")
        f.write("J003,Project Manager,Project Management,3,S003,5\n")
        f.write("J003,Project Manager,Project Management,3,S004,4\n")
    
    # Create sample employee database CSV
    employees_csv = SAMPLE_DATA_DIR / "employee_database.csv"
    with open(employees_csv, "w") as f:
        f.write("employee_id,name,department,current_job_id,skill_id,proficiency\n")
        f.write("E001,Alice Smith,Data Science,J001,S001,4\n")
        f.write("E001,Alice Smith,Data Science,J001,S002,3\n")
        f.write("E001,Alice Smith,Data Science,J001,S005,2\n")
        f.write("E002,Bob Jones,Engineering,J002,S001,5\n")
        f.write("E002,Bob Jones,Engineering,J002,S003,1\n")
        f.write("E002,Bob Jones,Engineering,J002,S004,2\n")
        f.write("E003,Charlie Brown,Project Management,J003,S003,4\n")
        f.write("E003,Charlie Brown,Project Management,J003,S004,5\n")
        f.write("E003,Charlie Brown,Project Management,J003,S001,1\n")
    
    return {
        "skills_csv": skills_csv,
        "jobs_csv": jobs_csv,
        "employees_csv": employees_csv
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
    output_file = SAMPLE_DATA_DIR / "test_config.yaml"
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
        f"--employee-id E001 --target-job-id J002"
    )
    result = run_command(command)
    assert result.returncode == 0, "Skill gap analysis command failed"

def test_department_filtering(sample_data):
    """Test filtering by department."""
    print("\n--- Testing department filtering ---")
    
    command = (
        f"python {PROJECT_ROOT}/scripts/skillsim.py job-similarity "
        f"{sample_data['skills_csv']} {sample_data['jobs_csv']} "
        f"--department 'Engineering'"
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