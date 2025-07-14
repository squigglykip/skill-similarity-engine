"""
Position History Generator

Generates position history records from enriched colleague position data for workforce intelligence.
This module creates temporal position tracking records that enable career pathway analysis and
strategic workforce planning.

Architecture: Configuration-Driven OOP Design
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path

from ..config.architectural_config_manager import ArchitecturalConfigManager
from ..business_context.position_enricher import PositionEnricher
from ..utils.progress import ProgressTracker, progress_context

logger = logging.getLogger(__name__)


class PositionHistoryGenerator:
    """
    Generates position history records from enriched colleague position data.
    
    This class creates temporal position tracking records by:
    1. Using PositionEnricher to get actual Position Numbers from colleague+position data
    2. Creating position periods for each employee based on their position history
    3. Generating database-ready position history records with organizational context
    4. Validating temporal consistency and data quality
    
    The output enables position-level movement analysis and career pathway intelligence.
    """
    
    def __init__(self, config_manager: ArchitecturalConfigManager):
        """
        Initialize position history generator.
        
        Args:
            config_manager: Configuration manager for architectural settings
        """
        self.config = config_manager
        self.position_history_config = self.config.get_models_position_history_config()
        self.position_enricher = PositionEnricher(config_manager)
        
    def generate_position_history_from_movements(self, 
                                               movements_df: pd.DataFrame,
                                                positions_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Generate position history records from movement data.
        
        This method is called when we have movement data but need to create proper
        position history records. It uses the PositionEnricher to get actual Position Numbers.
        
        Args:
            movements_df: DataFrame containing movement records
            positions_df: Optional positions data for additional context
            
        Returns:
            DataFrame containing position history records matching database schema
        """
        try:
            logger.info("🏗️ Generating position history from movement data...")
            
            # Check if we should use enriched colleague positions instead
            if self._should_use_enriched_data():
                logger.info("Using enriched colleague positions data for better accuracy")
                return self.generate_position_history_from_enriched_data()
            
            # Create position periods from movement data
            logger.info("Creating position periods from movement data...")
            position_periods = self._create_position_periods_from_movements(movements_df)
            
            # Enrich with position data if available
            if positions_df is not None:
                position_periods = self._enrich_with_position_data(position_periods, positions_df)
            
            # Generate final position history records
            position_history = self._generate_position_history_records(position_periods)
            
            logger.info(f"Generated {len(position_history):,} position history records")
            return position_history
            
        except Exception as e:
            logger.error(f"Failed to generate position history from movements: {e}")
            raise
    
    def generate_position_history_from_enriched_data(self,
                                                   colleague_positions_dir: Optional[str] = None,
                                                   positions_history_dir: Optional[str] = None) -> pd.DataFrame:
        """
        Generate position history from enriched colleague positions data.
        
        This is the preferred method as it uses actual Position Numbers from the
        position enrichment pipeline, enabling proper career pathway analysis.
        
        Args:
            colleague_positions_dir: Directory containing colleague positions files
            positions_history_dir: Directory containing positions history files
            
        Returns:
            DataFrame containing position history records matching database schema
        """
        try:
            logger.info("🏗️ Generating position history from enriched colleague positions...")
            
            # Use PositionEnricher to get enriched colleague positions data
            enriched_df = self.position_enricher.enrich_colleague_positions(
                colleague_positions_dir, positions_history_dir
            )
            
            # Create position periods from enriched data
            logger.info("Creating position periods from enriched data...")
            position_periods = self._create_position_periods_from_enriched_data(enriched_df)
            
            # Generate final position history records
            position_history = self._generate_position_history_records(position_periods)
            
            logger.info(f"Generated {len(position_history):,} position history records from enriched data")
            return position_history
            
        except Exception as e:
            logger.error(f"Failed to generate position history from enriched data: {e}")
            raise
    
    def _should_use_enriched_data(self) -> bool:
        """Determine if we should use enriched colleague positions data."""
        try:
            # Check if data directories are available
            enrichment_config = self.config.get_models_position_enrichment_config()
            data_sources = enrichment_config.get('data_sources', {})
            
            colleague_dir = data_sources.get('colleague_positions_dir')
            positions_dir = data_sources.get('positions_history_dir')
            
            if not colleague_dir or not positions_dir:
                return False
            
            # Check if directories exist
            colleague_path = Path(colleague_dir)
            positions_path = Path(positions_dir)
            
            return colleague_path.exists() and positions_path.exists()
            
        except Exception as e:
            logger.debug(f"Cannot use enriched data: {e}")
            return False
    
    def _create_position_periods_from_movements(self, movements_df: pd.DataFrame) -> pd.DataFrame:
        """Create position periods from movement records."""
        try:
            position_periods = []
            
            # Group movements by employee
            if 'employee_number' not in movements_df.columns:
                raise ValueError("Movement data must contain employee_number column")
            
            for employee_number, employee_movements in movements_df.groupby('employee_number'):
                # Sort movements by date
                if 'to_date' in employee_movements.columns:
                    employee_movements = employee_movements.sort_values('to_date')
            
            # Create position periods for this employee
                periods = self._create_employee_position_periods_from_movements(employee_movements)
                position_periods.extend(periods)
            
            df_periods = pd.DataFrame(position_periods)
            logger.info(f"Created {len(df_periods):,} position periods from movements")
            
            return df_periods
            
        except Exception as e:
            logger.error(f"Failed to create position periods from movements: {e}")
            raise
    
    def _create_position_periods_from_enriched_data(self, enriched_df: pd.DataFrame) -> pd.DataFrame:
        """Create position periods from enriched colleague positions data."""
        try:
            position_periods = []
            
            # Group by employee
            if 'employee_number' not in enriched_df.columns:
                raise ValueError("Enriched data must contain employee_number column")
            
            for employee_number, employee_data in enriched_df.groupby('employee_number'):
                # Sort by week ending date
                if 'week_ending' in employee_data.columns:
                    employee_data = employee_data.sort_values('week_ending')
                
                # Create position periods for this employee
                periods = self._create_employee_position_periods_from_enriched_data(employee_data)
                position_periods.extend(periods)
            
            df_periods = pd.DataFrame(position_periods)
            logger.info(f"Created {len(df_periods):,} position periods from enriched data")
            
            return df_periods
            
        except Exception as e:
            logger.error(f"Failed to create position periods from enriched data: {e}")
            raise
    
    def _create_employee_position_periods_from_movements(self, employee_movements: pd.DataFrame) -> List[Dict]:
        """Create position periods for a single employee from movement data."""
        try:
            periods = []
            
            for _, movement in employee_movements.iterrows():
                # Create a position period from this movement
                period = {
                    'employee_number': str(movement['employee_number']),
                    'position_key': movement.get('to_position', ''),
                    'effective_date': pd.to_datetime(movement.get('to_date')).date() if pd.notna(movement.get('to_date')) else None,
                    'end_date': None,  # Will be set by next movement
                    'position_title': '',
                    'organisational_unit': '',
                    'cost_centre_number': None,
                    'people_leader_number': None
                }
                
                periods.append(period)
            
            # Set end dates based on next movement start dates
            for i in range(len(periods) - 1):
                periods[i]['end_date'] = periods[i + 1]['effective_date']
            
            return periods
            
        except Exception as e:
            logger.error(f"Failed to create employee position periods from movements: {e}")
            return []
    
    def _create_employee_position_periods_from_enriched_data(self, employee_data: pd.DataFrame) -> List[Dict]:
        """Create position periods for a single employee from enriched data."""
        try:
            periods = []
            current_position = None
            current_start_date = None
            
            for _, record in employee_data.iterrows():
                position_key = record.get('position_key')
                week_ending = record.get('week_ending')
                
                if pd.isna(position_key) or not str(position_key).strip():
                    continue
                
                # Check if position changed
                if current_position != position_key:
                    # End previous position period
                    if current_position is not None:
                        periods.append({
                            'employee_number': str(record['employee_number']),
                            'position_key': current_position,
                            'effective_date': current_start_date,
                            'end_date': week_ending,
                            'position_title': record.get('position_title', ''),
                            'organisational_unit': record.get('organisational_unit', ''),
                            'cost_centre_number': record.get('cost_centre_number'),
                            'people_leader_number': record.get('people_leader_number')
                        })
                    
                    # Start new position period
                    current_position = position_key
                    current_start_date = week_ending
            
            # Add final position period (ongoing)
            if current_position is not None:
                periods.append({
                    'employee_number': str(employee_data.iloc[-1]['employee_number']),
                    'position_key': current_position,
                    'effective_date': current_start_date,
                    'end_date': None,  # Ongoing position
                    'position_title': employee_data.iloc[-1].get('position_title', ''),
                    'organisational_unit': employee_data.iloc[-1].get('organisational_unit', ''),
                    'cost_centre_number': employee_data.iloc[-1].get('cost_centre_number'),
                    'people_leader_number': employee_data.iloc[-1].get('people_leader_number')
                })
            
            return periods
            
        except Exception as e:
            logger.error(f"Failed to create employee position periods from enriched data: {e}")
            return []
    
    def _enrich_with_position_data(self, position_periods: pd.DataFrame, positions_df: pd.DataFrame) -> pd.DataFrame:
        """Enrich position periods with additional position data."""
        try:
            if positions_df.empty:
                return position_periods
            
            # Try to merge with positions data for additional context
            # This is a fallback when we don't have enriched data
            
            logger.info("Enriching position periods with additional position data...")
            
            # Prepare positions data for merge
            positions_for_merge = positions_df[['Position Number', 'JobProfileID']].drop_duplicates()
            positions_for_merge = positions_for_merge.rename(columns={
                'Position Number': 'position_key',
                'JobProfileID': 'jobprofile_id'
            })
            
            # Merge with position periods
            enriched_periods = position_periods.merge(
                positions_for_merge,
                on='position_key',
            how='left'
        )
        
            logger.info(f"Enriched {len(enriched_periods):,} position periods")
            return enriched_periods
        
        except Exception as e:
            logger.error(f"Failed to enrich with position data: {e}")
            return position_periods
    
    def _generate_position_history_records(self, position_periods: pd.DataFrame) -> pd.DataFrame:
        """Generate final position history records matching database schema."""
        try:
            logger.debug("Generating position history records")
            
            if position_periods.empty:
                logger.warning("No position periods to generate history from")
                return pd.DataFrame()
            
            # Create position history DataFrame with database schema
            position_history = pd.DataFrame()
            
            # Required fields for database schema
            position_history['employee_number'] = position_periods['employee_number'].astype(str)
            position_history['position_number'] = position_periods['position_key'].astype(str)
            position_history['effective_date'] = pd.to_datetime(position_periods['effective_date'], errors='coerce').dt.date
            position_history['end_date'] = pd.to_datetime(position_periods['end_date'], errors='coerce').dt.date
            
            # Optional organizational context fields
            position_history['position_title'] = position_periods.get('position_title', pd.Series(dtype=str)).fillna('')
            position_history['organisational_unit'] = position_periods.get('organisational_unit', pd.Series(dtype=str)).fillna('')
            position_history['cost_centre_number'] = position_periods.get('cost_centre_number')
            position_history['people_leader_number'] = position_periods.get('people_leader_number')
            
            # Job profile mapping (if available)
            if 'jobprofile_id' in position_periods.columns:
                position_history['jobprofile_id'] = position_periods['jobprofile_id'].fillna('')
            else:
                # Use position_number as fallback for jobprofile_id
                position_history['jobprofile_id'] = position_history['position_number']
            
            # Add derived fields
            position_history['change_type'] = 'Position Assignment'
            position_history['data_source'] = 'Position History Generator'
            
            # Remove records with missing essential data
            essential_fields = ['employee_number', 'position_number', 'effective_date']
            before_filter = len(position_history)
            position_history = position_history.dropna(subset=essential_fields)
            after_filter = len(position_history)
            
            if before_filter > after_filter:
                logger.warning(f"Filtered out {before_filter - after_filter:,} records with missing essential data")
            
            logger.info(f"Generated {len(position_history):,} position history records")
            return position_history
            
        except Exception as e:
            logger.error(f"Failed to generate position history records: {e}")
            raise
    
    def validate_position_history(self, position_history: pd.DataFrame) -> bool:
        """Validate generated position history records."""
        try:
            validation_config = self.position_history_config.get('validation', {})
            
            if position_history.empty:
                logger.error("Position history is empty")
                return False
            
            # Check required fields
            required_fields = ['employee_number', 'position_number', 'effective_date']
            missing_fields = [field for field in required_fields if field not in position_history.columns]
            
            if missing_fields:
                logger.error(f"Missing required fields: {missing_fields}")
                return False
            
            # Check for null values in required fields
            if validation_config.get('require_employee_number', True):
                null_employees = position_history['employee_number'].isna().sum()
                if null_employees > 0:
                    logger.error(f"Found {null_employees:,} records with null employee_number")
                    return False
            
            if validation_config.get('require_position_number', True):
                null_positions = position_history['position_number'].isna().sum()
                if null_positions > 0:
                    logger.error(f"Found {null_positions:,} records with null position_number")
                    return False
            
            if validation_config.get('require_effective_date', True):
                null_dates = position_history['effective_date'].isna().sum()
                if null_dates > 0:
                    logger.error(f"Found {null_dates:,} records with null effective_date")
                    return False
            
            # Check minimum record count
            min_records = validation_config.get('min_position_duration_days', 1)
            if len(position_history) < min_records:
                logger.error(f"Position history has only {len(position_history):,} records, minimum {min_records} required")
                return False
            
            logger.info("✅ Position history validation passed")
            return True 
            
        except Exception as e:
            logger.error(f"Position history validation failed: {e}")
            return False 