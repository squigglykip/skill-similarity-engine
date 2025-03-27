#!/usr/bin/env python3
"""
Functional tests for validating job-to-job similarity with real data.

This module contains tests that verify the job similarity functionality
produces valid and useful results with real organization data.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger("test_real_data_validation")

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture
from skill_similarity_engine.data.loaders import JobArchitectureLoader
from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator
from skill_similarity_engine.visualization.visualizer import VisualisationManager, ReportConfig


class TestRealDataJobSimilarity(unittest.TestCase):
    """Test job similarity functionality with real organization data."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        # Define data paths - modify these to point to your real data
        cls.use_real_data = os.environ.get("USE_REAL_DATA", "False").lower() == "true"
        
        if cls.use_real_data:
            # Path to real data - update these paths to your real data location
            cls.data_dir = os.environ.get("REAL_DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'real'))
            logger.info(f"Using real data from: {cls.data_dir}")
            
            # Check if real data directory exists
            if not os.path.exists(cls.data_dir):
                logger.warning(f"Real data directory does not exist: {cls.data_dir}")
                logger.warning("Falling back to sample data")
                cls.use_real_data = False
        
        # Use sample data as fallback
        if not cls.use_real_data:
            cls.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sample')
            logger.info(f"Using sample data from: {cls.data_dir}")
        
        # Setup output directory for test artifacts
        cls.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'output', 'tests', 'real_data')
        os.makedirs(cls.output_dir, exist_ok=True)
        
        # Load data
        logger.info("Loading skill taxonomy...")
        cls.skill_taxonomy = SkillTaxonomy.from_file(os.path.join(cls.data_dir, 'skills.csv'))
        logger.info(f"Loaded {len(cls.skill_taxonomy.skills)} skills")
        
        logger.info("Loading job architecture...")
        job_loader = JobArchitectureLoader(cls.skill_taxonomy)
        cls.job_architecture = job_loader.load_from_csv(os.path.join(cls.data_dir, 'jobs.csv'))
        logger.info(f"Loaded {len(cls.job_architecture.jobs)} jobs")
        
        # Initialize similarity calculator
        logger.info("Setting up similarity calculator...")
        cls.vectorizer = TfidfVectorizer(cls.skill_taxonomy)
        cls.calculator = CosineSimilarityCalculator(
            vectorizer=cls.vectorizer,
            skill_taxonomy=cls.skill_taxonomy,
            job_architecture=cls.job_architecture
        )
        
        # Get departments for testing
        cls.departments = set(job.department for job in cls.job_architecture.jobs.values())
        logger.info(f"Found {len(cls.departments)} departments")
        
        # Initialize visualization manager
        cls.vis_manager = VisualisationManager(
            skill_taxonomy=cls.skill_taxonomy,
            job_architecture=cls.job_architecture,
            output_dir=cls.output_dir
        )
    
    def setUp(self):
        """Set up test fixtures for each test."""
        # Skip tests if using sample data but real data is required
        if not self.use_real_data and os.environ.get("REQUIRE_REAL_DATA", "False").lower() == "true":
            self.skipTest("These tests require real data.")
    
    def test_job_similarity_distribution(self):
        """Test the distribution of job similarity scores."""
        # Select a department for testing
        if not self.departments:
            self.skipTest("No departments found in job architecture.")
        
        # Use Analytics department if available, otherwise use first department
        department = 'Analytics' if 'Analytics' in self.departments else next(iter(self.departments))
        logger.info(f"Testing job similarity distribution for department: {department}")
        
        # Generate similarity matrix
        similarity_df = self.vis_manager._data_exporter.export_job_similarity_matrix(
            department=department,
            config=ReportConfig(include_metadata=True)
        )
        
        # Output basic statistics
        similarity_stats = {
            "count": len(similarity_df),
            "mean": similarity_df['similarity'].mean(),
            "median": similarity_df['similarity'].median(),
            "std": similarity_df['similarity'].std(),
            "min": similarity_df['similarity'].min(),
            "max": similarity_df['similarity'].max(),
        }
        
        logger.info(f"Similarity statistics for {department}:")
        for key, value in similarity_stats.items():
            logger.info(f"  {key}: {value:.4f}" if isinstance(value, float) else f"  {key}: {value}")
        
        # Plot similarity distribution
        plt.figure(figsize=(10, 6))
        sns.histplot(similarity_df['similarity'], bins=20, kde=True)
        plt.title(f"Job Similarity Distribution - {department}")
        plt.xlabel("Similarity Score")
        plt.ylabel("Count")
        plt.tight_layout()
        
        # Save plot
        plot_path = os.path.join(self.output_dir, f"{department}_similarity_distribution.png")
        plt.savefig(plot_path)
        plt.close()
        logger.info(f"Saved similarity distribution plot to: {plot_path}")
        
        # Validate distribution - these thresholds should be adjusted based on your data
        # For real data validation, we expect reasonable similarity scores
        # These assertions are examples and should be customized for your specific context
        if self.use_real_data:
            self.assertGreater(similarity_stats["mean"], 0.1, "Mean similarity score is too low")
            self.assertLess(similarity_stats["mean"], 0.9, "Mean similarity score is too high")
            self.assertGreater(similarity_stats["std"], 0.05, "Similarity distribution has too little variance")
    
    def test_job_skill_vector_quality(self):
        """Test the quality of job skill vectors."""
        # Verify job skill vectors have reasonable properties
        logger.info("Testing job skill vector quality")
        
        # Sample jobs to test (limit to 20 for reasonable test time)
        sample_jobs = list(self.job_architecture.jobs.keys())[:20]
        
        # Get vectors for sampled jobs
        vectors = {}
        vector_stats = {}
        
        for job_id in sample_jobs:
            job = self.job_architecture.jobs[job_id]
            # Access the pre-computed job vectors directly from the calculator's job_vectors dictionary
            vector = self.calculator.job_vectors[job_id]
            vectors[job_id] = vector
            
            # Calculate basic statistics
            vector_stats[job_id] = {
                "job_title": job.title,
                "department": job.department,
                "num_skills": len(job.skills),
                "vector_size": len(vector),
                "non_zero": np.count_nonzero(vector),
                "sparsity": 1.0 - (np.count_nonzero(vector) / len(vector)),
                "mean": np.mean(vector),
                "std": np.std(vector)
            }
        
        # Log summary statistics
        df = pd.DataFrame.from_dict(vector_stats, orient='index')
        logger.info(f"Vector statistics summary:")
        logger.info(f"  Average number of skills per job: {df['num_skills'].mean():.2f}")
        logger.info(f"  Average vector sparsity: {df['sparsity'].mean():.2f}")
        logger.info(f"  Average vector mean: {df['mean'].mean():.4f}")
        logger.info(f"  Average vector std: {df['std'].mean():.4f}")
        
        # Save detailed statistics
        stats_path = os.path.join(self.output_dir, "job_vector_stats.csv")
        df.to_csv(stats_path)
        logger.info(f"Saved vector statistics to: {stats_path}")
        
        # Validate vector properties
        # These assertions need to be adjusted based on your specific data
        for job_id, stats in vector_stats.items():
            self.assertEqual(stats["vector_size"], len(self.skill_taxonomy.skills), 
                           f"Vector for job {job_id} has incorrect size")
            self.assertLessEqual(stats["non_zero"], stats["num_skills"], 
                               f"Vector for job {job_id} has more non-zero elements than skills")
    
    def test_cross_department_similarity(self):
        """Test similarity between jobs in different departments."""
        # Skip if we don't have at least 2 departments
        if len(self.departments) < 2:
            self.skipTest("Need at least 2 departments for cross-department testing.")
        
        logger.info("Testing cross-department job similarity")
        
        # Get two different departments
        departments = list(self.departments)[:2]
        dept1, dept2 = departments[0], departments[1]
        
        # Get jobs from each department
        dept1_jobs = [job_id for job_id, job in self.job_architecture.jobs.items() if job.department == dept1]
        dept2_jobs = [job_id for job_id, job in self.job_architecture.jobs.items() if job.department == dept2]
        
        # Limit to at most 5 jobs per department to keep test runtime reasonable
        dept1_jobs = dept1_jobs[:min(5, len(dept1_jobs))]
        dept2_jobs = dept2_jobs[:min(5, len(dept2_jobs))]
        
        # Calculate cross-department similarities
        similarities = []
        
        for job1_id in dept1_jobs:
            for job2_id in dept2_jobs:
                similarity = self.calculator.calculate_job_similarity(job1_id, job2_id)
                job1 = self.job_architecture.jobs[job1_id]
                job2 = self.job_architecture.jobs[job2_id]
                
                similarities.append({
                    "job1_id": job1_id,
                    "job1_title": job1.title,
                    "job1_department": dept1,
                    "job2_id": job2_id,
                    "job2_title": job2.title,
                    "job2_department": dept2,
                    "similarity": similarity
                })
        
        # Convert to DataFrame
        df = pd.DataFrame(similarities)
        
        # Log summary statistics
        logger.info(f"Cross-department similarity between {dept1} and {dept2}:")
        logger.info(f"  Number of job pairs: {len(df)}")
        logger.info(f"  Mean similarity: {df['similarity'].mean():.4f}")
        logger.info(f"  Median similarity: {df['similarity'].median():.4f}")
        logger.info(f"  Min similarity: {df['similarity'].min():.4f}")
        logger.info(f"  Max similarity: {df['similarity'].max():.4f}")
        
        # Save detailed results
        results_path = os.path.join(self.output_dir, f"cross_dept_{dept1}_{dept2}_similarity.csv")
        df.to_csv(results_path, index=False)
        logger.info(f"Saved cross-department similarities to: {results_path}")
        
        # Find most similar cross-department job pairs
        top_pairs = df.sort_values('similarity', ascending=False).head(3)
        logger.info("Top 3 most similar cross-department job pairs:")
        for idx, row in top_pairs.iterrows():
            logger.info(f"  {row['job1_title']} ({row['job1_department']}) <-> "
                      f"{row['job2_title']} ({row['job2_department']}): {row['similarity']:.4f}")
    
    def test_opportunity_flag_distribution(self):
        """Test the distribution of opportunity flags in job similarity results."""
        # Select a department for testing
        if not self.departments:
            self.skipTest("No departments found in job architecture.")
        
        # Use Analytics department if available, otherwise use first department
        department = 'Analytics' if 'Analytics' in self.departments else next(iter(self.departments))
        logger.info(f"Testing opportunity flag distribution for department: {department}")
        
        # Generate similarity matrix with opportunity flags
        similarity_df = self.vis_manager._data_exporter.export_job_similarity_matrix(
            department=department,
            config=ReportConfig(include_metadata=True, add_opportunity_flags=True)
        )
        
        # Count opportunities by type
        opportunity_counts = {
            "high_similarity": similarity_df['is_high_similarity_opportunity'].sum(),
            "internal_mobility": similarity_df['is_internal_mobility_opportunity'].sum(),
            "cross_departmental": similarity_df.get('is_cross_departmental_opportunity', pd.Series([False] * len(similarity_df))).sum()
        }
        
        # Log opportunity statistics
        total_pairs = len(similarity_df)
        logger.info(f"Opportunity distribution for {department} (out of {total_pairs} job pairs):")
        for key, value in opportunity_counts.items():
            percentage = (value / total_pairs) * 100 if total_pairs > 0 else 0
            logger.info(f"  {key}: {value} ({percentage:.1f}%)")
        
        # Create a distribution chart
        plt.figure(figsize=(10, 6))
        x = ['High Similarity', 'Internal Mobility', 'Cross Departmental']
        y = [opportunity_counts['high_similarity'], 
             opportunity_counts['internal_mobility'],
             opportunity_counts['cross_departmental']]
        
        plt.bar(x, y)
        plt.title(f"Opportunity Distribution - {department}")
        plt.ylabel("Number of Job Pairs")
        plt.tight_layout()
        
        # Save plot
        plot_path = os.path.join(self.output_dir, f"{department}_opportunity_distribution.png")
        plt.savefig(plot_path)
        plt.close()
        logger.info(f"Saved opportunity distribution plot to: {plot_path}")
        
        # Validate opportunity distribution
        # These thresholds should be adjusted based on expectations for your real data
        if self.use_real_data:
            self.assertLess(opportunity_counts['high_similarity'] / total_pairs, 0.5, 
                          "Too many high similarity opportunities (>50% of pairs)")


if __name__ == "__main__":
    # Run specific test case with real data if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--real-data":
        # Set environment variable to use real data
        os.environ["USE_REAL_DATA"] = "True"
        # Remove the flag from args so unittest doesn't try to interpret it
        sys.argv.pop(1)
    
    unittest.main() 