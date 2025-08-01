#!/usr/bin/env python3
"""
Workforce Schema Compatibility Test
==================================

Tests whether the schema builder will work with the actual workforce_context.csv data.
Performs gap analysis if compatibility issues are found.

This script:
1. Loads the actual workforce_context.csv file
2. Loads the current configuration mappings
3. Creates the database schema using SchemaBuilder
4. Tests data insertion to identify compatibility issues
5. Performs detailed gap analysis if problems are found
6. Provides specific recommendations for fixing issues

Usage:
    python scripts/test_workforce_schema_compatibility.py

Output:
    - Compatibility test results
    - Gap analysis if issues found
    - Specific recommendations for fixes
"""

import pandas as pd
import sqlite3
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import warnings

warnings.filterwarnings('ignore')

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
CONFIG_DIR = PROJECT_ROOT / 'config' / 'data'

class WorkforceSchemaCompatibilityTester:
    """Test compatibility between workforce CSV data and schema builder."""
    
    def __init__(self):
        """Initialize the compatibility tester."""
        self.project_root = PROJECT_ROOT
        self.data_dir = DATA_DIR
        self.config_dir = CONFIG_DIR
        
        # Test database path (in-memory)
        self.test_db_path = ':memory:'
        
        # Results storage
        self.csv_data = None
        self.config_data = None
        self.schema_created = False
        self.compatibility_results = {}
        
    def run_compatibility_test(self) -> Dict[str, Any]:
        """Run complete compatibility test."""
        print("🧪 WORKFORCE SCHEMA COMPATIBILITY TEST")
        print("=" * 60)
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Target: workforce_context.csv → core_workforce_current table")
        print("=" * 60)
        print()
        
        # Step 1: Load and analyze CSV data
        print("📊 STEP 1: Loading workforce_context.csv")
        print("-" * 40)
        csv_analysis = self._load_and_analyze_csv()
        if 'error' in csv_analysis:
            print(f"❌ CSV loading failed: {csv_analysis['error']}")
            return {'error': 'CSV loading failed', 'details': csv_analysis}
        print(f"✅ CSV loaded: {csv_analysis['rows']:,} rows, {csv_analysis['columns']} columns")
        print()
        
        # Step 2: Load configuration
        print("⚙️ STEP 2: Loading configuration mappings")
        print("-" * 40)
        config_analysis = self._load_configuration()
        if 'error' in config_analysis:
            print(f"❌ Configuration loading failed: {config_analysis['error']}")
            return {'error': 'Configuration loading failed', 'details': config_analysis}
        print(f"✅ Configuration loaded: {len(config_analysis['column_mappings'])} column mappings")
        print()
        
        # Step 3: Create test schema
        print("🗄️ STEP 3: Creating test database schema")
        print("-" * 40)
        schema_analysis = self._create_test_schema()
        if 'error' in schema_analysis:
            print(f"❌ Schema creation failed: {schema_analysis['error']}")
            return {'error': 'Schema creation failed', 'details': schema_analysis}
        print("✅ Test schema created successfully")
        print()
        
        # Step 4: Test data mapping and insertion
        print("🔄 STEP 4: Testing data mapping and insertion")
        print("-" * 40)
        mapping_analysis = self._test_data_mapping()
        if 'error' in mapping_analysis:
            print(f"⚠️ Data mapping issues detected")
        else:
            print("✅ Data mapping test successful")
        print()
        
        # Step 5: Test actual insertion
        print("💾 STEP 5: Testing database insertion")
        print("-" * 40)
        insertion_analysis = self._test_database_insertion()
        print()
        
        # Step 6: Generate compatibility report
        print("📋 STEP 6: Generating compatibility report")
        print("-" * 40)
        compatibility_report = self._generate_compatibility_report(
            csv_analysis, config_analysis, schema_analysis, 
            mapping_analysis, insertion_analysis
        )
        print()
        
        return compatibility_report
    
    def _load_and_analyze_csv(self) -> Dict[str, Any]:
        """Load and analyze the workforce_context.csv file."""
        workforce_csv = self.data_dir / 'workforce_context' / 'workforce_context.csv'
        
        if not workforce_csv.exists():
            return {'error': f'Workforce CSV not found: {workforce_csv}'}
        
        try:
            # Load the CSV file
            self.csv_data = pd.read_csv(workforce_csv, encoding='utf-8', low_memory=False)
            
            return {
                'file_path': str(workforce_csv),
                'rows': len(self.csv_data),
                'columns': len(self.csv_data.columns),
                'column_names': list(self.csv_data.columns),
                'column_types': {col: str(dtype) for col, dtype in self.csv_data.dtypes.items()},
                'sample_data': self.csv_data.head(3).to_dict('records'),
                'null_counts': self.csv_data.isnull().sum().to_dict(),
                'unique_counts': self.csv_data.nunique().to_dict()
            }
            
        except Exception as e:
            return {'error': f'Failed to load CSV: {e}'}
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load the current configuration for core_workforce_current."""
        config_file = self.config_dir / 'sources.yaml'
        
        if not config_file.exists():
            return {'error': f'Configuration file not found: {config_file}'}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            workforce_config = config.get('data_sources', {}).get('core_workforce_current', {})
            
            if not workforce_config:
                return {'error': 'core_workforce_current configuration not found'}
            
            self.config_data = workforce_config
            
            return {
                'file_path': str(config_file),
                'table_name': workforce_config.get('table_name'),
                'description': workforce_config.get('description'),
                'column_mappings': workforce_config.get('column_mapping', {}),
                'enrichment_config': workforce_config.get('enrichment', {}),
                'has_enrichment': 'enrichment' in workforce_config
            }
            
        except Exception as e:
            return {'error': f'Failed to load configuration: {e}'}
    
    def _create_test_schema(self) -> Dict[str, Any]:
        """Create test database schema using SchemaBuilder."""
        try:
            # Import schema builder
            sys.path.append(str(PROJECT_ROOT / 'src'))
            from skill_similarity_engine.business_context.schema_builder import SchemaBuilder
            
            # Create schema in test database
            schema_builder = SchemaBuilder(self.test_db_path)
            
            with sqlite3.connect(self.test_db_path) as conn:
                # Create just the core_workforce_current table
                schema_builder._create_core_workforce_current_table(conn)
                
                # Get table info to verify creation
                cursor = conn.execute("PRAGMA table_info(core_workforce_current)")
                columns = cursor.fetchall()
                
                table_info = {
                    'column_count': len(columns),
                    'columns': [
                        {
                            'name': col[1],
                            'type': col[2],
                            'not_null': bool(col[3]),
                            'default_value': col[4],
                            'primary_key': bool(col[5])
                        }
                        for col in columns
                    ]
                }
                
                self.schema_created = True
                
                return {
                    'schema_created': True,
                    'table_info': table_info,
                    'primary_key': [col['name'] for col in table_info['columns'] if col['primary_key']],
                    'required_columns': [col['name'] for col in table_info['columns'] if col['not_null'] and not col['primary_key']]
                }
                
        except Exception as e:
            return {'error': f'Schema creation failed: {e}'}
    
    def _test_data_mapping(self) -> Dict[str, Any]:
        """Test mapping CSV columns to database columns."""
        if self.csv_data is None or self.config_data is None:
            return {'error': 'CSV data or configuration not loaded'}
        
        csv_columns = set(self.csv_data.columns)
        config_mappings = self.config_data.get('column_mapping', {})
        
        # Test column mapping
        mapped_columns = set(config_mappings.keys())
        target_columns = set(config_mappings.values())
        
        # Find gaps
        missing_in_csv = mapped_columns - csv_columns
        unmapped_in_csv = csv_columns - mapped_columns
        
        # Test sample data mapping
        mapping_success = True
        mapping_errors = []
        
        try:
            # Create mapped sample data
            sample_data = self.csv_data.head(5).copy()
            
            # Apply column mappings
            mapped_sample = {}
            for csv_col, db_col in config_mappings.items():
                if csv_col in sample_data.columns:
                    mapped_sample[db_col] = sample_data[csv_col].tolist()
                else:
                    mapping_errors.append(f"Column '{csv_col}' not found in CSV")
                    mapping_success = False
            
            # Check for enrichment columns (like JobProfileID)
            enrichment_config = self.config_data.get('enrichment', {})
            for enrich_col, enrich_config in enrichment_config.items():
                mapped_sample[enrich_col] = [None] * 5  # Placeholder for enriched data
            
        except Exception as e:
            mapping_success = False
            mapping_errors.append(f"Mapping test failed: {e}")
        
        return {
            'mapping_success': mapping_success,
            'mapping_errors': mapping_errors,
            'csv_columns': list(csv_columns),
            'mapped_columns': list(mapped_columns),
            'target_columns': list(target_columns),
            'missing_in_csv': list(missing_in_csv),
            'unmapped_in_csv': list(unmapped_in_csv),
            'mapping_coverage': len(csv_columns & mapped_columns) / len(csv_columns) * 100 if csv_columns else 0
        }
    
    def _test_database_insertion(self) -> Dict[str, Any]:
        """Test actual database insertion with sample data."""
        if not self.schema_created or self.csv_data is None or self.config_data is None:
            return {'error': 'Prerequisites not met for insertion test'}
        
        try:
            with sqlite3.connect(self.test_db_path) as conn:
                # Prepare sample data for insertion
                sample_data = self.csv_data.head(10).copy()
                config_mappings = self.config_data.get('column_mapping', {})
                
                # Map columns
                mapped_data = {}
                for csv_col, db_col in config_mappings.items():
                    if csv_col in sample_data.columns:
                        mapped_data[db_col] = sample_data[csv_col]
                
                # Add enrichment columns with placeholder values
                enrichment_config = self.config_data.get('enrichment', {})
                for enrich_col in enrichment_config.keys():
                    mapped_data[enrich_col] = [f'TEST_{enrich_col}_{i}' for i in range(len(sample_data))]
                
                # Create DataFrame with mapped data
                mapped_df = pd.DataFrame(mapped_data)
                
                # Test insertion
                mapped_df.to_sql('core_workforce_current', conn, if_exists='append', index=False)
                
                # Verify insertion
                cursor = conn.execute("SELECT COUNT(*) FROM core_workforce_current")
                inserted_count = cursor.fetchone()[0]
                
                # Test for duplicates (the original UNIQUE constraint issue)
                cursor = conn.execute("""
                    SELECT employee_number, COUNT(*) as count 
                    FROM core_workforce_current 
                    GROUP BY employee_number 
                    HAVING COUNT(*) > 1
                """)
                duplicates = cursor.fetchall()
                
                return {
                    'insertion_success': True,
                    'inserted_rows': inserted_count,
                    'duplicate_employees': duplicates,
                    'has_duplicates': len(duplicates) > 0,
                    'test_passed': inserted_count == 10 and len(duplicates) == 0
                }
                
        except Exception as e:
            return {
                'insertion_success': False,
                'error': str(e),
                'test_passed': False
            }
    
    def _generate_compatibility_report(self, csv_analysis, config_analysis, 
                                     schema_analysis, mapping_analysis, 
                                     insertion_analysis) -> Dict[str, Any]:
        """Generate comprehensive compatibility report."""
        print("🎯 COMPATIBILITY TEST RESULTS")
        print("=" * 60)
        
        # Overall compatibility assessment
        overall_compatible = True
        critical_issues = []
        warnings = []
        recommendations = []
        
        # Check CSV analysis
        if 'error' in csv_analysis:
            overall_compatible = False
            critical_issues.append(f"CSV loading failed: {csv_analysis['error']}")
        else:
            print(f"✅ CSV Data: {csv_analysis['rows']:,} rows, {csv_analysis['columns']} columns")
        
        # Check configuration analysis
        if 'error' in config_analysis:
            overall_compatible = False
            critical_issues.append(f"Configuration loading failed: {config_analysis['error']}")
        else:
            print(f"✅ Configuration: {len(config_analysis['column_mappings'])} mappings loaded")
        
        # Check schema analysis
        if 'error' in schema_analysis:
            overall_compatible = False
            critical_issues.append(f"Schema creation failed: {schema_analysis['error']}")
        else:
            print(f"✅ Schema: {schema_analysis['table_info']['column_count']} columns created")
        
        # Check mapping analysis
        if 'error' in mapping_analysis:
            overall_compatible = False
            critical_issues.append(f"Data mapping failed: {mapping_analysis['error']}")
        elif not mapping_analysis['mapping_success']:
            overall_compatible = False
            critical_issues.extend(mapping_analysis['mapping_errors'])
        else:
            coverage = mapping_analysis['mapping_coverage']
            print(f"✅ Mapping: {coverage:.1f}% coverage")
            
            if mapping_analysis['missing_in_csv']:
                warnings.append(f"Missing CSV columns: {mapping_analysis['missing_in_csv']}")
            
            if mapping_analysis['unmapped_in_csv']:
                warnings.append(f"Unmapped CSV columns: {mapping_analysis['unmapped_in_csv']}")
        
        # Check insertion analysis
        if 'error' in insertion_analysis:
            overall_compatible = False
            critical_issues.append(f"Database insertion failed: {insertion_analysis['error']}")
        elif not insertion_analysis['test_passed']:
            if insertion_analysis.get('has_duplicates'):
                critical_issues.append("UNIQUE constraint violation detected in test data")
            else:
                warnings.append("Insertion test had unexpected results")
        else:
            print(f"✅ Insertion: {insertion_analysis['inserted_rows']} test rows inserted successfully")
        
        print()
        
        # Generate recommendations
        if critical_issues:
            print("🚨 CRITICAL ISSUES")
            print("-" * 30)
            for issue in critical_issues:
                print(f"   ❌ {issue}")
            print()
            
            # Specific recommendations based on issues
            if any('Column' in issue and 'not found' in issue for issue in critical_issues):
                recommendations.append("Update column mappings in config/data/sources.yaml to match actual CSV structure")
            
            if any('UNIQUE constraint' in issue for issue in critical_issues):
                recommendations.append("Check for duplicate employee numbers in source CSV data")
                recommendations.append("Consider using if_exists='replace' instead of 'append' in data loader")
            
            if any('Schema creation failed' in issue for issue in critical_issues):
                recommendations.append("Review database schema definition in schema_builder.py")
        
        if warnings:
            print("⚠️ WARNINGS")
            print("-" * 30)
            for warning in warnings:
                print(f"   🔔 {warning}")
            print()
        
        # Compatibility summary
        if overall_compatible:
            print("✅ OVERALL COMPATIBILITY: PASSED")
            print("   The current configuration should work with your CSV data.")
        else:
            print("❌ OVERALL COMPATIBILITY: FAILED")
            print("   Issues detected that will prevent successful data loading.")
        
        if recommendations:
            print()
            print("💡 RECOMMENDATIONS")
            print("-" * 30)
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        print()
        print("=" * 60)
        
        return {
            'overall_compatible': overall_compatible,
            'critical_issues': critical_issues,
            'warnings': warnings,
            'recommendations': recommendations,
            'csv_analysis': csv_analysis,
            'config_analysis': config_analysis,
            'schema_analysis': schema_analysis,
            'mapping_analysis': mapping_analysis,
            'insertion_analysis': insertion_analysis
        }

def main():
    """Main execution function."""
    tester = WorkforceSchemaCompatibilityTester()
    
    try:
        # Run compatibility test
        results = tester.run_compatibility_test()
        
        # Save results
        import json
        output_file = PROJECT_ROOT / 'workforce_schema_compatibility_test.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📄 Detailed results saved to: {output_file}")
        
        # Return appropriate exit code
        if results.get('overall_compatible', False):
            print("🎉 Test completed successfully - system is compatible!")
            return 0
        else:
            print("⚠️ Test completed with issues - review recommendations above")
            return 1
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())