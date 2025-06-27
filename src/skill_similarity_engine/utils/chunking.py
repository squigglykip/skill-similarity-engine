"""
Adaptive Chunking Utilities

This module provides utilities for breaking large datasets into manageable chunks
with adaptive sizing based on memory usage. These utilities are essential for
processing large datasets (35,000+ jobs) on standard hardware with memory constraints.
"""

import gc
import logging
import psutil
import heapq
from typing import List, Tuple, Any, Callable, TypeVar, Generic, Iterator, Optional
from dataclasses import dataclass
import time
import os
import json

from .performance import get_memory_usage, trigger_garbage_collection

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class ChunkingStrategy:
    """Configuration for adaptive chunking behavior"""
    initial_chunk_size: int
    min_chunk_size: int
    max_chunk_size: int
    growth_factor: float = 1.5
    shrink_factor: float = 0.5
    memory_threshold_percent: float = 80.0
    target_memory_percent: float = 70.0
    
    def __post_init__(self):
        """Validate the strategy parameters"""
        if self.min_chunk_size <= 0:
            raise ValueError("min_chunk_size must be positive")
        if self.max_chunk_size < self.min_chunk_size:
            raise ValueError("max_chunk_size must be >= min_chunk_size")
        if self.initial_chunk_size < self.min_chunk_size or self.initial_chunk_size > self.max_chunk_size:
            raise ValueError("initial_chunk_size must be between min_chunk_size and max_chunk_size")

class AdaptiveChunker(Generic[T]):
    """
    Handles adaptive chunking of large datasets based on memory usage.
    
    This class monitors memory consumption during processing and
    adjusts chunk sizes dynamically to optimize performance while
    preventing out-of-memory conditions.
    """
    
    def __init__(self, 
                 data: List[T], 
                 strategy: Optional[ChunkingStrategy] = None):
        """
        Initialize the chunker with data and optional strategy.
        
        Args:
            data: The data to chunk
            strategy: Chunking strategy configuration
        """
        self.data = data
        self.strategy = strategy or ChunkingStrategy(
            initial_chunk_size=1000,
            min_chunk_size=100,
            max_chunk_size=10000,
            memory_threshold_percent=80.0
        )
        self.current_chunk_size = self.strategy.initial_chunk_size
        logger.info(f"Initialized AdaptiveChunker with {len(data)} items, "
                   f"initial chunk size: {self.current_chunk_size}")
        
    def chunks(self) -> Iterator[List[T]]:
        """
        Generate chunks of data with adaptive sizing.
        
        Yields:
            Chunks of data with size adjusted based on memory usage
        """
        data_len = len(self.data)
        start_idx = 0
        chunk_num = 0
        
        while start_idx < data_len:
            # Determine end index for current chunk
            end_idx = min(start_idx + self.current_chunk_size, data_len)
            
            # Yield the current chunk
            current_chunk = self.data[start_idx:end_idx]
            chunk_num += 1
            logger.debug(f"Yielding chunk {chunk_num}: items {start_idx}-{end_idx} "
                        f"(size: {len(current_chunk)})")
            yield current_chunk
            
            # Check memory usage after processing
            memory_usage = get_memory_usage()
            memory_percent = (memory_usage.current_process_usage / 
                             (psutil.virtual_memory().total * 0.9)) * 100
            
            # Adjust chunk size based on memory usage
            prev_chunk_size = self.current_chunk_size
            if memory_percent > self.strategy.memory_threshold_percent:
                # Memory pressure is high, reduce chunk size
                self.current_chunk_size = max(
                    int(self.current_chunk_size * self.strategy.shrink_factor),
                    self.strategy.min_chunk_size
                )
                # Force garbage collection to free memory
                trigger_garbage_collection(full=True)
                logger.info(f"Memory pressure detected ({memory_percent:.1f}%), "
                           f"reducing chunk size: {prev_chunk_size} â†’ {self.current_chunk_size}")
            elif memory_percent < self.strategy.target_memory_percent:
                # Memory usage is low, increase chunk size
                self.current_chunk_size = min(
                    int(self.current_chunk_size * self.strategy.growth_factor),
                    self.strategy.max_chunk_size
                )
                if self.current_chunk_size > prev_chunk_size:
                    logger.debug(f"Memory usage low ({memory_percent:.1f}%), "
                               f"increasing chunk size: {prev_chunk_size} â†’ {self.current_chunk_size}")
            
            # Move to next chunk
            start_idx = end_idx

