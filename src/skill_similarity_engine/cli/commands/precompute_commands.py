"""
Precompute Commands for Similarity and Movement Analysis

Contains CLI commands for precomputation workflows, extracted from main.py
and modularized to follow the Command pattern with SSE architecture.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import sqlite3
import pandas as pd

from .base_command import BaseCommand, CommandResult
from ...similarity.precompute import create_precomputer, PrecomputeConfig
from ...models.versioning import setup_model_output_directory, ModelVersionManager
from ...cli.utilities import prompt_bool, prompt_int
from ...config.architectural_config_manager import get_config_manager
from ...utils.chunking import ChunkingStrategy


class SimilarityMatrixCommand(BaseCommand):
    """
    Command for generating similarity matrices and career pathways.
    
    Supports both basic and enhanced similarity algorithms:
    - Basic: Simple Jaccard/asymmetric coverage (default)
    - Enhanced: Rarity-weighted with defining skills boost (--enhanced flag)
    
    Enhanced algorithms show 0.76% improvement over basic similarity.
    """
    
    def __init__(self):
        super().__init__(
            name="similarity_matrix",
            description="Generate job similarity matrix and career pathways with optional enhanced algorithms"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for similarity matrix generation."""
        # Check for required data
        if 'architecture' not in kwargs:
            return CommandResult(
                success=False,
                message="Job architecture data is required",
                errors=["Missing 'architecture' argument - load data first"]
            )
        
        architecture = kwargs['architecture']
        if not hasattr(architecture, 'jobs') or not architecture.jobs:
            return CommandResult(
                success=False,
                message="Job architecture contains no jobs",
                errors=["Architecture data is empty or invalid"]
            )
        
        return CommandResult(success=True, message="Arguments validated")
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute similarity matrix generation.
        
        Args:
            architecture: JobArchitecture object with loaded job data
            enhanced: Whether to use enhanced similarity algorithms (default: False)
            output_parquet: Whether to generate Parquet output (default from prompt)
            output_csv: Whether to generate CSV output (default from prompt)
            chunk_size: Initial chunk size for processing (default from prompt)
            enable_checkpoints: Whether to enable checkpointing (default from prompt)
            estimate_runtime: Whether to show runtime estimates (default from prompt)
            
        Returns:
            CommandResult with generation status and output paths
        """
        try:
            architecture = kwargs['architecture']
            rarity_weighted_mode = kwargs.get('rarity_weighted', False) or kwargs.get('enhanced', False)  # Support both flags
            
            # Print header
            self._print_header(architecture, rarity_weighted_mode)
            
            # Setup rarity-weighted similarity if requested
            rarity_weighted_components = None
            if rarity_weighted_mode:
                rarity_weighted_components = self._setup_enhanced_similarity()
                if rarity_weighted_components is None:
                    return CommandResult(
                        success=False,
                        message="Rarity-weighted similarity setup failed",
                        errors=["Could not initialize rarity-weighted similarity components"]
                    )
            
            # Note: Output directory setup now handled by precomputer using daily folder strategy
            print(f"📁 Using enhanced daily folder strategy for outputs")
            
            # Get output format configuration
            output_config = self._get_output_configuration(kwargs)
            if not output_config:
                return CommandResult(
                    success=False,
                    message="No output format selected",
                    errors=["At least one output format must be selected"]
                )
            
            # Get processing configuration
            processing_config = self._get_processing_configuration(kwargs)
            
            # Create precomputation configuration
            config = PrecomputeConfig(
                initial_chunk_size=processing_config['chunk_size'],
                max_workers=None,  # Auto-detect based on CPU cores
                memory_limit_mb=None,  # Auto-detect based on available RAM
                enable_checkpointing=processing_config['enable_checkpoints'],
                output_dir="models"  # Will be handled by ModelVersionManager daily strategy
            )
            
            # Create precomputer with enhanced similarity support
            print(f"📊 Creating similarity matrix precomputer (enhanced={rarity_weighted_mode})...")
            precomputer = create_precomputer(
                job_architecture=architecture,
                config=config
            )
            
            # Inject enhanced similarity calculator if requested
            if rarity_weighted_mode and rarity_weighted_components:
                self._inject_rarity_weighted_calculator(precomputer, rarity_weighted_components)
            
            # Show runtime estimate if requested
            if processing_config['estimate_runtime']:
                estimate_result = self._show_runtime_estimates(precomputer, rarity_weighted_mode)
                if not estimate_result:
                    return CommandResult(
                        success=False,
                        message="Operation cancelled by user",
                        errors=["User chose not to proceed after seeing estimates"]
                    )
            
            # Generate similarity matrix and career pathways
            print(f"\n" + "="*60)
            if rarity_weighted_mode:
                # Load actual configuration values for display
                config_manager = self.config_manager if hasattr(self, 'config_manager') else get_config_manager()
                similarity_config = config_manager.get_nested_value(
                    'core', 'similarity_parameters', 'optuna_optimal'
                )
                
                if not similarity_config:
                    print("❌ Configuration Error: Missing core.similarity_parameters.optuna_optimal section")
                    print("   Please ensure config/core/similarity_parameters.yaml contains the required parameters.")
                    return CommandResult(
                        success=False,
                        message="Configuration error: Missing similarity parameters",
                        errors=["Missing core.similarity_parameters.optuna_optimal configuration"]
                    )
                
                print(f"🚀 STARTING RARITY-WEIGHTED PRECOMPUTATION PIPELINE")
                print(f"📊 Using rarity-weighted algorithms with defining skills boost")
                print(f"⚙️  Configuration: {similarity_config['defining_skills_percentile']}% percentile threshold, {similarity_config['defining_skills_multiplier']}x multiplier")
                print(f"📈 Expected improvement: 0.76% average, 12.5% positive rate (Optuna-optimized)")
            else:
                print(f"🚀 STARTING PRECOMPUTATION PIPELINE")
                print(f"📊 Using basic asymmetric coverage algorithms")
            print("="*60)
            
            output_path = precomputer.precompute_all()
            
            # Handle enhanced similarity database integration
            if rarity_weighted_mode and rarity_weighted_components:
                self._integrate_enhanced_results(output_path, rarity_weighted_components)
            
            # Handle output format conversion
            conversion_result = self._handle_output_conversion(
                output_path, output_config
            )
            
            # Print completion summary
            self._print_completion_summary(output_path, output_config, processing_config, rarity_weighted_mode)
            
            return CommandResult(
                success=True,
                message=f"Similarity matrix generation completed successfully ({'enhanced' if rarity_weighted_mode else 'basic'} algorithms)",
                data={
                    'output_path': str(output_path),
                    'formats_generated': output_config,
                    'conversion_results': conversion_result,
                    'enhanced_mode': rarity_weighted_mode
                },
                metadata={
                    'total_jobs': len(architecture.jobs),
                    'output_directory': str(output_path),
                    'config_used': processing_config,
                    'algorithm_type': 'enhanced_rarity_weighted' if rarity_weighted_mode else 'basic_asymmetric'
                }
            )
            
        except Exception as e:
            print(f"❌ Similarity matrix generation failed: {e}")
            print("   Please check your data and configuration files.")
            return CommandResult(
                success=False,
                message=f"Similarity matrix generation failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _setup_enhanced_similarity(self) -> Optional[Dict[str, Any]]:
        """
        Setup enhanced similarity components.
        
        Returns:
            Dictionary with enhanced similarity components or None if setup failed
        """
        try:
            print(f"\n🧠 Setting up enhanced similarity algorithms...")
            
            # Import enhanced similarity components
            from ...similarity.asymmetric import SkillIntelligenceEngine
            
            # Initialize skill intelligence engine
            skill_engine = SkillIntelligenceEngine()
            
            # Load skill universe and job-skill relationships
            print(f"📚 Loading skill universe with rarity data...")
            skill_universe_df = skill_engine.skill_universe_df
            
            print(f"🔗 Loading job-skill relationships...")
            job_to_skills = skill_engine.job_to_skills
            
            # Create defining skills map
            print(f"🎯 Creating job-specific defining skills map...")
            # Load job skills from database for defining skills analysis
            job_skills_df = skill_engine.defining_skills_analyzer.load_job_skills_from_database(
                str(skill_engine.config_manager.get_nested_value('business_context', 'database', 'path', default='data/business_context.sqlite'))
            )
            defining_skills_map = skill_engine.defining_skills_analyzer.create_job_specific_defining_skills(
                skill_universe_df, job_skills_df
            )
            
            print(f"✅ Enhanced similarity components initialized")
            print(f"   → Loaded {len(skill_universe_df):,} skills with rarity data")
            print(f"   → Mapped {len(job_to_skills):,} jobs to skill sets")
            print(f"   → Created defining skills for {len(defining_skills_map):,} jobs")
            
            return {
                'skill_engine': skill_engine,
                'skill_universe_df': skill_universe_df,
                'job_to_skills': job_to_skills,
                'defining_skills_map': defining_skills_map
            }
            
        except Exception as e:
            print(f"❌ Enhanced similarity setup failed: {e}")
            print("   Please verify your similarity configuration parameters.")
            print(f"❌ Enhanced similarity setup failed: {e}")
            print(f"   → Falling back to basic similarity algorithms")
            return None
    
    def _inject_enhanced_calculator(self, precomputer, enhanced_components: Dict[str, Any]):
        """
        Inject enhanced similarity calculator into the precomputer.
        
        Args:
            precomputer: The similarity matrix precomputer
            enhanced_components: Enhanced similarity components
        """
        try:
            from ...similarity.asymmetric import AsymmetricCoverageCalculator
            
            # Create enhanced calculator with skill universe data
            enhanced_calculator = AsymmetricCoverageCalculator(
                job_architecture=precomputer.job_architecture,
                skill_universe_df=enhanced_components['skill_universe_df']
            )
            
            # Replace the basic calculator
            precomputer.calculator = enhanced_calculator
            
            # Store enhanced components for later use
            precomputer._enhanced_components = enhanced_components
            
            print("✨ Enhanced similarity calculator injected into precomputer")
            
        except Exception as e:
            print(f"❌ Failed to inject enhanced calculator: {e}")
            print("   Check your enhanced similarity configuration.")
            raise
    
    def _inject_rarity_weighted_calculator(self, precomputer, rarity_weighted_components: Dict[str, Any]):
        """
        Inject rarity-weighted similarity calculator into the precomputer.
        
        This method is an alias for _inject_enhanced_calculator to maintain
        backward compatibility with existing code.
        
        Args:
            precomputer: The similarity matrix precomputer
            rarity_weighted_components: Enhanced similarity components
        """
        return self._inject_enhanced_calculator(precomputer, rarity_weighted_components)
    
    def _integrate_enhanced_results(self, output_path: Path, enhanced_components: Dict[str, Any]):
        """
        Integrate enhanced similarity results with database schema extensions.
        
        Args:
            output_path: Path to output directory
            enhanced_components: Enhanced similarity components
        """
        try:
            print(f"\n💾 Integrating enhanced similarity results...")
            
            # This would extend the job_similarities table with enhanced columns
            # For now, we'll create a metadata file with enhancement info
            from typing import Any
            import json
            
            # Load configuration values directly from core config
            config_manager = get_config_manager()
            similarity_config = config_manager.get_nested_value(
                'core', 'similarity_parameters', 'optuna_optimal'
            )
            rarity_thresholds = config_manager.get_nested_value(
                'core', 'similarity_parameters', 'rarity_thresholds'
            )
            
            if not similarity_config or not rarity_thresholds:
                print("⚠️ Missing similarity configuration for metadata generation")
                print("   Some metadata features may not be available.")
                similarity_config = {'defining_skills_percentile': 'Unknown', 'defining_skills_multiplier': 'Unknown'}
                rarity_thresholds = {'rare_threshold': 'Unknown', 'uncommon_threshold': 'Unknown', 'common_threshold': 'Unknown'}
            
            enhancement_metadata: Dict[str, Any] = {
                'algorithm_type': 'enhanced_rarity_weighted',
                'defining_skills_percentile': similarity_config['defining_skills_percentile'],
                'gentle_multiplier': similarity_config['defining_skills_multiplier'],
                'rarity_thresholds': {
                    'rare': rarity_thresholds['rare_threshold'],
                    'uncommon': rarity_thresholds['uncommon_threshold'],
                    'common': rarity_thresholds['common_threshold']
                },
                'total_skills_analyzed': len(enhanced_components['skill_universe_df']),
                'jobs_with_defining_skills': len(enhanced_components['defining_skills_map']),
                'config_source': 'config/core/similarity_parameters.yaml - optuna_optimal'
            }
            
            # Write enhancement metadata
            metadata_file = output_path / "enhanced_similarity_metadata.json"
            with open(str(metadata_file), 'w', encoding='utf-8') as f:
                json.dump(enhancement_metadata, f, indent=2)
            
            print(f"✅ Enhanced similarity metadata saved to {metadata_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to integrate enhanced results: {e}")
            print("   Enhanced features may not be available in output.")
            print(f"⚠️  Enhanced results integration failed: {e}")
    
    def _print_header(self, architecture, enhanced_mode: bool = False):
        """Print the similarity matrix generation header."""
        print(f"\n" + "="*60)
        if enhanced_mode:
            print(f"🔄 ENHANCED SIMILARITY MATRIX GENERATION")
            print(f"🧠 Using rarity-weighted algorithms with defining skills boost")
        else:
            print(f"🔄 SIMILARITY MATRIX GENERATION")
            print(f"📊 Using basic asymmetric coverage algorithms")
        print("="*60)
        print(f"📊 Jobs to process: {len(architecture.jobs):,}")
        
        if enhanced_mode:
            # Load actual configuration values for display
            config_manager = get_config_manager()
            similarity_config = config_manager.get_nested_value(
                'core', 'similarity_parameters', 'optuna_optimal'
            )
            
            if not similarity_config:
                print("❌ Configuration Error: Missing core.similarity_parameters.optuna_optimal section")
                print("   Please ensure config/core/similarity_parameters.yaml contains the required parameters.")
                return
            
            print(f"⚙️  Enhanced features:")
            print(f"   → Rarity-weighted similarity calculation")
            print(f"   → Defining skills boost ({similarity_config['defining_skills_multiplier']}x multiplier)")
            print(f"   → Expected 0.76% improvement over basic algorithms (Optuna-optimized)")
    
    def _show_runtime_estimates(self, precomputer, enhanced_mode: bool = False) -> bool:
        """Show runtime estimates and get user confirmation."""
        print(f"\n📊 Calculating runtime estimates...")
        estimates = precomputer.estimate_runtime()
        
        print(f"\n" + "-"*50)
        if enhanced_mode:
            print(f"⏱️  ENHANCED PROCESSING ESTIMATES")
            print(f"🧠 Algorithm: Rarity-weighted with defining skills boost")
        else:
            print(f"⏱️  PROCESSING ESTIMATES")
            print(f"📊 Algorithm: Basic asymmetric coverage")
        print("-"*50)
        print(f"📊 Total jobs: {estimates['total_jobs']:,}")
        print(f"🔄 Total comparisons: {estimates['total_comparisons']:,}")
        print(f"📦 Estimated chunks: {estimates['estimated_chunks']:,}")
        print(f"⚡ Parallel workers: {estimates['parallel_workers']} (auto-detected)")
        
        # Enhanced algorithms may take slightly longer due to rarity calculations
        time_multiplier = 1.1 if enhanced_mode else 1.0
        estimated_time = estimates['estimated_parallel_time_hours'] * time_multiplier
        print(f"⏳ Estimated time: {estimated_time:.2f} hours")
        
        print(f"💾 Memory per chunk: {estimates['estimated_memory_per_chunk_mb']:.2f} MB")
        
        if enhanced_mode:
            print(f"🧠 Enhanced processing overhead: ~10% additional time")
        
        # Show expected output file sizes
        estimated_csv_size = estimates['total_comparisons'] * 0.000040  # ~40 bytes per comparison in CSV
        print(f"📁 Expected CSV size: ~{estimated_csv_size:.1f} GB")
        
        estimated_parquet_size = estimated_csv_size * 0.1  # Parquet typically 10x smaller than CSV
        print(f"📁 Expected Parquet size: ~{estimated_parquet_size:.1f} GB")
        print("-"*50)
        
        from ...cli.utilities import prompt_bool
        prompt_text = "🚀 Proceed with enhanced similarity matrix generation?" if enhanced_mode else "🚀 Proceed with similarity matrix generation?"
        return prompt_bool(prompt_text, default=True)
    
    def _print_completion_summary(self, output_path: Path, output_config: Dict[str, bool], 
                                processing_config: Dict[str, Any], enhanced_mode: bool = False):
        """Print the completion summary."""
        print(f"\n" + "="*60)
        if enhanced_mode:
            print(f"✅ ENHANCED GENERATION COMPLETE!")
            print(f"🧠 Rarity-weighted algorithms with defining skills boost applied")
        else:
            print(f"✅ GENERATION COMPLETE!")
        print("="*60)
        print(f"📁 Output directory: {output_path}")
        
        if output_config['parquet'] and (output_path / "job_similarity_matrix.parquet").exists():
            print(f"📦 Parquet file: job_similarity_matrix.parquet")
        if output_config['csv'] and (output_path / "job_similarity_matrix.csv").exists():
            print(f"📄 CSV file: job_similarity_matrix.csv")
        print(f"📋 Metadata: metadata.json")
        
        if enhanced_mode:
            print(f"🧠 Enhanced metadata: enhanced_similarity_metadata.json")
        
        if processing_config['enable_checkpoints']:
            print(f"💾 Checkpoint file: checkpoint.json")
        
        print("="*60)
        if enhanced_mode:
            print("🎉 Enhanced similarity matrix and career pathways ready!")
            print("📈 Expect 0.76% average improvement in similarity scores")
        else:
            print("🎉 Similarity matrix and career pathways ready!")
        print("="*60)

    # ============================================================================
    # EXISTING METHODS - PRESERVED FOR BACKWARD COMPATIBILITY
    # ============================================================================
    
    def _get_output_configuration(self, kwargs: Dict[str, Any]) -> Optional[Dict[str, bool]]:
        """Get output format configuration."""
        print(f"\n📁 Output format configuration...")
        
        if 'output_parquet' in kwargs and 'output_csv' in kwargs:
            output_parquet = kwargs['output_parquet']
            output_csv = kwargs['output_csv']
        else:
            output_parquet = prompt_bool("Generate Parquet file (recommended for primary storage)?", default=True)
            output_csv = prompt_bool("Generate CSV file (required for Power BI cloud ingestion)?", default=True)
        
        if not output_parquet and not output_csv:
            print("[ERROR] At least one output format must be selected.")
            return None
        
        return {
            'parquet': output_parquet,
            'csv': output_csv
        }
    
    def _get_processing_configuration(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get processing configuration options."""
        config = {}
        
        if 'chunk_size' in kwargs:
            config['chunk_size'] = kwargs['chunk_size']
        else:
            config['chunk_size'] = prompt_int("Initial chunk size for processing", default=1000)
        
        if 'enable_checkpoints' in kwargs:
            config['enable_checkpoints'] = kwargs['enable_checkpoints']
        else:
            config['enable_checkpoints'] = prompt_bool("Enable checkpointing for resumable processing?", default=True)
        
        if 'estimate_runtime' in kwargs:
            config['estimate_runtime'] = kwargs['estimate_runtime']
        else:
            config['estimate_runtime'] = prompt_bool("Show runtime estimate before proceeding?", default=True)
        
        return config
    
    def _handle_output_conversion(self, output_path: Path, output_config: Dict[str, bool]) -> Dict[str, Any]:
        """Handle output format conversion based on configuration."""
        conversion_results = {}
        csv_file = output_path / "job_similarity_matrix.csv"
        
        if output_config['parquet'] and csv_file.exists():
            print("Converting CSV to Parquet format...")
            try:
                import pandas as pd
                df = pd.read_csv(csv_file)
                parquet_file = output_path / "job_similarity_matrix.parquet"
                df.to_parquet(parquet_file, compression='snappy', index=False)
                print(f"📦 Created Parquet file: {parquet_file}")
                print(f"✅ Parquet file created: {parquet_file}")
                conversion_results['parquet_created'] = True
                
            except ImportError:
                print("⚠️ pyarrow not available for Parquet conversion")
                print("   Install pyarrow to enable Parquet export: pip install pyarrow")
                conversion_results['parquet_created'] = False
                conversion_results['parquet_error'] = "pyarrow not installed"
                
            except Exception as e:
                print(f"⚠️ Parquet conversion failed: {e}")
                print("   CSV export will still be available.")
                conversion_results['parquet_created'] = False
                conversion_results['parquet_error'] = str(e)
        
        if not output_config['csv'] and csv_file.exists():
            # User didn't want CSV, remove it (but only if Parquet was successfully created)
            parquet_file = output_path / "job_similarity_matrix.parquet"
            if parquet_file.exists():
                csv_file.unlink()
                print("✅ CSV file removed (Parquet created successfully)")
                conversion_results['csv_removed'] = True
        
        return conversion_results


