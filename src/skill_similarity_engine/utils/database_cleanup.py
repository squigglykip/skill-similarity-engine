#!/usr/bin/env python3
"""
Database Cleanup Utilities
===========================

Utilities for cleaning up large temporary tables after analytics processing
to reduce database size and improve performance.

Focuses on removing tables that are only needed during intermediate processing
but consume significant storage space once analytics are complete.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DatabaseCleanupManager:
    """
    Manager for cleaning up unneeded database tables after analytics completion.
    
    Safely removes large intermediate tables that are no longer needed after
    analytics processing is complete, while preserving essential data.
    """
    
    # Tables that can be safely removed after analytics completion
    CLEANUP_TABLES = [
        'core_colleague_positions_history',  # Large historical position data (899,675 records)
        'core_position_timeline'             # Large timeline data (479,968 records)
    ]
    
    # Tables to preserve (never clean up)
    PROTECTED_TABLES = [
        'core_job_architecture',
        'core_skills_taxonomy', 
        'core_job_skill_requirements',
        'analytics_movement_patterns',
        'analytics_skill_demand_trends',
        'job_similarities',
        'jobs',
        'skills',
        'job_skills'
    ]
    
    def __init__(self, db_path: str):
        """
        Initialize the cleanup manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.cleanup_stats = {}
        
    def analyze_table_sizes(self) -> Dict[str, Dict]:
        """
        Analyze the size of tables in the database.
        
        Returns:
            Dictionary with table names and their size information
        """
        table_info = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    try:
                        # Get row count
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        row_count = cursor.fetchone()[0]
                        
                        # Get table size estimation using a more compatible approach
                        # Since pragma_page_list() isn't available in all SQLite versions,
                        # we'll estimate based on row count and average row size
                        
                        # Sample a few rows to estimate average row size
                        try:
                            cursor.execute(f"SELECT * FROM {table} LIMIT 100")
                            sample_rows = cursor.fetchall()
                            if sample_rows and len(sample_rows) > 0:
                                # Estimate average row size by serializing sample data
                                total_chars = sum(len(str(row)) for row in sample_rows[:10])
                                avg_row_size_bytes = (total_chars / min(len(sample_rows), 10)) * 1.5  # Factor for overhead
                                estimated_size_mb = (row_count * avg_row_size_bytes) / (1024 * 1024)
                            else:
                                estimated_size_mb = 0.0
                        except:
                            # Fallback: rough estimate based on row count
                            estimated_size_mb = (row_count * 200) / (1024 * 1024)  # Assume 200 bytes per row
                        
                        page_count = 0  # Not available without pragma_page_list
                        
                        table_info[table] = {
                            'row_count': row_count,
                            'page_count': page_count,
                            'estimated_size_mb': estimated_size_mb,
                            'can_cleanup': table.lower() in [t.lower() for t in self.CLEANUP_TABLES],
                            'is_protected': table.lower() in [t.lower() for t in self.PROTECTED_TABLES]
                        }
                        
                    except sqlite3.Error as e:
                        logger.warning(f"Could not analyze table {table}: {e}")
                        table_info[table] = {
                            'row_count': 0,
                            'page_count': 0,
                            'estimated_size_mb': 0,
                            'can_cleanup': False,
                            'is_protected': True,
                            'error': str(e)
                        }
                
        except Exception as e:
            logger.error(f"Failed to analyze table sizes: {e}")
            
        return table_info
    
    def get_cleanup_candidates(self) -> List[Tuple[str, Dict]]:
        """
        Get tables that are candidates for cleanup.
        
        Returns:
            List of (table_name, table_info) tuples for cleanup candidates
        """
        table_info = self.analyze_table_sizes()
        
        candidates = []
        for table_name, info in table_info.items():
            if info.get('can_cleanup', False) and info.get('row_count', 0) > 0:
                candidates.append((table_name, info))
        
        # Sort by size descending (largest tables first)
        candidates.sort(key=lambda x: x[1].get('estimated_size_mb', 0), reverse=True)
        
        return candidates
    
    def preview_cleanup(self) -> Dict:
        """
        Preview what would be cleaned up without actually performing cleanup.
        
        Returns:
            Dictionary with cleanup preview information
        """
        candidates = self.get_cleanup_candidates()
        
        total_rows_to_remove = sum(info['row_count'] for _, info in candidates)
        total_size_to_free_mb = sum(info['estimated_size_mb'] for _, info in candidates)
        
        preview = {
            'tables_to_cleanup': len(candidates),
            'total_rows_to_remove': total_rows_to_remove,
            'total_size_to_free_mb': total_size_to_free_mb,
            'cleanup_details': [
                {
                    'table_name': table_name,
                    'row_count': info['row_count'],
                    'estimated_size_mb': info['estimated_size_mb']
                }
                for table_name, info in candidates
            ]
        }
        
        return preview
    
    def perform_cleanup(self, confirm: bool = False) -> Dict:
        """
        Perform the actual cleanup of unneeded tables.
        
        Args:
            confirm: If True, actually perform the cleanup. If False, just preview.
            
        Returns:
            Dictionary with cleanup results
        """
        if not confirm:
            return self.preview_cleanup()
        
        candidates = self.get_cleanup_candidates()
        
        if not candidates:
            return {
                'success': True,
                'message': 'No tables need cleanup',
                'tables_cleaned': 0,
                'total_rows_removed': 0,
                'total_size_freed_mb': 0
            }
        
        cleaned_tables = []
        total_rows_removed = 0
        total_size_freed_mb = 0
        errors = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for table_name, info in candidates:
                    try:
                        logger.info(f"Cleaning up table: {table_name}")
                        
                        # Create backup of table schema in case of issues
                        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                        schema_backup = cursor.fetchone()
                        
                        # Drop the table
                        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                        
                        # Record cleanup stats
                        cleaned_tables.append({
                            'table_name': table_name,
                            'rows_removed': info['row_count'],
                            'size_freed_mb': info['estimated_size_mb'],
                            'schema_backup': schema_backup[0] if schema_backup else None
                        })
                        
                        total_rows_removed += info['row_count']
                        total_size_freed_mb += info['estimated_size_mb']
                        
                        logger.info(f"✅ Cleaned up {table_name}: {info['row_count']:,} rows, {info['estimated_size_mb']:.1f} MB")
                        
                    except sqlite3.Error as e:
                        error_msg = f"Failed to cleanup table {table_name}: {e}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                
                # Vacuum database to reclaim space
                if cleaned_tables:
                    logger.info("Running VACUUM to reclaim disk space...")
                    cursor.execute("VACUUM")
                    logger.info("✅ Database vacuum completed")
                
        except Exception as e:
            error_msg = f"Cleanup operation failed: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'errors': errors
            }
        
        # Store cleanup stats
        self.cleanup_stats = {
            'timestamp': self._get_timestamp(),
            'tables_cleaned': cleaned_tables,
            'total_rows_removed': total_rows_removed,
            'total_size_freed_mb': total_size_freed_mb,
            'errors': errors
        }
        
        success = len(errors) == 0
        
        return {
            'success': success,
            'message': f"Cleanup completed: {len(cleaned_tables)} tables, {total_rows_removed:,} rows, {total_size_freed_mb:.1f} MB freed",
            'tables_cleaned': len(cleaned_tables),
            'total_rows_removed': total_rows_removed,
            'total_size_freed_mb': total_size_freed_mb,
            'cleaned_tables': cleaned_tables,
            'errors': errors
        }
    
    def get_database_size_info(self) -> Dict:
        """
        Get overall database size information.
        
        Returns:
            Dictionary with database size information
        """
        try:
            # Get file size
            file_size_mb = self.db_path.stat().st_size / (1024 * 1024)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                try:
                    # Get page count and size
                    cursor.execute("PRAGMA page_count")
                    page_count = cursor.fetchone()[0]
                    
                    cursor.execute("PRAGMA page_size")
                    page_size = cursor.fetchone()[0]
                    
                    # Get freelist count (unused pages)
                    cursor.execute("PRAGMA freelist_count")
                    freelist_count = cursor.fetchone()[0]
                    
                    used_pages = page_count - freelist_count
                    used_size_mb = (used_pages * page_size) / (1024 * 1024)
                    free_size_mb = (freelist_count * page_size) / (1024 * 1024)
                    
                    return {
                        'file_size_mb': file_size_mb,
                        'total_pages': page_count,
                        'page_size': page_size,
                        'used_pages': used_pages,
                        'free_pages': freelist_count,
                        'used_size_mb': used_size_mb,
                        'free_size_mb': free_size_mb,
                        'database_path': str(self.db_path)
                    }
                except sqlite3.Error:
                    # Fallback if PRAGMA commands fail
                    return {
                        'file_size_mb': file_size_mb,
                        'total_pages': 0,
                        'page_size': 4096,  # Default
                        'used_pages': 0,
                        'free_pages': 0,
                        'used_size_mb': file_size_mb,
                        'free_size_mb': 0.0,
                        'database_path': str(self.db_path)
                    }
                
        except Exception as e:
            logger.error(f"Failed to get database size info: {e}")
            return {'error': str(e)}
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_cleanup_statistics(self) -> Dict:
        """
        Get statistics from the last cleanup operation.
        
        Returns:
            Dictionary with cleanup statistics or empty dict if no cleanup performed
        """
        return self.cleanup_stats.copy()


