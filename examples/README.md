# Skill Similarity Engine Examples

This directory contains example data and configurations to help you understand and use the Skill Similarity Engine.

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