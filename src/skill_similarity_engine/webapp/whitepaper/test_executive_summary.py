"""
Test script for Executive Summary Generation
Tests the integration of YAML templates, SQL queries, and Python generation logic.
"""

import sqlite3
import sys
from pathlib import Path

# Add the parent directory to path so we can import the generator
sys.path.append(str(Path(__file__).parent))

from executive_summary_generator import ExecutiveSummaryGenerator

def test_executive_summary_generation():
    """Test the executive summary generation with a sample job."""
    
    print("🧪 Testing Executive Summary Generation")
    print("=" * 50)
    
    # Connect to database (you'll need to update this path)
    db_path = Path(__file__).parent.parent.parent.parent.parent / "models" / "2025-Q2" / "business_context.sqlite"
    
    if not db_path.exists():
        print(f"⚠️ Database not found at: {db_path}")
        print("Please update the db_path in the test script to point to your database.")
        return
    
    try:
        # Connect to database
        print(f"📊 Connecting to database: {db_path}")
        db = sqlite3.connect(str(db_path))
        db.row_factory = sqlite3.Row  # Enable column access by name
        
        # Initialize generator
        print("🏗️ Initializing Executive Summary Generator...")
        generator = ExecutiveSummaryGenerator(db)
        
        # Test with a sample job (you can change this)
        test_job_id = "R0041.1"  # Data Scientist Associate from gold standard
        print(f"🎯 Generating executive summary for job: {test_job_id}")
        
        # Generate executive summary
        result = generator.generate(test_job_id)
        
        # Display results
        print("\n" + "=" * 50)
        print("📄 GENERATED EXECUTIVE SUMMARY")
        print("=" * 50)
        
        content = result.get('content', {})
        
        # Strategic Context
        if 'strategic_context' in content:
            print(f"\n### {content['strategic_context']['title']}")
            print(content['strategic_context']['content'])
        
        # Key Findings
        if 'key_findings' in content:
            print(f"\n### {content['key_findings']['title']}")
            print(content['key_findings']['content'])
        
        # Primary Recommendations
        if 'primary_recommendations' in content:
            print(f"\n### {content['primary_recommendations']['title']}")
            print(content['primary_recommendations']['content'])
        
        # Data-Driven Classification
        if 'data_driven_classification' in content:
            print(f"\n### Data-Driven Classification")
            print(content['data_driven_classification']['content'])
        
        # Confidence Assessment
        if 'confidence_assessment' in content:
            print(f"\n### {content['confidence_assessment']['title']}")
            print(content['confidence_assessment']['content'])
        
        # Show template variables for debugging
        print("\n" + "=" * 50)
        print("🔧 TEMPLATE VARIABLES (Debug Info)")
        print("=" * 50)
        
        variables = result.get('template_variables', {})
        key_variables = [
            'source_job_title', 'total_job_count', 'pathway_count', 
            'min_similarity', 'max_similarity', 'confidence_level',
            'opportunity_descriptor', 'percentile_descriptor'
        ]
        
        for var in key_variables:
            if var in variables:
                print(f"{var}: {variables[var]}")
        
        # Show top pathways
        top_pathways = variables.get('top_pathways', [])
        if top_pathways:
            print(f"\nTop {len(top_pathways)} pathways:")
            for i, pathway in enumerate(top_pathways, 1):
                print(f"  {i}. {pathway['target_job_title']} ({pathway['similarity_score']}%)")
                print(f"     Move Type: {pathway['move_type']}")
        
        # Show references
        print("\n" + "=" * 50)
        print("📚 REFERENCES")
        print("=" * 50)
        
        references = result.get('references', {})
        key_refs = ['1', '2', '13', '14', '15', '16']
        for ref in key_refs:
            if ref in references:
                print(f"({ref}) {references[ref]}")
        
        print("\n✅ Executive Summary generation completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'db' in locals():
            db.close()

def test_template_loading():
    """Test that the YAML template loads correctly."""
    
    print("\n🧪 Testing YAML Template Loading")
    print("=" * 50)
    
    try:
        # Test template loading without database
        generator = ExecutiveSummaryGenerator(None)
        
        if generator.template_data:
            print("✅ YAML template loaded successfully!")
            
            # Check key sections exist
            exec_summary = generator.template_data.get('executive_summary', {})
            required_sections = [
                'strategic_context', 'key_findings', 'primary_recommendations',
                'confidence_assessment'
            ]
            
            for section in required_sections:
                if section in exec_summary:
                    print(f"✅ Section '{section}' found")
                else:
                    print(f"❌ Section '{section}' missing")
            
            # Check references exist
            references = generator.template_data.get('references', {})
            if references:
                print(f"✅ References section found with {len(references)} references")
            else:
                print("❌ References section missing")
        
        else:
            print("❌ YAML template failed to load")
    
    except Exception as e:
        print(f"❌ Error testing template: {e}")

if __name__ == "__main__":
    # Test template loading first
    test_template_loading()
    
    # Then test full generation
    test_executive_summary_generation() 