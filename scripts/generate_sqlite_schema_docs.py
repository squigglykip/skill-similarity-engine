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
from typing import Dict, List, Tuple, Any
import json

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
        return {
            'file_path': str(self.db_path),
            'file_size_mb': round(stat.st_size / (1024 * 1024), 2),
            'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'analysis_date': datetime.now().isoformat()
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
        
        # Get sample data (first 10 rows)
        try:
            cursor = self.conn.execute(f"SELECT * FROM {table_name} LIMIT 10")
            sample_rows = [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            sample_rows = []
        
        # Get column statistics for key columns
        column_stats = self._get_column_statistics(table_name, columns)
        
        return {
            'name': table_name,
            'columns': columns,
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys,
            'row_count': row_count,
            'sample_rows': sample_rows,
            'column_statistics': column_stats
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
            'jobs': ['JobFamily', 'JobFamilyGroup'],
            'positions': ['Division', 'Business_Unit', 'Location'],
            'skills': ['Category', 'SkillType'],
            'career_pathways': ['career_move_type']
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
                    cursor = self.conn.execute(f"""
                        SELECT {column}, COUNT(*) as count
                        FROM {table}
                        WHERE {column} IS NOT NULL AND {column} != ''
                        GROUP BY {column}
                        ORDER BY count DESC
                        LIMIT 10
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
                    
                    # Get 10 sample values (non-null, distinct)
                    cursor = self.conn.execute(f"""
                        SELECT DISTINCT {quoted_col_name}
                        FROM {table_name}
                        WHERE {quoted_col_name} IS NOT NULL
                        LIMIT 10
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
                col_name = col['name']
                
                # Add primary key indicator
                pk_indicator = " PK" if col['is_primary_key'] else ""
                
                # Add foreign key indicator
                fk_indicator = ""
                for fk in table['foreign_keys']:
                    if fk['column'] == col_name:
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
                mermaid.append(f"    {target_table} ||--o{{ {source_table} : \"{fk['column']}\"")
        
        return "\n".join(mermaid)

def generate_schema_documentation(db_path: str, output_path: str) -> None:
    """Generate comprehensive schema documentation."""
    
    with SQLiteSchemaAnalyzer(db_path) as analyzer:
        # Gather all information
        db_info = analyzer.get_database_info()
        tables = analyzer.get_tables_info()
        indexes = analyzer.get_indexes_info()
        top_values = analyzer.get_top_values_for_key_columns()
        sample_data = analyzer.get_sample_data_for_all_columns()
        mermaid_diagram = analyzer.generate_mermaid_er_diagram(tables)
        
        # Generate markdown documentation
        doc_lines = []
        
        # Header
        doc_lines.extend([
            "# SQLite Schema Design for NAB Skill Similarity Engine",
            "## Business Context Database",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Database File**: `{db_info['file_path']}`",
            f"**Database Size**: {db_info['file_size_mb']} MB",
            f"**Last Modified**: {db_info['last_modified']}",
            "",
            "---",
            "",
            "## Overview",
            "",
            "This document provides comprehensive schema documentation for the NAB Skill Similarity Engine SQLite database.",
            "The database integrates job architecture, skill taxonomies, workforce context, and pre-computed similarities",
            "to support career pathway analysis and workforce planning.",
            "",
            "## Quick Reference for LLMs",
            "",
            "**Core Tables for Query Development:**",
            ""
        ])
        
        # Generate quick reference dynamically
        core_tables = {
            'jobs': 'JobProfileID, JobProfile, JobFamily, JobFamilyGroup',
            'career_pathways': 'source_job_id, target_job_id, similarity_rank, similarity_score, career_move_type',
            'job_similarities': 'job_from, job_to, similarity_score',
            'positions': 'JobProfileID, Division, Business_Unit, Location, Team',
            'job_skills': 'JobProfileID, Skill_ID, Skill_Weight',
            'skills': 'Skill_ID, Skill_Name, Category, SkillType'
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
            "- `jobs.JobProfileID` → `career_pathways.source_job_id/target_job_id`",
            "- `jobs.JobProfileID` → `job_similarities.job_from/job_to`",
            "- `jobs.JobProfileID` → `positions.JobProfileID`",
            "- `jobs.JobProfileID` → `job_skills.JobProfileID`",
            "- `skills.Skill_ID` → `job_skills.Skill_ID`",
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
            "",
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
                    doc_lines.append(f"- `{fk['column']}` → `{fk['references_table']}.{fk['references_column']}`")
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
            "SELECT DISTINCT j.JobProfile, j.JobFamily, COUNT(p.\"Position Number\") as position_count",
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
            "This schema documentation should be used to:",
            "1. **Inform LLMs** about database structure and relationships",
            "2. **Guide query development** for webapp endpoints",
            "3. **Validate data integrity** during pipeline updates",
            "4. **Plan schema evolution** for future requirements",
            "",
            f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ])
        
        # Write documentation
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(doc_lines))
        
        print(f"✅ Schema documentation generated: {output_file}")
        print(f"📊 Analyzed {len(tables)} tables with {sum(table['row_count'] for table in tables):,} total records")
        print(f"📄 Generated {len(doc_lines)} lines of documentation")

def main():
    """Main execution function."""
    # Find database file
    project_root = Path(__file__).parent.parent
    db_path = project_root / "models" / "2025-Q2" / "business_context.sqlite"
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        print("💡 Run 'python main.py' → Option 2 to generate the business context database first")
        return 1
    
    # Output path
    output_path = project_root / "docs" / "sqlite_schema_design.md"
    
    try:
        generate_schema_documentation(str(db_path), str(output_path))
        return 0
        
    except Exception as e:
        print(f"❌ Error generating schema documentation: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 