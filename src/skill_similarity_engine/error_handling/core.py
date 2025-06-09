from enum import Enum
from skill_similarity_engine.logging.config import setup_logging

logger = setup_logging()

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
    """
    Base error class for the Skill Similarity Engine with context and severity.
    """
    def __init__(self, message, category=ErrorCategory.UNKNOWN, severity=ErrorSeverity.ERROR, context=None):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.context = context or {}
        # Log the error when created
        logger.error({
            "event": "error",
            "category": self.category.value,
            "severity": self.severity.value,
            "context": self.context,
            "message": message
        })

# Example usage (as a comment):
# try:
#     raise EngineError("Failed to process job data", category=ErrorCategory.DATA, severity=ErrorSeverity.CRITICAL, context={"job_id": 123})
# except EngineError as e:
#     pass 