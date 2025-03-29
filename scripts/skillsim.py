#!/usr/bin/env python3
"""
Main CLI entry point for the Skill Similarity Engine.

This script provides a unified interface to all functionality of the
skill similarity engine, including similarity calculations, gap analysis,
and report generation.
"""

import os
import sys
import click
from pathlib import Path

# Add the src directory to the path so we can import our package
src_path = str(Path(__file__).parent.parent / 'src')
sys.path.insert(0, src_path)
from skill_similarity_engine.config.settings import get_config, ConfigFormat, AppConfig, load_config


@click.group()
@click.option(
    "--config",
    "-c", 
    type=click.Path(exists=True),
    help="Path to configuration file (YAML or JSON)"
)
@click.option(
    "--output-dir", 
    "-o", 
    type=click.Path(),
    help="Directory for output files"
)
@click.option(
    "--verbose/--quiet",
    default=True,
    help="Enable/disable verbose output"
)
@click.pass_context
def cli(ctx, config, output_dir, verbose):
    """
    Skill Similarity Engine - Workforce Analytics Tool.
    
    This tool provides functionality for analyzing skill similarities between
    jobs and employees, identifying reskilling opportunities, and generating
    reports for workforce planning.
    """
    # Initialize the context object
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    
    # Load configuration
    if config:
        try:
            load_config(config)
            config_obj = get_config()
        except Exception as e:
            click.echo(f"Error loading configuration: {e}", err=True)
            ctx.exit(2)
    else:
        config_obj = get_config()
    
    # Override output directory if specified
    if output_dir:
        config_obj.output_dir = output_dir
    
    # Create output directory if it doesn't exist
    os.makedirs(config_obj.output_dir, exist_ok=True)
    
    # Store configuration in context
    ctx.obj["config"] = config_obj
    
    if verbose:
        click.echo(f"Using configuration: {config or 'default'}")
        click.echo(f"Output directory: {config_obj.output_dir}")


# Import commands from other CLI scripts
sys.path.append(str(Path(__file__).parent))  # Add scripts directory to path
from run_similarity import job_similarity, employee_job_similarity, employee_similarity
from generate_reports import (
    skill_gap_analysis, job_similarity_export, 
    employee_similarity_export, workforce_planning_export
)

# Import configuration commands
from skill_similarity_engine.cli.config_cmd import config_group

# Add commands to the main CLI
cli.add_command(job_similarity)
cli.add_command(employee_job_similarity)
cli.add_command(employee_similarity)
cli.add_command(skill_gap_analysis)
cli.add_command(job_similarity_export)
cli.add_command(employee_similarity_export)
cli.add_command(workforce_planning_export)
cli.add_command(config_group)


@cli.command()
@click.option(
    "--output-format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format for the configuration template"
)
@click.argument("output_file", required=False)
@click.pass_context
def generate_config(ctx, output_format, output_file):
    """
    Generate a configuration file template.
    
    This command creates a template configuration file with default settings
    that can be customized for specific use cases.
    """
    # Create a default configuration
    config = AppConfig()
    
    # Determine the output file
    if not output_file:
        output_file = f"config_template.{output_format}"
    
    # Generate the configuration file
    if output_format == "yaml":
        import yaml
        with open(output_file, "w") as f:
            yaml.dump(config.__dict__, f, default_flow_style=False)
    else:  # json
        import json
        with open(output_file, "w") as f:
            json.dump(config.__dict__, f, indent=2)
    
    click.echo(f"Configuration template generated: {output_file}")


@cli.command()
@click.pass_context
def version(ctx):
    """
    Display the version information for the Skill Similarity Engine.
    """
    # Try to get version from the actual package
    try:
        from skill_similarity_engine import __version__
        version = __version__
    except (ImportError, AttributeError):
        # Fallback to a default version
        version = "0.1.0 (development)"
    
    click.echo(f"Skill Similarity Engine version: {version}")
    click.echo("Copyright (c) 2023 NAB")


if __name__ == "__main__":
    cli(obj={}) 