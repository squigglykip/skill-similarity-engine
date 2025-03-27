#!/usr/bin/env python3
"""
Functional tests for large-scale performance.

This module tests the performance of the system with large-scale datasets,
focusing on memory usage and processing time.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np
import time
import gc
import logging
import matplotlib.pyplot as plt
import psutil
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger("test_large_scale_performance")

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.models.skills import SkillTaxonomy, Skill
from skill_similarity_engine.models.jobs import JobArchitecture, Job
from skill_similarity_engine.data.loaders import JobArchitectureLoader
from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator


class TestLargeScalePerformance(unittest.TestCase):
    """Test the performance of the system with large-scale datasets."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        # Define data paths
        cls.use_real_data = os.environ.get("USE_REAL_DATA", "False").lower() == "true"
        
        if cls.use_real_data:
            # Path to real data
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
        cls.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'output', 'tests', 'performance')
        os.makedirs(cls.output_dir, exist_ok=True)
        
        # Load data
        logger.info("Loading skill taxonomy...")
        cls.skill_taxonomy = SkillTaxonomy.from_file(os.path.join(cls.data_dir, 'skills.csv'))
        logger.info(f"Loaded {len(cls.skill_taxonomy.skills)} skills")
        
        logger.info("Loading job architecture...")
        job_loader = JobArchitectureLoader(cls.skill_taxonomy)
        cls.job_architecture = job_loader.load_from_csv(os.path.join(cls.data_dir, 'jobs.csv'))
        logger.info(f"Loaded {len(cls.job_architecture.jobs)} jobs")
    
    def setUp(self):
        """Set up test fixtures for each test."""
        # Skip tests if using sample data but real data is required
        if not self.use_real_data and os.environ.get("REQUIRE_REAL_DATA", "False").lower() == "true":
            self.skipTest("These tests require real data.")
        
        # Run garbage collection before each test
        gc.collect()
    
    def _measure_memory_usage(self):
        """Measure current memory usage of the process."""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return memory_info.rss / (1024 * 1024)  # Convert to MB
    
    def test_memory_scaling_with_job_count(self):
        """Test how memory usage scales with increasing job count."""
        # Skip if psutil is not available
        try:
            import psutil
        except ImportError:
            self.skipTest("psutil not available for memory testing")
        
        logger.info("Testing memory scaling with increasing job count")
        
        # Test parameters
        job_counts = [10, 20, 50, 100, 200]
        if len(self.job_architecture.jobs) > 250:
            job_counts.extend([500, 1000])
        if len(self.job_architecture.jobs) > 1500:
            job_counts.extend([1500, 2000])
        
        # Ensure job counts don't exceed available jobs
        job_counts = [count for count in job_counts if count <= len(self.job_architecture.jobs)]
        
        # Measure memory for different job counts
        memory_usage = []
        processing_times = []
        
        for job_count in job_counts:
            logger.info(f"Testing with {job_count} jobs")
            
            # Create a subset of jobs
            job_ids = list(self.job_architecture.jobs.keys())[:job_count]
            job_subset = {job_id: self.job_architecture.jobs[job_id] for job_id in job_ids}
            
            # Create a subset job architecture
            job_arch_subset = JobArchitecture()
            job_arch_subset.jobs = job_subset
            
            # Record memory before
            gc.collect()  # Force garbage collection
            memory_before = self._measure_memory_usage()
            
            # Time the similarity calculation process
            start_time = time.time()
            
            # Initialize vectorizer and calculator
            vectorizer = TfidfVectorizer(self.skill_taxonomy)
            calculator = CosineSimilarityCalculator(
                vectorizer=vectorizer,
                skill_taxonomy=self.skill_taxonomy,
                job_architecture=job_arch_subset
            )
            
            # Calculate a sample of job pairs
            sample_size = min(10, job_count)
            sample_job_ids = job_ids[:sample_size]
            
            for i, job1_id in enumerate(sample_job_ids):
                for job2_id in sample_job_ids[i+1:]:
                    _ = calculator.calculate_job_similarity(job1_id, job2_id)
            
            # Record time and memory
            end_time = time.time()
            memory_after = self._measure_memory_usage()
            
            # Calculate memory used and processing time
            memory_used = memory_after - memory_before
            proc_time = end_time - start_time
            
            memory_usage.append(memory_used)
            processing_times.append(proc_time)
            
            logger.info(f"  Memory usage: {memory_used:.2f} MB")
            logger.info(f"  Processing time: {proc_time:.2f} seconds")
            
            # Clean up to free memory
            del vectorizer
            del calculator
            del job_arch_subset
            gc.collect()
        
        # Plot memory usage
        plt.figure(figsize=(10, 6))
        plt.plot(job_counts, memory_usage, marker='o')
        plt.xlabel('Number of Jobs')
        plt.ylabel('Memory Usage (MB)')
        plt.title('Memory Scaling with Job Count')
        plt.grid(True, alpha=0.3)
        
        # Add polynomial trend line
        if len(job_counts) > 2:
            z = np.polyfit(job_counts, memory_usage, 2)
            p = np.poly1d(z)
            x_trend = np.linspace(min(job_counts), max(job_counts), 100)
            plt.plot(x_trend, p(x_trend), 'r--', alpha=0.7)
            
            # Extrapolate for NAB scale
            target_jobs = 35000  # NAB job scale
            predicted_memory = p(target_jobs)
            plt.text(0.05, 0.95, f"Projected memory for {target_jobs} jobs: {predicted_memory:.2f} MB",
                   transform=plt.gca().transAxes, bbox=dict(facecolor='white', alpha=0.7))
        
        memory_plot_path = os.path.join(self.output_dir, "memory_scaling.png")
        plt.savefig(memory_plot_path)
        plt.close()
        logger.info(f"Saved memory scaling plot to: {memory_plot_path}")
        
        # Plot processing time
        plt.figure(figsize=(10, 6))
        plt.plot(job_counts, processing_times, marker='o')
        plt.xlabel('Number of Jobs')
        plt.ylabel('Processing Time (seconds)')
        plt.title('Processing Time Scaling with Job Count')
        plt.grid(True, alpha=0.3)
        
        # Add polynomial trend line
        if len(job_counts) > 2:
            z = np.polyfit(job_counts, processing_times, 2)
            p = np.poly1d(z)
            x_trend = np.linspace(min(job_counts), max(job_counts), 100)
            plt.plot(x_trend, p(x_trend), 'r--', alpha=0.7)
            
            # Extrapolate for NAB scale
            target_jobs = 35000  # NAB job scale
            predicted_time = p(target_jobs)
            plt.text(0.05, 0.95, f"Projected time for {target_jobs} jobs: {predicted_time:.2f} seconds",
                   transform=plt.gca().transAxes, bbox=dict(facecolor='white', alpha=0.7))
        
        time_plot_path = os.path.join(self.output_dir, "time_scaling.png")
        plt.savefig(time_plot_path)
        plt.close()
        logger.info(f"Saved time scaling plot to: {time_plot_path}")
        
        # Export data
        scaling_data = pd.DataFrame({
            'job_count': job_counts,
            'memory_usage_mb': memory_usage,
            'processing_time_sec': processing_times
        })
        
        export_path = os.path.join(self.output_dir, "scaling_data.csv")
        scaling_data.to_csv(export_path, index=False)
        logger.info(f"Exported scaling data to: {export_path}")
    
    def test_performance_with_synthetic_data(self):
        """Test performance using synthetically generated large-scale data."""
        logger.info("Testing performance with synthetic data")
        
        # Define synthetic data sizes
        if self.use_real_data:
            # With real data, generate smaller synthetic datasets to supplement
            job_counts = [500, 1000, 2000]
            skill_count = 1000
        else:
            # With sample data only, generate larger synthetic datasets
            job_counts = [100, 500, 1000]
            skill_count = 500
        
        # Check if we have enough base data to work with
        if len(self.skill_taxonomy.skills) < 20:
            self.skipTest("Not enough skills for synthetic data generation")
        
        # Generate synthetic skill taxonomy based on real taxonomy patterns
        logger.info(f"Generating synthetic skill taxonomy with {skill_count} skills")
        
        # Sample existing skills to use as templates
        existing_skills = list(self.skill_taxonomy.skills.values())
        synthetic_skills = {}
        
        for i in range(skill_count):
            skill_id = f"SYN_SKILL_{i+1:04d}"
            
            # Use an existing skill as template
            template_skill = np.random.choice(existing_skills)
            
            # Create new skill with similar properties but unique ID
            synthetic_skills[skill_id] = Skill(
                id=skill_id,
                name=f"Synthetic Skill {i+1}",
                category=template_skill.category,
                subcategory=template_skill.subcategory,
                description=f"Synthetic skill {i+1} for performance testing"
            )
        
        synthetic_taxonomy = SkillTaxonomy()
        synthetic_taxonomy.skills = synthetic_skills
        
        # Test different job counts
        for job_count in job_counts:
            logger.info(f"Testing with {job_count} synthetic jobs")
            
            # Generate synthetic jobs based on skill distribution patterns
            synthetic_jobs = {}
            
            # Sample existing jobs as templates for skill count distribution
            job_templates = list(self.job_architecture.jobs.values())
            skill_counts = [len(job.skills) for job in job_templates]
            
            for i in range(job_count):
                job_id = f"SYN_JOB_{i+1:04d}"
                
                # Determine how many skills to assign
                num_skills = int(np.random.choice(skill_counts))
                num_skills = min(num_skills, skill_count // 10)  # Don't use too many skills
                
                # Randomly select skills and assign proficiency levels
                selected_skill_ids = np.random.choice(list(synthetic_skills.keys()), 
                                                 size=num_skills, replace=False)
                
                skills = {}
                for skill_id in selected_skill_ids:
                    # Assign random proficiency between 1 and 5
                    skills[skill_id] = np.random.randint(1, 6)
                
                # Create the job
                synthetic_jobs[job_id] = Job(
                    id=job_id,
                    title=f"Synthetic Job {i+1}",
                    description=f"Synthetic job {i+1} for performance testing",
                    department=f"Department {i % 10 + 1}",
                    level=f"Level {i % 5 + 1}",
                    skills=skills
                )
            
            # Create synthetic job architecture
            synthetic_architecture = JobArchitecture()
            synthetic_architecture.jobs = synthetic_jobs
            
            # Measure performance
            gc.collect()  # Force garbage collection
            memory_before = self._measure_memory_usage()
            start_time = time.time()
            
            # Initialize vectorizer and calculator
            vectorizer = TfidfVectorizer(synthetic_taxonomy)
            calculator = CosineSimilarityCalculator(
                vectorizer=vectorizer,
                skill_taxonomy=synthetic_taxonomy,
                job_architecture=synthetic_architecture
            )
            
            # Calculate time for similarity matrix generation
            similarity_start_time = time.time()
            
            # Get sample of jobs for similarity matrix
            sample_size = min(100, job_count)
            sample_job_ids = list(synthetic_jobs.keys())[:sample_size]
            
            # Calculate similarity for each pair
            similarity_pairs = []
            for i, job1_id in enumerate(sample_job_ids):
                for j, job2_id in enumerate(sample_job_ids[i+1:], i+1):
                    similarity = calculator.calculate_job_similarity(job1_id, job2_id)
                    similarity_pairs.append({
                        'job1_id': job1_id,
                        'job2_id': job2_id,
                        'similarity': similarity
                    })
            
            similarity_time = time.time() - similarity_start_time
            total_time = time.time() - start_time
            memory_after = self._measure_memory_usage()
            memory_used = memory_after - memory_before
            
            # Log results
            logger.info(f"  Generated {len(similarity_pairs)} similarity pairs")
            logger.info(f"  Memory usage: {memory_used:.2f} MB")
            logger.info(f"  Vectorization time: {similarity_start_time - start_time:.2f} seconds")
            logger.info(f"  Similarity calculation time: {similarity_time:.2f} seconds")
            logger.info(f"  Total processing time: {total_time:.2f} seconds")
            
            # Clean up to free memory
            del vectorizer
            del calculator
            del synthetic_architecture
            del synthetic_jobs
            gc.collect()


if __name__ == "__main__":
    # Run specific test case with real data if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--real-data":
        # Set environment variable to use real data
        os.environ["USE_REAL_DATA"] = "True"
        # Remove the flag from args so unittest doesn't try to interpret it
        sys.argv.pop(1)
    
    unittest.main() 