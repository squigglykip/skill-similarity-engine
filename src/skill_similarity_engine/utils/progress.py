"""
Progress Tracking Utilities

This module provides utilities for tracking progress of long-running operations,
with integrated memory usage reporting. These utilities are essential for providing
feedback during operations that may take hours to complete, such as similarity
calculations for large datasets (35,000+ jobs).
"""

import time
import logging
from typing import Optional, Any, Dict, List, Callable, Union, Sequence
from dataclasses import dataclass
from contextlib import contextmanager
import threading
import os
import sys

import tqdm
import psutil

from .performance import get_memory_usage, MemoryUsage

logger = logging.getLogger(__name__)

# Global tqdm style/config for consistent progress bar appearance
TQDM_STYLE = {
    'bar_format': '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]',
    'colour': 'green',
    'ascii': False,
    'dynamic_ncols': True,   # Enable dynamic columns for better responsiveness
    'leave': True,          # Leave progress bars visible after completion
    'ncols': None,          # Auto-detect terminal width (None for auto-sizing)
    'miniters': 1,          # Update every iteration for smooth progress
    'mininterval': 0.1,     # Minimum time interval between updates (0.1 seconds)
    'file': None,           # Use default output (sys.stderr)
    'position': 0           # Position for nested progress bars
}

@dataclass
class ProgressStats:
    """Statistics about a long-running operation"""
    total_items: int
    completed_items: int = 0
    start_time: float = 0.0
    last_update_time: float = 0.0
    memory_usage: Optional[MemoryUsage] = None
    
    @property
    def percent_complete(self) -> float:
        """Calculate percentage complete"""
        return (self.completed_items / self.total_items) * 100 if self.total_items > 0 else 0
    
    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds"""
        if self.start_time == 0:
            return 0
        return time.time() - self.start_time
    
    @property
    def estimated_remaining_time(self) -> float:
        """Estimate remaining time in seconds"""
        if self.completed_items == 0 or self.total_items == 0:
            return float('inf')
        
        elapsed = self.elapsed_time
        items_per_second = self.completed_items / elapsed if elapsed > 0 else 0
        
        if items_per_second == 0:
            return float('inf')
        
        return (self.total_items - self.completed_items) / items_per_second
    
    def format_eta(self) -> str:
        """Format estimated time remaining as a string"""
        eta = self.estimated_remaining_time
        
        if eta == float('inf'):
            return "unknown"
        
        hours, remainder = divmod(eta, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{int(hours)}h {int(minutes)}m"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s"

class ProgressTracker:
    """
    Tracks progress of long-running operations with memory usage reporting.
    
    This class provides a high-level interface for tracking progress and
    estimating completion time, with integrated memory usage monitoring.
    """
    
    def __init__(self, 
                 total: int, 
                 desc: str = "Processing", 
                 memory_tracking: bool = True,
                 log_interval: int = 100,
                 show_tqdm: bool = True):
        """
        Initialize the progress tracker.
        
        Args:
            total: Total number of items to process
            desc: Description for the progress bar
            memory_tracking: Whether to track memory usage
            log_interval: Log progress every N items
            show_tqdm: Whether to display a tqdm progress bar
        """
        self.stats = ProgressStats(total_items=total)
        self.desc = desc
        self.memory_tracking = memory_tracking
        self.log_interval = log_interval
        self.show_tqdm = show_tqdm
        self.pbar = None
        
        # Initialize memory usage
        if self.memory_tracking:
            self.stats.memory_usage = get_memory_usage()
        
    def __enter__(self):
        """Start tracking progress"""
        self.stats.start_time = time.time()
        self.stats.last_update_time = self.stats.start_time
        
        if self.show_tqdm:
            self.pbar = tqdm.tqdm(
                total=self.stats.total_items,
                desc=self.desc,
                unit="items",
                **TQDM_STYLE  # Use global style
            )
        
        logger.info(f"Starting {self.desc}: {self.stats.total_items} items")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End tracking progress"""
        if self.pbar:
            if exc_type is None:
                # Successful completion - ensure it shows 100% completion
                if self.stats.completed_items < self.stats.total_items:
                    remaining = self.stats.total_items - self.stats.completed_items
                    self.pbar.update(remaining)
            
            # Close the progress bar (respects the leave=True setting from TQDM_STYLE)
            self.pbar.close()
        
        if exc_type is None:
            # Successful completion
            logger.info(f"Completed {self.desc}: {self.stats.completed_items}/{self.stats.total_items} items "
                       f"in {self.stats.elapsed_time:.1f}s")
            
            if self.memory_tracking and self.stats.memory_usage:
                logger.info(f"Final memory usage: {self.stats.memory_usage.current_process_usage_mb:.1f} MB")
    
    def update(self, n: int = 1) -> None:
        """
        Update progress by n items.
        
        Args:
            n: Number of items completed
        """
        self.stats.completed_items += n
        
        if self.pbar:
            self.pbar.update(n)
        
        # Update memory usage periodically
        if self.memory_tracking and self.stats.completed_items % self.log_interval == 0:
            self.stats.memory_usage = get_memory_usage()
            
            if self.pbar:
                self.pbar.set_postfix(
                    memory=f"{self.stats.memory_usage.current_process_usage_mb:.1f}MB",
                    eta=self.stats.format_eta()
                )
        
        # Log progress periodically using tqdm.write() to avoid interfering with progress bar
        if self.stats.completed_items % self.log_interval == 0:
            progress_msg = (f"{self.desc}: {self.stats.completed_items}/{self.stats.total_items} "
                           f"({self.stats.percent_complete:.1f}%) - ETA: {self.stats.format_eta()}")
            
            # Only log when progress bar is NOT active to avoid interference
            if not (self.show_tqdm and self.pbar):
                logger.info(progress_msg)
                
                if self.memory_tracking and self.stats.memory_usage:
                    logger.info(f"Memory usage: {self.stats.memory_usage.current_process_usage_mb:.1f} MB")
    
    def get_stats(self) -> ProgressStats:
        """
        Get current progress statistics.
        
        Returns:
            ProgressStats object with current statistics
        """
        # Update memory usage before returning stats
        if self.memory_tracking:
            self.stats.memory_usage = get_memory_usage()
            
        return self.stats

