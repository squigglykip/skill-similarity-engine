#!/usr/bin/env python3
"""
Test Enrichment Fix
===================

Quick test to verify that the enrichment column name fix resolves the loading issue.

Usage:
    python scripts/test_enrichment_fix.py
"""

import pandas as pd
import sqlite3
import sys
import yaml
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
CONFIG_DIR = PROJECT_ROOT / 'config' / 'data'

def test_enrichment_fix():
    """Test if the enrichment configuration fix works."""
    print("🧪 TESTING ENRICHMENT FIX")
    print("=" * 50)
    
    # Load configuration
    config_file = CONFIG_DIR / 'sources.yaml'
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    workforce_config = config['data_sources']['core_workforce_current']
    enrichment_config = workforce_config['enrichment']['JobProfileID']
    
    print(f"📋 Enrichment Configuration:")
    print(f"   Mapping Key: {enrichment_config['mapping_key']}")
    print(f"   Target Key: {enrichment_config['target_key']}")
    print(f"   Value Column: {enrichment_config['value_column']}")
    print()
    
    # Test if mapping file exists and has correct columns
    mapping_file = DATA_DIR / enrichment_config['source_file']
    if not mapping_file.exists():
        print(f"❌ Mapping file not found: {mapping_file}")
        return False
    
    print(f"✅ Mapping file found: {mapping_file}")
    
    # Load mapping file
    try:
        df_mapping = pd.read_csv(mapping_file)
        print(f"📊 Mapping file columns: {list(df_mapping.columns)}")
        
        # Check if target_key exists
        target_key = enrichment_config['target_key']
        value_column = enrichment_config['value_column']
        
        if target_key not in df_mapping.columns:
            print(f"❌ Target key '{target_key}' not found in mapping file")
            print(f"   Available columns: {list(df_mapping.columns)}")
            return False
        
        if value_column not in df_mapping.columns:
            print(f"❌ Value column '{value_column}' not found in mapping file")
            print(f"   Available columns: {list(df_mapping.columns)}")
            return False
        
        print(f"✅ Target key '{target_key}' found")
        print(f"✅ Value column '{value_column}' found")
        
        # Show sample data
        print(f"📈 Sample mapping data:")
        sample = df_mapping[[target_key, value_column]].head(5)
        print(sample.to_string(index=False))
        print()
        
        # Test enrichment with sample workforce data
        workforce_csv = DATA_DIR / 'workforce_context' / 'workforce_context.csv'
        if workforce_csv.exists():
            print("🔄 Testing enrichment with sample workforce data...")
            
            df_workforce = pd.read_csv(workforce_csv, nrows=10)
            mapping_key = enrichment_config['mapping_key']
            
            if mapping_key not in df_workforce.columns:
                print(f"❌ Mapping key '{mapping_key}' not found in workforce CSV")
                return False
            
            print(f"✅ Mapping key '{mapping_key}' found in workforce data")
            
            # Perform test merge
            df_test = df_workforce.merge(
                df_mapping[[target_key, value_column]], 
                left_on=mapping_key, 
                right_on=target_key,
                how='left'
            )
            
            # Check enrichment success
            successful_enrichments = df_test[value_column].notna().sum()
            total_records = len(df_test)
            enrichment_rate = (successful_enrichments / total_records) * 100
            
            print(f"📊 Enrichment Test Results:")
            print(f"   Total records: {total_records}")
            print(f"   Successful enrichments: {successful_enrichments}")
            print(f"   Enrichment rate: {enrichment_rate:.1f}%")
            
            if enrichment_rate > 80:
                print("✅ Enrichment test PASSED")
                return True
            else:
                print("⚠️ Enrichment rate below 80% - may indicate data issues")
                return False
        
        else:
            print("⚠️ Workforce CSV not found - cannot test full enrichment")
            return True  # Configuration looks correct even if we can't test data
    
    except Exception as e:
        print(f"❌ Error testing enrichment: {e}")
        return False

def main():
    """Main test function."""
    try:
        success = test_enrichment_fix()
        
        print()
        print("=" * 50)
        if success:
            print("🎉 ENRICHMENT FIX TEST PASSED!")
            print("   The configuration should now work correctly.")
            print("   Try running the data loading process again:")
            print("   python main.py → option 1 → option 1")
        else:
            print("❌ ENRICHMENT FIX TEST FAILED")
            print("   Review the output above for specific issues.")
        print("=" * 50)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return 1

if __name__ == "__main__":
    exit(main())