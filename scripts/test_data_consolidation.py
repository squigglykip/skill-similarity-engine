#!/usr/bin/env python3
"""
Data Consolidation Test Script

This script compares the old duplicated data sources with the new comprehensive ones
to identify potential issues before fully committing to the data consolidation changes.

Comparisons:
1. input_data/job_data.csv vs job_architecture/dummy_job_architecture.csv
2. input_data/skill_data.csv vs skills_library/lightcast_skills_comprehensive.csv
3. Cross-validation with job_skill_mapping.csv

Tests for:
- Data completeness and coverage
- Duplicate records
- Null/missing values
- Schema compatibility
- Data quality issues
- Performance implications
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Any, Optional
import sys
import os
from collections import Counter

# Add the src directory to the Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataConsolidationTester:
    """Test suite for data consolidation changes."""
    
    def __init__(self, data_root: Optional[Path] = None):
        """Initialize the tester with data root directory."""
        self.data_root = data_root or (project_root / "data")
        self.results = {}
        
        # File paths
        self.old_job_file = self.data_root / "input_data" / "job_data.csv"
        self.new_job_file = self.data_root / "job_architecture" / "dummy_job_architecture.csv"
        self.old_skill_file = self.data_root / "input_data" / "skill_data.csv"
        self.new_skill_file = self.data_root / "skills_library" / "lightcast_skills_comprehensive.csv"
        self.mapping_file = self.data_root / "input_data" / "job_skill_mapping.csv"
        
        print(f"ðŸ” Data Consolidation Test Suite")
        print(f"ðŸ“ Data root: {self.data_root}")
        print(f"=" * 60)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all consolidation tests."""
        print("\nðŸš€ Starting comprehensive data consolidation tests...\n")
        
        # Test 1: File existence and basic stats
        self.test_file_existence()
        
        # Test 2: Job data comparison
        self.test_job_data_comparison()
        
        # Test 3: Skill data comparison
        self.test_skill_data_comparison()
        
        # Test 4: Job-skill mapping validation
        self.test_mapping_validation()
        
        # Test 5: Data quality checks
        self.test_data_quality()
        
        # Test 6: Performance implications
        self.test_performance_implications()
        
        # Generate summary report
        self.generate_summary_report()
        
        return self.results
    
    def test_file_existence(self):
        """Test that all required files exist and are readable."""
        print("ðŸ“‹ Test 1: File Existence and Basic Statistics")
        print("-" * 50)
        
        files_info = {}
        
        for name, file_path in [
            ("Old Job Data", self.old_job_file),
            ("New Job Data", self.new_job_file),
            ("Old Skill Data", self.old_skill_file),
            ("New Skill Data", self.new_skill_file),
            ("Job-Skill Mapping", self.mapping_file)
        ]:
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                try:
                    df = pd.read_csv(file_path, nrows=5)  # Just peek at structure
                    files_info[name] = {
                        "exists": True,
                        "size_mb": round(size_mb, 2),
                        "columns": list(df.columns),
                        "readable": True
                    }
                    print(f"âœ… {name}: {size_mb:.2f} MB, {len(df.columns)} columns")
                except Exception as e:
                    files_info[name] = {
                        "exists": True,
                        "size_mb": round(size_mb, 2),
                        "readable": False,
                        "error": str(e)
                    }
                    print(f"âŒ {name}: File exists but not readable - {e}")
            else:
                files_info[name] = {"exists": False}
                print(f"âŒ {name}: File not found at {file_path}")
        
        self.results["file_existence"] = files_info
        print()
    
    def test_job_data_comparison(self):
        """Compare old and new job data sources."""
        print("ðŸ’¼ Test 2: Job Data Comparison")
        print("-" * 50)
        
        try:
            # Load both job datasets
            old_jobs = pd.read_csv(self.old_job_file)
            new_jobs = pd.read_csv(self.new_job_file)
            
            print(f"ðŸ“Š Old job data: {len(old_jobs):,} rows, {len(old_jobs.columns)} columns")
            print(f"ðŸ“Š New job data: {len(new_jobs):,} rows, {len(new_jobs.columns)} columns")
            
            # Schema comparison
            print(f"\nðŸ” Schema Comparison:")
            print(f"Old columns: {list(old_jobs.columns)}")
            print(f"New columns: {list(new_jobs.columns)}")
            
            # Check for JobProfileID coverage
            old_job_ids = set()
            new_job_ids = set()
            
            # Extract job IDs from old data (JobProfileID)
            if 'JobProfileID' in old_jobs.columns:
                old_job_ids = set(old_jobs['JobProfileID'].dropna().astype(str))
            
            # Extract job IDs from new data (JobProfileID)
            if 'JobProfileID' in new_jobs.columns:
                new_job_ids = set(new_jobs['JobProfileID'].dropna().astype(str))
            
            # Coverage analysis
            common_ids = old_job_ids & new_job_ids
            old_only = old_job_ids - new_job_ids
            new_only = new_job_ids - old_job_ids
            
            print(f"\nðŸ“ˆ Job ID Coverage Analysis:")
            print(f"   Common job IDs: {len(common_ids):,}")
            print(f"   Only in old data: {len(old_only):,}")
            print(f"   Only in new data: {len(new_only):,}")
            print(f"   Coverage rate: {len(common_ids)/len(old_job_ids)*100:.1f}%" if old_job_ids else "N/A")
            
            # Sample of missing IDs
            if old_only:
                sample_missing = list(old_only)[:5]
                print(f"   Sample missing from new: {sample_missing}")
            
            # Check for duplicates
            old_duplicates = old_jobs.duplicated(subset=['JobProfileID']).sum() if 'JobProfileID' in old_jobs.columns else 0
            new_duplicates = new_jobs.duplicated(subset=['JobProfileID']).sum() if 'JobProfileID' in new_jobs.columns else 0
            
            print(f"\nðŸ” Duplicate Analysis:")
            print(f"   Old data duplicates: {old_duplicates}")
            print(f"   New data duplicates: {new_duplicates}")
            
            # Null value analysis
            print(f"\nðŸ•³ï¸  Null Value Analysis:")
            for col in ['JobProfileID', 'RoleSet', 'JobProfile', 'Job']:
                if col in old_jobs.columns:
                    nulls = old_jobs[col].isnull().sum()
                    print(f"   Old {col} nulls: {nulls} ({nulls/len(old_jobs)*100:.1f}%)")
                if col in new_jobs.columns:
                    nulls = new_jobs[col].isnull().sum()
                    print(f"   New {col} nulls: {nulls} ({nulls/len(new_jobs)*100:.1f}%)")
            
            self.results["job_comparison"] = {
                "old_count": len(old_jobs),
                "new_count": len(new_jobs),
                "common_ids": len(common_ids),
                "old_only": len(old_only),
                "new_only": len(new_only),
                "old_duplicates": old_duplicates,
                "new_duplicates": new_duplicates,
                "coverage_rate": len(common_ids)/len(old_job_ids)*100 if old_job_ids else 0
            }
            
        except Exception as e:
            print(f"âŒ Error in job data comparison: {e}")
            self.results["job_comparison"] = {"error": str(e)}
        
        print()
    
    def test_skill_data_comparison(self):
        """Compare old and new skill data sources."""
        print("ðŸŽ¯ Test 3: Skill Data Comparison")
        print("-" * 50)
        
        try:
            # Load both skill datasets
            old_skills = pd.read_csv(self.old_skill_file)
            new_skills = pd.read_csv(self.new_skill_file, low_memory=False)  # Large file
            
            print(f"ðŸ“Š Old skill data: {len(old_skills):,} rows, {len(old_skills.columns)} columns")
            print(f"ðŸ“Š New skill data: {len(new_skills):,} rows, {len(new_skills.columns)} columns")
            
            # Schema comparison
            print(f"\nðŸ” Schema Comparison:")
            print(f"Old columns: {list(old_skills.columns)}")
            print(f"New columns: {list(new_skills.columns)}")
            
            # Check for Skill ID coverage
            old_skill_ids = set()
            new_skill_ids = set()
            
            # Extract skill IDs from old data
            if 'Skill_ID' in old_skills.columns:
                old_skill_ids = set(old_skills['Skill_ID'].dropna().astype(str))
            
            # Extract skill IDs from new data
            if 'skill_id' in new_skills.columns:
                new_skill_ids = set(new_skills['skill_id'].dropna().astype(str))
            
            # Coverage analysis
            common_ids = old_skill_ids & new_skill_ids
            old_only = old_skill_ids - new_skill_ids
            new_only = new_skill_ids - old_skill_ids
            
            print(f"\nðŸ“ˆ Skill ID Coverage Analysis:")
            print(f"   Common skill IDs: {len(common_ids):,}")
            print(f"   Only in old data: {len(old_only):,}")
            print(f"   Only in new data: {len(new_only):,}")
            print(f"   Coverage rate: {len(common_ids)/len(old_skill_ids)*100:.1f}%" if old_skill_ids else "N/A")
            
            # Sample of missing IDs
            if old_only:
                sample_missing = list(old_only)[:5]
                print(f"   Sample missing from new: {sample_missing}")
            
            # Check for duplicates
            old_duplicates = old_skills.duplicated(subset=['Skill_ID']).sum() if 'Skill_ID' in old_skills.columns else 0
            new_duplicates = new_skills.duplicated(subset=['skill_id']).sum() if 'skill_id' in new_skills.columns else 0
            
            print(f"\nðŸ” Duplicate Analysis:")
            print(f"   Old data duplicates: {old_duplicates}")
            print(f"   New data duplicates: {new_duplicates}")
            
            # Skill type comparison
            print(f"\nðŸ·ï¸  Skill Type Analysis:")
            if 'SkillType' in old_skills.columns:
                old_types = old_skills['SkillType'].value_counts()
                print(f"   Old skill types: {dict(old_types)}")
            
            if 'type' in new_skills.columns:
                new_types = new_skills['type'].value_counts()
                print(f"   New skill types: {dict(new_types.head(10))}")  # Top 10 due to potential size
            
            # Null value analysis
            print(f"\nðŸ•³ï¸  Null Value Analysis:")
            for col in ['Skill_ID', 'Skill_Name', 'skill_id', 'name']:
                if col in old_skills.columns:
                    nulls = old_skills[col].isnull().sum()
                    print(f"   Old {col} nulls: {nulls} ({nulls/len(old_skills)*100:.1f}%)")
                if col in new_skills.columns:
                    nulls = new_skills[col].isnull().sum()
                    print(f"   New {col} nulls: {nulls} ({nulls/len(new_skills)*100:.1f}%)")
            
            self.results["skill_comparison"] = {
                "old_count": len(old_skills),
                "new_count": len(new_skills),
                "common_ids": len(common_ids),
                "old_only": len(old_only),
                "new_only": len(new_only),
                "old_duplicates": old_duplicates,
                "new_duplicates": new_duplicates,
                "coverage_rate": len(common_ids)/len(old_skill_ids)*100 if old_skill_ids else 0
            }
            
        except Exception as e:
            print(f"âŒ Error in skill data comparison: {e}")
            self.results["skill_comparison"] = {"error": str(e)}
        
        print()
    
    def test_mapping_validation(self):
        """Validate job-skill mapping against both old and new data sources."""
        print("ðŸ”— Test 4: Job-Skill Mapping Validation")
        print("-" * 50)
        
        try:
            # Load mapping file
            mapping = pd.read_csv(self.mapping_file)
            print(f"ðŸ“Š Job-skill mappings: {len(mapping):,} rows")
            
            # Load data sources for validation
            old_jobs = pd.read_csv(self.old_job_file)
            new_jobs = pd.read_csv(self.new_job_file)
            old_skills = pd.read_csv(self.old_skill_file)
            new_skills = pd.read_csv(self.new_skill_file, low_memory=False)
            
            # Extract IDs from mapping
            mapping_job_ids = set(mapping['JobProfileID'].dropna().astype(str))
            mapping_skill_ids = set(mapping['Skill_ID'].dropna().astype(str))
            
            print(f"ðŸ“ˆ Mapping Coverage:")
            print(f"   Unique jobs in mapping: {len(mapping_job_ids):,}")
            print(f"   Unique skills in mapping: {len(mapping_skill_ids):,}")
            
            # Validate against job data sources
            old_job_ids = set(old_jobs['JobProfileID'].dropna().astype(str)) if 'JobProfileID' in old_jobs.columns else set()
            new_job_ids = set(new_jobs['JobProfileID'].dropna().astype(str)) if 'JobProfileID' in new_jobs.columns else set()
            
            print(f"\nðŸŽ¯ Job ID Validation:")
            old_job_coverage = len(mapping_job_ids & old_job_ids) / len(mapping_job_ids) * 100 if mapping_job_ids else 0
            new_job_coverage = len(mapping_job_ids & new_job_ids) / len(mapping_job_ids) * 100 if mapping_job_ids else 0
            
            print(f"   Coverage in old job data: {old_job_coverage:.1f}%")
            print(f"   Coverage in new job data: {new_job_coverage:.1f}%")
            
            missing_from_old = mapping_job_ids - old_job_ids
            missing_from_new = mapping_job_ids - new_job_ids
            
            if missing_from_old:
                print(f"   Missing from old data: {len(missing_from_old):,} jobs")
                print(f"   Sample: {list(missing_from_old)[:5]}")
            
            if missing_from_new:
                print(f"   Missing from new data: {len(missing_from_new):,} jobs")
                print(f"   Sample: {list(missing_from_new)[:5]}")
            
            # Validate against skill data sources
            old_skill_ids = set(old_skills['Skill_ID'].dropna().astype(str)) if 'Skill_ID' in old_skills.columns else set()
            new_skill_ids = set(new_skills['skill_id'].dropna().astype(str)) if 'skill_id' in new_skills.columns else set()
            
            print(f"\nðŸŽ¯ Skill ID Validation:")
            old_skill_coverage = len(mapping_skill_ids & old_skill_ids) / len(mapping_skill_ids) * 100 if mapping_skill_ids else 0
            new_skill_coverage = len(mapping_skill_ids & new_skill_ids) / len(mapping_skill_ids) * 100 if mapping_skill_ids else 0
            
            print(f"   Coverage in old skill data: {old_skill_coverage:.1f}%")
            print(f"   Coverage in new skill data: {new_skill_coverage:.1f}%")
            
            missing_skills_old = mapping_skill_ids - old_skill_ids
            missing_skills_new = mapping_skill_ids - new_skill_ids
            
            if missing_skills_old:
                print(f"   Missing from old data: {len(missing_skills_old):,} skills")
                print(f"   Sample: {list(missing_skills_old)[:5]}")
            
            if missing_skills_new:
                print(f"   Missing from new data: {len(missing_skills_new):,} skills")
                print(f"   Sample: {list(missing_skills_new)[:5]}")
            
            # Duplicate analysis in mapping
            mapping_duplicates = mapping.duplicated(subset=['JobProfileID', 'Skill_ID']).sum()
            print(f"\nðŸ” Mapping Quality:")
            print(f"   Duplicate mappings: {mapping_duplicates}")
            
            # Null analysis
            job_nulls = mapping['JobProfileID'].isnull().sum()
            skill_nulls = mapping['Skill_ID'].isnull().sum()
            print(f"   Null JobProfileIDs: {job_nulls}")
            print(f"   Null Skill_IDs: {skill_nulls}")
            
            self.results["mapping_validation"] = {
                "total_mappings": len(mapping),
                "unique_jobs": len(mapping_job_ids),
                "unique_skills": len(mapping_skill_ids),
                "old_job_coverage": old_job_coverage,
                "new_job_coverage": new_job_coverage,
                "old_skill_coverage": old_skill_coverage,
                "new_skill_coverage": new_skill_coverage,
                "duplicates": mapping_duplicates,
                "job_nulls": job_nulls,
                "skill_nulls": skill_nulls
            }
            
        except Exception as e:
            print(f"âŒ Error in mapping validation: {e}")
            self.results["mapping_validation"] = {"error": str(e)}
        
        print()
    
    def test_data_quality(self):
        """Test data quality issues that could affect the consolidation."""
        print("ðŸ”¬ Test 5: Data Quality Analysis")
        print("-" * 50)
        
        quality_issues = {}
        
        try:
            # Load all datasets
            datasets = {
                "old_jobs": pd.read_csv(self.old_job_file),
                "new_jobs": pd.read_csv(self.new_job_file),
                "old_skills": pd.read_csv(self.old_skill_file),
                "new_skills": pd.read_csv(self.new_skill_file, low_memory=False),
                "mapping": pd.read_csv(self.mapping_file)
            }
            
            for name, df in datasets.items():
                issues = []
                
                # Check for completely empty rows
                empty_rows = df.isnull().all(axis=1).sum()
                if empty_rows > 0:
                    issues.append(f"Empty rows: {empty_rows}")
                
                # Check for rows with only whitespace in string columns
                string_cols = df.select_dtypes(include=['object']).columns
                for col in string_cols:
                    try:
                        # Only check if column has string-like data
                        if df[col].dtype == 'object' and not df[col].isnull().all():
                            whitespace_rows = df[col].astype(str).str.strip().eq('').sum()
                            if whitespace_rows > 0:
                                issues.append(f"Whitespace-only in {col}: {whitespace_rows}")
                    except Exception:
                        continue  # Skip columns that can't be processed as strings
                
                # Check for extremely long values that might cause issues
                for col in string_cols:
                    try:
                        if df[col].dtype == 'object' and not df[col].isnull().all():
                            max_length = df[col].astype(str).str.len().max()
                            if max_length > 1000:  # Arbitrary threshold
                                issues.append(f"Very long values in {col}: max {max_length} chars")
                    except Exception:
                        continue  # Skip columns that can't be processed as strings
                
                # Check for non-ASCII characters that might cause encoding issues
                for col in string_cols:
                    try:
                        if df[col].dtype == 'object' and not df[col].isnull().all():
                            non_ascii = df[col].astype(str).str.contains(r'[^\x00-\x7F]', na=False).sum()
                            if non_ascii > 0:
                                issues.append(f"Non-ASCII characters in {col}: {non_ascii} rows")
                    except Exception:
                        continue  # Skip columns that can't be processed as strings
                
                quality_issues[name] = issues
                
                if issues:
                    print(f"âš ï¸  {name}: {len(issues)} quality issues found")
                    for issue in issues:
                        print(f"     â€¢ {issue}")
                else:
                    print(f"âœ… {name}: No quality issues detected")
            
            self.results["data_quality"] = quality_issues
            
        except Exception as e:
            print(f"âŒ Error in data quality analysis: {e}")
            self.results["data_quality"] = {"error": str(e)}
        
        print()
    
    def test_performance_implications(self):
        """Test performance implications of using larger comprehensive datasets."""
        print("âš¡ Test 6: Performance Implications")
        print("-" * 50)
        
        try:
            import time
            
            performance_results = {}
            
            # Test loading times
            for name, file_path in [
                ("old_jobs", self.old_job_file),
                ("new_jobs", self.new_job_file),
                ("old_skills", self.old_skill_file),
                ("new_skills", self.new_skill_file)
            ]:
                if file_path.exists():
                    start_time = time.time()
                    df = pd.read_csv(file_path, low_memory=False)
                    load_time = time.time() - start_time
                    
                    memory_usage = df.memory_usage(deep=True).sum() / (1024 * 1024)  # MB
                    
                    performance_results[name] = {
                        "load_time_seconds": round(load_time, 3),
                        "memory_usage_mb": round(memory_usage, 2),
                        "rows": len(df),
                        "columns": len(df.columns)
                    }
                    
                    print(f"ðŸ“Š {name}:")
                    print(f"     Load time: {load_time:.3f} seconds")
                    print(f"     Memory usage: {memory_usage:.2f} MB")
                    print(f"     Rows/cols: {len(df):,} / {len(df.columns)}")
            
            # Calculate performance impact
            if "old_skills" in performance_results and "new_skills" in performance_results:
                old_time = performance_results["old_skills"]["load_time_seconds"]
                new_time = performance_results["new_skills"]["load_time_seconds"]
                time_increase = ((new_time - old_time) / old_time * 100) if old_time > 0 else 0
                
                old_memory = performance_results["old_skills"]["memory_usage_mb"]
                new_memory = performance_results["new_skills"]["memory_usage_mb"]
                memory_increase = ((new_memory - old_memory) / old_memory * 100) if old_memory > 0 else 0
                
                print(f"\nðŸ“ˆ Performance Impact (Skills):")
                print(f"     Load time increase: {time_increase:+.1f}%")
                print(f"     Memory usage increase: {memory_increase:+.1f}%")
            
            if "old_jobs" in performance_results and "new_jobs" in performance_results:
                old_time = performance_results["old_jobs"]["load_time_seconds"]
                new_time = performance_results["new_jobs"]["load_time_seconds"]
                time_increase = ((new_time - old_time) / old_time * 100) if old_time > 0 else 0
                
                old_memory = performance_results["old_jobs"]["memory_usage_mb"]
                new_memory = performance_results["new_jobs"]["memory_usage_mb"]
                memory_increase = ((new_memory - old_memory) / old_memory * 100) if old_memory > 0 else 0
                
                print(f"\nðŸ“ˆ Performance Impact (Jobs):")
                print(f"     Load time increase: {time_increase:+.1f}%")
                print(f"     Memory usage increase: {memory_increase:+.1f}%")
            
            self.results["performance"] = performance_results
            
        except Exception as e:
            print(f"âŒ Error in performance analysis: {e}")
            self.results["performance"] = {"error": str(e)}
        
        print()
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        print("ðŸ“‹ CONSOLIDATION TEST SUMMARY REPORT")
        print("=" * 60)
        
        # Overall assessment
        issues_found = []
        warnings = []
        
        # Check job data issues
        if "job_comparison" in self.results:
            job_result = self.results["job_comparison"]
            if "coverage_rate" in job_result and job_result["coverage_rate"] < 95:
                issues_found.append(f"Job ID coverage only {job_result['coverage_rate']:.1f}%")
            if "old_duplicates" in job_result and job_result["old_duplicates"] > 0:
                warnings.append(f"Old job data has {job_result['old_duplicates']} duplicates")
            if "new_duplicates" in job_result and job_result["new_duplicates"] > 0:
                issues_found.append(f"New job data has {job_result['new_duplicates']} duplicates")
        
        # Check skill data issues
        if "skill_comparison" in self.results:
            skill_result = self.results["skill_comparison"]
            if "coverage_rate" in skill_result and skill_result["coverage_rate"] < 90:
                issues_found.append(f"Skill ID coverage only {skill_result['coverage_rate']:.1f}%")
            if "old_duplicates" in skill_result and skill_result["old_duplicates"] > 0:
                warnings.append(f"Old skill data has {skill_result['old_duplicates']} duplicates")
            if "new_duplicates" in skill_result and skill_result["new_duplicates"] > 0:
                issues_found.append(f"New skill data has {skill_result['new_duplicates']} duplicates")
        
        # Check mapping issues
        if "mapping_validation" in self.results:
            mapping_result = self.results["mapping_validation"]
            if "new_job_coverage" in mapping_result and mapping_result["new_job_coverage"] < 95:
                issues_found.append(f"Job mapping coverage only {mapping_result['new_job_coverage']:.1f}%")
            if "new_skill_coverage" in mapping_result and mapping_result["new_skill_coverage"] < 90:
                issues_found.append(f"Skill mapping coverage only {mapping_result['new_skill_coverage']:.1f}%")
            if "duplicates" in mapping_result and mapping_result["duplicates"] > 0:
                warnings.append(f"Job-skill mapping has {mapping_result['duplicates']} duplicates")
        
        # Check data quality issues
        if "data_quality" in self.results:
            for dataset, issues in self.results["data_quality"].items():
                if isinstance(issues, list) and issues:
                    warnings.extend([f"{dataset}: {issue}" for issue in issues])
        
        # Overall recommendation
        print(f"\nðŸŽ¯ OVERALL ASSESSMENT:")
        
        if not issues_found and not warnings:
            print("âœ… CONSOLIDATION SAFE TO PROCEED")
            print("   No critical issues found. Data consolidation should work smoothly.")
        elif issues_found:
            print("âš ï¸  CONSOLIDATION NEEDS ATTENTION")
            print("   Critical issues found that should be addressed:")
            for issue in issues_found:
                print(f"   â€¢ {issue}")
        else:
            print("âš ï¸  CONSOLIDATION PROCEED WITH CAUTION")
            print("   Minor issues found but consolidation should still work:")
        
        if warnings:
            print(f"\nâš ï¸  Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"   â€¢ {warning}")
        
        # Recommendations
        print(f"\nðŸ’¡ RECOMMENDATIONS:")
        
        if "skill_comparison" in self.results:
            skill_result = self.results["skill_comparison"]
            if "coverage_rate" in skill_result and skill_result["coverage_rate"] < 100:
                missing_pct = 100 - skill_result["coverage_rate"]
                print(f"   â€¢ {missing_pct:.1f}% of old skills not in new dataset - verify this is expected")
        
        if "job_comparison" in self.results:
            job_result = self.results["job_comparison"]
            if "coverage_rate" in job_result and job_result["coverage_rate"] < 100:
                missing_pct = 100 - job_result["coverage_rate"]
                print(f"   â€¢ {missing_pct:.1f}% of old jobs not in new dataset - verify this is expected")
        
        print(f"   â€¢ Test the updated loaders with a small sample before full deployment")
        print(f"   â€¢ Monitor performance during initial runs with new data sources")
        print(f"   â€¢ Keep backup of old data files until consolidation is confirmed working")
        
        print(f"\n" + "=" * 60)


def main():
    """Run the data consolidation test suite."""
    tester = DataConsolidationTester()
    results = tester.run_all_tests()
    
    # Save results to file
    import json
    results_file = Path(__file__).parent / "data_consolidation_test_results.json"
    with open(results_file, 'w') as f:
        # Convert any non-serializable objects to strings
        serializable_results = {}
        for key, value in results.items():
            if isinstance(value, dict):
                serializable_results[key] = {k: str(v) if not isinstance(v, (int, float, str, bool, list)) else v 
                                           for k, v in value.items()}
            else:
                serializable_results[key] = str(value)
        json.dump(serializable_results, f, indent=2)
    
    print(f"\nðŸ’¾ Detailed results saved to: {results_file}")


if __name__ == "__main__":
    main() 
