#!/usr/bin/env python3
"""
Test Position Merge Logic

Proof of concept script to test the position number merging logic
and understand why position_number fields are staying None
"""

import sys
import os
import sqlite3
import pandas as pd

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.models.colleague_position import ColleaguePosition

def load_position_mappings(db_path):
    """Load position mappings exactly like the production code does."""
    try:
        with sqlite3.connect(db_path) as conn:
            query = """
            SELECT DISTINCT PosIDLookupKey, Position_Number 
            FROM core_position_timeline 
            WHERE Position_Number IS NOT NULL
            """
            cursor = conn.execute(query)
            mappings = {float(row[0]): int(row[1]) for row in cursor.fetchall()}
            return mappings
    except Exception as e:
        print(f"❌ Failed to load position mappings: {e}")
        return {}

def load_sample_colleague_positions(db_path, limit=100):
    """Load a representative sample of colleague positions to test with."""
    try:
        with sqlite3.connect(db_path) as conn:
            # Use TABLESAMPLE or ORDER BY RANDOM() to get a representative sample
            # This should maintain the ~99% merge rate we see in the database
            query = f"""
            SELECT 
                h."Week Ending" as week_ending,
                h."Employee Number" as employee_number,
                h."Position Start Date" as position_start_date,
                h."Position Number" as h_position_number,
                h.PosIDLookupKey,
                h.Operational
            FROM core_colleague_positions_history h 
            ORDER BY RANDOM()
            LIMIT {limit}
            """
            
            df = pd.read_sql_query(query, conn)
            return df
    except Exception as e:
        print(f"❌ Failed to load colleague positions: {e}")
        return pd.DataFrame()

def create_colleague_position_objects(df):
    """Create ColleaguePosition objects from DataFrame."""
    positions = []
    
    for _, row in df.iterrows():
        try:
            # Create ColleaguePosition object
            pos = ColleaguePosition(
                pos_id_lookup_key=str(row['PosIDLookupKey']),
                employee_number=int(row['employee_number']),
                week_ending=row['week_ending'],  # Will be processed in __post_init__
                position_number=None,  # Should be set by merge
                position_start_date=row['position_start_date'],
                operational=str(row['Operational']).upper() in ['TRUE', 'T', '1', 'YES', 'Y']
            )
            positions.append(pos)
        except Exception as e:
            print(f"❌ Failed to create ColleaguePosition: {e}")
            continue
    
    return positions

def test_merge_logic(positions, position_mappings):
    """Test the merge logic exactly like the production code."""
    merged_count = 0
    orphan_count = 0
    
    print(f"\n🧪 Testing merge logic with {len(positions)} positions and {len(position_mappings)} mappings...")
    
    # Debug: Show some sample mappings
    sample_keys = list(position_mappings.keys())[:5]
    print(f"🔍 Sample mapping keys: {sample_keys}")
    
    # Debug: Show some colleague PosIDLookupKeys  
    colleague_keys = [float(pos.pos_id_lookup_key) for pos in positions[:5]]
    print(f"🔍 Sample colleague keys: {colleague_keys}")
    
    # Debug: Check if any colleague keys exist in mappings
    overlaps = [key for key in colleague_keys if key in position_mappings]
    print(f"🔍 Overlapping keys in first 5: {overlaps}")
    
    for i, colleague_pos in enumerate(positions):
        try:
            # Convert PosIDLookupKey to float for lookup (exactly like production)
            pos_id_lookup = float(colleague_pos.pos_id_lookup_key)
            
            if i < 10:  # Show first 10 detailed
                print(f"   Position {i+1}: PosIDLookupKey={pos_id_lookup}, Employee={colleague_pos.employee_number}")
                print(f"      Before merge: position_number={colleague_pos.position_number}")
            
            if pos_id_lookup in position_mappings:
                # Successful merge - set the real position number
                colleague_pos.position_number = position_mappings[pos_id_lookup]
                merged_count += 1
                if i < 10:
                    print(f"      ✅ After merge: position_number={colleague_pos.position_number}")
            else:
                # Orphan record - PosIDLookupKey not found in timeline
                colleague_pos.position_number = None
                orphan_count += 1
                if i < 10:
                    print(f"      ❌ Orphan: PosIDLookupKey not found in mappings")
                
        except (ValueError, TypeError) as e:
            # Invalid PosIDLookupKey format
            if i < 10:
                print(f"      ❌ Invalid PosIDLookupKey format: {colleague_pos.pos_id_lookup_key} - {e}")
            colleague_pos.position_number = None
            orphan_count += 1
    
    return merged_count, orphan_count

