#!/usr/bin/env python3
"""
Diagnostic Script for Retention Issues

This script investigates why 2025 data has lower retention than 2024,
and why overall retention is only 22.5%.
"""

import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime

def diagnose_retention_issues():
    """Diagnose retention and filtering issues"""
    
    print("🔍 DIAGNOSING RETENTION ISSUES")
    print("=" * 60)
    
    # Connect to database
    conn = sqlite3.connect('models/2025-Q3/workforce_intelligence.sqlite')
    
    # =============================================================================
    # 1. MOVEMENT DATA ANALYSIS
    # =============================================================================
    
    print("\n📊 MOVEMENT DATA ANALYSIS")
    print("-" * 40)
    
    # Get movement data with year breakdown
    movement_analysis = pd.read_sql_query("""
        SELECT 
            movement_year,
            COUNT(*) as total_movements,
            COUNT(DISTINCT from_position) as unique_from_positions,
            COUNT(DISTINCT to_position) as unique_to_positions,
            COUNT(CASE WHEN from_position IS NOT NULL AND to_position IS NOT NULL THEN 1 END) as non_null_movements
        FROM movement_fact
        GROUP BY movement_year
        ORDER BY movement_year
    """, conn)
    
    print("Movement data by year:")
    print(movement_analysis.to_string(index=False))
    
    # =============================================================================
    # 2. JOB PROFILE MATCHING ANALYSIS
    # =============================================================================
    
    print("\n📊 JOB PROFILE MATCHING ANALYSIS")
    print("-" * 40)
    
    # Check how many positions have job profiles
    position_job_mapping = pd.read_sql_query("""
        SELECT 
            COUNT(*) as total_positions,
            COUNT(DISTINCT [Position Number]) as unique_positions,
            COUNT(CASE WHEN JobProfileID IS NOT NULL THEN 1 END) as positions_with_job_profiles,
            COUNT(DISTINCT JobProfileID) as unique_job_profiles_in_positions
        FROM positions
    """, conn)
    
    print("Position-JobProfile mapping:")
    print(position_job_mapping.to_string(index=False))
    
    # Check current job profiles
    current_jobs = pd.read_sql_query("""
        SELECT 
            COUNT(*) as total_job_records,
            COUNT(DISTINCT JobProfileID) as unique_job_profiles
        FROM jobs
    """, conn)
    
    print("\nCurrent job architecture:")
    print(current_jobs.to_string(index=False))
    
    # =============================================================================
    # 3. DETAILED RETENTION ANALYSIS BY YEAR
    # =============================================================================
    
    print("\n📊 DETAILED RETENTION ANALYSIS BY YEAR")
    print("-" * 40)
    
    # Load movement data
    movements_df = pd.read_sql_query("""
        SELECT 
            movement_year,
            from_position,
            to_position
        FROM movement_fact
    """, conn)
    
    # Load positions and jobs
    positions_df = pd.read_sql_query("SELECT [Position Number], JobProfileID FROM positions", conn)
    jobs_df = pd.read_sql_query("SELECT JobProfileID FROM jobs", conn)
    
    # Create position to job profile mapping
    position_to_job = dict(zip(positions_df['Position Number'].astype(str), positions_df['JobProfileID']))
    current_job_profiles = set(jobs_df['JobProfileID'].unique())
    
    print(f"Total positions in mapping: {len(position_to_job):,}")
    print(f"Current job profiles: {len(current_job_profiles):,}")
    
    # Analyze retention by year
    retention_details = []
    
    for year in sorted(movements_df['movement_year'].unique()):
        year_data = movements_df[movements_df['movement_year'] == year]
        
        # Step 1: Non-null positions
        non_null = year_data.dropna(subset=['from_position', 'to_position'])
        
        # Step 2: Add job profiles
        non_null['from_job_profile'] = non_null['from_position'].astype(str).map(position_to_job)
        non_null['to_job_profile'] = non_null['to_position'].astype(str).map(position_to_job)
        
        # Step 3: Non-null job profiles
        with_job_profiles = non_null.dropna(subset=['from_job_profile', 'to_job_profile'])
        
        # Step 4: Current job profiles only
        current_only = with_job_profiles[
            with_job_profiles['from_job_profile'].isin(current_job_profiles) &
            with_job_profiles['to_job_profile'].isin(current_job_profiles)
        ]
        
        retention_details.append({
            'year': year,
            'total_movements': len(year_data),
            'non_null_positions': len(non_null),
            'with_job_profiles': len(with_job_profiles),
            'current_job_profiles_only': len(current_only),
            'retention_rate': len(current_only) / len(year_data) * 100 if len(year_data) > 0 else 0,
            'position_mapping_rate': len(non_null) / len(year_data) * 100 if len(year_data) > 0 else 0,
            'job_profile_mapping_rate': len(with_job_profiles) / len(non_null) * 100 if len(non_null) > 0 else 0,
            'current_job_filter_rate': len(current_only) / len(with_job_profiles) * 100 if len(with_job_profiles) > 0 else 0
        })
    
    retention_df = pd.DataFrame(retention_details)
    
    print("\nDetailed retention analysis:")
    print(retention_df.to_string(index=False))
    
    # =============================================================================
    # 4. IDENTIFY SPECIFIC ISSUES
    # =============================================================================
    
    print("\n📊 SPECIFIC ISSUE IDENTIFICATION")
    print("-" * 40)
    
    # Check for 2025 vs 2024 comparison
    if len(retention_df) >= 2:
        recent_years = retention_df.tail(2)
        if len(recent_years) == 2:
            year_2024 = recent_years.iloc[0] if recent_years.iloc[0]['year'] == 2024 else recent_years.iloc[1]
            year_2025 = recent_years.iloc[1] if recent_years.iloc[1]['year'] == 2025 else recent_years.iloc[0]
            
            print(f"2024 vs 2025 Analysis:")
            print(f"  2024 retention: {year_2024['retention_rate']:.1f}%")
            print(f"  2025 retention: {year_2025['retention_rate']:.1f}%")
            print(f"  2024 total movements: {year_2024['total_movements']:,}")
            print(f"  2025 total movements: {year_2025['total_movements']:,}")
            
            if year_2025['retention_rate'] < year_2024['retention_rate']:
                print("  🚨 2025 retention is LOWER than 2024 - investigating...")
                
                # Check if it's due to position mapping
                if year_2025['position_mapping_rate'] < year_2024['position_mapping_rate']:
                    print("    → Issue: 2025 has more null positions")
                
                # Check if it's due to job profile mapping
                if year_2025['job_profile_mapping_rate'] < year_2024['job_profile_mapping_rate']:
                    print("    → Issue: 2025 positions don't map to job profiles")
                
                # Check if it's due to current job filter
                if year_2025['current_job_filter_rate'] < year_2024['current_job_filter_rate']:
                    print("    → Issue: 2025 job profiles are not in current job architecture")
    
    # =============================================================================
    # 5. RECOMMENDATIONS
    # =============================================================================
    
    print("\n📊 RECOMMENDATIONS")
    print("-" * 40)
    
    overall_retention = retention_df['retention_rate'].mean()
    
    if overall_retention < 30:
        print("🚨 CRITICAL: Overall retention is very low (<30%)")
        print("   → Consider relaxing job profile filtering")
        print("   → Check if position-to-job mapping is incomplete")
        print("   → Verify job architecture is up to date")
    
    # Check for recent year issues
    if len(retention_df) > 0:
        latest_year = retention_df.iloc[-1]
        if latest_year['year'] == 2025 and latest_year['retention_rate'] < 35:
            print("🚨 2025 DATA ISSUE: Recent year has low retention")
            print("   → 2025 data may be incomplete")
            print("   → Consider excluding partial year data")
            print("   → Or adjust recency weighting to account for incomplete data")
    
    # Suggest alternative approaches
    print("\n💡 ALTERNATIVE APPROACHES:")
    print("1. Reduce recency decay rate (0.4 → 0.6) for more historical data")
    print("2. Include movements to/from historical job profiles")
    print("3. Use fuzzy matching for job profile mapping")
    print("4. Exclude incomplete years (2025) from analysis")
    print("5. Investigate data loading processes for recent periods")
    
    conn.close()
    print("\n🔒 Database connection closed")

if __name__ == "__main__":
    diagnose_retention_issues() 