class SimpleProgressReporter:
    """
    Simple CLI/log-only progress reporter for environments where tqdm is not desired.
    Prints progress to stdout or logs, with optional ETA.

    Usage:
        reporter = SimpleProgressReporter(total=100, desc="Processing")
        for i in range(100):
            # ... do work ...
            reporter.update()
        reporter.close()
    """
    def __init__(self, total: int, desc: str = "Processing", log: bool = False, log_interval: int = 10):
        self.total = total
        self.desc = desc
        self.completed = 0
        self.start_time = time.time()
        self.log = log
        self.log_interval = log_interval
        self.last_log = 0
        print(f"{self.desc}: 0/{self.total}", end="", flush=True)
    def update(self, n: int = 1):
        self.completed += n
        if self.completed % self.log_interval == 0 or self.completed == self.total:
            elapsed = time.time() - self.start_time
            percent = (self.completed / self.total) * 100
            eta = (elapsed / self.completed) * (self.total - self.completed) if self.completed > 0 else 0
            eta_str = f"ETA: {int(eta)}s" if self.completed < self.total else "Done"
            msg = f"\r{self.desc}: {self.completed}/{self.total} ({percent:.1f}%) {eta_str}"
            if self.log:
                logger.info(msg.strip())
            else:
                print(msg, end="", flush=True)
    def close(self):
        print()

class MultiProgressTracker:
    """
    Tracks progress of multiple operations simultaneously, supporting nested/multi-level progress bars.

    Usage example (nested progress):
        with MultiProgressTracker() as mpt:
            batch_tracker = mpt.add_tracker("batches", total=num_batches, desc="Batches")
            for batch in batches:
                batch_tracker.update(1)
                chunk_tracker = mpt.add_tracker("chunks", total=len(batch), desc="Chunks")
                for chunk in batch:
                    chunk_tracker.update(1)
                mpt.stop_tracker("chunks")
    """
    def __init__(self):
        self.trackers: Dict[str, ProgressTracker] = {}
        self.active_tracker: Optional[str] = None

    def add_tracker(self, name: str, total: int, desc: str = None, memory_tracking: bool = True, show_tqdm: bool = True) -> ProgressTracker:
        """
        Add and start a new progress tracker. If a tracker with this name exists, it is stopped and replaced.
        Returns the started tracker (as a context manager).
        """
        if name in self.trackers:
            self.stop_tracker(name)
        desc = desc or name
        tracker = ProgressTracker(total=total, desc=desc, memory_tracking=memory_tracking, show_tqdm=show_tqdm)
        tracker.__enter__()
        self.trackers[name] = tracker
        self.active_tracker = name
        return tracker

    def stop_tracker(self, name: str) -> None:
        """
        Stop and remove a tracker by name.
        """
        if name in self.trackers:
            self.trackers[name].__exit__(None, None, None)
            del self.trackers[name]
            if self.active_tracker == name:
                self.active_tracker = None

    def update(self, name: str, n: int = 1) -> None:
        """
        Update a tracker by name.
        """
        if name in self.trackers:
            self.trackers[name].update(n)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for name in list(self.trackers.keys()):
            self.stop_tracker(name)

