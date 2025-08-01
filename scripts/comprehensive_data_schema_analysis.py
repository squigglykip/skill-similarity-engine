#!/usr/bin/env python3
"""
Comprehensive Data & Schema Analysis Tool
==========================================

This script provides a complete gap analysis between:
1. Raw CSV data structure (what we have)
2. Database schema expectations (what the system expects)
3. Configuration mappings (how they should connect)
4. Existing database state (what's already loaded)

Usage:
    python scripts/comprehensive_data_schema_analysis.py

Output:
    - Complete CSV file inventory and analysis
    - Database schema structure analysis
    - Configuration mapping validation
    - Gap analysis and recommendations
    - Diagnostic information for UNIQUE constraint issues
"""

import pandas as pd
import sqlite3
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from collections import defaultdict
import warnings

warnings.filterwarnings('ignore')

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
CONFIG_DIR = PROJECT_ROOT / 'config' / 'data'
MODELS_DIR = PROJECT_ROOT / 'models'

class ComprehensiveAnalyzer:
    """Complete analysis of data pipeline from CSV to database."""
    
    def __init__(self):
        """Initialize analyzer with project paths."""
        self.project_root = PROJECT_ROOT
        self.data_dir = DATA_DIR
        self.config_dir = CONFIG_DIR
        self.models_dir = MODELS_DIR
        
        # Results storage
        self.csv_analysis = {}
        self.schema_analysis = {}
        self.config_analysis = {}
        self.database_analysis = {}
        self.gap_analysis = {}
        
    def run_complete_analysis(self) -> Dict[str, Any]:
        """Run complete analysis pipeline."""
        print("🔍 COMPREHENSIVE DATA & SCHEMA ANALYSIS")
        print("=" * 80)
        print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏠 Project Root: {self.project_root}")
        print("=" * 80)
        print()
        
        # Step 1: Analyze CSV data structure
        print("📊 STEP 1: Analyzing CSV Data Structure")
        print("-" * 50)
        self.csv_analysis = self._analyze_csv_data()
        print(f"✅ Found {len(self.csv_analysis)} CSV files")
        print()
        
        # Step 2: Analyze configuration mappings
        print("⚙️ STEP 2: Analyzing Configuration Mappings")
        print("-" * 50)
        self.config_analysis = self._analyze_configuration()
        print(f"✅ Found {len(self.config_analysis.get('data_sources', {}))} configured data sources")
        print()
        
        # Step 3: Analyze database schema expectations
        print("🗄️ STEP 3: Analyzing Database Schema")
        print("-" * 50)
        self.schema_analysis = self._analyze_database_schema()
        print(f"✅ Analyzed schema expectations")
        print()
        
        # Step 4: Analyze existing database state
        print("🔍 STEP 4: Analyzing Existing Database State")
        print("-" * 50)
        self.database_analysis = self._analyze_existing_databases()
        print(f"✅ Found {len(self.database_analysis)} database files")
        print()
        
        # Step 5: Perform gap analysis
        print("🎯 STEP 5: Performing Gap Analysis")
        print("-" * 50)
        self.gap_analysis = self._perform_gap_analysis()
        print("✅ Gap analysis complete")
        print()
        
        # Step 6: Generate comprehensive report
        print("📋 STEP 6: Generating Comprehensive Report")
        print("-" * 50)
        self._generate_comprehensive_report()
        print("✅ Report generated")
        print()
        
        return {
            'csv_analysis': self.csv_analysis,
            'config_analysis': self.config_analysis,
            'schema_analysis': self.schema_analysis,
            'database_analysis': self.database_analysis,
            'gap_analysis': self.gap_analysis
        }
    
    def _analyze_csv_data(self) -> Dict[str, Any]:
        """Analyze all CSV files in the data directory."""
        csv_files = list(self.data_dir.rglob('*.csv'))
        analysis = {
            'files': {},
            'summary': {
                'total_files': len(csv_files),
                'total_size_mb': 0,
                'total_rows': 0,
                'directories': set()
            }
        }
        
        for csv_file in csv_files:
            try:
                # Get file info
                stat = csv_file.stat()
                size_mb = round(stat.st_size / (1024 * 1024), 2)
                
                # Try to read CSV
                df = pd.read_csv(csv_file, encoding='utf-8', low_memory=False, nrows=1000)  # Sample first 1000 rows
                
                # Analyze structure
                file_analysis = {
                    'path': str(csv_file),
                    'relative_path': str(csv_file.relative_to(self.project_root)),
                    'directory': str(csv_file.parent.relative_to(self.data_dir)),
                    'size_mb': size_mb,
                    'total_rows': len(df),  # Note: this is sampled
                    'total_columns': len(df.columns),
                    'columns': list(df.columns),
                    'column_types': {col: str(dtype) for col, dtype in df.dtypes.items()},
                    'sample_data': df.head(3).to_dict('records'),
                    'null_counts': df.isnull().sum().to_dict(),
                    'unique_counts': df.nunique().to_dict()
                }
                
                # Get actual row count for smaller files
                if size_mb < 10:  # Only for files under 10MB
                    full_df = pd.read_csv(csv_file, encoding='utf-8', low_memory=False)
                    file_analysis['total_rows'] = len(full_df)
                    analysis['summary']['total_rows'] += len(full_df)
                else:
                    # Estimate based on sample
                    estimated_rows = int((stat.st_size / 1024) * 10)  # Rough estimate
                    file_analysis['total_rows_estimated'] = estimated_rows
                    analysis['summary']['total_rows'] += estimated_rows
                
                analysis['files'][csv_file.name] = file_analysis
                analysis['summary']['total_size_mb'] += size_mb
                analysis['summary']['directories'].add(file_analysis['directory'])
                
            except Exception as e:
                analysis['files'][csv_file.name] = {
                    'error': str(e),
                    'path': str(csv_file)
                }
        
        analysis['summary']['directories'] = list(analysis['summary']['directories'])
        return analysis
    
    def _analyze_configuration(self) -> Dict[str, Any]:
        """Analyze configuration files and mappings."""
        config_file = self.config_dir / 'sources.yaml'
        
        if not config_file.exists():
            return {'error': f'Configuration file not found: {config_file}'}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            analysis = {
                'config_file': str(config_file),
                'data_sources': config.get('data_sources', {}),
                'loading_sequence': config.get('loading_sequence', []),
                'processing_config': config.get('processing', {}),
                'quality_checks': config.get('quality_checks', {}),
                'mappings_analysis': {}
            }
            
            # Analyze each data source mapping
            for source_name, source_config in analysis['data_sources'].items():
                mapping_analysis = {
                    'file_path': source_config.get('file_path'),
                    'table_name': source_config.get('table_name'),
                    'has_enrichment': 'enrichment' in source_config,
                    'column_mappings': source_config.get('column_mapping', {}),
                    'mapping_count': len(source_config.get('column_mapping', {}))
                }
                
                # Check for special processing
                if 'file_pattern' in source_config:
                    mapping_analysis['is_multi_file'] = True
                    mapping_analysis['file_pattern'] = source_config['file_pattern']
                
                analysis['mappings_analysis'][source_name] = mapping_analysis
            
            return analysis
            
        except Exception as e:
            return {'error': f'Failed to analyze configuration: {e}'}
    
    def _analyze_database_schema(self) -> Dict[str, Any]:
        """Analyze expected database schema from schema builder."""
        try:
            # Import schema builder to get expected structure
            sys.path.append(str(PROJECT_ROOT / 'src'))
            from skill_similarity_engine.business_context.schema_builder import SchemaBuilder
            
            # Create a temporary in-memory database to analyze schema
            temp_db = ':memory:'
            schema_builder = SchemaBuilder(temp_db)
            
            with sqlite3.connect(temp_db) as conn:
                # Create schema without dropping (since it's empty)
                schema_builder.create_schema(drop_existing=False)
                
                # Get all table information
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                schema_info = {}
                for table in tables:
                    # Get column information
                    cursor = conn.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    
                    # Get foreign key information
                    cursor = conn.execute(f"PRAGMA foreign_key_list({table})")
                    foreign_keys = cursor.fetchall()
                    
                    # Get indexes
                    cursor = conn.execute(f"PRAGMA index_list({table})")
                    indexes = cursor.fetchall()
                    
                    schema_info[table] = {
                        'columns': [
                            {
                                'name': col[1],
                                'type': col[2],
                                'not_null': bool(col[3]),
                                'default_value': col[4],
                                'primary_key': bool(col[5])
                            }
                            for col in columns
                        ],
                        'foreign_keys': [
                            {
                                'column': fk[3],
                                'references_table': fk[2],
                                'references_column': fk[4]
                            }
                            for fk in foreign_keys
                        ],
                        'indexes': [idx[1] for idx in indexes],
                        'primary_keys': [col['name'] for col in schema_info.get(table, {}).get('columns', []) if col.get('primary_key')],
                        'required_columns': [col['name'] for col in schema_info.get(table, {}).get('columns', []) if col.get('not_null') and not col.get('primary_key')]
                    }
            
            return {
                'total_tables': len(tables),
                'tables': tables,
                'schema_details': schema_info,
                'core_tables': [t for t in tables if t.startswith('core_')],
                'analytics_tables': [t for t in tables if t.startswith('analytics_')],
                'system_tables': [t for t in tables if t.startswith('sys_')]
            }
            
        except Exception as e:
            return {'error': f'Failed to analyze schema: {e}'}
    
    def _analyze_existing_databases(self) -> Dict[str, Any]:
        """Analyze existing database files in models directory."""
        if not self.models_dir.exists():
            return {'error': f'Models directory not found: {self.models_dir}'}
        
        db_files = list(self.models_dir.rglob('*.sqlite'))
        analysis = {}
        
        for db_file in db_files:
            try:
                with sqlite3.connect(db_file) as conn:
                    # Get basic database info
                    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    table_data = {}
                    total_rows = 0
                    
                    for table in tables:
                        try:
                            # Get row count
                            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                            row_count = cursor.fetchone()[0]
                            total_rows += row_count
                            
                            # Get sample data if table has data
                            sample_data = []
                            if row_count > 0:
                                cursor = conn.execute(f"SELECT * FROM {table} LIMIT 3")
                                columns = [description[0] for description in cursor.description]
                                rows = cursor.fetchall()
                                sample_data = [dict(zip(columns, row)) for row in rows]
                            
                            table_data[table] = {
                                'row_count': row_count,
                                'sample_data': sample_data
                            }
                            
                        except Exception as e:
                            table_data[table] = {'error': str(e)}
                    
                    analysis[str(db_file.relative_to(self.project_root))] = {
                        'path': str(db_file),
                        'size_mb': round(db_file.stat().st_size / (1024 * 1024), 2),
                        'tables': tables,
                        'total_tables': len(tables),
                        'total_rows': total_rows,
                        'table_data': table_data,
                        'last_modified': datetime.fromtimestamp(db_file.stat().st_mtime).isoformat()
                    }
                    
            except Exception as e:
                analysis[str(db_file.relative_to(self.project_root))] = {
                    'error': str(e),
                    'path': str(db_file)
                }
        
        return analysis
    
    def _perform_gap_analysis(self) -> Dict[str, Any]:
        """Perform comprehensive gap analysis."""
        gaps = {
            'csv_to_config_gaps': {},
            'config_to_schema_gaps': {},
            'schema_to_database_gaps': {},
            'critical_issues': [],
            'recommendations': []
        }
        
        # Analyze CSV to Config gaps
        config_sources = self.config_analysis.get('data_sources', {})
        csv_files = self.csv_analysis.get('files', {})
        
        for source_name, source_config in config_sources.items():
            file_path = source_config.get('file_path', '')
            expected_file = file_path.split('/')[-1] if file_path else 'unknown'
            
            # Check if corresponding CSV exists
            if expected_file not in csv_files and not source_config.get('file_pattern'):
                gaps['csv_to_config_gaps'][source_name] = {
                    'issue': 'Missing CSV file',
                    'expected_file': expected_file,
                    'file_path': file_path
                }
            
            # Check column mappings against actual CSV columns
            if expected_file in csv_files and 'columns' in csv_files[expected_file]:
                csv_columns = set(csv_files[expected_file]['columns'])
                mapped_columns = set(source_config.get('column_mapping', {}).keys())
                
                missing_columns = mapped_columns - csv_columns
                unmapped_columns = csv_columns - mapped_columns
                
                if missing_columns or unmapped_columns:
                    gaps['csv_to_config_gaps'][source_name] = {
                        'missing_columns': list(missing_columns),
                        'unmapped_columns': list(unmapped_columns),
                        'csv_file': expected_file
                    }
        
        # Analyze Config to Schema gaps
        schema_tables = self.schema_analysis.get('schema_details', {})
        
        for source_name, source_config in config_sources.items():
            table_name = source_config.get('table_name')
            
            if table_name and table_name in schema_tables:
                schema_columns = {col['name'] for col in schema_tables[table_name]['columns']}
                mapped_targets = set(source_config.get('column_mapping', {}).values())
                
                missing_in_schema = mapped_targets - schema_columns
                missing_in_mapping = schema_columns - mapped_targets
                
                if missing_in_schema or missing_in_mapping:
                    gaps['config_to_schema_gaps'][source_name] = {
                        'missing_in_schema': list(missing_in_schema),
                        'missing_in_mapping': list(missing_in_mapping),
                        'table_name': table_name
                    }
        
        # Check for critical issues
        for db_path, db_info in self.database_analysis.items():
            if 'table_data' in db_info:
                for table_name, table_info in db_info['table_data'].items():
                    if table_name == 'core_workforce_current' and table_info.get('row_count', 0) > 0:
                        gaps['critical_issues'].append({
                            'type': 'existing_data_in_workforce_table',
                            'message': f'core_workforce_current table in {db_path} already has {table_info["row_count"]} rows',
                            'impact': 'This could cause UNIQUE constraint violations on employee_number',
                            'recommendation': 'Clear table before loading or use if_exists="replace"'
                        })
        
        # Generate recommendations
        if gaps['csv_to_config_gaps']:
            gaps['recommendations'].append('Review column mappings - some CSV columns are not mapped to database')
        
        if gaps['config_to_schema_gaps']:
            gaps['recommendations'].append('Update schema or configuration - mismatches detected')
        
        if gaps['critical_issues']:
            gaps['recommendations'].append('Address critical data loading issues before proceeding')
        
        return gaps
    
    def _generate_comprehensive_report(self):
        """Generate comprehensive analysis report."""
        print("=" * 80)
        print("COMPREHENSIVE DATA & SCHEMA ANALYSIS REPORT")
        print("=" * 80)
        print()
        
        # CSV Analysis Summary
        print("📊 CSV DATA ANALYSIS SUMMARY")
        print("-" * 50)
        csv_summary = self.csv_analysis.get('summary', {})
        print(f"Total CSV Files: {csv_summary.get('total_files', 0)}")
        print(f"Total Data Size: {csv_summary.get('total_size_mb', 0):.2f} MB")
        print(f"Total Rows: {csv_summary.get('total_rows', 0):,}")
        print(f"Data Directories: {len(csv_summary.get('directories', []))}")
        
        # Show directory breakdown
        for directory in csv_summary.get('directories', []):
            dir_files = [f for f in self.csv_analysis.get('files', {}).values() 
                        if f.get('directory') == directory and 'error' not in f]
            total_rows = sum(f.get('total_rows', 0) for f in dir_files)
            total_size = sum(f.get('size_mb', 0) for f in dir_files)
            print(f"  📂 {directory}/: {len(dir_files)} files, {total_rows:,} rows, {total_size:.2f} MB")
        print()
        
        # Configuration Analysis
        print("⚙️ CONFIGURATION ANALYSIS")
        print("-" * 50)
        config_sources = self.config_analysis.get('data_sources', {})
        print(f"Configured Data Sources: {len(config_sources)}")
        print(f"Loading Sequence: {self.config_analysis.get('loading_sequence', [])}")
        
        for source_name, mapping_info in self.config_analysis.get('mappings_analysis', {}).items():
            print(f"  🔧 {source_name}:")
            print(f"    Table: {mapping_info.get('table_name')}")
            print(f"    File: {mapping_info.get('file_path')}")
            print(f"    Columns Mapped: {mapping_info.get('mapping_count')}")
            if mapping_info.get('has_enrichment'):
                print(f"    ✨ Has enrichment")
        print()
        
        # Schema Analysis
        print("🗄️ DATABASE SCHEMA ANALYSIS")
        print("-" * 50)
        schema_info = self.schema_analysis
        if 'error' not in schema_info:
            print(f"Total Tables: {schema_info.get('total_tables', 0)}")
            print(f"Core Tables: {len(schema_info.get('core_tables', []))}")
            print(f"Analytics Tables: {len(schema_info.get('analytics_tables', []))}")
            print(f"System Tables: {len(schema_info.get('system_tables', []))}")
            
            # Show core table details
            print("\nCore Tables Structure:")
            for table in schema_info.get('core_tables', []):
                table_info = schema_info.get('schema_details', {}).get(table, {})
                columns = table_info.get('columns', [])
                primary_keys = [col['name'] for col in columns if col.get('primary_key')]
                print(f"  📋 {table}: {len(columns)} columns, PK: {primary_keys}")
        else:
            print(f"❌ Schema Analysis Error: {schema_info.get('error')}")
        print()
        
        # Database State Analysis
        print("🔍 EXISTING DATABASE STATE")
        print("-" * 50)
        db_analysis = self.database_analysis
        if db_analysis:
            for db_path, db_info in db_analysis.items():
                if 'error' not in db_info:
                    print(f"📁 {db_path}:")
                    print(f"    Size: {db_info.get('size_mb', 0):.2f} MB")
                    print(f"    Tables: {db_info.get('total_tables', 0)}")
                    print(f"    Total Rows: {db_info.get('total_rows', 0):,}")
                    print(f"    Modified: {db_info.get('last_modified', 'Unknown')}")
                    
                    # Show table details
                    for table_name, table_data in db_info.get('table_data', {}).items():
                        if 'error' not in table_data:
                            row_count = table_data.get('row_count', 0)
                            status = "📊" if row_count > 0 else "📝"
                            print(f"      {status} {table_name}: {row_count:,} rows")
                else:
                    print(f"❌ {db_path}: {db_info.get('error')}")
        else:
            print("No database files found")
        print()
        
        # Gap Analysis
        print("🎯 GAP ANALYSIS & CRITICAL ISSUES")
        print("-" * 50)
        gaps = self.gap_analysis
        
        # Critical Issues
        critical_issues = gaps.get('critical_issues', [])
        if critical_issues:
            print("🚨 CRITICAL ISSUES:")
            for issue in critical_issues:
                print(f"  ❌ {issue.get('type', 'Unknown')}")
                print(f"     Message: {issue.get('message', 'No details')}")
                print(f"     Impact: {issue.get('impact', 'Unknown impact')}")
                print(f"     Fix: {issue.get('recommendation', 'No recommendation')}")
                print()
        
        # CSV to Config Gaps
        csv_gaps = gaps.get('csv_to_config_gaps', {})
        if csv_gaps:
            print("📊➡️⚙️ CSV TO CONFIGURATION GAPS:")
            for source, gap_info in csv_gaps.items():
                print(f"  🔧 {source}:")
                if 'missing_columns' in gap_info:
                    print(f"    Missing in CSV: {gap_info['missing_columns']}")
                if 'unmapped_columns' in gap_info:
                    print(f"    Unmapped CSV columns: {gap_info['unmapped_columns']}")
                if 'issue' in gap_info:
                    print(f"    Issue: {gap_info['issue']}")
                print()
        
        # Config to Schema Gaps
        schema_gaps = gaps.get('config_to_schema_gaps', {})
        if schema_gaps:
            print("⚙️➡️🗄️ CONFIGURATION TO SCHEMA GAPS:")
            for source, gap_info in schema_gaps.items():
                print(f"  🔧 {source} -> {gap_info.get('table_name')}:")
                if gap_info.get('missing_in_schema'):
                    print(f"    Missing in schema: {gap_info['missing_in_schema']}")
                if gap_info.get('missing_in_mapping'):
                    print(f"    Missing in mapping: {gap_info['missing_in_mapping']}")
                print()
        
        # Recommendations
        recommendations = gaps.get('recommendations', [])
        if recommendations:
            print("💡 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        else:
            print("✅ No critical gaps detected!")
        
        print()
        print("=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)

def main():
    """Main execution function."""
    analyzer = ComprehensiveAnalyzer()
    
    # Verify required directories exist
    if not analyzer.data_dir.exists():
        print(f"❌ Data directory not found: {analyzer.data_dir}")
        return 1
    
    try:
        # Run complete analysis
        results = analyzer.run_complete_analysis()
        
        # Save results to file for later reference
        output_file = PROJECT_ROOT / 'comprehensive_analysis_results.json'
        import json
        
        # Convert results to JSON-serializable format
        json_results = {}
        for key, value in results.items():
            try:
                json.dumps(value)  # Test if serializable
                json_results[key] = value
            except (TypeError, ValueError):
                json_results[key] = str(value)  # Convert to string if not serializable
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2, default=str)
        
        print(f"📄 Detailed results saved to: {output_file}")
        return 0
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())