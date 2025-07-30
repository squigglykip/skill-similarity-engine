#!/usr/bin/env python3
"""
CSV Data Analysis Script
========================

Comprehensive analysis of all CSV files in the /data/ directory to understand:
- File locations and sizes
- Column headers and data types
- Sample data for each column
- Data quality metrics
- Structure comparison across files

This helps identify mismatches between raw CSV structure and database expectations.

Usage:
    python scripts/analyze_csv_data.py
"""

import pandas as pd
import os
import sys
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

class CSVAnalyzer:
    """Comprehensive CSV file analyzer."""
    
    def __init__(self, data_directory: Path):
        """Initialize with data directory path."""
        self.data_dir = Path(data_directory)
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_directory}")
    
    def find_all_csv_files(self) -> List[Path]:
        """Find all CSV files recursively in the data directory."""
        csv_files = []
        
        # Search recursively for CSV files
        for csv_file in self.data_dir.rglob('*.csv'):
            csv_files.append(csv_file)
        
        return sorted(csv_files)
    
    def analyze_csv_file(self, csv_path: Path) -> Dict[str, Any]:
        """Analyze a single CSV file comprehensively."""
        try:
            # Get file info
            stat = csv_path.stat()
            file_info = {
                'path': str(csv_path),
                'relative_path': str(csv_path.relative_to(PROJECT_ROOT)),
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'size_bytes': stat.st_size,
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'directory': str(csv_path.parent.relative_to(self.data_dir))
            }
            
            # Read CSV with error handling
            try:
                # Try different encodings
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        df = pd.read_csv(csv_path, encoding=encoding, low_memory=False)
                        file_info['encoding'] = encoding
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # If all encodings fail, try with error handling
                    df = pd.read_csv(csv_path, encoding='utf-8', errors='ignore', low_memory=False)
                    file_info['encoding'] = 'utf-8 (with errors ignored)'
                    
            except Exception as e:
                return {
                    **file_info,
                    'error': f"Failed to read CSV: {str(e)}",
                    'analysis_status': 'failed'
                }
            
            # Basic DataFrame info
            file_info.update({
                'rows': len(df),
                'columns': len(df.columns),
                'analysis_status': 'success'
            })
            
            # Column analysis
            columns_analysis = []
            for col in df.columns:
                col_analysis = self._analyze_column(df, col)
                columns_analysis.append(col_analysis)
            
            file_info['columns_analysis'] = columns_analysis
            
            # Data quality metrics
            file_info['data_quality'] = self._analyze_data_quality(df)
            
            # Sample data (first 5 rows)
            try:
                sample_data = df.head(5).to_dict('records')
                # Convert any NaN values to None for JSON serialization
                for row in sample_data:
                    for key, value in row.items():
                        if pd.isna(value):
                            row[key] = None
                file_info['sample_data'] = sample_data
            except Exception:
                file_info['sample_data'] = []
            
            return file_info
            
        except Exception as e:
            return {
                **file_info,
                'error': f"Analysis failed: {str(e)}",
                'analysis_status': 'failed'
            }
    
    def _analyze_column(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Analyze a single column comprehensively."""
        col_data = df[column]
        
        analysis = {
            'name': column,
            'pandas_dtype': str(col_data.dtype),
            'null_count': col_data.isnull().sum(),
            'null_percentage': round((col_data.isnull().sum() / len(col_data)) * 100, 2),
            'unique_count': col_data.nunique(),
            'total_count': len(col_data)
        }
        
        # Infer likely database data type
        analysis['inferred_db_type'] = self._infer_database_type(col_data)
        
        # Get sample values (non-null, unique)
        try:
            non_null_values = col_data.dropna().unique()
            if len(non_null_values) > 0:
                # Take up to 10 sample values
                sample_values = non_null_values[:10].tolist()
                # Convert any numpy types to Python types
                analysis['sample_values'] = [
                    None if pd.isna(val) else (val.item() if hasattr(val, 'item') else val)
                    for val in sample_values
                ]
            else:
                analysis['sample_values'] = []
        except Exception:
            analysis['sample_values'] = []
        
        # Type-specific analysis
        if col_data.dtype in ['object', 'string']:
            # Text column analysis
            non_null_col = col_data.dropna()
            if len(non_null_col) > 0:
                lengths = non_null_col.astype(str).str.len()
                analysis.update({
                    'min_length': int(lengths.min()),
                    'max_length': int(lengths.max()),
                    'avg_length': round(lengths.mean(), 2)
                })
        
        elif col_data.dtype in ['int64', 'int32', 'float64', 'float32']:
            # Numeric column analysis
            non_null_col = col_data.dropna()
            if len(non_null_col) > 0:
                analysis.update({
                    'min_value': non_null_col.min(),
                    'max_value': non_null_col.max(),
                    'mean_value': round(non_null_col.mean(), 4),
                    'std_value': round(non_null_col.std(), 4)
                })
        
        return analysis
    
    def _infer_database_type(self, col_data: pd.Series) -> str:
        """Infer appropriate database column type."""
        dtype = col_data.dtype
        
        if dtype in ['int64', 'int32']:
            return 'INTEGER'
        elif dtype in ['float64', 'float32']:
            return 'REAL'
        elif dtype == 'bool':
            return 'INTEGER'  # SQLite uses INTEGER for boolean
        elif dtype in ['object', 'string']:
            # Check if it looks like text or could be VARCHAR
            non_null_values = col_data.dropna()
            if len(non_null_values) == 0:
                return 'TEXT'
            
            # Check max length to decide between VARCHAR and TEXT
            max_length = non_null_values.astype(str).str.len().max()
            if max_length <= 255:
                return f'VARCHAR({max_length})'
            else:
                return 'TEXT'
        else:
            return 'TEXT'  # Default fallback
    
    def _analyze_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data quality metrics for the entire DataFrame."""
        total_cells = df.shape[0] * df.shape[1]
        null_cells = df.isnull().sum().sum()
        
        # Check for completely empty rows
        empty_rows = df.isnull().all(axis=1).sum()
        
        # Check for completely empty columns
        empty_columns = df.isnull().all(axis=0).sum()
        
        # Check for duplicate rows
        duplicate_rows = df.duplicated().sum()
        
        return {
            'total_cells': total_cells,
            'null_cells': null_cells,
            'null_percentage': round((null_cells / total_cells) * 100, 2) if total_cells > 0 else 0,
            'empty_rows': empty_rows,
            'empty_columns': empty_columns,
            'duplicate_rows': duplicate_rows,
            'completeness_score': round(((total_cells - null_cells) / total_cells) * 100, 2) if total_cells > 0 else 0
        }
    
    def generate_summary_report(self, csv_analyses: List[Dict[str, Any]]) -> None:
        """Generate a comprehensive summary report."""
        print("="*80)
        print("CSV DATA ANALYSIS REPORT")
        print("="*80)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Data Directory: {self.data_dir}")
        print(f"Total CSV Files Found: {len(csv_analyses)}")
        print()
        
        # Group by directory
        by_directory = defaultdict(list)
        successful_analyses = []
        failed_analyses = []
        
        for analysis in csv_analyses:
            directory = analysis.get('directory', 'root')
            by_directory[directory].append(analysis)
            
            if analysis.get('analysis_status') == 'success':
                successful_analyses.append(analysis)
            else:
                failed_analyses.append(analysis)
        
        print(f"✅ Successfully Analyzed: {len(successful_analyses)}")
        print(f"❌ Failed to Analyze: {len(failed_analyses)}")
        print()
        
        # Show failed analyses first
        if failed_analyses:
            print("❌ FAILED ANALYSES")
            print("-" * 50)
            for analysis in failed_analyses:
                print(f"• {analysis['relative_path']}")
                print(f"  Error: {analysis.get('error', 'Unknown error')}")
            print()
        
        # Directory-based summary
        print("📁 FILES BY DIRECTORY")
        print("-" * 50)
        for directory, files in sorted(by_directory.items()):
            print(f"\n📂 {directory}/")
            total_size = sum(f.get('size_mb', 0) for f in files)
            total_rows = sum(f.get('rows', 0) for f in files if f.get('analysis_status') == 'success')
            print(f"   Files: {len(files)} | Total Size: {total_size:.2f} MB | Total Rows: {total_rows:,}")
            
            for file_analysis in files:
                if file_analysis.get('analysis_status') == 'success':
                    filename = Path(file_analysis['relative_path']).name
                    rows = file_analysis.get('rows', 0)
                    cols = file_analysis.get('columns', 0)
                    size = file_analysis.get('size_mb', 0)
                    print(f"   └── {filename} ({rows:,} rows × {cols} cols, {size:.2f} MB)")
                else:
                    filename = Path(file_analysis['relative_path']).name
                    print(f"   └── {filename} (FAILED)")
        
        print()
        
        # Detailed analysis for each file
        print("📊 DETAILED FILE ANALYSIS")
        print("=" * 80)
        
        for i, analysis in enumerate(successful_analyses, 1):
            print(f"\n{i}. {analysis['relative_path']}")
            print("-" * 60)
            
            # File info
            print(f"📁 Location: {analysis['path']}")
            print(f"📏 Size: {analysis['size_mb']} MB ({analysis['size_bytes']:,} bytes)")
            print(f"📅 Modified: {analysis['last_modified']}")
            print(f"🔤 Encoding: {analysis['encoding']}")
            print(f"📊 Dimensions: {analysis['rows']:,} rows × {analysis['columns']} columns")
            
            # Data quality
            quality = analysis.get('data_quality', {})
            print(f"✅ Completeness: {quality.get('completeness_score', 0):.1f}%")
            if quality.get('duplicate_rows', 0) > 0:
                print(f"⚠️  Duplicates: {quality['duplicate_rows']:,} rows")
            if quality.get('empty_rows', 0) > 0:
                print(f"⚠️  Empty Rows: {quality['empty_rows']:,}")
            
            print()
            
            # Column details
            print("📋 COLUMN ANALYSIS:")
            columns = analysis.get('columns_analysis', [])
            if columns:
                # Header
                print(f"{'Column Name':<30} {'Type':<15} {'DB Type':<15} {'Nulls':<8} {'Unique':<8} {'Sample Values'}")
                print("-" * 120)
                
                for col in columns:
                    name = col['name'][:28] + '..' if len(col['name']) > 30 else col['name']
                    pandas_type = col['pandas_dtype'][:13] + '..' if len(col['pandas_dtype']) > 15 else col['pandas_dtype']
                    db_type = col['inferred_db_type'][:13] + '..' if len(col['inferred_db_type']) > 15 else col['inferred_db_type']
                    null_pct = f"{col['null_percentage']:.1f}%"
                    unique_count = f"{col['unique_count']:,}"
                    
                    # Format sample values
                    samples = col.get('sample_values', [])
                    if samples:
                        sample_str = ', '.join([str(s)[:20] + '..' if len(str(s)) > 20 else str(s) for s in samples[:3]])
                        if len(samples) > 3:
                            sample_str += f" ... (+{len(samples)-3} more)"
                    else:
                        sample_str = "(no data)"
                    
                    sample_str = sample_str[:50] + '..' if len(sample_str) > 50 else sample_str
                    
                    print(f"{name:<30} {pandas_type:<15} {db_type:<15} {null_pct:<8} {unique_count:<8} {sample_str}")
            
            # Sample data
            sample_data = analysis.get('sample_data', [])
            if sample_data:
                print(f"\n📝 SAMPLE DATA (first {len(sample_data)} rows):")
                print("-" * 60)
                
                # Show first sample record in detail
                if sample_data:
                    print("Row 1:")
                    for key, value in sample_data[0].items():
                        display_value = str(value)[:50] + '..' if len(str(value)) > 50 else str(value)
                        print(f"  {key}: {display_value}")
                    
                    if len(sample_data) > 1:
                        print(f"\n... and {len(sample_data)-1} more sample rows available")
            
            print("\n" + "="*80)
        
        # Summary statistics
        if successful_analyses:
            print("\n📈 SUMMARY STATISTICS")
            print("-" * 50)
            
            total_files = len(successful_analyses)
            total_size = sum(f['size_mb'] for f in successful_analyses)
            total_rows = sum(f['rows'] for f in successful_analyses)
            total_columns = sum(f['columns'] for f in successful_analyses)
            
            print(f"Total Files Analyzed: {total_files}")
            print(f"Total Data Size: {total_size:.2f} MB")
            print(f"Total Rows: {total_rows:,}")
            print(f"Total Columns: {total_columns:,}")
            print(f"Average Rows per File: {total_rows // total_files:,}")
            print(f"Average Columns per File: {total_columns // total_files}")
            
            # Largest files
            largest_files = sorted(successful_analyses, key=lambda x: x['rows'], reverse=True)[:5]
            print(f"\n🏆 LARGEST FILES BY ROW COUNT:")
            for i, file_info in enumerate(largest_files, 1):
                filename = Path(file_info['relative_path']).name
                print(f"{i}. {filename}: {file_info['rows']:,} rows")
        
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)

