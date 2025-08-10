"""
Parallel Processing Framework

This module provides a framework for parallel processing with memory awareness.
It enables efficient distribution of tasks across CPU cores while respecting
memory constraints, which is essential for processing large datasets (35,000+ jobs)
on standard hardware.
"""

import os
import time
import logging
import multiprocessing as mp
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import List, Callable, Any, TypeVar, Dict, Tuple, Iterator, Optional, Set
from dataclasses import dataclass, field
import threading
import queue
from collections import defaultdict

import psutil
import numpy as np

from .performance import get_memory_usage, trigger_garbage_collection
from .matrix_chunking import MatrixChunk
from .progress import ProgressTracker

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class CPUUtilizationSnapshot:
    """Snapshot of CPU utilization at a specific point in time"""
    timestamp: float
    overall_cpu_percent: float
    per_core_cpu_percent: List[float]
    cpu_count_logical: int
    cpu_count_physical: int
    load_average: Optional[Tuple[float, float, float]]  # 1min, 5min, 15min (Unix only)
    active_processes: int
    
    @property
    def average_core_utilization(self) -> float:
        """Average utilization across all cores"""
        return sum(self.per_core_cpu_percent) / len(self.per_core_cpu_percent) if self.per_core_cpu_percent else 0.0
    
    @property
    def max_core_utilization(self) -> float:
        """Maximum utilization of any single core"""
        return max(self.per_core_cpu_percent) if self.per_core_cpu_percent else 0.0
    
    @property
    def min_core_utilization(self) -> float:
        """Minimum utilization of any single core"""
        return min(self.per_core_cpu_percent) if self.per_core_cpu_percent else 0.0
    
    @property
    def core_utilization_variance(self) -> float:
        """Variance in core utilization (indicates load balancing)"""
        if not self.per_core_cpu_percent:
            return 0.0
        avg = self.average_core_utilization
        return sum((x - avg) ** 2 for x in self.per_core_cpu_percent) / len(self.per_core_cpu_percent)


