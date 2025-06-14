#!/usr/bin/env python3
"""
Focused test script for combined organizational filter fix.
Tests that combined filters require ALL criteria to be met in the SAME position record.
"""

import sqlite3
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_combined_filter_fix():
    """Test that the combined filter fix ensures all criteria apply to the same position."""
    
    # Database path
    db_path = "models/2025-Q2/business_context.sqlite"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print("🧪 TESTING COMBINED FILTER FIX")
    print("=" * 50)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Test job and filters that were failing
    test_job = "R0276.5"
    division_filter = "Business & Private Banking"
    business_unit_filter = "Corporate Banking"
    
    print(f"🎯 Test Setup:")
    print(f"   Starting Job: {test_job}")
    print(f"   Division Filter: {division_filter}")
    print(f"   Business Unit Filter: {business_unit_filter}")
    print()
    
    # Load the fixed SQL query
    with open("src/skill_similarity_engine/webapp/sql/career_pathways.sql", "r") as f:
        sql_content = f.read()
    
    # Extract the query
    query_start = sql_content.find("-- query_name: get_career_tree_fast")
    query_end = sql_content.find("-- query_name:", query_start + 1)
    if query_end == -1:
        query_end = len(sql_content)
    
    query_block = sql_content[query_start:query_end]
    query_lines = query_block.split('\n')
    sql_query = '\n'.join([line for line in query_lines if not line.strip().startswith('--')])
    sql_query = sql_query.replace('{job_placeholders}', '?')
    
    # Test the combined filter
    print("🔍 Testing FIXED combined filter logic...")
    
    params = [
        test_job, 0.0, 3, 10,
        division_filter, division_filter,
        business_unit_filter, business_unit_filter,
        '', '',  # No location filter
        '', ''   # No region filter
    ]
    
    try:
        results = conn.execute(sql_query, params).fetchall()
        
        # Analyze results
        level_1_jobs = [row for row in results if row['level'] == 1]
        
        print(f"📊 Level 1 jobs found: {len(level_1_jobs)}")
        print()
        
        # Validate each Level 1 job
        validation_errors = 0
        
        for job in level_1_jobs:
            job_id = str(job['id'])
            job_name = job['name']
            
            print(f"🔍 Validating {job_id}: {job_name}")
            
            # Check if this job has ANY position that matches BOTH criteria
            matching_positions = conn.execute("""
                SELECT Division, "Business_Unit", Location, Rg as Region
                FROM positions 
                WHERE JobProfileID = ? 
                  AND Division = ? 
                  AND "Business_Unit" = ?
            """, (job_id, division_filter, business_unit_filter)).fetchall()
            
            if matching_positions:
                print(f"   ✅ VALID: Has {len(matching_positions)} position(s) matching both criteria")
                for pos in matching_positions:
                    print(f"      - Division: {pos['Division']}, Business Unit: {pos['Business_Unit']}")
            else:
                validation_errors += 1
                print(f"   ❌ INVALID: No single position matches both criteria")
                
                # Show what positions this job actually has
                all_positions = conn.execute("""
                    SELECT DISTINCT Division, "Business_Unit"
                    FROM positions 
                    WHERE JobProfileID = ?
                """, (job_id,)).fetchall()
                
                print(f"      Available positions:")
                for pos in all_positions:
                    div_match = "✅" if pos['Division'] == division_filter else "❌"
                    bu_match = "✅" if pos['Business_Unit'] == business_unit_filter else "❌"
                    print(f"      {div_match} {bu_match} Division: {pos['Division']}, Business Unit: {pos['Business_Unit']}")
            
            print()
        
        # Summary
        print("=" * 50)
        print(f"📋 VALIDATION SUMMARY:")
        print(f"   ✅ Valid jobs: {len(level_1_jobs) - validation_errors}")
        print(f"   ❌ Invalid jobs: {validation_errors}")
        
        if validation_errors == 0:
            print(f"   🎉 SUCCESS: All Level 1 jobs have positions matching BOTH criteria!")
        else:
            print(f"   ⚠️  ISSUE: {validation_errors} jobs don't have any single position matching both criteria")
        
        # Compare with the previous logic (simulate the old behavior)
        print()
        print("🔍 Comparison with OLD logic (separate queries)...")
        
        # Old logic simulation: separate IN clauses
        old_logic_jobs = []
        
        # Jobs that match division filter
        division_jobs = set()
        div_results = conn.execute("""
            SELECT DISTINCT JobProfileID FROM positions WHERE Division = ?
        """, (division_filter,)).fetchall()
        division_jobs = {row['JobProfileID'] for row in div_results}
        
        # Jobs that match business unit filter  
        bu_jobs = set()
        bu_results = conn.execute("""
            SELECT DISTINCT JobProfileID FROM positions WHERE "Business_Unit" = ?
        """, (business_unit_filter,)).fetchall()
        bu_jobs = {row['JobProfileID'] for row in bu_results}
        
        # Old logic: intersection (jobs in BOTH sets, but not necessarily same position)
        old_logic_intersection = division_jobs & bu_jobs
        
        print(f"📊 OLD logic would include: {len(old_logic_intersection)} jobs")
        print(f"📊 NEW logic includes: {len(level_1_jobs)} jobs")
        
        if len(level_1_jobs) <= len(old_logic_intersection):
            print("✅ NEW logic is more restrictive (correct!)")
        else:
            print("❌ NEW logic is less restrictive (shouldn't happen)")
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    test_combined_filter_fix() 