def main():
    """Main execution function."""
    print("🔍 CSV DATA ANALYSIS TOOL")
    print("=" * 60)
    print("📂 Analyzing all CSV files in /data/ directory")
    print(f"🏠 Project Root: {PROJECT_ROOT}")
    print(f"📁 Data Directory: {DATA_DIR}")
    print()
    
    if not DATA_DIR.exists():
        print(f"❌ Data directory not found: {DATA_DIR}")
        print("Please ensure the /data/ directory exists with CSV files to analyze.")
        return 1
    
    try:
        analyzer = CSVAnalyzer(DATA_DIR)
        
        # Find all CSV files
        print("🔍 Searching for CSV files...")
        csv_files = analyzer.find_all_csv_files()
        
        if not csv_files:
            print("❌ No CSV files found in the data directory.")
            return 1
        
        print(f"📄 Found {len(csv_files)} CSV files")
        print()
        
        # Analyze each file
        analyses = []
        for i, csv_file in enumerate(csv_files, 1):
            print(f"🔄 Analyzing {i}/{len(csv_files)}: {csv_file.relative_to(PROJECT_ROOT)}")
            analysis = analyzer.analyze_csv_file(csv_file)
            analyses.append(analysis)
        
        print()
        
        # Generate comprehensive report
        analyzer.generate_summary_report(analyses)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 