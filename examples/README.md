# Skill Similarity Engine Examples

This directory contains practical examples demonstrating how to use different components of the Skill Similarity Engine. Unlike the test suite, which focuses on verifying functionality, these examples show real-world usage patterns and produce tangible outputs that help understand the system's behavior.

## Purpose

These examples serve multiple purposes:

1. **Documentation**: They show developers how to use various components of the system
2. **Validation**: They confirm that our APIs are intuitive and usable
3. **Demonstration**: They provide visual evidence of system behavior (e.g., memory usage patterns)
4. **Education**: They help new team members understand how different parts of the system work together

## Organization

The examples are organized by module or feature:

- `memory_management/`: Examples showing memory optimization features
- (Additional directories will be added as we develop examples for other features)

## Running the Examples

### Setup

Before running any examples, ensure that the Skill Similarity Engine package is installed or in your Python path:

```bash
# Navigate to the skill-similarity-engine root directory
cd skill-similarity-engine

# Either install in development mode
pip install -e .

# Or add the project root to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### Memory Management Examples

The `memory_management/` directory contains examples demonstrating memory tracking, visualization, and optimization:

1. **Dashboard Demo** (`dashboard_demo.py`): Shows real-time memory tracking during data processing.

   ```bash
   python examples/memory_management/dashboard_demo.py
   ```

   This script simulates a typical workflow (data loading, vectorization, similarity calculation) while tracking memory usage. It generates visualizations showing memory patterns at each stage.

2. **Memory-Efficient Comparison** (`memory_efficient_comparison.py`): Compares memory usage between standard and memory-efficient implementations.

   ```bash
   python examples/memory_management/memory_efficient_comparison.py
   ```

   This script loads progressively larger datasets into both standard and memory-efficient implementations, measuring the memory usage difference. It generates plots showing the memory savings achieved by the optimized implementation.

### Outputs

Most examples generate output files in a `memory_reports/` subdirectory within their own directory. These outputs include:

- PNG visualizations of memory usage
- CSV files with memory metrics 
- Text reports summarizing memory behavior

## Contributing New Examples

When adding new examples:

1. Create a subdirectory for the feature area if it doesn't exist
2. Include comprehensive comments explaining the purpose of the example
3. Make the example self-contained (include data generation if needed)
4. Add clear output that helps understand the system behavior
5. Update this README to include information about the new example

## Relationship to Formal Tests

These examples complement the formal test suite but serve a different purpose:

- **Tests** (in `/tests/`) verify that components work correctly through automated assertions
- **Examples** (in `/examples/`) demonstrate usage patterns and produce visual/tangible outputs

Both are essential for a complete quality assurance strategy.

## Available Examples

### HRIS Example

The `hris_example` directory demonstrates how to transform data from a Human Resource Information System (HRIS) into the format required by the Skill Similarity Engine. It includes:

- **job_data.csv**: Example job data from an HRIS system
- **skills_data.csv**: Example skill data from an HRIS system
- **job_skills_mapping.csv**: Example mapping between jobs and skills
- **hris_schema_mapping.yaml**: Example configuration for transforming the HRIS data

To use this example:

```bash
# Copy the example configuration to the config directory
cp examples/hris_example/hris_schema_mapping.yaml config/

# Run the transformation
python scripts/hris_transform.py --config-file config/hris_schema_mapping.yaml transform-all
```

See the [HRIS Integration Guide](../docs/hris_integration.md) for more details.

### Test Data

The `test_data` directory contains small datasets suitable for testing and demonstration purposes:

- **skills.csv**: A small skills taxonomy
- **jobs.csv**: A small job architecture
- **employees.csv**: Sample employee data

To use this test data:

```bash
# Configure the engine to use test data
python scripts/skillsim.py config init --config-file config/testing.yaml

# Run a similarity analysis
python scripts/run_similarity.py jobs-to-jobs
```

### Visualization Examples

The `visualizations` directory contains examples of various visualization outputs:

- **heatmap_sample.png**: Example heatmap of job similarities
- **network_graph_sample.png**: Example network graph of job relationships
- **career_path_sample.png**: Example career pathway visualization

## Creating Your Own Examples

To create your own examples:

1. Create a new directory under `examples/`
2. Include sample data files and configuration
3. Add a README.md explaining how to use your example
4. Reference your example in this main README 