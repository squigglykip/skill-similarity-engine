#!/usr/bin/env python3
"""
API Data Inspector

This script calls the real career analysis API endpoints to inspect the exact
data format for Skills Transition Analysis tables and compare it with test data
to identify why the first skill doesn't get hyperlink formatting.

Key API Endpoints:
1. /api/career-analysis-preview (POST) - Returns JSON preview data
2. /api/career-analysis-document (POST) - Generates Word document  

Focus: Skills Transition Analysis table data format
"""

import requests
import json
import sys
import os
from typing import Dict, Any

def test_api_preview_endpoint():
    """Test the preview API endpoint to get raw Skills Transition data."""
    
    print("🌐 Testing API Preview Endpoint")
    print("=" * 60)
    
    # API endpoint
    url = "http://localhost:5000/api/career-analysis-preview"
    
    # Test request data (matches what the JavaScript sends)
    test_data = {
        "job_from": "R0102.3",
        "analysis_mode": "top_matches", 
        "job_to": None,
        "scenario": "discovery",
        "audience": "executive",
        "top_n": 3,
        "similarity_min": 40,
        "similarity_max": 90,
        "output_format": "web"
    }
    
    print(f"📡 Making POST request to: {url}")
    print(f"📋 Request data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(
            url, 
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully received preview data")
            
            # Extract and analyze Skills Transition Analysis data
            extract_skills_transition_data(data)
            
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def extract_skills_transition_data(api_data: Dict[Any, Any]):
    """Extract and analyze Skills Transition Analysis data from API response."""
    
    print(f"\n🔍 Analyzing API Response Structure")
    print("=" * 60)
    
    if not isinstance(api_data, dict):
        print(f"❌ API data is not a dict: {type(api_data)}")
        return
    
    print(f"📋 Top-level keys: {list(api_data.keys())}")
    
    # Look for content in the response
    content = api_data.get('content', {})
    if not content:
        print(f"❌ No 'content' key found in API response")
        return
        
    print(f"📋 Content keys: {list(content.keys())}")
    
    # Look through all sections for Skills Transition Analysis
    skills_data_found = []
    
    for section_name, section_data in content.items():
        print(f"\n🔍 Examining section: {section_name}")
        
        if isinstance(section_data, dict):
            subsections = section_data.get('subsections', {})
            print(f"   📋 Subsections: {list(subsections.keys())}")
            
            for subsection_name, subsection_data in subsections.items():
                if 'skills' in subsection_name.lower() or 'transition' in subsection_name.lower():
                    print(f"   🎯 Found potential skills data in: {subsection_name}")
                    skills_data_found.append({
                        'section': section_name,
                        'subsection': subsection_name,
                        'data': subsection_data
                    })
                    
                    # Analyze this subsection
                    analyze_skills_subsection(subsection_name, subsection_data)
                
                # NEW: Check for opportunities section with embedded skills data
                elif subsection_name == 'opportunities':
                    print(f"   🎯 Found opportunities section - checking for embedded skills data")
                    analyze_opportunities_section(subsection_data)
    
    if not skills_data_found:
        print(f"\n⚠️ No explicit Skills Transition Analysis data found")
        print(f"Available sections: {list(content.keys())}")
        
        # Print pathway_analysis section in detail
        pathway_section = content.get('pathway_analysis', {})
        if pathway_section:
            print(f"\n📋 Detailed pathway_analysis structure:")
            print_detailed_structure(pathway_section, indent=1)

def analyze_opportunities_section(opportunities_data: Dict):
    """Analyze the opportunities section for embedded Skills Transition Analysis."""
    
    print(f"\n🎯 Analyzing Opportunities Section")
    print("-" * 40)
    
    if not isinstance(opportunities_data, dict):
        print(f"❌ Opportunities data is not dict: {type(opportunities_data)}")
        return
    
    print(f"📋 Opportunities keys: {list(opportunities_data.keys())}")
    
    # Look for content that might contain opportunities
    content = opportunities_data.get('content', '')
    if isinstance(content, str) and content:
        print(f"📄 Opportunities content (first 300 chars):")
        print(f"{content[:300]}...")
        
        # Check if this might be a Python list/dict string
        if content.strip().startswith('[') or content.strip().startswith('{'):
            print(f"🔍 Content looks like serialized Python data")
            try:
                # Try to parse as JSON first
                import ast
                parsed_content = ast.literal_eval(content)
                print(f"✅ Successfully parsed Python data")
                analyze_parsed_opportunities(parsed_content)
            except Exception as e:
                print(f"❌ Failed to parse Python data: {e}")
    
    elif isinstance(content, list):
        print(f"📊 Content is list with {len(content)} opportunities")
        analyze_parsed_opportunities(content)
    
    elif isinstance(content, dict):
        print(f"📊 Content is dict with keys: {list(content.keys())}")
        analyze_parsed_opportunities(content)

def analyze_parsed_opportunities(opportunities):
    """Analyze parsed opportunities data for Skills Transition Analysis."""
    
    print(f"\n🔍 Analyzing Parsed Opportunities")
    print("-" * 30)
    
    if isinstance(opportunities, list):
        print(f"📊 Found {len(opportunities)} opportunities")
        
        for i, opportunity in enumerate(opportunities[:2]):  # Check first 2
            print(f"\n📋 Opportunity {i+1}:")
            if isinstance(opportunity, dict):
                print(f"   Keys: {list(opportunity.keys())}")
                
                # Look for skills_transition_analysis directly
                if 'skills_transition_analysis' in opportunity:
                    print(f"   🎯 Found Skills Transition Analysis!")
                    skills_data = opportunity['skills_transition_analysis']
                    analyze_skills_subsection('skills_transition_analysis', skills_data)
                
                # Look for subsections
                subsections = opportunity.get('subsections', {})
                if isinstance(subsections, dict):
                    print(f"   Subsections: {list(subsections.keys())}")
                    
                    # Look for skills transition analysis
                    for sub_name, sub_data in subsections.items():
                        if 'skills' in sub_name.lower() and 'transition' in sub_name.lower():
                            print(f"   🎯 Found Skills Transition Analysis: {sub_name}")
                            analyze_skills_subsection(sub_name, sub_data)
                        elif 'skills' in sub_name.lower():
                            print(f"   🔍 Found skills-related section: {sub_name}")
                            analyze_skills_subsection(sub_name, sub_data)
    
    elif isinstance(opportunities, dict):
        print(f"📊 Opportunities is dict with keys: {list(opportunities.keys())}")
        # Check if this single dict has skills_transition_analysis
        if 'skills_transition_analysis' in opportunities:
            print(f"   🎯 Found Skills Transition Analysis!")
            skills_data = opportunities['skills_transition_analysis']
            analyze_skills_subsection('skills_transition_analysis', skills_data)

def print_detailed_structure(data, indent=0):
    """Print detailed structure of data for debugging."""
    
    indent_str = "  " * indent
    
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{indent_str}{key}: {type(value).__name__}")
                if indent < 3:  # Limit depth
                    print_detailed_structure(value, indent + 1)
            else:
                value_str = str(value)[:100] if len(str(value)) > 100 else str(value)
                print(f"{indent_str}{key}: {value_str}")
    
    elif isinstance(data, list):
        print(f"{indent_str}List with {len(data)} items:")
        for i, item in enumerate(data[:3]):  # First 3 items
            print(f"{indent_str}[{i}]: {type(item).__name__}")
            if indent < 3:  # Limit depth
                print_detailed_structure(item, indent + 1)

def analyze_skills_subsection(subsection_name: str, subsection_data: Dict):
    """Analyze a specific skills subsection to understand data format."""
    
    print(f"\n🧪 Analyzing Skills Subsection: {subsection_name}")
    print("-" * 40)
    
    if not isinstance(subsection_data, dict):
        print(f"❌ Subsection data is not dict: {type(subsection_data)}")
        return
    
    print(f"📋 Subsection keys: {list(subsection_data.keys())}")
    
    # Look for content
    content = subsection_data.get('content', '')
    content_type = subsection_data.get('content_type', 'unknown')
    formatting = subsection_data.get('formatting', {})
    
    print(f"📊 Content type: {content_type}")
    print(f"📊 Has formatting: {bool(formatting)}")
    
    if isinstance(content, str) and content:
        print(f"📄 Content (first 500 chars):")
        print(f"Raw: {repr(content[:500])}")
        
        # Look for skills with URLs
        if '|https://lightcast.io/' in content:
            print(f"✅ Found skills with URLs!")
            analyze_skills_with_urls(content)
        else:
            print(f"❌ No skills with URLs found")
            
        # Look for bullet points
        if '•' in content:
            print(f"✅ Found bullet points")
            lines = content.split('\n')
            print(f"📊 Lines count: {len(lines)}")
            for i, line in enumerate(lines[:5]):
                print(f"   Line {i+1}: {repr(line)}")
        else:
            print(f"❌ No bullet points found")
    
    elif isinstance(content, dict):
        print(f"📊 Content is dict with keys: {list(content.keys())}")
        
        # Look for structured table data
        if 'headers' in content and 'rows' in content:
            print(f"✅ Found structured table data!")
            analyze_structured_table(content)
    
    elif isinstance(content, list):
        print(f"📊 Content is list with {len(content)} items")
        for i, item in enumerate(content[:3]):
            print(f"   Item {i+1}: {str(item)[:100]}...")
    
    else:
        print(f"❌ Content type not recognized: {type(content)}")

def analyze_skills_with_urls(content: str):
    """Analyze skills content that contains URLs."""
    
    print(f"\n🔗 Analyzing Skills with URLs")
    print("-" * 30)
    
    # Split by newlines
    lines = content.split('\n')
    print(f"📊 Total lines: {len(lines)}")
    
    url_lines = []
    for i, line in enumerate(lines):
        if '|https://lightcast.io/' in line:
            url_lines.append((i, line))
            print(f"🔗 Line {i+1}: {repr(line)}")
    
    print(f"📊 Lines with URLs: {len(url_lines)}")
    
    if url_lines:
        first_line = url_lines[0][1]
        print(f"\n🎯 First skill with URL:")
        print(f"Raw: {repr(first_line)}")
        
        # Test parsing
        if '|https://lightcast.io/' in first_line:
            parts = first_line.split('|', 1)
            skill_name = parts[0].strip()
            skill_url = parts[1].strip()
            print(f"✅ Parsed successfully:")
            print(f"   Skill name: {repr(skill_name)}")
            print(f"   Skill URL: {repr(skill_url)}")
            
            # Test the _add_cell_content_with_hyperlinks logic
            print(f"\n🧪 Testing document_styles.py logic:")
            print(f"1. Check if '•' in content: {'•' in content}")
            print(f"2. Check if '|https://lightcast.io/' in content: {'|https://lightcast.io/' in content}")
            print(f"3. Split by newlines: {len(content.split('\\n'))} lines")
            
            skills = content.split('\n')
            for j, skill in enumerate(skills[:3]):
                skill = skill.strip()
                if not skill:
                    print(f"   Skill {j+1}: EMPTY - would continue")
                    continue
                    
                print(f"   Skill {j+1}: {repr(skill)}")
                
                if '|https://lightcast.io/' in skill:
                    parts = skill.split('|', 1)
                    skill_name = parts[0].strip()
                    skill_url = parts[1].strip()
                    print(f"      -> Would create hyperlink: '{skill_name}' -> '{skill_url}'")
                    
                    if j == 0:
                        print(f"      -> 🎯 THIS IS THE FIRST SKILL - PROBLEMATIC IN WEBAPP")
                else:
                    print(f"      -> Would add as regular text")
        else:
            print(f"❌ Parsing failed")

def analyze_structured_table(table_data: Dict):
    """Analyze structured table data."""
    
    print(f"\n📊 Analyzing Structured Table")
    print("-" * 30)
    
    headers = table_data.get('headers', [])
    rows = table_data.get('rows', [])
    
    print(f"📋 Headers: {headers}")
    print(f"📊 Row count: {len(rows)}")
    
    # Look at first few rows
    for i, row in enumerate(rows[:3]):
        print(f"Row {i+1}: {row}")
        
        # Check for skills with URLs in each cell
        if isinstance(row, list):
            for j, cell in enumerate(row):
                if isinstance(cell, str) and '|https://lightcast.io/' in cell:
                    print(f"   🔗 Cell {j+1} has URLs: {repr(cell[:100])}")
                    analyze_skills_with_urls(cell)
        elif isinstance(row, dict):
            for key, cell in row.items():
                if isinstance(cell, str) and '|https://lightcast.io/' in cell:
                    print(f"   🔗 Cell '{key}' has URLs: {repr(cell[:100])}")
                    analyze_skills_with_urls(cell)

def test_working_format():
    """Test the format that works in the test environment."""
    
    print(f"\n✅ Testing Working Format (Reference)")
    print("=" * 60)
    
    # This is the format that works in test_comprehensive_table_fixes.py
    working_format = """• Strategic Communication|https://lightcast.io/open-skills/skills/ID1
• Data Analysis|https://lightcast.io/open-skills/skills/ID2  
• Project Management|https://lightcast.io/open-skills/skills/ID3"""
    
    print(f"📄 Working format:")
    print(f"Raw: {repr(working_format)}")
    
    # Test parsing
    skills = working_format.split('\n')
    print(f"📊 Skills after split: {len(skills)}")
    
    for i, skill in enumerate(skills):
        skill = skill.strip()
        print(f"Skill {i+1}: {repr(skill)}")
        
        if '|https://lightcast.io/' in skill:
            parts = skill.split('|', 1)
            skill_name = parts[0].strip()
            skill_url = parts[1].strip()
            print(f"   ✅ HYPERLINK: '{skill_name}' -> '{skill_url}'")
            
            if i == 0:
                print(f"   🎯 THIS IS THE FIRST SKILL")
        else:
            print(f"   ❌ No hyperlink detected")

def compare_formats():
    """Compare different possible formats to identify the issue."""
    
    print(f"\n🔬 Format Comparison")
    print("=" * 60)
    
    # Different possible formats
    formats = {
        "Working (test)": """• Strategic Communication|https://lightcast.io/open-skills/skills/ID1
• Data Analysis|https://lightcast.io/open-skills/skills/ID2  
• Project Management|https://lightcast.io/open-skills/skills/ID3""",
        
        "API format 1": """• Strategic Communication|https://lightcast.io/open-skills/skills/ID1\n• Data Analysis|https://lightcast.io/open-skills/skills/ID2\n• Project Management|https://lightcast.io/open-skills/skills/ID3""",
        
        "API format 2": """ • Strategic Communication|https://lightcast.io/open-skills/skills/ID1
 • Data Analysis|https://lightcast.io/open-skills/skills/ID2
 • Project Management|https://lightcast.io/open-skills/skills/ID3""",
        
        "API format 3": """• Strategic Communication|https://lightcast.io/open-skills/skills/ID1

• Data Analysis|https://lightcast.io/open-skills/skills/ID2

• Project Management|https://lightcast.io/open-skills/skills/ID3"""
    }
    
    for format_name, format_data in formats.items():
        print(f"\n📋 Testing: {format_name}")
        print(f"Raw: {repr(format_data)}")
        
        # Test hyperlink processing (document_styles.py logic)
        test_hyperlink_processing(format_data)

def test_hyperlink_processing(content: str):
    """Test hyperlink processing logic from document_styles.py."""
    
    # Check if content contains skills with URLs
    if '•' in content and '|https://lightcast.io/' in content:
        # Split by newlines to handle multiple skills
        skills = content.split('\n')
        print(f"   📊 Skills after split: {len(skills)}")
        
        for i, skill in enumerate(skills):
            skill = skill.strip()
            if not skill:
                print(f"   Skill {i+1}: EMPTY - SKIPPED")
                continue
                
            print(f"   Skill {i+1}: {repr(skill)}")
            
            # Check if this skill has an embedded URL
            if '|https://lightcast.io/' in skill:
                # Extract skill name and URL
                parts = skill.split('|', 1)
                skill_name = parts[0].strip()
                skill_url = parts[1].strip()
                
                print(f"      -> ✅ HYPERLINK: '{skill_name}' -> '{skill_url}'")
                
                if i == 0:
                    print(f"      -> 🎯 THIS IS THE FIRST SKILL - CHECK IF PROBLEMATIC")
            else:
                print(f"      -> ❌ Regular text: '{skill}'")
    else:
        print(f"   ❌ No skills with URLs detected")

def main():
    """Main function to run all tests."""
    
    print("🚨 NAB Skills Intelligence Platform - API Data Inspector")
    print("🎯 Goal: Find why first skill doesn't get hyperlink formatting")
    print("🔬 Testing real API endpoints vs working test data")
    print("")
    
    # Test reference working format first
    test_working_format()
    
    # Compare different possible formats
    compare_formats()
    
    # Test the real API endpoint
    print(f"\n" + "="*80)
    print("🌐 TESTING REAL API ENDPOINT")
    print(f"="*80)
    test_api_preview_endpoint()
    
    print(f"\n🎯 Summary:")
    print("1. Check if API data has different line break handling")
    print("2. Look for extra whitespace or formatting differences") 
    print("3. Compare first skill vs other skills in same cell")
    print("4. Verify paragraph initialization in document_styles.py")

if __name__ == "__main__":
    main() 