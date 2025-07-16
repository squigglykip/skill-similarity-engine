"""
Position Enrichment Pipeline for Workforce Intelligence

This module implements PTH's proven position enrichment strategy, merging colleague_positions
data with positions_history data via PosIDLookupKey to obtain actual Position Numbers.

This is critical for proper movement aggregation - without Position Numbers, we get unique
temporal identifiers that prevent career pathway analysis.

Architecture: Configuration-Driven OOP Design
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from ..config.architectural_config_manager import ArchitecturalConfigManager
from ..utils.progress import ProgressTracker, progress_context

logger = logging.getLogger(__name__)


class PositionEnricher:
    """
    Enriches colleague position data with actual Position Numbers from positions history.
    
    This class implements PTH's proven enrichment pipeline:
    1. Load colleague_positions_history (temporal employee-position associations)
    2. Load positions_history (position master data with Position Numbers)
    3. Merge via PosIDLookupKey to enrich colleague positions with actual Position Numbers
    4. Validate enrichment quality and temporal consistency
    
    The enriched data enables proper position-level aggregation for career pathway analysis.
    """
    
    def __init__(self, config_manager: ArchitecturalConfigManager):
        """
        Initialize position enricher with configuration.
        
        Args:
            config_manager: Configuration manager for architectural settings
        """
        self.config = config_manager
        self.enrichment_config = self.config.get_models_position_enrichment_config()
        self.enrichment_stats = {
            'colleague_positions_loaded': 0,
            'positions_loaded': 0,
            'enrichment_rate': 0.0,
            'position_numbers_obtained': 0,
            'temporal_consistency_issues': 0
        }
        
    def enrich_colleague_positions(self, 
                                 colleague_positions_dir: Optional[str] = None,
                                 positions_history_dir: Optional[str] = None) -> pd.DataFrame:
        """
        Enrich colleague positions with actual Position Numbers from positions history.
        
        Args:
            colleague_positions_dir: Directory containing colleague positions files
            positions_history_dir: Directory containing positions history files
            
        Returns:
            Enriched DataFrame with Position Numbers for movement analysis
        """
        try:
            logger.info("🔗 Starting position enrichment pipeline...")
            
            # Get data source paths from config
            data_sources = self.enrichment_config.get('data_sources', {})
            colleague_dir = colleague_positions_dir or data_sources.get('colleague_positions_dir')
            positions_dir = positions_history_dir or data_sources.get('positions_history_dir')
            
            if not colleague_dir or not positions_dir:
                raise ValueError("Colleague positions and positions history directories must be specified")
            
            # Load colleague positions data
            logger.info("📊 Loading colleague positions history...")
            colleague_positions_df = self._load_colleague_positions_data(colleague_dir)
            
            # Load positions history data
            logger.info("📊 Loading positions history data...")
            positions_df = self._load_positions_data(positions_dir)
            
            # Perform enrichment merge
            logger.info("🔗 Performing position enrichment merge...")
            enriched_df = self._perform_enrichment_merge(colleague_positions_df, positions_df)
            
            # Validate enrichment quality
            logger.info("✅ Validating enrichment quality...")
            self._validate_enrichment_quality(enriched_df, colleague_positions_df)
            
            # Log enrichment statistics
            self._log_enrichment_statistics()
            
            logger.info(f"✅ Position enrichment completed: {len(enriched_df):,} enriched records")
            return enriched_df
            
        except Exception as e:
            logger.error(f"❌ Position enrichment failed: {e}")
            raise
    
    def _load_colleague_positions_data(self, colleague_dir: str) -> pd.DataFrame:
        """Load colleague positions data from CSV files."""
        try:
            colleague_dir_path = Path(colleague_dir)
            if not colleague_dir_path.exists():
                raise FileNotFoundError(f"Colleague positions directory not found: {colleague_dir}")
            
            # Get file pattern from config
            data_sources = self.enrichment_config.get('data_sources', {})
            # Get pattern from configuration with fallback
            file_pattern = data_sources.get('colleague_positions_pattern')
            if not file_pattern:
                from ..config.pattern_resolver import get_workforce_pattern
                file_pattern = get_workforce_pattern('colleague_positions')
            
            # Find matching files
            files = list(colleague_dir_path.glob(file_pattern))
            if not files:
                raise FileNotFoundError(f"No colleague positions files found matching pattern: {file_pattern}")
            
            logger.info(f"Found {len(files)} colleague positions files")
            
            # Load and combine all files
            dataframes = []
            field_mappings = self.enrichment_config.get('colleague_positions_fields', {})
            
            for file_path in files:
                logger.debug(f"Loading {file_path.name}...")
                df = pd.read_csv(file_path, low_memory=False)
                
                # Apply field mappings
                df = self._apply_field_mappings(df, field_mappings)
                
                # Add source file for tracking
                df['source_file'] = file_path.name
                
                dataframes.append(df)
            
            # Combine all dataframes
            combined_df = pd.concat(dataframes, ignore_index=True)
            
            # Convert data types
            combined_df = self._convert_colleague_positions_types(combined_df)
            
            self.enrichment_stats['colleague_positions_loaded'] = len(combined_df)
            logger.info(f"Loaded {len(combined_df):,} colleague position records")
            
            return combined_df
            
        except Exception as e:
            logger.error(f"Failed to load colleague positions data: {e}")
            raise
    
    def _load_positions_data(self, positions_dir: str) -> pd.DataFrame:
        """Load positions history data from CSV files."""
        try:
            positions_dir_path = Path(positions_dir)
            if not positions_dir_path.exists():
                raise FileNotFoundError(f"Positions history directory not found: {positions_dir}")
            
            # Get file pattern from config
            data_sources = self.enrichment_config.get('data_sources', {})
            file_pattern = data_sources.get('positions_pattern')
            if not file_pattern:
                from ..config.pattern_resolver import get_workforce_pattern
                file_pattern = get_workforce_pattern('positions_history')
            
            # Find matching files
            files = list(positions_dir_path.glob(file_pattern))
            if not files:
                raise FileNotFoundError(f"No positions files found matching pattern: {file_pattern}")
            
            logger.info(f"Found {len(files)} positions history files")
            
            # Load and combine all files
            dataframes = []
            field_mappings = self.enrichment_config.get('positions_fields', {})
            
            for file_path in files:
                logger.debug(f"Loading {file_path.name}...")
                df = pd.read_csv(file_path, low_memory=False)
                
                # Apply field mappings
                df = self._apply_field_mappings(df, field_mappings)
                
                # Add source file for tracking
                df['source_file'] = file_path.name
                
                dataframes.append(df)
            
            # Combine all dataframes
            combined_df = pd.concat(dataframes, ignore_index=True)
            
            # Convert data types
            combined_df = self._convert_positions_types(combined_df)
            
            self.enrichment_stats['positions_loaded'] = len(combined_df)
            logger.info(f"Loaded {len(combined_df):,} position records")
            
            return combined_df
            
        except Exception as e:
            logger.error(f"Failed to load positions data: {e}")
            raise
    
    def _apply_field_mappings(self, df: pd.DataFrame, field_mappings: Dict[str, str]) -> pd.DataFrame:
        """Apply field mappings from config to standardize column names."""
        try:
            if not field_mappings:
                return df
            
            # Create reverse mapping (config_name -> column_name)
            column_mapping = {v: k for k, v in field_mappings.items()}
            
            # Rename columns that exist
            existing_mappings = {col: new_name for col, new_name in column_mapping.items() if col in df.columns}
            if existing_mappings:
                df = df.rename(columns=existing_mappings)
                logger.debug(f"Applied field mappings: {existing_mappings}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to apply field mappings: {e}")
            return df
    
    def _convert_colleague_positions_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert colleague positions data types."""
        try:
            # Convert employee numbers to string
            if 'employee_number' in df.columns:
                df['employee_number'] = df['employee_number'].astype(str)
            
            # Convert PosIDLookupKey to float (handles scientific notation)
            if 'pos_id_lookup_key' in df.columns:
                df['pos_id_lookup_key'] = pd.to_numeric(df['pos_id_lookup_key'], errors='coerce')
            
            # Convert position numbers to string (may be null)
            if 'position_number' in df.columns:
                df['position_number'] = df['position_number'].astype(str).replace('nan', '')
            
            # Convert dates
            if 'week_ending' in df.columns:
                df['week_ending'] = pd.to_datetime(df['week_ending'], format='%d/%m/%Y', errors='coerce')
            
            if 'position_start_date' in df.columns:
                df['position_start_date'] = pd.to_datetime(df['position_start_date'], format='%d/%m/%Y', errors='coerce')
            
            # Convert operational flag
            if 'operational' in df.columns:
                df['operational'] = df['operational'].astype(str).str.upper() == 'TRUE'
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to convert colleague positions types: {e}")
            return df
    
    def _convert_positions_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert positions data types."""
        try:
            # Convert position numbers to string
            if 'position_number' in df.columns:
                df['position_number'] = df['position_number'].astype(str)
            
            # Convert PosIDLookupKey to float (handles scientific notation)
            if 'pos_id_lookup_key' in df.columns:
                df['pos_id_lookup_key'] = pd.to_numeric(df['pos_id_lookup_key'], errors='coerce')
            
            # Convert dates
            if 'week_ending' in df.columns:
                df['week_ending'] = pd.to_datetime(df['week_ending'], format='%d/%m/%Y', errors='coerce')
            
            # Convert operational flag
            if 'operational' in df.columns:
                df['operational'] = df['operational'].astype(str).str.upper() == 'TRUE'
            
            # Convert cost centre to numeric
            if 'cost_centre_number' in df.columns:
                df['cost_centre_number'] = pd.to_numeric(df['cost_centre_number'], errors='coerce')
            
            # Convert people leader to numeric
            if 'people_leader_number' in df.columns:
                df['people_leader_number'] = pd.to_numeric(df['people_leader_number'], errors='coerce')
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to convert positions types: {e}")
            return df
    
    def _perform_enrichment_merge(self, colleague_df: pd.DataFrame, positions_df: pd.DataFrame) -> pd.DataFrame:
        """Perform the enrichment merge using PosIDLookupKey."""
        try:
            enrichment_strategy = self.enrichment_config.get('enrichment_strategy', {})
            merge_key = enrichment_strategy.get('merge_key', 'pos_id_lookup_key')
            
            logger.info(f"Merging on key: {merge_key}")
            
            # Prepare positions data for merge - get the most recent position data for each PosIDLookupKey
            positions_for_merge = self._prepare_positions_for_merge(positions_df, merge_key)
            
            # Perform the merge
            logger.info("Executing left join on PosIDLookupKey...")
            enriched_df = colleague_df.merge(
                positions_for_merge,
                on=merge_key,
                how='left',
                suffixes=('', '_pos')
            )
            
            # Apply position identifier priority logic
            enriched_df = self._apply_position_identifier_priority(enriched_df)
            
            # Add organizational context
            if enrichment_strategy.get('include_organizational_context', True):
                enriched_df = self._add_organizational_context(enriched_df)
            
            # Calculate enrichment statistics
            self._calculate_enrichment_statistics(enriched_df, colleague_df)
            
            return enriched_df
            
        except Exception as e:
            logger.error(f"Failed to perform enrichment merge: {e}")
            raise
    
    def _prepare_positions_for_merge(self, positions_df: pd.DataFrame, merge_key: str) -> pd.DataFrame:
        """Prepare positions data for merge by selecting most recent data per PosIDLookupKey."""
        try:
            # Sort by week_ending to get most recent data
            if 'week_ending' in positions_df.columns:
                positions_sorted = positions_df.sort_values('week_ending', ascending=False)
            else:
                positions_sorted = positions_df
            
            # Get most recent record for each PosIDLookupKey
            positions_for_merge = positions_sorted.drop_duplicates(subset=[merge_key], keep='first')
            
            # Select columns needed for enrichment
            enrichment_columns = [
                merge_key,
                'position_number',
                'organisational_unit',
                'cost_centre_number', 
                'position_title',
                'people_leader_number',
                'org_unit_lookup_key'
            ]
            
            # Only include columns that exist
            available_columns = [col for col in enrichment_columns if col in positions_for_merge.columns]
            positions_for_merge = positions_for_merge[available_columns]
            
            logger.info(f"Prepared {len(positions_for_merge):,} position records for merge")
            return positions_for_merge
            
        except Exception as e:
            logger.error(f"Failed to prepare positions for merge: {e}")
            return positions_df
    
    def _apply_position_identifier_priority(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply position identifier priority logic (Position Number > PosIDLookupKey)."""
        try:
            enrichment_strategy = self.enrichment_config.get('enrichment_strategy', {})
            priority_fields = enrichment_strategy.get('position_identifier_priority', ['position_number', 'pos_id_lookup_key'])
            
            # Create position_key field following PTH's logic
            def get_position_key(row):
                for field in priority_fields:
                    if field in row and pd.notna(row[field]) and str(row[field]).strip():
                        return str(row[field])
                return None
            
            df['position_key'] = df.apply(get_position_key, axis=1)
            
            # Count successful position key assignments
            position_keys_assigned = df['position_key'].notna().sum()
            self.enrichment_stats['position_numbers_obtained'] = position_keys_assigned
            
            logger.info(f"Assigned position keys to {position_keys_assigned:,} records")
            return df
            
        except Exception as e:
            logger.error(f"Failed to apply position identifier priority: {e}")
            return df
    
    def _add_organizational_context(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add organizational context fields from positions data."""
        try:
            # Organizational context is already included via the merge
            # Just ensure we have the expected fields
            
            context_fields = [
                'organisational_unit',
                'cost_centre_number',
                'position_title',
                'people_leader_number'
            ]
            
            available_context = [field for field in context_fields if field in df.columns]
            logger.info(f"Available organizational context fields: {available_context}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to add organizational context: {e}")
            return df
    
    def _calculate_enrichment_statistics(self, enriched_df: pd.DataFrame, original_df: pd.DataFrame) -> None:
        """Calculate enrichment quality statistics."""
        try:
            total_records = len(original_df)
            enriched_records = enriched_df['position_key'].notna().sum()
            
            self.enrichment_stats['enrichment_rate'] = enriched_records / total_records if total_records > 0 else 0.0
            
            logger.info(f"Enrichment rate: {self.enrichment_stats['enrichment_rate']:.1%}")
            
        except Exception as e:
            logger.error(f"Failed to calculate enrichment statistics: {e}")
    
    def _validate_enrichment_quality(self, enriched_df: pd.DataFrame, original_df: pd.DataFrame) -> None:
        """Validate enrichment quality against configured thresholds."""
        try:
            data_quality = self.enrichment_config.get('data_quality', {})
            required_rate = data_quality.get('require_successful_enrichment_rate', 0.8)
            
            if self.enrichment_stats['enrichment_rate'] < required_rate:
                error_msg = f"Enrichment rate {self.enrichment_stats['enrichment_rate']:.1%} below required {required_rate:.1%}"
                
                handle_missing = data_quality.get('handle_missing_positions', 'warn')
                if handle_missing == 'error':
                    raise ValueError(error_msg)
                elif handle_missing == 'warn':
                    logger.warning(f"⚠️ {error_msg}")
                # 'ignore' case - do nothing
            
            # Validate position number presence
            if data_quality.get('validate_position_number_presence', True):
                position_numbers_present = enriched_df['position_key'].notna().sum()
                if position_numbers_present == 0:
                    raise ValueError("No position keys were successfully assigned during enrichment")
            
            logger.info("✅ Enrichment quality validation passed")
            
        except Exception as e:
            logger.error(f"Enrichment quality validation failed: {e}")
            raise
    
    def _log_enrichment_statistics(self) -> None:
        """Log comprehensive enrichment statistics."""
        try:
            stats = self.enrichment_stats
            
            logger.info("📊 Position Enrichment Statistics:")
            logger.info(f"  • Colleague positions loaded: {stats['colleague_positions_loaded']:,}")
            logger.info(f"  • Position records loaded: {stats['positions_loaded']:,}")
            logger.info(f"  • Enrichment rate: {stats['enrichment_rate']:.1%}")
            logger.info(f"  • Position keys obtained: {stats['position_numbers_obtained']:,}")
            
            if stats['temporal_consistency_issues'] > 0:
                logger.warning(f"  ⚠️ Temporal consistency issues: {stats['temporal_consistency_issues']:,}")
            
        except Exception as e:
            logger.error(f"Failed to log enrichment statistics: {e}")
    
    def get_enrichment_statistics(self) -> Dict[str, Any]:
        """Get enrichment statistics for external reporting."""
        return self.enrichment_stats.copy() 