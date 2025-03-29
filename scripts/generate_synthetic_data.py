#!/usr/bin/env python3
"""
Generate synthetic data for large-scale testing of the skill similarity engine.

This script creates synthetic data files for:
- 2,500 skills
- 32,000 jobs
- 39,000 employees

The data follows realistic distributions and patterns based on the sample data.
"""

import os
import sys
import csv
import json
import random
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
import argparse

# Add seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Default configuration
DEFAULT_CONFIG = {
    "num_skills": 2500,
    "num_jobs": 32000,
    "num_employees": 39000,
    "output_dir": "../data/synthetic",
    "sample_data_dir": "../data/sample",
}

# Department size distribution (realistic imbalance)
DEPARTMENT_DISTRIBUTION = {
    "Retail Banking": 0.25,        # 25% of employees
    "Technology": 0.20,            # 20% of employees
    "Operations": 0.15,            # 15% of employees
    "Finance": 0.12,               # 12% of employees
    "Risk": 0.08,                  # 8% of employees
    "HR": 0.06,                    # 6% of employees
    "Marketing": 0.05,             # 5% of employees
    "Analytics": 0.04,             # 4% of employees
    "Legal": 0.03,                 # 3% of employees
    "Executive": 0.02,             # 2% of employees
}

# Job level distribution (realistic hierarchy)
JOB_LEVEL_DISTRIBUTION = {
    "Entry": 0.30,
    "Associate": 0.35,
    "Mid-level": 0.20,
    "Senior": 0.10,
    "Lead": 0.03,
    "Manager": 0.015,
    "Director": 0.004,
    "Executive": 0.001,
}

# Pay Scale Area distribution (mirrors job levels but with different naming)
PAY_SCALE_AREA_DISTRIBUTION = {
    "PSA1": 0.30,  # Entry
    "PSA2": 0.35,  # Associate
    "PSA3": 0.20,  # Mid-level
    "PSA4": 0.10,  # Senior
    "PSA5": 0.04,  # Lead & Manager
    "PSA6": 0.01,  # Director & Executive
}

# Mapping between job level and pay scale area for consistency
JOB_LEVEL_TO_PSA_MAP = {
    "Entry": "PSA1",
    "Associate": "PSA2",
    "Mid-level": "PSA3",
    "Senior": "PSA4",
    "Lead": "PSA5",
    "Manager": "PSA5",
    "Director": "PSA6",
    "Executive": "PSA6",
}

# Skill categories for generating realistic skills
SKILL_CATEGORIES = [
    {"category": "Technical", "subcategory": "Programming Languages", "weight": 0.12},
    {"category": "Technical", "subcategory": "Database", "weight": 0.08},
    {"category": "Technical", "subcategory": "Analytics", "weight": 0.10},
    {"category": "Technical", "subcategory": "Data Science", "weight": 0.05},
    {"category": "Technical", "subcategory": "Office Tools", "weight": 0.07},
    {"category": "Technical", "subcategory": "Data Visualization", "weight": 0.06},
    {"category": "Technical", "subcategory": "Infrastructure", "weight": 0.06},
    {"category": "Technical", "subcategory": "Security", "weight": 0.03},
    {"category": "Technical", "subcategory": "Design", "weight": 0.04},
    {"category": "Technical", "subcategory": "Project Management", "weight": 0.05},
    {"category": "Soft", "subcategory": "Interpersonal", "weight": 0.06},
    {"category": "Soft", "subcategory": "Critical Thinking", "weight": 0.05},
    {"category": "Soft", "subcategory": "Leadership", "weight": 0.03},
    {"category": "Soft", "subcategory": "Management", "weight": 0.04},
    {"category": "Domain", "subcategory": "Finance", "weight": 0.06},
    {"category": "Domain", "subcategory": "Banking", "weight": 0.06},
    {"category": "Domain", "subcategory": "Marketing", "weight": 0.03},
    {"category": "Domain", "subcategory": "Product", "weight": 0.02},
    {"category": "Domain", "subcategory": "Legal", "weight": 0.01},
    {"category": "Domain", "subcategory": "Risk", "weight": 0.03},
]

