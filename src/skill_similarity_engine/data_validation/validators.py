import yaml
import os
import sys
import argparse
import pandas as pd
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

class TypeValidator(Validator):
    """
    Checks that a field is of a given type (string, int, float, bool).
    """
    def __init__(self, field, expected_type):
        super().__init__(f"TypeValidator({field}, {expected_type})")
        self.field = field
        self.expected_type = expected_type

    def validate(self, data):
        value = data.get(self.field)
        if value is None:
            return ValidationResult(True)  # NotNullValidator handles nulls
        type_map = {
            "string": str,
            "int": int,
            "float": float,
            "bool": bool
        }
        py_type = type_map.get(self.expected_type)
        if py_type is None:
            return ValidationResult(True)  # Unknown type, skip
        # Special case: allow int/float as string if value is string
        if self.expected_type == "string":
            if isinstance(value, str):
                return ValidationResult(True)
            # Accept numbers as strings if they can be cast
            try:
                str(value)
                return ValidationResult(True)
            except Exception:
                pass
        if not isinstance(value, py_type):
            msg = f"Field '{self.field}' expected type {self.expected_type}, got {type(value).__name__}."
            logger.warning({
                "event": "validation_failure",
                "validator": self.name,
                "field": self.field,
                "context": data
            })
            return ValidationResult(False, msg, {"field": self.field})
        return ValidationResult(True)

class ValidationEngine:
    """
    Loads a schema config and applies validators to a dataset.
    """
    def __init__(self, schema_section, config_path=None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '../../config/data_validation_schema.yaml')
        with open(config_path, 'r') as f:
            self.schema = yaml.safe_load(f)[schema_section]
        self.validators = self._create_validators()

    def _create_validators(self):
        validators = []
        for field, rules in self.schema.items():
            if rules.get('required', False):
                validators.append(NotNullValidator(field))
            if 'type' in rules:
                validators.append(TypeValidator(field, rules['type']))
        return validators

    def validate_row(self, row):
        results = []
        for validator in self.validators:
            result = validator.validate(row)
            results.append(result)
        return results

    def validate_dataset(self, dataset):
        """
        dataset: list of dicts (e.g., from DataFrame.to_dict(orient='records'))
        Returns: list of (row_idx, ValidationResult)
        """
        all_results = []
        for idx, row in enumerate(dataset):
            row_results = self.validate_row(row)
            for result in row_results:
                if not result.passed:
                    all_results.append((idx, result))
        return all_results

# Example usage:
# from skill_similarity_engine.data_validation.validators import ValidationEngine
# import pandas as pd
# df = pd.read_csv('job_data.csv')
# engine = ValidationEngine('jobs')
# results = engine.validate_dataset(df.to_dict(orient='records'))
# for idx, result in results:
#     print(f"Row {idx}: {result.message}")

if __name__ == "__main__":
    # args.file and args.type are set by argparse and are safe to use (linter may not recognise dynamic attributes)
    parser = argparse.ArgumentParser(description="Validate a CSV file against the schema config.")
    parser.add_argument('--type', required=True, choices=['jobs', 'job_skill_mapping', 'skills'], help='Schema section to validate against')
    parser.add_argument('--file', required=True, help='Path to CSV file to validate')
    args = parser.parse_args()

    try:
        df = pd.read_csv(args.file)
    except Exception as e:
        print(f"Error reading file {args.file}: {e}")
        sys.exit(1)

    engine = ValidationEngine(args.type)
    results = engine.validate_dataset(df.to_dict(orient='records'))

    if not results:
        print(f"Validation passed: {len(df)} rows checked, no errors found.")
        sys.exit(0)
    else:
        print(f"Validation failed: {len(results)} errors found in {len(df)} rows.")
        for idx, result in results:
            print(f"Row {idx+1}: {result.message}")
        sys.exit(1) 