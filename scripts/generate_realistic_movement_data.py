#!/usr/bin/env python3
"""
Generate Realistic Source CSV Data for Movement Analysis

This script creates 5 years of realistic colleague position history and position 
history CSV files that match the existing schema and file structure exactly.
Uses 50xxx position numbers from the database to ensure compatibility.

Purpose: Generate source data files for the precompute engine:
- colleague_position_history/ (5 CSV files, one per FY)
- positions_history/ (5 CSV files, one per FY)

The precompute engine (main.py → movement analysis) will then process these
CSV files to generate movement analysis data.

File Structure Generated:
├── data/colleague_position_history/
│   ├── d_colleague_position_fy2021.csv
│   ├── d_colleague_position_fy2022.csv
│   ├── d_colleague_position_fy2023.csv
│   ├── d_colleague_position_fy2024.csv
│   └── d_colleague_position_fy2025.csv
└── data/positions_history/
    ├── d_positions_fy2021.csv
    ├── d_positions_fy2022.csv
    ├── d_positions_fy2023.csv
    ├── d_positions_fy2024.csv
    └── d_positions_fy2025.csv
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import sqlite3
from calendar import monthrange

# Set random seed for reproducible data
random.seed(42)
np.random.seed(42)

# Configuration
DATABASE_FILE = Path(__file__).parent.parent / "models" / "2025-Q3" / "workforce_intelligence.sqlite"
OUTPUT_DIR_COLLEAGUES = Path(__file__).parent.parent / "data" / "colleague_position_history"
OUTPUT_DIR_POSITIONS = Path(__file__).parent.parent / "data" / "positions_history"

# Financial years to generate (5 years)
FINANCIAL_YEARS = [2021, 2022, 2023, 2024, 2025]

# Data generation parameters
COLLEAGUES_PER_YEAR = 500000  # Real world volume: many colleagues per position
POSITIONS_PER_YEAR = 120000   # Real world volume: fewer unique positions
WEEKS_PER_YEAR = 52

# Employee lifecycle parameters
NEW_HIRES_PER_MONTH = 200    # New employees joining
DEPARTURES_PER_MONTH = 150   # Employees leaving
MOVEMENT_PROBABILITY = 0.02  # 2% chance per month of changing positions
OPERATIONAL_RATE = 0.85      # 85% of positions are operational

class DatabasePositionLoader:
    """Loads position data from the SQLite database."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.positions_data = None
        self.job_profiles_data = None
        
    def load_positions_data(self) -> pd.DataFrame:
        """Load positions and job profile data from database."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
        
        conn = sqlite3.connect(self.db_path)
        
        # Load positions data
        positions_query = '''
        SELECT "Position Number", JobProfileID
        FROM positions 
        WHERE "Position Number" IS NOT NULL
        '''
        self.positions_data = pd.read_sql_query(positions_query, conn)
        print(f"Loaded {len(self.positions_data):,} positions from database")
        
        # Load job profiles data for organizational context
        jobs_query = '''
        SELECT JobProfileID, JobProfile, JobFunction, JobCategory, 
               ManagementLevel, is_Banker, Customer_Facing
        FROM jobs
        WHERE JobProfileID IS NOT NULL
        '''
        self.job_profiles_data = pd.read_sql_query(jobs_query, conn)
        print(f"Loaded {len(self.job_profiles_data):,} job profiles from database")
        
        conn.close()
        
        # Merge positions with job profile data
        merged_data = self.positions_data.merge(
            self.job_profiles_data, 
            on='JobProfileID', 
            how='left'
        )
        
        return merged_data
    
    def get_position_numbers(self) -> List[str]:
        """Get list of all position numbers as strings."""
        if self.positions_data is None:
            self.load_positions_data()
        return [str(pos) for pos in self.positions_data['Position Number'].tolist()]

class FinancialYearGenerator:
    """Generates weekly date sequences for financial years."""
    
    @staticmethod
    def get_fy_dates(fy_year: int) -> List[date]:
        """Generate weekly dates for a financial year (July to June)."""
        start_date = date(fy_year - 1, 7, 1)  # FY2025 starts July 1, 2024
        end_date = date(fy_year, 6, 30)       # FY2025 ends June 30, 2025
        
        dates = []
        current_date = start_date
        
        # Generate weekly dates (Mondays)
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=7)
        
        return dates

class ColleaguePositionsGenerator:
    """Generates colleague position history CSV files."""
    
    def __init__(self, db_loader: DatabasePositionLoader):
        self.db_loader = db_loader
        self.employee_pool = set()
        self.employee_counter = 30000000  # Start employee numbers at 30M
        
    def generate_employee_number(self) -> int:
        """Generate a unique employee number."""
        self.employee_counter += random.randint(1, 1000)
        return self.employee_counter
    
    def generate_colleague_position_for_year(self, fy_year: int, position_numbers: List[str]) -> pd.DataFrame:
        """Generate colleague positions data for one financial year."""
        print(f"Generating colleague positions for FY{fy_year}...")
        
        dates = FinancialYearGenerator.get_fy_dates(fy_year)
        all_records = []
        
        # Initialize employee pool for this year
        active_employees = {}
        
        # Generate initial employee cohort
        for _ in range(int(COLLEAGUES_PER_YEAR * 0.1)):  # 10% of total volume as base cohort
            emp_num = self.generate_employee_number()
            position = random.choice(position_numbers)
            
            # Generate position start date (some before FY, some during)
            if random.random() < 0.7:  # 70% started before this FY
                start_date = dates[0] - timedelta(days=random.randint(30, 730))
            else:  # 30% started during this FY
                start_date = random.choice(dates[:26])  # First half of year
            
            active_employees[emp_num] = {
                'position': position,
                'start_date': start_date,
                'operational': random.random() < OPERATIONAL_RATE
            }
        
        # Generate weekly snapshots
        for week_num, week_date in enumerate(dates):
            # Employee lifecycle: new hires
            if week_num % 4 == 0:  # Monthly new hires
                new_hires = random.randint(int(NEW_HIRES_PER_MONTH * 0.7), int(NEW_HIRES_PER_MONTH * 1.3))
                for _ in range(new_hires):
                    emp_num = self.generate_employee_number()
                    active_employees[emp_num] = {
                        'position': random.choice(position_numbers),
                        'start_date': week_date,
                        'operational': random.random() < OPERATIONAL_RATE
                    }
            
            # Employee lifecycle: departures
            if week_num % 4 == 0 and len(active_employees) > COLLEAGUES_PER_YEAR * 0.5:
                departures = random.randint(int(DEPARTURES_PER_MONTH * 0.7), int(DEPARTURES_PER_MONTH * 1.3))
                departing_employees = random.sample(list(active_employees.keys()), 
                                                  min(departures, len(active_employees)))
                for emp_num in departing_employees:
                    del active_employees[emp_num]
            
            # Employee movements
            for emp_num, emp_data in active_employees.items():
                if random.random() < MOVEMENT_PROBABILITY:
                    # Employee changes position
                    emp_data['position'] = random.choice(position_numbers)
                    emp_data['start_date'] = week_date
            
            # Generate records for this week
            for emp_num, emp_data in active_employees.items():
                # Generate PosIDLookupKey (scientific notation format)
                pos_id_lookup = random.uniform(1e11, 3e11)
                
                record = {
                    'Week Ending': week_date.strftime('%d/%m/%Y'),
                    'Employee Number': emp_num,
                    'Operational': emp_data['operational'],
                    'Position Start Date': emp_data['start_date'].strftime('%d/%m/%Y'),
                    'PosIDLookupKey': pos_id_lookup,
                    'Position Number': int(emp_data['position'])  # Convert to int for consistency
                }
                all_records.append(record)
        
        df = pd.DataFrame(all_records)
        
        # Sample down to target size if too large
        if len(df) > COLLEAGUES_PER_YEAR:
            df = df.sample(n=COLLEAGUES_PER_YEAR, random_state=42)
        
        # Sort by employee number and week ending
        df = df.sort_values(['Employee Number', 'Week Ending'])
        
        print(f"Generated {len(df):,} colleague position records for FY{fy_year}")
        return df

class PositionsHistoryGenerator:
    """Generates position history CSV files."""
    
    def __init__(self, db_loader: DatabasePositionLoader):
        self.db_loader = db_loader
        self.org_units = [
            'Customer Banking', 'Business Banking', 'Institutional Banking',
            'Risk Management', 'Technology', 'Operations', 'Human Resources',
            'Finance', 'Legal & Compliance', 'Marketing', 'Corporate Affairs'
        ]
        self.cost_centres = list(range(1000, 9999, 100))
        
    def generate_positions_history_for_year(self, fy_year: int, merged_data: pd.DataFrame) -> pd.DataFrame:
        """Generate positions history data for one financial year."""
        print(f"Generating positions history for FY{fy_year}...")
        
        dates = FinancialYearGenerator.get_fy_dates(fy_year)
        all_records = []
        
        # Use all positions from database
        for _, position_row in merged_data.iterrows():
            position_number = str(position_row['Position Number'])
            job_profile = position_row.get('JobProfile', 'Unknown Role')
            
            # Generate organizational context
            org_unit = random.choice(self.org_units)
            cost_centre = random.choice(self.cost_centres)
            
            # Generate people leader (optional)
            people_leader = None
            if random.random() < 0.7:  # 70% have people leaders
                people_leader = random.randint(20000000, 29999999)
            
            operational = random.random() < OPERATIONAL_RATE
            
            # Generate records for multiple weeks (not every week to match volume)
            weeks_to_include = random.sample(dates, random.randint(20, 40))
            
            for week_date in weeks_to_include:
                # Generate PosIDLookupKey (scientific notation format)
                pos_id_lookup = random.uniform(1e11, 3e11)
                org_unit_lookup = random.randint(1000000, 9999999)
                
                record = {
                    'Week Ending': week_date.strftime('%d/%m/%Y'),
                    'Position Number': int(position_number),
                    'PosIDLookupKey': pos_id_lookup,
                    'Organisational Unit': org_unit,
                    'Cost Centre Number': cost_centre,
                    'Position Title': job_profile,
                    'People Leader': people_leader,
                    'Operational': operational,
                    'OrgUnitIDLookupKey': org_unit_lookup
                }
                all_records.append(record)
        
        df = pd.DataFrame(all_records)
        
        # Sample down to target size if too large
        if len(df) > POSITIONS_PER_YEAR:
            df = df.sample(n=POSITIONS_PER_YEAR, random_state=42)
        
        # Sort by position number and week ending
        df = df.sort_values(['Position Number', 'Week Ending'])
        
        print(f"Generated {len(df):,} position history records for FY{fy_year}")
        return df

def main():
    """Generate all source CSV files for movement analysis."""
    
    print("=" * 80)
    print("Generating Source CSV Files for Movement Analysis")
    print("Using 50xxx Position Numbers from Database")
    print("=" * 80)
    
    # Initialize database loader
    db_loader = DatabasePositionLoader(DATABASE_FILE)
    merged_data = db_loader.load_positions_data()
    position_numbers = db_loader.get_position_numbers()
    
    print(f"\nLoaded {len(position_numbers):,} position numbers from database")
    print(f"Position number range: {min(position_numbers)} to {max(position_numbers)}")
    print(f"Sample positions: {position_numbers[:5]}")
    
    # Initialize generators
    colleague_gen = ColleaguePositionsGenerator(db_loader)
    positions_gen = PositionsHistoryGenerator(db_loader)
    
    # Create output directories
    OUTPUT_DIR_COLLEAGUES.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR_POSITIONS.mkdir(parents=True, exist_ok=True)
    
    # Generate files for each financial year
    for fy_year in FINANCIAL_YEARS:
        print(f"\n{'='*60}")
        print(f"Processing Financial Year {fy_year}")
        print(f"{'='*60}")
        
        # Generate colleague positions
        colleague_df = colleague_gen.generate_colleague_position_for_year(fy_year, position_numbers)
        colleague_file = OUTPUT_DIR_COLLEAGUES / f"d_colleague_position_fy{fy_year}.csv"
        colleague_df.to_csv(colleague_file, index=False)
        print(f"✅ Saved: {colleague_file}")
        
        # Generate positions history
        positions_df = positions_gen.generate_positions_history_for_year(fy_year, merged_data)
        positions_file = OUTPUT_DIR_POSITIONS / f"d_positions_fy{fy_year}.csv"
        positions_df.to_csv(positions_file, index=False)
        print(f"✅ Saved: {positions_file}")
    
    print(f"\n{'='*80}")
    print("✅ ALL SOURCE CSV FILES GENERATED SUCCESSFULLY!")
    print(f"{'='*80}")
    
    print(f"\n📁 Generated Files:")
    print(f"📂 Colleague Positions History:")
    for fy_year in FINANCIAL_YEARS:
        file_path = OUTPUT_DIR_COLLEAGUES / f"d_colleague_position_fy{fy_year}.csv"
        size_kb = file_path.stat().st_size / 1024
        print(f"   📄 d_colleague_position_fy{fy_year}.csv ({size_kb:.1f} KB)")
    
    print(f"\n📂 Positions History:")
    for fy_year in FINANCIAL_YEARS:
        file_path = OUTPUT_DIR_POSITIONS / f"d_positions_fy{fy_year}.csv"
        size_kb = file_path.stat().st_size / 1024
        print(f"   📄 d_positions_fy{fy_year}.csv ({size_kb:.1f} KB)")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Run main.py → Option 1 → Option 3 (Movement Analysis)")
    print(f"   2. This will process these CSV files using the precompute engine")
    print(f"   3. Generated movement analysis will be saved to models/YYYY-QX/YYYY-MM-DD/")
    print(f"   4. Run main.py → Option 2 (Workforce Intelligence) to load into database")
    
    print(f"\n✨ Ready for movement analysis precompute workflow!")

if __name__ == "__main__":
    main() 