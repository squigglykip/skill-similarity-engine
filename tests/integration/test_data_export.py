"""
Integration tests for data export functionality.

This module tests the integration of data export components with each other 
and with other parts of the system, focusing on output generation and formatting.
"""

import sys
import os

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import unittest
import tempfile
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from skill_similarity_engine.models.skills import Skill, SkillTaxonomy
from skill_similarity_engine.models.jobs import Job, JobArchitecture, JobLevel
from skill_similarity_engine.visualization.reports import DataExporter, ReportConfig
from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator


class TestDataExport(unittest.TestCase):
    """Test case for data export functionality."""
    
    def setUp(self):
        """Set up test fixtures using sample data."""
        # Get the path to sample data
        self.sample_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sample')
        
        # Load skill taxonomy from sample data
        self.taxonomy = SkillTaxonomy.from_file(os.path.join(self.sample_dir, 'skills.csv'))
        
        # Load job architecture from sample data
        from skill_similarity_engine.models.jobs import JobArchitecture
        from skill_similarity_engine.data.loaders import JobArchitectureLoader
        job_loader = JobArchitectureLoader(self.taxonomy)
        self.job_arch = job_loader.load_from_csv(os.path.join(self.sample_dir, 'jobs.csv'))
        
        # Create a temporary directory for output files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create the exporter
        self.exporter = DataExporter(
            skill_taxonomy=self.taxonomy,
            job_architecture=self.job_arch,
            output_dir=self.temp_dir.name
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def test_job_similarity_export(self):
        """Test exporting job similarity matrix."""
        # Get a department from our sample data
        departments = set(job.department for job in self.job_arch.jobs.values())
        test_department = next(iter(departments))
        
        # Export the matrix
        output_path = os.path.join(self.temp_dir.name, "test_matrix.csv")
        df = self.exporter.export_job_similarity_matrix(
            department=test_department,
            output_path=output_path
        )
        
        # Verify the DataFrame is not empty
        self.assertGreater(len(df), 0)
        
        # Verify the file was created
        self.assertTrue(os.path.exists(output_path))
        
        # Read the CSV and verify its contents
        df = pd.read_csv(output_path)
        self.assertGreater(len(df), 0)
        self.assertIn('job1_id', df.columns)
        self.assertIn('job2_id', df.columns)
        self.assertIn('similarity', df.columns)
        
        # Verify all jobs in the matrix belong to the specified department
        for _, row in df.iterrows():
            job1 = self.job_arch.get_job(row['job1_id'])
            job2 = self.job_arch.get_job(row['job2_id'])
            self.assertEqual(job1.department, test_department)
            self.assertEqual(job2.department, test_department)
    
    def test_job_similarity_export_with_invalid_department(self):
        """Test exporting job similarity matrix with invalid department."""
        # Try to export with non-existent department
        with self.assertRaises(ValueError):
            self.exporter.export_job_similarity_matrix(
                department="NonExistentDepartment",
                output_path=os.path.join(self.temp_dir.name, "test_matrix_invalid.csv")
            )
    
    def test_job_similarity_export_with_report_config(self):
        """Test exporting job similarity matrix with report configuration."""
        # Get a department from our sample data
        departments = set(job.department for job in self.job_arch.jobs.values())
        test_department = next(iter(departments))
        
        # Create a report configuration
        config = ReportConfig(
            include_metadata=True
        )
        
        # Export the matrix with configuration
        output_path = os.path.join(self.temp_dir.name, "test_matrix_config.csv")
        df = self.exporter.export_job_similarity_matrix(
            department=test_department,
            output_path=output_path,
            config=config
        )
        
        # Verify the DataFrame is not empty
        self.assertGreater(len(df), 0)
        
        # Verify the file was created
        self.assertTrue(os.path.exists(output_path))
        
        # Read the CSV and verify its contents
        df = pd.read_csv(output_path)
        self.assertGreater(len(df), 0)
        self.assertIn('job1_id', df.columns)
        self.assertIn('job2_id', df.columns)
        self.assertIn('similarity', df.columns)
        self.assertIn('job1_title', df.columns)  # Metadata column
        self.assertIn('job2_title', df.columns)  # Metadata column
        self.assertIn('department', df.columns)  # Metadata column


if __name__ == "__main__":
    unittest.main() 