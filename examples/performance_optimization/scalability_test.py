#!/usr/bin/env python
"""
Scalability Testing for Similarity Calculation

This script tests how the memory-efficient similarity calculation approach
scales with increasing job counts compared to the naive approach. It runs
a series of tests with different job counts and plots the results.
"""

import os
import sys
import time
import argparse
import logging
import numpy as np
import psutil
import json
from pathlib import Path
from typing import List, Dict, Tuple, Any
import matplotlib.pyplot as plt

# Add the project src directory to the path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

# Import from the demo to reuse functionality
from adaptive_similarity_demo import (
    SyntheticJobData, calculate_similarities_naive, calculate_similarities_chunked, 
    DEFAULT_NUM_SKILLS, DEFAULT_SIMILARITY_THRESHOLD, DEFAULT_MEMORY_LIMIT_MB
)

from skill_similarity_engine.utils.memory_aware import memory_aware_processing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scalability_test.log")
    ]
)
logger = logging.getLogger("scalability_test")

# Default test parameters
DEFAULT_MAX_JOBS = 10000
DEFAULT_JOB_STEP = 1000
DEFAULT_NUM_SKILLS = 500
DEFAULT_RUNS_PER_SIZE = 3

def run_scalability_test(
    max_jobs: int = DEFAULT_MAX_JOBS,
    job_step: int = DEFAULT_JOB_STEP,
    num_skills: int = DEFAULT_NUM_SKILLS,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
    runs_per_size: int = DEFAULT_RUNS_PER_SIZE,
    include_naive: bool = False,
    naive_max_jobs: int = 5000  # Maximum job count for naive approach
) -> Dict[str, Any]:
    """
    Run a scalability test with increasing job counts.
    
    Args:
        max_jobs: Maximum number of jobs to test
        job_step: Step size for increasing job count
        num_skills: Number of skills to use
        threshold: Similarity threshold
        memory_limit_mb: Memory limit per worker
        runs_per_size: Number of runs per job size for more reliable results
        include_naive: Whether to include the naive approach for comparison
        naive_max_jobs: Maximum job count for naive approach (to avoid OOM)
        
    Returns:
        Dictionary with test results
    """
    # Generate job sizes to test
    job_sizes = list(range(job_step, max_jobs + 1, job_step))
    
    # Results containers
    results = {
        "job_sizes": job_sizes,
        "chunked_times": [],
        "chunked_memory": [],
        "naive_times": [],
        "naive_memory": [],
        "parameters": {
            "num_skills": num_skills,
            "threshold": threshold,
            "memory_limit_mb": memory_limit_mb,
            "runs_per_size": runs_per_size
        }
    }
    
    # Test each job size
    for job_size in job_sizes:
        logger.info(f"Testing with {job_size} jobs")
        
        # Run multiple times for more reliable results
        chunked_times = []
        chunked_memories = []
        naive_times = []
        naive_memories = []
        
        for run in range(1, runs_per_size + 1):
            logger.info(f"Run {run}/{runs_per_size}")
            
            # Generate synthetic data for this run
            synthetic_data = SyntheticJobData(job_size, num_skills)
            job_vectors = synthetic_data.get_all_vectors()
            
            # Test chunked approach
            logger.info("Testing chunked approach")
            start_time = time.time()
            chunked_start_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            
            with memory_aware_processing():
                _ = calculate_similarities_chunked(
                    job_vectors, threshold, memory_limit_mb
                )
            
            elapsed_chunked = time.time() - start_time
            chunked_end_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            chunked_peak_memory = chunked_end_memory
            
            chunked_times.append(elapsed_chunked)
            chunked_memories.append(chunked_peak_memory)
            
            logger.info(f"Chunked approach: {elapsed_chunked:.2f}s, {chunked_peak_memory:.1f} MB")
            
            # Test naive approach (only for smaller job sizes)
            if include_naive and job_size <= naive_max_jobs:
                logger.info("Testing naive approach")
                start_time = time.time()
                naive_start_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                
                _ = calculate_similarities_naive(job_vectors, threshold)
                
                elapsed_naive = time.time() - start_time
                naive_end_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                naive_peak_memory = naive_end_memory
                
                naive_times.append(elapsed_naive)
                naive_memories.append(naive_peak_memory)
                
                logger.info(f"Naive approach: {elapsed_naive:.2f}s, {naive_peak_memory:.1f} MB")
            
        # Average the results from multiple runs
        results["chunked_times"].append(np.mean(chunked_times))
        results["chunked_memory"].append(np.mean(chunked_memories))
        
        if include_naive and job_size <= naive_max_jobs:
            results["naive_times"].append(np.mean(naive_times))
            results["naive_memory"].append(np.mean(naive_memories))
        else:
            # Fill with None for job sizes where naive wasn't run
            results["naive_times"].append(None)
            results["naive_memory"].append(None)
    
    return results

