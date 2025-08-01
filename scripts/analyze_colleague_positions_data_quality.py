#!/usr/bin/env python3
"""
Comprehensive Data Quality Analysis for Colleague Positions History Files

This script analyzes all colleague positions history files to identify:
1. UNIQUE constraint violations in PosIDLookupKey
2. Data consistency across files
3. Expected vs actual data structure
4. Cross-file duplicate analysis
"""

import sys
import os
import pandas as pd
from pathlib import Path
import json
import logging
from collections import defaultdict
import glob

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_colleague_positions_data_quality():
    """Comprehensive analysis of colleague positions data quality."""
    
    print("🔍 Colleague Positions History Data Quality Analysis")
    print("=" * 80)
    
    # Setup paths
    data_dir = project_root / "data" / "colleague_positions_history"
    
    results = {
        "analysis_timestamp": pd.Timestamp.now().isoformat(),
        "files_analyzed": {},
        "cross_file_analysis": {},
        "unique_constraint_violations": {},
        "recommendations": [],
        "summary": {}
    }
    
    # Find all colleague position files
    pattern = str(data_dir / "d_colleague_position_fy*.csv")
    files = glob.glob(pattern)
    files.sort()
    
    if not files:
        print(f"❌ No colleague position files found in {data_dir}")
        return results
    
    print(f"📁 Found {len(files)} colleague position files:")
    for f in files:
        print(f"   - {Path(f).name}")
    print()
    
    # Analyze each file individually
    all_posid_lookup_keys = set()
    all_dataframes = {}
    
    for file_path in files:
        file_name = Path(file_path).name
        fy_year = file_name.replace('d_colleague_position_fy', '').replace('.csv', '')
        
        print(f"📊 Analyzing {file_name}...")
        
        try:
            df = pd.read_csv(file_path, low_memory=False)
            all_dataframes[fy_year] = df
            
            file_analysis = {
                "file_path": file_path,
                "total_rows": len(df),
                "columns": list(df.columns),
                "column_count": len(df.columns)
            }
            
            # Analyze PosIDLookupKey specifically
            if 'PosIDLookupKey' in df.columns:
                posid_values = df['PosIDLookupKey']
                unique_posids = posid_values.nunique()
                total_posids = len(posid_values)
                
                file_analysis["posid_analysis"] = {
                    "total_posid_entries": total_posids,
                    "unique_posid_entries": unique_posids,
                    "duplicates_within_file": total_posids - unique_posids,
                    "has_internal_duplicates": total_posids != unique_posids,
                    "null_posids": posid_values.isnull().sum(),
                    "sample_posids": posid_values.dropna().head(5).tolist()
                }
                
                # Check for duplicates within this file
                if file_analysis["posid_analysis"]["has_internal_duplicates"]:
                    duplicate_posids = posid_values.value_counts()
                    duplicate_posids = duplicate_posids[duplicate_posids > 1]
                    
                    file_analysis["posid_analysis"]["duplicate_details"] = {
                        "count_of_duplicated_posids": len(duplicate_posids),
                        "top_duplicates": duplicate_posids.head(10).to_dict(),
                        "max_duplicate_count": duplicate_posids.max()
                    }
                    
                    print(f"   ⚠️  INTERNAL DUPLICATES: {len(duplicate_posids)} PosIDLookupKey values appear multiple times")
                    print(f"      Most duplicated: {duplicate_posids.index[0]} appears {duplicate_posids.iloc[0]} times")
                
                # Track all PosIDLookupKey values across files
                current_posids = set(posid_values.dropna())
                overlap_with_previous = all_posid_lookup_keys.intersection(current_posids)
                
                if overlap_with_previous:
                    file_analysis["posid_analysis"]["cross_file_duplicates"] = {
                        "count": len(overlap_with_previous),
                        "sample_overlapping_posids": list(overlap_with_previous)[:10]
                    }
                    print(f"   ⚠️  CROSS-FILE DUPLICATES: {len(overlap_with_previous)} PosIDLookupKey values already seen in previous files")
                
                all_posid_lookup_keys.update(current_posids)
                
            else:
                print(f"   ❌ PosIDLookupKey column not found!")
                file_analysis["posid_analysis"] = {"error": "PosIDLookupKey column missing"}
            
            # Analyze other key columns
            key_columns = ['Week Ending', 'Employee Number', 'Operational', 'Position Start Date']
            for col in key_columns:
                if col in df.columns:
                    col_analysis = {
                        "unique_values": df[col].nunique(),
                        "null_count": df[col].isnull().sum(),
                        "data_type": str(df[col].dtype)
                    }
                    
                    if col == 'Week Ending':
                        col_analysis["date_range"] = {
                            "min_date": str(df[col].min()),
                            "max_date": str(df[col].max()),
                            "unique_weeks": df[col].nunique()
                        }
                    elif col == 'Employee Number':
                        col_analysis["unique_employees"] = df[col].nunique()
                        col_analysis["sample_employees"] = df[col].dropna().head(5).tolist()
                    
                    file_analysis[f"{col.lower().replace(' ', '_')}_analysis"] = col_analysis
            
            results["files_analyzed"][fy_year] = file_analysis
            print(f"   ✅ {len(df):,} rows, {len(df.columns)} columns")
            
        except Exception as e:
            print(f"   ❌ Error analyzing {file_name}: {e}")
            results["files_analyzed"][fy_year] = {"error": str(e)}
    
    # Cross-file analysis
    print(f"\n🔗 Cross-File Analysis...")
    
    if all_dataframes:
        results["cross_file_analysis"] = {
            "total_files_analyzed": len(all_dataframes),
            "total_unique_posids_across_all_files": len(all_posid_lookup_keys),
            "years_covered": list(all_dataframes.keys())
        }
        
        # Check schema consistency
        first_file_columns = None
        schema_consistent = True
        
        for fy_year, df in all_dataframes.items():
            if first_file_columns is None:
                first_file_columns = set(df.columns)
            else:
                if set(df.columns) != first_file_columns:
                    schema_consistent = False
                    print(f"   ⚠️  Schema inconsistency in FY{fy_year}")
        
        results["cross_file_analysis"]["schema_consistent"] = schema_consistent
        
        if schema_consistent:
            print(f"   ✅ All files have consistent schema: {len(first_file_columns)} columns")
        
        # Analyze the expected database constraint
        print(f"\n🗄️  Database Constraint Analysis...")
        
        # The issue: PosIDLookupKey should be unique across ALL files when loaded into single table
        total_posid_entries = sum(len(df) for df in all_dataframes.values() if 'PosIDLookupKey' in df.columns)
        unique_posid_entries = len(all_posid_lookup_keys)
        
        constraint_violation_count = total_posid_entries - unique_posid_entries
        
        results["unique_constraint_violations"] = {
            "total_posid_entries_across_all_files": total_posid_entries,
            "unique_posid_entries_across_all_files": unique_posid_entries,
            "constraint_violations": constraint_violation_count,
            "would_cause_database_failure": constraint_violation_count > 0
        }
        
        if constraint_violation_count > 0:
            print(f"   ❌ UNIQUE CONSTRAINT VIOLATION DETECTED!")
            print(f"      Total PosIDLookupKey entries across all files: {total_posid_entries:,}")
            print(f"      Unique PosIDLookupKey values: {unique_posid_entries:,}")
            print(f"      Duplicate entries: {constraint_violation_count:,}")
            print(f"      This explains the database loading failure!")
            
            results["recommendations"].append("Remove duplicate PosIDLookupKey entries across all colleague position files")
            results["recommendations"].append("Investigate why the same PosIDLookupKey appears in multiple files")
            results["recommendations"].append("Consider if PosIDLookupKey + Week Ending should be the composite primary key instead")
        else:
            print(f"   ✅ No UNIQUE constraint violations detected")
    
    # Generate recommendations
    print(f"\n💡 Recommendations...")
    
    for rec in results["recommendations"]:
        print(f"   • {rec}")
    
    if not results["recommendations"]:
        print("   ✅ No specific recommendations - data appears clean for database loading")
    
    # Summary
    results["summary"] = {
        "files_processed": len(results["files_analyzed"]),
        "total_rows_across_files": sum(fa.get("total_rows", 0) for fa in results["files_analyzed"].values() if isinstance(fa, dict)),
        "constraint_violations_found": results.get("unique_constraint_violations", {}).get("constraint_violations", 0) > 0,
        "schema_consistent": results.get("cross_file_analysis", {}).get("schema_consistent", False),
        "ready_for_database_loading": (
            results.get("unique_constraint_violations", {}).get("constraint_violations", 0) == 0 and
            results.get("cross_file_analysis", {}).get("schema_consistent", False)
        )
    }
    
    print(f"\n📋 Summary:")
    print(f"   Files processed: {results['summary']['files_processed']}")
    print(f"   Total rows: {results['summary']['total_rows_across_files']:,}")
    print(f"   Schema consistent: {results['summary']['schema_consistent']}")
    print(f"   Constraint violations: {results['summary']['constraint_violations_found']}")
    print(f"   Ready for database loading: {results['summary']['ready_for_database_loading']}")
    
    # Save results
    results_file = project_root / "colleague_positions_data_quality_analysis.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    analyze_colleague_positions_data_quality()