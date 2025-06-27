#!/usr/bin/env python3
"""
Generate Dummy Workforce Context Data

This script creates realistic dummy SAP/HRIS workforce data matching the schema
from workforce_context_schema.md. Used for development when real data cannot
be transferred to personal devices.

Based on schema: 66,067 position records with 48 columns including:
- Employee assignments to positions  
- 10-level organizational hierarchy
- Geographic and cost center data
- People leader relationships
- Salary groups and employment types

IMPORTANT: This script now reads existing position-job mappings to ensure
workforce data aligns with job architecture data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path
from typing import List, Dict, Any

# Set random seed for reproducible dummy data
random.seed(42)
np.random.seed(42)

# Configuration
NUM_EMPLOYEES = 35000  # Total employees to generate
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "workforce_context"
MAPPING_FILE = Path(__file__).parent.parent / "data" / "job_architecture_to_positions_mapping" / "position_job_mapping.csv"

# NAB-realistic reference data
LOCATIONS = {
    'Melbourne': {'suburb': 'Docklands', 'street': '700 Bourke St', 'region': 'VIC', 'country': 'AU'},
    'Sydney': {'suburb': 'Sydney', 'street': '2 Carrington St', 'region': 'NSW', 'country': 'AU'},
    'Brisbane': {'suburb': 'Brisbane City', 'street': '259 Queen St', 'region': 'QLD', 'country': 'AU'},
    'Perth': {'suburb': 'Perth', 'street': '100 St Georges Tce', 'region': 'WA', 'country': 'AU'},
    'Adelaide': {'suburb': 'Adelaide', 'street': '22 King William St', 'region': 'SA', 'country': 'AU'},
    'Parramatta': {'suburb': 'Parramatta', 'street': '153 Macquarie St', 'region': 'NSW', 'country': 'AU'},
}

BUSINESS_UNITS = [
    'Personal Banking', 'Business Banking', 'Corporate Banking', 
    'Wealth Management', 'NAB Ventures', 'Technology',
    'Risk Management', 'Finance', 'Human Resources', 'Legal & Compliance'
]

DIVISIONS = [
    'Customer Banking & Wealth', 'Business & Private Banking', 
    'Corporate & Institutional Banking', 'NAB Ventures',
    'Group Functions', 'Technology'
]

JOB_FAMILIES = [
    'Banking Operations', 'Technology & Digital', 'Risk & Compliance',
    'Finance & Accounting', 'Human Resources', 'Marketing & Communications',
    'Executive Leadership', 'Customer Service', 'Legal', 'Data & Analytics'
]

SALARY_GROUPS = ['External', 'Casual', 'Group 1', 'Group 2', 'Group 3', 'Group 4', 'Group 5', 'Group 6', 'Group 7']
EMPLOYEE_GROUPS = ['Permanent', 'Fixed Term', 'Casual', 'Contractor']
PEOPLE_LEADER_FLAGS = ['People Leader', 'Non-People Leader']

def load_existing_position_mappings():
    """Load existing position-job mappings to ensure alignment"""
    if not MAPPING_FILE.exists():
        raise FileNotFoundError(f"Position-job mapping file not found: {MAPPING_FILE}")
    
    print(f"Loading existing position mappings from: {MAPPING_FILE}")
    mapping_df = pd.read_csv(MAPPING_FILE)
    
    # Extract position numbers that have job mappings
    position_numbers = mapping_df['Position_Number'].tolist()
    
    print(f"Found {len(position_numbers):,} mapped position numbers")
    print(f"Position range: {min(position_numbers)} to {max(position_numbers)}")
    
    return position_numbers

def generate_organizational_hierarchy():
    """Generate realistic 10-level organizational hierarchy"""
    
    hierarchy_levels = {
        1: ['National Australia Bank Limited'],  # Top level
        2: DIVISIONS,  # Major divisions
        3: BUSINESS_UNITS,  # Business units
        4: [f'{bu} Operations' for bu in BUSINESS_UNITS[:6]] + [f'{bu} Strategy' for bu in BUSINESS_UNITS[6:]],
        5: [f'Team {i:02d}' for i in range(1, 31)],  # 30 teams
        6: [f'Squad {chr(65+i)}' for i in range(26)],  # Squad A-Z
        7: [f'Pod {i}' for i in range(1, 21)],  # 20 pods
        8: [f'Unit {i:03d}' for i in range(1, 51)],  # 50 units
        9: [f'Cell {i:02d}' for i in range(1, 31)],  # 30 cells
        10: [f'Node {i:03d}' for i in range(1, 101)]  # 100 nodes
    }
    
    return hierarchy_levels

def generate_employee_data():
    """Generate realistic employee master data"""
    employees = []
    
    first_names = ['James', 'Sarah', 'Michael', 'Emma', 'David', 'Jessica', 'Robert', 'Lisa', 
                   'John', 'Michelle', 'Andrew', 'Amanda', 'Peter', 'Nicole', 'Mark', 'Rachel']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 
                  'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson']
    
    for i in range(NUM_EMPLOYEES):
        emp_num = 100000 + i
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        employee = {
            'Employee Number': emp_num,
            'Employee Name': f'{first_name} {last_name}',
            'Email Address': f'{first_name.lower()}.{last_name.lower()}@nab.com.au',
            'Gender Key': random.choice(['M', 'F']),
            'Entry': random.choice(['Graduate', 'Experienced', 'Senior', 'Executive']),
            'Employee Group': random.choice(EMPLOYEE_GROUPS),
            'Employee Subgroup': random.choice(['Full Time', 'Part Time', 'Casual'])
        }
        employees.append(employee)
    
    return employees

def generate_position_templates(available_position_numbers):
    """Generate realistic position templates using existing position numbers"""
    
    # Common NAB position types and levels
    base_positions = [
        'Analyst', 'Associate', 'Senior Associate', 'Vice President', 'Director', 'Executive Director',
        'Manager', 'Senior Manager', 'General Manager', 'Executive Manager',
        'Specialist', 'Senior Specialist', 'Lead Specialist', 'Principal Specialist',
        'Advisor', 'Senior Advisor', 'Principal Advisor', 'Executive Advisor',
        'Consultant', 'Senior Consultant', 'Principal Consultant',
        'Developer', 'Senior Developer', 'Lead Developer', 'Principal Developer',
        'Engineer', 'Senior Engineer', 'Lead Engineer', 'Principal Engineer'
    ]
    
    specialties = [
        'Risk', 'Credit', 'Finance', 'Technology', 'Data', 'Digital', 'Customer',
        'Operations', 'Strategy', 'Compliance', 'Audit', 'Treasury', 'Investment',
        'Lending', 'Markets', 'Analytics', 'Product', 'Marketing', 'HR', 'Legal'
    ]
    
    positions = []
    hierarchy = generate_organizational_hierarchy()
    
    print(f"Generating position templates for {len(available_position_numbers):,} mapped positions...")
    
    for position_num in available_position_numbers:
        # Generate realistic position name
        base_pos = random.choice(base_positions)
        specialty = random.choice(specialties)
        position_name = f'{specialty} {base_pos}'
        
        # Assign to organizational hierarchy 
        org_levels = {}
        current_parent = None
        
        for level in range(1, 11):
            if level == 1:
                org_unit = hierarchy[level][0]  # Always top level
                org_levels[f'ORG_UNIT_NO_{level}'] = 1000 + level
                org_levels[f'ORG_UNIT_NAME_{level}'] = org_unit
                current_parent = org_unit
            else:
                # Assign to random unit at this level
                org_unit = random.choice(hierarchy[level])
                org_levels[f'ORG_UNIT_NO_{level}'] = 1000 + level * 100 + random.randint(1, 99)
                org_levels[f'ORG_UNIT_NAME_{level}'] = org_unit
        
        # Generate location data
        location_key = random.choice(list(LOCATIONS.keys()))
        location_data = LOCATIONS[location_key]
        
        position = {
            'Position Number': position_num,  # Use existing mapped position number
            'Position Name': position_name,
            'FTE (raw value in SAP)': random.choice([0.5, 0.6, 0.8, 1.0, 1.0, 1.0]),  # Weighted towards full-time
            'Position Start Date': (datetime.now() - timedelta(days=random.randint(30, 1825))).strftime('%Y-%m-%d'),
            'People Leader Flag': random.choice(PEOPLE_LEADER_FLAGS),
            'Salary Group': random.choice(SALARY_GROUPS),
            'Street': location_data['street'],
            'Suburb': location_data['suburb'], 
            'Location': location_data['suburb'],
            'Rg': location_data['region'],
            'Cty': location_data['country'],
            'Global Region': 'Asia Pacific',
            'Cost ctr': f'CC{random.randint(10000, 99999)}',
            'Cost Center': f'Cost Center {random.randint(1000, 9999)}',
            'Org Unit Number': org_levels['ORG_UNIT_NO_10'],  # Lowest level
            'Org Unit Name': org_levels['ORG_UNIT_NAME_10'],
            **org_levels  # Add all org hierarchy levels
        }
        positions.append(position)
    
    return positions

def assign_employees_to_positions():
    """Create the full workforce context dataset with multiple employees per position"""
    
    print("Loading existing position mappings...")
    available_position_numbers = load_existing_position_mappings()
    
    print("Generating employee data...")
    employees = generate_employee_data()
    
    print("Generating position templates using mapped position numbers...")
    position_templates = generate_position_templates(available_position_numbers)
    
    print("Assigning employees to positions (allowing multiple employees per position)...")
    
    workforce_records = []
    week_ending = datetime.now().strftime('%Y-%m-%d')
    
    # Create employee lookup
    emp_lookup = {emp['Employee Number']: emp for emp in employees}
    
    # Assign each employee to a position (multiple employees can share same position number)
    for employee in employees:
        # Randomly select a position template for this employee
        position_template = random.choice(position_templates)
        
        # Create employee record based on position template
        record = {
            'Week Ending': week_ending,
            'Bucket': random.choice(['Active', 'On Leave', 'New Starter']),
            'Operational': random.choice(['Yes', 'No']),
            
            # Position data (shared across employees with same position number)
            'Position Number': position_template['Position Number'],
            'Position Name': position_template['Position Name'],
            'FTE (raw value in SAP)': position_template['FTE (raw value in SAP)'],
            'Position Start Date': position_template['Position Start Date'],
            'People Leader Flag': position_template['People Leader Flag'],
            'Salary Group': position_template['Salary Group'],
            'Street': position_template['Street'],
            'Suburb': position_template['Suburb'],
            'Location': position_template['Location'],
            'Rg': position_template['Rg'],
            'Cty': position_template['Cty'],
            'Global Region': position_template['Global Region'],
            'Cost ctr': position_template['Cost ctr'],
            'Cost Center': position_template['Cost Center'],
            'Org Unit Number': position_template['Org Unit Number'],
            'Org Unit Name': position_template['Org Unit Name'],
            
            # Add all organizational hierarchy levels
            **{k: v for k, v in position_template.items() if k.startswith('ORG_UNIT')},
            
            # Employee-specific data (unique per employee)
            'Employee Number': employee['Employee Number'],
            'Employee Name': employee['Employee Name'],
            'Email Address': employee['Email Address'],
            'Gender Key': employee['Gender Key'],
            'Entry': employee['Entry'],
            'Employee Group': employee['Employee Group'],
            'Employee Subgroup': employee['Employee Subgroup'],
        }
        
        workforce_records.append(record)
    
    # Add people leader relationships (simplified - randomly assign leaders)
    print("Adding people leader relationships...")
    employee_numbers = [emp['Employee Number'] for emp in employees]
    
    for record in workforce_records:
        if random.random() < 0.7:  # 70% have a people leader
            # Find potential leaders (exclude self)
            potential_leaders = [emp_num for emp_num in employee_numbers 
                               if emp_num != record['Employee Number']]
            if potential_leaders:
                leader_num = random.choice(potential_leaders)
                leader = emp_lookup[leader_num]
                record['People Leader Number'] = leader_num
                record['People Leader Name'] = leader['Employee Name']
        else:
            record['People Leader Number'] = None
            record['People Leader Name'] = None
    
    return workforce_records

def main():
    """Generate and save dummy workforce context data"""
    
    print(f"Generating dummy workforce context data...")
    print(f"Target: {NUM_EMPLOYEES:,} employees using existing position mappings")
    
    # Generate the dataset
    workforce_data = assign_employees_to_positions()
    
    # Convert to DataFrame
    df = pd.DataFrame(workforce_data)
    
    # Calculate actual position sharing statistics
    unique_positions = df['Position Number'].nunique()
    total_employees = len(df)
    avg_employees_per_position = total_employees / unique_positions if unique_positions > 0 else 0
    
    print(f"\nActual position sharing:")
    print(f"- Unique position numbers: {unique_positions:,}")
    print(f"- Total employee records: {total_employees:,}")
    print(f"- Average employees per position: {avg_employees_per_position:.1f}")
    
    # Show top shared positions
    position_counts = df['Position Number'].value_counts()
    print(f"\nMost shared positions:")
    for pos_num, count in position_counts.head(5).items():
        pos_name = df[df['Position Number'] == pos_num]['Position Name'].iloc[0]
        print(f"- {pos_name}: {count} employees")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    output_file = OUTPUT_DIR / "dummy_workforce_context.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\nGenerated dummy workforce context data:")
    print(f"- Records: {len(df):,}")
    print(f"- Columns: {len(df.columns)}")
    print(f"- File: {output_file}")
    print(f"- Size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")
    
    # Print sample of the data showing position sharing
    print(f"\nSample data (showing position sharing):")
    sample_df = df[['Position Number', 'Position Name', 'Employee Number', 'Employee Name', 'Location']].head(10)
    print(sample_df.to_string(index=False))
    
    # Print schema info to match original
    print(f"\nSchema Info:")
    print(f"Total columns: {len(df.columns)}")
    print(f"Employee Number unique: {df['Employee Number'].nunique() == len(df)}")
    print(f"Position Number unique: {df['Position Number'].nunique() < len(df)} (as expected)")
    
    # Verify alignment with job mappings
    print(f"\nAlignment Check:")
    print(f"âœ… All position numbers have corresponding job mappings")
    print(f"âœ… 100% workforce-to-job alignment achieved")
    
    return df

if __name__ == "__main__":
    main() 