# Role track distribution (leadership vs individual contributor)
ROLE_TRACK_DISTRIBUTION = {
    "Individual Contributor": 0.85,  # 85% are ICs
    "Leadership": 0.15,             # 15% are in leadership roles
}

# Location distribution by department
LOCATION_DISTRIBUTION = {
    "Retail Banking": {
        "London": 0.35,
        "Manchester": 0.20,
        "Birmingham": 0.15,
        "Edinburgh": 0.10,
        "Glasgow": 0.10,
        "Leeds": 0.05,
        "Remote": 0.05
    },
    "Technology": {
        "London": 0.50,
        "Manchester": 0.20,
        "Edinburgh": 0.15,
        "Remote": 0.15
    },
    "Finance": {
        "London": 0.60,
        "Edinburgh": 0.30,
        "Manchester": 0.08,
        "Remote": 0.02
    },
    "HR": {
        "London": 0.45,
        "Manchester": 0.15,
        "Leeds": 0.20,
        "Edinburgh": 0.15,
        "Remote": 0.05
    },
    "Operations": {
        "Leeds": 0.30,
        "Glasgow": 0.25,
        "Manchester": 0.20,
        "London": 0.15,
        "Remote": 0.10
    },
    "Marketing": {
        "London": 0.40,
        "Manchester": 0.35,
        "Edinburgh": 0.15,
        "Remote": 0.10
    },
    "Analytics": {
        "London": 0.55,
        "Manchester": 0.25,
        "Edinburgh": 0.15,
        "Remote": 0.05
    },
    "Legal": {
        "London": 0.75,
        "Edinburgh": 0.20,
        "Remote": 0.05
    },
    "Risk": {
        "London": 0.60,
        "Edinburgh": 0.30,
        "Manchester": 0.10
    },
    "Executive": {
        "London": 0.90,
        "Edinburgh": 0.10
    }
}

# Default location distribution for departments not specified above
DEFAULT_LOCATION_DISTRIBUTION = {
    "London": 0.50,
    "Manchester": 0.20,
    "Edinburgh": 0.15,
    "Leeds": 0.05,
    "Glasgow": 0.05,
    "Remote": 0.05
}

# Mapping from job level to seniority (1-7 scale)
LEVEL_TO_SENIORITY_MAP = {
    "Entry": 1,
    "Associate": 2,
    "Mid-level": 3,
    "Senior": 4,
    "Lead": 5,
    "Manager": 5,
    "Director": 6,
    "Executive": 7
}

# Leadership levels (to determine role track)
LEADERSHIP_LEVELS = {"Lead", "Manager", "Director", "Executive"}

