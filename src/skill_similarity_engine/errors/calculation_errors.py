"""
Calculation Error Classes for Fail-Fast Implementation
=====================================================

Custom exception classes for business intelligence calculation failures.
These ensure that calculation failures are explicit rather than hidden by fallbacks.
"""

class CalculationError(Exception):
    """Raised when a business intelligence calculation fails."""
    
    def __init__(self, message: str, calculation_type: str = None, data_context: dict = None):
        self.calculation_type = calculation_type
        self.data_context = data_context or {}
        super().__init__(message)

class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    
    def __init__(self, message: str, missing_config: str = None, fix_instruction: str = None):
        self.missing_config = missing_config
        self.fix_instruction = fix_instruction
        super().__init__(message)

class DataQualityError(Exception):
    """Raised when input data is insufficient for calculation."""
    
    def __init__(self, message: str, data_issue: str = None, required_conditions: str = None):
        self.data_issue = data_issue
        self.required_conditions = required_conditions
        super().__init__(message)

class BusinessLogicError(Exception):
    """Raised when business logic cannot be applied to the given data."""
    
    def __init__(self, message: str, business_rule: str = None, violation_details: str = None):
        self.business_rule = business_rule
        self.violation_details = violation_details
        super().__init__(message)
