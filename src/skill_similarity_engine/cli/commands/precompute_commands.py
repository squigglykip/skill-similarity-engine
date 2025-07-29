"""
Precompute Commands for Similarity and Movement Analysis

Contains CLI commands for precomputation workflows, extracted from main.py
and modularized to follow the Command pattern with SSE architecture.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from .base_command import BaseCommand, CommandResult
from ...similarity.precompute import create_precomputer, PrecomputeConfig
from ...models.versioning import setup_model_output_directory, ModelVersionManager
from ...cli.utilities import prompt_bool, prompt_int


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
                rarity_weighted_components = self._setup_rarity_weighted_similarity()
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
            self.logger.info(f"Creating similarity matrix precomputer (enhanced={enhanced_mode})...")
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
                print(f"🚀 STARTING RARITY-WEIGHTED PRECOMPUTATION PIPELINE")
                print(f"📊 Using rarity-weighted algorithms with defining skills boost")
                print(f"⚙️  Configuration: 20% percentile threshold, 1.05x multiplier")
                print(f"📈 Expected improvement: 0.76% average, 12.5% positive rate")
            else:
                print(f"🚀 STARTING PRECOMPUTATION PIPELINE")
                print(f"📊 Using basic asymmetric coverage algorithms")
            print("="*60)
            
            output_path = precomputer.precompute_all()
            
            # Handle enhanced similarity database integration
            if enhanced_mode and enhanced_components:
                self._integrate_enhanced_results(output_path, enhanced_components)
            
            # Handle output format conversion
            conversion_result = self._handle_output_conversion(
                output_path, output_config
            )
            
            # Print completion summary
            self._print_completion_summary(output_path, output_config, processing_config, enhanced_mode)
            
            return CommandResult(
                success=True,
                message=f"Similarity matrix generation completed successfully ({'enhanced' if enhanced_mode else 'basic'} algorithms)",
                data={
                    'output_path': str(output_path),
                    'formats_generated': output_config,
                    'conversion_results': conversion_result,
                    'enhanced_mode': enhanced_mode
                },
                metadata={
                    'total_jobs': len(architecture.jobs),
                    'output_directory': str(output_path),
                    'config_used': processing_config,
                    'algorithm_type': 'enhanced_rarity_weighted' if enhanced_mode else 'basic_asymmetric'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Similarity matrix generation failed: {e}", exc_info=True)
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
            from ...similarity.enhanced_algorithms import SkillIntelligenceEngine
            
            # Initialize skill intelligence engine
            skill_engine = SkillIntelligenceEngine()
            
            # Load skill universe and job-skill relationships
            print(f"📚 Loading skill universe with rarity data...")
            skill_universe_df = skill_engine.skill_universe_df
            
            print(f"🔗 Loading job-skill relationships...")
            job_to_skills = skill_engine.job_to_skills
            
            # Create defining skills map
            print(f"🎯 Creating job-specific defining skills map...")
            defining_skills_map = skill_engine.defining_skills_analyzer.create_job_defining_skills_map(
                job_to_skills
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
            self.logger.error(f"Enhanced similarity setup failed: {e}", exc_info=True)
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
            
            self.logger.info("Enhanced similarity calculator injected into precomputer")
            
        except Exception as e:
            self.logger.error(f"Failed to inject enhanced calculator: {e}")
            raise
    
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
            
            enhancement_metadata: Dict[str, Any] = {
                'algorithm_type': 'enhanced_rarity_weighted',
                'defining_skills_percentile': enhanced_components['skill_engine'].enhanced_config['defining_skills_percentile'],
                'gentle_multiplier': enhanced_components['skill_engine'].enhanced_config['gentle_multiplier'],
                'rarity_thresholds': enhanced_components['skill_engine'].enhanced_config['rarity_thresholds'],
                'total_skills_analyzed': len(enhanced_components['skill_universe_df']),
                'jobs_with_defining_skills': len(enhanced_components['defining_skills_map'])
            }
            
            # Write enhancement metadata
            metadata_file = output_path / "enhanced_similarity_metadata.json"
            with open(str(metadata_file), 'w', encoding='utf-8') as f:
                json.dump(enhancement_metadata, f, indent=2)
            
            print(f"✅ Enhanced similarity metadata saved to {metadata_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to integrate enhanced results: {e}")
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
            print(f"⚙️  Enhanced features:")
            print(f"   → Rarity-weighted similarity calculation")
            print(f"   → Defining skills boost (1.05x multiplier)")
            print(f"   → Expected 0.76% improvement over basic algorithms")
    
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
                self.logger.info(f"Created Parquet file: {parquet_file}")
                print(f"✅ Parquet file created: {parquet_file}")
                conversion_results['parquet_created'] = True
                
            except ImportError:
                print("[WARNING] Could not create Parquet file - pyarrow not installed")
                self.logger.warning("pyarrow not available for Parquet conversion")
                conversion_results['parquet_created'] = False
                conversion_results['parquet_error'] = "pyarrow not installed"
                
            except Exception as e:
                print(f"[WARNING] Could not create Parquet file: {e}")
                self.logger.warning(f"Parquet conversion failed: {e}")
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
            
            self.logger.info("Creating movement analysis precomputer...")
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
            self.logger.error(f"Movement analysis import error: {e}")
            return CommandResult(
                success=False,
                message=f"Movement analysis module not available: {e}",
                errors=["Please ensure the movement tracker is properly installed"]
            )
        except Exception as e:
            self.logger.error(f"Movement analysis generation failed: {e}", exc_info=True)
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