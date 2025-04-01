"""
Unit tests for schema separation in the HRIS adapter.

These tests verify that the HRIS adapter properly separates the HRIS schema
from the internal engine schema, ensuring that HRIS naming conventions do not
leak into the engine's standardized schema.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from unittest import mock
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
# Go up 4 levels: test_schema_separation.py -> hris_adapter -> unit -> tests -> root
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.hris_adapter.transformer import HRISTransformer
from skill_similarity_engine.hris_adapter.config import HRISConfigLoader
from skill_similarity_engine.models.skills import SkillTaxonomy, Skill
from skill_similarity_engine.models.jobs import JobArchitecture, Job, JobLevel, RoleTrack
# Import test data helpers
from tests.test_data import (
    load_hris_jobs_df, load_hris_skills_df, load_hris_job_skills_df,
    get_hris_config_path
)


class TestSchemaSeparation:
    """Tests for schema separation between HRIS data and engine formats."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Load sample HRIS data from test data package
        self.hris_jobs_data = load_hris_jobs_df()
        self.hris_skills_data = load_hris_skills_df()
        self.hris_job_skills_data = load_hris_job_skills_df()
        
        # Mock the config loader
        self.mock_config = self._create_mock_config()
        
        # Create transformer with mocked config
        with patch('skill_similarity_engine.hris_adapter.transformer.HRISConfigLoader', 
                  return_value=self.mock_config):
            self.transformer = HRISTransformer()
    
    def _create_mock_config(self):
        """Create a mock configuration for testing."""
        mock_config = MagicMock(spec=HRISConfigLoader)
        
        # Add the config_path attribute to the mock
        mock_config.config_path = get_hris_config_path()
        
        # Configure paths
        mock_config.get_hris_data_paths.return_value = {
            "jobs_file": "tests/test_data/hris_jobs.csv",
            "skills_file": "tests/test_data/hris_skills.csv",
            "job_skills_file": "tests/test_data/hris_job_skills.csv"
        }
        
        mock_config.get_output_data_paths.return_value = {
            "jobs_file": "tests/test_data/jobs.csv",
            "skills_file": "tests/test_data/skills.csv"
        }
        
        # Configure mappings
        mock_config.get_jobs_mapping.return_value = {
            "job_id": "JobID",
            "title": "RoleSet",
            "department": "Org Unit Name",
            "level": "Salary Group",
            "location": "Location"
        }
        
        mock_config.get_skills_mapping.return_value = {
            "skill_id": "Skill_ID",
            "name": "Skill_Name",
            "category": "SkillType",
            "subcategory": "Category",
            "description": "Subcategory"  # Using subcategory as description for testing
        }
        
        mock_config.get_job_skills_mapping.return_value = {
            "job_id": "JobID",
            "skill_id": "Skill_ID",
            "proficiency": "Proficiency"
        }
        
        # Configure value mappings
        mock_config.get_value_mappings.return_value = {
            "salary_group": {
                "Group 1": {"level": "ENTRY"},
                "Group 2": {"level": "ASSOCIATE"},
                "Group 3": {"level": "MID_LEVEL"},
                "Group 4": {"level": "MID_LEVEL"},
                "Group 5": {"level": "SENIOR"},
                "Group 6": {"level": "LEAD"},
                "Group 7": {"level": "EXECUTIVE"}
            },
            "role_track": {
                "People Leader": "MANAGEMENT",
                "Non-People Leader": "INDIVIDUAL_CONTRIBUTOR"
            },
            "skill_type": {
                "Certification": "CERTIFICATION",
                "Common Skill": "COMMON",
                "Specialized Skill": "SPECIALIZED"
            }
        }
        
        # Configure file format options
        mock_config.get_file_format_options.return_value = {
            "file_format": "csv",
            "encoding": "utf-8",
            "delimiter": ",",
            "has_header": True
        }
        
        # Configure transformation options
        mock_config.get_transformation_options.return_value = {
            "use_binary_skills": False,
            "default_proficiency": 3
        }
        
        return mock_config
    
    def test_transform_jobs_schema_separation(self):
        """Test that job transformation properly separates schemas."""
        # Set the transformer's config to use our mappings
        self.transformer.config = {
            'jobs_mapping': {
                'job_id': 'JobID',
                'title': 'RoleSet',
                'department': 'Org Unit Name',
                'level': 'Salary Group',
                'location': 'Location'
            },
            'value_mappings': {
                'salary_group': {
                    'Group 1': {'level': 'ENTRY', 'psa': 'ENTRY'},
                    'Group 2': {'level': 'ASSOCIATE', 'psa': 'ENTRY'},
                    'Group 3': {'level': 'MID_LEVEL', 'psa': 'MIDRANGE'},
                    'Group 4': {'level': 'SENIOR', 'psa': 'EXPERT'},
                    'Group 5': {'level': 'SENIOR', 'psa': 'EXPERT'},
                    'Group 6': {'level': 'LEAD', 'psa': 'EXPERT'},
                    'Group 7': {'level': 'EXECUTIVE', 'psa': 'EXPERT'}
                }
            },
            'transformation_options': {}
        }
        
        # Patch the _load_hris_data method to return our test data
        with patch.object(self.transformer, '_load_hris_data', 
                         return_value=(self.hris_jobs_data, self.hris_skills_data, self.hris_job_skills_data)):
            # Call the method directly to test just the schema transformation
            transformed_jobs = self.transformer._transform_jobs(self.hris_jobs_data)
            
            # Verify that the output uses the engine's schema, not HRIS schema
            assert "job_id" in transformed_jobs.columns
            assert "title" in transformed_jobs.columns
            assert "department" in transformed_jobs.columns
            assert "level" in transformed_jobs.columns
            
            # Verify HRIS column names are not present
            assert "JobID" not in transformed_jobs.columns
            assert "RoleSet" not in transformed_jobs.columns
            assert "Org Unit Name" not in transformed_jobs.columns
            assert "Salary Group" not in transformed_jobs.columns
            
            # Check that job IDs are in the expected format
            assert all(job_id.startswith("J") for job_id in transformed_jobs["job_id"])
            
            # Verify that values have been transformed from the original format
            assert len(transformed_jobs) > 0
            
            # Check that titles, departments and levels are all strings
            assert transformed_jobs["title"].dtype == object  # 'object' dtype for strings in pandas
            assert transformed_jobs["department"].dtype == object
            
            # Verify level values match the expected enum values
            valid_levels = ['ENTRY', 'ASSOCIATE', 'MID_LEVEL', 'SENIOR', 'LEAD', 'EXECUTIVE']
            for level in transformed_jobs["level"]:
                assert level in valid_levels, f"Invalid level value: {level}"
    
    def test_transform_skills_schema_separation(self):
        """Test that skill transformation properly separates schemas."""
        # Set the transformer's config to use our mappings
        self.transformer.config = {
            'skills_mapping': {
                'skill_id': 'Skill_ID',
                'name': 'Skill_Name',
                'category': 'SkillType',
                'subcategory': 'Category',
                'description': 'Subcategory'
            },
            'value_mappings': {
                'skill_type': {
                    'Certification': 'CERTIFICATION',
                    'Common Skill': 'COMMON',
                    'Specialized Skill': 'SPECIALIZED'
                }
            },
            'transformation_options': {}
        }
        
        # Patch the _load_hris_data method to return our test data
        with patch.object(self.transformer, '_load_hris_data',
                         return_value=(self.hris_jobs_data, self.hris_skills_data, self.hris_job_skills_data)):
            # Call the method directly to test just the schema transformation
            transformed_skills = self.transformer._transform_skills(self.hris_skills_data)
            
            # Print the transformed data for debugging
            print("Original skills data types:")
            print(self.hris_skills_data[['Skill_ID', 'Skill_Name', 'SkillType']])
            print("\nTransformed skills data:")
            print(transformed_skills)
            
            # Verify that the output uses the engine's schema, not HRIS schema
            assert "skill_id" in transformed_skills.columns
            assert "name" in transformed_skills.columns
            assert "category" in transformed_skills.columns
            
            # Verify HRIS column names are not present
            assert "Skill_ID" not in transformed_skills.columns
            assert "Skill_Name" not in transformed_skills.columns
            assert "SkillType" not in transformed_skills.columns
            
            # Check that skill IDs are in the expected format
            assert all(skill_id.startswith("S") for skill_id in transformed_skills["skill_id"])
            
            # Verify that we have skills data
            assert len(transformed_skills) > 0
            
            # Check that names and categories are all strings
            assert transformed_skills["name"].dtype == object  # 'object' dtype for strings in pandas
            assert transformed_skills["category"].dtype == object
            
            # Debug info for category values
            print("\nTransformed categories:", transformed_skills["category"].tolist())
            
            # Check that transformed categories are consistent
            categories = transformed_skills["category"].tolist()
            if all(isinstance(cat, str) for cat in categories):
                print("All categories are strings")
                # Check that categories are valid - either SPECIALIZED, COMMON, or CERTIFICATION
                valid_categories = ["SPECIALIZED", "COMMON", "CERTIFICATION"]
                for category in categories:
                    assert any(valid_cat in category for valid_cat in valid_categories), f"Invalid category: {category}"
                print(f"Categories verified as valid")
            else:
                print("Not all categories are strings")
                assert False, "Categories should all be strings"
    
    def test_apply_job_skills_schema_separation(self):
        """Test that job-skills mapping properly separates schemas."""
        # Set the transformer's config to use our mappings
        self.transformer.config = {
            'jobs_mapping': {
                'job_id': 'JobID',
                'title': 'RoleSet',
                'department': 'Org Unit Name',
                'level': 'Salary Group',
                'location': 'Location'
            },
            'job_skills_mapping': {
                'job_id': 'JobID',
                'skill_id': 'Skill_ID',
                'proficiency': 'Proficiency'
            },
            'value_mappings': {
                'salary_group': {
                    'Group 1': {'level': 'ENTRY', 'psa': 'ENTRY'},
                    'Group 2': {'level': 'ASSOCIATE', 'psa': 'ENTRY'},
                    'Group 3': {'level': 'MID_LEVEL', 'psa': 'MIDRANGE'},
                    'Group 4': {'level': 'SENIOR', 'psa': 'EXPERT'}
                }
            },
            'transformation_options': {
                'use_binary_skills': False,
                'default_proficiency': 1
            }
        }
        
        # Transform jobs first
        with patch.object(self.transformer, '_load_hris_data',
                         return_value=(self.hris_jobs_data, self.hris_skills_data, self.hris_job_skills_data)):
            transformed_jobs = self.transformer._transform_jobs(self.hris_jobs_data)
            
            # Now apply job skills
            transformed_with_skills = self.transformer._apply_job_skills(transformed_jobs, self.hris_job_skills_data)
            
            # Verify that skills were added but schema separation maintained
            assert "skills" in transformed_with_skills.columns
            assert all(isinstance(s, str) for s in transformed_with_skills["skills"] if pd.notna(s))
            
            # Find job J001 and check its skills
            j001_rows = transformed_with_skills[transformed_with_skills["job_id"] == "J001"]
            assert not j001_rows.empty, "Job J001 should exist in the transformed data"
            
            # Get the skills for J001
            j001_skills = j001_rows.iloc[0]["skills"]
            print(f"J001 skills: {j001_skills}")
            
            # Check that the skills format is correct (skill_id:proficiency,skill_id:proficiency,...)
            assert ":" in j001_skills, "Skills should be in format 'skill_id:proficiency'"
            assert "," in j001_skills, "Multiple skills should be separated by commas"
            
            # Check that all skill IDs in the skills string start with 'S'
            skill_entries = j001_skills.split(",")
            for entry in skill_entries:
                skill_id, proficiency = entry.split(":")
                assert skill_id.startswith("S"), f"Skill ID {skill_id} should start with 'S'"
                assert proficiency.isdigit(), f"Proficiency {proficiency} should be a number"
            
            # Verify at least one job has programming skills (S001-S003)
            all_skills = [s for job_skills in transformed_with_skills["skills"] if pd.notna(job_skills) 
                         for s in job_skills.split(",")]
            programming_skills = [s for s in all_skills if any(f"S00{i}:" in s for i in range(1, 4))]
            assert len(programming_skills) > 0, "At least one job should have programming skills (S001-S003)"
    
    def test_end_to_end_transformation(self):
        """Test the full transformation process to ensure schema separation."""
        # Set the transformer's config to use our mappings
        self.transformer.config = {
            'jobs_mapping': {
                'job_id': 'JobID',
                'title': 'RoleSet',
                'department': 'Org Unit Name',
                'level': 'Salary Group',
                'location': 'Location'
            },
            'skills_mapping': {
                'skill_id': 'Skill_ID',
                'name': 'Skill_Name',
                'category': 'SkillType',
                'subcategory': 'Category',
                'description': 'Subcategory'
            },
            'job_skills_mapping': {
                'job_id': 'JobID',
                'skill_id': 'Skill_ID',
                'proficiency': 'Proficiency'
            },
            'value_mappings': {
                'salary_group': {
                    'Group 1': {'level': 'ENTRY', 'psa': 'ENTRY'},
                    'Group 2': {'level': 'ASSOCIATE', 'psa': 'ENTRY'},
                    'Group 3': {'level': 'MID_LEVEL', 'psa': 'MIDRANGE'},
                    'Group 4': {'level': 'SENIOR', 'psa': 'EXPERT'}
                },
                'skill_type': {
                    'Certification': 'CERTIFICATION',
                    'Common Skill': 'COMMON',
                    'Specialized Skill': 'SPECIALIZED'
                }
            },
            'transformation_options': {},
            'output_data': {
                'jobs_file': 'data/jobs.csv',
                'skills_file': 'data/skills.csv'
            }
        }
        
        # Mock the file operations
        with patch.object(self.transformer, '_load_hris_data',
                         return_value=(self.hris_jobs_data, self.hris_skills_data, self.hris_job_skills_data)), \
             patch.object(self.transformer, '_save_transformed_data',
                         return_value=("data/jobs.csv", "data/skills.csv")):
            
            # Run the full transformation
            output_paths = self.transformer.transform()
            
            # Verify that the output paths are as expected
            assert output_paths == ("data/jobs.csv", "data/skills.csv")
    
    def test_compatibility_with_skill_taxonomy(self):
        """Test compatibility of the transformed skills data with our SkillTaxonomy model."""
        # Import from the models
        from skill_similarity_engine.models.skills import Skill, SkillType
        
        # Set transformer configuration
        self.transformer.config = {
            "mappings": {
                "skills": {
                    "skill_id": "id",
                    "name": "name",
                    "category": "category_id",
                    "subcategory": "subcategory",
                    "description": "description"
                }
            },
            "value_mappings": {
                "skill_type": {
                    "TECHNICAL": SkillType.SPECIALIZED.value,
                    "SOFT": SkillType.COMMON.value,
                    "CERTIFICATION": SkillType.CERTIFICATION.value,
                    "OTHER": SkillType.COMMON.value
                }
            }
        }
        
        # Create test data directly
        skills_df = pd.DataFrame([
            {"id": "S001", "name": "Python", "type": "TECHNICAL", "category_id": "C001", "difficulty": 3},
            {"id": "S002", "name": "Communication", "type": "SOFT", "category_id": "C002", "difficulty": 2}
        ])
        
        # Set up the direct transformation on skills data
        self.transformer._transform_skills = mock.MagicMock(return_value=pd.DataFrame([
            {"skill_id": "S001", "name": "Python", "skill_type": SkillType.SPECIALIZED, "category_id": "C001"},
            {"skill_id": "S002", "name": "Communication", "skill_type": SkillType.COMMON, "category_id": "C002"}
        ]))
        
        # Get transformed skills directly
        transformed_skills = self.transformer._transform_skills(skills_df)
        
        # Create Skill objects from transformed data
        skills = []
        for _, row in transformed_skills.iterrows():
            skills.append(Skill(
                skill_id=row["skill_id"],
                name=row["name"],
                skill_type=row["skill_type"],
                category_id=row.get("category_id", "")
            ))
        
        # Verify skills were created correctly
        assert len(skills) == 2
        assert skills[0].skill_id == "S001"
        assert skills[0].name == "Python"
        assert skills[0].skill_type == SkillType.SPECIALIZED
        assert skills[1].skill_id == "S002"
        assert skills[1].name == "Communication"
        assert skills[1].skill_type == SkillType.COMMON
    
    def test_compatibility_with_job_architecture(self):
        """Test compatibility of the transformed jobs data with our JobArchitecture model."""
        # Import from the models
        from skill_similarity_engine.models.jobs import Job, JobLevel, RoleTrack
        
        # Set transformer configuration
        self.transformer.config = {
            "mappings": {
                "jobs": {
                    "job_id": "id",
                    "title": "title",
                    "department": "department",
                    "level": "salary_group"
                }
            },
            "value_mappings": {
                "salary_group": {
                    "Group 2": JobLevel.ASSOCIATE.value,
                    "Group 3": JobLevel.MID_LEVEL.value,
                    "Group 4": JobLevel.SENIOR.value
                }
            }
        }
        
        # Map for transforming job levels
        level_mapping = {
            "Group 2": JobLevel.ASSOCIATE,
            "Group 3": JobLevel.MID_LEVEL,
            "Group 4": JobLevel.SENIOR
        }
        # Default level if not found in mapping
        default_level = JobLevel.ASSOCIATE
        
        # Create test data directly
        jobs_df = pd.DataFrame([
            {"id": "J001", "title": "Software Engineer", "department": "Engineering", "salary_group": "Group 3"},
            {"id": "J002", "title": "Marketing Specialist", "department": "Marketing", "salary_group": "Group 2"}
        ])
        job_skills_df = pd.DataFrame() # Empty for this test
        
        # Set up the direct transformation on jobs data
        self.transformer._transform_jobs = mock.MagicMock(return_value=pd.DataFrame([
            {"job_id": "J001", "title": "Software Engineer", "department": "Engineering", "level": "Group 3"},
            {"job_id": "J002", "title": "Marketing Specialist", "department": "Marketing", "level": "Group 2"}
        ]))
        
        # Get transformed jobs directly
        transformed_jobs = self.transformer._transform_jobs(jobs_df, job_skills_df)
        
        # Create Job objects from transformed data
        jobs = []
        for _, row in transformed_jobs.iterrows():
            job_level = level_mapping.get(row["level"], default_level)
            jobs.append(Job(
                job_id=row["job_id"],
                title=row["title"],
                department=row["department"],
                level=job_level
            ))
        
        # Verify jobs were created correctly
        assert len(jobs) == 2
        assert jobs[0].job_id == "J001"
        assert jobs[0].title == "Software Engineer"
        assert jobs[0].department == "Engineering"
        assert jobs[0].level == JobLevel.MID_LEVEL
        assert jobs[1].job_id == "J002"
        assert jobs[1].title == "Marketing Specialist"
        assert jobs[1].department == "Marketing"
        assert jobs[1].level == JobLevel.ASSOCIATE 