#!/usr/bin/env python
"""
Memory-Efficient Implementation Comparison

This example demonstrates the memory savings achieved by using the memory-efficient
implementations compared to standard implementations. It loads progressively larger
datasets into both implementations and compares their memory usage.
"""

import gc
import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple

# Add the project src directory to the path
import sys
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.utils.performance import get_memory_usage, trigger_garbage_collection
from skill_similarity_engine.utils.memory_efficient_base import (
    MemoryEfficientFactory,
    MemoryEfficientDict,
    WeakDictOfLists
)

# Suppress warnings during demonstration
import warnings
warnings.filterwarnings("ignore")

def create_sample_job_data(num_jobs: int, num_skills: int) -> pd.DataFrame:
    """Create a sample job-skill mapping DataFrame with the specified dimensions."""
    # Create job IDs
    job_ids = [f"job_{i}" for i in range(num_jobs)]
    
    # Create skill IDs
    skill_ids = [f"skill_{i}" for i in range(num_skills)]
    
    # Create a dataframe with job-skill mappings
    # Each job will have a random set of 5-15% of the skills
    rows = []
    
    for job_id in job_ids:
        # Decide how many skills this job will have (5-15% of total)
        num_job_skills = max(1, int(num_skills * (0.05 + 0.1 * np.random.random())))
        
        # Randomly select skills for this job
        job_skills = np.random.choice(skill_ids, size=num_job_skills, replace=False)
        
        # Add rows for each job-skill combination
        for skill_id in job_skills:
            rows.append({
                'job_id': job_id,
                'skill_id': skill_id,
                'importance': np.random.randint(1, 5)  # Random importance score
            })
    
    return pd.DataFrame(rows)

class StandardJobContainer:
    """A standard (non-memory-optimized) container for job data."""
    
    def __init__(self):
        self.jobs = {}
        self.job_skills = {}
    
    def load_jobs(self, job_skill_df: pd.DataFrame) -> None:
        """Load jobs from a DataFrame."""
        # First pass: Create job objects
        for job_id in job_skill_df['job_id'].unique():
            self.jobs[job_id] = {'id': job_id, 'skills': []}
            self.job_skills[job_id] = {}
        
        # Second pass: Add skills to jobs
        for _, row in job_skill_df.iterrows():
            job_id = row['job_id']
            skill_id = row['skill_id']
            importance = row['importance']
            
            # Add the skill to the job object
            self.jobs[job_id]['skills'].append(skill_id)
            
            # Store the importance in the job_skills dictionary
            self.job_skills[job_id][skill_id] = importance

class MemoryEfficientJobContainer:
    """A memory-optimized container for job data."""
    
    def __init__(self):
        self.jobs = MemoryEfficientDict()
        self.job_skills = MemoryEfficientDict()
    
    def load_jobs(self, job_skill_df: pd.DataFrame) -> None:
        """Load jobs from a DataFrame using memory-efficient structures."""
        # First pass: Create job objects
        for job_id in job_skill_df['job_id'].unique():
            self.jobs[job_id] = {'id': job_id, 'skills': []}
            self.job_skills[job_id] = MemoryEfficientDict()
        
        # Second pass: Add skills to jobs
        for _, row in job_skill_df.iterrows():
            job_id = row['job_id']
            skill_id = row['skill_id']
            importance = row['importance']
            
            # Add the skill to the job object
            self.jobs[job_id]['skills'].append(skill_id)
            
            # Store the importance in the job_skills dictionary
            self.job_skills[job_id][skill_id] = importance
    
    def cleanup(self) -> None:
        """Perform explicit cleanup to release memory."""
        if hasattr(self, 'jobs') and self.jobs:
            self.jobs.clear()
        
        if hasattr(self, 'job_skills') and self.job_skills:
            for job_id, skills in self.job_skills.items():
                if isinstance(skills, MemoryEfficientDict):
                    skills.clear()
            self.job_skills.clear()
        
        # Trigger garbage collection
        trigger_garbage_collection()

def measure_memory_usage(container_class, job_skill_df: pd.DataFrame) -> Tuple[float, float]:
    """
    Measure memory usage before and after loading data into the container.
    
    Args:
        container_class: Container class to instantiate
        job_skill_df: DataFrame containing job-skill mappings
        
    Returns:
        Tuple of (memory_before, memory_after) in MB
    """
    # Trigger garbage collection to start with a clean state
    gc.collect()
    
    # Measure memory before
    memory_before = get_memory_usage().current_process_usage_mb
    
    # Create and load the container
    container = container_class()
    container.load_jobs(job_skill_df)
    
    # Measure memory after
    memory_after = get_memory_usage().current_process_usage_mb
    
    # Clean up if possible
    if hasattr(container, 'cleanup') and callable(getattr(container, 'cleanup')):
        container.cleanup()
    
    return memory_before, memory_after

