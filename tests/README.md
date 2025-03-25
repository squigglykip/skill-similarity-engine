# Skill Similarity Engine Tests

This directory contains tests for the Skill Similarity Engine.

## Test Structure

The tests are organized into three main categories:

### 1. Unit Tests

Located in the `unit/` directory, these tests focus on testing individual components in isolation. Unit tests verify that the smallest testable parts of the application work correctly on their own.

Examples:
- Testing the `Skill` class methods
- Testing the CosineSimilarityCalculator independent of other components
- Testing the data normalization functions

### 2. Integration Tests

Located in the `integration/` directory, these tests focus on testing how components work together. Integration tests verify that different modules or services used by the application work well together.

Examples:
- Testing CSV export formats for Power BI
- Testing job similarity calculations
- Testing edge case handling across components

### 3. Functional Tests

Located in the `functional/` directory, these tests focus on testing complete workflows and end-to-end functionality. Functional tests verify that the system meets functional requirements.

Examples:
- Testing the CLI commands
- Testing the gap analysis workflow
- Testing performance with realistic data volumes

## Running Tests

### Run All Tests

To run all tests:

```bash
cd skill-similarity-engine
python -m unittest discover -s tests
```

### Run Specific Test Categories

To run unit tests only:

```bash
cd skill-similarity-engine
python -m unittest discover -s tests/unit
```

To run integration tests only:

```bash
cd skill-similarity-engine
python -m unittest discover -s tests/integration
```

To run functional tests only:

```bash
cd skill-similarity-engine
python -m unittest discover -s tests/functional
```

### Run a Specific Test File

To run a specific test file:

```bash
cd skill-similarity-engine
python tests/path/to/test_file.py
```

### Run with Verbose Output

Add the `-v` flag for more detailed output:

```bash
cd skill-similarity-engine
python -m unittest discover -s tests -v
```

## Writing New Tests

When adding new tests, please follow these guidelines:

1. **Unit Tests**: Focus on testing a single function or class in isolation. Use mocks for dependencies.
2. **Integration Tests**: Test interactions between components. Minimize mocking of internal components.
3. **Functional Tests**: Test end-to-end workflows. These tests should be as close to real usage as possible.

All test files should:
- Start with `test_` prefix
- Include docstrings explaining the purpose of the test
- Be written using the `unittest` framework
- Include appropriate assertions to verify behavior 