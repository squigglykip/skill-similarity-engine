"""
Functional tests for skill similarity engine.

These tests verify end-to-end functionality, focusing on the complete workflow
from data ingestion to final output.
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path
import yaml

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import from the test data module
from tests.test_data import (
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
from tests.functional.data_load_patch import get_test_data_files


class BaseFunctionalTest(unittest.TestCase):
    """Base class for functional tests that provides common setup and teardown."""
    
    def setUp(self):
        """Set up test environment with test data."""
        # Create a temporary directory for test outputs
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Get paths to all test data files
        test_files = get_test_data_files()
        self.hris_skills_csv = test_files['hris_skills']
        self.hris_jobs_csv = test_files['hris_jobs']
        self.hris_job_skills_csv = test_files['hris_job_skills']
        self.hris_employees_csv = test_files['hris_employees']
        self.engine_jobs_csv = test_files['engine_jobs']
        self.engine_skills_csv = test_files['engine_skills']
        self.engine_skills_json = test_files['engine_skills_json']
        self.engine_employees_csv = test_files['engine_employees']
        
        # Create a temporary HRIS config file based on the test config
        self.temp_hris_config_path = self.output_dir / "temp_hris_config.yaml"
        
        # Load the original config
        with open(TEST_HRIS_CONFIG, 'r') as f:
            self.hris_config = yaml.safe_load(f)
        
        # Update file paths to point to test data and our temp output directory
        self.hris_config['hris_data']['jobs_file'] = str(self.hris_jobs_csv).replace('\\', '/')
        self.hris_config['hris_data']['skills_file'] = str(self.hris_skills_csv).replace('\\', '/')
        self.hris_config['hris_data']['job_skills_file'] = str(self.hris_job_skills_csv).replace('\\', '/')
        self.hris_config['output_data']['jobs_file'] = str(self.output_dir / "jobs.csv").replace('\\', '/')
        self.hris_config['output_data']['skills_file'] = str(self.output_dir / "skills.csv").replace('\\', '/')
        
        # Save the modified config to our temp directory
        with open(self.temp_hris_config_path, 'w') as f:
            yaml.safe_dump(self.hris_config, f)
            
        # Set up file paths for transformed data
        self.output_jobs_path = self.output_dir / "jobs.csv"
        self.output_skills_path = self.output_dir / "skills.csv"
        
        # Load the skill taxonomy and job architecture from the test data
        self.skill_taxonomy = load_skill_taxonomy()
        self.job_architecture = load_job_architecture()
        self.employee_database = load_employee_database()
        
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
        
    def create_reports_directory(self):
        """Create a reports directory in the temporary output directory."""
        reports_dir = self.output_dir / "reports"
        reports_dir.mkdir(exist_ok=True)
        return reports_dir 
