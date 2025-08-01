#!/usr/bin/env python3
"""
Diagnose PosIDLookupKey precision issues during CSV parsing
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

project_root = Path(__file__).parent.parent
data_dir = project_root / "data" / "colleague_positions_history"

def diagnose_precision_issue():
    """Diagnose precision loss in PosIDLookupKey parsing."""
    
    print("🔬 PosIDLookupKey Precision Diagnostic")
    print("=" * 60)
    
    # Test with one file first
    test_file = data_dir / "d_colleague_position_fy20.csv"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"📁 Testing with: {test_file.name}")
    print()
    
    # Test 1: Default pandas parsing
    print("1️⃣ Default pandas parsing...")
    df_default = pd.read_csv(test_file, low_memory=False)
    posid_default = df_default['PosIDLookupKey']
    
    print(f"   Data type: {posid_default.dtype}")
    print(f"   Sample values: {posid_default.head(3).tolist()}")
    print(f"   Unique values: {posid_default.nunique():,}")
    print(f"   Total values: {len(posid_default):,}")
    print(f"   Duplicates: {len(posid_default) - posid_default.nunique():,}")
    print()
    
    # Test 2: Force string parsing then convert
    print("2️⃣ String parsing then convert...")
    df_string = pd.read_csv(test_file, dtype={'PosIDLookupKey': 'str'}, low_memory=False)
    posid_string = df_string['PosIDLookupKey']
    
    print(f"   Data type: {posid_string.dtype}")
    print(f"   Sample raw strings: {posid_string.head(3).tolist()}")
    
    # Check if any values are in scientific notation
    scientific_notation = posid_string.str.contains('e|E', na=False).sum()
    print(f"   Values in scientific notation: {scientific_notation}")
    
    # Convert to int64 carefully
    try:
        # Handle scientific notation if present
        posid_int64 = pd.to_numeric(posid_string, errors='coerce').astype('Int64')
        
        print(f"   After int64 conversion - Data type: {posid_int64.dtype}")
        print(f"   Sample converted values: {posid_int64.head(3).tolist()}")
        print(f"   Unique values: {posid_int64.nunique():,}")
        print(f"   Total values: {len(posid_int64):,}")
        print(f"   Duplicates: {len(posid_int64) - posid_int64.nunique():,}")
        print(f"   Null values after conversion: {posid_int64.isnull().sum()}")
        
        # Compare with default parsing
        precision_gained = posid_int64.nunique() - posid_default.nunique()
        duplicates_resolved = (len(posid_default) - posid_default.nunique()) - (len(posid_int64) - posid_int64.nunique())
        
        print()
        print("🔍 Precision Comparison:")
        print(f"   Unique values gained: {precision_gained:,}")
        print(f"   Duplicates resolved: {duplicates_resolved:,}")
        
        if duplicates_resolved > 0:
            print(f"   ✅ PRECISION ISSUE CONFIRMED!")
            print(f"      {duplicates_resolved:,} false duplicates caused by precision loss")
        else:
            print(f"   ❓ No precision improvement detected")
            
    except Exception as e:
        print(f"   ❌ Error in int64 conversion: {e}")
    
    print()
    
    # Test 3: Check specific duplicate values
    print("3️⃣ Analyzing specific duplicates...")
    
    # Find the most duplicated value
    value_counts = posid_default.value_counts()
    most_duplicated = value_counts.index[0]
    duplicate_count = value_counts.iloc[0]
    
    print(f"   Most duplicated value: {most_duplicated}")
    print(f"   Appears {duplicate_count} times")
    
    # Check if this is a precision artifact
    # Look at the raw string values for this "duplicate"
    if 'posid_string' in locals():
        duplicate_mask = pd.to_numeric(posid_string, errors='coerce') == most_duplicated
        raw_strings = posid_string[duplicate_mask].unique()
        
        print(f"   Raw string representations: {len(raw_strings)} unique")
        if len(raw_strings) <= 10:
            print(f"   Raw values: {raw_strings.tolist()}")
        else:
            print(f"   Sample raw values: {raw_strings[:5].tolist()}...")
    
    print()
    
    # Test 4: Recommend parsing strategy
    print("4️⃣ Recommended parsing strategy...")
    
    if duplicates_resolved > 0:
        print("   ✅ Use dtype={'PosIDLookupKey': 'str'} then pd.to_numeric() with Int64")
        print("   ✅ This preserves full 64-bit integer precision")
        
        # Test the fix on schema builder data type
        print()
        print("🔧 Database Schema Recommendation:")
        print("   Current: PosIDLookupKey REAL")
        print("   Better:  PosIDLookupKey INTEGER  -- Use INTEGER for 64-bit precision")
        
    else:
        print("   ❓ Precision may not be the issue - investigate further")
    
    return {
        'default_unique': int(posid_default.nunique()),
        'default_duplicates': int(len(posid_default) - posid_default.nunique()),
        'precision_unique': int(posid_int64.nunique()) if 'posid_int64' in locals() else 0,
        'precision_duplicates': int(len(posid_int64) - posid_int64.nunique()) if 'posid_int64' in locals() else 0,
        'duplicates_resolved': duplicates_resolved if 'duplicates_resolved' in locals() else 0
    }

if __name__ == "__main__":
    results = diagnose_precision_issue()
    
    # Save results (avoid JSON serialization issues)
    results_file = project_root / "posid_precision_diagnosis.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📝 Results saved to: {results_file}")