#!/usr/bin/env python3
"""
Unit tests for the configuration module.

These tests verify the functionality of the simplified configuration system,
using a single YAML config file.
"""

import os
import sys
import unittest
import tempfile
import yaml
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.config.settings import (
    NormalisationConfig,
    SimilarityConfig,
    GapAnalysisConfig,
    OpportunityConfig,
    AppConfig,
    ConfigManager,
    load_config,
    get_config,
    get_data_path,
    get_output_path
)


class TestConfigClasses(unittest.TestCase):
    """Test the configuration dataclasses."""
    
    def test_normalisation_config_defaults(self):
        """Test NormalisationConfig defaults."""
        config = NormalisationConfig()
        self.assertTrue(config.use_min_max_scaling)
        self.assertFalse(config.use_boolean_normalisation)
        self.assertTrue(config.use_tfidf_weighting)
        self.assertIsInstance(config.importance_weights, dict)
        self.assertIn("Technical", config.importance_weights)
        self.assertEqual(config.importance_weights["Technical"], 1.0)
    
    def test_similarity_config_defaults(self):
        """Test SimilarityConfig defaults."""
        config = SimilarityConfig()
        self.assertEqual(config.method, "cosine")
        self.assertEqual(config.threshold, 0.5)
        self.assertEqual(config.top_n_results, 5)
    
    def test_gap_analysis_config_defaults(self):
        """Test GapAnalysisConfig defaults."""
        config = GapAnalysisConfig()
        self.assertEqual(config.min_proficiency_ratio, 0.8)
        self.assertEqual(config.skill_difficulty_factor, 1.0)
        self.assertIsInstance(config.category_weights, dict)
        self.assertIn("Technical", config.category_weights)
        self.assertEqual(config.category_weights["Technical"], 1.0)
    
    def test_opportunity_config_defaults(self):
        """Test OpportunityConfig defaults."""
        config = OpportunityConfig()
        self.assertEqual(config.high_similarity_threshold, 0.8)
        self.assertEqual(config.low_gap_threshold, 20.0)
        self.assertEqual(config.high_match_percentage, 80.0)
        self.assertEqual(config.critical_gap_percentage, 50.0)
    
    def test_app_config_defaults(self):
        """Test AppConfig defaults."""
        config = AppConfig()
        self.assertEqual(config.environment, "development")
        self.assertEqual(config.data_dir, "data")
        self.assertEqual(config.output_dir, "output")
        self.assertIsInstance(config.normalisation, NormalisationConfig)
        self.assertIsInstance(config.similarity, SimilarityConfig)
        self.assertIsInstance(config.gap_analysis, GapAnalysisConfig)
        self.assertIsInstance(config.opportunity, OpportunityConfig)


class TestConfigManager(unittest.TestCase):
    """Test the ConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test config files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Reset ConfigManager singleton for each test
        ConfigManager._instance = None
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
        
        # Reset ConfigManager singleton after each test
        ConfigManager._instance = None
    
    def test_singleton_pattern(self):
        """Test that ConfigManager follows the singleton pattern."""
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        self.assertIs(manager1, manager2)
    
    def test_load_config_yaml(self):
        """Test loading config from YAML file."""
        # Create a test YAML config file
        config_path = os.path.join(self.temp_dir.name, "test_config.yaml")
        config_data = {
            "version": "0.1.0",
            "data_dir": "test_data",
            "output_dir": "test_output",
            "similarity": {
                "method": "cosine",
                "threshold": 0.7
            }
        }
        
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
        
        # Load the config
        manager = ConfigManager()
        manager.load_config(config_path)
        
        # Verify config was loaded correctly
        config = manager.config
        self.assertEqual(config.version, "0.1.0")
        self.assertEqual(config.data_dir, "test_data")
        self.assertEqual(config.output_dir, "test_output")
        self.assertEqual(config.similarity.method, "cosine")
        self.assertEqual(config.similarity.threshold, 0.7)
        self.assertEqual(config.similarity.top_n_results, 5)  # Default value
    
    def test_get_data_path(self):
        """Test getting data path."""
        # Set up config with custom data directory
        manager = ConfigManager()
        config = manager.config
        config.data_dir = "test_data"
        
        # Get data path
        data_path = manager.get_data_path("test_file.csv")
        
        # Check if the path contains the expected relative path at the end
        self.assertTrue(data_path.endswith(os.path.join("test_data", "test_file.csv")))
        # Verify it is an absolute path
        self.assertTrue(os.path.isabs(data_path))
    
    def test_get_output_path(self):
        """Test getting output path."""
        # Set up config with custom output directory
        manager = ConfigManager()
        config = manager.config
        config.output_dir = "test_output"
        
        # Get output path
        output_path = manager.get_output_path("test_report.csv")
        
        # Check if the path contains the expected relative path at the end
        self.assertTrue(output_path.endswith(os.path.join("test_output", "test_report.csv")))
        # Verify it is an absolute path
        self.assertTrue(os.path.isabs(output_path))


class TestConfigHelperFunctions(unittest.TestCase):
    """Test the configuration helper functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test config files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a test YAML config file
        config_path = os.path.join(self.temp_dir.name, "test_config.yaml")
        config_data = {
            "version": "0.1.0",
            "data_dir": "custom_data",
            "output_dir": "custom_output",
        }
        
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
        
        # Load the config
        self.config_path = config_path
        load_config(config_path)
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
        # Reset ConfigManager singleton after each test
        ConfigManager._instance = None
    
    def test_get_config(self):
        """Test get_config function."""
        config = get_config()
        self.assertEqual(config.version, "0.1.0")
        self.assertEqual(config.data_dir, "custom_data")
        self.assertEqual(config.output_dir, "custom_output")
    
    def test_get_data_path(self):
        """Test get_data_path function."""
        data_path = get_data_path("test_file.csv")
        
        # Check if the path contains the expected relative path at the end
        self.assertTrue(data_path.endswith(os.path.join("custom_data", "test_file.csv")))
        # Verify it is an absolute path
        self.assertTrue(os.path.isabs(data_path))
    
    def test_get_output_path(self):
        """Test get_output_path function."""
        output_path = get_output_path("test_report.csv")
        
        # Check if the path contains the expected relative path at the end
        self.assertTrue(output_path.endswith(os.path.join("custom_output", "test_report.csv")))
        # Verify it is an absolute path
        self.assertTrue(os.path.isabs(output_path))


if __name__ == "__main__":
    unittest.main() 