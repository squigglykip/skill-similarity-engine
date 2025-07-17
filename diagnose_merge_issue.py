#!/usr/bin/env python3
"""
Diagnose Movement Data Merge Issue

This script investigates why the merge between movement_fact data and 
positions data is failing, resulting in 0 records after enrichment.
"""

import sqlite3
import pandas as pd

def main():
    print("🔍 DIAGNOSING MOVEMENT DATA MERGE ISSUE")
    print("="*50)
    
    # Connect to database
    conn = sqlite3.connect('models/2025-Q3/workforce_intelligence.sqlite')
    
    # Check movement_fact data
    print("\n📊 MOVEMENT_FACT TABLE ANALYSIS:")
    movement_query = """
    SELECT 
        from_position, 
        to_position, 
        COUNT(*) as count
    FROM movement_fact 
    GROUP BY from_position, to_position 
    LIMIT 10
    """
    movement_df = pd.read_sql_query(movement_query, conn)
    print(f"Sample movement data:")
    print(movement_df.to_string(index=False))
    
    # Check unique positions in movement_fact
    unique_from_query = "SELECT COUNT(DISTINCT from_position) as unique_from FROM movement_fact"
    unique_to_query = "SELECT COUNT(DISTINCT to_position) as unique_to FROM movement_fact"
    
    unique_from = pd.read_sql_query(unique_from_query, conn)['unique_from'].iloc[0]
    unique_to = pd.read_sql_query(unique_to_query, conn)['unique_to'].iloc[0]
    
    print(f"\n📈 Movement data statistics:")
    print(f"   → Unique from_positions: {unique_from:,}")
    print(f"   → Unique to_positions: {unique_to:,}")
    
    # Check positions table
    print("\n📊 POSITIONS TABLE ANALYSIS:")
    positions_query = """
    SELECT 
        "Position Number", 
        JobProfileID,
        COUNT(*) as count
    FROM positions 
    GROUP BY "Position Number", JobProfileID
    LIMIT 10
    """
    positions_df = pd.read_sql_query(positions_query, conn)
    print(f"Sample positions data:")
    print(positions_df.to_string(index=False))
    
    # Check JobProfileID distribution
    jobprofile_query = """
    SELECT 
        JobProfileID,
        COUNT(*) as position_count
    FROM positions 
    WHERE JobProfileID IS NOT NULL
    GROUP BY JobProfileID
    LIMIT 10
    """
    jobprofile_df = pd.read_sql_query(jobprofile_query, conn)
    print(f"\nJobProfileID distribution:")
    print(jobprofile_df.to_string(index=False))
    
    # Check for null JobProfileIDs
    null_check_query = """
    SELECT 
        COUNT(*) as total_positions,
        COUNT(JobProfileID) as non_null_jobprofile,
        COUNT(*) - COUNT(JobProfileID) as null_jobprofile
    FROM positions
    """
    null_check_df = pd.read_sql_query(null_check_query, conn)
    print(f"\nJobProfileID null analysis:")
    print(null_check_df.to_string(index=False))
    
    # Test actual merge
    print("\n🔄 TESTING MERGE COMPATIBILITY:")
    
    # Get sample movement positions
    sample_movement_query = "SELECT DISTINCT from_position FROM movement_fact LIMIT 10"
    sample_positions = pd.read_sql_query(sample_movement_query, conn)['from_position'].tolist()
    
    print(f"Sample movement positions: {sample_positions}")
    
    # Check if these exist in positions table
    sample_positions_str = "', '".join(sample_positions)
    match_query = f"""
    SELECT 
        "Position Number",
        JobProfileID
    FROM positions 
    WHERE "Position Number" IN ('{sample_positions_str}')
    """
    
    matches_df = pd.read_sql_query(match_query, conn)
    print(f"\nMatching positions in positions table:")
    print(matches_df.to_string(index=False))
    print(f"Match count: {len(matches_df)} out of {len(sample_positions)} sample positions")
    
    # Check position number format comparison
    print("\n🔍 POSITION NUMBER FORMAT ANALYSIS:")
    
    movement_sample_query = "SELECT from_position FROM movement_fact LIMIT 5"
    movement_samples = pd.read_sql_query(movement_sample_query, conn)
    print("Movement position format:")
    for pos in movement_samples['from_position']:
        print(f"   → '{pos}' (type: {type(pos)}, length: {len(str(pos))})")
    
    positions_sample_query = 'SELECT "Position Number" FROM positions LIMIT 5'
    positions_samples = pd.read_sql_query(positions_sample_query, conn)
    print("\nPositions table format:")
    for pos in positions_samples['Position Number']:
        print(f"   → '{pos}' (type: {type(pos)}, length: {len(str(pos))})")
    
    conn.close()
    
    print("\n💡 DIAGNOSTIC COMPLETE")
    print("Check the output above to identify the merge compatibility issue.")

if __name__ == "__main__":
    main() 