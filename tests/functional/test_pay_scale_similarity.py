#!/usr/bin/env python3
"""
Functional test for job similarity calculation with Pay Scale Area adjustment.

This test demonstrates how to incorporate Pay Scale Area (job seniority level)
into the similarity calculation to provide more realistic similarity scores
that account for career progression.
"""

import os
import sys
import logging
import unittest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("psa_similarity_test")

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture, Job, JobLevel
from skill_similarity_engine.data.loaders import JobArchitectureLoader
from skill_similarity_engine.similarity.cosine import CosineSimilarityCalculator


class PSAAdjustedSimilarityCalculator:
    """
    Wrapper for similarity calculator that adjusts scores based on Pay Scale Area.
    
    This class extends the base similarity calculator to incorporate job seniority
    (Pay Scale Area) into the similarity calculation.
    """
    
    def __init__(self, base_calculator):
        """Initialize with a base similarity calculator."""
        self.base_calculator = base_calculator
        self.job_architecture = base_calculator.job_architecture
        
        # Define PSA adjustment factors
        # This determines how much to reduce similarity based on PSA differences
        self.psa_adjustment_factors = {
            0: 1.0,    # Same PSA - no adjustment
            1: 0.9,    # 1 level difference - minor adjustment
            2: 0.7,    # 2 levels difference - moderate adjustment
            3: 0.5,    # 3 levels difference - significant adjustment
            4: 0.3,    # 4 levels difference - major adjustment
            5: 0.2     # 5 levels difference - extreme adjustment
        }
    
    def calculate_job_similarity(self, job1_id, job2_id):
        """
        Calculate job similarity with Pay Scale Area adjustment.
        
        Args:
            job1_id: ID of the first job
            job2_id: ID of the second job
            
        Returns:
            float: Adjusted similarity score between 0 and 1
        """
        # Get base similarity score
        base_similarity = self.base_calculator.calculate_job_similarity(job1_id, job2_id)
        
        # Get jobs
        job1 = self.job_architecture.jobs.get(job1_id)
        job2 = self.job_architecture.jobs.get(job2_id)
        
        if not job1 or not job2:
            return base_similarity
        
        # Get Pay Scale Areas - handle both attribute and dictionary access
        psa1 = self._get_psa(job1)
        psa2 = self._get_psa(job2)
        
        # If PSA is not available, return base similarity
        if not psa1 or not psa2:
            return base_similarity
        
        # Extract numeric part (e.g., "PSA3" -> 3)
        try:
            psa1_level = int(psa1.replace("PSA", ""))
            psa2_level = int(psa2.replace("PSA", ""))
            
            # Calculate PSA difference
            psa_diff = abs(psa1_level - psa2_level)
            
            # Get adjustment factor (default to 0.1 for very large differences)
            adjustment_factor = self.psa_adjustment_factors.get(psa_diff, 0.1)
            
            # Apply adjustment
            adjusted_similarity = base_similarity * adjustment_factor
            
            return adjusted_similarity
            
        except (ValueError, AttributeError):
            # If there's an error parsing PSA, return base similarity
            return base_similarity
    
    def _get_psa(self, job):
        """
        Get Pay Scale Area from a job object, handling different data structures.
        
        Args:
            job: A Job object or dictionary
            
        Returns:
            str: Pay Scale Area value or None if not found
        """
        # Try as attribute first
        if hasattr(job, 'pay_scale_area'):
            return job.pay_scale_area
        
        # Try as dictionary key
        if isinstance(job, dict) and 'pay_scale_area' in job:
            return job['pay_scale_area']
        
        # For job objects that might store PSA in a metadata dict
        if hasattr(job, 'metadata') and isinstance(job.metadata, dict):
            return job.metadata.get('pay_scale_area')
        
        # Try deriving from job level if needed
        if hasattr(job, 'level'):
            # Map common level names to PSA values
            level_to_psa = {
                'Entry': 'PSA1',
                'Junior': 'PSA1',
                'Associate': 'PSA2',
                'Mid-level': 'PSA3',
                'Senior': 'PSA4',
                'Lead': 'PSA5',
                'Manager': 'PSA5',
                'Director': 'PSA6',
                'Executive': 'PSA6'
            }
            return level_to_psa.get(job.level)
            
        # Not found
        return None


