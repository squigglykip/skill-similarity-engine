#!/usr/bin/env python3
"""
Data Pipeline Analysis Script

Compares input CSV data files (as specified in data_sources.yaml) with the actual
contents of the SQLite business context database to identify:
- Row count differences
- Column mapping transformations  
- Data enrichment processes
- Missing or transformed data
- Schema differences

This helps validate the data loading pipeline and understand any discrepancies.
"""

import sqlite3
import pandas as pd
import yaml
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Any
from datetime import datetime
import sys

# Add the parent directory to the Python path to import the engine modules
sys.path.append(str(Path(__file__).parent.parent / 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataPipelineAnalyser:
    """Analyses differences between CSV input and SQLite output."""
    
    def __init__(self, 
                 config_path: str = "config/data_sources.yaml",
                 db_path: str = "models/2025-Q2/business_context.sqlite",
                 data_root: str = "data"):
        """
        Initialize the analyser.
        
        Args:
            config_path: Path to data sources configuration
            db_path: Path to SQLite database
            data_root: Root directory for CSV data files
        """
        self.config_path = Path(config_path)
        self.db_path = Path(db_path)
        self.data_root = Path(data_root)
        
        # Load configuration
        self.config = self._load_config()
        
        # Results storage
        self.analysis_results = {}
        
    def _load_config(self) -> Dict:
        """Load data sources configuration."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return {}
    
    def run_complete_analysis(self) -> Dict:
        """Run complete pipeline analysis."""
        logger.info("=== Starting Complete Data Pipeline Analysis ===")
        logger.info(f"Config: {self.config_path}")
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Data Root: {self.data_root}")
        
        if not self.db_path.exists():
            logger.error(f"Database not found: {self.db_path}")
            return {}
        
        # Analyse each dataset
        data_sources = self.config.get('data_sources', {})
        
        for dataset_name in ['jobs', 'skills', 'job_skills', 'positions']:
            if dataset_name in data_sources:
                logger.info(f"\n--- Analysing {dataset_name} ---")
                self.analysis_results[dataset_name] = self._analyse_dataset(
                    dataset_name, data_sources[dataset_name]
                )
        
        # Special analysis for position enrichment
        logger.info(f"\n--- Analysing Position Enrichment ---")
        self.analysis_results['position_enrichment'] = self._analyse_position_enrichment()
        
        # Database schema analysis
        logger.info(f"\n--- Analysing Database Schema ---")
        self.analysis_results['schema_analysis'] = self._analyse_database_schema()
        
        # Generate summary report
        self._generate_summary_report()
        
        return self.analysis_results
    
    def _analyse_dataset(self, dataset_name: str, dataset_config: Dict) -> Dict:
        """Analyse a specific dataset."""
        results = {
            'dataset_name': dataset_name,
            'csv_file_path': None,
            'csv_exists': False,
            'csv_row_count': 0,
            'csv_columns': [],
            'csv_sample_data': None,
            'sqlite_table_name': dataset_config.get('table_name', dataset_name),
            'sqlite_exists': False,
            'sqlite_row_count': 0,
            'sqlite_columns': [],
            'sqlite_sample_data': None,
            'column_mapping': dataset_config.get('column_mapping', {}),
            'row_count_difference': 0,
            'missing_columns': [],
            'extra_columns': [],
            'data_transformations': []
        }
        
        # Analyse CSV file
        csv_path = self.data_root / dataset_config['file_path']
        results['csv_file_path'] = str(csv_path)
        
        if csv_path.exists():
            results['csv_exists'] = True
            try:
                df_csv = pd.read_csv(csv_path, low_memory=False)
                results['csv_row_count'] = len(df_csv)
                results['csv_columns'] = list(df_csv.columns)
                results['csv_sample_data'] = df_csv.head(3).to_dict('records')
                logger.info(f"CSV: {results['csv_row_count']:,} rows, {len(results['csv_columns'])} columns")
            except Exception as e:
                logger.error(f"Failed to read CSV {csv_path}: {e}")
        else:
            logger.warning(f"CSV file not found: {csv_path}")
        
        # Analyse SQLite table
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if table exists
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (results['sqlite_table_name'],)
                )
                if cursor.fetchone():
                    results['sqlite_exists'] = True
                    
                    # Get row count
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {results['sqlite_table_name']}")
                    results['sqlite_row_count'] = cursor.fetchone()[0]
                    
                    # Get column names
                    cursor = conn.execute(f"PRAGMA table_info({results['sqlite_table_name']})")
                    results['sqlite_columns'] = [row[1] for row in cursor.fetchall()]
                    
                    # Get sample data
                    cursor = conn.execute(f"SELECT * FROM {results['sqlite_table_name']} LIMIT 3")
                    columns = [description[0] for description in cursor.description]
                    sample_rows = cursor.fetchall()
                    results['sqlite_sample_data'] = [
                        dict(zip(columns, row)) for row in sample_rows
                    ]
                    
                    logger.info(f"SQLite: {results['sqlite_row_count']:,} rows, {len(results['sqlite_columns'])} columns")
                else:
                    logger.warning(f"SQLite table {results['sqlite_table_name']} not found")
        except Exception as e:
            logger.error(f"Failed to analyse SQLite table: {e}")
        
        # Calculate differences
        if results['csv_exists'] and results['sqlite_exists']:
            results['row_count_difference'] = results['sqlite_row_count'] - results['csv_row_count']
            
            # Column mapping analysis
            mapped_columns = set(results['column_mapping'].values()) if results['column_mapping'] else set()
            sqlite_columns = set(results['sqlite_columns'])
            csv_columns = set(results['csv_columns'])
            
            results['missing_columns'] = list(csv_columns - sqlite_columns - mapped_columns)
            results['extra_columns'] = list(sqlite_columns - mapped_columns - csv_columns)
            
        return results
    
    def _analyse_position_enrichment(self) -> Dict:
        """Analyse the position enrichment process specifically."""
        results = {
            'workforce_context_file': None,
            'position_mapping_file': None,
            'enrichment_process': 'unknown',
            'enrichment_rate': 0,
            'positions_with_jobs': 0,
            'positions_without_jobs': 0,
            'total_positions': 0
        }
        
        # Check workforce context file
        workforce_path = self.data_root / "workforce_context" / "dummy_workforce_context.csv"
        mapping_path = self.data_root / "job_architecture_to_positions_mapping" / "position_job_mapping.csv"
        
        results['workforce_context_file'] = str(workforce_path)
        results['position_mapping_file'] = str(mapping_path)
        
        try:
            # Load workforce context
            if workforce_path.exists():
                df_workforce = pd.read_csv(workforce_path, low_memory=False)
                logger.info(f"Workforce context: {len(df_workforce):,} positions")
                
                # Check if JobProfileID is in original file
                if 'JobProfileID' in df_workforce.columns:
                    results['enrichment_process'] = 'already_enriched'
                    original_enrichment = df_workforce['JobProfileID'].notna().sum()
                    logger.info(f"Original file already has JobProfileID for {original_enrichment:,} positions")
                else:
                    results['enrichment_process'] = 'requires_mapping'
                    logger.info("Original file requires JobProfileID enrichment from mapping file")
            
            # Load position mapping
            if mapping_path.exists():
                df_mapping = pd.read_csv(mapping_path)
                logger.info(f"Position mapping: {len(df_mapping):,} mappings")
                
                # Analyse overlap
                if workforce_path.exists():
                    common_positions = set(df_workforce['Position Number']) & set(df_mapping['Position_Number'])
                    logger.info(f"Position overlap: {len(common_positions):,} positions have mappings")
            
            # Analyse SQLite result
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM positions")
                results['total_positions'] = cursor.fetchone()[0]
                
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM positions 
                    WHERE JobProfileID IS NOT NULL AND JobProfileID != ''
                """)
                results['positions_with_jobs'] = cursor.fetchone()[0]
                
                results['positions_without_jobs'] = results['total_positions'] - results['positions_with_jobs']
                results['enrichment_rate'] = (results['positions_with_jobs'] / results['total_positions'] * 100) if results['total_positions'] > 0 else 0
                
                logger.info(f"Final enrichment: {results['positions_with_jobs']:,} of {results['total_positions']:,} positions have JobProfileID ({results['enrichment_rate']:.1f}%)")
                
        except Exception as e:
            logger.error(f"Failed to analyse position enrichment: {e}")
        
        return results
    
    def _analyse_database_schema(self) -> Dict:
        """Analyse the database schema structure."""
        results = {
            'tables': {},
            'indexes': [],
            'foreign_keys': [],
            'schema_metadata': {}
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get all tables
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                table_names = [row[0] for row in cursor.fetchall()]
                
                for table_name in table_names:
                    # Get table info
                    cursor = conn.execute(f"PRAGMA table_info({table_name})")
                    columns = []
                    for row in cursor.fetchall():
                        columns.append({
                            'name': row[1],
                            'type': row[2],
                            'not_null': bool(row[3]),
                            'default_value': row[4],
                            'primary_key': bool(row[5])
                        })
                    
                    # Get row count
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    
                    results['tables'][table_name] = {
                        'columns': columns,
                        'row_count': row_count
                    }
                
                # Get indexes
                cursor = conn.execute(
                    "SELECT name, sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
                )
                results['indexes'] = [{'name': row[0], 'sql': row[1]} for row in cursor.fetchall()]
                
                # Get foreign keys for each table
                for table_name in table_names:
                    cursor = conn.execute(f"PRAGMA foreign_key_list({table_name})")
                    fks = cursor.fetchall()
                    if fks:
                        for fk in fks:
                            results['foreign_keys'].append({
                                'table': table_name,
                                'column': fk[3],
                                'references_table': fk[2],
                                'references_column': fk[4]
                            })
                
                # Get schema metadata if it exists
                if 'schema_metadata' in table_names:
                    cursor = conn.execute("SELECT key, value FROM schema_metadata")
                    results['schema_metadata'] = dict(cursor.fetchall())
                
        except Exception as e:
            logger.error(f"Failed to analyse database schema: {e}")
        
        return results
    
    def _generate_summary_report(self) -> None:
        """Generate and print a summary report."""
        print("\n" + "="*80)
        print("DATA PIPELINE ANALYSIS SUMMARY")
        print("="*80)
        print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Database: {self.db_path}")
        print(f"Data Root: {self.data_root}")
        
        # Dataset summary
        print(f"\n{'Dataset':<15} {'CSV Rows':<10} {'SQLite Rows':<12} {'Difference':<12} {'Status':<10}")
        print("-" * 70)
        
        for dataset_name, results in self.analysis_results.items():
            if dataset_name in ['jobs', 'skills', 'job_skills', 'positions']:
                csv_rows = results.get('csv_row_count', 0)
                sqlite_rows = results.get('sqlite_row_count', 0)
                difference = results.get('row_count_difference', 0)
                
                status = "✓ OK"
                if not results.get('csv_exists', False):
                    status = "✗ No CSV"
                elif not results.get('sqlite_exists', False):
                    status = "✗ No Table"
                elif abs(difference) > 0:
                    status = f"△ {difference:+d}"
                
                print(f"{dataset_name:<15} {csv_rows:<10,} {sqlite_rows:<12,} {difference:<12,} {status:<10}")
        
        # Position enrichment summary
        if 'position_enrichment' in self.analysis_results:
            enrichment = self.analysis_results['position_enrichment']
            print(f"\nPosition Enrichment Analysis:")
            print(f"  Process: {enrichment['enrichment_process']}")
            print(f"  Enrichment Rate: {enrichment['enrichment_rate']:.1f}%")
            print(f"  Positions with Jobs: {enrichment['positions_with_jobs']:,}")
            print(f"  Positions without Jobs: {enrichment['positions_without_jobs']:,}")
        
        # Schema summary
        if 'schema_analysis' in self.analysis_results:
            schema = self.analysis_results['schema_analysis']
            print(f"\nDatabase Schema Summary:")
            print(f"  Tables: {len(schema['tables'])}")
            print(f"  Indexes: {len(schema['indexes'])}")
            print(f"  Foreign Keys: {len(schema['foreign_keys'])}")
            
            for table_name, table_info in schema['tables'].items():
                print(f"    {table_name}: {table_info['row_count']:,} rows, {len(table_info['columns'])} columns")
        
        # Issues and recommendations
        print(f"\nIssues and Recommendations:")
        issues_found = False
        
        for dataset_name, results in self.analysis_results.items():
            if dataset_name in ['jobs', 'skills', 'job_skills', 'positions']:
                if not results.get('csv_exists', False):
                    print(f"  ⚠ {dataset_name}: CSV file missing - {results.get('csv_file_path')}")
                    issues_found = True
                elif not results.get('sqlite_exists', False):
                    print(f"  ⚠ {dataset_name}: SQLite table missing")
                    issues_found = True
                elif results.get('row_count_difference', 0) != 0:
                    diff = results.get('row_count_difference', 0)
                    print(f"  ⚠ {dataset_name}: Row count difference of {diff:+d} rows")
                    issues_found = True
                    
                if results.get('missing_columns'):
                    print(f"  ⚠ {dataset_name}: Missing columns from CSV: {results['missing_columns']}")
                    issues_found = True
        
        if not issues_found:
            print("  ✓ No major issues detected")
        
        print(f"\n{'='*80}")


def main():
    """Main function to run the analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyse data pipeline from CSV to SQLite')
    parser.add_argument('--config', default='config/data_sources.yaml', 
                      help='Path to data sources configuration')
    parser.add_argument('--database', default='models/2025-Q2/business_context.sqlite',
                      help='Path to SQLite database')
    parser.add_argument('--data-root', default='data',
                      help='Root directory for CSV data files')
    parser.add_argument('--export-results', 
                      help='Export detailed results to JSON file')
    
    args = parser.parse_args()
    
    # Create analyser and run analysis
    analyser = DataPipelineAnalyser(
        config_path=args.config,
        db_path=args.database,
        data_root=args.data_root
    )
    
    results = analyser.run_complete_analysis()
    
    # Export results if requested
    if args.export_results:
        import json
        with open(args.export_results, 'w') as f:
            # Convert non-serializable objects to strings
            serializable_results = json.loads(json.dumps(results, default=str))
            json.dump(serializable_results, f, indent=2)
        print(f"\nDetailed results exported to: {args.export_results}")


if __name__ == '__main__':
    main() 