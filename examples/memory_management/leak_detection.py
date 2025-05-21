#!/usr/bin/env python
"""
Memory Leak Detection Example

This example demonstrates how to use the MemoryLeakageDetector to identify potential
memory leaks in code. It creates various leak patterns and shows how to detect and fix them.
"""

import os
import time
import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Callable, Set, Optional

# Add the project src directory to the path
import sys
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.utils.memory_efficient_base import MemoryLeakageDetector
from skill_similarity_engine.utils.performance import (
    get_memory_usage,
    trigger_garbage_collection,
    memory_tracking
)

# Create an output directory for reports
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "memory_reports")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Global cache used to demonstrate leaks
_global_cache: Dict[str, Any] = {}

# ---- Memory Leak Patterns ----

def leak_pattern_1_global_cache(iterations: int = 10, size: int = 100000) -> None:
    """
    Leak pattern 1: Continuously adding items to a global cache without cleanup.
    
    This is a common source of memory leaks - data that gets cached globally
    but never cleaned up, even when no longer needed.
    
    Args:
        iterations: Number of data chunks to create
        size: Size of each data chunk
    """
    global _global_cache
    
    print(f"Running leak_pattern_1_global_cache with {iterations} iterations...")
    
    for i in range(iterations):
        # Create a unique key based on timestamp to ensure we always add new items
        key = f"data_{i}_{time.time()}"
        
        # Add a large chunk of data to the global cache
        _global_cache[key] = [random.random() for _ in range(size)]
        
        # Simulate some processing with the data
        time.sleep(0.1)

def leak_pattern_2_closure_capture() -> Callable[[], None]:
    """
    Leak pattern 2: Closure capturing large objects.
    
    This pattern creates a closure that captures a large object in its scope.
    Even if the function is called only once, the large object persists in memory
    as long as the closure is referenced.
    
    Returns:
        A closure function that captured a large object
    """
    # Create a large dataset that will be captured by the closure
    large_data = [random.random() for _ in range(1000000)]  # 1M random numbers
    
    def closure_function() -> None:
        """This function captures the large_data in its closure."""
        # Just accessing a small part of large_data to show it's captured
        print(f"Closure function accessing large_data: first element is {large_data[0]:.4f}")
    
    print(f"Created closure capturing large_data with {len(large_data):,} elements")
    return closure_function

def leak_pattern_3_circular_references(count: int = 1000) -> List[Dict[str, Any]]:
    """
    Leak pattern 3: Circular references between objects.
    
    This pattern creates objects that reference each other in a cycle,
    which can prevent garbage collection in some cases.
    
    Args:
        count: Number of object pairs to create
        
    Returns:
        List of dictionaries with circular references
    """
    print(f"Creating {count} objects with circular references...")
    
    objects = []
    for i in range(count):
        # Create a pair of objects that reference each other
        obj1 = {'name': f'obj1_{i}', 'data': [i] * 1000}
        obj2 = {'name': f'obj2_{i}', 'data': [i] * 1000}
        
        # Create the circular reference
        obj1['refers_to'] = obj2
        obj2['refers_to'] = obj1
        
        # Only store obj1 explicitly (but obj2 is still referenced by obj1)
        objects.append(obj1)
    
    return objects

def leak_pattern_4_callback_references(count: int = 100) -> Dict[str, Callable[[], None]]:
    """
    Leak pattern 4: Callback functions that hold references to large objects.
    
    This pattern creates callback functions that capture large objects in their closures.
    If these callbacks are stored in a global registry, the captured objects can't be
    garbage collected.
    
    Args:
        count: Number of callbacks to create
        
    Returns:
        Dictionary of callback functions
    """
    print(f"Creating {count} callback functions with captured data...")
    
    callbacks = {}
    for i in range(count):
        # Create a large chunk of data
        data = [random.random() for _ in range(10000)]  # 10K random numbers
        
        # Create a callback that captures this data
        def make_callback(data: List[float], index: int) -> Callable[[], None]:
            def callback() -> None:
                print(f"Callback {index} accessing data with sum: {sum(data):.2f}")
            return callback
        
        # Store the callback
        callbacks[f"callback_{i}"] = make_callback(data, i)
    
    return callbacks

# ---- Fixed versions of the leak patterns ----

