# Memory Management Examples

This directory contains examples demonstrating the memory management and optimization utilities in the Skill Similarity Engine. These examples focus on monitoring, visualizing, and improving memory usage patterns when processing large datasets.

## Background

Memory management is critical for the Skill Similarity Engine as it needs to process datasets with 35,000+ jobs requiring over 1 billion comparisons. These examples demonstrate practical techniques for:

1. **Monitoring memory usage** during processing
2. **Visualizing memory patterns** to identify bottlenecks
3. **Comparing implementations** to quantify optimization benefits
4. **Detecting memory leaks** before they cause issues
5. **Optimizing large-scale processing** to fit within memory constraints

## Examples

### 1. Dashboard Demo (`dashboard_demo.py`)

This example demonstrates the real-time memory tracking dashboard. It simulates a typical processing workflow (data loading, vectorization, similarity calculation) while tracking memory usage at each stage.

Features demonstrated:
- Starting a memory dashboard
- Marking events at key processing stages
- Generating visualizations of memory usage
- Predicting future memory requirements

To run:
```bash
python dashboard_demo.py
```

Outputs:
- `memory_reports/memory_after_loading.png`: Memory usage after data loading
- `memory_reports/memory_after_vectorization.png`: Memory usage after vectorization
- `memory_reports/memory_usage_[timestamp].png`: Overall memory usage
- `memory_reports/memory_report_[timestamp]/`: Comprehensive memory report with predictions

### 2. Memory-Efficient Comparison (`memory_efficient_comparison.py`)

This example compares memory usage between standard and memory-efficient implementations. It loads progressively larger datasets and measures the memory difference between the implementations.

Features demonstrated:
- Implementing memory-efficient containers
- Measuring memory usage before/after operations
- Comparing different implementation approaches
- Visualizing memory savings at scale

To run:
```bash
python memory_efficient_comparison.py
```

Outputs:
- `memory_reports/memory_comparison.png`: Comparison of memory usage
- `memory_reports/memory_savings.png`: Percentage of memory saved

### 3. Function-Level Profiling (`function_profiling.py`)

This example demonstrates how to use the `memory_profile` decorator to analyze memory usage at the function level. It profiles functions with different memory usage patterns and shows how to interpret the results.

Features demonstrated:
- Using the `@memory_profile` decorator
- Comparing memory usage of different implementations
- Using context managers for code block analysis
- Detecting functions with memory growth

To run:
```bash
python function_profiling.py
```

Outputs:
- Detailed console output showing memory usage of each function
- Memory statistics for different implementation approaches
- Memory impact of different coding patterns

### 4. Memory Leak Detection (`leak_detection.py`)

This example shows how to use the `MemoryLeakageDetector` to identify potential memory leaks in code. It creates various leak patterns and demonstrates how to detect and fix them.

Features demonstrated:
- Detecting common memory leak patterns
- Finding types with growing instance counts
- Tracking reference chains to leaking objects
- Implementing proper cleanup strategies

To run:
```bash
python leak_detection.py
```

Outputs:
- `memory_reports/leak_report_*.txt`: Detailed reports on detected memory leaks
- Console output comparing leaky vs. fixed implementations
- Reference tracking for problematic object types

## How Memory Management Works

The Skill Similarity Engine uses several memory optimization strategies:

1. **Efficient Data Structures**: Uses custom dict implementations and weak references to reduce overhead
2. **Tracking & Monitoring**: Monitors memory usage to detect leaks and identify bottlenecks
3. **Explicit Cleanup**: Provides methods to explicitly clean up large objects when no longer needed
4. **Garbage Collection**: Triggers garbage collection at optimal times to reclaim memory
5. **Memory-Efficient Processing**: Uses chunking and incremental processing to manage memory pressure

## Adding New Examples

When adding new memory management examples:

1. Follow the pattern of existing examples:
   - Include detailed comments explaining the memory concepts
   - Create self-contained scripts that generate their own test data
   - Produce visual outputs to help understand memory behavior
   
2. Update this README to document the new example

3. Focus on demonstrating a specific memory management concept or technique

## Scaling for Real-World Use

While these examples use modest-sized synthetic datasets for demonstration purposes, the techniques apply directly to the full-scale use case with 35,000+ jobs. The memory management utilities have been designed specifically for this scale. 