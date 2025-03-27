"""
Command-line interface for configuration management.

This module provides CLI commands for viewing and manipulating configuration.
"""

import json
import os
from pathlib import Path
from typing import Optional

import click
import yaml

from ..config.settings import load_config, get_config


@click.group(name="config")
def config_group():
    """Configuration management commands."""
    pass


@config_group.command(name="view")
@click.option(
    "--format",
    type=click.Choice(["json", "yaml"]),
    default="yaml",
    help="Output format"
)
@click.option(
    "--config-file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Configuration file path"
)
def view_config(format: str, config_file: Optional[str]):
    """
    View the current configuration.
    
    If --config-file is provided, the configuration will be loaded from that file.
    Otherwise, the default configuration will be used.
    """
    if config_file:
        load_config(config_file)
    
    config = get_config()
    
    # Convert config to dictionary with dataclasses.asdict
    from dataclasses import asdict
    config_dict = asdict(config)
    
    # Output in specified format
    if format == "json":
        click.echo(json.dumps(config_dict, indent=2))
    else:  # yaml
        click.echo(yaml.safe_dump(config_dict, default_flow_style=False, sort_keys=False))


@config_group.command(name="init")
@click.option(
    "--output-file",
    type=click.Path(file_okay=True, dir_okay=False),
    required=True,
    help="File path to create configuration in"
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing file"
)
def init_config(output_file: str, force: bool):
    """
    Initialize a configuration file at the specified path.
    
    This command creates a default configuration file with all available settings.
    """
    output_path = Path(output_file)
    
    # Create parent directories if they don't exist
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True)
    
    if force or not output_path.exists():
        with open(output_path, "w") as f:
            f.write("""# Main configuration file for the Skill Similarity Engine
# This file contains all settings for the application

# Version information
version: "0.1.0"

# Directory paths
data_dir: "./data"
output_dir: "./output"

# Normalisation settings
normalisation:
  min_max_scaling: true
  boolean_normalisation: false
  tfidf_weighting: true

# Similarity calculation settings
similarity:
  method: "cosine"
  threshold: 0.7

# Gap analysis settings
gap_analysis:
  min_proficiency_ratio: 0.65
  min_gap_threshold: 0.2
  category_weights:
    technical: 0.6
    soft: 0.3
    domain: 0.1

# Opportunity identification settings
opportunity:
  high_similarity_threshold: 0.8
  critical_skill_gap_threshold: 0.4

# Future extensions (all disabled by default)
future_extensions:
  seniority_weight: 0.0
  role_track_weight: 0.0
  location_weight: 0.0
""")
        click.echo(f"Created configuration file: {output_path}")
    else:
        click.echo(f"Skipped existing file: {output_path}")


def register_commands(cli):
    """Register configuration commands with the CLI."""
    cli.add_command(config_group) 