def verify_position_keys(positions):
    """Verify what position_key returns for each position."""
    print(f"\n🔍 Verifying position_key values:")
    
    for i, pos in enumerate(positions[:10]):
        position_key = pos.position_key
        print(f"   Position {i+1}: position_number={pos.position_number}, position_key={position_key}")
        
        # Check if position_key is using position_number or falling back to PosIDLookupKey
        if pos.position_number is not None:
            expected_key = pos.position_number
            source = "position_number"
        else:
            expected_key = int(float(pos.pos_id_lookup_key))
            source = "PosIDLookupKey fallback"
        
        print(f"      Expected: {expected_key} (from {source})")
        print(f"      Actual: {position_key}")
        print(f"      Match: {position_key == expected_key}")
        print()

def test_movement_detection_sample(positions):
    """Test if any movements would be detected with these positions."""
    print(f"\n🔄 Testing movement detection logic:")
    
    # Group by employee
    by_employee = {}
    for pos in positions:
        emp_id = pos.employee_number
        if emp_id not in by_employee:
            by_employee[emp_id] = []
        by_employee[emp_id].append(pos)
    
    # Sort by date and check for movements
    movements_found = 0
    for emp_id, emp_positions in by_employee.items():
        if len(emp_positions) < 2:
            continue
            
        # Sort by week_ending (string dates should sort correctly)
        emp_positions.sort(key=lambda p: p.week_ending)
        
        print(f"   Employee {emp_id}: {len(emp_positions)} positions")
        position_keys = [pos.position_key for pos in emp_positions]
        unique_keys = set(position_keys)
        
        print(f"      Position keys: {position_keys}")
        print(f"      Unique keys: {len(unique_keys)}")
        
        if len(unique_keys) > 1:
            movements_found += len(unique_keys) - 1
            print(f"      ✅ {len(unique_keys) - 1} movements detected!")
        else:
            print(f"      ❌ No movements (same position_key)")
        print()
    
    print(f"📊 Total movements detected: {movements_found}")
    return movements_found

def main():
    print("🧪 TESTING POSITION MERGE LOGIC")
    
    # Find database
    db_paths = ["models/2025-Q3/business_context.sqlite", "../models/2025-Q3/business_context.sqlite"]
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Database not found")
        return
    
    print(f"📂 Database: {db_path}")
    
    try:
        # Step 1: Load position mappings
        print("\n📋 Step 1: Loading position mappings...")
        position_mappings = load_position_mappings(db_path)
        print(f"   ✅ Loaded {len(position_mappings)} position mappings")
        
        # Step 2: Load sample colleague positions
        print("\n👥 Step 2: Loading sample colleague positions...")
        df = load_sample_colleague_positions(db_path, limit=50)
        print(f"   ✅ Loaded {len(df)} colleague position records")
        
        # Step 3: Create ColleaguePosition objects
        print("\n🏗️  Step 3: Creating ColleaguePosition objects...")
        positions = create_colleague_position_objects(df)
        print(f"   ✅ Created {len(positions)} ColleaguePosition objects")
        
        # Step 4: Test merge logic
        print("\n🔗 Step 4: Testing merge logic...")
        merged_count, orphan_count = test_merge_logic(positions, position_mappings)
        
        merge_rate = (merged_count / len(positions) * 100) if len(positions) > 0 else 0
        print(f"\n📊 Merge Results:")
        print(f"   • Total positions: {len(positions)}")
        print(f"   • Successfully merged: {merged_count}")
        print(f"   • Orphan records: {orphan_count}")
        print(f"   • Merge rate: {merge_rate:.1f}%")
        
        # Step 5: Verify position_key behavior
        verify_position_keys(positions)
        
        # Step 6: Test movement detection
        movements = test_movement_detection_sample(positions)
        
        print(f"\n🎯 Test Results Summary:")
        if merged_count > 0:
            print(f"   ✅ Position merge logic works: {merged_count}/{len(positions)} merged successfully")
        else:
            print(f"   ❌ Position merge failed: All position_number fields are None")
        
        if movements > 0:
            print(f"   ✅ Movement detection would work: {movements} movements detected")
        else:
            print(f"   ❌ No movements detected: All employees have same position_key")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()