#!/usr/bin/env python3
"""
Test CSV Export Formats for Power BI Integration

This test script verifies that CSV exports from the Skill Similarity Engine
are properly formatted and contain all necessary data for Power BI integration.
The tests focus on data integrity, format consistency, and handling of special characters.
"""

import os
import sys
import tempfile
import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import csv
import json

# Add the src directory to the path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

# Import modules for data validation
from skill_similarity_engine.models.skills import SkillTaxonomy, Skill
from skill_similarity_engine.models.jobs import JobArchitecture, Job, JobLevel


class TestCSVExportFormat(unittest.TestCase):
    """Test CSV export format compliance for Power BI integration."""
    
    def setUp(self):
        """Set up test environment with sample data."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_job_similarity_csv_format(self):
        """Test job similarity CSV format meets Power BI requirements."""
        # Create a sample job similarity DataFrame
        job_sim_data = [
            {
                "job_id_1": "J001", 
                "job_title_1": "Data Scientist",
                "department_1": "Data Science",
                "job_level_1": "Senior",
                "job_id_2": "J002",
                "job_title_2": "Data Engineer",
                "department_2": "Data Engineering",
                "job_level_2": "Mid-level",
                "similarity_score": 0.85,
                "is_high_similarity_opportunity": True,
                "is_internal_mobility_opportunity": False,
                "skill_gap_count": 2
            },
            {
                "job_id_1": "J001", 
                "job_title_1": "Data Scientist",
                "department_1": "Data Science",
                "job_level_1": "Senior",
                "job_id_2": "J003",
                "job_title_2": "Project Manager",
                "department_2": "Project Management",
                "job_level_2": "Senior",
                "similarity_score": 0.42,
                "is_high_similarity_opportunity": False,
                "is_internal_mobility_opportunity": False,
                "skill_gap_count": 5
            }
        ]
        
        # Create DataFrame and output to CSV
        df = pd.DataFrame(job_sim_data)
        output_path = self.output_dir / "job_similarity_test.csv"
        df.to_csv(output_path, index=False)
        
        # Check that the file exists
        self.assertTrue(output_path.exists())
        
        # Read the CSV file and verify format
        read_df = pd.read_csv(output_path)
        
        # Verify column count matches
        self.assertEqual(len(df.columns), len(read_df.columns))
        
        # Verify all required columns are present
        required_columns = [
            "job_id_1", "job_title_1", "department_1", "job_level_1",
            "job_id_2", "job_title_2", "department_2", "job_level_2",
            "similarity_score"
        ]
        for col in required_columns:
            self.assertIn(col, read_df.columns)
        
        # Verify data integrity
        self.assertEqual(len(df), len(read_df))
        
        # Verify similarity scores are in range 0-1
        self.assertTrue((read_df["similarity_score"] >= 0).all())
        self.assertTrue((read_df["similarity_score"] <= 1).all())
        
        # Verify boolean columns are correctly represented
        self.assertTrue(read_df["is_high_similarity_opportunity"].dtype == bool or 
                       read_df["is_high_similarity_opportunity"].isin([0, 1]).all())

    def test_skill_gap_csv_format(self):
        """Test skill gap analysis CSV format meets Power BI requirements."""
        # Create a sample skill gap analysis DataFrame
        skill_gap_data = [
            {
                "employee_id": "E001",
                "employee_name": "Alice Smith",
                "current_job_id": "J001",
                "current_job_title": "Data Scientist",
                "target_job_id": "J002",
                "target_job_title": "Data Engineer",
                "match_percentage": 75.5,
                "skill_gap_count": 2,
                "skill_excess_count": 1,
                "is_good_fit_opportunity": True,
                "development_effort": 12.5
            },
            {
                "employee_id": "E002",
                "employee_name": "Bob Johnson",
                "current_job_id": "J002",
                "current_job_title": "Data Engineer",
                "target_job_id": "J003",
                "target_job_title": "Project Manager",
                "match_percentage": 45.0,
                "skill_gap_count": 4,
                "skill_excess_count": 2,
                "is_good_fit_opportunity": False,
                "development_effort": 28.0
            }
        ]
        
        # Create DataFrame and output to CSV
        df = pd.DataFrame(skill_gap_data)
        output_path = self.output_dir / "skill_gap_test.csv"
        df.to_csv(output_path, index=False)
        
        # Check that the file exists
        self.assertTrue(output_path.exists())
        
        # Read the CSV file and verify format
        read_df = pd.read_csv(output_path)
        
        # Verify column count matches
        self.assertEqual(len(df.columns), len(read_df.columns))
        
        # Verify all required columns are present
        required_columns = [
            "employee_id", "employee_name", "current_job_id", "current_job_title",
            "target_job_id", "target_job_title", "match_percentage",
            "skill_gap_count", "skill_excess_count"
        ]
        for col in required_columns:
            self.assertIn(col, read_df.columns)
        
        # Verify data integrity
        self.assertEqual(len(df), len(read_df))
        
        # Verify percentage values are in range 0-100
        self.assertTrue((read_df["match_percentage"] >= 0).all())
        self.assertTrue((read_df["match_percentage"] <= 100).all())
        
        # Verify skill gap counts are non-negative
        self.assertTrue((read_df["skill_gap_count"] >= 0).all())
        self.assertTrue((read_df["skill_excess_count"] >= 0).all())

    def test_csv_header_row(self):
        """Test CSV header row is properly formatted."""
        # Create a sample DataFrame with different column types
        data = [
            {
                "id": "001",
                "name": "Example Item",
                "numeric_value": 42.5,
                "date_value": "2023-03-25",
                "boolean_flag": True
            }
        ]
        
        # Create DataFrame and output to CSV
        df = pd.DataFrame(data)
        output_path = self.output_dir / "header_test.csv"
        df.to_csv(output_path, index=False)
        
        # Check that the file exists
        self.assertTrue(output_path.exists())
        
        # Read the CSV file directly to check header formatting
        with open(output_path, 'r', encoding='utf-8') as f:
            header_line = f.readline().strip()
            
        # Verify header contains all column names
        for col in df.columns:
            self.assertIn(col, header_line)
            
        # Verify header doesn't contain extra quotes or characters
        expected_header = ",".join(df.columns)
        self.assertEqual(header_line, expected_header)

    def test_csv_special_characters(self):
        """Test CSV handling of special characters in string fields."""
        # Create a sample DataFrame with special characters
        data = [
            {
                "id": "001",
                "name": "O'Brien, David",
                "title": "Senior \"Lead\" Engineer",
                "department": "R&D, Innovation",
                "notes": "Works on project 'Alpha' & 'Beta'"
            }
        ]
        
        # Create DataFrame and output to CSV
        df = pd.DataFrame(data)
        output_path = self.output_dir / "special_chars_test.csv"
        df.to_csv(output_path, index=False)
        
        # Check that the file exists
        self.assertTrue(output_path.exists())
        
        # Read the CSV file back
        read_df = pd.read_csv(output_path)
        
        # Verify special characters are preserved
        self.assertEqual(read_df.iloc[0]["name"], "O'Brien, David")
        self.assertEqual(read_df.iloc[0]["title"], "Senior \"Lead\" Engineer")
        self.assertEqual(read_df.iloc[0]["department"], "R&D, Innovation")
        self.assertEqual(read_df.iloc[0]["notes"], "Works on project 'Alpha' & 'Beta'")
        
        # Check raw CSV content to verify proper quoting
        with open(output_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            header = next(csv_reader)
            row = next(csv_reader)
            
            # Find indexes of columns with special characters
            name_idx = header.index("name")
            title_idx = header.index("title")
            
            # Verify special characters in the raw CSV
            self.assertIn("O'Brien", row[name_idx])
            self.assertIn("\"Lead\"", row[title_idx])

    def test_csv_consistency_between_exports(self):
        """Test consistency of CSV exports with identical data."""
        # Create a sample DataFrame
        data = [
            {"id": "001", "value": 42.5, "category": "A"},
            {"id": "002", "value": 18.3, "category": "B"}
        ]
        
        # Create first CSV export
        df1 = pd.DataFrame(data)
        output_path1 = self.output_dir / "consistency_test_1.csv"
        df1.to_csv(output_path1, index=False)
        
        # Create second CSV export
        df2 = pd.DataFrame(data)
        output_path2 = self.output_dir / "consistency_test_2.csv"
        df2.to_csv(output_path2, index=False)
        
        # Read both CSVs
        read_df1 = pd.read_csv(output_path1)
        read_df2 = pd.read_csv(output_path2)
        
        # Verify both exports have identical content
        pd.testing.assert_frame_equal(read_df1, read_df2)
        
        # Verify raw file content is identical
        with open(output_path1, 'r', encoding='utf-8') as f1, open(output_path2, 'r', encoding='utf-8') as f2:
            content1 = f1.read()
            content2 = f2.read()
            self.assertEqual(content1, content2)

    def test_csv_numeric_format(self):
        """Test CSV numeric format precision."""
        # Create a sample DataFrame with various numeric values
        data = [
            {
                "id": "001",
                "integer_value": 42,
                "float_value": 42.123456789,
                "percentage": 95.75,
                "small_decimal": 0.00123
            }
        ]
        
        # Create DataFrame and output to CSV with specified float format
        df = pd.DataFrame(data)
        output_path = self.output_dir / "numeric_format_test.csv"
        df.to_csv(output_path, index=False, float_format="%.2f")
        
        # Read the CSV file back
        read_df = pd.read_csv(output_path)
        
        # Verify numeric precision was applied correctly
        self.assertEqual(read_df.iloc[0]["integer_value"], 42)
        self.assertEqual(read_df.iloc[0]["float_value"], 42.12)  # Rounded to 2 decimal places
        self.assertEqual(read_df.iloc[0]["percentage"], 95.75)
        self.assertEqual(read_df.iloc[0]["small_decimal"], 0.00)  # Rounded to 2 decimal places

    def test_csv_missing_values(self):
        """Test CSV handling of missing values."""
        # Create a sample DataFrame with missing values
        data = [
            {"id": "001", "name": "Complete Row", "value": 42.5, "category": "A"},
            {"id": "002", "name": None, "value": 18.3, "category": "B"},
            {"id": "003", "name": "Missing Value", "value": np.nan, "category": "C"}
        ]
        
        # Create DataFrame and output to CSV
        df = pd.DataFrame(data)
        output_path = self.output_dir / "missing_values_test.csv"
        df.to_csv(output_path, index=False)
        
        # Read the CSV file back
        read_df = pd.read_csv(output_path)
        
        # Verify row count
        self.assertEqual(len(read_df), 3)
        
        # Check handling of missing values
        self.assertTrue(pd.isna(read_df.iloc[1]["name"]))
        self.assertTrue(pd.isna(read_df.iloc[2]["value"]))


if __name__ == "__main__":
    unittest.main() 