class MovementAnalysisCommand(BaseCommand):
    """
    Command for generating movement analysis data.
    
    Extracted from main.py generate_movement_analysis function with enhanced
    modularity and error handling.
    """
    
    def __init__(self):
        super().__init__(
            name="movement_analysis",
            description="Generate workforce movement analysis and transition data"
        )
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute movement analysis generation.
        
        Args:
            output_parquet: Whether to generate Parquet output (default from prompt)
            output_csv: Whether to generate CSV output (default from prompt)
            estimate_runtime: Whether to show runtime estimates (default from prompt)
            
        Returns:
            CommandResult with generation status and output paths
        """
        try:
            # Print header
            self._print_header()
            
            # Get output configuration
            output_config = self._get_output_configuration(kwargs)
            if not output_config:
                return CommandResult(
                    success=False,
                    message="No output format selected",
                    errors=["At least one output format must be selected"]
                )
            
            # Get processing configuration
            processing_config = self._get_processing_configuration(kwargs)
            
            # Import and create movement precomputer
            from ...models.movement_precomputer import create_movement_precomputer
            
            print("📈 Creating movement analysis precomputer...")
            precomputer = create_movement_precomputer()
            
            # Show runtime estimate if requested
            if processing_config['estimate_runtime']:
                print(f"\n📊 Runtime estimates not available yet...")
                from ...cli.utilities import prompt_bool
                proceed = prompt_bool("🚀 Proceed with movement analysis?", default=True)
                if not proceed:
                    return CommandResult(
                        success=False,
                        message="Operation cancelled by user",
                        errors=["User chose not to proceed"]
                    )
            
            # Generate movement analysis
            print(f"\n" + "="*60)
            print(f"🚀 STARTING MOVEMENT ANALYSIS PIPELINE")
            print("="*60)
            
            # Get directories from configuration
            colleague_positions_dir = str(self.get_directory_path('colleague_positions'))
            positions_dir = str(self.get_directory_path('positions_history'))
            
            result = precomputer.generate_movement_analysis(
                colleague_positions_dir=colleague_positions_dir,
                positions_dir=positions_dir
            )
            
            if not result['success']:
                raise Exception(result['error'])
            
            output_path = result['output_directory']
            
            # Print completion summary
            self._print_completion_summary(output_path, output_config)
            
            return CommandResult(
                success=True,
                message="Movement analysis completed successfully",
                data={
                    'output_path': output_path,
                    'formats_generated': output_config,
                    'analysis_result': result
                },
                metadata={
                    'colleague_positions_dir': colleague_positions_dir,
                    'positions_dir': positions_dir,
                    'config_used': processing_config
                }
            )
            
        except ImportError as e:
            print(f"❌ Movement analysis import error: {e}")
            print("   Please ensure movement analysis dependencies are installed.")
            return CommandResult(
                success=False,
                message=f"Movement analysis module not available: {e}",
                errors=["Please ensure the movement tracker is properly installed"]
            )
        except Exception as e:
            print(f"❌ Movement analysis generation failed: {e}")
            print("   Check your movement data and configuration.")
            return CommandResult(
                success=False,
                message=f"Movement analysis generation failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _print_header(self):
        """Print the movement analysis header."""
        print(f"\n" + "="*60)
        print(f"👥 MOVEMENT ANALYSIS GENERATION")
        print("="*60)
        print("This will analyse workforce transition patterns and generate movement data.")
    
    def _get_output_configuration(self, kwargs: Dict[str, Any]) -> Optional[Dict[str, bool]]:
        """Get output format configuration."""
        print(f"\n⚙️ Movement Analysis Configuration...")
        
        if 'output_parquet' in kwargs and 'output_csv' in kwargs:
            output_parquet = kwargs['output_parquet']
            output_csv = kwargs['output_csv']
        else:
            output_parquet = prompt_bool("Generate Parquet file (recommended for analytics)?", default=True)
            output_csv = prompt_bool("Generate CSV file (for compatibility)?", default=True)
        
        if not output_parquet and not output_csv:
            print("[ERROR] At least one output format must be selected.")
            return None
        
        return {
            'parquet': output_parquet,
            'csv': output_csv
        }
    
    def _get_processing_configuration(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get processing configuration options."""
        config = {}
        
        if 'estimate_runtime' in kwargs:
            config['estimate_runtime'] = kwargs['estimate_runtime']
        else:
            config['estimate_runtime'] = prompt_bool("Show runtime estimate before proceeding?", default=True)
        
        # Movement detection parameters - capture ALL movements for ML/statistical analysis
        print("ℹ️  Capturing ALL movements without filtering (optimised for ML/statistical analysis)")
        config['min_movement_frequency'] = 1  # Capture single movements
        config['detection_window_weeks'] = 999  # No time window restriction  
        config['min_position_tenure_weeks'] = 1  # Capture even brief positions
        
        return config
    
    def _print_completion_summary(self, output_path: str, output_config: Dict[str, bool]):
        """Print the completion summary."""
        print(f"\n" + "="*60)
        print(f"✅ MOVEMENT ANALYSIS COMPLETE!")
        print("="*60)
        print(f"📁 Output directory: {output_path}")
        
        if output_config['parquet']:
            print(f"📦 Parquet files: employee_movements.parquet, movement_summary.parquet")
        if output_config['csv']:
            print(f"📄 CSV files: employee_movements.csv, movement_summary.csv")
        print(f"📋 Metadata: metadata.json")
        
        print("="*60)
        print("🎉 Movement analysis data ready for analytics!")
        print("="*60)


