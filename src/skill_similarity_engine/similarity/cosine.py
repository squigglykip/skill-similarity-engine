"""
Implementation of cosine similarity calculations using TF-IDF vectorization.

This module provides functionality for calculating similarity between skills,
jobs, and employees using the cosine similarity metric with TF-IDF vectors.
"""

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Union

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity

from ..models.employees import Employee, EmployeeDatabase
from ..models.jobs import Job, JobArchitecture
from ..models.skills import Skill, SkillTaxonomy


@dataclass
class TfidfVectorizer:
    """
    Vectorizer that transforms skill data into TF-IDF vectors.
    
    Attributes:
        skill_taxonomy: The skill taxonomy containing all skills
        idf_values: Dictionary mapping skill IDs to their IDF values
        skill_indices: Dictionary mapping skill IDs to their index in the vector
        num_skills: Total number of skills in the taxonomy
    """
    skill_taxonomy: SkillTaxonomy
    idf_values: Dict[str, float] = field(default_factory=dict)
    skill_indices: Dict[str, int] = field(default_factory=dict)
    num_skills: int = 0
    
    def __post_init__(self):
        """Initialize the vectorizer with skills from the taxonomy."""
        # Create mapping from skill IDs to indices in the vector
        for i, skill_id in enumerate(self.skill_taxonomy.skills.keys()):
            self.skill_indices[skill_id] = i
        
        self.num_skills = len(self.skill_indices)
    
    def fit(self, job_architecture: JobArchitecture) -> None:
        """
        Calculate IDF values for skills based on job occurrences.
        
        Args:
            job_architecture: The job architecture containing all jobs
        """
        # Count in how many jobs each skill appears
        skill_doc_counts = Counter()
        total_jobs = len(job_architecture.jobs)
        
        for job in job_architecture.jobs.values():
            # Count each skill only once per job
            for skill_id in job.skills:
                skill_doc_counts[skill_id] += 1
        
        # Calculate IDF values for each skill
        for skill_id in self.skill_taxonomy.skills:
            doc_count = skill_doc_counts.get(skill_id, 0)
            # Add 1 to avoid division by zero (smoothing)
            self.idf_values[skill_id] = math.log((total_jobs + 1) / (doc_count + 1)) + 1
    
    def transform_job(self, job: Job) -> np.ndarray:
        """
        Transform a job into a TF-IDF vector.
        
        Args:
            job: The job to transform
            
        Returns:
            TF-IDF vector representation of the job
        """
        # Initialize empty vector
        vector = np.zeros(self.num_skills)
        
        # Get total skill count for TF calculation
        total_skills = sum(proficiency for proficiency in job.skills.values())
        
        # Fill vector with TF-IDF values
        for skill_id, proficiency in job.skills.items():
            if skill_id in self.skill_indices:
                index = self.skill_indices[skill_id]
                # TF = skill proficiency / total of all proficiencies
                tf = proficiency / max(1, total_skills)
                idf = self.idf_values.get(skill_id, 1.0)
                vector[index] = tf * idf
        
        # Normalize vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector
    
    def transform_employee(self, employee: Employee) -> np.ndarray:
        """
        Transform an employee into a TF-IDF vector.
        
        Args:
            employee: The employee to transform
            
        Returns:
            TF-IDF vector representation of the employee
        """
        # Initialize empty vector
        vector = np.zeros(self.num_skills)
        
        # Get total skill proficiency for TF calculation
        total_proficiency = sum(proficiency for proficiency in employee.skills.values())
        
        # Fill vector with TF-IDF values
        for skill_id, proficiency in employee.skills.items():
            if skill_id in self.skill_indices:
                index = self.skill_indices[skill_id]
                # TF = skill proficiency / total of all proficiencies
                tf = proficiency / max(1, total_proficiency)
                idf = self.idf_values.get(skill_id, 1.0)
                vector[index] = tf * idf
        
        # Normalize vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector
    
    def transform_skill_set(self, skills: Dict[str, int]) -> np.ndarray:
        """
        Transform a generic set of skills with proficiency levels into a TF-IDF vector.
        
        Args:
            skills: Dictionary mapping skill IDs to proficiency levels
            
        Returns:
            TF-IDF vector representation of the skill set
        """
        # Initialize empty vector
        vector = np.zeros(self.num_skills)
        
        # Get total skill proficiency for TF calculation
        total_proficiency = sum(proficiency for proficiency in skills.values())
        
        # Fill vector with TF-IDF values
        for skill_id, proficiency in skills.items():
            if skill_id in self.skill_indices:
                index = self.skill_indices[skill_id]
                # TF = skill proficiency / total of all proficiencies
                tf = proficiency / max(1, total_proficiency)
                idf = self.idf_values.get(skill_id, 1.0)
                vector[index] = tf * idf
        
        # Normalize vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector


