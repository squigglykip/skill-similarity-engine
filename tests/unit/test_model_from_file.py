#!/usr/bin/env python3
"""
Unit tests for the from_file methods in model classes.

These tests verify that the SkillTaxonomy, JobArchitecture, and EmployeeDatabase
classes have properly functioning from_file methods.
"""

import sys
import os
import pandas as pd

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import unittest
import tempfile
from pathlib import Path

from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture
from skill_similarity_engine.models.employees import EmployeeDatabase


class TestModelFromFile(unittest.TestCase):
    """Test from_file class methods for model classes."""
    
    def setUp(self):
        """Set up test environment with sample data files."""
        # Get the path to sample data
        self.sample_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sample')
        
        # Create a temporary directory for any test files we need to create
        self.temp_dir = tempfile.TemporaryDirectory()
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
    
    def test_skill_taxonomy_has_from_file(self):
        """Test that SkillTaxonomy has the from_file class method."""
        self.assertTrue(hasattr(SkillTaxonomy, 'from_file'))
        self.assertTrue(callable(getattr(SkillTaxonomy, 'from_file')))
    
    def test_job_architecture_has_from_file(self):
        """Test that JobArchitecture has the from_file class method."""
        self.assertTrue(hasattr(JobArchitecture, 'from_file'))
        self.assertTrue(callable(getattr(JobArchitecture, 'from_file')))
    
    def test_employee_database_has_from_file(self):
        """Test that EmployeeDatabase has the from_file class method."""
        self.assertTrue(hasattr(EmployeeDatabase, 'from_file'))
        self.assertTrue(callable(getattr(EmployeeDatabase, 'from_file')))
    
    def test_skill_taxonomy_from_csv(self):
        """Test loading a SkillTaxonomy from a CSV file."""
        try:
            taxonomy = SkillTaxonomy.from_file(os.path.join(self.sample_dir, 'skills.csv'))
            self.assertIsInstance(taxonomy, SkillTaxonomy)
            
            # Check that we loaded some skills
            self.assertGreater(len(taxonomy.skills), 0)
            
            # Check the structure of loaded skills
            for skill_id, skill in taxonomy.skills.items():
                self.assertIsInstance(skill_id, str)
                self.assertIsInstance(skill.name, str)
                self.assertIsInstance(skill.skill_id, str)
                self.assertEqual(skill.skill_id, skill_id)
        except Exception as e:
            self.fail(f"SkillTaxonomy.from_file raised {type(e).__name__} unexpectedly: {e}")
    
    def test_job_architecture_from_csv(self):
        """Test loading a JobArchitecture from a CSV file."""
        try:
            # We need to first load the skill taxonomy for validation
            taxonomy = SkillTaxonomy.from_file(os.path.join(self.sample_dir, 'skills.csv'))
            
            # Then pass it to the job architecture loader
            from skill_similarity_engine.data.loaders import JobArchitectureLoader
            loader = JobArchitectureLoader(taxonomy)
            job_arch = loader.load_from_csv(os.path.join(self.sample_dir, 'jobs.csv'))
            
            self.assertIsInstance(job_arch, JobArchitecture)
            self.assertGreater(len(job_arch.jobs), 0)
            
            # Check the structure of loaded jobs
            for job_id, job in job_arch.jobs.items():
                self.assertIsInstance(job_id, str)
                self.assertIsInstance(job.title, str)
                self.assertIsInstance(job.department, str)
                self.assertIsInstance(job.skills, dict)
        except Exception as e:
            self.fail(f"JobArchitecture.from_file raised {type(e).__name__} unexpectedly: {e}")
    
    def test_employee_database_from_csv(self):
        """Test loading an EmployeeDatabase from a CSV file."""
        try:
            # We need to first load the skill taxonomy and job architecture
            taxonomy = SkillTaxonomy.from_file(os.path.join(self.sample_dir, 'skills.csv'))
            
            # Then pass it to the job architecture loader
            from skill_similarity_engine.data.loaders import JobArchitectureLoader, EmployeeLoader
            job_loader = JobArchitectureLoader(taxonomy)
            job_arch = job_loader.load_from_csv(os.path.join(self.sample_dir, 'jobs.csv'))
            
            # Now load employees
            employee_loader = EmployeeLoader(taxonomy, job_arch)
            employee_db = employee_loader.load_from_csv(os.path.join(self.sample_dir, 'employees.csv'))
            
            self.assertIsInstance(employee_db, EmployeeDatabase)
            self.assertGreater(len(employee_db.employees), 0)
            
            # Check the structure of loaded employees
            for emp_id, employee in employee_db.employees.items():
                self.assertIsInstance(emp_id, str)
                self.assertIsInstance(employee.name, str)
                self.assertIsInstance(employee.current_job, str)
                self.assertIsInstance(employee.skills, dict)
        except Exception as e:
            self.fail(f"EmployeeDatabase.from_file raised {type(e).__name__} unexpectedly: {e}")


if __name__ == "__main__":
    unittest.main() 