#!/usr/bin/env python3
"""
CLI script for generating reports with the skill similarity engine.

This script provides commands for generating various analytical reports
including skill gap analysis, opportunity reports, and data exports for
Power BI integration.
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
from skill_similarity_engine.analysis.gap import GapAnalyzer
from skill_similarity_engine.visualization.reports import ReportGenerator, ReportConfig


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
    Generate reports and visualisations from skill similarity data.
    
    This tool provides functionality to generate various analytical reports,
    including skill gap analysis, workforce planning reports, and exports
    optimised for Power BI integration.
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
@click.argument("employee_database_file", type=click.Path(exists=True))
@click.option(
    "--employee-id", 
    help="ID of the employee to analyze"
)
@click.option(
    "--target-job-id", 
    help="ID of the target job to analyze"
)
@click.option(
    "--department",
    help="Filter by department"
)
@click.option(
    "--add-opportunity-flags/--no-opportunity-flags",
    default=True,
    help="Whether to add opportunity flags to the output"
)
@click.option(
    "--output-format",
    type=click.Choice(["csv", "json", "excel"]),
    default="csv",
    help="Output file format"
)
@click.pass_context
def skill_gap_analysis(ctx, skill_taxonomy_file, job_architecture_file, 
                      employee_database_file, employee_id, target_job_id, 
                      department, add_opportunity_flags, output_format):
    """
    Generate skill gap analysis reports.
    
    This command analyzes the gap between current employee skills and
    target job requirements. It can analyze a specific employee against
    a specific job, or generate a comprehensive report of employees
    against potential target roles.
    """
    config = ctx.obj["config"]
    
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
    
    # Initialize report generator
    report_config = ReportConfig(
        include_job_metadata=True,
        include_employee_metadata=True,
        add_opportunity_flags=add_opportunity_flags
    )
    report_generator = ReportGenerator(taxonomy, report_config)
    
    # Generate output filename components
    parts = ["skill_gap"]
    if employee_id:
        parts.append(f"emp_{employee_id}")
    if target_job_id:
        parts.append(f"job_{target_job_id}")
    if department:
        parts.append(department)
    
    output_file = os.path.join(
        config.output_dir, 
        f"{'_'.join(parts)}.{output_format}"
    )
    
    # Generate the appropriate report based on parameters
    if employee_id and target_job_id:
        # Specific employee to specific job
        click.echo(f"Analyzing skill gap for employee {employee_id} against job {target_job_id}...")
        employee = employee_db.get_employee(employee_id)
        job = job_arch.get_job(target_job_id)
        
        gap_analyzer = GapAnalyzer(taxonomy, config.gap_analysis)
        gap_analysis = gap_analyzer.analyze_employee_job_gap(employee, job)
        
        if output_format == "csv":
            gap_analysis.to_csv(output_file)
        elif output_format == "json":
            gap_analysis.to_json(output_file, orient="records")
        else:  # excel
            gap_analysis.to_excel(output_file, index=False)
    else:
        # Comprehensive gap analysis
        click.echo("Generating comprehensive skill gap analysis...")
        
        if employee_id:
            # One employee against all jobs
            employee = employee_db.get_employee(employee_id)
            df = report_generator.export_skill_gap_analysis(
                employee=employee, 
                job_architecture=job_arch
            )
        elif target_job_id:
            # All employees against one job
            job = job_arch.get_job(target_job_id)
            df = report_generator.export_skill_gap_analysis(
                job=job, 
                employee_database=employee_db
            )
        else:
            # All employees against relevant jobs
            df = report_generator.export_skill_gap_analysis(
                employee_database=employee_db, 
                job_architecture=job_arch
            )
        
        # Save results
        click.echo(f"Saving results to {output_file}...")
        if output_format == "csv":
            df.to_csv(output_file, index=False)
        elif output_format == "json":
            df.to_json(output_file, orient="records")
        else:  # excel
            df.to_excel(output_file, index=False)
    
    click.echo("Skill gap analysis completed!")


@cli.command()
@click.argument("skill_taxonomy_file", type=click.Path(exists=True))
@click.argument("job_architecture_file", type=click.Path(exists=True))
@click.option(
    "--department",
    help="Filter by department"
)
@click.option(
    "--add-opportunity-flags/--no-opportunity-flags",
    default=True,
    help="Whether to add opportunity flags to the output"
)
@click.option(
    "--output-format",
    type=click.Choice(["csv", "json", "excel"]),
    default="csv",
    help="Output file format"
)
@click.pass_context
def job_similarity_export(ctx, skill_taxonomy_file, job_architecture_file, 
                         department, add_opportunity_flags, output_format):
    """
    Export job similarity data for Power BI integration.
    
    This command generates a structured export of job similarity data
    optimised for Power BI consumption, including metadata and opportunity flags.
    """
    config = ctx.obj["config"]
    
    click.echo("Loading skill taxonomy...")
    taxonomy = SkillTaxonomy.from_file(skill_taxonomy_file)
    
    click.echo("Loading job architecture...")
    job_arch = JobArchitecture.from_file(job_architecture_file)
    
    # Filter by department if specified
    if department:
        click.echo(f"Filtering jobs by department: {department}")
        job_arch = job_arch.filter_by_department(department)
    
    # Initialize report generator
    report_config = ReportConfig(
        include_job_metadata=True,
        add_opportunity_flags=add_opportunity_flags
    )
    report_generator = ReportGenerator(taxonomy, report_config)
    
    # Generate the job similarity export
    click.echo("Generating job similarity export...")
    df = report_generator.export_job_similarity_matrix(job_arch)
    
    # Generate output filename
    dept_suffix = f"_{department}" if department else ""
    output_file = os.path.join(
        config.output_dir, 
        f"job_similarity_export{dept_suffix}.{output_format}"
    )
    
    # Save results
    click.echo(f"Saving results to {output_file}...")
    if output_format == "csv":
        df.to_csv(output_file, index=False)
    elif output_format == "json":
        df.to_json(output_file, orient="records")
    else:  # excel
        df.to_excel(output_file, index=False)
    
    click.echo("Job similarity export completed!")


@cli.command()
@click.argument("skill_taxonomy_file", type=click.Path(exists=True))
@click.argument("job_architecture_file", type=click.Path(exists=True))
@click.argument("employee_database_file", type=click.Path(exists=True))
@click.option(
    "--department",
    help="Filter by department"
)
@click.option(
    "--add-opportunity-flags/--no-opportunity-flags",
    default=True,
    help="Whether to add opportunity flags to the output"
)
@click.option(
    "--output-format",
    type=click.Choice(["csv", "json", "excel"]),
    default="csv",
    help="Output file format"
)
@click.pass_context
def employee_similarity_export(ctx, skill_taxonomy_file, job_architecture_file,
                              employee_database_file, department, 
                              add_opportunity_flags, output_format):
    """
    Export employee similarity data for Power BI integration.
    
    This command generates a structured export of employee similarity data
    optimised for Power BI consumption, including metadata and opportunity flags.
    """
    config = ctx.obj["config"]
    
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
    
    # Initialize report generator
    report_config = ReportConfig(
        include_employee_metadata=True,
        include_job_metadata=True,
        add_opportunity_flags=add_opportunity_flags
    )
    report_generator = ReportGenerator(taxonomy, report_config)
    
    # Generate the employee similarity export
    click.echo("Generating employee similarity export...")
    df = report_generator.export_employee_similarity_matrix(employee_db)
    
    # Generate output filename
    dept_suffix = f"_{department}" if department else ""
    output_file = os.path.join(
        config.output_dir, 
        f"employee_similarity_export{dept_suffix}.{output_format}"
    )
    
    # Save results
    click.echo(f"Saving results to {output_file}...")
    if output_format == "csv":
        df.to_csv(output_file, index=False)
    elif output_format == "json":
        df.to_json(output_file, orient="records")
    else:  # excel
        df.to_excel(output_file, index=False)
    
    click.echo("Employee similarity export completed!")


@cli.command()
@click.argument("skill_taxonomy_file", type=click.Path(exists=True))
@click.argument("job_architecture_file", type=click.Path(exists=True))
@click.option(
    "--department",
    help="Filter jobs by department"
)
@click.option(
    "--add-opportunity-flags/--no-opportunity-flags",
    default=True,
    help="Whether to add opportunity flags to the output"
)
@click.option(
    "--output-format",
    type=click.Choice(["csv", "json", "excel"]),
    default="csv",
    help="Output file format"
)
@click.pass_context
def workforce_planning_export(ctx, skill_taxonomy_file, job_architecture_file, 
                             department, add_opportunity_flags, output_format):
    """
    Export workforce planning data for Power BI integration.
    
    This command generates a structured export of workforce planning data,
    including skill demand across jobs, optimised for Power BI consumption.
    """
    config = ctx.obj["config"]
    
    click.echo("Loading skill taxonomy...")
    taxonomy = SkillTaxonomy.from_file(skill_taxonomy_file)
    
    click.echo("Loading job architecture...")
    job_arch = JobArchitecture.from_file(job_architecture_file)
    
    # Filter by department if specified
    if department:
        click.echo(f"Filtering jobs by department: {department}")
        job_arch = job_arch.filter_by_department(department)
    
    # Initialize report generator
    report_config = ReportConfig(
        include_job_metadata=True,
        include_skill_metadata=True,
        add_opportunity_flags=add_opportunity_flags
    )
    report_generator = ReportGenerator(taxonomy, report_config)
    
    # Generate the workforce planning export
    click.echo("Generating workforce planning export...")
    df = report_generator.export_workforce_planning_data(job_arch)
    
    # Generate output filename
    dept_suffix = f"_{department}" if department else ""
    output_file = os.path.join(
        config.output_dir, 
        f"workforce_planning{dept_suffix}.{output_format}"
    )
    
    # Save results
    click.echo(f"Saving results to {output_file}...")
    if output_format == "csv":
        df.to_csv(output_file, index=False)
    elif output_format == "json":
        df.to_json(output_file, orient="records")
    else:  # excel
        df.to_excel(output_file, index=False)
    
    click.echo("Workforce planning export completed!")


if __name__ == "__main__":
    cli(obj={})
