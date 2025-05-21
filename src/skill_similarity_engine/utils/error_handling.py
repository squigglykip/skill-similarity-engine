"""
Error Handling and Recovery Utilities

This module provides utilities for handling errors and recovering from failures
in long-running operations. These utilities are essential for ensuring that
partial failures don't cause complete process termination, especially in
resource-intensive operations like similarity calculations for large datasets.
"""

import os
import time
import logging
import traceback
import pickle
from typing import Dict, Any, Optional, Callable, TypeVar, List, Tuple
from dataclasses import dataclass
from contextlib import contextmanager
import json
import hashlib

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')

@dataclass
class ErrorContext:
    """Context information for an error"""
    function_name: str
    args: tuple
    kwargs: Dict[str, Any]
    exception: Exception
    traceback_str: str
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "function_name": self.function_name,
            "args": str(self.args),
            "kwargs": str(self.kwargs),
            "exception_type": type(self.exception).__name__,
            "exception_message": str(self.exception),
            "traceback": self.traceback_str,
            "timestamp": self.timestamp,
            "timestamp_readable": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))
        }

class ErrorRegistry:
    """
    Registry for tracking errors across multiple operations.
    
    This class maintains a record of errors that occur during processing,
    enabling analysis of failure patterns and potential recovery strategies.
    """
    
    def __init__(self, max_errors: int = 1000):
        """
        Initialize the error registry.
        
        Args:
            max_errors: Maximum number of errors to store
        """
        self.errors: List[ErrorContext] = []
        self.max_errors = max_errors
        self.error_counts: Dict[str, int] = {}  # Exception type -> count
        
    def register_error(self, context: ErrorContext) -> None:
        """
        Register an error in the registry.
        
        Args:
            context: Error context information
        """
        # Add to list, maintaining max size
        self.errors.append(context)
        if len(self.errors) > self.max_errors:
            self.errors.pop(0)
        
        # Update error counts
        error_type = type(context.exception).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Log the error
        logger.error(f"Error in {context.function_name}: {context.exception}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of registered errors.
        
        Returns:
            Dictionary with error statistics
        """
        return {
            "total_errors": len(self.errors),
            "error_types": self.error_counts,
            "most_recent": self.errors[-1].to_dict() if self.errors else None,
            "most_common_type": max(self.error_counts.items(), key=lambda x: x[1])[0] 
                               if self.error_counts else None
        }
    
    def clear(self) -> None:
        """Clear all registered errors."""
        self.errors = []
        self.error_counts = {}

# Global error registry
_ERROR_REGISTRY = ErrorRegistry()

def get_error_registry() -> ErrorRegistry:
    """
    Get the global error registry.
    
    Returns:
        Global ErrorRegistry instance
    """
    return _ERROR_REGISTRY

@contextmanager
def error_context(function_name: str, *args, **kwargs):
    """
    Context manager for handling errors with proper context.
    
    Args:
        function_name: Name of the function being executed
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Yields:
        None
    """
    try:
        yield
    except Exception as e:
        # Capture traceback
        tb_str = traceback.format_exc()
        
        # Create error context
        context = ErrorContext(
            function_name=function_name,
            args=args,
            kwargs=kwargs,
            exception=e,
            traceback_str=tb_str,
            timestamp=time.time()
        )
        
        # Register error
        _ERROR_REGISTRY.register_error(context)
        
        # Re-raise the exception
        raise

def retry(max_attempts: int = 3, 
         delay: float = 1.0, 
         backoff_factor: float = 2.0,
         exceptions: tuple = (Exception,)):
    """
    Decorator for retrying functions that may fail transiently.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts in seconds
        backoff_factor: Factor by which delay increases with each attempt
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    
                    if attempt >= max_attempts:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.warning(f"Attempt {attempt}/{max_attempts} for {func.__name__} failed: {e}. "
                                 f"Retrying in {current_delay:.1f}s...")
                    
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            
            # This should never be reached due to the raise above
            raise RuntimeError("Unexpected code path in retry decorator")
        
        return wrapper
    
    return decorator

class Checkpoint:
    """
    Manages checkpoints for resumable processing.
    
    This class provides functionality to save and load processing state,
    enabling resumption of long-running operations after interruption.
    """
    
    def __init__(self, 
                checkpoint_dir: str, 
                operation_name: str,
                create_dir: bool = True):
        """
        Initialize the checkpoint manager.
        
        Args:
            checkpoint_dir: Directory for checkpoint files
            operation_name: Name of the operation (used in filenames)
            create_dir: Whether to create the checkpoint directory if it doesn't exist
        """
        self.checkpoint_dir = checkpoint_dir
        self.operation_name = operation_name
        
        # Create directory if needed
        if create_dir and not os.path.exists(checkpoint_dir):
            os.makedirs(checkpoint_dir)
    
    def _get_checkpoint_path(self, checkpoint_id: Optional[str] = None) -> str:
        """Get the path for a checkpoint file"""
        if checkpoint_id:
            return os.path.join(self.checkpoint_dir, 
                               f"{self.operation_name}_{checkpoint_id}.checkpoint")
        else:
            return os.path.join(self.checkpoint_dir, 
                               f"{self.operation_name}.checkpoint")
    
    def save(self, 
            state: Dict[str, Any], 
            checkpoint_id: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save a checkpoint.
        
        Args:
            state: State dictionary to save
            checkpoint_id: Optional identifier for the checkpoint
            metadata: Optional metadata to include
            
        Returns:
            Path to the saved checkpoint file
        """
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        
        # Add metadata
        full_state = {
            "state": state,
            "metadata": metadata or {},
            "timestamp": time.time(),
            "operation_name": self.operation_name
        }
        
        # Save to file
        with open(checkpoint_path, 'wb') as f:
            pickle.dump(full_state, f)
        
        logger.info(f"Saved checkpoint to {checkpoint_path}")
        return checkpoint_path
    
    def load(self, checkpoint_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Load a checkpoint.
        
        Args:
            checkpoint_id: Optional identifier for the checkpoint
            
        Returns:
            Loaded state dictionary
            
        Raises:
            FileNotFoundError: If the checkpoint file doesn't exist
        """
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")
        
        # Load from file
        with open(checkpoint_path, 'rb') as f:
            full_state = pickle.load(f)
        
        logger.info(f"Loaded checkpoint from {checkpoint_path} "
                   f"(created {time.time() - full_state['timestamp']:.1f}s ago)")
        
        return full_state["state"]
    
    def exists(self, checkpoint_id: Optional[str] = None) -> bool:
        """
        Check if a checkpoint exists.
        
        Args:
            checkpoint_id: Optional identifier for the checkpoint
            
        Returns:
            Whether the checkpoint exists
        """
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        return os.path.exists(checkpoint_path)
    
    def list_checkpoints(self) -> List[str]:
        """
        List all checkpoints for this operation.
        
        Returns:
            List of checkpoint IDs
        """
        prefix = f"{self.operation_name}_"
        suffix = ".checkpoint"
        
        checkpoint_files = [
            f for f in os.listdir(self.checkpoint_dir)
            if f.startswith(prefix) and f.endswith(suffix)
        ]
        
        # Extract IDs from filenames
        checkpoint_ids = [
            f[len(prefix):-len(suffix)]
            for f in checkpoint_files
        ]
        
        return checkpoint_ids
    
    def delete(self, checkpoint_id: Optional[str] = None) -> bool:
        """
        Delete a checkpoint.
        
        Args:
            checkpoint_id: Optional identifier for the checkpoint
            
        Returns:
            Whether the checkpoint was deleted
        """
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
            logger.info(f"Deleted checkpoint: {checkpoint_path}")
            return True
        
        return False

class ResumableOperation:
    """
    Base class for operations that can be resumed after interruption.
    
    This class provides a framework for implementing resumable operations
    that can be interrupted and continued without losing progress.
    """
    
    def __init__(self, 
                checkpoint_dir: str, 
                operation_name: str,
                auto_checkpoint_interval: int = 100):
        """
        Initialize the resumable operation.
        
        Args:
            checkpoint_dir: Directory for checkpoint files
            operation_name: Name of the operation
            auto_checkpoint_interval: Create checkpoints every N items
        """
        self.checkpoint = Checkpoint(checkpoint_dir, operation_name)
        self.auto_checkpoint_interval = auto_checkpoint_interval
        self.items_since_checkpoint = 0
        self.state: Dict[str, Any] = {}
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current operation state.
        
        Returns:
            State dictionary
        """
        return self.state
    
    def set_state(self, state: Dict[str, Any]) -> None:
        """
        Set the operation state.
        
        Args:
            state: State dictionary
        """
        self.state = state
    
    def save_checkpoint(self) -> None:
        """Save a checkpoint of the current state."""
        self.checkpoint.save(self.get_state())
        self.items_since_checkpoint = 0
    
    def load_checkpoint(self) -> bool:
        """
        Load the most recent checkpoint.
        
        Returns:
            Whether a checkpoint was loaded
        """
        try:
            state = self.checkpoint.load()
            self.set_state(state)
            return True
        except FileNotFoundError:
            logger.info("No checkpoint found, starting from scratch")
            return False
    
    def update_progress(self, items_processed: int = 1) -> None:
        """
        Update progress and create checkpoint if needed.
        
        Args:
            items_processed: Number of items processed
        """
        self.items_since_checkpoint += items_processed
        
        if self.items_since_checkpoint >= self.auto_checkpoint_interval:
            self.save_checkpoint()
    
    def execute(self) -> Any:
        """
        Execute the operation, potentially resuming from checkpoint.
        
        This method should be implemented by subclasses.
        
        Returns:
            Operation result
        """
        raise NotImplementedError("Subclasses must implement execute()")

def create_operation_id(operation_name: str, **kwargs) -> str:
    """
    Create a unique operation ID based on name and parameters.
    
    This is useful for creating checkpoint IDs that reflect the
    specific parameters of an operation.
    
    Args:
        operation_name: Name of the operation
        **kwargs: Operation parameters
        
    Returns:
        Unique operation ID
    """
    # Convert kwargs to a stable string representation
    params_str = json.dumps(kwargs, sort_keys=True)
    
    # Create a hash of the parameters
    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
    
    # Combine with operation name
    return f"{operation_name}_{params_hash}" 