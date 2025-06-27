import os
import time
import traceback
from contextlib import contextmanager
from typing import Callable, TypeVar
from skill_similarity_engine.error_handling.registry import ErrorRegistry, ErrorContext
from datetime import datetime
import threading
from functools import wraps

T = TypeVar('T')

def retry(max_attempts: int = 3, delay: float = 1.0, backoff_factor: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator for retrying functions that may fail transiently.
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
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            raise RuntimeError("Max retry attempts exceeded")
        return wrapper
    return decorator

@contextmanager
def error_context(function_name: str, *args, **kwargs):
    """
    Context manager for handling errors with proper context.
    Registers errors with ErrorRegistry.
    """
    try:
        yield
    except Exception as e:
        tb_str = traceback.format_exc()
        context = ErrorContext(
            function_name=function_name,
            args=args,
            kwargs=kwargs,
            exception=e,
            traceback_str=tb_str,
            timestamp=time.time()
        )
        ErrorRegistry().register(context)
        raise

def select_run_directory(log_dir):
    """
    Scan the log directory for run subfolders, check for incomplete runs (presence of any .checkpoint file),
    and prompt the user to resume. Present options with human-readable timestamps.
    Return the selected run directory or None.
    """
    run_dirs = [
        os.path.join(log_dir, d) for d in os.listdir(log_dir)
        if os.path.isdir(os.path.join(log_dir, d)) and d.startswith("run_")
    ]
    incomplete_runs = []
    for run_dir in run_dirs:
        checkpoint_dir = os.path.join(run_dir, "checkpoints")
        if os.path.isdir(checkpoint_dir):
            checkpoint_files = [f for f in os.listdir(checkpoint_dir) if f.endswith('.checkpoint')]
            if checkpoint_files:
                # Parse timestamp for human-readable label
                folder = os.path.basename(run_dir)
                try:
                    _, dt_str = folder.split("run_")
                    dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
                    label = dt.strftime("Run from %d %B %Y at %H:%M")
                except Exception:
                    label = folder
                incomplete_runs.append((run_dir, label))
    if not incomplete_runs:
        return None
    print("Found incomplete runs:")
    for idx, (run, label) in enumerate(incomplete_runs):
        print(f"{idx+1}: {label} ({run})")
    choice = input("Would you like to resume one? (y/n): ").strip().lower()
    if choice == "y":
        sel = int(input(f"Select run number (1-{len(incomplete_runs)}): "))
        return incomplete_runs[sel-1][0]
    return None

class CircuitBreaker:
    """
    Simple circuit breaker for blocking repeated failures.
    After `failure_threshold` consecutive failures, the breaker is 'open' and blocks calls for `recovery_timeout` seconds.
    After the timeout, the breaker resets and allows calls again.
    """
    def __init__(self, failure_threshold=3, recovery_timeout=10):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.lock = threading.Lock()
        self.state = 'closed'  # 'closed', 'open'

    def call(self, func, *args, **kwargs):
        with self.lock:
            if self.state == 'open':
                if self.last_failure_time is None or (time.time() - self.last_failure_time) >= self.recovery_timeout:
                    self.state = 'closed'
                    self.failure_count = 0
                else:
                    raise RuntimeError("Circuit breaker is open. Calls are temporarily blocked.")
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            with self.lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.state = 'open'
            raise
        else:
            with self.lock:
                self.failure_count = 0
                self.state = 'closed'
            return result

def circuit_breaker(failure_threshold=3, recovery_timeout=10):
    """
    Decorator for applying a circuit breaker to a function.
    Usage:
        @circuit_breaker(failure_threshold=2, recovery_timeout=5)
        def my_func(...):
            ...
    """
    breaker = CircuitBreaker(failure_threshold, recovery_timeout)
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator

def recovery_strategy(fallback=None, escalate=False):
    """
    Decorator to apply a simple recovery strategy: if the decorated function fails, call the fallback function (if provided).
    If escalate=True, re-raise the error after fallback; otherwise, return the fallback result or None.
    Usage:
        @recovery_strategy(fallback=my_fallback_func, escalate=False)
        def main_func(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if fallback is not None:
                    try:
                        return fallback(*args, **kwargs)
                    except Exception as fallback_exc:
                        if escalate:
                            raise fallback_exc
                        return None
                if escalate:
                    raise e
                return None
        return wrapper
    return decorator

def fallback_on_failure(fallback=None, default=None):
    """
    Decorator to provide a fallback mechanism: if the decorated function fails, call the fallback function (if provided),
    or return a default value. If neither is provided, return None.
    Usage:
        @fallback_on_failure(fallback=my_fallback_func, default="default value")
        def main_func(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                if fallback is not None:
                    return fallback(*args, **kwargs)
                return default
        return wrapper
    return decorator

# Example usage (as a comment):
#
# def fallback_func(*args, **kwargs):
#     print("Fallback function called!")
#     return "Fallback result"
#
# @fallback_on_failure(fallback=fallback_func, default="Default value")
# def main_func():
#     raise ValueError("Main function failed!")
#
# print(main_func())  # Output: Fallback function called!\nFallback result
