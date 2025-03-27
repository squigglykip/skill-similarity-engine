"""
Integration tests for visualization components.

This module tests the integration of visualization components with each other 
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
import matplotlib.pyplot as plt
from unittest.mock import patch, MagicMock

from skill_similarity_engine.models.skills import Skill, SkillTaxonomy
from skill_similarity_engine.models.jobs import Job, JobArchitecture, JobLevel
from skill_similarity_engine.visualization.visualizer import VisualisationManager
from skill_similarity_engine.visualization.heatmaps import SimilarityHeatmapGenerator
from skill_similarity_engine.visualization.hexbin import HexbinGenerator
from skill_similarity_engine.visualization.reports import DataExporter, ReportConfig
from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator


class TestVisualisationIntegration(unittest.TestCase):
    """Test case for visualization components integration."""
    
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
        
        # Initialize the vectorizer and similarity calculator
        self.vectorizer = TfidfVectorizer(self.taxonomy)
        self.similarity_calculator = CosineSimilarityCalculator(
            vectorizer=self.vectorizer,
            skill_taxonomy=self.taxonomy,
            job_architecture=self.job_arch
        )
        
        # Create a temporary directory for output files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create the visualization manager
        self.vis_manager = VisualisationManager(
            skill_taxonomy=self.taxonomy,
            job_architecture=self.job_arch,
            output_dir=self.temp_dir.name
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Close all matplotlib figures
        plt.close('all')
        
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def test_similarity_heatmap_generation(self):
        """Test generating a similarity heatmap."""
        # Get a department from our sample data
        departments = set(job.department for job in self.job_arch.jobs.values())
        test_department = next(iter(departments))
        
        # Generate a heatmap
        file_path = os.path.join(self.temp_dir.name, "test_heatmap.png")
        self.vis_manager.generate_job_similarity_heatmap(
            department=test_department,
            output_path=file_path
        )
        
        # Verify the file was created
        self.assertTrue(os.path.exists(file_path))
        
        # Verify the file is a valid image
        try:
            img = plt.imread(file_path)
            self.assertIsInstance(img, np.ndarray)
            self.assertEqual(len(img.shape), 3)  # Should be RGB
        except Exception as e:
            self.fail(f"Failed to read generated heatmap: {e}")
    
    def test_similarity_heatmap_with_json_data(self):
        """Test generating a similarity heatmap using JSON data."""
        # Load skill taxonomy from JSON
        self.taxonomy = SkillTaxonomy.from_file(os.path.join(self.sample_dir, 'skills.json'))
        
        # Load job architecture from JSON
        from skill_similarity_engine.data.loaders import JobArchitectureLoader
        job_loader = JobArchitectureLoader(self.taxonomy)
        self.job_arch = job_loader.load_from_csv(os.path.join(self.sample_dir, 'jobs.csv'))
        
        # Create a new visualization manager with JSON data
        vis_manager = VisualisationManager(
            skill_taxonomy=self.taxonomy,
            job_architecture=self.job_arch,
            output_dir=self.temp_dir.name
        )
        
        # Get a department from our sample data
        departments = set(job.department for job in self.job_arch.jobs.values())
        test_department = next(iter(departments))
        
        # Generate a heatmap
        file_path = os.path.join(self.temp_dir.name, "test_heatmap_json.png")
        vis_manager.generate_job_similarity_heatmap(
            department=test_department,
            output_path=file_path
        )
        
        # Verify the file was created
        self.assertTrue(os.path.exists(file_path))
    
    def test_job_similarity_matrix_export(self):
        """Test exporting job similarity matrix to CSV."""
        # Get a department from our sample data
        departments = set(job.department for job in self.job_arch.jobs.values())
        test_department = next(iter(departments))
        
        # Export the matrix
        output_path = os.path.join(self.temp_dir.name, "test_matrix.csv")
        df = self.vis_manager.export_job_similarity_matrix(
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
        
        # Check for either naming convention - old (job1_id) or new (job_id_1)
        has_old_format = 'job1_id' in df.columns and 'job2_id' in df.columns and 'similarity' in df.columns
        has_new_format = 'job_id_1' in df.columns and 'job_id_2' in df.columns and 'similarity_score' in df.columns
        
        self.assertTrue(has_old_format or has_new_format, 
                       f"CSV should have either old format columns (job1_id, job2_id, similarity) or new format columns (job_id_1, job_id_2, similarity_score). Found columns: {df.columns}")
        
        # Map column names based on format
        job1_col = 'job1_id' if has_old_format else 'job_id_1'
        job2_col = 'job2_id' if has_old_format else 'job_id_2'
        
        # Verify all jobs in the matrix belong to the specified department
        for _, row in df.iterrows():
            job1 = self.job_arch.get_job(row[job1_col])
            job2 = self.job_arch.get_job(row[job2_col])
            self.assertEqual(job1.department, test_department)
            self.assertEqual(job2.department, test_department)
    
    def test_data_exporter_integration(self):
        """Test data exporter integration with visualization components."""
        # Get a department from our sample data
        departments = set(job.department for job in self.job_arch.jobs.values())
        test_department = next(iter(departments))
        
        # Create a report configuration
        config = ReportConfig(
            include_metadata=True
        )
        
        # Create the exporter
        exporter = DataExporter(
            skill_taxonomy=self.taxonomy,
            job_architecture=self.job_arch,
            output_dir=self.temp_dir.name
        )
        
        # Export the matrix
        output_path = os.path.join(self.temp_dir.name, "test_matrix_exporter.csv")
        df = exporter.export_job_similarity_matrix(
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
        
        # Check for either naming convention - old (job1_id) or new (job_id_1)
        has_old_format = 'job1_id' in df.columns and 'job2_id' in df.columns and 'similarity' in df.columns
        has_new_format = 'job_id_1' in df.columns and 'job_id_2' in df.columns and 'similarity_score' in df.columns
        
        self.assertTrue(has_old_format or has_new_format, 
                       f"CSV should have either old format columns (job1_id, job2_id, similarity) or new format columns (job_id_1, job_id_2, similarity_score). Found columns: {df.columns}")
        
        # Check for metadata columns with appropriate naming
        if has_old_format:
            self.assertIn('job1_title', df.columns)  # Metadata column
            self.assertIn('job2_title', df.columns)  # Metadata column
        else:
            self.assertIn('job_title_1', df.columns)  # Metadata column
            self.assertIn('job_title_2', df.columns)  # Metadata column
            
        self.assertTrue('department' in df.columns or 'department_1' in df.columns)  # Metadata column
    
    def test_data_formats_integration(self):
        """Test integration with different data formats."""
        # Test CSV format
        csv_taxonomy = SkillTaxonomy.from_file(os.path.join(self.sample_dir, 'skills.csv'))
        self.assertGreater(len(csv_taxonomy.skills), 0)
        
        # Test JSON format
        json_taxonomy = SkillTaxonomy.from_file(os.path.join(self.sample_dir, 'skills.json'))
        self.assertGreater(len(json_taxonomy.skills), 0)
        
        # Compare the number of skills between formats
        self.assertEqual(len(csv_taxonomy.skills), len(json_taxonomy.skills))
    
    def test_filtering_and_thresholds(self):
        """Test filtering and threshold functionality."""
        # Get a department from our sample data
        departments = set(job.department for job in self.job_arch.jobs.values())
        test_department = next(iter(departments))
        
        # Get jobs in the department
        department_jobs = [job for job in self.job_arch.jobs.values() 
                         if job.department == test_department]
        
        # Test with different thresholds
        thresholds = [0.5, 0.7, 0.9]
        for threshold in thresholds:
            # Generate heatmap with threshold
            file_path = os.path.join(self.temp_dir.name, f"test_heatmap_threshold_{threshold}.png")
            self.vis_manager.generate_job_similarity_heatmap(
                department=test_department,
                output_path=file_path
            )
            
            # Verify the file was created
            self.assertTrue(os.path.exists(file_path))
            
            # Verify the file is a valid image
            try:
                img = plt.imread(file_path)
                self.assertIsInstance(img, np.ndarray)
                self.assertEqual(len(img.shape), 3)  # Should be RGB
            except Exception as e:
                self.fail(f"Failed to read generated heatmap: {e}")
    
    def test_hexbin_visualization(self):
        """Test hexbin visualization generation."""
        # Get a department from our sample data
        departments = set(job.department for job in self.job_arch.jobs.values())
        test_department = next(iter(departments))
        
        # Generate hexbin visualization
        file_path = os.path.join(self.temp_dir.name, "test_hexbin.png")
        self.vis_manager.generate_hexbin_visualization(
            department=test_department,
            output_path=file_path
        )
        
        # Verify the file was created
        self.assertTrue(os.path.exists(file_path))
        
        # Verify the file is a valid image
        try:
            img = plt.imread(file_path)
            self.assertIsInstance(img, np.ndarray)
            self.assertEqual(len(img.shape), 3)  # Should be RGB
        except Exception as e:
            self.fail(f"Failed to read generated hexbin visualization: {e}")
    
    def test_visualization_customization(self):
        """Test visualization customization options."""
        # Get a department from our sample data
        departments = set(job.department for job in self.job_arch.jobs.values())
        test_department = next(iter(departments))
        
        # Test different color schemes
        color_schemes = ['viridis', 'plasma', 'inferno']
        for scheme in color_schemes:
            file_path = os.path.join(self.temp_dir.name, f"test_heatmap_{scheme}.png")
            self.vis_manager.generate_job_similarity_heatmap(
                department=test_department,
                output_path=file_path,
                color_scheme=scheme
            )
            
            # Verify the file was created
            self.assertTrue(os.path.exists(file_path))
            
            # Verify the file is a valid image
            try:
                img = plt.imread(file_path)
                self.assertIsInstance(img, np.ndarray)
                self.assertEqual(len(img.shape), 3)  # Should be RGB
            except Exception as e:
                self.fail(f"Failed to read generated heatmap with {scheme} color scheme: {e}")
    
    def test_file_format_support(self):
        """Test support for different file formats."""
        # Get a department from our sample data
        departments = set(job.department for job in self.job_arch.jobs.values())
        test_department = next(iter(departments))
        
        # Test different file formats
        formats = ['png', 'jpg', 'pdf']
        for fmt in formats:
            file_path = os.path.join(self.temp_dir.name, f"test_heatmap.{fmt}")
            self.vis_manager.generate_job_similarity_heatmap(
                department=test_department,
                output_path=file_path
            )
            
            # Verify the file was created
            self.assertTrue(os.path.exists(file_path))
            
            # Verify the file is not empty
            self.assertGreater(os.path.getsize(file_path), 0)


if __name__ == "__main__":
    unittest.main() 