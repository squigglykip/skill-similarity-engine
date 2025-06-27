"""
Skills Library Updater

Integrates the Lightcast API client and endpoint extractor to update the skills library
data used by the skill similarity engine.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from .lightcast_client import LightcastSkillsClient
from .endpoint_extractor import EndpointExtractor
from ..utils.progress import ProgressTracker


class SkillsLibraryUpdater:
    """Updates the skills library from Lightcast API"""
    
    def __init__(self, 
                 credentials_file: str = "credentials.json",
                 skills_library_dir: str = "data/skills_library"):
        """
        Initialize the skills library updater
        
        Args:
            credentials_file: Path to Lightcast API credentials
            skills_library_dir: Directory containing skills library files
        """
        self.credentials_file = credentials_file
        self.skills_library_dir = Path(skills_library_dir)
        self.client = None
        
    def _ensure_credentials(self) -> bool:
        """Check if credentials file exists"""
        credentials_path = Path(self.credentials_file)
        
        # Check in current directory
        if credentials_path.exists():
            return True
            
        # Check in API directory
        api_credentials = Path("src/skill_similarity_engine/api") / self.credentials_file
        if api_credentials.exists():
            self.credentials_file = str(api_credentials)
            return True
            
        # Check in root directory
        root_credentials = Path(".") / self.credentials_file
        if root_credentials.exists():
            self.credentials_file = str(root_credentials)
            return True
            
        return False
    
    def _initialize_client(self) -> bool:
        """Initialize the Lightcast API client"""
        if not self._ensure_credentials():
            print(f"âŒ ERROR: Credentials file '{self.credentials_file}' not found")
            print("   Please ensure you have a valid Lightcast API credentials file")
            print("   Expected format: {'CLIENT_ID': 'your_id', 'CLIENT_SECRET': 'your_secret'}")
            return False
            
        try:
            self.client = LightcastSkillsClient.from_credentials_file(self.credentials_file)
            
            # Test the connection
            status = self.client.get_status()
            if not status.get("data", {}).get("healthy", False):
                print("âŒ ERROR: Lightcast API is not healthy")
                return False
                
            print("âœ… Successfully connected to Lightcast API")
            return True
            
        except Exception as e:
            print(f"âŒ ERROR: Failed to initialize Lightcast API client: {e}")
            return False
    
    def check_for_updates(self) -> Dict[str, Any]:
        """
        Check if there are updates available for the skills library
        
        Returns:
            Dict with update information
        """
        if not self.client and not self._initialize_client():
            return {"error": "Failed to initialize API client"}
        
        # At this point, self.client is guaranteed to be initialized
        assert self.client is not None
        
        try:
            # Get current version from local files
            current_version = self._get_current_version()
            
            # Get latest version from API
            latest_meta = self.client.get_version_metadata("latest")
            latest_version = latest_meta["data"]["version"]
            
            # Get skill counts
            current_count = self._get_current_skill_count()
            latest_count = latest_meta["data"]["skillCount"]
            
            update_info = {
                "current_version": current_version,
                "latest_version": latest_version,
                "current_skill_count": current_count,
                "latest_skill_count": latest_count,
                "update_available": current_version != latest_version,
                "skill_count_changed": current_count != latest_count
            }
            
            return update_info
            
        except Exception as e:
            return {"error": f"Failed to check for updates: {e}"}
    
    def _get_current_version(self) -> Optional[str]:
        """Get the current version from local files"""
        try:
            version_file = self.skills_library_dir / "version_latest.csv"
            if not version_file.exists():
                return None
                
            # Read the version from CSV (it's in the last column)
            with open(version_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    # Parse the CSV data (it's quoted)
                    data_line = lines[1].strip()
                    # Extract version from the end of the line (last quoted field)
                    version = data_line.split('","')[-1].strip('"')
                    return version
                    
        except Exception as e:
            print(f"Warning: Could not read current version: {e}")
            
        return None
    
    def _get_current_skill_count(self) -> int:
        """Get the current skill count from local files"""
        try:
            version_file = self.skills_library_dir / "version_latest.csv"
            if not version_file.exists():
                return 0
                
            with open(version_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    # Parse the CSV data to get skill count (3rd column)
                    data_line = lines[1].strip()
                    fields = data_line.split('","')
                    if len(fields) >= 3:
                        skill_count_str = fields[2].strip('"')
                        return int(skill_count_str)
                        
        except Exception as e:
            print(f"Warning: Could not read current skill count: {e}")
            
        return 0
    
    def update_skills_library(self, backup_existing: bool = True) -> bool:
        """
        Update the skills library from the Lightcast API
        
        Args:
            backup_existing: Whether to backup existing files before updating
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self.client and not self._initialize_client():
            return False
        
        # At this point, self.client is guaranteed to be initialized
        assert self.client is not None
        
        try:
            print(f"\nðŸ”„ Starting skills library update...")
            
            # Define update steps
            update_steps = [
                ("Backup existing files", lambda: self._backup_existing_files() if backup_existing else None),
                ("Initialize extractor", lambda: EndpointExtractor(self.client, str(self.skills_library_dir.parent))),
                ("Extract API data", None),  # Will be handled specially
                ("Move extracted files", None)  # Will be handled specially
            ]
            
            extractor = None
            
            with ProgressTracker(total=len(update_steps), desc="Skills Library Update", show_tqdm=True) as tracker:
                # Step 1: Backup
                if backup_existing:
                    self._backup_existing_files()
                tracker.update(1)
                
                # Step 2: Initialize extractor
                extractor = EndpointExtractor(
                    client=self.client,  # type: ignore[arg-type] # guaranteed non-None by assertion
                    output_dir=str(self.skills_library_dir),
                    use_timestamp=False
                )
                tracker.update(1)
                
                # Step 3: Run extraction
                extractor.run_extraction()
                tracker.update(1)
                
                # Step 4: Files are already in the right place (no move needed)
                # Since we output directly to skills_library, no file moving required
                tracker.update(1)
            
            print(f"âœ… Skills library updated successfully!")
            return True
            
        except Exception as e:
            print(f"âŒ ERROR: Failed to update skills library: {e}")
            return False
    
    def _backup_existing_files(self):
        """Backup existing skills library files"""
        if not self.skills_library_dir.exists():
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.skills_library_dir.parent / f"skills_library_backup_{timestamp}"
        
        print(f"ðŸ“ Creating backup: {backup_dir}")
        shutil.copytree(self.skills_library_dir, backup_dir)
        
        # Clear existing files instead of removing the entire directory (Windows-friendly)
        try:
            for item in self.skills_library_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
        except Exception as e:
            print(f"âš ï¸  Warning: Could not clear some files in skills_library: {e}")
            print("   This may cause file conflicts but won't prevent the update.")
    
    def _move_extracted_files(self, extraction_dir: Path):
        """Move extracted files to the skills library directory"""
        # Ensure the skills library directory exists
        self.skills_library_dir.mkdir(parents=True, exist_ok=True)
        
        # Define the files we want to move
        files_to_move = [
            "meta.csv",
            "status.csv", 
            "versions.csv",
            "version_latest.csv"
        ]
        
        # Move the comprehensive skills file (find the one with version number)
        skills_files = list(extraction_dir.glob("skills_*.csv"))
        comprehensive_file = extraction_dir / "skills_comprehensive_all_versions.csv"
        
        if comprehensive_file.exists():
            files_to_move.append("skills_comprehensive_all_versions.csv")
        elif skills_files:
            # If no comprehensive file, use the latest versioned skills file
            latest_skills_file = skills_files[0]  # Should be the latest
            files_to_move.append(latest_skills_file.name)
            # Also copy it as the comprehensive file
            shutil.copy2(latest_skills_file, self.skills_library_dir / "skills_comprehensive_all_versions.csv")
        
        # Move each file
        for filename in files_to_move:
            src_file = extraction_dir / filename
            if src_file.exists():
                dst_file = self.skills_library_dir / filename
                shutil.copy2(src_file, dst_file)
                print(f"âœ… Updated: {filename}")
            else:
                print(f"âš ï¸  Warning: {filename} not found in extraction")
        
        # Clean up extraction directory
        try:
            shutil.rmtree(extraction_dir)
        except Exception as e:
            print(f"Warning: Could not clean up extraction directory: {e}")


