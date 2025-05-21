#!/usr/bin/env python3
"""
Functional test for the complete job similarity workflow.

This module tests the end-to-end workflow for job similarity calculation,
from HRIS data transformation to visualization.
"""

import unittest
import os
import sys
import tempfile
from pathlib import Path
import pandas as pd

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Use non-GUI backend for matplotlib to avoid Tkinter dependency
import matplotlib
matplotlib.use('Agg')  # This must be done before any other matplotlib imports

# Import necessary modules
from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture
from skill_similarity_engine.hris_adapter.transformer import HRISTransformer
from skill_similarity_engine.hris_adapter.workflow import HRISWorkflow

# Import from our test data helper modules
from tests.test_data import (
    ENGINE_JOBS_CSV, 
    ENGINE_SKILLS_CSV,
    HRIS_JOBS_CSV,
    HRIS_SKILLS_CSV,
    HRIS_JOB_SKILLS_CSV
)
from tests.functional.data_load_patch import get_test_data_files, TEST_HRIS_CONFIG
from tests.functional import BaseFunctionalTest


class TestJobSimilarityWorkflow(BaseFunctionalTest):
    """Test complete job similarity workflow with HRIS adapter."""
    
    def test_end_to_end_workflow(self):
        """Test the complete workflow from HRIS data to visualization."""
        # Step 1: Transform HRIS data using the transformer
        try:
            # Use centralized test HRIS config
            hris_config = TEST_HRIS_CONFIG
            transformer = HRISTransformer(config_path=str(hris_config))
            
            # Override the HRIS data paths to use test data
            transformer.config['hris_data']['jobs_file'] = HRIS_JOBS_CSV
            transformer.config['hris_data']['skills_file'] = HRIS_SKILLS_CSV
            transformer.config['hris_data']['job_skills_file'] = HRIS_JOB_SKILLS_CSV
            
            # Use temporary output files
            output_dir = Path(tempfile.mkdtemp())
            jobs_output = output_dir / "jobs.csv"
            skills_output = output_dir / "skills.csv"
            transformer.config['output_data']['jobs_file'] = str(jobs_output)
            transformer.config['output_data']['skills_file'] = str(skills_output)
            
            # Transform data
            jobs_path, skills_path = transformer.transform()
            
            self.assertTrue(os.path.exists(jobs_path))
            self.assertTrue(os.path.exists(skills_path))
            
            print("✓ Successfully transformed HRIS data")
        except Exception as e:
            self.fail(f"Failed to transform HRIS data: {e}")
        
        # Step 2: Load transformed data into model objects
        try:
            skill_taxonomy = SkillTaxonomy.from_file(skills_path)
            job_architecture = JobArchitecture.from_file(jobs_path)
            
            # Verify we have expected number of skills and jobs
            self.assertGreater(len(skill_taxonomy.skills), 0)
            self.assertGreater(len(job_architecture.jobs), 0)
            
            # Read the transformed jobs file directly to see what was written
            print("\nDEBUG - Contents of transformed jobs file:")
            with open(jobs_path, 'r') as f:
                for i, line in enumerate(f):
                    if i < 5:  # Just print first few lines
                        print(f"  {line.strip()}")
            
            print("✓ Successfully loaded transformed data")
        except Exception as e:
            self.fail(f"Failed to load transformed data: {e}")
        
        # Step 3: Use the workflow to calculate similarity
        try:
            # Create a new workflow instance with the transformed output file paths
            workflow = HRISWorkflow(config_path=str(hris_config))
            
            # Override paths in the workflow transformer to use our transformed files
            workflow.transformer.config['output_data']['jobs_file'] = str(jobs_path)
            workflow.transformer.config['output_data']['skills_file'] = str(skills_path)
            
            # Skip transformation since we already did it, directly load the models and run analysis
            taxonomy, job_arch, employee_db = workflow._load_models(jobs_path, skills_path)
            similarity_matrix, job_ids = workflow._run_analysis("job_similarity", taxonomy, job_arch, employee_db)
            
            self.assertGreater(len(job_ids), 0)
            self.assertEqual(similarity_matrix.shape, (len(job_ids), len(job_ids)))
            
            # Verify similarity values (diagonal should be 1.0)
            for i in range(len(job_ids)):
                self.assertAlmostEqual(similarity_matrix[i, i], 1.0)
            
            print("✓ Successfully calculated job similarity")
        except Exception as e:
            self.fail(f"Failed to calculate similarity: {e}")
        
        # Step 4: Generate reports and visualizations
        try:
            reports_dir = Path(tempfile.mkdtemp())
            
            # Create visualization manager from visualizer.py (which has a different signature)
            from skill_similarity_engine.visualization.visualizer import VisualisationManager
            
            vis_manager = VisualisationManager(
                skill_taxonomy=skill_taxonomy,
                job_architecture=job_architecture,
                employee_database=None,  # No employee data needed for job similarity
                output_dir=str(reports_dir)
            )
            
            # Generate a simple heatmap report for all departments 
            departments = set(job.department for job in job_architecture.jobs.values())
            for department in departments:
                output_path = vis_manager.generate_job_similarity_heatmap(
                    department=department,
                    output_path=str(reports_dir / f"{department.lower()}_heatmap.png")
                )
                self.assertIsNotNone(output_path)
            
            # Check if reports were generated (at least one PNG file)
            report_files = list(reports_dir.glob("*.png"))
            self.assertGreater(len(report_files), 0)
            
            print("✓ Successfully generated reports and visualizations")
        except Exception as e:
            self.fail(f"Failed to generate reports: {e}")
            
        print("✓ All workflow steps completed successfully")
    
    def test_workflow_with_specific_department(self):
        """Test workflow with a specific department filter."""
        # Use centralized test HRIS config
        hris_config = TEST_HRIS_CONFIG
        transformer = HRISTransformer(config_path=str(hris_config))
        
        # Override the HRIS data paths to use test data
        transformer.config['hris_data']['jobs_file'] = HRIS_JOBS_CSV
        transformer.config['hris_data']['skills_file'] = HRIS_SKILLS_CSV
        transformer.config['hris_data']['job_skills_file'] = HRIS_JOB_SKILLS_CSV
        
        # Use temporary output files
        output_dir = Path(tempfile.mkdtemp())
        jobs_output = output_dir / "jobs.csv"
        skills_output = output_dir / "skills.csv"
        transformer.config['output_data']['jobs_file'] = str(jobs_output)
        transformer.config['output_data']['skills_file'] = str(skills_output)
        
        # Transform data
        jobs_path, skills_path = transformer.transform()
        
        # Get a specific department from the transformed jobs
        job_df = pd.read_csv(jobs_path)
        if 'department' in job_df.columns and not job_df['department'].empty:
            test_department = job_df['department'].iloc[0]
            
            # Load models ourselves
            skill_taxonomy = SkillTaxonomy.from_file(str(skills_path))
            job_architecture = JobArchitecture.from_file(str(jobs_path))
            
            # Generate report for this department
            reports_dir = output_dir / "department_reports"
            reports_dir.mkdir(exist_ok=True)
            
            try:
                # Create visualization manager
                from skill_similarity_engine.visualization.visualizer import VisualisationManager
                
                vis_manager = VisualisationManager(
                    skill_taxonomy=skill_taxonomy,
                    job_architecture=job_architecture,
                    employee_database=None,  # No employee data needed for job similarity
                    output_dir=str(reports_dir)
                )
                
                # Generate a simple heatmap for this department
                output_file = reports_dir / f"{test_department.lower()}_heatmap.png"
                output_path = vis_manager.generate_job_similarity_heatmap(
                    department=test_department,
                    output_path=str(output_file)
                )
                
                # If output_path is returned by the method, use it, otherwise use our expected file path
                file_to_check = output_path if output_path else str(output_file)
                
                # Verify the report was generated
                self.assertTrue(os.path.exists(file_to_check), f"Output file not found at {file_to_check}")
                print(f"✓ Successfully generated heatmap for department {test_department}")
            except Exception as e:
                self.fail(f"Failed to generate visualization: {e}")

    def test_visualisation_only(self):
        """Test that we can generate visualisations directly from data files."""
        
        # Step 1: Load test data directly
        try:
            # Use the imported test data constants instead of hardcoded paths
            jobs_path = Path(ENGINE_JOBS_CSV)
            skills_path = Path(ENGINE_SKILLS_CSV)
            
            if not jobs_path.exists() or not skills_path.exists():
                self.fail(f"Test data not found at expected locations: {jobs_path}, {skills_path}")
            
            # Load the data directly - convert Path objects to strings
            skill_taxonomy = SkillTaxonomy.from_file(str(skills_path))
            job_architecture = JobArchitecture.from_file(str(jobs_path))
            
            print("✓ Successfully loaded test data directly")
        except Exception as e:
            self.fail(f"Failed to load test data: {e}")
        
        # Step 2: Generate visualisations
        try:
            reports_dir = Path(tempfile.mkdtemp())
            
            # Create visualization manager from visualizer.py
            from skill_similarity_engine.visualization.visualizer import VisualisationManager
            
            vis_manager = VisualisationManager(
                skill_taxonomy=skill_taxonomy,
                job_architecture=job_architecture,
                employee_database=None,  # No employee data needed for job similarity
                output_dir=str(reports_dir)
            )
            
            # Generate a simple heatmap report for all departments
            departments = set(job.department for job in job_architecture.jobs.values())
            for department in departments:
                output_path = vis_manager.generate_job_similarity_heatmap(
                    department=department,
                    output_path=str(reports_dir / f"{department.lower()}_heatmap.png")
                )
                self.assertIsNotNone(output_path)
            
            # Check if reports were generated (at least one PNG file)
            report_files = list(reports_dir.glob("*.png"))
            self.assertGreater(len(report_files), 0)
            
            print("✓ Successfully generated visualisations directly")
        except Exception as e:
            self.fail(f"Failed to generate visualisations: {e}")


if __name__ == "__main__":
    unittest.main() 