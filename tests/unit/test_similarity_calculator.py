#!/usr/bin/env python3
"""
Unit tests for CosineSimilarityCalculator class.

These tests focus on testing the similarity calculator in isolation
with minimal dependencies on other components.
"""

import sys
import os
import numpy as np
import pandas as pd

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from skill_similarity_engine.similarity.cosine import CosineSimilarityCalculator
from skill_similarity_engine.similarity.cosine import TfidfVectorizer
from skill_similarity_engine.models.skills import Skill, SkillTaxonomy
from skill_similarity_engine.models.jobs import Job, JobArchitecture, JobLevel, RoleTrack
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity


class TestCosineSimilarityCalculator(unittest.TestCase):
    """Unit tests for CosineSimilarityCalculator class using mocks."""
    
    def setUp(self):
        """Set up test environment with mocks."""
        # Create mock skill taxonomy
        self.mock_skill_taxonomy = Mock()
        self.mock_skill_taxonomy.skills = {
            'S001': Mock(skill_id='S001', name='Python'),
            'S002': Mock(skill_id='S002', name='Data Analysis'),
            'S003': Mock(skill_id='S003', name='Machine Learning')
        }
        
        # Create mock job architecture
        self.mock_job_1 = Mock(job_id='J001', skills={'S001': 3, 'S002': 3})
        self.mock_job_2 = Mock(job_id='J002', skills={'S001': 2, 'S003': 4})
        self.mock_job_architecture = Mock()
        self.mock_job_architecture.jobs = {
            'J001': self.mock_job_1,
            'J002': self.mock_job_2
        }
        self.mock_job_architecture.get_job.side_effect = lambda job_id: self.mock_job_architecture.jobs.get(job_id)
        
        # Create a real vectorizer
        self.vectorizer = TfidfVectorizer(self.mock_skill_taxonomy)
        
        # Create the calculator
        self.calculator = CosineSimilarityCalculator(
            vectorizer=self.vectorizer,
            skill_taxonomy=self.mock_skill_taxonomy,
            job_architecture=self.mock_job_architecture
        )
    
    def test_calculator_initialization(self):
        """Test that the calculator is initialized correctly."""
        self.assertEqual(self.calculator.vectorizer, self.vectorizer)
        self.assertEqual(self.calculator.skill_taxonomy, self.mock_skill_taxonomy)
        self.assertEqual(self.calculator.job_architecture, self.mock_job_architecture)
    
    @patch('skill_similarity_engine.similarity.cosine.sklearn_cosine_similarity')
    def test_cosine_similarity_called(self, mock_cosine_similarity):
        """Test that sklearn's cosine_similarity is called correctly."""
        # Configure mock to return a known value
        # The correct format is a 2D array
        mock_cosine_similarity.return_value = np.array([[0.75]])
        
        # Mock the job vectors
        self.calculator.job_vectors = {
            'J001': np.array([0.5, 0.5, 0.0]),
            'J002': np.array([0.4, 0.0, 0.6])
        }
        
        # Configure job objects with required attributes
        self.mock_job_1.seniority = 3
        self.mock_job_2.seniority = 3
        self.mock_job_1.role_track = RoleTrack.INDIVIDUAL_CONTRIBUTOR
        self.mock_job_2.role_track = RoleTrack.INDIVIDUAL_CONTRIBUTOR
        self.mock_job_1.location = "New York"
        self.mock_job_2.location = "New York"
        
        # Call the function that should use our mocked sklearn_cosine_similarity
        result = self.calculator.calculate_job_similarity('J001', 'J002')
        
        # Verify cosine_similarity was called
        self.assertTrue(mock_cosine_similarity.called)
        
        # Just verify that the result is a float between 0 and 1
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)
    
    def test_calculate_job_similarity(self):
        """Test job similarity calculation by ID."""
        # We need to mock the job vectors, not the job objects
        # Use numpy arrays instead of lists to allow reshape
        self.calculator.job_vectors = {
            'J001': np.array([0.5, 0.5, 0.0]),
            'J002': np.array([0.4, 0.0, 0.6])
        }
        
        # Configure job objects with required attributes
        self.mock_job_1.seniority = 3
        self.mock_job_2.seniority = 4
        self.mock_job_1.role_track = RoleTrack.INDIVIDUAL_CONTRIBUTOR
        self.mock_job_2.role_track = RoleTrack.LEADERSHIP
        self.mock_job_1.location = "New York"
        self.mock_job_2.location = "Boston"
        
        # Mock the sklearn_cosine_similarity function to return a predictable value
        with patch('skill_similarity_engine.similarity.cosine.sklearn_cosine_similarity') as mock_cosine:
            # The correct format is a 2D array
            mock_cosine.return_value = np.array([[0.65]])
            
            # Calculate similarity
            result = self.calculator.calculate_job_similarity('J001', 'J002')
            
            # Just verify that the result is a float between 0 and 1
            # and that it's in a reasonable range considering the configuration
            self.assertIsInstance(result, float)
            self.assertGreaterEqual(result, 0.5)  # Lower bound
            self.assertLessEqual(result, 0.7)     # Upper bound
    
    def test_job_not_found(self):
        """Test handling of non-existent job IDs."""
        with self.assertRaises(ValueError):
            self.calculator.calculate_job_similarity('J001', 'NON_EXISTENT')
        
    def test_identical_jobs(self):
        """Test that identical jobs have similarity of 1.0."""
        # Configure job object with required attributes
        self.mock_job_1.seniority = 3
        self.mock_job_1.role_track = RoleTrack.INDIVIDUAL_CONTRIBUTOR
        self.mock_job_1.location = "New York"
        
        # Add the job to job_vectors
        self.calculator.job_vectors = {
            'J001': np.array([0.5, 0.5, 0.0]),
        }
        
        # Mock the sklearn_cosine_similarity function to return a predictable value
        with patch('skill_similarity_engine.similarity.cosine.sklearn_cosine_similarity') as mock_cosine:
            # The correct format is a 2D array
            mock_cosine.return_value = np.array([[1.0]])
            
            # Calculate similarity of job with itself
            result = self.calculator.calculate_job_similarity('J001', 'J001')
            
            # Verify the result using assertAlmostEqual instead of assertEqual for floating point comparison
            self.assertAlmostEqual(result, 1.0, places=10)


