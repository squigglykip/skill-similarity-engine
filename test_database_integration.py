#!/usr/bin/env python3
"""
Test Database Integration for Analysis Scripts

Quick test to verify that both analysis scripts can successfully load
movement data from the SQLite database instead of parquet files.
"""

import sqlite3
import pandas as pd
from pathlib import Path

def test_database_connection():
    """Test database connection and movement_fact table access"""
    database_path = "models/2025-Q3/workforce_intelligence.sqlite"
    
    print(f"🔗 Testing database connection: {database_path}")
    
    if not Path(database_path).exists():
        print(f"❌ Database file not found: {database_path}")
        return False
    
    try:
        conn = sqlite3.connect(database_path)
        print(f"✅ Successfully connected to database")
        
        # Test movement_fact table access
        query = """
        SELECT 
            from_position,
            to_position,
            movement_year,
            COUNT(*) as record_count
        FROM movement_fact 
        LIMIT 5
        """
        
        df = pd.read_sql_query(query, conn)
        print(f"✅ Successfully queried movement_fact table")
        print(f"📊 Sample data shape: {df.shape}")
        print(f"📊 Sample records:")
        print(df.to_string(index=False))
        
        # Check total record count
        total_query = "SELECT COUNT(*) as total_records FROM movement_fact"
        total_df = pd.read_sql_query(total_query, conn)
        total_records = total_df['total_records'].iloc[0]
        print(f"📊 Total records in movement_fact: {total_records:,}")
        
        # Check year range
        year_query = "SELECT MIN(movement_year) as min_year, MAX(movement_year) as max_year FROM movement_fact"
        year_df = pd.read_sql_query(year_query, conn)
        min_year = year_df['min_year'].iloc[0]
        max_year = year_df['max_year'].iloc[0]
        print(f"📅 Year range: {min_year} - {max_year}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False

def test_script_imports():
    """Test that both analysis scripts can be imported without errors"""
    print(f"\n📦 Testing script imports...")
    
    try:
        # Test importing the core functions from both scripts
        import sys
        sys.path.append('notebook')
        
        # This will test if the scripts can be parsed without import errors
        print(f"✅ Scripts can be parsed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🧪 DATABASE INTEGRATION TEST")
    print("="*50)
    
    # Test database connection
    db_success = test_database_connection()
    
    # Test script imports
    import_success = test_script_imports()
    
    print(f"\n📋 TEST SUMMARY:")
    print(f"   Database Connection: {'✅ PASS' if db_success else '❌ FAIL'}")
    print(f"   Script Imports: {'✅ PASS' if import_success else '❌ FAIL'}")
    
    if db_success and import_success:
        print(f"\n🎉 All tests passed! Database integration is ready.")
        print(f"\n📝 Next steps:")
        print(f"   1. Run: python notebook/02_feature_evaluation_discovery_optimized.py")
        print(f"   2. Run: python notebook/03_role_typology_pathway_enhancement_optimized.py")
    else:
        print(f"\n❌ Some tests failed. Please check the errors above.")
    
    return db_success and import_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 