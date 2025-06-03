#!/usr/bin/env python
"""
Adaptive Similarity Calculation Demo

This example demonstrates how to use the memory-aware processing framework,
chunking utilities, and parallel processing to efficiently calculate similarities
between a large number of items while adapting to memory constraints.

The demo simulates a job-to-job similarity calculation scenario with synthetic
data to demonstrate how the system handles large datasets (35,000+ jobs) on
standard hardware with limited memory (32GB RAM).
"""

import os
import sys
import time
import argparse
import logging
import numpy as np
import psutil
import threading
from pathlib import Path
from typing import List, Dict, Tuple, Any
import matplotlib.pyplot as plt

# Add the project src directory to the path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.utils.memory_aware import (
    MemoryStrategy, MemoryThresholds, memory_aware_processing,
    calculate_optimal_chunk_size, estimate_memory_requirements
)
from skill_similarity_engine.utils.matrix_chunking import (
    SimilarityMatrixChunker, MatrixChunk, reconstruct_symmetric_matrix
)
from skill_similarity_engine.utils.parallel import ParallelProcessor
from skill_similarity_engine.utils.progress import progress_context
from skill_similarity_engine.utils.error_handling import error_context, retry, Checkpoint
from skill_similarity_engine.utils.chunking import ChunkingStrategy
from skill_similarity_engine.utils.performance import get_memory_usage, trigger_garbage_collection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("adaptive_similarity_demo.log")
    ]
)
logger = logging.getLogger("adaptive_similarity_demo")

# Global constants
DEFAULT_NUM_JOBS = 5000
DEFAULT_NUM_SKILLS = 1000
DEFAULT_MATRIX_SIZE = 5000 
DEFAULT_SIMILARITY_THRESHOLD = 0.3  # Only store similarities above this threshold
DEFAULT_MEMORY_LIMIT_MB = 1000  # Target memory limit per worker

class SyntheticJobData:
    """
    Generates synthetic job-skill data for testing similarity calculations.
    
    This class creates random job vectors with a controlled sparsity level,
    similar to real-world job-skill mappings.
    """
    
    def __init__(self, num_jobs: int, num_skills: int, sparsity: float = 0.95):
        """
        Initialize the synthetic data generator.
        
        Args:
            num_jobs: Number of jobs to generate
            num_skills: Number of skills in the taxonomy
            sparsity: Percentage of zero values (higher = more sparse)
        """
        self.num_jobs = num_jobs
        self.num_skills = num_skills
        self.sparsity = sparsity
        
        logger.info(f"Generating synthetic data with {num_jobs} jobs, "
                    f"{num_skills} skills, and {sparsity:.2f} sparsity")
        
        # Generate the job vectors (each job has a subset of skills)
        self.job_vectors = self._generate_job_vectors()
        
        # Calculate average number of skills per job
        avg_skills = np.mean(np.sum(self.job_vectors > 0, axis=1))
        logger.info(f"Generated {num_jobs} jobs with average of {avg_skills:.1f} skills per job")
    
    def _generate_job_vectors(self) -> np.ndarray:
        """
        Generate synthetic job vectors with controlled sparsity.
        
        Returns:
            Array of shape (num_jobs, num_skills) with skill weights
        """
        # Create empty vectors
        vectors = np.zeros((self.num_jobs, self.num_skills), dtype=np.float32)
        
        # For each job, randomly activate some skills
        for i in range(self.num_jobs):
            # Decide how many skills this job has (random between 5-50)
            num_active_skills = np.random.randint(5, min(50, self.num_skills))
            
            # Randomly select the skills
            active_skills = np.random.choice(
                self.num_skills, size=num_active_skills, replace=False
            )
            
            # Assign random weights to the active skills (between 0.1 and 1.0)
            vectors[i, active_skills] = np.random.uniform(0.1, 1.0, size=num_active_skills)
        
        return vectors
    
    def get_job_vector(self, job_id: int) -> np.ndarray:
        """
        Get the vector for a specific job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Skill vector for the job
        """
        return self.job_vectors[job_id]
    
    def get_all_vectors(self) -> np.ndarray:
        """
        Get all job vectors.
        
        Returns:
            Array of all job vectors
        """
        return self.job_vectors

