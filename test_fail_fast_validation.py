#!/usr/bin/env python3
"""
Fail-Fast Validation Test Script
================================

Tests to validate that we're getting real calculated values vs hardcoded defaults.
Run this before and after implementing fail-fast fixes to compare behavior.
"""

import sqlite3
import pandas as pd
from pathlib import Path
import json

def test_hardcoded_values_detection():
    """Detect if we have hardcoded values masquerading as calculations."""
    print("🔍 Testing for Hardcoded Business Intelligence Values")
    print("=" * 60)
    
    db_path = Path("models/2025-Q3/business_context.sqlite")
    if not db_path.exists():
        print("❌ Database not found. Run analytics pipeline first.")
        return False
    
    with sqlite3.connect(db_path) as conn:
        # Test 1: Job Family Characteristics - Check for identical hardcoded values
        print("\n📊 Test 1: Job Family Characteristics")
        query = """
        SELECT 
            business_value_score,
            career_pathway_potential,
            skill_transferability,
            market_demand_level,
            typical_career_stage,
            COUNT(*) as count
        FROM analytics_job_family_characteristics 
        GROUP BY business_value_score, career_pathway_potential, 
                 skill_transferability, market_demand_level, typical_career_stage
        ORDER BY count DESC
        """
        
        df = pd.read_sql_query(query, conn)
        if len(df) > 0:
            print(f"   Records found: {df['count'].sum()}")
            print(f"   Unique value combinations: {len(df)}")
            
            # Check for suspicious patterns (all identical values)
            if len(df) == 1:
                print("   🚨 ISSUE: All records have identical values (likely hardcoded)")
                print(f"   Values: business_value={df.iloc[0]['business_value_score']}, "
                      f"career_pathway='{df.iloc[0]['career_pathway_potential']}', "
                      f"skill_transferability={df.iloc[0]['skill_transferability']}")
            else:
                print("   ✅ Multiple value combinations found (suggests real calculations)")
        else:
            print("   ⚠️ No records found")
            
        # Test 2: Bundle Characteristics - Check for null critical fields
        print("\n📊 Test 2: Bundle Characteristics - Missing Calculations")
        query = """
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN intra_bundle_cohesion IS NULL THEN 1 ELSE 0 END) as null_cohesion,
            SUM(CASE WHEN inter_bundle_separation IS NULL THEN 1 ELSE 0 END) as null_separation,
            SUM(CASE WHEN common_job_families IS NULL THEN 1 ELSE 0 END) as null_job_families,
            SUM(CASE WHEN typical_career_stage IS NULL THEN 1 ELSE 0 END) as null_career_stage
        FROM analytics_bundle_characteristics
        """
        
        df = pd.read_sql_query(query, conn)
        if len(df) > 0 and df.iloc[0]['total_records'] > 0:
            total = df.iloc[0]['total_records']
            null_cohesion = df.iloc[0]['null_cohesion']
            null_separation = df.iloc[0]['null_separation']
            null_job_families = df.iloc[0]['null_job_families']
            null_career_stage = df.iloc[0]['null_career_stage']
            
            print(f"   Total bundle records: {total}")
            print(f"   Missing cohesion calculation: {null_cohesion}/{total} ({null_cohesion/total*100:.1f}%)")
            print(f"   Missing separation calculation: {null_separation}/{total} ({null_separation/total*100:.1f}%)")
            print(f"   Missing job families analysis: {null_job_families}/{total} ({null_job_families/total*100:.1f}%)")
            print(f"   Missing career stage analysis: {null_career_stage}/{total} ({null_career_stage/total*100:.1f}%)")
            
            if null_cohesion > 0 or null_separation > 0:
                print("   🚨 ISSUE: Critical calculation fields are null")
            else:
                print("   ✅ All critical calculation fields populated")
        else:
            print("   ⚠️ No bundle characteristic records found")
            
        # Test 3: Movement Patterns - Check for missing success metrics
        print("\n📊 Test 3: Movement Patterns - Missing Success Metrics")
        query = """
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN skill_similarity_score IS NULL THEN 1 ELSE 0 END) as null_similarity,
            SUM(CASE WHEN difficulty_score IS NULL THEN 1 ELSE 0 END) as null_difficulty,
            SUM(CASE WHEN success_rate IS NULL THEN 1 ELSE 0 END) as null_success_rate
        FROM analytics_movement_patterns
        LIMIT 1000  -- Sample for performance
        """
        
        df = pd.read_sql_query(query, conn)
        if len(df) > 0 and df.iloc[0]['total_records'] > 0:
            total = df.iloc[0]['total_records']
            null_similarity = df.iloc[0]['null_similarity']
            null_difficulty = df.iloc[0]['null_difficulty']
            null_success_rate = df.iloc[0]['null_success_rate']
            
            print(f"   Total movement records (sample): {total}")
            print(f"   Missing similarity scores: {null_similarity}/{total} ({null_similarity/total*100:.1f}%)")
            print(f"   Missing difficulty scores: {null_difficulty}/{total} ({null_difficulty/total*100:.1f}%)")
            print(f"   Missing success rates: {null_success_rate}/{total} ({null_success_rate/total*100:.1f}%)")
            
            if null_similarity == total and null_difficulty == total and null_success_rate == total:
                print("   🚨 ISSUE: All movement success metrics are missing")
            else:
                print("   ✅ Some movement success metrics are populated")
        else:
            print("   ⚠️ No movement pattern records found")

