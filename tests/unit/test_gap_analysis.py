#!/usr/bin/env python3
"""
Unit tests for the gap analysis functionality.

This module tests the SkillGapAnalyzer and related classes in the analysis.gap module.
"""

import os
import sys
import unittest
import pandas as pd
from unittest.mock import Mock, patch

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.analysis.gap import (
    SkillGapType,
    SkillGap,
    GapAnalysisResult,
    SkillGapAnalyzer,
    TeamGapAnalyzer
)
from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture, Job, JobLevel
from skill_similarity_engine.models.employees import EmployeeDatabase, Employee
from skill_similarity_engine.data.loaders import JobArchitectureLoader, EmployeeLoader


class TestSkillGapClasses(unittest.TestCase):
    """Test the SkillGap and GapAnalysisResult classes."""
    
    def test_skill_gap_creation(self):
        """Test creating a SkillGap instance."""
        gap = SkillGap(
            skill_id="S001",
            skill_name="Python",
            employee_proficiency=3,
            job_proficiency=4,
            gap_type=SkillGapType.MISSING,
            proficiency_gap=1,
            development_effort=10.0
        )
        
        self.assertEqual(gap.skill_id, "S001")
        self.assertEqual(gap.skill_name, "Python")
        self.assertEqual(gap.employee_proficiency, 3)
        self.assertEqual(gap.job_proficiency, 4)
        self.assertEqual(gap.gap_type, SkillGapType.MISSING)
        self.assertEqual(gap.proficiency_gap, 1)
        self.assertEqual(gap.development_effort, 10.0)
    
    def test_gap_analysis_result_creation(self):
        """Test creating a GapAnalysisResult instance."""
        result = GapAnalysisResult(
            employee_id="E001",
            employee_name="John Doe",
            job_id="J001",
            job_title="Data Analyst"
        )
        
        self.assertEqual(result.employee_id, "E001")
        self.assertEqual(result.employee_name, "John Doe")
        self.assertEqual(result.job_id, "J001")
        self.assertEqual(result.job_title, "Data Analyst")
        self.assertEqual(result.missing_skills, [])
        self.assertEqual(result.excess_skills, [])
        self.assertEqual(result.matching_skills, [])
        self.assertEqual(result.total_development_effort, 0.0)
        self.assertEqual(result.skill_match_percentage, 0.0)
        self.assertEqual(result.reskilling_difficulty, 0.0)
    
    def test_gap_analysis_result_to_dataframe(self):
        """Test converting GapAnalysisResult to DataFrame."""
        result = GapAnalysisResult(
            employee_id="E001",
            employee_name="John Doe",
            job_id="J001",
            job_title="Data Analyst"
        )
        
        # Add some skill gaps
        missing_gap = SkillGap(
            skill_id="S001",
            skill_name="Python",
            employee_proficiency=3,
            job_proficiency=4,
            gap_type=SkillGapType.MISSING,
            proficiency_gap=1,
            development_effort=10.0
        )
        
        excess_gap = SkillGap(
            skill_id="S002",
            skill_name="SQL",
            employee_proficiency=4,
            job_proficiency=0,
            gap_type=SkillGapType.EXCESS,
            proficiency_gap=0,
            development_effort=0.0
        )
        
        match_gap = SkillGap(
            skill_id="S003",
            skill_name="Excel",
            employee_proficiency=4,
            job_proficiency=3,
            gap_type=SkillGapType.MATCH,
            proficiency_gap=0,
            development_effort=0.0
        )
        
        result.missing_skills.append(missing_gap)
        result.excess_skills.append(excess_gap)
        result.matching_skills.append(match_gap)
        
        df = result.to_dataframe()
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)  # 3 skill gaps
        self.assertIn("skill_id", df.columns)
        self.assertIn("gap_type", df.columns)
        self.assertIn("proficiency_gap", df.columns)
        
        # Verify skill types in dataframe
        self.assertEqual(df[df["skill_id"] == "S001"]["gap_type"].iloc[0], "Missing")
        self.assertEqual(df[df["skill_id"] == "S002"]["gap_type"].iloc[0], "Excess")
        self.assertEqual(df[df["skill_id"] == "S003"]["gap_type"].iloc[0], "Match")
    
    def test_gap_analysis_result_to_summary_dict(self):
        """Test converting GapAnalysisResult to summary dict."""
        result = GapAnalysisResult(
            employee_id="E001",
            employee_name="John Doe",
            job_id="J001",
            job_title="Data Analyst"
        )
        
        # Add some skill gaps
        missing_gap = SkillGap(
            skill_id="S001",
            skill_name="Python",
            employee_proficiency=3,
            job_proficiency=4,
            gap_type=SkillGapType.MISSING,
            proficiency_gap=1,
            development_effort=10.0
        )
        
        result.missing_skills.append(missing_gap)
        result.total_development_effort = 10.0
        result.skill_match_percentage = 75.0
        result.reskilling_difficulty = 2.5
        
        summary = result.to_summary_dict()
        
        self.assertIsInstance(summary, dict)
        self.assertEqual(summary["employee_id"], "E001")
        self.assertEqual(summary["job_id"], "J001")
        self.assertEqual(summary["missing_skills_count"], 1)
        self.assertEqual(summary["total_development_effort"], 10.0)
        self.assertEqual(summary["skill_match_percentage"], 75.0)
        self.assertEqual(summary["reskilling_difficulty"], 2.5)


