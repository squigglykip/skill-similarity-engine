#!/usr/bin/env python
"""
Function-Level Memory Profiling Example

This example demonstrates how to use the memory_profile decorator to analyze
memory usage at the function level. It profiles functions with different
memory usage patterns and shows how to interpret the results.
"""

import os
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Add the project src directory to the path
import sys
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.utils.performance import (
    memory_profile, 
    get_memory_usage,
    trigger_garbage_collection,
    memory_tracking
)

# Create an output directory for reports
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "memory_reports")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---- Functions with different memory usage patterns ----

@memory_profile
def function_with_growing_lists(size: int = 1000000) -> List[int]:
    """
    A function that creates a large list, demonstrating growing memory usage.
    
    Args:
        size: Size of the list to create
        
    Returns:
        The created list
    """
    result = []
    for i in range(size):
        result.append(i)
    return result

@memory_profile
def function_with_numpy_arrays(size: int = 1000000) -> np.ndarray:
    """
    A function that creates a large numpy array, demonstrating efficient memory usage.
    
    Args:
        size: Size of the array to create
        
    Returns:
        The created array
    """
    return np.arange(size)

@memory_profile
def function_with_memory_leak_pattern(iterations: int = 10) -> Dict[str, List[int]]:
    """
    A function that simulates a memory leak pattern by storing data in a global.
    
    Args:
        iterations: Number of iterations
        
    Returns:
        Dictionary with data from the current iteration
    """
    global _cached_data
    if '_cached_data' not in globals():
        _cached_data = {}
    
    # Create some data and store it in the global cache without any cleanup mechanism
    for i in range(iterations):
        key = f"data_{i}_{time.time()}"
        _cached_data[key] = [i] * 100000  # 100K integers per iteration
    
    # Return only the last chunk (but all chunks remain in memory)
    return {key: _cached_data[key]}

@memory_profile
def function_with_proper_cleanup(iterations: int = 10) -> Dict[str, List[int]]:
    """
    A function that demonstrates proper cleanup, avoiding the memory leak pattern.
    
    Args:
        iterations: Number of iterations
        
    Returns:
        Dictionary with data from the current iteration
    """
    result = {}
    
    # Create data but maintain only the latest version
    for i in range(iterations):
        key = f"data_{i}"
        result = {key: [i] * 100000}  # Replace previous data instead of accumulating
    
    return result

