#!/usr/bin/env python3
"""
Functional test for the gap analysis functionality.

This test verifies that the gap analysis functionality works correctly with small test datasets.
It tests skill gap identification and development effort calculation.
"""

import sys
import os

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import tempfile
import unittest
from pathlib import Path

from skill_similarity_engine.models.skills import SkillTaxonomy, Skill, SkillCategory
from skill_similarity_engine.models.jobs import JobArchitecture, Job, JobLevel
from skill_similarity_engine.models.employees import EmployeeDatabase, Employee
from skill_similarity_engine.analysis.gap import SkillGapAnalyzer
# Import ConfigManager directly if needed for manually setting config values
from skill_similarity_engine.config.settings import ConfigManager


class TestGapAnalysis(unittest.TestCase):
    """Test the gap analysis functionality with sample data."""
    
    def setUp(self):
        """Set up test environment with small sample data."""
        # Set up config manager for gap analysis settings
        self.config_manager = ConfigManager()
        # Set custom gap analysis config values directly on the singleton
        self.config_manager.config.gap_analysis.min_proficiency_ratio = 0.7
        self.config_manager.config.gap_analysis.skill_difficulty_factor = 1.2
        self.config_manager.config.gap_analysis.min_gap_threshold = 0.25
        self.config_manager.config.gap_analysis.category_weights = {
            "Technical Skills": 1.2,
            "Soft Skills": 0.8
        }
        
        # Create a skill taxonomy with a few sample skills and categories
        self.taxonomy = SkillTaxonomy()
        
        # Add categories
        self.taxonomy.add_category(SkillCategory(
            category_id="C001", 
            name="Technical Skills"
        ))
        self.taxonomy.add_category(SkillCategory(
            category_id="C002", 
            name="Soft Skills"
        ))
        
        # Add skills with different difficulty levels
        self.taxonomy.add_skill(Skill(
            skill_id="S001", 
            name="Python Programming",
            category_id="C001",
        ))
        self.taxonomy.skills["S001"].difficulty = 3
        
        self.taxonomy.add_skill(Skill(
            skill_id="S002", 
            name="Data Analysis",
            category_id="C001",
        ))
        self.taxonomy.skills["S002"].difficulty = 4
        
        self.taxonomy.add_skill(Skill(
            skill_id="S003", 
            name="Machine Learning",
            category_id="C001",
        ))
        self.taxonomy.skills["S003"].difficulty = 5
        
        self.taxonomy.add_skill(Skill(
            skill_id="S004", 
            name="Project Management",
            category_id="C002",
        ))
        self.taxonomy.skills["S004"].difficulty = 3
        
        self.taxonomy.add_skill(Skill(
            skill_id="S005", 
            name="Communication",
            category_id="C002",
        ))
        self.taxonomy.skills["S005"].difficulty = 2
        
        # Create a job architecture with a few sample jobs
        self.job_architecture = JobArchitecture()
        
        # Data Scientist job
        data_scientist = Job(
            job_id="J001",
            title="Data Scientist",
            department="Data Science",
            level=JobLevel.SENIOR,
            skills={"S001": 4, "S002": 5, "S003": 4}
        )
        self.job_architecture.add_job(data_scientist)
        
        # Data Engineer job
        data_engineer = Job(
            job_id="J002",
            title="Data Engineer",
            department="Data Engineering",
            level=JobLevel.MID_LEVEL,
            skills={"S001": 5, "S002": 3}
        )
        self.job_architecture.add_job(data_engineer)
        
        # Project Manager job
        project_manager = Job(
            job_id="J003",
            title="Project Manager",
            department="Project Management",
            level=JobLevel.SENIOR,
            skills={"S004": 5, "S005": 4}
        )
        self.job_architecture.add_job(project_manager)
        
        # Create an employee database with a few sample employees
        self.employee_database = EmployeeDatabase()
        
        # Alice - Data Scientist with some skills but missing Machine Learning
        alice = Employee(
            employee_id="E001",
            name="Alice Smith",
            current_job="J001",
            skills={"S001": 4, "S002": 4}  # Missing S003
        )
        self.employee_database.add_employee(alice)
        
        # Bob - Data Engineer with some machine learning skills
        bob = Employee(
            employee_id="E002",
            name="Bob Johnson",
            current_job="J002",
            skills={"S001": 5, "S002": 3, "S003": 2}
        )
        self.employee_database.add_employee(bob)
        
        # Charlie - Project Manager with some technical skills too
        charlie = Employee(
            employee_id="E003",
            name="Charlie Brown",
            current_job="J003",
            skills={"S001": 2, "S004": 5, "S005": 4}
        )
        self.employee_database.add_employee(charlie)
        
        # Create the gap analyzer using the config set above
        self.gap_analyzer = SkillGapAnalyzer(
            skill_taxonomy=self.taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
    
    def tearDown(self):
        """Clean up after the test."""
        # Reset the ConfigManager singleton to avoid affecting other tests
        ConfigManager._instance = None
    
    def test_skill_gap_identification(self):
        """Test skill gap identification."""
        # Analyze gap for Alice (Data Scientist missing Machine Learning)
        alice_gap = self.gap_analyzer.analyze_employee_job_gap("E001", "J001")
        
        # Check if S003 (Machine Learning) is in missing skills
        missing_skill_ids = [gap.skill_id for gap in alice_gap.missing_skills]
        self.assertIn("S003", missing_skill_ids)
        
        # Find the specific gap for S003
        s003_gap = next((gap for gap in alice_gap.missing_skills if gap.skill_id == "S003"), None)
        self.assertIsNotNone(s003_gap)
        self.assertEqual(s003_gap.job_proficiency, 4)  # Required level is 4
        
        # Alice should not have excess skills
        self.assertEqual(len(alice_gap.excess_skills), 0)
        
        # Alice should have matching skills for Python and Data Analysis
        matching_skill_ids = [gap.skill_id for gap in alice_gap.matching_skills]
        self.assertEqual(len(matching_skill_ids), 2)
        self.assertIn("S001", matching_skill_ids)
        self.assertIn("S002", matching_skill_ids)
        
        # Calculate match percentage based on our custom min_proficiency_ratio (0.7)
        # 2 out of 3 skills = ~67%
        self.assertAlmostEqual(alice_gap.skill_match_percentage, 67, delta=1)
    
    def test_cross_job_gap_analysis(self):
        """Test gap analysis between different jobs."""
        # Analyze gap for Bob (Data Engineer) moving to Data Scientist
        bob_to_ds_gap = self.gap_analyzer.analyze_employee_job_gap("E002", "J001")
        
        # Bob may need improvement on Machine Learning (S003)
        improvement_needed_ids = [
            gap.skill_id for gap in bob_to_ds_gap.missing_skills 
            if gap.employee_proficiency > 0 and gap.employee_proficiency < gap.job_proficiency
        ]
        self.assertIn("S003", improvement_needed_ids)
        
        # Find the specific gap for S003
        s003_gap = next((gap for gap in bob_to_ds_gap.missing_skills if gap.skill_id == "S003"), None)
        self.assertIsNotNone(s003_gap)
        self.assertEqual(s003_gap.employee_proficiency, 2)
        self.assertEqual(s003_gap.job_proficiency, 4)
        
        # Calculate match percentage (based on actual implementation, expect at least 30%)
        self.assertGreater(bob_to_ds_gap.skill_match_percentage, 30)
        
        # Analyze gap for Charlie (Project Manager) moving to Data Scientist
        charlie_to_ds_gap = self.gap_analyzer.analyze_employee_job_gap("E003", "J001")
        
        # Check overall match percentage (should be relatively low)
        self.assertLess(charlie_to_ds_gap.skill_match_percentage, 50)
        
        # Charlie should have Python as matching or missing (but present)
        s001_gap = next((gap for gap in charlie_to_ds_gap.missing_skills 
                         if gap.skill_id == "S001" and gap.employee_proficiency > 0), None)
        if not s001_gap:
            s001_gap = next((gap for gap in charlie_to_ds_gap.matching_skills 
                            if gap.skill_id == "S001"), None)
        self.assertIsNotNone(s001_gap)
    
    def test_development_effort_calculation(self):
        """Test development effort calculation."""
        # Analyze gap for Alice (Data Scientist missing Machine Learning)
        alice_gap = self.gap_analyzer.analyze_employee_job_gap("E001", "J001")
        
        # Find the specific gap for S003 (Machine Learning)
        s003_gap = next((gap for gap in alice_gap.missing_skills if gap.skill_id == "S003"), None)
        self.assertIsNotNone(s003_gap)
        
        # Should have calculated development effort
        self.assertGreater(s003_gap.development_effort, 0)
        
        # The development effort should be higher than just the raw gap (4)
        # because of the high difficulty (5) and technical category weight (1.2)
        self.assertGreater(s003_gap.development_effort, 4)
        
        # Check total development effort
        self.assertGreater(alice_gap.total_development_effort, 0)
        
        # Check reskilling difficulty (should be between 1-5)
        self.assertGreaterEqual(alice_gap.reskilling_difficulty, 1)
        self.assertLessEqual(alice_gap.reskilling_difficulty, 5)


if __name__ == "__main__":
    unittest.main() 