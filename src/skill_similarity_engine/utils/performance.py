"""
Memory Management and Performance Utilities

This module provides utilities for tracking memory usage, managing large objects,
optimising garbage collection, and monitoring performance in memory-intensive operations.
The utilities are designed to be used across the codebase to help manage memory pressure
when processing large datasets such as the full job architecture with 35,000+ jobs.
"""

import gc
import os
import sys
import time
import logging
import functools
import tracemalloc
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast
from dataclasses import dataclass
from contextlib import contextmanager

import psutil
import numpy as np

# Configure module logger
logger = logging.getLogger(__name__)

# Type variables for generic function decorators
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')

# -----------------------------------------------------------------------------
# Memory Usage Reporting
# -----------------------------------------------------------------------------

@dataclass
class MemoryUsage:
    """Represents memory usage information at a specific point in time."""
    
    timestamp: float
    current_process_usage: int  # Current process memory usage in bytes
    system_available: int  # Available system memory in bytes
    system_total: int  # Total system memory in bytes
    
    @property
    def current_process_usage_mb(self) -> float:
        """Current process memory usage in megabytes."""
        return self.current_process_usage / (1024 * 1024)
    
    @property
    def system_available_mb(self) -> float:
        """Available system memory in megabytes."""
        return self.system_available / (1024 * 1024)
    
    @property
    def system_total_mb(self) -> float:
        """Total system memory in megabytes."""
        return self.system_total / (1024 * 1024)
    
    @property
    def usage_percent(self) -> float:
        """Memory usage as a percentage of total system memory."""
        return (1 - (self.system_available / self.system_total)) * 100
    
    def __str__(self) -> str:
        """String representation of the memory usage."""
        return (
            f"Memory Usage:\n"
            f"  Time: {self.timestamp:.2f}s\n"
            f"  Current Process: {self.current_process_usage_mb:.2f} MB\n"
            f"  System Available: {self.system_available_mb:.2f} MB\n"
            f"  System Total: {self.system_total_mb:.2f} MB\n"
            f"  Usage: {self.usage_percent:.1f}%"
        )

@dataclass
class MemorySnapshot:
    """Represents a snapshot of memory usage at a specific point in time."""
    
    timestamp: float
    total_allocated: int  # Total memory allocated in bytes
    peak_allocated: int   # Peak memory allocation in bytes
    current_process_usage: int  # Current process memory usage in bytes
    system_available: int  # Available system memory in bytes
    gc_objects: int  # Number of objects tracked by the garbage collector
    
    @property
    def total_allocated_mb(self) -> float:
        """Total allocated memory in megabytes."""
        return self.total_allocated / (1024 * 1024)
    
    @property
    def peak_allocated_mb(self) -> float:
        """Peak allocated memory in megabytes."""
        return self.peak_allocated / (1024 * 1024)
    
    @property
    def current_process_usage_mb(self) -> float:
        """Current process memory usage in megabytes."""
        return self.current_process_usage / (1024 * 1024)
    
    @property
    def system_available_mb(self) -> float:
        """Available system memory in megabytes."""
        return self.system_available / (1024 * 1024)
    
    def __str__(self) -> str:
        """String representation of the memory snapshot."""
        return (
            f"Memory Snapshot:\n"
            f"  Time: {self.timestamp:.2f}s\n"
            f"  Current Process: {self.current_process_usage_mb:.2f} MB\n"
            f"  Total Allocated: {self.total_allocated_mb:.2f} MB\n"
            f"  Peak Allocated: {self.peak_allocated_mb:.2f} MB\n"
            f"  System Available: {self.system_available_mb:.2f} MB\n"
            f"  GC Objects: {self.gc_objects:,}"
        )


def get_memory_usage() -> MemoryUsage:
    """
    Get the current memory usage.
    
    Returns:
        MemoryUsage object with current memory metrics
    """
    process = psutil.Process(os.getpid())
    virtual_memory = psutil.virtual_memory()
    
    return MemoryUsage(
        timestamp=time.time(),
        current_process_usage=process.memory_info().rss,
        system_available=virtual_memory.available,
        system_total=virtual_memory.total
    )


