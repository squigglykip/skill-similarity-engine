import numpy as np
import sys
from pathlib import Path
from datetime import datetime
import platform
import random

# Add src to path for local imports
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.logging.config import setup_logging

# --- Logging Setup ---
logger = setup_logging(level="INFO", log_to_file=False, formatter="console")

# --- Log Run Start and Configuration ---
run_start = datetime.now()
config = {
    "num_jobs": 10,
    "num_skills": 6,
    "sparsity": 0.7
}
logger.info("Run started", extra={
    "timestamp": run_start.isoformat(),
    "config": config,
    "python_version": platform.python_version()
})

# --- Data Generation Stage ---
logger.info("Data generation started", extra={"stage": "data_generation"})
num_jobs = config["num_jobs"]
num_skills = config["num_skills"]
sparsity = config["sparsity"]

job_vectors = np.zeros((num_jobs, num_skills), dtype=np.float32)
for i in range(num_jobs):
    num_active = max(1, int(num_skills * (1 - sparsity)))
    active_skills = random.sample(range(num_skills), num_active)
    job_vectors[i, active_skills] = np.random.uniform(0.1, 1.0, size=num_active)
logger.info("Data generation complete", extra={"stage": "data_generation", "vector_shape": job_vectors.shape})

# --- Cosine Similarity Calculation Stage ---
logger.info("Similarity calculation started", extra={"stage": "similarity"})
def cosine_similarity(vec1, vec2):
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

similarity_matrix = np.zeros((num_jobs, num_jobs), dtype=np.float32)
for i in range(num_jobs):
    for j in range(num_jobs):
        similarity_matrix[i, j] = cosine_similarity(job_vectors[i], job_vectors[j])
logger.info("Similarity calculation complete", extra={"stage": "similarity"})

# --- Log End of Run and Summary ---
run_end = datetime.now()
duration = (run_end - run_start).total_seconds()
max_sim = float(np.max(similarity_matrix[np.triu_indices(num_jobs, k=1)]))
logger.info("Run completed", extra={
    "timestamp": run_end.isoformat(),
    "duration_sec": duration,
    "output": "in-memory (demo)",
    "max_similarity": max_sim
})

# --- Print a sample of the similarity matrix ---
print("\nSample similarity matrix:")
print(np.round(similarity_matrix, 2))

# --- (Optional) Emulate a user query against the precomputed matrix ---
query_job = 0
top_n = 3
similarities = similarity_matrix[query_job]
top_indices = np.argsort(similarities)[::-1][1:top_n+1]
logger.info("User query", extra={
    "query_type": "top_n_similar_jobs",
    "job_id": query_job,
    "top_n": top_n,
    "results": [{"job_id": int(idx), "similarity": float(similarities[idx])} for idx in top_indices]
})
print(f"\nTop {top_n} similar jobs to job {query_job}:")
for idx in top_indices:
    print(f"Job {idx}: similarity {similarities[idx]:.2f}") 