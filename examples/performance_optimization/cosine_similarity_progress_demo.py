import os
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

# Add src to path for local imports
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.error_handling.checkpoint import Checkpoint
from skill_similarity_engine.error_handling.recovery import retry, error_context
from skill_similarity_engine.logging.paths import get_run_log_dir

RUN_LOG_DIR = get_run_log_dir()
CHECKPOINT_DIR = os.path.join(RUN_LOG_DIR, "checkpoints")

# Parameters
NUM_JOBS = 1000
VECTOR_DIM = 128
CHUNK_SIZE = 100
SIMILARITY_THRESHOLD = 0.9

@retry(max_attempts=3, delay=1.0)
def process_chunk(chunk_idx, job_vectors, checkpoint):
    start = chunk_idx * CHUNK_SIZE
    end = min((chunk_idx + 1) * CHUNK_SIZE, NUM_JOBS)
    chunk = job_vectors[start:end]
    similarities = np.dot(chunk, job_vectors.T)
    norms = np.linalg.norm(chunk, axis=1, keepdims=True) * np.linalg.norm(job_vectors, axis=1)
    similarities = similarities / (norms + 1e-8)
    high_sim_pairs = np.argwhere(similarities > SIMILARITY_THRESHOLD)
    # Save progress
    checkpoint.save({"chunk_idx": chunk_idx, "high_sim_pairs": high_sim_pairs.tolist()})
    print(f"[INFO] Processed chunk {chunk_idx+1}, found {len(high_sim_pairs)} high-similarity pairs.")
    return high_sim_pairs

def cosine_similarity_progress_demo():
    print(f"[INFO] Run started at {datetime.now().isoformat()}")
    print(f"[INFO] Log directory: {RUN_LOG_DIR}")
    print(f"[INFO] Generating {NUM_JOBS} synthetic job vectors of dimension {VECTOR_DIM}...")
    job_vectors = np.random.rand(NUM_JOBS, VECTOR_DIM)
    checkpoint = Checkpoint(CHECKPOINT_DIR, "cosine_demo")
    # Try to resume
    state = checkpoint.load()
    start_chunk = 0
    if state and "chunk_idx" in state:
        start_chunk = state["chunk_idx"] + 1
        print(f"[INFO] Resuming from chunk {start_chunk}")
    else:
        print("[INFO] Starting from scratch.")
    all_high_sim_pairs = []
    try:
        for chunk_idx in range(start_chunk, (NUM_JOBS + CHUNK_SIZE - 1) // CHUNK_SIZE):
            with error_context("process_chunk", chunk_idx=chunk_idx):
                pairs = process_chunk(chunk_idx, job_vectors, checkpoint)
                all_high_sim_pairs.extend(pairs)
    except KeyboardInterrupt:
        print("\n[INFO] Process interrupted! Progress and checkpoint up to this point are saved.")
    print(f"[INFO] Run completed at {datetime.now().isoformat()}")
    print(f"[INFO] Total high-similarity pairs found: {len(all_high_sim_pairs)}")
    # Optionally, save summary to log dir
    summary_path = os.path.join(RUN_LOG_DIR, "summary.txt")
    with open(summary_path, "w") as f:
        f.write(f"Run completed at {datetime.now().isoformat()}\n")
        f.write(f"Total high-similarity pairs found: {len(all_high_sim_pairs)}\n")

if __name__ == "__main__":
    cosine_similarity_progress_demo() 