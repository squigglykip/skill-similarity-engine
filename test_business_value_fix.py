#!/usr/bin/env python3
"""
Test Business Value Calculation Fix
==================================

Quick test to validate that our business value calculation is working
and producing varied, realistic values instead of hardcoded 0.8.
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path

def test_business_value_calculation():
    """Test if business value calculation is working with real values."""
    print("🧪 Testing Business Value Calculation Fix")
    print("=" * 45)
    
    try:
        # Import the clustering analyzer
        sys.path.append('src')
        from skill_similarity_engine.models.clustering_analyzer import JobProfileClusterer
        
        print("✅ Successfully imported JobProfileClusterer")
        
        # Try to initialize (this will test our error handling)
        clusterer = JobProfileClusterer()
        print(f"✅ Clusterer initialized with algorithm: {clusterer.algorithm}")
        
        # Test the business value calculation method directly if we can access sample data
        db_path = Path("models/2025-Q3/business_context.sqlite")
        if db_path.exists():
            print("📊 Testing with real database...")
            
            with sqlite3.connect(db_path) as conn:
                # Get a small sample of job data to test calculation
                query = """
                SELECT JobProfileID, JobProfile, JobFunction, ManagementLevel
                FROM core_job_architecture 
                LIMIT 10
                """
                
                jobs_df = pd.read_sql_query(query, conn)
                print(f"   Loaded {len(jobs_df)} jobs for testing")
                
                # Create a mock cluster and metrics for testing
                from skill_similarity_engine.models.clustering_analyzer import ClusteringMetrics
                mock_metrics = ClusteringMetrics(
                    n_clusters=1,
                    silhouette_score=0.5,  # Middle-range score
                    noise_ratio=0.1
                )
                
                # Test the calculation
                try:
                    business_value = clusterer._calculate_business_value_score_or_fail(jobs_df, mock_metrics)
                    print(f"✅ Business value calculation succeeded: {business_value}")
                    
                    if business_value == 0.8:
                        print("🚨 WARNING: Got hardcoded value 0.8 - calculation may not be working")
                    else:
                        print(f"✅ Got calculated value {business_value} (not hardcoded)")
                        
                except Exception as e:
                    print(f"❌ Business value calculation failed: {e}")
                    print(f"   Error type: {type(e).__name__}")
        else:
            print("⚠️ Database not found - cannot test with real data")
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("   Check that error classes are created correctly")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print(f"   Error type: {type(e).__name__}")

def check_database_for_hardcoded_values():
    """Check if database still has hardcoded values."""
    print("\n📊 Checking Database for Hardcoded Values")
    print("=" * 42)
    
    db_path = Path("models/2025-Q3/business_context.sqlite")
    if not db_path.exists():
        print("❌ Database not found")
        return
        
    with sqlite3.connect(db_path) as conn:
        query = """
        SELECT 
            business_value_score,
            COUNT(*) as count
        FROM analytics_job_family_characteristics 
        GROUP BY business_value_score
        ORDER BY count DESC
        """
        
        df = pd.read_sql_query(query, conn)
        if len(df) > 0:
            print(f"Business value score distribution:")
            for _, row in df.iterrows():
                score = row['business_value_score']
                count = row['count']
                print(f"   {score}: {count} records")
                
            if len(df) == 1 and df.iloc[0]['business_value_score'] == 0.8:
                print("🚨 ISSUE: All records still have hardcoded value 0.8")
                print("   Need to re-run clustering analysis to apply the fix")
            else:
                print("✅ Multiple business value scores found (calculation working)")
        else:
            print("⚠️ No job family characteristics found")

if __name__ == "__main__":
    test_business_value_calculation()
    check_database_for_hardcoded_values()
    
    print("\n" + "=" * 60)
    print("Next Steps:")
    print("1. If calculation test passed, re-run clustering analysis:")
    print("   python main.py -> Option 3 -> Option 6 (Strategic Clustering Analytics)")
    print("2. Then re-run fail-fast validation test:")
    print("   python test_fail_fast_validation.py")
    print("3. Check that business value scores are now varied")
