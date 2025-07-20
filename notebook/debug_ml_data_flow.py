#!/usr/bin/env python3
"""
ML Data Flow Debug Script
=========================

This script debugs the ML pipeline data flow to identify issues with:
1. Data loading and aggregation
2. Recency weighting calculations  
3. Feature engineering pipeline
4. Target variable creation
5. Sanity checks on movement volumes

The goal is to understand why we're getting massive predicted movements
that don't align with the actual 120k movement corpus over 5 years.
"""

import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Database configuration
DATABASE_FILE = 'models/2025-Q3/workforce_intelligence.sqlite'

def print_section_header(title, description=""):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    if description:
        print(f"{description}")
        print()

def debug_raw_movement_data():
    """Debug the raw movement data loading"""
    print_section_header("DEBUG: RAW MOVEMENT DATA ANALYSIS")
    
    conn = sqlite3.connect(DATABASE_FILE)
    
    # Load raw movement_fact data
    movement_df = pd.read_sql_query("""
        SELECT * FROM movement_fact 
        WHERE movement_year >= 2020
        LIMIT 1000
    """, conn)
    
    print(f"📊 Raw movement_fact sample:")
    print(f"   → Shape: {movement_df.shape}")
    print(f"   → Columns: {list(movement_df.columns)}")
    print()
    
    # Show sample data
    print(f"📋 Sample Records:")
    print(movement_df.head(10))
    print()
    
    # Check movement_count distribution
    print(f"📈 Movement Count Distribution:")
    print(f"   → Min: {movement_df['movement_count'].min()}")
    print(f"   → Max: {movement_df['movement_count'].max()}")
    print(f"   → Mean: {movement_df['movement_count'].mean():.2f}")
    print(f"   → Median: {movement_df['movement_count'].median()}")
    print(f"   → Sum: {movement_df['movement_count'].sum():,}")
    print()
    
    # Check temporal distribution
    print(f"📅 Temporal Distribution:")
    temporal_summary = movement_df.groupby('movement_year')['movement_count'].agg([
        'count', 'sum', 'mean'
    ]).round(2)
    print(temporal_summary)
    print()
    
    # Check unique employees distribution
    print(f"👥 Unique Employees Distribution:")
    print(f"   → Min: {movement_df['unique_employees'].min()}")
    print(f"   → Max: {movement_df['unique_employees'].max()}")
    print(f"   → Mean: {movement_df['unique_employees'].mean():.2f}")
    print(f"   → Total unique employees represented: {movement_df['unique_employees'].sum():,}")
    print()
    
    conn.close()
    return movement_df

def debug_job_profile_mapping():
    """Debug the job profile mapping process"""
    print_section_header("DEBUG: JOB PROFILE MAPPING ANALYSIS")
    
    conn = sqlite3.connect(DATABASE_FILE)
    
    # Check position to job profile mapping
    positions_df = pd.read_sql_query("SELECT * FROM positions LIMIT 1000", conn)
    
    print(f"📊 Positions mapping sample:")
    print(f"   → Shape: {positions_df.shape}")
    print(f"   → Columns: {list(positions_df.columns)}")
    print()
    
    # Show sample mappings
    print(f"📋 Sample Position Mappings:")
    print(positions_df[['Position Number', 'JobProfileID']].head(10))
    print()
    
    # Check for missing mappings
    missing_job_profiles = positions_df['JobProfileID'].isna().sum()
    print(f"⚠️ Missing JobProfileID mappings: {missing_job_profiles:,} out of {len(positions_df):,}")
    print()
    
    # Load the full movement query with mappings
    movement_with_jobs_query = """
    SELECT 
        mf.movement_year,
        mf.movement_month,
        mf.movement_count,
        mf.avg_days_between,
        mf.pct_total_movements,
        mf.unique_employees,
        mf.monthly_total_movements,
        mf.predominant_movement_type,
        p_from.JobProfileID as JobProfileID_from,
        p_to.JobProfileID as JobProfileID_to,
        p_from.[Position Number] as pos_from,
        p_to.[Position Number] as pos_to
    FROM movement_fact mf
    JOIN positions p_from ON mf.from_position = p_from.[Position Number]
    JOIN positions p_to ON mf.to_position = p_to.[Position Number]
    WHERE mf.movement_year >= 2020
    AND p_from.JobProfileID IS NOT NULL 
    AND p_to.JobProfileID IS NOT NULL
    LIMIT 1000
    """
    
    movement_mapped_df = pd.read_sql_query(movement_with_jobs_query, conn)
    
    print(f"📊 Movement data with job mappings:")
    print(f"   → Shape: {movement_mapped_df.shape}")
    print(f"   → Sample records:")
    print(movement_mapped_df[['movement_count', 'JobProfileID_from', 'JobProfileID_to', 'movement_year']].head(10))
    print()
    
    conn.close()
    return movement_mapped_df

