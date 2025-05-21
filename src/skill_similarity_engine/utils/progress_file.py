import json
import time
from pathlib import Path

class ProgressStatsRecorder:
    def __init__(self, tracker, filepath, interval=100):
        """
        tracker: Any object with a get_stats() method returning a dataclass or dict
        filepath: Where to write the stats file
        interval: How often to write (every N updates)
        """
        self.tracker = tracker
        self.filepath = Path(filepath)
        self.interval = interval
        self.last_written = 0

    def maybe_record(self):
        if self.tracker.stats.completed_items - self.last_written >= self.interval:
            self.record()
            self.last_written = self.tracker.stats.completed_items

    def record(self):
        stats = self.tracker.get_stats()
        # Convert dataclass to dict if needed
        if hasattr(stats, '__dict__'):
            stats = stats.__dict__.copy()  # Use a copy to avoid mutating the original
        stats['timestamp'] = time.time()
        # Convert MemoryUsage to dict or just MB value
        if 'memory_usage' in stats and stats['memory_usage'] is not None:
            mem = stats['memory_usage']
            if hasattr(mem, '__dict__'):
                stats['memory_usage'] = mem.__dict__
            else:
                stats['memory_usage'] = str(mem)
        with self.filepath.open('w') as f:
            json.dump(stats, f, indent=2)

class CheckpointManager:
    def __init__(self, checkpoint_path):
        self.checkpoint_path = Path(checkpoint_path)

    def save(self, chunk_index):
        with self.checkpoint_path.open('w') as f:
            json.dump({'last_completed_chunk': chunk_index, 'timestamp': time.time()}, f)

    def load(self):
        if not self.checkpoint_path.exists():
            return None
        with self.checkpoint_path.open('r') as f:
            data = json.load(f)
        return data.get('last_completed_chunk') 