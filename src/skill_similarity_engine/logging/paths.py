import os
from datetime import datetime

# Define the central log directory relative to the project root
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../log'))
os.makedirs(LOG_DIR, exist_ok=True)

RUN_SUBDIRS = [
    'logs',
    'errors',
    'checkpoints',
    'progress',
    'validation',
    'metrics',
]

def get_run_log_dir():
    """
    Create and return a new per-run log directory with a timestamp, including standard subdirectories.
    Returns a dict with the run directory and all subdirectory paths.
    Usage:
        paths = get_run_log_dir()
        run_log_dir = paths['run']
        logs_dir = paths['logs']
    """
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_log_dir = os.path.join(LOG_DIR, f"run_{run_id}")
    os.makedirs(run_log_dir, exist_ok=True)
    subdirs = {}
    for sub in RUN_SUBDIRS:
        sub_path = os.path.join(run_log_dir, sub)
        os.makedirs(sub_path, exist_ok=True)
        subdirs[sub] = sub_path
    subdirs['run'] = run_log_dir
    return subdirs