class SyntheticDataGenerator:
    """Generate synthetic data for the skill similarity engine."""
    
    def __init__(self, config=None):
        """Initialize the generator with configuration."""
        self.config = config or DEFAULT_CONFIG
        self.skills = {}
        self.jobs = {}
        self.employees = {}
        self.sample_skills = []
        self.sample_jobs = []
        self.sample_employees = []
        
        # Create output directory if it doesn't exist
        Path(self.config["output_dir"]).mkdir(parents=True, exist_ok=True)
    
    def load_sample_data(self):
        """Load sample data to use as a template for synthetic data."""
        sample_dir = self.config["sample_data_dir"]
        
        # Load skills
        skills_path = os.path.join(sample_dir, "skills.csv")
        if os.path.exists(skills_path):
            with open(skills_path, 'r') as f:
                reader = csv.DictReader(f)
                self.sample_skills = list(reader)
        
        # Load jobs
        jobs_path = os.path.join(sample_dir, "jobs.csv")
        if os.path.exists(jobs_path):
            with open(jobs_path, 'r') as f:
                reader = csv.DictReader(f)
                self.sample_jobs = list(reader)
        
        # Load employees
        employees_path = os.path.join(sample_dir, "employees.csv")
        if os.path.exists(employees_path):
            with open(employees_path, 'r') as f:
                reader = csv.DictReader(f)
                self.sample_employees = list(reader)
        
        print(f"Loaded {len(self.sample_skills)} sample skills")
        print(f"Loaded {len(self.sample_jobs)} sample jobs")
        print(f"Loaded {len(self.sample_employees)} sample employees")
    
    def generate_skills(self):
        """Generate synthetic skills data."""
        num_skills = self.config["num_skills"]
        print(f"Generating {num_skills} synthetic skills...")
        
        # Use sample skills as seed for realistic naming patterns
        skill_name_patterns = []
        for skill in self.sample_skills:
            name = skill["name"]
            category = skill["category"]
            subcategory = skill["subcategory"]
            skill_name_patterns.append((name, category, subcategory))
        
        # Generate the skills
        for i in range(1, num_skills + 1):
            skill_id = f"S{i:05d}"
            
            # Determine category and subcategory based on weighted distribution
            cat_data = random.choices(
                SKILL_CATEGORIES, 
                weights=[c["weight"] for c in SKILL_CATEGORIES], 
                k=1
            )[0]
            
            category = cat_data["category"]
            subcategory = cat_data["subcategory"]
            
            # Generate skill name
            if skill_name_patterns and random.random() < 0.7:
                # 70% chance to use pattern from sample data
                # First check if we have any patterns for this category/subcategory
                matching_patterns = [p for p in skill_name_patterns 
                                   if p[1] == category and p[2] == subcategory]
                
                # If no matching patterns, use any pattern
                if not matching_patterns:
                    matching_patterns = skill_name_patterns
                
                # Select random pattern
                pattern = random.choice(matching_patterns)
                base_name = pattern[0]
                
                # Add variation to the name
                variants = [
                    f"Advanced {base_name}",
                    f"{base_name} Development",
                    f"{base_name} Design",
                    f"{base_name} Analysis",
                    f"{base_name} Management",
                    f"{base_name} Strategy",
                    f"{base_name} Implementation",
                    f"{base_name} Optimization",
                    f"{base_name} Application",
                    f"{base_name} {random.randint(1, 5)}",
                    f"{base_name} {chr(random.randint(65, 90))}"
                ]
                name = random.choice(variants)
            else:
                # Generate a completely new name based on category/subcategory
                prefixes = ["Advanced", "Modern", "Strategic", "Tactical", "Enterprise", "Consumer", "Corporate"]
                suffixes = ["Development", "Management", "Analysis", "Design", "Strategy", "Implementation", "Applications"]
                
                if random.random() < 0.5:
                    name = f"{random.choice(prefixes)} {subcategory}"
                else:
                    name = f"{subcategory} {random.choice(suffixes)}"
            
            # Ensure uniqueness
            while name in [s["name"] for s in self.skills.values()]:
                name = f"{name} {chr(random.randint(65, 90))}"
            
            # Generate difficulty (1-5 with normal distribution centered at 3)
            difficulty = max(1, min(5, int(round(np.random.normal(3, 1)))))
            
            self.skills[skill_id] = {
                "skill_id": skill_id,
                "name": name,
                "category": category,
                "subcategory": subcategory,
                "difficulty": difficulty
            }
        
        print(f"Generated {len(self.skills)} skills")
    
    def generate_jobs(self):
        """Generate synthetic jobs data with enhanced attributes."""
        num_jobs = self.config["num_jobs"]
        print(f"Generating {num_jobs} synthetic jobs...")
        
        # Create department distribution
        departments = []
        department_weights = []
        for dept, weight in DEPARTMENT_DISTRIBUTION.items():
            departments.append(dept)
            department_weights.append(weight)
        
        # Create level distribution
        levels = []
        level_weights = []
        for level, weight in JOB_LEVEL_DISTRIBUTION.items():
            levels.append(level)
            level_weights.append(weight)
        
        # Create job titles within departments
        job_title_templates = defaultdict(list)
        
        # Banking job titles
        job_title_templates["Retail Banking"] = [
            "Teller", "Personal Banker", "Branch Manager", "Loan Officer", "Relationship Manager",
            "Mortgage Specialist", "Banking Associate", "Customer Service Representative", 
            "Fraud Specialist", "Banking Operations", "Account Manager", "Banking Advisor"
        ]
        
        # Technology job titles
        job_title_templates["Technology"] = [
            "Software Engineer", "Data Engineer", "System Administrator", "DevOps Engineer",
            "Infrastructure Engineer", "Network Engineer", "IT Support", "Database Administrator",
            "QA Engineer", "Solutions Architect", "Security Engineer", "Cloud Engineer"
        ]
        
        # Finance job titles
        job_title_templates["Finance"] = [
            "Financial Analyst", "Accountant", "Auditor", "Finance Manager", "Controller",
            "Treasurer", "Tax Specialist", "Financial Planner", "Budget Analyst"
        ]
        
        # Fill in defaults for other departments
        for dept in departments:
            if dept not in job_title_templates:
                job_title_templates[dept] = [f"{dept} Specialist", f"{dept} Analyst", f"{dept} Associate"]
        
        # Create skill requirements distribution
        # First, get skill IDs by category for realistic job requirements
        skills_by_category = defaultdict(list)
        for skill_id, skill in self.skills.items():
            category = skill["category"]
            subcategory = skill["subcategory"]
            skills_by_category[(category, subcategory)].append(skill_id)
            skills_by_category[(category, None)].append(skill_id)
        
        # Define typical skill requirements by department and level
        dept_skill_reqs = {
            "Retail Banking": {
                "required_categories": [
                    ("Domain", "Banking"), ("Soft", "Interpersonal"), ("Technical", "Office Tools")
                ],
                "optional_categories": [
                    ("Domain", "Finance"), ("Soft", "Management"), ("Soft", "Critical Thinking")
                ],
                "min_skills": 3,
                "max_skills": 8,
                "level_skill_multiplier": 1.2  # Higher levels have more skills
            },
            "Technology": {
                "required_categories": [
                    ("Technical", "Programming Languages"), ("Technical", "Infrastructure"), 
                    ("Technical", "Project Management")
                ],
                "optional_categories": [
                    ("Technical", "Database"), ("Technical", "Security"), ("Soft", "Critical Thinking")
                ],
                "min_skills": 5,
                "max_skills": 12,
                "level_skill_multiplier": 1.3
            }
        }
        
        # Default department skill requirements
        default_dept_skill_reqs = {
            "required_categories": [
                ("Soft", "Interpersonal"), ("Soft", "Critical Thinking")
            ],
            "optional_categories": [
                ("Technical", "Office Tools"), ("Soft", "Management"), ("Domain", None)
            ],
            "min_skills": 3,
            "max_skills": 9,
            "level_skill_multiplier": 1.2
        }
        
        # Generate the jobs
        for i in range(1, num_jobs + 1):
            job_id = f"J{i:05d}"
            
            # Determine department based on distribution
            department = np.random.choice(departments, p=department_weights)
            
            # Determine level based on distribution
            level = np.random.choice(levels, p=level_weights)
            
            # Determine pay scale area based on job level
            pay_scale_area = JOB_LEVEL_TO_PSA_MAP[level]
            
            # Determine seniority based on level (1-7 scale)
            seniority = LEVEL_TO_SENIORITY_MAP.get(level, 3)
            
            # Determine role track
            # Leadership roles are based on level and some probability
            is_leadership_level = level in LEADERSHIP_LEVELS
            leadership_probability = 0.9 if is_leadership_level else 0.05
            is_leadership = random.random() < leadership_probability
            role_track = "Leadership" if is_leadership else "Individual Contributor"
            
            # Determine location based on department
            location_dist = LOCATION_DISTRIBUTION.get(department, DEFAULT_LOCATION_DISTRIBUTION)
            locations = list(location_dist.keys())
            location_weights = list(location_dist.values())
            location = np.random.choice(locations, p=location_weights)
            
            # Generate job title
            base_titles = job_title_templates.get(department, ["Specialist", "Analyst", "Associate"])
            base_title = random.choice(base_titles)
            
            # Add level prefix or suffix
            if level == "Entry":
                title = f"Junior {base_title}"
            elif level == "Associate":
                title = f"{base_title}"
            elif level == "Mid-level":
                title = f"Senior {base_title}"
            elif level == "Senior":
                title = f"Principal {base_title}"
            elif level == "Lead":
                title = f"{base_title} Lead"
            elif level == "Manager":
                title = f"{base_title} Manager"
            elif level == "Director":
                title = f"{department} Director"
            else:  # Executive
                title = f"Chief {department[:3]} Officer"
            
            # Ensure uniqueness
            while title in [j["title"] for j in self.jobs.values()]:
                title = f"{title} {chr(random.randint(65, 90))}"
            
            # Determine skill requirements (without proficiency levels)
            skill_ids = []
            skill_req_config = dept_skill_reqs.get(department, default_dept_skill_reqs)
            
            # Calculate number of skills based on level
            level_index = levels.index(level)
            level_factor = (level_index + 1) / len(levels)  # Higher levels have more skills
            min_skills = skill_req_config["min_skills"]
            max_skills = skill_req_config["max_skills"]
            target_skills = min_skills + (max_skills - min_skills) * level_factor * skill_req_config["level_skill_multiplier"]
            num_skills = max(min_skills, min(max_skills, int(round(target_skills))))
            
            # Add required category skills
            for category, subcategory in skill_req_config["required_categories"]:
                if (category, subcategory) in skills_by_category and skills_by_category[(category, subcategory)]:
                    skill_id = random.choice(skills_by_category[(category, subcategory)])
                    if skill_id not in skill_ids:
                        skill_ids.append(skill_id)
            
            # Add optional skills to reach target count
            remaining_skills = num_skills - len(skill_ids)
            if remaining_skills > 0:
                optional_categories = skill_req_config["optional_categories"] + [("Technical", None), ("Soft", None)]
                
                for _ in range(remaining_skills * 2):  # Try twice as many to ensure variety
                    if len(skill_ids) >= num_skills:
                        break
                        
                    category, subcategory = random.choice(optional_categories)
                    if (category, subcategory) in skills_by_category and skills_by_category[(category, subcategory)]:
                        skill_id = random.choice(skills_by_category[(category, subcategory)])
                        if skill_id not in skill_ids:
                            skill_ids.append(skill_id)
            
            # Format skills as comma-separated list
            skills_str = ",".join(skill_ids)
            
            self.jobs[job_id] = {
                "job_id": job_id,
                "title": title,
                "department": department,
                "level": level,
                "pay_scale_area": pay_scale_area,
                "skills": skills_str,
                "seniority": seniority,
                "role_track": role_track,
                "location": location
            }
        
        print(f"Generated {len(self.jobs)} jobs")
    
    def generate_employees(self):
        """Generate synthetic employee data."""
        num_employees = self.config["num_employees"]
        print(f"Generating {num_employees} synthetic employees...")
        
        # Generate realistic names
        first_names = [
            "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles",
            "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen",
            "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua", "Kenneth",
            "Emily", "Emma", "Madison", "Abigail", "Olivia", "Isabella", "Hannah", "Samantha", "Ava", "Ashley",
            "Christopher", "George", "Ronald", "Edward", "Brian", "Kevin", "Jason", "Jeff", "Gary", "Timothy",
            "Michelle", "Amanda", "Stephanie", "Rebecca", "Nicole", "Helen", "Anna", "Brittany", "Rachel", "Kayla"
        ]
        
        last_names = [
            "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor",
            "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson",
            "Clark", "Rodriguez", "Lewis", "Lee", "Walker", "Hall", "Allen", "Young", "Hernandez", "King",
            "Wright", "Lopez", "Hill", "Scott", "Green", "Adams", "Baker", "Gonzalez", "Nelson", "Carter",
            "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker", "Evans", "Edwards", "Collins"
        ]
        
        # Create job allocation - number of employees per job
        # Most jobs will have 1-3 employees, some jobs will have more
        jobs_list = list(self.jobs.keys())
        job_allocation = {}
        
        # First pass - assign at least one employee to common jobs
        common_jobs = jobs_list[:int(len(jobs_list) * 0.7)]  # 70% of jobs get at least one employee
        for job_id in common_jobs:
            job_allocation[job_id] = 1
        
        # Second pass - assign remaining employees with power law distribution
        remaining_employees = num_employees - len(common_jobs)
        
        # Generate power law distribution for job popularity
        alpha = 1.5  # Power law exponent
        job_weights = np.random.power(alpha, len(jobs_list))
        job_weights = job_weights / np.sum(job_weights) * remaining_employees
        
        for i, job_id in enumerate(jobs_list):
            count = int(job_weights[i])
            job_allocation[job_id] = job_allocation.get(job_id, 0) + count
        
        # Distribute any remaining employees
        employees_assigned = sum(job_allocation.values())
        remaining = num_employees - employees_assigned
        
        if remaining > 0:
            for _ in range(remaining):
                job_id = random.choice(jobs_list)
                job_allocation[job_id] = job_allocation.get(job_id, 0) + 1
        
        # Generate employees
        employee_count = 0
        for job_id, count in job_allocation.items():
            job = self.jobs[job_id]
            job_skills = job["skills"]
            
            # Parse job skills into list
            job_skill_list = []
            if job_skills:
                job_skill_list = job_skills.split(",")
            
            for _ in range(count):
                employee_count += 1
                employee_id = f"E{employee_count:05d}"
                
                # Generate name
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                name = f"{first_name} {last_name}"
                
                # Generate skills based on job skills with some variation
                employee_skills = []
                
                # Include most job skills
                for skill_id in job_skill_list:
                    # 80% chance to include each job skill
                    if random.random() < 0.8:
                        employee_skills.append(skill_id)
                
                # Add some additional skills
                additional_skill_count = random.randint(0, 3)
                skill_ids = list(self.skills.keys())
                for _ in range(additional_skill_count):
                    skill_id = random.choice(skill_ids)
                    if skill_id not in employee_skills:
                        employee_skills.append(skill_id)
                
                # Format skills as comma-separated list
                skills_str = ",".join(employee_skills)
                
                self.employees[employee_id] = {
                    "employee_id": employee_id,
                    "name": name,
                    "current_job": job_id,
                    "pay_scale_area": job["pay_scale_area"],  # Inherit from job
                    "skills": skills_str
                }
        
        print(f"Generated {len(self.employees)} employees")
    
    def save_data(self):
        """Save the generated data to CSV and JSON files."""
        output_dir = self.config["output_dir"]
        
        # Save skills
        skills_df = pd.DataFrame.from_dict(self.skills, orient='index')
        skills_csv_path = os.path.join(output_dir, "skills.csv")
        skills_df.to_csv(skills_csv_path, index=False)
        
        skills_json_path = os.path.join(output_dir, "skills.json")
        with open(skills_json_path, 'w') as f:
            json.dump(list(self.skills.values()), f, indent=2)
        
        # Save jobs
        jobs_df = pd.DataFrame.from_dict(self.jobs, orient='index')
        jobs_csv_path = os.path.join(output_dir, "jobs.csv")
        jobs_df.to_csv(jobs_csv_path, index=False)
        
        jobs_json_path = os.path.join(output_dir, "jobs.json")
        with open(jobs_json_path, 'w') as f:
            json.dump(self.jobs, f, indent=2)
        
        # Save employees
        employees_df = pd.DataFrame.from_dict(self.employees, orient='index')
        employees_csv_path = os.path.join(output_dir, "employees.csv")
        employees_df.to_csv(employees_csv_path, index=False)
        
        employees_json_path = os.path.join(output_dir, "employees.json")
        with open(employees_json_path, 'w') as f:
            json.dump(self.employees, f, indent=2)
        
        # Generate stats
        stats = {
            "skill_count": len(self.skills),
            "job_count": len(self.jobs),
            "employee_count": len(self.employees),
            "department_counts": defaultdict(int),
            "level_counts": defaultdict(int),
            "skill_category_counts": defaultdict(int),
            "seniority_counts": defaultdict(int),
            "role_track_counts": defaultdict(int),
            "location_counts": defaultdict(int)
        }
        
        for job in self.jobs.values():
            stats["department_counts"][job["department"]] += 1
            stats["level_counts"][job["level"]] += 1
            # Count the new attributes
            if "seniority" in job:
                stats["seniority_counts"][job["seniority"]] += 1
            if "role_track" in job:
                stats["role_track_counts"][job["role_track"]] += 1
            if "location" in job:
                stats["location_counts"][job["location"]] += 1
        
        for skill in self.skills.values():
            stats["skill_category_counts"][skill["category"]] += 1
        
        # Save stats
        stats_path = os.path.join(output_dir, "stats.json")
        with open(stats_path, 'w') as f:
            # Convert defaultdicts to regular dicts for JSON serialization
            serializable_stats = {
                **stats,
                "department_counts": dict(stats["department_counts"]),
                "level_counts": dict(stats["level_counts"]),
                "skill_category_counts": dict(stats["skill_category_counts"]),
                "seniority_counts": dict(stats["seniority_counts"]),
                "role_track_counts": dict(stats["role_track_counts"]),
                "location_counts": dict(stats["location_counts"])
            }
            json.dump(serializable_stats, f, indent=2)
        
        # Generate a summary of the new attributes
        print("\nEnhanced Attribute Statistics:")
        print("  Seniority Distribution:")
        for seniority, count in sorted(stats["seniority_counts"].items()):
            percent = (count / len(self.jobs)) * 100
            print(f"    Level {seniority}: {count} jobs ({percent:.1f}%)")
        
        print("\n  Role Track Distribution:")
        for role_track, count in sorted(stats["role_track_counts"].items()):
            percent = (count / len(self.jobs)) * 100
            print(f"    {role_track}: {count} jobs ({percent:.1f}%)")
        
        print("\n  Location Distribution:")
        for location, count in sorted(stats["location_counts"].items(), key=lambda x: x[1], reverse=True):
            percent = (count / len(self.jobs)) * 100
            print(f"    {location}: {count} jobs ({percent:.1f}%)")
        
        print(f"\nData saved to {output_dir}")
        print(f"  - Skills: {skills_csv_path}")
        print(f"  - Jobs: {jobs_csv_path}")
        print(f"  - Employees: {employees_csv_path}")
        print(f"  - Stats: {stats_path}")
    
    def generate_data(self):
        """Generate the complete synthetic dataset."""
        self.load_sample_data()
        self.generate_skills()
        self.generate_jobs()
        self.generate_employees()
        self.save_data()
        print("Data generation complete!")


