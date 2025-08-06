#!/usr/bin/env python3
"""
Unified Synthetic Data Generator

Creates synthetic workforce data with proper PosIDLookupKey relationships
between colleague_positions_history and positions_history files.

Key Features:
- Maintains exact schema from existing files
- Ensures PosIDLookupKey overlap between colleague and position tables
- Generates multiple financial years of data
- Creates realistic movement patterns for testing

Usage: python scripts/generate_unified_synthetic_data.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime, timedelta
import random
from typing import Dict, List, Tuple, Set
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Configuration
CONFIG = {
    # Data generation parameters
    'financial_years': ['fy22', 'fy23', 'fy24', 'fy25'],
    'position_count': 5000,  # Total unique positions
    'employee_count_per_year': 50000,  # Unique employees per year
    'weeks_per_year': 53,
    'org_units': ['Technology', 'Human Resources', 'Customer Banking', 'Risk Management', 
                  'Operations', 'Finance', 'Business Banking', 'Investment Banking',
                  'Digital & Data', 'Legal & Compliance', 'Marketing'],
    
    # Position number range (matches existing data)
    'position_number_start': 50000000,
    'position_number_end': 50004999,
    
    # Employee number ranges by year (matches existing pattern)
    'employee_number_ranges': {
        'fy22': (50000000, 60000000),
        'fy23': (80000000, 90000000),  
        'fy24': (110000000, 120000000),
        'fy25': (135000000, 145000000)
    },
    
    # Movement probability (what % of employees change positions per year)
    'movement_probability': 0.15,  # 15% of employees move per year
    
    # PosIDLookupKey generation (ensures uniqueness and overlap)
    'posid_base_range': (100000000000, 300000000000),
    
    # Files to generate
    'colleague_positions_per_year': 500000,  # Records per year
    'position_timeline_per_year': 120000,    # Records per year
}

def generate_position_master_list() -> pd.DataFrame:
    """Generate master list of positions with consistent PosIDLookupKeys."""
    
    print("🏗️ Generating master position list...")
    
    positions = []
    cost_centres = list(range(1000, 10000, 100))
    
    for i in range(CONFIG['position_count']):
        position_number = CONFIG['position_number_start'] + i
        
        # Generate a unique PosIDLookupKey for this position
        # This will be reused across years and tables to ensure consistency
        base_key = random.uniform(*CONFIG['posid_base_range'])
        posid_lookup_key = base_key
        
        # Assign organizational details
        org_unit = random.choice(CONFIG['org_units'])
        cost_centre = random.choice(cost_centres)
        
        positions.append({
            'Position_Number': position_number,
            'PosIDLookupKey': posid_lookup_key,
            'Organisational_Unit': org_unit,
            'Cost_Centre_Number': cost_centre,
            'Operational': random.choice([True, False]),
            'OrgUnitIDLookupKey': random.randint(1000000, 9999999)
        })
    
    df = pd.DataFrame(positions)
    print(f"✅ Generated {len(df):,} master positions")
    return df

def generate_week_dates(year_suffix: str) -> List[str]:
    """Generate realistic week ending dates for a financial year."""
    
    # Map year suffix to actual year range
    year_map = {
        'fy22': (2021, 2022),
        'fy23': (2022, 2023), 
        'fy24': (2023, 2024),
        'fy25': (2024, 2025)
    }
    
    start_year, end_year = year_map[year_suffix]
    
    # Generate week ending dates (typically Fridays)
    dates = []
    current_date = datetime(start_year, 7, 2)  # Start of financial year
    
    for week in range(CONFIG['weeks_per_year']):
        dates.append(current_date.strftime('%d/%m/%Y'))
        current_date += timedelta(days=7)
    
    return dates

def generate_colleague_positions_history(master_positions: pd.DataFrame, year_suffix: str) -> pd.DataFrame:
    """Generate colleague position history data for one financial year."""
    
    print(f"👥 Generating colleague positions for {year_suffix}...")
    
    week_dates = generate_week_dates(year_suffix)
    employee_start, employee_end = CONFIG['employee_number_ranges'][year_suffix]
    
    # Generate unique employees for this year
    unique_employees = random.sample(
        range(employee_start, employee_end), 
        CONFIG['employee_count_per_year']
    )
    
    records = []
    target_records = CONFIG['colleague_positions_per_year']
    
    # Create position assignment with movement patterns
    employee_positions = {}  # Track current position for each employee
    
    for employee in unique_employees:
        # Each employee starts with a random position
        initial_position = master_positions.sample(1).iloc[0]
        employee_positions[employee] = initial_position
    
    records_per_week = target_records // len(week_dates)
    
    for week_date in week_dates:
        week_records = 0
        
        # Apply movements (some employees change positions)
        if random.random() < CONFIG['movement_probability']:
            employees_to_move = random.sample(
                unique_employees, 
                int(len(unique_employees) * CONFIG['movement_probability'] * 0.1)  # 10% of movement rate per week
            )
            
            for employee in employees_to_move:
                # Move to a different position
                new_position = master_positions.sample(1).iloc[0]
                employee_positions[employee] = new_position
        
        # Generate records for this week
        employees_this_week = random.sample(unique_employees, min(records_per_week, len(unique_employees)))
        
        for employee in employees_this_week:
            if week_records >= records_per_week:
                break
                
            position_info = employee_positions[employee]
            
            # Generate position start date (sometime in the past)
            start_date = datetime.strptime(week_date, '%d/%m/%Y') - timedelta(days=random.randint(30, 365))
            
            records.append({
                'Week Ending': week_date,
                'Employee Number': employee,
                'Operational': random.choice([True, False]),
                'Position Start Date': start_date.strftime('%d/%m/%Y'),
                'PosIDLookupKey': position_info['PosIDLookupKey'],  # Critical: Use same key
                'Position Number': position_info['Position_Number']  # Critical: Use same number
            })
            
            week_records += 1
    
    df = pd.DataFrame(records)
    
    # Ensure we have the right number of records
    if len(df) > target_records:
        df = df.sample(target_records).reset_index(drop=True)
    
    print(f"✅ Generated {len(df):,} colleague position records for {year_suffix}")
    return df

def generate_positions_history(master_positions: pd.DataFrame, year_suffix: str) -> pd.DataFrame:
    """Generate position timeline data for one financial year."""
    
    print(f"🏢 Generating position timeline for {year_suffix}...")
    
    week_dates = generate_week_dates(year_suffix)
    target_records = CONFIG['position_timeline_per_year']
    
    records = []
    
    # Sample positions to include in this year's timeline
    positions_this_year = master_positions.sample(target_records // len(week_dates))
    
    for week_date in week_dates:
        for _, position in positions_this_year.iterrows():
            
            # Create unique position timeline ID
            position_timeline_id = f"{position['Position_Number']}/{week_date.replace('/', '')}"
            
            records.append({
                'position_timeline_id': position_timeline_id,
                'Week Ending': week_date,  # ← SPACE (as expected by sources.yaml)
                'Position Number': position['Position_Number'],  # ← SPACE (as expected by sources.yaml)
                # JobProfileID removed - will be added by enrichment process from mapping file
                'PosIDLookupKey': position['PosIDLookupKey'],  # Critical: Use same key
                'Organisational Unit': position['Organisational_Unit'],  # ← SPACE (as expected by sources.yaml)
                'Cost Centre Number': position['Cost_Centre_Number'],  # ← SPACE (as expected by sources.yaml)
                'Position Title': None,  # ← SPACE (as expected by sources.yaml)
                'People Leader': random.choice([None] * 3 + [random.uniform(20000000, 30000000)]),  # ← SPACE (as expected by sources.yaml)
                'Operational': position['Operational'],
                'OrgUnitIDLookupKey': position['OrgUnitIDLookupKey']
            })
    
    df = pd.DataFrame(records)
    
    # Ensure we have the right number of records
    if len(df) > target_records:
        df = df.sample(target_records).reset_index(drop=True)
    
    print(f"✅ Generated {len(df):,} position timeline records for {year_suffix}")
    return df

def save_dataframes_to_csv(colleague_dfs: Dict[str, pd.DataFrame], position_dfs: Dict[str, pd.DataFrame]):
    """Save generated dataframes to CSV files with proper directory structure."""
    
    print("💾 Saving CSV files...")
    
    # Create directories
    colleague_dir = DATA_DIR / "colleague_positions_history"
    position_dir = DATA_DIR / "positions_history" 
    
    colleague_dir.mkdir(parents=True, exist_ok=True)
    position_dir.mkdir(parents=True, exist_ok=True)
    
    # Save colleague position files
    for year, df in colleague_dfs.items():
        filename = f"d_colleague_position_{year}.csv"
        filepath = colleague_dir / filename
        df.to_csv(filepath, index=False)
        print(f"✅ Saved: {filepath} ({len(df):,} rows)")
    
    # Save position timeline files  
    for year, df in position_dfs.items():
        filename = f"d_positions_{year}.csv"
        filepath = position_dir / filename
        df.to_csv(filepath, index=False)
        print(f"✅ Saved: {filepath} ({len(df):,} rows)")

def generate_analysis_report(master_positions: pd.DataFrame, colleague_dfs: Dict, position_dfs: Dict):
    """Generate analysis report showing data quality and relationships."""
    
    print("\n📊 GENERATION ANALYSIS REPORT")
    print("=" * 80)
    
    # Master positions analysis
    print(f"🏗️ Master Positions Generated:")
    print(f"   Total positions: {len(master_positions):,}")
    print(f"   Position Number range: {master_positions['Position_Number'].min():,} to {master_positions['Position_Number'].max():,}")
    print(f"   PosIDLookupKey range: {master_positions['PosIDLookupKey'].min():,.0f} to {master_positions['PosIDLookupKey'].max():,.0f}")
    print(f"   Unique PosIDLookupKeys: {master_positions['PosIDLookupKey'].nunique():,}")
    
    # Relationship analysis
    print(f"\n🔗 PosIDLookupKey Relationship Analysis:")
    
    for year in CONFIG['financial_years']:
        colleague_df = colleague_dfs[year]
        position_df = position_dfs[year]
        
        # Get unique PosIDLookupKeys from each
        colleague_keys = set(colleague_df['PosIDLookupKey'].astype(float))
        position_keys = set(position_df['PosIDLookupKey'].astype(float))
        overlap = colleague_keys.intersection(position_keys)
        
        overlap_rate = (len(overlap) / len(colleague_keys)) * 100 if colleague_keys else 0
        
        print(f"   {year.upper()}:")
        print(f"      Colleague unique PosIDs: {len(colleague_keys):,}")
        print(f"      Position unique PosIDs: {len(position_keys):,}")
        print(f"      Overlapping PosIDs: {len(overlap):,}")
        print(f"      Overlap rate: {overlap_rate:.1f}%")
    
    # File size estimates
    print(f"\n📁 Generated File Information:")
    for year in CONFIG['financial_years']:
        colleague_df = colleague_dfs[year]
        position_df = position_dfs[year]
        
        print(f"   {year.upper()}:")
        print(f"      Colleague positions: {len(colleague_df):,} rows × {len(colleague_df.columns)} columns")
        print(f"      Position timeline: {len(position_df):,} rows × {len(position_df.columns)} columns")

def main():
    """Main function to generate unified synthetic data."""
    
    print("🚀 UNIFIED SYNTHETIC DATA GENERATOR")
    print("=" * 80)
    print(f"📂 Project root: {PROJECT_ROOT}")
    print(f"📁 Data directory: {DATA_DIR}")
    
    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    # Step 1: Generate master position list with consistent PosIDLookupKeys
    master_positions = generate_position_master_list()
    
    # Step 2: Generate colleague position data for each year
    colleague_dfs = {}
    for year in CONFIG['financial_years']:
        colleague_dfs[year] = generate_colleague_positions_history(master_positions, year)
    
    # Step 3: Generate position timeline data for each year
    position_dfs = {}
    for year in CONFIG['financial_years']:
        position_dfs[year] = generate_positions_history(master_positions, year)
    
    # Step 4: Save all dataframes to CSV files
    save_dataframes_to_csv(colleague_dfs, position_dfs)
    
    # Step 5: Generate analysis report
    generate_analysis_report(master_positions, colleague_dfs, position_dfs)
    
    print(f"\n✅ Unified synthetic data generation complete!")
    print(f"📊 Generated {len(CONFIG['financial_years'])} years of workforce data")
    print(f"🔗 PosIDLookupKey relationships properly established")
    print(f"💾 Files saved to: {DATA_DIR}")

if __name__ == "__main__":
    main()