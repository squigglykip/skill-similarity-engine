#!/usr/bin/env python3
"""
Skill Similarity Engine v2 - Modular Entry Point (Menu-Driven)

This script provides a menu-based CLI for the Skill Similarity Engine pipeline.
It demonstrates chunked/streaming data loading, validation, logging, and error handling.
More functionality will be added step by step.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# NOTE: Some linter errors below are false positives due to dynamic imports and os.path usage in Python.
# All imports and os.path usage are correct and will work at runtime if the environment is set up properly.

# Add the src directory to the Python path if not installed as a package
src_path = os.path.join(os.path.dirname(__file__), 'src')
if os.path.exists(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.logging.config import setup_logging
from skill_similarity_engine.error_handling.core import EngineError
from skill_similarity_engine.error_handling.registry import ErrorRegistry
from skill_similarity_engine.data.loaders import SkillTaxonomyLoader, JobArchitectureLoader
from skill_similarity_engine.similarity.precompute import create_precomputer, PrecomputeConfig
from skill_similarity_engine.models.versioning import setup_model_output_directory

# Welcome banner
BANNER = r'''
    ███████╗██╗  ██╗██╗██╗     ██╗                                        
    ██╔════╝██║ ██╔╝██║██║     ██║                                        
    ███████╗█████╔╝ ██║██║     ██║                                        
    ╚════██║██╔═██╗ ██║██║     ██║                                        
    ███████║██║  ██╗██║███████╗███████╗                                   
    ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝                                   
                                                                        
    ███████╗██╗███╗   ███╗██╗██╗      █████╗ ██████╗ ██╗████████╗██╗   ██╗
    ██╔════╝██║████╗ ████║██║██║     ██╔══██╗██╔══██╗██║╚══██╔══╝╚██╗ ██╔╝
    ███████╗██║██╔████╔██║██║██║     ███████║██████╔╝██║   ██║    ╚████╔╝ 
    ╚════██║██║██║╚██╔╝██║██║██║     ██╔══██║██╔══██╗██║   ██║     ╚██╔╝  
    ███████║██║██║ ╚═╝ ██║██║███████╗██║  ██║██║  ██║██║   ██║      ██║   
    ╚══════╝╚═╝╚═╝     ╚═╝╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝   ╚═╝      ╚═╝   
                                                                        
    ███████╗███╗   ██╗ ██████╗ ██╗███╗   ██╗███████╗                      
    ██╔════╝████╗  ██║██╔════╝ ██║████╗  ██║██╔════╝                      
    █████╗  ██╔██╗ ██║██║  ███╗██║██╔██╗ ██║█████╗                        
    ██╔══╝  ██║╚██╗██║██║   ██║██║██║╚██╗██║██╔══╝                        
    ███████╗██║ ╚████║╚██████╔╝██║██║ ╚████║███████╗                      
    ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝                                 

Skill Similarity Engine v2 - Modular Pipeline
'''

# Store loaded data globally for reuse between menu operations
loaded_taxonomy = None
loaded_architecture = None

def prompt_bool(prompt, default=False):
    while True:
        val = input(f"{prompt} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
        if not val:
            return default
        if val in ('y', 'yes'):
            return True
        if val in ('n', 'no'):
            return False
        print("Please enter 'y' or 'n'.")

def prompt_int(prompt, default):
    while True:
        val = input(f"{prompt} [default: {default}]: ").strip()
        if not val:
            return default
        try:
            return int(val)
        except ValueError:
            print("Please enter a valid integer.")

def main_menu():
    print(BANNER)
    print("Please select an option:")
    print("1. Precompute Skill Similarities")
    print("2. Query Skill Similarities (coming soon)")
    print("0. Exit")
    return input("Enter your choice: ").strip()

def precompute_menu():
    print("\nPrecompute Skill Similarities\n")
    print("Select a task:")
    print("1. Load and validate data")
    print("2. Generate job-to-job similarity matrix")
    print("3. Export results (coming soon)")
    print("0. Back to main menu")
    return input("Enter your choice: ").strip()

def load_and_validate_data(logger):
    global loaded_taxonomy, loaded_architecture
    
    print("\n=== Data Loading & Validation ===")
    skills_file = input("Enter path to skills CSV file: ").strip()
    jobs_file = input("Enter path to jobs CSV file: ").strip()
    job_skills_file = input("Enter path to job-skill mapping CSV file (or leave blank if not used): ").strip()
    chunked = prompt_bool("Enable chunked/streaming loading?", default=True)
    chunksize = prompt_int("Chunk size for streaming", default=10000)
    validate = prompt_bool("Enable schema validation?", default=True)
    verbose = prompt_bool("Enable verbose logging?", default=False)

    logger.setLevel('DEBUG' if verbose else 'INFO')
    error_registry = ErrorRegistry()

    # Step 1: Load Skill Taxonomy
    try:
        logger.info("Loading skill taxonomy...")
        taxonomy_loader = SkillTaxonomyLoader()
        taxonomy = taxonomy_loader.load_from_csv(
            skills_file=skills_file,
            chunked=chunked,
            chunksize=chunksize,
            validate=validate
        )
        loaded_taxonomy = taxonomy
        logger.info(f"Loaded {len(taxonomy.skills)} skills.")
    except Exception as e:
        logger.error(f"Failed to load skill taxonomy: {e}")
        error_registry.register(e)
        print("[ERROR] Failed to load skill taxonomy. See logs for details.")
        return False

    # Step 2: Load Job Architecture
    try:
        logger.info("Loading job architecture...")
        job_loader = JobArchitectureLoader(taxonomy)
        architecture = job_loader.load_from_csv(
            jobs_file=jobs_file,
            job_skills_file=job_skills_file if job_skills_file else None,
            chunked=chunked,
            chunksize=chunksize,
            validate=validate
        )
        loaded_architecture = architecture
        logger.info(f"Loaded {len(architecture.jobs)} jobs.")
    except Exception as e:
        logger.error(f"Failed to load job architecture: {e}")
        error_registry.register(e)
        print("[ERROR] Failed to load job architecture. See logs for details.")
        return False

    # Print summary
    print("\n=== Data Loading Summary ===")
    print(f"Skills loaded: {len(taxonomy.skills)}")
    print(f"Jobs loaded: {len(architecture.jobs)}")
    if job_skills_file:
        print(f"Job-skill mapping file: {job_skills_file}")
    print(f"Chunked loading: {'Enabled' if chunked else 'Disabled'} (chunksize={chunksize})")
    print(f"Validation: {'Enabled' if validate else 'Disabled'}")
    print(f"Verbose logging: {'Enabled' if verbose else 'Disabled'}")
    print("===========================\n")
    print("[INFO] Data loading complete. Ready to bolt on more functionality!")

    # Print any registered errors
    if len(error_registry.get_all()) > 0:
        print("\n[WARNING] Some errors were registered during execution:")
        for err in error_registry.get_all():
            print(f"- {err.get('message', err)}")
    
    return True

def generate_similarity_matrix(logger):
    global loaded_architecture
    
    if loaded_architecture is None:
        print("[ERROR] No job architecture loaded. Please load data first (option 1).")
        return
    
    print("\n=== Generate Job-to-Job Similarity Matrix ===")
    print(f"Jobs to process: {len(loaded_architecture.jobs)}")
    
    # Model versioning and output location
    print(f"\n=== Model Output Configuration ===")
    quarter_dir = setup_model_output_directory()
    print(f"Output directory created: {quarter_dir}")
    
    # Output format selection
    print(f"\n=== Output Format Selection ===")
    output_parquet = prompt_bool("Generate Parquet file (recommended for primary storage)?", default=True)
    output_csv = prompt_bool("Generate CSV file (required for Power BI cloud ingestion)?", default=True)
    
    if not output_parquet and not output_csv:
        print("[ERROR] At least one output format must be selected.")
        return
    
    # Configuration options (simplified - auto-detect cores and memory)
    chunk_size = prompt_int("Initial chunk size for processing", default=1000)
    enable_checkpoints = prompt_bool("Enable checkpointing for resumable processing?", default=True)
    
    # Estimate runtime before proceeding
    estimate_runtime = prompt_bool("Show runtime estimate before proceeding?", default=True)
    
    # Create precomputation configuration (auto-detect workers and memory)
    config = PrecomputeConfig(
        initial_chunk_size=chunk_size,
        max_workers=None,  # Auto-detect based on CPU cores
        memory_limit_mb=None,  # Auto-detect based on available RAM
        enable_checkpointing=enable_checkpoints,
        output_dir=str(quarter_dir)  # Convert Path to string
    )
    
    try:
        # Create precomputer
        logger.info("Creating similarity matrix precomputer...")
        precomputer = create_precomputer(
            job_architecture=loaded_architecture,
            config=config
        )
        
        # Show runtime estimate if requested
        if estimate_runtime:
            print("\n=== Runtime Estimation ===")
            logger.info("Calculating runtime estimate...")
            estimates = precomputer.estimate_runtime()
            
            print(f"Total jobs: {estimates['total_jobs']:,}")
            print(f"Total comparisons: {estimates['total_comparisons']:,}")
            print(f"Estimated chunks: {estimates['estimated_chunks']:,}")
            print(f"Parallel workers: {estimates['parallel_workers']} (auto-detected)")
            print(f"Estimated serial time: {estimates['estimated_serial_time_hours']:.2f} hours")
            print(f"Estimated parallel time: {estimates['estimated_parallel_time_hours']:.2f} hours")
            print(f"Memory per chunk: {estimates['estimated_memory_per_chunk_mb']:.2f} MB")
            
            # Show expected output file sizes
            estimated_csv_size = estimates['total_comparisons'] * 0.000040  # ~40 bytes per comparison in CSV
            print(f"Expected CSV file size: ~{estimated_csv_size:.1f} GB")
            if output_parquet:
                estimated_parquet_size = estimated_csv_size * 0.1  # Parquet typically 10x smaller than CSV
                print(f"Expected Parquet file size: ~{estimated_parquet_size:.1f} GB (after conversion)")
            if not output_csv and output_parquet:
                print("Note: CSV will be created first, then converted to Parquet and deleted")
            
            proceed = prompt_bool("Proceed with similarity matrix generation?", default=True)
            if not proceed:
                print("Operation cancelled.")
                return
        
        # Generate similarity matrix
        print("\n=== Starting Similarity Matrix Generation ===")
        logger.info("Starting similarity matrix precomputation...")
        
        output_path = precomputer.precompute_similarity_matrix()
        
        # Post-process output formats if needed
        csv_file = output_path / "job_similarity_matrix.csv"
        
        if output_parquet and csv_file.exists():
            print("Converting CSV to Parquet format...")
            try:
                # Read CSV and save as Parquet
                import pandas as pd
                df = pd.read_csv(csv_file)
                parquet_file = output_path / "job_similarity_matrix.parquet"
                df.to_parquet(parquet_file, compression='snappy', index=False)
                logger.info(f"Created Parquet file: {parquet_file}")
                print(f"✓ Parquet file created: {parquet_file}")
            except ImportError:
                print("[WARNING] Could not create Parquet file - pyarrow not installed")
                logger.warning("pyarrow not available for Parquet conversion")
            except Exception as e:
                print(f"[WARNING] Could not create Parquet file: {e}")
                logger.warning(f"Parquet conversion failed: {e}")
        
        if not output_csv and csv_file.exists():
            # User didn't want CSV, remove it (but only if Parquet was successfully created)
            parquet_file = output_path / "job_similarity_matrix.parquet"
            if parquet_file.exists():
                csv_file.unlink()
                print("✓ CSV file removed (Parquet created successfully)")
        
        print(f"\n=== Similarity Matrix Generation Complete ===")
        print(f"Output directory: {output_path}")
        if output_parquet and (output_path / "job_similarity_matrix.parquet").exists():
            print(f"Parquet file: {output_path / 'job_similarity_matrix.parquet'}")
        if output_csv and (output_path / "job_similarity_matrix.csv").exists():
            print(f"CSV file: {output_path / 'job_similarity_matrix.csv'}")
        print(f"Metadata: {output_path / 'metadata.json'}")
        print(f"Progress file: {output_path / 'progress.json'}")
        if enable_checkpoints:
            print(f"Checkpoint file: {output_path / 'checkpoint.json'}")
        
        print("===============================================\n")
        
        logger.info("Similarity matrix generation completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during similarity matrix generation: {e}")
        print(f"[ERROR] Similarity matrix generation failed: {e}")
        print("See logs for details.")

def main():
    logger = setup_logging(level='INFO')
    while True:
        choice = main_menu()
        if choice == '1':
            while True:
                sub_choice = precompute_menu()
                if sub_choice == '1':
                    load_and_validate_data(logger)
                elif sub_choice == '2':
                    generate_similarity_matrix(logger)
                elif sub_choice == '0':
                    break
                else:
                    print("[INFO] Option not yet implemented.")
        elif choice == '2':
            print("[INFO] Query Skill Similarities is coming soon.")
        elif choice == '0':
            print("Exiting. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter a valid option.")

if __name__ == "__main__":
    main()