#!/usr/bin/env python3
"""
Test the colleague positions schema fix
"""

import sys
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from skill_similarity_engine.business_context.schema_builder import SchemaBuilder

def test_schema_fix():
    """Test that the new schema allows duplicate PosIDLookupKey values with different Week Ending."""
    
    print("🧪 Testing Colleague Positions Schema Fix")
    print("=" * 50)
    
    # Create test database
    test_db = project_root / "test_colleague_positions_schema.sqlite"
    if test_db.exists():
        test_db.unlink()
    
    # Build schema
    schema_builder = SchemaBuilder(str(test_db))
    success = schema_builder.create_schema(drop_existing=True)
    
    if not success:
        print("❌ Failed to create schema")
        return False
    
    print("✅ Schema created successfully")
    
    # Test inserting duplicate PosIDLookupKey with different Week Ending
    try:
        with sqlite3.connect(str(test_db)) as conn:
            # Insert first record
            conn.execute("""
                INSERT INTO core_colleague_positions_history 
                ("Week Ending", "Employee Number", "Operational", "Position Start Date", "PosIDLookupKey", "Position Number")
                VALUES ('2024-01-01', 12345, 1, '2024-01-01', 1.23456789e+11, 67890)
            """)
            
            # Insert second record with SAME PosIDLookupKey but DIFFERENT Week Ending
            conn.execute("""
                INSERT INTO core_colleague_positions_history 
                ("Week Ending", "Employee Number", "Operational", "Position Start Date", "PosIDLookupKey", "Position Number")
                VALUES ('2024-01-08', 12345, 1, '2024-01-01', 1.23456789e+11, 67890)
            """)
            
            # This should work now with composite primary key
            conn.commit()
            
            # Verify both records exist
            cursor = conn.execute("SELECT COUNT(*) FROM core_colleague_positions_history")
            count = cursor.fetchone()[0]
            
            if count == 2:
                print("✅ Successfully inserted 2 records with same PosIDLookupKey, different Week Ending")
                
                # Test that true duplicates are still prevented
                try:
                    conn.execute("""
                        INSERT INTO core_colleague_positions_history 
                        ("Week Ending", "Employee Number", "Operational", "Position Start Date", "PosIDLookupKey", "Position Number")
                        VALUES ('2024-01-01', 99999, 1, '2024-01-01', 1.23456789e+11, 99999)
                    """)
                    conn.commit()
                    print("❌ ERROR: Should have prevented true duplicate (same PosIDLookupKey + Week Ending)")
                    return False
                except sqlite3.IntegrityError:
                    print("✅ Correctly prevented true duplicate (same PosIDLookupKey + Week Ending)")
                
                return True
            else:
                print(f"❌ Expected 2 records, found {count}")
                return False
                
    except sqlite3.IntegrityError as e:
        print(f"❌ Integrity error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Cleanup
        if test_db.exists():
            test_db.unlink()

if __name__ == "__main__":
    success = test_schema_fix()
    if success:
        print("\n🎉 Schema fix validated! Colleague positions should now load successfully.")
    else:
        print("\n❌ Schema fix failed validation.")