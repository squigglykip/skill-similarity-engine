"""
Matrix Chunking Utilities

This module provides specialized chunking utilities for matrix operations,
particularly for similarity calculations between large sets of vectors.
These utilities are essential for handling the quadratic complexity of
pairwise comparisons (35,000+ jobs = 1.2+ billion comparisons) within
memory constraints.
"""

import logging
import numpy as np
from typing import Tuple, List, Iterator, Any, Optional
from dataclasses import dataclass

from .chunking import ChunkingStrategy
from .performance import get_memory_usage, trigger_garbage_collection

logger = logging.getLogger(__name__)

@dataclass
class MatrixChunk:
    """
    Represents a chunk of a similarity matrix calculation
    
    This defines a rectangular region of the matrix to be computed,
    from (row_start, col_start) to (row_end, col_end) exclusive.
    """
    row_start: int
    row_end: int
    col_start: int
    col_end: int
    priority: float = 1.0
    
    @property
    def shape(self) -> Tuple[int, int]:
        """Get the shape of this chunk as (rows, cols)"""
        return (self.row_end - self.row_start, self.col_end - self.col_start)
    
    @property
    def size(self) -> int:
        """Get the total number of elements in this chunk"""
        return (self.row_end - self.row_start) * (self.col_end - self.col_start)
    
    def __str__(self) -> str:
        """String representation of the chunk"""
        return f"MatrixChunk({self.row_start}:{self.row_end}, {self.col_start}:{self.col_end})"

class SimilarityMatrixChunker:
    """
    Handles chunked processing of similarity matrix calculations.
    
    This class divides the similarity matrix into manageable chunks
    that can be processed independently, with adaptive sizing based
    on memory constraints.
    """
    
    def __init__(self, 
                 num_items: int,
                 strategy: Optional[ChunkingStrategy] = None,
                 symmetric: bool = True):
        """
        Initialize the matrix chunker.
        
        Args:
            num_items: Number of items to compare (matrix size)
            strategy: Chunking strategy configuration
            symmetric: Whether the matrix is symmetric (e.g., job-job similarity)
        """
        self.num_items = num_items
        self.strategy = strategy or ChunkingStrategy(
            initial_chunk_size=1000,
            min_chunk_size=100,
            max_chunk_size=5000,
            memory_threshold_percent=80.0
        )
        self.symmetric = symmetric
        self.current_chunk_size = self.strategy.initial_chunk_size
        
        logger.info(f"Initialized SimilarityMatrixChunker for {num_items}x{num_items} matrix, "
                   f"initial chunk size: {self.current_chunk_size}, symmetric: {symmetric}")
        
    def matrix_chunks(self) -> Iterator[MatrixChunk]:
        """
        Generate chunks of the similarity matrix for processing.
        
        For symmetric matrices, only generates the upper triangle.
        
        Yields:
            MatrixChunk objects defining regions of the matrix to calculate
        """
        for i in range(0, self.num_items, self.current_chunk_size):
            i_end = min(i + self.current_chunk_size, self.num_items)
            
            # For symmetric matrices, we only need to compute the upper triangle
            j_start = i if self.symmetric else 0
            
            for j in range(j_start, self.num_items, self.current_chunk_size):
                j_end = min(j + self.current_chunk_size, self.num_items)
                
                # Create and yield the chunk
                chunk = MatrixChunk(
                    row_start=i,
                    row_end=i_end,
                    col_start=j,
                    col_end=j_end,
                    # Prioritize diagonal chunks (likely to have higher similarity)
                    priority=1.5 if i == j else 1.0
                )
                
                logger.debug(f"Yielding {chunk} with shape {chunk.shape}")
                yield chunk
                
                # Check memory after processing and adjust chunk size
                self._adjust_chunk_size()
    
    def _adjust_chunk_size(self) -> None:
        """Adjust chunk size based on current memory usage"""
        memory_usage = get_memory_usage()
        # Calculate as percentage of 32GB (typical laptop upper limit)
        memory_percent = memory_usage.current_process_usage_mb / 32000 * 100
        
        prev_chunk_size = self.current_chunk_size
        if memory_percent > self.strategy.memory_threshold_percent:
            # Reduce chunk size under memory pressure
            self.current_chunk_size = max(
                int(self.current_chunk_size * self.strategy.shrink_factor),
                self.strategy.min_chunk_size
            )
            trigger_garbage_collection(full=True)
            logger.info(f"Memory pressure detected ({memory_percent:.1f}%), "
                       f"reducing chunk size: {prev_chunk_size} â†’ {self.current_chunk_size}")
        elif memory_percent < self.strategy.target_memory_percent:
            # Increase chunk size if memory usage is low
            self.current_chunk_size = min(
                int(self.current_chunk_size * self.strategy.growth_factor),
                self.strategy.max_chunk_size
            )
            if self.current_chunk_size > prev_chunk_size:
                logger.debug(f"Memory usage low ({memory_percent:.1f}%), "
                           f"increasing chunk size: {prev_chunk_size} â†’ {self.current_chunk_size}")

    def estimate_num_chunks(self) -> int:
        """
        Estimate the number of chunks that will be generated.
        
        This is useful for progress tracking and planning.
        
        Returns:
            Estimated number of chunks
        """
        # Calculate number of chunks in each dimension
        num_row_chunks = (self.num_items + self.current_chunk_size - 1) // self.current_chunk_size
        
        if self.symmetric:
            # For symmetric matrices, we only compute the upper triangle
            # Sum of 1 to n = n(n+1)/2
            return (num_row_chunks * (num_row_chunks + 1)) // 2
        else:
            # For non-symmetric matrices, we compute the full matrix
            num_col_chunks = num_row_chunks  # Same chunk size in both dimensions
            return num_row_chunks * num_col_chunks

    def estimate_memory_requirements(self, bytes_per_value: int = 8) -> float:
        """
        Estimate the memory requirements for the largest chunk.
        
        Args:
            bytes_per_value: Number of bytes per matrix value (default: 8 for float64)
            
        Returns:
            Estimated memory in MB for the largest chunk
        """
        # Maximum chunk size in each dimension
        max_chunk_dim = min(self.current_chunk_size, self.num_items)
        
        # Memory for the chunk
        chunk_memory = max_chunk_dim * max_chunk_dim * bytes_per_value
        
        # Convert to MB
        chunk_memory_mb = chunk_memory / (1024 * 1024)
        
        return chunk_memory_mb