@dataclass
class ProcessingPerformanceMetrics:
    """Comprehensive performance metrics for parallel processing"""
    start_time: float
    end_time: float
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    
    # CPU metrics
    cpu_snapshots: List[CPUUtilizationSnapshot] = field(default_factory=list)
    peak_cpu_utilization: float = 0.0
    average_cpu_utilization: float = 0.0
    cpu_efficiency_score: float = 0.0  # How well we utilized available cores
    
    # Memory metrics
    peak_memory_mb: float = 0.0
    average_memory_mb: float = 0.0
    memory_growth_mb: float = 0.0
    
    # Parallelization metrics
    workers_used: int = 0
    theoretical_speedup: float = 1.0
    actual_speedup: float = 1.0
    parallel_efficiency: float = 0.0  # actual_speedup / theoretical_speedup
    
    # Task distribution metrics
    tasks_per_worker: Dict[int, int] = field(default_factory=dict)
    worker_idle_time: Dict[int, float] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Total processing duration in seconds"""
        return self.end_time - self.start_time
    
    @property
    def tasks_per_second(self) -> float:
        """Average tasks completed per second"""
        return self.successful_tasks / self.duration if self.duration > 0 else 0.0
    
    @property
    def success_rate(self) -> float:
        """Percentage of tasks that completed successfully"""
        return (self.successful_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0.0
    
    def get_summary_report(self) -> str:
        """Generate a comprehensive performance report"""
        lines = [
            "🚀 Parallel Processing Performance Report",
            "=" * 50,
            f"📊 Task Metrics:",
            f"   • Total tasks: {self.total_tasks:,}",
            f"   • Successful: {self.successful_tasks:,} ({self.success_rate:.1f}%)",
            f"   • Failed: {self.failed_tasks:,}",
            f"   • Duration: {self.duration:.2f}s",
            f"   • Throughput: {self.tasks_per_second:.1f} tasks/sec",
            "",
            f"🖥️ CPU Utilization:",
            f"   • Peak CPU: {self.peak_cpu_utilization:.1f}%",
            f"   • Average CPU: {self.average_cpu_utilization:.1f}%",
            f"   • CPU Efficiency: {self.cpu_efficiency_score:.1f}%",
            "",
            f"⚡ Parallelization Effectiveness:",
            f"   • Workers used: {self.workers_used}",
            f"   • Theoretical speedup: {self.theoretical_speedup:.1f}x",
            f"   • Actual speedup: {self.actual_speedup:.1f}x",
            f"   • Parallel efficiency: {self.parallel_efficiency:.1f}%",
            "",
            f"💾 Memory Usage:",
            f"   • Peak memory: {self.peak_memory_mb:.1f} MB",
            f"   • Average memory: {self.average_memory_mb:.1f} MB",
            f"   • Memory growth: {self.memory_growth_mb:+.1f} MB",
        ]
        
        if self.tasks_per_worker:
            lines.extend([
                "",
                f"👥 Worker Distribution:",
            ])
            for worker_id, task_count in self.tasks_per_worker.items():
                idle_time = self.worker_idle_time.get(worker_id, 0.0)
                lines.append(f"   • Worker {worker_id}: {task_count} tasks, {idle_time:.1f}s idle")
        
        return "\n".join(lines)


class CPUUtilizationTracker:
    """Tracks CPU utilization during parallel processing"""
    
    def __init__(self, sampling_interval: float = 0.5):
        """
        Initialize CPU tracker.
        
        Args:
            sampling_interval: How often to sample CPU usage (seconds)
        """
        self.sampling_interval = sampling_interval
        self.snapshots: List[CPUUtilizationSnapshot] = []
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(__name__)
    
    def start_monitoring(self):
        """Start CPU utilization monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.snapshots.clear()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info(f"Started CPU monitoring (interval: {self.sampling_interval}s)")
    
    def stop_monitoring(self):
        """Stop CPU utilization monitoring"""
        if not self.monitoring:
            return
        
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        
        self.logger.info(f"Stopped CPU monitoring ({len(self.snapshots)} samples collected)")
    
    def _monitor_loop(self):
        """Main monitoring loop (runs in separate thread)"""
        while self.monitoring:
            try:
                snapshot = self._take_snapshot()
                self.snapshots.append(snapshot)
                time.sleep(self.sampling_interval)
            except Exception as e:
                self.logger.warning(f"Error taking CPU snapshot: {e}")
                time.sleep(self.sampling_interval)
    
    def _take_snapshot(self) -> CPUUtilizationSnapshot:
        """Take a snapshot of current CPU utilization"""
        # Get overall CPU usage
        overall_cpu = psutil.cpu_percent(interval=None)
        
        # Get per-core CPU usage
        per_core_cpu = psutil.cpu_percent(interval=None, percpu=True)
        
        # Get CPU counts
        logical_cores = psutil.cpu_count(logical=True)
        physical_cores = psutil.cpu_count(logical=False)
        
        # Get load average (Unix only)
        load_avg = None
        if hasattr(os, 'getloadavg'):
            try:
                load_avg = os.getloadavg()
            except (OSError, AttributeError):
                pass
        
        # Count active processes
        active_processes = len(psutil.pids())
        
        return CPUUtilizationSnapshot(
            timestamp=time.time(),
            overall_cpu_percent=overall_cpu,
            per_core_cpu_percent=per_core_cpu,
            cpu_count_logical=logical_cores,
            cpu_count_physical=physical_cores,
            load_average=load_avg,
            active_processes=active_processes
        )
    
    def get_peak_utilization(self) -> float:
        """Get peak CPU utilization during monitoring"""
        if not self.snapshots:
            return 0.0
        return max(snapshot.overall_cpu_percent for snapshot in self.snapshots)
    
    def get_average_utilization(self) -> float:
        """Get average CPU utilization during monitoring"""
        if not self.snapshots:
            return 0.0
        return sum(snapshot.overall_cpu_percent for snapshot in self.snapshots) / len(self.snapshots)
    
    def get_core_utilization_analysis(self) -> Dict[str, float]:
        """Analyze how well cores were utilized"""
        if not self.snapshots:
            return {}
        
        # Aggregate core utilization across all snapshots
        all_core_utils = []
        for snapshot in self.snapshots:
            all_core_utils.extend(snapshot.per_core_cpu_percent)
        
        if not all_core_utils:
            return {}
        
        return {
            'peak_core_utilization': max(all_core_utils),
            'average_core_utilization': sum(all_core_utils) / len(all_core_utils),
            'min_core_utilization': min(all_core_utils),
            'core_utilization_std': np.std(all_core_utils) if len(all_core_utils) > 1 else 0.0,
            'cores_above_50_percent': sum(1 for util in all_core_utils if util > 50.0),
            'cores_above_80_percent': sum(1 for util in all_core_utils if util > 80.0),
        }
    
    def calculate_parallel_efficiency(self, workers_used: int, baseline_time: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate parallel processing efficiency metrics.
        
        Args:
            workers_used: Number of workers that were used
            baseline_time: Time it would take with single-threaded processing
            
        Returns:
            Dictionary with efficiency metrics
        """
        if not self.snapshots:
            return {}
        
        avg_cpu = self.get_average_utilization()
        logical_cores = self.snapshots[0].cpu_count_logical if self.snapshots else 1
        
        # Calculate theoretical vs actual utilization
        theoretical_max_cpu = min(workers_used * 100, logical_cores * 100)
        cpu_efficiency = (avg_cpu / theoretical_max_cpu * 100) if theoretical_max_cpu > 0 else 0.0
        
        metrics = {
            'cpu_efficiency_percent': cpu_efficiency,
            'workers_used': workers_used,
            'logical_cores_available': logical_cores,
            'theoretical_max_cpu_percent': theoretical_max_cpu,
            'actual_avg_cpu_percent': avg_cpu,
        }
        
        if baseline_time:
            processing_time = self.snapshots[-1].timestamp - self.snapshots[0].timestamp
            theoretical_speedup = min(workers_used, logical_cores)
            actual_speedup = baseline_time / processing_time if processing_time > 0 else 1.0
            parallel_efficiency = (actual_speedup / theoretical_speedup * 100) if theoretical_speedup > 0 else 0.0
            
            metrics.update({
                'baseline_time_seconds': baseline_time,
                'parallel_time_seconds': processing_time,
                'theoretical_speedup': theoretical_speedup,
                'actual_speedup': actual_speedup,
                'parallel_efficiency_percent': parallel_efficiency,
            })
        
        return metrics


# Define top-level function for multiprocessing to avoid pickling issues
def process_chunk(func: Callable, chunk: MatrixChunk, args: tuple) -> Tuple[MatrixChunk, Any]:
    """
    Process a matrix chunk with the given function and arguments.
    
    Args:
        func: Function to apply to the chunk
        chunk: Matrix chunk to process
        args: Additional arguments to pass to the function
        
    Returns:
        Tuple of (chunk, result)
    """
    result = func(chunk, *args)
    return chunk, result


@dataclass
class WorkerStats:
    """Statistics about a worker process"""
    worker_id: int
    tasks_completed: int = 0
    last_task_duration: float = 0.0
    total_duration: float = 0.0
    memory_usage_mb: float = 0.0
    status: str = "idle"


def parallel_map_worker(args):
    """
    Top-level worker function for ParallelProcessor.map (Windows-safe).
    Args:
        args: Tuple (worker_id, item, func)
    Returns:
        Tuple (worker_id, result)
    """
    worker_id, item, func = args
    import time
    from .performance import get_memory_usage
    start_time = time.time()
    result = func(item)
    duration = time.time() - start_time
    # We cannot update self.worker_stats here (no access to self in subprocess),
    # but we return the worker_id and result for the parent to handle.
    return worker_id, result


class ParallelProcessor:
    """
    Manages parallel processing with memory awareness.
    
    This class handles distribution of tasks across multiple processes,
    with adaptive worker pool sizing based on CPU cores and memory constraints.
    """
    
    def __init__(self, 
                 max_workers: Optional[int] = None, 
                 memory_limit_mb: Optional[int] = None,
                 memory_per_worker_mb: int = 1000):
        """
        Initialize the parallel processor.
        
        Args:
            max_workers: Maximum number of worker processes (default: CPU count)
            memory_limit_mb: Maximum memory to use (default: 80% of system RAM)
            memory_per_worker_mb: Estimated memory per worker process
        """
        # Determine optimal worker count based on CPU and memory
        cpu_count = mp.cpu_count()
        system_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
        
        # Default to 80% of system memory if not specified
        memory_limit_mb = memory_limit_mb or int(system_memory_mb * 0.8)
        
        # Calculate workers based on memory constraint
        memory_based_workers = max(1, memory_limit_mb // memory_per_worker_mb)
        
        # Use the minimum of CPU count and memory-based worker count
        self.max_workers = min(
            cpu_count if max_workers is None else max_workers,
            memory_based_workers
        )
        
        self.memory_limit_mb = memory_limit_mb
        self.memory_per_worker_mb = memory_per_worker_mb
        self.worker_stats = {}
        
        # CPU tracking
        self.cpu_tracker = CPUUtilizationTracker(sampling_interval=0.5)
        self.enable_cpu_tracking = True
        
        logger.info(f"Initialized ParallelProcessor with {self.max_workers} workers, "
                   f"memory limit: {memory_limit_mb} MB, CPU tracking: enabled")
        
    def map(self, 
            func: Callable[[T], R], 
            items: List[T], 
            chunksize: int = 1) -> List[R]:
        """
        Apply a function to each item in parallel with progress and CPU tracking.
        
        Args:
            func: Function to apply to each item
            items: List of items to process
            chunksize: Number of items per task
            
        Returns:
            List of results
        """
        results = []
        start_time = time.time()
        
        # Start CPU monitoring
        if self.enable_cpu_tracking:
            self.cpu_tracker.start_monitoring()
        
        # Prepare arguments for the top-level worker
        worker_args = []
        for i, item in enumerate(items):
            worker_id = i % self.max_workers
            worker_args.append((worker_id, item, func))
        
        # Use progress tracking for visual feedback
        with ProgressTracker(
            total=len(items),
            desc=f"Parallel processing ({self.max_workers} workers)",
            memory_tracking=True,
            show_tqdm=True
        ) as progress:
            # Create a pool with the calculated number of workers
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # Initialize worker stats
                self.worker_stats = {
                    i: WorkerStats(worker_id=i)
                    for i in range(self.max_workers)
                }
                
                # Submit tasks
                futures = [executor.submit(parallel_map_worker, arg) for arg in worker_args]
                
                # Collect results as they complete with progress updates
                for future in as_completed(futures):
                    worker_id, result = future.result()
                    results.append(result)
                    
                    # Update progress
                    progress.update(1)
                    
                    # Mark worker as idle
                    if worker_id in self.worker_stats:
                        self.worker_stats[worker_id].status = "idle"
        
        # Stop CPU monitoring and generate performance report
        if self.enable_cpu_tracking:
            self.cpu_tracker.stop_monitoring()
            end_time = time.time()
            
            # Generate performance metrics
            performance_metrics = self._generate_performance_metrics(
                start_time, end_time, len(items), len(results)
            )
            
            # Store metrics for later retrieval
            self._last_performance_metrics = performance_metrics
            
            # Log performance summary
            logger.info("Parallel processing completed with CPU tracking:")
            logger.info(f"  Duration: {performance_metrics.duration:.2f}s")
            logger.info(f"  Peak CPU: {performance_metrics.peak_cpu_utilization:.1f}%")
            logger.info(f"  Average CPU: {performance_metrics.average_cpu_utilization:.1f}%")
            logger.info(f"  CPU Efficiency: {performance_metrics.cpu_efficiency_score:.1f}%")
            logger.info(f"  Throughput: {performance_metrics.tasks_per_second:.1f} tasks/sec")
        
        return results
    
    def process_matrix_chunks(self,
                             func: Callable[[MatrixChunk, Any], Any],
                             chunks: Iterator[MatrixChunk],
                             *args) -> Dict[Tuple[int, int, int, int], Any]:
        """
        Process matrix chunks in parallel with progress tracking.
        
        Args:
            func: Function to apply to each chunk (func(chunk, *args))
            chunks: Iterator of matrix chunks
            *args: Additional arguments to pass to the function
            
        Returns:
            Dictionary mapping chunk coordinates to results
        """
        results = {}
        
        # Convert iterator to list to get count for progress tracking
        chunk_list = list(chunks)
        
        # Use progress tracking for visual feedback
        with ProgressTracker(
            total=len(chunk_list),
            desc=f"Matrix chunks ({self.max_workers} workers)",
            memory_tracking=True,
            show_tqdm=True
        ) as progress:
            # Use a ProcessPoolExecutor for parallel processing
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all chunks for processing
                futures = {}
                for chunk in chunk_list:
                    # Use the top-level process_chunk function
                    future = executor.submit(process_chunk, func, chunk, args)
                    futures[future] = chunk
                
                # Collect results as they complete with progress updates
                for future in as_completed(futures):
                    chunk, result = future.result()
                    key = (chunk.row_start, chunk.row_end, chunk.col_start, chunk.col_end)
                    results[key] = result
                    
                    # Update progress
                    progress.update(1)
                    
                    # Check memory usage and trigger GC if needed
                    memory_usage = get_memory_usage()
                    if memory_usage.current_process_usage_mb > self.memory_limit_mb * 0.9:
                        trigger_garbage_collection(full=True)
        
        return results

    def get_worker_stats(self) -> Dict[int, WorkerStats]:
        """
        Get statistics about worker processes.
        
        Returns:
            Dictionary mapping worker IDs to their stats
        """
        return self.worker_stats.copy()
    
    def _generate_performance_metrics(self, start_time: float, end_time: float, 
                                    total_tasks: int, successful_tasks: int) -> ProcessingPerformanceMetrics:
        """
        Generate comprehensive performance metrics from CPU tracking data.
        
        Args:
            start_time: Processing start time
            end_time: Processing end time
            total_tasks: Total number of tasks
            successful_tasks: Number of successful tasks
            
        Returns:
            ProcessingPerformanceMetrics object with all metrics
        """
        failed_tasks = total_tasks - successful_tasks
        
        # CPU metrics
        peak_cpu = self.cpu_tracker.get_peak_utilization()
        avg_cpu = self.cpu_tracker.get_average_utilization()
        
        # Calculate CPU efficiency (how well we used available cores)
        logical_cores = psutil.cpu_count(logical=True)
        theoretical_max_cpu = min(self.max_workers * 100, logical_cores * 100)
        cpu_efficiency = (avg_cpu / theoretical_max_cpu * 100) if theoretical_max_cpu > 0 else 0.0
        
        # Memory metrics (basic - could be enhanced)
        current_memory = get_memory_usage().current_process_usage_mb
        
        # Parallelization metrics
        theoretical_speedup = min(self.max_workers, logical_cores)
        # Note: We'd need baseline single-threaded time to calculate actual speedup
        
        # Task distribution
        tasks_per_worker = defaultdict(int)
        for worker_id, stats in self.worker_stats.items():
            tasks_per_worker[worker_id] = stats.tasks_completed
        
        return ProcessingPerformanceMetrics(
            start_time=start_time,
            end_time=end_time,
            total_tasks=total_tasks,
            successful_tasks=successful_tasks,
            failed_tasks=failed_tasks,
            cpu_snapshots=self.cpu_tracker.snapshots.copy(),
            peak_cpu_utilization=peak_cpu,
            average_cpu_utilization=avg_cpu,
            cpu_efficiency_score=cpu_efficiency,
            peak_memory_mb=current_memory,
            average_memory_mb=current_memory,  # Simplified
            memory_growth_mb=0.0,  # Would need baseline
            workers_used=self.max_workers,
            theoretical_speedup=theoretical_speedup,
            actual_speedup=1.0,  # Would need baseline
            parallel_efficiency=0.0,  # Would need baseline
            tasks_per_worker=dict(tasks_per_worker),
            worker_idle_time={}  # Could be calculated from worker stats
        )
    
    def get_performance_report(self) -> str:
        """
        Get a detailed performance report from the last processing run.
        
        Returns:
            Formatted performance report string
        """
        if not hasattr(self, '_last_performance_metrics'):
            return "No performance data available. Run a processing task first."
        
        return self._last_performance_metrics.get_summary_report()
    
    def get_cpu_utilization_analysis(self) -> Dict[str, Any]:
        """
        Get detailed CPU utilization analysis from the last run.
        
        Returns:
            Dictionary with CPU utilization metrics
        """
        core_analysis = self.cpu_tracker.get_core_utilization_analysis()
        efficiency_metrics = self.cpu_tracker.calculate_parallel_efficiency(self.max_workers)
        
        return {
            'peak_cpu_percent': self.cpu_tracker.get_peak_utilization(),
            'average_cpu_percent': self.cpu_tracker.get_average_utilization(),
            'core_analysis': core_analysis,
            'efficiency_metrics': efficiency_metrics,
            'workers_used': self.max_workers,
            'logical_cores': psutil.cpu_count(logical=True),
            'physical_cores': psutil.cpu_count(logical=False),
        }


# Convenience functions for CPU tracking
def create_cpu_tracked_processor(max_workers: Optional[int] = None, 
                                memory_limit_mb: Optional[int] = None) -> ParallelProcessor:
    """
    Create a ParallelProcessor with CPU tracking enabled.
    
    Args:
        max_workers: Maximum number of worker processes
        memory_limit_mb: Maximum memory to use
        
    Returns:
        ParallelProcessor with CPU tracking enabled
    """
    processor = ParallelProcessor(max_workers=max_workers, memory_limit_mb=memory_limit_mb)
    processor.enable_cpu_tracking = True
    return processor


def benchmark_parallel_vs_sequential(func: Callable[[T], R], 
                                    items: List[T], 
                                    max_workers: Optional[int] = None) -> Dict[str, Any]:
    """
    Benchmark parallel vs sequential processing to measure actual speedup.
    
    Args:
        func: Function to apply to each item
        items: List of items to process
        max_workers: Number of workers for parallel processing
        
    Returns:
        Dictionary with benchmark results
    """
    # Sequential benchmark
    start_time = time.time()
    sequential_results = [func(item) for item in items]
    sequential_time = time.time() - start_time
    
    # Parallel benchmark with CPU tracking
    processor = create_cpu_tracked_processor(max_workers=max_workers)
    parallel_results = processor.map(func, items)
    
    # Get performance metrics
    cpu_analysis = processor.get_cpu_utilization_analysis()
    
    # Calculate speedup
    parallel_time = processor._last_performance_metrics.duration
    actual_speedup = sequential_time / parallel_time if parallel_time > 0 else 1.0
    
    return {
        'sequential_time': sequential_time,
        'parallel_time': parallel_time,
        'actual_speedup': actual_speedup,
        'workers_used': processor.max_workers,
        'cpu_analysis': cpu_analysis,
        'parallel_efficiency_percent': (actual_speedup / processor.max_workers * 100) if processor.max_workers > 0 else 0.0,
        'results_match': sequential_results == parallel_results,
        'performance_report': processor.get_performance_report()
    }


class WorkStealingQueue:
    """
    A thread-safe work queue that supports work stealing.
    
    This queue allows multiple workers to process tasks efficiently,
    with idle workers "stealing" tasks from busy workers to balance load.
    """
    
    def __init__(self, num_workers: int):
        """
        Initialize the work stealing queue.
        
        Args:
            num_workers: Number of workers
        """
        self.num_workers = num_workers
        self.queues = [[] for _ in range(num_workers)]  # List-based queues for each worker
        self.locks = [threading.Lock() for _ in range(num_workers)]
        self.global_queue = queue.Queue()
        self.global_lock = threading.Lock()
        
    def push_task(self, worker_id: int, task: Any) -> None:
        """
        Add a task to a specific worker's queue.
        
        Args:
            worker_id: ID of the worker
            task: Task to add
        """
        with self.locks[worker_id]:
            self.queues[worker_id].append(task)
    
    def push_global(self, task: Any) -> None:
        """
        Add a task to the global queue.
        
        Args:
            task: Task to add
        """
        self.global_queue.put(task)
    
    def pop_task(self, worker_id: int) -> Tuple[bool, Any]:
        """
        Get a task for a worker, potentially stealing from other workers.
        
        Args:
            worker_id: ID of the worker
            
        Returns:
            Tuple of (success, task)
        """
        # First try the worker's own queue
        with self.locks[worker_id]:
            if self.queues[worker_id]:
                return True, self.queues[worker_id].pop()
        
        # Then try the global queue
        try:
            return True, self.global_queue.get_nowait()
        except queue.Empty:
            pass
        
        # Finally, try stealing from other workers
        for victim_id in range(self.num_workers):
            if victim_id != worker_id:
                with self.locks[victim_id]:
                    if len(self.queues[victim_id]) > 1:  # Leave at least one task
                        return True, self.queues[victim_id].pop(0)  # Steal from front
        
        # No tasks found
        return False, None


@dataclass
class Task:
    """Represents a task with dependencies"""
    id: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)
    result: Any = None
    completed: bool = False
    

class TaskManager:
    """
    Manages tasks with dependencies.
    
    This class handles scheduling and execution of tasks with dependencies,
    ensuring that tasks are only executed when their dependencies are satisfied.
    """
    
    def __init__(self):
        """Initialize the task manager."""
        self.tasks: Dict[str, Task] = {}
        self.results: Dict[str, Any] = {}
        
    def add_task(self, 
                task_id: str, 
                func: Callable, 
                args: tuple = None, 
                kwargs: Dict[str, Any] = None,
                dependencies: List[str] = None) -> None:
        """
        Add a task to the manager.
        
        Args:
            task_id: Unique identifier for the task
            func: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            dependencies: List of task IDs that must complete before this task
        """
        self.tasks[task_id] = Task(
            id=task_id,
            func=func,
            args=args or (),
            kwargs=kwargs or {},
            dependencies=set(dependencies or [])
        )
    
    def get_ready_tasks(self) -> List[Task]:
        """
        Get tasks that are ready to execute (all dependencies satisfied).
        
        Returns:
            List of ready tasks
        """
        ready_tasks = []
        
        for task_id, task in self.tasks.items():
            if not task.completed and all(
                dep_id in self.results for dep_id in task.dependencies
            ):
                ready_tasks.append(task)
        
        return ready_tasks
    
    def execute_task(self, task: Task) -> Any:
        """
        Execute a task and store its result.
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
        """
        # Get results of dependencies if needed
        kwargs = task.kwargs.copy()
        for dep_id in task.dependencies:
            if dep_id in self.results:
                kwargs[f"dep_{dep_id}"] = self.results[dep_id]
        
        # Execute the task
        result = task.func(*task.args, **kwargs)
        
        # Store the result
        self.results[task.id] = result
        task.result = result
        task.completed = True
        
        return result
    
    def execute_all(self) -> Dict[str, Any]:
        """
        Execute all tasks in dependency order.
        
        Returns:
            Dictionary mapping task IDs to results
        """
        # Clear previous results
        self.results = {}
        for task in self.tasks.values():
            task.completed = False
            task.result = None
        
        # Execute tasks until all are complete or no progress is made
        while True:
            ready_tasks = self.get_ready_tasks()
            if not ready_tasks:
                break
            
            for task in ready_tasks:
                self.execute_task(task)
        
        # Check if all tasks were completed
        incomplete = [task_id for task_id, task in self.tasks.items() if not task.completed]
        if incomplete:
            raise RuntimeError(f"Could not complete tasks: {incomplete}")
        
        return self.results
    
    def execute_all_parallel(self, max_workers: int = None) -> Dict[str, Any]:
        """
        Execute all tasks in dependency order using parallel execution.
        
        Args:
            max_workers: Maximum number of worker threads
            
        Returns:
            Dictionary mapping task IDs to results
        """
        if max_workers is None:
            max_workers = os.cpu_count() or 4
        
        # Clear previous results
        self.results = {}
        for task in self.tasks.values():
            task.completed = False
            task.result = None
        
        # Create a thread pool
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Keep track of submitted tasks
            futures = {}
            
            # Execute until all tasks are complete
            while len(self.results) < len(self.tasks):
                # Submit ready tasks that haven't been submitted yet
                ready_tasks = self.get_ready_tasks()
                for task in ready_tasks:
                    if task.id not in futures:
                        future = executor.submit(self.execute_task, task)
                        futures[task.id] = future
                
                # Check if we've submitted any tasks
                if not futures:
                    # If no tasks were submitted but not all are complete,
                    # there must be a circular dependency
                    incomplete = [task_id for task_id, task in self.tasks.items() if not task.completed]
                    if incomplete:
                        raise RuntimeError(f"Circular dependency detected in tasks: {incomplete}")
                    break
                
                # Wait for at least one task to complete
                done, _ = concurrent.futures.wait(
                    list(futures.values()),
                    return_when=concurrent.futures.FIRST_COMPLETED
                )
                
                # Check results and clear completed futures
                completed_tasks = []
                for future in done:
                    for task_id, f in futures.items():
                        if f is future:
                            try:
                                f.result()  # Get result to catch exceptions
                                completed_tasks.append(task_id)
                            except Exception as e:
                                raise RuntimeError(f"Task {task_id} failed: {e}")
                
                                # Remove completed futures                for task_id in completed_tasks:                    del futures[task_id]                return self.results 
