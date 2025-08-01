#!/usr/bin/env python3
"""
UNIQUE Constraint Issue Diagnostic Tool
=======================================

Focused analysis to diagnose the specific UNIQUE constraint failure
on core_workforce_current.employee_number that occurs during data loading.

This script specifically checks:
1. CSV data for actual duplicates
2. Database state before/after loading attempts
3. Data loading configuration issues
4. Transaction and if_exists parameter problems

Usage:
    python scripts/diagnose_unique_constraint_issue.py

Output:
    - Specific diagnosis of UNIQUE constraint issue
    - Recommendations for fixing the data loading process
"""

import pandas as pd
import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import warnings

warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
MODELS_DIR = PROJECT_ROOT / 'models'

class UniqueConstraintDiagnoser:
    """Diagnostic tool for UNIQUE constraint failures."""
    
    def __init__(self):
        """Initialize diagnostic tool."""
        self.project_root = PROJECT_ROOT
        self.data_dir = DATA_DIR
        self.models_dir = MODELS_DIR
        
    def run_diagnosis(self) -> Dict[str, Any]:
        """Run complete diagnosis of UNIQUE constraint issue."""
        print("🔍 UNIQUE CONSTRAINT FAILURE DIAGNOSTIC")
        print("=" * 60)
        print(f"Target: core_workforce_current.employee_number")
        print(f"Issue: UNIQUE constraint failed during data loading")
        print("=" * 60)
        print()
        
        diagnosis = {}
        
        # Step 1: Check CSV data for duplicates
        print("📊 STEP 1: Analyzing CSV Data for Duplicates")
        print("-" * 40)
        diagnosis['csv_analysis'] = self._check_csv_duplicates()
        print()
        
        # Step 2: Check database state
        print("🗄️ STEP 2: Checking Database State")
        print("-" * 40)
        diagnosis['database_state'] = self._check_database_state()
        print()
        
        # Step 3: Analyze data loading configuration
        print("⚙️ STEP 3: Analyzing Data Loading Configuration")
        print("-" * 40)
        diagnosis['loading_config'] = self._analyze_loading_configuration()
        print()
        
        # Step 4: Generate specific diagnosis
        print("🎯 STEP 4: Generating Diagnosis & Recommendations")
        print("-" * 40)
        diagnosis['final_diagnosis'] = self._generate_diagnosis(diagnosis)
        print()
        
        return diagnosis
    
    def _check_csv_duplicates(self) -> Dict[str, Any]:
        """Check workforce_context.csv for duplicate employee numbers."""
        workforce_csv = self.data_dir / 'workforce_context' / 'workforce_context.csv'
        
        if not workforce_csv.exists():
            print(f"❌ Workforce CSV not found: {workforce_csv}")
            return {'error': 'CSV file not found'}
        
        try:
            print(f"📁 Reading: {workforce_csv}")
            df = pd.read_csv(workforce_csv, encoding='utf-8', low_memory=False)
            
            # Check for duplicates in Employee Number column
            employee_col = 'Employee Number'
            if employee_col not in df.columns:
                print(f"❌ Column '{employee_col}' not found in CSV")
                print(f"Available columns: {list(df.columns)}")
                return {'error': f'Column {employee_col} not found'}
            
            total_rows = len(df)
            unique_employees = df[employee_col].nunique()
            duplicates = df[employee_col].duplicated()
            duplicate_count = duplicates.sum()
            
            print(f"📊 CSV Analysis Results:")
            print(f"   Total rows: {total_rows:,}")
            print(f"   Unique employee numbers: {unique_employees:,}")
            print(f"   Duplicate employee numbers: {duplicate_count:,}")
            
            result = {
                'file_path': str(workforce_csv),
                'total_rows': total_rows,
                'unique_employees': unique_employees,
                'duplicate_count': duplicate_count,
                'has_duplicates': duplicate_count > 0
            }
            
            if duplicate_count > 0:
                print("🚨 DUPLICATES FOUND!")
                duplicate_employees = df[duplicates][employee_col].tolist()
                print(f"   Duplicate employee numbers: {duplicate_employees[:10]}...")  # Show first 10
                result['duplicate_employees'] = duplicate_employees
                
                # Show details for first few duplicates
                for emp_num in duplicate_employees[:3]:
                    emp_rows = df[df[employee_col] == emp_num]
                    print(f"   Employee {emp_num}: {len(emp_rows)} occurrences")
                    result[f'employee_{emp_num}_details'] = emp_rows.to_dict('records')
            else:
                print("✅ No duplicates found in CSV data")
            
            return result
            
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
            return {'error': str(e)}
    
    def _check_database_state(self) -> Dict[str, Any]:
        """Check existing database files for current state."""
        db_files = list(self.models_dir.rglob('*.sqlite'))
        
        if not db_files:
            print("📝 No database files found")
            return {'no_databases': True}
        
        analysis = {}
        
        for db_file in db_files:
            print(f"🗄️ Checking: {db_file.relative_to(self.project_root)}")
            
            try:
                with sqlite3.connect(db_file) as conn:
                    # Check if core_workforce_current table exists
                    cursor = conn.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='core_workforce_current'
                    """)
                    table_exists = cursor.fetchone() is not None
                    
                    if not table_exists:
                        print("   📝 core_workforce_current table does not exist")
                        analysis[str(db_file.relative_to(self.project_root))] = {
                            'table_exists': False
                        }
                        continue
                    
                    # Get table info
                    cursor = conn.execute("SELECT COUNT(*) FROM core_workforce_current")
                    row_count = cursor.fetchone()[0]
                    
                    # Check for duplicate employee numbers in database
                    cursor = conn.execute("""
                        SELECT employee_number, COUNT(*) as count 
                        FROM core_workforce_current 
                        GROUP BY employee_number 
                        HAVING COUNT(*) > 1
                    """)
                    db_duplicates = cursor.fetchall()
                    
                    # Get sample data
                    cursor = conn.execute("SELECT employee_number FROM core_workforce_current LIMIT 5")
                    sample_employees = [row[0] for row in cursor.fetchall()]
                    
                    print(f"   📊 Table exists with {row_count:,} rows")
                    print(f"   📊 Database duplicates: {len(db_duplicates)}")
                    if sample_employees:
                        print(f"   📊 Sample employee numbers: {sample_employees}")
                    
                    analysis[str(db_file.relative_to(self.project_root))] = {
                        'table_exists': True,
                        'row_count': row_count,
                        'db_duplicates': db_duplicates,
                        'sample_employees': sample_employees,
                        'has_data': row_count > 0
                    }
                    
                    if db_duplicates:
                        print("   🚨 DUPLICATES FOUND IN DATABASE!")
                        for emp_num, count in db_duplicates[:5]:
                            print(f"      Employee {emp_num}: {count} occurrences")
                    
            except Exception as e:
                print(f"   ❌ Error reading database: {e}")
                analysis[str(db_file.relative_to(self.project_root))] = {
                    'error': str(e)
                }
        
        return analysis
    
    def _analyze_loading_configuration(self) -> Dict[str, Any]:
        """Analyze data loading configuration for issues."""
        print("🔍 Examining data loading logic...")
        
        try:
            # Check if data loader uses append vs replace
            data_loader_file = self.project_root / 'src' / 'skill_similarity_engine' / 'business_context' / 'data_loader.py'
            
            if not data_loader_file.exists():
                print("❌ DataLoader file not found")
                return {'error': 'DataLoader file not found'}
            
            with open(data_loader_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for to_sql calls and if_exists parameter
            import re
            to_sql_matches = re.findall(r'\.to_sql\([^)]+\)', content)
            
            print("🔍 Found to_sql() calls:")
            analysis = {
                'to_sql_calls': to_sql_matches,
                'uses_append': 'if_exists=\'append\'' in content or 'if_exists="append"' in content,
                'uses_replace': 'if_exists=\'replace\'' in content or 'if_exists="replace"' in content,
                'content_snippet': content[content.find('to_sql'):content.find('to_sql')+200] if 'to_sql' in content else 'Not found'
            }
            
            for match in to_sql_matches[:3]:  # Show first 3
                print(f"   📝 {match}")
            
            if analysis['uses_append']:
                print("🚨 ISSUE IDENTIFIED: Using if_exists='append'")
                print("   This will cause UNIQUE constraint violations if table has existing data")
            
            if analysis['uses_replace']:
                print("✅ Uses if_exists='replace' - this should be safe")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error analyzing configuration: {e}")
            return {'error': str(e)}
    
    def _generate_diagnosis(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final diagnosis and recommendations."""
        print("🎯 FINAL DIAGNOSIS")
        print("=" * 40)
        
        csv_analysis = diagnosis.get('csv_analysis', {})
        db_state = diagnosis.get('database_state', {})
        loading_config = diagnosis.get('loading_config', {})
        
        # Determine root cause
        root_cause = "Unknown"
        recommendations = []
        
        # Check CSV duplicates
        if csv_analysis.get('has_duplicates'):
            root_cause = "CSV contains duplicate employee numbers"
            recommendations.append("Clean CSV data to remove duplicate employee numbers")
            print("🚨 ROOT CAUSE: CSV data has duplicate employee numbers")
        else:
            print("✅ CSV data is clean (no duplicates)")
        
        # Check database state
        has_existing_data = False
        for db_path, db_info in db_state.items():
            if db_info.get('has_data', False):
                has_existing_data = True
                print(f"🚨 ISSUE: Database {db_path} already has data ({db_info.get('row_count', 0)} rows)")
                break
        
        if has_existing_data and not csv_analysis.get('has_duplicates'):
            root_cause = "Database already contains data + using if_exists='append'"
            recommendations.extend([
                "Use if_exists='replace' instead of 'append'",
                "Or clear the database table before loading",
                "Or use proper transaction handling"
            ])
            print("🚨 ROOT CAUSE: Database has existing data + append mode")
        
        # Check loading configuration
        if loading_config.get('uses_append') and has_existing_data:
            print("🚨 CONFIRMED: Data loader uses 'append' mode with existing data")
            if "if_exists='replace'" not in recommendations:
                recommendations.append("Change data loader to use if_exists='replace'")
        
        # If no issues found in data
        if not csv_analysis.get('has_duplicates') and not has_existing_data:
            root_cause = "Possible transaction or connection issue"
            recommendations.extend([
                "Check database connection handling",
                "Verify schema creation completed successfully",
                "Check for concurrent access to database",
                "Review transaction commit/rollback logic"
            ])
            print("🤔 No obvious data issues - likely a transaction problem")
        
        final_diagnosis = {
            'root_cause': root_cause,
            'recommendations': recommendations,
            'csv_clean': not csv_analysis.get('has_duplicates', False),
            'database_has_data': has_existing_data,
            'uses_append_mode': loading_config.get('uses_append', False)
        }
        
        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        return final_diagnosis

def main():
    """Main execution function."""
    diagnoser = UniqueConstraintDiagnoser()
    
    try:
        results = diagnoser.run_diagnosis()
        
        # Save diagnosis results
        import json
        output_file = PROJECT_ROOT / 'unique_constraint_diagnosis.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Diagnosis saved to: {output_file}")
        return 0
        
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())