#!/usr/bin/env python3
"""
Test script for Current Role Context Generator with Structured Formatting
Tests the refactored generator to ensure it produces structured content metadata.
"""

import sys
import sqlite3
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the refactored generator
try:
    from src.skill_similarity_engine.webapp.whitepaper.src.current_role_context_generator import CurrentRoleContextGenerator
    from src.skill_similarity_engine.webapp.whitepaper.formatter import ContentFormatter
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def test_structured_current_role_context():
    """Test the structured approach for Current Role Context generation."""
    
    print("🚀 Testing Current Role Context with Structured Formatting")
    print("=" * 60)
    
    # Mock database connection for testing
    conn = sqlite3.connect(':memory:')
    
    # Create mock tables and data
    create_mock_data(conn)
    
    # Initialize generator
    generator = CurrentRoleContextGenerator(conn)
    
    # Test cases
    test_cases = [
        {
            'name': '📊 Test 1: Data Analyst Role',
            'job_id': 'JOB001',
            'include_deployment': False
        },
        {
            'name': '💻 Test 2: Software Engineer Role with Deployment',
            'job_id': 'JOB002', 
            'include_deployment': True
        },
        {
            'name': '🏦 Test 3: Risk Manager Role',
            'job_id': 'JOB003',
            'include_deployment': False
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}")
        print("-" * 50)
        
        try:
            # Generate content
            result = generator.generate(
                job_from=test_case['job_id'],
                include_organisational_deployment=test_case['include_deployment']
            )
            
            # Check that content has structured format
            if 'content' in result:
                validate_structured_content(result['content'], test_case['name'])
            else:
                print(f"❌ No content generated for {test_case['name']}")
                
        except Exception as e:
            print(f"❌ Error in {test_case['name']}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n✅ Key Benefits of Structured Current Role Context:")
    print("1. No hardcoded formatting keywords needed")
    print("2. Consistent formatting across all job types")
    print("3. Explicit content structure metadata")
    print("4. Easy to extend with new formatting patterns")
    print("5. Clean separation of content logic from presentation")

def create_mock_data(conn):
    """Create mock database tables and data for testing."""
    
    # Create jobs table
    conn.execute('''
        CREATE TABLE jobs (
            JobProfileID TEXT PRIMARY KEY,
            JobProfile TEXT,
            JobFunction TEXT,
            ManagementLevel TEXT,
            JobCategory TEXT
        )
    ''')
    
    # Create positions table
    conn.execute('''
        CREATE TABLE positions (
            "Employee Number" TEXT,
            JobProfileID TEXT,
            Division TEXT,
            Business_Unit TEXT,
            City TEXT
        )
    ''')
    
    # Create skills table
    conn.execute('''
        CREATE TABLE skills (
            Skill_ID TEXT PRIMARY KEY,
            SkillName TEXT,
            SkillCategory TEXT
        )
    ''')
    
    # Create job_skills table
    conn.execute('''
        CREATE TABLE job_skills (
            JobProfileID TEXT,
            Skill_ID TEXT
        )
    ''')
    
    # Insert mock job data
    mock_jobs = [
        ('JOB001', 'Data Analyst - Group 1', 'Analytics & Data Science', 'Group 1', 'Technical'),
        ('JOB002', 'Software Engineer - Group 2', 'Technology & Engineering', 'Group 2', 'Technical'),
        ('JOB003', 'Risk Manager - Group 3', 'Risk Management', 'Group 3', 'Management')
    ]
    
    conn.executemany('INSERT INTO jobs VALUES (?, ?, ?, ?, ?)', mock_jobs)
    
    # Insert mock position data
    mock_positions = [
        ('EMP001', 'JOB001', 'Technology', 'Data Analytics', 'Melbourne'),
        ('EMP002', 'JOB001', 'Technology', 'Data Analytics', 'Sydney'),
        ('EMP003', 'JOB002', 'Technology', 'Software Development', 'Melbourne'),
        ('EMP004', 'JOB002', 'Technology', 'Software Development', 'Sydney'),
        ('EMP005', 'JOB003', 'Risk', 'Credit Risk', 'Melbourne')
    ]
    
    conn.executemany('INSERT INTO positions VALUES (?, ?, ?, ?, ?)', mock_positions)
    
    # Insert mock skills data
    mock_skills = [
        ('SKILL001', 'Python Programming', 'Technical Skills'),
        ('SKILL002', 'Data Analysis', 'Technical Skills'),
        ('SKILL003', 'Risk Assessment', 'Business Skills'),
        ('SKILL004', 'Project Management', 'Business Skills'),
        ('SKILL005', 'SQL', 'Technical Skills')
    ]
    
    conn.executemany('INSERT INTO skills VALUES (?, ?, ?)', mock_skills)
    
    # Insert mock job-skills relationships
    mock_job_skills = [
        ('JOB001', 'SKILL001'),  # Data Analyst has Python
        ('JOB001', 'SKILL002'),  # Data Analyst has Data Analysis
        ('JOB001', 'SKILL005'),  # Data Analyst has SQL
        ('JOB002', 'SKILL001'),  # Software Engineer has Python
        ('JOB002', 'SKILL004'),  # Software Engineer has Project Management
        ('JOB003', 'SKILL003'),  # Risk Manager has Risk Assessment
        ('JOB003', 'SKILL004')   # Risk Manager has Project Management
    ]
    
    conn.executemany('INSERT INTO job_skills VALUES (?, ?)', mock_job_skills)
    
    conn.commit()

def validate_structured_content(content, test_name):
    """Validate that content sections use structured formatting."""
    
    sections_to_check = [
        'profile_overview',
        'core_competency_foundation', 
        'strategic_value_proposition',
        'strategic_intelligence_metrics'
    ]
    
    for section_key in sections_to_check:
        if section_key in content:
            section = content[section_key]
            
            # Check that section has title
            if 'title' in section:
                print(f"✅ {section_key}: Has title - '{section['title']}'")
            else:
                print(f"❌ {section_key}: Missing title")
                continue
            
            # Check content structure
            if 'content' in section:
                content_data = section['content']
                
                # Check if it's structured content (has formatting metadata)
                if isinstance(content_data, dict) and 'formatting' in content_data:
                    formatting = content_data['formatting']
                    content_type = formatting.get('content_type', 'unknown')
                    bold_labels = formatting.get('bold_labels', [])
                    
                    print(f"✅ {section_key}: Structured content type '{content_type}'")
                    if bold_labels:
                        print(f"   📝 Bold labels: {len(bold_labels)} defined")
                    
                    # Show a snippet of the text
                    text_snippet = content_data.get('text', '')[:100]
                    if text_snippet:
                        print(f"   📄 Content preview: {text_snippet}...")
                
                elif isinstance(content_data, str):
                    print(f"⚠️ {section_key}: Legacy string content (not structured)")
                    
                else:
                    print(f"❌ {section_key}: Unknown content format")
            else:
                print(f"❌ {section_key}: Missing content")
        else:
            print(f"❌ Missing section: {section_key}")
    
    print()

if __name__ == "__main__":
    test_structured_current_role_context() 