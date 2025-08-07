"""
Core MovementTracker for detecting colleague position transitions.

Ported from Position Transition History (PTH) to Skill Similarity Engine (SSE).
This is the heart of the movement detection system - it identifies
movement patterns and tracks transition pathways throughout the organisation.

Architecture: Enterprise OOP with SSE Performance Integration
ZERO hardcoded values - everything configured via architectural config
"""

import csv
import os
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
import pandas as pd

from .colleague_position import ColleaguePosition
from ..utils.progress import ProgressTracker
from ..config.workforce_config_loader import get_workforce_config_loader
from ..config.architectural_config_manager import get_config_manager

import logging
logger = logging.getLogger(__name__)


class MovementEvent:
    """
    Represents a single movement event between positions.
    
    Enhanced for SSE integration with additional metadata and analysis capabilities.
    Configuration-driven approach eliminates hardcoded date formats.
    """
    
    def __init__(self, 
                 employee_number: int,
                 from_position: int,
                 to_position: int,
                 from_date: str,
                 to_date: str,
                 movement_type: str = 'lateral',
                 organisational_context: Optional[Dict[str, Any]] = None):
        self.employee_number = employee_number
        self.from_position = from_position
        self.to_position = to_position
        self.from_date = from_date
        self.to_date = to_date
        self.movement_type = movement_type
        self.organisational_context = organisational_context or {}
        
        # Get date format from configuration - NO hardcoded "%Y-%m-%d"
        self.config_manager = get_config_manager()
        date_formats = self.config_manager.get_models_date_formats()
        self.movement_date_format = date_formats.get('movement_date_format', '%Y-%m-%d')
    
    @property
    def transition_key(self) -> Tuple[int, int]:
        """Get the transition pattern (from_position, to_position)."""
        return (self.from_position, self.to_position)
    
    @property
    def duration_days(self) -> Optional[int]:
        """Calculate duration between movements in days using configured date format."""
        try:
            from_dt = datetime.strptime(self.from_date, self.movement_date_format)
            to_dt = datetime.strptime(self.to_date, self.movement_date_format)
            delta = to_dt - from_dt
            return delta.days
        except ValueError:
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export/analysis."""
        return {
            'employee_number': self.employee_number,
            'from_position': self.from_position,
            'to_position': self.to_position,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'movement_type': self.movement_type,
            'duration_days': self.duration_days,
            'transition_key': f"{self.from_position}->{self.to_position}",
            **self.organisational_context
        }
    
    def __str__(self) -> str:
        return f"Employee {self.employee_number}: {self.from_position} → {self.to_position} ({self.from_date} to {self.to_date}) [{self.movement_type}]"


class MovementTracker:
    """
    Core engine for detecting and tracking colleague movements.
    
    Integrates PTH's movement detection algorithms with SSE's performance utilities.
    This class identifies movement patterns and builds arterial route maps
    throughout the organisation for strategic workforce planning.
    
    ZERO hardcoded values - all parameters from architectural configuration.
    """
    
    def __init__(self, config_loader=None):
        """Initialize MovementTracker with configuration-driven parameters."""
        self.colleague_positions: List[ColleaguePosition] = []
        self.movement_events: List[MovementEvent] = []
        self.employee_histories: Dict[int, List[ColleaguePosition]] = defaultdict(list)
        
        # Position enrichment (PTH pattern)
        self.position_mappings: Dict[float, int] = {}  # PosIDLookupKey -> Position Number
        
        # SSE Integration components
        self.config_loader = config_loader or get_workforce_config_loader()
        self.config_manager = get_config_manager()
        
        # Load configuration settings - NO hardcoded values
        operational_config = self.config_loader.load_operational_config()
        movement_settings = operational_config.get('movement_detection', {})
        
        self.min_movement_frequency = movement_settings.get('min_movement_frequency', 2)
        self.detection_window_weeks = movement_settings.get('detection_window_weeks', 52)
        self.min_position_tenure_weeks = movement_settings.get('min_position_tenure_weeks', 4)
        self.track_lateral_moves = movement_settings.get('track_lateral_moves', True)
        self.track_promotions = movement_settings.get('track_promotions', True)
        self.track_department_changes = movement_settings.get('track_department_changes', True)
        
        # Get movement analysis specific configuration - NO hardcoded intervals
        movement_analysis_config = self.config_manager.get_models_movement_analysis_config()
        self.progress_reporting_interval = movement_analysis_config.get('progress_reporting_interval', 10000)
        self.memory_usage_reporting = movement_analysis_config.get('memory_usage_reporting', True)
        self.enrichment_rate_calculation = movement_analysis_config.get('enrichment_rate_calculation', True)
        self.enrichment_percentage_multiplier = movement_analysis_config.get('enrichment_percentage_multiplier', 100)
        
        # Get export settings from configuration - NO hardcoded export parameters
        export_settings = self.config_manager.get_models_export_settings()
        self.csv_export_settings = export_settings.get('csv_export', {})
        self.parquet_export_settings = export_settings.get('parquet_export', {})
        
        # Get date formats from configuration - NO hardcoded date format strings
        date_formats = self.config_manager.get_models_date_formats()
        self.movement_date_format = date_formats.get('movement_date_format', '%Y-%m-%d')
        self.iso_format = date_formats.get('iso_format', '%Y-%m-%d')
        
        print("🏗️ MovementTracker initialized with configuration-driven parameters")
        print(f"   • Min movement frequency: {self.min_movement_frequency}")
        print(f"   • Detection window: {self.detection_window_weeks} weeks")
        print(f"   • Min position tenure: {self.min_position_tenure_weeks} weeks")
        print(f"   • Progress reporting interval: {self.progress_reporting_interval}")
    
    def load_from_directory(self, directory_path: str, pattern: str = None) -> None:
        """
        Load colleague positions from multiple CSV files using SSE's progress tracking.
        
        Args:
            directory_path: Path to directory containing CSV files
            pattern: Glob pattern to match CSV files (if None, loads from config)
        """
        # Get pattern from configuration if not provided
        if pattern is None:
            from ..config.pattern_resolver import get_workforce_pattern
            pattern = get_workforce_pattern('colleague_positions')
        
        directory_path = Path(directory_path)
        csv_files = list(directory_path.glob(pattern))
        
        if not csv_files:
            raise FileNotFoundError(f"No CSV files matching pattern '{pattern}' found in {directory_path}")
        
        # Sort files for consistent processing order
        csv_files = sorted(csv_files)
        
        print(f"📁 Found {len(csv_files)} files matching pattern '{pattern}'")
        
        # Use SSE's progress tracking for file loading
        with ProgressTracker(
            total=len(csv_files),
            desc="Loading colleague position files"
        ) as progress:
            
            for csv_file in csv_files:
                # Reduce logging verbosity during progress tracking
                logger.debug(f"📄 Processing {csv_file.name}")
                self.load_from_csv(str(csv_file))
                progress.update(1)
        
        self._build_employee_histories()
        
        print(f"✅ Successfully loaded data from {len(csv_files)} files")
        print(f"👥 Tracking {len(self.colleague_positions):,} total positions")
        print(f"👤 Following {len(self.employee_histories):,} unique colleagues")
        
    def load_from_csv(self, csv_file: str) -> None:
        """
        Load colleague position data from CSV file with configurable progress reporting.
        
        Args:
            csv_file: Path to the CSV file
        """
        successful_loads = 0
        failed_loads = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    if self._is_header_row(row):
                        continue
                    
                    try:
                        position = self._create_position_from_row(row)
                        if position:
                            self.colleague_positions.append(position)
                            successful_loads += 1
                        else:
                            failed_loads += 1
                    except Exception as e:
                        logger.debug(f"Failed to process row: {e}")
                        failed_loads += 1
                        
                    # Use configured progress reporting interval - NO hardcoded 10000
                    if successful_loads % self.progress_reporting_interval == 0 and successful_loads > 0:
                        logger.debug(f"  📊 Processed {successful_loads:,} records...")
                        
        except Exception as e:
            logger.error(f"❌ Error loading CSV file {csv_file}: {e}")
            raise
        
        logger.debug(f"  ✅ Successfully loaded {successful_loads:,} records")
        if failed_loads > 0:
            logger.debug(f"  ⚠️ Skipped {failed_loads:,} invalid records")
    
    def _create_position_from_row(self, row: Dict[str, Any]) -> Optional[ColleaguePosition]:
        """Create a ColleaguePosition from a CSV row."""
        try:
            # DEBUG: Let's see what we're working with
            if len(self.colleague_positions) < 3:  # Only debug first few rows
                print(f"🔧 DEBUG: Raw CSV row: {dict(list(row.items())[:3])}...")
            
            # Since ColleaguePosition.from_dict() does its own field mapping,
            # we should pass the raw CSV data directly without pre-mapping
            return ColleaguePosition.from_dict(row)
            
        except Exception as e:
            if len(self.colleague_positions) < 3:  # Only debug first few failures
                logger.warning(f"🔧 DEBUG: Failed to create position: {e}")
                logger.warning(f"🔧 DEBUG: Row data: {dict(list(row.items())[:5])}...")
            return None
    
    def _is_header_row(self, row_dict: Dict[str, Any]) -> bool:
        """Check if this row appears to be a header row."""
        # Look for common header patterns
        values = [str(v).lower().strip() for v in row_dict.values()]
        header_indicators = ['employee', 'position', 'date', 'id', 'number']
        
        # If any value contains header-like text, treat as header
        for value in values:
            if any(indicator in value for indicator in header_indicators):
                return True
        
        return False
    
    def _build_employee_histories(self) -> None:
        """Build employee histories from loaded positions."""
        print("🔗 Building employee histories...")
        
        for position in self.colleague_positions:
            self.employee_histories[position.employee_number].append(position)
        
        # Sort each employee's positions by date
        for employee_number in self.employee_histories:
            self.employee_histories[employee_number].sort(
                key=lambda pos: pos.week_ending
            )
        
        print(f"✅ Built histories for {len(self.employee_histories):,} employees")
    
    def detect_movements(self, use_parallel: bool = False) -> None:
        """
        Detect movements between positions for all employees.
        
        Args:
            use_parallel: Whether to use parallel processing (simplified for now)
        """
        if not self.employee_histories:
            self._build_employee_histories()
        
        print(f"🔍 Starting movement detection for {len(self.employee_histories):,} employees...")
        
        # For now, use sequential processing to avoid complexity
        self._detect_movements_sequential()
        
        print(f"✅ Movement detection complete")
        print(f"📊 Detected {len(self.movement_events):,} movement events")
    
    def _detect_movements_sequential(self) -> None:
        """Detect movements sequentially with progress tracking."""
        
        with ProgressTracker(
            total=len(self.employee_histories),
            desc="Detecting movements"
        ) as progress:
            
            for employee_number, positions in self.employee_histories.items():
                movements = self._detect_employee_movements(employee_number, positions)
                self.movement_events.extend(movements)
                progress.update(1)
    
    def _detect_employee_movements(self, employee_number: int, positions: List[ColleaguePosition]) -> List[MovementEvent]:
        """Detect movements for a single employee using configured date format."""
        movements = []
        
        if len(positions) < 2:
            return movements  # No movements possible with less than 2 positions
        
        for i in range(len(positions) - 1):
            current_pos = positions[i]
            next_pos = positions[i + 1]
            
            # Check if this is a genuine movement (different positions)
            if current_pos.position_key != next_pos.position_key:
                # Determine movement type (simplified)
                movement_type = 'lateral'  # Default
                
                try:
                    # Handle both string and date formats for week_ending using configured format
                    from_date = current_pos.week_ending if isinstance(current_pos.week_ending, str) else current_pos.week_ending.strftime(self.movement_date_format)
                    to_date = next_pos.week_ending if isinstance(next_pos.week_ending, str) else next_pos.week_ending.strftime(self.movement_date_format)
                    
                    movement = MovementEvent(
                        employee_number=employee_number,
                        from_position=current_pos.position_key,
                        to_position=next_pos.position_key,
                        from_date=from_date,
                        to_date=to_date,
                        movement_type=movement_type
                    )
                    
                    if self._should_track_movement(movement_type):
                        movements.append(movement)
                        
                except Exception as e:
                    logger.debug(f"Failed to create movement for employee {employee_number}: {e}")
        
        return movements
    
    def _should_track_movement(self, movement_type: str) -> bool:
        """Determine if we should track this type of movement."""
        if movement_type == 'lateral' and not self.track_lateral_moves:
            return False
        if movement_type == 'promotion' and not self.track_promotions:
            return False
        if movement_type == 'department_change' and not self.track_department_changes:
            return False
        return True
    
    def get_arterial_routes(self, min_frequency: int = None) -> List[Tuple[Tuple[int, int], int]]:
        """
        Get arterial routes (common movement pathways) sorted by frequency.
        
        Args:
            min_frequency: Minimum frequency threshold (default: from config)
            
        Returns:
            List of ((from_position, to_position), frequency) tuples
        """
        if min_frequency is None:
            min_frequency = self.min_movement_frequency
        
        # Count transition frequencies
        transition_counts = Counter()
        for movement in self.movement_events:
            transition_counts[movement.transition_key] += 1
        
        # Filter by minimum frequency and sort by frequency (descending)
        arterial_routes = [
            (transition, count) for transition, count in transition_counts.items()
            if count >= min_frequency
        ]
        
        return sorted(arterial_routes, key=lambda x: x[1], reverse=True)
    
    def get_employee_journey(self, employee_number: int) -> List[ColleaguePosition]:
        """
        Get the position journey for a specific employee.
        
        Args:
            employee_number: The employee to track
            
        Returns:
            List of positions in chronological order
        """
        return self.employee_histories.get(employee_number, [])
    
    def get_movement_summary(self) -> Dict[str, Any]:
        """Get summary statistics about detected movements."""        
        movement_types = Counter(event.movement_type for event in self.movement_events)
        
        if not self.movement_events:
            return {
                "total_movements": 0,
                "total_employees": len(self.employee_histories),
                "unique_employees_with_movements": 0,
                "movement_types": {},
                "arterial_routes_count": 0,
                "status": "No movements detected"
            }
        
        return {
            "total_movements": len(self.movement_events),
            "total_employees": len(self.employee_histories),
            "unique_employees_with_movements": len(set(event.employee_number for event in self.movement_events)),
            "movement_types": dict(movement_types),
            "arterial_routes_count": len(self.get_arterial_routes()),
            "date_range": {
                "earliest": min(event.from_date for event in self.movement_events),
                "latest": max(event.to_date for event in self.movement_events)
            }
        }
    
    def export_movements_to_parquet(self, output_path: str) -> None:
        """Export movements to Parquet format using configured export settings."""
        if not self.movement_events:
            logger.warning("No movements to export")
            return
        
        # Convert to DataFrame
        data = [event.to_dict() for event in self.movement_events]
        df = pd.DataFrame(data)
        
        # Use configured parquet export settings - NO hardcoded index=False
        export_kwargs = {
            'index': self.parquet_export_settings.get('index', False),
            'compression': self.parquet_export_settings.get('compression', 'snappy'),
            'engine': self.parquet_export_settings.get('engine', 'pyarrow')
        }
        
        # Export to Parquet with configured settings
        df.to_parquet(output_path, **export_kwargs)
        print(f"📄 Exported {len(self.movement_events):,} movements to {output_path}")
    
    def export_movements_to_csv(self, output_path: str) -> None:
        """Export movements to CSV format using configured export settings."""
        if not self.movement_events:
            logger.warning("No movements to export")
            return
        
        # Convert to DataFrame
        data = [event.to_dict() for event in self.movement_events]
        df = pd.DataFrame(data)
        
        # Use configured CSV export settings - NO hardcoded index=False
        export_kwargs = {
            'index': self.csv_export_settings.get('index', False),
            'encoding': self.csv_export_settings.get('encoding', 'utf-8')
        }
        
        # Export to CSV with configured settings
        df.to_csv(output_path, **export_kwargs)
        print(f"📄 Exported {len(self.movement_events):,} movements to {output_path}")
    
    def __len__(self) -> int:
        """Return the number of movement events detected."""
        return len(self.movement_events)
    
    def load_position_mappings(self, positions_directory: str) -> int:
        """
        Load position mappings from positions CSV files to enrich colleague positions.
        
        Args:
            positions_directory: Directory containing d_positions_fy*.csv files
            
        Returns:
            Number of position mappings loaded
        """
        print(f"📋 Loading position mappings from {positions_directory}")
        
        positions_path = Path(positions_directory)
        
        # Try multiple file patterns in order of preference
        patterns_to_try = [
            "d_positions_fy*.csv",
            "positions_fy*.csv", 
            "positions.csv",
            "position_id_to_job_profile.csv"
        ]
        
        csv_files = []
        pattern_used = None
        
        for pattern in patterns_to_try:
            csv_files = list(positions_path.glob(pattern))
            if csv_files:
                pattern_used = pattern
                print(f"✅ Found {len(csv_files)} files matching pattern: {pattern}")
                break
        
        if not csv_files:
            logger.warning(f"⚠️ No position files found in {positions_directory}")
            logger.warning(f"   Tried patterns: {', '.join(patterns_to_try)}")
            logger.warning(f"   Movement detection will use PosIDLookupKey directly")
            return 0
        
        total_loaded = 0
        
        # Use SSE's progress tracking for position file loading
        with ProgressTracker(
            total=len(csv_files),
            desc="Loading position mapping files"
        ) as progress:
            
            for csv_file in sorted(csv_files):
                logger.debug(f"  📄 Loading {csv_file.name}")
                file_loaded = 0
                
                try:
                    with open(csv_file, 'r', encoding='utf-8') as file:
                        reader = csv.DictReader(file)
                        
                        # Check which column scheme we're dealing with
                        headers = reader.fieldnames or []
                        has_position_number = 'Position Number' in headers
                        has_job_profile = 'Job_Profile_ID' in headers
                        
                        if not has_position_number and not has_job_profile:
                            logger.warning(f"    ⚠️ File missing required columns. Need either 'Position Number' or 'Job_Profile_ID'")
                            progress.update(1)
                            continue
                        
                        for row in reader:
                            # Handle BOM in first column if present
                            clean_row = {}
                            for key, value in row.items():
                                clean_key = key.lstrip('\ufeff') if isinstance(key, str) else key
                                clean_row[clean_key] = value
                            
                            try:
                                # Get PosIDLookupKey (always required)
                                pos_id_lookup = float(clean_row['PosIDLookupKey'])
                                
                                if has_position_number:
                                    # Direct Position Number mapping
                                    position_number = int(clean_row['Position Number'])
                                    self.position_mappings[pos_id_lookup] = position_number
                                    file_loaded += 1
                                elif has_job_profile:
                                    # Job Profile mapping (use profile ID as position identifier)
                                    job_profile_id = clean_row['Job_Profile_ID']
                                    # Convert job profile to a numeric position ID for consistency
                                    position_id = hash(job_profile_id) % (10**8)  # Convert to 8-digit positive int
                                    self.position_mappings[pos_id_lookup] = position_id
                                    file_loaded += 1
                                    
                            except (ValueError, KeyError) as e:
                                logger.debug(f"    ⚠️ Skipping invalid row: {e}")
                                continue
                    
                    total_loaded += file_loaded
                    logger.debug(f"  ✅ Loaded {file_loaded:,} positions from {csv_file.name}")
                    progress.update(1)
                    
                except Exception as e:
                    logger.error(f"  ❌ Error loading {csv_file.name}: {e}")
                    progress.update(1)
                    continue
        
        print(f"✅ Total position mappings loaded: {total_loaded:,}")
        print(f"📋 Unique position mappings: {len(self.position_mappings):,}")
        
        # Debug: Show sample mappings
        if self.position_mappings:
            sample_mappings = list(self.position_mappings.items())[:3]
            logger.debug(f"🔍 Sample mappings:")
            for lookup_key, position_id in sample_mappings:
                logger.debug(f"    {lookup_key} → {position_id}")
        
        return len(self.position_mappings)
    
    def enrich_colleague_positions_with_position_numbers(self) -> None:
        """Enrich colleague positions with actual Position Numbers from mappings using configured calculation."""
        if not self.position_mappings:
            print("⚠️ No position mappings available - movements will be tracked by PosIDLookupKey")
            return
        
        print("🔗 Enriching colleague positions with actual Position Numbers...")
        
        enriched_count = 0
        missing_count = 0
        
        for colleague_position in self.colleague_positions:
            # Convert PosIDLookupKey to float for lookup
            try:
                pos_id_lookup = float(colleague_position.pos_id_lookup_key)
                
                if pos_id_lookup in self.position_mappings:
                    colleague_position.position_number = self.position_mappings[pos_id_lookup]
                    enriched_count += 1
                else:
                    missing_count += 1
            except (ValueError, TypeError):
                missing_count += 1
                continue
        
        # Use configured enrichment rate calculation - NO hardcoded * 100
        if self.enrichment_rate_calculation and self.colleague_positions:
            enrichment_rate = (enriched_count / len(self.colleague_positions) * self.enrichment_percentage_multiplier)
        else:
            enrichment_rate = 0
        
        print(f"✅ Enriched {enriched_count:,} positions, {missing_count:,} missing mappings")
        print(f"📊 Enrichment rate: {enrichment_rate:.1f}%")
        
        if missing_count > 0:
            logger.warning(f"⚠️ {missing_count:,} positions could not be mapped to Position Numbers")
            logger.warning("   These will use PosIDLookupKey for movement tracking")
    
    def load_with_position_enrichment(self, colleague_positions_dir: str, positions_dir: str, pattern: str = None) -> None:
        """
        Load colleague positions and enrich them with Position Numbers for accurate movement detection.
        
        Args:
            colleague_positions_dir: Directory containing colleague position CSV files
            positions_dir: Directory containing position mapping CSV files  
            pattern: Pattern for colleague position files
        """
        print("🚀 Loading data with position enrichment...")
        
        # Step 1: Load position mappings
        print("📋 Step 1: Loading position mappings...")
        mappings_loaded = self.load_position_mappings(positions_dir)
        print(f"✅ Loaded {mappings_loaded:,} position mappings")
        
        # Step 2: Load colleague positions
        print("👥 Step 2: Loading colleague positions...")
        self.load_from_directory(colleague_positions_dir, pattern)
        
        # Step 3: Enrich colleague positions with Position Numbers
        print("🔗 Step 3: Enriching positions with Position Numbers...")
        self.enrich_colleague_positions_with_position_numbers()
        
        print("✅ Data loading with position enrichment completed successfully")

    def __str__(self) -> str:
        """String representation of the tracker."""
        return f"MovementTracker(positions={len(self.colleague_positions)}, movements={len(self.movement_events)}, employees={len(self.employee_histories)})" 