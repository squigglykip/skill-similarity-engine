"""
Tests for the enhanced similarity features that include seniority, role track, and location.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch
import numpy as np

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.models.jobs import Job, JobArchitecture, JobLevel, RoleTrack
from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.similarity.cosine import CosineSimilarityCalculator, TfidfVectorizer
from skill_similarity_engine.config.settings import ConfigManager, AppConfig, FutureExtensionConfig


class TestEnhancedSimilarity(unittest.TestCase):
    """Test cases for enhanced similarity calculations."""

    def setUp(self):
        """Set up test data and mock objects."""
        # Create a mock skill taxonomy
        self.skill_taxonomy = SkillTaxonomy()
        self.skill_taxonomy.add_skill("S001", "Programming", "Technical")
        self.skill_taxonomy.add_skill("S002", "Leadership", "Soft")
        self.skill_taxonomy.add_skill("S003", "Data Analysis", "Technical")
        
        # Create a job architecture with test jobs
        self.job_architecture = JobArchitecture()
        
        # Job 1: Junior Developer (IC, Seniority 1, London)
        job1 = Job(
            job_id="J001",
            title="Junior Developer",
            department="Engineering",
            level=JobLevel.ENTRY,
            skills={"S001": 3, "S003": 2},
            seniority=1,
            role_track=RoleTrack.INDIVIDUAL_CONTRIBUTOR,
            location="London"
        )
        
        # Job 2: Senior Developer (IC, Seniority 4, London)
        job2 = Job(
            job_id="J002",
            title="Senior Developer",
            department="Engineering",
            level=JobLevel.SENIOR,
            skills={"S001": 5, "S003": 4},
            seniority=4,
            role_track=RoleTrack.INDIVIDUAL_CONTRIBUTOR,
            location="London"
        )
        
        # Job 3: Engineering Manager (Leadership, Seniority 5, London)
        job3 = Job(
            job_id="J003",
            title="Engineering Manager",
            department="Engineering",
            level=JobLevel.MANAGER,
            skills={"S001": 4, "S002": 5, "S003": 3},
            seniority=5,
            role_track=RoleTrack.LEADERSHIP,
            location="London"
        )
        
        # Job 4: Senior Developer (IC, Seniority 4, Manchester)
        job4 = Job(
            job_id="J004",
            title="Senior Developer",
            department="Engineering",
            level=JobLevel.SENIOR,
            skills={"S001": 5, "S003": 4},
            seniority=4,
            role_track=RoleTrack.INDIVIDUAL_CONTRIBUTOR,
            location="Manchester"
        )
        
        # Add jobs to architecture
        self.job_architecture.add_job(job1)
        self.job_architecture.add_job(job2)
        self.job_architecture.add_job(job3)
        self.job_architecture.add_job(job4)
        
        # Create vectorizer
        self.vectorizer = TfidfVectorizer(self.skill_taxonomy)
        
        # Create config manager with mock config
        self.config_manager = ConfigManager()
        
        # Initialize calculator without enhancements enabled
        self.calculator = CosineSimilarityCalculator(
            vectorizer=self.vectorizer,
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            config_manager=self.config_manager
        )
    
    def test_basic_similarity(self):
        """Test similarity calculation without enhancements."""
        # Ensure weights are set to 0
        self.config_manager.config.future_extensions.seniority_weight = 0.0
        self.config_manager.config.future_extensions.role_track_weight = 0.0
        self.config_manager.config.future_extensions.location_weight = 0.0
        
        # Calculate similarity between Junior and Senior Developer
        similarity = self.calculator.calculate_job_similarity("J001", "J002")
        
        # Should be skills-based similarity only
        self.assertGreater(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
        
        # Junior Dev and Senior Dev should be similar based on skills
        similarity_j1_j2 = similarity
        
        # Senior Dev and Engineering Manager should be less similar based on skills
        similarity_j2_j3 = self.calculator.calculate_job_similarity("J002", "J003")
        
        # Expect the similarity to differ based on skills
        # Engineering Manager has leadership skill that developers don't
        self.assertNotEqual(similarity_j1_j2, similarity_j2_j3)
    
    def test_seniority_effect(self):
        """Test the effect of seniority on similarity."""
        # Enable only seniority with weight 1.0
        self.config_manager.config.future_extensions.seniority_weight = 1.0
        self.config_manager.config.future_extensions.role_track_weight = 0.0
        self.config_manager.config.future_extensions.location_weight = 0.0
        
        # Calculate similarity with seniority enabled
        similarity_with_seniority = self.calculator.calculate_job_similarity("J001", "J002")
        
        # Disable seniority
        self.config_manager.config.future_extensions.seniority_weight = 0.0
        
        # Calculate similarity without seniority
        similarity_without_seniority = self.calculator.calculate_job_similarity("J001", "J002")
        
        # Seniority should reduce similarity between Junior and Senior Developer
        self.assertLess(similarity_with_seniority, similarity_without_seniority)
        
        # Test similarity between two jobs with same seniority (J002 and J004)
        self.config_manager.config.future_extensions.seniority_weight = 1.0
        similarity_same_seniority = self.calculator.calculate_job_similarity("J002", "J004")
        
        # This similarity should be higher due to same seniority
        self.assertGreater(similarity_same_seniority, similarity_with_seniority)
    
    def test_role_track_effect(self):
        """Test the effect of role track on similarity."""
        # Enable only role track with weight 1.0
        self.config_manager.config.future_extensions.seniority_weight = 0.0
        self.config_manager.config.future_extensions.role_track_weight = 1.0
        self.config_manager.config.future_extensions.location_weight = 0.0
        
        # Calculate similarity between IC and Leadership roles
        similarity_diff_tracks = self.calculator.calculate_job_similarity("J002", "J003")
        
        # Calculate similarity between IC roles
        similarity_same_track = self.calculator.calculate_job_similarity("J001", "J002")
        
        # Same role track should have higher similarity
        self.assertGreater(similarity_same_track, similarity_diff_tracks)
        
        # Disable role track
        self.config_manager.config.future_extensions.role_track_weight = 0.0
        
        # Calculate similarity without role track between IC and Leadership
        similarity_without_track = self.calculator.calculate_job_similarity("J002", "J003")
        
        # Role track should have affected the similarity
        self.assertNotEqual(similarity_diff_tracks, similarity_without_track)
    
    def test_location_effect(self):
        """Test the effect of location on similarity."""
        # Enable only location with weight 1.0
        self.config_manager.config.future_extensions.seniority_weight = 0.0
        self.config_manager.config.future_extensions.role_track_weight = 0.0
        self.config_manager.config.future_extensions.location_weight = 1.0
        
        # Calculate similarity between jobs in same location
        similarity_same_location = self.calculator.calculate_job_similarity("J001", "J002")
        
        # Calculate similarity between jobs in different locations
        similarity_diff_location = self.calculator.calculate_job_similarity("J002", "J004")
        
        # Same location should have higher similarity
        self.assertGreater(similarity_same_location, similarity_diff_location)
        
        # Disable location
        self.config_manager.config.future_extensions.location_weight = 0.0
        
        # Calculate similarity without location between different locations
        similarity_without_location = self.calculator.calculate_job_similarity("J002", "J004")
        
        # Location should have affected the similarity
        self.assertNotEqual(similarity_diff_location, similarity_without_location)
    
    def test_combined_effects(self):
        """Test combined effects of all enhancements."""
        # Enable all enhancements with equal weights
        self.config_manager.config.future_extensions.seniority_weight = 0.5
        self.config_manager.config.future_extensions.role_track_weight = 0.5
        self.config_manager.config.future_extensions.location_weight = 0.5
        
        # Calculate similarity with all enhancements
        similarity_enhanced = self.calculator.calculate_job_similarity("J001", "J003")
        
        # Disable all enhancements
        self.config_manager.config.future_extensions.seniority_weight = 0.0
        self.config_manager.config.future_extensions.role_track_weight = 0.0
        self.config_manager.config.future_extensions.location_weight = 0.0
        
        # Calculate similarity without enhancements
        similarity_basic = self.calculator.calculate_job_similarity("J001", "J003")
        
        # The enhanced similarity should be different
        self.assertNotEqual(similarity_enhanced, similarity_basic)
        
        # The specific effect depends on the balance of factors,
        # but we can assert they're different
    
    def test_similarity_matrix(self):
        """Test that the similarity matrix calculation works with enhancements."""
        # Enable all enhancements
        self.config_manager.config.future_extensions.seniority_weight = 0.5
        self.config_manager.config.future_extensions.role_track_weight = 0.5
        self.config_manager.config.future_extensions.location_weight = 0.5
        
        # Calculate similarity matrix
        matrix, ids = self.calculator.calculate_similarity_matrix("job")
        
        # Check dimensions
        self.assertEqual(matrix.shape, (4, 4))
        self.assertEqual(len(ids), 4)
        
        # Diagonal should be 1.0 (self-similarity)
        for i in range(4):
            self.assertAlmostEqual(matrix[i, i], 1.0)
        
        # Matrix should be symmetric
        for i in range(4):
            for j in range(4):
                self.assertAlmostEqual(matrix[i, j], matrix[j, i])
        
        # Values should be in [0, 1] range
        self.assertTrue(np.all(matrix >= 0.0))
        self.assertTrue(np.all(matrix <= 1.0))


if __name__ == "__main__":
    unittest.main() 