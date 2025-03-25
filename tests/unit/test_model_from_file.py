#!/usr/bin/env python3
"""
Unit tests for the from_file methods in model classes.

These tests verify that the SkillTaxonomy, JobArchitecture, and EmployeeDatabase
classes have properly functioning from_file methods.
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path

# Add the src directory to the path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture
from skill_similarity_engine.models.employees import EmployeeDatabase


class TestModelFromFile(unittest.TestCase):
    """Test from_file class methods for model classes."""
    
    def setUp(self):
        """Set up test environment with sample data files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a sample skill taxonomy CSV
        self.skills_csv = Path(self.temp_dir.name) / "skill_taxonomy.csv"
        with open(self.skills_csv, "w") as f:
            f.write("skill_id,name,category,difficulty\n")
            f.write("S001,Python Programming,Technical,3\n")
            f.write("S002,Data Analysis,Technical,4\n")
        
        # Create a sample job architecture CSV
        self.jobs_csv = Path(self.temp_dir.name) / "job_architecture.csv"
        with open(self.jobs_csv, "w") as f:
            f.write("job_id,title,department,level,skills\n")
            f.write("J001,Data Scientist,Data Science,Senior,S001:4;S002:5\n")
        
        # Create a sample employee database CSV
        self.employees_csv = Path(self.temp_dir.name) / "employee_database.csv"
        with open(self.employees_csv, "w") as f:
            f.write("employee_id,name,current_job,skills\n")
            f.write("E001,Alice Smith,J001,S001:4;S002:3\n")
    
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
    
    def test_skill_taxonomy_from_file(self):
        """Test loading a SkillTaxonomy from a CSV file."""
        try:
            taxonomy = SkillTaxonomy.from_file(str(self.skills_csv))
            self.assertIsInstance(taxonomy, SkillTaxonomy)
            self.assertEqual(len(taxonomy.skills), 2)
            self.assertIn('S001', taxonomy.skills)
            self.assertIn('S002', taxonomy.skills)
        except Exception as e:
            self.fail(f"SkillTaxonomy.from_file raised {type(e).__name__} unexpectedly: {e}")
    
    def test_job_architecture_from_file(self):
        """Test loading a JobArchitecture from a CSV file."""
        try:
            # We need to first load the skill taxonomy for validation
            taxonomy = SkillTaxonomy.from_file(str(self.skills_csv))
            
            # Then pass it to the job architecture loader
            from skill_similarity_engine.data.loaders import JobArchitectureLoader
            loader = JobArchitectureLoader(taxonomy)
            job_arch = loader.load_from_csv(str(self.jobs_csv))
            
            self.assertIsInstance(job_arch, JobArchitecture)
            self.assertEqual(len(job_arch.jobs), 1)  # Only 1 unique job
            self.assertIn('J001', job_arch.jobs)
            self.assertEqual(job_arch.jobs['J001'].title, 'Data Scientist')
            
            # Check if skills were parsed correctly
            self.assertEqual(len(job_arch.jobs['J001'].skills), 2)
            self.assertEqual(job_arch.jobs['J001'].skills['S001'], 4)
            self.assertEqual(job_arch.jobs['J001'].skills['S002'], 5)
        except Exception as e:
            self.fail(f"JobArchitecture.from_file raised {type(e).__name__} unexpectedly: {e}")
    
    def test_employee_database_from_file(self):
        """Test loading an EmployeeDatabase from a CSV file."""
        try:
            # We need to first load the skill taxonomy and job architecture
            taxonomy = SkillTaxonomy.from_file(str(self.skills_csv))
            
            # Then pass it to the job architecture loader
            from skill_similarity_engine.data.loaders import JobArchitectureLoader, EmployeeLoader
            job_loader = JobArchitectureLoader(taxonomy)
            job_arch = job_loader.load_from_csv(str(self.jobs_csv))
            
            # Now load employees
            employee_loader = EmployeeLoader(taxonomy, job_arch)
            employee_db = employee_loader.load_from_csv(str(self.employees_csv))
            
            self.assertIsInstance(employee_db, EmployeeDatabase)
            self.assertEqual(len(employee_db.employees), 1)  # Only 1 unique employee
            self.assertIn('E001', employee_db.employees)
            self.assertEqual(employee_db.employees['E001'].name, 'Alice Smith')
            
            # Check if skills were parsed correctly
            self.assertEqual(len(employee_db.employees['E001'].skills), 2)
            self.assertEqual(employee_db.employees['E001'].skills['S001'], 4)
            self.assertEqual(employee_db.employees['E001'].skills['S002'], 3)
        except Exception as e:
            self.fail(f"EmployeeDatabase.from_file raised {type(e).__name__} unexpectedly: {e}")


if __name__ == "__main__":
    unittest.main() 