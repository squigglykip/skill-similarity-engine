"""
Unit tests for the reports module.

This module tests the DataExporter and ReportConfig classes in isolation,
focusing on their core functionality and edge cases.
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
from unittest.mock import Mock, patch

from skill_similarity_engine.visualization.reports import DataExporter, ReportConfig
from skill_similarity_engine.models.skills import Skill, SkillTaxonomy
from skill_similarity_engine.models.jobs import Job, JobArchitecture, JobLevel
from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator
from skill_similarity_engine.data.loaders import JobArchitectureLoader, EmployeeLoader


class TestReportConfig(unittest.TestCase):
    """Test cases for ReportConfig class."""
    
    def test_report_config_creation(self):
        """Test creating a ReportConfig instance."""
        config = ReportConfig()
        self.assertFalse(config.include_metadata)
        self.assertFalse(config.add_opportunity_flags)
        
        config = ReportConfig(include_metadata=True)
        self.assertTrue(config.include_metadata)
        self.assertFalse(config.add_opportunity_flags)
        
        config = ReportConfig(add_opportunity_flags=True)
        self.assertFalse(config.include_metadata)
        self.assertTrue(config.add_opportunity_flags)
        
        config = ReportConfig(include_metadata=True, add_opportunity_flags=True)
        self.assertTrue(config.include_metadata)
        self.assertTrue(config.add_opportunity_flags)


class TestDataExporter(unittest.TestCase):
    """Test cases for DataExporter class."""
    
    def setUp(self):
        """Set up test environment with real sample data."""
        # Load sample data from the existing data directory
        sample_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sample')
        
        # Load real sample data
        self.skill_taxonomy = SkillTaxonomy.from_file(os.path.join(sample_dir, 'skills.csv'))
        
        # Load jobs from real sample data
        job_loader = JobArchitectureLoader(self.skill_taxonomy)
        self.job_architecture = job_loader.load_from_csv(os.path.join(sample_dir, 'jobs.csv'))
        
        # Create a temporary directory for test outputs
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Initialize the exporter with real data
        self.exporter = DataExporter(
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            output_dir=self.temp_dir.name
        )
        
        # Setup real similarity calculator
        vectorizer = TfidfVectorizer(self.skill_taxonomy)
        self.real_calculator = CosineSimilarityCalculator(
            vectorizer=vectorizer,
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture
        )
        
        # Set mock calculator for consistent test results
        self.mock_calculator = Mock()
        self.mock_calculator.calculate_job_similarity.return_value = 0.9
        self.exporter.similarity_calculator = self.mock_calculator
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
    
    def test_exporter_initialization(self):
        """Test that the exporter is initialized correctly."""
        self.assertEqual(self.exporter.skill_taxonomy, self.skill_taxonomy)
        self.assertEqual(self.exporter.job_architecture, self.job_architecture)
        self.assertEqual(self.exporter.output_dir, self.temp_dir.name)
    
    def test_export_job_similarity_matrix_basic(self):
        """Test basic job similarity matrix export."""
        # Export the matrix for Analytics department
        output_path = os.path.join(self.temp_dir.name, "test_matrix.csv")
        df = self.exporter.export_job_similarity_matrix(
            department="Analytics",
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
    
    def test_export_job_similarity_matrix_with_metadata(self):
        """Test job similarity matrix export with metadata."""
        # Create a report configuration with metadata
        config = ReportConfig(include_metadata=True)
        
        # Export the matrix for Analytics department
        output_path = os.path.join(self.temp_dir.name, "test_matrix_metadata.csv")
        df = self.exporter.export_job_similarity_matrix(
            department="Analytics",
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
        
        # Make sure expected columns contain values
        self.assertFalse(df['job1_title'].isnull().any())
        self.assertFalse(df['job2_title'].isnull().any())
        self.assertFalse(df['department'].isnull().any())
    
    def test_export_job_similarity_matrix_with_opportunity_flags(self):
        """Test job similarity matrix export with opportunity flags."""
        # Create a report configuration with opportunity flags
        config = ReportConfig(add_opportunity_flags=True)
        
        # Export the matrix for Analytics department
        output_path = os.path.join(self.temp_dir.name, "test_matrix_flags.csv")
        df = self.exporter.export_job_similarity_matrix(
            department="Analytics",
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
        self.assertIn('is_high_similarity_opportunity', df.columns)
        self.assertIn('is_internal_mobility_opportunity', df.columns)
        self.assertIn('is_cross_departmental_opportunity', df.columns)
        
        # Verify at least some flag values are set
        self.assertTrue(df['is_high_similarity_opportunity'].any())
    
    def test_export_job_similarity_matrix_invalid_department(self):
        """Test job similarity matrix export with invalid department."""
        # Try to export with non-existent department
        with self.assertRaises(ValueError):
            self.exporter.export_job_similarity_matrix(
                department="NonExistentDepartment",
                output_path=os.path.join(self.temp_dir.name, "test_matrix_invalid.csv")
            )
    
    def test_export_job_similarity_matrix_empty_department(self):
        """Test job similarity matrix export with empty department."""
        # Temporarily clear the job architecture to simulate empty department
        orig_jobs = self.job_architecture.jobs
        self.job_architecture.jobs = {}
        
        try:
            # Try to export with empty department
            with self.assertRaises(ValueError):
                self.exporter.export_job_similarity_matrix(
                    department="Analytics",
                    output_path=os.path.join(self.temp_dir.name, "test_matrix_empty.csv")
                )
        finally:
            # Restore the original jobs
            self.job_architecture.jobs = orig_jobs
    
    def test_export_job_similarity_matrix_no_output_path(self):
        """Test job similarity matrix export without output path."""
        # Export without output path
        df = self.exporter.export_job_similarity_matrix(department="Analytics")
        
        # Verify the DataFrame is not empty
        self.assertGreater(len(df), 0)
        
        # Verify the DataFrame structure
        self.assertIn('job1_id', df.columns)
        self.assertIn('job2_id', df.columns)
        self.assertIn('similarity', df.columns)


if __name__ == "__main__":
    unittest.main() 
