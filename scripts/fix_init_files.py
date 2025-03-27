#!/usr/bin/env python3
"""
Utility script to fix encoding issues in __init__.py files.

This script creates clean __init__.py files in all directories of the package.
"""

import os
from pathlib import Path

# Map of module paths to content
MODULE_CONTENT = {
    "src/skill_similarity_engine/__init__.py": """\"\"\"
Skill Similarity Engine - A system for analyzing skill similarities and identifying reskilling opportunities.
\"\"\"

__version__ = "0.1.0"
""",
    "src/skill_similarity_engine/analysis/__init__.py": """\"\"\"Analysis package for skill gap and similarity analysis.\"\"\"
""",
    "src/skill_similarity_engine/config/__init__.py": """\"\"\"Config package for application configuration.\"\"\"
""",
    "src/skill_similarity_engine/data/__init__.py": """\"\"\"Data package for data loading and normalization.\"\"\"
""",
    "src/skill_similarity_engine/models/__init__.py": """\"\"\"Models package for data model definitions.\"\"\"
""", 
    "src/skill_similarity_engine/similarity/__init__.py": """\"\"\"Similarity package for calculating similarity between entities.\"\"\"
""",
    "src/skill_similarity_engine/utils/__init__.py": """\"\"\"Utility functions and helpers.\"\"\"
""",
    "src/skill_similarity_engine/visualization/__init__.py": """\"\"\"Visualization package for reports and visual representations.\"\"\"
"""
}

def main():
    """Fix all __init__.py files in the project."""
    project_root = Path(__file__).parent
    
    # Ensure the directories exist
    for module_path in MODULE_CONTENT:
        # Create directory if it doesn't exist
        dir_path = (project_root / Path(module_path)).parent
        os.makedirs(dir_path, exist_ok=True)
    
    # Create/fix the files
    for module_path, content in MODULE_CONTENT.items():
        file_path = project_root / module_path
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed: {module_path}")
    
    print("\nAll __init__.py files have been fixed!")

if __name__ == "__main__":
    main() 