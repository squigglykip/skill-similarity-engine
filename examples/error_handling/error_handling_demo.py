"""
Demonstration of Enhanced Error Handling Features (6.4.3)

This script showcases:
- ErrorRegistry usage
- CircuitBreaker decorator
- Recovery strategy decorator
- Fallback mechanism decorator
- Checkpoint and JSONCheckpoint usage
- ResumableBatchOperation usage

All outputs are written to the appropriate subdirectory of a timestamped run folder in 'log/'.
"""
import os
import random   
import sys
from pathlib import Path

# Add src to path for local imports
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.error_handling.core import EngineError, ErrorCategory, ErrorSeverity
from skill_similarity_engine.error_handling.registry import ErrorRegistry
from skill_similarity_engine.error_handling.recovery import circuit_breaker, recovery_strategy, fallback_on_failure
from skill_similarity_engine.error_handling.checkpoint import Checkpoint, JSONCheckpoint, ResumableBatchOperation
from skill_similarity_engine.logging.paths import get_run_log_dir

# --- Output Structure ---
RUN_PATHS = get_run_log_dir()
ERRORS_DIR = RUN_PATHS['errors']
CHECKPOINTS_DIR = RUN_PATHS['checkpoints']

# --- ErrorRegistry Demo ---
def error_registry_demo():
    print("\n--- ErrorRegistry Demo ---")
    try:
        raise EngineError("Simulated data error", category=ErrorCategory.DATA, severity=ErrorSeverity.ERROR, context={"job_id": 123})
    except EngineError:
        pass
    try:
        raise EngineError("Simulated validation warning", category=ErrorCategory.VALIDATION, severity=ErrorSeverity.WARNING, context={"field": "salary"})
    except EngineError:
        pass
    registry = ErrorRegistry()
    print("Error summary:", registry.summary())
    registry.export_json(os.path.join(ERRORS_DIR, "errors_demo.json"))
    registry.export_csv(os.path.join(ERRORS_DIR, "errors_demo.csv"))
    print(f"Exported errors to {ERRORS_DIR}/errors_demo.json and errors_demo.csv")

# --- CircuitBreaker Demo ---
@circuit_breaker(failure_threshold=2, recovery_timeout=3)
def flaky_func():
    if random.random() < 0.7:
        raise ValueError("Random failure!")
    return "Success!"
def circuit_breaker_demo():
    print("\n--- CircuitBreaker Demo ---")
    for i in range(6):
        try:
            print(f"Attempt {i+1}: {flaky_func()}")
        except Exception as e:
            print(f"Attempt {i+1}: {e}")

# --- Recovery Strategy Demo ---
def fallback_func(*args, **kwargs):
    print("Fallback called!")
    return "Fallback result"

@recovery_strategy(fallback=fallback_func, escalate=False)
def main_func():
    raise RuntimeError("Main function failed!")
def recovery_strategy_demo():
    print("\n--- Recovery Strategy Demo ---")
    print(main_func())

# --- Fallback Mechanism Demo ---
@fallback_on_failure(fallback=fallback_func, default="Default value")
def another_flaky_func():
    raise Exception("Always fails!")
def fallback_mechanism_demo():
    print("\n--- Fallback Mechanism Demo ---")
    print(another_flaky_func())

# --- Checkpoint Demo ---
def checkpoint_demo():
    print("\n--- Checkpoint Demo ---")
    checkpoint_dir = CHECKPOINTS_DIR
    operation_name = "demo_op"
    checkpoint = Checkpoint(checkpoint_dir, operation_name)
    state = {"step": 5, "data": [1, 2, 3]}
    checkpoint.save(state)
    print("Checkpoint saved.")
    loaded_state = checkpoint.load()
    print("Loaded state:", loaded_state)
    # JSONCheckpoint
    json_cp = JSONCheckpoint(os.path.join(checkpoint_dir, "json_checkpoint.json"))
    json_cp.save({"progress": 42})
    print("JSONCheckpoint saved.")
    print("Loaded JSONCheckpoint:", json_cp.load())

# --- ResumableBatchOperation Demo ---
def process_batch(batch):
    print(f"Processing batch: {batch}")
    return sum(batch)
def resumable_batch_demo():
    print("\n--- ResumableBatchOperation Demo ---")
    batches = [[1,2,3], [4,5,6], [7,8,9]]
    op = ResumableBatchOperation(batches, process_batch, checkpoint_path=os.path.join(CHECKPOINTS_DIR, "batch_checkpoint.json"))
    results = op.process()
    print("Batch results:", results)
    op.clear_checkpoint()
    print("Batch checkpoint cleared.")

def main():
    error_registry_demo()
    circuit_breaker_demo()
    recovery_strategy_demo()
    fallback_mechanism_demo()
    checkpoint_demo()
    resumable_batch_demo()

if __name__ == "__main__":
    main() 