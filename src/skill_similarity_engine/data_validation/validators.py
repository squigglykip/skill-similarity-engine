import os
import yaml
import sys
import argparse
import logging
import pandas as pd

# Import field mapping utilities
from ..config.field_mapping import get_field_mapper, get_raw_field_name
from ..config.architectural_config_manager import get_config_manager

# Setup basic logging
logger = logging.getLogger(__name__)

def find_schema_path():
    """
    Find schema path using architectural configuration manager.
    
    Returns:
        Path to data validation schema file
        
    Raises:
        RuntimeError: If schema file cannot be found
    """
    try:
        # Use architectural config manager for schema discovery
        config_manager = get_config_manager()
        schema_config = config_manager.get_nested_value('data_validation', 'schema_files', default={})
        
        search_paths = schema_config.get('schema_search_paths', [
            'config/data',
            '../config/data', 
            '../../config/data',
            'config',  # Legacy fallback
            '../config', 
            '../../config'
        ])
        schema_filenames = schema_config.get('alternative_schema_names', [
            'validation_schema.yaml',  # New modular name
            'data_validation_schema.yaml'  # Legacy name
        ])
        
        # Search in configured paths
        from pathlib import Path
        here = Path(__file__).parent
        
        for search_path in search_paths:
            config_dir = here / search_path
            for filename in schema_filenames:
                schema_path = config_dir / filename
                if schema_path.is_file():
                    return str(schema_path)
        
        # Fallback to legacy search if configuration fails
        return _legacy_find_schema_path()
        
    except Exception:
        # Fallback to legacy search method
        return _legacy_find_schema_path()


def _legacy_find_schema_path():
    """Legacy schema path discovery method with modular structure support."""
    from pathlib import Path
    here = Path(__file__).parent
    
    # Try new modular structure first
    search_locations = [
        ('config/data', 'validation_schema.yaml'),  # New modular location
        ('config/data', 'data_validation_schema.yaml'),  # Legacy name in new location
        ('config', 'data_validation_schema.yaml'),  # Original legacy location
    ]
    
    for config_subdir, filename in search_locations:
        current = here
        while True:
            config_dir = current / config_subdir
            schema_path = config_dir / filename
            if schema_path.is_file():
                return str(schema_path)
            parent = current.parent
            if parent == current:
                break  # Reached root, try next location
            current = parent
    
    raise RuntimeError("Could not find validation schema file in any location (tried: validation_schema.yaml, data_validation_schema.yaml)")


SCHEMA_PATH = find_schema_path()

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
    def __init__(self, field, validation_config=None):
        super().__init__(f"NotNullValidator({field})")
        self.field = field
        self.validation_config = validation_config or {}

    def validate(self, data):
        if data.get(self.field) is None:
            msg = f"Field '{self.field}' is null."
            if self.validation_config.get('log_validation_failures', True):
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
    def __init__(self, field, expected_type, validation_config=None):
        super().__init__(f"TypeValidator({field}, {expected_type})")
        self.field = field
        self.expected_type = expected_type
        self.validation_config = validation_config or {}

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
            if self.validation_config.get('log_validation_failures', True):
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
    Now integrated with field mapping system to use canonical field names internally.
    
    Architecture: Configuration-Driven Design Pattern following PTH's enterprise patterns
    """
    def __init__(self, schema_section, config_path=None):
        if config_path is None:
            config_path = SCHEMA_PATH
        with open(config_path, 'r') as f:
            self.schema = yaml.safe_load(f)[schema_section]
        self.schema_section = schema_section
        
        # Load validation behaviour configuration
        try:
            config_manager = get_config_manager()
            self.validation_config = config_manager.get_nested_value('data_validation', 'validation_behaviour', default={})
        except Exception:
            self.validation_config = {}
        
        # Initialize field mapper for canonical name resolution
        self.field_mapper = get_field_mapper()
        
        self.validators = self._create_validators()

    def _create_validators(self):
        """
        Create validators using canonical field names and validation configuration.
        Maps raw schema field names to canonical names.
        """
        validators = []
        for raw_field_name, rules in self.schema.items():
            # Map raw field name to canonical name
            canonical_field_name = self._map_to_canonical_name(raw_field_name)
            
            if rules.get('required', False):
                validators.append(NotNullValidator(canonical_field_name, self.validation_config))
            if 'type' in rules:
                validators.append(TypeValidator(canonical_field_name, rules['type'], self.validation_config))
        return validators
    
    def _map_to_canonical_name(self, raw_field_name):
        """
        Map raw schema field name to canonical field name.
        
        Args:
            raw_field_name: Raw field name from schema (e.g., 'Skill_ID', 'RoleSet')
            
        Returns:
            Canonical field name (e.g., 'skill_id', 'title')
        """
        # Create reverse mapping from field mapping configuration
        field_mappings = self.field_mapper.get_field_mapping_dict(self.schema_section)
        
        # Look for canonical name that maps to this raw field name
        for canonical_name, raw_mapping in field_mappings.items():
            if isinstance(raw_mapping, str):
                if raw_mapping == raw_field_name:
                    return canonical_name
            elif isinstance(raw_mapping, list):
                if raw_field_name in raw_mapping:
                    return canonical_name
        
        # If no mapping found, use the raw field name as canonical 
        # (with configurable normalisation)
        if self.validation_config.get('normalise_field_names', True):
            canonical_name = raw_field_name.lower().replace(' ', '_')
        else:
            canonical_name = raw_field_name
        
        if self.validation_config.get('log_validation_failures', True):
            logger.warning(f"No canonical mapping found for raw field '{raw_field_name}' in section '{self.schema_section}', using normalised name '{canonical_name}'")
        
        return canonical_name

    def validate_row(self, row):
        """
        Validate a row using canonical field names.
        Maps row fields from raw to canonical names before validation.
        
        Args:
            row: Dictionary with raw field names
            
        Returns:
            List of ValidationResult objects
        """
        # Map row fields from raw to canonical names
        canonical_row = self._map_row_to_canonical(row)
        
        results = []
        for validator in self.validators:
            result = validator.validate(canonical_row)
            results.append(result)
        return results
    
    def _map_row_to_canonical(self, row):
        """
        Map row fields from raw names to canonical names.
        
        Args:
            row: Dictionary with raw field names
            
        Returns:
            Dictionary with canonical field names
        """
        canonical_row = {}
        
        for raw_field_name, value in row.items():
            canonical_name = self._map_to_canonical_name(raw_field_name)
            canonical_row[canonical_name] = value
            
        return canonical_row

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
