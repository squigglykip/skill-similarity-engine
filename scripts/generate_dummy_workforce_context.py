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
NUM_POSITIONS = 5000  # Smaller than real 66K for development
NUM_EMPLOYEES = 3500  # Some positions vacant
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "workforce_context"

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

def generate_position_data():
    """Generate realistic position data with NAB-style naming"""
    
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
    
    for i in range(NUM_POSITIONS):
        position_num = 50000000 + i
        
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
                org_levels[f'ORG UNIT NO_{level}'] = 1000 + level
                org_levels[f'ORG UNIT NAME_{level}'] = org_unit
                current_parent = org_unit
            else:
                # Assign to random unit at this level
                org_unit = random.choice(hierarchy[level])
                org_levels[f'ORG UNIT NO_{level}'] = 1000 + level * 100 + random.randint(1, 99)
                org_levels[f'ORG UNIT NAME_{level}'] = org_unit
        
        # Generate location data
        location_key = random.choice(list(LOCATIONS.keys()))
        location_data = LOCATIONS[location_key]
        
        position = {
            'Position Number': position_num,
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
            'Org Unit Number': org_levels['ORG UNIT NO_10'],  # Lowest level
            'Org Unit Name': org_levels['ORG UNIT NAME_10'],
            **org_levels  # Add all org hierarchy levels
        }
        positions.append(position)
    
    return positions

def assign_employees_to_positions():
    """Create the full workforce context dataset"""
    
    print("Generating employee data...")
    employees = generate_employee_data()
    
    print("Generating position data...")
    positions = generate_position_data()
    
    print("Assigning employees to positions...")
    
    workforce_records = []
    week_ending = datetime.now().strftime('%Y-%m-%d')
    
    # Create employee lookup
    emp_lookup = {emp['Employee Number']: emp for emp in employees}
    
    # Assign employees to positions (some positions may be vacant)
    assigned_employees = random.sample(list(emp_lookup.keys()), min(len(employees), len(positions)))
    
    for i, position in enumerate(positions):
        # Base record with position data
        record = {
            'Week Ending': week_ending,
            'Bucket': random.choice(['Active', 'On Leave', 'New Starter']) if i < len(assigned_employees) else 'Vacant',
            'Operational': random.choice(['Yes', 'No', None]),
            **position
        }
        
        # Add employee data if position is filled
        if i < len(assigned_employees):
            emp_num = assigned_employees[i]
            employee = emp_lookup[emp_num]
            record.update(employee)
            
            # Add people leader relationship (simplified)
            if random.random() < 0.8:  # 80% have a people leader
                leader_pool = [e for e in assigned_employees if e != emp_num]
                if leader_pool:
                    leader_num = random.choice(leader_pool)
                    leader = emp_lookup[leader_num]
                    record['People Leader Number'] = leader_num
                    record['People Leader Name'] = leader['Employee Name']
        else:
            # Vacant position - null out employee fields
            record.update({
                'Employee Number': None,
                'Employee Name': None,
                'Email Address': None,
                'Gender Key': None,
                'Entry': None,
                'Employee Group': None,
                'Employee Subgroup': None,
                'People Leader Number': None,
                'People Leader Name': None,
                'Operational': None
            })
        
        workforce_records.append(record)
    
    return workforce_records

def main():
    """Generate and save dummy workforce context data"""
    
    print(f"Generating dummy workforce context data...")
    print(f"Target: {NUM_POSITIONS:,} positions, {NUM_EMPLOYEES:,} employees")
    
    # Generate the dataset
    workforce_data = assign_employees_to_positions()
    
    # Convert to DataFrame
    df = pd.DataFrame(workforce_data)
    
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
    
    # Print sample of the data
    print(f"\nSample data:")
    print(df[['Position Number', 'Position Name', 'Employee Name', 'Org Unit Name', 'Location']].head(10))
    
    # Print schema info to match original
    print(f"\nSchema Info:")
    print(df.info())

if __name__ == "__main__":
    main() 