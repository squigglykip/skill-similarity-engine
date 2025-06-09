"""
Precomputation Strategy for Similarity Matrix Generation

This module implements the chunked and parallelized generation of base job-to-job
similarity matrices using the sophisticated infrastructure from utils. It focuses
on generating unweighted skill similarity matrices that can be processed efficiently
on standard hardware (32GB laptops) for large datasets (35,000+ jobs).

The precomputed matrices contain only base skill similarity without context modifiers
(seniority, role track, location), which are applied dynamically at query time.
"""

import logging
import time
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Iterator, Any
from dataclasses import dataclass
import pandas as pd
import numpy as np

from ..models.jobs import JobArchitecture
from ..utils.chunking import AdaptiveChunker, ChunkingStrategy
from ..utils.parallel import ParallelProcessor
from ..utils.matrix_chunking import SimilarityMatrixChunker, MatrixChunk
from ..utils.performance import get_memory_usage, trigger_garbage_collection
from ..error_handling.core import EngineError
from .asymmetric import AsymmetricCoverageCalculator

logger = logging.getLogger(__name__)

@dataclass
class PrecomputeConfig:
    """Configuration for precomputation strategy"""
    initial_chunk_size: int = 1000
    min_chunk_size: int = 100
    max_chunk_size: int = 5000
    memory_threshold_percent: float = 80.0
    target_memory_percent: float = 70.0
    max_workers: Optional[int] = None
    memory_limit_mb: Optional[int] = None
    enable_checkpointing: bool = True
    checkpoint_interval: int = 10  # Save checkpoint every N chunks
    output_dir: str = "data/precomputed"


class SimpleProgressTracker:
    """Simple progress tracking for precomputation"""
    
    def __init__(self, output_file: Path):
        self.output_file = output_file
        self.start_time = time.time()
    
    def record_progress(self, items_processed: int, total_items: int, 
                       current_item: str, memory_usage_mb: float):
        """Record progress to file"""
        progress_data = {
            'timestamp': time.time(),
            'elapsed_time': time.time() - self.start_time,
            'items_processed': items_processed,
            'total_items': total_items,
            'current_item': current_item,
            'memory_usage_mb': memory_usage_mb,
            'progress_percent': (items_processed / total_items * 100) if total_items > 0 else 0
        }
        
        # Write JSON with explicit file mode
        with open(str(self.output_file), 'w') as f:
            json.dump(progress_data, f)
    
    def record_completion(self):
        """Record completion"""
        completion_data = {
            'timestamp': time.time(),
            'elapsed_time': time.time() - self.start_time,
            'status': 'completed'
        }
        
        # Write JSON with explicit file mode
        with open(str(self.output_file), 'w') as f:
            json.dump(completion_data, f)


