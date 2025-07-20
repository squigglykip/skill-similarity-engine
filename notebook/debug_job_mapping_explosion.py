#!/usr/bin/env python3
"""
Job Mapping Explosion Debug Script
==================================

This script investigates the position-to-job-profile mapping that's causing
a cartesian product explosion during the join operation.

The issue: Raw movement_fact has 124k movements, but after joining with 
positions table we get 1M+ movements (8x explosion).

Expected: Many positions → One job profile (many-to-one)
Actual: Appears to be many-to-many causing cartesian explosion
"""

import pandas as pd
import sqlite3
import warnings

warnings.filterwarnings('ignore')

DATABASE_FILE = 'models/2025-Q3/workforce_intelligence.sqlite'

def print_section_header(title, description=""):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    if description:
        print(f"{description}")
        print()

def investigate_position_job_mapping():
    """Investigate the position to job profile mapping relationship"""
    print_section_header("POSITION-TO-JOB-PROFILE MAPPING INVESTIGATION")
    
    conn = sqlite3.connect(DATABASE_FILE)
    
    # Check the positions table structure and uniqueness
    print("🔍 Positions Table Analysis:")
    
    positions_count_query = """
    SELECT COUNT(*) as total_positions,
           COUNT(DISTINCT [Position Number]) as unique_positions,
           COUNT(DISTINCT JobProfileID) as unique_job_profiles
    FROM positions
    """
    positions_counts = pd.read_sql_query(positions_count_query, conn)
    
    print(f"   → Total position records: {positions_counts['total_positions'].iloc[0]:,}")
    print(f"   → Unique position numbers: {positions_counts['unique_positions'].iloc[0]:,}")
    print(f"   → Unique job profile IDs: {positions_counts['unique_job_profiles'].iloc[0]:,}")
    
    # Check if Position Number is unique (should be primary key)
    if positions_counts['total_positions'].iloc[0] == positions_counts['unique_positions'].iloc[0]:
        print(f"   ✅ Position Number appears to be unique (good)")
    else:
        duplicates = positions_counts['total_positions'].iloc[0] - positions_counts['unique_positions'].iloc[0]
        print(f"   ❌ Position Number has {duplicates:,} duplicates (BAD - causing explosion!)")
    
    # Check for duplicate position numbers
    duplicate_positions_query = """
    SELECT [Position Number], COUNT(*) as count
    FROM positions
    GROUP BY [Position Number]
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC
    LIMIT 10
    """
    duplicate_positions = pd.read_sql_query(duplicate_positions_query, conn)
    
    if len(duplicate_positions) > 0:
        print(f"\n❌ DUPLICATE POSITION NUMBERS FOUND:")
        print(f"   → {len(duplicate_positions):,} position numbers have duplicates")
        print(f"   → Top duplicates:")
        for _, row in duplicate_positions.head(5).iterrows():
            print(f"     • Position {row['Position Number']}: {row['count']} records")
        
        # Show examples of what these duplicates look like
        sample_duplicate = duplicate_positions.iloc[0]['Position Number']
        sample_records_query = f"""
        SELECT [Position Number], JobProfileID, [Position Name], Division, Business_Unit
        FROM positions
        WHERE [Position Number] = {sample_duplicate}
        """
        sample_records = pd.read_sql_query(sample_records_query, conn)
        print(f"\n   → Example duplicate records for Position {sample_duplicate}:")
        print(sample_records)
        print()
    else:
        print(f"\n✅ No duplicate position numbers found")
    
    conn.close()
    return len(duplicate_positions) > 0

