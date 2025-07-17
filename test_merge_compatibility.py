#!/usr/bin/env python3
"""
Test Merge Compatibility Script

Quick diagnostic tool to test if movement_fact_table.parquet position numbers
can successfully merge with the database position and job data.
"""

import pandas as pd
import sqlite3
from pathlib import Path

def normalize_column_names(df):
    """Normalize column names to lowercase with underscores"""
    column_mapping = {}
    for col in df.columns:
        normalized = col.lower().replace(' ', '_').replace('-', '_')
        column_mapping[col] = normalized
    return df.rename(columns=column_mapping)

def test_merge_compatibility():
    """Test merge compatibility between movement data and database"""
    
    print("🔍 MOVEMENT DATA & DATABASE MERGE COMPATIBILITY TEST")
    print("=" * 60)
    
    # File paths
    movement_file = "models/2025-Q3/2025-07-14/movement_fact_table.parquet"
    database_file = "models/2025-Q3/workforce_intelligence.sqlite"
    
    # Load movement data
    print(f"\n📁 Loading movement data: {movement_file}")
    try:
        movement_df = pd.read_parquet(movement_file)
        movement_df = normalize_column_names(movement_df)
        print(f"✅ Loaded {len(movement_df):,} movement records")
        print(f"📊 Columns: {list(movement_df.columns)}")
    except Exception as e:
        print(f"❌ Failed to load movement data: {e}")
        return
    
    # Load database data
    print(f"\n🔗 Loading database: {database_file}")
    try:
        conn = sqlite3.connect(database_file)
        positions_df = pd.read_sql_query("SELECT * FROM positions LIMIT 10000", conn)
        jobs_df = pd.read_sql_query("SELECT * FROM jobs", conn)
        print(f"✅ Loaded {len(positions_df):,} position records")
        print(f"✅ Loaded {len(jobs_df):,} job records")
    except Exception as e:
        print(f"❌ Failed to load database: {e}")
        return
    
    # Analyze position numbers
    print(f"\n🔍 POSITION NUMBER ANALYSIS")
    print("-" * 40)
    
    # Get unique position numbers from movement data
    movement_positions = set()
    if 'from_position' in movement_df.columns:
        movement_positions.update(movement_df['from_position'].astype(str).unique())
    if 'to_position' in movement_df.columns:
        movement_positions.update(movement_df['to_position'].astype(str).unique())
    
    print(f"📊 Unique positions in movement data: {len(movement_positions):,}")
    print(f"📊 Sample movement positions: {list(movement_positions)[:10]}")
    
    # Get unique position numbers from database
    db_positions = set(positions_df['Position Number'].astype(str).unique())
    print(f"📊 Unique positions in database: {len(db_positions):,}")
    print(f"📊 Sample database positions: {list(db_positions)[:10]}")
    
    # Check overlap
    overlap = movement_positions.intersection(db_positions)
    print(f"\n🎯 OVERLAP ANALYSIS")
    print("-" * 40)
    print(f"📊 Positions that match: {len(overlap):,}")
    print(f"📊 Movement positions not in DB: {len(movement_positions - db_positions):,}")
    print(f"📊 DB positions not in movement: {len(db_positions - movement_positions):,}")
    
    if len(overlap) > 0:
        overlap_rate = len(overlap) / len(movement_positions) * 100
        print(f"✅ Overlap rate: {overlap_rate:.1f}%")
        print(f"📊 Sample matching positions: {list(overlap)[:10]}")
    else:
        print("❌ NO OVERLAP FOUND - This explains the merge failure!")
    
    # Test actual merge
    print(f"\n🔄 TESTING ACTUAL MERGE")
    print("-" * 40)
    
    # Convert data types
    positions_df['Position Number'] = positions_df['Position Number'].astype(str)
    movement_df['from_position'] = movement_df['from_position'].astype(str)
    movement_df['to_position'] = movement_df['to_position'].astype(str)
    
    # Test merge with from positions
    test_sample = movement_df.head(1000)  # Test with first 1000 records
    merged_from = test_sample.merge(
        positions_df[['Position Number', 'JobProfileID']],
        left_on='from_position',
        right_on='Position Number',
        how='left'
    )
    
    successful_from_merges = merged_from['JobProfileID'].notna().sum()
    print(f"📊 Successful 'from_position' merges: {successful_from_merges:,} / {len(test_sample):,}")
    
    # Test merge with to positions
    merged_to = test_sample.merge(
        positions_df[['Position Number', 'JobProfileID']],
        left_on='to_position',
        right_on='Position Number',
        how='left'
    )
    
    successful_to_merges = merged_to['JobProfileID'].notna().sum()
    print(f"📊 Successful 'to_position' merges: {successful_to_merges:,} / {len(test_sample):,}")
    
    # Test full pipeline
    if successful_from_merges > 0 and successful_to_merges > 0:
        print(f"\n✅ MERGE TEST RESULTS")
        print("-" * 40)
        print("✅ Merges are working - position numbers match database")
        print("✅ The issue might be elsewhere in the pipeline")
    else:
        print(f"\n❌ MERGE TEST RESULTS")
        print("-" * 40)
        print("❌ Merges are failing - position numbers don't match database")
        print("❌ This confirms the merge compatibility issue")
        
        # Suggest solutions
        print(f"\n💡 SUGGESTED SOLUTIONS")
        print("-" * 40)
        print("1. Use the original synthetic test data that was designed for this database")
        print("2. Update the movement data generation to use current position numbers")
        print("3. Update the database with historical position data")
        print("4. Create a position mapping table for historical data")
    
    # Show data type info
    print(f"\n🔍 DATA TYPE ANALYSIS")
    print("-" * 40)
    print(f"Movement 'from_position' type: {movement_df['from_position'].dtype}")
    print(f"Movement 'to_position' type: {movement_df['to_position'].dtype}")
    print(f"Database 'Position Number' type: {positions_df['Position Number'].dtype}")
    
    conn.close()

if __name__ == "__main__":
    test_merge_compatibility() 