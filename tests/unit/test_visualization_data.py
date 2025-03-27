import unittest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
import os
import json

from skill_similarity_engine.visualization.visualizer import VisualisationManager, ReportConfig
from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture, Job, JobLevel
from skill_similarity_engine.models.employees import EmployeeDatabase
from skill_similarity_engine.data.loaders import JobArchitectureLoader, EmployeeLoader

class TestVisualisationDataProcessing(unittest.TestCase):
    """Test data processing for visualisation components."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Load sample data from the existing data directory
        sample_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'sample')
        
        # Load skills from real sample data
        self.skill_taxonomy = SkillTaxonomy.from_file(os.path.join(sample_dir, 'skills.csv'))
        
        # Load jobs from real sample data
        job_loader = JobArchitectureLoader(self.skill_taxonomy)
        self.job_architecture = job_loader.load_from_csv(os.path.join(sample_dir, 'jobs.csv'))
        
        # Load employees from real sample data
        employee_loader = EmployeeLoader(self.skill_taxonomy, self.job_architecture)
        self.employee_database = employee_loader.load_from_csv(os.path.join(sample_dir, 'employees.csv'))
        
        # Initialize visualisation manager
        self.vis_manager = VisualisationManager(
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
        
        # Create sample similarity matrix using real job IDs
        self.sample_matrix = pd.DataFrame([
            {'job1_id': 'J001', 'job2_id': 'J002', 'similarity': 0.8},
            {'job1_id': 'J001', 'job2_id': 'J003', 'similarity': 0.6},
            {'job2_id': 'J001', 'job1_id': 'J002', 'similarity': 0.8},
            {'job2_id': 'J001', 'job1_id': 'J003', 'similarity': 0.6},
            {'job1_id': 'J002', 'job2_id': 'J003', 'similarity': 0.4},
            {'job2_id': 'J002', 'job1_id': 'J003', 'similarity': 0.4}
        ])
    
    def test_job_similarity_heatmap_data(self):
        """Test data processing for job similarity heatmap."""
        # Mock the data exporter
        self.vis_manager._data_exporter = Mock()
        self.vis_manager._data_exporter.export_job_similarity_matrix.return_value = self.sample_matrix
        
        # Generate heatmap data
        df = self.vis_manager._data_exporter.export_job_similarity_matrix(
            department='Analytics',
            config=ReportConfig(format="csv")
        )
        
        # Verify data structure
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertIn('job1_id', df.columns)
        self.assertIn('job2_id', df.columns)
        self.assertIn('similarity', df.columns)
        
        # Verify data content
        self.assertEqual(len(df), 6)  # 6 pairs of jobs
        self.assertEqual(df.iloc[0]['similarity'], 0.8)
    
    def test_hexbin_visualization_data(self):
        """Test data processing for hexbin visualization."""
        # Mock the data exporter
        self.vis_manager._data_exporter = Mock()
        self.vis_manager._data_exporter.export_job_similarity_matrix.return_value = self.sample_matrix
        
        # Generate hexbin data
        df = self.vis_manager._data_exporter.export_job_similarity_matrix(
            department='Analytics',
            config=ReportConfig(format="csv")
        )
        
        # Verify data structure
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertIn('job1_id', df.columns)
        self.assertIn('job2_id', df.columns)
        self.assertIn('similarity', df.columns)
        
        # Verify data content
        self.assertEqual(len(df), 6)  # 6 pairs of jobs
        self.assertEqual(df.iloc[0]['similarity'], 0.8)
    
    def test_gap_analysis_heatmap_data(self):
        """Test data processing for gap analysis heatmap."""
        # Mock the gap heatmap generator
        self.vis_manager._gap_heatmap_generator = Mock()
        self.vis_manager._gap_heatmap_generator.generate_heatmap.return_value = "test_output.png"
        
        # Generate gap analysis data
        output_path = self.vis_manager.generate_gap_analysis_heatmap(
            department='Analytics',
            save_to_file=False
        )
        
        # Verify data processing
        self.vis_manager._gap_heatmap_generator.generate_heatmap.assert_called_once_with(
            department='Analytics',
            save_to_file=False,
            output_path=None,
            color_scheme='viridis',
            figsize=(10, 8),
            dpi=300
        )

if __name__ == '__main__':
    unittest.main() 