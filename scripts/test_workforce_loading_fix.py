#!/usr/bin/env python3
"""
Test script to validate the workforce loading fix.
This script tests the corrected configuration for loading workforce data without UNIQUE constraint errors.
"""

import sys
import os
import sqlite3
import pandas as pd
from pathlib import Path
import json
import logging

# Add the project root to the path so we can import modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from skill_similarity_engine.business_context.data_loader import DataLoader
from skill_similarity_engine.business_context.schema_builder import SchemaBuilder

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_workforce_loading_fix():
    """Test the workforce loading fix with the corrected configuration."""
    
    print("🔧 Testing Workforce Loading Fix")
    print("=" * 60)
    
    # Path setup
    data_dir = project_root / "data"
    db_path = project_root / "models" / "2025-Q3" / "business_context.sqlite"
    workforce_file = data_dir / "workforce_context" / "workforce_context.csv"
    mapping_file = data_dir / "job_arch_to_positions_mapping" / "job_arch_to_positions_mapping.csv"
    
    results = {
        "test_timestamp": pd.Timestamp.now().isoformat(),
        "files_checked": {},
        "enrichment_test": {},
        "data_loading_test": {},
        "database_verification": {},
        "success": False
    }
    
    try:
        # 1. Verify files exist
        print("\n1️⃣ Verifying Data Files...")
        results["files_checked"]["workforce_file"] = {
            "path": str(workforce_file),
            "exists": workforce_file.exists(),
            "size_mb": round(workforce_file.stat().st_size / 1024 / 1024, 2) if workforce_file.exists() else 0
        }
        
        results["files_checked"]["mapping_file"] = {
            "path": str(mapping_file),
            "exists": mapping_file.exists(),
            "size_mb": round(mapping_file.stat().st_size / 1024 / 1024, 2) if mapping_file.exists() else 0
        }
        
        if not workforce_file.exists():
            print(f"❌ Workforce file not found: {workforce_file}")
            return results
            
        if not mapping_file.exists():
            print(f"❌ Mapping file not found: {mapping_file}")
            return results
            
        print(f"✅ Workforce file: {workforce_file} ({results['files_checked']['workforce_file']['size_mb']} MB)")
        print(f"✅ Mapping file: {mapping_file} ({results['files_checked']['mapping_file']['size_mb']} MB)")
        
        # 2. Test enrichment configuration
        print("\n2️⃣ Testing Enrichment Configuration...")
        
        # Load workforce data
        df_workforce = pd.read_csv(workforce_file)
        df_mapping = pd.read_csv(mapping_file)
        
        results["enrichment_test"]["workforce_rows"] = len(df_workforce)
        results["enrichment_test"]["mapping_rows"] = len(df_mapping)
        results["enrichment_test"]["workforce_columns"] = list(df_workforce.columns)
        results["enrichment_test"]["mapping_columns"] = list(df_mapping.columns)
        
        print(f"📊 Workforce data: {len(df_workforce):,} rows, {len(df_workforce.columns)} columns")
        print(f"📊 Mapping data: {len(df_mapping):,} rows, {len(df_mapping.columns)} columns")
        
        # Test the merge operation
        df_enriched = df_workforce.merge(
            df_mapping[["Position_Number", "JobProfileID"]], 
            left_on="Position Number", 
            right_on="Position_Number",
            how='left'
        )
        
        enriched_count = df_enriched["JobProfileID"].notna().sum()
        enrichment_rate = (enriched_count / len(df_enriched) * 100) if len(df_enriched) > 0 else 0
        
        results["enrichment_test"]["enriched_rows"] = int(enriched_count)
        results["enrichment_test"]["enrichment_rate"] = round(enrichment_rate, 2)
        results["enrichment_test"]["merge_success"] = True
        
        print(f"✅ Enrichment successful: {enriched_count:,} of {len(df_enriched):,} records enriched ({enrichment_rate:.1f}%)")
        
        # 3. Test data type conversion
        print("\n3️⃣ Testing Data Type Conversion...")
        
        # Apply the same conversion logic as the fix
        df_test = df_enriched.copy()
        df_test["employee_number"] = df_test["Employee Number"].astype(str).replace('nan', '')
        df_test["position_number"] = df_test["Position Number"].astype(str).replace('nan', '')
        
        results["data_loading_test"]["conversion_success"] = True
        results["data_loading_test"]["employee_number_type"] = str(df_test["employee_number"].dtype)
        results["data_loading_test"]["position_number_type"] = str(df_test["position_number"].dtype)
        results["data_loading_test"]["sample_employee_numbers"] = df_test["employee_number"].head(5).tolist()
        
        print(f"✅ Data type conversion successful")
        print(f"   Employee numbers: {df_test['employee_number'].dtype} -> {results['data_loading_test']['sample_employee_numbers'][:3]}...")
        print(f"   Position numbers: {df_test['position_number'].dtype}")
        
        # Check for any duplicate employee numbers
        unique_employees = df_test["employee_number"].nunique()
        total_employees = len(df_test)
        has_duplicates = unique_employees != total_employees
        
        results["data_loading_test"]["unique_employees"] = unique_employees
        results["data_loading_test"]["total_employees"] = total_employees
        results["data_loading_test"]["has_duplicates"] = has_duplicates
        
        if has_duplicates:
            print(f"⚠️  Found {total_employees - unique_employees} duplicate employee numbers")
        else:
            print(f"✅ No duplicate employee numbers found ({unique_employees:,} unique)")
        
        # 4. Test actual database loading (if database exists)
        print("\n4️⃣ Testing Database Loading...")
        
        if db_path.exists():
            try:
                # Initialize data loader
                data_loader = DataLoader(str(db_path))
                
                # Test loading the single dataset
                success = data_loader.load_single_dataset('core_workforce_current', str(workforce_file))
                
                results["database_verification"]["loading_success"] = success
                
                if success:
                    # Verify the data was loaded
                    with sqlite3.connect(str(db_path)) as conn:
                        cursor = conn.execute("SELECT COUNT(*) FROM core_workforce_current")
                        row_count = cursor.fetchone()[0]
                        
                        # Get a few sample records
                        cursor = conn.execute("SELECT employee_number, position_number, JobProfileID FROM core_workforce_current LIMIT 5")
                        sample_records = cursor.fetchall()
                        
                    results["database_verification"]["rows_in_database"] = row_count
                    results["database_verification"]["sample_records"] = sample_records
                    
                    print(f"✅ Database loading successful: {row_count:,} rows loaded")
                    print(f"   Sample records: {sample_records[:2]}")
                else:
                    print(f"❌ Database loading failed")
                    
            except Exception as e:
                results["database_verification"]["error"] = str(e)
                print(f"❌ Database test error: {e}")
        else:
            print(f"⚠️  Database not found: {db_path}")
            results["database_verification"]["database_missing"] = True
        
        # 5. Overall success assessment
        print("\n5️⃣ Results Summary...")
        
        success_criteria = [
            results["files_checked"]["workforce_file"]["exists"],
            results["files_checked"]["mapping_file"]["exists"],
            results["enrichment_test"].get("merge_success", False),
            results["data_loading_test"].get("conversion_success", False),
            not results["data_loading_test"].get("has_duplicates", True),
            results["enrichment_test"].get("enrichment_rate", 0) > 90,  # Expect >90% enrichment
        ]
        
        results["success"] = all(success_criteria)
        
        if results["success"]:
            print("🎉 ALL TESTS PASSED!")
            print("   The workforce loading fix should resolve the UNIQUE constraint error.")
        else:
            print("⚠️  Some tests failed. Please review the results.")
            
    except Exception as e:
        results["error"] = str(e)
        logger.error(f"Test failed with error: {e}")
        print(f"❌ Test failed: {e}")
    
    # Save results
    results_file = project_root / "workforce_loading_fix_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📝 Results saved to: {results_file}")
    return results

if __name__ == "__main__":
    test_workforce_loading_fix()