def debug_recency_weighting(movement_mapped_df):
    """Debug the recency weighting calculation"""
    print_section_header("DEBUG: RECENCY WEIGHTING CALCULATION")
    
    # Calculate recency weights manually to verify
    current_year = movement_mapped_df['movement_year'].max()
    print(f"📅 Current year (max in data): {current_year}")
    
    movement_mapped_df['years_ago'] = current_year - movement_mapped_df['movement_year']
    movement_mapped_df['recency_weight'] = 0.4 ** movement_mapped_df['years_ago']
    movement_mapped_df['weighted_movement_count'] = movement_mapped_df['movement_count'] * movement_mapped_df['recency_weight']
    
    print(f"🔢 Recency Weight Examples:")
    sample_weights = movement_mapped_df[['movement_year', 'years_ago', 'recency_weight', 'movement_count', 'weighted_movement_count']].head(10)
    print(sample_weights)
    print()
    
    # Check the impact of recency weighting
    print(f"📊 Recency Weighting Impact:")
    by_year = movement_mapped_df.groupby('movement_year').agg({
        'movement_count': ['sum', 'mean'],
        'weighted_movement_count': ['sum', 'mean'],
        'recency_weight': 'first'
    }).round(3)
    print(by_year)
    print()
    
    # Check extreme values
    print(f"⚠️ Extreme Values Check:")
    print(f"   → Max raw movement_count: {movement_mapped_df['movement_count'].max()}")
    print(f"   → Max weighted movement: {movement_mapped_df['weighted_movement_count'].max():.2f}")
    print(f"   → Total raw movements: {movement_mapped_df['movement_count'].sum():,}")
    print(f"   → Total weighted movements: {movement_mapped_df['weighted_movement_count'].sum():,.2f}")
    print()
    
    return movement_mapped_df

