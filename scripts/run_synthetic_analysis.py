#!/usr/bin/env python3
"""
Run analysis on synthetic data to test large-scale performance.

This script loads the synthetic data and runs various analyses to test
the performance and scalability of the skill similarity engine with large datasets.
"""

import os
import sys
import time
import logging
import argparse
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("synthetic_analysis")

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture
from skill_similarity_engine.models.employees import EmployeeDatabase
from skill_similarity_engine.data.loaders import JobArchitectureLoader, EmployeeLoader
from skill_similarity_engine.similarity.cosine import CosineSimilarityCalculator
from skill_similarity_engine.visualization.visualizer import VisualisationManager


def time_execution(func):
    """Decorator to time the execution of a function."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"{func.__name__} executed in {duration:.2f} seconds")
        return result, duration
    return wrapper


class SyntheticDataAnalyzer:
    """Analyze synthetic data and measure performance."""
    
    def __init__(self, data_dir, output_dir=None, sample_size=None):
        """Initialize the analyzer with data directory."""
        self.data_dir = data_dir
        self.output_dir = output_dir or os.path.join(os.path.dirname(data_dir), 'analysis')
        self.sample_size = sample_size
        
        # Create output directory
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Data models
        self.skill_taxonomy = None
        self.job_architecture = None
        self.employee_database = None
        self.similarity_calculator = None
        self.visualization_manager = None
        
        # Timing metrics
        self.load_times = {}
        self.analysis_times = {}
    
    @time_execution
    def load_skills(self):
        """Load skill taxonomy."""
        logger.info(f"Loading skills from {self.data_dir}...")
        skills_path = os.path.join(self.data_dir, "skills.csv")
        self.skill_taxonomy = SkillTaxonomy.from_file(skills_path)
        logger.info(f"Loaded {len(self.skill_taxonomy.skills)} skills")
        return self.skill_taxonomy
    
    @time_execution
    def load_jobs(self):
        """Load job architecture."""
        logger.info(f"Loading jobs from {self.data_dir}...")
        jobs_path = os.path.join(self.data_dir, "jobs.csv")
        job_loader = JobArchitectureLoader(self.skill_taxonomy)
        
        # Apply sampling if specified
        if self.sample_size and self.sample_size.get('jobs'):
            logger.info(f"Sampling {self.sample_size['jobs']} jobs")
            # Load full jobs CSV
            jobs_df = pd.read_csv(jobs_path)
            # Sample rows
            sampled_jobs = jobs_df.sample(n=min(self.sample_size['jobs'], len(jobs_df)), random_state=42)
            # Save to temporary file
            temp_jobs_path = os.path.join(self.output_dir, "sampled_jobs.csv")
            sampled_jobs.to_csv(temp_jobs_path, index=False)
            # Use the temporary file
            self.job_architecture = job_loader.load_from_csv(temp_jobs_path)
        else:
            self.job_architecture = job_loader.load_from_csv(jobs_path)
            
        logger.info(f"Loaded {len(self.job_architecture.jobs)} jobs")
        return self.job_architecture
    
    @time_execution
    def load_employees(self):
        """Load employee database."""
        logger.info(f"Loading employees from {self.data_dir}...")
        employees_path = os.path.join(self.data_dir, "employees.csv")
        employee_loader = EmployeeLoader(self.skill_taxonomy, self.job_architecture)
        
        # Apply sampling if specified
        if self.sample_size and self.sample_size.get('employees'):
            logger.info(f"Sampling {self.sample_size['employees']} employees")
            # Load full employees CSV
            employees_df = pd.read_csv(employees_path)
            # Sample rows
            sampled_employees = employees_df.sample(n=min(self.sample_size['employees'], len(employees_df)), random_state=42)
            # Save to temporary file
            temp_employees_path = os.path.join(self.output_dir, "sampled_employees.csv")
            sampled_employees.to_csv(temp_employees_path, index=False)
            # Use the temporary file
            self.employee_database = employee_loader.load_from_csv(temp_employees_path)
        else:
            self.employee_database = employee_loader.load_from_csv(employees_path)
            
        logger.info(f"Loaded {len(self.employee_database.employees)} employees")
        return self.employee_database
    
    @time_execution
    def initialize_similarity_calculator(self):
        """Initialize similarity calculator."""
        logger.info("Initializing similarity calculator...")
        self.similarity_calculator = CosineSimilarityCalculator(
            vectorizer=None,  # Will be initialized within the calculator
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture
        )
        return self.similarity_calculator
    
    @time_execution
    def initialize_visualization_manager(self):
        """Initialize visualization manager."""
        logger.info("Initializing visualization manager...")
        self.visualization_manager = VisualisationManager(
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database,
            output_dir=self.output_dir
        )
        return self.visualization_manager
    
    @time_execution
    def analyze_department_similarity(self, department):
        """Analyze job similarity within a department."""
        logger.info(f"Analyzing job similarity for department: {department}")
        
        # Get jobs in the department
        dept_jobs = [job_id for job_id, job in self.job_architecture.jobs.items() 
                      if job.department == department]
        
        if not dept_jobs:
            logger.warning(f"No jobs found in department: {department}")
            return None
        
        logger.info(f"Found {len(dept_jobs)} jobs in department {department}")
        
        # Calculate similarity matrix
        similarity_pairs = []
        for i, job1_id in enumerate(dept_jobs):
            for j, job2_id in enumerate(dept_jobs[i+1:], i+1):
                job1 = self.job_architecture.jobs[job1_id]
                job2 = self.job_architecture.jobs[job2_id]
                
                # Calculate base similarity
                similarity = self.similarity_calculator.calculate_job_similarity(job1_id, job2_id)
                
                # Apply pay scale area adjustment
                # If pay scale areas are very different, reduce similarity
                psa1 = getattr(job1, 'pay_scale_area', None)
                psa2 = getattr(job2, 'pay_scale_area', None)
                
                if psa1 and psa2 and psa1 != psa2:
                    # Extract numeric part from PSA (e.g., "PSA4" -> 4)
                    psa1_level = int(psa1.replace("PSA", ""))
                    psa2_level = int(psa2.replace("PSA", ""))
                    
                    # Calculate difference in pay scale (0-5 range)
                    psa_diff = abs(psa1_level - psa2_level)
                    
                    # Adjust similarity based on PSA difference
                    # Greater difference = lower similarity
                    if psa_diff >= 3:
                        similarity *= 0.5  # Major difference
                    elif psa_diff == 2:
                        similarity *= 0.7  # Moderate difference
                    elif psa_diff == 1:
                        similarity *= 0.9  # Minor difference
                
                similarity_pairs.append({
                    'job1_id': job1_id,
                    'job2_id': job2_id,
                    'job1_psa': psa1,
                    'job2_psa': psa2,
                    'similarity': similarity
                })
        
        # Create DataFrame
        similarity_df = pd.DataFrame(similarity_pairs)
        
        # Calculate statistics
        if similarity_df.empty:
            logger.warning("No similarity pairs generated")
            return similarity_df
            
        logger.info(f"Generated {len(similarity_df)} similarity pairs")
        logger.info(f"Similarity stats - Mean: {similarity_df['similarity'].mean():.4f}, "
                   f"Median: {similarity_df['similarity'].median():.4f}, "
                   f"Min: {similarity_df['similarity'].min():.4f}, "
                   f"Max: {similarity_df['similarity'].max():.4f}")
        
        # Save to CSV
        output_path = os.path.join(self.output_dir, f"{department}_similarity.csv")
        similarity_df.to_csv(output_path, index=False)
        logger.info(f"Saved similarity matrix to: {output_path}")
        
        return similarity_df
    
    @time_execution
    def generate_department_visualization(self, department):
        """Generate visualization for a department."""
        logger.info(f"Generating visualization for department: {department}")
        
        # Generate hexbin visualization
        output_path = self.visualization_manager.generate_hexbin_visualization(
            department=department,
            color_scheme='viridis',
            figsize=(12, 10),
            dpi=300
        )
        
        logger.info(f"Generated hexbin visualization at: {output_path}")
        return output_path
    
    @time_execution
    def analyze_cross_department_similarity(self, dept1, dept2):
        """Analyze job similarity between two departments."""
        logger.info(f"Analyzing cross-department similarity: {dept1} vs {dept2}")
        
        # Get jobs in each department
        dept1_jobs = [job_id for job_id, job in self.job_architecture.jobs.items() 
                      if job.department == dept1]
        dept2_jobs = [job_id for job_id, job in self.job_architecture.jobs.items() 
                      if job.department == dept2]
        
        if not dept1_jobs or not dept2_jobs:
            logger.warning(f"Insufficient jobs found in departments: {dept1}, {dept2}")
            return None
        
        logger.info(f"Found {len(dept1_jobs)} jobs in {dept1} and {len(dept2_jobs)} jobs in {dept2}")
        
        # Calculate similarity matrix
        similarity_pairs = []
        
        # If too many jobs, sample
        max_pairs = 1000
        if len(dept1_jobs) * len(dept2_jobs) > max_pairs:
            logger.info(f"Too many job pairs ({len(dept1_jobs) * len(dept2_jobs)}), sampling {max_pairs}")
            
            # Sample job IDs from each department
            sample_size1 = min(len(dept1_jobs), int(np.sqrt(max_pairs)))
            sample_size2 = min(len(dept2_jobs), int(max_pairs / sample_size1))
            
            sampled_dept1_jobs = np.random.choice(dept1_jobs, size=sample_size1, replace=False)
            sampled_dept2_jobs = np.random.choice(dept2_jobs, size=sample_size2, replace=False)
            
            for job1_id in sampled_dept1_jobs:
                for job2_id in sampled_dept2_jobs:
                    job1 = self.job_architecture.jobs[job1_id]
                    job2 = self.job_architecture.jobs[job2_id]
                    
                    # Calculate base similarity
                    similarity = self.similarity_calculator.calculate_job_similarity(job1_id, job2_id)
                    
                    # Apply pay scale area adjustment
                    psa1 = getattr(job1, 'pay_scale_area', None)
                    psa2 = getattr(job2, 'pay_scale_area', None)
                    
                    if psa1 and psa2 and psa1 != psa2:
                        # Extract numeric part from PSA (e.g., "PSA4" -> 4)
                        psa1_level = int(psa1.replace("PSA", ""))
                        psa2_level = int(psa2.replace("PSA", ""))
                        
                        # Calculate difference in pay scale (0-5 range)
                        psa_diff = abs(psa1_level - psa2_level)
                        
                        # Adjust similarity based on PSA difference
                        if psa_diff >= 3:
                            similarity *= 0.5  # Major difference
                        elif psa_diff == 2:
                            similarity *= 0.7  # Moderate difference
                        elif psa_diff == 1:
                            similarity *= 0.9  # Minor difference
                    
                    similarity_pairs.append({
                        'job1_id': job1_id,
                        'job2_id': job2_id,
                        'job1_psa': psa1,
                        'job2_psa': psa2,
                        'similarity': similarity
                    })
        else:
            for job1_id in dept1_jobs:
                for job2_id in dept2_jobs:
                    job1 = self.job_architecture.jobs[job1_id]
                    job2 = self.job_architecture.jobs[job2_id]
                    
                    # Calculate base similarity
                    similarity = self.similarity_calculator.calculate_job_similarity(job1_id, job2_id)
                    
                    # Apply pay scale area adjustment
                    psa1 = getattr(job1, 'pay_scale_area', None)
                    psa2 = getattr(job2, 'pay_scale_area', None)
                    
                    if psa1 and psa2 and psa1 != psa2:
                        # Extract numeric part from PSA (e.g., "PSA4" -> 4)
                        psa1_level = int(psa1.replace("PSA", ""))
                        psa2_level = int(psa2.replace("PSA", ""))
                        
                        # Calculate difference in pay scale (0-5 range)
                        psa_diff = abs(psa1_level - psa2_level)
                        
                        # Adjust similarity based on PSA difference
                        if psa_diff >= 3:
                            similarity *= 0.5  # Major difference
                        elif psa_diff == 2:
                            similarity *= 0.7  # Moderate difference
                        elif psa_diff == 1:
                            similarity *= 0.9  # Minor difference
                    
                    similarity_pairs.append({
                        'job1_id': job1_id,
                        'job2_id': job2_id,
                        'job1_psa': psa1,
                        'job2_psa': psa2,
                        'similarity': similarity
                    })
        
        # Create DataFrame
        similarity_df = pd.DataFrame(similarity_pairs)
        
        # Calculate statistics
        if similarity_df.empty:
            logger.warning("No similarity pairs generated")
            return similarity_df
            
        logger.info(f"Generated {len(similarity_df)} similarity pairs")
        logger.info(f"Similarity stats - Mean: {similarity_df['similarity'].mean():.4f}, "
                   f"Median: {similarity_df['similarity'].median():.4f}, "
                   f"Min: {similarity_df['similarity'].min():.4f}, "
                   f"Max: {similarity_df['similarity'].max():.4f}")
        
        # Save to CSV
        output_path = os.path.join(self.output_dir, f"{dept1}_vs_{dept2}_similarity.csv")
        similarity_df.to_csv(output_path, index=False)
        logger.info(f"Saved cross-department similarity to: {output_path}")
        
        return similarity_df
    
    @time_execution
    def plot_performance_metrics(self):
        """Plot performance metrics from the analysis."""
        logger.info("Plotting performance metrics...")
        
        # Combine timing metrics
        metrics = {
            **{f"Load {k}": v for k, v in self.load_times.items()},
            **{f"Analysis {k}": v for k, v in self.analysis_times.items()}
        }
        
        if not metrics:
            logger.warning("No performance metrics to plot")
            return
        
        # Create bar chart
        plt.figure(figsize=(12, 8))
        plt.bar(metrics.keys(), metrics.values())
        plt.xlabel('Operation')
        plt.ylabel('Time (seconds)')
        plt.title('Performance Metrics')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save plot
        output_path = os.path.join(self.output_dir, "performance_metrics.png")
        plt.savefig(output_path)
        plt.close()
        logger.info(f"Saved performance metrics plot to: {output_path}")
        
        # Save metrics to CSV
        metrics_df = pd.DataFrame(list(metrics.items()), columns=['Operation', 'Time (seconds)'])
        metrics_csv_path = os.path.join(self.output_dir, "performance_metrics.csv")
        metrics_df.to_csv(metrics_csv_path, index=False)
        logger.info(f"Saved performance metrics to: {metrics_csv_path}")
    
    def run_analysis(self):
        """Run the complete analysis pipeline."""
        # Load data
        self.skill_taxonomy, duration = self.load_skills()
        self.load_times['skills'] = duration
        
        self.job_architecture, duration = self.load_jobs()
        self.load_times['jobs'] = duration
        
        self.employee_database, duration = self.load_employees()
        self.load_times['employees'] = duration
        
        # Initialize components
        _, duration = self.initialize_similarity_calculator()
        self.load_times['similarity_calculator'] = duration
        
        _, duration = self.initialize_visualization_manager()
        self.load_times['visualization_manager'] = duration
        
        # Get departments
        departments = set(job.department for job in self.job_architecture.jobs.values())
        logger.info(f"Found {len(departments)} departments: {', '.join(departments)}")
        
        # Analyze largest departments
        dept_counts = {}
        for job in self.job_architecture.jobs.values():
            dept_counts[job.department] = dept_counts.get(job.department, 0) + 1
        
        top_departments = sorted(dept_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        logger.info(f"Top departments by job count: {top_departments}")
        
        # Analyze each top department
        for dept, _ in top_departments:
            _, duration = self.analyze_department_similarity(dept)
            self.analysis_times[f'{dept}_similarity'] = duration
            
            _, duration = self.generate_department_visualization(dept)
            self.analysis_times[f'{dept}_visualization'] = duration
        
        # Analyze cross-department similarity for top 2 departments
        if len(top_departments) >= 2:
            dept1, _ = top_departments[0]
            dept2, _ = top_departments[1]
            _, duration = self.analyze_cross_department_similarity(dept1, dept2)
            self.analysis_times[f'{dept1}_vs_{dept2}_similarity'] = duration
        
        # Plot performance metrics
        self.plot_performance_metrics()
        
        logger.info("Analysis complete!")


def main():
    """Command line interface for the synthetic data analyzer."""
    parser = argparse.ArgumentParser(description="Analyze synthetic data for performance testing")
    
    parser.add_argument("--data-dir", type=str, required=True,
                        help="Directory containing synthetic data")
    
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory for analysis results")
    
    parser.add_argument("--sample-jobs", type=int, default=None,
                        help="Sample a subset of jobs for analysis")
    
    parser.add_argument("--sample-employees", type=int, default=None,
                        help="Sample a subset of employees for analysis")
    
    args = parser.parse_args()
    
    # Set up sample sizes if specified
    sample_size = None
    if args.sample_jobs or args.sample_employees:
        sample_size = {}
        if args.sample_jobs:
            sample_size['jobs'] = args.sample_jobs
        if args.sample_employees:
            sample_size['employees'] = args.sample_employees
    
    analyzer = SyntheticDataAnalyzer(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        sample_size=sample_size
    )
    analyzer.run_analysis()


if __name__ == "__main__":
    main() 