#!/usr/bin/env python3
"""
CSV Schema Analysis Tool

Detailed analysis of CSV file schemas to understand data structure,
especially focusing on PosIDLookupKey relationships between tables.

Usage: python scripts/analyze_csv_schemas.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from typing import Dict, List, Any, Set

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

def analyze_csv_file(csv_path: Path) -> Dict[str, Any]:
    """Analyze a single CSV file and return detailed schema information."""
    
    print(f"\n🔍 ANALYZING: {csv_path.name}")
    print("=" * 80)
    
    try:
        # Read the CSV
        df = pd.read_csv(csv_path)
        
        analysis = {
            'file_path': str(csv_path),
            'file_name': csv_path.name,
            'file_size_mb': csv_path.stat().st_size / (1024 * 1024),
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': {},
            'sample_data': {},
            'posid_analysis': {}
        }
        
        print(f"📊 Dimensions: {len(df):,} rows × {len(df.columns)} columns")
        print(f"📁 File size: {analysis['file_size_mb']:.2f} MB")
        
        # Analyze each column
        print(f"\n📋 COLUMN ANALYSIS:")
        print(f"{'Column Name':<30} {'Type':<15} {'Nulls':<8} {'Unique':<10} {'Sample Values'}")
        print("-" * 100)
        
        for col in df.columns:
            col_data = df[col]
            
            # Basic stats
            null_count = col_data.isnull().sum()
            null_pct = (null_count / len(df)) * 100
            unique_count = col_data.nunique()
            
            # Sample values (non-null)
            sample_values = col_data.dropna().head(5).tolist()
            sample_str = ", ".join([str(v)[:20] + "..." if len(str(v)) > 20 else str(v) for v in sample_values])
            
            # Store in analysis
            analysis['columns'][col] = {
                'dtype': str(col_data.dtype),
                'null_count': null_count,
                'null_percentage': null_pct,
                'unique_count': unique_count,
                'sample_values': sample_values
            }
            
            print(f"{col:<30} {str(col_data.dtype):<15} {null_pct:>6.1f}% {unique_count:>8,} {sample_str}")
        
        # Special analysis for PosIDLookupKey column
        if 'PosIDLookupKey' in df.columns:
            print(f"\n🔍 POSIDLOOKUPKEY DETAILED ANALYSIS:")
            posid_col = df['PosIDLookupKey']
            
            analysis['posid_analysis'] = {
                'count': len(posid_col),
                'unique_count': posid_col.nunique(),
                'min_value': float(posid_col.min()),
                'max_value': float(posid_col.max()),
                'mean_value': float(posid_col.mean()),
                'std_value': float(posid_col.std()),
                'sample_values': posid_col.head(10).tolist(),
                'value_ranges': {}
            }
            
            print(f"   Total values: {len(posid_col):,}")
            print(f"   Unique values: {posid_col.nunique():,}")
            print(f"   Range: {posid_col.min():,.0f} to {posid_col.max():,.0f}")
            print(f"   Mean: {posid_col.mean():,.0f}")
            print(f"   Std Dev: {posid_col.std():,.0f}")
            
            # Analyze value distribution
            print(f"\n   📊 Value Distribution:")
            ranges = [
                (100000000000, 150000000000, "100B-150B"),
                (150000000000, 200000000000, "150B-200B"),
                (200000000000, 250000000000, "200B-250B"),
                (250000000000, 300000000000, "250B-300B"),
            ]
            
            for min_val, max_val, label in ranges:
                count = len(posid_col[(posid_col >= min_val) & (posid_col < max_val)])
                pct = (count / len(posid_col)) * 100
                analysis['posid_analysis']['value_ranges'][label] = {
                    'count': count,
                    'percentage': pct
                }
                print(f"      {label}: {count:,} values ({pct:.1f}%)")
            
            print(f"\n   🎯 Sample PosIDLookupKey values:")
            for i, val in enumerate(posid_col.head(10)):
                print(f"      {i+1:2d}: {val:>20,.0f}")
        
        # Special analysis for Position Number column
        if 'Position Number' in df.columns:
            print(f"\n🔍 POSITION NUMBER DETAILED ANALYSIS:")
            pos_col = df['Position Number']
            
            print(f"   Total values: {len(pos_col):,}")
            print(f"   Unique values: {pos_col.nunique():,}")
            print(f"   Range: {pos_col.min():,} to {pos_col.max():,}")
            print(f"   Sample values: {pos_col.head(10).tolist()}")
        
        # Sample data for first 3 rows
        print(f"\n📝 SAMPLE DATA (first 3 rows):")
        print("-" * 80)
        for i in range(min(3, len(df))):
            print(f"Row {i+1}:")
            for col in df.columns:
                value = df.iloc[i][col]
                print(f"  {col}: {value}")
            print()
            
            analysis['sample_data'][f'row_{i+1}'] = df.iloc[i].to_dict()
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error analyzing {csv_path}: {e}")
        return {'error': str(e)}

def compare_posid_keys(colleague_file: Path, position_file: Path):
    """Compare PosIDLookupKey values between colleague and position files."""
    
    print(f"\n🔄 COMPARING POSIDLOOKUPKEY VALUES")
    print("=" * 80)
    
    try:
        # Load PosIDLookupKey from both files
        print("📊 Loading colleague positions PosIDLookupKey...")
        colleague_df = pd.read_csv(colleague_file)
        colleague_posids = set(colleague_df['PosIDLookupKey'].astype(float))
        
        print("📊 Loading position history PosIDLookupKey...")
        position_df = pd.read_csv(position_file)
        position_posids = set(position_df['PosIDLookupKey'].astype(float))
        
        # Calculate overlap
        overlap = colleague_posids.intersection(position_posids)
        colleague_only = colleague_posids - position_posids
        position_only = position_posids - colleague_posids
        
        print(f"\n📊 OVERLAP ANALYSIS:")
        print(f"   Colleague file unique PosIDs: {len(colleague_posids):,}")
        print(f"   Position file unique PosIDs: {len(position_posids):,}")
        print(f"   Overlapping PosIDs: {len(overlap):,}")
        print(f"   Colleague-only PosIDs: {len(colleague_only):,}")
        print(f"   Position-only PosIDs: {len(position_only):,}")
        
        if len(colleague_posids) > 0:
            overlap_rate = (len(overlap) / len(colleague_posids)) * 100
            print(f"   Overlap rate: {overlap_rate:.2f}%")
        
        # Show sample overlapping values
        if overlap:
            print(f"\n✅ SAMPLE OVERLAPPING POSIDLOOKUPKEYS:")
            sample_overlap = list(overlap)[:10]
            for i, posid in enumerate(sample_overlap):
                print(f"      {i+1:2d}: {posid:>20,.0f}")
        
        # Show sample non-overlapping values
        if colleague_only:
            print(f"\n❌ SAMPLE COLLEAGUE-ONLY POSIDLOOKUPKEYS:")
            sample_colleague_only = list(colleague_only)[:5]
            for i, posid in enumerate(sample_colleague_only):
                print(f"      {i+1:2d}: {posid:>20,.0f}")
        
        if position_only:
            print(f"\n❌ SAMPLE POSITION-ONLY POSIDLOOKUPKEYS:")
            sample_position_only = list(position_only)[:5]
            for i, posid in enumerate(sample_position_only):
                print(f"      {i+1:2d}: {posid:>20,.0f}")
        
        # Analyze ranges
        print(f"\n📊 RANGE ANALYSIS:")
        colleague_min, colleague_max = min(colleague_posids), max(colleague_posids)
        position_min, position_max = min(position_posids), max(position_posids)
        
        print(f"   Colleague range: {colleague_min:>20,.0f} to {colleague_max:>20,.0f}")
        print(f"   Position range:  {position_min:>20,.0f} to {position_max:>20,.0f}")
        print(f"   Ranges overlap: {colleague_min <= position_max and position_min <= colleague_max}")
        
        return {
            'colleague_count': len(colleague_posids),
            'position_count': len(position_posids),
            'overlap_count': len(overlap),
            'overlap_rate': (len(overlap) / len(colleague_posids)) * 100 if colleague_posids else 0,
            'colleague_range': (colleague_min, colleague_max),
            'position_range': (position_min, position_max)
        }
        
    except Exception as e:
        print(f"❌ Error comparing PosIDLookupKeys: {e}")
        return {'error': str(e)}

def main():
    """Main function to analyze CSV schemas."""
    
    print("🔍 CSV SCHEMA ANALYSIS TOOL")
    print("=" * 80)
    print(f"📂 Project root: {PROJECT_ROOT}")
    
    # Define files to analyze
    files_to_analyze = [
        "data/colleague_positions_history/d_colleague_position_fy22.csv",
        "data/positions_history/d_positions_fy22.csv",
    ]
    
    analyses = {}
    
    # Analyze each file
    for file_rel_path in files_to_analyze:
        file_path = PROJECT_ROOT / file_rel_path
        
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            continue
        
        analysis = analyze_csv_file(file_path)
        analyses[file_rel_path] = analysis
    
    # Compare PosIDLookupKey values between the two main files
    colleague_file = PROJECT_ROOT / "data/colleague_positions_history/d_colleague_position_fy22.csv"
    position_file = PROJECT_ROOT / "data/positions_history/d_positions_fy22.csv"
    
    if colleague_file.exists() and position_file.exists():
        comparison = compare_posid_keys(colleague_file, position_file)
    
    # Summary
    print(f"\n📈 SUMMARY")
    print("=" * 80)
    
    for file_path, analysis in analyses.items():
        if 'error' in analysis:
            print(f"❌ {file_path}: Error - {analysis['error']}")
        else:
            print(f"✅ {file_path}:")
            print(f"   📊 {analysis['row_count']:,} rows × {analysis['column_count']} columns")
            print(f"   📁 {analysis['file_size_mb']:.2f} MB")
            
            if 'posid_analysis' in analysis and analysis['posid_analysis']:
                posid = analysis['posid_analysis']
                print(f"   🔑 PosIDLookupKey: {posid['unique_count']:,} unique values")
                print(f"      Range: {posid['min_value']:,.0f} to {posid['max_value']:,.0f}")

if __name__ == "__main__":
    main()