def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return np.dot(vec1, vec2) / (norm1 * norm2)

def calculate_chunk_similarities(
    chunk: MatrixChunk,
    job_vectors: np.ndarray,
    threshold: float = 0.0
) -> np.ndarray:
    """
    Calculate similarities for a specific chunk of the matrix.
    
    Args:
        chunk: Matrix chunk to process
        job_vectors: Array of job vectors
        threshold: Similarity threshold (pairs below this are set to 0)
        
    Returns:
        Matrix of similarity scores for the chunk
    """
    rows = job_vectors[chunk.row_start:chunk.row_end]
    cols = job_vectors[chunk.col_start:chunk.col_end]
    
    # Initialize the result matrix
    result = np.zeros((len(rows), len(cols)), dtype=np.float32)
    
    # Calculate similarities for each pair in the chunk
    for i in range(len(rows)):
        for j in range(len(cols)):
            # For symmetric matrices, we can skip the lower triangle
            # (when processing a diagonal chunk)
            if chunk.row_start == chunk.col_start and j < i:
                continue
            
            similarity = calculate_cosine_similarity(rows[i], cols[j])
            
            # Apply threshold
            if similarity >= threshold:
                result[i, j] = similarity
    
    return result

def calculate_similarities_naive(
    job_vectors: np.ndarray,
    threshold: float = 0.0
) -> np.ndarray:
    """
    Calculate similarity matrix using a naive approach (all at once).
    
    This is used as a baseline for comparison.
    
    Args:
        job_vectors: Array of job vectors
        threshold: Similarity threshold
        
    Returns:
        Full similarity matrix
    """
    num_jobs = len(job_vectors)
    similarities = np.zeros((num_jobs, num_jobs), dtype=np.float32)
    
    with progress_context(total=num_jobs, desc="Calculating similarities (naive)") as progress:
        for i in range(num_jobs):
            for j in range(i, num_jobs):  # Only calculate upper triangle
                similarity = calculate_cosine_similarity(job_vectors[i], job_vectors[j])
                
                # Apply threshold
                if similarity >= threshold:
                    similarities[i, j] = similarity
                    similarities[j, i] = similarity  # Symmetric
            
            progress.update()
    
    return similarities

def process_chunk_wrapper(chunk_with_args):
    """
    Top-level wrapper for processing a matrix chunk with arguments. This is needed for multiprocessing on Windows.
    Args:
        chunk_with_args: Tuple (chunk, job_vectors, threshold)
    Returns:
        Tuple (chunk, result)
    """
    chunk, vectors, thresh = chunk_with_args
    result = calculate_chunk_similarities(chunk, vectors, thresh)
    return (chunk, result)