class IndexChunker:
    """
    Generates chunks of indices for processing large arrays or matrices.
    
    This is useful when the actual data is too large to copy or when
    you need to process specific ranges of indices.
    """
    
    def __init__(self, 
                 size: int,
                 strategy: Optional[ChunkingStrategy] = None):
        """
        Initialize the index chunker.
        
        Args:
            size: Total number of indices to chunk
            strategy: Chunking strategy configuration
        """
        self.size = size
        self.strategy = strategy or ChunkingStrategy(
            initial_chunk_size=1000,
            min_chunk_size=100,
            max_chunk_size=10000,
            memory_threshold_percent=80.0
        )
        self.current_chunk_size = self.strategy.initial_chunk_size
        
    def index_chunks(self) -> Iterator[Tuple[int, int]]:
        """
        Generate chunks of indices as (start, end) tuples.
        
        Yields:
            Tuples of (start_idx, end_idx) with end_idx exclusive
        """
        start_idx = 0
        chunk_num = 0
        
        while start_idx < self.size:
            # Determine end index for current chunk
            end_idx = min(start_idx + self.current_chunk_size, self.size)
            
            # Yield the index range
            chunk_num += 1
            logger.debug(f"Yielding index chunk {chunk_num}: {start_idx}-{end_idx} "
                        f"(size: {end_idx - start_idx})")
            yield start_idx, end_idx
            
            # Check memory usage after processing
            memory_usage = get_memory_usage()
            memory_percent = (memory_usage.current_process_usage / 
                             (psutil.virtual_memory().total * 0.9)) * 100
            
            # Adjust chunk size based on memory usage
            prev_chunk_size = self.current_chunk_size
            if memory_percent > self.strategy.memory_threshold_percent:
                # Memory pressure is high, reduce chunk size
                self.current_chunk_size = max(
                    int(self.current_chunk_size * self.strategy.shrink_factor),
                    self.strategy.min_chunk_size
                )
                # Force garbage collection to free memory
                trigger_garbage_collection(full=True)
                logger.info(f"Memory pressure detected ({memory_percent:.1f}%), "
                           f"reducing chunk size: {prev_chunk_size} â†’ {self.current_chunk_size}")
            elif memory_percent < self.strategy.target_memory_percent:
                # Memory usage is low, increase chunk size
                self.current_chunk_size = min(
                    int(self.current_chunk_size * self.strategy.growth_factor),
                    self.strategy.max_chunk_size
                )
                if self.current_chunk_size > prev_chunk_size:
                    logger.debug(f"Memory usage low ({memory_percent:.1f}%), "
                               f"increasing chunk size: {prev_chunk_size} â†’ {self.current_chunk_size}")
            
            # Move to next chunk
            start_idx = end_idx

def chunk_by_memory(data_size: int, 
                   item_size_bytes: float,
                   target_chunk_memory_mb: float = 500.0,
                   min_chunk_size: int = 100) -> int:
    """
    Calculate an appropriate chunk size based on estimated memory usage.
    
    Args:
        data_size: Total number of items in the dataset
        item_size_bytes: Estimated memory size per item in bytes
        target_chunk_memory_mb: Target memory usage per chunk in MB
        min_chunk_size: Minimum chunk size to return
        
    Returns:
        Recommended chunk size
    """
    # Convert target memory to bytes
    target_bytes = target_chunk_memory_mb * 1024 * 1024
    
    # Calculate chunk size
    chunk_size = int(target_bytes / item_size_bytes)
    
    # Apply constraints
    chunk_size = max(chunk_size, min_chunk_size)
    chunk_size = min(chunk_size, data_size)
    
    logger.info(f"Calculated chunk size: {chunk_size} items "
               f"(estimated {(chunk_size * item_size_bytes) / (1024 * 1024):.1f} MB per chunk)")
    
    return chunk_size 

