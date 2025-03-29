#!/usr/bin/env python3
"""
Script to update sample data with the new attributes for enhanced similarity:
- seniority (1-7)
- role_track (INDIVIDUAL_CONTRIBUTOR or LEADERSHIP)
- location

This script enriches the existing sample job data with these attributes
for testing the enhanced similarity features.
"""

import json
import os
import sys
from pathlib import Path

# Add the src directory to the path so we can import our package
src_path = str(Path(__file__).parent.parent / 'src')
sys.path.insert(0, src_path)

from skill_similarity_engine.models.jobs import JobLevel, RoleTrack


def update_sample_jobs(input_file, output_file=None):
    """
    Update sample job data with seniority, role_track, and location.
    
    Args:
        input_file: Path to the input JSON file with job data
        output_file: Path to save the updated data. If None, overwrites the input file.
    """
    if output_file is None:
        output_file = input_file
    
    # Load the job data
    with open(input_file, 'r') as f:
        job_data = json.load(f)
    
    # Define mappings for departmental locations
    department_to_location = {
        "Analytics": "London",
        "Technology": "London",
        "Business": "Edinburgh",
        "Finance": "Edinburgh",
        "Product": "Manchester",
        "Marketing": "Manchester",
        "HR": "Leeds",
        "IT": "London",
        "Sales": "Bristol",
        "Operations": "Glasgow"
    }
    
    # Define a mapping from job level to seniority (1-7)
    level_to_seniority = {
        JobLevel.ENTRY.value: 1,
        JobLevel.ASSOCIATE.value: 2,
        JobLevel.MID_LEVEL.value: 3,
        JobLevel.SENIOR.value: 4,
        JobLevel.LEAD.value: 5,
        JobLevel.MANAGER.value: 5,
        JobLevel.DIRECTOR.value: 6,
        JobLevel.EXECUTIVE.value: 7
    }
    
    # Define which levels are leadership positions
    leadership_levels = {
        JobLevel.MANAGER.value,
        JobLevel.DIRECTOR.value,
        JobLevel.EXECUTIVE.value
    }
    
    # Check format - the jobs.json can be either a dictionary or a list
    is_dict_format = isinstance(job_data, dict)
    
    if is_dict_format:
        # Dictionary format (key-value pairs where key is job_id)
        for job_id, job in job_data.items():
            # Determine seniority based on level
            level = job.get("level", JobLevel.MID_LEVEL.value)
            job["seniority"] = level_to_seniority.get(level, 3)
            
            # Determine role track based on level and title
            is_leadership = level in leadership_levels or any(
                leadership_term in job.get("title", "").lower() 
                for leadership_term in ["manager", "director", "lead", "head", "chief"]
            )
            
            job["role_track"] = (
                RoleTrack.LEADERSHIP.value if is_leadership 
                else RoleTrack.INDIVIDUAL_CONTRIBUTOR.value
            )
            
            # Determine location based on department
            # For some jobs, assign a remote location to test location similarity
            department = job.get("department", "")
            job["location"] = department_to_location.get(department, "London")
            
            # Make some jobs remote for testing location similarity
            if job_id.endswith("4") or job_id.endswith("9"):
                job["location"] = "Remote"
    else:
        # List format (list of job objects)
        for job in job_data:
            # Extract job_id
            job_id = job.get("job_id", "")
            
            # Determine seniority based on level
            level = job.get("level", JobLevel.MID_LEVEL.value)
            job["seniority"] = level_to_seniority.get(level, 3)
            
            # Determine role track based on level and title
            is_leadership = level in leadership_levels or any(
                leadership_term in job.get("title", "").lower() 
                for leadership_term in ["manager", "director", "lead", "head", "chief"]
            )
            
            job["role_track"] = (
                RoleTrack.LEADERSHIP.value if is_leadership 
                else RoleTrack.INDIVIDUAL_CONTRIBUTOR.value
            )
            
            # Determine location based on department
            # For some jobs, assign a remote location to test location similarity
            department = job.get("department", "")
            job["location"] = department_to_location.get(department, "London")
            
            # Make some jobs remote for testing location similarity
            if job_id.endswith("4") or job_id.endswith("9"):
                job["location"] = "Remote"
    
    # Save the updated data
    with open(output_file, 'w') as f:
        json.dump(job_data, f, indent=2)
    
    print(f"Updated job data saved to {output_file}")
    print(f"Added attributes: seniority, role_track, location")
    
    # Print some statistics
    leadership_count = 0
    ic_count = 0
    locations = {}
    seniority_counts = {}
    
    if is_dict_format:
        # Dictionary format
        job_list = job_data.values()
    else:
        # List format
        job_list = job_data
    
    for job in job_list:
        # Count role tracks
        if job.get("role_track") == RoleTrack.LEADERSHIP.value:
            leadership_count += 1
        elif job.get("role_track") == RoleTrack.INDIVIDUAL_CONTRIBUTOR.value:
            ic_count += 1
        
        # Count locations
        loc = job.get("location", "")
        locations[loc] = locations.get(loc, 0) + 1
        
        # Count seniority levels
        sen = job.get("seniority", 0)
        seniority_counts[sen] = seniority_counts.get(sen, 0) + 1
    
    print(f"\nRole Track Distribution:")
    print(f"  Leadership: {leadership_count} jobs")
    print(f"  Individual Contributor: {ic_count} jobs")
    
    print(f"\nLocation Distribution:")
    for loc, count in sorted(locations.items()):
        print(f"  {loc}: {count} jobs")
    
    print(f"\nSeniority Distribution:")
    for sen, count in sorted(seniority_counts.items()):
        print(f"  Level {sen}: {count} jobs")


