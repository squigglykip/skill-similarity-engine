#!/usr/bin/env python3
"""
Table Debug Test - Core Competency Foundation & Strategic Intelligence Metrics
Debug why these tables aren't being formatted properly in the Word document
"""

import sys
import os
import sqlite3
sys.path.append('src')

from skill_similarity_engine.webapp.career_analysis.services.career_analysis_service import CareerAnalysisService
from skill_similarity_engine.webapp.career_analysis.config.document_styles import DocumentStyles

def test_table_content():
    """Test what content is being generated for the problematic tables"""
    
    print("🧪 NAB Skills Intelligence Platform - Table Debug Test")
    print("🎯 Goal: Debug Core Competency Foundation & Strategic Intelligence Metrics tables")
    print("=" * 80)
    
    # Initialize database connection (same as webapp)
    db_path = "models/2025-Q2/business_context.sqlite"
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return
    
    try:
        db_connection = sqlite3.connect(db_path)
        service = CareerAnalysisService(db_connection)
        print("✅ CareerAnalysisService initialized with database connection")
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        return
    
    # Test data
    test_job = "R0102.3"
    form_data = {
        'job_from': test_job,
        'analysis_mode': 'top_matches',
        'job_to': None,
        'scenario': 'discovery',
        'audience': 'executive',
        'division_from': None,
        'division_to': None,
        'top_n': 3,
        'similarity_min': 40,
        'similarity_max': 90,
        'tie_breaking_options': {
            'same_function_priority': False,
            'career_progression_priority': False,
            'minimal_level_jump': False,
            'skills_overlap_detail': False
        },
        'output_format': 'word'
    }
    
    print(f"🔍 Testing with job: {test_job}")
    print()
    
    try:
        # Generate the document analysis
        analysis_data = service.generate_analysis(
            job_from=form_data['job_from'],
            analysis_mode=form_data['analysis_mode'], 
            output_mode='document',
            job_to=form_data['job_to'],
            similarity_min=form_data['similarity_min'],
            similarity_max=form_data['similarity_max'],
            top_n=form_data['top_n'],
            tie_breaking_options=form_data['tie_breaking_options']
        )
        
        # Check the analysis data structure
        print(f"📋 Analysis data structure:")
        print(f"  Top-level keys: {list(analysis_data.keys())}")
        
        # Check if there's a sections dict
        sections = analysis_data.get('sections', analysis_data)
        current_role_context = sections.get('current_role_context', {})
        
        if not current_role_context:
            print("❌ No current_role_context found in analysis data")
            print(f"Available sections: {list(sections.keys())}")
            return
        
        # Check if current_role_context has subsections
        subsections = current_role_context.get('subsections', current_role_context)
        print("📋 Current Role Context subsections found:")
        for key in subsections.keys():
            print(f"  • {key}")
        print()
        
        # Test Core Competency Foundation
        core_competency = subsections.get('core_competency_foundation', {})
        if core_competency:
            print("🔍 CORE COMPETENCY FOUNDATION")
            print("-" * 40)
            print(f"Title: {core_competency.get('title', 'No title')}")
            content = core_competency.get('content', '')
            print(f"Content length: {len(content)} characters")
            print("Content preview:")
            print(repr(content[:200]) + "..." if len(content) > 200 else repr(content))
            print()
            
            # Test table detection
            styles = DocumentStyles()
            print("🧪 Testing table detection on Core Competency content...")
            has_tables = '|' in content and content.count('|') >= 2
            print(f"Contains pipes: {'|' in content}")
            print(f"Pipe count: {content.count('|')}")
            print(f"Looks like table: {has_tables}")
            
            if has_tables:
                lines = content.strip().split('\n')
                print(f"Content lines: {len(lines)}")
                for i, line in enumerate(lines[:5]):  # Show first 5 lines
                    print(f"  Line {i}: {repr(line)}")
            print()
        else:
            print("❌ No core_competency_foundation found")
            print()
        
        # Test Strategic Intelligence Metrics
        strategic_metrics = subsections.get('strategic_intelligence_metrics', {})
        if strategic_metrics:
            print("🔍 STRATEGIC INTELLIGENCE METRICS")
            print("-" * 40)
            print(f"Title: {strategic_metrics.get('title', 'No title')}")
            content = strategic_metrics.get('content', '')
            print(f"Content length: {len(content)} characters")
            print("Content preview:")
            print(repr(content[:200]) + "..." if len(content) > 200 else repr(content))
            print()
            
            # Test table detection
            print("🧪 Testing table detection on Strategic Metrics content...")
            has_tables = '|' in content and content.count('|') >= 2
            print(f"Contains pipes: {'|' in content}")
            print(f"Pipe count: {content.count('|')}")
            print(f"Looks like table: {has_tables}")
            
            if has_tables:
                lines = content.strip().split('\n')
                print(f"Content lines: {len(lines)}")
                for i, line in enumerate(lines[:5]):  # Show first 5 lines
                    print(f"  Line {i}: {repr(line)}")
            print()
        else:
            print("❌ No strategic_intelligence_metrics found")
            print()
        
        # Test the table detection logic directly
        print("🔧 TESTING TABLE DETECTION LOGIC")
        print("-" * 40)
        
        test_contents = []
        if core_competency.get('content'):
            test_contents.append(("Core Competency Foundation", core_competency['content']))
        if strategic_metrics.get('content'):
            test_contents.append(("Strategic Intelligence Metrics", strategic_metrics['content']))
        
        styles = DocumentStyles()
        for name, content in test_contents:
            print(f"Testing {name}:")
            
            # Test the NEW improved table detection logic
            if '|' in content:
                lines = content.strip().split('\n')
                lines = [line.strip() for line in lines if line.strip()]
                
                # Use the new scanning logic
                table_start_idx = -1
                table_headers = []
                
                for i, line in enumerate(lines):
                    if '|' in line:
                        potential_headers = [h.strip() for h in line.split('|') if h.strip()]
                        
                        if len(potential_headers) >= 2:
                            # Check for header patterns
                            header_indicators = [
                                'skill type', 'skill count', 'all skills',  # Core Competency Foundation
                                'metric', 'score', 'assessment', 'strategic significance',  # Strategic Intelligence Metrics
                                'category', 'current', 'new', 'gap',  # Skills tables
                                'pathway', 'similarity', 'opportunity'  # Pathway tables
                            ]
                            
                            line_lower = line.lower()
                            matches = [indicator for indicator in header_indicators if indicator in line_lower]
                            
                            if matches:
                                table_start_idx = i
                                table_headers = potential_headers
                                print(f"  ✅ Found table headers at line {i}: {potential_headers}")
                                print(f"  ✅ Matched indicators: {matches}")
                                break
                            
                            # Also check if next line is a separator
                            if i + 1 < len(lines):
                                next_line = lines[i + 1]
                                if set(next_line.replace('|', '').replace('-', '').replace(' ', '')) == set():
                                    table_start_idx = i
                                    table_headers = potential_headers
                                    print(f"  ✅ Found table headers at line {i} (separator detected): {potential_headers}")
                                    break
                
                if table_start_idx == -1:
                    print(f"  ❌ {name} no table headers found")
                    # Show what lines contain pipes
                    for i, line in enumerate(lines):
                        if '|' in line:
                            print(f"    Line {i} with pipes: {repr(line)}")
                else:
                    print(f"  ✅ {name} should be detected as a table starting at line {table_start_idx}")
            else:
                print(f"  ❌ {name} has no pipes in content")
            print()
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_table_content() 