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

import psutil
import numpy as np

from .performance import get_memory_usage, trigger_garbage_collection
from .matrix_chunking import MatrixChunk
from .progress import ProgressTracker

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


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
        
        logger.info(f"Initialized ParallelProcessor with {self.max_workers} workers, "
                   f"memory limit: {memory_limit_mb} MB")
        
    def map(self, 
            func: Callable[[T], R], 
            items: List[T], 
            chunksize: int = 1) -> List[R]:
        """
        Apply a function to each item in parallel with progress tracking.
        
        Args:
            func: Function to apply to each item
            items: List of items to process
            chunksize: Number of items per task
            
        Returns:
            List of results
        """
        results = []
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