def cleanup_database_tables(db_path: str, confirm: bool = False) -> Dict:
    """
    Main entry point for database table cleanup.
    
    Args:
        db_path: Path to the SQLite database
        confirm: If True, actually perform cleanup. If False, preview only.
        
    Returns:
        Dictionary with cleanup results
    """
    manager = DatabaseCleanupManager(db_path)
    return manager.perform_cleanup(confirm=confirm)


def analyze_database_size(db_path: str) -> Dict:
    """
    Analyze database size and cleanup opportunities.
    
    Args:
        db_path: Path to the SQLite database
        
    Returns:
        Dictionary with size analysis
    """
    manager = DatabaseCleanupManager(db_path)
    
    size_info = manager.get_database_size_info()
    table_info = manager.analyze_table_sizes()
    cleanup_preview = manager.preview_cleanup()
    
    return {
        'database_size': size_info,
        'table_analysis': table_info,
        'cleanup_preview': cleanup_preview
    }


if __name__ == "__main__":
    """Test the cleanup functionality"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python database_cleanup.py <database_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    print("🧹 DATABASE CLEANUP ANALYSIS")
    print("="*50)
    
    # Analyze current state
    analysis = analyze_database_size(db_path)
    
    print(f"📊 Database Size Information:")
    size_info = analysis['database_size']
    if 'error' not in size_info:
        print(f"   → File Size: {size_info['file_size_mb']:.1f} MB")
        print(f"   → Used Space: {size_info['used_size_mb']:.1f} MB")
        print(f"   → Free Space: {size_info['free_size_mb']:.1f} MB")
    
    print(f"\n🗂️  Cleanup Opportunities:")
    preview = analysis['cleanup_preview']
    if preview['tables_to_cleanup'] > 0:
        print(f"   → Tables to cleanup: {preview['tables_to_cleanup']}")
        print(f"   → Rows to remove: {preview['total_rows_to_remove']:,}")
        print(f"   → Space to free: {preview['total_size_to_free_mb']:.1f} MB")
        
        print(f"\n📋 Cleanup Details:")
        for detail in preview['cleanup_details']:
            print(f"   • {detail['table_name']}: {detail['row_count']:,} rows ({detail['estimated_size_mb']:.1f} MB)")
    else:
        print("   → No tables need cleanup")