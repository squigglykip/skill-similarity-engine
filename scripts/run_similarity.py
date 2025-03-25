#!/usr/bin/env python3
"""
CLI script for running similarity calculations with the skill similarity engine.

This script provides commands for calculating job-to-job, employee-to-job,
and employee-to-employee similarities based on skill profiles.
"""

import os
import sys
import click
from pathlib import Path

# Add the src directory to the path so we can import our package
src_path = str(Path(__file__).parent.parent / 'src')
sys.path.insert(0, src_path)
from skill_similarity_engine.config.settings import get_config, ConfigFormat
from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture
from skill_similarity_engine.models.employees import EmployeeDatabase
from skill_similarity_engine.similarity.cosine import CosineSimilarityCalculator


@click.group()
@click.option(
    "--config-file", 
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
@click.pass_context
def cli(ctx, config_file, output_dir):
    """
    Run similarity calculations between jobs and/or employees.
    
    This tool provides functionality to calculate similarity scores between
    jobs, employees, or employees and jobs based on their skill profiles.
    """
    # Initialize the context object
    ctx.ensure_object(dict)
    
    # Load configuration
    if config_file:
        config_format = ConfigFormat.from_file_extension(config_file)
        config = get_config(config_file, config_format)
    else:
        config = get_config()
    
    # Override output directory if specified
    if output_dir:
        config.output_dir = output_dir
    
    # Create output directory if it doesn't exist
    os.makedirs(config.output_dir, exist_ok=True)
    
    # Store configuration in context
    ctx.obj["config"] = config


@cli.command()
@click.argument("skill_taxonomy_file", type=click.Path(exists=True))
@click.argument("job_architecture_file", type=click.Path(exists=True))
@click.option(
    "--department",
    help="Filter jobs by department"
)
@click.option(
    "--top-n",
    type=int,
    help="Number of top similar jobs to return"
)
@click.option(
    "--threshold",
    type=float,
    help="Similarity threshold (0.0-1.0)"
)
@click.option(
    "--cluster/--no-cluster",
    default=False,
    help="Whether to cluster similar jobs together"
)
@click.option(
    "--output-format",
    type=click.Choice(["csv", "json"]),
    default="csv",
    help="Output file format"
)
@click.pass_context
def job_similarity(ctx, skill_taxonomy_file, job_architecture_file, department, 
                   top_n, threshold, cluster, output_format):
    """
    Calculate job-to-job similarity scores.
    
    This command loads the skill taxonomy and job architecture data,
    and calculates similarity scores between pairs of jobs based on
    their skill profiles.
    """
    config = ctx.obj["config"]
    
    # Override config with command-line options if provided
    if top_n:
        config.similarity.top_n_results = top_n
    if threshold:
        config.similarity.threshold = threshold
    
    click.echo("Loading skill taxonomy...")
    taxonomy = SkillTaxonomy.from_file(skill_taxonomy_file)
    
    click.echo("Loading job architecture...")
    job_arch = JobArchitecture.from_file(job_architecture_file)
    
    click.echo("Calculating job similarities...")
    calculator = CosineSimilarityCalculator(taxonomy)
    
    # Filter by department if specified
    if department:
        click.echo(f"Filtering jobs by department: {department}")
        job_arch = job_arch.filter_by_department(department)
    
    # Calculate similarities
    similarity_matrix = calculator.calculate_job_similarity_matrix(job_arch)
    
    # Generate output filename
    dept_suffix = f"_{department}" if department else ""
    output_file = os.path.join(
        config.output_dir, 
        f"job_similarity{dept_suffix}.{output_format}"
    )
    
    # Save results
    click.echo(f"Saving results to {output_file}...")
    if output_format == "csv":
        similarity_matrix.to_csv(output_file)
    else:
        similarity_matrix.to_json(output_file, orient="records")
    
    click.echo("Job similarity calculation completed!")


@cli.command()
@click.argument("skill_taxonomy_file", type=click.Path(exists=True))
@click.argument("job_architecture_file", type=click.Path(exists=True))
@click.argument("employee_database_file", type=click.Path(exists=True))
@click.option(
    "--department",
    help="Filter by department"
)
@click.option(
    "--top-n",
    type=int,
    help="Number of top similar matches to return"
)
@click.option(
    "--threshold",
    type=float,
    help="Similarity threshold (0.0-1.0)"
)
@click.option(
    "--output-format",
    type=click.Choice(["csv", "json"]),
    default="csv",
    help="Output file format"
)
@click.pass_context
def employee_job_similarity(ctx, skill_taxonomy_file, job_architecture_file, 
                           employee_database_file, department, top_n, 
                           threshold, output_format):
    """
    Calculate employee-to-job similarity scores.
    
    This command loads the skill taxonomy, job architecture, and employee data,
    and calculates how well each employee matches with different jobs based on
    their skill profiles.
    """
    config = ctx.obj["config"]
    
    # Override config with command-line options if provided
    if top_n:
        config.similarity.top_n_results = top_n
    if threshold:
        config.similarity.threshold = threshold
    
    click.echo("Loading skill taxonomy...")
    taxonomy = SkillTaxonomy.from_file(skill_taxonomy_file)
    
    click.echo("Loading job architecture...")
    job_arch = JobArchitecture.from_file(job_architecture_file)
    
    click.echo("Loading employee database...")
    employee_db = EmployeeDatabase.from_file(employee_database_file)
    
    # Filter by department if specified
    if department:
        click.echo(f"Filtering by department: {department}")
        job_arch = job_arch.filter_by_department(department)
        employee_db = employee_db.filter_by_department(department)
    
    click.echo("Calculating employee-job similarities...")
    calculator = CosineSimilarityCalculator(taxonomy)
    similarity_matrix = calculator.calculate_employee_job_similarity_matrix(
        employee_db, job_arch
    )
    
    # Generate output filename
    dept_suffix = f"_{department}" if department else ""
    output_file = os.path.join(
        config.output_dir, 
        f"employee_job_similarity{dept_suffix}.{output_format}"
    )
    
    # Save results
    click.echo(f"Saving results to {output_file}...")
    if output_format == "csv":
        similarity_matrix.to_csv(output_file)
    else:
        similarity_matrix.to_json(output_file, orient="records")
    
    click.echo("Employee-job similarity calculation completed!")


@cli.command()
@click.argument("skill_taxonomy_file", type=click.Path(exists=True))
@click.argument("employee_database_file", type=click.Path(exists=True))
@click.option(
    "--department",
    help="Filter employees by department"
)
@click.option(
    "--top-n",
    type=int,
    help="Number of top similar employees to return"
)
@click.option(
    "--threshold",
    type=float,
    help="Similarity threshold (0.0-1.0)"
)
@click.option(
    "--output-format",
    type=click.Choice(["csv", "json"]),
    default="csv",
    help="Output file format"
)
@click.pass_context
def employee_similarity(ctx, skill_taxonomy_file, employee_database_file, 
                         department, top_n, threshold, output_format):
    """
    Calculate employee-to-employee similarity scores.
    
    This command loads the skill taxonomy and employee data, and calculates
    similarity scores between pairs of employees based on their skill profiles.
    """
    config = ctx.obj["config"]
    
    # Override config with command-line options if provided
    if top_n:
        config.similarity.top_n_results = top_n
    if threshold:
        config.similarity.threshold = threshold
    
    click.echo("Loading skill taxonomy...")
    taxonomy = SkillTaxonomy.from_file(skill_taxonomy_file)
    
    click.echo("Loading employee database...")
    employee_db = EmployeeDatabase.from_file(employee_database_file)
    
    # Filter by department if specified
    if department:
        click.echo(f"Filtering employees by department: {department}")
        employee_db = employee_db.filter_by_department(department)
    
    click.echo("Calculating employee similarities...")
    calculator = CosineSimilarityCalculator(taxonomy)
    similarity_matrix = calculator.calculate_employee_similarity_matrix(employee_db)
    
    # Generate output filename
    dept_suffix = f"_{department}" if department else ""
    output_file = os.path.join(
        config.output_dir, 
        f"employee_similarity{dept_suffix}.{output_format}"
    )
    
    # Save results
    click.echo(f"Saving results to {output_file}...")
    if output_format == "csv":
        similarity_matrix.to_csv(output_file)
    else:
        similarity_matrix.to_json(output_file, orient="records")
    
    click.echo("Employee similarity calculation completed!")


if __name__ == "__main__":
    cli(obj={})
