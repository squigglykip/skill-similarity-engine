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
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity

from ..config.settings import ConfigManager
from ..models.employees import Employee, EmployeeDatabase
from ..models.jobs import Job, JobArchitecture, RoleTrack
from ..models.skills import Skill, SkillTaxonomy

# Constants for similarity calculations
MAX_SENIORITY_DIFFERENCE = 6  # Maximum difference between seniority levels (1-7)
MAX_LOCATION_SIMILARITY = 1.0  # Maximum similarity score for location


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
        config_manager: Configuration manager for similarity settings
    """
    vectorizer: TfidfVectorizer
    skill_taxonomy: SkillTaxonomy
    job_architecture: JobArchitecture
    employee_database: Optional[EmployeeDatabase] = None
    job_vectors: Dict[str, np.ndarray] = field(default_factory=dict)
    employee_vectors: Dict[str, np.ndarray] = field(default_factory=dict)
    config_manager: ConfigManager = field(default_factory=ConfigManager)
    
    def __post_init__(self):
        """Initialize the calculator by fitting the vectorizer and caching vectors."""
        # Fit the vectorizer on the job architecture
        self.vectorizer.fit(self.job_architecture)
        
        # Pre-compute vectors for all jobs
        for job_id, job in self.job_architecture.jobs.items():
            self.job_vectors[job_id] = self.vectorizer.transform_job(job)
        
        # Pre-compute vectors for all employees if provided
        if self.employee_database is not None:
            for employee_id, employee in self.employee_database.employees.items():
                self.employee_vectors[employee_id] = self.vectorizer.transform_employee(employee)
    
    def prepare_job_vectors(self):
        """
        Prepare job vectors for similarity calculations.
        
        This method recomputes TF-IDF vectors for all jobs in the job architecture.
        It's useful when the job architecture has been updated.
        """
        # Fit the vectorizer on the job architecture
        self.vectorizer.fit(self.job_architecture)
        
        # Pre-compute vectors for all jobs
        for job_id, job in self.job_architecture.jobs.items():
            self.job_vectors[job_id] = self.vectorizer.transform_job(job)
    
    def calculate_job_similarity(self, job1_id: str, job2_id: str) -> float:
        """
        Calculate the similarity between two jobs, including enhancements for seniority, role track, and location.
        
        Args:
            job1_id: ID of the first job
            job2_id: ID of the second job
            
        Returns:
            Weighted similarity score between the two jobs
            
        Raises:
            ValueError: If any of the job IDs are not found
        """
        if job1_id not in self.job_vectors:
            raise ValueError(f"Job with ID {job1_id} not found")
        
        if job2_id not in self.job_vectors:
            raise ValueError(f"Job with ID {job2_id} not found")
        
        # Get jobs
        job1 = self.job_architecture.jobs[job1_id]
        job2 = self.job_architecture.jobs[job2_id]
        
        # Calculate base similarity using skills
        vector1 = self.job_vectors[job1_id].reshape(1, -1)
        vector2 = self.job_vectors[job2_id].reshape(1, -1)
        skill_similarity = float(sklearn_cosine_similarity(vector1, vector2)[0, 0])
        
        # Get extension weights from config
        config = self.config_manager.get_config()
        seniority_weight = config.future_extensions.seniority_weight
        role_track_weight = config.future_extensions.role_track_weight
        location_weight = config.future_extensions.location_weight
        skill_type_weight = config.future_extensions.skill_type_weight
        
        # Get total weight excluding base skills weight (which is always 1.0)
        extension_weight_sum = seniority_weight + role_track_weight + location_weight + skill_type_weight
        
        # If no enhancements are enabled, return the plain skill similarity
        if extension_weight_sum == 0:
            return skill_similarity
        
        # Calculate the weight for skills in the final weighted average
        skill_weight = 1.0
        
        # Calculate weighted components
        weighted_skill_similarity = skill_similarity * skill_weight
        weighted_seniority_similarity = 0.0
        weighted_role_track_similarity = 0.0
        weighted_location_similarity = 0.0
        weighted_skill_type_similarity = 0.0
        
        # Calculate seniority similarity if enabled
        if seniority_weight > 0:
            seniority_similarity = self._calculate_seniority_similarity(job1, job2)
            weighted_seniority_similarity = seniority_similarity * seniority_weight
        
        # Calculate role track similarity if enabled
        if role_track_weight > 0:
            role_track_similarity = self._calculate_role_track_similarity(job1, job2)
            weighted_role_track_similarity = role_track_similarity * role_track_weight
        
        # Calculate location similarity if enabled
        if location_weight > 0:
            location_similarity = self._calculate_location_similarity(job1, job2)
            weighted_location_similarity = location_similarity * location_weight
            
        # Calculate skill type similarity if enabled
        if skill_type_weight > 0:
            skill_type_similarity = self._calculate_skill_type_similarity(job1, job2)
            weighted_skill_type_similarity = skill_type_similarity * skill_type_weight
        
        # Calculate weighted average similarity
        total_weight = skill_weight + extension_weight_sum
        weighted_similarity = (
            weighted_skill_similarity + 
            weighted_seniority_similarity + 
            weighted_role_track_similarity + 
            weighted_location_similarity +
            weighted_skill_type_similarity
        ) / total_weight
        
        return weighted_similarity
    
    def _calculate_seniority_similarity(self, job1: Job, job2: Job) -> float:
        """
        Calculate similarity based on seniority levels, favouring career progression.
        
        Args:
            job1: First job (the reference job)
            job2: Second job (the job being compared to)
            
        Returns:
            Similarity score based on seniority (0-1 range)
            
        Note:
            This implementation strongly favours career progression using configurable thresholds.
            Typically, same level and one step up are favourably scored, while steps down are penalised.
        """
        # Get configuration values
        config = self.config_manager.get_config().future_extensions
        
        # Calculate difference in seniority (positive if job2 is higher level)
        seniority_diff = job2.seniority - job1.seniority
        
        # Same level = highest similarity
        if seniority_diff == 0:
            return config.seniority_same_level_similarity
        
        # One step up = good similarity
        elif seniority_diff == 1:
            return config.seniority_one_up_similarity
        
        # Multiple steps up = moderate similarity decreasing with distance
        elif seniority_diff > 1:
            # Similarity decreases based on the configured step penalty
            return max(0.0, config.seniority_one_up_similarity - ((seniority_diff - 1) * config.seniority_up_step_penalty))
        
        # Any step down = extremely low similarity (effectively eliminating demotion recommendations)
        else:
            # Apply a severe penalty for any downward movement
            abs_diff = abs(seniority_diff)
            if abs_diff == 1:
                return config.seniority_one_down_similarity
            else:
                return config.seniority_down_similarity
    
    def _calculate_role_track_similarity(self, job1: Job, job2: Job) -> float:
        """
        Calculate similarity based on role tracks, favouring natural career progression.
        
        Args:
            job1: First job (the reference job)
            job2: Second job (the job being compared to)
            
        Returns:
            Similarity score based on role tracks (0-1 range)
            
        Note:
            This implementation considers career progression patterns:
            - Same role track = full similarity
            - IC to Leadership (career progression) = good similarity
            - Leadership to IC (demotion) = poor similarity
        """
        # Get configuration values
        config = self.config_manager.get_config().future_extensions
        
        # Same role track = full similarity
        if job1.role_track == job2.role_track:
            return config.role_track_same_similarity
        
        # Different role tracks - direction matters
        if job1.role_track == RoleTrack.INDIVIDUAL_CONTRIBUTOR and job2.role_track == RoleTrack.LEADERSHIP:
            # IC to Leadership is a natural career progression
            return config.role_track_different_similarity
        else:
            # Leadership to IC is typically a demotion/regression
            # This should be heavily penalized
            return config.role_track_regression_similarity
    
    def _calculate_location_similarity(self, job1: Job, job2: Job) -> float:
        """
        Calculate similarity based on location.
        
        Args:
            job1: First job
            job2: Second job
            
        Returns:
            Similarity score based on location (0-1 range)
        """
        # Get configuration values
        config = self.config_manager.get_config().future_extensions
        
        # If either location is empty, don't penalize
        if not job1.location or not job2.location:
            return config.location_same_similarity
        
        # Same location = full similarity
        if job1.location.lower() == job2.location.lower():
            return config.location_same_similarity
        
        # Different locations get lower similarity
        return config.location_different_similarity
    
    def _calculate_skill_type_similarity(self, job1: Job, job2: Job) -> float:
        """
        Calculate similarity based on skill types, giving different weights to different types of skills.
        
        Args:
            job1: First job
            job2: Second job
            
        Returns:
            Similarity score based on skill types (0-1 range)
            
        Note:
            This implementation applies the configured weights to different skill types,
            with higher weights reducing similarity scores when specialized skills are missing.
        """
        # Get configuration values
        config = self.config_manager.get_config().future_extensions
        skill_type_weights = config.skill_type_similarity_weights
        
        # Get skills from both jobs
        job1_skills = set(job1.skills.keys())
        job2_skills = set(job2.skills.keys())
        
        # Get all skills from both jobs
        all_skills = job1_skills.union(job2_skills)
        
        # If there are no skills, return 1.0 (perfect similarity)
        if not all_skills:
            return 1.0
        
        # Calculate weighted similarity score
        total_similarity = 0.0
        total_weight = 0.0
        
        for skill_id in all_skills:
            # Determine if the skill is present in both jobs
            in_job1 = skill_id in job1_skills
            in_job2 = skill_id in job2_skills
            
            # Get skill details from the taxonomy
            skill_type = "OTHER"  # Default if not found
            if skill_id in self.skill_taxonomy.skills:
                skill = self.skill_taxonomy.skills[skill_id]
                if hasattr(skill, 'skill_type') and skill.skill_type:
                    skill_type = skill.skill_type.name
            
            # Get weight for this skill type
            weight = skill_type_weights.get(skill_type, 1.0)
            
            # Apply weighted similarity calculation:
            # - If both have the skill or neither has it: full similarity (1.0)
            # - If only one has it: apply a penalty based on the weight
            #   Higher weights should result in lower similarity scores
            if in_job1 == in_job2:
                skill_similarity = 1.0
            else:
                # Apply weight as a penalty factor - higher weight means lower similarity
                # We use 1.0 divided by the weight to convert weight to a penalty
                # This ensures that higher weights lead to lower similarity values
                skill_similarity = 1.0 / (1.0 + weight)
            
            # Add to totals
            total_similarity += skill_similarity * weight
            total_weight += weight
        
        # Calculate weighted average
        if total_weight > 0:
            return total_similarity / total_weight
        
        return 1.0  # Default if no weights
    
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
        Find the most similar jobs to a given job, using enhanced similarity.
        
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
        
        # Calculate similarity with all other jobs
        similarities = []
        for other_id in self.job_architecture.jobs.keys():
            if other_id != job_id:  # Skip self
                similarity = self.calculate_job_similarity(job_id, other_id)
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
            # Get all job IDs in consistent order
            ids = list(self.job_architecture.jobs.keys())
            
            # Initialize matrix
            n_jobs = len(ids)
            similarity_matrix = np.zeros((n_jobs, n_jobs))
            
            # Calculate pairwise similarities, but only for upper triangle
            # to ensure matrix symmetry
            for i in range(n_jobs):
                # Diagonal is always 1.0
                similarity_matrix[i, i] = 1.0
                
                # Calculate upper triangle only
                for j in range(i+1, n_jobs):
                    # Calculate enhanced similarity
                    similarity = self.calculate_job_similarity(ids[i], ids[j])
                    
                    # Set both (i,j) and (j,i) to ensure symmetry
                    similarity_matrix[i, j] = similarity
                    similarity_matrix[j, i] = similarity
            
        elif entity_type.lower() == "employee":
            if not self.employee_database:
                raise ValueError("Employee database not set for employee similarity matrix")
            
            # Get all employee vectors in consistent order
            ids = list(self.employee_vectors.keys())
            vectors = np.array([self.employee_vectors[employee_id] for employee_id in ids])
            
            # Calculate pairwise cosine similarity
            similarity_matrix = sklearn_cosine_similarity(vectors)
            
        elif entity_type.lower() == "emp_job":
            if not self.employee_database:
                raise ValueError("Employee database not set for employee-job similarity matrix")
            
            # Get all employee and job IDs in consistent order
            employee_ids = list(self.employee_vectors.keys())
            job_ids = list(self.job_vectors.keys())
            
            # Initialize matrix with employees as rows and jobs as columns
            n_employees = len(employee_ids)
            n_jobs = len(job_ids)
            similarity_matrix = np.zeros((n_employees, n_jobs))
            
            # Calculate similarities between each employee and job
            for i, employee_id in enumerate(employee_ids):
                employee_vector = self.employee_vectors[employee_id].reshape(1, -1)
                for j, job_id in enumerate(job_ids):
                    job_vector = self.job_vectors[job_id].reshape(1, -1)
                    similarity = float(sklearn_cosine_similarity(employee_vector, job_vector)[0, 0])
                    similarity_matrix[i, j] = similarity
            
            # Return matrix, employee IDs, and job IDs
            return similarity_matrix, employee_ids, job_ids
            
        else:
            raise ValueError(f"Invalid entity type: {entity_type}. Must be 'job', 'employee', or 'emp_job'")
        
        # Ensure values are within [0, 1] range
        similarity_matrix = np.clip(similarity_matrix, 0, 1)
        
        return similarity_matrix, ids
        
    def calculate_employee_job_similarity_matrix(self, employee_db, job_arch):
        """
        Calculate a similarity matrix between employees and jobs.
        
        Args:
            employee_db: The employee database
            job_arch: The job architecture
            
        Returns:
            Pandas DataFrame with employee IDs as rows and job IDs as columns,
            containing similarity scores between each employee and job
        """
        import pandas as pd
        
        # Ensure employee database is set
        if not self.employee_database:
            self.employee_database = employee_db
            # Pre-compute vectors for all employees
            for employee_id, employee in employee_db.employees.items():
                self.employee_vectors[employee_id] = self.vectorizer.transform_employee(employee)
        
        # Calculate similarity matrix
        similarity_matrix, employee_ids, job_ids = self.calculate_similarity_matrix("emp_job")
        
        # Convert to pandas DataFrame for easier manipulation and output
        df = pd.DataFrame(similarity_matrix, index=employee_ids, columns=job_ids)
        
        return df 