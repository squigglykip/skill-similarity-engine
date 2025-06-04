import sys
import os
from pathlib import Path

# Add src to path for local imports
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.error_handling.core import EngineError, ErrorCategory, ErrorSeverity
from skill_similarity_engine.error_handling.registry import ErrorRegistry
from skill_similarity_engine.logging.paths import get_run_log_dir

# --- Output Structure ---
# This example writes error reports to the 'errors' subdirectory of a timestamped run folder in 'log/'.
# All outputs for this run are grouped by type under that folder.

RUN_PATHS = get_run_log_dir()
ERRORS_DIR = RUN_PATHS['errors']

def error_demo():
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

if __name__ == "__main__":
    error_demo()