def run_comparison(max_jobs: int = 40000, step: int = 1000, num_skills: int = 1000) -> Dict[str, List[Tuple[int, float]]]:
    """
    Run a comparison between standard and memory-efficient implementations.
    
    Args:
        max_jobs: Maximum number of jobs to test
        step: Number of jobs to add in each step
        num_skills: Number of skills in the dataset
        
    Returns:
        Dictionary with memory usage data for each implementation
    """
    results = {
        'standard': [],
        'efficient': []
    }
    
    # Create progressively larger datasets and measure memory usage
    for num_jobs in range(step, max_jobs + step, step):
        print(f"Testing with {num_jobs} jobs...")
        
        # Create sample data
        job_skill_df = create_sample_job_data(num_jobs, num_skills)
        
        # Measure standard implementation
        before_std, after_std = measure_memory_usage(StandardJobContainer, job_skill_df)
        std_usage = after_std - before_std
        results['standard'].append((num_jobs, std_usage))
        
        # Allow time for garbage collection
        time.sleep(1)
        
        # Measure memory-efficient implementation
        before_eff, after_eff = measure_memory_usage(MemoryEfficientJobContainer, job_skill_df)
        eff_usage = after_eff - before_eff
        results['efficient'].append((num_jobs, eff_usage))
        
        # Report the difference
        diff_pct = (std_usage - eff_usage) / std_usage * 100 if std_usage > 0 else 0
        print(f"  Standard: {std_usage:.2f} MB, Efficient: {eff_usage:.2f} MB, Savings: {diff_pct:.1f}%")
        
        # Clean up
        del job_skill_df
        gc.collect()
    
    return results

def plot_results(results: Dict[str, List[Tuple[int, float]]]) -> None:
    """
    Plot the memory usage comparison results.
    
    Args:
        results: Dictionary with memory usage data for each implementation
    """
    plt.figure(figsize=(12, 6))
    
    # Extract data for plotting
    jobs_std = [x[0] for x in results['standard']]
    mem_std = [x[1] for x in results['standard']]
    
    jobs_eff = [x[0] for x in results['efficient']]
    mem_eff = [x[1] for x in results['efficient']]
    
    # Plot the data
    plt.plot(jobs_std, mem_std, 'bo-', label='Standard Implementation')
    plt.plot(jobs_eff, mem_eff, 'go-', label='Memory-Efficient Implementation')
    
    # Fill the area between the lines to highlight the difference
    plt.fill_between(jobs_std, mem_std, mem_eff, alpha=0.2, color='green',
                     label='Memory Savings')
    
    # Add labels and legend
    plt.xlabel('Number of Jobs')
    plt.ylabel('Memory Usage (MB)')
    plt.title('Memory Usage Comparison: Standard vs Memory-Efficient Implementation')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save the plot
    output_dir = os.path.join(os.path.dirname(__file__), "memory_reports")
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, 'memory_comparison.png'), dpi=300, bbox_inches='tight')
    
    # Also create a savings plot
    plt.figure(figsize=(12, 6))
    savings = [(s - e) / s * 100 if s > 0 else 0 
               for (_, s), (_, e) in zip(results['standard'], results['efficient'])]
    
    plt.plot(jobs_std, savings, 'r.-', linewidth=2)
    plt.xlabel('Number of Jobs')
    plt.ylabel('Memory Savings (%)')
    plt.title('Memory Savings Percentage with Memory-Efficient Implementation')
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color='k', linestyle='-', alpha=0.2)
    
    # Save this plot too
    plt.savefig(os.path.join(output_dir, 'memory_savings.png'), dpi=300, bbox_inches='tight')
    
    # Show info about the plots
    print(f"Plots saved to {output_dir}")

def main():
    print("Starting memory efficiency comparison...")
    print("This will compare memory usage between standard and memory-efficient implementations")
    print("as they process progressively larger datasets.")
    print()
    
    # Run with modest parameters for a quick demonstration
    # In a real test, you might use larger values
    results = run_comparison(max_jobs=40000, step=5000, num_skills=1000)
    
    # Plot the results
    plot_results(results)
    
    print("\nComparison complete!")

if __name__ == "__main__":
    main() 