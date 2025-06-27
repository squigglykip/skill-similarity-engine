#!/usr/bin/env python3
"""
Generate Position to Job Profile Mapping Data

This script creates a mapping between Position Numbers (from workforce context)
and JobProfileIDs (from job architecture). This bridge data enables the webapp
to connect employee positions to their job profiles for enhanced filtering and analysis.

Relationship: Each Position Number maps to exactly one JobProfileID (one-to-one)
Multiple positions can share the same JobProfileID (multiple people in same role)
"""

import pandas as pd
import numpy as np
import random
from pathlib import Path

# Set random seed for reproducible dummy data
random.seed(42)
np.random.seed(42)

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = DATA_DIR / "job_architecture_to_positions_mapping"
WORKFORCE_FILE = DATA_DIR / "workforce_context" / "dummy_workforce_context.csv"
JOB_ARCH_FILE = DATA_DIR / "job_architecture" / "dummy_job_architecture.csv"

# JobProfileIDs provided by user (717 unique IDs)
JOB_PROFILE_IDS = [
    'R0001.5', 'R0001.6', 'R0002.0', 'R0002.1', 'R0002.3', 'R0002.2', 'R0002.4',
    'R0003.2', 'R0003.0', 'R0005.1', 'R0007.1', 'R0009.0', 'R0009.1', 'R0010.1',
    'R0022.6', 'R0023.3', 'R0023.2', 'R0025.3', 'R0025.2', 'R0025.5', 'R0030.4',
    'R0037.0', 'R0037.3', 'R0038.6', 'R0039.4', 'R0039.0', 'R0039.2', 'R0039.3',
    'R0039.1', 'R0039.5', 'R0040.2', 'R0040.0', 'R0040.3', 'R0040.1', 'R0040.5',
    'R0041.3', 'R0041.0', 'R0041.1', 'R0041.2', 'R0041.4', 'R0042.6', 'R0043.3',
    'R0043.5', 'R0043.0', 'R0043.2', 'R0043.4', 'R0043.1', 'R0044.3', 'R0044.4',
    'R0044.0', 'R0044.2', 'R0045.0', 'R0045.3', 'R0045.4', 'R0045.5', 'R0045.2',
    'R0046.6', 'R0047.2', 'R0047.0', 'R0047.4', 'R0049.3', 'R0049.4', 'R0050.0',
    'R0050.4', 'R0050.3', 'R0050.5', 'R0050.2', 'R0050.1', 'R0051.6', 'R0052.3',
    'R0053.0', 'R0053.4', 'R0053.3', 'R0053.1', 'R0053.5', 'R0053.2', 'R0054.2',
    'R0054.4', 'R0054.3', 'R0054.0', 'R0054.5', 'R0058.0', 'R0058.5', 'R0067.7',
    'R0069.7', 'R0070.7', 'R0072.7', 'R0073.7', 'R0074.7', 'R0075.3', 'R0075.2',
    'R0075.4', 'R0075.5', 'R0078.6', 'R0079.4', 'R0079.3', 'R0079.5', 'R0079.0',
    'R0079.2', 'R0080.6', 'R0081.6', 'R0082.3', 'R0082.4', 'R0082.5', 'R0083.2',
    'R0083.5', 'R0083.3', 'R0084.5', 'R0084.2', 'R0084.3', 'R0084.0', 'R0084.4',
    'R0086.6', 'R0087.6', 'R0088.3', 'R0088.4', 'R0088.0', 'R0088.5', 'R0090.2',
    'R0090.0', 'R0090.3', 'R0091.3', 'R0091.2', 'R0091.4', 'R0091.0', 'R0091.1',
    'R0092.3', 'R0092.1', 'R0092.4', 'R0092.0', 'R0092.2', 'R0092.5', 'R0094.0',
    'R0094.4', 'R0094.2', 'R0094.1', 'R0094.3', 'R0094.5', 'R0096.4', 'R0096.0',
    'R0096.3', 'R0096.2', 'R0097.4', 'R0097.0', 'R0097.2', 'R0097.3', 'R0097.5',
    'R0099.3', 'R0099.5', 'R0099.2', 'R0100.2', 'R0102.3', 'R0102.5', 'R0103.2',
    'R0103.3', 'R0103.4', 'R0103.5', 'R0103.0', 'R0104.3', 'R0111.6', 'R0116.2',
    'R0116.3', 'R0116.4', 'R0172.5', 'R0172.3', 'R0181.2', 'R0181.3', 'R0187.1',
    'R0187.3', 'R0187.2', 'R0187.0', 'R0187.4', 'R0187.5', 'R0191.3', 'R0202.1',
    'R0202.5', 'R0202.0', 'R0207.3', 'R0208.3', 'R0208.4', 'R0208.1', 'R0208.2',
    'R0208.0', 'R0210.0', 'R0211.3', 'R0211.5', 'R0212.3', 'R0212.0', 'R0213.3',
    'R0213.4', 'R0213.2', 'R0213.1', 'R0213.0', 'R0214.5', 'R0214.4', 'R0214.3',
    'R0214.2', 'R0214.0', 'R0217.3', 'R0217.4', 'R0217.0', 'R0217.2', 'R0218.3',
    'R0218.4', 'R0218.1', 'R0218.0', 'R0218.5', 'R0218.2', 'R0220.4', 'R0222.3',
    'R0222.5', 'R0222.2', 'R0222.4', 'R0222.0', 'R0223.5', 'R0223.4', 'R0223.3',
    'R0223.0', 'R0223.2', 'R0224.5', 'R0224.0', 'R0224.2', 'R0224.4', 'R0225.4',
    'R0225.0', 'R0228.4', 'R0228.0', 'R0228.3', 'R0228.5', 'R0228.2', 'R0230.3',
    'R0230.4', 'R0230.0', 'R0230.2', 'R0231.3', 'R0231.2', 'R0231.4', 'R0231.5',
    'R0231.1', 'R0233.3', 'R0233.2', 'R0233.0', 'R0233.4', 'R0234.3', 'R0234.4',
    'R0234.0', 'R0235.3', 'R0235.0', 'R0235.2', 'R0235.5', 'R0235.4', 'R0236.4',
    'R0236.2', 'R0236.3', 'R0237.3', 'R0237.4', 'R0237.2', 'R0237.5', 'R0237.1',
    'R0237.0', 'R0238.0', 'R0238.4', 'R0238.2', 'R0238.3', 'R0238.5', 'R0239.0',
    'R0239.5', 'R0239.4', 'R0239.3', 'R0239.2', 'R0240.4', 'R0240.0', 'R0240.3',
    'R0240.5', 'R0240.2', 'R0241.0', 'R0241.3', 'R0241.4', 'R0241.2', 'R0241.5',
    'R0242.3', 'R0242.0', 'R0242.2', 'R0242.4', 'R0242.5', 'R0243.6', 'R0246.4',
    'R0248.6', 'R0249.5', 'R0249.3', 'R0249.4', 'R0249.2', 'R0251.6', 'R0252.6',
    'R0252.5', 'R0253.2', 'R0253.1', 'R0253.0', 'R0253.3', 'R0253.4', 'R0254.4',
    'R0254.5', 'R0254.0', 'R0254.3', 'R0254.2', 'R0254.1', 'R0255.4', 'R0255.0',
    'R0256.4', 'R0256.2', 'R0256.3', 'R0257.6', 'R0258.2', 'R0258.3', 'R0258.0',
    'R0258.5', 'R0259.6', 'R0262.0', 'R0262.1', 'R0262.5', 'R0262.4', 'R0263.4',
    'R0263.5', 'R0263.3', 'R0263.2', 'R0264.6', 'R0266.3', 'R0266.4', 'R0267.3',
    'R0268.1', 'R0268.3', 'R0268.2', 'R0268.4', 'R0268.0', 'R0270.2', 'R0270.1',
    'R0270.3', 'R0270.4', 'R0270.5', 'R0270.0', 'R0276.5', 'R0276.2', 'R0276.1',
    'R0276.3', 'R0276.4', 'R0277.2', 'R0277.3', 'R0277.5', 'R0279.5', 'R0279.6',
    'R0280.5', 'R0280.2', 'R0280.3', 'R0281.0', 'R0281.5', 'R0281.2', 'R0281.1',
    'R0281.4', 'R0281.3', 'R0282.6', 'R0283.3', 'R0283.5', 'R0283.4', 'R0283.2',
    'R0284.5', 'R0285.5', 'R0285.4', 'R0286.3', 'R0286.5', 'R0286.4', 'R0286.0',
    'R0287.4', 'R0287.3', 'R0287.2', 'R0288.6', 'R0289.2', 'R0289.4', 'R0289.5',
    'R0290.5', 'R0290.3', 'R0290.0', 'R0291.6', 'R0292.5', 'R0292.3', 'R0292.4',
    'R0292.2', 'R0292.0', 'R0293.3', 'R0293.2', 'R0293.0', 'R0293.4', 'R0293.5',
    'R0296.3', 'R0298.5', 'R0298.3', 'R0298.2', 'R0302.4', 'R0302.3', 'R0302.5',
    'R0303.2', 'R0303.3', 'R0303.4', 'R0303.0', 'R0303.5', 'R0304.3', 'R0304.2',
    'R0304.4', 'R0304.0', 'R0304.5', 'R0305.3', 'R0305.4', 'R0305.2', 'R0305.0',
    'R0305.5', 'R0306.3', 'R0306.4', 'R0306.0', 'R0307.6', 'R0308.4', 'R0308.3',
    'R0308.2', 'R0308.5', 'R0309.6', 'R0310.3', 'R0310.5', 'R0310.4', 'R0313.4',
    'R0313.2', 'R0313.3', 'R0313.0', 'R0313.5', 'R0315.0', 'R0315.6', 'R0316.5',
    'R0316.2', 'R0316.4', 'R0317.0', 'R0317.2', 'R0317.3', 'R0317.4', 'R0318.5',
    'R0318.4', 'R0319.4', 'R0319.5', 'R0320.1', 'R0320.3', 'R0320.5', 'R0320.0',
    'R0320.4', 'R0320.2', 'R0321.3', 'R0321.0', 'R0323.0', 'R0323.5', 'R0323.2',
    'R0323.3', 'R0323.4', 'R0325.5', 'R0325.4', 'R0328.4', 'R0328.0', 'R0329.6',
    'R0330.5', 'R0330.0', 'R0330.4', 'R0331.4', 'R0331.0', 'R0331.2', 'R0332.3',
    'R0332.4', 'R0332.2', 'R0333.3', 'R0333.4', 'R0333.2', 'R0333.0', 'R0333.5',
    'R0335.0', 'R0335.4', 'R0335.2', 'R0335.3', 'R0341.0', 'R0341.3', 'R0341.4',
    'R0341.5', 'R0343.2', 'R0343.0', 'R0343.4', 'R0343.3', 'R0346.4', 'R0346.0',
    'R0346.3', 'R0346.2', 'R0347.2', 'R0347.0', 'R0347.3', 'R0347.4', 'R0348.0',
    'R0348.3', 'R0348.4', 'R0348.2', 'R0348.1', 'R0348.5', 'R0349.2', 'R0349.4',
    'R0349.0', 'R0349.3', 'R0349.5', 'R0349.1', 'R0350.2', 'R0350.4', 'R0350.0',
    'R0350.3', 'R0350.5', 'R0350.1', 'R0351.5', 'R0351.2', 'R0351.3', 'R0351.4',
    'R0352.0', 'R0352.3', 'R0352.4', 'R0352.2', 'R0354.3', 'R0354.0', 'R0354.2',
    'R0354.1', 'R0354.4', 'R0354.5', 'R0355.0', 'R0355.3', 'R0355.2', 'R0355.4',
    'R0355.5', 'R0362.4', 'R0362.0', 'R0362.3', 'R0365.4', 'R0367.0', 'R0367.1',
    'R0367.2', 'R0367.3', 'R0368.3', 'R0368.1', 'R0368.2', 'R0368.4', 'R0368.0',
    'R0374.6', 'R0376.0', 'R0376.3', 'R0376.4', 'R0377.3', 'R0377.2', 'R0377.0',
    'R0377.4', 'R0377.5', 'R0380.0', 'R0380.4', 'R0380.3', 'R0380.2', 'R0380.5',
    'R0381.6', 'R0384.6', 'R0385.6', 'R0386.6', 'R0387.6', 'R0388.6', 'R0389.6',
    'R0399.6', 'R0400.6', 'R0401.6', 'R0402.6', 'R0403.6', 'R0404.6', 'R0405.6',
    'R0406.6', 'R0407.6', 'R0408.6', 'R0409.6', 'R0411.6', 'R0417.6', 'R0418.6',
    'R0419.6', 'R0420.6', 'R0420.0', 'R0424.3', 'R0424.4', 'R0424.0', 'R0424.2',
    'R0424.5', 'R0425.1', 'R0425.0', 'R0426.0', 'R0426.5', 'R0426.2', 'R0427.2',
    'R0427.3', 'R0427.0', 'R0427.5', 'R0427.4', 'R0427.1', 'R0428.3', 'R0428.4',
    'R0429.4', 'R0429.5', 'R0429.3', 'R0433.5', 'R0433.4', 'R0433.3', 'R0433.0',
    'R0433.2', 'R0434.3', 'R0434.2', 'R0434.5', 'R0434.4', 'R0434.0', 'R0435.3',
    'R0435.4', 'R0435.0', 'R0435.5', 'R0436.0', 'R0436.3', 'R0437.4', 'R0437.5',
    'R0437.3', 'R0437.2', 'R0437.0', 'R0438.2', 'R0438.3', 'R0438.4', 'R0438.0',
    'R0438.5', 'R0439.0', 'R0439.3', 'R0439.2', 'R0439.4', 'R0439.5', 'R0440.4',
    'R0440.3', 'R0440.2', 'R0440.5', 'R0440.0', 'R0441.2', 'R0441.3', 'R0441.0',
    'R0441.5', 'R0441.4', 'R0441.1', 'R0442.0', 'R0442.3', 'R0442.5', 'R0442.2',
    'R0442.4', 'R0444.6', 'R0446.6', 'R0447.6', 'R0449.3', 'R0451.3', 'R0452.6',
    'R0453.2', 'R0453.0', 'R0453.1', 'R0454.3', 'R0454.5', 'R0454.0', 'R0454.4',
    'R0454.2', 'R0456.5', 'R0456.0', 'R0456.2', 'R0456.4', 'R0456.3', 'R0456.1',
    'R0457.3', 'R0457.4', 'R0457.2', 'R0457.0', 'R0457.5', 'R0458.4', 'R0463.3',
    'R0463.4', 'R0463.5', 'R0463.2', 'R0464.2', 'R0465.0', 'R0465.3', 'R0465.5',
    'R0465.4', 'R0466.2', 'R0466.0', 'R0466.4', 'R0466.3', 'R0466.5', 'R0467.0',
    'R0467.3', 'R0467.5', 'R0467.2', 'R0467.4', 'R0468.3', 'R0469.4', 'R0469.0',
    'R0470.0', 'R0471.0', 'R0472.2', 'R0472.3', 'R0472.0', 'R0472.5', 'R0473.2',
    'R0474.2', 'R0475.2', 'R0475.3', 'R0475.4', 'R0475.5', 'R0476.5', 'R0476.2',
    'R0477.0'
]

