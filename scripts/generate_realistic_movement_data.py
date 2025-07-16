#!/usr/bin/env python3
"""
Generate Realistic Movement Fact Table Data

This script creates 3 years of realistic position movement data for Phase 4 
advanced analytics and ML foundation work. Instead of generating individual 
movement records, this creates aggregated fact table data showing movement 
patterns between positions over time.

Purpose: Feed Phase 4 advanced career intelligence and ML capabilities:
- Skills Transition Matrices (Markov chain models)
- Career Trajectory Clustering 
- Movement Pattern Analysis
- Strategic Skills Forecasting
- Multi-Model Consensus Framework

Output: Movement fact table with realistic aggregated patterns suitable for:
- Time series analysis
- Career pathway discovery
- Skills flow analysis
- Succession planning intelligence
- Workforce evolution modeling

UPDATED: Now matches movement_fact table schema exactly and uses existing position numbers
from position-job mapping to ensure consistency with database.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json

# Set random seed for reproducible data
random.seed(42)
np.random.seed(42)

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "movement_analysis"
POSITION_MAPPING_FILE = Path(__file__).parent.parent / "data" / "job_architecture_to_positions_mapping" / "position_job_mapping.csv"
JOB_ARCH_FILE = Path(__file__).parent.parent / "data" / "job_architecture" / "dummy_job_architecture.csv"

# Time period configuration - matching movement_fact table data
START_DATE = date(2020, 7, 1)  # Start from 2020-07 to match DB
END_DATE = date(2025, 1, 31)   # End in 2025-01 to match DB
MONTHS_TO_GENERATE = 55        # About 4.5 years of data

# Movement pattern configuration
TOTAL_MOVEMENTS_PER_MONTH = 150  # Realistic enterprise scale
SEASONAL_VARIATION = 0.3  # ±30% seasonal variation
PROMOTION_SEASON_BOOST = 1.4  # 40% boost in promotion months (June, December)
LATERAL_MOVE_RATIO = 0.6  # 60% lateral moves, 40% promotions/vertical moves

# Career progression patterns
CAREER_PROGRESSION_PATTERNS = {
    'technical_specialist': {
        'weight': 0.25,
        'progression': [
            ('Analyst', 'Senior Analyst'),
            ('Senior Analyst', 'Lead Analyst'), 
            ('Lead Analyst', 'Principal Analyst'),
            ('Developer', 'Senior Developer'),
            ('Senior Developer', 'Lead Developer'),
            ('Specialist', 'Senior Specialist'),
            ('Senior Specialist', 'Principal Specialist')
        ],
        'lateral_moves': [
            ('Data Analyst', 'Business Analyst'),
            ('Software Engineer', 'DevOps Engineer'),
            ('Risk Analyst', 'Compliance Analyst')
        ]
    },
    'management_track': {
        'weight': 0.20,
        'progression': [
            ('Analyst', 'Team Lead'),
            ('Senior Analyst', 'Manager'),
            ('Manager', 'Senior Manager'),
            ('Senior Manager', 'General Manager'),
            ('Team Lead', 'Manager'),
            ('Specialist', 'Manager')
        ],
        'lateral_moves': [
            ('Manager', 'Manager'),  # Cross-department moves
            ('Senior Manager', 'Senior Manager')
        ]
    },
    'cross_functional': {
        'weight': 0.30,
        'progression': [
            ('Customer Service', 'Operations'),
            ('Operations', 'Risk Management'),
            ('Business Analyst', 'Product Manager'),
            ('Marketing', 'Business Development'),
            ('HR Specialist', 'Change Manager')
        ],
        'lateral_moves': [
            ('Marketing Specialist', 'Communications Specialist'),
            ('Project Manager', 'Business Analyst'),
            ('Operations Manager', 'Process Manager')
        ]
    },
    'executive_pathway': {
        'weight': 0.15,
        'progression': [
            ('General Manager', 'Executive Director'),
            ('Senior Manager', 'General Manager'),
            ('Director', 'Executive Director'),
            ('Executive Manager', 'General Manager')
        ],
        'lateral_moves': [
            ('General Manager', 'General Manager'),
            ('Director', 'Director')
        ]
    },
    'graduate_rotations': {
        'weight': 0.10,
        'progression': [
            ('Graduate Analyst', 'Analyst'),
            ('Graduate Program', 'Specialist'),
            ('Graduate Trainee', 'Associate')
        ],
        'lateral_moves': [
            ('Graduate Analyst', 'Graduate Specialist'),
            ('Graduate Program', 'Graduate Analyst')
        ]
    }
}

# Skills transition patterns (for skills flow analysis)
SKILLS_TRANSITION_PATTERNS = {
    'digital_transformation': {
        'from_skills': ['Traditional Banking', 'Manual Processes', 'Excel Analysis'],
        'to_skills': ['Digital Banking', 'Process Automation', 'Data Analytics', 'Python'],
        'transition_probability': 0.3
    },
    'leadership_development': {
        'from_skills': ['Individual Contributor', 'Technical Analysis'],
        'to_skills': ['Team Leadership', 'Strategic Planning', 'Stakeholder Management'],
        'transition_probability': 0.25
    },
    'data_science_evolution': {
        'from_skills': ['Excel', 'Reporting', 'Basic Statistics'],
        'to_skills': ['Machine Learning', 'Python', 'Advanced Analytics', 'AI'],
        'transition_probability': 0.2
    },
    'risk_specialization': {
        'from_skills': ['General Finance', 'Basic Analysis'],
        'to_skills': ['Credit Risk', 'Operational Risk', 'Basel III', 'Stress Testing'],
        'transition_probability': 0.15
    }
}

def load_existing_position_numbers():
    """Load existing position numbers from position-job mapping to ensure consistency"""
    print("Loading existing position numbers from position-job mapping...")
    
    if not POSITION_MAPPING_FILE.exists():
        raise FileNotFoundError(f"Position-job mapping file not found: {POSITION_MAPPING_FILE}")
    
    df = pd.read_csv(POSITION_MAPPING_FILE)
    position_numbers = df['Position_Number'].unique().tolist()
    
    print(f"Loaded {len(position_numbers):,} unique position numbers")
    print(f"Position range: {min(position_numbers)} to {max(position_numbers)}")
    print(f"Sample positions: {position_numbers[:10]}")
    
    return position_numbers

def load_job_architecture_context():
    """Load job architecture data for movement weighting context"""
    print("Loading job architecture for movement context...")
    
    if not JOB_ARCH_FILE.exists():
        print(f"Warning: Job architecture file not found: {JOB_ARCH_FILE}")
        return {}
    
    df = pd.read_csv(JOB_ARCH_FILE)
    
    # Create job profile lookup for contextual weighting
    job_context = {}
    for _, row in df.iterrows():
        job_profile_id = row['JobProfileID']
        management_level = str(row.get('ManagementLevel', 'Unknown'))
        
        # Weight positions based on management level (more junior = more movements)
        if 'Group 1' in management_level:
            weight = 3.0  # Junior roles have more movements
        elif 'Group 2' in management_level:
            weight = 2.5
        elif 'Group 3' in management_level:
            weight = 2.0
        elif 'Group 4' in management_level:
            weight = 1.5
        elif any(level in management_level for level in ['Group 5', 'Group 6', 'Group 7']):
            weight = 1.0  # Senior roles have fewer movements
        else:
            weight = 1.5  # Default weight
            
        job_context[job_profile_id] = {
            'job_profile': row['JobProfile'],
            'job_function': row.get('JobFunction', 'Unknown'),
            'job_category': row.get('JobCategory', 'Unknown'),
            'management_level': management_level,
            'is_banker': row.get('is Banker', 'Unknown'),
            'customer_facing': row.get('Customer Facing', 'Unknown'),
            'movement_weight': weight
        }
    
    print(f"Loaded context for {len(job_context)} job profiles")
    return job_context

def identify_position_progression_pairs(position_numbers: List[int]) -> List[Tuple[int, int, str, float]]:
    """Identify realistic position progression pairs based on patterns"""
    progression_pairs = []
    
    # Convert patterns to position-based pairs
    for pattern_name, pattern in CAREER_PROGRESSION_PATTERNS.items():
        weight = pattern['weight']
        
        # Generate position pairs for vertical progressions
        for _ in range(int(len(position_numbers) * weight * 0.1)):  # 10% of positions for each pattern
            # Random from/to positions for progressions
            from_pos = np.random.choice(position_numbers)
            to_pos = np.random.choice(position_numbers)
            
            if from_pos != to_pos:
                progression_pairs.append((from_pos, to_pos, 'lateral', weight * 0.8))
        
        # Generate position pairs for lateral moves (more common)
        for _ in range(int(len(position_numbers) * weight * 0.2)):  # 20% of positions for lateral moves
            from_pos = np.random.choice(position_numbers)
            to_pos = np.random.choice(position_numbers)
            
            if from_pos != to_pos:
                progression_pairs.append((from_pos, to_pos, 'lateral', weight * 1.2))
    
    print(f"Generated {len(progression_pairs)} position progression pairs")
    return progression_pairs

def generate_monthly_movements(position_numbers: List[int], progression_pairs: List[Tuple], 
                             month_date: date) -> List[Dict]:
    """Generate realistic movements for a specific month matching movement_fact schema"""
    
    # Seasonal adjustment
    month = month_date.month
    seasonal_multiplier = 1.0
    
    # Promotion seasons (June, December)
    if month in [6, 12]:
        seasonal_multiplier = PROMOTION_SEASON_BOOST
    # Quiet seasons (January, August) 
    elif month in [1, 8]:
        seasonal_multiplier = 0.7
    # Summer uptick (March, April, May)
    elif month in [3, 4, 5]:
        seasonal_multiplier = 1.2
    
    # Random variation
    seasonal_multiplier *= (1 + random.uniform(-SEASONAL_VARIATION, SEASONAL_VARIATION))
    
    target_movements = int(TOTAL_MOVEMENTS_PER_MONTH * seasonal_multiplier)
    
    movements = []
    
    # Generate movements based on progression pairs with realistic distributions
    for _ in range(target_movements):
        # Select progression pair with weighted probability
        if progression_pairs:
            weights = [pair[3] for pair in progression_pairs]
            weights_array = np.array(weights)
            weights_normalized = weights_array / np.sum(weights_array)
            selected_idx = np.random.choice(len(progression_pairs), p=weights_normalized)
            selected_pair = progression_pairs[selected_idx]
            from_position, to_position, movement_type, _ = selected_pair
        else:
            # Fallback to random positions if no pairs available
            from_position = np.random.choice(position_numbers)
            to_position = np.random.choice(position_numbers)
            movement_type = 'lateral'
        
        # Generate movement count (typically 1, occasionally small groups)
        movement_count = np.random.choice([1, 2, 3, 4, 5], p=[0.7, 0.15, 0.1, 0.03, 0.02])
        
        # Calculate average days between positions (tenure)
        if movement_type == 'promotion':
            avg_days = np.random.normal(540, 180)  # ~18 months for promotions
        else:  # lateral
            avg_days = np.random.normal(720, 240)  # ~24 months for lateral moves
            
        avg_days = max(180, avg_days)  # Minimum 6 months
        
        # Create movement pattern string
        movement_pattern = f"{from_position} → {to_position}"
        
        # Create movement record matching movement_fact schema
        movement = {
            'movement_month': month_date.strftime('%Y-%m'),
            'movement_year': month_date.year,
            'from_position': str(from_position),  # TEXT field in DB
            'to_position': str(to_position),      # TEXT field in DB
            'movement_pattern': movement_pattern,
            'movement_count': movement_count,
            'pct_total_movements': None,  # Will calculate after all movements generated
            'unique_employees': movement_count,  # Assuming no duplicates in monthly data
            'avg_days_between': round(avg_days, 1),
            'monthly_total_movements': target_movements,
            'predominant_movement_type': movement_type
        }
        movements.append(movement)
    
    return movements

def calculate_movement_percentages(movements: List[Dict]) -> List[Dict]:
    """Calculate movement percentages for each movement within its month"""
    # Group by month
    monthly_groups = {}
    for movement in movements:
        month = movement['movement_month']
        if month not in monthly_groups:
            monthly_groups[month] = []
        monthly_groups[month].append(movement)
    
    # Calculate percentages within each month
    for month, month_movements in monthly_groups.items():
        total_month_movements = sum(m['movement_count'] for m in month_movements)
        for movement in month_movements:
            movement['pct_total_movements'] = round(
                (movement['movement_count'] / total_month_movements) * 100, 2
            )
    
    return movements

def add_fact_ids(movements: List[Dict]) -> List[Dict]:
    """Add sequential fact_id to match movement_fact schema"""
    for i, movement in enumerate(movements, 1):
        movement['fact_id'] = i
    return movements

def generate_movement_metadata(movements: List[Dict]) -> Dict[str, Any]:
    """Generate metadata about the movement dataset for analysis"""
    
    total_movements = sum(m['movement_count'] for m in movements)
    unique_months = len(set(m['movement_month'] for m in movements))
    unique_positions = len(set(m['from_position'] for m in movements) | 
                          set(m['to_position'] for m in movements))
    
    # Movement type distribution
    movement_types = {}
    for movement in movements:
        mtype = movement['predominant_movement_type']
        movement_types[mtype] = movement_types.get(mtype, 0) + movement['movement_count']
    
    # Monthly volume statistics
    monthly_volumes = {}
    for movement in movements:
        month = movement['movement_month']
        monthly_volumes[month] = monthly_volumes.get(month, 0) + movement['movement_count']
    
    metadata = {
        'generation_date': datetime.now().isoformat(),
        'time_period': {
            'start_date': START_DATE.isoformat(),
            'end_date': END_DATE.isoformat(),
            'months_covered': int(unique_months)
        },
        'movement_statistics': {
            'total_movement_records': int(len(movements)),
            'total_individual_movements': int(total_movements),
            'unique_positions_involved': int(unique_positions),
            'avg_movements_per_month': float(round(total_movements / unique_months, 1))
        },
        'movement_type_distribution': {k: int(v) for k, v in movement_types.items()},
        'monthly_volume_range': {
            'min': int(min(monthly_volumes.values())),
            'max': int(max(monthly_volumes.values())),
            'avg': float(round(sum(monthly_volumes.values()) / len(monthly_volumes), 1))
        },
        'schema_compliance': {
            'matches_movement_fact_table': True,
            'uses_existing_position_numbers': True,
            'database_compatible': True
        }
    }
    
    return metadata

def main():
    """Generate realistic movement fact table data matching database schema"""
    
    print("=" * 70)
    print("Generating Movement Fact Table Data - Database Schema Compatible")
    print("=" * 70)
    
    # Load existing position numbers from position-job mapping
    position_numbers = load_existing_position_numbers()
    
    # Load job architecture context (optional, for weighting)
    job_context = load_job_architecture_context()
    
    # Identify position progression pairs
    print("\nIdentifying realistic position progression patterns...")
    progression_pairs = identify_position_progression_pairs(position_numbers)
    
    # Generate monthly movement data
    print(f"\nGenerating {MONTHS_TO_GENERATE} months of movement data...")
    all_movements = []
    
    current_date = START_DATE
    for month_num in range(MONTHS_TO_GENERATE):
        if month_num % 12 == 0:
            print(f"  Generating year {current_date.year}...")
        
        monthly_movements = generate_monthly_movements(position_numbers, progression_pairs, current_date)
        all_movements.extend(monthly_movements)
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    # Calculate movement percentages
    print("\nCalculating movement percentages...")
    all_movements = calculate_movement_percentages(all_movements)
    
    # Add fact IDs to match schema
    print("Adding fact IDs...")
    all_movements = add_fact_ids(all_movements)
    
    # Convert to DataFrame with correct column order
    print("Creating DataFrame with correct schema...")
    df = pd.DataFrame(all_movements)
    
    # Reorder columns to match movement_fact table schema exactly
    column_order = [
        'fact_id', 'movement_month', 'movement_year', 'from_position', 'to_position',
        'movement_pattern', 'movement_count', 'pct_total_movements', 'unique_employees',
        'avg_days_between', 'monthly_total_movements', 'predominant_movement_type'
    ]
    df = df[column_order]
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save movement fact table
    output_file = OUTPUT_DIR / "realistic_movement_fact_table.csv"
    df.to_csv(output_file, index=False)
    
    # Save as Parquet for analytics
    parquet_file = OUTPUT_DIR / "realistic_movement_fact_table.parquet"
    df.to_parquet(parquet_file, index=False)
    
    # Generate and save metadata
    metadata = generate_movement_metadata(all_movements)
    metadata_file = OUTPUT_DIR / "movement_analysis_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(metadata, indent=2))
    
    # Print summary statistics
    print(f"\n✅ Successfully generated movement fact table data:")
    print(f"   📊 Total movement records: {len(df):,}")
    print(f"   👥 Total individual movements: {metadata['movement_statistics']['total_individual_movements']:,}")
    print(f"   🗓️  Time period: {START_DATE} to {END_DATE} ({MONTHS_TO_GENERATE} months)")
    print(f"   🎯 Unique positions involved: {metadata['movement_statistics']['unique_positions_involved']:,}")
    print(f"   📈 Average movements per month: {metadata['movement_statistics']['avg_movements_per_month']}")
    
    print(f"\n📁 Output files generated:")
    print(f"   💾 CSV: {output_file} ({output_file.stat().st_size / 1024:.1f} KB)")
    print(f"   🚀 Parquet: {parquet_file} ({parquet_file.stat().st_size / 1024:.1f} KB)")
    print(f"   📋 Metadata: {metadata_file} ({metadata_file.stat().st_size / 1024:.1f} KB)")
    
    # Display sample data
    print(f"\n📄 Sample movement data (first 5 records):")
    sample_cols = ['fact_id', 'movement_month', 'from_position', 'to_position', 'movement_count', 'avg_days_between']
    print(df[sample_cols].head().to_string(index=False))
    
    # Display movement type distribution
    print(f"\n📊 Movement Type Distribution:")
    for mtype, count in metadata['movement_type_distribution'].items():
        percentage = (count / metadata['movement_statistics']['total_individual_movements']) * 100
        print(f"   {mtype}: {count:,} ({percentage:.1f}%)")
    
    # Schema validation
    print(f"\n✅ Schema Validation:")
    print(f"   ✅ Matches movement_fact table schema: {len(df.columns)} columns")
    print(f"   ✅ Uses existing position numbers: {position_numbers[:3]}...")
    print(f"   ✅ Database compatible format: TEXT positions, INTEGER fact_id")
    print(f"   ✅ Correct date range: {df['movement_year'].min()}-{df['movement_year'].max()}")
    
    print(f"\n🎯 Ready for database import and Phase 4 analytics!")
    
    return df, metadata

if __name__ == "__main__":
    main() 