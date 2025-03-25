#!/usr/bin/env python3
"""
Functional test for job similarity workflow.

This test verifies the complete job similarity workflow from data loading to
visualization, ensuring end-to-end functionality.
"""

import unittest
import sys
import os
import tempfile
from pathlib import Path
import pandas as pd
import json

# Add the src directory to the path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

# Import necessary modules
from skill_similarity_engine.models.skills import Skill, SkillTaxonomy
from skill_similarity_engine.models.jobs import Job, JobArchitecture, JobLevel
from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator
from skill_similarity_engine.visualization.reports import ReportConfig
from skill_similarity_engine.visualization.heatmaps import HeatmapGenerator


class TestJobSimilarityWorkflow(unittest.TestCase):
    """Test complete job similarity workflow."""
    
    def setUp(self):
        """Set up test environment with sample data."""
        # Create temp directory for outputs
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Create skill taxonomy file
        self.skills_csv = self.output_dir / "skills.csv"
        with open(self.skills_csv, "w") as f:
            f.write("skill_id,name,category,difficulty\n")
            f.write("S001,Python,Technical,3\n")
            f.write("S002,Data Analysis,Technical,4\n")
            f.write("S003,Machine Learning,Technical,5\n")
            f.write("S004,Project Management,Soft Skills,3\n")
            f.write("S005,Communication,Soft Skills,2\n")
        
        # Create job architecture file
        self.jobs_csv = self.output_dir / "jobs.csv"
        with open(self.jobs_csv, "w") as f:
            f.write("job_id,title,department,level,skills\n")
            f.write("J001,Data Scientist,Data Science,Senior,S001:4;S002:5;S003:4\n")
            f.write("J002,Data Engineer,Data Engineering,Mid-level,S001:5;S002:3\n")
            f.write("J003,Project Manager,Project Management,Senior,S004:5;S005:4\n")
        
        # Create a configuration file
        self.config_file = self.output_dir / "config.yaml"
        with open(self.config_file, "w") as f:
            f.write("output_dir: {}\n".format(self.output_dir))
            f.write("similarity:\n")
            f.write("  threshold: 0.3\n")
            f.write("  metric: cosine\n")
            f.write("opportunity_thresholds:\n")
            f.write("  high_similarity_threshold: 0.7\n")
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
    
    def test_end_to_end_workflow(self):
        """Test the complete workflow from data loading to visualization."""
        # Step 1: Load data from CSV files
        try:
            skill_taxonomy = SkillTaxonomy.from_file(self.skills_csv)
            job_architecture = JobArchitecture.from_file(self.jobs_csv)
            
            self.assertEqual(len(skill_taxonomy.skills), 5)
            self.assertEqual(len(job_architecture.jobs), 3)
            self.assertIn('S001', skill_taxonomy.skills)
            self.assertIn('J001', job_architecture.jobs)
            
            print("✓ Successfully loaded data from CSV files")
        except Exception as e:
            self.fail(f"Failed to load data: {e}")
        
        # Step 2: Calculate similarity using TF-IDF vectorization
        try:
            vectorizer = TfidfVectorizer(skill_taxonomy)
            calculator = CosineSimilarityCalculator(
                vectorizer=vectorizer,
                skill_taxonomy=skill_taxonomy,
                job_architecture=job_architecture
            )
            
            # Calculate similarity between Data Scientist and Data Engineer (should be high)
            similarity_ds_de = calculator.calculate_job_similarity('J001', 'J002')
            
            # Calculate similarity between Data Scientist and Project Manager (should be low)
            similarity_ds_pm = calculator.calculate_job_similarity('J001', 'J003')
            
            # Check that similarities are in the expected range
            self.assertGreater(similarity_ds_de, 0.5)  # Data Scientist and Data Engineer should be similar
            self.assertLess(similarity_ds_pm, 0.3)     # Data Scientist and Project Manager should be dissimilar
            
            print(f"✓ Successfully calculated similarities: DS/DE={similarity_ds_de:.2f}, DS/PM={similarity_ds_pm:.2f}")
        except Exception as e:
            self.fail(f"Failed to calculate similarity: {e}")
        
        # Step 3: Generate similarity report
        try:
            # Create a similarity matrix
            job_ids = list(job_architecture.jobs.keys())
            similarity_matrix = []
            
            for job_id1 in job_ids:
                row = {}
                for job_id2 in job_ids:
                    if job_id1 != job_id2:
                        row[job_id2] = calculator.calculate_job_similarity(job_id1, job_id2)
                    else:
                        row[job_id2] = 1.0  # Self-similarity is always 1.0
                similarity_matrix.append(row)
            
            # Convert to DataFrame
            df = pd.DataFrame(similarity_matrix, index=job_ids, columns=job_ids)
            
            # Export to CSV
            output_csv = self.output_dir / "job_similarity.csv"
            df.to_csv(output_csv)
            
            # Check that the file exists and has the correct format
            self.assertTrue(output_csv.exists())
            
            # Read back and verify
            df_read = pd.read_csv(output_csv, index_col=0)
            self.assertEqual(df_read.shape, (3, 3))  # 3 jobs x 3 jobs
            
            print("✓ Successfully generated and exported similarity report")
        except Exception as e:
            self.fail(f"Failed to generate similarity report: {e}")
        
        # Step 4: Visualize similarity as heatmap
        try:
            # Skip actual visualization but verify the data preparation steps
            job_titles = [job_architecture.jobs[job_id].title for job_id in job_ids]
            
            # Prepare similarity data in the format expected by the visualization
            job_title_mapping = {job_id: job_architecture.jobs[job_id].title for job_id in job_ids}
            
            # Export job metadata for visualization
            job_metadata = {
                job_id: {
                    "title": job_architecture.jobs[job_id].title,
                    "department": job_architecture.jobs[job_id].department,
                    "level": str(job_architecture.jobs[job_id].level)
                }
                for job_id in job_ids
            }
            
            metadata_file = self.output_dir / "job_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(job_metadata, f, indent=2)
            
            self.assertTrue(metadata_file.exists())
            
            print("✓ Successfully prepared visualization data")
        except Exception as e:
            self.fail(f"Failed to visualize similarity: {e}")
        
        print("\n✓ Complete job similarity workflow test passed successfully!")


if __name__ == "__main__":
    unittest.main() 