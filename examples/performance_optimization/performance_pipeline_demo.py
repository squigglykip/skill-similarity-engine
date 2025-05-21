import time
import random
from pathlib import Path
import sys
import string
from tqdm import tqdm
import os
import threading
import numpy as np
import psutil
from collections import defaultdict

# Add src to path for local imports
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.utils.chunking import AdaptiveChunker, ChunkingStrategy
from skill_similarity_engine.utils.performance import get_memory_usage
from skill_similarity_engine.utils.parallel import ParallelProcessor
from skill_similarity_engine.utils.progress import RefreshableProgressDisplay, refreshable_progress_context

class CPUMonitor:
    """
    Monitors CPU usage of our Python script processes during execution.
    
    This class runs in a separate thread, collecting CPU utilization
    statistics at regular intervals only for processes that belong to our script.
    """
    
    def __init__(self, sampling_interval=0.5):
        """
        Initialize the CPU monitor.
        
        Args:
            sampling_interval: Time between CPU usage samples in seconds
        """
        self.sampling_interval = sampling_interval
        self.running = False
        self.thread = None
        self.cpu_samples = defaultdict(list)  # {core_id: [utilization samples]}
        self.overall_samples = []
        self.our_processes = {}  # {pid: process_object}
        self.process_samples = defaultdict(list)  # {pid: [cpu_percent samples]}
        self.process_names = {}  # {pid: name}
        
    def start(self):
        """Start the CPU monitoring thread."""
        self.running = True
        
        # Initialize our process tracking with the current Python process
        self._initialize_process_tracking()
        
        # Start a background thread to collect CPU stats
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True  # Don't block program exit
        self.thread.start()
        
        # Give a little time for baseline CPU measurements to be established
        time.sleep(0.5)
        
    def stop(self):
        """Stop the CPU monitoring thread."""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _initialize_process_tracking(self):
        """Initialize process tracking with the current Python process and establish baseline CPU measurements."""
        # Get the main Python process
        try:
            current_process = psutil.Process()
            self.our_processes[current_process.pid] = current_process
            self.process_names[current_process.pid] = current_process.name()
            
            # Initialize CPU percent for this process (this establishes a baseline)
            current_process.cpu_percent()
            
            # Also get children processes and initialize their CPU percent
            for child in current_process.children(recursive=True):
                try:
                    self.our_processes[child.pid] = child
                    self.process_names[child.pid] = child.name()
                    child.cpu_percent()  # Initialize CPU percent (sets baseline)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    def _update_process_list(self):
        """
        Update the list of processes related to our Python script.
        
        Returns:
            Number of processes being tracked
        """
        # Get the main Python process
        try:
            current_process = psutil.Process()
            
            # Add the main process if not already tracked
            if current_process.pid not in self.our_processes:
                self.our_processes[current_process.pid] = current_process
                self.process_names[current_process.pid] = current_process.name()
                # Initialize CPU percent
                current_process.cpu_percent()
            
            # Update child processes
            children = []
            try:
                children = current_process.children(recursive=True)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
            # Add any new child processes
            for child in children:
                try:
                    if child.pid not in self.our_processes:
                        self.our_processes[child.pid] = child
                        self.process_names[child.pid] = child.name()
                        # Initialize CPU percent
                        child.cpu_percent()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
            # Remove any processes that no longer exist
            for pid in list(self.our_processes.keys()):
                try:
                    # Check if process still exists by accessing a property
                    self.our_processes[pid].is_running()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process no longer exists or can't be accessed
                    del self.our_processes[pid]
                    if pid in self.process_names:
                        del self.process_names[pid]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
        return len(self.our_processes)
    
    def _monitor_loop(self):
        """Main monitoring loop that collects samples."""
        while self.running:
            # Sleep first to give time for baseline CPU measurements to be established
            time.sleep(self.sampling_interval)
            
            # Update our process list
            self._update_process_list()
            
            # Get overall system CPU utilization
            system_percent = psutil.cpu_percent()
            self.overall_samples.append(system_percent)
            
            # Get per-core CPU utilization (includes all processes)
            per_cpu = psutil.cpu_percent(percpu=True)
            for i, util in enumerate(per_cpu):
                self.cpu_samples[i].append(util)
            
            # Sample our script's processes specifically
            for pid, proc in list(self.our_processes.items()):
                try:
                    # Get CPU percent - this will return the percentage since the last call
                    proc_percent = proc.cpu_percent()
                    if proc_percent is not None:  # Guard against None values
                        self.process_samples[pid].append(proc_percent)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process no longer exists or can't be accessed
                    if pid in self.our_processes:
                        del self.our_processes[pid]
                    if pid in self.process_names:
                        del self.process_names[pid]
    
    def get_statistics(self):
        """
        Get statistics about CPU utilization.
        
        Returns:
            Dictionary with CPU statistics
        """
        stats = {
            "per_core": {},
            "system_overall": {},
            "our_processes": {},
            "process_names": self.process_names.copy()
        }
        
        # Calculate statistics per core
        for core_id, samples in self.cpu_samples.items():
            if samples:
                stats["per_core"][core_id] = {
                    "mean": np.mean(samples),
                    "min": np.min(samples),
                    "max": np.max(samples),
                    "stddev": np.std(samples)
                }
        
        # Calculate overall system statistics
        if self.overall_samples:
            stats["system_overall"] = {
                "mean": np.mean(self.overall_samples),
                "min": np.min(self.overall_samples),
                "max": np.max(self.overall_samples),
                "stddev": np.std(self.overall_samples)
            }
        
        # Calculate our processes' statistics
        for pid, samples in self.process_samples.items():
            if samples:
                stats["our_processes"][pid] = {
                    "mean": np.mean(samples),
                    "min": np.min(samples),
                    "max": np.max(samples),
                    "stddev": np.std(samples),
                    "name": self.process_names.get(pid, "Unknown")
                }
        
        # Also calculate combined statistics for all our processes
        all_samples = []
        for samples in self.process_samples.values():
            all_samples.extend(samples)
            
        if all_samples:
            stats["our_processes_combined"] = {
                "mean": np.mean(all_samples),
                "min": np.min(all_samples),
                "max": np.max(all_samples),
                "stddev": np.std(all_samples),
                "count": len(self.process_samples)
            }
        
        return stats
    
    def print_summary(self):
        """Print a summary of CPU utilization."""
        stats = self.get_statistics()
        
        print("\n" + "=" * 80)
        print("CPU UTILISATION SUMMARY:")
        print("-" * 80)
        
        # Print our processes statistics
        if "our_processes_combined" in stats:
            our_processes = stats["our_processes_combined"]
            print(f"OUR SCRIPT PROCESSES ({our_processes['count']} processes):")
            print(f"Average CPU: {our_processes['mean']:.1f}% (Min: {our_processes['min']:.1f}%, Max: {our_processes['max']:.1f}%, StdDev: {our_processes['stddev']:.1f}%)")
            print(f"This represents the CPU utilisation specifically from our Python script processes.")
            
            # Print top 5 processes by CPU usage
            if stats["our_processes"]:
                print("\nTop Python Processes:")
                processes = [(pid, data["mean"], data["name"]) 
                           for pid, data in stats["our_processes"].items()]
                processes.sort(key=lambda x: x[1], reverse=True)
                print(f"{'PID':<8} {'CPU %':<8} {'Name':<20}")
                print("-" * 40)
                for pid, cpu, name in processes[:5]:  # Show top 5
                    print(f"{pid:<8} {cpu:<8.1f} {name:<20}")
            
            print("-" * 80)
        
        # Print overall system statistics
        overall = stats["system_overall"]
        print(f"SYSTEM-WIDE CPU UTILISATION (all processes):")
        print(f"Average CPU: {overall['mean']:.1f}% (Min: {overall['min']:.1f}%, Max: {overall['max']:.1f}%, StdDev: {overall['stddev']:.1f}%)")
        print(f"This includes our script plus all other system and background processes.")
        print("-" * 80)
        
        # Print per-core statistics for the system
        print("\nPer-Core Utilisation (All System Processes):")
        print(f"{'Core':<6} {'Average':<10} {'Min':<8} {'Max':<8} {'StdDev':<10}")
        print("-" * 50)
        
        for core_id in sorted(stats["per_core"].keys()):
            core_stats = stats["per_core"][core_id]
            print(f"{core_id:<6} {core_stats['mean']:<10.1f} {core_stats['min']:<8.1f} {core_stats['max']:<8.1f} {core_stats['stddev']:<10.1f}")
        
        # Calculate and print standard deviation across cores (to show balance)
        core_means = [stats["per_core"][core_id]["mean"] for core_id in stats["per_core"]]
        core_means_stddev = np.std(core_means)
        
        print("\nWork Distribution Analysis:")
        print(f"StdDev Across Cores: {core_means_stddev:.1f}%")
        
        if core_means_stddev < 5:
            print("✅ Work is well-balanced across cores (low standard deviation)")
        elif core_means_stddev < 15:
            print("⚠️ Work distribution has some imbalance across cores")
        else:
            print("❌ Work is poorly balanced across cores (high standard deviation)")
            
        # Provide context about the measurements
        print("\nMEASUREMENT CONTEXT:")
        print("- System measurements include ALL processes running on your Windows system")
        print("- Our script measurements track the Python interpreter and multiprocessing workers")
        print("- 'it/s' in progress bars stands for 'iterations per second' - how many")
        print("  documents are being processed each second")
        print("- Core imbalance may be caused by Windows scheduling algorithms and")
        print("  competition from other system processes")

