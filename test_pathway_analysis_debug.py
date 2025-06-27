#!/usr/bin/env python3
"""
Debug script for pathway analysis generation

This script tests the career analysis service directly to examine
the exact data structure being generated, particularly focusing on
the pathway analysis opportunities content that's causing JSON parsing issues.
"""

import sys
import json
import sqlite3
from pathlib import Path

def main():
    print("🔍 Pathway Analysis Debug Script")
    print("=" * 50)
    
    # Setup paths
    webapp_dir = Path(__file__).parent / "src" / "skill_similarity_engine" / "webapp"
    services_dir = webapp_dir / "career_analysis" / "services"
    db_path = Path(__file__).parent / "models" / "2025-Q2" / "business_context.sqlite"
    
    print(f"📁 Webapp directory: {webapp_dir}")
    print(f"📁 Services directory: {services_dir}")
    print(f"📊 Database path: {db_path}")
    
    # Add services to Python path
    sys.path.insert(0, str(services_dir))
    
    try:
        # Import the service
        from career_analysis_service import CareerAnalysisService
        print("✅ Successfully imported CareerAnalysisService")
    except ImportError as e:
        print(f"❌ Failed to import CareerAnalysisService: {e}")
        return
    
    # Connect to database
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Initialize service
    try:
        service = CareerAnalysisService(conn)
        print("✅ CareerAnalysisService initialized")
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        conn.close()
        return
    
    # Test pathway analysis generation
    print("\n🎯 Testing pathway analysis generation for R0102.3...")
    try:
        result = service.generate_analysis(
            job_from='R0102.3',
            analysis_mode='top_matches',
            output_mode='web',
            similarity_min=40,
            similarity_max=90,
            top_n=3
        )
        print("✅ Analysis generation completed")
    except Exception as e:
        print(f"❌ Analysis generation failed: {e}")
        conn.close()
        return
    
    # Examine results
    print(f"\n📊 Analysis Result:")
    print(f"   Success: {result.get('success')}")
    
    if not result.get('success'):
        print(f"   Error: {result.get('error')}")
        conn.close()
        return
    
    print(f"   Sections: {list(result.get('sections', {}).keys())}")
    print(f"   Output mode: {result.get('output_mode')}")
    
    # Focus on pathway analysis
    sections = result.get('sections', {})
    if 'pathway_analysis' not in sections:
        print("❌ No pathway_analysis section found")
        conn.close()
        return
    
    pathway = sections['pathway_analysis']
    print(f"\n🛤️ Pathway Analysis Section:")
    print(f"   Title: {pathway.get('title')}")
    print(f"   Section Key: {pathway.get('section_key')}")
    print(f"   Subsections: {list(pathway.get('subsections', {}).keys())}")
    
    # Examine opportunities subsection
    subsections = pathway.get('subsections', {})
    if 'opportunities' not in subsections:
        print("❌ No opportunities subsection found")
        conn.close()
        return
    
    opportunities = subsections['opportunities']
    print(f"\n🎯 Opportunities Subsection:")
    print(f"   Title: {opportunities.get('title')}")
    print(f"   Type: {opportunities.get('type')}")
    
    content = opportunities.get('content')
    print(f"   Content type: {type(content)}")
    print(f"   Content length: {len(str(content))}")
    
    # Show content structure
    if isinstance(content, str):
        print(f"\n📝 Content is STRING:")
        print(f"   First 200 chars: {content[:200]}...")
        print(f"   Last 200 chars: ...{content[-200:]}")
        
        # Check if it looks like a Python list representation
        if content.strip().startswith('[') and content.strip().endswith(']'):
            print("   ✅ Looks like Python list format")
        elif content.strip().startswith('[') and not content.strip().endswith(']'):
            print("   ⚠️ Looks like TRUNCATED Python list (starts with [ but doesn't end with ])")
        else:
            print("   ❓ Unknown string format")
    
    elif isinstance(content, list):
        print(f"\n📝 Content is LIST with {len(content)} items:")
        for i, item in enumerate(content[:2]):  # Show first 2 items
            print(f"   Item {i}: {type(item)}")
            if isinstance(item, dict):
                print(f"     Keys: {list(item.keys())}")
                if 'header' in item:
                    print(f"     Header preview: {str(item['header'])[:100]}...")
    
    elif isinstance(content, dict):
        print(f"\n📝 Content is DICT:")
        print(f"   Keys: {list(content.keys())}")
    
    else:
        print(f"\n📝 Content is {type(content)}: {content}")
    
    # Test JSON serialization
    print(f"\n🧪 Testing JSON serialization...")
    try:
        json_str = json.dumps(content, default=str)
        print(f"   ✅ JSON serialization successful")
        print(f"   JSON length: {len(json_str)}")
        
        # Test parsing back
        try:
            parsed = json.loads(json_str)
            print(f"   ✅ JSON parsing successful")
        except Exception as e:
            print(f"   ❌ JSON parsing failed: {e}")
    
    except Exception as e:
        print(f"   ❌ JSON serialization failed: {e}")
        print(f"   Error type: {type(e)}")
        
        # Try to identify the problematic part
        if hasattr(e, 'args') and e.args:
            print(f"   Error details: {e.args[0]}")
    
    # Test Flask jsonify equivalent and dump the full response
    print(f"\n🌐 Testing Flask jsonify simulation...")
    try:
        from flask import Flask, jsonify
        app = Flask(__name__)
        
        with app.app_context():
            # Create the full response structure that Flask would send
            full_response = {
                'success': True,
                'content': {
                    'pathway_analysis': pathway
                },
                'metadata': {}
            }
            
            response = jsonify(full_response)
            print(f"   ✅ Flask jsonify successful")
            
            # Get the actual JSON data that would be sent to browser
            json_data = response.get_json()
            
            # Save to file for inspection
            output_file = Path(__file__).parent / "debug_pathway_output.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            print(f"   📁 Full JSON response saved to: {output_file}")
            
            # Check specifically the opportunities content in the saved data
            saved_opportunities = json_data.get('content', {}).get('pathway_analysis', {}).get('subsections', {}).get('opportunities', {}).get('content', '')
            print(f"   📊 Saved opportunities content length: {len(saved_opportunities)}")
            
            if isinstance(saved_opportunities, str):
                if saved_opportunities.strip().endswith(']'):
                    print(f"   ✅ Saved content ends properly with ']'")
                else:
                    print(f"   ⚠️ Saved content does NOT end with ']'")
                    print(f"   Last 100 chars: {saved_opportunities[-100:]}")
            
    except Exception as e:
        print(f"   ❌ Flask jsonify failed: {e}")
    
    conn.close()
    print("\n✅ Analysis complete")

if __name__ == "__main__":
    main() 