def debug_job_level_aggregation():
    """Debug the job-level aggregation process"""
    print_section_header("DEBUG: JOB-LEVEL AGGREGATION ANALYSIS")
    
    conn = sqlite3.connect(DATABASE_FILE)
    
    # Load full movement data with job mappings
    movement_features_query = """
    SELECT 
        mf.movement_year,
        mf.movement_month,
        mf.movement_count,
        mf.avg_days_between,
        mf.pct_total_movements,
        mf.unique_employees,
        mf.monthly_total_movements,
        mf.predominant_movement_type,
        p_from.JobProfileID as JobProfileID_from,
        p_to.JobProfileID as JobProfileID_to
    FROM movement_fact mf
    JOIN positions p_from ON mf.from_position = p_from.[Position Number]
    JOIN positions p_to ON mf.to_position = p_to.[Position Number]
    WHERE mf.movement_year >= 2020
    AND p_from.JobProfileID IS NOT NULL 
    AND p_to.JobProfileID IS NOT NULL
    """
    
    movement_features_df = pd.read_sql_query(movement_features_query, conn)
    print(f"📊 Full movement features loaded: {len(movement_features_df):,} records")
    
    # Calculate recency weights
    current_year = movement_features_df['movement_year'].max()
    movement_features_df['years_ago'] = current_year - movement_features_df['movement_year']
    movement_features_df['recency_weight'] = 0.4 ** movement_features_df['years_ago']
    
    # Show pre-aggregation statistics
    print(f"\n📋 Pre-Aggregation Statistics:")
    print(f"   → Total records: {len(movement_features_df):,}")
    print(f"   → Unique job pair transitions: {movement_features_df[['JobProfileID_from', 'JobProfileID_to']].drop_duplicates().shape[0]:,}")
    print(f"   → Total raw movement_count: {movement_features_df['movement_count'].sum():,}")
    print(f"   → Total recency-weighted activity: {(movement_features_df['movement_count'] * movement_features_df['recency_weight']).sum():,.2f}")
    print()
    
    # Perform aggregation step by step
    print(f"🔄 Performing job-level aggregation...")
    
    job_level_features = movement_features_df.groupby([
        'JobProfileID_from', 'JobProfileID_to'
    ]).agg({
        'movement_count': 'sum',                    # Total movements (from DB)
        'unique_employees': 'sum',                  # Total unique people (from DB)
        'avg_days_between': 'mean',                # Average transition time (from DB)
        'pct_total_movements': 'mean',             # Average market share (from DB)
        'movement_year': ['count', 'min', 'max'],   # Frequency, first year, last year
        'recency_weight': 'sum',                    # Total recency-weighted activity
        'monthly_total_movements': 'mean',          # Average monthly market volume (from DB)
        'predominant_movement_type': lambda x: x.mode().iloc[0] if not x.empty else 'lateral'
    }).reset_index()
    
    # Flatten column names
    job_level_features.columns = [
        'JobProfileID_from', 'JobProfileID_to',
        'total_movement_count',         
        'total_unique_employees',       
        'avg_days_between',            
        'avg_pct_total_movements',     
        'transition_frequency',        
        'first_observed_year',         
        'last_observed_year',          
        'recency_weighted_activity',   
        'avg_monthly_market_volume',   
        'predominant_movement_type'    
    ]
    
    print(f"✅ Aggregation completed: {len(job_level_features):,} job profile pairs")
    print()
    
    # Analyze the aggregated results
    print(f"📊 Post-Aggregation Analysis:")
    print(f"   → Total movement count (sum): {job_level_features['total_movement_count'].sum():,}")
    print(f"   → Total recency-weighted activity (sum): {job_level_features['recency_weighted_activity'].sum():,.2f}")
    print(f"   → Max recency-weighted activity: {job_level_features['recency_weighted_activity'].max():,.2f}")
    print(f"   → Mean recency-weighted activity: {job_level_features['recency_weighted_activity'].mean():.2f}")
    print(f"   → Median recency-weighted activity: {job_level_features['recency_weighted_activity'].median():.2f}")
    print()
    
    # Find the highest volume transitions
    print(f"🔝 Top 10 Highest Volume Transitions (Recency-Weighted):")
    top_transitions = job_level_features.nlargest(10, 'recency_weighted_activity')
    for _, row in top_transitions.iterrows():
        print(f"   → {row['JobProfileID_from']} → {row['JobProfileID_to']}: {row['recency_weighted_activity']:.1f} weighted movements ({row['total_movement_count']} raw)")
    print()
    
    # Check for suspicious patterns
    print(f"⚠️ Suspicious Pattern Detection:")
    very_high = job_level_features[job_level_features['recency_weighted_activity'] > 1000]
    print(f"   → Transitions with >1000 weighted movements: {len(very_high)}")
    
    extremely_high = job_level_features[job_level_features['recency_weighted_activity'] > 10000]
    print(f"   → Transitions with >10,000 weighted movements: {len(extremely_high)}")
    
    if len(extremely_high) > 0:
        print(f"   → Extreme cases:")
        for _, row in extremely_high.head(5).iterrows():
            print(f"     • {row['JobProfileID_from']} → {row['JobProfileID_to']}: {row['recency_weighted_activity']:.1f} weighted ({row['total_movement_count']} raw)")
    print()
    
    conn.close()
    return job_level_features

