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
    print("2. Generate job-to-job similarity matrix (coming soon)")
    print("3. Export results (coming soon)")
    print("0. Back to main menu")
    return input("Enter your choice: ").strip()

def load_and_validate_data(logger):
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
        logger.info(f"Loaded {len(taxonomy.skills)} skills.")
    except Exception as e:
        logger.error(f"Failed to load skill taxonomy: {e}")
        error_registry.register(e)
        print("[ERROR] Failed to load skill taxonomy. See logs for details.")
        return

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
        logger.info(f"Loaded {len(architecture.jobs)} jobs.")
    except Exception as e:
        logger.error(f"Failed to load job architecture: {e}")
        error_registry.register(e)
        print("[ERROR] Failed to load job architecture. See logs for details.")
        return

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

def main():
    logger = setup_logging(level='INFO')
    while True:
        choice = main_menu()
        if choice == '1':
            while True:
                sub_choice = precompute_menu()
                if sub_choice == '1':
                    load_and_validate_data(logger)
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