def generate_synthetic_documents(num_docs=35000, words_per_doc=800):
    # Simulate a realistic job title/description generator
    job_titles = [
        "Data Scientist", "Software Engineer", "Business Analyst", "Project Manager",
        "Senior Solutions Architect", "Lead DevOps Engineer", "AI Researcher", "Cloud Security Specialist",
        "Full Stack Developer", "Machine Learning Engineer", "HR Business Partner", "Finance Operations Lead",
        "Customer Experience Manager", "Digital Product Owner", "Risk & Compliance Analyst"
    ]
    vocab = [f"word{i}" for i in range(2000)]
    phrases = [
        "stakeholder engagement", "agile transformation", "cloud migration", "regulatory compliance",
        "cross-functional team", "continuous improvement", "customer-centric approach", "data-driven insights",
        "end-to-end delivery", "strategic alignment", "process automation", "change management"
    ]
    punctuation = list(string.punctuation)
    docs = []
    for _ in range(num_docs):
        # Start with a random job title (multi-word)
        doc = [random.choice(job_titles)]
        # Add a mix of phrases, vocab, numbers, and punctuation
        for _ in range(words_per_doc):
            r = random.random()
            if r < 0.05:
                doc.append(random.choice(phrases))
            elif r < 0.10:
                doc.append(str(random.randint(100, 9999)))
            elif r < 0.12:
                doc.append(random.choice(punctuation))
            else:
                doc.append(random.choice(vocab))
        docs.append(" ".join(doc))
    return docs

