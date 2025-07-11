"""
Data Loading and Validation Commands

Contains CLI commands for data loading workflows, extracted from main.py
and modularized to follow the Command pattern with SSE architecture.
"""

import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .base_command import BaseCommand, CommandResult
from ...data.loaders import SkillTaxonomyLoader, JobArchitectureLoader
from ...cli.utilities import prompt_file_path, prompt_bool, prompt_int


class DataLoadCommand(BaseCommand):
    """
    Command for loading and validating skills and job architecture data.
    
    Extracted from main.py load_and_validate_data function with enhanced
    error handling and configuration integration.
    """
    
    def __init__(self):
        super().__init__(
            name="data_load",
            description="Load and validate skills taxonomy and job architecture data"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for data loading command."""
        # Optional arguments that can be provided
        allowed_args = {
            'skills_file', 'job_skills_file', 'chunked', 'chunksize', 
            'validate', 'verbose', 'auto_update_skills'
        }
        
        unknown_args = set(kwargs.keys()) - allowed_args
        if unknown_args:
            return CommandResult(
                success=False,
                message=f"Unknown arguments: {unknown_args}",
                errors=[f"Argument '{arg}' not recognized" for arg in unknown_args]
            )
        
        return CommandResult(success=True, message="Arguments validated")
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute data loading and validation.
        
        Args:
            skills_file: Optional path to skills CSV file
            job_skills_file: Optional path to job-skill mapping CSV file  
            chunked: Whether to enable chunked loading (default from config)
            chunksize: Chunk size for streaming (default from config)
            validate: Whether to enable schema validation (default from config)
            verbose: Whether to enable verbose logging (default from config)
            auto_update_skills: Whether to automatically check for skills updates
            
        Returns:
            CommandResult with loaded taxonomy and architecture data
        """
        try:
            result_data = {}
            
            # Print header banner
            self._print_header()
            
            # Check for skills library updates if requested
            auto_update_default = self.get_config_value('cli', 'data_loading', 'skills_updates', 'auto_check_enabled', default=True)
            if kwargs.get('auto_update_skills', auto_update_default):
                update_result = self._check_skills_updates()
                if not update_result:
                    return CommandResult(
                        success=False,
                        message="Skills library update failed",
                        errors=["Skills update process failed"]
                    )
            
            # Get file paths (interactive or from args)
            file_paths = self._get_file_paths(kwargs)
            if not file_paths:
                return CommandResult(
                    success=False,
                    message="Failed to get valid file paths",
                    errors=["Could not determine input file paths"]
                )
            
            # Get processing options (interactive or from args)
            options = self._get_processing_options(kwargs)
            
            # Configure logging level
            if options['verbose']:
                self.logger.setLevel('DEBUG')
            else:
                self.logger.setLevel('WARNING')
            
            # Load skill taxonomy
            taxonomy_result = self._load_skill_taxonomy(file_paths, options)
            if not taxonomy_result.success:
                return taxonomy_result
            
            result_data['taxonomy'] = taxonomy_result.data
            
            # Load job architecture 
            architecture_result = self._load_job_architecture(
                file_paths, options, taxonomy_result.data
            )
            if not architecture_result.success:
                return architecture_result
            
            result_data['architecture'] = architecture_result.data
            
            # Print summary
            self._print_summary(result_data['taxonomy'], result_data['architecture'], file_paths, options)
            
            # Prepare metadata with safe access to loaded data
            taxonomy = result_data.get('taxonomy')
            architecture = result_data.get('architecture')
            
            skills_count = len(taxonomy.skills) if taxonomy and hasattr(taxonomy, 'skills') else 0
            jobs_count = len(architecture.jobs) if architecture and hasattr(architecture, 'jobs') else 0
            
            return CommandResult(
                success=True,
                message="Data loading completed successfully",
                data=result_data,
                metadata={
                    'skills_count': skills_count,
                    'jobs_count': jobs_count,
                    'files_processed': file_paths,
                    'options_used': options
                }
            )
            
        except Exception as e:
            self.logger.error(f"Data loading failed: {e}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Data loading failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _print_header(self):
        """Print the data loading header."""
        # Get header configuration from config
        header_text = self.get_config_value('cli', 'data_loading', 'header_text', 
                                          default="DATA LOADING & VALIDATION (SIMPLIFIED ARCHITECTURE)")
        separator_char = self.get_config_value('utils', 'display', 'default_separator_char', default="=")
        separator_length = self.get_config_value('utils', 'display', 'default_separator_length', default=60)
        
        print(f"\n{separator_char * separator_length}")
        print(f"🔧 {header_text}")
        print(f"{separator_char * separator_length}")
        print("Default data files will be used if you press Enter without typing a path.")
        print("Jobs will be auto-generated from the job-skill mapping file.")
    
    def _check_skills_updates(self) -> bool:
        """Check for skills library updates."""
        try:
            from ...api.skills_updater import prompt_skills_update
            if not prompt_skills_update(self.logger):
                print("❌ Skills library update failed. Exiting...")
                return False
            return True
        except ImportError as e:
            print(f"⚠️  Skills updater not available: {e}")
            print("   Proceeding with existing skills library...")
            return True
        except Exception as e:
            print(f"⚠️  Error checking for skills updates: {e}")
            print("   Proceeding with existing skills library...")
            return True
    
    def _get_file_paths(self, kwargs: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Get file paths either from arguments or interactive prompts."""
        # Get default file paths from configuration
        try:
            # Get the full paths from config
            full_skills_path = str(self.get_file_path('skills_comprehensive'))
            full_job_skills_path = str(self.get_file_path('job_skill_mapping'))
            
            print(f"🔍 DEBUG: Config full paths:")
            print(f"   • Skills: {full_skills_path}")
            print(f"   • Job skills: {full_job_skills_path}")
            
            # Extract relative paths (remove data/ prefix if present at the beginning)
            # The loaders expect relative paths that will be joined with base_dir
            default_skills_file = self._remove_data_prefix(full_skills_path)
            default_job_skills_file = self._remove_data_prefix(full_job_skills_path)
            
            print(f"🔍 DEBUG: Calculated defaults:")
            print(f"   • Skills: {default_skills_file}")
            print(f"   • Job skills: {default_job_skills_file}")
            
        except Exception as e:
            print(f"🔍 DEBUG: Config loading failed: {e}")
            # Fallback to configuration defaults if get_file_path fails
            full_skills_default = self.get_config_value('cli', 'data_loading', 'file_discovery', 'default_skills_file', 
                                                      default="data/skills_library/skills_comprehensive_all_versions.csv")
            full_job_skills_default = self.get_config_value('cli', 'data_loading', 'file_discovery', 'default_job_skills_file',
                                                          default="data/input_data/job_skill_mapping.csv")
            
            print(f"🔍 DEBUG: Fallback paths:")
            print(f"   • Skills: {full_skills_default}")
            print(f"   • Job skills: {full_job_skills_default}")
            
            # Extract relative paths
            default_skills_file = self._remove_data_prefix(full_skills_default)
            default_job_skills_file = self._remove_data_prefix(full_job_skills_default)
            
            print(f"🔍 DEBUG: Fallback relative paths:")
            print(f"   • Skills: {default_skills_file}")
            print(f"   • Job skills: {default_job_skills_file}")
        
        # Use provided arguments or prompt interactively
        if 'skills_file' in kwargs and 'job_skills_file' in kwargs:
            skills_file_input = str(kwargs['skills_file'])
            job_skills_file_input = str(kwargs['job_skills_file'])
        else:
            skills_file_input = str(prompt_file_path("Enter path to skills CSV file", default_skills_file))
            job_skills_file_input = str(prompt_file_path("Enter path to job-skill mapping CSV file", default_job_skills_file))
        
        # Ensure we have relative paths for the loaders
        # If user provided full paths, extract the relative part
        skills_file = self._remove_data_prefix(skills_file_input)
        job_skills_file = self._remove_data_prefix(job_skills_file_input)
        
        print(f"🔍 DEBUG: Final paths for loaders:")
        print(f"   • Skills: {skills_file}")
        print(f"   • Job skills: {job_skills_file}")
        
        # Validate that required files exist (check both relative and absolute paths)
        for file_path, file_type in [(skills_file, "skills"), (job_skills_file, "job-skill mapping")]:
            # Build potential paths to check
            potential_paths = [
                file_path,  # As-is (relative or absolute)
                f"data/{file_path}",  # With data/ prefix
                f"data\\{file_path}",  # With data\ prefix (Windows)
            ]
            
            file_found = False
            for check_path in potential_paths:
                if Path(check_path).exists():
                    file_found = True
                    break
            
            if not file_found:
                print(f"❌ ERROR: {file_type} file not found at any of these locations:")
                for check_path in potential_paths:
                    print(f"   • {check_path}")
                return None
        
        return {
            'skills_file': skills_file,
            'job_skills_file': job_skills_file
        }
    
    def _remove_data_prefix(self, path: str) -> str:
        """
        Remove data/ or data\ prefix from path if it exists at the beginning.
        
        Args:
            path: The file path to process
            
        Returns:
            str: Path with data prefix removed if it was at the beginning
            
        Examples:
            "data/skills_library/file.csv" -> "skills_library/file.csv"
            "data\\input_data\\file.csv" -> "input_data\\file.csv"  
            "input_data/file.csv" -> "input_data/file.csv" (unchanged)
        """
        # Convert to forward slashes for consistent processing
        normalized_path = path.replace('\\', '/')
        
        # Remove data/ prefix only if it's at the beginning
        if normalized_path.startswith('data/'):
            return normalized_path[5:]  # Remove 'data/' (5 characters)
        
        # Return original path if no data/ prefix
        return path
    
    def _get_processing_options(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get processing options either from arguments or interactive prompts."""
        options = {}
        
        # Get defaults from configuration
        default_chunked = self.get_config_value('cli', 'data_loading', 'defaults', 'chunked_enabled', default=True)
        default_chunksize = self.get_config_value('cli', 'data_loading', 'defaults', 'chunk_size', default=10000)
        default_validate = self.get_config_value('cli', 'data_loading', 'defaults', 'schema_validation_enabled', default=False)
        default_verbose = self.get_config_value('cli', 'data_loading', 'defaults', 'verbose_logging_enabled', default=False)
        
        if 'chunked' in kwargs:
            options['chunked'] = kwargs['chunked']
        else:
            options['chunked'] = prompt_bool("Enable chunked/streaming loading?", default=default_chunked)
        
        if 'chunksize' in kwargs:
            options['chunksize'] = kwargs['chunksize']
        else:
            options['chunksize'] = prompt_int("Chunk size for streaming", default=default_chunksize)
        
        if 'validate' in kwargs:
            options['validate'] = kwargs['validate']
        else:
            options['validate'] = prompt_bool("Enable schema validation?", default=default_validate)
        
        if 'verbose' in kwargs:
            options['verbose'] = kwargs['verbose']
        else:
            options['verbose'] = prompt_bool("Enable verbose logging?", default=default_verbose)
        
        return options
    
    def _load_skill_taxonomy(self, file_paths: Dict[str, str], options: Dict[str, Any]) -> CommandResult:
        """Load the skill taxonomy."""
        step_name = self.get_config_value('cli', 'data_loading', 'steps', 'skills_taxonomy', 'name', 
                                        default="Loading skill taxonomy")
        print(f"\n📊 Step 1: {step_name}...")
        
        try:
            taxonomy_loader = SkillTaxonomyLoader()
            
            # Check if we should disable validation for comprehensive library
            disable_validation = self.get_config_value('cli', 'data_loading', 'steps', 'skills_taxonomy', 
                                                     'disable_validation_for_comprehensive', default=True)
            
            taxonomy = taxonomy_loader.load_from_csv(
                skills_file=file_paths['skills_file'],
                chunked=options['chunked'],
                chunksize=options['chunksize'],
                validate=False if disable_validation else options['validate']
            )
            
            skills_count = len(taxonomy.skills)
            print(f"✅ Loaded {skills_count:,} skills successfully")
            
            return CommandResult(
                success=True,
                message=f"Skill taxonomy loaded: {skills_count} skills",
                data=taxonomy
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load skill taxonomy: {e}")
            self.error_registry.register(e)
            print(f"❌ ERROR: Failed to load skill taxonomy - {e}")
            
            return CommandResult(
                success=False,
                message=f"Failed to load skill taxonomy: {e}",
                errors=[str(e)]
            )
    
    def _load_job_architecture(self, file_paths: Dict[str, str], options: Dict[str, Any], taxonomy) -> CommandResult:
        """Load the job architecture."""
        step_name = self.get_config_value('cli', 'data_loading', 'steps', 'job_architecture', 'name',
                                        default="Auto-generating job architecture from job-skill mapping")
        print(f"\n📊 Step 2: {step_name}...")
        
        try:
            job_loader = JobArchitectureLoader(taxonomy)
            architecture = job_loader.load_from_csv(
                job_skills_file=file_paths['job_skills_file'],
                jobs_file=None,  # No jobs file - auto-generate from mapping
                chunked=options['chunked'],
                chunksize=options['chunksize'],
                validate=options['validate']
            )
            
            jobs_count = len(architecture.jobs)
            print(f"✅ Auto-generated {jobs_count:,} jobs successfully")
            
            return CommandResult(
                success=True,
                message=f"Job architecture loaded: {jobs_count} jobs",
                data=architecture
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load job architecture: {e}")
            self.error_registry.register(e)
            print(f"❌ ERROR: Failed to auto-generate job architecture - {e}")
            
            return CommandResult(
                success=False,
                message=f"Failed to load job architecture: {e}",
                errors=[str(e)]
            )
    
    def _print_summary(self, taxonomy, architecture, file_paths: Dict[str, str], options: Dict[str, Any]):
        """Print the data loading summary."""
        # Get separator configuration
        separator_char = self.get_config_value('utils', 'display', 'default_separator_char', default="=")
        separator_length = self.get_config_value('utils', 'display', 'default_separator_length', default=60)
        
        print(f"\n{separator_char * separator_length}")
        print(f"📋 DATA LOADING SUMMARY")
        print(f"{separator_char * separator_length}")
        print(f"✅ Skills loaded: {len(taxonomy.skills):,}")
        print(f"✅ Jobs auto-generated: {len(architecture.jobs):,}")
        print(f"\n📁 Data sources:")
        print(f"   • Skills: {file_paths['skills_file']}")
        print(f"   • Job-skill mapping: {file_paths['job_skills_file']}")
        print(f"   • Jobs: Auto-generated from mapping (simplified architecture)")
        print(f"\n⚙️  Configuration:")
        print(f"   • Chunked loading: {'✅ Enabled' if options['chunked'] else '❌ Disabled'} (size: {options['chunksize']:,})")
        print(f"   • Schema validation: {'✅ Enabled' if options['validate'] else '❌ Disabled'}")
        print(f"   • Verbose logging: {'✅ Enabled' if options['verbose'] else '❌ Disabled'}")
        print(f"{separator_char * separator_length}")
        print("🚀 Ready for similarity matrix generation!")
        print(f"{separator_char * separator_length}")
        
        # Print any registered errors
        if len(self.error_registry.get_all()) > 0:
            print(f"\n⚠️  Some warnings occurred during processing:")
            for err in self.error_registry.get_all():
                print(f"   • {err.get('message', err)}")
            print()
        
        # Brief pause to let user read the summary (configurable)
        pause_duration = self.get_config_value('cli', 'data_loading', 'summary_pause_seconds', default=1.5)
        time.sleep(pause_duration)


class DataValidationCommand(BaseCommand):
    """
    Command for standalone data validation operations.
    
    Provides data quality checks and validation reports.
    """
    
    def __init__(self):
        super().__init__(
            name="data_validate", 
            description="Validate data quality and schema compliance"
        )
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute data validation.
        
        Args:
            data_sources: List of data sources to validate
            validation_rules: Custom validation rules to apply
            
        Returns:
            CommandResult with validation report
        """
        # TODO: Implement standalone data validation
        # This would leverage the existing data_validation module
        return CommandResult(
            success=True,
            message="Data validation not yet implemented",
            data={'status': 'coming_soon'}
        ) 