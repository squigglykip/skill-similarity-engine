#!/usr/bin/env python3
"""
Lightcast Skills API Endpoint Extractor

Extracts data from the 5 main API endpoints and saves each as a CSV file.
Simple approach - one endpoint = one CSV file.
"""

import sys
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import tqdm

from .lightcast_client import LightcastSkillsClient
from ..utils.progress import ProgressTracker, progress_context
from ..utils.performance import get_memory_usage

logger = logging.getLogger(__name__)

class EndpointExtractor:
    """Simple extractor for the 5 main Lightcast API endpoints"""
    
    def __init__(self, client: LightcastSkillsClient, output_dir: str = "data", use_timestamp: bool = True):
        self.client = client
        self.output_dir = Path(output_dir)
        self.use_timestamp = use_timestamp
        
        if use_timestamp:
            self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_dir = self.output_dir / f"extraction_{self.timestamp}"
        else:
            self.session_dir = self.output_dir
        
        # Create output directory
        self.session_dir.mkdir(parents=True, exist_ok=True)
        print(f"Output directory: {self.session_dir}")
    
    def unpack_fields(self, record: Dict) -> Dict:
        """Unpack nested fields in a record"""
        unpacked = {}
        
        for key, value in record.items():
            # Skip original category and subcategory fields entirely - we only want the unpacked versions
            if key in ['category', 'subcategory']:
                if isinstance(value, dict):
                    # If it's a dict with 'id' and 'name', unpack both
                    if 'id' in value and 'name' in value:
                        unpacked[f"{key}_id"] = value['id']
                        unpacked[f"{key}_name"] = value['name']
                    # If it has other fields, unpack them too
                    elif 'id' in value:
                        unpacked[f"{key}_id"] = value['id']
                    elif 'name' in value:
                        unpacked[f"{key}_name"] = value['name']
                # Skip the original field entirely for category/subcategory
                continue
            
            if isinstance(value, dict):
                # If it's a dict with 'id' and 'name', unpack both
                if 'id' in value and 'name' in value:
                    unpacked[f"{key}_id"] = value['id']
                    unpacked[f"{key}_name"] = value['name']
                    unpacked[key] = json.dumps(value)
                # If it has other fields, unpack them too
                elif 'id' in value:
                    unpacked[f"{key}_id"] = value['id']
                    unpacked[key] = json.dumps(value)
                elif 'name' in value:
                    unpacked[f"{key}_name"] = value['name']
                    unpacked[key] = json.dumps(value)
                else:
                    # Just convert to JSON string
                    unpacked[key] = json.dumps(value)
            elif isinstance(value, list):
                # Special handling for 'tags' field
                if key == 'tags' and value:
                    # Extract key-value pairs from tags
                    for tag in value:
                        if isinstance(tag, dict) and 'key' in tag and 'value' in tag:
                            tag_key = tag['key']
                            tag_value = tag['value']
                            unpacked[f"tag_{tag_key}"] = tag_value
                    # Also keep the original as JSON for reference
                    unpacked[key] = json.dumps(value)
                else:
                    # Convert other lists to JSON strings
                    unpacked[key] = json.dumps(value)
            else:
                # Keep simple values as-is
                unpacked[key] = value
        
        return unpacked
    
    def sanitise_text(self, text: str) -> str:
        """Sanitise text fields to remove problematic characters for CSV"""
        if not text or not isinstance(text, str):
            return str(text) if text is not None else ""
        
        # Replace newlines with spaces
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Replace tabs with spaces
        text = text.replace('\t', ' ')
        
        # Remove or replace other control characters
        text = ''.join(char if ord(char) >= 32 or char in '\t\n\r' else ' ' for char in text)
        
        # Collapse multiple spaces into single spaces
        import re
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def save_to_csv(self, data: List[Dict], filename: str) -> str:
        """Save data to CSV with field unpacking and text sanitisation"""
        if not data:
            print(f"No data for {filename}")
            return ""
        
        filepath = self.session_dir / f"{filename}.csv"
        
        # Unpack all records
        unpacked_data = [self.unpack_fields(record) for record in data]
        
        # Get all fieldnames
        fieldnames = set()
        for record in unpacked_data:
            fieldnames.update(record.keys())
        fieldnames = sorted(list(fieldnames))
        
        # Save to CSV with proper quoting and sanitisation
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            
            for record in unpacked_data:
                # Sanitise and ensure all fields are clean strings
                clean_record = {}
                for field in fieldnames:
                    value = record.get(field, "")
                    if value is not None:
                        # Sanitise text fields (especially tag_wikipediaExtract and description)
                        clean_value = self.sanitise_text(str(value))
                        clean_record[field] = clean_value
                    else:
                        clean_record[field] = ""
                writer.writerow(clean_record)
        
        # Quietly save - progress is tracked elsewhere
        return str(filepath)
    
    def extract_status(self):
        """Endpoint: /status"""
        response = self.client.get_status()
        self.save_to_csv([response["data"]], "status")
    
    def extract_meta(self):
        """Endpoint: /meta"""
        response = self.client.get_metadata()
        self.save_to_csv([response["data"]], "meta")
    
    def extract_versions(self):
        """Endpoint: /versions"""
        versions = self.client.list_versions()
        # Convert to list of dicts
        version_data = [{"version": v} for v in versions]
        self.save_to_csv(version_data, "versions")
    
    def extract_version_latest(self):
        """Endpoint: /versions/latest"""
        response = self.client.get_version_metadata("latest")
        
        # The response has nested data - let's flatten it properly
        version_data = response["data"]
        
        # Extract main version info
        main_info = {
            "version": version_data["version"],
            "skillCount": version_data["skillCount"],
            "removedSkillCount": version_data["removedSkillCount"],
            "fields": json.dumps(version_data["fields"]),
            "types": json.dumps(version_data["types"])
        }
        
        self.save_to_csv([main_info], "version_latest")
    
    def extract_skills(self):
        """Endpoint: /versions/latest/skills"""
        
        # Get version metadata to know what fields are available and the version number
        version_meta = self.client.get_version_metadata("latest")
        all_fields = version_meta["data"]["fields"]
        expected_count = version_meta["data"]["skillCount"]
        version_number = version_meta["data"]["version"]
        
        # Try to get all skills
        try:
            response = self.client.list_skills(
                version="latest",
                fields=all_fields,
                limit=100000  # Try high limit to get all
            )
            
            skills = response.get("data", [])
            
            if len(skills) < expected_count:
                print(f"âš ï¸  Retrieved {len(skills):,} of {expected_count:,} expected skills (API pagination limit)")
            
            # Use version number in filename
            filename = f"skills_{version_number}"
            self.save_to_csv(skills, filename)
            
        except Exception as e:
            print(f"âš ï¸  Error extracting skills: {e}")
            # Try with no limit
            try:
                response = self.client.list_skills(
                    version="latest",
                    fields=all_fields
                )
                skills = response.get("data", [])
                
                # Use version number in filename
                filename = f"skills_{version_number}"
                self.save_to_csv(skills, filename)
            except Exception as e2:
                print(f"âŒ Failed to extract skills: {e2}")
                raise
    
    def extract_all_skills_comprehensive(self):
        """Endpoint 6: /versions/{version}/skills for compatible versions - comprehensive historical dataset"""
        print("Extracting comprehensive skills dataset from schema-compatible versions...")
        
        # Get the reference schema from latest version
        print("Getting reference schema from latest version...")
        latest_meta = self.client.get_version_metadata("latest")
        reference_fields = set(latest_meta["data"]["fields"])
        latest_version = latest_meta["data"]["version"]
        
        print(f"Reference schema (v{latest_version}): {', '.join(sorted(reference_fields))}")
        
        # Get all available versions
        versions = self.client.list_versions()
        print(f"Found {len(versions)} versions to check for compatibility")
        
        # Filter versions that have the same schema
        compatible_versions = []
        print("\nChecking schema compatibility...")
        
        for version in versions:
            try:
                version_meta = self.client.get_version_metadata(version)
                version_fields = set(version_meta["data"]["fields"])
                
                if version_fields == reference_fields:
                    compatible_versions.append(version)
                    print(f"  ✅ {version} - Compatible")
                else:
                    missing = reference_fields - version_fields
                    extra = version_fields - reference_fields
                    print(f"  âœ— {version} - Incompatible (missing: {len(missing)}, extra: {len(extra)})")
                    
            except Exception as e:
                print(f"  âœ— {version} - Error getting metadata: {e}")
        
        print(f"\nFound {len(compatible_versions)} compatible versions out of {len(versions)} total")
        print(f"Compatible versions: {', '.join(compatible_versions[:10])}{'...' if len(compatible_versions) > 10 else ''}")
        
        if not compatible_versions:
            print("No compatible versions found!")
            return
        
        # Track all skills with their latest version
        all_skills_dict = {}  # key: skill_id, value: skill_data_with_version
        total_skills_processed = 0
        successful_versions = 0
        
        # Process each compatible version (from oldest to newest to ensure latest version wins)
        reversed_versions = list(reversed(compatible_versions))
        with ProgressTracker(total=len(reversed_versions), desc="Processing Versions", show_tqdm=True) as version_tracker:
            for i, version in enumerate(reversed_versions):
                
                try:
                    # Get skills for this version using the reference fields
                    response = self.client.list_skills(
                        version=version,
                        fields=list(reference_fields),
                        limit=100000
                    )
                    
                    skills = response.get("data", [])
                    successful_versions += 1
                    
                    # Process skills silently - no logging during processing
                    for skill in skills:
                        skill_id = skill.get("id")
                        if skill_id:
                            # Add version information to the skill
                            skill_with_version = skill.copy()
                            skill_with_version["source_version"] = version
                            
                            # Store/update skill (later versions will overwrite earlier ones)
                            all_skills_dict[skill_id] = skill_with_version
                            total_skills_processed += 1
                    
                    # Update progress bar once per version
                    version_tracker.update(1)
                    
                except Exception as e:
                    tqdm.tqdm.write(f"  âŒ Error processing version {version}: {e}")
                    version_tracker.update(1)  # Still update progress
                    continue
        
        # Convert to list and sort by skill ID for consistency
        comprehensive_skills = list(all_skills_dict.values())
        comprehensive_skills.sort(key=lambda x: x.get("id", ""))
        
        print(f"\nComprehensive dataset summary:")
        print(f"  Compatible versions found: {len(compatible_versions)}")
        print(f"  Versions successfully processed: {successful_versions}")
        print(f"  Total skills processed: {total_skills_processed:,}")
        print(f"  Unique skills (deduplicated): {len(comprehensive_skills):,}")
        
        # Save comprehensive dataset
        if comprehensive_skills:
            self.save_to_csv(comprehensive_skills, "skills_comprehensive_all_versions")
            print(f"Saved comprehensive skills dataset with latest version of each skill")
        else:
            print("No comprehensive skills data to save")
    
    def run_extraction(self):
        """Extract data from all 6 endpoints"""
        print("=" * 50)
        print("LIGHTCAST API ENDPOINT EXTRACTION")
        print("=" * 50)
        
        # Define extraction steps
        basic_steps = [
            ("Status", self.extract_status),
            ("Metadata", self.extract_meta),
            ("Versions", self.extract_versions),
            ("Latest Version", self.extract_version_latest),
            ("Skills", self.extract_skills)
        ]
        
        try:
            # Extract basic endpoint data with progress tracking
            with ProgressTracker(total=len(basic_steps), desc="Basic Endpoints", show_tqdm=True) as tracker:
                for step_name, step_func in basic_steps:
                    step_func()
                    tracker.update(1)
            
            # Extract comprehensive historical skills dataset
            print("\n" + "=" * 50)
            print("COMPREHENSIVE HISTORICAL EXTRACTION")
            print("=" * 50)
            self.extract_all_skills_comprehensive()
            
            print("=" * 50)
            print("âœ… EXTRACTION COMPLETE!")
            print(f"ðŸ“ Output directory: {self.session_dir}")
            print("ðŸ“„ Files created:")
            print("  1. status.csv")
            print("  2. meta.csv") 
            print("  3. versions.csv")
            print("  4. version_latest.csv")
            print("  5. skills_[version].csv (latest version only)")
            print("  6. skills_comprehensive_all_versions.csv (all versions, latest appearance)")
            print("=" * 50)
            
        except Exception as e:
            print(f"âŒ ERROR: {e}")
            raise


def main():
    """Main execution"""
    try:
        print("Initializing API client...")
        client = LightcastSkillsClient.from_credentials_file('credentials.json')
        
        extractor = EndpointExtractor(client)
        extractor.run_extraction()
        
        return 0
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 
