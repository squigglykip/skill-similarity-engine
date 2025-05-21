import time
import os
import logging
import psutil
from pathlib import Path

# Add src to path for local imports
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
import sys
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.utils.parallel import ParallelProcessor

def cpu_bound_task(duration_sec: int = 10) -> int:
    """
    Simple CPU-bound task: busy loop for a set duration.
    Returns the number of iterations completed.
    """
    start = time.time()
    count = 0
    while time.time() - start < duration_sec:
        count += 1  # Busy work
    return count

# Top-level function for multiprocessing (must be picklable)
def run_cpu_bound_task(duration):
    return cpu_bound_task(duration)

def monitor_cpu_usage(duration_sec: int, interval: float = 0.5):
    """
    Monitor and print CPU usage per core during the test.
    """
    print(f"Monitoring CPU usage for {duration_sec} seconds...")
    cpu_history = []
    for _ in range(int(duration_sec / interval)):
        usage = psutil.cpu_percent(percpu=True)
        cpu_history.append(usage)
        print(f"CPU usage per core: {['{:.1f}%'.format(u) for u in usage]}")
        time.sleep(interval)
    return cpu_history

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    num_cores = psutil.cpu_count(logical=True)
    print(f"Detected {num_cores} logical CPU cores.")
    duration = 10  # seconds
    print(f"Launching {num_cores} CPU-bound tasks for {duration} seconds each...")

    # Start CPU monitoring in a background thread
    import threading
    cpu_history = []
    monitor_thread = threading.Thread(target=lambda: cpu_history.extend(monitor_cpu_usage(duration, 0.5)))
    monitor_thread.start()

    # Run CPU-bound tasks in parallel using ParallelProcessor
    processor = ParallelProcessor(max_workers=num_cores)
    results = processor.map(run_cpu_bound_task, [duration] * num_cores)

    monitor_thread.join()

    print("\nTest complete. Summary:")
    print(f"Total iterations per task: {results}")
    # Summarise CPU usage
    cpu_history = cpu_history[:int(duration/0.5)]  # Trim in case of overrun
    cpu_history = list(zip(*cpu_history))  # Transpose: list per core
    for i, core_usage in enumerate(cpu_history):
        avg = sum(core_usage) / len(core_usage)
        print(f"Core {i}: Average usage {avg:.1f}% (min {min(core_usage):.1f}%, max {max(core_usage):.1f}%)")
    # Check if all cores were active
    all_active = all(max(core) > 80 for core in cpu_history)
    if all_active:
        print("All CPU cores were fully utilised during the test.")
    else:
        print("Warning: Not all CPU cores reached high utilisation. Check your parallel processing setup.")

if __name__ == "__main__":
    main() 