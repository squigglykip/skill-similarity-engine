"""
Performance tests for the skill similarity engine.

This module contains tests designed to evaluate the performance
of the system with larger datasets.
"""

import sys
import os
import pandas as pd
import numpy as np

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import unittest
import time
import random
import logging

from skill_similarity_engine.models.skills import Skill, SkillTaxonomy
from skill_similarity_engine.models.jobs import Job, JobArchitecture, JobLevel
from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator


class TestPerformance(unittest.TestCase):
    """Test case for measuring performance with larger datasets."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for all tests in this class."""
        # Configure logging to track performance metrics
        logging.basicConfig(level=logging.INFO)
        cls.logger = logging.getLogger(__name__)
    
    def test_large_job_architecture_performance(self):
        """Test performance with a larger job architecture."""
        # Get the path to sample data
        sample_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sample')
        
        # Load base taxonomy from sample data
        self.logger.info("Loading base taxonomy from sample data")
        taxonomy = SkillTaxonomy()
        skills_df = pd.read_csv(os.path.join(sample_dir, 'skills.csv'))
        for _, row in skills_df.iterrows():
            taxonomy.add_skill(Skill(skill_id=row['skill_id'], name=row['name']))
        
        # Load base job architecture from sample data
        self.logger.info("Loading base job architecture from sample data")
        job_arch = JobArchitecture()
        jobs_df = pd.read_csv(os.path.join(sample_dir, 'jobs.csv'))
        for _, row in jobs_df.iterrows():
            # Convert skills string to dictionary
            skills_dict = {}
            if pd.notna(row['skills']):  # Check if skills field is not NaN
                skills_list = row['skills'].split(',')
                for skill in skills_list:
                    skill_id, level = skill.split(':')
                    skills_dict[skill_id] = int(level)
            
            job = Job(
                job_id=row['job_id'],
                title=row['title'],
                department=row['department'],
                level=JobLevel(row['level']),
                skills=skills_dict
            )
            job_arch.add_job(job)
        
        # Scale up the data for performance testing
        num_skills = 500  # Adjust for larger test (production has ~35,000)
        num_jobs = 200    # Adjust for larger test (production has ~35,000)
        
        self.logger.info(f"Scaling up to {num_skills} skills and {num_jobs} jobs")
        
        # Time the taxonomy scaling
        start_time = time.time()
        
        # Scale up the taxonomy
        base_skill_count = len(taxonomy.skills)
        for i in range(base_skill_count + 1, num_skills + 1):
            skill_id = f"S{i:05d}"
            name = f"Skill {i}"
            # Use only valid skill types from the SkillType enum
            skill_type = random.choice(["technical", "soft", "domain", "methodology", "tool"])
            taxonomy.add_skill(Skill(skill_id=skill_id, name=name, skill_type=skill_type))
        
        taxonomy_time = time.time() - start_time
        self.logger.info(f"Scaled up to {num_skills} skills in {taxonomy_time:.2f} seconds")
        
        # Time the job architecture scaling
        start_time = time.time()
        
        # Scale up the job architecture
        base_job_count = len(job_arch.jobs)
        all_skill_ids = list(taxonomy.skills.keys())
        
        for i in range(base_job_count + 1, num_jobs + 1):
            job_id = f"J{i:05d}"
            title = f"Job {i}"
            # Use departments from sample data
            department = random.choice(list(set(job.department for job in job_arch.jobs.values())))
            level = random.choice(list(JobLevel))
            
            # Assign random skills to each job
            num_job_skills = random.randint(5, 20)
            job_skill_ids = random.sample(all_skill_ids, num_job_skills)
            
            skills = {}
            for skill_id in job_skill_ids:
                skills[skill_id] = random.randint(1, 5)  # Random proficiency 1-5
            
            job = Job(
                job_id=job_id,
                title=title,
                department=department,
                level=level,
                skills=skills
            )
            job_arch.add_job(job)
        
        job_arch_time = time.time() - start_time
        self.logger.info(f"Scaled up to {num_jobs} jobs in {job_arch_time:.2f} seconds")
        
        # Time the vectorizer creation and fitting
        start_time = time.time()
        
        # Create a vectorizer and calculator
        vectorizer = TfidfVectorizer(taxonomy)
        calculator = CosineSimilarityCalculator(
            vectorizer=vectorizer,
            skill_taxonomy=taxonomy,
            job_architecture=job_arch
        )
        
        setup_time = time.time() - start_time
        self.logger.info(f"Set up similarity calculator in {setup_time:.2f} seconds")
        
        # Time similarity calculations
        start_time = time.time()
        num_calculations = 100
        
        # Calculate similarities between random job pairs
        for _ in range(num_calculations):
            job1_id = random.choice(list(job_arch.jobs.keys()))
            job2_id = random.choice(list(job_arch.jobs.keys()))
            calculator.calculate_job_similarity(job1_id, job2_id)
        
        calc_time = time.time() - start_time
        self.logger.info(f"Calculated {num_calculations} job similarities in {calc_time:.2f} seconds")
        self.logger.info(f"Average time per similarity: {calc_time/num_calculations:.4f} seconds")
        
        # Time matrix generation
        start_time = time.time()
        matrix_size = 50
        
        # Generate similarity matrix for a subset of jobs
        job_ids = random.sample(list(job_arch.jobs.keys()), matrix_size)
        matrix = np.zeros((matrix_size, matrix_size))
        
        for i, job1_id in enumerate(job_ids):
            for j, job2_id in enumerate(job_ids):
                matrix[i, j] = calculator.calculate_job_similarity(job1_id, job2_id)
        
        matrix_time = time.time() - start_time
        self.logger.info(f"Generated similarity matrix for {matrix_size} jobs in {matrix_time:.2f} seconds")
        
        # Log total test time
        total_time = taxonomy_time + job_arch_time + setup_time + calc_time + matrix_time
        self.logger.info(f"Total test time: {total_time:.2f} seconds")
        
        # Verify reasonable performance - these are very rough guidelines
        # Will depend heavily on the machine running the tests
        self.assertLess(calc_time/num_calculations, 0.1, "Average similarity calculation time too high")
        self.assertLess(total_time, 60, "Total test time too high")


if __name__ == "__main__":
    unittest.main() 