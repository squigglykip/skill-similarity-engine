#!/usr/bin/env python3
"""
Schema Analysis Script for Skill Similarity Engine

Generates comprehensive schema documentation for CSV files, including:
- Metadata (row count, column count, memory usage)
- Column-by-column analysis (data types, null values, unique values, statistics)
- Examples and common values
- Categorical detection
- JSON export

Usage:
    python scripts/generate_schema_analysis.py --file data/skills_library/skills_comprehensive_all_versions.csv --output docs/skills_comprehensive_schema.json
    python scripts/generate_schema_analysis.py --file data/job_architecture/dummy_job_architecture.csv --output docs/job_arch_schema.json
"""

import argparse
import json
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from typing import Dict, Any, List, Optional, Union
import re


class SchemaAnalyzer:
    """Comprehensive CSV schema analyzer"""
    
    def __init__(self, file_path: str, sample_size: int = 10000):
        """
        Initialize the schema analyzer
        
        Args:
            file_path: Path to the CSV file to analyze
            sample_size: Number of rows to sample for analysis (0 = all rows)
        """
        self.file_path = Path(file_path)
        self.sample_size = sample_size
        self.df = None
        self.schema = {}
        
    def load_data(self) -> None:
        """Load the CSV data with appropriate sampling"""
        print(f"Loading data from: {self.file_path}")
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        try:
            # First, get total row count
            total_rows = sum(1 for _ in open(self.file_path, 'r', encoding='utf-8')) - 1  # Subtract header
            print(f"Total rows in file: {total_rows:,}")
            
            # Load data with sampling if needed
            if self.sample_size > 0 and total_rows > self.sample_size:
                print(f"Sampling {self.sample_size:,} rows for analysis")
                # Use random sampling
                skip_rows = sorted(np.random.choice(range(1, total_rows + 1), 
                                                  size=total_rows - self.sample_size, 
                                                  replace=False))
                self.df = pd.read_csv(self.file_path, skiprows=skip_rows)
            else:
                print("Loading all rows")
                self.df = pd.read_csv(self.file_path)
                
            print(f"Loaded {len(self.df):,} rows × {len(self.df.columns)} columns")
            
        except Exception as e:
            raise RuntimeError(f"Error loading CSV file: {e}")
    
    def analyze_metadata(self) -> Dict[str, Any]:
        """Analyze file-level metadata"""
        memory_usage = self.df.memory_usage(deep=True).sum()
        
        # Check for duplicate rows
        duplicate_count = self.df.duplicated().sum()
        
        metadata = {
            "row_count": len(self.df),
            "column_count": len(self.df.columns),
            "memory_usage": f"{memory_usage / (1024**2)} MB",
            "column_names": list(self.df.columns),
            "duplicate_rows": int(duplicate_count),
            "duplicate_percentage": round((duplicate_count / len(self.df)) * 100, 2)
        }
        
        return metadata
    
    def analyze_column(self, column_name: str) -> Dict[str, Any]:
        """Analyze a single column comprehensively"""
        series = self.df[column_name]
        
        # Basic info
        column_analysis = {
            "data_type": str(series.dtype),
            "memory_usage": f"{series.memory_usage(deep=True) / 1024} KB",
        }
        
        # Null value analysis
        null_count = series.isnull().sum()
        column_analysis["null_values"] = {
            "count": int(null_count),
            "percentage": round((null_count / len(series)) * 100, 2)
        }
        
        # Unique value analysis
        unique_count = series.nunique()
        column_analysis["unique_values"] = {
            "count": int(unique_count),
            "percentage": round((unique_count / len(series)) * 100, 2)
        }
        
        # String-specific analysis
        if series.dtype == 'object':
            non_null_series = series.dropna().astype(str)
            if len(non_null_series) > 0:
                lengths = non_null_series.str.len()
                column_analysis["statistics"] = {
                    "min_length": int(lengths.min()) if not lengths.empty else 0,
                    "max_length": int(lengths.max()) if not lengths.empty else 0,
                    "mean_length": float(lengths.mean()) if not lengths.empty else 0.0
                }
                
                # Check if might contain JSON
                json_pattern = r'^\s*[\{\[].*[\}\]]\s*$'
                json_like_count = non_null_series.str.match(json_pattern).sum()
                column_analysis["possibly_contains_json"] = bool(json_like_count > 0)
            else:
                column_analysis["statistics"] = {
                    "min_length": 0,
                    "max_length": 0,
                    "mean_length": 0.0
                }
                column_analysis["possibly_contains_json"] = False
        
        # Numeric-specific analysis
        elif pd.api.types.is_numeric_dtype(series):
            non_null_series = series.dropna()
            if len(non_null_series) > 0:
                column_analysis["statistics"] = {
                    "min": float(non_null_series.min()),
                    "max": float(non_null_series.max()),
                    "mean": float(non_null_series.mean()),
                    "median": float(non_null_series.median()),
                    "std": float(non_null_series.std()) if len(non_null_series) > 1 else 0.0
                }
            else:
                column_analysis["statistics"] = {
                    "min": None,
                    "max": None,
                    "mean": None,
                    "median": None,
                    "std": None
                }
        
        # Most common values (top 5)
        value_counts = series.value_counts(dropna=False).head(5)
        column_analysis["most_common_values"] = {}
        for value, count in value_counts.items():
            # Handle NaN values
            if pd.isna(value):
                key = "nan"
            else:
                key = str(value)
            column_analysis["most_common_values"][key] = int(count)
        
        # Examples (first 3 non-null values)
        non_null_values = series.dropna().head(3)
        column_analysis["examples"] = [str(val) for val in non_null_values.tolist()]
        
        # Categorical detection
        is_categorical = self._is_likely_categorical(series)
        column_analysis["potential_categorical"] = is_categorical
        
        if is_categorical:
            all_categories = sorted([str(val) for val in series.dropna().unique()])
            column_analysis["all_categories"] = all_categories
        
        return column_analysis
    
    def _is_likely_categorical(self, series: pd.Series) -> bool:
        """Determine if a column is likely categorical"""
        unique_count = series.nunique()
        total_count = len(series)
        
        # If less than 5% unique values and less than 50 total unique values
        if unique_count <= 50 and (unique_count / total_count) <= 0.05:
            return True
        
        # Special case for boolean-like values
        if series.dtype == 'object':
            unique_values = set(str(val).lower() for val in series.dropna().unique())
            boolean_patterns = [
                {'true', 'false'},
                {'yes', 'no'},
                {'y', 'n'},
                {'1', '0'},
                {'on', 'off'},
                {'enabled', 'disabled'},
                {'active', 'inactive'}
            ]
            if any(unique_values.issubset(pattern) for pattern in boolean_patterns):
                return True
        
        return False
    
    def analyze_schema(self) -> Dict[str, Any]:
        """Perform complete schema analysis"""
        print("Analyzing metadata...")
        metadata = self.analyze_metadata()
        
        print("Analyzing columns...")
        schema = {}
        
        for i, column in enumerate(self.df.columns):
            print(f"  Analyzing column {i+1}/{len(self.df.columns)}: {column}")
            schema[column] = self.analyze_column(column)
        
        return {
            "metadata": metadata,
            "schema": schema
        }
    
    def generate_summary_report(self) -> str:
        """Generate a human-readable summary report"""
        analysis = self.analyze_schema()
        
        report = []
        report.append("=" * 60)
        report.append(f"SCHEMA ANALYSIS REPORT: {self.file_path.name}")
        report.append("=" * 60)
        
        # Metadata summary
        metadata = analysis["metadata"]
        report.append(f"\n📊 METADATA:")
        report.append(f"   • Rows: {metadata['row_count']:,}")
        report.append(f"   • Columns: {metadata['column_count']}")
        report.append(f"   • Memory: {metadata['memory_usage']}")
        report.append(f"   • Duplicates: {metadata['duplicate_rows']:,} ({metadata['duplicate_percentage']}%)")
        
        # Column summaries
        schema = analysis["schema"]
        report.append(f"\n📋 COLUMNS:")
        
        categorical_cols = []
        text_cols = []
        numeric_cols = []
        high_null_cols = []
        
        for col_name, col_info in schema.items():
            if col_info["null_values"]["percentage"] > 50:
                high_null_cols.append(col_name)
            
            if col_info.get("potential_categorical", False):
                categorical_cols.append(col_name)
            elif col_info["data_type"] == "object":
                text_cols.append(col_name)
            else:
                numeric_cols.append(col_name)
        
        if categorical_cols:
            report.append(f"\n   🏷️  Categorical ({len(categorical_cols)}):")
            for col in categorical_cols[:10]:  # Show first 10
                unique_count = schema[col]["unique_values"]["count"]
                report.append(f"      • {col} ({unique_count} categories)")
            if len(categorical_cols) > 10:
                report.append(f"      ... and {len(categorical_cols) - 10} more")
        
        if text_cols:
            report.append(f"\n   📝 Text ({len(text_cols)}):")
            for col in text_cols[:10]:  # Show first 10
                unique_pct = schema[col]["unique_values"]["percentage"]
                report.append(f"      • {col} ({unique_pct}% unique)")
            if len(text_cols) > 10:
                report.append(f"      ... and {len(text_cols) - 10} more")
        
        if numeric_cols:
            report.append(f"\n   🔢 Numeric ({len(numeric_cols)}):")
            for col in numeric_cols[:10]:  # Show first 10
                data_type = schema[col]["data_type"]
                report.append(f"      • {col} ({data_type})")
            if len(numeric_cols) > 10:
                report.append(f"      ... and {len(numeric_cols) - 10} more")
        
        if high_null_cols:
            report.append(f"\n   ⚠️  High Null Percentage:")
            for col in high_null_cols:
                null_pct = schema[col]["null_values"]["percentage"]
                report.append(f"      • {col} ({null_pct}% null)")
        
        return "\n".join(report)
    
    def export_to_json(self, output_path: str) -> None:
        """Export schema analysis to JSON file"""
        analysis = self.analyze_schema()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=4, ensure_ascii=False)
        
        print(f"Schema analysis exported to: {output_file}")


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description="Analyze CSV file schema and generate comprehensive documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze skills library
  python scripts/generate_schema_analysis.py --file data/skills_library/skills_comprehensive_all_versions.csv --output docs/skills_schema.json
  
  # Analyze job architecture with summary report
  python scripts/generate_schema_analysis.py --file data/job_architecture/dummy_job_architecture.csv --output docs/job_arch_schema.json --summary
  
  # Quick analysis with smaller sample
  python scripts/generate_schema_analysis.py --file large_file.csv --sample 5000 --summary
        """
    )
    
    parser.add_argument(
        '--file', '-f',
        required=True,
        help='Path to the CSV file to analyze'
    )
    
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output path for the JSON schema file'
    )
    
    parser.add_argument(
        '--sample', '-s',
        type=int,
        default=10000,
        help='Number of rows to sample (0 = all rows, default: 10000)'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Print a summary report to console'
    )
    
    args = parser.parse_args()
    
    try:
        # Create analyzer
        analyzer = SchemaAnalyzer(args.file, args.sample)
        
        # Load and analyze
        analyzer.load_data()
        
        # Export JSON
        analyzer.export_to_json(args.output)
        
        # Print summary if requested
        if args.summary:
            print("\n" + analyzer.generate_summary_report())
        
        print(f"\n✅ Schema analysis complete!")
        print(f"   📁 Input file: {args.file}")
        print(f"   📄 Output file: {args.output}")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 