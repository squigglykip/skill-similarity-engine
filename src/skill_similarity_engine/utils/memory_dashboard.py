"""
Memory Usage Dashboard and Visualisation

This module provides tools for visualising memory usage patterns, 
generating memory consumption reports, and predicting future memory needs
based on current usage patterns.
"""

import os
import csv
import time
import logging
from typing import Any, Dict, List, Tuple, Optional, Union
from datetime import datetime
import threading
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from scipy.optimize import curve_fit

from .performance import get_memory_usage, MemorySnapshot, log_memory_summary

logger = logging.getLogger(__name__)

class MemoryUsageTracker:
    """
    Tracks memory usage over time and provides visualisation capabilities.
    
    This class maintains a history of memory snapshots and can generate
    visualisations and predictions based on the collected data.
    """
    
    def __init__(self, 
                 max_history: int = 1000, 
                 output_dir: Optional[str] = None) -> None:
        """
        Initialize the memory usage tracker.
        
        Args:
            max_history: Maximum number of snapshots to store
            output_dir: Directory to save output files (default: current directory)
        """
        self.max_history = max_history
        self.output_dir = output_dir or os.getcwd()
        
        # Create the output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize the history
        self.history: List[MemorySnapshot] = []
        self.timestamps: List[float] = []
        self.reference_points: Dict[str, int] = {}  # Maps labels to indices
        
        # Threading lock for thread safety
        self._lock = threading.RLock()
    
    def take_snapshot(self, label: Optional[str] = None) -> MemorySnapshot:
        """
        Take a memory snapshot and add it to the history.
        
        Args:
            label: Optional label for the snapshot (for reference points)
            
        Returns:
            The snapshot that was taken
        """
        with self._lock:
            # Take a snapshot
            snapshot = get_memory_usage()
            
            # Add the snapshot to the history
            self.history.append(snapshot)
            self.timestamps.append(time.time())
            
            # Trim the history if it's too long
            if len(self.history) > self.max_history:
                self.history.pop(0)
                self.timestamps.pop(0)
                
                # Update reference point indices
                for ref_label, idx in list(self.reference_points.items()):
                    if idx == 0:
                        # Reference point is being removed
                        del self.reference_points[ref_label]
                    else:
                        # Adjust the index
                        self.reference_points[ref_label] = idx - 1
            
            # If a label was provided, add a reference point
            if label:
                self.reference_points[label] = len(self.history) - 1
            
            return snapshot
    
    def add_reference_point(self, label: str) -> None:
        """
        Add a reference point with the given label at the current position.
        
        Args:
            label: Label for the reference point
        """
        with self._lock:
            if self.history:
                self.reference_points[label] = len(self.history) - 1
    
    def clear_history(self) -> None:
        """Clear the snapshot history and reference points."""
        with self._lock:
            self.history.clear()
            self.timestamps.clear()
            self.reference_points.clear()
    
    def plot_memory_usage(self, 
                          show_details: bool = True,
                          show_reference_points: bool = True,
                          prediction_window: Optional[int] = None) -> Figure:
        """
        Generate a plot of memory usage over time.
        
        Args:
            show_details: Whether to show detailed memory information
            show_reference_points: Whether to show reference points
            prediction_window: If set, predict memory usage for this many snapshots
                               into the future
            
        Returns:
            Matplotlib figure object
        """
        with self._lock:
            if not self.history:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, "No data available", 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=ax.transAxes)
                return fig
            
            # Create a figure with subplots based on what we want to show
            num_plots = 1 + (2 if show_details else 0)
            fig, axes = plt.subplots(num_plots, 1, figsize=(12, 4 * num_plots), 
                                    sharex=True)
            
            # If we only have one plot, make axes a list
            if num_plots == 1:
                axes = [axes]
            
            # Convert absolute timestamps to relative time in seconds
            start_time = self.timestamps[0]
            rel_times = [t - start_time for t in self.timestamps]
            
            # Plot the overall memory usage
            ax = axes[0]
            process_mem = [s.current_process_usage_mb for s in self.history]
            ax.plot(rel_times, process_mem, 'b-', label='Process Memory')
            
            # If we have a prediction window, predict future memory usage
            if prediction_window is not None and len(rel_times) >= 5:
                # Predict future memory usage
                predicted_times, predicted_mem = self._predict_memory_usage(
                    rel_times, process_mem, prediction_window
                )
                
                # Plot the prediction
                ax.plot(predicted_times, predicted_mem, 'r--', 
                        label='Predicted Memory')
            
            # Add reference points if requested
            if show_reference_points and self.reference_points:
                for label, idx in self.reference_points.items():
                    if 0 <= idx < len(rel_times):
                        ax.axvline(x=rel_times[idx], color='g', linestyle='--', alpha=0.7)
                        ax.text(rel_times[idx], ax.get_ylim()[1] * 0.9, label,
                                rotation=90, verticalalignment='top')
            
            ax.set_title('Memory Usage Over Time')
            ax.set_ylabel('Memory (MB)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # If showing details, add plots for peak allocation and system memory
            if show_details:
                # Plot peak allocation
                ax = axes[1]
                peak_mem = [s.peak_allocated_mb for s in self.history]
                total_mem = [s.total_allocated_mb for s in self.history]
                ax.plot(rel_times, peak_mem, 'r-', label='Peak Allocated')
                ax.plot(rel_times, total_mem, 'g-', label='Total Allocated')
                ax.set_title('Memory Allocation')
                ax.set_ylabel('Memory (MB)')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                # Plot available system memory
                ax = axes[2]
                avail_mem = [s.system_available_mb for s in self.history]
                ax.plot(rel_times, avail_mem, 'm-', label='System Available')
                ax.set_title('System Memory')
                ax.set_xlabel('Time (seconds)')
                ax.set_ylabel('Memory (MB)')
                ax.legend()
                ax.grid(True, alpha=0.3)
            else:
                # Add x-axis label to the only plot
                axes[0].set_xlabel('Time (seconds)')
            
            plt.tight_layout()
            return fig
    
    def _predict_memory_usage(self, 
                             times: List[float], 
                             memory: List[float], 
                             prediction_window: int) -> Tuple[List[float], List[float]]:
        """
        Predict future memory usage based on past patterns.
        
        Args:
            times: List of relative times
            memory: List of memory values
            prediction_window: Number of snapshots to predict
            
        Returns:
            Tuple of (predicted_times, predicted_memory)
        """
        # If we don't have enough data points, use linear prediction
        if len(times) < 10:
            return self._predict_linear(times, memory, prediction_window)
        
        # Try polynomial regression
        try:
            return self._predict_polynomial(times, memory, prediction_window)
        except:
            # Fall back to linear prediction
            logger.warning("Polynomial prediction failed, falling back to linear.")
            return self._predict_linear(times, memory, prediction_window)
    
    def _predict_linear(self, 
                       times: List[float], 
                       memory: List[float],
                       prediction_window: int) -> Tuple[List[float], List[float]]:
        """
        Linear prediction of future memory usage.
        
        Args:
            times: List of relative times
            memory: List of memory values
            prediction_window: Number of snapshots to predict
            
        Returns:
            Tuple of (predicted_times, predicted_memory)
        """
        # Convert to numpy arrays
        x = np.array(times)
        y = np.array(memory)
        
        # Fit a linear model
        slope, intercept = np.polyfit(x, y, 1)
        
        # Create prediction points
        # Estimate the time step based on the average of the last few steps
        if len(times) >= 2:
            step = (times[-1] - times[-min(5, len(times) - 1)]) / min(5, len(times) - 1)
        else:
            step = 1.0  # Default step if we can't calculate
        
        # Create future time points
        future_times = [times[-1] + step * (i + 1) for i in range(prediction_window)]
        
        # Predict memory at those points
        future_memory = [slope * t + intercept for t in future_times]
        
        # Return the predicted values
        return future_times, future_memory
    
    def _predict_polynomial(self, 
                           times: List[float], 
                           memory: List[float],
                           prediction_window: int) -> Tuple[List[float], List[float]]:
        """
        Polynomial prediction of future memory usage.
        
        Args:
            times: List of relative times
            memory: List of memory values
            prediction_window: Number of snapshots to predict
            
        Returns:
            Tuple of (predicted_times, predicted_memory)
        """
        # Convert to numpy arrays
        x = np.array(times)
        y = np.array(memory)
        
        # Determine the appropriate polynomial degree
        # Use higher degree for more data points, but max out at 3
        degree = min(3, max(1, len(times) // 10))
        
        # Fit a polynomial model
        coeffs = np.polyfit(x, y, degree)
        poly = np.poly1d(coeffs)
        
        # Create prediction points
        # Estimate the time step based on the average of the last few steps
        if len(times) >= 2:
            step = (times[-1] - times[-min(5, len(times) - 1)]) / min(5, len(times) - 1)
        else:
            step = 1.0  # Default step if we can't calculate
        
        # Create future time points
        future_times = [times[-1] + step * (i + 1) for i in range(prediction_window)]
        
        # Predict memory at those points
        future_memory = [poly(t) for t in future_times]
        
        # Return the predicted values
        return future_times, future_memory
    
    def save_plot(self, 
                 filename: Optional[str] = None, 
                 show_details: bool = True,
                 show_reference_points: bool = True,
                 prediction_window: Optional[int] = None) -> str:
        """
        Generate and save a memory usage plot.
        
        Args:
            filename: Filename to save the plot (default: memory_usage_{timestamp}.png)
            show_details: Whether to show detailed memory information
            show_reference_points: Whether to show reference points
            prediction_window: If set, predict memory usage for this many snapshots
                               into the future
            
        Returns:
            Path to the saved file
        """
        # Generate a default filename if none provided
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"memory_usage_{timestamp}.png"
        
        # Make sure the filename has a .png extension
        if not filename.lower().endswith('.png'):
            filename += '.png'
        
        # Get the full path
        filepath = os.path.join(self.output_dir, filename)
        
        # Generate the plot
        fig = self.plot_memory_usage(
            show_details=show_details,
            show_reference_points=show_reference_points,
            prediction_window=prediction_window
        )
        
        # Save the figure
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"Memory usage plot saved to: {filepath}")
        return filepath
    
    def export_csv(self, filename: Optional[str] = None) -> str:
        """
        Export memory usage history to a CSV file.
        
        Args:
            filename: Filename to save the CSV (default: memory_usage_{timestamp}.csv)
            
        Returns:
            Path to the saved file
        """
        with self._lock:
            # Generate a default filename if none provided
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"memory_usage_{timestamp}.csv"
            
            # Make sure the filename has a .csv extension
            if not filename.lower().endswith('.csv'):
                filename += '.csv'
            
            # Get the full path
            filepath = os.path.join(self.output_dir, filename)
            
            # Define the CSV columns
            columns = [
                'timestamp', 
                'relative_time', 
                'process_usage_mb', 
                'total_allocated_mb',
                'peak_allocated_mb', 
                'system_available_mb', 
                'gc_objects',
                'reference_point'
            ]
            
            # Calculate reference point labels for each snapshot
            reference_labels = [''] * len(self.history)
            for label, idx in self.reference_points.items():
                if 0 <= idx < len(reference_labels):
                    reference_labels[idx] = label
            
            # Write the CSV file
            with open(filepath, 'w', newline='') as csv_file:
                writer = csv.writer(csv_file)
                
                # Write the header
                writer.writerow(columns)
                
                # Calculate relative times
                start_time = self.timestamps[0] if self.timestamps else 0
                rel_times = [t - start_time for t in self.timestamps]
                
                # Write the data
                for i, snapshot in enumerate(self.history):
                    # Format the timestamp as a string
                    ts_str = datetime.fromtimestamp(self.timestamps[i]).strftime(
                        '%Y-%m-%d %H:%M:%S.%f'
                    )
                    
                    writer.writerow([
                        ts_str,
                        f"{rel_times[i]:.3f}",
                        f"{snapshot.current_process_usage_mb:.2f}",
                        f"{snapshot.total_allocated_mb:.2f}",
                        f"{snapshot.peak_allocated_mb:.2f}",
                        f"{snapshot.system_available_mb:.2f}",
                        snapshot.gc_objects,
                        reference_labels[i]
                    ])
            
            logger.info(f"Memory usage data exported to: {filepath}")
            return filepath


class MemoryDashboard:
    """
    A dashboard for monitoring and visualising memory usage.
    
    This class provides real-time memory monitoring, visualization,
    and prediction capabilities.
    """
    
    def __init__(self, 
                 output_dir: Optional[str] = None,
                 monitor_interval: float = 5.0) -> None:
        """
        Initialize the memory dashboard.
        
        Args:
            output_dir: Directory to save output files (default: current directory)
            monitor_interval: Interval in seconds for periodic monitoring
        """
        self.output_dir = output_dir or os.path.join(os.getcwd(), 'memory_dashboard')
        self.monitor_interval = monitor_interval
        
        # Create the output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize the tracker
        self.tracker = MemoryUsageTracker(output_dir=self.output_dir)
        
        # Initialize monitoring state
        self._monitoring = False
        self._monitor_thread = None
        self._stop_monitoring = threading.Event()
    
    def start_monitoring(self) -> None:
        """Start real-time memory monitoring."""
        if self._monitoring:
            logger.warning("Memory monitoring is already active.")
            return
        
        # Reset the stop event
        self._stop_monitoring.clear()
        
        # Start the monitoring thread
        self._monitor_thread = threading.Thread(
            target=self._monitor_thread_func,
            daemon=True
        )
        self._monitor_thread.start()
        
        self._monitoring = True
        logger.info(f"Memory monitoring started with {self.monitor_interval}s interval.")
    
    def stop_monitoring(self) -> None:
        """Stop real-time memory monitoring."""
        if not self._monitoring:
            logger.warning("Memory monitoring is not active.")
            return
        
        # Signal the thread to stop
        self._stop_monitoring.set()
        
        # Wait for the thread to finish
        if self._monitor_thread:
            self._monitor_thread.join(timeout=self.monitor_interval * 2)
        
        self._monitoring = False
        logger.info("Memory monitoring stopped.")
    
    def _monitor_thread_func(self) -> None:
        """Thread function for periodic memory monitoring."""
        while not self._stop_monitoring.is_set():
            try:
                # Take a snapshot
                self.tracker.take_snapshot()
                
                # Generate a plot every 10 snapshots
                if len(self.tracker.history) % 10 == 0:
                    self.tracker.save_plot()
                
                # Generate a CSV export every 50 snapshots
                if len(self.tracker.history) % 50 == 0:
                    self.tracker.export_csv()
            except Exception as e:
                logger.error(f"Error in memory monitoring: {e}")
            
            # Wait for the next interval or until stopped
            self._stop_monitoring.wait(self.monitor_interval)
    
    def mark_event(self, label: str) -> None:
        """
        Mark an event with the given label.
        
        Args:
            label: Label for the event
        """
        self.tracker.add_reference_point(label)
        logger.info(f"Memory event marked: {label}")
    
    def generate_report(self, 
                       include_plot: bool = True,
                       include_prediction: bool = True,
                       prediction_window: int = 20) -> str:
        """
        Generate a comprehensive memory usage report.
        
        Args:
            include_plot: Whether to include a plot in the report
            include_prediction: Whether to include memory usage prediction
            prediction_window: Number of snapshots to predict
            
        Returns:
            Path to the report directory
        """
        # Create a timestamped report directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_dir = os.path.join(self.output_dir, f"memory_report_{timestamp}")
        os.makedirs(report_dir, exist_ok=True)
        
        # Export the data to CSV
        csv_path = os.path.join(report_dir, "memory_data.csv")
        self.tracker.export_csv(csv_path)
        
        # Generate plots if requested
        if include_plot:
            plot_path = os.path.join(report_dir, "memory_usage.png")
            self.tracker.save_plot(
                plot_path, 
                show_details=True,
                show_reference_points=True,
                prediction_window=prediction_window if include_prediction else None
            )
        
        # Generate a summary report
        summary_path = os.path.join(report_dir, "summary.txt")
        with open(summary_path, 'w') as f:
            # Write a header
            f.write("MEMORY USAGE SUMMARY REPORT\n")
            f.write("==========================\n\n")
            
            # Write a timestamp
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Write statistics
            if self.tracker.history:
                current = self.tracker.history[-1]
                f.write(f"Current memory usage: {current.current_process_usage_mb:.2f} MB\n")
                f.write(f"Peak allocated memory: {current.peak_allocated_mb:.2f} MB\n")
                f.write(f"Available system memory: {current.system_available_mb:.2f} MB\n")
                f.write(f"Garbage collector objects: {current.gc_objects:,}\n\n")
                
                # Calculate change over time
                if len(self.tracker.history) >= 2:
                    first = self.tracker.history[0]
                    duration = self.tracker.timestamps[-1] - self.tracker.timestamps[0]
                    mem_change = current.current_process_usage_mb - first.current_process_usage_mb
                    rate = mem_change / duration if duration > 0 else 0
                    
                    f.write(f"Monitoring duration: {duration:.2f} seconds\n")
                    f.write(f"Memory change: {mem_change:+.2f} MB\n")
                    f.write(f"Growth rate: {rate:.2f} MB/sec\n\n")
                
                # If we have reference points, list them
                if self.tracker.reference_points:
                    f.write("Reference Points:\n")
                    for label, idx in self.tracker.reference_points.items():
                        if 0 <= idx < len(self.tracker.history):
                            rel_time = self.tracker.timestamps[idx] - self.tracker.timestamps[0]
                            mem = self.tracker.history[idx].current_process_usage_mb
                            f.write(f"  - {label}: {rel_time:.2f}s, {mem:.2f} MB\n")
                    f.write("\n")
                
                # Include prediction if requested
                if include_prediction and len(self.tracker.history) >= 5:
                    f.write("Memory Usage Prediction:\n")
                    
                    # Get prediction data
                    times = [t - self.tracker.timestamps[0] for t in self.tracker.timestamps]
                    memory = [s.current_process_usage_mb for s in self.tracker.history]
                    
                    future_times, future_memory = self.tracker._predict_memory_usage(
                        times, memory, prediction_window
                    )
                    
                    # Write prediction for a few points
                    for i in range(min(5, len(future_times))):
                        f.write(f"  - Time +{future_times[i] - times[-1]:.2f}s: {future_memory[i]:.2f} MB\n")
                    
                    # Calculate when memory might exceed certain thresholds
                    thresholds = [
                        current.current_process_usage_mb * 2,  # Double current
                        8 * 1024,  # 8 GB
                        16 * 1024  # 16 GB
                    ]
                    
                    for threshold in thresholds:
                        for i, mem in enumerate(future_memory):
                            if mem >= threshold:
                                time_to_threshold = future_times[i] - times[-1]
                                f.write(f"\nMemory may reach {threshold:.2f} MB in {time_to_threshold:.2f} seconds\n")
                                break
                        else:
                            # Loop completed without finding the threshold
                            f.write(f"\nMemory is not predicted to reach {threshold:.2f} MB within the prediction window\n")
            else:
                f.write("No memory data available.\n")
        
        logger.info(f"Memory usage report generated in: {report_dir}")
        return report_dir


def start_memory_dashboard(output_dir: Optional[str] = None,
                         monitor_interval: float = 5.0) -> MemoryDashboard:
    """
    Create and start a memory dashboard.
    
    This is a convenience function to quickly set up a memory dashboard
    and start monitoring.
    
    Args:
        output_dir: Directory to save output files
        monitor_interval: Interval in seconds for periodic monitoring
        
    Returns:
        The created and started dashboard
    """
    # Create the dashboard
    dashboard = MemoryDashboard(
        output_dir=output_dir,
        monitor_interval=monitor_interval
    )
    
    # Start monitoring
    dashboard.start_monitoring()
    
    # Log the startup
    logger.info(f"Memory dashboard started with {monitor_interval}s interval.")
    if output_dir:
        logger.info(f"Dashboard output directory: {output_dir}")
    
    return dashboard


def track_function_memory(func: Any, output_dir: Optional[str] = None) -> Any:
    """
    Decorator to track memory usage of a function and generate a report.
    
    Args:
        func: Function to track
        output_dir: Directory to save the report
        
    Returns:
        Decorated function
    """
    # Use the function name if output_dir is not specified
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), f"memory_track_{func.__name__}")
    
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Create a tracker for this function call
        tracker = MemoryUsageTracker(output_dir=output_dir)
        
        # Take initial snapshot
        tracker.take_snapshot("Start")
        
        # Record function parameters if they're simple types
        param_str = ""
        try:
            arg_strs = [str(arg) for arg in args if isinstance(arg, (int, float, str, bool))]
            kwarg_strs = [f"{k}={v}" for k, v in kwargs.items() 
                         if isinstance(v, (int, float, str, bool))]
            param_str = ", ".join(arg_strs + kwarg_strs)
            if len(param_str) > 50:
                param_str = param_str[:47] + "..."
        except:
            param_str = f"{len(args)} args, {len(kwargs)} kwargs"
        
        function_call = f"{func.__name__}({param_str})"
        logger.info(f"Tracking memory for {function_call}")
        
        try:
            # Call the function
            result = func(*args, **kwargs)
            
            # Take final snapshot
            tracker.take_snapshot("End")
            
            # Generate reports
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            tracker.save_plot(f"memory_{func.__name__}_{timestamp}.png")
            tracker.export_csv(f"memory_{func.__name__}_{timestamp}.csv")
            
            return result
        except Exception as e:
            # Take snapshot on error
            tracker.take_snapshot("Error")
            
            # Generate reports
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            tracker.save_plot(f"memory_{func.__name__}_error_{timestamp}.png")
            tracker.export_csv(f"memory_{func.__name__}_error_{timestamp}.csv")
            
            # Re-raise the exception
            raise
    
    return wrapper 