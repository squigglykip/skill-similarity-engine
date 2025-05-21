"""
Memory-Aware Processing Framework

This module provides a framework for memory-aware processing that continuously
monitors memory usage and adapts processing strategies in real-time. This is
essential for handling large datasets (35,000+ jobs) on standard hardware with
memory constraints.
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, Callable, TypeVar, List, Tuple, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
import gc

import psutil
import numpy as np

from .performance import get_memory_usage, trigger_garbage_collection, MemoryUsage

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')

@dataclass
class MemoryThresholds:
    """Memory usage thresholds for adaptive processing"""
    warning_percent: float = 70.0  # First warning level
    critical_percent: float = 85.0  # Critical level - take action
    emergency_percent: float = 95.0  # Emergency level - aggressive action
    
    # System memory thresholds in MB
    system_reserve_mb: float = 2000.0  # Keep this much memory free for system
    
    def __post_init__(self):
        """Validate thresholds"""
        if not 0 < self.warning_percent < self.critical_percent < self.emergency_percent <= 100:
            raise ValueError("Thresholds must be in ascending order and between 0-100")

@dataclass
class MemoryStrategy:
    """Strategy for memory-aware processing"""
    # Initial chunk size parameters
    initial_chunk_size: int = 1000
    min_chunk_size: int = 100
    max_chunk_size: int = 10000
    
    # Growth and shrink factors
    growth_factor: float = 1.5  # Multiply chunk size by this when memory is low
    shrink_factor: float = 0.5  # Multiply chunk size by this when memory is high
    
    # Memory thresholds
    thresholds: MemoryThresholds = field(default_factory=MemoryThresholds)
    
    # Monitoring parameters
    check_interval_seconds: float = 1.0  # How often to check memory
    averaging_window: int = 5  # Number of samples to average
    
    # GC strategy
    gc_at_warning: bool = False  # Run GC at warning threshold
    gc_at_critical: bool = True  # Run GC at critical threshold
    gc_full_at_emergency: bool = True  # Run full GC at emergency threshold

class MemoryMonitor:
    """
    Monitors memory usage in a background thread.
    
    This class provides real-time memory usage information and can trigger
    callbacks when memory usage crosses specified thresholds.
    """
    
    def __init__(self, 
                 strategy: Optional[MemoryStrategy] = None,
                 warning_callback: Optional[Callable[[MemoryUsage, float], None]] = None,
                 critical_callback: Optional[Callable[[MemoryUsage, float], None]] = None,
                 emergency_callback: Optional[Callable[[MemoryUsage, float], None]] = None):
        """
        Initialize the memory monitor.
        
        Args:
            strategy: Memory strategy parameters
            warning_callback: Called when memory exceeds warning threshold
            critical_callback: Called when memory exceeds critical threshold
            emergency_callback: Called when memory exceeds emergency threshold
        """
        self.strategy = strategy or MemoryStrategy()
        self.warning_callback = warning_callback
        self.critical_callback = critical_callback
        self.emergency_callback = emergency_callback
        
        self.running = False
        self.thread = None
        self.memory_history: List[MemoryUsage] = []
        self.current_memory: Optional[MemoryUsage] = None
        self.current_percent: float = 0.0
        
        # Track threshold states to avoid repeated callbacks
        self.warning_triggered = False
        self.critical_triggered = False
        self.emergency_triggered = False
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def start(self) -> None:
        """Start the memory monitoring thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Memory monitor started")
    
    def stop(self) -> None:
        """Stop the memory monitoring thread."""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logger.info("Memory monitor stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop that runs in a background thread."""
        while self.running:
            # Get current memory usage
            memory_usage = get_memory_usage()
            
            # Calculate memory usage as percentage of available memory
            system_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB
            usable_memory = system_memory - self.strategy.thresholds.system_reserve_mb
            percent = (memory_usage.current_process_usage_mb / usable_memory) * 100
            
            # Update state with thread safety
            with self.lock:
                self.current_memory = memory_usage
                self.current_percent = percent
                
                # Keep history limited to window size
                self.memory_history.append(memory_usage)
                if len(self.memory_history) > self.strategy.averaging_window:
                    self.memory_history.pop(0)
            
            # Check thresholds and trigger callbacks
            self._check_thresholds(memory_usage, percent)
            
            # Sleep until next check
            time.sleep(self.strategy.check_interval_seconds)
    
    def _check_thresholds(self, memory_usage: MemoryUsage, percent: float) -> None:
        """Check memory thresholds and trigger callbacks if needed."""
        thresholds = self.strategy.thresholds
        
        # Emergency threshold (highest priority)
        if percent >= thresholds.emergency_percent:
            if not self.emergency_triggered:
                logger.warning(f"EMERGENCY memory usage: {percent:.1f}% "
                              f"({memory_usage.current_process_usage_mb:.1f} MB)")
                
                # Run full GC if configured
                if self.strategy.gc_full_at_emergency:
                    trigger_garbage_collection(full=True)
                
                # Call callback if provided
                if self.emergency_callback:
                    self.emergency_callback(memory_usage, percent)
                
                self.emergency_triggered = True
        else:
            self.emergency_triggered = False
        
        # Critical threshold
        if percent >= thresholds.critical_percent:
            if not self.critical_triggered:
                logger.warning(f"Critical memory usage: {percent:.1f}% "
                              f"({memory_usage.current_process_usage_mb:.1f} MB)")
                
                # Run GC if configured
                if self.strategy.gc_at_critical:
                    trigger_garbage_collection(full=False)
                
                # Call callback if provided
                if self.critical_callback:
                    self.critical_callback(memory_usage, percent)
                
                self.critical_triggered = True
        else:
            self.critical_triggered = False
        
        # Warning threshold
        if percent >= thresholds.warning_percent:
            if not self.warning_triggered:
                logger.info(f"Warning: memory usage at {percent:.1f}% "
                           f"({memory_usage.current_process_usage_mb:.1f} MB)")
                
                # Run GC if configured
                if self.strategy.gc_at_warning:
                    trigger_garbage_collection(full=False)
                
                # Call callback if provided
                if self.warning_callback:
                    self.warning_callback(memory_usage, percent)
                
                self.warning_triggered = True
        else:
            self.warning_triggered = False
    
    def get_current_usage(self) -> Tuple[MemoryUsage, float]:
        """
        Get current memory usage and percentage.
        
        Returns:
            Tuple of (memory_usage, percentage)
        """
        with self.lock:
            return self.current_memory, self.current_percent
    
    def get_average_usage(self) -> float:
        """
        Get average memory usage percentage over the averaging window.
        
        Returns:
            Average memory usage percentage
        """
        with self.lock:
            if not self.memory_history:
                return 0.0
            
            avg_mb = sum(m.current_process_usage_mb for m in self.memory_history) / len(self.memory_history)
            system_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB
            usable_memory = system_memory - self.strategy.thresholds.system_reserve_mb
            return (avg_mb / usable_memory) * 100
    
    def is_memory_critical(self) -> bool:
        """
        Check if memory usage is at or above the critical threshold.
        
        Returns:
            Whether memory is critical
        """
        _, percent = self.get_current_usage()
        return percent >= self.strategy.thresholds.critical_percent

class MemoryAwareProcessor:
    """
    Processes data in a memory-aware manner, adapting to available memory.
    
    This class monitors memory usage and adjusts processing strategies to
    avoid running out of memory when handling large datasets.
    """
    
    def __init__(self, strategy: Optional[MemoryStrategy] = None):
        """
        Initialize the memory-aware processor.
        
        Args:
            strategy: Memory strategy parameters
        """
        self.strategy = strategy or MemoryStrategy()
        self.monitor = MemoryMonitor(
            strategy=self.strategy,
            warning_callback=self._on_warning,
            critical_callback=self._on_critical,
            emergency_callback=self._on_emergency
        )
        self.current_chunk_size = self.strategy.initial_chunk_size
    
    def __enter__(self):
        """Start the memory monitor when used as a context manager."""
        self.monitor.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the memory monitor when exiting the context."""
        self.monitor.stop()
    
    def _on_warning(self, memory_usage: MemoryUsage, percent: float) -> None:
        """Called when memory usage exceeds the warning threshold."""
        # At warning level, we don't change chunk size yet
        pass
    
    def _on_critical(self, memory_usage: MemoryUsage, percent: float) -> None:
        """Called when memory usage exceeds the critical threshold."""
        # Decrease chunk size to reduce memory pressure
        old_size = self.current_chunk_size
        self.current_chunk_size = max(
            self.strategy.min_chunk_size,
            int(self.current_chunk_size * self.strategy.shrink_factor)
        )
        logger.info(f"Reduced chunk size from {old_size} to {self.current_chunk_size} due to memory pressure")
        
        # Explicitly trigger garbage collection
        collected = trigger_garbage_collection(full=False)
        logger.info(f"Triggered garbage collection: {collected[0]} objects collected")
    
    def _on_emergency(self, memory_usage: MemoryUsage, percent: float) -> None:
        """Called when memory usage exceeds the emergency threshold."""
        # Aggressively reduce chunk size to minimum
        old_size = self.current_chunk_size
        self.current_chunk_size = self.strategy.min_chunk_size
        logger.warning(f"Emergency: reduced chunk size to minimum ({self.current_chunk_size})")
        
        # Trigger full garbage collection
        collected = trigger_garbage_collection(full=True)
        logger.warning(f"Triggered full garbage collection: {collected[0]} objects collected")
    
    def get_chunk_size(self) -> int:
        """
        Get the current recommended chunk size based on memory conditions.
        
        Returns:
            The current chunk size
        """
        # Check current memory usage
        memory_usage, percent = self.monitor.get_current_usage()
        
        # If memory pressure is low, we can try to increase chunk size
        if percent < self.strategy.thresholds.warning_percent * 0.7:  # Well below warning
            new_size = min(
                self.strategy.max_chunk_size,
                int(self.current_chunk_size * self.strategy.growth_factor)
            )
            
            # Only log if we're actually increasing
            if new_size > self.current_chunk_size:
                logger.info(f"Increased chunk size from {self.current_chunk_size} to {new_size}")
                self.current_chunk_size = new_size
        
        return self.current_chunk_size
    
    def process_in_chunks(self, 
                         items: List[T], 
                         process_func: Callable[[List[T]], R]) -> List[R]:
        """
        Process items in memory-aware chunks.
        
        Args:
            items: List of items to process
            process_func: Function to process each chunk
            
        Returns:
            List of results from processing each chunk
        """
        results = []
        remaining_items = list(items)  # Copy to avoid modifying original
        
        while remaining_items:
            # Get current chunk size based on memory conditions
            chunk_size = self.get_chunk_size()
            
            # Extract the next chunk
            chunk = remaining_items[:chunk_size]
            remaining_items = remaining_items[chunk_size:]
            
            # Process the chunk
            logger.info(f"Processing chunk of {len(chunk)} items "
                       f"({len(remaining_items)} remaining)")
            
            result = process_func(chunk)
            results.append(result)
            
            # Allow some time for memory to stabilize
            time.sleep(0.1)
        
        return results

@contextmanager
def memory_aware_processing(strategy: Optional[MemoryStrategy] = None):
    """
    Context manager for memory-aware processing.
    
    Args:
        strategy: Memory strategy parameters
        
    Yields:
        MemoryAwareProcessor object for controlling processing
    """
    processor = MemoryAwareProcessor(strategy=strategy)
    processor.monitor.start()
    
    try:
        yield processor
    finally:
        processor.monitor.stop()

def calculate_optimal_chunk_size(item_size_bytes: float,
                               target_memory_mb: float = 500.0,
                               min_chunk_size: int = 100,
                               max_chunk_size: int = 10000) -> int:
    """
    Calculate an optimal chunk size based on item size and target memory usage.
    
    Args:
        item_size_bytes: Average size of each item in bytes
        target_memory_mb: Target memory usage for a chunk in MB
        min_chunk_size: Minimum chunk size
        max_chunk_size: Maximum chunk size
        
    Returns:
        Optimal chunk size
    """
    # Convert target memory to bytes
    target_memory_bytes = target_memory_mb * 1024 * 1024
    
    # Calculate raw chunk size
    chunk_size = int(target_memory_bytes / item_size_bytes)
    
    # Apply constraints
    chunk_size = max(min_chunk_size, min(max_chunk_size, chunk_size))
    
    return chunk_size

def estimate_memory_requirements(num_items: int, 
                              item_size_bytes: float,
                              processing_overhead_factor: float = 1.5) -> float:
    """
    Estimate memory requirements for processing a dataset.
    
    Args:
        num_items: Number of items to process
        item_size_bytes: Average size of each item in bytes
        processing_overhead_factor: Factor to account for processing overhead
        
    Returns:
        Estimated memory requirement in MB
    """
    # Calculate base memory for items
    base_memory_bytes = num_items * item_size_bytes
    
    # Apply overhead factor for processing
    total_memory_bytes = base_memory_bytes * processing_overhead_factor
    
    # Convert to MB
    total_memory_mb = total_memory_bytes / (1024 * 1024)
    
    return total_memory_mb

def check_memory_feasibility(memory_required_mb: float,
                          available_memory_mb: Optional[float] = None) -> bool:
    """
    Check if a processing operation is feasible with available memory.
    
    Args:
        memory_required_mb: Estimated memory requirement in MB
        available_memory_mb: Available memory in MB (if None, uses system available)
        
    Returns:
        Whether the operation is feasible
    """
    if available_memory_mb is None:
        # Get system available memory
        available_memory_mb = psutil.virtual_memory().available / (1024 * 1024)
    
    # Leave some buffer for system
    usable_memory_mb = available_memory_mb - 2000  # 2GB buffer
    
    return memory_required_mb <= usable_memory_mb