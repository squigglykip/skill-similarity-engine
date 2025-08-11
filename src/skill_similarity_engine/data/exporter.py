import sqlite3
import logging
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime
import pandas as pd
import os

logger = logging.getLogger(__name__)


class Exporter:
    def export_job_similarity_matrix(
        self,
        similarity_matrix: pd.DataFrame,
        department: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Export job similarity matrix, optionally filtered by department.
        
        Args:
            similarity_matrix: The similarity matrix DataFrame
            department: Optional department to filter by
            
        Returns:
            DataFrame containing the similarity matrix
        """
        if department:
            # Note: This method requires job_arch to be properly initialized
            # For now, return unfiltered matrix as this is legacy functionality
            # TODO: Implement proper department filtering when job_arch is available
            pass
        
        return similarity_matrix


class AnalyticsExporter:
    """
    Dedicated exporter for analytics tables with memory-efficient processing.
    
    Handles export of all analytics_* tables to individual CSV files with
    chunked processing for large tables and comprehensive progress tracking.
    """
    
    # Define analytics tables with their expected characteristics
    ANALYTICS_TABLES = {
        'analytics_bundle_characteristics': {'size_category': 'small', 'chunk_size': None},
        'analytics_job_defining_skills': {'size_category': 'medium', 'chunk_size': 5000},
        'analytics_job_families': {'size_category': 'small', 'chunk_size': None},
        'analytics_job_family_characteristics': {'size_category': 'small', 'chunk_size': None},
        'analytics_job_similarities': {'size_category': 'large', 'chunk_size': 10000},
        'analytics_movement_patterns': {'size_category': 'medium', 'chunk_size': 5000},
        'analytics_pathway_predictions': {'size_category': 'medium', 'chunk_size': 5000},
        'analytics_skill_bundles': {'size_category': 'small', 'chunk_size': None},
        'analytics_skill_demand_trends': {'size_category': 'small', 'chunk_size': None},
        'analytics_skill_rarity': {'size_category': 'small', 'chunk_size': None},
        'analytics_specialized_skills': {'size_category': 'small', 'chunk_size': None}
    }
    
    def __init__(self, db_path: str, output_directory: Optional[str] = None):
        """
        Initialize the analytics exporter.
        
        Args:
            db_path: Path to the SQLite database
            output_directory: Output directory for CSV files (defaults to 'exports/analytics')
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        # Set up output directory
        if output_directory:
            self.output_dir = Path(output_directory)
        else:
            self.output_dir = Path("exports") / "analytics"
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export timestamp for file naming
        self.export_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
        logger.info(f"Analytics exporter initialized - Database: {self.db_path}, Output: {self.output_dir}")
    
    def get_table_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about available analytics tables.
        
        Returns:
            Dictionary with table names and their metadata
        """
        table_info = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for table_name in self.ANALYTICS_TABLES.keys():
                    # Check if table exists and get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    
                    # Get column information
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    table_info[table_name] = {
                        'row_count': row_count,
                        'column_count': len(columns),
                        'columns': columns,
                        'size_category': self.ANALYTICS_TABLES[table_name]['size_category'],
                        'exists': True
                    }
                    
        except sqlite3.Error as e:
            logger.error(f"Error getting table info: {e}")
            # Mark tables as not existing if there's an error
            for table_name in self.ANALYTICS_TABLES.keys():
                table_info[table_name] = {
                    'row_count': 0,
                    'column_count': 0,
                    'columns': [],
                    'size_category': self.ANALYTICS_TABLES[table_name]['size_category'],
                    'exists': False,
                    'error': str(e)
                }
        
        return table_info
    
    def export_table_chunked(self, table_name: str, chunk_size: int) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Export a large table using chunked processing.
        
        Args:
            table_name: Name of the table to export
            chunk_size: Number of rows to process per chunk
            
        Returns:
            Tuple of (success, file_path, metadata)
        """
        output_file = self.output_dir / f"{table_name}_{self.export_timestamp}.csv"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get total row count for progress tracking
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_rows = cursor.fetchone()[0]
                
                if total_rows == 0:
                    logger.warning(f"Table {table_name} is empty, creating empty CSV")
                    # Create empty CSV with headers
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
                    empty_df = pd.DataFrame(columns=[desc[0] for desc in cursor.description])
                    empty_df.to_csv(output_file, index=False, encoding='utf-8')
                    
                    return True, str(output_file), {
                        'rows_exported': 0,
                        'chunks_processed': 0,
                        'file_size_mb': 0.0
                    }
                
                chunks_processed = 0
                total_chunks = (total_rows + chunk_size - 1) // chunk_size
                first_chunk = True
                
                print(f"   📊 Exporting {table_name}: {total_rows:,} rows in {total_chunks:,} chunks")
                
                for offset in range(0, total_rows, chunk_size):
                    query = f"SELECT * FROM {table_name} LIMIT {chunk_size} OFFSET {offset}"
                    chunk_df = pd.read_sql_query(query, conn)
                    
                    # Write chunk to CSV (append after first chunk)
                    chunk_df.to_csv(
                        output_file, 
                        mode='w' if first_chunk else 'a',
                        header=first_chunk,
                        index=False,
                        encoding='utf-8'
                    )
                    
                    chunks_processed += 1
                    first_chunk = False
                    
                    # Progress update for large tables
                    if total_chunks > 10:  # Only show progress for tables with many chunks
                        progress = (chunks_processed / total_chunks) * 100
                        print(f"      Progress: {progress:.1f}% ({chunks_processed}/{total_chunks} chunks)")
                
                # Get file size
                file_size_mb = output_file.stat().st_size / (1024 * 1024)
                
                return True, str(output_file), {
                    'rows_exported': total_rows,
                    'chunks_processed': chunks_processed,
                    'file_size_mb': file_size_mb
                }
                
        except Exception as e:
            logger.error(f"Error exporting {table_name}: {e}")
            return False, "", {'error': str(e)}
    
    def export_table_simple(self, table_name: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Export a small table in a single operation.
        
        Args:
            table_name: Name of the table to export
            
        Returns:
            Tuple of (success, file_path, metadata)
        """
        output_file = self.output_dir / f"{table_name}_{self.export_timestamp}.csv"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = f"SELECT * FROM {table_name}"
                df = pd.read_sql_query(query, conn)
                
                # Export to CSV
                df.to_csv(output_file, index=False, encoding='utf-8')
                
                # Get file size
                file_size_mb = output_file.stat().st_size / (1024 * 1024)
                
                print(f"   📄 Exported {table_name}: {len(df):,} rows")
                
                return True, str(output_file), {
                    'rows_exported': len(df),
                    'chunks_processed': 1,
                    'file_size_mb': file_size_mb
                }
                
        except Exception as e:
            logger.error(f"Error exporting {table_name}: {e}")
            return False, "", {'error': str(e)}
    
    def export_all_tables(self, selected_tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Export all or selected analytics tables to CSV files.
        
        Args:
            selected_tables: Optional list of specific tables to export
            
        Returns:
            Dictionary with export results and summary
        """
        if selected_tables is None:
            tables_to_export = list(self.ANALYTICS_TABLES.keys())
        else:
            tables_to_export = [t for t in selected_tables if t in self.ANALYTICS_TABLES]
        
        results = {}
        successful_exports = 0
        failed_exports = 0
        total_rows_exported = 0
        total_file_size_mb = 0.0
        
        print(f"\n🚀 Starting analytics export to: {self.output_dir}")
        print(f"📅 Export timestamp: {self.export_timestamp}")
        print(f"📊 Tables to export: {len(tables_to_export)}")
        print()
        
        for i, table_name in enumerate(tables_to_export, 1):
            print(f"[{i}/{len(tables_to_export)}] Processing {table_name}...")
            
            table_config = self.ANALYTICS_TABLES[table_name]
            chunk_size = table_config['chunk_size']
            
            if chunk_size:
                # Use chunked export for large tables
                success, file_path, metadata = self.export_table_chunked(table_name, chunk_size)
            else:
                # Use simple export for small tables
                success, file_path, metadata = self.export_table_simple(table_name)
            
            results[table_name] = {
                'success': success,
                'file_path': file_path,
                'metadata': metadata
            }
            
            if success:
                successful_exports += 1
                total_rows_exported += metadata.get('rows_exported', 0)
                total_file_size_mb += metadata.get('file_size_mb', 0.0)
            else:
                failed_exports += 1
                print(f"   ❌ Failed to export {table_name}: {metadata.get('error', 'Unknown error')}")
        
        # Generate summary
        summary = {
            'export_timestamp': self.export_timestamp,
            'output_directory': str(self.output_dir),
            'tables_requested': len(tables_to_export),
            'successful_exports': successful_exports,
            'failed_exports': failed_exports,
            'total_rows_exported': total_rows_exported,
            'total_file_size_mb': round(total_file_size_mb, 2),
            'results': results
        }
        
        return summary
    
    def export_single_table(self, table_name: str) -> Dict[str, Any]:
        """
        Export a single analytics table.
        
        Args:
            table_name: Name of the table to export
            
        Returns:
            Dictionary with export result
        """
        if table_name not in self.ANALYTICS_TABLES:
            return {
                'success': False,
                'error': f"Table '{table_name}' is not a valid analytics table",
                'available_tables': list(self.ANALYTICS_TABLES.keys())
            }
        
        summary = self.export_all_tables([table_name])
        result = summary['results'].get(table_name, {})
        result['summary'] = summary
        
        return result 
