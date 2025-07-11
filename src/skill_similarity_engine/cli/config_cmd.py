"""
Command-line interface for configuration management.

This module provides CLI commands for viewing and manipulating configuration.

NO HARDCODED VALUES - All configuration externalized following PTH philosophy.
"""

import json
import os
from pathlib import Path
from typing import Optional

import click
import yaml

from ..config.architectural_config_manager import get_config_manager
from ..config.settings import load_config, get_config


@click.group(name="config")
def config_group():
    """Configuration management commands."""
    pass


@config_group.command(name="view")
@click.option(
    "--format",
    type=click.Choice(["json", "yaml"]),
    default=None,  # Will be set from configuration
    help="Output format"
)
@click.option(
    "--config-file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Configuration file path"
)
def view_config(format: Optional[str], config_file: Optional[str]):
    """
    View the current configuration.
    
    If --config-file is provided, the configuration will be loaded from that file.
    Otherwise, the default configuration will be used.
    """
    # Use architectural configuration manager for defaults
    config_manager = get_config_manager()
    
    # Get default format from configuration if not specified
    if format is None:
        format = config_manager.get_nested_value('cli', 'output_formats', 'default', default='yaml')
    
    if config_file:
        load_config(config_file)
    
    config = get_config()
    
    # Convert config to dictionary with dataclasses.asdict
    from dataclasses import asdict
    config_dict = asdict(config)
    
    # Output in specified format
    if format == "json":
        click.echo(json.dumps(config_dict, indent=2, default=str))
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
        # Get configuration template from architectural configuration (NO hardcoded values)
        config_manager = get_config_manager()
        template_config = config_manager.get_nested_value('cli', 'default_config_template', default={})
        
        # Generate configuration content from template
        config_content = "# Main configuration file for the Skill Similarity Engine\n"
        config_content += "# This file contains all settings for the application\n\n"
        config_content += yaml.safe_dump(template_config, default_flow_style=False, sort_keys=False)
        
        with open(output_path, "w") as f:
            f.write(config_content)
        click.echo(f"Created configuration file: {output_path}")
    else:
        click.echo(f"Skipped existing file: {output_path}")


def register_commands(cli):
    """Register configuration commands with the CLI."""
    cli.add_command(config_group) 
