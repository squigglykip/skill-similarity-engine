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
from ..utils.progress import ProgressTracker, progress_context
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
            datestamp = datetime.now().strftime('%Y%m%d')  # Date only, no time
            run_name = f"precompute_{datestamp}"
        
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
        total_chunks = self.matrix_chunker.estimate_num_chunks()
        
        try:
            # Use the full ProgressTracker with beautiful tqdm progress bars
            with ProgressTracker(
                total=total_chunks,
                desc="Processing similarity chunks",
                memory_tracking=True,
                show_tqdm=True
            ) as progress:
                
                chunk_count = 0
                
                # Process chunks
                for chunk in self.matrix_chunker.matrix_chunks():
                    chunk_count += 1
                    
                    logger.debug(f"Processing chunk {chunk_count}/{total_chunks}: {chunk}")
                    
                    # Process the chunk
                    start_time = time.time()
                    chunk_df = self._process_chunk(chunk)
                    chunk_duration = time.time() - start_time
                    
                    logger.debug(f"Chunk {chunk_count} processed in {chunk_duration:.2f}s, "
                               f"generated {len(chunk_df)} comparisons")
                    
                    chunk_results.append(chunk_df)
                    
                    # Update progress bar (with memory tracking)
                    progress.update(1)
                    
                    # Checkpoint periodically (also record legacy progress for file-based tracking)
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
                        
                        # Also record progress for file-based tracking
                        if self.progress_tracker:
                            self.progress_tracker.record_progress(
                                items_processed=chunk_count,
                                total_items=total_chunks,
                                current_item=f"Chunk {chunk_count}",
                                memory_usage_mb=get_memory_usage().current_process_usage_mb
                            )
                    
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
    
    def precompute_career_pathways(self, similarity_df: pd.DataFrame, output_path: Path) -> Path:
        """
        Precompute career pathways from similarity matrix using chunked processing.
        
        Args:
            similarity_df: DataFrame with job similarities (job_from, job_to, similarity)
            output_path: Output directory for saving results
            
        Returns:
            Path to the career pathways parquet file
        """
        logger.info("🚀 Starting career pathways precomputation...")
        
        # Configuration
        TOP_N_PATHWAYS = 24  # Top N most similar jobs per source job
        MIN_SIMILARITY_THRESHOLD = 0.01  # Minimum similarity to include (lowered from 0.15)
        
        # Get all unique job IDs and their families
        job_families = {job_id: getattr(job, 'job_family', 'Unknown') for job_id, job in self.job_architecture.jobs.items()}
        all_job_ids = list(job_families.keys())
        
        logger.info(f"📊 Generating pathways for {len(all_job_ids)} jobs (top {TOP_N_PATHWAYS} per job)")
        
        try:
            # Use chunking to process jobs in batches for memory efficiency
            from ..utils.chunking import AdaptiveChunker
            
            job_chunker = AdaptiveChunker(
                data=all_job_ids,
                strategy=self.chunking_strategy
            )
            
            pathway_records = []
            total_processed = 0
            
            # Process jobs in chunks
            with ProgressTracker(
                total=len(all_job_ids),
                desc="Generating career pathways",
                memory_tracking=True,
                show_tqdm=True
            ) as progress:
                
                for job_chunk in job_chunker.chunks():
                    chunk_pathways = []
                    
                    for source_job_id in job_chunk:
                        # Get similarities for this source job
                        job_similarities = similarity_df[
                            (similarity_df['job_from'] == source_job_id) &
                            (similarity_df['job_to'] != source_job_id) &
                            (similarity_df['similarity'] >= MIN_SIMILARITY_THRESHOLD)
                        ].copy()
                        
                        # Sort by similarity score and take top N
                        job_similarities = job_similarities.sort_values('similarity', ascending=False).head(TOP_N_PATHWAYS)
                        
                        # Generate pathway records with ranking and metadata
                        for rank, (_, row) in enumerate(job_similarities.iterrows(), 1):
                            target_job_id = row['job_to']
                            similarity_score = row['similarity']
                            
                            # Get job families
                            source_family = job_families.get(source_job_id, 'Unknown')
                            target_family = job_families.get(target_job_id, 'Unknown')
                            
                            # Determine career move type
                            if source_family == target_family:
                                if similarity_score >= 0.8:
                                    move_type = 'lateral'  # Very similar role in same family
                                else:
                                    move_type = 'progression'  # Different seniority/specialization
                            else:
                                move_type = 'cross_family'  # Career change to different family
                            
                            # Calculate difficulty score (inverse of similarity + cross-family penalty)
                            difficulty = 1.0 - similarity_score
                            if move_type == 'cross_family':
                                difficulty *= 1.2  # 20% penalty for cross-family moves
                            difficulty = min(1.0, difficulty)  # Cap at 1.0
                            
                            # Estimate shared skills count (simplified calculation)
                            shared_skills_count = int(similarity_score * 20)  # Approximate based on similarity
                            
                            pathway_record = {
                                'source_job_id': source_job_id,
                                'target_job_id': target_job_id,
                                'similarity_rank': rank,
                                'similarity_score': similarity_score,
                                'skill_overlap_score': similarity_score,  # Use same as similarity for now
                                'shared_skills_count': shared_skills_count,
                                'career_move_type': move_type,
                                'difficulty_score': difficulty
                            }
                            
                            chunk_pathways.append(pathway_record)
                        
                        total_processed += 1
                        progress.update(1)
                    
                    # Add chunk pathways to main list
                    pathway_records.extend(chunk_pathways)
                    
                    # Trigger garbage collection every few chunks
                    if len(pathway_records) % (self.config.initial_chunk_size * 5) == 0:
                        trigger_garbage_collection(full=True)
            
            # Convert to DataFrame with proper column structure
            if pathway_records:
                pathways_df = pd.DataFrame(pathway_records)
            else:
                # Create empty DataFrame with proper schema
                pathways_df = pd.DataFrame(columns=[
                    'source_job_id', 'target_job_id', 'similarity_rank', 'similarity_score',
                    'skill_overlap_score', 'shared_skills_count', 'career_move_type', 'difficulty_score'
                ])
            
            # Save as parquet file
            pathways_file = output_path / "career_pathways.parquet"
            pathways_df.to_parquet(pathways_file, compression='snappy', index=False)
            
            logger.info(f"✅ Career pathways saved to {pathways_file}")
            logger.info(f"📊 Generated {len(pathways_df):,} career pathway relationships")
            logger.info(f"📊 Average pathways per job: {len(pathways_df) / len(all_job_ids):.1f}")
            
            # Also save as CSV for compatibility
            csv_file = output_path / "career_pathways.csv"
            pathways_df.to_csv(csv_file, index=False)
            logger.info(f"✅ Career pathways CSV saved to {csv_file}")
            
            return pathways_file
            
        except Exception as e:
            logger.error(f"Error during career pathways precomputation: {e}")
            raise EngineError(f"Career pathways precomputation failed: {e}") from e
    
    def precompute_all(self, run_name: Optional[str] = None) -> Path:
        """
        Precompute both similarity matrix and career pathways.
        
        Args:
            run_name: Optional name for this precomputation run
            
        Returns:
            Path to the output directory containing both results
        """
        logger.info("🚀 Starting complete precomputation pipeline...")
        
        # Step 1: Precompute similarity matrix
        logger.info("📊 Step 1: Computing job-to-job similarity matrix...")
        output_path = self.precompute_similarity_matrix(run_name)
        
        # Step 2: Load similarity matrix and compute career pathways
        logger.info("🔗 Step 2: Computing career pathways from similarity matrix...")
        
        # Read the similarity matrix we just created
        similarity_file = output_path / "job_similarity_matrix.csv"
        if not similarity_file.exists():
            raise EngineError(f"Similarity matrix file not found: {similarity_file}")
        
        logger.info(f"📖 Loading similarity matrix from {similarity_file}")
        similarity_df = pd.read_csv(similarity_file)
        logger.info(f"📊 Loaded {len(similarity_df):,} similarity relationships")
        
        # Generate career pathways
        pathways_file = self.precompute_career_pathways(similarity_df, output_path)
        
        # Create metadata file with both outputs
        metadata = {
            'run_name': run_name or output_path.name,
            'timestamp': datetime.now().isoformat(),
            'total_jobs': self.num_jobs,
            'total_similarities': len(similarity_df),
            'outputs': {
                'similarity_matrix_csv': str(similarity_file),
                'career_pathways_parquet': str(pathways_file),
                'career_pathways_csv': str(output_path / "career_pathways.csv")
            },
            'configuration': {
                'chunk_size': self.config.initial_chunk_size,
                'memory_threshold': self.config.memory_threshold_percent,
                'checkpointing_enabled': self.config.enable_checkpointing
            }
        }
        
        metadata_file = output_path / "metadata.json"
        with open(str(metadata_file), 'w') as f:
            json.dump(metadata, f)
        
        logger.info("🎯 Complete precomputation pipeline finished successfully!")
        logger.info(f"📁 Output directory: {output_path}")
        logger.info(f"📊 Similarity matrix: {similarity_file}")
        logger.info(f"🔗 Career pathways: {pathways_file}")
        
        return output_path
    
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