"""
Unit tests for the field mapping functionality.

Tests the FieldMapper class and related functions to ensure proper
mapping between canonical and raw field names.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, mock_open

# Add src to path - simpler approach that worked in simple_test.py
current_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(os.path.dirname(current_dir))  # go up to tests/
project_root = os.path.dirname(tests_dir)  # go up to project root
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.config.field_mapping import (
    FieldMapper, 
    FieldMappingError,
    get_field_mapper,
    get_raw_field_name,
    map_row_fields
)

class TestFieldMapper(unittest.TestCase):
    """Test cases for the FieldMapper class."""
    
    def test_field_mapper_initialization_with_config_path(self):
        """Test FieldMapper initialization with provided config path."""
        # Create a temporary config file
        config_content = """
version: "1.0.0"
skills:
  skill_id: "Skill_ID"
  name: "Skill_Name"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            mapper = FieldMapper(config_path)
            self.assertEqual(mapper.config_path, config_path)
            self.assertEqual(mapper.config['version'], "1.0.0")
            self.assertEqual(mapper.config['skills']['skill_id'], "Skill_ID")
        finally:
            os.unlink(config_path)
    
    def test_field_mapper_invalid_config_path(self):
        """Test FieldMapper with invalid config path raises error."""
        with self.assertRaises(FieldMappingError):
            FieldMapper("/nonexistent/path/to/config.yaml")
    
    def test_field_mapper_invalid_yaml_content(self):
        """Test FieldMapper with invalid YAML content raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = f.name
        
        try:
            with self.assertRaises(FieldMappingError):
                FieldMapper(config_path)
        finally:
            os.unlink(config_path)
    
    def test_get_raw_field_name_simple_mapping(self):
        """Test getting raw field name for simple string mapping."""
        config_content = """
skills:
  skill_id: "Skill_ID"
  name: "Skill_Name"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            mapper = FieldMapper(config_path)
            
            # Test simple mappings
            self.assertEqual(mapper.get_raw_field_name('skill_id', 'skills'), "Skill_ID")
            self.assertEqual(mapper.get_raw_field_name('name', 'skills'), "Skill_Name")
        finally:
            os.unlink(config_path)
    
    def test_get_raw_field_name_list_mapping(self):
        """Test getting raw field name for list mapping (returns first option)."""
        config_content = """
skills:
  skill_type:
    - "SkillType"
    - "skill_type"
    - "category"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            mapper = FieldMapper(config_path)
            
            # Should return first option from list
            self.assertEqual(mapper.get_raw_field_name('skill_type', 'skills'), "SkillType")
        finally:
            os.unlink(config_path)
    
    def test_get_raw_field_name_fallback_sections(self):
        """Test fallback to other sections when field not found."""
        config_content = """
skills:
  skill_id: "Skill_ID"
jobs:
  job_id: "JobProfileID"
legacy:
  skills:
    name: "legacy_skill_name"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            mapper = FieldMapper(config_path)
            
            # Test fallback to other sections
            self.assertEqual(mapper.get_raw_field_name('job_id', 'skills', ['jobs']), "JobProfileID")
            
            # Test fallback to legacy section
            self.assertEqual(mapper.get_raw_field_name('name', 'skills'), "legacy_skill_name")
        finally:
            os.unlink(config_path)
    
    def test_get_raw_field_name_not_found(self):
        """Test behavior when field mapping is not found."""
        config_content = """
skills:
  skill_id: "Skill_ID"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            mapper = FieldMapper(config_path)
            
            # Should return canonical name when not found
            self.assertEqual(mapper.get_raw_field_name('unknown_field', 'skills'), "unknown_field")
        finally:
            os.unlink(config_path)
    
    def test_get_field_mapping_dict(self):
        """Test getting all field mappings for a section."""
        config_content = """
skills:
  skill_id: "Skill_ID"
  name: "Skill_Name"
  skill_type:
    - "SkillType"
    - "category"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            mapper = FieldMapper(config_path)
            
            mappings = mapper.get_field_mapping_dict('skills')
            
            self.assertEqual(mappings['skill_id'], "Skill_ID")
            self.assertEqual(mappings['name'], "Skill_Name")
            self.assertEqual(mappings['skill_type'], "SkillType")  # First from list
        finally:
            os.unlink(config_path)
    
    def test_map_row_fields_forward(self):
        """Test mapping row fields from canonical to raw names."""
        config_content = """
skills:
  skill_id: "Skill_ID"
  name: "Skill_Name"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            mapper = FieldMapper(config_path)
            
            input_row = {
                'skill_id': 'S001',
                'name': 'Python Programming',
                'unmapped_field': 'some_value'
            }
            
            mapped_row = mapper.map_row_fields(input_row, 'skills')
            
            self.assertEqual(mapped_row['Skill_ID'], 'S001')
            self.assertEqual(mapped_row['Skill_Name'], 'Python Programming')
            self.assertEqual(mapped_row['unmapped_field'], 'some_value')  # Unmapped fields pass through
        finally:
            os.unlink(config_path)
    
    def test_map_row_fields_reverse(self):
        """Test mapping row fields from raw to canonical names."""
        config_content = """
