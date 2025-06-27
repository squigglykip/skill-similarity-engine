"""
Unit tests for the HRIS adapter configuration module.

These tests verify that the HRISConfigLoader correctly loads and processes 
HRIS schema mapping configurations.
"""

import os
import sys
import pytest
import tempfile
import yaml
from unittest.mock import patch, mock_open

# Add the src directory to the Python path
# Go up 4 levels: test_config.py -> hris_adapter -> unit -> tests -> root
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.hris_adapter.config import HRISConfigLoader, HRISConfigError

class TestHRISConfigLoader:
    """Tests for the HRISConfigLoader class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_config = {
            "hris_data": {
                "jobs_file": "data/input/hris_jobs.csv",
                "skills_file": "data/input/hris_skills.csv",
                "job_skills_file": "data/input/hris_job_skills.csv",
                "file_format": "csv",
                "encoding": "utf-8",
                "delimiter": ",",
                "has_header": True
            },
            "output_data": {
                "jobs_file": "data/jobs.csv",
                "skills_file": "data/skills.csv"
            },
            "jobs_mapping": {
                "job_id": "JobID",
                "title": "RoleSet",
                "department": "Org Unit Name",
                "level": "Salary Group"
            },
            "skills_mapping": {
                "skill_id": "Skill_ID",
                "name": "Skill_Name"
            },
            "job_skills_mapping": {
                "job_id": "JobID",
                "skill_id": "Skill_ID"
            },
            "salary_group_mapping": {
                "Group 1": {"level": "ENTRY", "psa": "ENTRY"},
                "Group 2": {"level": "ASSOCIATE", "psa": "ENTRY"}
            }
        }
    
    def test_init_with_config_path(self):
        """Test initialization with a specific config path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(self.sample_config, temp_file)
            temp_file_path = temp_file.name
        
        try:
            loader = HRISConfigLoader(temp_file_path)
            assert loader.config_path == temp_file_path
            assert loader.config == self.sample_config
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
    
    @patch('os.path.exists')
    def test_get_default_config_path(self, mock_exists):
        """Test the _get_default_config_path method."""
        # Set up the mock to make the first path exist
        mock_exists.side_effect = lambda path: path.endswith('hris_schema_mapping.yaml')
        
        loader = HRISConfigLoader.__new__(HRISConfigLoader)
        path = loader._get_default_config_path()
        
        assert path.endswith('hris_schema_mapping.yaml')
        assert mock_exists.call_count > 0
    
    @patch('builtins.open', new_callable=mock_open, read_data='')
    @patch('yaml.safe_load')
    def test_load_config(self, mock_yaml_load, mock_file_open):
        """Test loading configuration from file."""
        mock_yaml_load.return_value = self.sample_config
        
        with patch.object(HRISConfigLoader, '_validate_config') as mock_validate:
            loader = HRISConfigLoader.__new__(HRISConfigLoader)
            loader.config_path = 'dummy_path.yaml'
            result = loader._load_config()
            
            mock_file_open.assert_called_once_with('dummy_path.yaml', 'r')
            mock_yaml_load.assert_called_once()
            mock_validate.assert_called_once_with(self.sample_config)
            assert result == self.sample_config
    
    def test_validate_config_valid(self):
        """Test validation with a valid config."""
        loader = HRISConfigLoader.__new__(HRISConfigLoader)
        # Should not raise an exception
        loader._validate_config(self.sample_config)
    
    def test_validate_config_missing_section(self):
        """Test validation with a missing required section."""
        loader = HRISConfigLoader.__new__(HRISConfigLoader)
        invalid_config = self.sample_config.copy()
        invalid_config.pop('jobs_mapping')
        
        with pytest.raises(HRISConfigError, match="Missing required configuration section: jobs_mapping"):
            loader._validate_config(invalid_config)
    
    def test_validate_config_missing_job_field(self):
        """Test validation with a missing required job field."""
        loader = HRISConfigLoader.__new__(HRISConfigLoader)
        invalid_config = self.sample_config.copy()
        invalid_config['jobs_mapping'] = {
            "job_id": "JobID",
            "title": "RoleSet",
            # Missing 'department'
            "level": "Salary Group"
        }
        
        with pytest.raises(HRISConfigError, match="Missing required job mapping field: department"):
            loader._validate_config(invalid_config)
    
    def test_validate_config_missing_skill_field(self):
        """Test validation with a missing required skill field."""
        loader = HRISConfigLoader.__new__(HRISConfigLoader)
        invalid_config = self.sample_config.copy()
        invalid_config['skills_mapping'] = {
            "skill_id": "Skill_ID",
            # Missing 'name'
        }
        
        with pytest.raises(HRISConfigError, match="Missing required skill mapping field: name"):
            loader._validate_config(invalid_config)
    
    def test_get_hris_data_paths(self):
        """Test getting HRIS data paths."""
        loader = HRISConfigLoader.__new__(HRISConfigLoader)
        loader.config = self.sample_config
        
        paths = loader.get_hris_data_paths()
        assert paths['jobs_file'] == "data/input/hris_jobs.csv"
        assert paths['skills_file'] == "data/input/hris_skills.csv"
        assert paths['job_skills_file'] == "data/input/hris_job_skills.csv"
    
    def test_get_output_data_paths(self):
        """Test getting output data paths."""
        loader = HRISConfigLoader.__new__(HRISConfigLoader)
        loader.config = self.sample_config
        
        paths = loader.get_output_data_paths()
        assert paths['jobs_file'] == "data/jobs.csv"
        assert paths['skills_file'] == "data/skills.csv"
    
    def test_get_jobs_mapping(self):
        """Test getting job field mappings."""
        loader = HRISConfigLoader.__new__(HRISConfigLoader)
        loader.config = self.sample_config
        
        mapping = loader.get_jobs_mapping()
        assert mapping['job_id'] == "JobID"
        assert mapping['title'] == "RoleSet"
        assert mapping['department'] == "Org Unit Name"
        assert mapping['level'] == "Salary Group"
    
    def test_get_skills_mapping(self):
        """Test getting skill field mappings."""
        loader = HRISConfigLoader.__new__(HRISConfigLoader)
        loader.config = self.sample_config
        
        mapping = loader.get_skills_mapping()
        assert mapping['skill_id'] == "Skill_ID"
        assert mapping['name'] == "Skill_Name"
    
    def test_get_value_mappings(self):
        """Test getting value mappings."""
        loader = HRISConfigLoader.__new__(HRISConfigLoader)
        loader.config = self.sample_config
        
        mappings = loader.get_value_mappings()
        assert mappings['salary_group']['Group 1']['level'] == "ENTRY"
        assert mappings['salary_group']['Group 2']['level'] == "ASSOCIATE"
    
    def test_get_file_format_options(self):
        """Test getting file format options."""
        loader = HRISConfigLoader.__new__(HRISConfigLoader)
        loader.config = self.sample_config
        
        options = loader.get_file_format_options()
        assert options['file_format'] == "csv"
        assert options['encoding'] == "utf-8"
        assert options['delimiter'] == ","
        assert options['has_header'] == True 