def fake_tfidf_vectorise(doc):
    # Simulate CPU work
    time.sleep(0.002)
    return hash(doc) % 1000

def non_optimized_process(docs):
    """
    Process documents without any optimizations - single-threaded, no chunking.
    This serves as a baseline for comparison with the optimized version.
    """
    results = []
    for doc in tqdm(docs, desc="Non-optimized processing", ncols=100):
        # Simulate CPU work (same as optimized version)
        time.sleep(0.002)
        results.append(hash(doc) % 1000)
    return results

def performance_pipeline_demo():
    # Create header messages for the progress display
    header_messages = [
        "[WARNING] This demo will generate and process 35,000 large, complex synthetic documents.",
        "This will put significant strain on memory and CPU.",
        "Monitor your system resources and be prepared for a longer runtime.",
        "[INFO] Generating synthetic documents...",
        "[INFO] Running both optimized and non-optimized versions for comparison..."
    ]
    
    print("\n=== Performance Pipeline Demo ===")
    print("[WARNING] This demo will generate and process 35,000 large, complex synthetic documents.\n"
          "This will put significant strain on memory and CPU.\n"
          "Monitor your system resources and be prepared for a longer runtime.")
    print("[INFO] Generating synthetic documents...")
    docs = generate_synthetic_documents(num_docs=35000, words_per_doc=800)
    total_docs = len(docs)
    
    # Create the CPU monitor - start it before processing
    cpu_monitor = CPUMonitor(sampling_interval=1.0)
    cpu_monitor.start()
    
    # Wait a moment for CPU monitoring to establish baselines
    time.sleep(1)
    
    # First run the non-optimized version
    print("\n=== Running Non-optimized Version ===")
    start_time = time.time()
    non_optimized_results = non_optimized_process(docs)
    non_optimized_time = time.time() - start_time
    
    # Get CPU stats for non-optimized run
    non_optimized_stats = cpu_monitor.get_statistics()
    
    # Reset CPU monitor for optimized run
    cpu_monitor.stop()
    time.sleep(1)  # Give time for monitoring to stop
    cpu_monitor = CPUMonitor(sampling_interval=1.0)
    cpu_monitor.start()
    time.sleep(1)  # Give time for new baseline
    
    # Now run the optimized version
    print("\n=== Running Optimized Version ===")
    print("[INFO] Setting up AdaptiveChunker from chunking.py (memory-aware chunking)...")
    chunk_size = 1000
    strategy = ChunkingStrategy(
        initial_chunk_size=chunk_size,
        min_chunk_size=200,
        max_chunk_size=2000,
        memory_threshold_percent=60.0,  # Lower to trigger adaptation sooner
        target_memory_percent=50.0
    )
    chunker = AdaptiveChunker(docs, strategy)
    
    # Get all chunks in advance
    chunks = list(chunker.chunks())
    
    # Create processor with explicit max_workers to demonstrate parallelism
    num_cores = psutil.cpu_count(logical=True)
    processor = ParallelProcessor(max_workers=num_cores, memory_limit_mb=2000)
    
    print(f"[INFO] Starting parallel processing with {num_cores} cores")
    total_processed = 0
    
    # Use the refreshable_progress_context for clean, platform-independent progress display
    with refreshable_progress_context(
        total_items=total_docs,
        title="=== Optimized Processing ===",
        header_messages=header_messages
    ) as progress:
        # Process each chunk with a progress bar
        for i, chunk in enumerate(chunks):
            # Create and display chunk progress bar
            with tqdm(total=len(chunk), desc=f"Chunk {i+1}", ncols=100, leave=True) as chunk_bar:
                # Process the chunk
                results = list(processor.map(fake_tfidf_vectorise, chunk))
                
                # Update chunk progress
                for _ in results:
                    chunk_bar.update(1)
            
            # After chunk completes, update total progress
            total_processed += len(chunk)
            progress.update_total_progress(total_processed)
            progress.add_completed_chunk(i+1, len(chunk))
    
    # Get timing for optimized run
    optimized_time = time.time() - start_time
    
    # Stop CPU monitoring and get statistics
    time.sleep(1)
    cpu_monitor.stop()
    optimized_stats = cpu_monitor.get_statistics()
    
    # Print comparison summary
    print("\n" + "=" * 80)
    print("PERFORMANCE COMPARISON SUMMARY:")
    print("-" * 80)
    print(f"Total documents processed: {total_docs}")
    print("\nTiming:")
    print(f"Non-optimized version: {non_optimized_time:.2f} seconds")
    print(f"Optimized version: {optimized_time:.2f} seconds")
    print(f"Speedup factor: {non_optimized_time/optimized_time:.2f}x")
    
    print("\nCPU Utilization:")
    print("Non-optimized version:")
    if "our_processes_combined" in non_optimized_stats:
        non_opt_cpu = non_optimized_stats["our_processes_combined"]
        print(f"  Average CPU: {non_opt_cpu['mean']:.1f}%")
        print(f"  Max CPU: {non_opt_cpu['max']:.1f}%")
    
    print("\nOptimized version:")
    if "our_processes_combined" in optimized_stats:
        opt_cpu = optimized_stats["our_processes_combined"]
        print(f"  Average CPU: {opt_cpu['mean']:.1f}%")
        print(f"  Max CPU: {opt_cpu['max']:.1f}%")
    
    print("\nCore Utilization:")
    print("Non-optimized version:")
    for core_id in sorted(non_optimized_stats["per_core"].keys()):
        core_stats = non_optimized_stats["per_core"][core_id]
        print(f"  Core {core_id}: {core_stats['mean']:.1f}% average")
    
    print("\nOptimized version:")
    for core_id in sorted(optimized_stats["per_core"].keys()):
        core_stats = optimized_stats["per_core"][core_id]
        print(f"  Core {core_id}: {core_stats['mean']:.1f}% average")
    
    print("\n" + "=" * 80)
    print("\nPipeline demo complete. All modules demonstrated:")
    print("- chunking.py: AdaptiveChunker (memory-aware chunking)")
    print("- performance.py: get_memory_usage (RAM monitoring)")
    print("- progress.py: RefreshableProgressDisplay (overall + per-chunk progress)")
    print("- parallel.py: ParallelProcessor (CPU core utilisation)")

if __name__ == "__main__":
    performance_pipeline_demo() 