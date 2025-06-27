"""
Unit tests for the HRIS adapter CLI module.

These tests verify that the command-line interface for the HRIS adapter
correctly parses arguments and calls the appropriate workflow functions.
"""

import os
import sys
import pytest
import tempfile
import yaml
import argparse
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
# Go up 4 levels: test_hris_adapter_cli.py -> hris_adapter -> unit -> tests -> root
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)


class TestHRISAdapterCLI:
    """Tests for the HRIS adapter CLI module."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary HRIS config file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_config_path = os.path.join(self.temp_dir.name, "test_hris_config.yaml")
        
        # Get absolute paths to POC data files
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        poc_dir = os.path.join(repo_root, "data", "poc")
        
        self.poc_jobs_file = os.path.join(poc_dir, "jobs_data_20250331_175651.csv")
        self.poc_skills_file = os.path.join(poc_dir, "skills_data_20250331_175651.csv")
        self.poc_job_skills_file = os.path.join(poc_dir, "job_skills_mapping_20250331_175651.csv")
        
        # Create config file that points to the POC data
        config = {
            "hris_data": {
                "jobs_file": self.poc_jobs_file,
                "skills_file": self.poc_skills_file,
                "job_skills_file": self.poc_job_skills_file,
                "file_format": "csv",
                "encoding": "utf-8",
                "delimiter": ","
            },
            "output_data": {
                "jobs_file": os.path.join(self.temp_dir.name, "transformed_jobs.csv"),
                "skills_file": os.path.join(self.temp_dir.name, "transformed_skills.csv")
            },
            "jobs_mapping": {
                "job_id": "JobID",
                "title": "RoleSet",
                "department": "Org Unit Name",
                "level": "Salary Group"
            },
            "skills_mapping": {
                "skill_id": "Skill_ID",
                "name": "Skill_Name",
                "category": "Category",
                "subcategory": "Subcategory"
            },
            "job_skills_mapping": {
                "job_id": "JobID",
                "skill_id": "Skill_ID"
            }
        }
        
        with open(self.temp_config_path, "w") as f:
            yaml.dump(config, f)
        
        # CLI arguments
        self.valid_args = [
            "--analysis-type", "job_similarity", 
            "--config", self.temp_config_path,
            "--output-dir", self.temp_dir.name,
            "--verbose"
        ]
    
    def teardown_method(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
    
    def test_parse_arguments(self):
        """Test argument parsing with valid arguments."""
        # Import here to ensure patching works
        from skill_similarity_engine.hris_adapter.cli import parse_arguments
        
        with patch('sys.argv', ['hris_analysis.py'] + self.valid_args):
            args = parse_arguments()
            
            assert args.analysis_type == "job_similarity"
            assert args.config == self.temp_config_path
            assert args.output_dir == self.temp_dir.name
            assert args.verbose is True
            assert args.employee_id is None  # Default value
            assert args.job_id is None  # Default value
    
    def test_parse_arguments_with_employee_job(self):
        """Test argument parsing with employee and job IDs."""
        # Import here to ensure patching works
        from skill_similarity_engine.hris_adapter.cli import parse_arguments
        
        test_args = self.valid_args + ["--employee-id", "E001", "--job-id", "J001"]
        with patch('sys.argv', ['hris_analysis.py'] + test_args):
            args = parse_arguments()
            
            assert args.employee_id == "E001"
            assert args.job_id == "J001"
    
    def test_parse_arguments_missing_required(self):
        """Test argument parsing with missing required argument."""
        # Import here to ensure patching works
        from skill_similarity_engine.hris_adapter.cli import parse_arguments
        
        with patch('sys.argv', ['hris_analysis.py', "--config", self.temp_config_path]):
            with pytest.raises(SystemExit):
                # This should exit because analysis-type is required
                parse_arguments()
    
    @patch('skill_similarity_engine.hris_adapter.workflow.HRISWorkflow.run_pipeline')
    def test_main_job_similarity(self, mock_run_pipeline):
        """Test main function with job similarity analysis type."""
        # Import here to ensure patching works
        from skill_similarity_engine.hris_adapter.cli import main
        
        # Configure the mock
        mock_run_pipeline.return_value = (
            [[1.0, 0.5], [0.5, 1.0]],  # similarity matrix
            ["J001", "J002"]  # job IDs
        )
        
        # Call main with job similarity arguments
        with patch('sys.argv', ['hris_analysis.py'] + self.valid_args):
            with patch('pandas.DataFrame.to_csv', MagicMock()):  # Prevent actual file write
                result = main()
                
                # Verify the workflow method was called with correct parameters
                mock_run_pipeline.assert_called_once_with("job_similarity")
                
                # Verify the result
                assert result == 0
    
    @patch('skill_similarity_engine.hris_adapter.workflow.HRISWorkflow.run_pipeline')
    def test_main_skill_gap_analysis(self, mock_run_pipeline):
        """Test main function with skill gap analysis type."""
        # Import here to ensure patching works
        from skill_similarity_engine.hris_adapter.cli import main
        import pandas as pd
        
        # Configure the mock with properly structured DataFrame
        data = [
            {"employee_id": "E001", "job_id": "J001", "skill_id": "S001", "skill_name": "Python", 
             "employee_proficiency": 3, "job_required": 4, "gap": 1},
            {"employee_id": "E001", "job_id": "J001", "skill_id": "S002", "skill_name": "SQL", 
             "employee_proficiency": 2, "job_required": 3, "gap": 1}
        ]
        mock_df = pd.DataFrame(data)
        mock_run_pipeline.return_value = mock_df
        
        # Call main with skill gap analysis arguments
        args = self.valid_args.copy()
        args[1] = "skill_gap_analysis"  # Change analysis type
        args.extend(["--employee-id", "E001", "--job-id", "J001"])
        
        with patch('sys.argv', ['hris_analysis.py'] + args):
            with patch('pandas.DataFrame.to_csv', MagicMock()):  # Prevent actual file write
                result = main()
                
                # Verify the correct workflow method was called with employee and job IDs
                mock_run_pipeline.assert_called_once_with(
                    "skill_gap_analysis",
                    employee_id="E001", 
                    job_id="J001"
                )
                
                # Verify the result
                assert result == 0
    
    @patch('skill_similarity_engine.hris_adapter.workflow.HRISWorkflow.run_pipeline')
    def test_main_employee_similarity(self, mock_run_pipeline):
        """Test main function with employee similarity analysis type."""
        # Import here to ensure patching works
        from skill_similarity_engine.hris_adapter.cli import main
        
        # Configure the mock
        mock_run_pipeline.return_value = (
            [[1.0, 0.7], [0.7, 1.0]],  # similarity matrix
            ["E001", "E002"]  # employee IDs
        )
        
        # Call main with employee similarity arguments
        args = self.valid_args.copy()
        args[1] = "employee_similarity"  # Change analysis type
        args.extend(["--employee-id", "E001"])
        
        with patch('sys.argv', ['hris_analysis.py'] + args):
            with patch('pandas.DataFrame.to_csv', MagicMock()):  # Prevent actual file write
                result = main()
                
                # Verify the correct workflow method was called with employee ID
                mock_run_pipeline.assert_called_once_with(
                    "employee_similarity",
                    employee_id="E001"
                )
                
                # Verify the result
                assert result == 0
    
    @patch('skill_similarity_engine.hris_adapter.workflow.HRISWorkflow.run_pipeline')
    def test_main_employee_job_similarity(self, mock_run_pipeline):
        """Test main function with employee-job similarity analysis type."""
        # Import here to ensure patching works
        from skill_similarity_engine.hris_adapter.cli import main
        
        # Configure the mock
        mock_run_pipeline.return_value = (
            [[0.8, 0.6]],  # similarity matrix
            ["E001"],  # employee IDs
            ["J001", "J002"]  # job IDs
        )
        
        # Call main with employee-job similarity arguments
        args = self.valid_args.copy()
        args[1] = "employee_job_similarity"  # Change analysis type
        args.extend(["--employee-id", "E001"])
        
        with patch('sys.argv', ['hris_analysis.py'] + args):
            with patch('pandas.DataFrame.to_csv', MagicMock()):  # Prevent actual file write
                result = main()
                
                # Verify the correct workflow method was called with employee ID
                # Match only the parameters that are actually passed
                mock_run_pipeline.assert_called_once_with(
                    "employee_job_similarity",
                    employee_id="E001"
                )
                
                # Verify the result
                assert result == 0
    
    @patch('skill_similarity_engine.hris_adapter.workflow.HRISWorkflow.run_pipeline')
    def test_main_error_handling(self, mock_run_pipeline):
        """Test main function error handling."""
        # Import here to ensure patching works
        from skill_similarity_engine.hris_adapter.cli import main
        
        # Configure the mock to raise an exception
        mock_run_pipeline.side_effect = Exception("Test error")
        
        # Call main with arguments that will cause the error
        with patch('sys.argv', ['hris_analysis.py'] + self.valid_args):
            with patch('sys.stderr') as mock_stderr:
                result = main()
                
                # Verify that error was printed to stderr
                assert mock_stderr.write.call_count > 0
                
                # Verify the error result
                assert result == 1  # Error exit code 