class TestSkillGapAnalyzer(unittest.TestCase):
    """Test the SkillGapAnalyzer with real sample data."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Load sample data from the existing data directory
        sample_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'sample')
        
        # Load real sample data
        self.skill_taxonomy = SkillTaxonomy.from_file(os.path.join(sample_dir, 'skills.csv'))
        
        # Load jobs from real sample data
        job_loader = JobArchitectureLoader(self.skill_taxonomy)
        self.job_architecture = job_loader.load_from_csv(os.path.join(sample_dir, 'jobs.csv'))
        
        # Load employees from real sample data
        employee_loader = EmployeeLoader(self.skill_taxonomy, self.job_architecture)
        self.employee_database = employee_loader.load_from_csv(os.path.join(sample_dir, 'employees.csv'))
        
        # Initialize the analyzer
        self.gap_analyzer = SkillGapAnalyzer(
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
    
    def test_analyzer_initialization(self):
        """Test that the analyzer is initialized correctly."""
        self.assertEqual(self.gap_analyzer.skill_taxonomy, self.skill_taxonomy)
        self.assertEqual(self.gap_analyzer.job_architecture, self.job_architecture)
        self.assertEqual(self.gap_analyzer.employee_database, self.employee_database)
        
        # Verify configuration defaults
        self.assertGreater(self.gap_analyzer.min_proficiency_ratio, 0)
        self.assertLess(self.gap_analyzer.min_proficiency_ratio, 1)
        self.assertIsInstance(self.gap_analyzer.category_weights, dict)
    
    def test_analyze_employee_job_gap(self):
        """Test analyzing gap between an employee and a job."""
        # Get first employee and job from real data
        employee_id = next(iter(self.employee_database.employees))
        job_id = next(iter(self.job_architecture.jobs))
        
        # Analyze gap
        result = self.gap_analyzer.analyze_employee_job_gap(
            employee_id=employee_id,
            job_id=job_id
        )
        
        # Verify result structure
        self.assertIsInstance(result, GapAnalysisResult)
        self.assertEqual(result.employee_id, employee_id)
        self.assertEqual(result.job_id, job_id)
        
        # Verify that all skill lists are populated
        self.assertIsInstance(result.missing_skills, list)
        self.assertIsInstance(result.excess_skills, list)
        self.assertIsInstance(result.matching_skills, list)
        
        # Verify calculated metrics
        self.assertGreaterEqual(result.total_development_effort, 0)
        self.assertGreaterEqual(result.skill_match_percentage, 0)
        self.assertLessEqual(result.skill_match_percentage, 100)
        self.assertGreaterEqual(result.reskilling_difficulty, 0)
    
    def test_generate_job_transition_report(self):
        """Test generating job transition report."""
        # Get first employee from real data
        employee_id = next(iter(self.employee_database.employees))
        
        # Generate transition report
        df = self.gap_analyzer.generate_job_transition_report(
            employee_id=employee_id,
            top_n=3
        )
        
        # Verify DataFrame structure
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertLessEqual(len(df), 3)  # top_n=3
        
        # Verify columns
        self.assertIn("job_id", df.columns)
        self.assertIn("job_title", df.columns)
        self.assertIn("skill_match_percentage", df.columns)
        self.assertIn("total_development_effort", df.columns)
        self.assertIn("reskilling_difficulty", df.columns)
        
        # Verify sorting (highest match percentage first)
        self.assertTrue(df["skill_match_percentage"].is_monotonic_decreasing)


class TestTeamGapAnalyzer(unittest.TestCase):
    """Test the TeamGapAnalyzer with real sample data."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Load sample data from the existing data directory
        sample_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'sample')
        
        # Load real sample data
        self.skill_taxonomy = SkillTaxonomy.from_file(os.path.join(sample_dir, 'skills.csv'))
        
        # Load jobs from real sample data
        job_loader = JobArchitectureLoader(self.skill_taxonomy)
        self.job_architecture = job_loader.load_from_csv(os.path.join(sample_dir, 'jobs.csv'))
        
        # Load employees from real sample data
        employee_loader = EmployeeLoader(self.skill_taxonomy, self.job_architecture)
        self.employee_database = employee_loader.load_from_csv(os.path.join(sample_dir, 'employees.csv'))
        
        # Initialize the analyzer
        self.team_analyzer = TeamGapAnalyzer(
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
    
    def test_team_analyzer_initialization(self):
        """Test that the team analyzer is initialized correctly."""
        self.assertEqual(self.team_analyzer.skill_taxonomy, self.skill_taxonomy)
        self.assertEqual(self.team_analyzer.job_architecture, self.job_architecture)
        self.assertEqual(self.team_analyzer.employee_database, self.employee_database)
    
    def test_analyze_team_skill_coverage(self):
        """Test analyzing skill coverage of a team."""
        # Get two employees from real data
        employee_ids = list(self.employee_database.employees.keys())[:2]
        
        # Get a job
        job_id = next(iter(self.job_architecture.jobs))
        
        # Analyze team skill coverage
        result = self.team_analyzer.analyze_team_skill_coverage(
            employee_ids=employee_ids,
            job_id=job_id
        )
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertIn("job_id", result)
        self.assertIn("job_title", result)
        self.assertIn("team_size", result)
        self.assertIn("fully_covered_skills", result)
        self.assertIn("partially_covered_skills", result)
        self.assertIn("uncovered_skills", result)
        self.assertIn("fully_covered_percentage", result)
        self.assertIn("overall_coverage_score", result)
        
        # Verify coverage metrics
        self.assertEqual(result["team_size"], 2)
        self.assertGreaterEqual(result["overall_coverage_score"], 0)
        self.assertLessEqual(result["overall_coverage_score"], 100)
        
        # Verify skills coverage
        fully_covered_skills = result["fully_covered_skills"]
        self.assertIsInstance(fully_covered_skills, list)
        
        # Check a skill in the coverage if available
        if fully_covered_skills:
            first_skill = fully_covered_skills[0]
            self.assertIn("skill_id", first_skill)
            self.assertIn("skill_name", first_skill)
            self.assertIn("required_proficiency", first_skill)
            self.assertIn("team_proficiency", first_skill)
            self.assertIn("gap", first_skill)
    
    def test_identify_critical_skill_gaps(self):
        """Test identifying critical skill gaps in a department."""
        # Get a department from real data
        departments = set(job.department for job in self.job_architecture.jobs.values())
        if departments:
            department = next(iter(departments))
            
            # Identify critical skill gaps
            df = self.team_analyzer.identify_critical_skill_gaps(
                department=department,
                min_gap_threshold=1.0  # Low threshold to ensure we get results
            )
            
            # Verify DataFrame structure
            self.assertIsInstance(df, pd.DataFrame)
            
            # Only check columns if the DataFrame is not empty
            if not df.empty:
                self.assertIn("skill_id", df.columns)
                self.assertIn("skill_name", df.columns)
                self.assertIn("avg_required_proficiency", df.columns)
                self.assertIn("avg_available_proficiency", df.columns)
                self.assertIn("proficiency_gap", df.columns)
                self.assertIn("criticality", df.columns)
                
                # Verify gaps are above threshold
                self.assertTrue((df["proficiency_gap"] >= 1.0).all())


if __name__ == "__main__":
    unittest.main() 