def load_existing_data():
    """Load existing workforce and job architecture data"""
    print("Loading existing data files...")
    
    # Load workforce context to get position numbers
    try:
        workforce_df = pd.read_csv(WORKFORCE_FILE)
        position_numbers = workforce_df['Position Number'].unique()
        print(f"Loaded {len(position_numbers):,} unique position numbers from workforce context")
    except FileNotFoundError:
        print(f"Error: Workforce context file not found: {WORKFORCE_FILE}")
        return None, None
    
    # Load job architecture to validate JobProfileIDs
    try:
        job_arch_df = pd.read_csv(JOB_ARCH_FILE)
        job_profile_ids = job_arch_df['JobProfileID'].unique()
        print(f"Loaded {len(job_profile_ids):,} unique JobProfileIDs from job architecture")
    except FileNotFoundError:
        print(f"Error: Job architecture file not found: {JOB_ARCH_FILE}")
        return None, None
    
    return position_numbers, job_profile_ids

def generate_position_mappings(position_numbers, job_profile_ids):
    """Generate one-to-one mapping between positions and job profiles"""
    
    print("Generating position to job profile mappings...")
    
    # Create weighted distribution - some job profiles should be more common than others
    # Simulate realistic distribution where some roles have many positions
    weights = np.random.exponential(scale=2, size=len(job_profile_ids))
    weights = weights / weights.sum()  # Normalize to sum to 1
    
    # Assign JobProfileIDs to positions using weighted random selection
    assigned_job_profiles = np.random.choice(
        job_profile_ids, 
        size=len(position_numbers), 
        replace=True,  # Multiple positions can have same job profile
        p=weights
    )
    
    # Create mapping records
    mapping_records = []
    for position_num, job_profile_id in zip(position_numbers, assigned_job_profiles):
        record = {
            'Position_Number': int(position_num),
            'JobProfileID': job_profile_id
        }
        mapping_records.append(record)
    
    return mapping_records

