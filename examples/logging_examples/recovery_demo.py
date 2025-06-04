import sys
import os
from pathlib import Path

# Add src to path for local imports
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.error_handling.recovery import retry, error_context, select_run_directory
from skill_similarity_engine.error_handling.registry import ErrorRegistry
try:
    from skill_similarity_engine.logging.paths import LOG_DIR
except ImportError:
    LOG_DIR = os.path.join(str(project_root), 'log')

# Use select_run_directory to choose or create a run directory
RUN_LOG_DIR = select_run_directory(LOG_DIR) or LOG_DIR  # fallback to LOG_DIR if none selected
print(f"This run's log directory: {RUN_LOG_DIR}")

@retry(max_attempts=3, delay=0.5)
def flaky_function():
    import random
    if random.random() < 0.8:
        raise ValueError("Random failure!")
    return "Success!"

def recovery_demo():
    try:
        with error_context("flaky_function"):
            result = flaky_function()
            print("Function result:", result)
    except Exception as e:
        print("Caught exception after retries:", e)

    registry = ErrorRegistry()
    print("Error summary after recovery demo:", registry.summary())
    # Optionally export errors to the run log dir
    # registry.export_json(os.path.join(RUN_LOG_DIR, "recovery_demo_errors.json"))

if __name__ == "__main__":
    recovery_demo()
