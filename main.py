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
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import matplotlib.pyplot as plt

# Add the src directory to the Python path if not installed as a package
src_path = os.path.join(os.path.dirname(__file__), 'src')
if os.path.exists(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import key components
from skill_similarity_engine.models.skills import Skill, SkillTaxonomy, SkillCategory, SkillType
from skill_similarity_engine.models.jobs import JobArchitecture, Job, JobLevel
from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator
from skill_similarity_engine.visualization.manager import VisualisationManager
from skill_similarity_engine.visualization.reports import DataExporter, ReportConfig

# Allow direct file loading without HRIS adapter
from skill_similarity_engine.config.settings import get_config

# Import HRISWorkflow when needed (in the function that uses it)
# This prevents the error from occurring at the top level

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
    # Import here to avoid the import error at the top level
    from skill_similarity_engine.hris_adapter.workflow import create_workflow
    
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

def map_job_level(level_str: str) -> JobLevel:
    """
    Convert a string representation to a JobLevel enum value.
    
    Args:
        level_str: String representation of job level
        
    Returns:
        Corresponding JobLevel enum value
    """
    level_map = {
        "Group 1": JobLevel.ENTRY,
        "Group 2": JobLevel.ASSOCIATE,
        "Group 3": JobLevel.MID_LEVEL,
        "Group 4": JobLevel.SENIOR,
        "Group 5": JobLevel.MANAGER,
        "Group 6": JobLevel.DIRECTOR,
        "Group 7": JobLevel.EXECUTIVE,
        # Add uppercase variants
        "GROUP 1": JobLevel.ENTRY,
        "GROUP 2": JobLevel.ASSOCIATE,
        "GROUP 3": JobLevel.MID_LEVEL,
        "GROUP 4": JobLevel.SENIOR,
        "GROUP 5": JobLevel.MANAGER,
        "GROUP 6": JobLevel.DIRECTOR,
        "GROUP 7": JobLevel.EXECUTIVE,
    }
    
    # Try to get the level from the map
    if level_str in level_map:
        return level_map[level_str]
    
    # Default to ASSOCIATE if not found
    return JobLevel.ASSOCIATE

def load_data_directly(
    skills_file: str,
    jobs_file: str,
    job_skills_file: Optional[str],
    department: Optional[str],
    logger: logging.Logger,
    chunk_size: int = 100000,
    memory_efficient: bool = False
) -> Tuple[pd.DataFrame, JobArchitecture, SkillTaxonomy]:
    """Load data directly from CSV files with optimized memory usage."""
    logger.info("\n" + "="*80)
    logger.info("STARTING DATA LOADING PROCESS")
    logger.info("="*80 + "\n")
    
    # Load skills with optimized dtypes
    logger.info("Loading skills data...")
    dtype_map = {
        'Skill_ID': 'str',
        'Skill_Name': 'str',
        'SkillType': 'category',
        'Category': 'category',
        'Subcategory': 'category'
    }
    skills_df = pd.read_csv(skills_file, dtype=dtype_map)
    logger.info(f"Loaded {len(skills_df)} skills")
    logger.info(f"Memory usage: {skills_df.memory_usage().sum() / 1024 / 1024:.2f} MB")
    
    # Map HRIS column names to internal column names
    logger.info("Mapping column names...")
    column_mapping = {
        'Skill_ID': 'skill_id',
        'Skill_Name': 'name',
        'SkillType': 'skill_type',
        'Category': 'category',
        'Subcategory': 'subcategory'
    }
    
    # Rename columns to match internal schema
    skills_df = skills_df.rename(columns=column_mapping)
    
    # Preprocess skill names - replace spaces with underscores
    logger.info("Preprocessing skill names (replacing spaces with underscores)...")
    original_names = skills_df['name'].copy()
    skills_df['name'] = skills_df['name'].str.replace(' ', '_')
    
    # Create mapping of transformed skill names to original names for reference
    skill_name_mapping = dict(zip(skills_df['name'], original_names))
    logger.info(f"Processed {len(skill_name_mapping)} skill names")

    # Load jobs with optimized dtypes
    logger.info("\nLoading jobs data...")
    jobs_dtype_map = {
        'JobID': 'str', 
        'RoleSet': 'str',
        'Org Unit Name': 'category',
        'Salary Group': 'category',
        'People Leader Flag': 'category',
        'Org Unit Number': 'str'
    }
    jobs_df = pd.read_csv(jobs_file, dtype=jobs_dtype_map)
    logger.info(f"Loaded {len(jobs_df)} jobs")
    logger.info(f"Memory usage: {jobs_df.memory_usage().sum() / 1024 / 1024:.2f} MB")
    
    # Map HRIS job column names to internal column names
    logger.info("\nMapping job column names...")
    job_column_mapping = {
        'JobID': 'job_id',
        'RoleSet': 'title',
        'Org Unit Name': 'department',
        'Salary Group': 'level',
        'People Leader Flag': 'role_track',
        'Org Unit Number': 'org_unit_number'  # Add this to capture unit number for uniqueness
    }
    
    # Rename columns to match internal schema
    jobs_df = jobs_df.rename(columns=job_column_mapping)
    
    # Create unique job IDs by combining job_id with org_unit_number
    if 'job_id' in jobs_df.columns and 'org_unit_number' in jobs_df.columns:
        jobs_df['unique_job_id'] = jobs_df['job_id'] + '_' + jobs_df['org_unit_number'].astype(str)
        logger.info("\nCreated unique job IDs by combining JobID with Org Unit Number")
    else:
        # If the required columns don't exist, we can't create unique IDs
        logger.error("Can't create unique job IDs: 'job_id' or 'org_unit_number' column missing")
        raise ValueError("Jobs file must have both 'JobID' and 'Org Unit Number' columns to create unique job IDs")

    # If job skills file is provided, load with chunking for large files
    if job_skills_file:
        logger.info("\nLoading job skills data...")
        job_skills_list = []
        
        job_skills_dtype_map = {
            'JobID': 'str',
            'Skill_ID': 'str',
            'Proficiency': 'int'
        }
        
        for chunk in tqdm(pd.read_csv(job_skills_file, dtype=job_skills_dtype_map, chunksize=chunk_size), desc="Loading job skills"):
            if department:
                # Filter by department if specified
                dept_jobs = jobs_df[jobs_df['department'] == department]['job_id'].unique()
                chunk = chunk[chunk['JobID'].isin(dept_jobs)]
            job_skills_list.append(chunk)
            
        job_skills_df = pd.concat(job_skills_list, ignore_index=True)
        
        # Map job skills column names if needed
        skill_mapping = {
            'JobID': 'job_id',
            'Skill_ID': 'skill_id',
            'Proficiency': 'proficiency'
        }
        
        # Rename columns
        job_skills_df = job_skills_df.rename(columns=skill_mapping)
        
        logger.info(f"Loaded {len(job_skills_df)} job-skill mappings")
        logger.info(f"Memory usage: {job_skills_df.memory_usage().sum() / 1024 / 1024:.2f} MB")

    # Create taxonomy using the loader
    logger.info("\n" + "-"*40)
    logger.info("STEP 2: CREATING SKILL TAXONOMY")
    logger.info("-"*40)
    from skill_similarity_engine.data.loaders import SkillTaxonomyLoader
    taxonomy_loader = SkillTaxonomyLoader(base_dir=os.path.dirname(os.path.abspath(__file__)))
    
    # Create an empty taxonomy and populate it directly with the DataFrame we've already loaded
    taxonomy = SkillTaxonomy()
    
    # Save mapping of original to transformed names in the taxonomy
    taxonomy.skill_name_mapping = skill_name_mapping
    
    # Create category mapping if categories are in the DataFrame
    category_mapping = {}
    if "category" in skills_df.columns:
        for _, row in skills_df.iterrows():
            if pd.notna(row.get("category", None)):
                # Create a category ID based on category name
                category_name = row["category"]
                parent_id = None
                
                if category_name not in category_mapping:
                    category_id = "C" + str(len(category_mapping) + 1).zfill(3)
                    category_mapping[category_name] = category_id
                    
                    # Add category to taxonomy
                    if not taxonomy.get_category(category_id):
                        taxonomy.add_category(SkillCategory(
                            category_id=category_id,
                            name=category_name,
                            parent_id=parent_id,
                            description=f"{category_name} skills"
                        ))
                
                # Handle subcategory if available
                if pd.notna(row.get("subcategory", None)):
                    subcategory_name = row["subcategory"]
                    parent_id = category_mapping[category_name]
                    
                    if subcategory_name not in category_mapping:
                        subcategory_id = "C" + str(len(category_mapping) + 1).zfill(3)
                        category_mapping[subcategory_name] = subcategory_id
                        
                        # Add subcategory to taxonomy with parent relationship
                        if not taxonomy.get_category(subcategory_id):
                            taxonomy.add_category(SkillCategory(
                                category_id=subcategory_id,
                                name=subcategory_name,
                                parent_id=parent_id,
                                description=f"{subcategory_name} skills"
                            ))
    
    # Process skills
    processed_skill_ids = set()  # Track skill IDs we've already processed
    duplicate_count = 0
    
    for _, row in skills_df.iterrows():
        # Check for duplicate skill ID
        skill_id = str(row["skill_id"])
        if skill_id in processed_skill_ids:
            duplicate_count += 1
            logger.warning(f"Skipping duplicate skill ID: {skill_id}")
            continue
            
        # Parse skill type
        skill_type = SkillType.COMMON  # Default to COMMON
        
        if "skill_type" in row and pd.notna(row["skill_type"]):
            try:
                skill_type = SkillType.from_string(row["skill_type"])
            except ValueError:
                pass
        
        # Get category ID
        category_id = None
        if "category" in row and "subcategory" in row:
            category_id = category_mapping.get(row.get("subcategory")) or category_mapping.get(row.get("category"))
        
        # Build skill object
        skill = Skill(
            skill_id=skill_id,
            name=row["name"],
            description=row.get("description", ""),
            category_id=category_id,
            skill_type=skill_type,
            aliases=[],
            related_skills=[],
            prerequisites=[]
        )
        
        # Add skill to taxonomy
        taxonomy.add_skill(skill)
        processed_skill_ids.add(skill_id)
    
    if duplicate_count > 0:
        logger.warning(f"Found and skipped {duplicate_count} duplicate skill IDs")
        
    logger.info(f"Successfully loaded {len(taxonomy.skills)} skills into taxonomy")
    
    # Create job architecture directly from the DataFrame
    logger.info("\n" + "-"*40)
    logger.info("STEP 3: CREATING JOB ARCHITECTURE")
    logger.info("-"*40)
    
    # Create empty job architecture
    job_architecture = JobArchitecture()
    
    # Create jobs from DataFrame
    for _, row in jobs_df.iterrows():
        # Parse job level
        job_level = JobLevel.ASSOCIATE  # Default level
        if 'level' in row and pd.notna(row['level']):
            try:
                # Use our custom mapper instead of from_string
                job_level = map_job_level(str(row['level']))
            except Exception as e:
                logger.warning(f"Error parsing job level: {row['level']} - {str(e)}")
                logger.warning(f"Using ASSOCIATE as default level")
        
        # Create job object with unique ID
        job = Job(
            job_id=row['unique_job_id'],
            title=row['title'],
            department=row['department'],
            level=job_level,
            skills={}  # Empty skills dict, will be filled from job_skills_file
        )
        
        # Add job to architecture
        job_architecture.add_job(job)
    
    # Load job skills if provided
    if job_skills_file:
        logger.info("\n" + "-"*40)
        logger.info("STEP 5: LOADING JOB SKILLS")
        logger.info("-"*40)
        logger.info(f"Loading job skills from: {job_skills_file}")
        
        # Map job skills to jobs
        skills_mapped = 0
        skills_skipped = 0
        
        # Create a mapping between original job_id + org_unit combinations and unique_job_id
        # This allows us to map skills even if the job skills file only has JobID
        job_id_mapping = {}
        for _, row in jobs_df.iterrows():
            job_id = row['job_id']
            unique_id = row['unique_job_id']
            
            # Support mapping from simple job_id to all matching unique_job_ids
            if job_id not in job_id_mapping:
                job_id_mapping[job_id] = []
            job_id_mapping[job_id].append(unique_id)
        
        # For each job skill entry
        for _, row in job_skills_df.iterrows():
            job_id = str(row['job_id'])
            skill_id = str(row['skill_id'])
            
            # Skip if skill doesn't exist in taxonomy
            if skill_id not in taxonomy.skills:
                logger.warning(f"Skill ID {skill_id} not found in taxonomy, skipping")
                skills_skipped += 1
                continue
            
            # Get proficiency (default to 3 if not specified)
            proficiency = 3
            if 'proficiency' in row and pd.notna(row['proficiency']):
                try:
                    proficiency = int(row['proficiency'])
                    # Validate proficiency range (1-5)
                    if not 1 <= proficiency <= 5:
                        logger.warning(f"Invalid proficiency value: {proficiency}, using 3 as default")
                        proficiency = 3
                except ValueError:
                    logger.warning(f"Non-integer proficiency value: {row['proficiency']}, using 3 as default")
            
            # Add skill to all matching jobs (this handles the case where multiple jobs share a JobID)
            if job_id in job_id_mapping:
                for unique_job_id in job_id_mapping[job_id]:
                    if unique_job_id in job_architecture.jobs:
                        job_architecture.jobs[unique_job_id].add_skill(skill_id, proficiency)
                        skills_mapped += 1
            else:
                logger.warning(f"Job ID {job_id} not found in job architecture, skipping skill {skill_id}")
                skills_skipped += 1
        
        logger.info(f"Mapped {skills_mapped} skills to jobs (skipped {skills_skipped})")
    
    logger.info(f"Successfully loaded {len(job_architecture.jobs)} jobs into architecture")
    
    # Set up similarity calculator
    logger.info("\n" + "-"*40)
    logger.info("STEP 5: SETTING UP SIMILARITY CALCULATOR")
    logger.info("-"*40)
    
    # Initialize vectorizer and then calculator
    logger.info("Initializing TF-IDF vectorizer...")
    vectorizer = TfidfVectorizer(taxonomy)
    
    # Get the actual calculator class from the module
    from skill_similarity_engine.similarity.cosine import CosineSimilarityCalculator as ModuleCalculator
    
    # Create calculator instance
    calculator = ModuleCalculator(
        vectorizer=vectorizer,
        skill_taxonomy=taxonomy,
        job_architecture=job_architecture
    )
    
    # Calculate similarity
    logger.info("\n" + "-"*40)
    logger.info("STEP 6: CALCULATING SIMILARITY MATRIX")
    logger.info("-"*40)
    
    # Add debug info about number of jobs
    total_jobs = len(job_architecture.jobs)
    logger.info(f"Starting similarity calculations for {total_jobs} jobs")
    logger.info(f"This will result in {total_jobs * total_jobs} comparisons")
    
    if department:
        logger.info(f"Filtering by department: {department}")
        # Get jobs for the specified department
        dept_jobs = {job_id: job for job_id, job in job_architecture.jobs.items() 
                    if job.department == department}
        filtered_jobs = len(dept_jobs)
        logger.info(f"Filtered to {filtered_jobs} jobs in department {department}")
        logger.info(f"This will result in {filtered_jobs * filtered_jobs} comparisons")
        
        # Create a temporary JobArchitecture with just these jobs
        filtered_architecture = JobArchitecture(dept_jobs)
        
        # Calculate similarity for these jobs
        logger.info("Starting TF-IDF vectorization...")
        similarity_matrix, job_ids = calculator.calculate_similarity_matrix(
            "job", job_architecture=filtered_architecture
        )
        logger.info(f"Completed similarity calculations for {filtered_jobs} jobs")
    else:
        # Calculate similarity for all jobs
        logger.info("Starting TF-IDF vectorization...")
        similarity_matrix, job_ids = calculator.calculate_similarity_matrix("job")
        logger.info(f"Completed similarity calculations for {total_jobs} jobs")
    
    # Create a dataframe for the similarity matrix
    df = pd.DataFrame(similarity_matrix, index=job_ids, columns=job_ids)
    logger.info(f"Generated similarity matrix with shape: {df.shape}")
    logger.info(f"Memory usage of similarity matrix: {df.memory_usage().sum() / 1024 / 1024:.2f} MB")
    
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
    logger: logging.Logger,
    batch_size: int = 5,
    memory_efficient: bool = False
) -> None:
    """Generate only tabular data for Power BI, skipping visualizations."""
    logger.info("Generating tabular data for Power BI...")
    
    # Import the calculator class for data export
    from skill_similarity_engine.similarity.cosine import CosineSimilarityCalculator, TfidfVectorizer
    
    # Create vectorizer and calculator
    vectorizer = TfidfVectorizer(taxonomy)
    similarity_calculator = CosineSimilarityCalculator(
        vectorizer=vectorizer,
        skill_taxonomy=taxonomy,
        job_architecture=job_architecture
    )
    
    # Create data exporter directly
    exporter = DataExporter(
        skill_taxonomy=taxonomy,
        job_architecture=job_architecture,
        similarity_calculator=similarity_calculator,
        output_dir=output_dir
    )
    
    # Process departments in batches to manage memory
    departments = [department] if department else list(set(job.department for job in job_architecture.jobs.values()))
    
    logger.info(f"Exporting data for {len(departments)} departments")
    
    # Clean department names for file output
    clean_department_names = {}
    for dept in departments:
        # Replace problematic characters in department names
        clean_name = dept.replace('\\', '_').replace('/', '_').replace(':', '_')
        clean_department_names[dept] = clean_name
    
    for i in range(0, len(departments), batch_size):
        batch_departments = departments[i:i + batch_size]
        logger.info(f"Processing departments {i+1}-{min(i+batch_size, len(departments))} of {len(departments)}")
        
        for dept in tqdm(batch_departments, desc="Generating department data"):
            try:
                # Export department-specific data only - skip visualizations
                dept_matrix = exporter.export_job_similarity_matrix(
                    department=dept,
                    config=ReportConfig(include_metadata=True, add_opportunity_flags=True)
                )
                
                # Use clean name for file
                clean_dept = clean_department_names[dept]
                dept_matrix.to_csv(os.path.join(output_dir, f"job_similarity_{clean_dept}.csv"), index=False)
                
                # Export job skills for this department
                dept_jobs = [job for job_id, job in job_architecture.jobs.items() 
                            if job.department == dept]
                
                for job in dept_jobs:
                    try:
                        skills_df = exporter.export_job_skills(
                            job_id=job.job_id,
                            config=ReportConfig(include_metadata=True)
                        )
                        # Save to department-specific folder
                        dept_dir = os.path.join(output_dir, "job_skills", clean_dept)
                        os.makedirs(dept_dir, exist_ok=True)
                        skills_df.to_csv(os.path.join(dept_dir, f"skills_{job.job_id}.csv"), index=False)
                    except Exception as e:
                        logger.warning(f"Error exporting skills for job {job.job_id}: {e}")
                
                # Clear memory
                del dept_matrix
                
            except Exception as e:
                logger.warning(f"Error processing department '{dept}': {e}")
                continue
            
    # Export all-departments similarity matrix in tabular format
    logger.info("Exporting all-departments similarity matrix...")
    config = ReportConfig(
        include_metadata=True,  # Include job titles, departments, etc.
        add_opportunity_flags=True  # Include mobility opportunity flags
    )
    
    try:
        all_dept_matrix = exporter.export_job_similarity_matrix_all_departments(
            config=config
        )
        # Save the tabular data
        all_dept_matrix.to_csv(os.path.join(output_dir, "job_similarity_all_departments.csv"), index=False)
        
        # Generate summary statistics
        logger.debug("Generating summary statistics...")
        # Calculate statistics from the all-departments tabular data
        stats = {
            "mean_similarity": float(all_dept_matrix["similarity"].mean()),
            "min_similarity": float(all_dept_matrix["similarity"].min()),
            "max_similarity": float(all_dept_matrix["similarity"].max()),
            "median_similarity": float(all_dept_matrix["similarity"].median()),
            "std_similarity": float(all_dept_matrix["similarity"].std()),
            "total_jobs": len(job_architecture.jobs),
            "total_comparisons": len(all_dept_matrix),
            "departments_analyzed": len(departments),
            "cross_department_opportunities": int(all_dept_matrix["is_cross_departmental_opportunity"].sum()),
            "high_similarity_opportunities": int(all_dept_matrix["is_high_similarity_opportunity"].sum()),
            "internal_mobility_opportunities": int(all_dept_matrix["is_internal_mobility_opportunity"].sum())
        }
        
        # Add department-specific statistics
        dept_stats = {}
        for dept in departments:
            dept_data = all_dept_matrix[
                (all_dept_matrix["job1_department"] == dept) & 
                (all_dept_matrix["job2_department"] == dept)
            ]
            dept_stats[dept] = {
                "job_count": len(set(dept_data["job1_id"])),
                "mean_similarity": float(dept_data["similarity"].mean()),
                "high_similarity_opportunities": int(dept_data["is_high_similarity_opportunity"].sum()),
                "internal_mobility_opportunities": int(dept_data["is_internal_mobility_opportunity"].sum())
            }
        
        # Save statistics
        pd.DataFrame([stats]).to_csv(
            os.path.join(output_dir, "summary_statistics.csv"), 
            index=False
        )
        
        # Save department-specific statistics with clean names
        clean_dept_stats = {}
        for dept, stat in dept_stats.items():
            clean_dept = clean_department_names[dept]
            clean_dept_stats[clean_dept] = stat
            
        pd.DataFrame.from_dict(clean_dept_stats, orient="index").to_csv(
            os.path.join(output_dir, "department_statistics.csv")
        )
        
        logger.info(f"All tabular data exported to: {output_dir}")
        logger.info(f"Processed {len(departments)} departments")
        logger.info(f"Found {stats['high_similarity_opportunities']} high similarity opportunities")
        logger.info(f"Found {stats['internal_mobility_opportunities']} internal mobility opportunities")
        logger.info(f"Found {stats['cross_department_opportunities']} cross-department opportunities")
        
    except Exception as e:
        logger.error(f"Error exporting all-departments matrix: {e}")
        if logger.getEffectiveLevel() == logging.DEBUG:
            logger.error(traceback.format_exc())

