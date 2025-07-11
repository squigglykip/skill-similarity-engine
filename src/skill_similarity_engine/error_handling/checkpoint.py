import os
import time
import pickle
import json
import hashlib
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

# Import architectural configuration manager
try:
    from ..config.architectural_config_manager import get_config_manager
except ImportError:
    # Fallback if architectural config unavailable
    get_config_manager = None


def _get_checkpoint_config():
    """Get checkpoint configuration from architectural config manager."""
    if get_config_manager is None:
        # Fallback configuration
        return {
            'auto_checkpoint_interval': 100,
            'checkpoint_file_extension': '.checkpoint',
            'default_checkpoint_dir': 'checkpoints',
            'create_dir_if_missing': True
        }
    
    try:
        config_manager = get_config_manager()
        return config_manager.get_nested_value('error_handling', 'checkpoints', default={
            'auto_checkpoint_interval': 100,
            'checkpoint_file_extension': '.checkpoint',
            'default_checkpoint_dir': 'checkpoints',
            'create_dir_if_missing': True
        })
    except Exception:
        # Fallback if configuration loading fails
        return {
            'auto_checkpoint_interval': 100,
            'checkpoint_file_extension': '.checkpoint',
            'default_checkpoint_dir': 'checkpoints',
            'create_dir_if_missing': True
        }


class Checkpoint:
    """
    Manages checkpoints for resumable processing.
    """
    def __init__(self, checkpoint_dir: Optional[str] = None, operation_name: str = "operation", create_dir: Optional[bool] = None):
        # Load configuration
        config = _get_checkpoint_config()
        
        self.checkpoint_dir = checkpoint_dir or config.get('default_checkpoint_dir', 'checkpoints')
        self.operation_name = operation_name
        self.file_extension = config.get('checkpoint_file_extension', '.checkpoint')
        
        create_dir_setting = create_dir if create_dir is not None else config.get('create_dir_if_missing', True)
        if create_dir_setting and not os.path.exists(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir)
    def _get_checkpoint_path(self, checkpoint_id: Optional[str] = None) -> str:
        if checkpoint_id:
            return os.path.join(self.checkpoint_dir, f"{self.operation_name}_{checkpoint_id}{self.file_extension}")
        else:
            return os.path.join(self.checkpoint_dir, f"{self.operation_name}{self.file_extension}")
    def save(self, state: Dict[str, Any], checkpoint_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        full_state = {
            "state": state,
            "metadata": metadata or {},
            "timestamp": time.time(),
            "operation_name": self.operation_name
        }
        with open(checkpoint_path, 'wb') as f:
            pickle.dump(full_state, f)
        return checkpoint_path
    def load(self, checkpoint_id: Optional[str] = None) -> Dict[str, Any]:
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")
        with open(checkpoint_path, 'rb') as f:
            full_state = pickle.load(f)
        return full_state["state"]
    def exists(self, checkpoint_id: Optional[str] = None) -> bool:
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        return os.path.exists(checkpoint_path)
    def list_checkpoints(self) -> List[str]:
        prefix = f"{self.operation_name}_"
        suffix = self.file_extension
        checkpoint_files = [
            f for f in os.listdir(self.checkpoint_dir)
            if f.startswith(prefix) and f.endswith(suffix)
        ]
        checkpoint_ids = [
            f[len(prefix):-len(suffix)]
            for f in checkpoint_files
        ]
        return checkpoint_ids
    def delete(self, checkpoint_id: Optional[str] = None) -> bool:
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
            return True
        return False

class ResumableOperation:
    """
    Base class for operations that can be resumed after interruption.
    """
    def __init__(self, checkpoint_dir: Optional[str] = None, operation_name: str = "operation", auto_checkpoint_interval: Optional[int] = None):
        # Load configuration
        config = _get_checkpoint_config()
        
        self.checkpoint = Checkpoint(checkpoint_dir, operation_name)
        self.auto_checkpoint_interval = auto_checkpoint_interval or config.get('auto_checkpoint_interval', 100)
        self.items_since_checkpoint = 0
        self.state: Dict[str, Any] = {}
    def get_state(self) -> Dict[str, Any]:
        return self.state
    def set_state(self, state: Dict[str, Any]) -> None:
        self.state = state
    def save_checkpoint(self) -> None:
        self.checkpoint.save(self.get_state())
        self.items_since_checkpoint = 0
    def load_checkpoint(self) -> bool:
        try:
            state = self.checkpoint.load()
            self.set_state(state)
            return True
        except FileNotFoundError:
            return False
    def update_progress(self, items_processed: int = 1) -> None:
        self.items_since_checkpoint += items_processed
        if self.items_since_checkpoint >= self.auto_checkpoint_interval:
            self.save_checkpoint()
    def execute(self) -> Any:
        raise NotImplementedError("Subclasses must implement execute()")

def create_operation_id(operation_name: str, **kwargs) -> str:
    params_str = json.dumps(kwargs, sort_keys=True)
    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
    return f"{operation_name}_{params_hash}"

class JSONCheckpoint:
    """
    Lightweight checkpointing using JSON files (for batch/chunk progress, stats, etc).
    """
    def __init__(self, checkpoint_path: str):
        self.checkpoint_path = Path(checkpoint_path)

    def save(self, state: dict):
        with self.checkpoint_path.open('w') as f:
            json.dump(state, f)

    def load(self) -> dict:
        if not self.checkpoint_path.exists():
            return {}
        with self.checkpoint_path.open('r') as f:
            return json.load(f)

    def exists(self) -> bool:
        return self.checkpoint_path.exists()

    def delete(self):
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()

class ResumableBatchOperation:
    """
    Processes batches with checkpointing, allowing resumption after interruption.
    Uses JSONCheckpoint by default.
    """
    def __init__(self, batches: List, process_fn: Callable, checkpoint_path: Optional[str] = None):
        # Load configuration
        config = _get_checkpoint_config()
        naming_config = config.get('naming', {})
        
        self.batches = batches
        self.process_fn = process_fn
        default_path = naming_config.get('batch_checkpoint_filename', 'batch_checkpoint.json')
        self.checkpoint = JSONCheckpoint(checkpoint_path or default_path)
        self.start_index = 0
        self._load_checkpoint()

    def _load_checkpoint(self):
        if self.checkpoint.exists():
            data = self.checkpoint.load()
            self.start_index = data.get("last_completed", 0) + 1
        else:
            self.start_index = 0

    def _save_checkpoint(self, idx: int):
        self.checkpoint.save({"last_completed": idx})

    def process(self) -> list:
        results = [None] * len(self.batches)
        for idx in range(self.start_index, len(self.batches)):
            batch = self.batches[idx]
            result = self.process_fn(batch)
            results[idx] = result
            self._save_checkpoint(idx)
        return results

    def clear_checkpoint(self):
        self.checkpoint.delete()

# Example usage (as a comment):
#
# def process_batch(batch):
#     print(f"Processing batch: {batch}")
#     return sum(batch)
#
# batches = [[1,2,3], [4,5,6], [7,8,9]]
# op = ResumableBatchOperation(batches, process_batch, checkpoint_path="my_batch_checkpoint.json")
# results = op.process()
# print(results)
#
# # For general state checkpointing, use Checkpoint/ResumableOperation as before.
# ... existing code ... 
