#!/usr/bin/env python3
"""
Debug script to investigate hyperlink formatting issues in NAB Skills Intelligence Platform.

This script compares:
1. How test data (working) formats skills with URLs
2. How API data (problematic) formats skills with URLs
3. The differences in hyperlink processing

Focus: Why first skill in each cell doesn't get hyperlink formatting in webapp.
"""

import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from docx import Document
    from docx.shared import Pt, RGBColor
except ImportError:
    print("Warning: python-docx not available")

def test_skills_data_formats():
    """Test different skills data formats to identify the hyperlink issue."""
    
    print("🔍 Debug: Skills Data Format Testing")
    print("=" * 60)
    
    # Test data format 1: Working test format
    test_working_format = """• Strategic Communication|https://lightcast.io/open-skills/skills/ID1
• Data Analysis|https://lightcast.io/open-skills/skills/ID2  
• Project Management|https://lightcast.io/open-skills/skills/ID3"""
    
    # Test data format 2: Possible API format with different line breaks
    api_format_1 = """• Strategic Communication|https://lightcast.io/open-skills/skills/ID1\n• Data Analysis|https://lightcast.io/open-skills/skills/ID2\n• Project Management|https://lightcast.io/open-skills/skills/ID3"""
    
    # Test data format 3: Possible API format with extra whitespace
    api_format_2 = """ • Strategic Communication|https://lightcast.io/open-skills/skills/ID1
 • Data Analysis|https://lightcast.io/open-skills/skills/ID2
 • Project Management|https://lightcast.io/open-skills/skills/ID3"""
    
    formats = [
        ("Working Test Format", test_working_format),
        ("API Format 1 (\\n)", api_format_1),
        ("API Format 2 (whitespace)", api_format_2)
    ]
    
    for format_name, format_data in formats:
        print(f"\n📋 Testing: {format_name}")
        print(f"Raw data: {repr(format_data)}")
        
        # Test skills parsing
        skills = format_data.split('\n')
        print(f"Skills count: {len(skills)}")
        
        for i, skill in enumerate(skills):
            skill = skill.strip()
            print(f"  Skill {i+1}: {repr(skill)}")
            
            # Check hyperlink detection
            if '|https://lightcast.io/' in skill:
                parts = skill.split('|', 1)
                skill_name = parts[0].strip()
                skill_url = parts[1].strip()
                print(f"    ✅ Hyperlink detected: '{skill_name}' -> '{skill_url}'")
            else:
                print(f"    ❌ No hyperlink detected")
    
    print("\n" + "=" * 60)

def test_cell_content_processing():
    """Test how cell content gets processed for hyperlinks."""
    
    print("\n🧪 Debug: Cell Content Processing")
    print("=" * 60)
    
    try:
        # Import the document styles
        from skill_similarity_engine.webapp.career_analysis.config.document_styles import DocumentStyles
        
        # Create a test document
        doc = Document()
        styles = DocumentStyles()
        
        # Test data
        test_cell_content = """• Strategic Communication|https://lightcast.io/open-skills/skills/ID1
• Data Analysis|https://lightcast.io/open-skills/skills/ID2
• Project Management|https://lightcast.io/open-skills/skills/ID3"""
        
        print(f"📋 Test cell content:")
        print(f"Raw: {repr(test_cell_content)}")
        
        # Test the processing
        print(f"\n🔍 Processing steps:")
        
        # Check if content contains skills with URLs
        has_skills_with_urls = '•' in test_cell_content and '|https://lightcast.io/' in test_cell_content
        print(f"1. Has skills with URLs: {has_skills_with_urls}")
        
        if has_skills_with_urls:
            # Split by newlines to handle multiple skills
            skills = test_cell_content.split('\n')
            print(f"2. Skills after split: {len(skills)} items")
            
            for i, skill in enumerate(skills):
                skill = skill.strip()
                print(f"   Skill {i+1}: {repr(skill)}")
                
                if not skill:
                    print(f"      -> Empty skill, skipping")
                    continue
                    
                # Check if this skill has an embedded URL
                if '|https://lightcast.io/' in skill:
                    # Extract skill name and URL
                    parts = skill.split('|', 1)
                    skill_name = parts[0].strip()
                    skill_url = parts[1].strip()
                    
                    print(f"      -> ✅ HYPERLINK: '{skill_name}' -> '{skill_url}'")
                    
                    if i == 0:
                        print(f"      -> ⚠️  THIS IS THE FIRST SKILL - PROBLEMATIC?")
                else:
                    print(f"      -> ❌ Regular text: '{skill}'")
        
    except ImportError as e:
        print(f"❌ Could not import DocumentStyles: {e}")
        print("This suggests we're not in the right environment")
    
    print("\n" + "=" * 60)

def test_api_call_simulation():
    """Simulate an API call to see the actual data format."""
    
    print("\n🌐 Debug: API Call Simulation")
    print("=" * 60)
    
    try:
        # Try to import the services to test API data format
        from skill_similarity_engine.webapp.career_analysis.services.career_analysis_service import CareerAnalysisService
        
        print("📡 Attempting to initialize CareerAnalysisService...")
        service = CareerAnalysisService()
        print("✅ Service initialized successfully")
        
        # Try to get data that would contain skills
        print("🔍 Looking for available methods...")
        methods = [method for method in dir(service) if not method.startswith('_')]
        print(f"Available methods: {methods}")
        
        # Let's see if we can find a method that returns skills data
        if hasattr(service, 'get_job_data'):
            print("📋 Testing get_job_data method...")
            try:
                job_data = service.get_job_data('R0102.3')
                print(f"Job data keys: {list(job_data.keys()) if isinstance(job_data, dict) else 'Not a dict'}")
            except Exception as e:
                print(f"❌ Error calling get_job_data: {e}")
        
    except ImportError as e:
        print(f"❌ Could not import CareerAnalysisService: {e}")
    except Exception as e:
        print(f"❌ Error with service: {e}")
    
    print("\n" + "=" * 60)

def main():
    """Main debug function."""
    print("🚨 NAB Skills Intelligence Platform - Hyperlink Debug")
    print("🎯 Investigating: Why first skill in each cell doesn't get hyperlink formatting")
    print("🔬 Comparing: Test data (working) vs API data (problematic)")
    print("")
    
    # Run debug tests
    test_skills_data_formats()
    test_cell_content_processing()
    test_api_call_simulation()
    
    print("\n🎯 Summary:")
    print("- Look for differences in line break handling")
    print("- Check if first skill processing has paragraph issues")
    print("- Compare test vs API data formats")
    print("- Verify hyperlink method is being called correctly")

if __name__ == "__main__":
    main() 