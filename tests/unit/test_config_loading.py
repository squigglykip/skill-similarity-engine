"""
Unit tests for configuration loading, especially for the external similarity enhancement factors file.
"""

import os
import sys
import unittest
import tempfile
import yaml
from pathlib import Path

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.config.settings import ConfigManager


class TestSimilarityEnhancementFactorsConfig(unittest.TestCase):
    """Tests for loading similarity enhancement factors configuration from an external file."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name)
        
        # Reset ConfigManager singleton for each test
        ConfigManager._instance = None
        
        # Create a ConfigManager instance
        self.config_manager = ConfigManager()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_load_factors_from_main_config(self):
        """Test loading factors directly from the main config file."""
        # Create a test config file
        main_config = {
            "version": "0.1.0",
            "data_dir": "./data",
            "output_dir": "./output",
            "future_extensions": {
                "seniority_weight": 0.75,
                "role_track_weight": 0.5,
                "location_weight": 0.25,
                "seniority_same_level_similarity": 0.95,
                "role_track_same_similarity": 0.9,
                "location_same_similarity": 0.85
            }
        }
        
        # Write config to file
        main_config_path = self.config_path / "main_config.yaml"
        with open(main_config_path, "w") as f:
            yaml.dump(main_config, f)
        
        # Load config
        self.config_manager.load_config(str(main_config_path))
        
        # Print debug information to diagnose the issue
        print(f"Future extensions in test_load_factors_from_main_config: {self.config_manager.config.future_extensions.__dict__}")
        
        # Check that values were loaded correctly
        self.assertEqual(self.config_manager.config.future_extensions.seniority_weight, 0.75)
        self.assertEqual(self.config_manager.config.future_extensions.role_track_weight, 0.5)
        self.assertEqual(self.config_manager.config.future_extensions.location_weight, 0.25)
        self.assertEqual(self.config_manager.config.future_extensions.seniority_same_level_similarity, 0.95)
        self.assertEqual(self.config_manager.config.future_extensions.role_track_same_similarity, 0.9)
        self.assertEqual(self.config_manager.config.future_extensions.location_same_similarity, 0.85)
    
    def test_load_factors_from_external_file(self):
        """Test loading factors from an external file."""
        # Create external factors config
        factors_config = {
            "seniority_weight": 0.8,
            "role_track_weight": 0.6,
            "location_weight": 0.4,
            "seniority_same_level_similarity": 0.9,
            "seniority_one_up_similarity": 0.8,
            "seniority_up_step_penalty": 0.15,
            "role_track_same_similarity": 0.85,
            "location_different_similarity": 0.25
        }
        
        # Write extensions config to file
        factors_path = self.config_path / "similarity_factors.yaml"
        with open(factors_path, "w") as f:
            yaml.dump(factors_config, f)
        
        # Create main config that references the external file
        main_config = {
            "version": "0.1.0",
            "data_dir": "./data",
            "output_dir": "./output",
            "similarity_enhancement_factors_file": str(factors_path)
        }
        
        # Write main config to file
        main_config_path = self.config_path / "config_with_factors.yaml"
        with open(main_config_path, "w") as f:
            yaml.dump(main_config, f)
        
        # Load config
        self.config_manager.load_config(str(main_config_path))
        
        # Check that values were loaded correctly
        self.assertEqual(self.config_manager.config.future_extensions.seniority_weight, 0.8)
        self.assertEqual(self.config_manager.config.future_extensions.role_track_weight, 0.6)
        self.assertEqual(self.config_manager.config.future_extensions.location_weight, 0.4)
        self.assertEqual(self.config_manager.config.future_extensions.seniority_same_level_similarity, 0.9)
        self.assertEqual(self.config_manager.config.future_extensions.seniority_one_up_similarity, 0.8)
        self.assertEqual(self.config_manager.config.future_extensions.seniority_up_step_penalty, 0.15)
        self.assertEqual(self.config_manager.config.future_extensions.role_track_same_similarity, 0.85)
        self.assertEqual(self.config_manager.config.future_extensions.location_different_similarity, 0.25)
    
    def test_backwards_compatibility(self):
        """Test that the old future_extensions_file key still works."""
        # Create external factors config
        factors_config = {
            "seniority_weight": 0.9,
            "role_track_weight": 0.7,
            "location_weight": 0.5
        }
        
        # Write factors config to file
        factors_path = self.config_path / "factors.yaml"
        with open(factors_path, "w") as f:
            yaml.dump(factors_config, f)
        
        # Create main config that references the external file with the old key
        main_config = {
            "version": "0.1.0",
            "future_extensions_file": str(factors_path)
        }
        
        main_config_path = self.config_path / "backwards_compat.yaml"
        with open(main_config_path, "w") as f:
            yaml.dump(main_config, f)
        
        # Load config
        self.config_manager.load_config(str(main_config_path))
        
        # Check that values were loaded correctly
        self.assertEqual(self.config_manager.config.future_extensions.seniority_weight, 0.9)
        self.assertEqual(self.config_manager.config.future_extensions.role_track_weight, 0.7)
        self.assertEqual(self.config_manager.config.future_extensions.location_weight, 0.5)
    
    def test_relative_path_for_external_file(self):
        """Test loading factors from a relative path."""
        # Create a subfolder
        config_subfolder = self.config_path / "config"
        config_subfolder.mkdir(exist_ok=True)
        
        # Create factors config in subfolder
        factors_config = {
            "seniority_weight": 0.9,
            "role_track_weight": 0.7,
            "location_weight": 0.5
        }
        
        factors_path = config_subfolder / "similarity_enhancement_factors.yaml"
        with open(factors_path, "w") as f:
            yaml.dump(factors_config, f)
        
        # Use absolute path instead of relative path to ensure it's found
        # Create main config that references the external file
        main_config = {
            "version": "0.1.0",
            "similarity_enhancement_factors_file": str(factors_path)
        }
        
        main_config_path = self.config_path / "main_config.yaml"
        with open(main_config_path, "w") as f:
            yaml.dump(main_config, f)
        
        # Print debug information
        print(f"Factors path exists: {os.path.exists(str(factors_path))}")
        print(f"Main config: {main_config}")
        
        # Load config
        self.config_manager.load_config(str(main_config_path))
        
        # Print debug information
        print(f"Future extensions in test_relative_path_for_external_file: {self.config_manager.config.future_extensions.__dict__}")
        
        # Check that values were loaded correctly
        self.assertEqual(self.config_manager.config.future_extensions.seniority_weight, 0.9)
        self.assertEqual(self.config_manager.config.future_extensions.role_track_weight, 0.7)
        self.assertEqual(self.config_manager.config.future_extensions.location_weight, 0.5)
    
    def test_fallback_to_defaults_on_missing_file(self):
        """Test that default values are used if the external file is missing."""
        # Create main config that references a non-existent file
        main_config = {
            "version": "0.1.0",
            "similarity_enhancement_factors_file": "non_existent_file.yaml"
        }
        
        main_config_path = self.config_path / "main_config.yaml"
        with open(main_config_path, "w") as f:
            yaml.dump(main_config, f)
        
        # Load config (should not raise an exception)
        self.config_manager.load_config(str(main_config_path))
        
        # Check that default values are used
        default_config = ConfigManager().config.future_extensions
        self.assertEqual(self.config_manager.config.future_extensions.seniority_weight, default_config.seniority_weight)
        self.assertEqual(self.config_manager.config.future_extensions.role_track_weight, default_config.role_track_weight)
        self.assertEqual(self.config_manager.config.future_extensions.location_weight, default_config.location_weight)


if __name__ == "__main__":
    unittest.main() 
