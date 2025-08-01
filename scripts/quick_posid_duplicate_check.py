#!/usr/bin/env python3
"""
Quick check to confirm PosIDLookupKey duplicates across colleague position files
"""

import pandas as pd
from pathlib import Path
import glob

project_root = Path(__file__).parent.parent
data_dir = project_root / "data" / "colleague_positions_history"

print("🔍 Quick PosIDLookupKey Duplicate Analysis")
print("=" * 50)

# Find all files
files = glob.glob(str(data_dir / "d_colleague_position_fy*.csv"))
files.sort()

all_posids = []
file_posids = {}

for file_path in files:
    file_name = Path(file_path).name
    fy = file_name.replace('d_colleague_position_fy', '').replace('.csv', '')
    
    print(f"📁 {file_name}...")
    
    try:
        df = pd.read_csv(file_path, low_memory=False)
        posids = df['PosIDLookupKey'].dropna().tolist()
        file_posids[fy] = set(posids)
        all_posids.extend(posids)
        
        print(f"   Rows: {len(df):,}")
        print(f"   PosIDLookupKey values: {len(posids):,}")
        print(f"   Unique PosIDLookupKey: {len(set(posids)):,}")
        
        # Check internal duplicates
        internal_dupes = len(posids) - len(set(posids))
        if internal_dupes > 0:
            print(f"   ⚠️  Internal duplicates: {internal_dupes}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

print(f"\n🔗 Cross-File Analysis:")
print(f"Total PosIDLookupKey entries: {len(all_posids):,}")
print(f"Unique PosIDLookupKey values: {len(set(all_posids)):,}")
print(f"Cross-file duplicates: {len(all_posids) - len(set(all_posids)):,}")

if len(all_posids) != len(set(all_posids)):
    print(f"\n❌ CONFIRMED: PosIDLookupKey values appear in multiple files!")
    print(f"   This causes UNIQUE constraint failures when loading into single table.")
    
    # Find which years have overlapping PosIDs
    years = list(file_posids.keys())
    for i, year1 in enumerate(years):
        for year2 in years[i+1:]:
            overlap = file_posids[year1].intersection(file_posids[year2])
            if overlap:
                print(f"   FY{year1} ∩ FY{year2}: {len(overlap):,} shared PosIDLookupKey values")
else:
    print(f"\n✅ No cross-file duplicates found")