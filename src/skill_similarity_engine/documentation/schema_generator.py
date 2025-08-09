#!/usr/bin/env python3
"""
Enhanced SQLite Schema Documentation Generator

Modularized version of the schema documentation generator with enhanced features:
- Interactive table of contents with anchor links
- Enhanced Mermaid ERD with color coding
- Business context and developer guides
- Cross-references and navigation aids
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

class EnhancedSchemaDocGenerator:
    """Enhanced SQLite database schema analyzer and documenter."""
    
    def __init__(self, db_path: str):
        """Initialize with database path."""
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Table categories for organization and color coding
        self.table_categories = {
            'core': ['core_job_architecture', 'core_skills_taxonomy', 'core_job_skill_requirements', 
                    'core_workforce_current', 'core_colleague_positions_history', 'core_position_timeline'],
            'analytics': ['analytics_job_similarities', 'analytics_movement_patterns', 'analytics_skill_rarity',
                         'analytics_job_defining_skills', 'analytics_pathway_predictions', 'analytics_job_families',
                         'analytics_skill_bundles', 'analytics_skill_demand_trends', 'analytics_specialized_skills',
                         'analytics_bundle_characteristics'],
            'system': ['sys_schema_metadata']
        }
        
    def _quote_ident(self, name: str) -> str:
        """Safely quote an SQLite identifier."""
        return '"' + str(name).replace('"', '""') + '"'

    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
    
    def get_table_category(self, table_name: str) -> str:
        """Get the category of a table for color coding."""
        for category, tables in self.table_categories.items():
            if table_name.lower() in [t.lower() for t in tables]:
                return category
        return 'other'
    
    def generate_table_of_contents(self, tables: List[Dict[str, Any]]) -> str:
        """Generate an interactive table of contents with anchor links."""
        toc_lines = [
            "## 📋 Table of Contents",
            "",
            "### Quick Navigation",
            "- [📊 Database Overview](#-database-overview)",
            "- [🎯 Quick Reference](#-quick-reference-for-llms)",
            "- [📈 Performance Analysis](#-performance-analysis)",
            "- [🔗 Entity Relationship Diagram](#-entity-relationship-diagram)",
            "- [📋 Table Definitions](#-table-definitions)",
            "- [🔍 Data Distributions](#-key-data-distributions)",
            "- [⚡ Query Patterns](#-common-query-patterns)",
            "- [🏷️ Business Context](#-business-context-guide)",
            "",
            "### 📊 Tables by Category",
            ""
        ]
        
        # Organize tables by category
        categorized_tables = defaultdict(list)
        for table in tables:
            category = self.get_table_category(table['name'])
            categorized_tables[category].append(table)
        
        # Core tables
        if categorized_tables['core']:
            toc_lines.extend([
                "#### 🏗️ Core Data Tables",
                ""
            ])
            for table in sorted(categorized_tables['core'], key=lambda x: x['name']):
                anchor = table['name'].lower().replace('_', '-')
                row_count = f"{table['row_count']:,}" if table['row_count'] > 0 else "empty"
                toc_lines.append(f"- [{table['name']}](#{anchor}) - {row_count} records")
            toc_lines.append("")
        
        # Analytics tables
        if categorized_tables['analytics']:
            toc_lines.extend([
                "#### 📊 Analytics Tables",
                ""
            ])
            for table in sorted(categorized_tables['analytics'], key=lambda x: x['name']):
                anchor = table['name'].lower().replace('_', '-')
                row_count = f"{table['row_count']:,}" if table['row_count'] > 0 else "empty"
                toc_lines.append(f"- [{table['name']}](#{anchor}) - {row_count} records")
            toc_lines.append("")
        
        # System tables
        if categorized_tables['system']:
            toc_lines.extend([
                "#### ⚙️ System Tables",
                ""
            ])
            for table in sorted(categorized_tables['system'], key=lambda x: x['name']):
                anchor = table['name'].lower().replace('_', '-')
                row_count = f"{table['row_count']:,}" if table['row_count'] > 0 else "empty"
                toc_lines.append(f"- [{table['name']}](#{anchor}) - {row_count} records")
            toc_lines.append("")
        
        # Other tables
        if categorized_tables['other']:
            toc_lines.extend([
                "#### 🔧 Other Tables",
                ""
            ])
            for table in sorted(categorized_tables['other'], key=lambda x: x['name']):
                anchor = table['name'].lower().replace('_', '-')
                row_count = f"{table['row_count']:,}" if table['row_count'] > 0 else "empty"
                toc_lines.append(f"- [{table['name']}](#{anchor}) - {row_count} records")
            toc_lines.append("")
        
        return "\n".join(toc_lines)
    
    def generate_enhanced_mermaid_erd(self, tables, *, max_tables=6, strict_subset=True) -> str:
        """
        Generate Mermaid ERD with proper syntax.
        Fixes:
        - Composite primary keys (only mark one column as PK)
        - Correct relationship syntax (||--o| instead of ||--o{)
        - Handle reserved words and special characters
        """
        lines = ["```mermaid", "erDiagram"]

        # Pick tables
        if strict_subset:
            important = []
            for t in tables:
                if (t['name'].startswith('core_') or 
                    t['name'] in ['analytics_job_similarities', 'analytics_movement_patterns', 'analytics_skill_rarity']):
                    important.append(t)
            tables_to_show = important[:max_tables]
        else:
            tables_to_show = tables[:max_tables] if max_tables else tables

        # Build FK map (only within shown tables)
        shown = {t['name'] for t in tables_to_show}
        fk_map = {f"{t['name']}.{fk['column']}": fk['references_table']
                for t in tables_to_show for fk in t['foreign_keys']}

        # Entities
        for t in tables_to_show:
            entity = t['name'].upper().replace('-', '_').replace(' ', '_')
            lines.append(f"    {entity} {{")
            
            # Get primary key columns
            pk_columns = [c for c in t['columns'] if c['is_primary_key']]
            non_pk_columns = [c for c in t['columns'] if not c['is_primary_key']]
            
            # For composite primary keys, only mark the first one as PK in Mermaid
            pk_marked = False
            
            # Show PKs first
            for c in pk_columns:
                ct = (c['type'] or '').lower()
                dtype = "string"
                if 'int' in ct:
                    dtype = "int"
                elif any(x in ct for x in ['real', 'numeric', 'decimal', 'float', 'double']):
                    dtype = "float"
                name = c['name'].replace(' ', '_').replace('-', '_').replace('.', '_')
                
                # Handle reserved words that break Mermaid parsing
                reserved_words = {
                    'from': 'from_col', 'to': 'to_col', 'group': 'group_col', 'order': 'order_col',
                    'index': 'index_col', 'key': 'key_col', 'type': 'type_col', 'desc': 'desc_col'
                }
                if name.lower() in reserved_words:
                    name = reserved_words[name.lower()]
                
                # Only mark the first column as PK for Mermaid syntax
                if not pk_marked:
                    lines.append(f"        {dtype} {name} PK")
                    pk_marked = True
                else:
                    # Subsequent PK columns are just regular columns in Mermaid
                    is_fk = f"{t['name']}.{c['name']}" in fk_map
                    if is_fk:
                        lines.append(f"        {dtype} {name} FK")
                    else:
                        lines.append(f"        {dtype} {name}")
            
            # Then show non-PK columns (FKs and others)
            for c in non_pk_columns:
                ct = (c['type'] or '').lower()
                dtype = "string"
                if 'int' in ct:
                    dtype = "int"
                elif any(x in ct for x in ['real', 'numeric', 'decimal', 'float', 'double']):
                    dtype = "float"
                name = c['name'].replace(' ', '_').replace('-', '_').replace('.', '_')
                
                # Handle reserved words that break Mermaid parsing
                reserved_words = {
                    'from': 'from_col', 'to': 'to_col', 'group': 'group_col', 'order': 'order_col',
                    'index': 'index_col', 'key': 'key_col', 'type': 'type_col', 'desc': 'desc_col'
                }
                if name.lower() in reserved_words:
                    name = reserved_words[name.lower()]
                
                is_fk = f"{t['name']}.{c['name']}" in fk_map
                if is_fk:
                    lines.append(f"        {dtype} {name} FK")
                else:
                    lines.append(f"        {dtype} {name}")
            
            lines.append("    }")

        # Relationships - using correct Mermaid ERD syntax
        added = set()
        rel_count = 0
        for t in tables_to_show:
            src = t['name'].upper().replace('-', '_').replace(' ', '_')
            for fk in t['foreign_keys']:
                tgt_raw = fk['references_table']
                if tgt_raw not in shown:
                    continue
                tgt = tgt_raw.upper().replace('-', '_').replace(' ', '_')
                label = fk['column'].replace(' ', '_').replace('-', '_').replace('.', '_')
                
                # Handle reserved words in relationship labels
                reserved_words = {
                    'from': 'from_col', 'to': 'to_col', 'group': 'group_col', 'order': 'order_col',
                    'index': 'index_col', 'key': 'key_col', 'type': 'type_col', 'desc': 'desc_col'
                }
                if label.lower() in reserved_words:
                    label = reserved_words[label.lower()]
                
                # Create unique key to avoid duplicate relationships
                key = (tgt, src, label)
                if key in added:
                    continue
                
                # Use correct Mermaid ERD relationship syntax: ||--o| for one-to-many
                lines.append(f"    {tgt} ||--o| {src} : {label}")
                added.add(key)
                rel_count += 1

        # If no relationships found, add a comment
        if rel_count == 0:
            lines.append("    %% No FK relationships among the selected tables")

        lines.append("```")
        return "\n".join(lines)
 
    def generate_text_based_erd(self, tables: List[Dict[str, Any]]) -> str:
        """Generate a simple text-based entity relationship diagram as fallback."""
        text_lines = []
        
        # Group tables by type
        core_tables = [t for t in tables if t['name'].startswith('core_')]
        analytics_tables = [t for t in tables if t['name'].startswith('analytics_')]
        
        if core_tables:
            text_lines.extend([
                "**🏗️ Core Data Tables:**",
                ""
            ])
            
            for table in core_tables[:6]:  # Limit for readability
                pk_columns = [col['name'] for col in table['columns'] if col['is_primary_key']]
                fk_relationships = [f"→ {fk['references_table']}" for fk in table['foreign_keys']]
                
                text_lines.append(f"• **{table['name']}** ({table['row_count']:,} records)")
                if pk_columns:
                    text_lines.append(f"  - Primary Key: {', '.join(pk_columns)}")
                if fk_relationships:
                    text_lines.append(f"  - References: {', '.join(fk_relationships)}")
                text_lines.append("")
        
        if analytics_tables:
            text_lines.extend([
                "**📊 Analytics Tables:**",
                ""
            ])
            
            for table in analytics_tables[:6]:  # Limit for readability
                pk_columns = [col['name'] for col in table['columns'] if col['is_primary_key']]
                fk_relationships = [f"→ {fk['references_table']}" for fk in table['foreign_keys']]
                
                text_lines.append(f"• **{table['name']}** ({table['row_count']:,} records)")
                if pk_columns:
                    text_lines.append(f"  - Primary Key: {', '.join(pk_columns)}")
                if fk_relationships:
                    text_lines.append(f"  - References: {', '.join(fk_relationships)}")
                text_lines.append("")
        
        # Add key relationship summary
        text_lines.extend([
            "**🔗 Key Relationships:**",
            ""
        ])
        
        # Find and display main relationships
        relationships = []
        for table in tables:
            for fk in table['foreign_keys']:
                relationships.append(f"• {table['name']}.{fk['column']} → {fk['references_table']}.{fk['references_column']}")
        
        for rel in relationships[:8]:  # Show top 8 relationships
            text_lines.append(rel)
        
        if len(relationships) > 8:
            text_lines.append(f"• ... and {len(relationships) - 8} more relationships")
        
        return "\n".join(text_lines)
    
    def generate_business_context_guide(self, tables: List[Dict[str, Any]]) -> str:
        """Generate business context guide for tables."""
        guide_lines = [
            "## 🏷️ Business Context Guide",
            "",
            "Understanding what each table represents in business terms and how they support workforce intelligence.",
            "",
            "### 🏗️ Core Data Foundation",
            ""
        ]
        
        # Core table descriptions
        core_descriptions = {
            'core_job_architecture': {
                'purpose': 'Defines the organizational job structure and hierarchies',
                'business_use': 'Job family analysis, role comparison, organizational design',
                'update_frequency': 'Quarterly or when org structure changes',
                'key_insights': 'Job relationships, management levels, customer-facing roles'
            },
            'core_skills_taxonomy': {
                'purpose': 'Master catalog of all skills with categorization and metadata',
                'business_use': 'Skill gap analysis, capability mapping, training needs',
                'update_frequency': 'Monthly with market skill trends',
                'key_insights': 'Skill categories, types, emerging vs traditional skills'
            },
            'core_job_skill_requirements': {
                'purpose': 'Links jobs to required skills (many-to-many relationship)',
                'business_use': 'Career pathway analysis, recruitment planning',
                'update_frequency': 'Bi-annually or when roles evolve',
                'key_insights': 'Skill demand patterns, role complexity'
            },
            'core_workforce_current': {
                'purpose': 'Current workforce snapshot with organizational context',
                'business_use': 'Workforce planning, diversity analysis, succession planning',
                'update_frequency': 'Weekly or real-time',
                'key_insights': 'Team structures, location distribution, role distribution'
            }
        }
        
        for table_name, desc in core_descriptions.items():
            guide_lines.extend([
                f"#### {table_name}",
                f"**Purpose**: {desc['purpose']}",
                f"**Business Use**: {desc['business_use']}",
                f"**Update Frequency**: {desc['update_frequency']}",
                f"**Key Insights**: {desc['key_insights']}",
                ""
            ])
        
        guide_lines.extend([
            "### 📊 Analytics Intelligence",
            "",
            "Pre-computed analytics tables that power business insights and decision-making.",
            ""
        ])
        
        # Analytics table descriptions
        analytics_descriptions = {
            'analytics_job_similarities': {
                'purpose': 'Pre-computed similarity scores between all job pairs',
                'business_use': 'Career pathway recommendations, lateral move suggestions',
                'derived_from': 'core_job_architecture + core_job_skill_requirements',
                'refresh_trigger': 'Job architecture or skill requirements change'
            },
            'analytics_movement_patterns': {
                'purpose': 'Historical career movement patterns and trends',
                'business_use': 'Succession planning, career pathway validation',
                'derived_from': 'core_colleague_positions_history',
                'refresh_trigger': 'Monthly with new position history'
            },
            'analytics_skill_rarity': {
                'purpose': 'Skill scarcity analysis and market positioning',
                'business_use': 'Talent acquisition strategy, skill premium analysis',
                'derived_from': 'core_job_skill_requirements + workforce data',
                'refresh_trigger': 'Quarterly skill market analysis'
            }
        }
        
        for table_name, desc in analytics_descriptions.items():
            guide_lines.extend([
                f"#### {table_name}",
                f"**Purpose**: {desc['purpose']}",
                f"**Business Use**: {desc['business_use']}",
                f"**Derived From**: {desc['derived_from']}",
                f"**Refresh Trigger**: {desc['refresh_trigger']}",
                ""
            ])
        
        return "\n".join(guide_lines)
    
    def generate_developer_guide(self) -> str:
        """Generate developer-focused usage guide."""
        guide_lines = [
            "## 🔧 Developer Guide",
            "",
            "### 🚀 Common Query Patterns",
            "",
            "#### Career Pathway Analysis",
            "```sql",
            "-- Find career paths from a specific role",
            "SELECT ",
            "    j2.JobProfile as target_role,",
            "    js.similarity_score,",
            "    j2.JobFunction,",
            "    j2.ManagementLevel",
            "FROM analytics_job_similarities js",
            "JOIN core_job_architecture j1 ON js.job_from = j1.JobProfileID",
            "JOIN core_job_architecture j2 ON js.job_to = j2.JobProfileID",
            "WHERE j1.JobProfile = 'Senior Business Analyst'",
            "  AND js.similarity_score > 0.7",
            "ORDER BY js.similarity_score DESC",
            "LIMIT 10;",
            "```",
            "",
            "#### Skill Gap Analysis",
            "```sql",
            "-- Compare skills between current and target role",
            "SELECT ",
            "    st.Skill_Name,",
            "    st.Category,",
            "    CASE WHEN current_skills.Skill_ID IS NOT NULL THEN 'HAS' ELSE 'MISSING' END as current_status,",
            "    sr.rarity_category",
            "FROM core_job_skill_requirements target_skills",
            "JOIN core_skills_taxonomy st ON target_skills.Skill_ID = st.Skill_ID",
            "LEFT JOIN analytics_skill_rarity sr ON st.Skill_ID = sr.skill_id",
            "LEFT JOIN (",
            "    SELECT jsr.Skill_ID",
            "    FROM core_job_skill_requirements jsr",
            "    JOIN core_job_architecture ja ON jsr.JobProfileID = ja.JobProfileID",
            "    WHERE ja.JobProfile = 'Current Role'",
            ") current_skills ON target_skills.Skill_ID = current_skills.Skill_ID",
            "JOIN core_job_architecture ja ON target_skills.JobProfileID = ja.JobProfileID",
            "WHERE ja.JobProfile = 'Target Role'",
            "ORDER BY sr.rarity_score DESC;",
            "```",
            "",
            "#### Movement Pattern Analysis",
            "```sql",
            "-- Analyze movement patterns from specific job families",
            "SELECT ",
            "    mp.to_position,",
            "    mp.movement_count,",
            "    mp.avg_days_between,",
            "    mp.success_rate,",
            "    ja.JobFunction as target_function",
            "FROM analytics_movement_patterns mp",
            "JOIN core_job_architecture ja ON mp.to_job_profile_id = ja.JobProfileID",
            "WHERE mp.from_position LIKE '%Analyst%'",
            "  AND mp.movement_count >= 5",
            "ORDER BY mp.movement_count DESC;",
            "```",
            "",
            "### ⚡ Performance Tips",
            "",
            "1. **Use Indexes**: Key columns are automatically indexed, but consider composite indexes for complex queries",
            "2. **Limit Results**: Always use LIMIT for exploratory queries on large tables",
            "3. **Join Strategy**: Start with smaller tables (job_architecture) and join to larger ones",
            "4. **Filter Early**: Apply WHERE conditions on indexed columns first",
            "",
            "### 🔗 Key Relationships",
            "",
            "- **JobProfileID**: Primary key linking jobs across all tables",
            "- **Skill_ID**: Primary key linking skills across taxonomy and requirements",
            "- **Similarity Scores**: Pre-computed to avoid expensive calculations",
            "- **Movement Patterns**: Aggregated to provide statistical significance",
            ""
        ]
        
        return "\n".join(guide_lines)
    
    def add_back_to_top_links(self, content: str) -> str:
        """Add 'back to top' navigation links throughout the document."""
        # Add back to top links after major sections
        sections_to_enhance = [
            "## 📊 Database Statistics",
            "## 🔗 Entity Relationship Diagram", 
            "## 📋 Table Definitions",
            "## 🔍 Key Data Distributions",
            "## ⚡ Common Query Patterns",
            "## 🏷️ Business Context Guide",
            "## 🔧 Developer Guide"
        ]
        
        for section in sections_to_enhance:
            content = content.replace(
                section, 
                f"{section}\n\n[⬆️ Back to Table of Contents](#-table-of-contents)"
            )
        
        return content
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get basic database information."""
        stat = self.db_path.stat()
        
        # Get SQLite version and settings
        cursor = self.conn.execute("SELECT sqlite_version()")
        sqlite_version = cursor.fetchone()[0]
        
        return {
            'file_path': str(self.db_path),
            'file_size_mb': round(stat.st_size / (1024 * 1024), 2),
            'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'sqlite_version': sqlite_version
        }
    
    def get_tables_info(self) -> List[Dict[str, Any]]:
        """Get comprehensive information about all tables and views across attached databases."""
        tables: List[Dict[str, Any]] = []

        # Discover attached databases (main, temp, and any ATTACH'ed)
        dbs = [row[1] for row in self.conn.execute("PRAGMA database_list").fetchall()]

        for schema in dbs:
            # Enumerate tables and views; exclude internal sqlite_* objects
            query = (
                f"SELECT name, type FROM {schema}.sqlite_schema "
                "WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )

            for name, obj_type in self.conn.execute(query).fetchall():
                quoted_name = self._quote_ident(name)
                qualified = f"{schema}.{quoted_name}"

                # Column info (xinfo includes hidden/generated columns)
                columns: List[Dict[str, Any]] = []
                try:
                    col_rows = self.conn.execute(
                        f"PRAGMA {schema}.table_xinfo({quoted_name})"
                    ).fetchall()
                except sqlite3.Error:
                    col_rows = []
                for row in col_rows:
                    columns.append(
                        {
                            'name': row[1],
                            'type': row[2],
                            'is_primary_key': bool(row[5]),
                        }
                    )

                # Foreign key info (empty for views in most cases)
                foreign_keys: List[Dict[str, Any]] = []
                try:
                    fk_rows = self.conn.execute(
                        f"PRAGMA {schema}.foreign_key_list({quoted_name})"
                    ).fetchall()
                    for row in fk_rows:
                        foreign_keys.append(
                            {
                                'column': row[3],
                                'references_table': row[2],
                                'references_column': row[4],
                            }
                        )
                except sqlite3.Error:
                    pass

                # Row count (supported for views; may be slower)
                try:
                    row_count = self.conn.execute(
                        f"SELECT COUNT(*) FROM {qualified}"
                    ).fetchone()[0]
                except sqlite3.Error:
                    row_count = 0

                # Sample rows
                try:
                    cur = self.conn.execute(f"SELECT * FROM {qualified} LIMIT 5")
                    sample_rows = [dict(r) for r in cur.fetchall()]
                except sqlite3.Error:
                    sample_rows = []

                # Column statistics (use qualified name so attached DBs work)
                column_stats = self._get_basic_column_statistics(f"{schema}.{name}", columns)

                tables.append(
                    {
                        'schema': schema,
                        'name': name,
                        'object_type': obj_type,
                        'columns': columns,
                        'foreign_keys': foreign_keys,
                        'row_count': row_count,
                        'sample_rows': sample_rows,
                        'column_statistics': column_stats,
                    }
                )

        return tables
    
    def _get_basic_column_statistics(self, table_name: str, columns: List[Dict]) -> Dict[str, Any]:
        """Get basic statistics for key columns."""
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
                            'avg_length': round(row[2], 2) if row[2] else 0
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
    
    def generate_enhanced_documentation(self, output_path: str, create_debug_erd: bool = False) -> bool:
        """Generate the complete enhanced documentation."""
        try:
            from pathlib import Path
            
            print("🔍 Analyzing database structure...")
            db_info = self.get_database_info()
            tables = self.get_tables_info()
            
            # Debug toggle for ERD generation
            DEBUG_ERD_ALL_TABLES = False  # toggle when debugging
            
            # Build ERD once so we can validate and reuse
            erd_block = self.generate_enhanced_mermaid_erd(
                tables,
                max_tables=0 if DEBUG_ERD_ALL_TABLES else 6,
                strict_subset=not DEBUG_ERD_ALL_TABLES
            )
            assert erd_block.rstrip().endswith("```"), "Mermaid ERD block is missing a closing code fence"
            
            # Optionally emit a standalone .erd.mmd for easy validation in Mermaid Live Editor
            if create_debug_erd:
                erd_path = Path(output_path).with_suffix(".erd.mmd")
                erd_path.write_text(erd_block, encoding="utf-8")
                print(f"📊 ERD debug file written: {erd_path}")
            
            # Generate enhanced content
            doc_lines = []
            
            # Header with enhanced styling
            doc_lines.extend([
                "# 🗄️ SQLite Schema Design for NAB Skill Similarity Engine",
                "## 💼 Workforce Intelligence Database",
                "",
                f"**📅 Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"**📂 Database File**: `{db_info['file_path']}`",
                f"**💾 Database Size**: {db_info['file_size_mb']} MB",
                f"**⚙️ SQLite Version**: {db_info['sqlite_version']}",
                f"**🕒 Last Modified**: {db_info['last_modified']}",
                "",
                "---",
                ""
            ])
            
            # Table of Contents
            doc_lines.append(self.generate_table_of_contents(tables))
            doc_lines.append("\n---\n")
            
            # Database Overview
            doc_lines.extend([
                "## 📊 Database Overview",
                "",
                "This document provides comprehensive schema documentation for the NAB Skill Similarity Engine SQLite database.",
                "The database integrates job architecture, skill taxonomies, workforce context, movement analysis, and pre-computed similarities",
                "to support career pathway analysis, workforce planning, and strategic workforce intelligence.",
                "",
                f"### 📈 Quick Stats",
                f"- **Total Tables**: {len(tables)}",
                f"- **Total Records**: {sum(table['row_count'] for table in tables):,}",
                f"- **Database Size**: {db_info['file_size_mb']} MB",
                ""
            ])
            
            # Enhanced Mermaid ERD
            doc_lines.extend([
                "",
                "## 🔗 Entity Relationship Diagram",
                "",
                "Interactive ERD showing table relationships and key columns:",
                "",
                erd_block,
                "",
                "### Alternative Text-Based Relationship Map",
                "",
                "*If the Mermaid diagram above doesn't render, here's a text-based view:*",
                "",
                self.generate_text_based_erd(tables),
                ""
            ])
            
            # Table Definitions
            doc_lines.extend([
                "## 📋 Table Definitions",
                ""
            ])
            
            # Add simplified table documentation
            for i, table in enumerate(tables, 1):
                anchor = table['name'].lower().replace('_', '-')
                doc_lines.extend([
                    f"### {i}. **{table['name']}** - {table['row_count']:,} records",
                    f"<a name=\"{anchor}\"></a>",
                    ""
                ])
                
                # Table schema
                doc_lines.extend([
                    "```sql",
                    f"CREATE TABLE {table['name']} ("
                ])
                
                for j, col in enumerate(table['columns']):
                    col_def = f"    {col['name']} {col['type']}"
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
                
                # Column statistics
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
                
                # Sample records
                if table['sample_rows']:
                    doc_lines.extend([
                        "**Sample Records:**",
                        ""
                    ])
                    
                    # Show sample records in a readable format
                    for idx, sample in enumerate(table['sample_rows'][:3], 1):  # Limit to 3 samples
                        doc_lines.append(f"**Record {idx}:**")
                        for key, value in sample.items():
                            if value is not None:
                                # Truncate long values and handle different data types
                                display_value = str(value)
                                if len(display_value) > 100:
                                    display_value = display_value[:97] + "..."
                                
                                # Handle special characters in column names
                                formatted_key = f"`{key}`" if ' ' in key or '-' in key else key
                                doc_lines.append(f"  - **{formatted_key}**: {display_value}")
                            else:
                                formatted_key = f"`{key}`" if ' ' in key or '-' in key else key
                                doc_lines.append(f"  - **{formatted_key}**: NULL")
                        doc_lines.append("")
                    
                    # If there are more records, show a summary
                    if len(table['sample_rows']) > 3:
                        doc_lines.append(f"*... and {len(table['sample_rows']) - 3} more sample records*")
                        doc_lines.append("")
                elif table['row_count'] > 0:
                    doc_lines.extend([
                        "**Sample Records:**",
                        "",
                        "*No sample data available (query may have failed)*",
                        ""
                    ])
                else:
                    doc_lines.extend([
                        "**Sample Records:**",
                        "",
                        "*Table is empty*",
                        ""
                    ])
                
                doc_lines.extend(["---", ""])
            
            # Add business context guide
            doc_lines.append(self.generate_business_context_guide(tables))
            
            # Add developer guide
            doc_lines.append(self.generate_developer_guide())
            
            # Write the documentation
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Add back to top links
            final_content = "\n".join(doc_lines)
            final_content = self.add_back_to_top_links(final_content)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            print(f"✅ Enhanced schema documentation generated: {output_file}")
            print(f"📊 Analyzed {len(tables)} tables with {sum(table['row_count'] for table in tables):,} total records")
            print(f"📄 Generated enhanced documentation with navigation and business context")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating enhanced documentation: {e}")
            return False


def generate_enhanced_schema_docs(db_path: str, output_path: str, create_debug_erd: bool = False) -> bool:
    """
    Generate enhanced schema documentation with navigation and business context.
    
    Args:
        db_path: Path to SQLite database
        output_path: Path for output markdown file
        create_debug_erd: Whether to create a separate .erd.mmd debug file (default: False)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with EnhancedSchemaDocGenerator(db_path) as generator:
            return generator.generate_enhanced_documentation(output_path, create_debug_erd)
    except Exception as e:
        print(f"❌ Documentation generation failed: {e}")
        return False