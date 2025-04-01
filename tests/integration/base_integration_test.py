"""
Base class for integration tests.

This module provides a common base class for integration tests, ensuring that
all tests use the standardized test data from the tests/test_data directory.
"""

import os
import sys
import tempfile
import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import test data helpers
from tests.test_data import (
    load_skill_taxonomy, load_job_architecture, load_employee_database,
    ENGINE_JOBS_CSV, ENGINE_SKILLS_CSV, ENGINE_SKILLS_JSON
)

# Import core models
from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture
from skill_similarity_engine.models.employees import EmployeeDatabase
from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator


class BaseIntegrationTest(unittest.TestCase):
    """Base class for all integration tests.
    
    This class provides standard setup and teardown procedures
    for integration tests, ensuring consistent use of test data.
    """
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test outputs
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Load models from standardized test data
        self.skill_taxonomy = load_skill_taxonomy()
        self.job_architecture = load_job_architecture()
        
        try:
            # Only load employee database if tests need it
            self.employee_database = load_employee_database()
        except Exception as e:
            # Some tests might not need the employee database
            self.employee_database = None
            print(f"Note: Employee database not loaded: {e}")
        
        # Initialize the vectorizer and similarity calculator
        self.vectorizer = TfidfVectorizer(self.skill_taxonomy)
        self.similarity_calculator = CosineSimilarityCalculator(
            vectorizer=self.vectorizer,
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture
        )
        
    def tearDown(self):
        """Clean up after tests."""
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def get_test_department(self):
        """Get a valid department for testing.
        
        Returns:
            A valid department name from the test job architecture.
        """
        departments = set(job.department for job in self.job_architecture.jobs.values())
        if not departments:
            return "Engineering"  # Fallback default
        return next(iter(departments))
    
    # Tkinter check is no longer needed with matplotlib Agg backend
    # def check_tkinter_available(self):
    #     """Check if Tkinter is properly configured for visualization tests.
    #     
    #     Returns:
    #         Boolean indicating if Tkinter is available.
    #     """
    #     try:
    #         import tkinter
    #         import _tkinter
    #         # Try initializing Tkinter
    #         try:
    #             root = tkinter.Tk()
    #             root.destroy()
    #             return True
    #         except _tkinter.TclError:
    #             return False
    #     except ImportError:
    #         return False 