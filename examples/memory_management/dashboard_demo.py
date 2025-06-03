#!/usr/bin/env python
"""
Memory Dashboard Demonstration

This example demonstrates how to use the memory dashboard to track and visualize
memory usage during a simulated data processing workflow.
"""

import os
import time
import random
import numpy as np
from pathlib import Path

# Add the project src directory to the path
import sys
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.utils.memory_dashboard import start_memory_dashboard

def simulate_large_data_loading(size_mb=100):
    """Simulate loading large data into memory."""
    print(f"Loading {size_mb}MB of data...")
    # Create large numpy arrays to simulate data loading
    # Each float64 takes 8 bytes, so 1MB = 131,072 floats
    data = []
    MB = 131_072  # Number of float64 values in 1MB
    
    # Create arrays in chunks to simulate progressive loading
    chunk_size = 10  # MB per chunk
    total_chunks = size_mb // chunk_size
    
    for i in range(total_chunks):
        # Create a chunk of data
        chunk = np.random.randn(chunk_size * MB)
        data.append(chunk)
        time.sleep(0.5)  # Simulate I/O time
        
    return data

def simulate_vectorization(data, dimensions=10_000):
    """Simulate vectorizing job data into high-dimensional space."""
    print(f"Vectorizing data into {dimensions} dimensions...")
    vectors = []
    
    for i, chunk in enumerate(data):
        # Create sparse vectors to simulate job vectorization
        # Most jobs only have a small subset of all possible skills
        for j in range(len(chunk) // 10_000):  # Create vectors from chunks
            # Create a sparse vector (mostly zeros)
            vector = np.zeros(dimensions)
            # Set about 1% of dimensions to non-zero
            indices = random.sample(range(dimensions), dimensions // 100)
            vector[indices] = np.abs(chunk[j*100:(j+1)*100])  # Use some values from data
            vectors.append(vector)
            
            if j % 10 == 0:
                time.sleep(0.1)  # Simulate processing time
                
    return vectors

def simulate_similarity_calculation(vectors, max_comparisons=100_000):
    """Simulate calculating similarity between vectors."""
    print(f"Calculating similarity between vectors (max: {max_comparisons} comparisons)...")
    similarities = {}
    
    # Limit the total number of comparisons for the demo
    comparison_count = 0
    n = len(vectors)
    
    for i in range(n):
        for j in range(i+1, n):
            # Calculate cosine similarity between vectors[i] and vectors[j]
            dot_product = np.dot(vectors[i], vectors[j])
            norm_i = np.linalg.norm(vectors[i])
            norm_j = np.linalg.norm(vectors[j])
            
            if norm_i > 0 and norm_j > 0:  # Avoid division by zero
                similarity = dot_product / (norm_i * norm_j)
            else:
                similarity = 0
                
            similarities[(i, j)] = similarity
            
            comparison_count += 1
            if comparison_count >= max_comparisons:
                break
        
        if comparison_count >= max_comparisons:
            break
            
        if i % 10 == 0:
            time.sleep(0.1)  # Simulate processing time
            
    return similarities

def main():
    # Create an output directory for the memory reports
    output_dir = os.path.join(os.path.dirname(__file__), "memory_reports")
    os.makedirs(output_dir, exist_ok=True)
    
    # Start the memory dashboard with 0.5-second intervals
    print("Starting memory dashboard...")
    dashboard = start_memory_dashboard(
        output_dir=output_dir,
        monitor_interval=0.5
    )
    
    try:
        # Mark the starting point
        dashboard.mark_event("Start")
        time.sleep(1)  # Pause to establish baseline
        
        # Load large dataset
        dashboard.mark_event("Begin data loading")
        data = simulate_large_data_loading(size_mb=200)
        dashboard.mark_event("Data loading complete")
        
        # Generate a report after data loading
        dashboard.tracker.save_plot(
            os.path.join(output_dir, "memory_after_loading.png"),
            show_details=True
        )
        
        # Vectorize the data
        dashboard.mark_event("Begin vectorization")
        vectors = simulate_vectorization(data)
        
        # Remove the raw data to free up memory
        del data
        dashboard.mark_event("Vectors created, raw data released")
        
        # Generate a report after vectorization
        dashboard.tracker.save_plot(
            os.path.join(output_dir, "memory_after_vectorization.png"),
            show_details=True
        )
        
        # Calculate similarities
        dashboard.mark_event("Begin similarity calculation")
        similarities = simulate_similarity_calculation(vectors)
        dashboard.mark_event("Similarity calculation complete")
        
        # Generate a final report with prediction
        dashboard.mark_event("Processing complete")
        report_dir = dashboard.generate_report(include_prediction=True)
        print(f"Memory report generated in: {report_dir}")
        
    finally:
        # Always stop monitoring
        dashboard.stop_monitoring()
        print("Memory monitoring stopped.")
        print(f"Check {output_dir} for visualizations and reports.")

if __name__ == "__main__":
    main() 