def investigate_movement_join_explosion():
    """Investigate what happens during the movement_fact join"""
    print_section_header("MOVEMENT_FACT JOIN EXPLOSION ANALYSIS")
    
    conn = sqlite3.connect(DATABASE_FILE)
    
    # Sample a small subset to see the explosion in action
    print("🔍 Testing join explosion with small sample:")
    
    # Get a small sample of movement_fact records
    sample_movements_query = """
    SELECT from_position, to_position, movement_count
    FROM movement_fact
    WHERE movement_year >= 2020
    LIMIT 5
    """
    sample_movements = pd.read_sql_query(sample_movements_query, conn)
    print(f"   → Sample movement records:")
    print(sample_movements)
    print()
    
    # Check how many position records exist for these specific positions
    for _, row in sample_movements.iterrows():
        from_pos = row['from_position']
        to_pos = row['to_position']
        
        from_count_query = f"SELECT COUNT(*) as count FROM positions WHERE [Position Number] = {from_pos}"
        to_count_query = f"SELECT COUNT(*) as count FROM positions WHERE [Position Number] = {to_pos}"
        
        from_count = pd.read_sql_query(from_count_query, conn)['count'].iloc[0]
        to_count = pd.read_sql_query(to_count_query, conn)['count'].iloc[0]
        
        explosion_factor = from_count * to_count
        
        print(f"   → Movement {from_pos} → {to_pos}:")
        print(f"     • From position records: {from_count}")
        print(f"     • To position records: {to_count}")
        print(f"     • Explosion factor: {explosion_factor}x")
        
        if explosion_factor > 1:
            print(f"     ❌ This single movement will create {explosion_factor} records!")
        else:
            print(f"     ✅ This movement will remain as 1 record")
        print()
    
    # Test the actual join to see the explosion
    print("🔍 Testing actual join result:")
    test_join_query = """
    SELECT 
        mf.from_position,
        mf.to_position,
        mf.movement_count,
        p_from.JobProfileID as JobProfileID_from,
        p_to.JobProfileID as JobProfileID_to,
        p_from.[Position Name] as from_name,
        p_to.[Position Name] as to_name
    FROM movement_fact mf
    JOIN positions p_from ON mf.from_position = p_from.[Position Number]
    JOIN positions p_to ON mf.to_position = p_to.[Position Number]
    WHERE mf.movement_year >= 2020
    AND mf.from_position IN (65189465, 65254996, 65254701, 65212105, 65257516)
    """
    
    test_join_result = pd.read_sql_query(test_join_query, conn)
    print(f"   → Join result for sample positions:")
    print(f"     • Records returned: {len(test_join_result)}")
    print(test_join_result)
    print()
    
    conn.close()

def investigate_data_quality_root_cause():
    """Investigate the root cause of duplicate positions"""
    print_section_header("ROOT CAUSE ANALYSIS - WHY DUPLICATE POSITIONS?")
    
    conn = sqlite3.connect(DATABASE_FILE)
    
    # Look at the structure of duplicate position records
    print("🔍 Analyzing duplicate position record structure:")
    
    # Find positions with duplicates and analyze them
    duplicate_analysis_query = """
    SELECT 
        p1.[Position Number],
        p1.JobProfileID,
        p1.[Position Name],
        p1.Division,
        p1.Business_Unit,
        p1.Team,
        p1.[Employee Group],
        COUNT(*) OVER (PARTITION BY p1.[Position Number]) as duplicate_count
    FROM positions p1
    WHERE p1.[Position Number] IN (
        SELECT [Position Number]
        FROM positions
        GROUP BY [Position Number]
        HAVING COUNT(*) > 1
    )
    ORDER BY p1.[Position Number], p1.JobProfileID
    LIMIT 20
    """
    
    duplicate_analysis = pd.read_sql_query(duplicate_analysis_query, conn)
    
    if len(duplicate_analysis) > 0:
        print(f"   → Sample duplicate position analysis:")
        print(duplicate_analysis[['Position Number', 'JobProfileID', 'Position Name', 'Division', 'duplicate_count']])
        print()
        
        # Check if duplicates have different job profiles (bad) or same (maybe OK)
        job_profile_variance_query = """
        SELECT 
            [Position Number],
            COUNT(DISTINCT JobProfileID) as unique_job_profiles,
            COUNT(*) as total_records
        FROM positions
        WHERE [Position Number] IN (
            SELECT [Position Number]
            FROM positions
            GROUP BY [Position Number]
            HAVING COUNT(*) > 1
        )
        GROUP BY [Position Number]
        ORDER BY unique_job_profiles DESC, total_records DESC
        LIMIT 10
        """
        
        job_profile_variance = pd.read_sql_query(job_profile_variance_query, conn)
        print(f"   → Job profile variance in duplicates:")
        print(job_profile_variance)
        print()
        
        multiple_job_profiles = job_profile_variance[job_profile_variance['unique_job_profiles'] > 1]
        if len(multiple_job_profiles) > 0:
            print(f"   ❌ CRITICAL: {len(multiple_job_profiles)} positions map to multiple job profiles!")
            print(f"   → This creates many-to-many relationships causing the explosion")
        else:
            print(f"   ✅ All duplicate positions have the same job profile")
            print(f"   → Duplicates won't cause job profile explosion")
    
    conn.close()