def calculate_similarities_chunked(
    job_vectors: np.ndarray,
    threshold: float = 0.0,
    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB
) -> np.ndarray:
    """
    Calculate similarity matrix using adaptive chunking.
    
    Args:
        job_vectors: Array of job vectors
        threshold: Similarity threshold
        memory_limit_mb: Memory limit per worker in MB
        
    Returns:
        Full similarity matrix
    """
    num_jobs = len(job_vectors)
    
    # Configure memory-aware chunking
    thresholds = MemoryThresholds(
        warning_percent=70.0,
        critical_percent=85.0,
        emergency_percent=95.0
    )
    
    # Calculate optimal initial chunk size based on vector size
    bytes_per_value = 4  # float32
    vector_bytes = job_vectors.nbytes / num_jobs
    chunk_size = calculate_optimal_chunk_size(
        item_size_bytes=vector_bytes * 2,  # Include output matrix
        target_memory_mb=memory_limit_mb * 0.8,  # Leave some buffer
        min_chunk_size=50,
        max_chunk_size=2000
    )
    
    # Create a chunking strategy
    chunking_strategy = ChunkingStrategy(
        initial_chunk_size=chunk_size,
        min_chunk_size=50,
        max_chunk_size=2000,
        memory_threshold_percent=85.0,
        target_memory_percent=70.0
    )
    
    # Create matrix chunker
    matrix_chunker = SimilarityMatrixChunker(
        num_items=num_jobs,
        strategy=chunking_strategy,
        symmetric=True  # Only calculate upper triangle
    )
    
    # Estimate the number of chunks
    estimated_chunks = matrix_chunker.estimate_num_chunks()
    logger.info(f"Will process similarity matrix in approximately {estimated_chunks} chunks")
    # Use parallel processing based on available memory and CPU cores
    processor = ParallelProcessor(
        memory_limit_mb=memory_limit_mb,
        memory_per_worker_mb=memory_limit_mb // 2
    )
    
    # Process chunks in parallel and collect results
    chunks_dict = {}
    
    with progress_context(total=estimated_chunks, desc="Processing matrix chunks") as progress:
        # Prepare chunks with their arguments for Windows-compatible parallel processing
        chunk_items = []
        for chunk in matrix_chunker.matrix_chunks():
            chunk_items.append((chunk, job_vectors, threshold))
        
        # Process chunks using map instead of process_matrix_chunks for Windows compatibility
        results = processor.map(process_chunk_wrapper, chunk_items)
        
        # Convert results to dictionary format
        for chunk, result in results:
            key = (chunk.row_start, chunk.row_end, chunk.col_start, chunk.col_end)
            chunks_dict[key] = result
            progress.update(1)
            
        # Check memory usage and trigger GC if needed
        memory_usage = get_memory_usage()
        if memory_usage.current_process_usage_mb > memory_limit_mb * 0.9:
            trigger_garbage_collection(full=True)
            
    # Reconstruct the full matrix from chunks
    logger.info(f"Reconstructing full matrix from {len(chunks_dict)} chunks")

    similarities = reconstruct_symmetric_matrix(chunks_dict, num_jobs)
    
    return similarities

def plot_memory_usage(memory_usage: List[float], title: str, output_path: str) -> None:
    """
    Plot memory usage over time.
    
    Args:
        memory_usage: List of memory usage values (MB)
        title: Plot title
        output_path: Path to save the plot
    """
    plt.figure(figsize=(10, 6))
    plt.plot(memory_usage, 'b-')
    plt.title(title)
    plt.xlabel("Time Steps")
    plt.ylabel("Memory Usage (MB)")
    plt.grid(True)
    plt.savefig(output_path)
    logger.info(f"Memory usage plot saved to {output_path}")

def monitor_cpu_usage(interval=1.0):
    """
    Monitor CPU usage over time with per-core tracking.
    
    Args:
        interval: Sampling interval in seconds
        
    Returns:
        Dictionary containing CPU usage data
    """
    cpu_data = {
        'timestamp': [],
        'per_core': [],
        'average': []
    }
    
    # Flag to control monitoring thread
    monitoring = {'active': True}
    
    def collect_cpu_data():
        start_time = time.time()
        while monitoring['active']:
            # Get per-core CPU usage
            per_core = psutil.cpu_percent(interval=None, percpu=True)
            avg_usage = sum(per_core) / len(per_core)
            
            # Record data
            cpu_data['timestamp'].append(time.time() - start_time)
            cpu_data['per_core'].append(per_core)
            cpu_data['average'].append(avg_usage)
            
            # Sleep for the specified interval
            time.sleep(interval)
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=collect_cpu_data)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Return both the data dictionary and the control flag
    return cpu_data, monitoring