class StreamingChunkProcessor:
    """
    Processes data in a streaming/batched fashion, applying a processing function to each chunk.
    Useful for large datasets where results should be yielded incrementally to avoid high memory usage.
    """
    def __init__(self, 
                 chunker: Any, 
                 process_fn: Callable[[Any], Any],
                 progress_callback: Optional[Callable[[int], None]] = None):
        """
        Args:
            chunker: An object with a chunk-yielding method (e.g., AdaptiveChunker, IndexChunker)
            process_fn: Function to apply to each chunk (should accept a chunk and return a result)
            progress_callback: Optional function called after each chunk is processed (receives chunk index)
        """
        self.chunker = chunker
        self.process_fn = process_fn
        self.progress_callback = progress_callback

    def process(self) -> Iterator[Any]:
        """
        Process all chunks, yielding results for each chunk.
        Yields:
            The result of process_fn for each chunk
        """
        for idx, chunk in enumerate(self.chunker.chunks() if hasattr(self.chunker, 'chunks') else self.chunker.index_chunks()):
            result = self.process_fn(chunk)
            if self.progress_callback:
                self.progress_callback(idx)
            yield result 

class BatchQueueManager:
    """
    Manages a queue of data batches, ensuring memory constraints are respected.
    Supports memory-aware FIFO or priority-based batch scheduling.
    """
    def __init__(self, 
                 batch_generator: Iterator[Any],
                 max_memory_mb: float = 1000.0,
                 estimate_batch_size_fn: Optional[Callable[[Any], float]] = None,
                 use_priority: bool = False):
        """
        Args:
            batch_generator: Iterator yielding batches to process
            max_memory_mb: Maximum memory (in MB) allowed for batches in memory
            estimate_batch_size_fn: Optional function to estimate batch size in MB (receives a batch)
            use_priority: If True, enable priority-based scheduling (batches must be (priority, batch) tuples)
        """
        self.batch_generator = batch_generator
        self.max_memory_mb = max_memory_mb
        self.estimate_batch_size_fn = estimate_batch_size_fn or (lambda batch: 1.0)  # Default: 1MB per batch
        self.use_priority = use_priority
        self.queue = []  # List for FIFO or heap for priority
        self.current_memory_mb = 0.0
        self.finished = False

    def _can_accept_batch(self, batch: Any) -> bool:
        # If using priority, batch is (priority, batch_data)
        batch_data = batch[1] if self.use_priority else batch
        batch_size = self.estimate_batch_size_fn(batch_data)
        return (self.current_memory_mb + batch_size) <= self.max_memory_mb

    def fill_queue(self, max_batches: Optional[int] = None):
        """
        Fill the queue with as many batches as possible within memory constraints.
        Args:
            max_batches: Optional maximum number of batches to queue at once
        """
        while not self.finished and (max_batches is None or len(self.queue) < max_batches):
            try:
                batch = next(self.batch_generator)
            except StopIteration:
                self.finished = True
                break
            batch_data = batch[1] if self.use_priority else batch
            batch_size = self.estimate_batch_size_fn(batch_data)
            if (self.current_memory_mb + batch_size) > self.max_memory_mb:
                # Stop filling if memory would be exceeded
                break
            if self.use_priority:
                heapq.heappush(self.queue, batch)
            else:
                self.queue.append(batch)
            self.current_memory_mb += batch_size

    def get_next_batch(self) -> Optional[Any]:
        """
        Return the next batch from the queue, updating memory usage.
        Returns:
            The next batch, or None if the queue is empty.
        """
        if not self.queue:
            return None
        if self.use_priority:
            batch = heapq.heappop(self.queue)
            batch_data = batch[1]
        else:
            batch = self.queue.pop(0)
            batch_data = batch
        batch_size = self.estimate_batch_size_fn(batch_data)
        self.current_memory_mb -= batch_size
        return batch

    def has_more_batches(self) -> bool:
        """
        Returns True if there are more batches to process (in queue or generator).
        """
        return bool(self.queue) or not self.finished 

