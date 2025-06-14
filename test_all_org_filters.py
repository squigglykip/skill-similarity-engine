#!/usr/bin/env python3
"""
Comprehensive test script for all organizational filters.
Tests Division, Business Unit, Location, and Region filters individually and in combination.
"""

import sqlite3
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_all_organizational_filters():
    """Test all organizational filters individually and in combination."""
    
    # Database path
    db_path = "models/2025-Q2/business_context.sqlite"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print("🧪 COMPREHENSIVE ORGANIZATIONAL FILTER TESTING")
    print("=" * 70)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Test job
    test_job = "R0276.5"  # Data Scientist - Director
    
    print(f"🎯 Test Setup: Starting Job = {test_job}")
    print()
    
    # Load the SQL query
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
    
    # First, check what organizational data exists for Level 1 jobs with no filters
    print("🔍 STEP 1: Analyzing available organizational data for Level 1 jobs")
    print("-" * 70)
    
    # Get Level 1 jobs without any filters
    params_no_filter = [test_job, 0.0, 3, 10, '', '', '', '', '', '', '', '']
    results_no_filter = conn.execute(sql_query, params_no_filter).fetchall()
    level_1_jobs_no_filter = [row for row in results_no_filter if row['level'] == 1]
    
    print(f"📊 Found {len(level_1_jobs_no_filter)} Level 1 jobs without filters")
    print()
    
    # Analyze organizational distribution
    all_divisions = set()
    all_business_units = set()
    all_locations = set()
    all_regions = set()
    
    for job in level_1_jobs_no_filter:
        job_id = str(job['id'])
        org_data = conn.execute("""
            SELECT DISTINCT Division, "Business_Unit", Location, Rg as Region 
            FROM positions 
            WHERE JobProfileID = ?
        """, (job_id,)).fetchall()
        
        for row in org_data:
            if row['Division']: all_divisions.add(row['Division'])
            if row['Business_Unit']: all_business_units.add(row['Business_Unit'])
            if row['Location']: all_locations.add(row['Location'])
            if row['Region']: all_regions.add(row['Region'])
    
    print(f"📋 Available organizational values:")
    print(f"   Divisions ({len(all_divisions)}): {sorted(list(all_divisions))}")
    print(f"   Business Units ({len(all_business_units)}): {sorted(list(all_business_units))}")
    print(f"   Locations ({len(all_locations)}): {sorted(list(all_locations))}")
    print(f"   Regions ({len(all_regions)}): {sorted(list(all_regions))}")
    print()
    
    # Test individual filters
    test_cases = [
        {
            'name': 'No Filters (Baseline)',
            'filters': {'division': '', 'business_unit': '', 'location': '', 'region': ''},
            'expected': 'All Level 1 jobs'
        },
        {
            'name': 'Division Filter Only',
            'filters': {'division': 'Business & Private Banking', 'business_unit': '', 'location': '', 'region': ''},
            'expected': 'Jobs in Business & Private Banking division'
        },
        {
            'name': 'Business Unit Filter Only',
            'filters': {'division': '', 'business_unit': 'Corporate Banking', 'location': '', 'region': ''},
            'expected': 'Jobs in Corporate Banking business unit'
        },
        {
            'name': 'Location Filter Only',
            'filters': {'division': '', 'business_unit': '', 'location': 'Brisbane City', 'region': ''},
            'expected': 'Jobs in Brisbane City location'
        },
        {
            'name': 'Region Filter Only',
            'filters': {'division': '', 'business_unit': '', 'location': '', 'region': 'VIC'},
            'expected': 'Jobs in VIC region'
        },
        {
            'name': 'Division + Business Unit',
            'filters': {'division': 'Business & Private Banking', 'business_unit': 'Corporate Banking', 'location': '', 'region': ''},
            'expected': 'Jobs in both Division AND Business Unit'
        },
        {
            'name': 'All Filters Combined',
            'filters': {'division': 'Business & Private Banking', 'business_unit': 'Corporate Banking', 'location': 'Brisbane City', 'region': 'QLD'},
            'expected': 'Jobs matching ALL criteria'
        }
    ]
    
    print("🧪 STEP 2: Testing individual and combined filters")
    print("=" * 70)
    
    results_summary = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🔬 Test {i}: {test_case['name']}")
        print(f"   Expected: {test_case['expected']}")
        
        filters = test_case['filters']
        params = [
            test_job, 0.0, 3, 10,
            filters['division'], filters['division'],
            filters['business_unit'], filters['business_unit'],
            filters['location'], filters['location'],
            filters['region'], filters['region']
        ]
        
        try:
            results = conn.execute(sql_query, params).fetchall()
            level_counts = {}
            level_1_jobs = []
            
            for row in results:
                level = row['level']
                level_counts[level] = level_counts.get(level, 0) + 1
                if level == 1:
                    level_1_jobs.append(row)
            
            print(f"   📊 Results: {level_counts}")
            print(f"   📋 Level 1 jobs: {len(level_1_jobs)}")
            
            # Validate Level 1 jobs against the applied filters
            validation_errors = 0
            
            for job in level_1_jobs:
                job_id = str(job['id'])
                org_data = conn.execute("""
                    SELECT DISTINCT Division, "Business_Unit", Location, Rg as Region 
                    FROM positions 
                    WHERE JobProfileID = ?
                """, (job_id,)).fetchall()
                
                # Check each filter
                for row in org_data:
                    passes_division = not filters['division'] or row['Division'] == filters['division']
                    passes_business_unit = not filters['business_unit'] or row['Business_Unit'] == filters['business_unit']
                    passes_location = not filters['location'] or row['Location'] == filters['location']
                    passes_region = not filters['region'] or row['Region'] == filters['region']
                    
                    if passes_division and passes_business_unit and passes_location and passes_region:
                        break  # At least one position matches all criteria
                else:
                    # No position matched all criteria
                    validation_errors += 1
                    print(f"   ❌ Job {job_id} doesn't match filter criteria")
            
            if validation_errors == 0:
                print(f"   ✅ All Level 1 jobs match filter criteria")
            else:
                print(f"   ⚠️  {validation_errors} jobs don't match filter criteria")
            
            results_summary.append({
                'test': test_case['name'],
                'level_1_count': len(level_1_jobs),
                'validation_errors': validation_errors,
                'total_nodes': sum(level_counts.values())
            })
            
        except Exception as e:
            print(f"   ❌ Query failed: {e}")
            results_summary.append({
                'test': test_case['name'],
                'level_1_count': 'ERROR',
                'validation_errors': 'ERROR',
                'total_nodes': 'ERROR'
            })
        
        print()
    
    # Summary table
    print("📊 SUMMARY TABLE")
    print("=" * 70)
    print(f"{'Test Name':<25} {'Level 1':<8} {'Errors':<8} {'Total':<8}")
    print("-" * 70)
    
    for result in results_summary:
        print(f"{result['test']:<25} {str(result['level_1_count']):<8} {str(result['validation_errors']):<8} {str(result['total_nodes']):<8}")
    
    print()
    
    # Check for progressive filtering (each additional filter should reduce or maintain count)
    print("🔍 STEP 3: Validating progressive filtering behavior")
    print("-" * 70)
    
    baseline_count = None
    for result in results_summary:
        if result['test'] == 'No Filters (Baseline)':
            baseline_count = result['level_1_count']
            break
    
    if baseline_count and isinstance(baseline_count, int):
        print(f"📊 Baseline (no filters): {baseline_count} Level 1 jobs")
        
        for result in results_summary[1:]:  # Skip baseline
            if isinstance(result['level_1_count'], int):
                if result['level_1_count'] <= baseline_count:
                    print(f"   ✅ {result['test']}: {result['level_1_count']} jobs (properly restrictive)")
                else:
                    print(f"   ❌ {result['test']}: {result['level_1_count']} jobs (additive behavior detected!)")
            else:
                print(f"   ❓ {result['test']}: {result['level_1_count']} (error)")
    
    conn.close()
    
    print()
    print("🎯 Test completed! Check results above for any issues.")

if __name__ == "__main__":
    test_all_organizational_filters() 