def update_all_sample_files():
    """Update all sample job files in the data directory."""
    # Get the path to the sample data directories
    data_dir = Path(__file__).parent.parent / 'data'
    
    # Look for job.json files in various data directories
    sample_dirs = [
        data_dir / 'sample',
        data_dir / 'synthetic',
        data_dir / 'analysis',
        data_dir / 'production'
    ]
    
    # Process each directory
    for directory in sample_dirs:
        if not directory.exists():
            print(f"Directory not found: {directory}")
            continue
        
        print(f"\nProcessing directory: {directory}")
        jobs_file = directory / 'jobs.json'
        
        if jobs_file.exists():
            print(f"Found jobs file: {jobs_file}")
            
            # Create a backup of the original file
            backup_file = directory / 'jobs_original.json'
            if not backup_file.exists():
                print(f"Creating backup of original file at {backup_file}")
                import shutil
                shutil.copy(jobs_file, backup_file)
            
            # Update the sample jobs
            update_sample_jobs(jobs_file)
        else:
            print(f"No jobs.json file found in {directory}")


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Update sample job data with new attributes")
    parser.add_argument('--file', type=str, help='Specific jobs.json file to update')
    parser.add_argument('--all', action='store_true', help='Update all sample files in all data directories')
    
    args = parser.parse_args()
    
    if args.file:
        # Update a specific file
        jobs_file = Path(args.file)
        if not jobs_file.exists():
            print(f"Error: File not found: {jobs_file}")
            return
        
        # Create backup
        backup_file = jobs_file.with_name(f"{jobs_file.stem}_original{jobs_file.suffix}")
        if not backup_file.exists():
            print(f"Creating backup of original file at {backup_file}")
            import shutil
            shutil.copy(jobs_file, backup_file)
        
        # Update the file
        update_sample_jobs(jobs_file)
    elif args.all:
        # Update all sample files
        update_all_sample_files()
    else:
        # Default: update jobs.json in the sample directory
        sample_dir = Path(__file__).parent.parent / 'data' / 'sample'
        jobs_file = sample_dir / 'jobs.json'
        
        if not jobs_file.exists():
            print(f"Error: Sample jobs file not found: {jobs_file}")
            return
        
        # Create a backup of the original file
        backup_file = sample_dir / 'jobs_original.json'
        if not backup_file.exists():
            print(f"Creating backup of original file at {backup_file}")
            import shutil
            shutil.copy(jobs_file, backup_file)
        
        # Update the sample jobs
        update_sample_jobs(jobs_file)


if __name__ == "__main__":
    main() 