class MovementPatternPopulationCommand(BaseCommand):
    """
    Command for populating analytics_movement_patterns table from database.
    
    This command integrates the existing movement analysis modules with the database,
    replacing CSV-based workflows with direct database population following
    Step 2.1 of the Movement Analysis Intelligence Pipeline.
    """
    
    def __init__(self):
        super().__init__(
            name="movement_pattern_population",
            description="Populate analytics_movement_patterns table using database-integrated movement analysis"
        )
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute movement pattern population from database sources.
        
        Returns:
            CommandResult with population status and performance metrics
        """
        import time
        from ...utils.progress import ProgressTracker
        from ...utils.chunking import AdaptiveChunker, ChunkingStrategy
        from ...utils.performance import get_memory_usage
        from ...models.movement_tracker import MovementTracker
        from ...models.movement_fact_builder import MovementFactBuilder
        from ...business_context.database_integrator import DatabaseIntegrator
        from ...models.versioning import ModelVersionManager
        from pathlib import Path
        import pandas as pd
        import sqlite3
        
        start_time = time.time()
        performance_metrics = {}
        
        try:
            print("💾 Starting movement pattern population from database")
            
            # Step 1: Initialize database connection and validate source data
            with ProgressTracker(total=1, desc="Initializing database connection", memory_tracking=True) as progress:
                # Get database path using the established version manager pattern
                version_manager = ModelVersionManager()
                output_dir = version_manager.setup_output_directory(
                    interactive=False,
                    output_type='business_context'
                )
                db_path = output_dir / 'business_context.sqlite'
                
                if not db_path.exists():
                    return CommandResult(
                        success=False,
                        message="Business context database not found. Please build the workforce database first.",
                        errors=[f"Database file not found: {db_path}"]
                    )
                
                # Initialize database integrator
                db_integrator = DatabaseIntegrator(db_path)
                progress.update(1)
                print(f"🔗 Connected to database: {db_path}")
            
            # Step 2: Validate required source tables exist and have data
            with ProgressTracker(total=1, desc="Validating source data", memory_tracking=True) as progress:
                source_counts = self._validate_source_tables(db_path)
                if not source_counts:
                    return CommandResult(
                        success=False,
                        message="Required source tables missing or empty",
                        errors=["Please ensure core_colleague_positions_history and core_position_timeline are populated"]
                    )
                progress.update(1)
                print(f"✅ Source validation complete: {source_counts}")
            
            # Step 3: Initialize movement analysis modules
            from ...config.workforce_config_loader import get_workforce_config_loader
            workforce_config_loader = get_workforce_config_loader()
            movement_tracker = MovementTracker(workforce_config_loader)
            fact_builder = MovementFactBuilder(self.config_manager)  # Uses ArchitecturalConfigManager
            
            # Step 4: Load position mappings from database for Python-based merge
            with ProgressTracker(total=1, desc="Loading position mappings", memory_tracking=True) as progress:
                position_mappings = self._load_position_mappings_from_db(db_path)
                progress.update(1)
                print(f"🗺️ Loaded {len(position_mappings):,} position mappings for merge")
            
            # Step 5: Load colleague positions with adaptive chunking (2M+ records)
            colleague_positions_count = source_counts['core_colleague_positions_history']
            print(f"⚙️ Processing {colleague_positions_count:,} colleague position records")
            
            with ProgressTracker(total=colleague_positions_count, desc="Loading and merging colleague positions", memory_tracking=True) as progress:
                # Use adaptive chunking for memory management
                strategy = ChunkingStrategy(
                    initial_chunk_size=50000,
                    min_chunk_size=10000,
                    max_chunk_size=100000,
                    memory_threshold_percent=75.0
                )
                
                colleague_positions = []
                total_processed = 0
                total_merged = 0
                total_orphans = 0
                
                for chunk in self._load_colleague_positions_chunked(db_path, strategy):
                    # Perform Python-based merge with position mappings
                    merged_chunk, chunk_merged, chunk_orphans = self._merge_position_numbers(chunk, position_mappings)
                    colleague_positions.extend(merged_chunk)
                    
                    total_processed += len(chunk)
                    total_merged += chunk_merged
                    total_orphans += chunk_orphans
                    
                    progress.update(len(chunk))
                
                # Log merge statistics
                merge_rate = (total_merged / total_processed * 100) if total_processed > 0 else 0
                print(f"✅ Position merge completed: {total_merged:,}/{total_processed:,} records merged ({merge_rate:.1f}%)")
                if total_orphans > 0:
                    print(f"⚠️ Found {total_orphans:,} orphan records (PosIDLookupKey not in position timeline)")
                    print("   These records will be excluded from movement analysis.")
                
                movement_tracker.colleague_positions = colleague_positions
            
            # Step 6: Skip position enrichment - Position Numbers already loaded directly
            print("✅ Position Numbers already available - skipping enrichment step")
            
            # Step 7: Detect movements (existing MovementTracker logic)
            employee_count = len(movement_tracker.employee_histories) if hasattr(movement_tracker, 'employee_histories') else len(set(pos.employee_number for pos in colleague_positions))
            with ProgressTracker(total=employee_count, desc="Detecting movements", memory_tracking=True) as progress:
                movement_tracker.detect_movements()
                progress.update(employee_count)
            
            movements_count = len(movement_tracker.movement_events)
            print(f"📊 Detected {movements_count:,} movement events")
            
            # Step 8: Build fact table (existing MovementFactBuilder logic)
            with ProgressTracker(total=1, desc="Building movement fact table", memory_tracking=True) as progress:
                movements_df = self._convert_movements_to_dataframe(movement_tracker.movement_events)
                movement_facts_df = fact_builder.build_fact_table_from_movements(movements_df)
                progress.update(1)
                print(f"📈 Built fact table with {len(movement_facts_df):,} patterns")
            
            # Step 9: Enrich with JobProfileIDs and prepare for database
            with ProgressTracker(total=1, desc="Enriching with job profile data", memory_tracking=True) as progress:
                enriched_df = self._enrich_with_job_profile_ids(movement_facts_df, db_path)
                progress.update(1)
                print(f"✨ Enriched {len(enriched_df):,} patterns with job profile data")
            
            # Step 10: Insert into database using established pattern
            with ProgressTracker(total=len(enriched_df), desc="Inserting movement patterns", memory_tracking=True) as progress:
                success = db_integrator.populate_movement_patterns(enriched_df)
                if not success:
                    return CommandResult(
                        success=False,
                        message="Failed to populate analytics_movement_patterns table",
                        errors=["Database insertion failed - check logs for details"]
                    )
                progress.update(len(enriched_df))
            
            # Collect performance metrics
            end_time = time.time()
            final_memory = get_memory_usage()
            
            performance_metrics = {
                'total_records_processed': colleague_positions_count,
                'movements_detected': movements_count,
                'fact_patterns_created': len(enriched_df),
                'processing_time_seconds': end_time - start_time,
                'peak_memory_mb': final_memory.current_process_usage_mb
            }
            
            return CommandResult(
                success=True,
                message=f"Successfully populated {len(enriched_df):,} movement patterns from {movements_count:,} detected movements",
                data={'performance_metrics': performance_metrics},
                metadata={
                    'database_path': str(db_path),
                    'source_counts': source_counts,
                    'processing_strategy': 'database_integrated'
                }
            )
            
        except Exception as e:
            print(f"❌ Movement pattern population failed: {e}")
            print("   Check your database connection and movement data.")
            return CommandResult(
                success=False,
                message=f"Movement pattern population failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _validate_source_tables(self, db_path: Path) -> dict:
        """Validate that required source tables exist and have data."""
        try:
            with sqlite3.connect(db_path) as conn:
                # Check colleague positions history
                colleague_count = conn.execute(
                    "SELECT COUNT(*) FROM core_colleague_positions_history"
                ).fetchone()[0]
                
                # Check position timeline
                position_count = conn.execute(
                    "SELECT COUNT(*) FROM core_position_timeline"
                ).fetchone()[0]
                
                if colleague_count == 0 or position_count == 0:
                    return {}
                
                return {
                    'core_colleague_positions_history': colleague_count,
                    'core_position_timeline': position_count
                }
        except Exception as e:
            print(f"❌ Source table validation failed: {e}")
            print("   Check your database schema and data integrity.")
            return {}
    
    def _load_position_mappings_from_db(self, db_path: Path) -> dict:
        """Load position mappings from database (replaces CSV loading)."""
        try:
            with sqlite3.connect(db_path) as conn:
                query = """
                SELECT DISTINCT PosIDLookupKey, Position_Number 
                FROM core_position_timeline 
                WHERE Position_Number IS NOT NULL
                """
                cursor = conn.execute(query)
                mappings = {float(row[0]): int(row[1]) for row in cursor.fetchall()}
                return mappings
        except Exception as e:
            print(f"❌ Failed to load position mappings: {e}")
            print("   Ensure position timeline data is available.")
            return {}
    
    def _load_colleague_positions_chunked(self, db_path: Path, strategy: ChunkingStrategy):
        """Load colleague positions in chunks using adaptive strategy."""
        try:
            with sqlite3.connect(db_path) as conn:
                # Get total count for chunking
                total_count = conn.execute(
                    "SELECT COUNT(*) FROM core_colleague_positions_history"
                ).fetchone()[0]
                
                # Load in chunks
                offset = 0
                chunk_size = strategy.initial_chunk_size
                
                while offset < total_count:
                    query = """
                    SELECT "Employee Number", PosIDLookupKey, "Week Ending"
                    FROM core_colleague_positions_history 
                    ORDER BY "Employee Number", "Week Ending"
                    LIMIT ? OFFSET ?
                    """
                    
                    cursor = conn.execute(query, (chunk_size, offset))
                    
                    # Import ColleaguePosition class for proper object creation
                    from ...models.colleague_position import ColleaguePosition
                    
                    chunk_data = []
                    for row in cursor.fetchall():
                        # Create ColleaguePosition objects with PosIDLookupKey (to be merged later)
                        colleague_pos = ColleaguePosition(
                            pos_id_lookup_key=str(row[1]),  # Store PosIDLookupKey for merge
                            employee_number=int(row[0]),
                            week_ending=row[2],
                            position_number=None  # Will be set during merge
                        )
                        chunk_data.append(colleague_pos)
                    
                    if not chunk_data:
                        break
                    
                    yield chunk_data
                    offset += len(chunk_data)
                    
        except Exception as e:
            print(f"❌ Failed to load colleague positions: {e}")
            print("   Check colleague positions data availability.")
            yield []
    
    def _merge_position_numbers(self, chunk: list, position_mappings: dict) -> tuple:
        """
        Merge position numbers into colleague position chunk using Python-based join.
        
        Args:
            chunk: List of ColleaguePosition objects with PosIDLookupKey
            position_mappings: Dict mapping PosIDLookupKey -> Position_Number
            
        Returns:
            Tuple of (merged_chunk, merged_count, orphan_count)
        """
        merged_count = 0
        orphan_count = 0
        
        for colleague_pos in chunk:
            try:
                # Convert PosIDLookupKey to float for lookup
                pos_id_lookup = float(colleague_pos.pos_id_lookup_key)
                
                if pos_id_lookup in position_mappings:
                    # Successful merge - set the real position number
                    colleague_pos.position_number = position_mappings[pos_id_lookup]
                    merged_count += 1
                else:
                    # Orphan record - PosIDLookupKey not found in timeline
                    colleague_pos.position_number = None
                    orphan_count += 1
                    
            except (ValueError, TypeError) as e:
                # Invalid PosIDLookupKey format
                self.logger.debug(f"Invalid PosIDLookupKey format: {colleague_pos.pos_id_lookup_key} - {e}")
                colleague_pos.position_number = None
                orphan_count += 1
        
        return chunk, merged_count, orphan_count
    
    def _convert_movements_to_dataframe(self, movement_events: list) -> pd.DataFrame:
        """Convert MovementEvent objects to DataFrame format expected by MovementFactBuilder."""
        try:
            # Convert MovementEvent objects using their to_dict() method for consistency
            movements_data = []
            for event in movement_events:
                # Use the MovementEvent.to_dict() method to ensure correct column names
                movements_data.append(event.to_dict())
            
            return pd.DataFrame(movements_data)
        except Exception as e:
            print(f"❌ Failed to convert movements to DataFrame: {e}")
            print("   Check movement data format and structure.")
            return pd.DataFrame()
    
    def _enrich_with_job_profile_ids(self, movement_facts_df: pd.DataFrame, db_path: Path) -> pd.DataFrame:
        """Enrich movement facts with JobProfileIDs for database foreign keys."""
        try:
            with sqlite3.connect(db_path) as conn:
                # Load position to job profile mapping
                query = """
                SELECT DISTINCT Position_Number, JobProfileID 
                FROM core_position_timeline 
                WHERE Position_Number IS NOT NULL AND JobProfileID IS NOT NULL
                """
                position_to_jobprofile = dict(conn.execute(query).fetchall())
            
            # Create enriched DataFrame with database schema
            enriched_data = []
            
            for _, row in movement_facts_df.iterrows():
                # Use the existing movement_pattern_id from MovementFactBuilder (don't regenerate)
                movement_pattern_id = row.get('movement_pattern_id')
                
                # Map positions to job profile IDs (convert strings to integers for lookup)
                try:
                    from_position = row.get('from_position')
                    to_position = row.get('to_position')
                    
                    if from_position is not None and to_position is not None:
                        from_position_int = int(from_position)
                        to_position_int = int(to_position)
                        from_job_profile_id = position_to_jobprofile.get(from_position_int)
                        to_job_profile_id = position_to_jobprofile.get(to_position_int)
                    else:
                        from_job_profile_id = None
                        to_job_profile_id = None
                except (ValueError, TypeError):
                    # Handle non-numeric position identifiers (PosIDLookupKeys)
                    from_job_profile_id = None
                    to_job_profile_id = None
                
                enriched_data.append({
                    'movement_pattern_id': movement_pattern_id,
                    'movement_month': row.get('movement_month'),
                    'from_position': str(row.get('from_position')),
                    'to_position': str(row.get('to_position')),
                    'from_job_profile_id': from_job_profile_id,
                    'to_job_profile_id': to_job_profile_id,
                    'movement_count': row.get('movement_count', 0),
                    'unique_employees': row.get('unique_employees', 0),
                    'avg_days_between': row.get('avg_days_between', 0.0),
                    'pct_total_movements': row.get('pct_total_movements', 0.0),
                    'movement_type': row.get('movement_type', 'lateral'),  # Use from MovementFactBuilder
                    'skill_similarity_score': row.get('skill_similarity_score'),  # Use from MovementFactBuilder
                    'difficulty_score': row.get('difficulty_score'),  # Use from MovementFactBuilder
                    'success_rate': row.get('success_rate'),  # Use from MovementFactBuilder
                    'created_timestamp': pd.Timestamp.now().isoformat()
                })
            
            return pd.DataFrame(enriched_data)
            
        except Exception as e:
            print(f"❌ Failed to enrich with job profile IDs: {e}")
            print("   Check job architecture data availability.")
            return movement_facts_df


class MovementMLTrainingCommand(BaseCommand):
    """
    Command for training ML models from populated movement patterns data.
    
    This command implements Phase 2.2 of the movement analysis pipeline:
    - Loads movement patterns from analytics_movement_patterns table
    - Engineers ML features from job architecture and movement data
    - Trains ensemble models (Random Forest, XGBoost, Gradient Boosting)
    - Generates pathway predictions and saves to database
    - Saves trained models as .joblib files for webapp consumption
    """
    
    def __init__(self):
        super().__init__(
            name="movement_ml_training",
            description="Train ML models for career pathway prediction from movement patterns"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for ML training."""
        # Check database path
        db_path = kwargs.get('db_path')
        if not db_path:
            return CommandResult(
                success=False,
                message="Database path is required",
                errors=["Missing 'db_path' argument"]
            )
        
        if not Path(db_path).exists():
            return CommandResult(
                success=False,
                message=f"Database file not found: {db_path}",
                errors=[f"Database file does not exist: {db_path}"]
            )
        
        # Check if movement patterns table has data
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM analytics_movement_patterns")
                count = cursor.fetchone()[0]
                
                if count == 0:
                    return CommandResult(
                        success=False,
                        message="No movement patterns found in database",
                        errors=["analytics_movement_patterns table is empty - run movement pattern population first"]
                    )
                
                print(f"🤖 Found {count:,} movement patterns ready for ML training")
        
        except sqlite3.Error as e:
            return CommandResult(
                success=False,
                message=f"Database validation failed: {e}",
                errors=[f"Cannot access analytics_movement_patterns table: {e}"]
            )
        
        return CommandResult(success=True, message="Arguments validated successfully")
    
    def execute(self, **kwargs) -> CommandResult:
        """Execute ML model training pipeline."""
        try:
            print("🚀 Starting Phase 2.2: ML Model Training")
            
            # Get database path
            db_path = Path(kwargs['db_path'])
            
            # Setup output directory for models
            version_manager = ModelVersionManager()
            output_dir = version_manager.setup_output_directory(
                output_type='business_context',
                interactive=kwargs.get('interactive', True)
            )
            
            # Import ML trainer
            from ...models.movement_ml_trainer import MovementMLTrainer
            
            # Initialize trainer
            trainer = MovementMLTrainer(db_path=db_path)
            
            # Execute full ML pipeline
            print("🔧 Executing complete ML training pipeline...")
            results = trainer.execute_full_ml_pipeline(output_dir=output_dir)
            
            if not results['success']:
                return CommandResult(
                    success=False,
                    message=f"ML training failed: {results.get('error', 'Unknown error')}",
                    errors=[results.get('error', 'ML training pipeline failed')]
                )
            
            # Extract results
            predictions_df = results['predictions_df']
            model_results = results['model_results']
            best_model_name = results['best_model_name']
            performance_metrics = results['performance_metrics']
            saved_files = results['saved_files']
            
            print("✅ ML training completed successfully:")
            print(f"   • Best model: {best_model_name}")
            print(f"   • R² score: {performance_metrics['best_model_r2']:.3f}")
            print(f"   • Average error: {performance_metrics['best_model_mae']:.1f} movements")
            print(f"   • Total predictions: {performance_metrics['total_predictions']:,}")
            print(f"   • Models saved to: {output_dir}")
            
            return CommandResult(
                success=True,
                message=f"ML training completed - {performance_metrics['total_predictions']:,} predictions generated",
                data={
                    'predictions_df': predictions_df,
                    'model_results': model_results,
                    'best_model_name': best_model_name,
                    'performance_metrics': performance_metrics,
                    'output_directory': str(output_dir),
                    'saved_files': {str(k): str(v) for k, v in saved_files.items()}
                },
                metadata={
                    'algorithm_type': 'ensemble_ml_v1.0',
                    'model_count': len(model_results),
                    'feature_count': performance_metrics['feature_count'],
                    'training_timestamp': pd.Timestamp.now().isoformat()
                }
            )
            
        except Exception as e:
            print(f"❌ ML training command failed: {e}")
            print("   Check your training data and model configuration.")
            return CommandResult(
                success=False,
                message=f"ML training failed: {str(e)}",
                errors=[str(e)]
            )


