#!/usr/bin/env python3
"""
Test script to verify multiple job targets fix for ValidationService
"""

import sys
import os
import sqlite3
sys.path.append('src')

from skill_similarity_engine.webapp.career_analysis.services.validation_service import ValidationService

def test_multiple_job_validation():
    """Test that ValidationService properly validates multiple job targets."""
    
    print("🧪 Testing Multiple Job Targets Validation Fix")
    print("=" * 60)
    
    # Create database connection (use real database)
    db_path = "models/2025-Q2/business_context.sqlite"
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    
    # Initialize validation service
    validation_service = ValidationService(db)
    
    # Test case 1: Single job target (should work)
    print("\n📝 Test 1: Single job target")
    form_data_single = {
        'job_from': 'R0102.3',
        'analysis_mode': 'specific', 
        'job_to': 'R0355.0',
        'similarity_min': 40,
        'similarity_max': 90,
        'top_n': 3
    }
    
    is_valid, cleaned_data, errors = validation_service.validate_form_data(form_data_single)
    print(f"  Valid: {is_valid}")
    print(f"  job_to: {cleaned_data.get('job_to')}")
    print(f"  Errors: {errors}")
    
    # Test case 2: Multiple job targets (the fix)
    print("\n📝 Test 2: Multiple job targets (5 jobs)")
    form_data_multiple = {
        'job_from': 'R0102.3',
        'analysis_mode': 'specific',
        'job_to': 'R0355.0,R0424.2,R0464.2,R0096.0,R0001.1',  # 5 jobs
        'similarity_min': 40,
        'similarity_max': 90,
        'top_n': 3
    }
    
    is_valid, cleaned_data, errors = validation_service.validate_form_data(form_data_multiple)
    print(f"  Valid: {is_valid}")
    print(f"  job_to: {cleaned_data.get('job_to')}")
    print(f"  Target count: {len(cleaned_data.get('job_to', '').split(',')) if cleaned_data.get('job_to') else 0}")
    print(f"  Errors: {errors}")
    
    # Test case 3: Many job targets (should work without limit)
    print("\n📝 Test 3: Many job targets (6 jobs - should work)")
    form_data_many = {
        'job_from': 'R0102.3',
        'analysis_mode': 'specific',
        'job_to': 'R0355.0,R0424.2,R0464.2,R0096.0,R0064.1,R0001.0',  # 6 jobs with valid ones
        'similarity_min': 40,
        'similarity_max': 90,
        'top_n': 3
    }
    
    is_valid, cleaned_data, errors = validation_service.validate_form_data(form_data_many)
    print(f"  Valid: {is_valid}")
    print(f"  job_to: {cleaned_data.get('job_to')}")
    print(f"  Target count: {len(cleaned_data.get('job_to', '').split(',')) if cleaned_data.get('job_to') else 0}")
    print(f"  Errors: {errors}")
    
    # Test case 4: Invalid job in list (should filter out)
    print("\n📝 Test 4: Invalid job in list (should filter out invalid ones)")
    form_data_invalid = {
        'job_from': 'R0102.3',
        'analysis_mode': 'specific',
        'job_to': 'R0355.0,INVALID123,R0424.2',  # One invalid job
        'similarity_min': 40,
        'similarity_max': 90,
        'top_n': 3
    }
    
    is_valid, cleaned_data, errors = validation_service.validate_form_data(form_data_invalid)
    print(f"  Valid: {is_valid}")
    print(f"  job_to: {cleaned_data.get('job_to')}")
    print(f"  Valid jobs found: {len(cleaned_data.get('job_to', '').split(',')) if cleaned_data.get('job_to') else 0}")
    print(f"  Errors: {errors}")
    
    db.close()
    print("\n✅ Multiple job targets validation test completed!")
    return True

if __name__ == "__main__":
    test_multiple_job_validation() 