class SimpleCheckpointManager:
    """Simple checkpoint manager for precomputation"""
    
    def __init__(self, checkpoint_file: Path):
        self.checkpoint_file = checkpoint_file
    
    def save_checkpoint(self, data: Dict[str, Any]):
        """Save checkpoint data"""
        checkpoint_data = {
            'timestamp': time.time(),
        }
        checkpoint_data.update(data)
        
        # Write JSON with explicit file mode
        with open(str(self.checkpoint_file), 'w') as f:
            json.dump(checkpoint_data, f)
    
    def load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Load checkpoint data"""
        if not self.checkpoint_file.exists():
            return None
        
        with open(str(self.checkpoint_file), 'r') as f:
            return json.load(f)


class SimilarityMatrixPrecomputer:
    """
    Handles chunked and parallelized precomputation of job-to-job similarity matrices.
    
    This class uses the sophisticated chunking and parallel processing infrastructure
    to efficiently generate base similarity matrices for large datasets while
    respecting memory constraints on standard hardware.
    """
    
    def __init__(self,
                 job_architecture: JobArchitecture,
                 calculator: AsymmetricCoverageCalculator,
                 config: Optional[PrecomputeConfig] = None):
        """
        Initialize the precomputer.
        
        Args:
            job_architecture: Job architecture containing all jobs
            calculator: Asymmetric coverage calculator for similarity computation
            config: Configuration for precomputation strategy
        """
        self.job_architecture = job_architecture
        self.calculator = calculator
        self.config = config or PrecomputeConfig()
        
        # Get list of job IDs for processing
        self.job_ids = list(job_architecture.jobs.keys())
        self.num_jobs = len(self.job_ids)
        
        # Setup chunking strategy
        self.chunking_strategy = ChunkingStrategy(
            initial_chunk_size=self.config.initial_chunk_size,
            min_chunk_size=self.config.min_chunk_size,
            max_chunk_size=self.config.max_chunk_size,
            memory_threshold_percent=self.config.memory_threshold_percent,
            target_memory_percent=self.config.target_memory_percent
        )
        
        # Setup matrix chunker for similarity matrix generation
        self.matrix_chunker = SimilarityMatrixChunker(
            num_items=self.num_jobs,
            strategy=self.chunking_strategy,
            symmetric=False  # Asymmetric coverage matrix
        )
        
        # Setup parallel processor
        self.parallel_processor = ParallelProcessor(
            max_workers=self.config.max_workers,
            memory_limit_mb=self.config.memory_limit_mb
        )
        
        # Setup progress tracking and checkpointing
        self.progress_tracker = None
        self.checkpoint_manager = None
        
        logger.info(f"Initialized SimilarityMatrixPrecomputer for {self.num_jobs} jobs")
        logger.info(f"Estimated chunks: {self.matrix_chunker.estimate_num_chunks()}")
        logger.info(f"Estimated memory per chunk: {self.matrix_chunker.estimate_memory_requirements():.2f} MB")
    
    def _setup_output_directory(self, run_name: Optional[str] = None) -> Path:
        """Setup output directory for this precomputation run"""
        if run_name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            run_name = f"precompute_{timestamp}"
        
        output_path = Path(self.config.output_dir) / run_name
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Setup progress and checkpoint tracking
        if self.config.enable_checkpointing:
            self.progress_tracker = SimpleProgressTracker(
                output_file=output_path / "progress.json"
            )
            self.checkpoint_manager = SimpleCheckpointManager(
                checkpoint_file=output_path / "checkpoint.json"
            )
        
        return output_path
    
    def _process_chunk(self, chunk: MatrixChunk) -> pd.DataFrame:
        """
        Process a single matrix chunk to calculate similarities.
        
        Args:
            chunk: Matrix chunk defining the region to process
            
        Returns:
            DataFrame with job_from, job_to, similarity columns
        """
        results = []
        
        # Get job ID ranges for this chunk
        job_from_ids = self.job_ids[chunk.row_start:chunk.row_end]
        job_to_ids = self.job_ids[chunk.col_start:chunk.col_end]
        
        # Calculate similarities for all pairs in this chunk
        for i, job_from in enumerate(job_from_ids):
            for j, job_to in enumerate(job_to_ids):
                # Skip self-comparisons
                if job_from == job_to:
                    continue
                
                # Calculate base similarity (unweighted skill coverage)
                similarity = self.calculator.calculate_job_coverage(job_from, job_to)
                
                results.append({
                    'job_from': job_from,
                    'job_to': job_to,
                    'similarity': similarity
                })
        
        return pd.DataFrame(results)
    
    def _save_chunk_results(self, chunk_results: List[pd.DataFrame], output_path: Path) -> None:
        """
        Save chunk results to the final output file.
        
        Args:
            chunk_results: List of DataFrames from chunk processing
            output_path: Output directory path
        """
        logger.info("Combining and saving chunk results...")
        
        # Combine all chunk results
        if chunk_results:
            final_df = pd.concat(chunk_results, ignore_index=True)
        else:
            # Create empty DataFrame with correct structure
            final_df = pd.DataFrame(columns=['job_from', 'job_to', 'similarity'])
        
        # Sort by job_from, then job_to for consistency
        final_df = final_df.sort_values(['job_from', 'job_to']).reset_index(drop=True)
        
        # Save to CSV
        output_file = output_path / "job_similarity_matrix.csv"
        final_df.to_csv(output_file, index=False)
        
        logger.info(f"Saved similarity matrix to {output_file}")
        logger.info(f"Matrix shape: {final_df.shape}")
        logger.info(f"Total job pairs: {len(final_df):,}")
    
    def precompute_similarity_matrix(self, run_name: Optional[str] = None) -> Path:
        """
        Precompute the full job-to-job similarity matrix using chunked processing.
        
        Args:
            run_name: Optional name for this precomputation run
            
        Returns:
            Path to the output directory containing results
        """
        logger.info("Starting similarity matrix precomputation...")
        
        # Setup output directory
        output_path = self._setup_output_directory(run_name)
        logger.info(f"Output directory: {output_path}")
        
        # Track overall progress and memory
        chunk_results = []
        chunk_count = 0
        total_chunks = self.matrix_chunker.estimate_num_chunks()
        
        try:
            # Process chunks
            for chunk in self.matrix_chunker.matrix_chunks():
                chunk_count += 1
                
                logger.info(f"Processing chunk {chunk_count}/{total_chunks}: {chunk}")
                
                # Record progress
                if self.progress_tracker:
                    self.progress_tracker.record_progress(
                        items_processed=chunk_count,
                        total_items=total_chunks,
                        current_item=f"Chunk {chunk_count}",
                        memory_usage_mb=get_memory_usage().current_process_usage_mb
                    )
                
                # Process the chunk
                start_time = time.time()
                chunk_df = self._process_chunk(chunk)
                chunk_duration = time.time() - start_time
                
                logger.debug(f"Chunk {chunk_count} processed in {chunk_duration:.2f}s, "
                           f"generated {len(chunk_df)} comparisons")
                
                chunk_results.append(chunk_df)
                
                # Checkpoint periodically
                if (self.config.enable_checkpointing and 
                    self.checkpoint_manager and 
                    chunk_count % self.config.checkpoint_interval == 0):
                    
                    checkpoint_data = {
                        'chunk_count': chunk_count,
                        'total_chunks': total_chunks,
                        'chunks_completed': chunk_count,
                        'output_path': str(output_path)
                    }
                    self.checkpoint_manager.save_checkpoint(checkpoint_data)
                    logger.info(f"Checkpoint saved at chunk {chunk_count}")
                
                # Trigger garbage collection to manage memory
                if chunk_count % 5 == 0:  # Every 5 chunks
                    trigger_garbage_collection(full=True)
            
            # Save final results
            self._save_chunk_results(chunk_results, output_path)
            
            # Final progress update
            if self.progress_tracker:
                self.progress_tracker.record_completion()
            
            logger.info("Similarity matrix precomputation completed successfully!")
            return output_path
            
        except Exception as e:
            logger.error(f"Error during precomputation: {e}")
            # Save partial results if any were generated
            if chunk_results:
                logger.info("Saving partial results...")
                self._save_chunk_results(chunk_results, output_path)
            raise EngineError(f"Precomputation failed: {e}") from e
    
    def estimate_runtime(self) -> Dict[str, Any]:
        """
        Estimate the runtime and resource requirements for precomputation.
        
        Returns:
            Dictionary with runtime estimates and resource requirements
        """
        # Estimate based on a small sample
        sample_size = min(100, self.num_jobs)
        sample_job_ids = self.job_ids[:sample_size]
        
        logger.info(f"Estimating runtime based on {sample_size} job sample...")
        
        start_time = time.time()
        sample_count = 0
        
        for i, job_from in enumerate(sample_job_ids):
            for j, job_to in enumerate(sample_job_ids):
                if job_from == job_to:
                    continue
                _ = self.calculator.calculate_job_coverage(job_from, job_to)
                sample_count += 1
                
                if sample_count >= 1000:  # Stop after 1000 comparisons
                    break
            if sample_count >= 1000:
                break
        
        sample_duration = time.time() - start_time
        avg_time_per_comparison = sample_duration / sample_count if sample_count > 0 else 0
        
        # Estimate total comparisons (N * (N-1) for asymmetric)
        total_comparisons = self.num_jobs * (self.num_jobs - 1)
        estimated_total_time = total_comparisons * avg_time_per_comparison
        
        # Estimate with parallel processing
        num_workers = self.parallel_processor.max_workers
        estimated_parallel_time = estimated_total_time / num_workers if num_workers > 0 else estimated_total_time
        
        # Estimate memory requirements
        estimated_memory_mb = self.matrix_chunker.estimate_memory_requirements()
        
        return {
            'total_jobs': self.num_jobs,
            'total_comparisons': total_comparisons,
            'sample_comparisons': sample_count,
            'avg_time_per_comparison_ms': avg_time_per_comparison * 1000,
            'estimated_serial_time_hours': estimated_total_time / 3600,
            'estimated_parallel_time_hours': estimated_parallel_time / 3600,
            'estimated_chunks': self.matrix_chunker.estimate_num_chunks(),
            'estimated_memory_per_chunk_mb': estimated_memory_mb,
            'parallel_workers': num_workers,
        }


def create_precomputer(job_architecture: JobArchitecture, 
                      config: Optional[PrecomputeConfig] = None) -> SimilarityMatrixPrecomputer:
    """
    Factory function to create a configured precomputer.
    
    Args:
        job_architecture: Job architecture containing all jobs
        config: Optional configuration for precomputation
        
    Returns:
        Configured SimilarityMatrixPrecomputer instance
    """
    # Create simplified calculator (no weights, no context modifiers)
    calculator = AsymmetricCoverageCalculator(
        job_architecture=job_architecture
    )
    
    return SimilarityMatrixPrecomputer(
        job_architecture=job_architecture,
        calculator=calculator,
        config=config
    ) 