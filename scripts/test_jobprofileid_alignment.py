#!/usr/bin/env python3
"""
Test JobProfileID Alignment

This script verifies that the JobProfileIDs in the dummy job architecture data
perfectly match those in the job-skill mapping file, ensuring database queries
will work correctly.
"""

import pandas as pd
from pathlib import Path

def test_jobprofileid_alignment():
    """Test that JobProfileIDs are perfectly aligned between files"""
    
    # File paths
    base_dir = Path(__file__).parent.parent
    job_arch_file = base_dir / "data" / "job_architecture" / "dummy_job_architecture.csv"
    job_skill_mapping_file = base_dir / "data" / "input_data" / "job_skill_mapping.csv"
    
    print("ðŸ” JobProfileID Alignment Test")
    print("=" * 50)
    print(f"ðŸ“ Job Architecture: {job_arch_file.name}")
    print(f"ðŸ“ Job-Skill Mapping: {job_skill_mapping_file.name}")
    print()
    
    # Check if files exist
    if not job_arch_file.exists():
        print(f"âŒ ERROR: Job architecture file not found at {job_arch_file}")
        return False
        
    if not job_skill_mapping_file.exists():
        print(f"âŒ ERROR: Job-skill mapping file not found at {job_skill_mapping_file}")
        return False
    
    try:
        # Load both files
        print("ðŸ“Š Loading data files...")
        job_arch_df = pd.read_csv(job_arch_file)
        job_skill_df = pd.read_csv(job_skill_mapping_file)
        
        # Extract JobProfileIDs from both files
        arch_ids = set(job_arch_df['JobProfileID'].unique())
        mapping_ids = set(job_skill_df['JobProfileID'].unique())
        
        print(f"âœ… Job Architecture JobProfileIDs: {len(arch_ids):,}")
        print(f"âœ… Job-Skill Mapping JobProfileIDs: {len(mapping_ids):,}")
        print()
        
        # Test 1: Check if all job architecture IDs are in mapping
        print("ðŸŽ¯ Test 1: All Job Architecture IDs in Job-Skill Mapping")
        print("-" * 50)
        missing_in_mapping = arch_ids - mapping_ids
        
        if not missing_in_mapping:
            print("âœ… PASS: All job architecture JobProfileIDs found in mapping file")
        else:
            print(f"âŒ FAIL: {len(missing_in_mapping)} job architecture IDs missing from mapping:")
            for missing_id in sorted(list(missing_in_mapping)[:10]):  # Show first 10
                print(f"   â€¢ {missing_id}")
            if len(missing_in_mapping) > 10:
                print(f"   ... and {len(missing_in_mapping) - 10} more")
        print()
        
        # Test 2: Check if all mapping IDs are in job architecture
        print("ðŸŽ¯ Test 2: All Job-Skill Mapping IDs in Job Architecture")
        print("-" * 50)
        missing_in_arch = mapping_ids - arch_ids
        
        if not missing_in_arch:
            print("âœ… PASS: All job-skill mapping JobProfileIDs found in architecture file")
        else:
            print(f"âŒ FAIL: {len(missing_in_arch)} mapping IDs missing from job architecture:")
            for missing_id in sorted(list(missing_in_arch)[:10]):  # Show first 10
                print(f"   â€¢ {missing_id}")
            if len(missing_in_arch) > 10:
                print(f"   ... and {len(missing_in_arch) - 10} more")
        print()
        
        # Test 3: Perfect bidirectional match
        print("ðŸŽ¯ Test 3: Perfect Bidirectional Alignment")
        print("-" * 50)
        perfect_match = (len(missing_in_mapping) == 0) and (len(missing_in_arch) == 0)
        
        if perfect_match:
            print("âœ… PASS: Perfect bidirectional alignment!")
            print(f"   ðŸ“Š Both files contain exactly {len(arch_ids):,} matching JobProfileIDs")
        else:
            print("âŒ FAIL: JobProfileIDs are not perfectly aligned")
            print(f"   ðŸ“Š Intersection: {len(arch_ids & mapping_ids):,} IDs")
            print(f"   ðŸ“Š Only in architecture: {len(missing_in_mapping):,} IDs")
            print(f"   ðŸ“Š Only in mapping: {len(missing_in_arch):,} IDs")
        print()
        
        # Test 4: Sample comparison
        print("ðŸŽ¯ Test 4: Sample ID Comparison")
        print("-" * 50)
        common_ids = arch_ids & mapping_ids
        if common_ids:
            sample_ids = sorted(list(common_ids))[:5]
            print(f"âœ… Sample matching JobProfileIDs:")
            for sample_id in sample_ids:
                print(f"   â€¢ {sample_id}")
        else:
            print("âŒ No common JobProfileIDs found!")
        print()
        
        # Test 5: Duplicates check
        print("ðŸŽ¯ Test 5: Duplicate JobProfileIDs Check")
        print("-" * 50)
        
        arch_duplicates = job_arch_df['JobProfileID'].duplicated().sum()
        mapping_unique_count = job_skill_df['JobProfileID'].nunique()
        mapping_total_count = len(job_skill_df)
        
        if arch_duplicates == 0:
            print("âœ… PASS: No duplicate JobProfileIDs in job architecture")
        else:
            print(f"âŒ FAIL: {arch_duplicates} duplicate JobProfileIDs in job architecture")
            
        print(f"ðŸ“Š Job-skill mapping: {mapping_unique_count:,} unique IDs from {mapping_total_count:,} total rows")
        print()
        
        # Final summary
        print("ðŸ“‹ FINAL SUMMARY")
        print("=" * 50)
        if perfect_match and arch_duplicates == 0:
            print("ðŸŽ‰ SUCCESS: JobProfileID alignment is perfect!")
            print("   âœ… All job architecture IDs exist in job-skill mapping")
            print("   âœ… All job-skill mapping IDs exist in job architecture")
            print("   âœ… No duplicate JobProfileIDs in job architecture")
            print("   ðŸŽ¯ Database queries will work perfectly!")
            return True
        else:
            print("âš ï¸  WARNING: JobProfileID alignment issues detected!")
            if not perfect_match:
                print("   âŒ JobProfileIDs don't match perfectly between files")
            if arch_duplicates > 0:
                print("   âŒ Duplicate JobProfileIDs found in job architecture")
            print("   ðŸ”§ Please regenerate dummy job architecture data")
            return False
            
    except Exception as e:
        print(f"âŒ ERROR during alignment test: {e}")
        return False

def main():
    """Run the JobProfileID alignment test"""
    success = test_jobprofileid_alignment()
    
    if success:
        print("\nðŸš€ Ready for holistic data architecture restructure!")
    else:
        print("\nðŸ”§ Please fix alignment issues before proceeding.")
    
    return success

if __name__ == "__main__":
    main() 