@dataclass
class CosineSimilarityCalculator:
    """
    Calculator for cosine similarity between skills, jobs, and employees.
    
    Attributes:
        vectorizer: The TF-IDF vectorizer for transforming skill data
        skill_taxonomy: The skill taxonomy containing all skills
        job_architecture: The job architecture containing all jobs
        employee_database: The employee database containing all employees
        job_vectors: Cached TF-IDF vectors for jobs
        employee_vectors: Cached TF-IDF vectors for employees
    """
    vectorizer: TfidfVectorizer
    skill_taxonomy: SkillTaxonomy
    job_architecture: JobArchitecture
    employee_database: Optional[EmployeeDatabase] = None
    job_vectors: Dict[str, np.ndarray] = field(default_factory=dict)
    employee_vectors: Dict[str, np.ndarray] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the calculator by fitting the vectorizer and caching vectors."""
        # Fit the vectorizer on the job architecture
        self.vectorizer.fit(self.job_architecture)
        
        # Pre-compute vectors for all jobs
        for job_id, job in self.job_architecture.jobs.items():
            self.job_vectors[job_id] = self.vectorizer.transform_job(job)
        
        # Pre-compute vectors for all employees if provided
        if self.employee_database:
            for employee_id, employee in self.employee_database.employees.items():
                self.employee_vectors[employee_id] = self.vectorizer.transform_employee(employee)
    
    def calculate_job_similarity(self, job1_id: str, job2_id: str) -> float:
        """
        Calculate the similarity between two jobs.
        
        Args:
            job1_id: ID of the first job
            job2_id: ID of the second job
            
        Returns:
            Cosine similarity score between the two jobs
            
        Raises:
            ValueError: If any of the job IDs are not found
        """
        if job1_id not in self.job_vectors:
            raise ValueError(f"Job with ID {job1_id} not found")
        
        if job2_id not in self.job_vectors:
            raise ValueError(f"Job with ID {job2_id} not found")
        
        vector1 = self.job_vectors[job1_id].reshape(1, -1)
        vector2 = self.job_vectors[job2_id].reshape(1, -1)
        
        return float(sklearn_cosine_similarity(vector1, vector2)[0, 0])
    
    def calculate_employee_similarity(self, employee1_id: str, employee2_id: str) -> float:
        """
        Calculate the similarity between two employees.
        
        Args:
            employee1_id: ID of the first employee
            employee2_id: ID of the second employee
            
        Returns:
            Cosine similarity score between the two employees
            
        Raises:
            ValueError: If any of the employee IDs are not found or employee database is not set
        """
        if not self.employee_database:
            raise ValueError("Employee database not set")
        
        if employee1_id not in self.employee_vectors:
            raise ValueError(f"Employee with ID {employee1_id} not found")
        
        if employee2_id not in self.employee_vectors:
            raise ValueError(f"Employee with ID {employee2_id} not found")
        
        vector1 = self.employee_vectors[employee1_id].reshape(1, -1)
        vector2 = self.employee_vectors[employee2_id].reshape(1, -1)
        
        return float(sklearn_cosine_similarity(vector1, vector2)[0, 0])
    
    def calculate_job_employee_similarity(self, job_id: str, employee_id: str) -> float:
        """
        Calculate the similarity between a job and an employee.
        
        Args:
            job_id: ID of the job
            employee_id: ID of the employee
            
        Returns:
            Cosine similarity score between the job and employee
            
        Raises:
            ValueError: If the job ID or employee ID is not found or employee database is not set
        """
        if not self.employee_database:
            raise ValueError("Employee database not set")
        
        if job_id not in self.job_vectors:
            raise ValueError(f"Job with ID {job_id} not found")
        
        if employee_id not in self.employee_vectors:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        job_vector = self.job_vectors[job_id].reshape(1, -1)
        employee_vector = self.employee_vectors[employee_id].reshape(1, -1)
        
        return float(sklearn_cosine_similarity(job_vector, employee_vector)[0, 0])
    
    def find_similar_jobs(self, job_id: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Find the most similar jobs to a given job.
        
        Args:
            job_id: ID of the job to find similar jobs for
            top_n: Number of similar jobs to return
            
        Returns:
            List of tuples containing job IDs and similarity scores, sorted by score
            
        Raises:
            ValueError: If the job ID is not found
        """
        if job_id not in self.job_vectors:
            raise ValueError(f"Job with ID {job_id} not found")
        
        job_vector = self.job_vectors[job_id].reshape(1, -1)
        
        # Calculate similarity with all other jobs
        similarities = []
        for other_id, other_vector in self.job_vectors.items():
            if other_id != job_id:  # Skip self
                similarity = float(sklearn_cosine_similarity(job_vector, other_vector.reshape(1, -1))[0, 0])
                similarities.append((other_id, similarity))
        
        # Sort by similarity score in descending order
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_n]
    
    def find_similar_employees(self, employee_id: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Find the most similar employees to a given employee.
        
        Args:
            employee_id: ID of the employee to find similar employees for
            top_n: Number of similar employees to return
            
        Returns:
            List of tuples containing employee IDs and similarity scores, sorted by score
            
        Raises:
            ValueError: If the employee ID is not found or employee database is not set
        """
        if not self.employee_database:
            raise ValueError("Employee database not set")
        
        if employee_id not in self.employee_vectors:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        employee_vector = self.employee_vectors[employee_id].reshape(1, -1)
        
        # Calculate similarity with all other employees
        similarities = []
        for other_id, other_vector in self.employee_vectors.items():
            if other_id != employee_id:  # Skip self
                similarity = float(sklearn_cosine_similarity(employee_vector, other_vector.reshape(1, -1))[0, 0])
                similarities.append((other_id, similarity))
        
        # Sort by similarity score in descending order
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_n]
    
    def find_suitable_jobs(self, employee_id: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Find the most suitable jobs for a given employee based on skill similarity.
        
        Args:
            employee_id: ID of the employee to find suitable jobs for
            top_n: Number of suitable jobs to return
            
        Returns:
            List of tuples containing job IDs and similarity scores, sorted by score
            
        Raises:
            ValueError: If the employee ID is not found or employee database is not set
        """
        if not self.employee_database:
            raise ValueError("Employee database not set")
        
        if employee_id not in self.employee_vectors:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        employee_vector = self.employee_vectors[employee_id].reshape(1, -1)
        
        # Calculate similarity with all jobs
        similarities = []
        for job_id, job_vector in self.job_vectors.items():
            similarity = float(sklearn_cosine_similarity(employee_vector, job_vector.reshape(1, -1))[0, 0])
            similarities.append((job_id, similarity))
        
        # Sort by similarity score in descending order
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_n]
    
    def find_suitable_employees(self, job_id: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Find the most suitable employees for a given job based on skill similarity.
        
        Args:
            job_id: ID of the job to find suitable employees for
            top_n: Number of suitable employees to return
            
        Returns:
            List of tuples containing employee IDs and similarity scores, sorted by score
            
        Raises:
            ValueError: If the job ID is not found or employee database is not set
        """
        if not self.employee_database:
            raise ValueError("Employee database not set")
        
        if job_id not in self.job_vectors:
            raise ValueError(f"Job with ID {job_id} not found")
        
        job_vector = self.job_vectors[job_id].reshape(1, -1)
        
        # Calculate similarity with all employees
        similarities = []
        for employee_id, employee_vector in self.employee_vectors.items():
            similarity = float(sklearn_cosine_similarity(job_vector, employee_vector.reshape(1, -1))[0, 0])
            similarities.append((employee_id, similarity))
        
        # Sort by similarity score in descending order
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_n]
    
    def calculate_similarity_matrix(self, entity_type: str = "job") -> Tuple[np.ndarray, List[str]]:
        """
        Calculate a similarity matrix for jobs or employees.
        
        Args:
            entity_type: Type of entity to calculate matrix for ("job" or "employee")
            
        Returns:
            Tuple containing the similarity matrix and list of entity IDs
            
        Raises:
            ValueError: If entity_type is invalid or employee database is not set for employee matrix
        """
        if entity_type.lower() == "job":
            # Get all job vectors in consistent order
            ids = list(self.job_vectors.keys())
            vectors = np.array([self.job_vectors[job_id] for job_id in ids])
            
        elif entity_type.lower() == "employee":
            if not self.employee_database:
                raise ValueError("Employee database not set for employee similarity matrix")
            
            # Get all employee vectors in consistent order
            ids = list(self.employee_vectors.keys())
            vectors = np.array([self.employee_vectors[employee_id] for employee_id in ids])
            
        else:
            raise ValueError(f"Invalid entity type: {entity_type}. Must be 'job' or 'employee'")
        
        # Calculate pairwise cosine similarity
        similarity_matrix = sklearn_cosine_similarity(vectors)
        
        return similarity_matrix, ids 