def debug_target_variable_creation(job_level_features):
    """Debug the target variable creation process"""
    print_section_header("DEBUG: TARGET VARIABLE CREATION")
    
    # Use recency_weighted_activity as target (same as ML script)
    movement_target = job_level_features['recency_weighted_activity']
    max_movement = movement_target.max()
    
    print(f"🎯 Target Variable Analysis:")
    print(f"   → Target variable: recency_weighted_activity")
    print(f"   → Range: {movement_target.min():.1f} to {movement_target.max():.1f}")
    print(f"   → Mean: {movement_target.mean():.1f}")
    print(f"   → Median: {movement_target.median():.1f}")
    print(f"   → Std Dev: {movement_target.std():.1f}")
    print(f"   → Max movement (for normalization): {max_movement:.1f}")
    print()
    
    # Calculate feasibility percentages
    feasibility_percentages = (movement_target / max_movement) * 100
    
    print(f"📊 Feasibility Percentage Distribution:")
    print(f"   → Range: {feasibility_percentages.min():.1f}% to {feasibility_percentages.max():.1f}%")
    print(f"   → Mean: {feasibility_percentages.mean():.1f}%")
    print(f"   → Median: {feasibility_percentages.median():.1f}%")
    print(f"   → High feasibility (≥70%): {(feasibility_percentages >= 70).sum()}")
    print(f"   → Moderate feasibility (30-69%): {((feasibility_percentages >= 30) & (feasibility_percentages < 70)).sum()}")
    print(f"   → Low feasibility (<30%): {(feasibility_percentages < 30).sum()}")
    print()
    
    # Distribution analysis
    print(f"📈 Distribution Percentiles:")
    percentiles = [50, 75, 90, 95, 99, 99.9]
    for p in percentiles:
        value = np.percentile(movement_target, p)
        feasibility = (value / max_movement) * 100
        print(f"   → {p}th percentile: {value:.1f} movements ({feasibility:.1f}% feasible)")
    print()
    
    # Check for outliers driving the scale
    print(f"⚠️ Outlier Analysis:")
    q75 = np.percentile(movement_target, 75)
    q25 = np.percentile(movement_target, 25)
    iqr = q75 - q25
    outlier_threshold = q75 + 1.5 * iqr
    outliers = movement_target[movement_target > outlier_threshold]
    
    print(f"   → IQR: {iqr:.1f}")
    print(f"   → Outlier threshold (Q3 + 1.5*IQR): {outlier_threshold:.1f}")
    print(f"   → Number of outliers: {len(outliers)}")
    print(f"   → Outlier impact on scale: {outliers.max():.1f} (max outlier) vs {movement_target.median():.1f} (median)")
    print()
    
    return movement_target, max_movement, feasibility_percentages

