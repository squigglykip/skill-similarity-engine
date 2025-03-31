#!/usr/bin/env python3
"""
Functional test for job similarity workflow with HRIS adapter.

This test verifies the complete job similarity workflow from HRIS data transformation
to final visualization, ensuring end-to-end functionality.
"""

import sys
import os

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import unittest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import json
import yaml

# Import necessary modules
from skill_similarity_engine.models.skills import Skill, SkillTaxonomy
from skill_similarity_engine.models.jobs import Job, JobArchitecture, JobLevel
from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator
from skill_similarity_engine.visualization.reports import ReportConfig
from skill_similarity_engine.visualization.heatmaps import HeatmapGenerator
from skill_similarity_engine.hris_adapter.transformer import HRISTransformer
from skill_similarity_engine.hris_adapter.workflow import HRISWorkflow


class TestJobSimilarityWorkflow(unittest.TestCase):
    """Test complete job similarity workflow with HRIS adapter."""
    
    def setUp(self):
        """Set up test environment with sample HRIS data."""
        # Create temp directory for outputs
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Create HRIS skill taxonomy file
        self.hris_skills_csv = self.output_dir / "hris_skills.csv"
        with open(self.hris_skills_csv, "w") as f:
            f.write("skill_id,name,category,difficulty\n")
            f.write("S001,Python,Technical,3\n")
            f.write("S002,Data Analysis,Technical,4\n")
            f.write("S003,Machine Learning,Technical,5\n")
            f.write("S004,Project Management,Soft Skills,3\n")
            f.write("S005,Communication,Soft Skills,2\n")
        
        # Create HRIS job architecture file
        self.hris_jobs_csv = self.output_dir / "hris_jobs.csv"
        with open(self.hris_jobs_csv, "w") as f:
            f.write("job_id,title,department,salary_group\n")
            f.write("J001,Data Scientist,Data Science,Group 4\n")
            f.write("J002,Data Engineer,Data Engineering,Group 2\n")
            f.write("J003,Project Manager,Project Management,Group 3\n")
        
        # Create HRIS job-skills mapping file
        self.hris_job_skills_csv = self.output_dir / "hris_job_skills.csv"
        with open(self.hris_job_skills_csv, "w") as f:
            f.write("job_id,skill_id,proficiency\n")
            f.write("J001,S001,4\n")
            f.write("J001,S002,5\n")
            f.write("J001,S003,4\n")
            f.write("J002,S001,5\n")
            f.write("J002,S002,3\n")
            f.write("J003,S004,5\n")
            f.write("J003,S005,4\n")
        
        # Create a HRIS schema mapping file
        self.hris_config_path = self.output_dir / "hris_config.yaml"
        with open(self.hris_config_path, "w") as f:
            f.write("""
# HRIS Schema Mapping Configuration for Testing
hris_data:
  jobs_file: {jobs_file}
  skills_file: {skills_file}
  job_skills_file: {job_skills_file}
  file_format: csv
  encoding: utf-8
  delimiter: ","
  has_header: true

output_data:
  jobs_file: {output_dir}/jobs.csv
  skills_file: {output_dir}/skills.csv

jobs_mapping:
  job_id: job_id
  title: title
  department: department
  level: salary_group

skills_mapping:
  skill_id: skill_id
  name: name
  category: category

job_skills_mapping:
  job_id: job_id
  skill_id: skill_id
  proficiency: proficiency

salary_group_mapping:
  Group 1:
    level: ENTRY
    seniority: 1
  Group 2:
    level: ASSOCIATE
    seniority: 2
  Group 3:
    level: PROFESSIONAL
    seniority: 3
  Group 4:
    level: PROFESSIONAL
    seniority: 4

transformation_options:
  use_binary_skills: false
  default_proficiency: 3
            """.format(
                jobs_file=str(self.hris_jobs_csv).replace('\\', '/'), 
                skills_file=str(self.hris_skills_csv).replace('\\', '/'),
                job_skills_file=str(self.hris_job_skills_csv).replace('\\', '/'),
                output_dir=str(self.output_dir).replace('\\', '/')
            ))
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
    
    def test_end_to_end_workflow(self):
        """Test the complete workflow from HRIS data to visualization."""
        # Step 1: Transform HRIS data using the transformer
        try:
            transformer = HRISTransformer(config_path=str(self.hris_config_path))
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
            
            self.assertEqual(len(skill_taxonomy.skills), 5)
            self.assertEqual(len(job_architecture.jobs), 3)
            self.assertIn('S001', skill_taxonomy.skills)
            self.assertIn('J001', job_architecture.jobs)
            
            # DEBUG: Print the actual job level values
            print("\nDEBUG - Actual Job Level Mapping:")
            for job_id, job in job_architecture.jobs.items():
                print(f"  Job ID: {job_id}, Title: {job.title}, Seniority: {job.seniority}, Level: {job.level.name}, Value: {job.level.value}")
            
            # Read the transformed jobs file directly to see what was written
            print("\nDEBUG - Contents of transformed jobs file:")
            with open(jobs_path, 'r') as f:
                for i, line in enumerate(f):
                    if i < 5:  # Just print first few lines
                        print(f"  {line.strip()}")
            
            # Verify the salary group to level mapping worked
            self.assertEqual(job_architecture.jobs['J001'].level.value, "Mid-level")  # Maps from PROFESSIONAL to MID_LEVEL
            self.assertEqual(job_architecture.jobs['J002'].level.value, "Associate")  # Maps from ASSOCIATE to ASSOCIATE
            self.assertEqual(job_architecture.jobs['J003'].level.value, "Mid-level")  # Maps from PROFESSIONAL to MID_LEVEL
            
            # Verify the seniority values are correctly set
            self.assertEqual(job_architecture.jobs['J001'].seniority, 4)
            self.assertEqual(job_architecture.jobs['J002'].seniority, 2)
            self.assertEqual(job_architecture.jobs['J003'].seniority, 3)
            
            print("✓ Successfully loaded transformed data")
        except Exception as e:
            self.fail(f"Failed to load transformed data: {e}")
        
        # Step 3: Use the workflow to calculate similarity
        try:
            workflow = HRISWorkflow(config_path=str(self.hris_config_path))
            similarity_matrix, job_ids = workflow.run_pipeline("job_similarity")
            
            self.assertEqual(len(job_ids), 3)
            self.assertEqual(similarity_matrix.shape, (3, 3))
            
            # Get specific similarity values for testing
            j1_index = job_ids.index('J001')
            j2_index = job_ids.index('J002')
            j3_index = job_ids.index('J003')
            
            # Data Scientist and Data Engineer should be similar (both have Python, Data Analysis)
            ds_de_similarity = similarity_matrix[j1_index, j2_index]
            # Data Scientist and Project Manager should be dissimilar (no common skills)
            ds_pm_similarity = similarity_matrix[j1_index, j3_index]
            
            self.assertGreater(ds_de_similarity, 0.5)
            self.assertLess(ds_pm_similarity, 0.3)
            
            print(f"✓ Successfully calculated similarities using workflow: DS/DE={ds_de_similarity:.2f}, DS/PM={ds_pm_similarity:.2f}")
        except Exception as e:
            self.fail(f"Failed to run similarity workflow: {e}")
        
        # Step A (Alternative): Calculate similarity using direct calculator
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
            
            print(f"✓ Successfully calculated similarities directly: DS/DE={similarity_ds_de:.2f}, DS/PM={similarity_ds_pm:.2f}")
        except Exception as e:
            self.fail(f"Failed to calculate similarity directly: {e}")
        
        # Step 4: Generate and export similarity report
        try:
            # Create a similarity matrix for export
            job_ids = list(job_architecture.jobs.keys())
            similarity_rows = []
            
            for job_id1 in job_ids:
                for job_id2 in job_ids:
                    if job_id1 != job_id2:
                        similarity = calculator.calculate_job_similarity(job_id1, job_id2)
                        job1_title = job_architecture.jobs[job_id1].title
                        job2_title = job_architecture.jobs[job_id2].title
                        job1_dept = job_architecture.jobs[job_id1].department
                        job2_dept = job_architecture.jobs[job_id2].department
                        
                        similarity_rows.append({
                            'job_id_1': job_id1,
                            'job_id_2': job_id2,
                            'job_title_1': job1_title,
                            'job_title_2': job2_title,
                            'department_1': job1_dept,
                            'department_2': job2_dept,
                            'similarity_score': similarity
                        })
            
            # Convert to DataFrame and export
            similarity_df = pd.DataFrame(similarity_rows)
            output_csv = self.output_dir / "job_similarity_report.csv"
            similarity_df.to_csv(output_csv, index=False)
            
            # Verify export
            self.assertTrue(output_csv.exists())
            exported_df = pd.read_csv(output_csv)
            self.assertEqual(len(exported_df), len(similarity_rows))
            
            print("✓ Successfully generated and exported similarity report")
        except Exception as e:
            self.fail(f"Failed to generate similarity report: {e}")
        
        print("\n✓ Complete job similarity workflow with HRIS adapter test passed successfully!")


if __name__ == "__main__":
    unittest.main() 