class TestPayScaleSimilarity(unittest.TestCase):
    """Test Pay Scale Area adjusted similarity calculation for jobs."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        # Get project root from src_path
        project_root = os.path.dirname(src_path)
        
        # Use sample data or synthetic data if available
        data_paths = [
            os.path.join(project_root, 'data', 'synthetic'),
            os.path.join(project_root, 'data', 'sample')
        ]
        
        # Find first existing data path
        cls.data_dir = next((path for path in data_paths if os.path.exists(path)), None)
        if not cls.data_dir:
            raise FileNotFoundError("No suitable data directory found. Please create sample or synthetic data.")
        
        logger.info(f"Using data from {cls.data_dir}")
        
        # Create output directory
        cls.output_dir = os.path.join(project_root, 'output', 'tests', 'psa_similarity')
        Path(cls.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Load skill taxonomy and job architecture
        cls.skill_taxonomy = SkillTaxonomy.from_file(os.path.join(cls.data_dir, 'skills.csv'))
        logger.info(f"Loaded {len(cls.skill_taxonomy.skills)} skills")
        
        job_loader = JobArchitectureLoader(cls.skill_taxonomy)
        cls.job_architecture = job_loader.load_from_csv(os.path.join(cls.data_dir, 'jobs.csv'))
        logger.info(f"Loaded {len(cls.job_architecture.jobs)} jobs")
        
        # Initialize similarity calculators
        cls.base_calculator = CosineSimilarityCalculator(
            vectorizer=None,  # Will be initialized within the calculator
            skill_taxonomy=cls.skill_taxonomy,
            job_architecture=cls.job_architecture
        )
        
        cls.psa_calculator = PSAAdjustedSimilarityCalculator(cls.base_calculator)
    
    def test_psa_adjusted_similarity(self):
        """Test that Pay Scale Area adjustment affects similarity scores as expected."""
        # Get all departments
        departments = set(job.department for job in self.job_architecture.jobs.values())
        
        # Choose largest department
        dept_counts = {}
        for job in self.job_architecture.jobs.values():
            dept_counts[job.department] = dept_counts.get(job.department, 0) + 1
        
        largest_dept = max(dept_counts.items(), key=lambda x: x[1])[0]
        logger.info(f"Testing with largest department: {largest_dept}")
        
        # Get jobs in the department
        dept_jobs = [job_id for job_id, job in self.job_architecture.jobs.items() 
                      if job.department == largest_dept]
        
        if len(dept_jobs) < 2:
            self.skipTest("Not enough jobs in department for testing")
        
        # Calculate similarities with and without PSA adjustment
        similarity_pairs = []
        
        # Take a sample if there are many jobs
        if len(dept_jobs) > 20:
            dept_jobs = np.random.choice(dept_jobs, size=20, replace=False)
        
        for i, job1_id in enumerate(dept_jobs):
            for j, job2_id in enumerate(dept_jobs[i+1:], i+1):
                job1 = self.job_architecture.jobs[job1_id]
                job2 = self.job_architecture.jobs[job2_id]
                
                # Get PSA values safely
                psa1 = self.psa_calculator._get_psa(job1)
                psa2 = self.psa_calculator._get_psa(job2)
                
                # Skip if PSA can't be determined
                if not psa1 or not psa2:
                    continue
                
                base_similarity = self.base_calculator.calculate_job_similarity(job1_id, job2_id)
                adjusted_similarity = self.psa_calculator.calculate_job_similarity(job1_id, job2_id)
                
                # Calculate PSA difference directly
                try:
                    psa_diff = abs(int(psa1.replace("PSA", "")) - int(psa2.replace("PSA", "")))
                    
                    similarity_pairs.append({
                        'job1_id': job1_id,
                        'job2_id': job2_id,
                        'job1_title': job1.title if hasattr(job1, 'title') else job1_id,
                        'job2_title': job2.title if hasattr(job2, 'title') else job2_id,
                        'job1_psa': psa1,
                        'job2_psa': psa2,
                        'psa_diff': psa_diff,
                        'base_similarity': base_similarity,
                        'adjusted_similarity': adjusted_similarity,
                        'adjustment_factor': adjusted_similarity / base_similarity if base_similarity > 0 else 1.0
                    })
                except (ValueError, TypeError):
                    # Skip if PSA values can't be parsed as numbers
                    continue
        
        if not similarity_pairs:
            self.skipTest("No valid job pairs with PSA found for testing")
        
        # Create DataFrame
        df = pd.DataFrame(similarity_pairs)
        
        # Save to CSV
        csv_path = os.path.join(self.output_dir, f"{largest_dept}_psa_similarity.csv")
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved similarity comparison to {csv_path}")
        
        # Verify that PSA adjustments are being applied
        self.assertTrue(any(row['base_similarity'] != row['adjusted_similarity'] for _, row in df.iterrows()),
                       "PSA adjustment is not affecting any similarity scores")
        
        # Verify that larger PSA differences lead to lower similarity
        if len(df) >= 2:
            high_diff = df[df['psa_diff'] >= 2]['adjustment_factor'].mean()
            low_diff = df[df['psa_diff'] <= 1]['adjustment_factor'].mean()
            self.assertLess(high_diff, low_diff, 
                           "Larger PSA differences should result in lower similarity scores")
        
        # Generate visualization
        self.generate_psa_effect_visualization(df)
    
    def generate_psa_effect_visualization(self, df):
        """Generate visualization showing the effect of PSA adjustment on similarity."""
        # Check if we have enough data to plot
        if len(df) < 2:
            logger.warning("Not enough data points for visualization")
            return
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # Plot 1: Scatter plot of base vs adjusted similarity by PSA difference
        scatter = ax1.scatter(df['base_similarity'], df['adjusted_similarity'], 
                             c=df['psa_diff'], cmap='viridis', 
                             alpha=0.7, s=50)
        
        # Add diagonal reference line
        ax1.plot([0, 1], [0, 1], 'k--', alpha=0.5)
        
        ax1.set_xlabel('Base Similarity')
        ax1.set_ylabel('PSA-Adjusted Similarity')
        ax1.set_title('Effect of PSA Adjustment on Similarity Scores')
        ax1.grid(True, alpha=0.3)
        
        # Add colorbar
        cbar = fig.colorbar(scatter, ax=ax1)
        cbar.set_label('PSA Difference')
        
        # Plot 2: Bar chart of average adjustment by PSA difference
        # Group by PSA difference
        try:
            psa_group = df.groupby('psa_diff')['adjustment_factor'].mean().reset_index()
            
            # Check if we have data to plot
            if len(psa_group) > 0:
                bars = ax2.bar(psa_group['psa_diff'], psa_group['adjustment_factor'], 
                              color='steelblue', alpha=0.7)
                
                ax2.set_xlabel('PSA Difference')
                ax2.set_ylabel('Average Adjustment Factor')
                ax2.set_title('Similarity Adjustment by PSA Difference')
                ax2.set_xticks(psa_group['psa_diff'])
                ax2.grid(True, alpha=0.3, axis='y')
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                            f'{height:.2f}', ha='center', va='bottom')
            else:
                ax2.text(0.5, 0.5, "Insufficient data for adjustment factor chart", 
                        ha='center', va='center')
                ax2.set_title('Similarity Adjustment by PSA Difference')
        except Exception as e:
            logger.warning(f"Error generating adjustment factor chart: {e}")
            ax2.text(0.5, 0.5, "Error generating chart", ha='center', va='center')
            ax2.set_title('Similarity Adjustment by PSA Difference')
        
        plt.tight_layout()
        
        # Save figure
        try:
            plot_path = os.path.join(self.output_dir, "psa_similarity_effect.png")
            plt.savefig(plot_path, dpi=300)
            plt.close()
            logger.info(f"Generated visualization at {plot_path}")
        except Exception as e:
            logger.error(f"Error saving visualization: {e}")
            plt.close()
    
    def test_career_progression_paths(self):
        """Test identifying career progression paths that respect Pay Scale Area."""
        # Choose a department with a good distribution of levels
        tech_jobs = [job for job_id, job in self.job_architecture.jobs.items() 
                    if job.department == 'Technology']
        
        if len(tech_jobs) < 5:
            self.skipTest("Not enough Technology jobs for testing career paths")
        
        # Pick a junior role as starting point by checking PSA values
        junior_jobs = []
        for job in tech_jobs:
            psa = self.psa_calculator._get_psa(job)
            if psa == 'PSA1':
                junior_jobs.append(job)
        
        if not junior_jobs:
            # Try PSA2 if no PSA1 jobs found
            for job in tech_jobs:
                psa = self.psa_calculator._get_psa(job)
                if psa == 'PSA2':
                    junior_jobs.append(job)
            
        if not junior_jobs:
            self.skipTest("No junior roles found for testing career paths")
        
        start_job = junior_jobs[0]
        start_psa = self.psa_calculator._get_psa(start_job)
        logger.info(f"Starting career path from: {start_job.job_id} - {start_job.title if hasattr(start_job, 'title') else start_job.job_id} ({start_psa})")
        
        # Calculate similarity to all other technology jobs
        career_paths = []
        
        for job in tech_jobs:
            if job.job_id == start_job.job_id:
                continue
            
            # Get PSA for target job
            job_psa = self.psa_calculator._get_psa(job)
            
            # Skip if PSA can't be determined
            if not job_psa:
                continue
            
            # Calculate both similarities
            base_similarity = self.base_calculator.calculate_job_similarity(start_job.job_id, job.job_id)
            adjusted_similarity = self.psa_calculator.calculate_job_similarity(start_job.job_id, job.job_id)
            
            try:
                # Get PSA values as integers
                start_psa_level = int(start_psa.replace("PSA", ""))
                job_psa_level = int(job_psa.replace("PSA", ""))
                
                # Calculate PSA difference
                psa_diff = job_psa_level - start_psa_level
                
                # Determine if this is a good career progression step
                # We want jobs that are 1-2 levels higher in PSA
                good_progression = psa_diff > 0 and psa_diff <= 2
                
                career_paths.append({
                    'start_job_id': start_job.job_id,
                    'target_job_id': job.job_id,
                    'start_title': start_job.title if hasattr(start_job, 'title') else start_job.job_id,
                    'target_title': job.title if hasattr(job, 'title') else job.job_id,
                    'start_psa': start_psa,
                    'target_psa': job_psa,
                    'psa_diff': psa_diff,
                    'base_similarity': base_similarity,
                    'adjusted_similarity': adjusted_similarity,
                    'good_progression': good_progression
                })
            except (ValueError, TypeError):
                # Skip if PSA values can't be parsed as numbers
                continue
                
        if not career_paths:
            self.skipTest("No valid career path job pairs found")
        
        # Create DataFrame
        df = pd.DataFrame(career_paths)
        
        # Save to CSV
        csv_path = os.path.join(self.output_dir, "career_progression_paths.csv")
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved career progression paths to {csv_path}")
        
        # Generate a visualisation of the potential career paths
        self.generate_career_path_visualization(df, start_job)
        
        # Verify that PSA adjustment helps identify better career paths
        # The average similarity of good progression paths should be higher with PSA adjustment
        good_paths = df[df['good_progression']]
        
        if len(good_paths) > 0:
            # Calculate the ratio of adjusted to base similarity for good paths
            good_paths_ratio = good_paths['adjusted_similarity'].sum() / good_paths['base_similarity'].sum()
            
            # Calculate the same ratio for poor progression paths
            poor_paths = df[~df['good_progression']]
            if len(poor_paths) > 0:
                poor_paths_ratio = poor_paths['adjusted_similarity'].sum() / poor_paths['base_similarity'].sum()
                
                # The good paths should have a better ratio (less adjustment/penalty)
                self.assertGreater(good_paths_ratio, poor_paths_ratio, 
                                  "PSA adjustment should favor appropriate career progression paths")
    
    def generate_career_path_visualization(self, df, start_job):
        """Generate visualization of career progression paths from a starting job."""
        # Sort by PSA and then by similarity
        df = df.sort_values(by=['psa_diff', 'adjusted_similarity'], ascending=[True, False])
        
        # Create figure
        plt.figure(figsize=(12, 8))
        
        # Set up colors based on whether it's a good progression or not
        colors = ['green' if x else 'red' for x in df['good_progression']]
        
        # Get job title for chart title
        start_job_title = start_job.title if hasattr(start_job, 'title') else start_job.job_id
        start_job_psa = self.psa_calculator._get_psa(start_job)
        
        # Plot bars
        bars = plt.barh(range(len(df)), df['adjusted_similarity'], color=colors, alpha=0.7)
        
        # Add base similarity as smaller, transparent bars
        plt.barh(range(len(df)), df['base_similarity'], color='blue', alpha=0.3)
        
        # Create labels safely
        labels = []
        for _, row in df.iterrows():
            try:
                label = f"{row.target_title} ({row.target_psa}, Diff: +{row.psa_diff})"
            except (AttributeError, ValueError):
                # Fall back to job ID if there's an issue
                label = f"Job {row.target_job_id} (Diff: +{row.psa_diff})"
            labels.append(label)
        
        # Add PSA information to labels
        plt.yticks(ticks=range(len(df)), labels=labels)
        
        plt.xlabel('Similarity Score')
        plt.title(f'Career Progression Paths from {start_job_title} ({start_job_psa})')
        
        # Add legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color='green', lw=4, label='Good Progression (1-2 levels up)'),
            Line2D([0], [0], color='red', lw=4, label='Poor Progression (too big jump or lateral/down)'),
            Line2D([0], [0], color='blue', lw=4, alpha=0.3, label='Base Similarity (no PSA adjustment)')
        ]
        plt.legend(handles=legend_elements, loc='lower right')
        
        plt.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        
        # Save figure
        plot_path = os.path.join(self.output_dir, "career_progression_paths.png")
        plt.savefig(plot_path, dpi=300)
        plt.close()
        
        logger.info(f"Generated career path visualization at {plot_path}")


if __name__ == '__main__':
    unittest.main() 