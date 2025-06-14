#!/usr/bin/env python3
"""
Test script to validate organizational filter behavior in career pathways.
This tests the newly fixed filtering logic.
"""

import sqlite3
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_organizational_filters():
    """Test that organizational filters work correctly - restrictive, not additive."""
    
    # Database path
    db_path = "models/2025-Q2/business_context.sqlite"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print("🧪 TESTING ORGANIZATIONAL FILTERS (FIXED LOGIC)")
    print("=" * 60)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Test job
    test_job = "R0276.5"  # Data Scientist - Director (from your debug output)
    division_filter = "Business & Private Banking"
    
    print(f"🎯 Test Setup:")
    print(f"   Starting Job: {test_job}")
    print(f"   Division Filter: {division_filter}")
    print()
    
    # Load the fixed SQL query
    with open("src/skill_similarity_engine/webapp/sql/career_pathways.sql", "r") as f:
        sql_content = f.read()
    
    # Extract the fixed query
    query_start = sql_content.find("-- query_name: get_career_tree_fast")
    query_end = sql_content.find("-- query_name:", query_start + 1)
    if query_end == -1:
        query_end = len(sql_content)
    
    query_block = sql_content[query_start:query_end]
    query_lines = query_block.split('\n')
    sql_query = '\n'.join([line for line in query_lines if not line.strip().startswith('--')])
    
    # Replace placeholder
    sql_query = sql_query.replace('{job_placeholders}', '?')
    
    # Test parameters
    params = [
        test_job,                    # Starting job
        0.0,                        # similarity_threshold (very low to see all matches)
        3,                          # max_depth  
        10,                         # max_results
        division_filter, division_filter,  # Division filter (check + value)
        '', '',                             # Business Unit filter (empty)
        '', '',                             # Location filter (empty)
        '', ''                              # Region filter (empty)
    ]
    
    print("🔍 Executing query with organizational filter...")
    
    try:
        results = conn.execute(sql_query, params).fetchall()
        
        # Analyze results
        level_counts = {}
        level_1_jobs = []
        
        for row in results:
            level = row['level']
            level_counts[level] = level_counts.get(level, 0) + 1
            
            if level == 1:
                level_1_jobs.append(row)
        
        print(f"📊 Results by level: {level_counts}")
        print(f"📋 Total Level 1 jobs found: {len(level_1_jobs)}")
        print()
        
        # Validate Level 1 jobs against the division filter
        print(f"🔍 Validating Level 1 jobs against Division filter '{division_filter}':")
        print("-" * 60)
        
        correct_matches = 0
        incorrect_matches = 0
        
        for job in level_1_jobs:
            job_id = str(job['id'])
            job_name = job['name']
            
            # Check if this job exists in the specified division
            division_check = conn.execute(
                "SELECT DISTINCT Division FROM positions WHERE JobProfileID = ?", 
                (job_id,)
            ).fetchall()
            
            divisions = [d['Division'] for d in division_check] if division_check else []
            matches_filter = division_filter in divisions
            
            if matches_filter:
                correct_matches += 1
                status = "✅ CORRECT"
            else:
                incorrect_matches += 1
                status = "❌ INCORRECT"
            
            print(f"{status}: {job_id} - {job_name[:50]}")
            print(f"         Divisions: {divisions}")
            print()
        
        # Summary
        print("=" * 60)
        print(f"📋 VALIDATION SUMMARY:")
        print(f"   ✅ Correct matches: {correct_matches}")
        print(f"   ❌ Incorrect matches: {incorrect_matches}")
        print(f"   📊 Success rate: {(correct_matches / len(level_1_jobs) * 100):.1f}%")
        
        if incorrect_matches == 0:
            print("   🎉 SUCCESS: All Level 1 jobs match the organizational filter!")
        else:
            print("   ⚠️  ISSUE: Some Level 1 jobs don't match the filter")
        
        print()
        
        # Test without filter for comparison
        print("🧪 COMPARISON: Running same query WITHOUT organizational filter...")
        
        params_no_filter = [
            test_job,        # Starting job
            0.0,            # similarity_threshold
            3,              # max_depth  
            10,             # max_results
            '', '',         # No division filter
            '', '',         # No business unit filter
            '', '',         # No location filter
            '', ''          # No region filter
        ]
        
        results_no_filter = conn.execute(sql_query, params_no_filter).fetchall()
        
        level_counts_no_filter = {}
        for row in results_no_filter:
            level = row['level']
            level_counts_no_filter[level] = level_counts_no_filter.get(level, 0) + 1
        
        print(f"📊 Results WITHOUT filter: {level_counts_no_filter}")
        print(f"📊 Results WITH filter:    {level_counts}")
        
        # Check if filtering worked
        level_1_no_filter = level_counts_no_filter.get(1, 0)
        level_1_with_filter = level_counts.get(1, 0)
        
        if level_1_with_filter < level_1_no_filter:
            print(f"✅ Filter is RESTRICTIVE: Reduced Level 1 jobs from {level_1_no_filter} to {level_1_with_filter}")
        elif level_1_with_filter == level_1_no_filter:
            print(f"⚠️  Filter has NO EFFECT: Level 1 jobs remain {level_1_no_filter}")
        else:
            print(f"❌ Filter is ADDITIVE: Increased Level 1 jobs from {level_1_no_filter} to {level_1_with_filter}")
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    test_organizational_filters() 