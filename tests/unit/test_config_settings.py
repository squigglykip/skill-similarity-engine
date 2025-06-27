"""
Unit tests for the configuration system.

This module tests loading a single configuration file and accessing
configuration settings.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

import yaml

# Import from project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')))
from skill_similarity_engine.config.settings import (
    ConfigManager, AppConfig, load_config, get_config
)


class TestConfigSettings(TestCase):
    """Tests for the simplified configuration system."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test config files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)
        
        # Create test config file
        self._create_config()
        
        # Reset singleton
        ConfigManager._instance = None
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()
        
        # Reset singleton
        ConfigManager._instance = None
    
    def _create_config(self):
        """Create a configuration file for testing."""
        config = {
            "version": "0.1.0",
            "environment": "development",
            "data_dir": "data",
            "output_dir": "output",
            "similarity": {
                "method": "cosine",
                "threshold": 0.5,
                "top_n_results": 5
            },
            "gap_analysis": {
                "min_proficiency_ratio": 0.8,
                "skill_difficulty_factor": 1.0,
                "min_gap_threshold": 0.2,
                "category_weights": {
                    "Technical": 1.0,
                    "Soft": 0.8,
                    "Domain": 0.7
                }
            }
        }
        
        with open(self.config_dir / "config.yaml", "w") as f:
            yaml.safe_dump(config, f)
    
    def test_load_config(self):
        """Test loading a single configuration file."""
        config_path = str(self.config_dir / "config.yaml")
        
        load_config(config_path)
        config = get_config()
        
        self.assertEqual(config.version, "0.1.0")
        self.assertEqual(config.environment, "development")
        self.assertEqual(config.data_dir, "data")
        self.assertEqual(config.output_dir, "output")
        self.assertEqual(config.similarity.method, "cosine")
        self.assertEqual(config.similarity.threshold, 0.5)
        self.assertEqual(config.similarity.top_n_results, 5)
        self.assertEqual(config.gap_analysis.min_proficiency_ratio, 0.8)
        self.assertEqual(config.gap_analysis.skill_difficulty_factor, 1.0)
        self.assertEqual(config.gap_analysis.min_gap_threshold, 0.2)
        self.assertEqual(config.gap_analysis.category_weights["Technical"], 1.0)
        self.assertEqual(config.gap_analysis.category_weights["Soft"], 0.8)
        self.assertEqual(config.gap_analysis.category_weights["Domain"], 0.7)
    
    def test_missing_config_file(self):
        """Test handling missing configuration file."""
        with self.assertRaises(FileNotFoundError):
            load_config("nonexistent.yaml") 