def fixed_pattern_1_global_cache(iterations: int = 10, size: int = 100000) -> None:
    """
    Fixed version of leak pattern 1: Using a bounded cache with cleanup.
    
    This version maintains a limited number of items in the cache and
    removes old entries when adding new ones.
    
    Args:
        iterations: Number of data chunks to create
        size: Size of each data chunk
    """
    global _global_cache
    
    print(f"Running fixed_pattern_1_global_cache with {iterations} iterations...")
    
    # Limit the cache size
    MAX_CACHE_ITEMS = 5
    
    for i in range(iterations):
        # Create a unique key based on iteration only (allows reuse)
        key = f"data_{i}"
        
        # Add a large chunk of data to the global cache
        _global_cache[key] = [random.random() for _ in range(size)]
        
        # Cleanup: If we have too many items, remove the oldest ones
        if len(_global_cache) > MAX_CACHE_ITEMS:
            # Sort keys, assuming they're named in a way that older ones come first
            keys = sorted(list(_global_cache.keys()))
            # Remove oldest keys to get back to the limit
            for old_key in keys[:len(keys) - MAX_CACHE_ITEMS]:
                del _global_cache[old_key]
        
        # Simulate some processing with the data
        time.sleep(0.1)

def fixed_pattern_2_closure_capture() -> Callable[[], None]:
    """
    Fixed version of leak pattern 2: Limiting data capture in closures.
    
    This version only captures the specific data needed by the closure,
    not the entire large object.
    
    Returns:
        A closure function with minimal captured data
    """
    # Create a large dataset
    large_data = [random.random() for _ in range(1000000)]  # 1M random numbers
    
    # Extract only the needed data before creating the closure
    first_element = large_data[0]
    
    def closure_function() -> None:
        """This function captures only the data it needs, not the entire large object."""
        print(f"Closure function accessing first element: {first_element:.4f}")
    
    # Let the large_data be garbage collected
    del large_data
    
    print("Created closure capturing only the needed data")
    return closure_function

def fixed_pattern_3_circular_references(count: int = 1000) -> List[Dict[str, Any]]:
    """
    Fixed version of leak pattern 3: Using weak references for circular dependencies.
    
    This version breaks the circular reference by using a weakref for one direction.
    
    Args:
        count: Number of object pairs to create
        
    Returns:
        List of dictionaries with proper references
    """
    import weakref
    
    print(f"Creating {count} objects with weakref for circular dependencies...")
    
    objects = []
    references = []  # Store references to prevent immediate garbage collection
    
    for i in range(count):
        # Create a pair of objects
        obj1 = {'name': f'obj1_{i}', 'data': [i] * 1000}
        obj2 = {'name': f'obj2_{i}', 'data': [i] * 1000}
        
        # Store a regular reference in one direction
        obj1['refers_to'] = obj2
        
        # Instead of using weakref.proxy on a dict (which doesn't work),
        # we'll use a different approach to break the circular reference
        # Store a reference to a key in obj1 rather than the whole object
        obj2['refers_to'] = obj1['name']
        
        # Store objects in our result list
        objects.append(obj1)
        references.append(obj2)  # Keep a reference to obj2 as well
    
    return objects

def fixed_pattern_4_callback_references(count: int = 100) -> Dict[str, Callable[[], None]]:
    """
    Fixed version of leak pattern 4: Avoiding capturing large objects in callbacks.
    
    This version computes and stores only the essential data needed by the callback,
    rather than capturing the entire large object.
    
    Args:
        count: Number of callbacks to create
        
    Returns:
        Dictionary of callback functions
    """
    print(f"Creating {count} callback functions without capturing large data...")
    
    callbacks = {}
    for i in range(count):
        # Create a large chunk of data
        data = [random.random() for _ in range(10000)]  # 10K random numbers
        
        # Pre-compute the value needed by the callback
        data_sum = sum(data)
        
        # Create a callback that captures only the sum, not the entire data
        def make_callback(precomputed_sum: float, index: int) -> Callable[[], None]:
            def callback() -> None:
                print(f"Callback {index} accessing precomputed sum: {precomputed_sum:.2f}")
            return callback
        
        # Store the callback with minimal captured data
        callbacks[f"callback_{i}"] = make_callback(data_sum, i)
        
        # Let the original data be garbage collected
        del data
    
    return callbacks

# ---- Leak detection and demonstration ----

