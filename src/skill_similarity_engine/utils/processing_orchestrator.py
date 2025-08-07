"""
Processing Orchestrator

This module provides centralized orchestration of processing tasks that combine
similarity calculations with intelligent chunking, progress tracking, and 
parallelization. This separates core algorithm logic (in similarity/) from 
processing strategy concerns (in utils/).

Key Features:
- Intelligent processing strategy selection (chunked vs. item-by-item)
- Memory-aware adaptive chunking
- Parallel processing coordination
- Advanced progress tracking with ETA and memory monitoring
- Unified interface for different similarity calculation types

Usage:
    from skill_similarity_engine.utils.processing_orchestrator import SimilarityProcessingOrchestrator
    
    orchestrator = SimilarityProcessingOrchestrator()
    
    # Process with intelligent strategy selection
    results = orchestrator.process_job_similarities(
        calculator=rarity_weighted_calculator,
        job_pairs=job_pairs,
        job_to_skills=job_to_skills,
        job_defining_skills=job_defining_skills
    )
"""

import logging
from typing import Dict, Set, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass

from .progress import progress_context
from .parallel import ParallelProcessor, create_cpu_tracked_processor, benchmark_parallel_vs_sequential
from .chunking import AdaptiveChunker, ChunkingStrategy

logger = logging.getLogger(__name__)


def _benchmark_similarity_calculation(pair_and_data: Tuple[Tuple[str, str], Any, Dict, Dict]) -> Dict[str, Any]:
    """
    Module-level function for benchmarking similarity calculations.
    Required at module level for multiprocessing pickle compatibility.
    """
    pair, calculator, job_to_skills, job_defining_skills = pair_and_data
    job_a_id, job_b_id = pair
    return calculator.calculate_single_similarity(
        job_a_id, job_b_id, job_to_skills, job_defining_skills
    )


@dataclass
class ProcessingConfig:
    """Configuration for processing orchestration"""
    # Memory thresholds
    memory_threshold_mb: float = 1000.0
    item_size_estimate_bytes: float = 300.0
    
    # Chunking strategy
    target_chunk_count: int = 20
    min_chunk_size: int = 5000
    max_chunk_size: int = 50000
    
    # Parallel processing
    max_workers: Optional[int] = None
    enable_parallel: bool = False  # Conservative default
    
    # Progress tracking
    progress_desc: str = "Processing"
    show_memory_tracking: bool = True


