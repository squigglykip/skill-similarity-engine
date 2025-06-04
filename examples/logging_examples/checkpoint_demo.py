import os
import sys
from pathlib import Path

# Add src to path for local imports
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from skill_similarity_engine.error_handling.checkpoint import Checkpoint
from skill_similarity_engine.logging.paths import get_run_log_dir

RUN_LOG_DIR = get_run_log_dir()

def checkpoint_demo():
    checkpoint_dir = os.path.join(RUN_LOG_DIR, "checkpoints")
    operation_name = "demo_op"
    checkpoint = Checkpoint(checkpoint_dir, operation_name)

    # Simulate saving state
    state = {"step": 5, "data": [1, 2, 3]}
    checkpoint.save(state)
    print("Checkpoint saved.")

    # Simulate loading state
    loaded_state = checkpoint.load()
    print("Loaded state:", loaded_state)

if __name__ == "__main__":
    checkpoint_demo()
