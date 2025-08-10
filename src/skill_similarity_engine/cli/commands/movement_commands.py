"""
Movement Commands for Analysis and Pattern Detection

Contains CLI commands for movement analysis workflows, extracted from precompute_commands.py
and focused on workforce movement detection, pattern population, and ML training.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import sqlite3
import pandas as pd
import time

from .base_command import BaseCommand, CommandResult
from ...models.versioning import ModelVersionManager
from ...cli.utilities import prompt_bool, prompt_int
from ...utils.chunking import ChunkingStrategy


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
        from ...utils.progress import ProgressTracker
        from ...utils.chunking import AdaptiveChunker, ChunkingStrategy
        from ...utils.performance import get_memory_usage
        from ...models.movement_tracker import MovementTracker
        from ...models.movement_fact_builder import MovementFactBuilder
        from ...business_context.database_integrator import DatabaseIntegrator
        
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
