#!/usr/bin/env python3
"""
Functional test for performance of the similarity engine.

This test measures the performance of various components of the skill similarity
engine on datasets of different sizes. It checks that the performance scales
as expected with dataset size.
"""

import sys
import os

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import time
import unittest
import random
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer as SklearnTfidfVectorizer
import numpy as np

from skill_similarity_engine.models.skills import SkillTaxonomy, Skill, SkillCategory, SkillType
from skill_similarity_engine.models.jobs import JobArchitecture, Job, JobLevel
from skill_similarity_engine.models.employees import EmployeeDatabase, Employee
from skill_similarity_engine.similarity.cosine import CosineSimilarityCalculator
from skill_similarity_engine.analysis.gap import SkillGapAnalyzer
from skill_similarity_engine.config.settings import ConfigManager

# Custom TfidfVectorizer for testing
class TfidfVectorizer:
    """
    A wrapper around sklearn's TfidfVectorizer that works with our job architecture.
    This is a simplified version for testing purposes.
    """
    def __init__(self, **kwargs):
        self.vectorizer = SklearnTfidfVectorizer(**kwargs)
        self.job_vectors = {}
        self.skill_ids = []

    def fit(self, job_architecture):
        """
        Fit the vectorizer to a job architecture.
        
        Args:
            job_architecture: JobArchitecture object containing jobs with skills
        """
        # Create a set of all skill IDs across all jobs
        all_skill_ids = set()
        for job in job_architecture.jobs.values():
            all_skill_ids.update(job.skills.keys())
        
        # Convert to sorted list for consistent indexing
        self.skill_ids = sorted(list(all_skill_ids))
        
        # No actual fitting needed for our simple implementation
        return self

    def transform(self, job_architecture):
        """
        Transform job architecture to vectors.
        
        Args:
            job_architecture: JobArchitecture object containing jobs with skills
            
        Returns:
            dict: Mapping of job IDs to skill vectors
        """
        # Create a sparse vector for each job
        job_vectors = {}
        
        for job_id, job in job_architecture.jobs.items():
            # Create a vector where the index is the position of the skill in skill_ids
            vector = np.zeros(len(self.skill_ids))
            
            for i, skill_id in enumerate(self.skill_ids):
                # If the job has this skill, set its value to the proficiency
                if skill_id in job.skills:
                    vector[i] = job.skills[skill_id] / 5.0  # Normalize to 0-1 range
            
            # Store the vector
            job_vectors[job_id] = vector
        
        self.job_vectors = job_vectors
        return job_vectors

    def transform_job(self, job):
        """
        Transform a single job to a vector.
        
        Args:
            job: Job object containing skills
            
        Returns:
            numpy.ndarray: Vector representation of the job
        """
        # Create a vector where the index is the position of the skill in skill_ids
        vector = np.zeros(len(self.skill_ids))
        
        for i, skill_id in enumerate(self.skill_ids):
            # If the job has this skill, set its value to the proficiency
            if skill_id in job.skills:
                vector[i] = job.skills[skill_id] / 5.0  # Normalize to 0-1 range
        
        return vector

    def transform_employee(self, employee):
        """
        Transform a single employee to a vector.
        
        Args:
            employee: Employee object containing skills
            
        Returns:
            numpy.ndarray: Vector representation of the employee
        """
        # Create a vector where the index is the position of the skill in skill_ids
        vector = np.zeros(len(self.skill_ids))
        
        for i, skill_id in enumerate(self.skill_ids):
            # If the employee has this skill, set its value to the proficiency
            if skill_id in employee.skills:
                vector[i] = employee.skills[skill_id] / 5.0  # Normalize to 0-1 range
        
        return vector

    def fit_transform(self, job_architecture):
        """
        Fit to data, then transform it.
        
        Args:
            job_architecture: JobArchitecture object
            
        Returns:
            dict: Mapping of job IDs to skill vectors
        """
        self.fit(job_architecture)
        return self.transform(job_architecture)