class SkillsOptimizationCommand(BaseCommand):
    """
    Command for optimizing skills clustering parameters across multiple algorithms.
    
    Tests DBSCAN, Hierarchical, and K-means clustering across Jaccard, Cosine,
    and Combined similarity measures with taxonomy alignment validation.
    """
    
    def __init__(self):
        super().__init__(
            name="skills_optimization",
            description="Optimize skills clustering parameters with multiple similarity measures and algorithms"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for skills optimization."""
        return CommandResult(
            success=True,
            message="Skills optimization arguments validated"
        )
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute skills clustering parameter optimization.
        
        Returns:
            CommandResult with optimization status and results
        """
        try:
            print("\n🔗 Skills Clustering Parameter Optimization")
            print("="*50)
            print("📊 This will analyze your skills data to find optimal clustering parameters")
            print("   • DBSCAN parameters (eps/min_samples)")
            print("   • Hierarchical clustering (n_clusters/linkage)")
            print("   • K-means parameters (n_clusters)")
            print("   • Multiple similarity measures (Jaccard, Cosine, Combined)")
            print("   • Taxonomy alignment validation")
            print()
            
            # Get database path from kwargs or use default
            db_path = kwargs.get('db_path')
            if not db_path:
                # Fallback to default path
                db_path = "models/2025-Q3/business_context.sqlite"
            
            # Verify database exists
            if not Path(db_path).exists():
                return CommandResult(
                    success=False,
                    message=f"Database not found: {db_path}",
                    errors=[f"Database file not found at {db_path}"]
                )
            
            print(f"📂 Database: {db_path}")
            print()
            
            # Import and run skills optimization
            from ...models.clustering_optimizer import SkillsParameterOptimizer
            
            print("🔍 Initializing skills parameter optimizer...")
            optimizer = SkillsParameterOptimizer(db_path)
            
            print("📊 Starting comprehensive parameter analysis...")
            print("   • Loading skills co-occurrence data")
            print("   • Creating multiple similarity matrices")
            print("   • Testing algorithm combinations")
            print("   • Calculating taxonomy alignment scores")
            print()
            
            # Run optimization
            results = optimizer.optimize_skills_parameters()
            
            if results:
                # Save skills configuration to separate YAML file
                print("💾 Saving skills clustering configuration...")
                save_success = optimizer.save_skills_configuration(results)
                if save_success:
                    print("✅ Configuration saved to config/core/skills_clustering.yaml")
                else:
                    print("⚠️  Warning: Failed to save configuration file")
                
                print()
                print("✅ Skills parameter optimization completed successfully!")
                print(f"   • Best Algorithm: {results.get('algorithm', 'Unknown')}")
                print(f"   • Best Similarity Method: {results.get('similarity_method', 'Unknown')}")
                print(f"   • Silhouette Score: {results.get('silhouette_score', 0):.3f}")
                print(f"   • Taxonomy Alignment: {results.get('taxonomy_alignment', 0):.3f}")
                print(f"   • Combined Score: {results.get('combined_score', 0):.3f}")
                
                if results['algorithm'] == 'dbscan':
                    print(f"   • Optimal eps: {results.get('eps', 'N/A')}")
                    print(f"   • Optimal min_samples: {results.get('min_samples', 'N/A')}")
                    print(f"   • Expected clusters: {results.get('n_clusters', 'N/A')}")
                    print(f"   • Noise ratio: {results.get('noise_ratio', 0):.1%}")
                elif results['algorithm'] == 'hierarchical':
                    print(f"   • Optimal clusters: {results.get('n_clusters', 'N/A')}")
                    print(f"   • Optimal linkage: {results.get('linkage', 'N/A')}")
                elif results['algorithm'] == 'kmeans':
                    print(f"   • Optimal clusters: {results.get('n_clusters', 'N/A')}")
                
                return CommandResult(
                    success=True,
                    message="Skills clustering parameters optimized successfully",
                    data={'optimization_results': results}
                )
            else:
                return CommandResult(
                    success=False,
                    message="Skills parameter optimization failed to find optimal parameters",
                    errors=["No valid clustering configurations found"]
                )
                
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Skills optimization failed: {str(e)}",
                errors=[str(e)]
            )