def debug_data_consistency_checks():
    """Perform consistency checks across the data pipeline"""
    print_section_header("DEBUG: DATA CONSISTENCY CHECKS")
    
    conn = sqlite3.connect(DATABASE_FILE)
    
    # Check total movement counts at different levels
    print(f"🔍 Movement Count Consistency Checks:")
    
    # Raw movement_fact totals
    raw_total_query = """
    SELECT 
        SUM(movement_count) as total_movements,
        COUNT(*) as total_records,
        MIN(movement_year) as min_year,
        MAX(movement_year) as max_year
    FROM movement_fact 
    WHERE movement_year >= 2020
    """
    raw_totals = pd.read_sql_query(raw_total_query, conn)
    print(f"   → Raw movement_fact totals:")
    print(f"     • Total movements: {raw_totals['total_movements'].iloc[0]:,}")
    print(f"     • Total records: {raw_totals['total_records'].iloc[0]:,}")
    print(f"     • Year range: {raw_totals['min_year'].iloc[0]} - {raw_totals['max_year'].iloc[0]}")
    print()
    
    # Movement_fact totals with job mappings
    mapped_total_query = """
    SELECT 
        SUM(mf.movement_count) as total_movements,
        COUNT(*) as total_records
    FROM movement_fact mf
    JOIN positions p_from ON mf.from_position = p_from.[Position Number]
    JOIN positions p_to ON mf.to_position = p_to.[Position Number]
    WHERE mf.movement_year >= 2020
    AND p_from.JobProfileID IS NOT NULL 
    AND p_to.JobProfileID IS NOT NULL
    """
    mapped_totals = pd.read_sql_query(mapped_total_query, conn)
    print(f"   → Movement_fact with job mappings:")
    print(f"     • Total movements: {mapped_totals['total_movements'].iloc[0]:,}")
    print(f"     • Total records: {mapped_totals['total_records'].iloc[0]:,}")
    print()
    
    # Loss in mapping process
    raw_movements = raw_totals['total_movements'].iloc[0]
    mapped_movements = mapped_totals['total_movements'].iloc[0]
    loss_pct = ((raw_movements - mapped_movements) / raw_movements) * 100
    print(f"   → Data loss in mapping: {raw_movements - mapped_movements:,} movements ({loss_pct:.1f}%)")
    print()
    
    # Check for duplicate or unusual patterns
    print(f"🔍 Pattern Analysis:")
    
    # Check for self-transitions (same job to same job)
    self_transitions_query = """
    SELECT 
        COUNT(*) as self_transition_records,
        SUM(mf.movement_count) as self_transition_movements
    FROM movement_fact mf
    JOIN positions p_from ON mf.from_position = p_from.[Position Number]
    JOIN positions p_to ON mf.to_position = p_to.[Position Number]
    WHERE mf.movement_year >= 2020
    AND p_from.JobProfileID IS NOT NULL 
    AND p_to.JobProfileID IS NOT NULL
    AND p_from.JobProfileID = p_to.JobProfileID
    """
    self_transitions = pd.read_sql_query(self_transitions_query, conn)
    print(f"   → Self-transitions (same job to same job):")
    print(f"     • Records: {self_transitions['self_transition_records'].iloc[0]:,}")
    print(f"     • Movements: {self_transitions['self_transition_movements'].iloc[0]:,}")
    print()
    
    # Check for high-volume individual transitions
    high_volume_query = """
    SELECT 
        mf.from_position,
        mf.to_position,
        p_from.JobProfileID as JobProfileID_from,
        p_to.JobProfileID as JobProfileID_to,
        mf.movement_count,
        mf.movement_year,
        mf.movement_month
    FROM movement_fact mf
    JOIN positions p_from ON mf.from_position = p_from.[Position Number]
    JOIN positions p_to ON mf.to_position = p_to.[Position Number]
    WHERE mf.movement_year >= 2020
    AND p_from.JobProfileID IS NOT NULL 
    AND p_to.JobProfileID IS NOT NULL
    AND mf.movement_count > 1000
    ORDER BY mf.movement_count DESC
    LIMIT 10
    """
    high_volume = pd.read_sql_query(high_volume_query, conn)
    print(f"   → High-volume individual transitions (>1000 movements):")
    if len(high_volume) > 0:
        for _, row in high_volume.iterrows():
            print(f"     • {row['JobProfileID_from']} → {row['JobProfileID_to']}: {row['movement_count']:,} movements ({row['movement_year']}-{row['movement_month']:02d})")
    else:
        print(f"     • No individual transitions >1000 movements")
    print()
    
    conn.close()

def main():
    """Main debug execution"""
    print_section_header(
        "ML DATA FLOW DEBUG ANALYSIS",
        "Investigating data loading, aggregation, and target variable creation"
    )
    
    # Step 1: Debug raw movement data
    raw_movement_sample = debug_raw_movement_data()
    
    # Step 2: Debug job profile mapping
    movement_mapped_sample = debug_job_profile_mapping()
    
    # Step 3: Debug recency weighting
    weighted_sample = debug_recency_weighting(movement_mapped_sample)
    
    # Step 4: Debug job-level aggregation
    job_level_features = debug_job_level_aggregation()
    
    # Step 5: Debug target variable creation
    movement_target, max_movement, feasibility_pct = debug_target_variable_creation(job_level_features)
    
    # Step 6: Data consistency checks
    debug_data_consistency_checks()
    
    print_section_header("DEBUG ANALYSIS COMPLETE")
    print(f"🎯 Key Findings Summary:")
    print(f"   → Job profile transitions analyzed: {len(job_level_features):,}")
    print(f"   → Max recency-weighted volume: {max_movement:.1f}")
    print(f"   → Mean recency-weighted volume: {movement_target.mean():.1f}")
    print(f"   → Transitions with >10k weighted movements: {(movement_target > 10000).sum()}")
    print(f"   → This debug should help identify why ML predictions are so high!")

if __name__ == "__main__":
    main() 