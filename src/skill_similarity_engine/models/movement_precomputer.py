"""
Movement Analysis Precompute Module

Integrates Position Transition History (PTH) movement detection into SSE's 
precompute workflow for quarterly model generation and analysis.

This module follows SSE's precompute patterns while applying PTH's 
enterprise-grade object-oriented design.

Architecture: Configuration-driven with ZERO hardcoded values
All parameters externalized to architectural configuration.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

from .movement_tracker import MovementTracker
from .versioning import ModelVersionManager
from ..utils.performance import get_memory_usage, MemoryUsage
from ..config.workforce_config_loader import get_workforce_config_loader
from ..config.architectural_config_manager import get_config_manager

logger = logging.getLogger(__name__)


class MovementPrecomputer:
    """
    Precompute movement analysis following SSE's quarterly model generation patterns.
    
    Integrates PTH's movement detection algorithms with SSE's performance utilities,
    model versioning, and export infrastructure.
    
    ZERO hardcoded values - all parameters from architectural configuration.
    """
    
    def __init__(self, config_loader=None):
        """Initialize with configuration-driven parameters."""
        self.config_loader = config_loader or get_workforce_config_loader()
        self.config_manager = get_config_manager()
        self.movement_tracker = MovementTracker(config_loader)
        self.version_manager = ModelVersionManager()
        
        # Get precompute configuration - NO hardcoded values
        precompute_config = self.config_manager.get_models_precompute_config()
        self.enable_memory_monitoring = precompute_config.get('enable_memory_monitoring', True)
        self.memory_warning_threshold_mb = precompute_config.get('memory_warning_threshold_mb', 1000)
        self.export_individual_movements = precompute_config.get('export_individual_movements', True)
        self.export_movement_summary = precompute_config.get('export_movement_summary', True)
        self.export_metadata = precompute_config.get('export_metadata', True)
        
        # Get export configuration - NO hardcoded export settings
        export_config = self.config_manager.get_models_export_settings()
        self.parquet_compression = export_config.get('parquet_export', {}).get('compression', 'snappy')
        self.parquet_engine = export_config.get('parquet_export', {}).get('engine', 'pyarrow')
        
        # Get timestamp configuration - NO hardcoded timestamp formats
        date_formats = self.config_manager.get_models_date_formats()
        self.run_timestamp_format = date_formats.get('run_timestamp_format', '%Y%m%d_%H%M%S')
        self.metadata_timestamp_format = date_formats.get('metadata_timestamp_format', '%Y-%m-%d %H:%M:%S')
        
        # Get directory configuration - NO hardcoded directory names
        directories = self.config_manager.get_models_directories_config()
        self.movement_analysis_subdir = directories.get('movement_analysis_subdir', 'movement_analysis')
        
        logger.info("🏗️ MovementPrecomputer initialized with configuration-driven parameters")
    
    def generate_movement_analysis(self, 
                                 colleague_positions_dir: str,
                                 positions_dir: str,
                                 output_type: str = None) -> Dict[str, Any]:
        """
        Generate complete movement analysis using SSE precompute patterns.
        
        Args:
            colleague_positions_dir: Directory containing colleague position CSV files
            positions_dir: Directory containing position mapping CSV files
            output_type: Type of output for versioning (default from config)
            
        Returns:
            Dictionary containing analysis results and metadata
        """
        logger.info("🚀 Starting movement analysis precompute...")
        
        # Initialize memory tracking if configured
        initial_memory = None
        if self.enable_memory_monitoring:
            initial_memory = get_memory_usage()
            logger.info(f"📊 Memory monitoring enabled (warning threshold: {self.memory_warning_threshold_mb}MB)")
            logger.info(f"📊 Initial memory usage: {initial_memory.current_process_usage_mb:.1f}MB")
        
        try:
            # Step 1: Load data with position enrichment
            logger.info("📊 Step 1: Loading and enriching data...")
            self.movement_tracker.load_with_position_enrichment(
                colleague_positions_dir, 
                positions_dir
            )
            
            if self.enable_memory_monitoring:
                current_memory = get_memory_usage()
                if current_memory.current_process_usage_mb > self.memory_warning_threshold_mb:
                    logger.warning(f"⚠️ High memory usage after data loading: {current_memory.current_process_usage_mb:.1f}MB")
            
            # Step 2: Detect movements
            logger.info("🔍 Step 2: Detecting movements...")
            self.movement_tracker.detect_movements()
            
            movement_summary = self.movement_tracker.get_movement_summary()
            logger.info(f"✅ Detected {movement_summary['total_movements']:,} movements")
            
            if self.enable_memory_monitoring:
                current_memory = get_memory_usage()
                logger.info(f"📊 Memory usage after movement detection: {current_memory.current_process_usage_mb:.1f}MB")
            
            # Step 3: Generate outputs using versioning
            logger.info("📁 Step 3: Generating versioned outputs...")
            output_type_str = output_type or self.movement_analysis_subdir
            output_dir = self.version_manager.setup_output_directory(
                interactive=False,
                output_type=output_type_str
            )
            
            # Export results based on configuration
            exported_files = {}
            
            if self.export_individual_movements:
                movements_file = output_dir / "employee_movements.parquet"
                self.movement_tracker.export_movements_to_parquet(str(movements_file))
                exported_files['movements'] = str(movements_file)
                logger.info(f"✅ Exported individual movements: {movements_file.name}")
            
            if self.export_movement_summary:
                summary_file = output_dir / "movement_summary.parquet"
                self._export_movement_summary(str(summary_file), movement_summary)
                exported_files['summary'] = str(summary_file)
                logger.info(f"✅ Exported movement summary: {summary_file.name}")
            
            if self.export_metadata:
                metadata_file = output_dir / "metadata.json"
                metadata = self._generate_metadata(movement_summary, initial_memory)
                self._export_metadata(str(metadata_file), metadata)
                exported_files['metadata'] = str(metadata_file)
                logger.info(f"✅ Exported metadata: {metadata_file.name}")
            
            # Note: Current symlink is handled automatically by setup_output_directory
            logger.info(f"📁 Model version setup complete")
            
            logger.info("🎉 Movement analysis precompute completed successfully")
            logger.info(f"📁 Output directory: {output_dir}")
            
            return {
                'success': True,
                'output_directory': str(output_dir),
                'movement_summary': movement_summary,
                'exported_files': exported_files,
                'memory_initial_mb': initial_memory.current_process_usage_mb if initial_memory else None
            }
            
        except Exception as e:
            logger.error(f"❌ Movement analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'output_directory': None,
                'movement_summary': None,
                'exported_files': {},
                'memory_initial_mb': initial_memory.current_process_usage_mb if initial_memory else None
            }
    
    def _export_movement_summary(self, output_path: str, summary_data: Dict[str, Any]) -> None:
        """Export movement summary to Parquet using configured settings."""
        # Create position-month level summary data for time series analysis
        summary_records = []
        
        # Generate basic summary record
        summary_record = {
            'analysis_timestamp': datetime.now().strftime(self.metadata_timestamp_format),
            'total_movements': summary_data.get('total_movements', 0),
            'total_employees': summary_data.get('total_employees', 0),
            'total_positions': summary_data.get('total_positions', 0),
            'analysis_period_start': summary_data.get('analysis_period_start', ''),
            'analysis_period_end': summary_data.get('analysis_period_end', ''),
        }
        
        # Add movement type breakdown if available
        movement_types = summary_data.get('movement_types', {})
        for movement_type, count in movement_types.items():
            summary_record[f'movements_{movement_type}'] = count
        
        summary_records.append(summary_record)
        
        # Export using configured parquet settings
        if summary_records:
            df = pd.DataFrame(summary_records)
            df.to_parquet(
                output_path, 
                index=False,
                compression=self.parquet_compression,
                engine=self.parquet_engine
            )
        else:
            # Create empty DataFrame with schema
            df = pd.DataFrame(columns=['analysis_timestamp', 'total_movements'])
            df.to_parquet(
                output_path,
                index=False,
                compression=self.parquet_compression,
                engine=self.parquet_engine
            )
    
    def _generate_metadata(self, movement_summary: Dict[str, Any], initial_memory: Optional[MemoryUsage]) -> Dict[str, Any]:
        """Generate analysis metadata using configured timestamp format."""
        operational_config = self.config_loader.load_operational_config()
        
        metadata = {
            'analysis_info': {
                'run_timestamp': datetime.now().strftime(self.metadata_timestamp_format),
                'run_id': datetime.now().strftime(self.run_timestamp_format),
                'analysis_type': 'workforce_movement_analysis',
                'version': '1.0'
            },
            'configuration': {
                'memory_monitoring': self.enable_memory_monitoring,
                'memory_warning_threshold_mb': self.memory_warning_threshold_mb,
                'export_individual_movements': self.export_individual_movements,
                'export_movement_summary': self.export_movement_summary,
                'parquet_compression': self.parquet_compression
            },
            'data_processing': {
                'total_movements': movement_summary.get('total_movements', 0),
                'total_employees': movement_summary.get('total_employees', 0),
                'total_positions': movement_summary.get('total_positions', 0),
                'analysis_period': {
                    'start': movement_summary.get('analysis_period_start', ''),
                    'end': movement_summary.get('analysis_period_end', '')
                }
            },
            'system_info': {
                'memory_initial_mb': initial_memory.current_process_usage_mb if initial_memory else None,
                'quarter': self.version_manager.get_current_quarter()
            }
        }
        
        return metadata
    
    def _export_metadata(self, output_path: str, metadata: Dict[str, Any]) -> None:
        """Export metadata to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def get_analysis_status(self) -> Dict[str, Any]:
        """Get current analysis status and configuration."""
        return {
            'precomputer_ready': True,
            'movement_tracker_ready': self.movement_tracker is not None,
            'version_manager_ready': self.version_manager is not None,
            'memory_monitoring_enabled': self.enable_memory_monitoring,
            'memory_warning_threshold_mb': self.memory_warning_threshold_mb,
            'export_settings': {
                'individual_movements': self.export_individual_movements,
                'movement_summary': self.export_movement_summary,
                'metadata': self.export_metadata,
                'parquet_compression': self.parquet_compression,
                'parquet_engine': self.parquet_engine
            },
            'current_quarter': self.version_manager.get_current_quarter(),
            'movement_analysis_subdir': self.movement_analysis_subdir
        }
    
    def __str__(self) -> str:
        """String representation of the precomputer."""
        return f"MovementPrecomputer(memory_monitoring={self.enable_memory_monitoring}, quarter={self.version_manager.get_current_quarter()})"


# Factory function for creating movement precomputer
def create_movement_precomputer(config_loader=None) -> MovementPrecomputer:
    """
    Create a movement precomputer instance with configuration.
    
    Args:
        config_loader: Optional configuration loader
        
    Returns:
        Configured MovementPrecomputer instance
    """
    return MovementPrecomputer(config_loader)


# Configuration class for precompute parameters
class MovementPrecomputeConfig:
    """Configuration class for movement precompute operations."""
    
    def __init__(self, 
                 export_csv: bool = True,
                 export_parquet: bool = True,
                 min_movement_frequency: int = 1,
                 detection_window_weeks: int = 999,
                 min_position_tenure_weeks: int = 1):
        self.export_csv = export_csv
        self.export_parquet = export_parquet
        self.min_movement_frequency = min_movement_frequency
        self.detection_window_weeks = detection_window_weeks
        self.min_position_tenure_weeks = min_position_tenure_weeks 