class ClusteringOptimizationCommand(BaseCommand):
    """
    Command for optimizing clustering parameters using systematic analysis.
    
    Performs silhouette analysis, elbow method, and stability assessment
    to find optimal DBSCAN parameters for job profile clustering.
    Updates configuration files automatically with optimized parameters.
    """
    
    def __init__(self):
        super().__init__(
            name="clustering_optimization",
            description="Optimize clustering parameters using Bayesian analysis and update configuration"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for clustering optimization."""
        return CommandResult(
            success=True,
            message="Clustering optimization arguments validated"
        )
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute clustering parameter optimization.
        
        Returns:
            CommandResult with optimization status and results
        """
        try:
            print("\n🎯 Clustering Parameter Optimization")
            print("="*50)
            print("📊 This will analyze your data to find optimal clustering parameters")
            print("   • Job profile clustering (DBSCAN eps/min_samples)")
            print("   • Skills clustering and bundling parameters")
            print("   • Silhouette analysis across parameter ranges")
            print("   • Elbow method validation")
            print()
            
            # Import clustering optimizer
            from ...models.clustering_optimizer import ClusteringParameterOptimizer
            
            if not ClusteringParameterOptimizer.is_available():
                print("❌ Clustering optimization not available.")
                print("   Required dependencies may be missing.")
                return CommandResult(
                    success=False,
                    message="Clustering optimization dependencies not available",
                    errors=["Missing scikit-learn or related dependencies"]
                )
            
            # Get database path
            from ...config.architectural_config_manager import get_config_manager
            config_manager = get_config_manager()
            
            # Try to get database path from config or use default
            try:
                db_config = config_manager.get_nested_value('database', 'paths')
                if db_config and 'business_context' in db_config:
                    db_path = db_config['business_context']
                else:
                    # Fallback to default path
                    db_path = "models/2025-Q3/business_context.sqlite"
            except:
                db_path = "models/2025-Q3/business_context.sqlite"
            
            print(f"📂 Database: {db_path}")
            print()
            
            # Confirm with user since this overwrites config
            print("⚠️  This will update config/core/clustering_analysis.yaml")
            print("   with optimized parameters based on your data analysis.")
            
            if not kwargs.get('auto_confirm', False):
                confirm = input("   Continue? (y/N): ").strip().lower()
                if confirm != 'y':
                    print("   Optimization cancelled.")
                    return CommandResult(
                        success=False,
                        message="Optimization cancelled by user"
                    )
            
            # Run optimization
            print("🔍 Initializing clustering parameter optimizer...")
            optimizer = ClusteringParameterOptimizer(db_path)
            
            print("📊 Starting parameter analysis...")
            print("   • Loading job similarity data")
            print("   • Testing DBSCAN parameter combinations")
            print("   • Calculating silhouette scores")
            print("   • Performing elbow method analysis")
            print()
            
            success = optimizer.optimize_and_update()
            
            if success:
                # Reload configuration to pick up new parameters
                config_manager.reload_configuration()
                
                print("✅ Clustering parameter optimization completed successfully!")
                print()
                print("📋 Next Steps:")
                print("   1. Review the updated configuration file")
                print("   2. Run 'Strategic Clustering Analytics' to apply optimized parameters")
                print("   3. Validate clustering results in your database")
                print()
                
                return CommandResult(
                    success=True,
                    message="Clustering parameters optimized successfully",
                    metadata={
                        'config_updated': True,
                        'database_path': db_path
                    }
                )
            else:
                print("❌ Clustering parameter optimization failed.")
                print("   Check your database and ensure job similarity data exists.")
                return CommandResult(
                    success=False,
                    message="Clustering parameter optimization failed",
                    errors=["Optimization process failed - check logs for details"]
                )
                
        except Exception as e:
            print(f"❌ Clustering optimization command failed: {e}")
            print("   Check your database and configuration.")
            return CommandResult(
                success=False,
                message=f"Clustering optimization failed: {str(e)}",
                errors=[str(e)]
            )


class ClusteringAnalysisCommand(BaseCommand):
    """
    Command for executing production clustering analysis.
    
    Performs job profile clustering, skills bundling, and velocity analysis
    using optimized parameters from configuration. Populates database tables
    with comprehensive clustering intelligence.
    """
    
    def __init__(self):
        super().__init__(
            name="clustering_analysis", 
            description="Execute production clustering analysis and populate database tables"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for clustering analysis."""
        return CommandResult(
            success=True,
            message="Clustering analysis arguments validated"
        )
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute comprehensive clustering analysis.
        
        Returns:
            CommandResult with analysis status and results
        """
        try:
            print("\n🧩 Production Clustering Analytics")
            print("="*50)
            print("📊 Comprehensive clustering analysis for strategic intelligence:")
            print("   • Job Families: DBSCAN clustering of job profiles with business naming")
            print("   • Skill Bundles: DBSCAN clustering of skills with specialization detection")
            print("   • Cluster quality metrics and validation")
            print("   • Database population with clustering results")
            print()
            
            # Import clustering analyzer
            from ...models.clustering_analyzer import ClusteringAnalyzer
            from ...config.architectural_config_manager import get_config_manager
            
            config_manager = get_config_manager()
            
            # Get database path
            try:
                db_config = config_manager.get_nested_value('database', 'paths')
                if db_config and 'business_context' in db_config:
                    db_path = db_config['business_context']
                else:
                    db_path = "models/2025-Q3/business_context.sqlite"
            except:
                db_path = "models/2025-Q3/business_context.sqlite"
            
            print(f"📂 Database: {db_path}")
            
            # Check if clustering configuration exists
            clustering_config = config_manager.get_nested_value('core', 'clustering_analysis')
            if not clustering_config:
                print("⚠️  No clustering configuration found.")
                print("   Run 'Optimize Clustering Parameters' first to generate optimal parameters.")
                print("   Proceeding with default parameters...")
            else:
                print("✅ Using optimized clustering parameters from configuration")
            
            print()
            
            # Initialize clustering analyzer
            print("🔧 Initializing clustering analyzer...")
            analyzer = ClusteringAnalyzer(config_manager)
            
            print("📊 Executing clustering analysis...")
            print("   • Job profile clustering (DBSCAN)")
            print("   • Skills clustering and bundling")
            print("   • Business context generation")
            print("   • Quality metrics calculation")
            
            # Execute clustering analysis
            clustering_result = analyzer.execute_clustering_analysis(db_path)
            
            print()
            print("💾 Populating database tables...")
            
            # Import database integrator for clustering results
            from ...business_context.database_integrator import DatabaseIntegrator
            from pathlib import Path
            
            db_integrator = DatabaseIntegrator(Path(db_path))
            
            # Populate clustering tables
            success = self._populate_clustering_tables(db_integrator, clustering_result)
            
            if success:
                print("✅ Clustering analysis completed successfully!")
                print()
                print("📊 Results Summary:")
                metadata = clustering_result.metadata
                job_meta = metadata.get('job_clustering', {})
                skills_meta = metadata.get('skills_clustering', {})
                
                print(f"   • Job Clusters: {job_meta.get('n_clusters', 0)} clusters")
                print(f"   • Job Clustering Quality: {job_meta.get('quality_assessment', 'Unknown')}")
                print(f"   • Silhouette Score: {job_meta.get('silhouette_score', 0):.3f}")
                print(f"   • Skills Bundles: {skills_meta.get('n_bundles', 0)} bundles")
                print(f"   • Specialized Skills: {skills_meta.get('n_specialized', 0)} skills")
                print(f"   • Total Skills Processed: {skills_meta.get('total_skills', 0)}")
                print()
                
                return CommandResult(
                    success=True,
                    message="Clustering analysis completed successfully",
                    data=clustering_result.metadata,
                    metadata={
                        'database_path': db_path,
                        'job_clusters': job_meta.get('n_clusters', 0),
                        'skills_bundles': skills_meta.get('n_bundles', 0),
                        'specialized_skills': skills_meta.get('n_specialized', 0)
                    }
                )
            else:
                print("❌ Failed to populate clustering tables.")
                return CommandResult(
                    success=False,
                    message="Clustering analysis completed but database population failed",
                    errors=["Database population failed"]
                )
                
        except Exception as e:
            print(f"❌ Clustering analysis command failed: {e}")
            print("   Check your database and configuration.")
            return CommandResult(
                success=False,
                message=f"Clustering analysis failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _populate_clustering_tables(self, db_integrator, clustering_result) -> bool:
        """Populate database tables with clustering results."""
        try:
            print("   📊 Populating clustering analytics tables...")
            
            # Populate job families table
            print("     • Job families (cluster assignments)...")
            
            # Filter DataFrame to match database schema
            job_families_df = clustering_result.job_clusters_df.copy()
            
            # Map DataFrame columns to database schema columns
            schema_columns = [
                'job_profile_id', 'job_profile', 'job_function', 'job_sub_function', 
                'job_category', 'management_level', 'cluster_id', 'cluster_name', 
                'cluster_description', 'cluster_rationale', 'cluster_size', 
                'sample_jobs', 'sample_skills', 'cluster_confidence', 'silhouette_score',
                'intra_cluster_similarity', 'inter_cluster_distance', 'clustering_algorithm', 
                'algorithm_parameters', 'analysis_date', 'created_timestamp'
            ]
            
            # Rename columns to match schema
            column_mapping = {
                'JobProfileID': 'job_profile_id',
                'JobProfile': 'job_profile', 
                'JobFunction': 'job_function',
                'JobSubFunction': 'job_sub_function',
                'JobCategory': 'job_category',
                'ManagementLevel': 'management_level'
            }
            
            # Apply column mapping
            job_families_df = job_families_df.rename(columns=column_mapping)
            
            # Select only schema columns that exist in the DataFrame
            available_columns = [col for col in schema_columns if col in job_families_df.columns]
            job_families_df = job_families_df[available_columns]
            
            job_success = db_integrator.populate_job_families(job_families_df)
            if not job_success:
                print("     ❌ Failed to populate job families")
                return False
            
            # Populate skill bundles table
            print("     • Skill bundles (cluster assignments)...")
            bundles_success = db_integrator.populate_skill_bundles(clustering_result.skill_bundles_df)
            if not bundles_success:
                print("     ❌ Failed to populate skill bundles")
                return False
            
            # Populate bundle characteristics table
            print("     • Bundle characteristics (cluster metadata)...")
            chars_success = db_integrator.populate_bundle_characteristics(clustering_result.skill_characteristics_df)
            if not chars_success:
                print("     ❌ Failed to populate bundle characteristics")
                return False
            
            # Populate specialized skills table (if available)
            if hasattr(clustering_result, 'specialized_skills_df') and clustering_result.specialized_skills_df is not None:
                print("     • Specialized skills...")
                specialized_success = db_integrator.populate_specialized_skills(clustering_result.specialized_skills_df)
                if not specialized_success:
                    print("     ⚠️ Failed to populate specialized skills (non-critical)")
            
            print("   ✅ All clustering tables populated successfully")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to populate clustering tables: {e}")
            return False


class VelocityAnalysisCommand(BaseCommand):
    """
    Command for executing skill velocity analysis.
    
    Analyzes skill demand trends over time using CAGR calculations
    and categorizes skills by velocity patterns for strategic planning.
    """
    
    def __init__(self):
        super().__init__(
            name="velocity_analysis",
            description="Execute skill velocity analysis and trend categorization"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for velocity analysis."""
        return CommandResult(
            success=True,
            message="Velocity analysis arguments validated"
        )
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute skill velocity analysis.
        
        Returns:
            CommandResult with velocity analysis status and results
        """
        try:
            print("\n📈 Skill Velocity Analysis")
            print("="*50)
            print("🕒 Multi-timeframe skill demand trend analysis:")
            print("   • CAGR calculation (1, 2, 3 year timeframes)")
            print("   • Velocity categorization (accelerating, growing, stable, declining)")
            print("   • Recency-weighted growth metrics")
            print("   • Strategic trend intelligence")
            print()
            
            # Import and use the proper SkillVelocityAnalyzer
            from ...models.velocity_analyzer import SkillVelocityAnalyzer
            from ...config.architectural_config_manager import get_config_manager
            
            config_manager = get_config_manager()
            
            # Get database path
            try:
                db_config = config_manager.get_nested_value('database', 'paths')
                if db_config and 'business_context' in db_config:
                    db_path = db_config['business_context']
                else:
                    db_path = "models/2025-Q3/business_context.sqlite"
            except:
                db_path = "models/2025-Q3/business_context.sqlite"
            
            print(f"📂 Database: {db_path}")
            print()
            
            print("📊 Executing velocity analysis...")
            print("   • Loading skills with temporal demand data")
            print("   • Calculating multi-timeframe CAGR")
            print("   • Categorizing velocity patterns")
            print("   • Generating trend intelligence")
            print()
            
            # Initialize and run velocity analyzer
            analyzer = SkillVelocityAnalyzer(config_manager)
            velocity_result = analyzer.analyze_all_skills_velocity(db_path)
            
            velocity_df = velocity_result.velocity_df
            summary = velocity_result.velocity_summary
            
            if summary and velocity_df is not None:
                print("✅ Velocity analysis completed successfully!")
                print()
                print("📊 Results Summary:")
                
                print(f"   • Total Skills Analyzed: {summary.get('total_skills_analyzed', 0)}")
                
                categories = summary.get('velocity_categories', {})
                print(f"   • Accelerating Skills: {categories.get('accelerating', 0)}")
                print(f"   • Growing Skills: {categories.get('growing', 0)}")
                print(f"   • Stable Skills: {categories.get('stable', 0)}")
                print(f"   • Declining Skills: {categories.get('declining', 0)}")
                
                # Show top accelerating skills
                top_accelerating = summary.get('top_accelerating_skills', [])[:3]
                if top_accelerating:
                    print("   • Top Accelerating Skills:")
                    for skill in top_accelerating:
                        print(f"     - {skill.get('skill_name', 'Unknown')} ({skill.get('short_term_cagr', 0):.1%} CAGR)")
                
                print()
                
                return CommandResult(
                    success=True,
                    message="Velocity analysis completed successfully",
                    data=summary,
                    metadata={
                        'total_skills': summary.get('total_skills_analyzed', 0),
                        'velocity_categories': categories
                    }
                )
            else:
                print("❌ Velocity analysis returned no results.")
                return CommandResult(
                    success=False,
                    message="Velocity analysis completed but returned no results",
                    errors=["No velocity data returned"]
                )
                
        except Exception as e:
            print(f"❌ Velocity analysis command failed: {e}")
            print("   Check your database and ensure temporal data exists.")
            return CommandResult(
                success=False,
                message=f"Velocity analysis failed: {str(e)}",
                errors=[str(e)]
            )


class DiagnosticsAnalysisCommand(BaseCommand):
    """
    Command for executing job architecture health diagnostics.
    
    Analyzes job architecture structural integrity including role differentiation,
    duplicate detection, network analysis, and entropy metrics for strategic planning.
    """
    
    def __init__(self):
        super().__init__(
            name="diagnostics_analysis",
            description="Execute job architecture health diagnostics and governance analysis"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for diagnostics analysis."""
        return CommandResult(
            success=True,
            message="Diagnostics analysis arguments validated"
        )
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute job architecture health diagnostics.
        
        Returns:
            CommandResult with diagnostics analysis status and results
        """
        try:
            print("\n🏥 Job Architecture Health Diagnostics")
            print("="*50)
            print("🩺 Comprehensive architecture health evaluation:")
            print("   • Silhouette score analysis (role differentiation)")
            print("   • Near-duplicate role detection (similarity thresholds)")
            print("   • Network analysis (hub skills, communities)")
            print("   • Entropy analysis (role focus vs generality)")
            print("   • Executive summary with governance recommendations")
            print()
            
            # Import the modularized diagnostics analyzer
            from ...models.diagnostics_analyzer import analyze_job_architecture_health
            from ...config.architectural_config_manager import get_config_manager
            
            config_manager = get_config_manager()
            
            # Get database path
            try:
                db_config = config_manager.get_nested_value('database', 'paths')
                if db_config and 'business_context' in db_config:
                    db_path = db_config['business_context']
                else:
                    db_path = "models/2025-Q3/business_context.sqlite"
            except:
                db_path = "models/2025-Q3/business_context.sqlite"
            
            print(f"📂 Loading diagnostics from: {__file__.replace('precompute_commands.py', '../models/diagnostics_analyzer.py')}")
            print("📊 Executing diagnostics analysis...")
            print("   • Loading job architecture data")
            print("   • Calculating role differentiation metrics")
            print("   • Detecting near-duplicate roles")
            print("   • Analyzing skill network structure")
            print("   • Generating governance recommendations")
            print()
            
            # Execute diagnostics analysis
            results = analyze_job_architecture_health(db_path)
            
            if results:
                print("✅ Job architecture diagnostics completed successfully!")
                print()
                print("📊 Results Summary:")
                
                # Extract summary information from results
                summary = self._extract_summary(results)
                
                print(f"   • Total Roles Analyzed: {summary.get('total_roles_analyzed', 0)}")
                print(f"   • Near-Duplicate Pairs: {summary.get('near_duplicate_pairs', 0)}")
                print(f"   • Hub Skills Identified: {summary.get('hub_skills_count', 0)}")
                print(f"   • Communities Detected: {summary.get('communities_detected', 0)}")
                
                # Show key insights
                if summary.get('top_insights'):
                    print("   • Key Insights:")
                    for i, insight in enumerate(summary['top_insights'][:3], 1):
                        print(f"     {i}. {insight}")
                
                # Show governance recommendations
                if summary.get('governance_recommendations'):
                    print("   • Governance Recommendations:")
                    for i, rec in enumerate(summary['governance_recommendations'][:3], 1):
                        print(f"     {i}. {rec}")
                
                print()
                
                return CommandResult(
                    success=True,
                    message="Job architecture diagnostics completed successfully",
                    data=summary,
                    metadata={
                        'total_roles': summary.get('total_roles_analyzed', 0),
                        'duplicate_pairs': summary.get('near_duplicate_pairs', 0),
                        'communities': summary.get('communities_detected', 0)
                    }
                )
            else:
                print("❌ Diagnostics analysis returned no results.")
                return CommandResult(
                    success=False,
                    message="Diagnostics analysis completed but returned no results",
                    errors=["No diagnostics data returned"]
                )
                
        except Exception as e:
            print(f"❌ Diagnostics analysis command failed: {e}")
            print("   Check your database and ensure job architecture data exists.")
            return CommandResult(
                success=False,
                message=f"Diagnostics analysis failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _extract_summary(self, results) -> dict:
        """Extract summary information from diagnostics results."""
        try:
            # Default summary structure - the actual implementation will depend on 
            # what the diagnostics main() function returns
            summary = {
                'total_roles_analyzed': 0,
                'near_duplicate_pairs': 0,
                'hub_skills_count': 0,
                'communities_detected': 0,
                'top_insights': [],
                'governance_recommendations': []
            }
            
            # If results is a dictionary, extract values
            if isinstance(results, dict):
                summary.update({
                    'total_roles_analyzed': results.get('total_roles', 0),
                    'near_duplicate_pairs': results.get('duplicate_pairs', 0),
                    'hub_skills_count': results.get('hub_skills', 0),
                    'communities_detected': results.get('communities', 0),
                    'top_insights': results.get('insights', []),
                    'governance_recommendations': results.get('recommendations', [])
                })
            
            return summary
            
        except Exception as e:
            print(f"   ⚠️  Warning: Could not extract summary: {e}")
            return {
                'total_roles_analyzed': 'Unknown',
                'near_duplicate_pairs': 'Unknown',
                'hub_skills_count': 'Unknown',
                'communities_detected': 'Unknown',
                'top_insights': ['Analysis completed - check detailed output above'],
                'governance_recommendations': ['Review detailed diagnostics output for recommendations']
            }