class RefreshableProgressDisplay:
    """
    Displays progress with a refreshable interface that works well across platforms,
    especially on Windows PowerShell where cursor positioning can be unreliable.
    
    This class uses a screen-clearing approach to ensure clean display of:
    1. A single total progress bar at the top
    2. Multiple chunk progress bars that accumulate below
    
    Usage:
        display = RefreshableProgressDisplay(total_items=35000)
        display.initialize()
        
        for i, chunk in enumerate(chunks):
            with tqdm.tqdm(total=len(chunk), desc=f"Chunk {i+1}", leave=False) as chunk_bar:
                # Process chunk
                ...
                chunk_bar.update(1)
                
            # After chunk completes
            display.update_total_progress(items_processed, total_items)
        
        display.finalize()
    """
    
    def __init__(self, 
                 total_items: int, 
                 title: str = "=== Performance Pipeline Demo ===",
                 header_messages: Optional[List[str]] = None,
                 separator_char: str = "=",
                 separator_length: int = 80):
        """
        Initialize the refreshable progress display.
        
        Args:
            total_items: Total number of items to process
            title: Title to display at the top
            header_messages: Additional messages to display in the header
            separator_char: Character to use for section separators
            separator_length: Length of separator lines
        """
        self.total_items = total_items
        self.processed_items = 0
        self.title = title
        self.header_messages = header_messages or []
        self.separator_char = separator_char
        self.separator_length = separator_length
        self.completed_chunks = []
        
    def initialize(self):
        """Initialize the display with header and initial progress"""
        self._refresh_display()
        
    def update_total_progress(self, processed_items: int, total_items: Optional[int] = None):
        """
        Update the total progress display.
        
        Args:
            processed_items: Number of items processed so far
            total_items: Updated total (if changed since initialization)
        """
        self.processed_items = processed_items
        if total_items is not None:
            self.total_items = total_items
            
        self._refresh_display()
        
    def add_completed_chunk(self, chunk_number: int, chunk_size: int, elapsed_time: Optional[float] = None, items_per_second: Optional[float] = None):
        """
        Add a completed chunk to the display.
        
        Args:
            chunk_number: Chunk number (1-based)
            chunk_size: Size of the chunk
            elapsed_time: Time taken to process the chunk in seconds
            items_per_second: Processing rate in items per second
        """
        time_info = ""
        if elapsed_time is not None:
            # Format elapsed time as [00:00:00.00]
            minutes, seconds = divmod(elapsed_time, 60)
            hours, minutes = divmod(minutes, 60)
            time_info = f"[{int(hours):02d}:{int(minutes):02d}:{seconds:04.2f}]"
            
            # Add items per second if provided
            if items_per_second is not None:
                time_info += f", {items_per_second:.2f}it/s"
        
        # Create a completed bar (100%)
        bar = "â–ˆ" * 50  # Fixed width bar
        
        # Create the chunk summary
        chunk_info = f"Chunk {chunk_number}: 100%|{bar}| {chunk_size}/{chunk_size}"
        if time_info:
            chunk_info += f" {time_info}"
            
        self.completed_chunks.append(chunk_info)
        self._refresh_display()
    
    def add_current_chunk(self, chunk_number: int, completed_items: int, total_items: int):
        """
        Add the current in-progress chunk to the display.
        
        Args:
            chunk_number: Chunk number (1-based)
            completed_items: Number of items completed in this chunk
            total_items: Total number of items in this chunk
        """
        # Calculate progress percentage
        percent = int((completed_items / total_items) * 100) if total_items > 0 else 0
        
        # Create a partial bar based on completion percentage
        filled_length = int(50 * completed_items / total_items) if total_items > 0 else 0
        bar = "â–ˆ" * filled_length + " " * (50 - filled_length)
        
        # Create the chunk summary without adding to completed_chunks
        chunk_info = f"Chunk {chunk_number}: {percent}%|{bar}| {completed_items}/{total_items}"
        
        # Temporarily add this chunk for display but don't store it
        temp_chunks = self.completed_chunks.copy()
        temp_chunks.append(chunk_info)
        self._refresh_display(temp_chunks)
    
    def finalize(self):
        """Finalize the display, showing completion"""
        self._refresh_display()
        print("\n" + self.separator_char * self.separator_length)
        print("\nPipeline completed. All chunks processed successfully.")
    
    def _refresh_display(self, chunks_to_display=None):
        """
        Refresh the entire display.
        
        Args:
            chunks_to_display: Optional list of chunks to display (including temporary in-progress chunk)
        """
        # Clear the screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Print the header
        print(f"\n{self.title}")
        for message in self.header_messages:
            print(message)
        
        # Print the overall progress section
        print("\n" + self.separator_char * self.separator_length)
        print("OVERALL PROGRESS:")
        print("-" * self.separator_length)
        
        # Calculate and display total progress
        progress_percent = int((self.processed_items / self.total_items) * 100) if self.total_items > 0 else 0
        blocks = int(progress_percent / 2)  # 50 blocks = 100%
        progress_bar = "â–ˆ" * blocks + " " * (50 - blocks)
        print(f"Total Progress: {progress_percent:2d}%|{progress_bar}| {self.processed_items}/{self.total_items}")
        
        # Print the chunk progress section
        print("\n" + self.separator_char * self.separator_length)
        print("CHUNK PROGRESS:")
        print("-" * self.separator_length)
        
        # Print all completed chunks
        for chunk_info in (chunks_to_display or self.completed_chunks):
            print(chunk_info)