def reconstruct_matrix(chunks: dict, shape: Tuple[int, int], dtype=np.float32) -> np.ndarray:
    """
    Reconstruct a full matrix from chunks.
    
    Args:
        chunks: Dictionary mapping (row_start, row_end, col_start, col_end) to chunk data
        shape: Shape of the full matrix as (rows, cols)
        dtype: Data type for the output matrix
        
    Returns:
        Reconstructed matrix
    """
    # Create the output matrix
    result = np.zeros(shape, dtype=dtype)
    
    # Fill in the chunks
    for (row_start, row_end, col_start, col_end), chunk_data in chunks.items():
        result[row_start:row_end, col_start:col_end] = chunk_data
    
    return result

def reconstruct_symmetric_matrix(chunks: dict, size: int, dtype=np.float32) -> np.ndarray:
    """
    Reconstruct a symmetric matrix from upper triangle chunks.
    
    Args:
        chunks: Dictionary mapping (row_start, row_end, col_start, col_end) to chunk data
        size: Size of the square matrix
        dtype: Data type for the output matrix
        
    Returns:
        Reconstructed symmetric matrix
    """
    # Create the output matrix
    result = np.zeros((size, size), dtype=dtype)
    
    # Fill in the chunks
    for (row_start, row_end, col_start, col_end), chunk_data in chunks.items():
        # Fill the upper triangle
        result[row_start:row_end, col_start:col_end] = chunk_data
        
        # If this is not a diagonal chunk, fill the lower triangle
        if row_start != col_start or row_end != col_end:
            result[col_start:col_end, row_start:row_end] = chunk_data.T
    
    return result 
