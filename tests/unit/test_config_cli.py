"""
Unit tests for configuration CLI commands.

This module tests the CLI commands for configuration management.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import click
from click.testing import CliRunner

# Import from project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')))
from skill_similarity_engine.cli.config_cmd import config_group


class TestConfigCLI(TestCase):
    """Tests for the configuration CLI commands."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        
        # Create a temporary directory for test config files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()
    
    def test_init_command(self):
        """Test the 'init' command with our simplified approach."""
        config_file = self.config_dir / "config.yaml"
        
        result = self.runner.invoke(config_group, [
            'init',
            '--output-file', str(config_file)
        ])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Created configuration file", result.output)
        
        # Check that file was created
        self.assertTrue(config_file.exists())
        
        # Read the content to verify
        with open(config_file, "r") as f:
            content = f.read()
        
        # Verify key sections exist
        self.assertIn("version:", content)
        self.assertIn("data_dir:", content)
        self.assertIn("normalisation:", content)
        self.assertIn("similarity:", content)
        self.assertIn("gap_analysis:", content)
        self.assertIn("opportunity:", content)
        self.assertIn("future_extensions:", content)
    
    @patch('skill_similarity_engine.cli.config_cmd.load_config')
    def test_view_command(self, mock_load_config):
        """Test the 'view' command with our simplified approach."""
        # Set up a mock config to be returned
        from skill_similarity_engine.config.settings import ConfigManager, AppConfig
        ConfigManager._instance = None
        config_manager = ConfigManager()
        config_manager.config = AppConfig()
        config_manager.config.version = "0.1.0"
        config_manager.config.environment = "testing"
        config_manager.config.data_dir = "test_data"
        
        # Create a test config file
        config_file = self.config_dir / "config.yaml"
        with open(config_file, "w") as f:
            f.write("version: 0.1.0\ndata_dir: test_data\n")
        
        # Mock the return value of get_config
        with patch('skill_similarity_engine.cli.config_cmd.get_config', return_value=config_manager.config):
            # Run the command
            result = self.runner.invoke(config_group, [
                'view',
                '--format', 'yaml',
                '--config-file', str(config_file)
            ])
            
            self.assertEqual(result.exit_code, 0)
            self.assertIn("version: 0.1.0", result.output)
            self.assertIn("data_dir: test_data", result.output)
            
            # Check that load_config was called with the right path
            mock_load_config.assert_called_once_with(str(config_file))


if __name__ == "__main__":
    unittest.main() 