skills:
  skill_id: "Skill_ID"
  name: "Skill_Name"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            mapper = FieldMapper(config_path)
            
            input_row = {
                'Skill_ID': 'S001',
                'Skill_Name': 'Python Programming',
                'unmapped_field': 'some_value'
            }
            
            mapped_row = mapper.map_row_fields(input_row, 'skills', reverse=True)
            
            self.assertEqual(mapped_row['skill_id'], 'S001')
            self.assertEqual(mapped_row['name'], 'Python Programming')
            self.assertEqual(mapped_row['unmapped_field'], 'some_value')  # Unmapped fields pass through
        finally:
            os.unlink(config_path)
    
    def test_get_available_sections(self):
        """Test getting all available configuration sections."""
        config_content = """
version: "1.0.0"
skills:
  skill_id: "Skill_ID"
jobs:
  job_id: "JobProfileID"
field_name_alternatives:
  enable_fallback: true
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            mapper = FieldMapper(config_path)
            
            sections = mapper.get_available_sections()
            
            self.assertIn('skills', sections)
            self.assertIn('jobs', sections)
            self.assertNotIn('field_name_alternatives', sections)  # Excluded section
            self.assertNotIn('version', sections)  # Not a dict
        finally:
            os.unlink(config_path)


class TestFieldMappingIntegration(unittest.TestCase):
    """Integration tests for field mapping with real config structure."""
    
    def test_realistic_field_mapping_config(self):
        """Test with a realistic field mapping configuration."""
        config_content = """
version: "1.0.0"

skills:
  skill_id: "Skill_ID"
  name: "Skill_Name"
  skill_type: "SkillType"
  category: "Category"
  subcategory: "Subcategory"

jobs:
  job_id: "JobProfileID"
  title: "RoleSet"
  salary_group: "Salary Group"
  people_leader_flag: "People Leader Flag"
  location: "Location"

job_skills:
  job_id: "JobID"
  skill_id: "Skill_ID"
  proficiency: "proficiency"

field_name_alternatives:
  enable_fallback: true
  log_fallback_usage: true
  case_sensitive: false
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            mapper = FieldMapper(config_path)
            
            # Test skills mapping
            self.assertEqual(mapper.get_raw_field_name('skill_id', 'skills'), "Skill_ID")
            self.assertEqual(mapper.get_raw_field_name('name', 'skills'), "Skill_Name")
            self.assertEqual(mapper.get_raw_field_name('skill_type', 'skills'), "SkillType")
            
            # Test jobs mapping
            self.assertEqual(mapper.get_raw_field_name('job_id', 'jobs'), "JobProfileID")
            self.assertEqual(mapper.get_raw_field_name('title', 'jobs'), "RoleSet")
            self.assertEqual(mapper.get_raw_field_name('salary_group', 'jobs'), "Salary Group")
            
            # Test job_skills mapping
            self.assertEqual(mapper.get_raw_field_name('job_id', 'job_skills'), "JobID")
            self.assertEqual(mapper.get_raw_field_name('skill_id', 'job_skills'), "Skill_ID")
            self.assertEqual(mapper.get_raw_field_name('proficiency', 'job_skills'), "proficiency")
            
            # Test row mapping for skills
            skills_row = {
                'skill_id': 'S001',
                'name': 'Python Programming',
                'skill_type': 'SPECIALIZED'
            }
            
            mapped_skills_row = mapper.map_row_fields(skills_row, 'skills')
            expected_skills_row = {
                'Skill_ID': 'S001',
                'Skill_Name': 'Python Programming',
                'SkillType': 'SPECIALIZED'
            }
            self.assertEqual(mapped_skills_row, expected_skills_row)
            
            # Test reverse mapping
            reverse_mapped = mapper.map_row_fields(expected_skills_row, 'skills', reverse=True)
            self.assertEqual(reverse_mapped, skills_row)
            
        finally:
            os.unlink(config_path)
    
    def test_missing_section_handling(self):
        """Test behavior when requesting mapping for non-existent section."""
        config_content = """
skills:
  skill_id: "Skill_ID"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            mapper = FieldMapper(config_path)
            
            # Should return canonical name for non-existent section
            self.assertEqual(mapper.get_raw_field_name('field_name', 'nonexistent_section'), "field_name")
            
            # Should return empty dict for non-existent section
            self.assertEqual(mapper.get_field_mapping_dict('nonexistent_section'), {})
            
        finally:
            os.unlink(config_path)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""
    
    @patch('skill_similarity_engine.config.field_mapping.get_field_mapper')
    def test_get_raw_field_name_function(self, mock_get_mapper):
        """Test the get_raw_field_name convenience function."""
        mock_mapper = mock_get_mapper.return_value
        mock_mapper.get_raw_field_name.return_value = "Skill_ID"
        
        result = get_raw_field_name('skill_id', 'skills')
        
        self.assertEqual(result, "Skill_ID")
        mock_mapper.get_raw_field_name.assert_called_once_with('skill_id', 'skills', None)
    
    @patch('skill_similarity_engine.config.field_mapping.get_field_mapper')
    def test_map_row_fields_function(self, mock_get_mapper):
        """Test the map_row_fields convenience function."""
        mock_mapper = mock_get_mapper.return_value
        mock_mapper.map_row_fields.return_value = {'Skill_ID': 'S001'}
        
        input_row = {'skill_id': 'S001'}
        result = map_row_fields(input_row, 'skills')
        
        self.assertEqual(result, {'Skill_ID': 'S001'})
        mock_mapper.map_row_fields.assert_called_once_with(input_row, 'skills', False)


if __name__ == "__main__":
    unittest.main() 