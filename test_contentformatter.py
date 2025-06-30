#!/usr/bin/env python3
"""
Test ContentFormatter Import and Functionality
==============================================

This script tests whether ContentFormatter is properly available and functional.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path (same as import_fix.py)
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir / 'src'
if src_dir.exists():
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
        print(f"✅ Added to Python path: {src_dir}")

# Now test the import
print("🧪 Testing ContentFormatter import...")

try:
    # Try the same import pattern as current_role_context_generator.py
    ContentFormatter = None
    try:
        from skill_similarity_engine.webapp.career_analysis.formatter import ContentFormatter
        print("✅ SUCCESS: Direct import from skill_similarity_engine.webapp.career_analysis.formatter")
    except ImportError as e1:
        print(f"❌ FAILED: Direct import - {e1}")
        try:
            # Try relative import (won't work from script but let's see the error)
            import sys
            career_analysis_path = current_dir / 'src' / 'skill_similarity_engine' / 'webapp' / 'career_analysis'
            sys.path.insert(0, str(career_analysis_path))
            from formatter import ContentFormatter
            print("✅ SUCCESS: Import from formatter after path adjustment")
        except ImportError as e2:
            print(f"❌ FAILED: Relative import - {e2}")
            ContentFormatter = None
    
    # Test if ContentFormatter is available
    if ContentFormatter:
        print(f"✅ ContentFormatter is available: {ContentFormatter}")
        print(f"✅ ContentFormatter type: {type(ContentFormatter)}")
        
        # Test if it has expected methods
        expected_methods = ['create_paragraph', 'create_skills_analysis_table', 'create_formatted_content']
        for method in expected_methods:
            if hasattr(ContentFormatter, method):
                print(f"✅ Method {method}: Available")
            else:
                print(f"❌ Method {method}: Missing")
        
        # Test a simple method call
        try:
            test_paragraph = ContentFormatter.create_paragraph("Test content", [])
            print(f"✅ create_paragraph test: SUCCESS - {type(test_paragraph)}")
        except Exception as e:
            print(f"❌ create_paragraph test: FAILED - {e}")
        
    else:
        print("❌ ContentFormatter is None or not available")
        
        # Try to understand why by checking the formatter.py file
        formatter_path = current_dir / 'src' / 'skill_similarity_engine' / 'webapp' / 'career_analysis' / 'formatter.py'
        if formatter_path.exists():
            print(f"✅ formatter.py exists at: {formatter_path}")
            try:
                with open(formatter_path, 'r') as f:
                    content = f.read()
                    if 'ContentFormatter' in content:
                        print("✅ ContentFormatter class found in formatter.py")
                        # Find the class definition
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if 'class ContentFormatter' in line:
                                print(f"✅ Found ContentFormatter class at line {i+1}: {line.strip()}")
                                break
                    else:
                        print("❌ ContentFormatter class NOT found in formatter.py")
            except Exception as e:
                print(f"❌ Error reading formatter.py: {e}")
        else:
            print(f"❌ formatter.py NOT found at: {formatter_path}")

except Exception as e:
    print(f"❌ CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 Test completed!") 