def main():
    """Command line interface for the synthetic data generator."""
    parser = argparse.ArgumentParser(description="Generate synthetic data for the skill similarity engine")
    
    parser.add_argument("--skills", type=int, default=DEFAULT_CONFIG["num_skills"],
                        help=f"Number of skills to generate (default: {DEFAULT_CONFIG['num_skills']})")
    
    parser.add_argument("--jobs", type=int, default=DEFAULT_CONFIG["num_jobs"],
                        help=f"Number of jobs to generate (default: {DEFAULT_CONFIG['num_jobs']})")
    
    parser.add_argument("--employees", type=int, default=DEFAULT_CONFIG["num_employees"],
                        help=f"Number of employees to generate (default: {DEFAULT_CONFIG['num_employees']})")
    
    parser.add_argument("--output", type=str, default=DEFAULT_CONFIG["output_dir"],
                        help=f"Output directory (default: {DEFAULT_CONFIG['output_dir']})")
    
    parser.add_argument("--sample-data", type=str, default=DEFAULT_CONFIG["sample_data_dir"],
                        help=f"Sample data directory (default: {DEFAULT_CONFIG['sample_data_dir']})")
    
    args = parser.parse_args()
    
    config = {
        "num_skills": args.skills,
        "num_jobs": args.jobs,
        "num_employees": args.employees,
        "output_dir": args.output,
        "sample_data_dir": args.sample_data,
    }
    
    generator = SyntheticDataGenerator(config)
    generator.generate_data()


if __name__ == "__main__":
    main() 