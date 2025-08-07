#!/usr/bin/env python3
"""
Generate Comprehensive SQLite Schema Documentation
=================================================

This script analyzes the NAB Skill Similarity Engine SQLite database and generates
comprehensive documentation including:
- Table schemas with column details
- Relationships and foreign keys
- Data statistics and sample records
- Index information
- Query patterns and examples
- Mermaid ER diagrams
- Cross-table relationship analysis
- Data quality assessments
- Comprehensive content inspection

Usage:
    python scripts/generate_sqlite_schema_docs.py

Output:
    docs/sqlite_schema_design.md (updated)
"""

import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import json
import re
from collections import defaultdict, Counter

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class SQLiteSchemaAnalyzer:
    """Comprehensive SQLite database schema analyzer and documenter."""
    
    def __init__(self, db_path: str):
        """Initialize with database path."""
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get basic database information."""
        stat = self.db_path.stat()
        
        # Get SQLite version and settings
        cursor = self.conn.execute("SELECT sqlite_version()")
        sqlite_version = cursor.fetchone()[0]
        
        # Get database page size and count
        cursor = self.conn.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        
        cursor = self.conn.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        
        # Get foreign key enforcement status
        cursor = self.conn.execute("PRAGMA foreign_keys")
        foreign_keys_enabled = bool(cursor.fetchone()[0])
        
        return {
            'file_path': str(self.db_path),
            'file_size_mb': round(stat.st_size / (1024 * 1024), 2),
            'file_size_bytes': stat.st_size,
            'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'analysis_date': datetime.now().isoformat(),
            'sqlite_version': sqlite_version,
            'page_size': page_size,
            'page_count': page_count,
            'database_size_pages': page_count,
            'foreign_keys_enabled': foreign_keys_enabled
        }
    
    def get_tables_info(self) -> List[Dict[str, Any]]:
        """Get comprehensive information about all tables."""
        tables = []
        
        # Get all table names
        cursor = self.conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        table_names = [row[0] for row in cursor.fetchall()]
        
        for table_name in table_names:
            table_info = self._analyze_table(table_name)
            tables.append(table_info)
            
        return tables
    
    def _analyze_table(self, table_name: str) -> Dict[str, Any]:
        """Analyze a single table comprehensively."""
        # Get table schema
        cursor = self.conn.execute(f"PRAGMA table_info({table_name})")
        columns = []
        primary_keys = []
        
        for row in cursor.fetchall():
            col_info = {
                'name': row[1],
                'type': row[2],
                'not_null': bool(row[3]),
                'default_value': row[4],
                'is_primary_key': bool(row[5])
            }
            columns.append(col_info)
            if col_info['is_primary_key']:
                primary_keys.append(col_info['name'])
        
        # Get foreign keys
        cursor = self.conn.execute(f"PRAGMA foreign_key_list({table_name})")
        foreign_keys = []
        for row in cursor.fetchall():
            foreign_keys.append({
                'column': row[3],
                'references_table': row[2],
                'references_column': row[4]
            })
        
        # Get row count
        cursor = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Get table size information
        cursor = self.conn.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if cursor.fetchone()[0] > 0:
            try:
                # Get approximate table size
                cursor = self.conn.execute(f"SELECT SUM(pgsize) FROM dbstat WHERE name='{table_name}'")
                table_size = cursor.fetchone()[0] or 0
            except sqlite3.Error:
                table_size = 0
        else:
            table_size = 0
        
        # Get sample data (first 10 rows)
        try:
            cursor = self.conn.execute(f"SELECT * FROM {table_name} LIMIT 10")
            sample_rows = [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            sample_rows = []
        
        # Get column statistics for key columns
        column_stats = self._get_column_statistics(table_name, columns)
        
        # Get data quality metrics
        data_quality = self._get_data_quality_metrics(table_name, columns)
        
        return {
            'name': table_name,
            'columns': columns,
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys,
            'row_count': row_count,
            'table_size_bytes': table_size,
            'sample_rows': sample_rows,
            'column_statistics': column_stats,
            'data_quality': data_quality
        }
    
    def _get_column_statistics(self, table_name: str, columns: List[Dict]) -> Dict[str, Any]:
        """Get statistics for important columns."""
        stats = {}
        
        for col in columns:
            col_name = col['name']
            col_type = col['type'].upper()
            
            try:
                # Handle column names with spaces or special characters
                quoted_col_name = f'"{col_name}"' if ' ' in col_name or '-' in col_name else col_name
                
                if 'TEXT' in col_type or 'VARCHAR' in col_type:
                    # Text column statistics
                    cursor = self.conn.execute(f"""
                        SELECT 
                            COUNT(DISTINCT {quoted_col_name}) as unique_count,
                            COUNT({quoted_col_name}) as non_null_count,
                            MIN(LENGTH({quoted_col_name})) as min_length,
                            MAX(LENGTH({quoted_col_name})) as max_length,
                            AVG(LENGTH({quoted_col_name})) as avg_length
                        FROM {table_name}
                        WHERE {quoted_col_name} IS NOT NULL
                    """)
                    row = cursor.fetchone()
                    if row:
                        stats[col_name] = {
                            'type': 'text',
                            'unique_values': row[0],
                            'non_null_count': row[1],
                            'min_length': row[2],
                            'max_length': row[3],
                            'avg_length': round(row[4], 2) if row[4] else 0
                        }
                        
                elif 'REAL' in col_type or 'NUMERIC' in col_type or 'DECIMAL' in col_type:
                    # Numeric column statistics
                    cursor = self.conn.execute(f"""
                        SELECT 
                            COUNT(DISTINCT {quoted_col_name}) as unique_count,
                            COUNT({quoted_col_name}) as non_null_count,
                            MIN({quoted_col_name}) as min_value,
                            MAX({quoted_col_name}) as max_value,
                            AVG({quoted_col_name}) as avg_value
                        FROM {table_name}
                        WHERE {quoted_col_name} IS NOT NULL
                    """)
                    row = cursor.fetchone()
                    if row:
                        stats[col_name] = {
                            'type': 'numeric',
                            'unique_values': row[0],
                            'non_null_count': row[1],
                            'min_value': row[2],
                            'max_value': row[3],
                            'avg_value': round(row[4], 4) if row[4] else 0
                        }
                        
                elif 'INTEGER' in col_type:
                    # Integer column statistics
                    cursor = self.conn.execute(f"""
                        SELECT 
                            COUNT(DISTINCT {quoted_col_name}) as unique_count,
                            COUNT({quoted_col_name}) as non_null_count,
                            MIN({quoted_col_name}) as min_value,
                            MAX({quoted_col_name}) as max_value
                        FROM {table_name}
                        WHERE {quoted_col_name} IS NOT NULL
                    """)
                    row = cursor.fetchone()
                    if row:
                        stats[col_name] = {
                            'type': 'integer',
                            'unique_values': row[0],
                            'non_null_count': row[1],
                            'min_value': row[2],
                            'max_value': row[3]
                        }
                        
            except sqlite3.Error:
                # Skip columns that cause errors
                continue
                
        return stats
    
    def _get_data_quality_metrics(self, table_name: str, columns: List[Dict]) -> Dict[str, Any]:
        """Get data quality metrics for a table."""
        quality_metrics = {
            'completeness': {},
            'consistency': {},
            'duplicates': {},
            'outliers': {}
        }
        
        try:
            # Get total row count
            cursor = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_rows = cursor.fetchone()[0]
            
            if total_rows == 0:
                return quality_metrics
            
            # Check completeness (null values)
            for col in columns:
                col_name = col['name']
                quoted_col_name = f'"{col_name}"' if ' ' in col_name or '-' in col_name else col_name
                
                try:
                    cursor = self.conn.execute(f"""
                        SELECT 
                            COUNT(*) as total,
                            COUNT({quoted_col_name}) as non_null,
                            COUNT(*) - COUNT({quoted_col_name}) as null_count
                        FROM {table_name}
                    """)
                    row = cursor.fetchone()
                    
                    quality_metrics['completeness'][col_name] = {
                        'total_rows': row[0],
                        'non_null_count': row[1],
                        'null_count': row[2],
                        'completeness_percentage': round((row[1] / row[0]) * 100, 2) if row[0] > 0 else 0
                    }
                except sqlite3.Error:
                    continue
            
            # Check for duplicate rows
            try:
                # Create a query to find duplicate rows
                col_names = [f'"{col["name"]}"' if ' ' in col["name"] or '-' in col["name"] else col["name"] for col in columns]
                col_list = ', '.join(col_names)
                
                cursor = self.conn.execute(f"""
                    SELECT COUNT(*) as duplicate_count
                    FROM (
                        SELECT {col_list}, COUNT(*) as cnt
                        FROM {table_name}
                        GROUP BY {col_list}
                        HAVING COUNT(*) > 1
                    )
                """)
                duplicate_groups = cursor.fetchone()[0]
                
                quality_metrics['duplicates'] = {
                    'duplicate_groups': duplicate_groups,
                    'has_duplicates': duplicate_groups > 0
                }
            except sqlite3.Error:
                quality_metrics['duplicates'] = {'error': 'Could not check duplicates', 'duplicate_groups': 0, 'has_duplicates': False}
                
        except sqlite3.Error as e:
            quality_metrics['error'] = {'message': str(e)}
            
        return quality_metrics
    
    def get_cross_table_relationships(self, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze relationships between tables."""
        relationships = {
            'foreign_key_relationships': [],
            'potential_relationships': [],
            'orphaned_records': {},
            'referential_integrity': {}
        }
        
        # Collect all foreign key relationships
        for table in tables:
            for fk in table['foreign_keys']:
                relationships['foreign_key_relationships'].append({
                    'source_table': table['name'],
                    'source_column': fk['column'],
                    'target_table': fk['references_table'],
                    'target_column': fk['references_column']
                })
        
        # Check for potential relationships based on column names
        for table in tables:
            for col in table['columns']:
                col_name = col['name'].lower()
                
                # Look for ID columns that might reference other tables
                if 'id' in col_name or col_name.endswith('_id'):
                    # Check if this might reference another table
                    potential_table = col_name.replace('_id', '').replace('id', '')
                    
                    for other_table in tables:
                        if other_table['name'] != table['name']:
                            # Check if there's a matching table or column
                            if (potential_table in other_table['name'].lower() or 
                                any(potential_table in other_col['name'].lower() for other_col in other_table['columns'])):
                                
                                # Check if this isn't already a declared foreign key
                                is_declared_fk = any(
                                    fk['column'] == col['name'] and fk['references_table'] == other_table['name']
                                    for fk in table['foreign_keys']
                                )
                                
                                if not is_declared_fk:
                                    relationships['potential_relationships'].append({
                                        'source_table': table['name'],
                                        'source_column': col['name'],
                                        'potential_target_table': other_table['name'],
                                        'confidence': 'medium'
                                    })
        
        # Check referential integrity for declared foreign keys
        for fk_rel in relationships['foreign_key_relationships']:
            try:
                source_table = fk_rel['source_table']
                source_col = fk_rel['source_column']
                target_table = fk_rel['target_table']
                target_col = fk_rel['target_column']
                
                # Quote column names if they contain spaces or special characters
                quoted_source_col = f'"{source_col}"' if ' ' in source_col or '-' in source_col else source_col
                quoted_target_col = f'"{target_col}"' if ' ' in target_col or '-' in target_col else target_col
                
                # Check for orphaned records (foreign key values that don't exist in target table)
                cursor = self.conn.execute(f"""
                    SELECT COUNT(*) as orphaned_count
                    FROM {source_table} s
                    WHERE s.{quoted_source_col} IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1 FROM {target_table} t 
                        WHERE t.{quoted_target_col} = s.{quoted_source_col}
                    )
                """)
                orphaned_count = cursor.fetchone()[0]
                
                relationships['referential_integrity'][f"{source_table}.{source_col}"] = {
                    'target': f"{target_table}.{target_col}",
                    'orphaned_records': orphaned_count,
                    'has_orphans': orphaned_count > 0
                }
                
            except sqlite3.Error:
                relationships['referential_integrity'][f"{source_table}.{source_col}"] = {
                    'error': 'Could not check referential integrity'
                }
        
        return relationships
    
    def get_comprehensive_data_analysis(self, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform comprehensive data analysis across all tables."""
        analysis = {
            'data_distribution': {},
            'key_metrics': {},
            'business_insights': {},
            'data_patterns': {}
        }
        
        # Analyze key business tables (using production table names)
        business_tables = {
            'core_job_architecture': ['JobProfile', 'JobFamily', 'JobFamilyGroup'],
            'core_skills_taxonomy': ['Skill_Name', 'Category', 'SkillType'],
            'core_workforce_current': ['Division', 'Business_Unit', 'Location'],
            'analytics_career_pathways': ['career_move_type', 'similarity_score'],
            'analytics_job_similarities': ['similarity_score'],
            'core_colleague_positions_history': ['Employee Number', 'Position Number'],
            'analytics_movement_patterns': ['movement_pattern', 'movement_count']
        }
        
        for table_name, key_columns in business_tables.items():
            # Check if table exists
            table_exists = any(table['name'] == table_name for table in tables)
            if not table_exists:
                continue
                
            table_analysis = {}
            
            for column in key_columns:
                try:
                    # Get value distribution
                    quoted_col = f'"{column}"' if ' ' in column or '-' in column else column
                    cursor = self.conn.execute(f"""
                        SELECT {quoted_col} as value, COUNT(*) as count
                        FROM {table_name}
                        WHERE {quoted_col} IS NOT NULL
                        GROUP BY {quoted_col}
                        ORDER BY count DESC
                        LIMIT 20
                    """)
                    
                    distribution = [(row[0], row[1]) for row in cursor.fetchall()]
                    table_analysis[column] = {
                        'distribution': distribution,
                        'unique_values': len(distribution)
                    }
                    
                except sqlite3.Error:
                    continue
            
            if table_analysis:
                analysis['data_distribution'][table_name] = table_analysis
        
        # Calculate key business metrics (using production table names)
        try:
            # Job metrics
            cursor = self.conn.execute("SELECT COUNT(DISTINCT JobProfileID) FROM core_job_architecture")
            result = cursor.fetchone()
            total_jobs = result[0] if result else 0
            
            cursor = self.conn.execute("SELECT COUNT(DISTINCT JobFamily) FROM core_job_architecture")
            result = cursor.fetchone()
            total_job_families = result[0] if result else 0
            
            # Skills metrics
            cursor = self.conn.execute("SELECT COUNT(DISTINCT Skill_ID) FROM core_skills_taxonomy")
            result = cursor.fetchone()
            total_skills = result[0] if result else 0
            
            # Position metrics (try both possible tables)
            total_positions = 0
            try:
                cursor = self.conn.execute("SELECT COUNT(DISTINCT \"Position Number\") FROM core_workforce_current")
                result = cursor.fetchone()
                total_positions = result[0] if result else 0
            except sqlite3.Error:
                try:
                    cursor = self.conn.execute("SELECT COUNT(DISTINCT \"Position Number\") FROM core_colleague_positions_history")
                    result = cursor.fetchone()
                    total_positions = result[0] if result else 0
                except sqlite3.Error:
                    total_positions = 0
            
            analysis['key_metrics'] = {
                'total_jobs': total_jobs,
                'total_job_families': total_job_families,
                'total_skills': total_skills,
                'total_positions': total_positions
            }
            
        except sqlite3.Error:
            analysis['key_metrics'] = {'error': 'Could not calculate key metrics'}
        
        # Look for interesting data patterns
        try:
            # Check for movement analysis data (try production table names)
            movement_count = 0
            try:
                cursor = self.conn.execute("SELECT COUNT(*) FROM core_colleague_positions_history")
                result = cursor.fetchone()
                movement_count = result[0] if result else 0
            except sqlite3.Error:
                try:
                    cursor = self.conn.execute("SELECT COUNT(*) FROM colleague_movements")
                    result = cursor.fetchone()
                    movement_count = result[0] if result else 0
                except sqlite3.Error:
                    movement_count = 0
            
            if movement_count > 0:
                # Analyze movement patterns
                cursor = self.conn.execute("""
                    SELECT movement_type, COUNT(*) as count
                    FROM colleague_movements
                    GROUP BY movement_type
                    ORDER BY count DESC
                """)
                movement_patterns = cursor.fetchall()
                
                analysis['data_patterns']['movement_analysis'] = {
                    'total_movements': movement_count,
                    'movement_types': [(row[0], row[1]) for row in movement_patterns]
                }
            
            # Check career pathways effectiveness (try production table names)
            pathway_count = 0
            try:
                cursor = self.conn.execute("SELECT COUNT(*) FROM analytics_career_pathways")
                result = cursor.fetchone()
                pathway_count = result[0] if result else 0
            except sqlite3.Error:
                try:
                    cursor = self.conn.execute("SELECT COUNT(*) FROM career_pathways")
                    result = cursor.fetchone()
                    pathway_count = result[0] if result else 0
                except sqlite3.Error:
                    pathway_count = 0
            
            if pathway_count > 0:
                cursor = self.conn.execute("""
                    SELECT 
                        career_move_type,
                        COUNT(*) as count,
                        AVG(similarity_score) as avg_similarity,
                        MIN(similarity_score) as min_similarity,
                        MAX(similarity_score) as max_similarity
                    FROM career_pathways
                    GROUP BY career_move_type
                    ORDER BY count DESC
                """)
                pathway_analysis = cursor.fetchall()
                
                analysis['data_patterns']['career_pathways'] = {
                    'total_pathways': pathway_count,
                    'pathway_types': [
                        {
                            'type': row[0],
                            'count': row[1],
                            'avg_similarity': round(row[2], 4),
                            'min_similarity': round(row[3], 4),
                            'max_similarity': round(row[4], 4)
                        }
                        for row in pathway_analysis
                    ]
                }
                
        except sqlite3.Error:
            pass
        
        return analysis
    
    def get_query_performance_analysis(self, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze query performance characteristics."""
        performance_analysis = {
            'table_sizes': {},
            'index_coverage': {},
            'query_recommendations': []
        }
        
        # Analyze table sizes and performance characteristics
        for table in tables:
            table_name = table['name']
            row_count = table['row_count']
            
            performance_analysis['table_sizes'][table_name] = {
                'row_count': row_count,
                'size_category': self._categorize_table_size(row_count),
                'performance_impact': self._assess_performance_impact(row_count)
            }
        
        # Check index coverage
        indexes = self.get_indexes_info()
        index_coverage = {}
        
        for table in tables:
            table_name = table['name']
            table_indexes = [idx for idx in indexes if idx['table'] == table_name]
            
            # Check if primary key columns are indexed
            pk_indexed = len(table['primary_keys']) > 0  # Primary keys are automatically indexed
            
            # Check if foreign key columns are indexed
            fk_columns = [fk['column'] for fk in table['foreign_keys']]
            fk_indexed = []
            
            for fk_col in fk_columns:
                is_indexed = any(fk_col in idx['sql'] for idx in table_indexes if idx['sql'])
                fk_indexed.append({'column': fk_col, 'indexed': is_indexed})
            
            index_coverage[table_name] = {
                'total_indexes': len(table_indexes),
                'primary_key_indexed': pk_indexed,
                'foreign_key_coverage': fk_indexed
            }
        
        performance_analysis['index_coverage'] = index_coverage
        
        # Generate query recommendations
        recommendations = []
        
        # Check for large tables without proper indexing
        for table in tables:
            if table['row_count'] > 10000:  # Large table threshold
                table_indexes = [idx for idx in indexes if idx['table'] == table['name']]
                if len(table_indexes) < 2:  # Minimal indexing
                    recommendations.append({
                        'type': 'indexing',
                        'table': table['name'],
                        'issue': f"Large table ({table['row_count']:,} rows) with minimal indexing",
                        'recommendation': "Consider adding indexes on frequently queried columns"
                    })
        
        # Check for foreign keys without indexes
        for table in tables:
            for fk in table['foreign_keys']:
                fk_col = fk['column']
                table_indexes = [idx for idx in indexes if idx['table'] == table['name']]
                is_indexed = any(fk_col in idx['sql'] for idx in table_indexes if idx['sql'])
                
                if not is_indexed and table['row_count'] > 1000:
                    recommendations.append({
                        'type': 'foreign_key_indexing',
                        'table': table['name'],
                        'column': fk_col,
                        'issue': f"Foreign key column '{fk_col}' not indexed",
                        'recommendation': f"CREATE INDEX idx_{table['name']}_{fk_col} ON {table['name']}({fk_col})"
                    })
        
        performance_analysis['query_recommendations'] = recommendations
        
        return performance_analysis
    
    def _categorize_table_size(self, row_count: int) -> str:
        """Categorize table size for performance analysis."""
        if row_count < 1000:
            return 'small'
        elif row_count < 100000:
            return 'medium'
        elif row_count < 1000000:
            return 'large'
        else:
            return 'very_large'
    
    def _assess_performance_impact(self, row_count: int) -> str:
        """Assess performance impact based on table size."""
        if row_count < 1000:
            return 'minimal'
        elif row_count < 10000:
            return 'low'
        elif row_count < 100000:
            return 'moderate'
        else:
            return 'high'
    
    def get_indexes_info(self) -> List[Dict[str, Any]]:
        """Get information about database indexes."""
        cursor = self.conn.execute("""
            SELECT name, tbl_name, sql 
            FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
            ORDER BY tbl_name, name
        """)
        
        indexes = []
        for row in cursor.fetchall():
            indexes.append({
                'name': row[0],
                'table': row[1],
                'sql': row[2]
            })
            
        return indexes
    
    def get_top_values_for_key_columns(self) -> Dict[str, List[Tuple[str, int]]]:
        """Get top values for key categorical columns."""
        key_columns = {
            'core_job_architecture': ['JobFamily', 'JobFamilyGroup'],
            'core_workforce_current': ['Division', 'Business_Unit', 'Location'],
            'core_skills_taxonomy': ['Category', 'SkillType'],
            'analytics_career_pathways': ['career_move_type'],
            'core_colleague_positions_history': ['Employee Number', 'Position Number'],
            'analytics_movement_patterns': ['movement_pattern']
        }
        
        top_values = {}
        
        for table, columns in key_columns.items():
            # Check if table exists
            cursor = self.conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table,))
            
            if not cursor.fetchone():
                continue
                
            for column in columns:
                try:
                    quoted_col = f'"{column}"' if ' ' in column or '-' in column else column
                    cursor = self.conn.execute(f"""
                        SELECT {quoted_col}, COUNT(*) as count
                        FROM {table}
                        WHERE {quoted_col} IS NOT NULL AND {quoted_col} != ''
                        GROUP BY {quoted_col}
                        ORDER BY count DESC
                        LIMIT 15
                    """)
                    
                    results = cursor.fetchall()
                    if results:
                        top_values[f"{table}.{column}"] = [(row[0], row[1]) for row in results]
                        
                except sqlite3.Error:
                    continue
                    
        return top_values
    
    def get_sample_data_for_all_columns(self) -> Dict[str, Dict[str, List[Any]]]:
        """Get sample data for all columns in all tables."""
        sample_data = {}
        
        # Get all table names
        cursor = self.conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        table_names = [row[0] for row in cursor.fetchall()]
        
        for table_name in table_names:
            sample_data[table_name] = {}
            
            # Get column names
            cursor = self.conn.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            
            for column in columns:
                try:
                    # Handle column names with spaces or special characters
                    quoted_col_name = f'"{column}"' if ' ' in column or '-' in column else column
                    
                    # Get 15 sample values (non-null, distinct)
                    cursor = self.conn.execute(f"""
                        SELECT DISTINCT {quoted_col_name}
                        FROM {table_name}
                        WHERE {quoted_col_name} IS NOT NULL
                        ORDER BY {quoted_col_name}
                        LIMIT 15
                    """)
                    
                    values = [row[0] for row in cursor.fetchall()]
                    sample_data[table_name][column] = values
                    
                except sqlite3.Error:
                    sample_data[table_name][column] = []
                    
        return sample_data
    
    def generate_mermaid_er_diagram(self, tables: List[Dict[str, Any]]) -> str:
        """Generate Mermaid ER diagram from table information."""
        mermaid = ["erDiagram"]
        
        # Add table definitions
        for table in tables:
            table_name = table['name'].upper()
            mermaid.append(f"    {table_name} {{")
            
            for col in table['columns']:
                col_type = col['type'].lower()
                col_name = col['name'].replace(' ', '_').replace('-', '_')
                
                # Add primary key indicator
                pk_indicator = " PK" if col['is_primary_key'] else ""
                
                # Add foreign key indicator
                fk_indicator = ""
                for fk in table['foreign_keys']:
                    if fk['column'] == col['name']:
                        fk_indicator = " FK"
                        break
                
                mermaid.append(f"        {col_type} {col_name}{pk_indicator}{fk_indicator}")
            
            mermaid.append("    }")
            mermaid.append("")
        
        # Add relationships
        for table in tables:
            for fk in table['foreign_keys']:
                source_table = table['name'].upper()
                target_table = fk['references_table'].upper()
                relationship_label = fk['column'].replace(' ', '_').replace('-', '_')
                mermaid.append(f"    {target_table} ||--o{{ {source_table} : \"{relationship_label}\"")
        
        return "\n".join(mermaid)


