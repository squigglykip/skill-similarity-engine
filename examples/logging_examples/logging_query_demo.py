import numpy as np
import sys
from pathlib import Path
from datetime import datetime
import platform
import os

# Add src to path for local imports
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.logging.config import setup_logging

# --- Logging Setup ---
logger = setup_logging(level="INFO", log_to_file=False, formatter="console")

# --- Query Session Start ---
query_start = datetime.now()
logger.info("Query session started", extra={
    "timestamp": query_start.isoformat(),
    "python_version": platform.python_version()
})

# --- Load Precomputed Similarity Matrix ---
matrix_file = "precomputed_similarity.npy"  # Change as needed
if os.path.exists(matrix_file):
    similarity_matrix = np.load(matrix_file)
    logger.info("Loaded precomputed similarity matrix from file", extra={"file": matrix_file, "shape": similarity_matrix.shape})
else:
    # Fallback: create a small synthetic matrix for demo
    similarity_matrix = np.array([
        [1.0, 0.8, 0.2, 0.0],
        [0.8, 1.0, 0.3, 0.1],
        [0.2, 0.3, 1.0, 0.5],
        [0.0, 0.1, 0.5, 1.0]
    ])
    logger.info("Using synthetic similarity matrix for demo", extra={"shape": similarity_matrix.shape})

# --- Query Parameters ---
query_job = 1
top_n = 2
logger.info("User query received", extra={
    "query_type": "top_n_similar_jobs",
    "job_id": query_job,
    "top_n": top_n
})

# --- Perform Query ---
similarities = similarity_matrix[query_job]
top_indices = np.argsort(similarities)[::-1][1:top_n+1]  # Exclude self
results = [{"job_id": int(idx), "similarity": float(similarities[idx])} for idx in top_indices]

logger.info("Query results", extra={
    "job_id": query_job,
    "top_n": top_n,
    "results": results
})

# --- Print Results ---
print(f"\nTop {top_n} similar jobs to job {query_job}:")
for r in results:
    print(f"Job {r['job_id']}: similarity {r['similarity']:.2f}")

# --- Query Session End ---
query_end = datetime.now()
duration = (query_end - query_start).total_seconds()
logger.info("Query session completed", extra={
    "timestamp": query_end.isoformat(),
    "duration_sec": duration
}) 