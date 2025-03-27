#!/usr/bin/env python3
"""
Functional test for the CLI report generation scripts.

This test verifies that the export functionality works correctly with small test datasets,
including job similarity exports, employee similarity exports, and skill gap analysis exports.
"""

import sys
import os
import tempfile
import unittest
import subprocess
import json
import pandas as pd
from pathlib import Path

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.models.skills import SkillTaxonomy, Skill
from skill_similarity_engine.models.jobs import JobArchitecture, Job, JobLevel
from skill_similarity_engine.models.employees import EmployeeDatabase, Employee
from skill_similarity_engine.visualization.reports import ReportGenerator


class TestCliReports(unittest.TestCase):
    """Test the CLI report generation functionality with sample data."""
    
    def setUp(self):
        """Set up test environment with small sample data files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name) / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Create a skill taxonomy CSV file
        self.skills_csv = Path(self.temp_dir.name) / "skills.csv"
        with open(self.skills_csv, "w") as f:
            f.write("skill_id,name,category,difficulty\n")
            f.write("S001,Python Programming,Technical,3\n")
            f.write("S002,Data Analysis,Technical,4\n")
            f.write("S003,Machine Learning,Technical,5\n")
            f.write("S004,Project Management,Soft Skills,3\n")
            f.write("S005,Communication,Soft Skills,2\n")
        
        # Create a job architecture CSV file
        self.jobs_csv = Path(self.temp_dir.name) / "jobs.csv"
        with open(self.jobs_csv, "w") as f:
            f.write("job_id,title,department,level,skills\n")
            f.write("J001,Data Scientist,Data Science,Senior,S001:4;S002:5;S003:4\n")
            f.write("J002,Data Engineer,Data Engineering,Mid-level,S001:5;S002:3\n")
            f.write("J003,Project Manager,Project Management,Senior,S004:5;S005:4\n")
        
        # Create an employee database CSV file
        self.employees_csv = Path(self.temp_dir.name) / "employees.csv"
        with open(self.employees_csv, "w") as f:
            f.write("employee_id,name,current_job,skills\n")
            f.write("E001,Alice Smith,J001,S001:4;S002:4\n")
            f.write("E002,Bob Johnson,J002,S001:5;S002:3;S003:2\n")
            f.write("E003,Charlie Brown,J003,S001:2;S004:5;S005:4\n")
        
        # Create a simple configuration file
        self.config_yaml = Path(self.temp_dir.name) / "config.yaml"
        with open(self.config_yaml, "w") as f:
            f.write("data_dir: {}\n".format(self.temp_dir.name))
            f.write("output_dir: {}\n".format(self.output_dir))
            f.write("opportunity_thresholds:\n")
            f.write("  high_similarity_threshold: 0.7\n")
            f.write("  low_gap_threshold: 20.0\n")
            f.write("  high_match_percentage: 80.0\n")
            f.write("  critical_gap_percentage: 50.0\n")
        
        # Load the models directly for some tests
        self.taxonomy = SkillTaxonomy.from_file(self.skills_csv)
        self.job_architecture = JobArchitecture.from_file(self.jobs_csv)
        self.employee_database = EmployeeDatabase.from_file(self.employees_csv, self.job_architecture)
        
        # Create a report generator
        self.report_generator = ReportGenerator(
            skill_taxonomy=self.taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database,
            output_dir=self.output_dir
        )
        
        # Path to the CLI script
        self.script_path = Path(__file__).parent.parent.parent / "scripts" / "generate_reports.py"
        
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
    
    def test_report_generator_direct(self):
        """Test report generation directly using the ReportGenerator."""
        # Generate job similarity export
        job_sim_csv = self.report_generator.export_job_similarity_matrix(
            output_format="csv",
            add_opportunity_flags=True
        )
        
        # Verify the file exists
        self.assertTrue(os.path.exists(job_sim_csv))
        
        # Load the CSV and check content
        df = pd.read_csv(job_sim_csv)
        self.assertGreater(len(df), 0)
        self.assertIn("job_id_1", df.columns)
        self.assertIn("job_id_2", df.columns)
        self.assertIn("similarity_score", df.columns)
        self.assertIn("is_high_similarity_opportunity", df.columns)
        
        # Generate employee similarity export
        emp_sim_csv = self.report_generator.export_employee_similarity_matrix(
            output_format="csv",
            add_opportunity_flags=True
        )
        
        # Verify the file exists
        self.assertTrue(os.path.exists(emp_sim_csv))
        
        # Load the CSV and check content
        df = pd.read_csv(emp_sim_csv)
        self.assertGreater(len(df), 0)
        self.assertIn("employee_id_1", df.columns)
        self.assertIn("employee_id_2", df.columns)
        self.assertIn("similarity_score", df.columns)
        self.assertIn("is_high_similarity_opportunity", df.columns)
        
        # Generate skill gap analysis export
        gap_csv = self.report_generator.export_skill_gap_analysis(
            output_format="csv",
            add_opportunity_flags=True
        )
        
        # Verify the file exists
        self.assertTrue(os.path.exists(gap_csv))
        
        # Load the CSV and check content
        df = pd.read_csv(gap_csv)
        self.assertGreater(len(df), 0)
        self.assertIn("employee_id", df.columns)
        self.assertIn("job_id", df.columns)
        self.assertIn("match_percentage", df.columns)
        self.assertIn("is_good_fit_opportunity", df.columns)
    
    def test_cli_script_exists(self):
        """Test that the CLI script exists."""
        self.assertTrue(os.path.exists(self.script_path))
    
    def run_cli_command(self, args):
        """Run a CLI command and return the result."""
        full_command = [sys.executable, str(self.script_path)] + args
        result = subprocess.run(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result


if __name__ == "__main__":
    unittest.main() 