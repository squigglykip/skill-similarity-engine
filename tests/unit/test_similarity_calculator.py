#!/usr/bin/env python3
"""
Unit tests for CosineSimilarityCalculator class.

These tests focus on testing the similarity calculator in isolation
with minimal dependencies on other components.
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add the src directory to the path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from skill_similarity_engine.similarity.cosine import CosineSimilarityCalculator
from skill_similarity_engine.similarity.cosine import TfidfVectorizer


class TestCosineSimilarityCalculator(unittest.TestCase):
    """Unit tests for CosineSimilarityCalculator class."""
    
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
    
    @patch('skill_similarity_engine.similarity.cosine.cosine_similarity')
    def test_cosine_similarity_called(self, mock_cosine_similarity):
        """Test that sklearn's cosine_similarity is called correctly."""
        # Configure mock to return a known value
        mock_cosine_similarity.return_value = [[0.75]]
        
        # Call the calculator
        result = self.calculator.calculate_similarity(
            {'S001': 3, 'S002': 3},
            {'S001': 2, 'S003': 4}
        )
        
        # Verify cosine_similarity was called
        self.assertTrue(mock_cosine_similarity.called)
        # Verify the return value is as expected
        self.assertEqual(result, 0.75)
    
    def test_calculate_job_similarity(self):
        """Test job similarity calculation by ID."""
        # Add vectorized skills mock
        self.mock_job_1.skill_vector = Mock()
        self.mock_job_2.skill_vector = Mock()
        self.mock_job_1.skill_vector.cosine_similarity.return_value = 0.65
        
        # Calculate similarity
        result = self.calculator.calculate_job_similarity('J001', 'J002')
        
        # Verify the job architecture was used to get jobs
        self.mock_job_architecture.get_job.assert_any_call('J001')
        self.mock_job_architecture.get_job.assert_any_call('J002')
        
        # Verify the result
        self.assertEqual(result, 0.65)
    
    def test_job_not_found(self):
        """Test handling of non-existent job IDs."""
        with self.assertRaises(ValueError):
            self.calculator.calculate_job_similarity('J001', 'NON_EXISTENT')
        
    def test_identical_jobs(self):
        """Test that identical jobs have similarity of 1.0."""
        # Add vectorized skills mock
        self.mock_job_1.skill_vector = Mock()
        self.mock_job_1.skill_vector.cosine_similarity.return_value = 1.0
        
        # Calculate similarity of job with itself
        result = self.calculator.calculate_job_similarity('J001', 'J001')
        
        # Verify the result
        self.assertEqual(result, 1.0)


if __name__ == '__main__':
    unittest.main() 