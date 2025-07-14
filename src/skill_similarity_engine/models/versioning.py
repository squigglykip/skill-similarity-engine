"""
Model Versioning and Output Management

This module handles the versioning strategy for precomputed similarity matrices,
including quarterly directory management, conflict resolution for multiple runs
within the same quarter, and maintaining symlinks to current versions.

The versioning scheme is now configuration-driven following PTH's architecture.
NO hardcoded values - everything externalized to architectural configuration.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

from ..config.architectural_config_manager import get_config_manager

logger = logging.getLogger(__name__)


class ModelVersionManager:
    """Manages model versioning and output directory structure using configuration-driven approach."""
    
    def __init__(self, base_models_dir: Optional[str] = None):
        """
        Initialize version manager with configuration-driven defaults.
        
        Args:
            base_models_dir: Optional override for base directory (uses config if None)
        """
        self.config_manager = get_config_manager()
        
        # Get directories configuration - NO hardcoded "models" directory
        directories_config = self.config_manager.get_models_directories_config()
        self.base_models_dir = Path(base_models_dir or directories_config.get('base_models_dir', 'models'))
        
        # Get output types and file patterns from configuration
        models_config = self.config_manager.get_models_config()
        self.output_types = models_config.get('output_types', {})
        self.file_patterns = models_config.get('file_patterns', {})
        
        # Get versioning patterns from configuration
        versioning_config = models_config.get('versioning_patterns', {})
        self.quarterly_pattern = versioning_config.get('quarterly_pattern', '%Y-Q%q')
        self.daily_pattern = versioning_config.get('daily_pattern', '%Y-%m-%d')
        self.timestamp_pattern = versioning_config.get('timestamp_pattern', '%Y%m%d_%H%M%S')
        self.date_stamp_pattern = versioning_config.get('date_stamp_pattern', '%Y%m%d')
        
        # Get daily folder strategy configuration
        self.daily_strategy = models_config.get('daily_folder_strategy', {})
        self.daily_enabled = self.daily_strategy.get('enabled', True)
        self.consolidate_precomputes = self.daily_strategy.get('consolidate_precomputes', True)
        self.overwrite_within_day = self.daily_strategy.get('overwrite_within_day', True)
        
        # Get validation settings from configuration
        validation_config = self.config_manager.get_models_validation_config()
        self.min_year = validation_config.get('min_year', 1900)
        self.max_year = validation_config.get('max_year', 2100)
        self.valid_quarters = validation_config.get('valid_quarters', [1, 2, 3, 4])
        self.win_error_symlink = validation_config.get('win_error_symlink', 1314)
    
    def get_current_quarter(self) -> str:
        """Get current quarter using configuration format."""
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        return f"{now.year}-Q{quarter}"
    
    def get_current_daily_folder(self) -> str:
        """Get current daily folder name using configuration format."""
        now = datetime.now()
        return now.strftime(self.daily_pattern)
    
    def get_daily_output_directory(self, 
                                 custom_quarter: Optional[str] = None,
                                 custom_daily: Optional[str] = None) -> Path:
        """
        Get the daily output directory path following the new strategy.
        
        Args:
            custom_quarter: Optional custom quarter (default: current quarter)
            custom_daily: Optional custom daily folder (default: today)
            
        Returns:
            Path to daily directory: models/2025-Q3/2025-07-10/
        """
        quarter = custom_quarter or self.get_current_quarter()
        daily = custom_daily or self.get_current_daily_folder()
        
        return self.base_models_dir / quarter / daily
    
    def setup_output_directory(self, 
                              interactive: bool = True,
                              custom_path: Optional[str] = None,
                              output_type: Optional[str] = None) -> Path:
        """
        Set up versioned output directory with enhanced daily folder strategy.
        
        NEW BEHAVIOR: Returns daily folder path for precompute outputs, quarterly for business_context
        
        Args:
            interactive: Whether to prompt user for conflict resolution
            custom_path: Optional custom path (overrides daily/quarterly logic)
            output_type: Type of output (from configuration, defaults to similarity_matrix)
            
        Returns:
            Path to the appropriate output directory:
            - Daily folder for precomputes: models/2025-Q3/2025-07-10/
            - Quarterly folder for business_context: models/2025-Q3/
        """
        # Use configured default output type if none specified
        if output_type is None:
            output_type = self.output_types.get('similarity_matrix', 'similarity_matrix')
        
        # Ensure output_type is now guaranteed to be a string
        assert output_type is not None
        
        if custom_path:
            output_dir = Path(custom_path)
            logger.info(f"Using custom output directory: {output_dir}")
            return output_dir
        
        # NEW STRATEGY: Check if daily folder strategy is enabled and determine output level
        if self.daily_enabled and self._should_use_daily_folder(output_type):
            # Use daily folder for precompute outputs
            output_dir = self.get_daily_output_directory()
            logger.info(f"Using daily folder strategy: {output_dir}")
            
            # Handle conflicts at daily level if interactive
            if output_dir.exists() and interactive and not self.overwrite_within_day:
                output_dir = self._handle_daily_directory_conflict(output_dir, output_type)
                
        else:
            # Use quarterly folder for business_context or when daily strategy disabled
            current_quarter = self.get_current_quarter()
            output_dir = self.base_models_dir / current_quarter
            logger.info(f"Using quarterly folder: {output_dir}")
            
            # Handle conflicts at quarterly level if interactive
            if output_dir.exists() and interactive:
                output_dir = self._handle_directory_conflict(output_dir, output_type)
        
        # Create appropriate directory structure
        if self.daily_enabled and self._should_use_daily_folder(output_type):
            self._create_daily_directory_structure(output_dir)
        else:
            # Only create subdirectories for precompute output types, not business_context
            if output_type != self.output_types.get('business_context', 'business_context'):
                self._create_directory_structure(output_dir)
            else:
                # For business_context, just create the main directory without subdirectories
                output_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created business context directory without subdirectories: {output_dir}")
        
        # Update current symlink for quarterly directories
        quarterly_dir = output_dir if not self._should_use_daily_folder(output_type) else output_dir.parent
        if quarterly_dir.parent == self.base_models_dir:
            self._update_current_symlink(quarterly_dir)
        
        logger.info(f"Output directory ready: {output_dir}")
        return output_dir
    
    def _should_use_daily_folder(self, output_type: str) -> bool:
        """
        Determine if the given output type should use daily folder strategy.
        
        Args:
            output_type: Type of output being generated
            
        Returns:
            True if should use daily folder, False for quarterly folder
        """
        business_context_type = self.output_types.get('business_context', 'business_context')
        
        # Business context stays at quarterly level, everything else goes to daily
        return output_type != business_context_type
    
    def _handle_daily_directory_conflict(self, daily_dir: Path, output_type: str) -> Path:
        """
        Handle conflicts when daily directory already exists.
        
        Args:
            daily_dir: The conflicting daily directory path
            output_type: Type of output being generated
            
        Returns:
            Path to use (may create new daily folder with timestamp)
        """
        print(f"[INFO] Daily folder already exists: {daily_dir}")
        print("Daily folder strategy allows same-day overwrites by default.")
        
        if self.overwrite_within_day:
            print("[INFO] Overwriting files within same day as configured.")
            return daily_dir
        
        print("\nOptions:")
        print("1. Overwrite files in existing daily folder")
        print("2. Create new timestamped daily folder")
        print("3. Cancel and specify custom location")
        
        while True:
            choice = input("Choose option [1/2/3]: ").strip()
            
            if choice == '1':
                print("Will overwrite existing files in daily folder.")
                return daily_dir
                
            elif choice == '2':
                # Create timestamped variant of daily folder
                timestamp = datetime.now().strftime(self.timestamp_pattern)
                timestamped_daily = daily_dir.parent / f"{daily_dir.name}_{timestamp}"
                print(f"Using timestamped daily folder: {timestamped_daily}")
                return timestamped_daily
                
            elif choice == '3':
                custom_path = input("Enter custom output directory: ").strip()
                custom_dir = Path(custom_path)
                print(f"Using custom location: {custom_dir}")
                return custom_dir
                
            else:
                print("Please enter 1, 2, or 3.")
    
    def _create_daily_directory_structure(self, daily_dir: Path) -> None:
        """
        Create the directory structure for daily folders.
        
        Args:
            daily_dir: Daily directory to create (models/2025-Q3/2025-07-10/)
        """
        # Create the daily directory
        daily_dir.mkdir(parents=True, exist_ok=True)
        
        # For daily folders, we put files directly in the folder
        # No subdirectories needed based on the strategy
        logger.debug(f"Created daily directory structure: {daily_dir}")
        
        # Ensure parent quarterly directory has the standard structure too
        quarterly_dir = daily_dir.parent
        if not quarterly_dir.exists() or not any(quarterly_dir.iterdir()):
            self._create_directory_structure(quarterly_dir)
    
    def _handle_directory_conflict(self, quarter_dir: Path, output_type: str) -> Path:
        """
        Handle conflicts when output directory already exists.
        
        Args:
            quarter_dir: The conflicting directory path
            output_type: Type of output being generated
            
        Returns:
            Path to use (may be modified for timestamped version)
        """
        # Check for existing outputs of the same type
        existing_outputs = self._check_existing_outputs(quarter_dir, output_type)
        
        if not existing_outputs:
            # No conflict for this output type, proceed with existing directory
            print(f"[INFO] Using existing directory: {quarter_dir}")
            print(f"[INFO] No existing {output_type} outputs found - safe to proceed")
            return quarter_dir
        
        print(f"[WARNING] Output directory already exists: {quarter_dir}")
        print(f"Existing {output_type} outputs found:")
        for output in existing_outputs:
            print(f"  - {output}")
        
        print("\nOptions:")
        print("1. Overwrite existing files (recommended for quarterly refresh)")
        print("2. Create timestamped version (for testing/comparison)")
        print("3. Cancel and specify custom location")
        
        while True:
            choice = input("Choose option [1/2/3]: ").strip()
            
            if choice == '1':
                print("Will overwrite existing files.")
                return quarter_dir
                
            elif choice == '2':
                datestamp = datetime.now().strftime(self.date_stamp_pattern)
                timestamped_dir = quarter_dir.parent / f"{quarter_dir.name}_{datestamp}"
                print(f"Using date-stamped location: {timestamped_dir}")
                return timestamped_dir
                
            elif choice == '3':
                custom_path = input("Enter custom output directory: ").strip()
                custom_dir = Path(custom_path)
                print(f"Using custom location: {custom_dir}")
                return custom_dir
                
            else:
                print("Please enter 1, 2, or 3.")
    
    def _check_existing_outputs(self, quarter_dir: Path, output_type: str) -> list[Path]:
        """
        Check for existing outputs of a specific type in the directory.
        
        Args:
            quarter_dir: Directory to check
            output_type: Type of output to look for
            
        Returns:
            List of existing output files/directories
        """
        existing_outputs = []
        
        # Get file patterns from configuration
        similarity_matrix_type = self.output_types.get('similarity_matrix', 'similarity_matrix')
        business_context_type = self.output_types.get('business_context', 'business_context')
        
        if output_type == similarity_matrix_type:
            # Check for similarity matrix files using configured patterns
            similarity_patterns = [
                self.file_patterns.get('job_similarity_matrix_parquet', 'job_similarity_matrix.parquet'),
                self.file_patterns.get('job_similarity_matrix_csv', 'job_similarity_matrix.csv'),
                self.file_patterns.get('precompute_pattern', 'precompute_*')
            ]
            
            for pattern in similarity_patterns:
                matches = list(quarter_dir.glob(pattern))
                existing_outputs.extend(matches)
                
        elif output_type == business_context_type:
            # Check for business context database using configured pattern
            business_context_file = quarter_dir / self.file_patterns.get('business_context_db', 'business_context.sqlite')
            if business_context_file.exists():
                existing_outputs.append(business_context_file)
                
        return existing_outputs
    
    def _create_directory_structure(self, output_dir: Path) -> None:
        """
        Create the standard directory structure for model outputs using configuration.
        
        Args:
            output_dir: Base output directory
        """
        # Get directory structure from configuration - NO hardcoded directory names
        directories_config = self.config_manager.get_models_directories_config()
        
        subdirectories = [
            output_dir / directories_config.get('similarity_matrices_subdir', 'similarity_matrices'),
            output_dir / directories_config.get('metadata_subdir', 'metadata'),
            output_dir / directories_config.get('validation_subdir', 'validation'),
            output_dir / directories_config.get('powerbi_ready_subdir', 'exports/powerbi_ready'),
            output_dir / directories_config.get('department_analyses_subdir', 'exports/department_analyses')
        ]
        
        for directory in subdirectories:
            directory.mkdir(parents=True, exist_ok=True)
            
        logger.debug(f"Created directory structure in {output_dir}")
    
    def _update_current_symlink(self, quarter_dir: Path) -> None:
        """
        Update the 'current' symlink to point to the latest quarterly version.
        
        Args:
            quarter_dir: Directory to link to
        """
        # Get symlink name from configuration - NO hardcoded "current"
        directories_config = self.config_manager.get_models_directories_config()
        symlink_name = directories_config.get('current_symlink_name', 'current')
        current_symlink = self.base_models_dir / symlink_name
        
        # Remove existing symlink
        if current_symlink.exists():
            current_symlink.unlink()
        
        try:
            # Create new symlink
            current_symlink.symlink_to(quarter_dir.name, target_is_directory=True)
            print(f"Updated '{symlink_name}' symlink to point to {quarter_dir.name}")
            logger.info(f"Updated current symlink: {current_symlink} -> {quarter_dir.name}")
            
        except OSError as e:
            # Symlinks require admin privileges on Windows - this is expected behavior
            if str(self.win_error_symlink) in str(e):
                # Windows privilege error - common and expected
                logger.debug(f"Symlink creation skipped on Windows (requires admin privileges): {e}")
                logger.info(f"Note: models/{symlink_name} symlink not created (Windows requires admin privileges)")
            else:
                # Other OS errors
                print(f"Note: Could not create symlink (models/{symlink_name} -> {quarter_dir.name})")
                logger.warning(f"Symlink creation failed: {e}")
    
    def list_versions(self) -> list[Path]:
        """
        List all existing model versions.
        
        Returns:
            List of version directories
        """
        if not self.base_models_dir.exists():
            return []
        
        # Get symlink name from configuration
        directories_config = self.config_manager.get_models_directories_config()
        symlink_name = directories_config.get('current_symlink_name', 'current')
        
        versions = []
        for item in self.base_models_dir.iterdir():
            if item.is_dir() and item.name != symlink_name:
                versions.append(item)
        
        return sorted(versions, key=lambda x: x.name)
    
    def get_current_version_path(self) -> Optional[Path]:
        """
        Get the path to the current version (via symlink if available).
        
        Returns:
            Path to current version or None if not found
        """
        # Get symlink name from configuration
        directories_config = self.config_manager.get_models_directories_config()
        symlink_name = directories_config.get('current_symlink_name', 'current')
        current_symlink = self.base_models_dir / symlink_name
        
        if current_symlink.exists():
            if current_symlink.is_symlink():
                return current_symlink.resolve()
            elif current_symlink.is_dir():
                return current_symlink
        
        # Fallback: find most recent quarterly version
        versions = self.list_versions()
        quarterly_versions = [v for v in versions if self._is_quarterly_version(v.name)]
        
        if quarterly_versions:
            return max(quarterly_versions, key=lambda x: x.name)
        
        return None
    
    def _is_quarterly_version(self, version_name: str) -> bool:
        """
        Check if a version name follows the quarterly pattern (YYYY-QN).
        
        Args:
            version_name: Name to check
            
        Returns:
            True if it's a quarterly version
        """
        try:
            parts = version_name.split('-')
            if len(parts) != 2:
                return False
            
            year = int(parts[0])
            quarter_part = parts[1]
            
            if not quarter_part.startswith('Q'):
                return False
                
            quarter = int(quarter_part[1:])
            return self.min_year <= year <= self.max_year and quarter in self.valid_quarters
            
        except (ValueError, IndexError):
            return False


def setup_model_output_directory(base_dir: Optional[str] = None, 
                                interactive: bool = True,
                                custom_path: Optional[str] = None,
                                output_type: Optional[str] = None) -> Path:
    """
    Convenience function to set up a versioned model output directory using configuration.
    
    Args:
        base_dir: Base directory for model versions (uses config default if None)
        interactive: Whether to prompt for conflict resolution
        custom_path: Optional custom path
        output_type: Type of output (uses config default if None)
        
    Returns:
        Path to the configured output directory
    """
    manager = ModelVersionManager(base_dir)
    return manager.setup_output_directory(
        interactive=interactive, 
        custom_path=custom_path, 
        output_type=output_type
    ) 