def plot_results(results: Dict[str, Any], output_dir: str = ".") -> None:
    """
    Plot the test results.
    
    Args:
        results: Test results from run_scalability_test
        output_dir: Directory to save plots
    """
    os.makedirs(output_dir, exist_ok=True)
    
    job_sizes = results["job_sizes"]
    chunked_times = results["chunked_times"]
    chunked_memory = results["chunked_memory"]
    naive_times = results["naive_times"]
    naive_memory = results["naive_memory"]
    
    # Filter out None values for naive approach
    valid_naive_indices = [i for i, t in enumerate(naive_times) if t is not None]
    valid_job_sizes = [job_sizes[i] for i in valid_naive_indices]
    valid_naive_times = [naive_times[i] for i in valid_naive_indices]
    valid_naive_memory = [naive_memory[i] for i in valid_naive_indices]
    
    # Execution Time Plot
    plt.figure(figsize=(12, 8))
    plt.plot(job_sizes, chunked_times, 'g-o', label='Chunked Approach')
    
    if valid_naive_indices:
        plt.plot(valid_job_sizes, valid_naive_times, 'r-o', label='Naive Approach')
    
    plt.title("Execution Time vs. Job Count")
    plt.xlabel("Number of Jobs")
    plt.ylabel("Execution Time (seconds)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "execution_time.png"))
    
    # Memory Usage Plot
    plt.figure(figsize=(12, 8))
    plt.plot(job_sizes, chunked_memory, 'g-o', label='Chunked Approach')
    
    if valid_naive_indices:
        plt.plot(valid_job_sizes, valid_naive_memory, 'r-o', label='Naive Approach')
    
    plt.title("Memory Usage vs. Job Count")
    plt.xlabel("Number of Jobs")
    plt.ylabel("Memory Usage (MB)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "memory_usage.png"))
    
    # If we have naive approach results, plot the speedup
    if valid_naive_indices:
        # Calculate speedup for the sizes where we have naive results
        speedups = [naive_times[i] / chunked_times[i] if naive_times[i] is not None else None 
                   for i in range(len(job_sizes))]
        valid_speedups = [speedups[i] for i in valid_naive_indices]
        
        plt.figure(figsize=(12, 8))
        plt.plot(valid_job_sizes, valid_speedups, 'b-o')
        plt.axhline(y=1.0, color='k', linestyle='--', label='Breakeven')
        plt.title("Speedup vs. Job Count (Naive/Chunked)")
        plt.xlabel("Number of Jobs")
        plt.ylabel("Speedup Factor")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "speedup.png"))
    
    # Calculate quadratic vs. linear trend
    job_sizes_array = np.array(job_sizes)
    chunked_times_array = np.array(chunked_times)
    
    # Fit quadratic and linear models
    quad_coeffs = np.polyfit(job_sizes_array, chunked_times_array, 2)
    linear_coeffs = np.polyfit(job_sizes_array, chunked_times_array, 1)
    
    quad_fit = np.polyval(quad_coeffs, job_sizes_array)
    linear_fit = np.polyval(linear_coeffs, job_sizes_array)
    
    # Plot scaling behavior
    plt.figure(figsize=(12, 8))
    plt.plot(job_sizes, chunked_times, 'go', label='Actual Data')
    plt.plot(job_sizes, quad_fit, 'r-', label=f'Quadratic Fit (y = {quad_coeffs[0]:.2e}x² + {quad_coeffs[1]:.2e}x + {quad_coeffs[2]:.2e})')
    plt.plot(job_sizes, linear_fit, 'b-', label=f'Linear Fit (y = {linear_coeffs[0]:.2e}x + {linear_coeffs[1]:.2e})')
    plt.title("Scaling Behavior Analysis")
    plt.xlabel("Number of Jobs")
    plt.ylabel("Execution Time (seconds)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "scaling_behavior.png"))
    
    # Save results as JSON for later analysis
    with open(os.path.join(output_dir, "scalability_results.json"), "w") as f:
        # Convert numpy values to native Python types
        results_json = {k: v if not isinstance(v, np.ndarray) else v.tolist() for k, v in results.items()}
        json.dump(results_json, f, indent=4)
    
    logger.info(f"Plots saved to {output_dir}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Scalability Testing for Similarity Calculation")
    
    parser.add_argument(
        "--max-jobs", type=int, default=DEFAULT_MAX_JOBS,
        help=f"Maximum number of jobs to test (default: {DEFAULT_MAX_JOBS})"
    )
    parser.add_argument(
        "--job-step", type=int, default=DEFAULT_JOB_STEP,
        help=f"Step size for increasing job count (default: {DEFAULT_JOB_STEP})"
    )
    parser.add_argument(
        "--num-skills", type=int, default=DEFAULT_NUM_SKILLS,
        help=f"Number of skills to use (default: {DEFAULT_NUM_SKILLS})"
    )
    parser.add_argument(
        "--threshold", type=float, default=DEFAULT_SIMILARITY_THRESHOLD,
        help=f"Similarity threshold (default: {DEFAULT_SIMILARITY_THRESHOLD})"
    )
    parser.add_argument(
        "--memory-limit", type=int, default=DEFAULT_MEMORY_LIMIT_MB,
        help=f"Memory limit per worker in MB (default: {DEFAULT_MEMORY_LIMIT_MB})"
    )
    parser.add_argument(
        "--runs", type=int, default=DEFAULT_RUNS_PER_SIZE,
        help=f"Number of runs per job size for more reliable results (default: {DEFAULT_RUNS_PER_SIZE})"
    )
    parser.add_argument(
        "--include-naive", action="store_true",
        help="Include the naive approach for comparison (may cause OOM for large job counts)"
    )
    parser.add_argument(
        "--naive-max-jobs", type=int, default=5000,
        help="Maximum job count for naive approach (default: 5000)"
    )
    parser.add_argument(
        "--output-dir", type=str, default="scalability_results",
        help="Directory to save results and plots (default: 'scalability_results')"
    )
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    
    try:
        # Create output directory
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Run the test
        logger.info("Starting scalability test")
        results = run_scalability_test(
            max_jobs=args.max_jobs,
            job_step=args.job_step,
            num_skills=args.num_skills,
            threshold=args.threshold,
            memory_limit_mb=args.memory_limit,
            runs_per_size=args.runs,
            include_naive=args.include_naive,
            naive_max_jobs=args.naive_max_jobs
        )
        
        # Plot and save results
        plot_results(results, args.output_dir)
        
        logger.info("Scalability test completed successfully")
    
    except Exception as e:
        logger.exception(f"Error in scalability test: {e}")
        sys.exit(1) 