class TestCosineSimilarityCalculatorWithRealData(unittest.TestCase):
    """Unit tests for CosineSimilarityCalculator using standardized test data."""
    
    def setUp(self):
        """Set up test environment with standardized test data."""
        # Import test data helpers
        from tests.test_data import load_skill_taxonomy, load_job_architecture
        
        # Load models from test data
        self.taxonomy = load_skill_taxonomy()
        self.job_arch = load_job_architecture()
        
        # Initialize the vectorizer and similarity calculator
        self.vectorizer = TfidfVectorizer(self.taxonomy)
        self.calculator = CosineSimilarityCalculator(
            vectorizer=self.vectorizer,
            skill_taxonomy=self.taxonomy,
            job_architecture=self.job_arch
        )
        
        # Prepare job vectors
        self.calculator.prepare_job_vectors()
    
    def test_calculator_initialization_with_real_data(self):
        """Test that the calculator is initialized correctly with real data."""
        self.assertEqual(self.calculator.vectorizer, self.vectorizer)
        self.assertEqual(self.calculator.skill_taxonomy, self.taxonomy)
        self.assertEqual(self.calculator.job_architecture, self.job_arch)
        
        # Check that we have loaded some data
        self.assertGreater(len(self.taxonomy.skills), 0)
        self.assertGreater(len(self.job_arch.jobs), 0)
    
    def test_calculate_job_similarity_with_real_data(self):
        """Test job similarity calculation with real data."""
        # Get two jobs from our sample data
        job_ids = list(self.job_arch.jobs.keys())
        if len(job_ids) >= 2:
            job1_id, job2_id = job_ids[:2]
            
            # Calculate similarity
            similarity = self.calculator.calculate_job_similarity(job1_id, job2_id)
            
            # Verify the result is between 0 and 1
            self.assertGreaterEqual(similarity, 0.0)
            self.assertLessEqual(similarity, 1.0)
    
    def test_identical_jobs_with_real_data(self):
        """Test that identical jobs have similarity of 1.0 with real data."""
        # Get a job from our sample data
        job_ids = list(self.job_arch.jobs.keys())
        if job_ids:
            job_id = job_ids[0]
            
            # Calculate similarity of job with itself
            similarity = self.calculator.calculate_job_similarity(job_id, job_id)
            
            # Verify the result is 1.0
            self.assertAlmostEqual(similarity, 1.0, places=10)
    
    def test_job_not_found_with_real_data(self):
        """Test handling of non-existent job IDs with real data."""
        with self.assertRaises(ValueError):
            self.calculator.calculate_job_similarity('NON_EXISTENT', 'ALSO_NON_EXISTENT')
    
    def test_similarity_matrix_with_real_data(self):
        """Test generating similarity matrix with real data."""
        # Calculate similarity matrix
        matrix, job_ids = self.calculator.calculate_similarity_matrix("job")
        
        # Verify matrix properties
        self.assertIsInstance(matrix, np.ndarray)
        self.assertEqual(matrix.shape, (len(job_ids), len(job_ids)))
        self.assertTrue(np.allclose(matrix.diagonal(), 1.0))  # Diagonal should be 1.0
        self.assertTrue(np.all(matrix >= 0) and np.all(matrix <= 1))  # All values between 0 and 1


if __name__ == '__main__':
    unittest.main() 
