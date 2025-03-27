#!/usr/bin/env python3
"""
Example script showing how to use the configuration system.

This script demonstrates how to load the configuration and use it in the application.
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from src.skill_similarity_engine.config.settings import load_config, get_config


def main():
    """Run the script with configuration."""
    parser = argparse.ArgumentParser(description="Run with configuration")
    parser.add_argument(
        "--config-file",
        type=str,
        default=os.path.join(project_root, "config", "config.yaml"),
        help="Path to configuration file"
    )
    args = parser.parse_args()
    
    # Load configuration
    print(f"Loading configuration from {args.config_file}")
    load_config(args.config_file)
    
    # Get and display configuration
    config = get_config()
    print(f"Configuration version: {config.version}")
    print(f"Data directory: {config.data_dir}")
    print(f"Output directory: {config.output_dir}")
    print(f"Similarity threshold: {config.similarity.threshold}")
    print(f"Gap analysis min proficiency ratio: {config.gap_analysis.min_proficiency_ratio}")
    print(f"Gap analysis min gap threshold: {config.gap_analysis.min_gap_threshold}")
    
    # Example of using the configuration
    print("\nExample of configuration usage:")
    if config.similarity.threshold > 0.7:
        print("Using high similarity threshold - matches will be more precise but fewer")
    else:
        print("Using lower similarity threshold - more matches but less precise")


if __name__ == "__main__":
    main() 