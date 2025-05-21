import time
import numpy as np
from tqdm import tqdm
import psutil
from pathlib import Path
import sys

# Add src to path for local imports
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.utils.progress import ProgressTracker
from skill_similarity_engine.utils.progress_file import ProgressStatsRecorder, CheckpointManager
from skill_similarity_engine.utils.chunking import AdaptiveChunker, ChunkingStrategy
from skill_similarity_engine.utils.parallel import ParallelProcessor

# --- Synthetic Data Generation ---
def generate_synthetic_vectors(num_docs=5000, dim=300):
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

def compute_cosine_row(args):
    vectors, i = args
    n = vectors.shape[0]
    row_result = np.zeros(n, dtype=np.float32)
    for j in range(n):
        row_result[j] = cosine_similarity(vectors[i], vectors[j])
    return (i, row_result)

def cosine_similarity_progress_demo():
    print("\n=== Cosine Similarity Progress Demo (with interruption, chunking, parallel, checkpoint) ===")
    num_docs = 5000
    dim = 300
    chunk_size = 100
    interruption_chunk = 14  # Simulate interruption after this many chunks
    print(f"[INFO] Generating {num_docs} synthetic vectors of dimension {dim}...")
    vectors = generate_synthetic_vectors(num_docs=num_docs, dim=dim)
    print(f"[INFO] Computing all pairwise cosine similarities ({num_docs} x {num_docs}) in chunks of {chunk_size}")

    n = vectors.shape[0]
    # Use AdaptiveChunker for chunking
    chunker = AdaptiveChunker(list(range(n)), strategy=ChunkingStrategy(
        initial_chunk_size=chunk_size,
        min_chunk_size=50,
        max_chunk_size=200,
        memory_threshold_percent=80.0,
        target_memory_percent=60.0
    ))
    chunks = list(chunker.chunks())
    total_chunks = len(chunks)

    # Set up progress tracker, file recorder, and checkpointing
    tracker = ProgressTracker(total=total_chunks, desc="Cosine Chunks", memory_tracking=True, log_interval=1)
    recorder = ProgressStatsRecorder(tracker, "progress.json", interval=1)
    checkpoint = CheckpointManager("checkpoint.json")

    # Resume logic
    last_chunk = checkpoint.load()
    start_chunk = last_chunk + 1 if last_chunk is not None else 0
    if start_chunk > 0:
        print(f"[INFO] Resuming from chunk {start_chunk} (skipping {start_chunk} already completed chunks)")

    results = np.zeros((n, n), dtype=np.float32)
    processor = ParallelProcessor(max_workers=psutil.cpu_count(logical=True))

    try:
        with tracker:
            for chunk_idx, chunk in enumerate(tqdm(chunks, desc="Chunks", ncols=100), start=0):
                if chunk_idx < start_chunk:
                    continue  # Skip already processed chunks
                if chunk_idx == interruption_chunk:
                    print(f"\n[SIMULATION] Interrupting process after chunk {chunk_idx}. Exiting early...")
                    checkpoint.save(chunk_idx - 1)  # Save last completed chunk
                    raise KeyboardInterrupt("Simulated interruption for demo.")
                # Use ParallelProcessor for this chunk
                args = [(vectors, i) for i in chunk]
                chunk_results = processor.map(compute_cosine_row, args)
                for i, row_result in chunk_results:
                    results[i, :] = row_result
                tracker.update(1)
                recorder.maybe_record()
                checkpoint.save(chunk_idx)
                time.sleep(0.05)
    except KeyboardInterrupt:
        print("\n[INFO] Process interrupted! Progress and checkpoint up to this point are saved.")
        print("[INFO] You can resume from the last completed chunk using the checkpoint.")
        return

    print("\n[INFO] All chunks processed. Progress written to progress.json and checkpoint.json after each chunk.")
    print("[INFO] You can inspect progress.json at any time during the run to see current progress.")
    print("[INFO] Demo complete.")

if __name__ == "__main__":
    cosine_similarity_progress_demo() 