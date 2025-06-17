#!/usr/bin/env python3
"""
Skill Similarity Engine v2 - Modular Entry Point (Menu-Driven)

This script provides a menu-based CLI for the Skill Similarity Engine pipeline.
It demonstrates chunked/streaming data loading, validation, logging, and error handling.
More functionality will be added step by step.
"""

import sys
import os
import time
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
from skill_similarity_engine.business_context import BusinessContextOrchestrator

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
    print("2. Generate Business Context Database")
    print("3. Query Skill Similarities (coming soon)")
    print("0. Exit")
    return input("Enter your choice: ").strip()

def precompute_menu():
    print("\nPrecompute Engine - Generate Parquet Files\n")
    print("Select a task:")
    print("1. Load and validate data")
    print("2. Generate similarity matrix + career pathways (both as parquet)")
    print("3. Export results (coming soon)")
    print("0. Back to main menu")
    return input("Enter your choice: ").strip()

def prompt_file_path(prompt, default_path):
    """Prompt for file path with a default option"""
    user_input = input(f"{prompt} [default: {default_path}]: ").strip()
    return user_input if user_input else default_path

def load_and_validate_data(logger):
    global loaded_taxonomy, loaded_architecture
    
    print("\n" + "="*60)
    print("🔧 DATA LOADING & VALIDATION (SIMPLIFIED ARCHITECTURE)")
    print("="*60)
    print("Default data files will be used if you press Enter without typing a path.")
    print("Jobs will be auto-generated from the job-skill mapping file.")
    
    # Check for skills library updates first
    try:
        from skill_similarity_engine.api.skills_updater import prompt_skills_update
        if not prompt_skills_update(logger):
            print("❌ Skills library update failed. Exiting...")
            return False
    except ImportError as e:
        print(f"⚠️  Skills updater not available: {e}")
        print("   Proceeding with existing skills library...")
    except Exception as e:
        print(f"⚠️  Error checking for skills updates: {e}")
        print("   Proceeding with existing skills library...")
    
    # Load default file paths from config
    try:
        from skill_similarity_engine.config.settings import get_config
        import yaml
        
        # Load data sources config
        config_path = Path("config/data_sources.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                data_sources_config = yaml.safe_load(f)
                default_skills_file = data_sources_config['similarity_calculation']['skills_library']['file_path']
                default_job_skills_file = data_sources_config['similarity_calculation']['job_skill_mapping']['file_path']
        else:
            # Fallback defaults
            default_skills_file = "skills_library/skills_comprehensive_all_versions.csv"
            default_job_skills_file = "input_data/job_skill_mapping.csv"
    except Exception:
        # Fallback defaults if config loading fails
        default_skills_file = "skills_library/skills_comprehensive_all_versions.csv"
        default_job_skills_file = "input_data/job_skill_mapping.csv"
    
    skills_file = prompt_file_path("Enter path to skills CSV file", default_skills_file)
    job_skills_file = prompt_file_path("Enter path to job-skill mapping CSV file", default_job_skills_file)
    
    # Validate that required files exist (check with data/ prefix if needed)
    from pathlib import Path
    for file_path, file_type in [(skills_file, "skills"), (job_skills_file, "job-skill mapping")]:
        # First check the path as-is
        if Path(file_path).exists():
            continue
        # If that fails, check with data/ prefix (for default paths)
        elif Path(f"data/{file_path}").exists():
            continue
        else:
            print(f"❌ ERROR: {file_type} file not found at either:")
            print(f"   • {file_path}")
            print(f"   • data/{file_path}")
            return False
    
    chunked = prompt_bool("Enable chunked/streaming loading?", default=True)
    chunksize = prompt_int("Chunk size for streaming", default=10000)
    validate = prompt_bool("Enable schema validation?", default=False)  # Disabled by default for comprehensive library
    verbose = prompt_bool("Enable verbose logging?", default=False)

    # Set logging level (reduce noise during normal operation)
    logger.setLevel('DEBUG' if verbose else 'WARNING')
    error_registry = ErrorRegistry()

    print(f"\n⏳ Processing data files...")
    print(f"   📊 Skills: {Path(skills_file).name}")
    print(f"   🔗 Job-skill mapping: {Path(job_skills_file).name}")
    print(f"   💼 Jobs: Auto-generated from mapping file")
    
    # Step 1: Load Skill Taxonomy
    print(f"\n📊 Step 1: Loading skill taxonomy...")
    try:
        taxonomy_loader = SkillTaxonomyLoader()
        taxonomy = taxonomy_loader.load_from_csv(
            skills_file=skills_file,
            chunked=chunked,
            chunksize=chunksize,
            validate=False  # Disable validation for comprehensive skills library
        )
        loaded_taxonomy = taxonomy
        print(f"✅ Loaded {len(taxonomy.skills):,} skills successfully")
    except Exception as e:
        logger.error(f"Failed to load skill taxonomy: {e}")
        error_registry.register(e)
        print(f"❌ ERROR: Failed to load skill taxonomy - {e}")
        return False

    # Step 2: Load Job Architecture (auto-generated from job-skill mapping)
    print(f"\n💼 Step 2: Auto-generating job architecture from job-skill mapping...")
    try:
        job_loader = JobArchitectureLoader(taxonomy)
        architecture = job_loader.load_from_csv(
            job_skills_file=job_skills_file,
            jobs_file=None,  # No jobs file - auto-generate from mapping
            chunked=chunked,
            chunksize=chunksize,
            validate=validate
        )
        loaded_architecture = architecture
        print(f"✅ Auto-generated {len(architecture.jobs):,} jobs successfully")
    except Exception as e:
        logger.error(f"Failed to load job architecture: {e}")
        error_registry.register(e)
        print(f"❌ ERROR: Failed to auto-generate job architecture - {e}")
        return False

    # Print summary with clear visual separation
    print(f"\n" + "="*60)
    print(f"📋 DATA LOADING SUMMARY")
    print("="*60)
    print(f"✅ Skills loaded: {len(taxonomy.skills):,}")
    print(f"✅ Jobs auto-generated: {len(architecture.jobs):,}")
    print(f"\n📁 Data sources:")
    print(f"   • Skills: {skills_file}")
    print(f"   • Job-skill mapping: {job_skills_file}")
    print(f"   • Jobs: Auto-generated from mapping (simplified architecture)")
    print(f"\n⚙️  Configuration:")
    print(f"   • Chunked loading: {'✅ Enabled' if chunked else '❌ Disabled'} (size: {chunksize:,})")
    print(f"   • Schema validation: {'✅ Enabled' if validate else '❌ Disabled'}")
    print(f"   • Verbose logging: {'✅ Enabled' if verbose else '❌ Disabled'}")
    print("="*60)
    print("🚀 Ready for similarity matrix generation!")
    print("="*60)

    # Print any registered errors
    if len(error_registry.get_all()) > 0:
        print(f"\n⚠️  Some warnings occurred during processing:")
        for err in error_registry.get_all():
            print(f"   • {err.get('message', err)}")
        print()
    
    # Brief pause to let user read the summary
    time.sleep(1.5)
    
    return True

def generate_similarity_matrix(logger):
    global loaded_architecture
    
    if loaded_architecture is None:
        print("❌ ERROR: No job architecture loaded. Please load data first (option 1).")
        return
    
    print(f"\n" + "="*60)
    print(f"🔄 SIMILARITY MATRIX GENERATION")
    print("="*60)
    print(f"📊 Jobs to process: {len(loaded_architecture.jobs):,}")
    
    # Model versioning and output location
    print(f"\n📁 Setting up output directory...")
    quarter_dir = setup_model_output_directory()
    print(f"✅ Output directory ready: {quarter_dir}")
    
    # Output format selection
    print(f"\n📝 Output format configuration...")
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
            print(f"\n📊 Calculating runtime estimates...")
            estimates = precomputer.estimate_runtime()
            
            print(f"\n" + "-"*50)
            print(f"⏱️  PROCESSING ESTIMATES")
            print("-"*50)
            print(f"📊 Total jobs: {estimates['total_jobs']:,}")
            print(f"🔄 Total comparisons: {estimates['total_comparisons']:,}")
            print(f"📦 Estimated chunks: {estimates['estimated_chunks']:,}")
            print(f"⚡ Parallel workers: {estimates['parallel_workers']} (auto-detected)")
            print(f"⏳ Estimated time: {estimates['estimated_parallel_time_hours']:.2f} hours")
            print(f"💾 Memory per chunk: {estimates['estimated_memory_per_chunk_mb']:.2f} MB")
            
            # Show expected output file sizes
            estimated_csv_size = estimates['total_comparisons'] * 0.000040  # ~40 bytes per comparison in CSV
            print(f"📁 Expected CSV size: ~{estimated_csv_size:.1f} GB")
            if output_parquet:
                estimated_parquet_size = estimated_csv_size * 0.1  # Parquet typically 10x smaller than CSV
                print(f"📁 Expected Parquet size: ~{estimated_parquet_size:.1f} GB")
            print("-"*50)
            
            proceed = prompt_bool("🚀 Proceed with similarity matrix generation?", default=True)
            if not proceed:
                print("❌ Operation cancelled.")
                return
        
        # Generate similarity matrix and career pathways
        print(f"\n" + "="*60)
        print(f"🚀 STARTING PRECOMPUTATION PIPELINE")
        print("="*60)
        
        output_path = precomputer.precompute_all()
        
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
        
        print(f"\n" + "="*60)
        print(f"✅ GENERATION COMPLETE!")
        print("="*60)
        print(f"📁 Output directory: {output_path}")
        
        if output_parquet and (output_path / "job_similarity_matrix.parquet").exists():
            print(f"📦 Parquet file: job_similarity_matrix.parquet")
        if output_csv and (output_path / "job_similarity_matrix.csv").exists():
            print(f"📄 CSV file: job_similarity_matrix.csv")
        print(f"📋 Metadata: metadata.json")
        if enable_checkpoints:
            print(f"💾 Checkpoint file: checkpoint.json")
        
        print("="*60)
        print("🎉 Similarity matrix and career pathways ready!")
        print("="*60)
        
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
            # Business Context Database Generation
            try:
                orchestrator = BusinessContextOrchestrator()
                orchestrator.handle_business_context_menu()
            except Exception as e:
                logger.error(f"Business context menu error: {e}")
                print(f"[ERROR] Business context menu failed: {e}")
        elif choice == '3':
            print("[INFO] Query Skill Similarities is coming soon.")
        elif choice == '0':
            print("Exiting. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter a valid option.")

if __name__ == "__main__":
    main()