def generate_schema_documentation(db_path: str, output_path: str) -> None:
    """Generate comprehensive schema documentation."""
    
    with SQLiteSchemaAnalyzer(db_path) as analyzer:
        # Gather all information
        print("🔍 Analyzing database structure...")
        db_info = analyzer.get_database_info()
        tables = analyzer.get_tables_info()
        indexes = analyzer.get_indexes_info()
        
        print("📊 Gathering data distributions...")
        top_values = analyzer.get_top_values_for_key_columns()
        sample_data = analyzer.get_sample_data_for_all_columns()
        
        print("🔗 Analyzing relationships...")
        relationships = analyzer.get_cross_table_relationships(tables)
        
        print("📈 Performing comprehensive data analysis...")
        data_analysis = analyzer.get_comprehensive_data_analysis(tables)
        
        print("⚡ Analyzing query performance...")
        performance_analysis = analyzer.get_query_performance_analysis(tables)
        
        print("🎨 Generating ER diagram...")
        mermaid_diagram = analyzer.generate_mermaid_er_diagram(tables)
        
        # Generate markdown documentation
        doc_lines = []
        
        # Header
        doc_lines.extend([
            "# SQLite Schema Design for NAB Skill Similarity Engine",
            "## Workforce Intelligence Database",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Database File**: `{db_info['file_path']}`",
            f"**Database Size**: {db_info['file_size_mb']} MB",
            f"**SQLite Version**: {db_info['sqlite_version']}",
            f"**Page Size**: {db_info['page_size']} bytes",
            f"**Total Pages**: {db_info['page_count']:,}",
            f"**Foreign Keys**: {'Enabled' if db_info['foreign_keys_enabled'] else 'Disabled'}",
            f"**Last Modified**: {db_info['last_modified']}",
            "",
            "---",
            "",
            "## Overview",
            "",
            "This document provides comprehensive schema documentation for the NAB Skill Similarity Engine SQLite database.",
            "The database integrates job architecture, skill taxonomies, workforce context, movement analysis, and pre-computed similarities",
            "to support career pathway analysis, workforce planning, and strategic workforce intelligence.",
            "",
            "## Quick Reference for LLMs",
            "",
            "**Core Tables for Query Development:**",
            ""
        ])
        
        # Generate quick reference dynamically (using production table names)
        core_tables = {
            'core_job_architecture': 'JobProfileID, JobProfile, JobFamily, JobFamilyGroup',
            'analytics_career_pathways': 'source_job_id, target_job_id, similarity_rank, similarity_score, career_move_type',
            'analytics_job_similarities': 'job_from, job_to, similarity_score',
            'core_workforce_current': 'JobProfileID, Division, Business_Unit, Location, Team',
            'core_job_skill_requirements': 'JobProfileID, Skill_ID, Skill_Weight',
            'core_skills_taxonomy': 'Skill_ID, Skill_Name, Category, SkillType',
            'core_colleague_positions_history': 'Employee Number, Position Number, Week Ending, PosIDLookupKey',
            'analytics_movement_patterns': 'movement_pattern, movement_count, month, avg_days_in_position'
        }
        
        for table in tables:
            table_name = table['name']
            if table_name in core_tables:
                row_count = table['row_count']
                key_columns = core_tables[table_name]
                doc_lines.append(f"- **`{table_name}`** ({row_count:,} records) - {key_columns}")
        
        doc_lines.extend([
            "",
            "**Key Relationships:**",
            "- `jobs.JobProfileID` â†’ `career_pathways.source_job_id/target_job_id`",
            "- `jobs.JobProfileID` â†’ `job_similarities.job_from/job_to`",
            "- `jobs.JobProfileID` â†’ `positions.JobProfileID`",
            "- `jobs.JobProfileID` â†’ `job_skills.JobProfileID`",
            "- `skills.Skill_ID` â†’ `job_skills.Skill_ID`",
            "",
            "**Critical for D3 Tree Queries:**",
            "- Use `career_pathways` table for pre-computed relationships (fast!)",
            "- `similarity_rank` 1-12 gives top pathways per job",
            "- `career_move_type`: 'lateral', 'progression', 'cross_family'",
            "- Handle quoted column names: `\"Position Number\"`, `\"Business_Unit\"`",
            "",
            "---",
            "",
            "## Database Statistics",
            "",
            f"- **Total Tables**: {len(tables)}",
            f"- **Total Records**: {sum(table['row_count'] for table in tables):,}",
            f"- **Total Indexes**: {len(indexes)}",
            f"- **Database Size**: {db_info['file_size_mb']} MB",
            ""
        ])
        
        # Add key business metrics
        if 'key_metrics' in data_analysis and data_analysis['key_metrics']:
            metrics = data_analysis['key_metrics']
            doc_lines.extend([
                "### Key Business Metrics",
                ""
            ])
            
            if 'total_jobs' in metrics:
                doc_lines.append(f"- **Total Job Profiles**: {metrics['total_jobs']:,}")
            if 'total_job_families' in metrics:
                doc_lines.append(f"- **Total Job Families**: {metrics['total_job_families']:,}")
            if 'total_skills' in metrics:
                doc_lines.append(f"- **Total Skills**: {metrics['total_skills']:,}")
            if 'total_positions' in metrics:
                doc_lines.append(f"- **Total Positions**: {metrics['total_positions']:,}")
            
            doc_lines.append("")
        
        # Add movement analysis summary if available
        if 'data_patterns' in data_analysis and 'movement_analysis' in data_analysis['data_patterns']:
            movement_data = data_analysis['data_patterns']['movement_analysis']
            doc_lines.extend([
                "### Movement Analysis Summary",
                "",
                f"- **Total Movements Tracked**: {movement_data['total_movements']:,}",
                "- **Movement Types**:"
            ])
            
            for move_type, count in movement_data['movement_types'][:5]:  # Top 5
                doc_lines.append(f"  - {move_type}: {count:,}")
            
            doc_lines.append("")
        
        # Add career pathways summary if available
        if 'data_patterns' in data_analysis and 'career_pathways' in data_analysis['data_patterns']:
            pathway_data = data_analysis['data_patterns']['career_pathways']
            doc_lines.extend([
                "### Career Pathways Summary",
                "",
                f"- **Total Career Pathways**: {pathway_data['total_pathways']:,}",
                "- **Pathway Types**:"
            ])
            
            for pathway_type in pathway_data['pathway_types']:
                doc_lines.append(f"  - {pathway_type['type']}: {pathway_type['count']:,} pathways (avg similarity: {pathway_type['avg_similarity']})")
            
            doc_lines.append("")
        
        # Add relationship analysis
        if relationships:
            doc_lines.extend([
                "## Relationship Analysis",
                "",
                f"### Foreign Key Relationships ({len(relationships['foreign_key_relationships'])})",
                ""
            ])
            
            for rel in relationships['foreign_key_relationships']:
                doc_lines.append(f"- `{rel['source_table']}.{rel['source_column']}` → `{rel['target_table']}.{rel['target_column']}`")
            
            doc_lines.append("")
            
            # Add referential integrity check
            if 'referential_integrity' in relationships and relationships['referential_integrity']:
                doc_lines.extend([
                    "### Referential Integrity Check",
                    ""
                ])
                
                integrity_issues = []
                for rel_key, integrity_info in relationships['referential_integrity'].items():
                    if integrity_info.get('has_orphans', False):
                        integrity_issues.append(f"- ⚠️ **{rel_key}**: {integrity_info['orphaned_records']} orphaned records")
                    else:
                        integrity_issues.append(f"- ✅ **{rel_key}**: No orphaned records")
                
                if integrity_issues:
                    doc_lines.extend(integrity_issues)
                    doc_lines.append("")
        
        # Add performance analysis
        if performance_analysis:
            doc_lines.extend([
                "## Performance Analysis",
                "",
                "### Table Size Categories",
                ""
            ])
            
            size_categories = defaultdict(list)
            for table_name, size_info in performance_analysis['table_sizes'].items():
                size_categories[size_info['size_category']].append((table_name, size_info['row_count']))
            
            for category in ['small', 'medium', 'large', 'very_large']:
                if category in size_categories:
                    doc_lines.append(f"**{category.replace('_', ' ').title()} Tables:**")
                    for table_name, row_count in size_categories[category]:
                        doc_lines.append(f"- {table_name}: {row_count:,} rows")
                    doc_lines.append("")
            
            # Add query recommendations
            if 'query_recommendations' in performance_analysis and performance_analysis['query_recommendations']:
                doc_lines.extend([
                    "### Query Optimization Recommendations",
                    ""
                ])
                
                for rec in performance_analysis['query_recommendations']:
                    doc_lines.append(f"- **{rec['type']}**: {rec['issue']}")
                    if 'recommendation' in rec:
                        doc_lines.append(f"  - Recommendation: {rec['recommendation']}")
                
                doc_lines.append("")
        
        doc_lines.extend([
            "## Entity Relationship Diagram",
            "",
            "```mermaid",
            mermaid_diagram,
            "```",
            "",
            "---",
            "",
            "## Table Definitions",
            ""
        ])
        
        # Table documentation
        for i, table in enumerate(tables, 1):
            doc_lines.extend([
                f"### {i}. **{table['name']}** - {table['row_count']:,} records",
                ""
            ])
            
            # Table schema
            doc_lines.extend([
                "```sql",
                f"CREATE TABLE {table['name']} ("
            ])
            
            for j, col in enumerate(table['columns']):
                col_def = f"    {col['name']} {col['type']}"
                
                if col['not_null']:
                    col_def += " NOT NULL"
                    
                if col['default_value']:
                    col_def += f" DEFAULT {col['default_value']}"
                    
                if col['is_primary_key']:
                    col_def += " PRIMARY KEY"
                
                # Add comma except for last column
                if j < len(table['columns']) - 1:
                    col_def += ","
                    
                doc_lines.append(col_def)
            
            doc_lines.extend([
                ");",
                "```",
                ""
            ])
            
            # Foreign keys
            if table['foreign_keys']:
                doc_lines.extend([
                    "**Foreign Key Relationships:**",
                    ""
                ])
                for fk in table['foreign_keys']:
                    doc_lines.append(f"- `{fk['column']}` â†’ `{fk['references_table']}.{fk['references_column']}`")
                doc_lines.append("")
            
            # Column statistics with unique values count
            if table['column_statistics']:
                doc_lines.extend([
                    "**Column Statistics:**",
                    ""
                ])
                
                for col_name, stats in table['column_statistics'].items():
                    unique_count = stats.get('unique_values', 0) or 0
                    non_null_count = stats.get('non_null_count', 0) or 0
                    
                    if stats['type'] == 'text':
                        avg_length = stats.get('avg_length', 0) or 0
                        doc_lines.append(f"- **{col_name}**: {unique_count:,} unique values ({non_null_count:,} non-null), avg length {avg_length}")
                    elif stats['type'] == 'numeric':
                        min_val = stats.get('min_value', 0) or 0
                        max_val = stats.get('max_value', 0) or 0
                        avg_val = stats.get('avg_value', 0) or 0
                        doc_lines.append(f"- **{col_name}**: {unique_count:,} unique values ({non_null_count:,} non-null), range {min_val:.4f} - {max_val:.4f}, avg {avg_val:.4f}")
                    elif stats['type'] == 'integer':
                        min_val = stats.get('min_value', 0) or 0
                        max_val = stats.get('max_value', 0) or 0
                        doc_lines.append(f"- **{col_name}**: {unique_count:,} unique values ({non_null_count:,} non-null), range {min_val} - {max_val}")
                
                doc_lines.append("")
            
            # Data quality metrics
            if 'data_quality' in table and table['data_quality']:
                quality = table['data_quality']
                
                # Completeness metrics
                if 'completeness' in quality and quality['completeness']:
                    doc_lines.extend([
                        "**Data Quality - Completeness:**",
                        ""
                    ])
                    
                    for col_name, completeness_info in quality['completeness'].items():
                        completeness_pct = completeness_info.get('completeness_percentage', 0)
                        null_count = completeness_info.get('null_count', 0)
                        if completeness_pct < 100:
                            doc_lines.append(f"- **{col_name}**: {completeness_pct}% complete ({null_count:,} null values)")
                        else:
                            doc_lines.append(f"- **{col_name}**: 100% complete")
                    
                    doc_lines.append("")
                
                # Duplicate check
                if 'duplicates' in quality and quality['duplicates']:
                    duplicate_info = quality['duplicates']
                    if duplicate_info.get('has_duplicates', False):
                        doc_lines.extend([
                            "**Data Quality - Duplicates:**",
                            "",
                            f"- ⚠️ Found {duplicate_info['duplicate_groups']} groups of duplicate records",
                            ""
                        ])
                    else:
                        doc_lines.extend([
                            "**Data Quality - Duplicates:**",
                            "",
                            "- ✅ No duplicate records found",
                            ""
                        ])
            
            # Sample data for each column
            table_name = table['name']
            if table_name in sample_data and sample_data[table_name]:
                doc_lines.extend([
                    "**Sample Data by Column:**",
                    ""
                ])
                
                for col in table['columns']:
                    col_name = col['name']
                    if col_name in sample_data[table_name] and sample_data[table_name][col_name]:
                        samples = sample_data[table_name][col_name]
                        # Format sample values, truncating if too long
                        formatted_samples = []
                        for sample in samples[:10]:  # Limit to 10 samples
                            if sample is not None:
                                sample_str = str(sample)
                                if len(sample_str) > 30:
                                    sample_str = sample_str[:27] + "..."
                                formatted_samples.append(f"`{sample_str}`")
                        
                        if formatted_samples:
                            doc_lines.append(f"- **{col_name}**: {', '.join(formatted_samples)}")
                
                doc_lines.append("")
            
            # Sample complete records
            if table['sample_rows']:
                doc_lines.extend([
                    "**Sample Complete Records:**",
                    ""
                ])
                
                # Show first 3 complete sample records in a readable format
                for idx, sample in enumerate(table['sample_rows'][:3], 1):
                    doc_lines.append(f"**Record {idx}:**")
                    for key, value in sample.items():
                        if value is not None:
                            # Truncate long values
                            display_value = str(value)
                            if len(display_value) > 50:
                                display_value = display_value[:47] + "..."
                            doc_lines.append(f"  - `{key}`: {display_value}")
                    doc_lines.append("")
                
                doc_lines.extend(["---", ""])
        
        # Top values for key columns
        if top_values:
            doc_lines.extend([
                "## Key Data Distributions",
                "",
                "Top values for important categorical columns:",
                ""
            ])
            
            for column_key, values in top_values.items():
                doc_lines.extend([
                    f"### {column_key}",
                    ""
                ])
                
                for value, count in values:
                    doc_lines.append(f"- **{value}**: {count:,} records")
                
                doc_lines.append("")
        
        # Indexes
        if indexes:
            doc_lines.extend([
                "## Database Indexes",
                "",
                "Performance indexes for optimized queries:",
                ""
            ])
            
            current_table = None
            for index in indexes:
                if index['table'] != current_table:
                    current_table = index['table']
                    doc_lines.extend([
                        f"### {current_table} table indexes",
                        ""
                    ])
                
                doc_lines.extend([
                    f"**{index['name']}**",
                    "```sql",
                    index['sql'],
                    "```",
                    ""
                ])
        
        # Add comprehensive data insights section
        if data_analysis and 'data_distribution' in data_analysis:
            doc_lines.extend([
                "## Data Distribution Analysis",
                "",
                "Key data patterns and distributions across business tables:",
                ""
            ])
            
            for table_name, table_data in data_analysis['data_distribution'].items():
                doc_lines.extend([
                    f"### {table_name} Distribution",
                    ""
                ])
                
                for column_name, column_data in table_data.items():
                    distribution = column_data.get('distribution', [])
                    unique_count = column_data.get('unique_values', 0)
                    
                    if distribution:
                        doc_lines.extend([
                            f"**{column_name}** ({unique_count} unique values):",
                            ""
                        ])
                        
                        for value, count in distribution[:10]:  # Top 10
                            percentage = (count / sum(item[1] for item in distribution)) * 100
                            doc_lines.append(f"- {value}: {count:,} ({percentage:.1f}%)")
                        
                        doc_lines.append("")
                
                doc_lines.append("")
        
        # Common query patterns
        doc_lines.extend([
            "## Common Query Patterns",
            "",
            "### 1. Career Pathway Exploration",
            "```sql",
            "-- Find similar roles with high similarity scores",
            "SELECT j2.JobProfile, js.similarity_score, j2.JobFamily",
            "FROM job_similarities js",
            "JOIN jobs j1 ON js.job_from = j1.JobProfileID",
            "JOIN jobs j2 ON js.job_to = j2.JobProfileID",
            "WHERE j1.JobProfileID = 'R0001.1'",
            "  AND js.similarity_score > 0.7",
            "ORDER BY js.similarity_score DESC",
            "LIMIT 10;",
            "```",
            "",
            "### 2. Skills Gap Analysis",
            "```sql",
            "-- Compare skills between two jobs",
            "SELECT s.Skill_Name, s.Category,",
            "       source_skills.Skill_Weight as current_weight,",
            "       target_skills.Skill_Weight as target_weight",
            "FROM skills s",
            "LEFT JOIN job_skills source_skills ON s.Skill_ID = source_skills.Skill_ID",
            "  AND source_skills.JobProfileID = 'R0001.1'",
            "LEFT JOIN job_skills target_skills ON s.Skill_ID = target_skills.Skill_ID",
            "  AND target_skills.JobProfileID = 'R0002.1'",
            "WHERE source_skills.Skill_ID IS NOT NULL",
            "   OR target_skills.Skill_ID IS NOT NULL",
            "ORDER BY s.Category, s.Skill_Name;",
            "```",
            "",
            "### 3. Organizational Context",
            "```sql",
            "-- Find roles in specific business units",
            "SELECT DISTINCT j.JobProfile, j.JobFamily, COUNT(DISTINCT p.\"Position Number\") as position_count",
            "FROM jobs j",
            "JOIN positions p ON j.JobProfileID = p.JobProfileID",
            "WHERE p.Business_Unit = 'Technology'",
            "GROUP BY j.JobProfileID, j.JobProfile, j.JobFamily",
            "ORDER BY position_count DESC;",
            "```",
            "",
            "### 4. Career Pathways (Pre-computed)",
            "```sql",
            "-- Get career pathway options using pre-computed table",
            "SELECT j.JobProfile, cp.similarity_score, cp.career_move_type, cp.difficulty_score",
            "FROM career_pathways cp",
            "JOIN jobs j ON cp.target_job_id = j.JobProfileID",
            "WHERE cp.source_job_id = 'R0001.1'",
            "  AND cp.similarity_score > 0.6",
            "ORDER BY cp.similarity_rank",
            "LIMIT 12;",
            "```",
            "",
            "---",
            "",
            "## Schema Evolution Notes",
            "",
            "- **Version**: Current schema represents production-ready structure",
            "- **Performance**: Optimized for webapp queries with appropriate indexes",
            "- **Scalability**: Handles current data volumes efficiently",
            "- **Future Extensions**: Schema designed for additive changes",
            "",
            "## Usage in Development",
            "",
            "This comprehensive schema documentation should be used to:",
            "1. **Inform LLMs** about database structure, relationships, and data patterns",
            "2. **Guide query development** for webapp endpoints with performance considerations",
            "3. **Validate data integrity** during pipeline updates and data quality checks",
            "4. **Plan schema evolution** for future requirements and optimizations",
            "5. **Understand business context** through movement analysis and career pathways",
            "6. **Optimize performance** using the query recommendations and size analysis",
            "",
            "## Analysis Summary",
            "",
            f"- **Database Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Tables Analyzed**: {len(tables)}",
            f"- **Relationships Mapped**: {len(relationships.get('foreign_key_relationships', []))}",
            f"- **Performance Recommendations**: {len(performance_analysis.get('query_recommendations', []))}",
            f"- **Data Quality Checks**: Completeness, duplicates, referential integrity",
            f"- **Business Insights**: Movement patterns, career pathways, skill distributions"
        ])
        
        # Write documentation
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(doc_lines))
        
        print(f"✅ Schema documentation generated: {output_file}")
        print(f"ðŸ“Š Analyzed {len(tables)} tables with {sum(table['row_count'] for table in tables):,} total records")
        print(f"ðŸ“„ Generated {len(doc_lines)} lines of documentation")


def main():
    """Main execution function."""
    # Find database file
    project_root = Path(__file__).parent.parent
    db_path = project_root / "models" / "2025-Q3" / "business_context.sqlite"
    
    if not db_path.exists():
        print(f"âŒ Database not found at: {db_path}")
        print("📊¡ Run 'python main.py' â†’ Option 2 to generate the business context database first")
        return 1
    
    # Output path
    output_path = project_root / "docs" / "sqlite_schema_design.md"
    
    try:
        generate_schema_documentation(str(db_path), str(output_path))
        return 0
        
    except Exception as e:
        print(f"âŒ Error generating schema documentation: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 