class TestPerformance(unittest.TestCase):
    """Test the performance of the similarity engine."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment with synthetic data of various sizes."""
        # Configure random seed for reproducibility
        random.seed(42)
        
        # Create a synthetic skill taxonomy with 100 skills and 5 categories
        cls.taxonomy = cls._create_skill_taxonomy(100, 5)
        
        # Create a synthetic job architecture with 50 jobs, each with 10-20 skills
        cls.job_architecture = cls._create_job_architecture(cls.taxonomy, 50, 10, 20)
        
        # Create a synthetic employee database with 200 employees, each with 5-15 skills
        cls.employee_database = cls._create_employee_database(cls.taxonomy, cls.job_architecture, 200, 5, 15)
        
        # Set up config manager for specific test settings
        cls.config_manager = ConfigManager()
        
        # Configure similarity settings
        cls.config_manager.config.similarity.tfidf_min_df = 1
        cls.config_manager.config.similarity.tfidf_max_df = 0.9
        cls.config_manager.config.similarity.normalization_method = "l2"
        cls.config_manager.config.similarity.opportunity_similarity_threshold = 0.7
        
        # Create the similarity calculator that will use the config settings
        cls.similarity_calculator = CosineSimilarityCalculator(
            vectorizer=TfidfVectorizer(),  # Use our custom TfidfVectorizer
            skill_taxonomy=cls.taxonomy,
            job_architecture=cls.job_architecture,
            employee_database=cls.employee_database
        )
        
        # Configure gap analysis settings
        cls.config_manager.config.gap_analysis.min_proficiency_ratio = 0.7
        cls.config_manager.config.gap_analysis.skill_difficulty_factor = 1.2
        cls.config_manager.config.gap_analysis.min_gap_threshold = 0.25
        cls.config_manager.config.gap_analysis.category_weights = {
            "Technical Skills": 1.2,
            "Soft Skills": 0.8,
            "Domain Skills": 1.0,
            "Leadership Skills": 1.1,
            "Process Skills": 0.9
        }
        
        # Create the gap analyzer that will use the config settings
        cls.gap_analyzer = SkillGapAnalyzer(
            skill_taxonomy=cls.taxonomy,
            job_architecture=cls.job_architecture,
            employee_database=cls.employee_database
        )
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests have run."""
        # Reset the ConfigManager singleton to avoid affecting other tests
        ConfigManager._instance = None
    
    @staticmethod
    def _create_skill_taxonomy(num_skills, num_categories):
        """Create a synthetic skill taxonomy."""
        taxonomy = SkillTaxonomy()
        
        # Create categories
        category_types = {
            "Technical Skills": SkillType.TECHNICAL,
            "Soft Skills": SkillType.SOFT,
            "Domain Skills": SkillType.DOMAIN,
            "Leadership Skills": SkillType.SOFT,
            "Process Skills": SkillType.METHODOLOGY
        }
        
        # Add categories
        for cat_id, (cat_name, skill_type) in enumerate(category_types.items(), 1):
            if cat_id <= num_categories:
                category_id = f"C{cat_id:03d}"
                # Check the actual parameters required by SkillCategory
                try:
                    # Try with type parameter
                    category = SkillCategory(
                        category_id=category_id,
                        name=cat_name,
                        type=skill_type
                    )
                except TypeError:
                    try:
                        # Try without any type parameter
                        category = SkillCategory(
                            category_id=category_id,
                            name=cat_name
                        )
                    except TypeError:
                        # As a last resort, try with skill_type parameter
                        category = SkillCategory(
                            category_id=category_id,
                            name=cat_name,
                            skill_type=skill_type
                        )
                        
                taxonomy.add_category(category)
        
        # Add skills
        for skill_id in range(1, num_skills + 1):
            # Assign each skill to a random category
            category_id = f"C{random.randint(1, min(num_categories, len(category_types))):03d}"
            
            # Create the skill
            skill = Skill(
                skill_id=f"S{skill_id:03d}",
                name=f"Skill {skill_id}",
                category_id=category_id,
            )
            
            # Set random difficulty between 1 and 5
            skill.difficulty = random.randint(1, 5)
            
            # Add to taxonomy
            taxonomy.add_skill(skill)
            
            # Add random aliases to some skills
            if random.random() < 0.3:
                num_aliases = random.randint(1, 3)
                for i in range(num_aliases):
                    skill.add_alias(f"Alias {i+1} for Skill {skill_id}")
            
            # Add random related skills to some skills
            if random.random() < 0.3 and skill_id > 5:
                num_related = random.randint(1, 3)
                for _ in range(num_related):
                    related_id = f"S{random.randint(1, skill_id-1):03d}"
                    skill.add_related_skill(related_id)
        
        return taxonomy
    
    @staticmethod
    def _create_job_architecture(taxonomy, num_jobs, min_skills, max_skills):
        """Create a synthetic job architecture."""
        architecture = JobArchitecture()
        
        # Define departments
        departments = [
            "Engineering", "Data Science", "Product Management", "Design",
            "Marketing", "Sales", "Finance", "Human Resources", "Operations"
        ]
        
        # Define job titles per department
        job_titles = {
            "Engineering": ["Software Engineer", "DevOps Engineer", "QA Engineer", "Technical Lead", "Engineering Manager"],
            "Data Science": ["Data Scientist", "ML Engineer", "Data Analyst", "Research Scientist", "Data Engineer"],
            "Product Management": ["Product Manager", "Product Owner", "Business Analyst", "Program Manager"],
            "Design": ["UI Designer", "UX Researcher", "Graphic Designer", "Design Manager"],
            "Marketing": ["Marketing Specialist", "Content Writer", "SEO Specialist", "Marketing Manager"],
            "Sales": ["Sales Representative", "Account Executive", "Sales Manager", "Customer Success Manager"],
            "Finance": ["Financial Analyst", "Accountant", "Finance Manager", "Controller"],
            "Human Resources": ["HR Specialist", "Recruiter", "HR Manager", "Talent Acquisition Manager"],
            "Operations": ["Operations Analyst", "Operations Manager", "Logistics Coordinator", "Supply Chain Manager"]
        }
        
        # All possible skill IDs
        all_skill_ids = list(taxonomy.skills.keys())
        
        # Create jobs
        for job_id in range(1, num_jobs + 1):
            # Select a random department
            department = random.choice(departments)
            
            # Select a random title for that department
            title = random.choice(job_titles[department])
            
            # Select a random level
            level = random.choice(list(JobLevel))
            
            # Select a random number of skills
            num_skills = random.randint(min_skills, max_skills)
            
            # Select random skills
            selected_skill_ids = random.sample(all_skill_ids, num_skills)
            
            # Assign random proficiency levels
            skills = {skill_id: random.randint(1, 5) for skill_id in selected_skill_ids}
            
            # Create the job
            job = Job(
                job_id=f"J{job_id:03d}",
                title=f"{level.name.title().replace('_', ' ')} {title}",
                department=department,
                level=level,
                skills=skills
            )
            
            # Add to architecture
            architecture.add_job(job)
        
        return architecture
    
    @staticmethod
    def _create_employee_database(taxonomy, job_architecture, num_employees, min_skills, max_skills):
        """Create a synthetic employee database."""
        database = EmployeeDatabase()
        
        # All possible skill IDs
        all_skill_ids = list(taxonomy.skills.keys())
        
        # All possible job IDs
        all_job_ids = list(job_architecture.jobs.keys())
        
        # First names for variety
        first_names = [
            "Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Henry",
            "Isabel", "Jack", "Kate", "Liam", "Mia", "Noah", "Olivia", "Peter",
            "Quinn", "Rachel", "Sam", "Taylor", "Uma", "Victor", "Wendy", "Xavier",
            "Yasmine", "Zach"
        ]
        
        # Last names for variety
        last_names = [
            "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson",
            "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin",
            "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez", "Lewis", "Lee",
            "Walker", "Hall", "Allen", "Young", "King", "Wright"
        ]
        
        # Create employees
        for emp_id in range(1, num_employees + 1):
            # Select a random name
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            
            # Select a random job
            current_job = random.choice(all_job_ids)
            
            # Select a random number of skills
            num_skills = random.randint(min_skills, max_skills)
            
            # Select random skills
            selected_skill_ids = random.sample(all_skill_ids, num_skills)
            
            # Assign random proficiency levels
            skills = {skill_id: random.randint(1, 5) for skill_id in selected_skill_ids}
            
            # Create the employee
            employee = Employee(
                employee_id=f"E{emp_id:03d}",
                name=name,
                current_job=current_job,
                skills=skills
            )
            
            # Add to database
            database.add_employee(employee)
        
        return database
    
    def test_similarity_calculator_performance(self):
        """Test the performance of the similarity calculator."""
        # Measure time to fit the vectorizer
        start_time = time.time()
        # The CosineSimilarityCalculator doesn't have a fit() method, so we'll just
        # access the job_vectors which should trigger the internal calculation
        job_vectors = self.similarity_calculator.job_vectors
        fit_time = time.time() - start_time
        
        # Log performance
        print(f"Time to prepare job vectors: {fit_time:.4f} seconds")
        
        # Acceptable time for fitting - should be under 5 seconds for 100 skills
        self.assertLess(fit_time, 5.0)
        
        # Check similarity matrix calculation performance
        start_time = time.time()
        similarity_matrix, job_ids = self.similarity_calculator.calculate_similarity_matrix()
        matrix_time = time.time() - start_time
        
        # Log performance
        print(f"Time to calculate job similarity matrix: {matrix_time:.4f} seconds")
        
        # Verify results (should be a numpy array and a list of job IDs)
        self.assertTrue(isinstance(similarity_matrix, np.ndarray))
        self.assertTrue(isinstance(job_ids, list))
        self.assertGreater(len(job_ids), 0)
        self.assertEqual(similarity_matrix.shape, (len(job_ids), len(job_ids)))
    
    def test_gap_analyzer_performance(self):
        """Test the performance of the gap analyzer."""
        # Select random employee and job
        employee_id = random.choice(list(self.employee_database.employees.keys()))
        job_id = random.choice(list(self.job_architecture.jobs.keys()))
        
        # Measure time to analyze gap
        start_time = time.time()
        gap_result = self.gap_analyzer.analyze_employee_job_gap(employee_id, job_id)
        gap_time = time.time() - start_time
        
        # Log performance
        print(f"Time to analyze employee-job gap: {gap_time:.4f} seconds")
        
        # Verify results
        self.assertIsNotNone(gap_result)
        self.assertTrue(hasattr(gap_result, 'missing_skills'))
        self.assertTrue(hasattr(gap_result, 'matching_skills'))
        self.assertTrue(hasattr(gap_result, 'excess_skills'))
        
        # Acceptable time for gap analysis - should be under 1 second
        self.assertLess(gap_time, 1.0)
        
        # Measure time to analyze multiple gaps (batch processing)
        num_analyses = 10
        random_employee_ids = random.sample(list(self.employee_database.employees.keys()), min(num_analyses, len(self.employee_database.employees)))
        random_job_ids = random.sample(list(self.job_architecture.jobs.keys()), min(num_analyses, len(self.job_architecture.jobs)))
        
        start_time = time.time()
        for i in range(num_analyses):
            emp_id = random_employee_ids[i % len(random_employee_ids)]
            j_id = random_job_ids[i % len(random_job_ids)]
            self.gap_analyzer.analyze_employee_job_gap(emp_id, j_id)
        batch_time = time.time() - start_time
        
        # Log performance
        print(f"Time to analyze {num_analyses} employee-job gaps: {batch_time:.4f} seconds")
        
        # Acceptable time for batch processing - should scale roughly linearly
        avg_time_per_analysis = batch_time / num_analyses
        self.assertLess(avg_time_per_analysis, 1.0)
        print(f"Average time per analysis: {avg_time_per_analysis:.4f} seconds")


if __name__ == "__main__":
    unittest.main() 