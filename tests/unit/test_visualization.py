import unittest
import os
import json
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
import pytest

from skill_similarity_engine.visualization.visualizer import (
    VisualisationManager,
    SimilarityHeatmapGenerator,
    HexbinGenerator,
    GapAnalysisHeatmapGenerator,
    ReportConfig
)
from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture, Job, JobLevel
from skill_similarity_engine.models.employees import EmployeeDatabase
from skill_similarity_engine.data.loaders import JobArchitectureLoader, EmployeeLoader

class TestVisualizationComponents(unittest.TestCase):
    """Test visualization components and data preprocessing."""
    
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
        
        # Initialize visualization components
        self.vis_manager = VisualisationManager(
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
        
        # Create sample similarity matrix using real job IDs from the sample data
        analytics_jobs = [job_id for job_id, job in self.job_architecture.jobs.items() 
                         if job.department == 'Analytics']
        self.sample_matrix = pd.DataFrame([
            {'job1_id': job1, 'job2_id': job2, 'similarity': 0.8}
            for job1 in analytics_jobs
            for job2 in analytics_jobs
            if job1 < job2  # Avoid duplicates and self-similarities
        ])
    
    def test_job_similarity_heatmap_generation(self):
        """Test generation of job similarity heatmap."""
        try:
            import tkinter
            import _tkinter
            # Try initializing Tkinter to check if it's properly configured
            try:
                root = tkinter.Tk()
                root.destroy()
            except _tkinter.TclError:
                pytest.skip("Tkinter not properly configured - skipping visualization test")
        except ImportError:
            pytest.skip("Tkinter not available - skipping visualization test")
        
        # Mock the data exporter with real sample data
        self.vis_manager._data_exporter = Mock()
        self.vis_manager._data_exporter.export_job_similarity_matrix.return_value = self.sample_matrix
        
        # Generate heatmap
        output_path = self.vis_manager.generate_job_similarity_heatmap(
            department='Analytics',
            save_to_file=False
        )
        
        # Check that the output is a valid path or object
        self.assertIsNotNone(output_path)
    
    def test_hexbin_visualization_generation(self):
        """Test generation of hexbin visualization."""
        # Mock the data exporter with real sample data
        self.vis_manager._data_exporter = Mock()
        self.vis_manager._data_exporter.export_job_similarity_matrix.return_value = self.sample_matrix
        
        # Generate hexbin visualization
        output_path = self.vis_manager.generate_hexbin_visualization(
            department='Analytics',
            output_path=None,
            color_scheme='viridis',
            figsize=(10, 8),
            dpi=300
        )
        
        # Verify data exporter was called correctly
        self.vis_manager._data_exporter.export_job_similarity_matrix.assert_called_once_with(
            department='Analytics',
            config=ReportConfig(format="csv")
        )
    
    def test_gap_analysis_heatmap_generation(self):
        """Test generation of gap analysis heatmap."""
        # Mock the gap heatmap generator
        self.vis_manager._gap_heatmap_generator = Mock()
        self.vis_manager._gap_heatmap_generator.generate_heatmap.return_value = "test_output.png"
        
        # Generate gap analysis heatmap
        output_path = self.vis_manager.generate_gap_analysis_heatmap(
            department='Analytics',
            save_to_file=False
        )
        
        # Verify gap heatmap generator was called correctly
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