class BatchSizeBenchmark:
    """
    Utility to benchmark different batch sizes for a given processing function,
    recording processing time and memory usage for each batch size.
    """
    def __init__(self, data: list, process_fn: Callable[[list], Any], batch_sizes: list, estimate_batch_size_fn: Optional[Callable[[list], float]] = None):
        """
        Args:
            data: The full dataset to process
            process_fn: Function to apply to each batch (should accept a batch and return a result)
            batch_sizes: List of batch sizes to benchmark
            estimate_batch_size_fn: Optional function to estimate batch size in MB (receives a batch)
        """
        self.data = data
        self.process_fn = process_fn
        self.batch_sizes = batch_sizes
        self.estimate_batch_size_fn = estimate_batch_size_fn or (lambda b: 1.0)

    def run(self) -> list:
        """
        Run the benchmark for each batch size.
        Returns:
            List of dicts with batch size, average time per batch, and average memory usage per batch.
        """
        results = []
        for batch_size in self.batch_sizes:
            batches = [self.data[i:i+batch_size] for i in range(0, len(self.data), batch_size)]
            times = []
            mems = []
            for batch in batches:
                start_mem = get_memory_usage().current_process_usage_mb
                start_time = time.time()
                self.process_fn(batch)
                elapsed = time.time() - start_time
                end_mem = get_memory_usage().current_process_usage_mb
                times.append(elapsed)
                mems.append(end_mem - start_mem)
            avg_time = sum(times) / len(times)
            avg_mem = sum(mems) / len(mems)
            results.append({
                'batch_size': batch_size,
                'avg_time_per_batch': avg_time,
                'avg_mem_delta_per_batch': avg_mem,
                'num_batches': len(batches)
            })
        return results 

class ResumableBatchProcessor:
    """
    Processes batches with checkpointing, allowing processing to be resumed after interruption.
    Saves the index of the last completed batch to a checkpoint file after each batch.
    """
    def __init__(self, 
                 batches: list,
                 process_fn: Callable[[Any], Any],
                 checkpoint_path: str = "batch_checkpoint.json"):
        """
        Args:
            batches: List of batches to process
            process_fn: Function to apply to each batch
            checkpoint_path: Path to checkpoint file
        """
        self.batches = batches
        self.process_fn = process_fn
        self.checkpoint_path = checkpoint_path
        self.start_index = 0
        self._load_checkpoint()

    def _load_checkpoint(self):
        if os.path.exists(self.checkpoint_path):
            try:
                with open(self.checkpoint_path, "r") as f:
                    data = json.load(f)
                    self.start_index = data.get("last_completed", 0) + 1
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
                self.start_index = 0
        else:
            self.start_index = 0

    def _save_checkpoint(self, idx: int):
        try:
            with open(self.checkpoint_path, "w") as f:
                json.dump({"last_completed": idx}, f)
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")

    def process(self) -> list:
        """
        Process all batches, resuming from the last checkpoint if present.
        Returns:
            List of results for each batch (None for skipped batches if resuming)
        """
        results = [None] * len(self.batches)
        for idx in range(self.start_index, len(self.batches)):
            batch = self.batches[idx]
            result = self.process_fn(batch)
            results[idx] = result
            self._save_checkpoint(idx)
        return results

    def clear_checkpoint(self):
        if os.path.exists(self.checkpoint_path):
            os.remove(self.checkpoint_path) 