def test_configuration_dependency():
    """Test if clustering fails appropriately without proper configuration."""
    print("\n🔧 Testing Configuration Dependency")
    print("=" * 40)
    
    try:
        # Try to import and initialize clustering analyzer
        from src.skill_similarity_engine.models.clustering_analyzer import JobProfileClusterer
        
        # This should either work (if config is proper) or fail explicitly (good)
        # It should NOT silently use defaults
        clusterer = JobProfileClusterer()
        
        print(f"   ✅ Clustering initialized successfully")
        print(f"   Algorithm: {clusterer.algorithm}")
        print(f"   Eps: {clusterer.eps}")
        print(f"   Min samples: {clusterer.min_samples}")
        
        # Check if these look like defaults (potential issue)
        if clusterer.eps == 0.1 and clusterer.min_samples == 2:
            print("   ⚠️ WARNING: Using default parameters - check if optimization was run")
        
    except Exception as e:
        print(f"   🚨 Configuration Error: {e}")
        print("   This could be good (fail-fast) or bad (missing setup)")

def test_calculation_variance():
    """Test if calculated values show realistic variance."""
    print("\n📈 Testing Calculation Variance")
    print("=" * 35)
    
    db_path = Path("models/2025-Q3/business_context.sqlite")
    if not db_path.exists():
        print("❌ Database not found.")
        return False
        
    with sqlite3.connect(db_path) as conn:
        # Test variance in business value scores
        query = """
        SELECT 
            MIN(business_value_score) as min_score,
            MAX(business_value_score) as max_score,
            AVG(business_value_score) as avg_score,
            COUNT(DISTINCT business_value_score) as unique_scores
        FROM analytics_bundle_characteristics
        WHERE business_value_score IS NOT NULL
        """
        
        df = pd.read_sql_query(query, conn)
        if len(df) > 0 and df.iloc[0]['unique_scores'] is not None:
            min_score = df.iloc[0]['min_score']
            max_score = df.iloc[0]['max_score']
            avg_score = df.iloc[0]['avg_score']
            unique_scores = df.iloc[0]['unique_scores']
            
            print(f"   Business Value Scores:")
            print(f"     Range: {min_score:.3f} - {max_score:.3f}")
            print(f"     Average: {avg_score:.3f}")
            print(f"     Unique values: {unique_scores}")
            
            if unique_scores == 1:
                print("   🚨 ISSUE: All business value scores are identical (likely hardcoded)")
            elif max_score - min_score < 0.1:
                print("   ⚠️ WARNING: Very little variance in scores (check calculation logic)")
            else:
                print("   ✅ Good variance in business value scores")
        else:
            print("   ⚠️ No business value scores found")

def main():
    """Run all validation tests."""
    print("🚨 FAIL-FAST VALIDATION TEST SUITE")
    print("==================================")
    print("Testing current state of business intelligence calculations...")
    print()
    
    test_hardcoded_values_detection()
    test_configuration_dependency()
    test_calculation_variance()
    
    print("\n" + "=" * 60)
    print("✅ Validation complete!")
    print()
    print("Next Steps:")
    print("1. Review issues identified above")
    print("2. Implement fail-fast fixes per FAIL_FAST_AUDIT_PLAN.md")
    print("3. Re-run this test to validate improvements")

if __name__ == "__main__":
    main()