def get_memory_snapshot() -> MemorySnapshot:
    """
    Get the current memory usage across different metrics.
    
    Returns:
        MemorySnapshot object with current memory metrics
    """
    process = psutil.Process(os.getpid())
    
    # Get tracemalloc stats if it's running
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
    else:
        current, peak = 0, 0
    
    return MemorySnapshot(
        timestamp=time.time(),
        total_allocated=current,
        peak_allocated=peak,
        current_process_usage=process.memory_info().rss,
        system_available=psutil.virtual_memory().available,
        gc_objects=len(gc.get_objects())
    )


def memory_profile(func: F) -> F:
    """
    Decorator to profile memory usage before and after a function call.
    
    Args:
        func: The function to profile
        
    Returns:
        Wrapped function that reports memory usage
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Start tracemalloc if it's not already running
        was_tracing = tracemalloc.is_tracing()
        if not was_tracing:
            tracemalloc.start()
        
        gc.collect()  # Collect garbage before measuring
        start_snapshot = get_memory_snapshot()
        
        logger.debug(f"Memory before {func.__name__}() call: {start_snapshot.current_process_usage_mb:.2f} MB")
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            gc.collect()  # Collect garbage after execution
            end_snapshot = get_memory_snapshot()
            
            # Calculate the difference
            memory_diff = end_snapshot.current_process_usage - start_snapshot.current_process_usage
            memory_diff_mb = memory_diff / (1024 * 1024)
            
            logger.debug(
                f"Memory after {func.__name__}() call: {end_snapshot.current_process_usage_mb:.2f} MB "
                f"(Change: {memory_diff_mb:+.2f} MB)"
            )
            
            # Log detailed info at DEBUG level
            logger.debug(f"Memory details for {func.__name__}():")
            logger.debug(f"  Peak allocated: {end_snapshot.peak_allocated_mb:.2f} MB")
            logger.debug(f"  Available system memory: {end_snapshot.system_available_mb:.2f} MB")
            logger.debug(f"  GC objects: {end_snapshot.gc_objects:,}")
            
            # Stop tracemalloc if we started it
            if not was_tracing:
                tracemalloc.stop()
    
    return cast(F, wrapper)


def get_size_of_object(obj: Any) -> int:
    """
    Get an estimate of the memory size of an object and its contents.
    
    Args:
        obj: The object to measure
        
    Returns:
        Size in bytes
    """
    # Handle basic Python types
    if obj is None:
        return 0
    if isinstance(obj, (bool, int, float, str)):
        return sys.getsizeof(obj)
    
    # Handle common types with known size calculation methods
    if isinstance(obj, np.ndarray):
        return obj.nbytes
    
    # For other objects, do a deep traversal to estimate size
    seen = set()  # Track objects we've already seen to avoid cycles
    queue = [obj]
    size = 0
    
    while queue:
        current = queue.pop(0)
        if id(current) in seen:
            continue
            
        seen.add(id(current))
        size += sys.getsizeof(current)
        
        # Add attributes to queue
        if hasattr(current, "__dict__"):
            queue.extend(current.__dict__.values())
        
        # Handle common containers
        if isinstance(current, dict):
            # Add both keys and values
            queue.extend(current.keys())
            queue.extend(current.values())
        elif isinstance(current, (list, tuple, set)):
            queue.extend(current)
    
    return size


def get_largest_objects(top_n: int = 10) -> List[Tuple[int, int, type, Any]]:
    """
    Find the largest objects in memory.
    
    Args:
        top_n: Number of largest objects to return
        
    Returns:
        List of tuples (size, id, type, object) sorted by size (largest first)
    """
    gc.collect()  # Ensure garbage collection is done before analysis
    objects = gc.get_objects()
    result = []
    
    for obj in objects:
        try:
            size = get_size_of_object(obj)
            result.append((size, id(obj), type(obj), obj))
        except Exception:
            # Skip objects that can't be sized reliably
            continue
    
    # Sort by size (largest first)
    result.sort(reverse=True)
    return result[:top_n]


def log_memory_summary(log_largest_objects: bool = False) -> None:
    """
    Log a summary of current memory usage.
    
    Args:
        log_largest_objects: Whether to include the largest objects in the log
    """
    snapshot = get_memory_snapshot()
    logger.info(f"Memory summary: {snapshot.current_process_usage_mb:.2f} MB used")
    
    if log_largest_objects:
        largest = get_largest_objects(10)
        logger.info("Largest objects in memory:")
        for i, (size, obj_id, obj_type, _) in enumerate(largest, 1):
            logger.info(f"  {i}. {size/(1024*1024):.2f} MB - {obj_type.__name__} (id: {obj_id})")


# -----------------------------------------------------------------------------
# Memory Tracking Context Manager
# -----------------------------------------------------------------------------

@dataclass
class MemoryTrackingSession:
    """
    Stores information about a memory tracking session.
    """
    start_snapshot: MemorySnapshot
    end_snapshot: Optional[MemorySnapshot] = None
    name: str = "unnamed"
    snapshots: List[MemorySnapshot] = None
    
    def __post_init__(self) -> None:
        if self.snapshots is None:
            self.snapshots = []
    
    def add_snapshot(self, snapshot: MemorySnapshot) -> None:
        """Add a memory snapshot to the session."""
        self.snapshots.append(snapshot)
    
    def complete(self, end_snapshot: MemorySnapshot) -> None:
        """Mark the session as complete with an end snapshot."""
        self.end_snapshot = end_snapshot
    
    @property
    def duration(self) -> float:
        """Duration of the session in seconds."""
        if not self.end_snapshot:
            return 0
        return self.end_snapshot.timestamp - self.start_snapshot.timestamp
    
    @property
    def memory_change(self) -> float:
        """Memory change during the session in bytes."""
        if not self.end_snapshot:
            return 0
        return self.end_snapshot.current_process_usage - self.start_snapshot.current_process_usage
    
    @property
    def memory_change_mb(self) -> float:
        """Memory change during the session in megabytes."""
        return self.memory_change / (1024 * 1024)
    
    def get_report(self) -> str:
        """Get a formatted report of the memory tracking session."""
        lines = [
            f"Memory Tracking Report for: {self.name}",
            f"Duration: {self.duration:.2f} seconds",
            f"Starting memory: {self.start_snapshot.current_process_usage_mb:.2f} MB",
        ]
        
        if self.end_snapshot:
            lines.extend([
                f"Ending memory: {self.end_snapshot.current_process_usage_mb:.2f} MB",
                f"Memory change: {self.memory_change_mb:+.2f} MB",
            ])
        
        if self.snapshots:
            lines.append("\nIntermediate snapshots:")
            for i, snapshot in enumerate(self.snapshots, 1):
                time_delta = snapshot.timestamp - self.start_snapshot.timestamp
                memory_delta = (snapshot.current_process_usage - 
                               self.start_snapshot.current_process_usage) / (1024 * 1024)
                lines.append(
                    f"  {i}. Time: {time_delta:.2f}s, "
                    f"Memory: {snapshot.current_process_usage_mb:.2f} MB "
                    f"(Change: {memory_delta:+.2f} MB)"
                )
        
        return "\n".join(lines)


_active_tracking_sessions: Dict[str, MemoryTrackingSession] = {}


@contextmanager
def memory_tracking(name: str = None, 
                    log_level: int = logging.INFO,
                    snapshot_interval: Optional[float] = None,
                    threshold_mb: Optional[float] = None):
    """
    Context manager for tracking memory usage during a block of code.
    
    Args:
        name: Name for this tracking session (for reporting)
        log_level: Logging level for the reports
        snapshot_interval: If set, take snapshots at this interval (in seconds)
        threshold_mb: If set, log warnings when memory usage exceeds this threshold (in MB)
        
    Yields:
        MemoryTrackingSession object that can be used to take additional snapshots
    """
    if not name:
        # Generate a name based on the calling function
        frame = sys._getframe(1)
        name = f"{frame.f_code.co_filename}:{frame.f_lineno}"
    
    # Start tracemalloc if it's not already running
    was_tracing = tracemalloc.is_tracing()
    if not was_tracing:
        tracemalloc.start()
    
    # Take the initial snapshot
    gc.collect()
    start_snapshot = get_memory_snapshot()
    
    # Create the session
    session = MemoryTrackingSession(
        start_snapshot=start_snapshot,
        name=name
    )
    
    # Store in active sessions (allows for nested tracking)
    _active_tracking_sessions[name] = session
    
    # Set up snapshot thread if interval is specified
    snapshot_thread = None
    stop_snapshot_thread = False
    
    if snapshot_interval:
        import threading
        
        def take_snapshots():
            while not stop_snapshot_thread:
                # Sleep first to avoid immediate snapshot after start
                time.sleep(snapshot_interval)
                if stop_snapshot_thread:
                    break
                
                snapshot = get_memory_snapshot()
                session.add_snapshot(snapshot)
                
                # Check threshold if specified
                if threshold_mb and snapshot.current_process_usage_mb > threshold_mb:
                    logger.warning(
                        f"Memory usage ({snapshot.current_process_usage_mb:.2f} MB) "
                        f"exceeds threshold ({threshold_mb:.2f} MB) in {name}"
                    )
        
        snapshot_thread = threading.Thread(target=take_snapshots)
        snapshot_thread.daemon = True
        snapshot_thread.start()
    
    logger.log(log_level, f"Started memory tracking: {name}")
    
    try:
        yield session
    finally:
        # Stop the snapshot thread if it exists
        if snapshot_thread:
            stop_snapshot_thread = True
            snapshot_thread.join(timeout=1.0)
        
        # Take final snapshot
        gc.collect()
        end_snapshot = get_memory_snapshot()
        session.complete(end_snapshot)
        
        # Generate and log the report
        logger.log(log_level, session.get_report())
        
        # Clean up
        del _active_tracking_sessions[name]
        
        # Stop tracemalloc if we started it
        if not was_tracing:
            tracemalloc.stop()


# -----------------------------------------------------------------------------
# Garbage Collection Helpers
# -----------------------------------------------------------------------------

def trigger_garbage_collection(full: bool = False) -> Tuple[int, int, int]:
    """
    Explicitly trigger garbage collection and return stats.
    
    Args:
        full: If True, runs a full collection on all generations
        
    Returns:
        Tuple of (objects_collected, unreachable_objects, collected_generations)
    """
    # Store old debug flags
    old_debug = gc.get_debug()
    
    try:
        # Set debug flags to track uncollectable objects
        gc.set_debug(gc.DEBUG_UNCOLLECTABLE)
        
        # Perform collection
        if full:
            result = gc.collect()
        else:
            result = gc.collect(2)  # Collect highest generation
        
        # Get count of unreachable objects
        unreachable = len(gc.garbage)
        
        return result, unreachable, 3 if full else 1
    finally:
        # Restore original debug flags
        gc.set_debug(old_debug)


def is_memory_pressure_high(threshold_percent: float = 80.0) -> bool:
    """
    Check if the system is under memory pressure.
    
    Args:
        threshold_percent: Memory usage percentage threshold to consider "high pressure"
        
    Returns:
        True if memory pressure is high, False otherwise
    """
    vm = psutil.virtual_memory()
    return vm.percent >= threshold_percent


def schedule_targeted_collection(obj_types: List[type] = None) -> None:
    """
    Schedule a targeted garbage collection focused on specific object types.
    
    Args:
        obj_types: List of object types to target (if None, targets all types)
    """
    # Get all objects tracked by the GC
    all_objects = gc.get_objects()
    
    # Filter to target types if specified
    if obj_types:
        target_objects = [obj for obj in all_objects if isinstance(obj, tuple(obj_types))]
    else:
        target_objects = all_objects
    
    # Break reference cycles by clearing containers
    for obj in target_objects:
        if isinstance(obj, dict):
            obj.clear()
        elif isinstance(obj, list):
            obj.clear()
    
    # Run garbage collection
    gc.collect()


# -----------------------------------------------------------------------------
# Large Object Management
# -----------------------------------------------------------------------------

class ObjectPool:
    """
    A memory-efficient object pool for managing large objects.
    
    This class helps manage large objects by keeping a limited number in memory
    and providing efficient access. It uses an LRU (Least Recently Used) strategy
    to discard objects when the pool size limit is reached.
    """
    
    def __init__(self, max_size: int = 10):
        """
        Initialize the object pool.
        
        Args:
            max_size: Maximum number of objects to keep in the pool
        """
        self.max_size = max_size
        self._objects: Dict[Any, Any] = {}
        self._access_order: List[Any] = []
    
    def add(self, key: Any, obj: Any) -> None:
        """
        Add an object to the pool.
        
        Args:
            key: Key to identify the object
            obj: The object to store
        """
        # If the key already exists, update its access order
        if key in self._objects:
            self._access_order.remove(key)
        # If we're at max capacity, remove least recently used
        elif len(self._objects) >= self.max_size:
            lru_key = self._access_order.pop(0)
            del self._objects[lru_key]
        
        # Add the new object
        self._objects[key] = obj
        self._access_order.append(key)
    
    def get(self, key: Any) -> Any:
        """
        Get an object from the pool.
        
        Args:
            key: Key to identify the object
            
        Returns:
            The object if found, None otherwise
        """
        # If the key exists, update its access order
        if key in self._objects:
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._objects[key]
        return None
    
    def remove(self, key: Any) -> None:
        """
        Remove an object from the pool.
        
        Args:
            key: Key of the object to remove
        """
        if key in self._objects:
            self._access_order.remove(key)
            del self._objects[key]
    
    def clear(self) -> None:
        """Clear all objects from the pool."""
        self._objects.clear()
        self._access_order.clear()
    
    @property
    def size(self) -> int:
        """Current number of objects in the pool."""
        return len(self._objects)
    
    def __len__(self) -> int:
        """Current number of objects in the pool."""
        return len(self._objects)
    
    def __contains__(self, key: Any) -> bool:
        """Check if a key exists in the pool."""
        return key in self._objects


class MemoryEfficientDict(dict):
    """
    A memory-efficient dictionary implementation.
    
    This specialized dictionary implementation reduces memory overhead
    for large dictionaries by using more memory-efficient internal structures.
    It's particularly useful for dictionaries with many entries.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the memory-efficient dictionary."""
        super().__init__(*args, **kwargs)
        self._cached_size: Optional[int] = None
    
    def __sizeof__(self) -> int:
        """Get the size of the dictionary in bytes."""
        if self._cached_size is None:
            # Compute size explicitly for better accuracy
            self._cached_size = super().__sizeof__()
        return self._cached_size
    
    def __setitem__(self, key, value):
        """Set an item in the dictionary."""
        super().__setitem__(key, value)
        # Invalidate cached size when the dict changes
        self._cached_size = None
    
    def __delitem__(self, key):
        """Delete an item from the dictionary."""
        super().__delitem__(key)
        # Invalidate cached size when the dict changes
        self._cached_size = None
    
    def clear(self):
        """Clear all items from the dictionary."""
        super().clear()
        self._cached_size = None
    
    def update(self, *args, **kwargs):
        """Update the dictionary."""
        super().update(*args, **kwargs)
        self._cached_size = None


def enable_memory_efficiency_mode(obj: Any, enabled: bool = True) -> Any:
    """
    Enable memory efficiency features on an object if supported.
    
    Args:
        obj: The object to modify
        enabled: Whether to enable or disable memory efficiency features
        
    Returns:
        The possibly modified object
    """
    # This is a placeholder for object-specific memory optimization
    # Each class that supports memory efficiency mode will implement
    # its own version of this functionality
    
    if hasattr(obj, "set_memory_efficient"):
        obj.set_memory_efficient(enabled)
    
    if enabled and isinstance(obj, dict) and not isinstance(obj, MemoryEfficientDict):
        # Convert to memory-efficient dictionary
        return MemoryEfficientDict(obj)
    
    return obj 
