"""
Movement Analysis Data Integrator for Business Context Database

PURE INGESTION SERVICE: This module ONLY loads pre-computed parquet files into SQLite database.
It should perform NO calculations, NO data processing, NO enrichment during database creation.

The workflow is:
1. Precompute Phase (main.py → option 1): Generate all .parquet files with calculations
2. Database Creation Phase (main.py → option 2): Ingest .parquet files into SQLite (THIS MODULE)

This module handles the loading of:
- colleague movements (from employee_movements.parquet)
- movement fact table (from movement_fact_table.parquet) 
- position history (from pre-computed files only)
- workforce context (from pre-computed files only)
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd

from ..models.versioning import ModelVersionManager
from ..models.position_history_generator import PositionHistoryGenerator
from ..config.architectural_config_manager import ArchitecturalConfigManager
from ..utils.progress import ProgressTracker, progress_context

logger = logging.getLogger(__name__)


class MovementIntegrator:
    """Integrates movement analysis data from parquet files into SQLite database."""
    
    def __init__(self, db_path: str):
        """
        Initialize movement integrator.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.version_manager = ModelVersionManager()
        self.config = ArchitecturalConfigManager()
        self.position_history_generator = PositionHistoryGenerator(self.config)
        
    def integrate_movement_data(self, chunk_size: int = 10000) -> bool:
        """
        Load movement analysis data from most recent parquet files into database.
        
        Args:
            chunk_size: Number of rows to process at once
            
        Returns:
            True if integration successful
        """
        try:
            logger.info("Starting movement analysis data integration...")
            
            # Find the most recent movement analysis output directory
            movement_dir = self._find_latest_movement_directory()
            if not movement_dir:
                logger.error("No movement analysis data found")
                return False
            
            logger.info(f"Using movement data from: {movement_dir}")
            
            # Load each movement analysis file
            success = True
            
            # Load employee movements
            employee_movements_file = movement_dir / "employee_movements.parquet"
            if employee_movements_file.exists():
                success &= self._load_employee_movements(employee_movements_file, chunk_size)
            else:
                logger.warning("Employee movements file not found")
            
            # Load movement summary (position-month aggregations)
            movement_summary_file = movement_dir / "movement_summary.parquet"
            if movement_summary_file.exists():
                success &= self._load_movement_summary(movement_summary_file, chunk_size)
            else:
                logger.warning("Movement summary file not found")
            
            # Load movement fact table (rich movement aggregation)
            fact_table_file = movement_dir / "movement_fact_table.parquet"
            if fact_table_file.exists():
                success &= self._load_movement_fact_table(fact_table_file, chunk_size)
            else:
                logger.warning("Movement fact table file not found")
            
            # Load metadata if available
            metadata_file = movement_dir / "metadata.json"
            if metadata_file.exists():
                success &= self._load_movement_metadata(metadata_file)
            
            logger.info("Movement analysis data integration completed")
            return success
            
        except Exception as e:
            logger.error(f"Movement data integration failed: {e}")
            return False
    
    def _find_latest_movement_directory(self) -> Optional[Path]:
        """Find the most recent movement analysis output directory."""
        try:
            # Look for models directory in the current working directory
            models_dir = Path("models")
            if not models_dir.exists():
                logger.error("Models directory not found")
                return None
            
            # Find the latest quarter directory
            quarter_dirs = [d for d in models_dir.iterdir() if d.is_dir() and d.name.startswith('2025-Q')]
            if not quarter_dirs:
                logger.error("No quarter directories found")
                return None
            
            latest_quarter = max(quarter_dirs, key=lambda d: d.name)
            
            # Look for daily folders with movement analysis data
            daily_dirs = []
            for daily_dir in latest_quarter.iterdir():
                if daily_dir.is_dir() and daily_dir.name.startswith('2025-'):
                    # Check if this directory contains movement analysis files
                    if (daily_dir / "employee_movements.parquet").exists():
                        daily_dirs.append(daily_dir)
            
            if not daily_dirs:
                logger.error("No movement analysis directories found")
                return None
            
            # Return the most recent directory
            latest_dir = max(daily_dirs, key=lambda d: d.name)
            logger.info(f"Found latest movement analysis directory: {latest_dir}")
            return latest_dir
            
        except Exception as e:
            logger.error(f"Error finding movement directory: {e}")
            return None
    
    def _load_employee_movements(self, parquet_file: Path, chunk_size: int) -> bool:
        """Load employee movements from parquet file into colleague_movements table."""
        try:
            logger.info(f"Loading employee movements from {parquet_file}")
            
            # Read parquet file
            df = pd.read_parquet(parquet_file)
            logger.info(f"Loaded {len(df):,} movement records")
            
            # Transform data to match database schema
            df_transformed = self._transform_employee_movements(df)
            
            # Load into database
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM colleague_movements")
                
                # Insert new data in chunks
                logger.info(f"Loading {len(df_transformed):,} movement records...")
                if len(df_transformed) > chunk_size:
                    df_transformed.to_sql('colleague_movements', conn, if_exists='append', 
                                        index=False, chunksize=chunk_size)
                else:
                    df_transformed.to_sql('colleague_movements', conn, if_exists='append', 
                                        index=False)
                
                # Get final row count
                cursor = conn.execute("SELECT COUNT(*) FROM colleague_movements")
                row_count = cursor.fetchone()[0]
                logger.info(f"Loaded {row_count:,} movement records into database")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load employee movements: {e}")
            return False
    
    def _load_movement_summary(self, parquet_file: Path, chunk_size: int) -> bool:
        """Load movement summary from parquet file into position_history table."""
        try:
            logger.info(f"Loading movement summary from {parquet_file}")
            
            # Read parquet file
            df = pd.read_parquet(parquet_file)
            logger.info(f"Loaded {len(df):,} summary records")
            
            # Check if this is the high-level summary file (only 1 row with statistics)
            if len(df) == 1 and 'total_movements' in df.columns:
                logger.info("Detected high-level summary file - skipping position history generation (database creation should only ingest pre-computed files)")
                logger.info("Note: If position history is needed, run the movement analysis precompute step first")
                return True  # Skip position history generation during database creation
            
            # Transform data to match database schema
            df_transformed = self._transform_movement_summary(df)
            
            # Load into database
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM position_history")
                
                # Insert new data in chunks
                logger.info(f"Loading {len(df_transformed):,} summary records...")
                if len(df_transformed) > chunk_size:
                    df_transformed.to_sql('position_history', conn, if_exists='append', 
                                        index=False, chunksize=chunk_size)
                else:
                    df_transformed.to_sql('position_history', conn, if_exists='append', 
                                        index=False)
                
                # Get final row count
                cursor = conn.execute("SELECT COUNT(*) FROM position_history")
                row_count = cursor.fetchone()[0]
                logger.info(f"Loaded {row_count:,} summary records into database")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load movement summary: {e}")
            return False
    
    def _generate_position_history_from_movements(self, chunk_size: int) -> bool:
        """
        DEPRECATED: This method should not be called during database creation.
        Position history should be pre-computed during movement analysis phase.
        """
        logger.warning("_generate_position_history_from_movements() called during database creation")
        logger.warning("This method is deprecated for database creation workflow")
        logger.warning("Position history should be pre-computed during movement analysis (main.py → option 1 → option 3)")
        return True  # Return success to avoid breaking the workflow
    
    def _generate_position_history_from_available_data(self, 
                                                     movements_df: pd.DataFrame,
                                                     colleague_positions_file: Path,
                                                     positions_schema_file: Path) -> pd.DataFrame:
        """Generate position history using available data files for enrichment."""
        try:
            logger.info("Loading colleague positions and schema data for enrichment...")
            
            # Load colleague positions data
            df_colleagues = pd.read_csv(colleague_positions_file, low_memory=False)
            logger.info(f"Loaded {len(df_colleagues):,} colleague position records")
            
            # Load positions schema data
            df_positions = pd.read_csv(positions_schema_file, low_memory=False)
            logger.info(f"Loaded {len(df_positions):,} position schema records")
            
            # Create position history records from movements with enrichment
            position_history_records = []
            
            for _, movement in movements_df.iterrows():
                employee_number = str(movement['employee_number'])
                to_position = str(movement['to_position'])
                to_date = movement.get('to_date')
                
                # Create position history record
                record = {
                    'employee_number': employee_number,
                    'position_number': to_position,
                    'effective_date': pd.to_datetime(to_date).date() if pd.notna(to_date) else None,
                    'end_date': None,  # Will be set by next movement
                    'jobprofile_id': to_position,  # Use position as job profile ID
                    'position_title': '',
                    'organisational_unit': '',
                    'cost_centre_number': None,
                    'people_leader_number': None,
                    'change_type': 'Position Assignment',
                    'data_source': 'Movement Integration'
                }
                
                position_history_records.append(record)
            
            # Convert to DataFrame
            df_position_history = pd.DataFrame(position_history_records)
            
            # Sort by employee and date
            df_position_history = df_position_history.sort_values(['employee_number', 'effective_date'])
            
            # Set end dates based on next movements
            for employee_number in df_position_history['employee_number'].unique():
                employee_records = df_position_history[df_position_history['employee_number'] == employee_number]
                for i in range(len(employee_records) - 1):
                    idx = employee_records.index[i]
                    next_idx = employee_records.index[i + 1]
                    df_position_history.loc[idx, 'end_date'] = df_position_history.loc[next_idx, 'effective_date']
            
            logger.info(f"Generated {len(df_position_history):,} position history records from available data")
            return df_position_history
            
        except Exception as e:
            logger.error(f"Failed to generate position history from available data: {e}")
            # Fallback to basic generation
            return self.position_history_generator.generate_position_history_from_movements(movements_df, None)
    
    def _load_movement_fact_table(self, parquet_file: Path, chunk_size: int) -> bool:
        """Load movement fact table from parquet file into movement_fact_table table."""
        try:
            logger.info(f"Loading movement fact table from {parquet_file}")
            
            # Read parquet file
            df = pd.read_parquet(parquet_file)
            logger.info(f"Loaded {len(df):,} fact table records")
            
            # Transform data to match database schema
            df_transformed = self._transform_movement_fact_table(df)
            
            # Load into database
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM movement_fact")
                
                # Insert new data in chunks
                logger.info(f"Loading {len(df_transformed):,} fact table records...")
                if len(df_transformed) > chunk_size:
                    df_transformed.to_sql('movement_fact', conn, if_exists='append', 
                                        index=False, chunksize=chunk_size)
                else:
                    df_transformed.to_sql('movement_fact', conn, if_exists='append', 
                                        index=False)
                
                # Get final row count
                cursor = conn.execute("SELECT COUNT(*) FROM movement_fact")
                row_count = cursor.fetchone()[0]
                logger.info(f"Loaded {row_count:,} fact table records into database")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load movement fact table: {e}")
            return False
    
    def _load_movement_metadata(self, metadata_file: Path) -> bool:
        """Load movement analysis metadata into workforce_context table."""
        try:
            logger.info(f"Loading movement metadata from {metadata_file}")
            
            import json
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            logger.info("Metadata loaded successfully - skipping workforce context generation during database creation")
            logger.info("Note: Workforce context should be pre-computed during movement analysis phase")
            
            # During database creation, we should only ingest pre-computed parquet files
            # Workforce context generation should happen during precompute phase
            return True
            
        except Exception as e:
            logger.error(f"Failed to load movement metadata: {e}")
            return False
    
    def _generate_workforce_context_data(self) -> pd.DataFrame:
        """Generate workforce context data from positions table."""
        try:
            logger.info("Generating workforce context data from positions table...")
            
            # Load positions data to generate context
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT 
                    p."Employee Number" as employee_number,
                    p.JobProfileID as jobprofile_id,
                    p.Division,
                    p.Business_Unit,
                    p.Team,
                    p.Location,
                    p.Rg,
                    p."Employee Group",
                    p."Salary Group"
                FROM positions p
                WHERE p.JobProfileID IS NOT NULL AND p.JobProfileID != ''
                LIMIT 10000
                """
                
                df_positions = pd.read_sql_query(query, conn)
            
            if df_positions.empty:
                logger.warning("No positions data found for context generation")
                return pd.DataFrame()
            
            # Generate context records
            context_records = []
            
            for _, row in df_positions.iterrows():
                employee_number = row['employee_number']
                jobprofile_id = row['jobprofile_id']
                effective_date = datetime.now().date()
                
                # Create context records for different attributes
                context_mappings = {
                    'division': row['Division'],
                    'business_unit': row['Business_Unit'],
                    'team': row['Team'],
                    'location': row['Location'],
                    'region': row['Rg'],
                    'employee_group': row['Employee Group'],
                    'salary_group': row['Salary Group']
                }
                
                for context_type, context_value in context_mappings.items():
                    if context_value and str(context_value).strip():
                        context_records.append({
                            'employee_number': str(employee_number),
                            'jobprofile_id': str(jobprofile_id),
                            'context_type': context_type,
                            'context_value': str(context_value),
                            'effective_date': effective_date,
                            'end_date': None
                        })
            
            df_context = pd.DataFrame(context_records)
            
            if df_context.empty:
                logger.warning("No context records generated")
                return pd.DataFrame()
            
            logger.info(f"Generated {len(df_context):,} workforce context records")
            return df_context
            
        except Exception as e:
            logger.error(f"Failed to generate workforce context data: {e}")
            return pd.DataFrame()
    
    def _transform_movement_metadata(self, metadata: Dict[str, Any]) -> pd.DataFrame:
        """Transform movement metadata to workforce context records."""
        try:
            # This method is no longer used - we generate context from positions data instead
            logger.info("Using position-based context generation instead of metadata transformation")
            return self._generate_workforce_context_data()
            
        except Exception as e:
            logger.error(f"Error transforming movement metadata: {e}")
            return pd.DataFrame()
    
    def _transform_employee_movements(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform employee movements data to match database schema."""
        try:
            # Create a new DataFrame with the required columns
            df_transformed = pd.DataFrame()
            
            # Map columns from parquet to database schema
            if 'employee_number' in df.columns:
                df_transformed['employee_number'] = df['employee_number'].astype(str)
            
            if 'to_position' in df.columns:
                df_transformed['jobprofile_id'] = df['to_position'].astype(str)
            
            if 'movement_type' in df.columns:
                df_transformed['movement_type'] = df['movement_type'].fillna('Internal Movement')
            else:
                df_transformed['movement_type'] = 'Internal Movement'
            
            if 'to_date' in df.columns:
                df_transformed['movement_date'] = pd.to_datetime(df['to_date'], errors='coerce').dt.date  # type: ignore
                df_transformed['effective_date'] = pd.to_datetime(df['to_date'], errors='coerce').dt.date  # type: ignore
            
            if 'from_date' in df.columns:
                df_transformed['end_date'] = pd.to_datetime(df['from_date'], errors='coerce').dt.date  # type: ignore
            
            df_transformed['change_reason'] = 'Career Progression'
            
            # Filter out rows with missing essential data
            df_transformed = df_transformed.dropna(subset=['employee_number', 'jobprofile_id', 'movement_date'])
            
            logger.info(f"Transformed {len(df_transformed):,} movement records")
            return df_transformed
            
        except Exception as e:
            logger.error(f"Error transforming employee movements: {e}")
            return pd.DataFrame()
    
    def _transform_movement_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform movement summary data to match database schema."""
        try:
            # Create a new DataFrame with the required columns
            df_transformed = pd.DataFrame()
            
            # Map columns from parquet to database schema
            if 'position_id' in df.columns:
                df_transformed['position_number'] = df['position_id'].astype(str)
                df_transformed['jobprofile_id'] = df['position_id'].astype(str)
            
            if 'month' in df.columns:
                df_transformed['effective_date'] = pd.to_datetime(df['month'], errors='coerce').dt.date  # type: ignore
            
            # Create synthetic employee numbers for summary data
            df_transformed['employee_number'] = 'SUMMARY_' + df_transformed.index.astype(str)
            df_transformed['change_type'] = 'Monthly Summary'
            
            # Filter out rows with missing essential data
            df_transformed = df_transformed.dropna(subset=['position_number', 'effective_date'])
            
            logger.info(f"Transformed {len(df_transformed):,} summary records")
            return df_transformed
            
        except Exception as e:
            logger.error(f"Error transforming movement summary: {e}")
            return pd.DataFrame()
    
    def _transform_movement_fact_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform movement fact table data to match database schema."""
        try:
            logger.info(f"Transforming fact table with columns: {df.columns.tolist()}")
            
            # The movement_fact_table.parquet contains aggregated movement patterns
            # We need to map these to the database schema
            
            # Check if we have the expected PTH fact table structure
            expected_columns = ['Movement_Month', 'From_Position', 'To_Position', 'Movement_Count']
            missing_columns = [col for col in expected_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"Missing expected fact table columns: {missing_columns}")
                logger.error(f"Available columns: {df.columns.tolist()}")
                return pd.DataFrame()
            
            # Create transformed DataFrame with database schema
            df_transformed = pd.DataFrame()
            
            # Map columns from parquet to database schema
            df_transformed['movement_month'] = df['Movement_Month']
            df_transformed['movement_year'] = df['Movement_Year'] if 'Movement_Year' in df.columns else df['Movement_Month'].str[:4].astype(int)
            df_transformed['from_position'] = df['From_Position'].astype(str)
            df_transformed['to_position'] = df['To_Position'].astype(str)
            df_transformed['movement_pattern'] = df['Movement_Pattern'] if 'Movement_Pattern' in df.columns else df['From_Position'].astype(str) + ' → ' + df['To_Position'].astype(str)
            df_transformed['movement_count'] = df['Movement_Count']
            df_transformed['pct_total_movements'] = df['Pct_Total_Movements'] if 'Pct_Total_Movements' in df.columns else None
            df_transformed['unique_employees'] = df['Unique_Employees'] if 'Unique_Employees' in df.columns else df['Movement_Count']
            df_transformed['avg_days_between'] = df['Avg_Days_Between'] if 'Avg_Days_Between' in df.columns else None
            df_transformed['monthly_total_movements'] = df['Monthly_Total_Movements'] if 'Monthly_Total_Movements' in df.columns else df['Movement_Count']
            df_transformed['predominant_movement_type'] = df['Predominant_Movement_Type'] if 'Predominant_Movement_Type' in df.columns else 'lateral'
            
            # Filter out rows with missing essential data
            df_transformed = df_transformed.dropna(subset=['movement_month', 'from_position', 'to_position', 'movement_count'])
            
            # Ensure data types
            df_transformed['movement_count'] = df_transformed['movement_count'].astype(int)
            df_transformed['unique_employees'] = df_transformed['unique_employees'].astype(int)
            df_transformed['monthly_total_movements'] = df_transformed['monthly_total_movements'].astype(int)
            
            logger.info(f"Transformed {len(df_transformed):,} aggregated movement patterns")
            logger.info(f"Sample patterns: {df_transformed['movement_pattern'].head(3).tolist()}")
            
            return df_transformed
            
        except Exception as e:
            logger.error(f"Error transforming movement fact table: {e}")
            logger.error(f"Available columns: {df.columns.tolist() if 'df' in locals() else 'Unknown'}")
            return pd.DataFrame()
    
    def get_integration_stats(self) -> Dict[str, int]:
        """Get statistics about integrated movement data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                
                # Count records in each table
                tables = ['colleague_movements', 'position_history', 'workforce_context', 'movement_fact']
                for table in tables:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[table] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get integration stats: {e}")
            return {} 