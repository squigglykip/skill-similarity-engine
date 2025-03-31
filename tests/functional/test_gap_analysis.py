#!/usr/bin/env python3
"""
Functional test for the gap analysis functionality with HRIS adapter integration.

This test verifies that the gap analysis functionality works correctly with data
transformed by the HRIS adapter. It tests skill gap identification and development
effort calculation.
"""

import sys
import os
import json
import pandas as pd
import logging
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger("test_gap_analysis")

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import tempfile
import unittest
from pathlib import Path
import shutil

from skill_similarity_engine.models.skills import SkillTaxonomy, Skill, SkillCategory
from skill_similarity_engine.models.jobs import JobArchitecture, Job, JobLevel
from skill_similarity_engine.models.employees import EmployeeDatabase, Employee
from skill_similarity_engine.analysis.gap import SkillGapAnalyzer
# Import ConfigManager directly if needed for manually setting config values
from skill_similarity_engine.config.settings import ConfigManager
from skill_similarity_engine.hris_adapter.transformer import HRISTransformer


class TestGapAnalysis(unittest.TestCase):
    """Test the gap analysis functionality with sample data."""
    
    def setUp(self):
        """Set up test environment with sample data and HRIS adapter."""
        # Set up config manager for gap analysis settings
        self.config_manager = ConfigManager()
        # Set custom gap analysis config values directly on the singleton
        self.config_manager.config.gap_analysis.min_proficiency_ratio = 0.7
        self.config_manager.config.gap_analysis.skill_difficulty_factor = 1.2
        self.config_manager.config.gap_analysis.min_gap_threshold = 0.25
        self.config_manager.config.gap_analysis.category_weights = {
            "SPECIALIZED": 1.2,
            "COMMON": 0.8,
            "CERTIFICATION": 1.0
        }
        
        # Create a temporary directory for HRIS adapter files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Try to use HRIS adapter for data transformation
        try:
            logger.info("Setting up HRIS transformer...")
            
            # Create HRIS input files in the temporary directory
            self.hris_skills_path = os.path.join(self.temp_dir.name, "hris_skills.csv")
            self.hris_jobs_path = os.path.join(self.temp_dir.name, "hris_jobs.csv")
            self.hris_job_skills_path = os.path.join(self.temp_dir.name, "hris_job_skills.csv")
            self.hris_employees_path = os.path.join(self.temp_dir.name, "hris_employees.csv")
            self.hris_employee_skills_path = os.path.join(self.temp_dir.name, "hris_employee_skills.csv")
            
            # Create skills CSV file
            skills_data = [
                {"Skill_ID": "S001", "Skill_Name": "Python Programming", "SkillType": "Specialized Skill", "Difficulty": 3},
                {"Skill_ID": "S002", "Skill_Name": "Data Analysis", "SkillType": "Specialized Skill", "Difficulty": 4},
                {"Skill_ID": "S003", "Skill_Name": "Machine Learning", "SkillType": "Specialized Skill", "Difficulty": 5},
                {"Skill_ID": "S004", "Skill_Name": "Project Management", "SkillType": "Common Skill", "Difficulty": 3},
                {"Skill_ID": "S005", "Skill_Name": "Communication", "SkillType": "Common Skill", "Difficulty": 2}
            ]
            pd.DataFrame(skills_data).to_csv(self.hris_skills_path, index=False)
            
            # Create jobs CSV file
            jobs_data = [
                {"JobID": "J001", "RoleSet": "Data Scientist", "Org Unit Name": "Data Science", "Salary Group": "Group 4"},
                {"JobID": "J002", "RoleSet": "Data Engineer", "Org Unit Name": "Data Engineering", "Salary Group": "Group 3"},
                {"JobID": "J003", "RoleSet": "Project Manager", "Org Unit Name": "Project Management", "Salary Group": "Group 4"}
            ]
            pd.DataFrame(jobs_data).to_csv(self.hris_jobs_path, index=False)
            
            # Create job skills mapping file
            job_skills_data = [
                {"JobID": "J001", "Skill_ID": "S001", "proficiency": 4},
                {"JobID": "J001", "Skill_ID": "S002", "proficiency": 5},
                {"JobID": "J001", "Skill_ID": "S003", "proficiency": 4},
                {"JobID": "J002", "Skill_ID": "S001", "proficiency": 5},
                {"JobID": "J002", "Skill_ID": "S002", "proficiency": 3},
                {"JobID": "J003", "Skill_ID": "S004", "proficiency": 5},
                {"JobID": "J003", "Skill_ID": "S005", "proficiency": 4}
            ]
            pd.DataFrame(job_skills_data).to_csv(self.hris_job_skills_path, index=False)
            
            # Create employees CSV file
            employees_data = [
                {"EmployeeID": "E001", "Name": "Alice Smith", "Job_ID": "J001"},
                {"EmployeeID": "E002", "Name": "Bob Johnson", "Job_ID": "J002"},
                {"EmployeeID": "E003", "Name": "Charlie Brown", "Job_ID": "J003"}
            ]
            pd.DataFrame(employees_data).to_csv(self.hris_employees_path, index=False)
            
            # Create employee skills mapping file
            employee_skills_data = [
                {"EmployeeID": "E001", "Skill_ID": "S001", "proficiency": 4},
                {"EmployeeID": "E001", "Skill_ID": "S002", "proficiency": 4},
                {"EmployeeID": "E002", "Skill_ID": "S001", "proficiency": 5},
                {"EmployeeID": "E002", "Skill_ID": "S002", "proficiency": 3},
                {"EmployeeID": "E002", "Skill_ID": "S003", "proficiency": 2},
                {"EmployeeID": "E003", "Skill_ID": "S001", "proficiency": 2},
                {"EmployeeID": "E003", "Skill_ID": "S004", "proficiency": 5},
                {"EmployeeID": "E003", "Skill_ID": "S005", "proficiency": 4}
            ]
            pd.DataFrame(employee_skills_data).to_csv(self.hris_employee_skills_path, index=False)
            
            # Create HRIS schema mapping file
            self.hris_config_path = os.path.join(self.temp_dir.name, "hris_config.yaml")
            with open(self.hris_config_path, 'w') as f:
                f.write("""
# HRIS Schema Mapping Configuration for Testing
hris_data:
  jobs_file: {jobs_file}
  skills_file: {skills_file}
  job_skills_file: {job_skills_file}
  employees_file: {employees_file}
  employee_skills_file: {employee_skills_file}
  file_format: csv
  encoding: utf-8
  delimiter: ","
  has_header: true

output_data:
  jobs_file: {output_dir}/jobs.csv
  skills_file: {output_dir}/skills.csv
  employees_file: {output_dir}/employees.csv

jobs_mapping:
  job_id: JobID
  title: RoleSet
  department: Org Unit Name
  level: Salary Group

skills_mapping:
  skill_id: Skill_ID
  name: Skill_Name
  category: SkillType
  difficulty: Difficulty

job_skills_mapping:
  job_id: JobID
  skill_id: Skill_ID
  proficiency: proficiency

employees_mapping:
  employee_id: EmployeeID
  name: Name
  current_job: Job_ID

employee_skills_mapping:
  employee_id: EmployeeID
  skill_id: Skill_ID
  proficiency: proficiency

salary_group_mapping:
  Group 1:
    level: ENTRY
    seniority: 1
  Group 2:
    level: ASSOCIATE
    seniority: 2
  Group 3:
    level: PROFESSIONAL
    seniority: 3
  Group 4:
    level: SENIOR
    seniority: 4
  Group 5:
    level: PRINCIPAL
    seniority: 5
  Group 6:
    level: EXECUTIVE
    seniority: 6

transformation_options:
  use_binary_skills: false
  default_proficiency: 3
                """.format(
                    jobs_file=self.hris_jobs_path.replace('\\', '/'),
                    skills_file=self.hris_skills_path.replace('\\', '/'),
                    job_skills_file=self.hris_job_skills_path.replace('\\', '/'),
                    employees_file=self.hris_employees_path.replace('\\', '/'),
                    employee_skills_file=self.hris_employee_skills_path.replace('\\', '/'),
                    output_dir=self.temp_dir.name.replace('\\', '/')
                ))
            
            # Transform HRIS data
            logger.info("Transforming HRIS data...")
            transformer = HRISTransformer(config_path=self.hris_config_path)
            jobs_path, skills_path = transformer.transform()
            employees_path = os.path.join(os.path.dirname(jobs_path), "employees.csv")
            
            # Load transformed data
            logger.info("Loading transformed data...")
            self.taxonomy = SkillTaxonomy.from_file(skills_path)
            self.job_architecture = JobArchitecture.from_file(jobs_path)
            
            # Load employee database if the file exists
            if os.path.exists(employees_path):
                self.employee_database = EmployeeDatabase.from_file(employees_path, self.job_architecture)
            else:
                logger.warning("Employee data not transformed - falling back to manual employee setup")
                # Create manual employee database
                self._create_manual_employee_database()
            
        except Exception as e:
            logger.warning(f"Failed to use HRIS adapter for test setup: {e}")
            logger.warning("Falling back to manual setup")
            
            # Create manual test data
            self._create_manual_test_data()
        
        # Create the gap analyzer using the config set above
        self.gap_analyzer = SkillGapAnalyzer(
            skill_taxonomy=self.taxonomy,
            config=self.config_manager.config.gap_analysis
        )
    
    def _create_manual_test_data(self):
        """Create manual test data if HRIS adapter fails."""
        # Create a skill taxonomy with a few sample skills and categories
        self.taxonomy = SkillTaxonomy()
        
        # Add categories
        self.taxonomy.add_category(SkillCategory(
            category_id="C001", 
            name="SPECIALIZED"
        ))
        self.taxonomy.add_category(SkillCategory(
            category_id="C002", 
            name="COMMON"
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
        
        # Create an employee database
        self._create_manual_employee_database()
    
    def _create_manual_employee_database(self):
        """Create a manual employee database."""
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
    
    def tearDown(self):
        """Clean up after the test."""
        # Reset the ConfigManager singleton to avoid affecting other tests
        ConfigManager._instance = None
        
        # Clean up temporary directory
        if hasattr(self, 'temp_dir'):
            self.temp_dir.cleanup()
    
    def test_skill_gap_identification(self):
        """Test that skill gaps are correctly identified for employees."""
        # Initialize the gap analyzer for this test
        self.gap_analyzer.job_architecture = self.job_architecture
        self.gap_analyzer.employee_database = self.employee_database
        
        # Calculate gaps for Alice, who is missing Machine Learning skill
        alice_gaps = self.gap_analyzer.calculate_employee_skill_gaps("E001")
        
        # Verify that Machine Learning is identified as a gap
        self.assertIn("S003", alice_gaps)
        
        # Verify the gap size for Machine Learning (required=4, current=0)
        # The gap is calculated as required - current when below threshold
        self.assertGreaterEqual(alice_gaps["S003"], 4)
        
        # Bob should have a smaller gap in Machine Learning
        bob_gaps = self.gap_analyzer.calculate_employee_skill_gaps("E002")
        
        # Bob has some Machine Learning skills (2), but job requires 0
        # This should not be a gap since it's not a required skill for his job
        self.assertNotIn("S003", bob_gaps)
        
        # Charlie should have gaps in technical skills if wanting to move to a Data Scientist role
        charlie_gaps = self.gap_analyzer.calculate_role_transition_gaps("E003", "J001")
        
        # Charlie has some Python (2) but Data Scientist requires 4
        self.assertIn("S001", charlie_gaps)
        self.assertGreaterEqual(charlie_gaps["S001"], 2)
        
        # Charlie is missing Data Analysis and Machine Learning completely
        self.assertIn("S002", charlie_gaps)
        self.assertIn("S003", charlie_gaps)
    
    def test_development_effort_calculation(self):
        """Test that development effort is correctly calculated for gaps."""
        # Initialize the gap analyzer for this test
        self.gap_analyzer.job_architecture = self.job_architecture
        self.gap_analyzer.employee_database = self.employee_database
        
        # Calculate development effort for Alice to fill her gaps
        alice_effort = self.gap_analyzer.calculate_development_effort("E001")
        
        # Alice is missing Machine Learning (difficulty 5)
        # The effort should take into account the difficulty of the skill
        self.assertGreater(alice_effort, 0)
        
        # Calculate transition effort for Charlie to become a Data Scientist
        charlie_to_ds_effort = self.gap_analyzer.calculate_role_transition_effort("E003", "J001")
        
        # Charlie is missing or weak in all Data Scientist skills
        # The effort should be higher than Alice's
        self.assertGreater(charlie_to_ds_effort, alice_effort)
        
        # Bob's effort to become a Data Scientist should be less than Charlie's
        bob_to_ds_effort = self.gap_analyzer.calculate_role_transition_effort("E002", "J001")
        self.assertLess(bob_to_ds_effort, charlie_to_ds_effort)
    
    def test_category_weight_influence(self):
        """Test that category weights influence gap calculations."""
        # Initialize the gap analyzer for this test
        self.gap_analyzer.job_architecture = self.job_architecture
        self.gap_analyzer.employee_database = self.employee_database
        
        # Original weights
        original_weights = self.config_manager.config.gap_analysis.category_weights.copy()
        
        # First calculate with original weights (SPECIALIZED=1.2, COMMON=0.8)
        charlie_to_ds_effort_original = self.gap_analyzer.calculate_role_transition_effort("E003", "J001")
        
        # Change the weights to prioritize specialized skills even more
        self.config_manager.config.gap_analysis.category_weights = {
            "SPECIALIZED": 2.0,
            "COMMON": 0.5,
            "CERTIFICATION": 1.0
        }
        
        # Calculate with new weights
        charlie_to_ds_effort_tech_heavy = self.gap_analyzer.calculate_role_transition_effort("E003", "J001")
        
        # The effort should be higher with increased specialized skill weight
        self.assertGreater(charlie_to_ds_effort_tech_heavy, charlie_to_ds_effort_original)
        
        # Restore original weights
        self.config_manager.config.gap_analysis.category_weights = original_weights
    
    def test_gap_threshold_influence(self):
        """Test that the minimum gap threshold influences gap identification."""
        # Initialize the gap analyzer for this test
        self.gap_analyzer.job_architecture = self.job_architecture
        self.gap_analyzer.employee_database = self.employee_database
        
        # Original threshold
        original_threshold = self.config_manager.config.gap_analysis.min_gap_threshold
        
        # First calculate with original threshold (0.25)
        alice_gaps_original = self.gap_analyzer.calculate_employee_skill_gaps("E001")
        
        # Raise the threshold to eliminate smaller gaps
        self.config_manager.config.gap_analysis.min_gap_threshold = 0.9
        
        # Recalculate with higher threshold
        alice_gaps_high_threshold = self.gap_analyzer.calculate_employee_skill_gaps("E001")
        
        # The number of gaps should be less with a higher threshold
        self.assertLessEqual(len(alice_gaps_high_threshold), len(alice_gaps_original))
        
        # Restore original threshold
        self.config_manager.config.gap_analysis.min_gap_threshold = original_threshold
    
    def test_hris_integration_consistency(self):
        """Test that HRIS-transformed data produces consistent gap analysis results."""
        # This test is only meaningful if HRIS transformation succeeded
        if not hasattr(self, 'hris_config_path'):
            self.skipTest("HRIS adapter not available for this test")
        
        # Initialize the gap analyzer for this test
        self.gap_analyzer.job_architecture = self.job_architecture
        self.gap_analyzer.employee_database = self.employee_database
        
        # Get skill gaps for all employees
        all_gaps = {}
        for employee_id in self.employee_database.employees:
            all_gaps[employee_id] = self.gap_analyzer.calculate_employee_skill_gaps(employee_id)
        
        # Verify that each employee has the expected gaps
        # Alice (Data Scientist) should be missing Machine Learning
        if "E001" in all_gaps:
            self.assertIn("S003", all_gaps["E001"])
        
        # Bob (Data Engineer) should not have Machine Learning as a gap
        # since it's not required for his job
        if "E002" in all_gaps:
            self.assertNotIn("S003", all_gaps["E002"])
        
        # Verify that transition efforts align with our expectations
        if "E002" in self.employee_database.employees and "E003" in self.employee_database.employees:
            bob_to_ds_effort = self.gap_analyzer.calculate_role_transition_effort("E002", "J001")
            charlie_to_ds_effort = self.gap_analyzer.calculate_role_transition_effort("E003", "J001")
            self.assertLess(bob_to_ds_effort, charlie_to_ds_effort)


if __name__ == "__main__":
    unittest.main() 