"""
Skills Library API Management

This module handles the integration with Lightcast Open Skills API to maintain
an up-to-date, comprehensive skills taxonomy. It manages version tracking,
incremental updates, and CSV generation for downstream business context processing.

Key Features:
- OAuth 2.0 authentication with Lightcast API
- Version tracking and incremental updates 
- Historical skills database maintenance
- CSV export for business context integration
"""

import os
import json
import pandas as pd
import requests
from requests.exceptions import RequestException
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, TextIO
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if it exists
except ImportError:
    pass  # dotenv not available, rely on system environment variables

from ..logging.config import setup_logging


@dataclass
class SkillsLibraryConfig:
    """Configuration for Skills Library API operations."""
    api_base_url: str = "https://emsiservices.com/skills"
    client_id: str = ""
    client_secret: str = ""
    skills_library_path: str = "data/skills_library"
    versions_file: str = "lightcast_versions.json"
    skills_csv_file: str = "lightcast_skills_comprehensive.csv"
    max_retries: int = 3
    timeout_seconds: int = 30
    
    def __post_init__(self):
        """Load credentials from environment variables if not provided."""
        if not self.client_id:
            self.client_id = os.getenv('CLIENT_ID', '')
        if not self.client_secret:
            self.client_secret = os.getenv('CLIENT_SECRET', '')