def prompt_skills_update(logger) -> bool:
    """
    Prompt user to update skills library and perform the update if requested
    
    Args:
        logger: Logger instance
        
    Returns:
        True if update was performed (or skipped), False if update failed
    """
    print(f"\nðŸ” Checking for skills library updates...")
    
    updater = SkillsLibraryUpdater()
    
    # Check for updates
    update_info = updater.check_for_updates()
    
    if "error" in update_info:
        print(f"âš ï¸  Could not check for updates: {update_info['error']}")
        print("   Proceeding with existing skills library...")
        return True
    
    # Display update information
    print(f"\nðŸ“Š Skills Library Status:")
    print(f"   Current version: {update_info['current_version'] or 'Unknown'}")
    print(f"   Latest version:  {update_info['latest_version']}")
    print(f"   Current skills:  {update_info['current_skill_count']:,}")
    print(f"   Latest skills:   {update_info['latest_skill_count']:,}")
    
    if update_info['update_available']:
        print(f"   ðŸ†• Version update available!")
    
    if update_info['skill_count_changed']:
        skill_diff = update_info['latest_skill_count'] - update_info['current_skill_count']
        if skill_diff > 0:
            print(f"   ðŸ“ˆ {skill_diff:,} new skills available")
        else:
            print(f"   ðŸ“‰ {abs(skill_diff):,} skills removed")
    
    if not update_info['update_available'] and not update_info['skill_count_changed']:
        print(f"   âœ… Skills library is up to date")
        return True
    
    # Prompt user for update
    print(f"\nâ“ Would you like to update the skills library?")
    print(f"   This will download the latest skills data from Lightcast API")
    print(f"   and may take a few minutes to complete.")
    
    while True:
        choice = input("   Update skills library? [y/N]: ").strip().lower()
        if choice in ['y', 'yes']:
            # Perform the update
            success = updater.update_skills_library(backup_existing=True)
            if success:
                logger.info("Skills library updated successfully")
                return True
            else:
                logger.error("Skills library update failed")
                print("âŒ Update failed. Proceeding with existing skills library...")
                return True  # Continue with existing data
        elif choice in ['n', 'no', '']:
            print("ðŸ“‹ Proceeding with existing skills library...")
            return True
        else:
            print("   Please enter 'y' or 'n'") 
