#!/usr/bin/env python3
"""
Performance testing for the Skill Similarity Engine.

This script measures the performance of key operations in the
skill similarity engine using generated data of different sizes.
"""

import os
import sys
import time
import random
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture
from skill_similarity_engine.models.employees import EmployeeDatabase
from skill_similarity_engine.similarity.cosine import CosineSimilarityCalculator
from skill_similarity_engine.analysis.gap import GapAnalyzer
from skill_similarity_engine.config.settings import AppConfig


def generate_sample_data(num_skills=100, num_jobs=50, num_employees=200, 
                         skills_per_job=10, skills_per_employee=8):
    """Generate sample data for performance testing."""
    print(f"Generating sample data: {num_skills} skills, {num_jobs} jobs, {num_employees} employees")
    
    # Create a temporary directory for the data
    data_dir = Path(tempfile.mkdtemp())
    
    # Generate skill taxonomy
    skills = []
    categories = ["Technical", "Soft", "Domain", "Methodology", "Tool", "Certification"]
    
    for i in range(1, num_skills + 1):
        skill_id = f"S{i:04d}"
        skill_name = f"Skill {i}"
        category = random.choice(categories)
        difficulty = random.randint(1, 5)
        skills.append({
            "skill_id": skill_id,
            "skill_name": skill_name,
            "category": category,
            "difficulty": difficulty
        })
    
    skills_df = pd.DataFrame(skills)
    skills_csv = data_dir / "skill_taxonomy.csv"
    skills_df.to_csv(skills_csv, index=False)
    
    # Generate job architecture
    job_skills = []
    departments = ["IT", "Finance", "HR", "Marketing", "Operations", "Sales"]
    
    for j in range(1, num_jobs + 1):
        job_id = f"J{j:04d}"
        job_title = f"Job {j}"
        department = random.choice(departments)
        level = random.randint(1, 5)
        
        # Assign random skills to this job
        job_skill_ids = random.sample([s["skill_id"] for s in skills], 
                                     min(skills_per_job, num_skills))
        
        for skill_id in job_skill_ids:
            required_proficiency = random.randint(1, 5)
            job_skills.append({
                "job_id": job_id,
                "job_title": job_title,
                "department": department,
                "level": level,
                "skill_id": skill_id,
                "required_proficiency": required_proficiency
            })
    
    jobs_df = pd.DataFrame(job_skills)
    jobs_csv = data_dir / "job_architecture.csv"
    jobs_df.to_csv(jobs_csv, index=False)
    
    # Generate employee database
    employee_skills = []
    
    for e in range(1, num_employees + 1):
        employee_id = f"E{e:04d}"
        name = f"Employee {e}"
        
        # Select a random job
        job_row = random.choice(job_skills)
        job_id = job_row["job_id"]
        department = job_row["department"]
        
        # Assign skills to this employee (some from their job, some random)
        job_skill_ids = jobs_df[jobs_df["job_id"] == job_id]["skill_id"].unique()
        
        # Ensure we don't try to sample more skills than available
        num_job_skills = min(len(job_skill_ids), skills_per_employee // 2)
        num_random_skills = skills_per_employee - num_job_skills
        
        # Get skills from the job
        selected_job_skills = np.random.choice(
            job_skill_ids, 
            size=num_job_skills, 
            replace=False
        )
        
        # Get random skills not in the job
        other_skills = [s for s in [s["skill_id"] for s in skills]
                       if s not in selected_job_skills]
        selected_random_skills = np.random.choice(
            other_skills, 
            size=min(num_random_skills, len(other_skills)), 
            replace=False
        )
        
        # Combine skills
        employee_skill_ids = list(selected_job_skills) + list(selected_random_skills)
        
        for skill_id in employee_skill_ids:
            proficiency = random.randint(1, 5)
            employee_skills.append({
                "employee_id": employee_id,
                "name": name,
                "department": department,
                "current_job_id": job_id,
                "skill_id": skill_id,
                "proficiency": proficiency
            })
    
    employees_df = pd.DataFrame(employee_skills)
    employees_csv = data_dir / "employee_database.csv"
    employees_df.to_csv(employees_csv, index=False)
    
    return {
        "data_dir": data_dir,
        "skills_csv": skills_csv,
        "jobs_csv": jobs_csv,
        "employees_csv": employees_csv,
        "num_skills": num_skills,
        "num_jobs": num_jobs,
        "num_employees": num_employees
    }


def time_function(func, *args, **kwargs):
    """Time a function call and return the result and execution time."""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    execution_time = end_time - start_time
    return result, execution_time


def test_data_loading(data_params):
    """Test data loading performance."""
    print("\n--- Testing data loading performance ---")
    
    # Time skill taxonomy loading
    _, skill_time = time_function(
        SkillTaxonomy.from_file, 
        data_params["skills_csv"]
    )
    print(f"Loading {data_params['num_skills']} skills took {skill_time:.2f} seconds")
    
    # Time job architecture loading
    _, job_time = time_function(
        JobArchitecture.from_file, 
        data_params["jobs_csv"]
    )
    print(f"Loading {data_params['num_jobs']} jobs took {job_time:.2f} seconds")
    
    # Time employee database loading
    _, emp_time = time_function(
        EmployeeDatabase.from_file, 
        data_params["employees_csv"]
    )
    print(f"Loading {data_params['num_employees']} employees took {emp_time:.2f} seconds")
    
    return {
        "skill_loading_time": skill_time,
        "job_loading_time": job_time,
        "employee_loading_time": emp_time
    }


def test_similarity_calculation(data_params):
    """Test similarity calculation performance."""
    print("\n--- Testing similarity calculation performance ---")
    
    # Load data
    taxonomy = SkillTaxonomy.from_file(data_params["skills_csv"])
    job_arch = JobArchitecture.from_file(data_params["jobs_csv"])
    employee_db = EmployeeDatabase.from_file(data_params["employees_csv"])
    
    # Initialize calculator
    calculator = CosineSimilarityCalculator(taxonomy)
    
    # Time job similarity calculation
    _, job_sim_time = time_function(
        calculator.calculate_job_similarity_matrix,
        job_arch
    )
    print(f"Job-to-job similarity calculation for {data_params['num_jobs']} jobs took {job_sim_time:.2f} seconds")
    
    # Time employee similarity calculation
    _, emp_sim_time = time_function(
        calculator.calculate_employee_similarity_matrix,
        employee_db
    )
    print(f"Employee-to-employee similarity calculation for {data_params['num_employees']} employees took {emp_sim_time:.2f} seconds")
    
    # Time employee-job similarity calculation
    _, emp_job_sim_time = time_function(
        calculator.calculate_employee_job_similarity_matrix,
        employee_db, job_arch
    )
    print(f"Employee-to-job similarity calculation for {data_params['num_employees']} employees and {data_params['num_jobs']} jobs took {emp_job_sim_time:.2f} seconds")
    
    return {
        "job_similarity_time": job_sim_time,
        "employee_similarity_time": emp_sim_time,
        "employee_job_similarity_time": emp_job_sim_time
    }


def test_gap_analysis(data_params):
    """Test gap analysis performance."""
    print("\n--- Testing gap analysis performance ---")
    
    # Load data
    taxonomy = SkillTaxonomy.from_file(data_params["skills_csv"])
    job_arch = JobArchitecture.from_file(data_params["jobs_csv"])
    employee_db = EmployeeDatabase.from_file(data_params["employees_csv"])
    
    # Initialize analyzer
    config = AppConfig()
    analyzer = GapAnalyzer(taxonomy, config.gap_analysis)
    
    # Get a random employee and job
    employee_id = employee_db.employees.iloc[0]["employee_id"]
    job_id = job_arch.jobs.iloc[0]["job_id"]
    
    employee = employee_db.get_employee(employee_id)
    job = job_arch.get_job(job_id)
    
    # Time single gap analysis
    _, single_gap_time = time_function(
        analyzer.analyze_employee_job_gap,
        employee, job
    )
    print(f"Single employee-job gap analysis took {single_gap_time:.2f} seconds")
    
    # Time batch gap analysis (sample of 10 employees against all jobs)
    sample_employees = [employee_db.get_employee(e_id) for e_id in 
                        employee_db.employees["employee_id"].unique()[:min(10, len(employee_db.employees))]]
    
    def analyze_batch():
        results = []
        for emp in sample_employees:
            for j_id in job_arch.jobs["job_id"].unique():
                j = job_arch.get_job(j_id)
                results.append(analyzer.analyze_employee_job_gap(emp, j))
        return results
    
    _, batch_gap_time = time_function(analyze_batch)
    batch_size = len(sample_employees) * len(job_arch.jobs["job_id"].unique())
    print(f"Batch gap analysis for {batch_size} combinations took {batch_gap_time:.2f} seconds")
    
    return {
        "single_gap_analysis_time": single_gap_time,
        "batch_gap_analysis_time": batch_gap_time,
        "batch_size": batch_size
    }


def main():
    """Run performance tests with different data sizes."""
    try:
        # Small dataset
        small_data = generate_sample_data(
            num_skills=50, num_jobs=20, num_employees=100,
            skills_per_job=8, skills_per_employee=6
        )
        print("\n=== Testing with small dataset ===")
        small_loading = test_data_loading(small_data)
        small_similarity = test_similarity_calculation(small_data)
        small_gap = test_gap_analysis(small_data)
        
        # Medium dataset
        medium_data = generate_sample_data(
            num_skills=100, num_jobs=50, num_employees=200,
            skills_per_job=10, skills_per_employee=8
        )
        print("\n=== Testing with medium dataset ===")
        medium_loading = test_data_loading(medium_data)
        medium_similarity = test_similarity_calculation(medium_data)
        medium_gap = test_gap_analysis(medium_data)
        
        # Print summary
        print("\n=== Performance Test Summary ===")
        print("\nData Loading Times (seconds):")
        print(f"{'Size':<10} {'Skills':<10} {'Jobs':<10} {'Employees':<10}")
        print(f"{'Small':<10} {small_loading['skill_loading_time']:<10.2f} {small_loading['job_loading_time']:<10.2f} {small_loading['employee_loading_time']:<10.2f}")
        print(f"{'Medium':<10} {medium_loading['skill_loading_time']:<10.2f} {medium_loading['job_loading_time']:<10.2f} {medium_loading['employee_loading_time']:<10.2f}")
        
        print("\nSimilarity Calculation Times (seconds):")
        print(f"{'Size':<10} {'Job-Job':<10} {'Emp-Emp':<10} {'Emp-Job':<10}")
        print(f"{'Small':<10} {small_similarity['job_similarity_time']:<10.2f} {small_similarity['employee_similarity_time']:<10.2f} {small_similarity['employee_job_similarity_time']:<10.2f}")
        print(f"{'Medium':<10} {medium_similarity['job_similarity_time']:<10.2f} {medium_similarity['employee_similarity_time']:<10.2f} {medium_similarity['employee_job_similarity_time']:<10.2f}")
        
        print("\nGap Analysis Times (seconds):")
        print(f"{'Size':<10} {'Single':<10} {'Batch':<10} {'Batch Size':<10}")
        print(f"{'Small':<10} {small_gap['single_gap_analysis_time']:<10.2f} {small_gap['batch_gap_analysis_time']:<10.2f} {small_gap['batch_size']:<10}")
        print(f"{'Medium':<10} {medium_gap['single_gap_analysis_time']:<10.2f} {medium_gap['batch_gap_analysis_time']:<10.2f} {medium_gap['batch_size']:<10}")
        
    except Exception as e:
        print(f"Error during performance testing: {e}")
        return 1
    finally:
        # Clean up temporary directories
        for data in [small_data, medium_data]:
            import shutil
            shutil.rmtree(data["data_dir"])
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 