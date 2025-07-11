"""
Precompute Commands for Similarity and Movement Analysis

Contains CLI commands for precomputation workflows, extracted from main.py
and modularized to follow the Command pattern with SSE architecture.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from .base_command import BaseCommand, CommandResult
from ...similarity.precompute import create_precomputer, PrecomputeConfig
from ...models.versioning import setup_model_output_directory
from ...cli.utilities import prompt_bool, prompt_int


class SimilarityMatrixCommand(BaseCommand):
    """
    Command for generating similarity matrices and career pathways.
    
    Extracted from main.py generate_similarity_matrix function with enhanced
    modularity and configuration management.
    """
    
    def __init__(self):
        super().__init__(
            name="similarity_matrix",
            description="Generate job similarity matrix and career pathways"
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
            
            # Print header
            self._print_header(architecture)
            
            # Setup output directory
            quarter_dir = setup_model_output_directory()
            print(f"✅ Output directory ready: {quarter_dir}")
            
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
                output_dir=str(quarter_dir)
            )
            
            # Create precomputer
            self.logger.info("Creating similarity matrix precomputer...")
            precomputer = create_precomputer(
                job_architecture=architecture,
                config=config
            )
            
            # Show runtime estimate if requested
            if processing_config['estimate_runtime']:
                estimate_result = self._show_runtime_estimates(precomputer)
                if not estimate_result:
                    return CommandResult(
                        success=False,
                        message="Operation cancelled by user",
                        errors=["User chose not to proceed after seeing estimates"]
                    )
            
            # Generate similarity matrix and career pathways
            print(f"\n" + "="*60)
            print(f"🚀 STARTING PRECOMPUTATION PIPELINE")
            print("="*60)
            
            output_path = precomputer.precompute_all()
            
            # Handle output format conversion
            conversion_result = self._handle_output_conversion(
                output_path, output_config
            )
            
            # Print completion summary
            self._print_completion_summary(output_path, output_config, processing_config)
            
            return CommandResult(
                success=True,
                message="Similarity matrix generation completed successfully",
                data={
                    'output_path': str(output_path),
                    'formats_generated': output_config,
                    'conversion_results': conversion_result
                },
                metadata={
                    'total_jobs': len(architecture.jobs),
                    'output_directory': str(quarter_dir),
                    'config_used': processing_config
                }
            )
            
        except Exception as e:
            self.logger.error(f"Similarity matrix generation failed: {e}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Similarity matrix generation failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _print_header(self, architecture):
        """Print the similarity matrix generation header."""
        print(f"\n" + "="*60)
        print(f"🔄 SIMILARITY MATRIX GENERATION")
        print("="*60)
        print(f"📊 Jobs to process: {len(architecture.jobs):,}")
    
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
    
    def _show_runtime_estimates(self, precomputer) -> bool:
        """Show runtime estimates and get user confirmation."""
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
        
        estimated_parquet_size = estimated_csv_size * 0.1  # Parquet typically 10x smaller than CSV
        print(f"📁 Expected Parquet size: ~{estimated_parquet_size:.1f} GB")
        print("-"*50)
        
        from ...cli.utilities import prompt_bool
        return prompt_bool("🚀 Proceed with similarity matrix generation?", default=True)
    
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
    
    def _print_completion_summary(self, output_path: Path, output_config: Dict[str, bool], processing_config: Dict[str, Any]):
        """Print the completion summary."""
        print(f"\n" + "="*60)
        print(f"✅ GENERATION COMPLETE!")
        print("="*60)
        print(f"📁 Output directory: {output_path}")
        
        if output_config['parquet'] and (output_path / "job_similarity_matrix.parquet").exists():
            print(f"📦 Parquet file: job_similarity_matrix.parquet")
        if output_config['csv'] and (output_path / "job_similarity_matrix.csv").exists():
            print(f"📄 CSV file: job_similarity_matrix.csv")
        print(f"📋 Metadata: metadata.json")
        if processing_config['enable_checkpoints']:
            print(f"💾 Checkpoint file: checkpoint.json")
        
        print("="*60)
        print("🎉 Similarity matrix and career pathways ready!")
        print("="*60)


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