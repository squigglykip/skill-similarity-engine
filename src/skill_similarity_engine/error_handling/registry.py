import threading
from datetime import datetime
import json
import csv
from typing import Optional, Dict, Any, List

# Import architectural configuration manager
try:
    from ..config.architectural_config_manager import get_config_manager
except ImportError:
    # Fallback if architectural config unavailable
    get_config_manager = None

# Import error types with fallback
try:
    from .core import EngineError, ErrorCategory, ErrorSeverity
except ImportError:
    # Basic fallback definitions for standalone usage
    from enum import Enum
    
    class ErrorSeverity(Enum):
        INFO = "info"
        WARNING = "warning"
        ERROR = "error"
        CRITICAL = "critical"
    
    class ErrorCategory(Enum):
        DATA = "data"
        VALIDATION = "validation"
        PROCESSING = "processing"
        SYSTEM = "system"
        UNKNOWN = "unknown"
    
    class EngineError(Exception):
        def __init__(self, message, category=None, severity=None, context=None):
            super().__init__(message)
            self.category = category or ErrorCategory.UNKNOWN
            self.severity = severity or ErrorSeverity.ERROR
            self.context = context or {}


def _get_registry_config():
    """Get error registry configuration from architectural config manager."""
    if get_config_manager is None:
        # Fallback configuration
        return {
            'export_formats': ['json', 'csv'],
            'default_export_format': 'json',
            'export_directory': 'error_reports',
            'auto_categorise_errors': True,
            'log_all_registrations': True,
            'max_errors_per_category': 1000,
            'error_summary_threshold': 50
        }
    
    try:
        config_manager = get_config_manager()
        return config_manager.get_nested_value('error_handling', 'registry', default={
            'export_formats': ['json', 'csv'],
            'default_export_format': 'json',
            'export_directory': 'error_reports',
            'auto_categorise_errors': True,
            'log_all_registrations': True,
            'max_errors_per_category': 1000,
            'error_summary_threshold': 50
        })
    except Exception:
        # Fallback if configuration loading fails
        return {
            'export_formats': ['json', 'csv'],
            'default_export_format': 'json',
            'export_directory': 'error_reports',
            'auto_categorise_errors': True,
            'log_all_registrations': True,
            'max_errors_per_category': 1000,
            'error_summary_threshold': 50
        }


class ErrorContext:
    """
    Context information for an error (from utils/error_handling.py)
    """
    def __init__(self, function_name, args, kwargs, exception, traceback_str, timestamp):
        self.function_name = function_name
        self.args = args
        self.kwargs = kwargs
        self.exception = exception
        self.traceback_str = traceback_str
        self.timestamp = timestamp
    def to_dict(self):
        return {
            "function_name": self.function_name,
            "args": str(self.args),
            "kwargs": str(self.kwargs),
            "exception_type": type(self.exception).__name__,
            "exception_message": str(self.exception),
            "traceback": self.traceback_str,
            "timestamp": self.timestamp,
            "timestamp_readable": datetime.fromtimestamp(self.timestamp).isoformat()
        }

class ErrorRegistry:
    """
    Singleton registry for tracking errors during a run.
    Can register EngineError or ErrorContext objects.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._errors = []
            return cls._instance

    def register(self, error):
        if isinstance(error, ErrorContext):
            entry = error.to_dict()
        else:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "category": getattr(error, 'category', ErrorCategory.UNKNOWN).value,
                "severity": getattr(error, 'severity', ErrorSeverity.ERROR).value,
                "context": getattr(error, 'context', {}),
                "message": str(error),
                "type": type(error).__name__,
            }
        self._errors.append(entry)

    def get_all(self):
        return list(self._errors)

    def filter(self, category=None, severity=None):
        return [e for e in self._errors
                if (category is None or e.get("category") == (category.value if category else None))
                and (severity is None or e.get("severity") == (severity.value if severity else None))]

    def summary(self):
        from collections import Counter
        cat_counts = Counter(e.get("category", "") for e in self._errors)
        sev_counts = Counter(e.get("severity", "") for e in self._errors)
        return {"by_category": dict(cat_counts), "by_severity": dict(sev_counts), "total": len(self._errors)}

    def export_json(self, filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self._errors, f, indent=2)

    def export_csv(self, filepath):
        if not self._errors:
            return
        keys = list(self._errors[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self._errors)

# Patch EngineError to auto-register with the registry
_old_init = EngineError.__init__
def _new_init(self, *args, **kwargs):
    _old_init(self, *args, **kwargs)
    ErrorRegistry().register(self)
EngineError.__init__ = _new_init