class SimilarityProcessingOrchestrator:
    """
    Orchestrates similarity processing with intelligent strategy selection.
    
    This class handles the coordination between similarity algorithms and
    processing utilities (chunking, progress, parallelization) while keeping
    the similarity modules focused on their core algorithms.
    """
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        """
        Initialize the processing orchestrator.
        
        Args:
            config: Processing configuration, uses defaults if None
        """
        self.config = config or ProcessingConfig()
        self.logger = logging.getLogger(__name__)
    
    def process_job_similarities(self,
                               calculator: Any,
                               job_pairs: List[Tuple[str, str]],
                               job_to_skills: Dict[str, Set[str]],
                               job_defining_skills: Dict[str, Set[str]],
                               use_intelligent_processing: bool = True) -> List[Dict[str, Any]]:
        """
        Process job similarity calculations with intelligent strategy selection.
        
        Args:
            calculator: Similarity calculator instance with calculate_single_similarity method
            job_pairs: List of (job_a_id, job_b_id) tuples to process
            job_to_skills: Dict mapping job ID to set of skill names
            job_defining_skills: Dict mapping job ID to set of defining skill names
            use_intelligent_processing: Whether to use intelligent processing strategies
            
        Returns:
            List of similarity records
        """
        total_pairs = len(job_pairs)
        # Removed verbose logging - parent will handle user messaging
        
        # Create a processing function that the orchestrator can call
        def process_single_pair(pair: Tuple[str, str]) -> Dict[str, Any]:
            job_a_id, job_b_id = pair
            return calculator.calculate_single_similarity(
                job_a_id, job_b_id, job_to_skills, job_defining_skills
            )
        
        if use_intelligent_processing:
            return self._process_with_intelligent_strategy(job_pairs, process_single_pair)
        else:
            return self._process_simple(job_pairs, process_single_pair)
    
    def _process_with_intelligent_strategy(self,
                                         job_pairs: List[Tuple[str, str]],
                                         process_func: Callable[[Tuple[str, str]], Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process using intelligent strategy selection (chunking, memory-aware, etc.)
        """
        # Removed verbose processing details - parent will handle user messaging
        
        results = []
        
        # Use progress context for tracking only - handle processing ourselves
        with progress_context(
            total=len(job_pairs),
            desc=self.config.progress_desc,
            memory_tracking=self.config.show_memory_tracking,
            show_tqdm=True
        ) as progress:
            for pair in job_pairs:
                result = process_func(pair)
                results.append(result)
                progress.update(1)
        
        # Removed verbose completion logging - parent will handle user messaging
        return results
    
    def _process_simple(self,
                       job_pairs: List[Tuple[str, str]],
                       process_func: Callable[[Tuple[str, str]], Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process using simple sequential approach with basic progress tracking
        """
        from .progress import progress_context
        
        results = []
        
        with progress_context(
            total=len(job_pairs),
            desc=self.config.progress_desc,
            memory_tracking=self.config.show_memory_tracking,
            show_tqdm=True
        ) as progress:
            for i, pair in enumerate(job_pairs):
                result = process_func(pair)
                results.append(result)
                
                # Update progress periodically
                if i % 1000 == 0:
                    progress.update(1000)
            
            # Update remaining progress
            remaining = len(job_pairs) % 1000
            if remaining > 0:
                progress.update(remaining)
        
        self.logger.info(f"Simple processing completed: {len(results):,} results")
        return results
    
    def process_with_chunking(self,
                            job_pairs: List[Tuple[str, str]],
                            process_func: Callable[[List[Tuple[str, str]]], List[Dict[str, Any]]],
                            chunk_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Process using explicit chunking strategy.
        
        Args:
            job_pairs: List of job pairs to process
            process_func: Function that processes a chunk of pairs and returns results
            chunk_size: Explicit chunk size, calculated automatically if None
            
        Returns:
            List of similarity records
        """
        if chunk_size is None:
            chunk_size = self.config.min_chunk_size
        
        # Create chunking strategy
        chunking_strategy = ChunkingStrategy(
            initial_chunk_size=chunk_size,
            min_chunk_size=self.config.min_chunk_size,
            max_chunk_size=self.config.max_chunk_size,
            memory_threshold_percent=80.0
        )
        
        # Use adaptive chunker
        chunker = AdaptiveChunker(job_pairs, chunking_strategy)
        
        all_results = []
        chunk_num = 0
        
        self.logger.info(f"Processing with explicit chunking (chunk size: {chunk_size})")
        
        for chunk in chunker.chunks():
            chunk_num += 1
            self.logger.info(f"Processing chunk {chunk_num} with {len(chunk)} pairs")
            
            chunk_results = process_func(chunk)
            all_results.extend(chunk_results)
        
        self.logger.info(f"Chunked processing completed: {len(all_results):,} results from {chunk_num} chunks")
        return all_results
    
    def process_with_parallel(self,
                            job_pairs: List[Tuple[str, str]],
                            process_func: Callable[[Tuple[str, str]], Dict[str, Any]],
                            max_workers: Optional[int] = None,
                            enable_cpu_tracking: bool = True) -> List[Dict[str, Any]]:
        """
        Process using parallel processing with optional CPU tracking.
        
        Args:
            job_pairs: List of job pairs to process
            process_func: Function that processes a single pair
            max_workers: Maximum number of worker processes
            enable_cpu_tracking: Whether to enable CPU utilization tracking
            
        Returns:
            List of similarity records
        """
        if max_workers is None:
            max_workers = self.config.max_workers
        
        self.logger.info(f"Processing with parallel strategy (max_workers: {max_workers}, CPU tracking: {enable_cpu_tracking})")
        
        # Use CPU-tracked parallel processor if requested
        if enable_cpu_tracking:
            processor = create_cpu_tracked_processor(max_workers=max_workers)
        else:
            processor = ParallelProcessor(max_workers=max_workers)
        
        results = processor.map(process_func, job_pairs)
        
        # Log CPU performance if tracking was enabled
        if enable_cpu_tracking and hasattr(processor, '_last_performance_metrics'):
            metrics = processor._last_performance_metrics
            self.logger.info(f"CPU Performance Summary:")
            self.logger.info(f"  Peak CPU: {metrics.peak_cpu_utilization:.1f}%")
            self.logger.info(f"  Average CPU: {metrics.average_cpu_utilization:.1f}%")
            self.logger.info(f"  CPU Efficiency: {metrics.cpu_efficiency_score:.1f}%")
            self.logger.info(f"  Throughput: {metrics.tasks_per_second:.1f} tasks/sec")
        
        self.logger.info(f"Parallel processing completed: {len(results):,} results")
        return results
    
    def benchmark_processing_strategies(self,
                                      calculator: Any,
                                      job_pairs_sample: List[Tuple[str, str]],
                                      job_to_skills: Dict[str, Set[str]],
                                      job_defining_skills: Dict[str, Set[str]]) -> Dict[str, Any]:
        """
        Benchmark different processing strategies to find the most efficient approach.
        
        Args:
            calculator: Similarity calculator instance
            job_pairs_sample: Sample of job pairs for benchmarking
            job_to_skills: Job to skills mapping
            job_defining_skills: Job to defining skills mapping
            
        Returns:
            Dictionary with benchmark results and recommendations
        """
        self.logger.info(f"Benchmarking processing strategies with {len(job_pairs_sample)} job pairs")
        
        # Prepare data for module-level function (required for multiprocessing)
        job_pairs_with_data = [
            (pair, calculator, job_to_skills, job_defining_skills) 
            for pair in job_pairs_sample
        ]
        
        # Benchmark parallel vs sequential
        benchmark_results = benchmark_parallel_vs_sequential(
            _benchmark_similarity_calculation, job_pairs_with_data, max_workers=self.config.max_workers
        )
        
        # Add recommendations
        recommendations = []
        if benchmark_results['actual_speedup'] > 1.5:
            recommendations.append("✅ Parallel processing provides significant speedup")
        elif benchmark_results['actual_speedup'] > 1.1:
            recommendations.append("⚠️ Parallel processing provides modest speedup")
        else:
            recommendations.append("❌ Parallel processing not beneficial for this task")
        
        cpu_analysis = benchmark_results['cpu_analysis']
        if cpu_analysis.get('peak_cpu_percent', 0) > 80:
            recommendations.append("✅ Good CPU utilization achieved")
        else:
            recommendations.append("⚠️ Low CPU utilization - consider task optimization")
        
        benchmark_results['recommendations'] = recommendations
        
        self.logger.info(f"Benchmark completed: {benchmark_results['actual_speedup']:.2f}x speedup")
        for rec in recommendations:
            self.logger.info(f"  {rec}")
        
        return benchmark_results
    
    def estimate_processing_requirements(self, num_pairs: int) -> Dict[str, Any]:
        """
        Estimate processing requirements for the given number of pairs.
        
        Args:
            num_pairs: Number of job pairs to process
            
        Returns:
            Dictionary with estimates for memory, time, and strategy recommendations
        """
        estimated_memory_mb = (num_pairs * self.config.item_size_estimate_bytes) / (1024 * 1024)
        
        # Simple strategy: use chunking if estimated memory exceeds threshold
        should_chunk = estimated_memory_mb > self.config.memory_threshold_mb
        chunk_size = min(num_pairs, self.config.max_chunk_size) if should_chunk else num_pairs
        
        return {
            'num_pairs': num_pairs,
            'estimated_memory_mb': estimated_memory_mb,
            'should_use_chunking': should_chunk,
            'recommended_chunk_size': chunk_size,
            'estimated_chunks': (num_pairs + chunk_size - 1) // chunk_size if should_chunk else 1,
            'processing_strategy': 'chunked' if should_chunk else 'item_by_item',
            'memory_threshold_mb': self.config.memory_threshold_mb
        }


# Convenience function for common use case
def process_similarities_with_orchestrator(calculator: Any,
                                         job_pairs: List[Tuple[str, str]],
                                         job_to_skills: Dict[str, Set[str]],
                                         job_defining_skills: Dict[str, Set[str]],
                                         config: Optional[ProcessingConfig] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to process similarities with intelligent orchestration.
    
    Args:
        calculator: Similarity calculator with calculate_single_similarity method
        job_pairs: List of (job_a_id, job_b_id) tuples
        job_to_skills: Job to skills mapping
        job_defining_skills: Job to defining skills mapping
        config: Processing configuration
        
    Returns:
        List of similarity records
    """
    orchestrator = SimilarityProcessingOrchestrator(config)
    return orchestrator.process_job_similarities(
        calculator, job_pairs, job_to_skills, job_defining_skills
    )