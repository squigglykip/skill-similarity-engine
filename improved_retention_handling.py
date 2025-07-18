#!/usr/bin/env python3
"""
Improved Retention Handling

This script provides better logic for handling incomplete years and 
more flexible filtering to improve data retention rates.
"""

import pandas as pd
import numpy as np
from datetime import datetime

def calculate_smart_recency_weight(movement_date, reference_date=None, decay_rate=0.4, incomplete_year_boost=1.2):
    """
    Smart recency weighting that accounts for incomplete years
    """
    from datetime import datetime
    
    if reference_date is None:
        reference_date = datetime.now()
    
    # Convert to pandas datetime for consistent handling
    movement_date = pd.to_datetime(movement_date)
    reference_date = pd.to_datetime(reference_date)
    
    # Calculate years difference
    days_diff = (reference_date - movement_date).days
    years_ago = days_diff / 365.25
    
    # Base weight calculation
    weight = decay_rate ** years_ago
    
    # Boost for incomplete current year (2025)
    if movement_date.year == reference_date.year:
        # If it's the current year, boost the weight to account for incomplete data
        weight *= incomplete_year_boost
    
    return max(weight, 0.05)  # Minimum weight threshold

def create_flexible_movement_dataset(movement_df, jobs_df, max_retention_threshold=0.15):
    """
    More flexible movement dataset creation with adaptive filtering
    """
    from datetime import datetime
    
    original_count = len(movement_df)
    
    print(f"   → Initial records: {len(movement_df):,}")
    
    # Step 1: Basic data cleaning - remove null positions
    clean_df = movement_df.dropna(subset=['from_position', 'to_position'])
    print(f"   → After removing null positions: {len(clean_df):,}")
    
    # Step 2: Check if we have JobProfileID columns
    if 'JobProfileID_from' in clean_df.columns and 'JobProfileID_to' in clean_df.columns:
        # Remove null job profiles
        clean_df = clean_df.dropna(subset=['JobProfileID_from', 'JobProfileID_to'])
        print(f"   → After removing null job profiles: {len(clean_df):,}")
        
        # Get current job profiles
        current_job_profiles = set(jobs_df['JobProfileID'].unique())
        print(f"   → Current job profiles available: {len(current_job_profiles):,}")
        
        # Try strict filtering first
        before_filter = len(clean_df)
        strict_filtered = clean_df[
            clean_df['JobProfileID_from'].isin(current_job_profiles) &
            clean_df['JobProfileID_to'].isin(current_job_profiles)
        ]
        
        strict_retention = len(strict_filtered) / original_count
        print(f"   → Strict filtering retention: {strict_retention:.1%}")
        
        if strict_retention < max_retention_threshold:
            print(f"   ⚠️  Strict filtering too aggressive ({strict_retention:.1%} < {max_retention_threshold:.1%})")
            print(f"   → Switching to relaxed filtering...")
            
            # Relaxed filtering - allow movements FROM current job profiles
            relaxed_filtered = clean_df[
                clean_df['JobProfileID_from'].isin(current_job_profiles) |
                clean_df['JobProfileID_to'].isin(current_job_profiles)
            ]
            
            relaxed_retention = len(relaxed_filtered) / original_count
            print(f"   → Relaxed filtering retention: {relaxed_retention:.1%}")
            
            if relaxed_retention > strict_retention * 1.5:  # If relaxed is significantly better
                clean_df = relaxed_filtered
                print(f"   → Using relaxed filtering")
            else:
                clean_df = strict_filtered
                print(f"   → Using strict filtering despite low retention")
        else:
            clean_df = strict_filtered
            print(f"   → Using strict filtering")
    
    # Step 3: Apply smart recency weighting
    if 'movement_year' in clean_df.columns:
        clean_df = clean_df.copy()
        clean_df['movement_date'] = pd.to_datetime(clean_df['movement_year'], format='%Y')
        
        # Calculate smart recency weights
        recency_weights = []
        current_year = datetime.now().year
        
        for date_val in clean_df['movement_date']:
            # Use boosted weighting for current year
            if date_val.year == current_year:
                weight = calculate_smart_recency_weight(date_val, incomplete_year_boost=1.3)
            else:
                weight = calculate_smart_recency_weight(date_val, incomplete_year_boost=1.0)
            recency_weights.append(weight)
        
        clean_df['recency_weight'] = recency_weights
    else:
        print("⚠️  No movement_year column found, using uniform weights")
        clean_df = clean_df.copy()
        clean_df['recency_weight'] = 1.0
    
    # Step 4: Filter out movements with negligible weight (but be less aggressive)
    clean_df['recency_weight'] = pd.to_numeric(clean_df['recency_weight'], errors='coerce')
    clean_df = clean_df[clean_df['recency_weight'] >= 0.005]  # Reduced from 0.01 to 0.005
    
    # Step 5: Enhanced retention reporting
    if 'movement_year' in movement_df.columns:
        print("   → Enhanced retention by year:")
        
        for year in sorted(movement_df['movement_year'].unique()):
            original_year = len(movement_df[movement_df['movement_year'] == year])
            clean_year = len(clean_df[clean_df['movement_year'] == year])
            retention = (clean_year / original_year * 100) if original_year > 0 else 0
            
            # Flag concerning drops
            if year >= 2024 and retention < 25:
                status = "🚨 LOW"
            elif year >= 2023 and retention < 20:
                status = "⚠️ CONCERNING"
            else:
                status = "✅ OK"
            
            print(f"     {year}: {retention:.1f}% retained {status}")
    
    total_retention = len(clean_df) / original_count * 100
    print(f"   → Overall retention: {total_retention:.1f}%")
    
    # Final recommendations
    if total_retention < 20:
        print("   🚨 CRITICAL: Very low retention - consider data quality review")
    elif total_retention < 30:
        print("   ⚠️ WARNING: Low retention - may need parameter adjustment")
    else:
        print("   ✅ GOOD: Acceptable retention rate")
    
    return clean_df

def exclude_incomplete_years(df, exclude_current_year=True):
    """
    Option to exclude incomplete years from analysis
    """
    from datetime import datetime
    
    if 'movement_year' not in df.columns:
        return df
    
    current_year = datetime.now().year
    
    if exclude_current_year:
        # Exclude current year if it's incomplete
        filtered_df = df[df['movement_year'] < current_year]
        excluded_count = len(df) - len(filtered_df)
        print(f"   → Excluded {excluded_count:,} records from {current_year} (incomplete year)")
        return filtered_df
    else:
        return df

# Example usage functions that can be integrated into main script:

def get_retention_recommendations(retention_by_year):
    """
    Provide specific recommendations based on retention patterns
    """
    recommendations = []
    
    # Check for recent year drops
    if len(retention_by_year) >= 2:
        recent_years = retention_by_year[-2:]
        if len(recent_years) == 2:
            if recent_years[1] < recent_years[0]:
                recommendations.append("🚨 Recent year retention dropping - investigate data completeness")
    
    # Check overall retention
    avg_retention = np.mean(retention_by_year)
    if avg_retention < 20:
        recommendations.append("📊 Consider relaxing job profile filtering criteria")
        recommendations.append("🔍 Review position-to-job-profile mapping completeness")
    
    if avg_retention < 30:
        recommendations.append("⚖️ Consider reducing recency decay rate (0.4 → 0.6)")
        recommendations.append("📅 Consider excluding incomplete years from analysis")
    
    return recommendations

if __name__ == "__main__":
    print("Improved retention handling functions loaded")
    print("These can be integrated into the main role typology script") 