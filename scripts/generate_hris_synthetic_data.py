#!/usr/bin/env python3
"""
Script for generating synthetic HRIS data that matches the actual schema.
This script creates synthetic job data, skills data, and job-skill mappings
that can be used for testing the Skill Similarity Engine.
"""

import os
import sys
import random
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set

# Add the src directory to the path so we can import our package
src_path = str(Path(__file__).parent.parent / 'src')
sys.path.insert(0, src_path)

# Constants for data generation
NUM_JOBS = 40000
NUM_SKILLS = 30000
NUM_DEPARTMENTS = 50
NUM_LOCATIONS = 100
NUM_ORG_UNITS = 200

# Sample data for realistic values
DEPARTMENTS = [
    "Technology", "Finance", "HR", "Marketing", "Sales", "Operations",
    "Legal", "Risk", "Compliance", "Customer Service", "Product",
    "Research", "Strategy", "Communications", "Facilities"
]

LOCATIONS = {
    "AU": ["Sydney", "Melbourne", "Brisbane", "Perth", "Canberra"],
    "NZ": ["Auckland", "Wellington", "Christchurch", "Hamilton"],
    "UK": ["London", "Manchester", "Birmingham", "Edinburgh"],
    "SG": ["Singapore"],
    "IN": ["Mumbai", "Bangalore", "Chennai", "Hyderabad"]
}

SKILL_TYPES = ["Certification", "Common Skill", "Specialized Skill"]
SKILL_CATEGORIES = [
    "Finance", "Technology", "Customer Service", "Leadership",
    "Project Management", "Risk Management", "Compliance",
    "Data Analysis", "Communication", "Problem Solving"
]

SKILL_SUBCATEGORIES = {
    "Finance": ["Financial Analysis", "Investment Management", "Risk Assessment"],
    "Technology": ["Software Development", "Infrastructure", "Data Engineering"],
    "Customer Service": ["Client Support", "Account Management", "Service Delivery"],
    "Leadership": ["Team Management", "Strategic Planning", "Change Management"],
    "Project Management": ["Agile", "Waterfall", "Resource Planning"],
    "Risk Management": ["Operational Risk", "Compliance Risk", "Market Risk"],
    "Compliance": ["Regulatory Compliance", "Policy Management", "Audit"],
    "Data Analysis": ["Business Intelligence", "Statistical Analysis", "Reporting"],
    "Communication": ["Written Communication", "Presentation", "Stakeholder Management"],
    "Problem Solving": ["Critical Thinking", "Decision Making", "Innovation"]
}

def generate_job_ids(num_jobs: int) -> List[str]:
    """Generate synthetic job IDs in the format R0001, R0002, etc."""
    return [f"R{str(i).zfill(4)}" for i in range(1, num_jobs + 1)]

def generate_skill_ids(num_skills: int) -> List[str]:
    """Generate synthetic skill IDs in the format BGS10EE289B9FDE2C4B1."""
    return [f"BGS{''.join(random.choices('0123456789ABCDEF', k=16))}" for _ in range(num_skills)]

def generate_org_unit_numbers(num_units: int) -> List[str]:
    """Generate synthetic org unit numbers in the format 55000370."""
    return [f"55{str(i).zfill(6)}" for i in range(1, num_units + 1)]

def generate_jobs_data(num_jobs: int) -> pd.DataFrame:
    """Generate synthetic jobs data matching the HRIS schema."""
    jobs_data = {
        "JobID": generate_job_ids(num_jobs),
        "RoleSet": [f"Role {i}" for i in range(1, num_jobs + 1)],
        "Org Unit Number": random.choices(generate_org_unit_numbers(NUM_ORG_UNITS), k=num_jobs),
        "Org Unit Name": [f"{random.choice(generate_org_unit_numbers(NUM_ORG_UNITS))} {random.choice(DEPARTMENTS)} (Manager {i})" 
                         for i in range(1, num_jobs + 1)],
        "Salary Group": random.choices([f"Group {i}" for i in range(1, 8)], k=num_jobs),
        "People Leader Flag": random.choices(["People Leader", "Non-People Leader"], 
                                           weights=[0.2, 0.8], k=num_jobs),
        "Street": [f"{random.randint(1, 999)} {random.choice(['Main St', 'High St', 'Queen St', 'King St'])}" 
                  for _ in range(num_jobs)],
        "Suburb": [random.choice([city for cities in LOCATIONS.values() for city in cities]) 
                  for _ in range(num_jobs)],
        "Location": [random.choice(list(LOCATIONS.keys())) for _ in range(num_jobs)],
        "Cty": [random.choice(list(LOCATIONS.keys())) for _ in range(num_jobs)]
    }
    return pd.DataFrame(jobs_data)

def generate_skills_data(num_skills: int) -> pd.DataFrame:
    """Generate synthetic skills data matching the HRIS schema."""
    skills_data = {
        "Skill_ID": generate_skill_ids(num_skills),
        "Skill_Name": [f"Skill {i}" for i in range(1, num_skills + 1)],
        "SkillType": random.choices(SKILL_TYPES, k=num_skills),
        "Category": random.choices(SKILL_CATEGORIES, k=num_skills),
        "Subcategory": [random.choice(SKILL_SUBCATEGORIES[cat]) 
                       for cat in random.choices(SKILL_CATEGORIES, k=num_skills)]
    }
    return pd.DataFrame(skills_data)

def generate_job_skills_mapping(jobs_df: pd.DataFrame, skills_df: pd.DataFrame) -> pd.DataFrame:
    """Generate synthetic job-skills mapping data."""
    # Generate 2-5 skills per job
    mappings = []
    for job_id in jobs_df["JobID"]:
        num_skills = random.randint(2, 5)
        selected_skills = random.sample(skills_df["Skill_ID"].tolist(), num_skills)
        mappings.extend([{"JobID": job_id, "Skill_ID": skill_id} 
                        for skill_id in selected_skills])
    
    return pd.DataFrame(mappings)

def main():
    """Main function to generate synthetic HRIS data."""
    # Create output directory
    output_dir = Path(__file__).parent.parent / "data" / "poc"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    print(f"Generating {NUM_JOBS} jobs...")
    jobs_df = generate_jobs_data(NUM_JOBS)
    
    print(f"Generating {NUM_SKILLS} skills...")
    skills_df = generate_skills_data(NUM_SKILLS)
    
    print("Generating job-skills mappings...")
    job_skills_df = generate_job_skills_mapping(jobs_df, skills_df)
    
    # Save data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    jobs_file = output_dir / f"jobs_data_{timestamp}.csv"
    skills_file = output_dir / f"skills_data_{timestamp}.csv"
    job_skills_file = output_dir / f"job_skills_mapping_{timestamp}.csv"
    
    jobs_df.to_csv(jobs_file, index=False)
    skills_df.to_csv(skills_file, index=False)
    job_skills_df.to_csv(job_skills_file, index=False)
    
    print(f"\nGenerated synthetic HRIS data:")
    print(f"Jobs: {len(jobs_df)} records")
    print(f"Skills: {len(skills_df)} records")
    print(f"Job-Skills mappings: {len(job_skills_df)} records")
    print(f"\nFiles saved to:")
    print(f"- {jobs_file}")
    print(f"- {skills_file}")
    print(f"- {job_skills_file}")

if __name__ == "__main__":
    main() 