@memory_profile
def recursive_function(depth: int = 10, size: int = 100000) -> List[List[int]]:
    """
    A recursive function that demonstrates memory usage in recursive calls.
    
    Args:
        depth: Recursion depth
        size: Size of the data at each level
        
    Returns:
        Nested list structure
    """
    # Base case
    if depth <= 0:
        return [[0] * 100]  # Small base case
    
    # Create data at this level
    data = [depth] * size
    
    # Recurse with smaller data size to avoid excessive memory usage
    sub_result = recursive_function(depth - 1, size // 10)
    
    return [data, sub_result]

# ---- Examples of using the functions and analyzing results ----

def run_and_compare_functions() -> None:
    """Run and compare different function memory usage patterns."""
    print("\n1. Comparing list vs. numpy array memory usage:")
    
    # Run the list version
    print("\nRunning function_with_growing_lists...")
    list_result = function_with_growing_lists(1000000)
    list_size = len(list_result)
    del list_result  # Clean up
    
    # Run the numpy version
    print("\nRunning function_with_numpy_arrays...")
    array_result = function_with_numpy_arrays(1000000)
    array_size = len(array_result)
    del array_result  # Clean up
    
    print(f"\nBoth functions created sequences of {list_size:,} integers.")
    print("The @memory_profile decorator shows the memory difference.")

def demonstrate_memory_leak_detection() -> None:
    """Demonstrate detecting memory leak patterns."""
    print("\n2. Detecting memory leak patterns:")
    
    # First trigger garbage collection to start clean
    trigger_garbage_collection()
    start_memory = get_memory_usage().current_process_usage_mb
    
    # Run the function with a memory leak pattern multiple times
    print("\nRunning function_with_memory_leak_pattern multiple times...")
    for i in range(5):
        print(f"  Run {i+1}...")
        result = function_with_memory_leak_pattern(5)
        del result  # This doesn't clean up the global
    
    # Check memory after the leaky function
    after_leak = get_memory_usage().current_process_usage_mb
    
    # Run the proper cleanup version
    print("\nRunning function_with_proper_cleanup multiple times...")
    for i in range(5):
        print(f"  Run {i+1}...")
        result = function_with_proper_cleanup(5)
        del result
    
    # Check memory after the proper cleanup function
    after_proper = get_memory_usage().current_process_usage_mb
    
    # Report the results
    print("\nMemory usage comparison:")
    print(f"  Starting memory: {start_memory:.2f} MB")
    print(f"  After leaky function: {after_leak:.2f} MB (change: {after_leak - start_memory:+.2f} MB)")
    print(f"  After proper cleanup: {after_proper:.2f} MB (change: {after_proper - after_leak:+.2f} MB)")
    
    if after_leak - start_memory > 10:  # If we have a significant leak
        print("\nThe memory leak pattern is evident from the increasing memory usage.")
        print("The @memory_profile decorator shows where memory is allocated but not released.")

def demonstrate_context_manager() -> None:
    """Demonstrate using the memory_tracking context manager for specific blocks."""
    print("\n3. Using memory_tracking context manager:")
    
    # Track a specific block of code
    print("\nTracking a specific block with growing memory:")
    with memory_tracking("Growing list block"):
        big_list = []
        for i in range(1000000):
            big_list.append(i)
        print(f"  List created with {len(big_list):,} elements")
    
    # Track another block with better memory usage
    print("\nTracking a block with more efficient memory usage:")
    with memory_tracking("Numpy array block"):
        array = np.arange(1000000)
        print(f"  Array created with {len(array):,} elements")
    
    # Track a nested block
    print("\nTracking nested blocks:")
    with memory_tracking("Outer block"):
        outer_list = []
        for i in range(10):
            with memory_tracking(f"Inner block {i}"):
                inner_list = [i] * 100000
                outer_list.append(inner_list)
        print(f"  Created nested structure with {len(outer_list)} lists of {len(outer_list[0])} elements each")

def analyze_recursive_memory_usage() -> None:
    """Analyze memory usage in recursive functions."""
    print("\n4. Analyzing recursive function memory usage:")
    
    print("\nRunning recursive_function with depth=10...")
    result = recursive_function(depth=10)
    
    # Print some information about the structure
    def get_structure_info(data: Any, level: int = 0) -> str:
        """Analyze the structure of the recursive result."""
        if isinstance(data, list):
            if level < 3:  # Only recurse a few levels to keep output manageable
                items = [get_structure_info(item, level + 1) for item in data]
                return f"List with {len(data)} items: [{', '.join(items)}]"
            else:
                return f"List with {len(data)} items"
        else:
            return str(data)
    
    structure = get_structure_info(result)
    print(f"\nResult structure: {structure[:100]}...")  # Truncate for readability
    
    # The memory profile is automatically printed by the decorator
    print("\nThe memory profile shows how recursion affects memory usage.")
    print("Each level allocates memory, which is held until the entire call stack returns.")

def main() -> None:
    """Run all memory profiling demonstrations."""
    print("=" * 80)
    print("FUNCTION-LEVEL MEMORY PROFILING EXAMPLES")
    print("=" * 80)
    
    print("\nThis example demonstrates how to use the @memory_profile decorator")
    print("and other memory tracking utilities to analyze memory usage patterns.")
    
    # Run the different demonstrations
    run_and_compare_functions()
    demonstrate_memory_leak_detection()
    demonstrate_context_manager()
    analyze_recursive_memory_usage()
    
    # Final cleanup and report
    if '_cached_data' in globals():
        # Clean up the global that we used to demonstrate a memory leak
        global _cached_data
        _cached_data.clear()
        del _cached_data
    
    trigger_garbage_collection()
    final_memory = get_memory_usage().current_process_usage_mb
    
    print("\n" + "=" * 80)
    print(f"Demonstrations complete. Final memory usage: {final_memory:.2f} MB")
    print("=" * 80)

if __name__ == "__main__":
    main() 