@contextmanager
def refreshable_progress_context(total_items: int,
                                title: str = "=== Processing === ",
                                header_messages: Optional[List[str]] = None,
                                chunk_processor: Optional[Callable[[Any, tqdm.tqdm], None]] = None,
                                chunks: Optional[Sequence[Any]] = None):
    """
    Context manager for refreshable progress display.
    
    Args:
        total_items: Total number of items to process
        title: Title to display at the top
        header_messages: Additional messages to display in the header
        chunk_processor: Function to process each chunk (receives chunk and tqdm bar)
        chunks: Optional sequence of chunks to process
        
    Yields:
        RefreshableProgressDisplay object
    """
    display = RefreshableProgressDisplay(
        total_items=total_items,
        title=title,
        header_messages=header_messages
    )
    
    display.initialize()
    
    try:
        if chunks is not None and chunk_processor is not None:
            total_processed = 0
            
            # Process each chunk with a progress bar
            for i, chunk in enumerate(chunks):
                # Create and display chunk progress bar
                with tqdm.tqdm(total=len(chunk), desc=f"Chunk {i+1}", leave=False) as chunk_bar:
                    # Process the chunk
                    chunk_processor(chunk, chunk_bar)
                
                # Track items processed
                chunk_size = len(chunk)
                total_processed += chunk_size
                
                # Update progress display
                display.update_total_progress(total_processed)
                display.add_completed_chunk(i+1, chunk_size)
        
        yield display
    finally:
        display.finalize()

@contextmanager
def progress_context(total: int, 
                    desc: str = "Processing", 
                    memory_tracking: bool = True,
                    show_tqdm: bool = True):
    """
    Context manager for tracking progress.
    
    Args:
        total: Total number of items to process
        desc: Description for the progress bar
        memory_tracking: Whether to track memory usage
        show_tqdm: Whether to display a tqdm progress bar
        
    Yields:
        ProgressTracker object
    """
    tracker = ProgressTracker(
        total=total,
        desc=desc,
        memory_tracking=memory_tracking,
        show_tqdm=show_tqdm
    )
    
    with tracker:
        yield tracker

def track_progress_thread(func: Callable, 
                         args: tuple = None, 
                         kwargs: dict = None, 
                         update_interval: float = 1.0,
                         memory_tracking: bool = True) -> Any:
    """
    Run a function in a separate thread while tracking progress in the main thread.
    
    This is useful for functions that don't have built-in progress reporting.
    
    Args:
        func: Function to run
        args: Arguments for the function
        kwargs: Keyword arguments for the function
        update_interval: Interval in seconds for progress updates
        memory_tracking: Whether to track memory usage
        
    Returns:
        Result of the function
    """
    args = args or ()
    kwargs = kwargs or {}
    
    # Variables for communication between threads
    result = [None]
    exception = [None]
    completed = [False]
    
    # Thread function
    def worker():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e
        finally:
            completed[0] = True
    
    # Start worker thread
    thread = threading.Thread(target=worker)
    thread.start()
    
    # Track progress in main thread
    start_time = time.time()
    last_memory_usage = None
    
    try:
        while not completed[0]:
            # Print progress
            elapsed = time.time() - start_time
            print(f"\rRunning... {elapsed:.1f}s elapsed", end="")
            
            # Track memory if requested
            if memory_tracking:
                memory_usage = get_memory_usage()
                if last_memory_usage != memory_usage.current_process_usage_mb:
                    last_memory_usage = memory_usage.current_process_usage_mb
                    print(f" | Memory: {memory_usage.current_process_usage_mb:.1f} MB", end="")
            
            # Wait for next update
            time.sleep(update_interval)
        
        # Clear line on completion
        print("\r" + " " * 80 + "\r", end="")
        
        # Re-raise any exception from the worker
        if exception[0]:
            raise exception[0]
        
        return result[0]
    finally:
        # Ensure thread is joined
        thread.join() 
