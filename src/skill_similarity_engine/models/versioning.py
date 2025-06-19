"""
Model Versioning and Output Management

This module handles the versioning strategy for precomputed similarity matrices,
including quarterly directory management, conflict resolution for multiple runs
within the same quarter, and maintaining symlinks to current versions.

The versioning scheme follows: models/YYYY-QN/ (e.g., models/2024-Q4/)
with support for timestamped variants within quarters for testing/comparison.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class ModelVersionManager:
    """Manages model versioning and output directory structure."""
    
    def __init__(self, base_models_dir: str = "models"):
        """
        Initialize version manager.
        
        Args:
            base_models_dir: Base directory for all model versions
        """
        self.base_models_dir = Path(base_models_dir)
    
    def get_current_quarter(self) -> str:
        """Get current quarter in YYYY-QN format."""
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        return f"{now.year}-Q{quarter}"
    
    def setup_output_directory(self, 
                              interactive: bool = True,
                              custom_path: Optional[str] = None,
                              output_type: str = "similarity_matrix") -> Path:
        """
        Set up versioned output directory with conflict resolution.
        
        Args:
            interactive: Whether to prompt user for conflict resolution
            custom_path: Optional custom path (overrides quarterly logic)
            output_type: Type of output ('similarity_matrix', 'business_context', etc.)
            
        Returns:
            Path to the output directory to use
        """
        if custom_path:
            quarter_dir = Path(custom_path)
            logger.info(f"Using custom output directory: {quarter_dir}")
        else:
            current_quarter = self.get_current_quarter()
            quarter_dir = self.base_models_dir / current_quarter
            logger.info(f"Default output location: {quarter_dir}")
        
        # Handle conflicts if directory exists and has conflicting output type
        if quarter_dir.exists() and interactive:
            quarter_dir = self._handle_directory_conflict(quarter_dir, output_type)
        
        # Create directory structure
        self._create_directory_structure(quarter_dir)
        
        # Update current symlink if this is a quarterly version
        if not custom_path and quarter_dir.parent == self.base_models_dir:
            self._update_current_symlink(quarter_dir)
        
        logger.info(f"Output directory ready: {quarter_dir}")
        return quarter_dir
    
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
                datestamp = datetime.now().strftime("%Y%m%d")
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
        
        if output_type == "similarity_matrix":
            # Check for similarity matrix files
            similarity_patterns = [
                "job_similarity_matrix.parquet",
                "job_similarity_matrix.csv",
                "precompute_*"  # Timestamped precompute directories
            ]
            
            for pattern in similarity_patterns:
                matches = list(quarter_dir.glob(pattern))
                existing_outputs.extend(matches)
                
        elif output_type == "business_context":
            # Check for business context database
            business_context_file = quarter_dir / "business_context.sqlite"
            if business_context_file.exists():
                existing_outputs.append(business_context_file)
                
        return existing_outputs
    
    def _create_directory_structure(self, output_dir: Path) -> None:
        """
        Create the standard directory structure for model outputs.
        
        Args:
            output_dir: Base output directory
        """
        directories = [
            output_dir / "similarity_matrices",
            output_dir / "metadata", 
            output_dir / "validation",
            output_dir / "exports" / "powerbi_ready",
            output_dir / "exports" / "department_analyses"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
        logger.debug(f"Created directory structure in {output_dir}")
    
    def _update_current_symlink(self, quarter_dir: Path) -> None:
        """
        Update the 'current' symlink to point to the latest quarterly version.
        
        Args:
            quarter_dir: Directory to link to
        """
        current_symlink = self.base_models_dir / "current"
        
        # Remove existing symlink
        if current_symlink.exists():
            current_symlink.unlink()
        
        try:
            # Create new symlink
            current_symlink.symlink_to(quarter_dir.name, target_is_directory=True)
            print(f"Updated 'current' symlink to point to {quarter_dir.name}")
            logger.info(f"Updated current symlink: {current_symlink} -> {quarter_dir.name}")
            
        except OSError as e:
            # Symlinks require admin privileges on Windows - this is expected behavior
            if "WinError 1314" in str(e):
                # Windows privilege error - common and expected
                logger.debug(f"Symlink creation skipped on Windows (requires admin privileges): {e}")
                logger.info(f"Note: models/current symlink not created (Windows requires admin privileges)")
            else:
                # Other OS errors
                print(f"Note: Could not create symlink (models/current -> {quarter_dir.name})")
                logger.warning(f"Symlink creation failed: {e}")
    
    def list_versions(self) -> list[Path]:
        """
        List all existing model versions.
        
        Returns:
            List of version directories
        """
        if not self.base_models_dir.exists():
            return []
        
        versions = []
        for item in self.base_models_dir.iterdir():
            if item.is_dir() and item.name != "current":
                versions.append(item)
        
        return sorted(versions, key=lambda x: x.name)
    
    def get_current_version_path(self) -> Optional[Path]:
        """
        Get the path to the current version (via symlink if available).
        
        Returns:
            Path to current version or None if not found
        """
        current_symlink = self.base_models_dir / "current"
        
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
            return 1900 <= year <= 2100 and 1 <= quarter <= 4
            
        except (ValueError, IndexError):
            return False


def setup_model_output_directory(base_dir: str = "models", 
                                interactive: bool = True,
                                custom_path: Optional[str] = None,
                                output_type: str = "similarity_matrix") -> Path:
    """
    Convenience function to set up a versioned model output directory.
    
    Args:
        base_dir: Base directory for model versions
        interactive: Whether to prompt for conflict resolution
        custom_path: Optional custom path
        output_type: Type of output ('similarity_matrix', 'business_context', etc.)
        
    Returns:
        Path to the configured output directory
    """
    manager = ModelVersionManager(base_dir)
    return manager.setup_output_directory(
        interactive=interactive, 
        custom_path=custom_path, 
        output_type=output_type
    ) 