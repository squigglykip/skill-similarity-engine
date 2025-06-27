"""
Helper module for JSON format adaptation.

This module provides helper functions to adapt our list-format JSON files
to the dictionary format expected by the SkillTaxonomy.from_file method.
"""

import os
import json
import tempfile


def adapt_json_format(json_file_path, output_path=None):
    """
    Convert a list-format JSON file to a dictionary-format JSON file.
    
    Args:
        json_file_path: Path to the list-format JSON file
        output_path: Path to write the adapted JSON file (if None, creates a temp file)
        
    Returns:
        Path to the adapted JSON file
    """
    # Read the list-format JSON file
    with open(json_file_path, 'r') as f:
        skills_list = json.load(f)
    
    # Convert list to dictionary with skill_id as keys
    skills_dict = {}
    for skill in skills_list:
        skill_id = skill['skill_id']
        skills_dict[skill_id] = skill
    
    # Create output path if not provided
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
    
    # Write the dictionary-format JSON file
    with open(output_path, 'w') as f:
        json.dump(skills_dict, f, indent=2)
    
    return output_path 
