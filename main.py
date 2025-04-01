#!/usr/bin/env python3
"""
Skill Similarity Engine - POC Run Entry Point

This script provides a simple entry point to run analyses on synthetic HRIS data,
generating job similarity matrices and visualizations for the POC run.
"""

import argparse
import os
import sys
import traceback
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Add the src directory to the Python path if not installed as a package
src_path = os.path.join(os.path.dirname(__file__), 'src')
if os.path.exists(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.hris_adapter.workflow import HRISWorkflow, create_workflow
from skill_similarity_engine.config.settings import get_config
from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture
from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator
from skill_similarity_engine.visualization.manager import VisualisationManager

def setup_logging(verbose: bool = False) -> logging.Logger:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger("skill_similarity_engine")
    logger.setLevel(level)
    
    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(ch)
    
    return logger

def load_data_with_hris_adapter(
    config_path: str,
    analysis_type: str,
    department: Optional[str],
    logger: logging.Logger
) -> Tuple[pd.DataFrame, JobArchitecture, SkillTaxonomy]:
    """Load data using the HRIS adapter workflow."""
    logger.info("\n" + "="*80)
    logger.info("STARTING HRIS ADAPTER WORKFLOW")
    logger.info("="*80 + "\n")
    
    try:
        # Initialize HRIS workflow
        logger.info("\n" + "-"*40)
        logger.info("STEP 1: INITIALIZING HRIS WORKFLOW")
        logger.info("-"*40)
        logger.info(f"Using configuration from: {config_path}")
        workflow = create_workflow(config_path=config_path, log_level="INFO")
        
        # Run the pipeline to transform data and calculate similarity
        logger.info("\n" + "-"*40)
        logger.info("STEP 2: RUNNING HRIS PIPELINE")
        logger.info("-"*40)
        logger.info(f"Analysis type: {analysis_type}")
        if department:
            logger.info(f"Filtering by department: {department}")
        
        # Run the pipeline with department filter if specified
        kwargs = {"department": department} if department else {}
        similarity_matrix, job_ids = workflow.run_pipeline(
            analysis_type=analysis_type,
            **kwargs
        )
        
        # Create a dataframe for the similarity matrix
        logger.info("\n" + "-"*40)
        logger.info("STEP 3: CREATING SIMILARITY MATRIX")
        logger.info("-"*40)
        df = pd.DataFrame(similarity_matrix, index=job_ids, columns=job_ids)
        logger.info(f"Generated similarity matrix with shape: {df.shape}")
        
        # Get the model objects from the workflow
        logger.info("\n" + "-"*40)
        logger.info("STEP 4: RETRIEVING MODEL OBJECTS")
        logger.info("-"*40)
        job_architecture = workflow.job_architecture
        taxonomy = workflow.taxonomy
        logger.info(f"Retrieved job architecture with {len(job_architecture.jobs)} jobs")
        logger.info(f"Retrieved skill taxonomy with {len(taxonomy.skills)} skills")
        
        logger.info("\n" + "="*80)
        logger.info("HRIS ADAPTER WORKFLOW COMPLETED")
        logger.info("="*80 + "\n")
        
        return df, job_architecture, taxonomy
        
    except Exception as e:
        logger.error(f"Error in HRIS adapter workflow: {e}")
        if logger.getEffectiveLevel() == logging.DEBUG:
            logger.error(traceback.format_exc())
        raise

def load_data_directly(
    skills_file: str,
    jobs_file: str,
    job_skills_file: Optional[str],
    department: Optional[str],
    logger: logging.Logger
) -> Tuple[pd.DataFrame, JobArchitecture, SkillTaxonomy]:
    """Load data directly from files without using the HRIS adapter."""
    logger.info("\n" + "="*80)
    logger.info("STARTING DATA LOADING PROCESS")
    logger.info("="*80 + "\n")
    
    # Convert relative paths to absolute paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    skills_file = os.path.join(base_dir, skills_file)
    jobs_file = os.path.join(base_dir, jobs_file)
    if job_skills_file:
        job_skills_file = os.path.join(base_dir, job_skills_file)
    
    # First, verify the file structure
    logger.info("\n" + "-"*40)
    logger.info("STEP 1: LOADING SKILLS DATA")
    logger.info("-"*40)
    logger.info(f"Loading skills from: {skills_file}")
    skills_df = pd.read_csv(skills_file)
    
    # Debug: Print columns in the skills DataFrame
    logger.info("\nColumns found in skills file:")
    for col in skills_df.columns.tolist():
        logger.info(f"  - {col}")
    
    # Map HRIS column names to internal column names
    logger.info("\nMapping column names...")
    column_mapping = {
        'Skill_ID': 'skill_id',
        'Skill_Name': 'name',
        'SkillType': 'skill_type',
        'Category': 'category',
        'Subcategory': 'subcategory'
    }
    
    # Rename columns to match internal schema
    skills_df = skills_df.rename(columns=column_mapping)
    
    # Debug: Print columns after mapping
    logger.info("\nColumns after mapping:")
    for col in skills_df.columns.tolist():
        logger.info(f"  - {col}")
    
    # Verify required columns exist
    required_columns = ['skill_id', 'name', 'skill_type']
    missing_columns = [col for col in required_columns if col not in skills_df.columns]
    if missing_columns:
        raise ValueError(f"Skills file missing required columns: {missing_columns}")
    
    # Create taxonomy using the loader
    logger.info("\n" + "-"*40)
    logger.info("STEP 2: CREATING SKILL TAXONOMY")
    logger.info("-"*40)
    from skill_similarity_engine.data.loaders import SkillTaxonomyLoader
    taxonomy_loader = SkillTaxonomyLoader(base_dir=base_dir)
    taxonomy = taxonomy_loader.load_from_csv(skills_file)
    logger.info(f"Successfully loaded {len(taxonomy.skills)} skills into taxonomy")
    
    # Load job architecture
    logger.info("\n" + "-"*40)
    logger.info("STEP 3: LOADING JOBS DATA")
    logger.info("-"*40)
    logger.info(f"Loading jobs from: {jobs_file}")
    jobs_df = pd.read_csv(jobs_file)
    
    # Debug: Print columns in the jobs DataFrame
    logger.info("\nColumns found in jobs file:")
    for col in jobs_df.columns.tolist():
        logger.info(f"  - {col}")
    
    # Map HRIS job column names to internal column names
    logger.info("\nMapping job column names...")
    job_column_mapping = {
        'JobID': 'job_id',
        'RoleSet': 'title',
        'Org Unit Name': 'department',
        'Salary Group': 'level',
        'People Leader Flag': 'role_track'
    }
    
    # Rename columns to match internal schema
    jobs_df = jobs_df.rename(columns=job_column_mapping)
    
    # Debug: Print columns after mapping
    logger.info("\nColumns after mapping:")
    for col in jobs_df.columns.tolist():
        logger.info(f"  - {col}")
    
    # Verify required job columns exist
    required_job_columns = ['job_id', 'title', 'department', 'level']
    missing_job_columns = [col for col in required_job_columns if col not in jobs_df.columns]
    if missing_job_columns:
        raise ValueError(f"Jobs file missing required columns: {missing_job_columns}")
    
    # Create job architecture using the loader
    logger.info("\n" + "-"*40)
    logger.info("STEP 4: CREATING JOB ARCHITECTURE")
    logger.info("-"*40)
    from skill_similarity_engine.data.loaders import JobArchitectureLoader
    job_loader = JobArchitectureLoader(taxonomy, base_dir=base_dir)
    job_architecture = job_loader.load_from_csv(jobs_file, job_skills_file)
    logger.info(f"Successfully loaded {len(job_architecture.jobs)} jobs into architecture")
    
    # Set up similarity calculator
    logger.info("\n" + "-"*40)
    logger.info("STEP 5: SETTING UP SIMILARITY CALCULATOR")
    logger.info("-"*40)
    vectorizer = TfidfVectorizer(taxonomy)
    calculator = CosineSimilarityCalculator(
        vectorizer=vectorizer,
        skill_taxonomy=taxonomy,
        job_architecture=job_architecture
    )
    
    # Calculate similarity
    logger.info("\n" + "-"*40)
    logger.info("STEP 6: CALCULATING SIMILARITY MATRIX")
    logger.info("-"*40)
    if department:
        logger.info(f"Filtering by department: {department}")
        # Get jobs for the specified department
        dept_jobs = {job_id: job for job_id, job in job_architecture.jobs.items() 
                    if job.department == department}
        # Create a temporary JobArchitecture with just these jobs
        filtered_architecture = JobArchitecture(dept_jobs)
        # Calculate similarity for these jobs
        similarity_matrix, job_ids = calculator.calculate_similarity_matrix(
            "job", job_architecture=filtered_architecture
        )
    else:
        # Calculate similarity for all jobs
        similarity_matrix, job_ids = calculator.calculate_similarity_matrix("job")
    
    # Create a dataframe for the similarity matrix
    df = pd.DataFrame(similarity_matrix, index=job_ids, columns=job_ids)
    logger.info(f"Generated similarity matrix with shape: {df.shape}")
    
    logger.info("\n" + "="*80)
    logger.info("DATA LOADING PROCESS COMPLETED")
    logger.info("="*80 + "\n")
    
    return df, job_architecture, taxonomy

def save_results(
    df: pd.DataFrame,
    output_dir: str,
    output_format: str,
    department: Optional[str],
    logger: logging.Logger
) -> str:
    """Save the similarity matrix results."""
    logger.info("Saving results...")
    
    # Create output filename
    output_filename = "all_departments"
    if department:
        output_filename = f"dept_{department}"
    
    output_file = os.path.join(output_dir, f"job_similarity_{output_filename}.{output_format}")
    
    # Save to the requested format
    logger.debug(f"Saving to {output_format} format...")
    if output_format == "csv":
        df.to_csv(output_file)
    elif output_format == "json":
        df.to_json(output_file, orient="split")
    else:  # excel
        df.to_excel(output_file, index=True)
    
    logger.info(f"Results saved to: {output_file}")
    return output_file

def generate_visualizations(
    df: pd.DataFrame,
    job_architecture: JobArchitecture,
    taxonomy: SkillTaxonomy,
    output_dir: str,
    department: Optional[str],
    logger: logging.Logger
) -> None:
    """Generate visualizations for the results."""
    logger.info("Generating visualizations...")
    
    # Create visualization manager
    vis_manager = VisualisationManager(
        skill_taxonomy=taxonomy,
        job_architecture=job_architecture,
        similarity_calculator=None,  # We don't need this for visualization
        output_dir=output_dir
    )
    
    # Determine departments to visualize
    if department:
        departments = [department]
    else:
        departments = set(job.department for job in job_architecture.jobs.values())
    
    # Generate a heatmap for each department
    for dept in departments:
        logger.debug(f"Generating heatmap for department: {dept}")
        heatmap_path = os.path.join(output_dir, f"heatmap_{dept}.png")
        vis_manager.generate_job_similarity_heatmap(
            departments=[dept],
            output_path=heatmap_path
        )
        
        # Export department-specific similarity matrix
        matrix_path = os.path.join(output_dir, f"similarity_matrix_{dept}.csv")
        vis_manager.export_job_similarity_matrix(
            department=dept,
            output_path=matrix_path
        )
    
    # Generate summary statistics
    logger.debug("Generating summary statistics...")
    # Basic statistics for the similarity matrix
    flat_sim = df.values.flatten()
    flat_sim = flat_sim[flat_sim != 1.0]  # Remove self-similarities
    stats = {
        "mean_similarity": float(flat_sim.mean()),
        "min_similarity": float(flat_sim.min()),
        "max_similarity": float(flat_sim.max()),
        "median_similarity": float(pd.Series(flat_sim).median()),
        "std_similarity": float(flat_sim.std()),
        "total_jobs": len(df),
        "total_comparisons": len(flat_sim)
    }
    
    # Save statistics
    pd.DataFrame([stats]).to_csv(
        os.path.join(output_dir, "summary_statistics.csv"), index=False
    )
    
    logger.info(f"Visualizations saved to: {output_dir}")

def main():
    """Main entry point for the HRIS POC analysis tool."""
    parser = argparse.ArgumentParser(
        description="Run skill similarity analysis POC on synthetic HRIS data"
    )
    
    # Analysis type
    parser.add_argument(
        "--analysis-type", "-a",
        choices=["job_similarity"],
        default="job_similarity",
        help="Type of analysis to run (currently only job_similarity is supported for POC)"
    )
    
    # Input files (either use the hris_workflow or specify direct file paths)
    data_source = parser.add_argument_group("Data Source Options")
    data_source.add_argument(
        "--use-hris-adapter", "-u",
        action="store_true",
        default=False,  # Changed to False to use direct file loading by default
        help="Use the HRIS adapter to transform data (default is to use files directly)"
    )
    data_source.add_argument(
        "--config", "-c",
        default="config/hris_schema_mapping.yaml",  # Default config path
        help="Path to HRIS configuration file (used if --use-hris-adapter is specified)"
    )
    data_source.add_argument(
        "--skills-file",
        help="Path to skills data CSV (used if not using HRIS adapter)"
    )
    data_source.add_argument(
        "--jobs-file",
        help="Path to jobs data CSV (used if not using HRIS adapter)"
    )
    data_source.add_argument(
        "--job-skills-file",
        help="Path to job-skills mapping CSV (used if not using HRIS adapter)"
    )
    
    # Analysis parameters
    parser.add_argument(
        "--department", "-d",
        help="Filter analysis by department"
    )
    
    # Output options
    parser.add_argument(
        "--output-dir", "-o",
        default="./data/poc/output",
        help="Directory for output files"
    )
    parser.add_argument(
        "--output-format", "-f",
        choices=["csv", "json", "excel"],
        default="csv",
        help="Output file format for data exports"
    )
    parser.add_argument(
        "--no-visualizations",
        action="store_true",
        help="Skip generating visualizations (heatmaps, etc.)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    # Debug options
    parser.add_argument(
        "--debug-step",
        choices=["load", "transform", "analyze", "visualize", "all"],
        default="all",
        help="Run only specific steps in debug mode"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging(args.verbose)
    logger.info("Starting Skill Similarity Engine POC run")
    
    # Make sure the output directory exists
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output_dir, f"poc_run_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    logger.debug(f"Created output directory: {output_dir}")
    
    try:
        # Initialize variables that might be needed across steps
        df = None
        job_architecture = None
        taxonomy = None
        
        # Step 1: Load and transform data
        if args.debug_step in ["load", "all"]:
            logger.info("Step 1: Loading and transforming data")
            if args.use_hris_adapter:
                df, job_architecture, taxonomy = load_data_with_hris_adapter(
                    args.config,
                    args.analysis_type,
                    args.department,
                    logger
                )
            else:
                if not args.skills_file or not args.jobs_file:
                    parser.error("When not using HRIS adapter, --skills-file and --jobs-file are required")
                df, job_architecture, taxonomy = load_data_directly(
                    args.skills_file,
                    args.jobs_file,
                    args.job_skills_file,
                    args.department,
                    logger
                )
        
        # Step 2: Save results
        if args.debug_step in ["transform", "all"]:
            if df is None or job_architecture is None or taxonomy is None:
                logger.error("Cannot save results: data not loaded. Please run with --debug-step load first.")
                sys.exit(1)
                
            logger.info("Step 2: Saving results")
            output_file = save_results(
                df,
                output_dir,
                args.output_format,
                args.department,
                logger
            )
        
        # Step 3: Generate visualizations
        if args.debug_step in ["visualize", "all"] and not args.no_visualizations:
            if df is None or job_architecture is None or taxonomy is None:
                logger.error("Cannot generate visualizations: data not loaded. Please run with --debug-step load first.")
                sys.exit(1)
                
            logger.info("Step 3: Generating visualizations")
            generate_visualizations(
                df,
                job_architecture,
                taxonomy,
                output_dir,
                args.department,
                logger
            )
        
        logger.info("POC run completed successfully!")
        logger.info(f"All results saved to: {output_dir}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 