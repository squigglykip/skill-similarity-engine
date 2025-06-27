"""
Test Service Layer

Simple test script to verify the new service layer integrates correctly with
the existing generators and produces the expected output.
"""

import sqlite3
import sys
from pathlib import Path

# Add the services path to sys.path for imports
services_path = Path(__file__).parent / 'services'
sys.path.insert(0, str(services_path))

def test_service_layer():
    """Test the service layer with a simple example."""
    
    # Set up database connection
    db_path = Path(__file__).parent.parent.parent.parent.parent / 'models' / '2025-Q2' / 'business_context.sqlite'
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        print("Please ensure the database path is correct")
        return False
    
    try:
        # Connect to database
        print(f"🔌 Connecting to database: {db_path}")
        db = sqlite3.connect(str(db_path))
        db.row_factory = sqlite3.Row
        
        # Test job validation
        print("\n📋 Testing ValidationService...")
        from validation_service import ValidationService
        
        validation_service = ValidationService(db)
        
        # Test valid job
        test_form_data = {
            'job_from': 'R0102.3',
            'analysis_mode': 'top_matches',
            'similarity_min': 40,
            'similarity_max': 90,
            'top_n': 3
        }
        
        is_valid, cleaned_data, errors = validation_service.validate_form_data(test_form_data)
        
        if is_valid:
            print("✅ Validation passed")
            print(f"   Cleaned data: {cleaned_data}")
        else:
            print(f"❌ Validation failed: {errors}")
            return False
        
        # Test PreviewService
        print("\n🎯 Testing PreviewService...")
        from preview_service import PreviewService
        
        preview_service = PreviewService(db)
        result = preview_service.generate_preview(test_form_data)
        
        if result['success']:
            print("✅ Preview generation successful")
            print(f"   Generated {len(result['content'])} sections:")
            for section_key in result['content'].keys():
                print(f"     - {section_key}")
            
            # Show a sample of content structure
            if 'executive_summary' in result['content']:
                exec_summary = result['content']['executive_summary']
                print(f"   Executive Summary structure:")
                print(f"     - Title: {exec_summary.get('title', 'N/A')}")
                print(f"     - Subsections: {len(exec_summary.get('subsections', {}))}")
                
        else:
            print(f"❌ Preview generation failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Test CareerAnalysisService directly
        print("\n🚀 Testing CareerAnalysisService...")
        from career_analysis_service import CareerAnalysisService
        
        analysis_service = CareerAnalysisService(db)
        analysis_result = analysis_service.generate_analysis(
            job_from='R0102.3',
            analysis_mode='top_matches',
            output_mode='web',
            similarity_min=40,
            similarity_max=90,
            top_n=3
        )
        
        if analysis_result['success']:
            print("✅ Analysis service successful")
            print(f"   Output mode: {analysis_result['output_mode']}")
            print(f"   Metadata: {analysis_result['metadata']['source_job_title']}")
        else:
            print(f"❌ Analysis service failed: {analysis_result.get('error', 'Unknown error')}")
            return False
        
        print("\n🎉 All service layer tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("This is expected if generators are missing dependencies")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("🧪 Testing Career Analysis Service Layer...")
    success = test_service_layer()
    sys.exit(0 if success else 1) 