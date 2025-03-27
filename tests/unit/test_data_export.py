import unittest
import pandas as pd
from unittest.mock import Mock, patch
import os
import tempfile
import json

from skill_similarity_engine.visualization.reports import DataExporter, ReportConfig
from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture, Job, JobLevel
from skill_similarity_engine.models.employees import EmployeeDatabase
from skill_similarity_engine.data.loaders import JobArchitectureLoader, EmployeeLoader
from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator

class TestDataExporter(unittest.TestCase):
    """Test the DataExporter class functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Load sample data from the existing data directory
        sample_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'sample')
        
        # Load real sample data
        self.skill_taxonomy = SkillTaxonomy.from_file(os.path.join(sample_dir, 'skills.csv'))
        
        # Load jobs from real sample data
        job_loader = JobArchitectureLoader(self.skill_taxonomy)
        self.job_architecture = job_loader.load_from_csv(os.path.join(sample_dir, 'jobs.csv'))
        
        # Create a temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize the exporter
        self.exporter = DataExporter(
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            output_dir=self.temp_dir
        )
        
        # Setup real similarity calculator
        vectorizer = TfidfVectorizer(self.skill_taxonomy)
        self.similarity_calculator = CosineSimilarityCalculator(
            vectorizer=vectorizer,
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary directory and its contents
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def test_export_job_similarity_matrix_basic(self):
        """Test basic job similarity matrix export."""
        # Mock the similarity calculator for consistent results
        self.exporter.similarity_calculator = Mock()
        self.exporter.similarity_calculator.calculate_job_similarity.return_value = 0.8
        
        # Export matrix for Analytics department
        df = self.exporter.export_job_similarity_matrix(
            department='Analytics',
            config=ReportConfig(department='Analytics')
        )
        
        # Verify DataFrame structure
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertIn('job1_id', df.columns)
        self.assertIn('job2_id', df.columns)
        self.assertIn('similarity', df.columns)
    
    def test_export_job_similarity_matrix_with_metadata(self):
        """Test job similarity matrix export with metadata."""
        # Mock the similarity calculator
        self.exporter.similarity_calculator = Mock()
        self.exporter.similarity_calculator.calculate_job_similarity.return_value = 0.8
        
        # Export matrix with metadata for Analytics department
        df = self.exporter.export_job_similarity_matrix(
            department='Analytics',
            config=ReportConfig(include_metadata=True)
        )
        
        # Verify metadata columns
        self.assertIn('job1_title', df.columns)
        self.assertIn('job2_title', df.columns)
        self.assertIn('department', df.columns)
        
        # Make sure expected columns contain values
        self.assertFalse(df['job1_title'].isnull().any())
        self.assertFalse(df['job2_title'].isnull().any())
        self.assertFalse(df['department'].isnull().any())
    
    def test_export_job_similarity_matrix_with_opportunity_flags(self):
        """Test job similarity matrix export with opportunity flags."""
        # Mock the similarity calculator
        self.exporter.similarity_calculator = Mock()
        self.exporter.similarity_calculator.calculate_job_similarity.return_value = 0.8
        
        # Export matrix with opportunity flags for Analytics department
        df = self.exporter.export_job_similarity_matrix(
            department='Analytics',
            config=ReportConfig(add_opportunity_flags=True)
        )
        
        # Verify opportunity flag columns
        self.assertIn('is_high_similarity_opportunity', df.columns)
        self.assertIn('is_internal_mobility_opportunity', df.columns)
        self.assertIn('is_cross_departmental_opportunity', df.columns)
        
        # Verify flag values
        self.assertTrue(df['is_high_similarity_opportunity'].any())
        self.assertTrue(df['is_internal_mobility_opportunity'].any())
    
    def test_export_job_similarity_matrix_empty_department(self):
        """Test job similarity matrix export with empty department."""
        # Export matrix for non-existent department
        with self.assertRaises(ValueError) as cm:
            self.exporter.export_job_similarity_matrix(
                department='NonExistent',
                config=ReportConfig()
            )
        
        # Verify error message
        self.assertEqual(str(cm.exception), "No jobs found for department: NonExistent")
    
    def test_export_job_similarity_matrix_with_threshold(self):
        """Test job similarity matrix export with threshold filtering."""
        # Mock the similarity calculator with different values
        self.exporter.similarity_calculator = Mock()
        
        # Different similarity values based on job pairs
        def side_effect(job1_id, job2_id):
            if job1_id == 'J001' and job2_id == 'J002':
                return 0.8
            elif job1_id == 'J001' and job2_id == 'J003':
                return 0.3
            elif job1_id == 'J002' and job2_id == 'J003':
                return 0.4
            else:
                return 0.5

        self.exporter.similarity_calculator.calculate_job_similarity.side_effect = side_effect
        
        # Export matrix with threshold for Analytics department
        df = self.exporter.export_job_similarity_matrix(
            department='Analytics',
            config=ReportConfig(threshold=0.5)
        )
        
        # Verify threshold filtering
        for index, row in df.iterrows():
            self.assertGreaterEqual(row['similarity'], 0.5)
    
    def test_export_job_similarity_matrix_file_output(self):
        """Test job similarity matrix export to file."""
        # Mock the similarity calculator
        self.exporter.similarity_calculator = Mock()
        self.exporter.similarity_calculator.calculate_job_similarity.return_value = 0.8
        
        # Define output path
        output_path = os.path.join(self.temp_dir, 'test_matrix.csv')
        
        # Export matrix to file for Analytics department
        df = self.exporter.export_job_similarity_matrix(
            department='Analytics',
            config=ReportConfig(),
            output_path=output_path
        )
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_path))
        
        # Verify file contents
        loaded_df = pd.read_csv(output_path)
        self.assertEqual(len(loaded_df), len(df))
        self.assertGreaterEqual(loaded_df['similarity'].iloc[0], 0)
        self.assertLessEqual(loaded_df['similarity'].iloc[0], 1)

if __name__ == '__main__':
    unittest.main() 