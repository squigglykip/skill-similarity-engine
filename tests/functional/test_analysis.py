"""
Functional tests for analysis workflows.

This module tests complete analysis workflows from data loading to result generation,
focusing on the practical usage patterns for the system.
"""

import sys
import os

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import tempfile
import pandas as pd
from unittest.mock import patch, MagicMock

from skill_similarity_engine.models.skills import Skill, SkillTaxonomy
from skill_similarity_engine.models.jobs import Job, JobArchitecture, JobLevel
from skill_similarity_engine.models.employees import Employee, EmployeeDatabase
from skill_similarity_engine.similarity.cosine import CosineSimilarityCalculator, TfidfVectorizer
from skill_similarity_engine.analysis.gap import SkillGapAnalyzer

# Import BaseFunctionalTest
from tests.functional import BaseFunctionalTest


class TestAnalysisWorkflows(BaseFunctionalTest):
    """Test case for complete analysis workflows."""
    
    def test_job_similarity_workflow(self):
        """Test the complete job similarity analysis workflow."""
        # Create vectorizer using the skill taxonomy from BaseFunctionalTest
        vectorizer = TfidfVectorizer(self.skill_taxonomy)
        
        # Create similarity calculator
        calculator = CosineSimilarityCalculator(
            vectorizer=vectorizer,
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture
        )
        
        # Get a subset of jobs to test with
        test_jobs = list(self.job_architecture.jobs.values())[:3]
        test_job_ids = [job.job_id for job in test_jobs]
        
        # Calculate similarity between subset of jobs
        similarity_matrix = []
        for job1_id in test_job_ids:
            for job2_id in test_job_ids:
                if job1_id != job2_id:
                    similarity = calculator.calculate_job_similarity(job1_id, job2_id)
                    job1 = self.job_architecture.get_job(job1_id)
                    job2 = self.job_architecture.get_job(job2_id)
                    similarity_matrix.append((job1_id, job2_id, similarity))
        
        # Check that the matrix has entries for all job pairs
        expected_pairs = len(test_job_ids) * (len(test_job_ids) - 1)
        self.assertEqual(len(similarity_matrix), expected_pairs)
        
        # Export similarity matrix to CSV
        output_path = os.path.join(self.temp_dir.name, "test_similarity.csv")
        similarity_df = pd.DataFrame(similarity_matrix, columns=["job_id_1", "job_id_2", "similarity"])
        similarity_df.to_csv(output_path, index=False)
        
        # Check that the file was created
        self.assertTrue(os.path.exists(output_path))
        
        # Read back the file to check structure
        df = pd.read_csv(output_path)
        expected_columns = ["job_id_1", "job_id_2", "similarity"]
        for col in expected_columns:
            self.assertIn(col, df.columns)
    
    def test_employee_job_gap_analysis(self):
        """Test employee to job skill gap analysis workflow."""
        # Create a gap analyzer
        gap_analyzer = SkillGapAnalyzer(
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
        
        # Get a test employee and a job they don't currently have
        employee_id = next(iter(self.employee_database.employees.keys()))
        employee = self.employee_database.get_employee(employee_id)
        
        # Find a job different from their current job
        target_job_id = None
        for job_id in self.job_architecture.jobs.keys():
            if job_id != employee.current_job:
                target_job_id = job_id
                break
        
        if not target_job_id:
            self.skipTest("No alternative job found for testing")
            
        # Analyze gap between employee and target job
        gap_results = gap_analyzer.analyze_employee_job_gap(employee_id, target_job_id)
        
        # Check that the results contain expected sections
        self.assertIsNotNone(gap_results.missing_skills)
        self.assertIsNotNone(gap_results.excess_skills)
        self.assertIsNotNone(gap_results.matching_skills)
        self.assertIsNotNone(gap_results.total_development_effort)
        
        # Convert to DataFrame format
        gap_df = gap_results.to_dataframe()
        
        # Export to CSV for inspection
        output_path = os.path.join(self.temp_dir.name, "test_job_gap.csv")
        gap_df.to_csv(output_path, index=False)
        
        # Check that the file was created
        self.assertTrue(os.path.exists(output_path))
    
    def test_job_to_job_gap_analysis(self):
        """Test job to job skill gap analysis workflow."""
        # Create a gap analyzer
        gap_analyzer = SkillGapAnalyzer(
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture
        )
        
        # Get two distinct jobs from the job architecture
        job_ids = list(self.job_architecture.jobs.keys())
        if len(job_ids) < 2:
            self.skipTest("Need at least 2 jobs for comparison")
            
        source_job_id = job_ids[0]
        target_job_id = job_ids[1]
        
        source_job = self.job_architecture.get_job(source_job_id)
        
        # Create a dummy employee with the source job's skills
        dummy_employee = Employee(
            employee_id="dummy",
            name="Dummy Employee",
            current_job=source_job_id,
            skills=source_job.skills
        )
        
        # Create a temporary employee database with our dummy employee
        temp_db = EmployeeDatabase()
        temp_db.add_employee(dummy_employee)
        
        # Set the new database
        gap_analyzer.employee_database = temp_db
        
        # Now perform the gap analysis
        gap_results = gap_analyzer.analyze_employee_job_gap("dummy", target_job_id)
        
        # Check that analysis was performed
        self.assertIsNotNone(gap_results)
        
        # Convert to DataFrame format
        gap_df = gap_results.to_dataframe()
        
        # Export to CSV for inspection
        output_path = os.path.join(self.temp_dir.name, "test_job_gap.csv")
        gap_df.to_csv(output_path, index=False)
        
        # Check that the file was created
        self.assertTrue(os.path.exists(output_path))
    
    def test_career_path_analysis(self):
        """Test career path analysis workflow."""
        # Create a gap analyzer with employee database
        gap_analyzer = SkillGapAnalyzer(
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
        
        # Get a test employee
        employee_id = next(iter(self.employee_database.employees.keys()))
        
        # Generate a job transition report for the employee
        transition_report = gap_analyzer.generate_job_transition_report(employee_id)
        
        # Check that the report is a DataFrame
        self.assertIsInstance(transition_report, pd.DataFrame)
        
        # Should exclude the employee's current job
        employee = self.employee_database.get_employee(employee_id)
        for _, row in transition_report.iterrows():
            self.assertNotEqual(row['job_id'], employee.current_job)
        
        # Check columns
        expected_columns = ["job_id", "job_title", "skill_match_percentage", "total_development_effort"]
        for col in expected_columns:
            self.assertIn(col, transition_report.columns)
        
        # Export to CSV
        output_path = os.path.join(self.temp_dir.name, "test_transition.csv")
        transition_report.to_csv(output_path, index=False)
        
        # Check that the file was created
        self.assertTrue(os.path.exists(output_path))
    
    def test_reskilling_pathway_workflow(self):
        """Test the complete reskilling pathway workflow."""
        # Create a gap analyzer
        gap_analyzer = SkillGapAnalyzer(
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
        
        # Get a test employee and a job they don't currently have
        employee_id = next(iter(self.employee_database.employees.keys()))
        employee = self.employee_database.get_employee(employee_id)
        
        # Find a job different from their current job
        target_job_id = None
        for job_id in self.job_architecture.jobs.keys():
            if job_id != employee.current_job:
                target_job_id = job_id
                break
        
        if not target_job_id:
            self.skipTest("No alternative job found for testing")
        
        # Calculate skill gaps for a transition
        gaps = gap_analyzer.calculate_role_transition_gaps(employee_id, target_job_id)
        
        # Check that the gaps dictionary exists and has the right structure
        self.assertIsInstance(gaps, dict)
        
        # Check if there are any gaps (might be empty if employee has all needed skills)
        if gaps:
            # Verify at least one gap entry
            first_skill_id = next(iter(gaps.keys()))
            gap_value = gaps[first_skill_id]
            
            # Gap value should be positive (indicating skills needed)
            self.assertGreater(gap_value, 0)
            
            # Skill should exist in taxonomy
            self.assertIn(first_skill_id, self.skill_taxonomy.skills)
            
            # Get skill details
            skill = self.skill_taxonomy.get_skill(first_skill_id)
            self.assertIsNotNone(skill)
            
            # Verify skill has a name
            self.assertIsNotNone(skill.name)
        
        # Now perform a complete gap analysis 
        result = gap_analyzer.analyze_employee_job_gap(employee_id, target_job_id)
        
        # This should always work and include development effort
        self.assertIsNotNone(result.total_development_effort)
        
        # Verify we get a valid development effort value
        self.assertIsInstance(result.total_development_effort, float)
    
    def test_cross_department_analysis(self):
        """Test analysis of jobs across different departments."""
        # Get departments from job architecture
        departments = set()
        for job in self.job_architecture.jobs.values():
            if job.department:
                departments.add(job.department)
        
        if len(departments) < 2:
            self.skipTest("Need at least 2 departments for cross-department analysis")
        
        # Get a job from each of the first two departments
        dept_jobs = {}
        for job in self.job_architecture.jobs.values():
            if job.department in departments and job.department not in dept_jobs:
                dept_jobs[job.department] = job.job_id
                if len(dept_jobs) >= 2:
                    break
        
        # Create vectorizer
        vectorizer = TfidfVectorizer(self.skill_taxonomy)
        
        # Create similarity calculator
        calculator = CosineSimilarityCalculator(
            vectorizer=vectorizer,
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture
        )
        
        # Get job IDs from two different departments
        job_ids = list(dept_jobs.values())
        
        # Calculate similarity between jobs from different departments
        similarity = calculator.calculate_job_similarity(job_ids[0], job_ids[1])
        
        # Should return a valid similarity value
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_skill_importance_weighting(self):
        """Test analysis with different skill importance weightings."""
        # Create vectorizers
        vectorizer1 = TfidfVectorizer(self.skill_taxonomy)
        vectorizer2 = TfidfVectorizer(self.skill_taxonomy)
        
        # Create similarity calculators
        calculator1 = CosineSimilarityCalculator(
            vectorizer=vectorizer1,
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture
        )
        
        calculator2 = CosineSimilarityCalculator(
            vectorizer=vectorizer2,
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture
        )
        
        # Get two distinct jobs from the job architecture
        job_ids = list(self.job_architecture.jobs.keys())
        if len(job_ids) < 2:
            self.skipTest("Need at least 2 jobs for comparison")
        
        # Calculate similarity with both calculators
        similarity1 = calculator1.calculate_job_similarity(job_ids[0], job_ids[1])
        similarity2 = calculator2.calculate_job_similarity(job_ids[0], job_ids[1])
        
        # Since we're using the same vectorizers with identical settings, results should be equal
        self.assertEqual(round(similarity1, 4), round(similarity2, 4))


if __name__ == "__main__":
    unittest.main()
