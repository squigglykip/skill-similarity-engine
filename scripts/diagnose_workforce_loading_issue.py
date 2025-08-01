#!/usr/bin/env python3
"""
Workforce Loading Issue Diagnostic Script
=========================================

This script diagnoses the UNIQUE constraint failed issue when loading workforce_context.csv.
It performs comprehensive analysis of:
1. CSV data integrity
2. Existing database state
3. Data loading configuration
4. Potential conflicts

Run this script on your production environment to identify the exact cause.

Usage:
    python scripts/diagnose_workforce_loading_issue.py

Output:
    - Detailed diagnostic report
    - Specific recommendations to fix the issue
    - JSON file with complete analysis
"""

import pandas as pd
import sqlite3
import sys
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import warnings

warnings.filterwarnings('ignore')

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
CONFIG_DIR = PROJECT_ROOT / 'config' / 'data'

class WorkforceLoadingDiagnostic:
    """Comprehensive diagnostic for workforce loading UNIQUE constraint issue."""
    
    def __init__(self):
        """Initialize the diagnostic tool."""
        self.project_root = PROJECT_ROOT
        self.data_dir = DATA_DIR
        self.config_dir = CONFIG_DIR
        
        # Database paths to check
        self.db_paths = [
            PROJECT_ROOT / 'models' / '2025-Q3' / 'business_context.sqlite',
            PROJECT_ROOT / 'business_context.sqlite',
            PROJECT_ROOT / 'data' / 'business_context.sqlite'
        ]
        
        # Results storage
        self.results = {}
        
    def run_diagnostic(self) -> Dict[str, Any]:
        """Run complete diagnostic analysis."""
        print("🔍 WORKFORCE LOADING DIAGNOSTIC")
        print("=" * 60)
        print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Target: Diagnose UNIQUE constraint failed: core_workforce_current.employee_number")
        print("=" * 60)
        print()
        
        # Step 1: Analyze CSV data
        print("📊 STEP 1: Analyzing CSV Data Integrity")
        print("-" * 50)
        csv_analysis = self._analyze_csv_data()
        self.results['csv_analysis'] = csv_analysis
        self._print_csv_results(csv_analysis)
        print()
        
        # Step 2: Check database state
        print("🗄️ STEP 2: Analyzing Database State")
        print("-" * 50)
        db_analysis = self._analyze_database_state()
        self.results['database_analysis'] = db_analysis
        self._print_database_results(db_analysis)
        print()
        
        # Step 3: Check configuration
        print("⚙️ STEP 3: Analyzing Configuration")
        print("-" * 50)
        config_analysis = self._analyze_configuration()
        self.results['config_analysis'] = config_analysis
        self._print_config_results(config_analysis)
        print()
        
        # Step 4: Test data loading behavior
        print("🧪 STEP 4: Testing Data Loading Behavior")
        print("-" * 50)
        loading_analysis = self._test_loading_behavior()
        self.results['loading_analysis'] = loading_analysis
        self._print_loading_results(loading_analysis)
        print()
        
        # Step 5: Generate recommendations
        print("💡 STEP 5: Generating Recommendations")
        print("-" * 50)
        recommendations = self._generate_recommendations()
        self.results['recommendations'] = recommendations
        self._print_recommendations(recommendations)
        print()
        
        return self.results
    
    def _analyze_csv_data(self) -> Dict[str, Any]:
        """Analyze workforce_context.csv for data integrity issues."""
        workforce_csv = self.data_dir / 'workforce_context' / 'workforce_context.csv'
        
        if not workforce_csv.exists():
            return {'error': f'Workforce CSV not found: {workforce_csv}'}
        
        try:
            # Load CSV data
            df = pd.read_csv(workforce_csv, encoding='utf-8', low_memory=False)
            
            # Check for duplicate employee numbers
            employee_col = 'Employee Number'
            if employee_col not in df.columns:
                return {'error': f'Employee Number column not found in CSV'}
            
            # Analyze duplicates
            duplicates = df[df[employee_col].duplicated(keep=False)]
            duplicate_employees = df[employee_col].value_counts()
            duplicate_employees = duplicate_employees[duplicate_employees > 1]
            
            # Check for null/empty employee numbers
            null_employees = df[employee_col].isnull().sum()
            empty_employees = (df[employee_col] == '').sum() if df[employee_col].dtype == 'object' else 0
            
            # Data type analysis
            employee_dtype = str(df[employee_col].dtype)
            
            # Sample data for validation
            sample_employees = df[employee_col].head(10).tolist()
            
            return {
                'file_path': str(workforce_csv),
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'employee_column_exists': True,
                'employee_dtype': employee_dtype,
                'unique_employees': df[employee_col].nunique(),
                'total_employees': len(df),
                'has_duplicates': len(duplicates) > 0,
                'duplicate_count': len(duplicates),
                'duplicate_employees': duplicate_employees.to_dict() if len(duplicate_employees) > 0 else {},
                'null_employees': int(null_employees),
                'empty_employees': int(empty_employees),
                'sample_employees': sample_employees,
                'data_integrity_score': self._calculate_data_integrity_score(df, employee_col)
            }
            
        except Exception as e:
            return {'error': f'Failed to analyze CSV: {e}'}
    
    def _analyze_database_state(self) -> Dict[str, Any]:
        """Analyze current database state."""
        results = {
            'databases_found': [],
            'active_database': None,
            'table_exists': False,
            'existing_data': {},
            'schema_info': {}
        }
        
        # Check all possible database locations
        for db_path in self.db_paths:
            if db_path.exists():
                results['databases_found'].append({
                    'path': str(db_path),
                    'size_mb': round(db_path.stat().st_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(db_path.stat().st_mtime).isoformat()
                })
                
                # Use the first found database as active
                if results['active_database'] is None:
                    results['active_database'] = str(db_path)
                    
                    try:
                        with sqlite3.connect(db_path) as conn:
                            # Check if table exists
                            cursor = conn.execute(
                                "SELECT name FROM sqlite_master WHERE type='table' AND name='core_workforce_current'"
                            )
                            table_exists = cursor.fetchone() is not None
                            results['table_exists'] = table_exists
                            
                            if table_exists:
                                # Get table info
                                cursor = conn.execute("PRAGMA table_info(core_workforce_current)")
                                columns = cursor.fetchall()
                                results['schema_info'] = {
                                    'column_count': len(columns),
                                    'columns': [
                                        {
                                            'name': col[1],
                                            'type': col[2],
                                            'not_null': bool(col[3]),
                                            'primary_key': bool(col[5])
                                        }
                                        for col in columns
                                    ],
                                    'primary_key': [col[1] for col in columns if col[5]]
                                }
                                
                                # Check existing data
                                cursor = conn.execute("SELECT COUNT(*) FROM core_workforce_current")
                                row_count = cursor.fetchone()[0]
                                
                                results['existing_data']['row_count'] = row_count
                                
                                if row_count > 0:
                                    # Sample existing data
                                    cursor = conn.execute(
                                        "SELECT employee_number FROM core_workforce_current LIMIT 10"
                                    )
                                    sample_data = [row[0] for row in cursor.fetchall()]
                                    results['existing_data']['sample_employees'] = sample_data
                                    
                                    # Check for duplicates in existing data
                                    cursor = conn.execute("""
                                        SELECT employee_number, COUNT(*) as count 
                                        FROM core_workforce_current 
                                        GROUP BY employee_number 
                                        HAVING COUNT(*) > 1
                                    """)
                                    existing_duplicates = cursor.fetchall()
                                    results['existing_data']['has_duplicates'] = len(existing_duplicates) > 0
                                    results['existing_data']['duplicate_employees'] = {
                                        str(emp): count for emp, count in existing_duplicates
                                    }
                                    
                                    # Check employee number range
                                    cursor = conn.execute(
                                        "SELECT MIN(employee_number), MAX(employee_number) FROM core_workforce_current"
                                    )
                                    min_emp, max_emp = cursor.fetchone()
                                    results['existing_data']['employee_range'] = {
                                        'min': str(min_emp) if min_emp else None,
                                        'max': str(max_emp) if max_emp else None
                                    }
                                else:
                                    results['existing_data']['sample_employees'] = []
                                    results['existing_data']['has_duplicates'] = False
                                    results['existing_data']['duplicate_employees'] = {}
                                    
                    except Exception as e:
                        results['database_error'] = str(e)
        
        return results
    
    def _analyze_configuration(self) -> Dict[str, Any]:
        """Analyze data loading configuration."""
        config_file = self.config_dir / 'sources.yaml'
        
        if not config_file.exists():
            return {'error': f'Configuration file not found: {config_file}'}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            workforce_config = config.get('data_sources', {}).get('core_workforce_current', {})
            
            if not workforce_config:
                return {'error': 'core_workforce_current configuration not found'}
            
            # Analyze loading strategy
            loading_strategy = workforce_config.get('loading_strategy', {})
            if_exists_mode = loading_strategy.get('if_exists', 'append')
            
            return {
                'file_path': str(config_file),
                'config_exists': True,
                'table_name': workforce_config.get('table_name'),
                'if_exists_mode': if_exists_mode,
                'column_mappings': workforce_config.get('column_mapping', {}),
                'enrichment_config': workforce_config.get('enrichment', {}),
                'has_enrichment': 'enrichment' in workforce_config,
                'loading_strategy': loading_strategy,
                'potential_issue': if_exists_mode == 'append' and 'existing data detected'
            }
            
        except Exception as e:
            return {'error': f'Failed to analyze configuration: {e}'}
    
    def _test_loading_behavior(self) -> Dict[str, Any]:
        """Test the data loading behavior with sample data."""
        try:
            # Load sample CSV data
            workforce_csv = self.data_dir / 'workforce_context' / 'workforce_context.csv'
            if not workforce_csv.exists():
                return {'error': 'CSV file not found for testing'}
            
            df = pd.read_csv(workforce_csv, encoding='utf-8', low_memory=False, nrows=100)
            
            # Test in-memory database insertion
            test_results = {}
            
            # Test with empty database (should work)
            try:
                with sqlite3.connect(':memory:') as conn:
                    # Create table schema
                    sys.path.append(str(PROJECT_ROOT / 'src'))
                    from skill_similarity_engine.business_context.schema_builder import SchemaBuilder
                    
                    schema_builder = SchemaBuilder(':memory:')
                    schema_builder._create_core_workforce_current_table(conn)
                    
                    # Prepare test data (first 10 rows)
                    test_data = df.head(10).copy()
                    test_data = test_data.rename(columns={'Employee Number': 'employee_number'})
                    test_data['JobProfileID'] = 'TEST_PROFILE'
                    
                    # Test insertion
                    test_data.to_sql('core_workforce_current', conn, if_exists='append', index=False)
                    
                    cursor = conn.execute("SELECT COUNT(*) FROM core_workforce_current")
                    inserted_count = cursor.fetchone()[0]
                    
                    test_results['empty_db_test'] = {
                        'success': True,
                        'inserted_rows': inserted_count,
                        'expected_rows': 10
                    }
                    
            except Exception as e:
                test_results['empty_db_test'] = {
                    'success': False,
                    'error': str(e)
                }
            
            # Test with duplicate data (should fail)
            try:
                with sqlite3.connect(':memory:') as conn:
                    schema_builder = SchemaBuilder(':memory:')
                    schema_builder._create_core_workforce_current_table(conn)
                    
                    # Insert same data twice
                    test_data = df.head(5).copy()
                    test_data = test_data.rename(columns={'Employee Number': 'employee_number'})
                    test_data['JobProfileID'] = 'TEST_PROFILE'
                    
                    # First insertion
                    test_data.to_sql('core_workforce_current', conn, if_exists='append', index=False)
                    
                    # Second insertion (should cause UNIQUE constraint error)
                    test_data.to_sql('core_workforce_current', conn, if_exists='append', index=False)
                    
                    test_results['duplicate_test'] = {
                        'success': True,  # This shouldn't succeed
                        'unexpected': 'Duplicate insertion should have failed'
                    }
                    
            except Exception as e:
                test_results['duplicate_test'] = {
                    'success': False,
                    'error': str(e),
                    'expected': 'UNIQUE constraint' in str(e)
                }
            
            return test_results
            
        except Exception as e:
            return {'error': f'Loading behavior test failed: {e}'}
    
    def _generate_recommendations(self) -> Dict[str, Any]:
        """Generate specific recommendations based on analysis."""
        recommendations = []
        root_cause = "Unknown"
        severity = "Medium"
        
        # Analyze results to determine root cause
        csv_analysis = self.results.get('csv_analysis', {})
        db_analysis = self.results.get('database_analysis', {})
        config_analysis = self.results.get('config_analysis', {})
        
        # Check for CSV duplicates
        if csv_analysis.get('has_duplicates', False):
            root_cause = "CSV contains duplicate employee numbers"
            severity = "High"
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'Duplicate employee numbers in source CSV',
                'recommendation': 'Clean the workforce_context.csv file to remove duplicate employee records',
                'action': 'Review and deduplicate CSV data before loading'
            })
        
        # Check for existing database data with append mode
        elif (db_analysis.get('existing_data', {}).get('row_count', 0) > 0 and 
              config_analysis.get('if_exists_mode') == 'append'):
            root_cause = "Attempting to append data to existing populated table"
            severity = "High"
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'Database table already contains data, but using append mode',
                'recommendation': 'Change loading strategy to "replace" mode or clear existing data first',
                'action': 'Update sources.yaml loading_strategy.if_exists to "replace" OR clear the database table'
            })
        
        # Check for existing duplicates in database
        elif db_analysis.get('existing_data', {}).get('has_duplicates', False):
            root_cause = "Database already contains duplicate employee numbers"
            severity = "Critical"
            recommendations.append({
                'priority': 'CRITICAL',
                'issue': 'Database table already contains duplicate employee records',
                'recommendation': 'Clean the database table by removing duplicates',
                'action': 'Run SQL to deduplicate existing data or recreate the table'
            })
        
        # Check for configuration issues
        elif not config_analysis.get('config_exists', False):
            root_cause = "Configuration file missing or invalid"
            severity = "Critical"
            recommendations.append({
                'priority': 'CRITICAL',
                'issue': 'Data loading configuration not found',
                'recommendation': 'Ensure config/data/sources.yaml exists and is properly configured',
                'action': 'Check configuration file path and content'
            })
        
        # Check for data type mismatches
        elif (csv_analysis.get('employee_dtype') and 
              'int' in csv_analysis.get('employee_dtype', '') and
              db_analysis.get('schema_info', {}).get('columns')):
            # Check if database schema expects TEXT but CSV has int
            db_employee_col = next((col for col in db_analysis['schema_info']['columns'] 
                                  if col['name'] == 'employee_number'), None)
            if db_employee_col and db_employee_col['type'] == 'TEXT':
                recommendations.append({
                    'priority': 'MEDIUM',
                    'issue': 'Data type mismatch between CSV (int) and database (TEXT)',
                    'recommendation': 'Ensure data type consistency in data loading process',
                    'action': 'Convert employee numbers to string format during loading'
                })
        
        # Default recommendation if no specific issue found
        if not recommendations:
            recommendations.append({
                'priority': 'MEDIUM',
                'issue': 'UNIQUE constraint error without obvious cause',
                'recommendation': 'Clear existing data and reload with replace mode',
                'action': 'Drop and recreate the core_workforce_current table, then reload data'
            })
        
        # Add general recommendations
        recommendations.extend([
            {
                'priority': 'LOW',
                'issue': 'Data loading resilience',
                'recommendation': 'Consider using "replace" mode for initial data loads',
                'action': 'Update sources.yaml: loading_strategy.if_exists = "replace"'
            },
            {
                'priority': 'LOW',
                'issue': 'Data validation',
                'recommendation': 'Add data validation checks before database insertion',
                'action': 'Implement pre-insertion data quality checks'
            }
        ])
        
        return {
            'root_cause': root_cause,
            'severity': severity,
            'total_recommendations': len(recommendations),
            'recommendations': recommendations,
            'next_steps': self._get_next_steps(root_cause)
        }
    
    def _get_next_steps(self, root_cause: str) -> List[str]:
        """Get specific next steps based on root cause."""
        if "duplicate employee numbers in source CSV" in root_cause.lower():
            return [
                "1. Back up the original workforce_context.csv file",
                "2. Remove duplicate employee records from the CSV",
                "3. Verify data integrity before reloading",
                "4. Retry the data loading process"
            ]
        elif "append data to existing populated table" in root_cause.lower():
            return [
                "1. Update config/data/sources.yaml",
                "2. Change loading_strategy.if_exists from 'append' to 'replace'",
                "3. OR clear the existing database table first",
                "4. Retry the data loading process"
            ]
        elif "database already contains duplicate" in root_cause.lower():
            return [
                "1. Connect to the database",
                "2. Run: DELETE FROM core_workforce_current",
                "3. OR DROP TABLE core_workforce_current and recreate",
                "4. Retry the data loading process"
            ]
        else:
            return [
                "1. Review the diagnostic report above",
                "2. Address the highest priority recommendations first",
                "3. Test with a small sample of data",
                "4. Retry the full data loading process"
            ]
    
    def _calculate_data_integrity_score(self, df: pd.DataFrame, employee_col: str) -> float:
        """Calculate a data integrity score (0-100)."""
        score = 100.0
        
        # Penalize for duplicates
        if df[employee_col].duplicated().any():
            duplicate_rate = df[employee_col].duplicated().sum() / len(df)
            score -= (duplicate_rate * 50)  # Up to 50 points off for duplicates
        
        # Penalize for nulls
        null_rate = df[employee_col].isnull().sum() / len(df)
        score -= (null_rate * 30)  # Up to 30 points off for nulls
        
        # Penalize for empty strings
        if df[employee_col].dtype == 'object':
            empty_rate = (df[employee_col] == '').sum() / len(df)
            score -= (empty_rate * 20)  # Up to 20 points off for empty strings
        
        return max(0.0, score)
    
    def _print_csv_results(self, analysis: Dict[str, Any]) -> None:
        """Print CSV analysis results."""
        if 'error' in analysis:
            print(f"❌ {analysis['error']}")
            return
        
        print(f"📊 Total Records: {analysis['total_rows']:,}")
        print(f"👥 Unique Employees: {analysis['unique_employees']:,}")
        
        if analysis['has_duplicates']:
            print(f"⚠️ DUPLICATE EMPLOYEES FOUND: {analysis['duplicate_count']} duplicates")
            print(f"   Duplicate employee numbers: {list(analysis['duplicate_employees'].keys())[:5]}...")
        else:
            print("✅ No duplicate employee numbers found")
        
        if analysis['null_employees'] > 0:
            print(f"⚠️ NULL employee numbers: {analysis['null_employees']}")
        
        if analysis['empty_employees'] > 0:
            print(f"⚠️ Empty employee numbers: {analysis['empty_employees']}")
        
        print(f"📈 Data Integrity Score: {analysis['data_integrity_score']:.1f}/100")
    
    def _print_database_results(self, analysis: Dict[str, Any]) -> None:
        """Print database analysis results."""
        if not analysis['databases_found']:
            print("❌ No database files found")
            return
        
        print(f"💾 Databases Found: {len(analysis['databases_found'])}")
        for db in analysis['databases_found']:
            print(f"   📁 {db['path']} ({db['size_mb']} MB)")
        
        if analysis['active_database']:
            print(f"🎯 Active Database: {analysis['active_database']}")
            
            if analysis['table_exists']:
                print("✅ core_workforce_current table exists")
                
                row_count = analysis['existing_data'].get('row_count', 0)
                print(f"📊 Existing Records: {row_count:,}")
                
                if row_count > 0:
                    if analysis['existing_data'].get('has_duplicates', False):
                        print("⚠️ EXISTING DUPLICATES FOUND in database")
                        dups = analysis['existing_data']['duplicate_employees']
                        print(f"   Duplicate employees: {list(dups.keys())[:3]}...")
                    else:
                        print("✅ No duplicates in existing database data")
                        
                    emp_range = analysis['existing_data'].get('employee_range', {})
                    if emp_range.get('min') and emp_range.get('max'):
                        print(f"📈 Employee Number Range: {emp_range['min']} - {emp_range['max']}")
            else:
                print("❌ core_workforce_current table does not exist")
        
        if 'database_error' in analysis:
            print(f"⚠️ Database Error: {analysis['database_error']}")
    
    def _print_config_results(self, analysis: Dict[str, Any]) -> None:
        """Print configuration analysis results."""
        if 'error' in analysis:
            print(f"❌ {analysis['error']}")
            return
        
        print(f"⚙️ Configuration File: Found")
        print(f"📋 Loading Mode: {analysis['if_exists_mode']}")
        
        if analysis['if_exists_mode'] == 'append':
            print("⚠️ APPEND MODE: Will add to existing data (potential duplicate risk)")
        else:
            print("✅ REPLACE MODE: Will replace existing data")
        
        print(f"🔗 Column Mappings: {len(analysis['column_mappings'])}")
        print(f"⚡ Has Enrichment: {analysis['has_enrichment']}")
    
    def _print_loading_results(self, analysis: Dict[str, Any]) -> None:
        """Print loading behavior test results."""
        if 'error' in analysis:
            print(f"❌ {analysis['error']}")
            return
        
        # Empty database test
        empty_test = analysis.get('empty_db_test', {})
        if empty_test.get('success'):
            print(f"✅ Empty Database Test: PASSED ({empty_test['inserted_rows']} rows)")
        else:
            print(f"❌ Empty Database Test: FAILED - {empty_test.get('error')}")
        
        # Duplicate test
        dup_test = analysis.get('duplicate_test', {})
        if not dup_test.get('success') and dup_test.get('expected'):
            print("✅ Duplicate Detection Test: PASSED (correctly rejected duplicates)")
        else:
            print(f"⚠️ Duplicate Detection Test: {dup_test}")
    
    def _print_recommendations(self, recommendations: Dict[str, Any]) -> None:
        """Print recommendations."""
        print(f"🎯 ROOT CAUSE: {recommendations['root_cause']}")
        print(f"⚠️ SEVERITY: {recommendations['severity']}")
        print()
        
        print("📋 RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations['recommendations'], 1):
            priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢", "CRITICAL": "🚨"}.get(rec['priority'], "📌")
            print(f"{i}. {priority_emoji} {rec['priority']}: {rec['issue']}")
            print(f"   💡 {rec['recommendation']}")
            print(f"   🔧 {rec['action']}")
            print()
        
        print("🚀 NEXT STEPS:")
        for step in recommendations['next_steps']:
            print(f"   {step}")

def main():
    """Main execution function."""
    diagnostic = WorkforceLoadingDiagnostic()
    
    try:
        # Run complete diagnostic
        results = diagnostic.run_diagnostic()
        
        # Save detailed results
        output_file = PROJECT_ROOT / 'workforce_loading_diagnostic.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        print()
        print("=" * 60)
        print(f"📄 Detailed diagnostic saved to: {output_file}")
        print("🎯 Run this report and share the results to get targeted fix recommendations!")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())