def plot_cpu_usage(cpu_data, title, output_path):
    """
    Plot CPU usage over time.
    
    Args:
        cpu_data: Dictionary containing CPU usage data
        title: Plot title
        output_path: Path to save the plot
    """
    plt.figure(figsize=(12, 6))
    
    # Convert per-core data to numpy array for easier plotting
    if cpu_data['per_core']:
        per_core_array = np.array(cpu_data['per_core'])
        num_cores = per_core_array.shape[1]
        
        # Plot each core with light lines
        for i in range(num_cores):
            plt.plot(cpu_data['timestamp'], per_core_array[:, i], 
                     alpha=0.3, linewidth=1, label=f"Core {i}" if i == 0 else None)
        
        # Plot average with a thicker line
        plt.plot(cpu_data['timestamp'], cpu_data['average'], 
                 'r-', linewidth=2, label="Average")
        
        # Add a single "Cores" entry to the legend
        plt.plot([], [], 'b-', alpha=0.3, label="Individual Cores")
    
    plt.title(title)
    plt.xlabel("Time (seconds)")
    plt.ylabel("CPU Usage (%)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    logger.info(f"CPU usage plot saved to {output_path}")

def memory_efficient_similarity_demo(
    num_jobs: int = DEFAULT_NUM_JOBS,
    num_skills: int = DEFAULT_NUM_SKILLS,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
    compare_naive: bool = False
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Demonstrate memory-efficient similarity calculation.
    
    Args:
        num_jobs: Number of jobs to generate
        num_skills: Number of skills in the taxonomy
        threshold: Similarity threshold
        memory_limit_mb: Memory limit per worker in MB
        compare_naive: Whether to also run the naive approach for comparison
        
    Returns:
        Tuple of (similarity_matrix, performance_metrics)
    """
    logger.info(f"Starting similarity demo with {num_jobs} jobs and {num_skills} skills")
    logger.info(f"Using similarity threshold: {threshold}")
    
    # Track memory usage during execution
    memory_usage_naive = []
    memory_usage_chunked = []
    
    # Start CPU monitoring
    cpu_data, cpu_monitoring = monitor_cpu_usage(interval=1.0)
    
    # Generate synthetic job data
    synthetic_data = SyntheticJobData(num_jobs, num_skills)
    job_vectors = synthetic_data.get_all_vectors()
    
    # Estimate memory requirements
    vector_memory_mb = job_vectors.nbytes / (1024 * 1024)
    full_matrix_memory_mb = (num_jobs * num_jobs * 4) / (1024 * 1024)  # 4 bytes per float32
    
    logger.info(f"Job vectors memory: {vector_memory_mb:.1f} MB")
    logger.info(f"Full similarity matrix memory: {full_matrix_memory_mb:.1f} MB")
    
    # Performance metrics
    metrics = {
        "num_jobs": num_jobs,
        "num_skills": num_skills,
        "vector_memory_mb": vector_memory_mb,
        "matrix_memory_mb": full_matrix_memory_mb,
        "threshold": threshold,
    }
    
    similarities_naive = None
    if compare_naive and num_jobs <= 5000:  # Don't run naive with too many jobs
        logger.info("Running naive similarity calculation as baseline")
        
        # Track memory during naive calculation
        def track_memory():
            memory_usage_naive.append(psutil.Process().memory_info().rss / (1024 * 1024))
        
        # Run naive calculation with timing
        start_time = time.time()
        track_memory()  # Initial memory usage
        
        similarities_naive = calculate_similarities_naive(job_vectors, threshold)
        
        elapsed_naive = time.time() - start_time
        track_memory()  # Final memory usage
        
        metrics.update({
            "naive_time_seconds": elapsed_naive,
            "naive_peak_memory_mb": max(memory_usage_naive),
        })
        
        logger.info(f"Naive calculation completed in {elapsed_naive:.2f} seconds")
        logger.info(f"Naive calculation peak memory: {max(memory_usage_naive):.1f} MB")
    
    # Run chunked calculation with timing
    logger.info("Running memory-aware chunked similarity calculation")
    
    # Track memory during chunked calculation
    def track_chunked_memory():
        try:
            memory_usage_chunked.append(psutil.Process().memory_info().rss / (1024 * 1024))
        except Exception as e:
            logger.error(f"Error tracking memory: {e}")
    
    # Run with adaptive memory monitoring
    start_time = time.time()
    track_chunked_memory()  # Initial memory usage
    
    with memory_aware_processing() as processor:
        similarities_chunked = calculate_similarities_chunked(
            job_vectors, threshold, memory_limit_mb
        )
        # Track memory periodically
        track_chunked_memory()
    
    elapsed_chunked = time.time() - start_time
    track_chunked_memory()  # Final memory usage
    
    # Stop CPU monitoring
    cpu_monitoring['active'] = False
    time.sleep(2)  # Give the monitoring thread time to finish
    
    metrics.update({
        "chunked_time_seconds": elapsed_chunked,
        "chunked_peak_memory_mb": max(memory_usage_chunked),
        "chunked_final_memory_mb": memory_usage_chunked[-1],
    })
    
    logger.info(f"Chunked calculation completed in {elapsed_chunked:.2f} seconds")
    logger.info(f"Chunked calculation peak memory: {max(memory_usage_chunked):.1f} MB")
    
    # Create comparison plots
    if compare_naive and similarities_naive is not None:
        # Verify results match
        diff = np.abs(similarities_naive - similarities_chunked)
        max_diff = np.max(diff)
        avg_diff = np.mean(diff)
        
        logger.info(f"Verification - Max difference: {max_diff:.6f}, Average difference: {avg_diff:.6f}")
        
        metrics.update({
            "max_difference": float(max_diff),
            "avg_difference": float(avg_diff),
        })
        
        # Plot memory usage comparison
        plt.figure(figsize=(12, 6))
        plt.plot(memory_usage_naive, 'r-', label='Naive')
        plt.plot(memory_usage_chunked, 'g-', label='Chunked')
        plt.title(f"Memory Usage Comparison ({num_jobs} jobs)")
        plt.xlabel("Time Steps")
        plt.ylabel("Memory Usage (MB)")
        plt.legend()
        plt.grid(True)
        plt.savefig("memory_comparison.png")
        logger.info("Memory comparison plot saved to memory_comparison.png")
    else:
        # Just plot chunked memory usage
        plot_memory_usage(
            memory_usage_chunked,
            f"Memory Usage - Chunked Processing ({num_jobs} jobs)",
            "memory_chunked.png"
        )
    
    # Plot CPU usage
    plot_cpu_usage(
        cpu_data,
        f"CPU Utilization During Similarity Calculation ({num_jobs} jobs)",
        "cpu_usage.png"
    )
    
    # Add CPU metrics to the results
    if cpu_data['average']:
        metrics.update({
            "avg_cpu_usage": np.mean(cpu_data['average']),
            "max_cpu_usage": np.max(cpu_data['average']),
            "cpu_usage_by_phase": {
                "data_generation": np.mean(cpu_data['average'][:5]) if len(cpu_data['average']) > 5 else 0,
                "calculation": np.mean(cpu_data['average'][5:]) if len(cpu_data['average']) > 5 else 0
            }
        })
    
    return similarities_chunked, metrics

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Adaptive Similarity Calculation Demo")
    
    parser.add_argument(
        "--num-jobs", type=int, default=DEFAULT_NUM_JOBS,
        help=f"Number of jobs to generate (default: {DEFAULT_NUM_JOBS})"
    )
    parser.add_argument(
        "--num-skills", type=int, default=DEFAULT_NUM_SKILLS,
        help=f"Number of skills in the taxonomy (default: {DEFAULT_NUM_SKILLS})"
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
        "--compare-naive", action="store_true",
        help="Also run naive calculation for comparison (only for small datasets)"
    )
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    
    try:
        # Run the demo
        similarity_matrix, metrics = memory_efficient_similarity_demo(
            num_jobs=args.num_jobs,
            num_skills=args.num_skills,
            threshold=args.threshold,
            memory_limit_mb=args.memory_limit,
            compare_naive=args.compare_naive
        )
        
        # Print summary
        logger.info("=== Performance Summary ===")
        for key, value in metrics.items():
            if key != "cpu_usage_by_phase":  # Skip nested dictionary for console output
                logger.info(f"{key}: {value}")
        
        # Print CPU usage summary
        if "cpu_usage_by_phase" in metrics:
            logger.info("=== CPU Usage by Phase ===")
            for phase, usage in metrics["cpu_usage_by_phase"].items():
                logger.info(f"{phase}: {usage:.1f}%")
        
        logger.info(f"Matrix shape: {similarity_matrix.shape}")
        logger.info(f"Non-zero elements: {np.count_nonzero(similarity_matrix)}")
        logger.info(f"Sparsity: {1.0 - np.count_nonzero(similarity_matrix) / similarity_matrix.size:.4f}")
        
        logger.info("Demo completed successfully")
    
    except Exception as e:
        logger.exception(f"Error in similarity demo: {e}")
        sys.exit(1) 