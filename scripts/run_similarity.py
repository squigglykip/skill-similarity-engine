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
import pandas as pd

# Add the src directory to the path so we can import our package
src_path = str(Path(__file__).parent.parent / 'src')
sys.path.insert(0, src_path)
from skill_similarity_engine.config.settings import get_config, ConfigFormat, ConfigManager
from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture
from skill_similarity_engine.models.employees import EmployeeDatabase
from skill_similarity_engine.similarity.cosine import CosineSimilarityCalculator, TfidfVectorizer
from skill_similarity_engine.visualization.manager import VisualisationManager


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
@click.option(
    "--output-dir", 
    type=click.Path(),
    help="Directory for output files"
)
@click.option(
    "--seniority-weight",
    type=float,
    help="Weight for seniority in similarity calculation (0.0-1.0)"
)
@click.option(
    "--role-track-weight",
    type=float,
    help="Weight for role track in similarity calculation (0.0-1.0)"
)
@click.option(
    "--location-weight",
    type=float,
    help="Weight for location in similarity calculation (0.0-1.0)"
)
@click.pass_context
def job_similarity(ctx, skill_taxonomy_file, job_architecture_file, department, 
                  top_n, threshold, cluster, output_format, output_dir,
                  seniority_weight, role_track_weight, location_weight):
    """
    Calculate job-to-job similarity scores.
    
    This command loads the skill taxonomy and job architecture data,
    and calculates similarity scores between pairs of jobs based on
    their skill profiles and other factors if enabled (seniority, role track, location).
    
    Enhancements can be toggled with the following options:
    --seniority-weight: Weight for seniority similarity (0.0 = disabled, 1.0 = max effect)
    --role-track-weight: Weight for role track similarity (0.0 = disabled, 1.0 = max effect)
    --location-weight: Weight for location similarity (0.0 = disabled, 1.0 = max effect)
    """
    config = ctx.obj["config"]
    
    # Override config with command-line options if provided
    if top_n:
        config.similarity.top_n_results = top_n
    if threshold:
        config.similarity.threshold = threshold
    if output_dir:
        config.output_dir = output_dir
    
    # Update enhancement weights if provided
    if seniority_weight is not None:
        config.future_extensions.seniority_weight = seniority_weight
    if role_track_weight is not None:
        config.future_extensions.role_track_weight = role_track_weight
    if location_weight is not None:
        config.future_extensions.location_weight = location_weight
    
    # Log the enhancement settings
    enhancements_enabled = (
        config.future_extensions.seniority_weight > 0 or
        config.future_extensions.role_track_weight > 0 or
        config.future_extensions.location_weight > 0
    )
    
    click.echo("Loading skill taxonomy...")
    taxonomy = SkillTaxonomy.from_file(skill_taxonomy_file)
    
    click.echo("Loading job architecture...")
    job_arch = JobArchitecture.from_file(job_architecture_file)
    
    # Log information about the enhancement features used
    if enhancements_enabled:
        click.echo("Enhancement features enabled:")
        if config.future_extensions.seniority_weight > 0:
            click.echo(f"  - Seniority (weight: {config.future_extensions.seniority_weight:.2f})")
        if config.future_extensions.role_track_weight > 0:
            click.echo(f"  - Role Track (weight: {config.future_extensions.role_track_weight:.2f})")
        if config.future_extensions.location_weight > 0:
            click.echo(f"  - Location (weight: {config.future_extensions.location_weight:.2f})")
    else:
        click.echo("Using skills-only similarity (no enhancements)")
    
    click.echo("Calculating job similarities...")
    # Create the calculator with support for enhancements
    from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator
    from skill_similarity_engine.config.settings import ConfigManager
    
    # Create vectorizer
    vectorizer = TfidfVectorizer(taxonomy)
    
    # Get config manager
    config_manager = ConfigManager()
    config_manager.config = config
    
    # Create calculator
    calculator = CosineSimilarityCalculator(
        vectorizer=vectorizer,
        skill_taxonomy=taxonomy,
        job_architecture=job_arch,
        config_manager=config_manager
    )
    
    # Filter by department if specified
    if department:
        click.echo(f"Filtering jobs by department: {department}")
        filtered_jobs = [job for job in job_arch.jobs.values() if job.department == department]
        # Create a new job architecture with just the filtered jobs
        filtered_arch = JobArchitecture()
        for job in filtered_jobs:
            filtered_arch.add_job(job)
        job_arch = filtered_arch
    
    # Calculate similarities
    similarity_matrix, job_ids = calculator.calculate_similarity_matrix("job")
    
    # Create pandas DataFrame from the matrix
    import numpy as np
    
    # Create a DataFrame with the similarity matrix
    df = pd.DataFrame(
        similarity_matrix,
        index=job_ids,
        columns=job_ids
    )
    
    # Generate output filename with enhancement indicators
    dept_suffix = f"_{department}" if department else ""
    enhancement_suffix = ""
    if enhancements_enabled:
        enhancement_parts = []
        if config.future_extensions.seniority_weight > 0:
            enhancement_parts.append("sen")
        if config.future_extensions.role_track_weight > 0:
            enhancement_parts.append("role")
        if config.future_extensions.location_weight > 0:
            enhancement_parts.append("loc")
        enhancement_suffix = f"_{'_'.join(enhancement_parts)}"
    
    output_file = os.path.join(
        config.output_dir, 
        f"job_similarity{dept_suffix}{enhancement_suffix}.{output_format}"
    )
    
    # Save results
    click.echo(f"Saving results to {output_file}...")
    if output_format == "csv":
        df.to_csv(output_file)
    else:
        df.to_json(output_file, orient="records")
    
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
@click.option(
    "--output-dir", 
    type=click.Path(),
    help="Directory for output files"
)
@click.pass_context
def employee_job_similarity(ctx, skill_taxonomy_file, job_architecture_file, 
                           employee_database_file, department, top_n, 
                           threshold, output_format, output_dir):
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
    if output_dir:
        config.output_dir = output_dir
    
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
    # Initialize the TF-IDF vectorizer first
    vectorizer = TfidfVectorizer(taxonomy)
    # Create the similarity calculator with all required parameters
    calculator = CosineSimilarityCalculator(vectorizer, taxonomy, job_arch, employee_db)
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
@click.option(
    "--output-dir", 
    type=click.Path(),
    help="Directory for output files"
)
@click.pass_context
def employee_similarity(ctx, skill_taxonomy_file, employee_database_file, 
                         department, top_n, threshold, output_format, output_dir):
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
    if output_dir:
        config.output_dir = output_dir
    
    click.echo("Loading skill taxonomy...")
    taxonomy = SkillTaxonomy.from_file(skill_taxonomy_file)
    
    click.echo("Loading employee database...")
    employee_db = EmployeeDatabase.from_file(employee_database_file)
    
    # Filter by department if specified
    if department:
        click.echo(f"Filtering employees by department: {department}")
        employee_db = employee_db.filter_by_department(department)
    
    click.echo("Calculating employee similarities...")
    # Create a minimal empty job architecture for the calculator
    job_arch = JobArchitecture()
    # Initialize the TF-IDF vectorizer first
    vectorizer = TfidfVectorizer(taxonomy)
    # Create the similarity calculator with all required parameters
    calculator = CosineSimilarityCalculator(vectorizer, taxonomy, job_arch, employee_db)
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