def main():
    """Generate and save position to job profile mapping data"""
    
    print("=" * 60)
    print("Generating Position to Job Profile Mapping Data")
    print("=" * 60)
    
    # Load existing data
    position_numbers, existing_job_profile_ids = load_existing_data()
    if position_numbers is None or existing_job_profile_ids is None:
        print("Failed to load required data files. Exiting.")
        return
    
    # Use provided JobProfileIDs (717 IDs from user)
    print(f"Using {len(JOB_PROFILE_IDS)} JobProfileIDs provided by user")
    
    # Validate that provided IDs match existing job architecture
    matching_ids = set(JOB_PROFILE_IDS) & set(existing_job_profile_ids)
    print(f"Found {len(matching_ids)} matching JobProfileIDs between provided list and job architecture")
    
    # Generate mappings
    mapping_data = generate_position_mappings(position_numbers, JOB_PROFILE_IDS)
    
    # Convert to DataFrame
    df = pd.DataFrame(mapping_data)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    output_file = OUTPUT_DIR / "position_job_mapping.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\nGenerated position to job profile mapping:")
    print(f"- Records: {len(df):,}")
    print(f"- Unique Positions: {df['Position_Number'].nunique():,}")
    print(f"- Unique JobProfileIDs: {df['JobProfileID'].nunique():,}")
    print(f"- File: {output_file}")
    print(f"- Size: {output_file.stat().st_size / 1024:.1f} KB")
    
    # Show distribution statistics
    print(f"\nJobProfile Distribution (Top 10):")
    job_profile_counts = df['JobProfileID'].value_counts()
    for job_id, count in job_profile_counts.head(10).items():
        print(f"- {job_id}: {count} positions")
    
    # Print sample of the data
    print(f"\nSample mapping data:")
    print(df[['Position_Number', 'JobProfileID']].head(10))
    
    # Show schema info
    print(f"\nSchema Info:")
    print(df.info())
    
    print(f"\nâœ… Position to Job Profile mapping completed successfully!")

if __name__ == "__main__":
    main() 