def demonstrate_leak_detector(
    leaky_function: Callable[..., Any],
    fixed_function: Callable[..., Any],
    description: str,
    args: Optional[List[Any]] = None,
    kwargs: Optional[Dict[str, Any]] = None
) -> None:
    """
    Demonstrate leak detection by comparing a leaky function with its fixed version.
    
    Args:
        leaky_function: Function with a memory leak
        fixed_function: Improved version without the leak
        description: Description of the leak pattern
        args: Positional arguments for the functions
        kwargs: Keyword arguments for the functions
    """
    args = args or []
    kwargs = kwargs or {}
    
    print("\n" + "=" * 80)
    print(f"DEMONSTRATING: {description}")
    print("=" * 80 + "\n")
    
    # Create a detector
    detector = MemoryLeakageDetector()
    
    # Take an initial sample before any activity
    detector.take_sample()
    print("Initial memory sample taken.")
    
    # Run the leaky function multiple times
    print("\n1. Running leaky implementation multiple times...")
    leaky_results = []
    for i in range(3):
        with memory_tracking(f"Leaky function run {i+1}"):
            result = leaky_function(*args, **kwargs)
            leaky_results.append(result)
        
        # Take a sample after each run
        detector.take_sample()
        print(f"Memory sample taken after run {i+1}")
    
    # Find types with growing instance counts
    growing_types = detector.find_growing_types()
    print("\nTypes with potentially leaking instances:")
    for i, (type_obj, old_count, new_count) in enumerate(growing_types[:5], 1):
        growth = new_count - old_count
        print(f"  {i}. {type_obj.__name__}: {old_count} -> {new_count} (+{growth})")
    
    # Track references for the most problematic type
    if growing_types:
        problematic_type = growing_types[0][0]
        detector.track_references(problematic_type)
        print(f"\nTracking references to {problematic_type.__name__}")
    
    # Clean up the leaky results
    leaky_results.clear()
    trigger_garbage_collection()
    
    # Take another sample after cleanup
    detector.take_sample()
    print("\nMemory sample taken after attempting to clean up leaky results")
    
    # Run the fixed function multiple times
    print("\n2. Running fixed implementation multiple times...")
    fixed_results = []
    for i in range(3):
        with memory_tracking(f"Fixed function run {i+1}"):
            result = fixed_function(*args, **kwargs)
            fixed_results.append(result)
        
        # Take a sample after each run
        detector.take_sample()
        print(f"Memory sample taken after run {i+1}")
    
    # Clean up the fixed results
    fixed_results.clear()
    trigger_garbage_collection()
    
    # Take a final sample
    detector.take_sample()
    print("\nFinal memory sample taken after cleanup")
    
    # Generate a leak detection report
    report = detector.get_report()
    print("\nMEMORY LEAK DETECTION REPORT:")
    print("-" * 40)
    print(report)
    
    # Save the report to a file
    report_path = os.path.join(OUTPUT_DIR, f"leak_report_{leaky_function.__name__}.txt")
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"\nDetailed leak report saved to: {report_path}")

def main() -> None:
    """Run memory leak detection demonstrations for various leak patterns."""
    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("=" * 80)
    print("MEMORY LEAK DETECTION EXAMPLES")
    print("=" * 80)
    
    print("\nThis example demonstrates how to use MemoryLeakageDetector to identify")
    print("various types of memory leaks and how to fix them.")
    
    # Clear the global cache before we start
    global _global_cache
    _global_cache.clear()
    
    # Demonstrate leak pattern 1: Global cache without cleanup
    demonstrate_leak_detector(
        leak_pattern_1_global_cache,
        fixed_pattern_1_global_cache,
        "Global cache without cleanup",
        args=[10, 50000]  # Reduce size for demonstration
    )
    
    # Clear the global cache between demonstrations
    _global_cache.clear()
    trigger_garbage_collection()
    
    # Demonstrate leak pattern 2: Closure capturing large objects
    demonstrate_leak_detector(
        leak_pattern_2_closure_capture,
        fixed_pattern_2_closure_capture,
        "Closure capturing large objects"
    )
    
    # Demonstrate leak pattern 3: Circular references
    demonstrate_leak_detector(
        leak_pattern_3_circular_references,
        fixed_pattern_3_circular_references,
        "Circular references between objects",
        args=[500]  # Reduce count for demonstration
    )
    
    # Demonstrate leak pattern 4: Callback references
    demonstrate_leak_detector(
        leak_pattern_4_callback_references,
        fixed_pattern_4_callback_references,
        "Callback functions capturing large objects",
        args=[50]  # Reduce count for demonstration
    )
    
    # Final cleanup
    _global_cache.clear()
    trigger_garbage_collection()
    
    print("\n" + "=" * 80)
    print("Memory leak detection demonstrations completed.")
    print(f"Reports saved in: {OUTPUT_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    main() 