def propose_fix_strategy():
    """Propose strategies to fix the join explosion"""
    print_section_header("FIX STRATEGY RECOMMENDATIONS")
    
    print("🔧 Recommended Fix Approaches:")
    print()
    
    print("1. **IMMEDIATE FIX - Deduplicate Position Mapping:**")
    print("   → Use DISTINCT in the join to eliminate duplicate mappings")
    print("   → Or use window functions to pick one record per position")
    print()
    
    print("2. **QUERY MODIFICATION - Use DISTINCT Position Mapping:**")
    print("   ```sql")
    print("   -- Instead of direct join, use deduplicated position mapping")
    print("   WITH unique_positions AS (")
    print("       SELECT DISTINCT [Position Number], JobProfileID")
    print("       FROM positions")
    print("   )")
    print("   SELECT ...")
    print("   FROM movement_fact mf")
    print("   JOIN unique_positions p_from ON mf.from_position = p_from.[Position Number]")
    print("   JOIN unique_positions p_to ON mf.to_position = p_to.[Position Number]")
    print("   ```")
    print()
    
    print("3. **DATA CLEANUP - Fix Source Data:**")
    print("   → Investigate why positions table has duplicates")
    print("   → Clean up the positions table to have unique Position Numbers")
    print("   → Ensure proper primary key constraints")
    print()
    
    print("4. **DEFENSIVE CODING - Row Number Selection:**")
    print("   ```sql")
    print("   WITH numbered_positions AS (")
    print("       SELECT *, ROW_NUMBER() OVER (PARTITION BY [Position Number] ORDER BY JobProfileID) as rn")
    print("       FROM positions")
    print("   )")
    print("   SELECT ...")
    print("   FROM movement_fact mf")
    print("   JOIN numbered_positions p_from ON mf.from_position = p_from.[Position Number] AND p_from.rn = 1")
    print("   JOIN numbered_positions p_to ON mf.to_position = p_to.[Position Number] AND p_to.rn = 1")
    print("   ```")

def main():
    """Main debug execution for join explosion"""
    print_section_header(
        "JOB MAPPING EXPLOSION DEBUG",
        "Investigating why movement_fact join creates 8x data explosion"
    )
    
    # Step 1: Check position-job mapping uniqueness
    has_duplicates = investigate_position_job_mapping()
    
    # Step 2: Investigate the join explosion mechanism
    investigate_movement_join_explosion()
    
    # Step 3: Root cause analysis
    investigate_data_quality_root_cause()
    
    # Step 4: Propose fix strategies
    propose_fix_strategy()
    
    print_section_header("EXPLOSION DEBUG COMPLETE")
    print(f"🎯 Summary:")
    if has_duplicates:
        print(f"   ❌ PROBLEM IDENTIFIED: Duplicate position numbers in positions table")
        print(f"   → This creates cartesian product during JOIN operations")
        print(f"   → 124k movements become 1M+ movements (8x explosion)")
        print(f"   → Solution: Use DISTINCT or ROW_NUMBER() to deduplicate joins")
    else:
        print(f"   🤔 No obvious duplicates found - need deeper investigation")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. Implement DISTINCT join fix in ML pipeline")
    print(f"   2. Test with deduplication to verify explosion is resolved")
    print(f"   3. Validate that movement totals match expected 124k corpus")

if __name__ == "__main__":
    main() 