class SkillsLibraryAPI:
    """
    Manages Lightcast Open Skills API integration for comprehensive skills taxonomy.
    
    This class handles authentication, version management, and incremental updates
    to maintain a complete historical skills database while minimising API calls.
    """
    
    def __init__(self, config: Optional[SkillsLibraryConfig] = None):
        """
        Initialise the Skills Library API manager.
        
        Args:
            config: Configuration object, defaults to SkillsLibraryConfig()
        """
        self.config = config or SkillsLibraryConfig()
        self.logger = setup_logging()
        self.access_token = None
        self.token_expires_at = None
        
        # Ensure directory structure exists
        self.skills_library_dir = Path(self.config.skills_library_path)
        self.skills_library_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up file paths
        self.versions_file_path = self.skills_library_dir / self.config.versions_file
        self.skills_csv_path = self.skills_library_dir / self.config.skills_csv_file
        
    def authenticate(self) -> bool:
        """
        Authenticate with Lightcast API using OAuth 2.0 client credentials flow.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        if not self.config.client_id or not self.config.client_secret:
            self.logger.error("Missing Lightcast API credentials")
            return False
            
        auth_url = "https://auth.emsicloud.com/connect/token"
        
        payload = {
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret,
            'grant_type': 'client_credentials',
            'scope': 'emsi_open'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(
                auth_url,
                data=payload,
                headers=headers,
                timeout=self.config.timeout_seconds
            )
            response.raise_for_status()
            
            auth_data = response.json()
            self.access_token = auth_data['access_token']
            self.token_expires_at = datetime.now().timestamp() + auth_data['expires_in']
            
            self.logger.info("Successfully authenticated with Lightcast API")
            return True
            
        except RequestException as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
    
    def _ensure_authenticated(self) -> bool:
        """
        Ensure we have a valid access token, refreshing if needed.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        if (not self.access_token or 
            not self.token_expires_at or 
            datetime.now().timestamp() >= self.token_expires_at - 300):  # Refresh 5 minutes early
            return self.authenticate()
        return True
    
    def get_available_versions(self) -> List[str]:
        """
        Fetch all available skills data versions from Lightcast API.
        
        Returns:
            List[str]: List of version identifiers, or empty list if failed
        """
        if not self._ensure_authenticated():
            return []
        
        versions_url = f"{self.config.api_base_url}/versions"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.get(
                versions_url, 
                headers=headers,
                timeout=self.config.timeout_seconds
            )
            response.raise_for_status()
            
            versions_data = response.json()
            # Extract version identifiers from API response
            # The API returns simple strings like ["9.31", "9.30", ...] not objects
            versions = versions_data.get('data', [])
            
            self.logger.info(f"Found {len(versions)} available versions")
            return versions
            
        except RequestException as e:
            self.logger.error(f"Failed to fetch available versions: {e}")
            return []
    
    def get_processed_versions(self) -> List[str]:
        """
        Get list of versions already processed and stored locally.
        
        Returns:
            List[str]: List of processed version identifiers
        """
        if not self.versions_file_path.exists():
            self.logger.info("No versions file found, starting fresh")
            return []
        
        try:
            with open(self.versions_file_path, 'r') as f:
                versions_data = json.load(f)
            
            # Handle different file formats:
            # 1. New format: {"processed_versions": ["version1", "version2", ...]} - clean list
            # 2. Legacy format: {"data": [...]} or mixed with individual version keys
            if isinstance(versions_data, dict):
                if 'processed_versions' in versions_data and isinstance(versions_data['processed_versions'], list):
                    # New clean format
                    return versions_data['processed_versions']
                elif 'data' in versions_data and isinstance(versions_data['data'], list):
                    # Legacy format: migrate from 'data' array
                    return versions_data['data']
                else:
                    # Legacy format: individual version keys (excluding 'data')
                    version_keys = [k for k in versions_data.keys() if k != 'data']
                    return version_keys
            
            return []
        except (json.JSONDecodeError, IOError) as e:
            self.logger.warning(f"Could not read versions file: {e}")
            return []
    
    def identify_new_versions(self) -> List[str]:
        """
        Compare available versions with processed versions to find new ones.
        
        Returns:
            List[str]: List of new version identifiers to process
        """
        available_versions = self.get_available_versions()
        processed_versions = set(self.get_processed_versions())
        
        new_versions = [v for v in available_versions if v not in processed_versions]
        
        self.logger.info(f"Found {len(new_versions)} new versions to process")
        return new_versions
    
    def fetch_skills_for_version(self, version: str) -> Optional[List[Dict]]:
        """
        Fetch all skills data for a specific version.
        
        Args:
            version: Version identifier to fetch
            
        Returns:
            List[Dict]: Skills data, or None if failed
        """
        if not self._ensure_authenticated():
            return None
        
        skills_url = f"{self.config.api_base_url}/versions/{version}/skills"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.get(
                skills_url,
                headers=headers,
                timeout=self.config.timeout_seconds
            )
            response.raise_for_status()
            
            skills_data = response.json()
            skills = skills_data.get('data', [])
            
            self.logger.info(f"Fetched {len(skills)} skills for version {version}")
            return skills
            
        except RequestException as e:
            self.logger.error(f"Failed to fetch skills for version {version}: {e}")
            return None
    
    def update_skills_library(self, force_full_refresh: bool = False) -> bool:
        """
        Update the local skills library with new versions from Lightcast API.
        
        Args:
            force_full_refresh: If True, re-process all versions
            
        Returns:
            bool: True if update successful, False otherwise
        """
        self.logger.info("Starting skills library update...")
        
        if force_full_refresh:
            self.logger.info("Forcing full refresh of all versions")
            new_versions = self.get_available_versions()
        else:
            new_versions = self.identify_new_versions()
        
        if not new_versions:
            self.logger.info("No new versions to process")
            return True
        
        # Load existing processed versions list
        processed_versions_list = self.get_processed_versions()
        
        # Process new versions and keep skills data in memory
        new_versions_skills_data = {}
        for version in new_versions:
            self.logger.info(f"Processing version: {version}")
            
            skills = self.fetch_skills_for_version(version)
            if skills is None:
                self.logger.error(f"Failed to fetch skills for version {version}")
                continue
            
            # Store skills data in memory
            new_versions_skills_data[version] = skills
            
            # Add to processed versions list
            processed_versions_list.append(version)
            
            # Update versions file after each successful version
            try:
                with open(self.versions_file_path, 'w', encoding='utf-8') as f:
                    json.dump({"processed_versions": processed_versions_list}, f, indent=2, ensure_ascii=False)  # type: ignore
                self.logger.info(f"Updated versions file with {version}")
            except IOError as e:
                self.logger.error(f"Failed to update versions file: {e}")
        
        # Generate consolidated CSV with pre-fetched skills data
        return self.generate_skills_csv(newly_processed_versions=new_versions, 
                                       new_skills_data=new_versions_skills_data)
    
    def regenerate_full_csv(self) -> bool:
        """
        Regenerate the complete CSV by fetching all processed versions.
        Use this for full refresh or if incremental updates fail.
        
        Returns:
            bool: True if CSV regeneration successful, False otherwise
        """
        self.logger.info("Regenerating complete skills CSV from all versions...")
        
        try:
            # Get all processed versions
            all_versions = self.get_processed_versions()
            if not all_versions:
                self.logger.warning("No processed versions found")
                return False
            
            # Temporarily backup existing CSV if it exists
            backup_path = None
            if self.skills_csv_path.exists():
                backup_path = self.skills_csv_path.with_suffix('.csv.backup')
                self.skills_csv_path.rename(backup_path)
                self.logger.info(f"Backed up existing CSV to {backup_path}")
            
            # Use the incremental method but with all versions as "new"
            success = self.generate_skills_csv(newly_processed_versions=all_versions)
            
            if success and backup_path and backup_path.exists():
                # Remove backup if successful
                backup_path.unlink()
                self.logger.info("Removed backup file after successful regeneration")
            elif not success and backup_path and backup_path.exists():
                # Restore backup if failed
                backup_path.rename(self.skills_csv_path)
                self.logger.warning("Restored backup file after failed regeneration")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to regenerate CSV: {e}")
            return False
    
    def generate_skills_csv(self, newly_processed_versions: Optional[List[str]] = None, 
                           new_skills_data: Optional[Dict[str, List[Dict]]] = None) -> bool:
        """
        Generate consolidated skills_library.csv using incremental updates.
        
        Args:
            newly_processed_versions: List of versions just processed, for incremental updates
            new_skills_data: Pre-fetched skills data keyed by version to avoid duplicate API calls
            
        Returns:
            bool: True if CSV generation successful, False otherwise
        """
        self.logger.info("Generating consolidated skills CSV...")
        
        try:
            # If no new versions, nothing to do
            if newly_processed_versions is None:
                newly_processed_versions = []
            
            if not newly_processed_versions:
                self.logger.info("No new versions to process for CSV update")
                return True
            
            # Load existing CSV data if it exists
            existing_skills_df = None
            if self.skills_csv_path.exists():
                try:
                    existing_skills_df = pd.read_csv(self.skills_csv_path)
                    self.logger.info(f"Loaded existing CSV with {len(existing_skills_df)} skills")
                except Exception as e:
                    self.logger.warning(f"Could not load existing CSV: {e}")
                    existing_skills_df = None
            
            # Process skills data (either from memory or fetch from API)
            new_skills = []
            for version in newly_processed_versions:
                # Use pre-fetched data if available, otherwise fetch from API
                if new_skills_data and version in new_skills_data:
                    self.logger.info(f"Using cached skills data for version: {version}")
                    skills = new_skills_data[version]
                else:
                    self.logger.info(f"Fetching skills for new version: {version}")
                    skills = self.fetch_skills_for_version(version)
                
                if not skills:
                    continue
                
                for skill in skills:
                    skill_id = skill.get('id')
                    if not skill_id:
                        continue
                    
                    # Flatten complex fields for CSV
                    flattened_skill = {
                        'skill_id': skill_id,
                        'name': skill.get('name', ''),
                        'category': skill.get('category', {}).get('name', ''),
                        'subcategory': skill.get('subcategory', {}).get('name', ''),
                        'tags': ', '.join([tag.get('name', '') if isinstance(tag, dict) else str(tag) for tag in skill.get('tags', [])]),
                        'type': skill.get('type', {}).get('name', ''),
                        'latest_version': version,
                        'processed_at': datetime.now().isoformat()
                    }
                    new_skills.append(flattened_skill)
            
            if not new_skills:
                self.logger.warning("No new skills found in newly processed versions")
                return True
            
            # Create DataFrame for new skills
            new_skills_df = pd.DataFrame(new_skills)
            self.logger.info(f"Processed {len(new_skills_df)} skills from new versions")
            
            # Combine with existing data
            if existing_skills_df is not None:
                # Rename version_source to latest_version if it exists in old format
                if 'version_source' in existing_skills_df.columns and 'latest_version' not in existing_skills_df.columns:
                    existing_skills_df = existing_skills_df.rename(columns={'version_source': 'latest_version'})
                
                # Combine new and existing data
                combined_df = pd.concat([existing_skills_df, new_skills_df], ignore_index=True)
            else:
                combined_df = new_skills_df
            
            # Add version_order for proper sorting (like in the notebook)
            # For existing data, we need to assign order based on version
            if 'version_order' not in combined_df.columns:
                # Create version_order based on version numbers
                combined_df['version_order'] = combined_df['latest_version'].apply(self._get_version_order)
            
            # Deduplicate: Keep the most recent version of each skill
            # Sort by version_order (ascending) so newest (lowest number) appears first
            combined_df = combined_df.sort_values('version_order', ascending=True)
            
            # Remove duplicates, keeping first occurrence (most recent)
            deduplicated_df = combined_df.drop_duplicates(subset=['skill_id'], keep='first')
            
            # Clean up temporary sorting column
            deduplicated_df = deduplicated_df.drop('version_order', axis=1)
            
            # Sort by skill_id for consistent output
            deduplicated_df = deduplicated_df.sort_values('skill_id')
            
            # Save updated CSV
            deduplicated_df.to_csv(self.skills_csv_path, index=False)
            
            skills_added = len(new_skills_df)
            final_count = len(deduplicated_df)
            duplicates_removed = len(combined_df) - final_count
            
            self.logger.info(f"CSV update complete:")
            self.logger.info(f"  - Added {skills_added} skills from {len(newly_processed_versions)} new versions")
            self.logger.info(f"  - Removed {duplicates_removed} duplicates")
            self.logger.info(f"  - Final skills count: {final_count}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate skills CSV: {e}")
            return False
    
    def _get_version_order(self, version) -> int:
        """
        Get version order where lower numbers = newer versions (like in notebook).
        
        Args:
            version: Version string like '9.31' or potentially NaN/float
            
        Returns:
            int: Version order where 1=newest, higher numbers=older
        """
        try:
            # Handle NaN or non-string values
            if pd.isna(version) or not isinstance(version, str):
                return 999999  # Put invalid versions at the end
            
            # Parse version like '9.31' into major.minor
            parts = version.split('.')
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            
            # Create order where higher version numbers get lower order (newer first)
            # Use a large number minus the version components
            # This makes 9.31 < 9.30 < 9.29 etc.
            return (1000 - major) * 1000 + (1000 - minor)
            
        except (ValueError, IndexError, AttributeError):
            # Fallback for malformed version numbers
            return 999999
    
    def get_library_status(self) -> Dict:
        """
        Get current status of the skills library.
        
        Returns:
            Dict: Status information including version counts, last update, etc.
        """
        status = {
            'versions_processed': 0,
            'total_skills': 0,
            'last_update': None,
            'csv_exists': self.skills_csv_path.exists(),
            'csv_size_mb': 0
        }
        
        # Check processed versions
        processed_versions = self.get_processed_versions()
        status['versions_processed'] = len(processed_versions)
        
        # Check CSV file
        if self.skills_csv_path.exists():
            status['csv_size_mb'] = self.skills_csv_path.stat().st_size / (1024 * 1024)
            
            try:
                df = pd.read_csv(self.skills_csv_path)
                status['total_skills'] = len(df)
            except Exception:
                pass
        
        # Check last update from file modification time
        if self.versions_file_path.exists():
            try:
                status['last_update'] = datetime.fromtimestamp(
                    self.versions_file_path.stat().st_mtime
                ).isoformat()
            except Exception:
                pass
        
        return status 