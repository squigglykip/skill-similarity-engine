from skill_similarity_engine.logging.config import setup_logging

logger = setup_logging()

class ValidationResult:
    def __init__(self, passed, message=None, context=None):
        self.passed = passed
        self.message = message
        self.context = context or {}

class Validator:
    """
    Base class for data validators.
    """
    def __init__(self, name):
        self.name = name

    def validate(self, data):
        """
        Validate the input data. Should be overridden by subclasses.
        Returns a ValidationResult.
        """
        raise NotImplementedError

class NotNullValidator(Validator):
    def __init__(self, field):
        super().__init__(f"NotNullValidator({field})")
        self.field = field

    def validate(self, data):
        if data.get(self.field) is None:
            msg = f"Field '{self.field}' is null."
            logger.warning({
                "event": "validation_failure",
                "validator": self.name,
                "field": self.field,
                "context": data
            })
            return ValidationResult(False, msg, {"field": self.field})
        return ValidationResult(True)

# Example usage (as a comment):
# validator = NotNullValidator("job_id")
# result = validator.validate({"job_id": None, "title": "Analyst"})
# if not result.passed:
#     print(result.message) 