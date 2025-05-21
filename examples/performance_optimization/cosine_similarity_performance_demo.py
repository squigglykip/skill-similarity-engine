import time
import random
import numpy as np
from tqdm import tqdm
import psutil
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import sys
from pathlib import Path

# Add src to path for local imports
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.utils.chunking import AdaptiveChunker, ChunkingStrategy
from skill_similarity_engine.utils.parallel import ParallelProcessor
from skill_similarity_engine.utils.progress import refreshable_progress_context

# --- Synthetic Data Generation ---
def generate_synthetic_vectors(num_docs=5000, dim=300):
    # Generate random float vectors (simulate TF-IDF or skill vectors)
    rng = np.random.default_rng(42)
    return rng.random((num_docs, dim)).astype(np.float32)

# --- Cosine Similarity Function ---
def cosine_similarity(vec1, vec2):
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

# --- Non-Optimised (Single-threaded) ---
def non_optimised_cosine_all_pairs(vectors):
    n = vectors.shape[0]
    results = np.zeros((n, n), dtype=np.float32)
    for i in tqdm(range(n), desc="Non-optimised", ncols=100):
        for j in range(n):
            results[i, j] = cosine_similarity(vectors[i], vectors[j])
    return results

# --- Optimised (Parallel/Chunked) ---
def chunk_indices(n, chunk_size):
    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        yield (start, end)

def compute_chunk(args):
    vectors, i_start, i_end = args
    n = vectors.shape[0]
    chunk_result = np.zeros((i_end - i_start, n), dtype=np.float32)
    for idx, i in enumerate(range(i_start, i_end)):
        for j in range(n):
            chunk_result[idx, j] = cosine_similarity(vectors[i], vectors[j])
    return (i_start, i_end, chunk_result)

def optimised_cosine_all_pairs(vectors, chunk_size=100):
    n = vectors.shape[0]
    results = np.zeros((n, n), dtype=np.float32)
    indices = list(chunk_indices(n, chunk_size))
    with ProcessPoolExecutor(max_workers=psutil.cpu_count(logical=True)) as executor:
        futures = []
        for i_start, i_end in indices:
            futures.append(executor.submit(compute_chunk, (vectors, i_start, i_end)))
        for fut in tqdm(futures, desc="Optimised (parallel)", ncols=100):
            i_start, i_end, chunk_result = fut.result()
            results[i_start:i_end, :] = chunk_result
    return results

# --- Main Demo Function ---
def cosine_similarity_performance_demo():
    print("\n=== Cosine Similarity Performance Demo ===")
    num_docs = 10000
    dim = 300
    chunk_size = 100
    print(f"[INFO] Generating {num_docs} synthetic vectors of dimension {dim}...")
    vectors = generate_synthetic_vectors(num_docs=num_docs, dim=dim)
    print(f"[INFO] Computing all pairwise cosine similarities ({num_docs} x {num_docs})")

    # Non-optimised
    print("\n--- Non-optimised (single-threaded) ---")
    start = time.time()
    non_opt_results = non_optimised_cosine_all_pairs(vectors)
    non_opt_time = time.time() - start
    print(f"[RESULT] Non-optimised: {non_opt_time:.2f} seconds.")

    # Optimised
    print("\n--- Optimised (parallel/chunked) ---")
    start = time.time()
    opt_results = optimised_cosine_all_pairs(vectors, chunk_size=chunk_size)
    opt_time = time.time() - start
    print(f"[RESULT] Optimised: {opt_time:.2f} seconds.")

    # Check correctness
    diff = np.abs(non_opt_results - opt_results).max()
    print(f"[CHECK] Max abs diff: {diff:.6f}")

    speedup = non_opt_time / opt_time if opt_time > 0 else float('inf')
    print("\n=== BENCHMARK RESULT ===")
    print(f"Docs: {num_docs}")
    print(f"Non-optimised: {non_opt_time:.2f} seconds")
    print(f"Optimised:    {opt_time:.2f} seconds")
    print(f"Speedup:      {speedup:.2f}x")
    print(f"Max diff:     {diff:.6f}")
    print("\nBenchmark complete.")

if __name__ == "__main__":
    cosine_similarity_performance_demo() 