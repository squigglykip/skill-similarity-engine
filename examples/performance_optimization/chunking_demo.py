import sys
from pathlib import Path
import numpy as np
import random
import time
import os

# Add the project src directory to the path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.utils.chunking import (
    ChunkingStrategy, AdaptiveChunker, IndexChunker, StreamingChunkProcessor, BatchQueueManager, ResumableBatchProcessor
)
from skill_similarity_engine.utils.performance import get_memory_usage
from skill_similarity_engine.utils.progress import ProgressTracker, MultiProgressTracker

def print_memory_usage():
    mem = get_memory_usage()
    print(f"Current process memory: {mem.current_process_usage_mb:.2f} MB")

def demo_adaptive_chunker():
    print("\n=== AdaptiveChunker Demo ===")
    data = list(range(10000))
    strategy = ChunkingStrategy(initial_chunk_size=1000, min_chunk_size=100, max_chunk_size=2000)
    chunker = AdaptiveChunker(data, strategy)
    chunk_count = 0
    with ProgressTracker(total=len(data)//strategy.initial_chunk_size + 1, desc="AdaptiveChunker", show_tqdm=True) as progress:
        for chunk in chunker.chunks():
            print(f"Chunk {chunk_count+1}: size={len(chunk)} (first={chunk[0]}, last={chunk[-1]})")
            chunk_count += 1
            progress.update(1)
            if chunk_count % 3 == 0:
                print_memory_usage()
    print(f"Total chunks: {chunk_count}")

def demo_index_chunker():
    print("\n=== IndexChunker Demo ===")
    size = 5000
    strategy = ChunkingStrategy(initial_chunk_size=500, min_chunk_size=100, max_chunk_size=1000)
    chunker = IndexChunker(size, strategy)
    chunk_count = 0
    total_chunks = size // strategy.initial_chunk_size + 1
    with ProgressTracker(total=total_chunks, desc="IndexChunker", show_tqdm=True) as progress:
        for start, end in chunker.index_chunks():
            print(f"Index chunk {chunk_count+1}: {start}-{end} (size={end-start})")
            chunk_count += 1
            progress.update(1)
            if chunk_count % 5 == 0:
                print_memory_usage()
    print(f"Total index chunks: {chunk_count}")

def demo_streaming_chunk_processor():
    print("\n=== StreamingChunkProcessor Demo ===")
    data = np.random.rand(10000)
    strategy = ChunkingStrategy(initial_chunk_size=1000, min_chunk_size=200, max_chunk_size=2000)
    chunker = AdaptiveChunker(list(data), strategy)
    def process_fn(chunk):
        # Simulate some processing
        time.sleep(0.01)
        return np.sum(chunk)
    # Count total chunks for progress bar
    total_chunks = len(data) // strategy.initial_chunk_size + 1
    with ProgressTracker(total=total_chunks, desc="StreamingChunkProcessor", show_tqdm=True) as progress:
        def progress_callback(idx):
            progress.update(1)
        processor = StreamingChunkProcessor(chunker, process_fn, progress_callback=progress_callback)
        results = list(processor.process())
    print(f"Processed {len(results)} chunks. Example result: {results[0]:.4f}")

def demo_batch_queue_manager():
    print("\n=== BatchQueueManager Demo (FIFO) ===")
    def batch_gen():
        for i in range(10):
            yield list(range(i*100, (i+1)*100))
    bqm = BatchQueueManager(batch_gen(), max_memory_mb=2, estimate_batch_size_fn=lambda b: 0.5)
    bqm.fill_queue()
    count = 0
    total_batches = 10
    with ProgressTracker(total=total_batches, desc="BatchQueueManager", show_tqdm=True) as progress:
        while bqm.has_more_batches():
            batch = bqm.get_next_batch()
            if batch is not None:
                print(f"Processing batch {count+1}, size={len(batch)}")
                count += 1
                progress.update(1)
                bqm.fill_queue()
    print(f"Total batches processed: {count}")

def demo_batch_queue_manager_priority():
    print("\n=== BatchQueueManager Demo (Priority) ===")
    def batch_gen():
        for i in range(10):
            # Random priority, lower = higher priority
            yield (random.randint(1, 5), list(range(i*100, (i+1)*100)))
    bqm = BatchQueueManager(batch_gen(), max_memory_mb=2, estimate_batch_size_fn=lambda b: 0.5, use_priority=True)
    bqm.fill_queue()
    count = 0
    total_batches = 10
    with ProgressTracker(total=total_batches, desc="BatchQueueManagerPriority", show_tqdm=True) as progress:
        while bqm.has_more_batches():
            batch = bqm.get_next_batch()
            if batch is not None:
                priority, data = batch
                print(f"Processing batch {count+1}, priority={priority}, size={len(data)}")
                count += 1
                progress.update(1)
                bqm.fill_queue()
    print(f"Total priority batches processed: {count}")

def demo_batch_size_benchmark():
    print("\n=== BatchSizeBenchmark Demo ===")
    from skill_similarity_engine.utils.chunking import BatchSizeBenchmark
    data = list(range(10000))
    batch_sizes = [100, 500, 1000, 2000, 5000]
    def process_fn(batch):
        # Simulate some processing
        time.sleep(0.005)
        return sum(batch)
    benchmark = BatchSizeBenchmark(data, process_fn, batch_sizes)
    results = benchmark.run()
    print("Batch Size | Avg Time/Batch (s) | Avg Mem Delta (MB) | Num Batches")
    print("---------------------------------------------------------------")
    for r in results:
        print(f"{r['batch_size']:10d} | {r['avg_time_per_batch']:.4f}         | {r['avg_mem_delta_per_batch']:.4f}           | {r['num_batches']:11d}")

def demo_resumable_batch_processor():
    print("\n=== ResumableBatchProcessor Demo ===")
    checkpoint_path = "resumable_demo_checkpoint.json"
    data = list(range(1000))
    batch_size = 100
    batches = [data[i:i+batch_size] for i in range(0, len(data), batch_size)]
    def process_fn(batch):
        print(f"Processing batch with first={batch[0]}, last={batch[-1]}")
        time.sleep(0.01)
        return sum(batch)

    # Simulate first run (interrupted after 3 batches)
    print("First run (simulate interruption after 3 batches):")
    processor = ResumableBatchProcessor(batches, process_fn, checkpoint_path=checkpoint_path)
    results = []
    with ProgressTracker(total=len(batches), desc="ResumableBatchProcessor", show_tqdm=True) as progress:
        for idx, batch in enumerate(batches):
            if idx < 3:
                result = process_fn(batch)
                processor._save_checkpoint(idx)
                results.append(result)
                progress.update(1)
            else:
                print("Simulating interruption!")
                break

    # Simulate resume
    print("\nResuming from checkpoint:")
    processor2 = ResumableBatchProcessor(batches, process_fn, checkpoint_path=checkpoint_path)
    with ProgressTracker(total=len(batches)-3, desc="ResumableBatchProcessor (Resume)", show_tqdm=True) as progress:
        resumed_results = processor2.process()
        for _ in resumed_results:
            progress.update(1)
    print(f"Resumed and processed remaining {len(batches) - 3} batches.")

    # Clean up checkpoint file
    processor2.clear_checkpoint()
    if not os.path.exists(checkpoint_path):
        print("Checkpoint file cleaned up.")

def demo_nested_progress():
    print("\n=== Nested Progress Demo (MultiProgressTracker) ===")
    num_batches = 5
    chunks_per_batch = 8
    with MultiProgressTracker() as mpt:
        batch_tracker = mpt.add_tracker("batches", total=num_batches, desc="Batches")
        for b in range(num_batches):
            time.sleep(0.1)  # Simulate batch processing
            batch_tracker.update(1)
            chunk_tracker = mpt.add_tracker("chunks", total=chunks_per_batch, desc=f"Chunks (Batch {b+1})")
            for c in range(chunks_per_batch):
                time.sleep(0.05)  # Simulate chunk processing
                chunk_tracker.update(1)
            mpt.stop_tracker("chunks")
    print("Nested progress demo complete.")

if __name__ == "__main__":
    demo_adaptive_chunker()
    demo_index_chunker()
    demo_streaming_chunk_processor()
    demo_batch_queue_manager()
    demo_batch_queue_manager_priority()
    demo_batch_size_benchmark()
    demo_resumable_batch_processor()
    demo_nested_progress()
