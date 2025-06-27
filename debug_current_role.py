#!/usr/bin/env python3
"""
Debug script to investigate Current Role Context generator issues.
"""

import sys
import os
import json
import sqlite3

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from skill_similarity_engine.webapp.career_analysis.src.current_role_context_generator import CurrentRoleContextGenerator

def get_db():
    """Get database connection."""
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'career_transitions.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return conn

def debug_current_role_context():
    """Debug the Current Role Context generator to find why sections are empty."""
    
    print("🔍 Starting Current Role Context Debug...")
    
    # Get database connection
    db = get_db()
    
    # Create generator
    generator = CurrentRoleContextGenerator(db)
    
    # Generate content
    print(f"\n📋 Generating content for job R0102.3...")
    result = generator.generate('R0102.3', include_organisational_deployment=True)
    
    print(f"\n=== GENERATOR RESULT STRUCTURE ===")
    print(f"Keys in result: {list(result.keys())}")
    
    content = result.get('content', {})
    print(f"\nContent sections: {list(content.keys())}")
    
    print(f"\n=== DETAILED SECTION ANALYSIS ===")
    for section_name, section_data in content.items():
        print(f"\n--- {section_name} ---")
        print(f"Type: {type(section_data)}")
        print(f"Keys: {list(section_data.keys()) if isinstance(section_data, dict) else 'Not a dict'}")
        
        if isinstance(section_data, dict):
            content_value = section_data.get('content', 'NO CONTENT KEY')
            print(f"Content type: {type(content_value)}")
            print(f"Content length: {len(str(content_value))}")
            
            if isinstance(content_value, list):
                print(f"Content list length: {len(content_value)}")
                for i, item in enumerate(content_value):
                    print(f"  Item {i}: {type(item)}")
                    if isinstance(item, dict):
                        print(f"    Keys: {list(item.keys())}")
                        if 'text' in item:
                            print(f"    Text length: {len(str(item['text']))}")
                            print(f"    Text preview: {str(item['text'])[:100]}...")
            elif isinstance(content_value, str):
                print(f"Content preview: {content_value[:200]}...")
            else:
                print(f"Content value: {content_value}")
    
    print(f"\n=== PROBLEMATIC SECTIONS FOCUS ===")
    for section_name in ['core_competency_foundation', 'strategic_intelligence_metrics']:
        print(f"\n🎯 Analyzing {section_name}:")
        section_data = content.get(section_name, {})
        
        if not section_data:
            print(f"  ❌ Section completely missing!")
            continue
            
        content_value = section_data.get('content', 'NO CONTENT KEY')
        print(f"  Content type: {type(content_value)}")
        
        if isinstance(content_value, list):
            print(f"  List with {len(content_value)} items")
            for i, item in enumerate(content_value):
                print(f"    Item {i}: {type(item)}")
                if isinstance(item, dict) and 'text' in item:
                    text_content = item['text']
                    print(f"      Text length: {len(text_content)}")
                    if len(text_content) > 0:
                        print(f"      Text sample: {text_content[:100]}...")
                    else:
                        print(f"      ❌ Empty text content!")
        elif isinstance(content_value, str):
            if len(content_value) == 0:
                print(f"  ❌ Empty string content!")
            else:
                print(f"  Content length: {len(content_value)}")
                print(f"  Content: {content_value[:200]}...")
        else:
            print(f"  Content: {content_value}")
    
    print(f"\n✅ Debug analysis complete!")

if __name__ == '__main__':
    debug_current_role_context() 