def calculate_similarity_batch(args):
    """Helper function for parallel similarity calculation"""
    start_idx, end_idx, job_ids, vectors = args
    batch_size = end_idx - start_idx
    similarities = np.zeros((batch_size, len(job_ids)))
    
    for i in range(batch_size):
        idx = start_idx + i
        for j in range(len(job_ids)):
            if idx != j:
                similarities[i, j] = np.dot(vectors[idx], vectors[j])
    
    return similarities

# Renamed to avoid conflicts with imported class
class LocalCosineSimilarityCalculator:
    """Local implementation for optimized similarity matrix calculation"""
    def calculate_similarity_matrix(self, analysis_type, job_architecture=None):
        """Calculate similarity matrix with parallel processing"""
        if analysis_type != "job":
            raise ValueError(f"Unsupported analysis type: {analysis_type}")
            
        job_arch = job_architecture or self.job_architecture
        job_ids = list(job_arch.jobs.keys())
        n_jobs = len(job_ids)
        
        # Pre-compute TF-IDF vectors for all jobs
        vectors = []
        for job_id in tqdm(job_ids, desc="Vectorizing jobs"):
            vectors.append(self.vectorizer.vectorize_job(job_arch.jobs[job_id]))
        vectors = np.array(vectors)
        
        # Prepare batches for parallel processing
        n_cores = cpu_count()
        batch_size = max(1, n_jobs // (n_cores * 4))  # Smaller batches for better load balancing
        batches = []
        
        for start_idx in range(0, n_jobs, batch_size):
            end_idx = min(start_idx + batch_size, n_jobs)
            batches.append((start_idx, end_idx, job_ids, vectors))
        
        # Calculate similarities in parallel
        with Pool(processes=n_cores) as pool:
            results = list(tqdm(
                pool.imap(calculate_similarity_batch, batches),
                total=len(batches),
                desc="Calculating similarities"
            ))
        
        # Combine results
        similarity_matrix = np.vstack(results)
        
        # Ensure the matrix is symmetric
        similarity_matrix = np.maximum(similarity_matrix, similarity_matrix.T)
        np.fill_diagonal(similarity_matrix, 1.0)
        
        return similarity_matrix, job_ids

def main():
    """Main entry point for the HRIS POC analysis tool."""
    parser = argparse.ArgumentParser(
        description="Run skill similarity analysis POC on synthetic HRIS data"
    )
    
    # Add performance optimization options
    performance = parser.add_argument_group("Performance Options")
    performance.add_argument(
        "--num-processes",
        type=int,
        default=cpu_count(),
        help="Number of processes to use for parallel processing (default: number of CPU cores)"
    )
    performance.add_argument(
        "--chunk-size",
        type=int,
        default=100000,
        help="Chunk size for reading large files (default: 100000)"
    )
    performance.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Batch size for processing departments (default: 5)"
    )
    performance.add_argument(
        "--memory-efficient",
        action="store_true",
        help="Use memory-efficient mode (trades speed for lower memory usage)"
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
        default=True,  # Changed to True to skip visualizations by default
        help="Skip generating visualizations (heatmaps, etc.) - DEFAULT=True"
    )
    parser.add_argument(
        "--tabular-only",
        action="store_true",
        default=True,  # New option, True by default
        help="Generate only tabular data for Power BI - DEFAULT=True"
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
                    logger,
                    chunk_size=args.chunk_size,
                    memory_efficient=args.memory_efficient
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
                logger,
                batch_size=args.batch_size,
                memory_efficient=args.memory_efficient
            )
        # Generate tabular output for Power BI
        elif args.debug_step in ["visualize", "all"] and args.tabular_only:
            if df is None or job_architecture is None or taxonomy is None:
                logger.error("Cannot generate tabular data: data not loaded. Please run with --debug-step load first.")
                sys.exit(1)
                
            logger.info("Step 3: Generating tabular data for Power BI")
            generate_visualizations(  # We're reusing this function but it's been modified to skip visualizations
                df,
                job_architecture,
                taxonomy,
                output_dir,
                args.department,
                logger,
                batch_size=args.batch_size,
                memory_efficient=args.memory_efficient
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