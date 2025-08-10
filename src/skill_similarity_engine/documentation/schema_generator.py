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
                         'analytics_job_family_characteristics', 'analytics_skill_bundles', 'analytics_skill_demand_trends', 
                         'analytics_specialized_skills', 'analytics_bundle_characteristics'],
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
    
    def generate_enhanced_mermaid_erd(self, tables, *, max_tables=None, strict_subset=False, 
                                     include_zoom_controls=True) -> str:
        """
        Generate Mermaid ERD with proper syntax.
        Fixes:
        - Composite primary keys (only mark one column as PK)
        - Correct relationship syntax (||--o| instead of ||--o{)
        - Handle reserved words and special characters
        
        Args:
            tables: List of table dictionaries
            max_tables: Maximum number of tables to include (None for no limit)
            strict_subset: If True, only include core_ and specific analytics tables
        """
        lines = ["```mermaid", "erDiagram"]

        # Pick tables
        if strict_subset:
            important = []
            for t in tables:
                if (t['name'].startswith('core_') or 
                    t['name'] in ['analytics_job_similarities', 'analytics_movement_patterns', 'analytics_skill_rarity']):
                    important.append(t)
            tables_to_show = important[:max_tables] if max_tables else important
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
        
        # Add zoom controls and enhanced interactivity if requested
        if include_zoom_controls:
            erd_content = "\n".join(lines)
            return self._wrap_erd_with_zoom_controls(erd_content)
        else:
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
    
    def _wrap_erd_with_zoom_controls(self, erd_content: str) -> str:
        """Wrap the ERD with HTML zoom controls and interactivity."""
        return f"""
<div id="erd-container" style="position: relative; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; background: #fafafa;">
  <!-- Zoom Controls -->
  <div id="erd-controls" style="position: absolute; top: 10px; right: 10px; z-index: 100; background: rgba(255,255,255,0.9); border-radius: 6px; padding: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <button onclick="zoomERD(1.2)" style="margin: 2px; padding: 4px 8px; border: 1px solid #ccc; background: white; cursor: pointer; border-radius: 3px;" title="Zoom In">🔍+</button>
    <button onclick="zoomERD(0.8)" style="margin: 2px; padding: 4px 8px; border: 1px solid #ccc; background: white; cursor: pointer; border-radius: 3px;" title="Zoom Out">🔍-</button>
    <button onclick="resetERDZoom()" style="margin: 2px; padding: 4px 8px; border: 1px solid #ccc; background: white; cursor: pointer; border-radius: 3px;" title="Reset Zoom">⌂</button>
    <button onclick="toggleERDFullscreen()" style="margin: 2px; padding: 4px 8px; border: 1px solid #ccc; background: white; cursor: pointer; border-radius: 3px;" title="Fullscreen">⛶</button>
  </div>
  
  <!-- ERD Content -->
  <div id="erd-content" style="transform-origin: top left; transition: transform 0.3s ease; max-height: 600px; overflow: auto; padding: 20px;">
{erd_content}
  </div>
</div>

<script>
let erdZoomLevel = 1;
let isFullscreen = false;

function zoomERD(factor) {{
  erdZoomLevel *= factor;
  const content = document.getElementById('erd-content');
  content.style.transform = `scale(${{erdZoomLevel}})`;
  
  // Adjust container size based on zoom
  const container = document.getElementById('erd-container');
  if (erdZoomLevel > 1) {{
    container.style.overflow = 'scroll';
  }}
}}

function resetERDZoom() {{
  erdZoomLevel = 1;
  const content = document.getElementById('erd-content');
  content.style.transform = 'scale(1)';
  const container = document.getElementById('erd-container');
  container.style.overflow = 'auto';
}}

function toggleERDFullscreen() {{
  const container = document.getElementById('erd-container');
  const content = document.getElementById('erd-content');
  
  if (!isFullscreen) {{
    // Enter fullscreen
    container.style.position = 'fixed';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100vw';
    container.style.height = '100vh';
    container.style.zIndex = '9999';
    container.style.background = 'white';
    content.style.maxHeight = 'calc(100vh - 80px)';
    content.style.padding = '40px';
    isFullscreen = true;
  }} else {{
    // Exit fullscreen
    container.style.position = 'relative';
    container.style.top = 'auto';
    container.style.left = 'auto';
    container.style.width = 'auto';
    container.style.height = 'auto';
    container.style.zIndex = 'auto';
    container.style.background = '#fafafa';
    content.style.maxHeight = '600px';
    content.style.padding = '20px';
    isFullscreen = false;
  }}
}}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {{
  if (e.target.closest('#erd-container')) {{
    if (e.key === '+' || e.key === '=') {{
      e.preventDefault();
      zoomERD(1.2);
    }} else if (e.key === '-') {{
      e.preventDefault();
      zoomERD(0.8);
    }} else if (e.key === '0') {{
      e.preventDefault();
      resetERDZoom();
    }} else if (e.key === 'f' || e.key === 'F') {{
      e.preventDefault();
      toggleERDFullscreen();
    }} else if (e.key === 'Escape' && isFullscreen) {{
      e.preventDefault();
      toggleERDFullscreen();
    }}
  }}
}});

// Mouse wheel zoom
document.getElementById('erd-container').addEventListener('wheel', function(e) {{
  if (e.ctrlKey) {{
    e.preventDefault();
    const factor = e.deltaY > 0 ? 0.9 : 1.1;
    zoomERD(factor);
  }}
}});
</script>

<div style="margin-top: 10px; padding: 10px; background: #f0f8ff; border-left: 4px solid #4CAF50; font-size: 0.9em;">
  <strong>💡 ERD Navigation Tips:</strong>
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Zoom:</strong> Use +/- buttons, keyboard +/-, or Ctrl+scroll wheel</li>
    <li><strong>Reset:</strong> Click ⌂ button or press '0'</li>
    <li><strong>Fullscreen:</strong> Click ⛶ button or press 'F' (Escape to exit)</li>
    <li><strong>Pan:</strong> Use scroll bars when zoomed in</li>
  </ul>
</div>
"""
    
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
    
    def generate_standalone_zoomable_erd(self, tables: List[Dict[str, Any]], output_path: str, 
                                        show_all_tables: bool = True) -> bool:
        """Generate a standalone HTML file with an interactive, zoomable ERD."""
        try:
            from pathlib import Path
            
            # Generate the Mermaid ERD content (without HTML wrapper)
            erd_block = self.generate_enhanced_mermaid_erd(
                tables,
                max_tables=None if show_all_tables else 6,
                strict_subset=not show_all_tables,
                include_zoom_controls=False  # We'll add our own enhanced controls
            )
            
            # Extract just the Mermaid code (remove the ``` markers and any HTML)
            if "</script>" in erd_block:
                # ERD has HTML controls, extract Mermaid from within
                start_marker = '```mermaid\n'
                end_marker = '\n```'
                start_idx = erd_block.find(start_marker)
                end_idx = erd_block.find(end_marker, start_idx)
                if start_idx != -1 and end_idx != -1:
                    mermaid_code = erd_block[start_idx + len(start_marker):end_idx].strip()
                else:
                    # Fallback - generate clean Mermaid code
                    clean_erd = self.generate_enhanced_mermaid_erd(
                        tables,
                        max_tables=None if show_all_tables else 6,
                        strict_subset=not show_all_tables,
                        include_zoom_controls=False
                    )
                    mermaid_code = clean_erd.replace('```mermaid\n', '').replace('\n```', '').strip()
            else:
                # ERD is clean Mermaid code
                mermaid_code = erd_block.replace('```mermaid\n', '').replace('\n```', '').strip()
            
            # Create enhanced HTML with Mermaid.js
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Database ERD - Schema Visualisation</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f7fa;
            color: #333;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .erd-container {{
            position: relative;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
            min-height: 70vh;
        }}
        
        .controls {{
            position: absolute;
            top: 15px;
            right: 15px;
            z-index: 1000;
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            border-radius: 8px;
            padding: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        
        .control-btn {{
            padding: 8px 12px;
            border: 1px solid #e0e6ed;
            background: white;
            cursor: pointer;
            border-radius: 6px;
            font-size: 14px;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            min-width: 40px;
            text-align: center;
        }}
        
        .control-btn:hover {{
            background: #f8f9fa;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        
        .control-btn:active {{
            transform: translateY(0);
        }}
        
        .erd-content {{
            transform-origin: center center;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            padding: 40px;
            min-height: calc(100vh - 200px);
            overflow: auto;
        }}
        
        .fullscreen {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            z-index: 9999 !important;
            border-radius: 0 !important;
        }}
        
        .tips {{
            margin-top: 20px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        }}
        
        .tips h3 {{
            margin-top: 0;
            color: #fff;
        }}
        
        .tips ul {{
            margin: 0;
            padding-left: 20px;
        }}
        
        .tips li {{
            margin: 8px 0;
            opacity: 0.95;
        }}
        
        .zoom-indicator {{
            position: absolute;
            bottom: 15px;
            left: 15px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
        }}
        
        #mermaid-diagram {{
            width: 100%;
            height: 100%;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🗄️ Interactive Database Schema ERD</h1>
        <p>Explore your database structure with zoom, pan, and fullscreen capabilities</p>
    </div>
    
    <div class="erd-container" id="erd-container">
        <div class="controls">
            <button class="control-btn" onclick="zoomIn()" title="Zoom In">🔍+</button>
            <button class="control-btn" onclick="zoomOut()" title="Zoom Out">🔍-</button>
            <button class="control-btn" onclick="resetZoom()" title="Reset Zoom">⌂</button>
            <button class="control-btn" onclick="fitToWindow()" title="Fit to Window">⤢</button>
            <button class="control-btn" onclick="toggleFullscreen()" title="Toggle Fullscreen">⛶</button>
            <button class="control-btn" onclick="downloadSVG()" title="Download SVG">💾</button>
        </div>
        
        <div class="erd-content" id="erd-content">
            <div id="mermaid-diagram"></div>
        </div>
        
        <div class="zoom-indicator" id="zoom-indicator">100%</div>
    </div>
    
    <div class="tips">
        <h3>🎮 Navigation Controls</h3>
        <ul>
            <li><strong>Zoom:</strong> Use buttons, mouse wheel (Ctrl+scroll), or keyboard +/-</li>
            <li><strong>Pan:</strong> Click and drag the diagram when zoomed in</li>
            <li><strong>Reset:</strong> Click ⌂ or press '0' to return to original size</li>
            <li><strong>Fit:</strong> Click ⤢ to fit diagram to current window size</li>
            <li><strong>Fullscreen:</strong> Click ⛶ or press 'F' (Escape to exit)</li>
            <li><strong>Download:</strong> Click 💾 to save diagram as SVG file</li>
        </ul>
    </div>

    <script>
        // Initialize Mermaid
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{
                primaryColor: '#ff6b6b',
                primaryTextColor: '#333',
                primaryBorderColor: '#ff6b6b',
                lineColor: '#666',
                secondaryColor: '#4ecdc4',
                tertiaryColor: '#45b7d1'
            }},
            er: {{
                diagramPadding: 20,
                layoutDirection: 'TB',
                minEntityWidth: 100,
                minEntityHeight: 75,
                entityPadding: 15,
                stroke: '#333',
                fill: '#f9f9f9',
                fontSize: 12
            }}
        }});

        // Global variables
        let currentZoom = 1;
        let isDragging = false;
        let lastMouseX = 0;
        let lastMouseY = 0;
        let translateX = 0;
        let translateY = 0;
        let isFullscreen = false;

        // Render the Mermaid diagram
        const mermaidCode = `{mermaid_code}`;
        
        mermaid.render('erd-svg', mermaidCode).then((result) => {{
            document.getElementById('mermaid-diagram').innerHTML = result.svg;
            setupDragAndZoom();
        }});

        function setupDragAndZoom() {{
            const content = document.getElementById('erd-content');
            const diagram = document.querySelector('#mermaid-diagram svg');
            
            if (diagram) {{
                diagram.style.cursor = 'grab';
                
                // Mouse drag for panning
                diagram.addEventListener('mousedown', startDrag);
                document.addEventListener('mousemove', drag);
                document.addEventListener('mouseup', endDrag);
                
                // Touch support
                diagram.addEventListener('touchstart', startDrag);
                document.addEventListener('touchmove', drag);
                document.addEventListener('touchend', endDrag);
            }}
        }}

        function startDrag(e) {{
            e.preventDefault();
            isDragging = true;
            const clientX = e.clientX || e.touches[0].clientX;
            const clientY = e.clientY || e.touches[0].clientY;
            lastMouseX = clientX;
            lastMouseY = clientY;
            
            const diagram = document.querySelector('#mermaid-diagram svg');
            if (diagram) diagram.style.cursor = 'grabbing';
        }}

        function drag(e) {{
            if (!isDragging) return;
            e.preventDefault();
            
            const clientX = e.clientX || e.touches[0].clientX;
            const clientY = e.clientY || e.touches[0].clientY;
            const deltaX = clientX - lastMouseX;
            const deltaY = clientY - lastMouseY;
            
            translateX += deltaX;
            translateY += deltaY;
            
            updateTransform();
            
            lastMouseX = clientX;
            lastMouseY = clientY;
        }}

        function endDrag() {{
            isDragging = false;
            const diagram = document.querySelector('#mermaid-diagram svg');
            if (diagram) diagram.style.cursor = 'grab';
        }}

        function updateTransform() {{
            const content = document.getElementById('erd-content');
            content.style.transform = `translate(${{translateX}}px, ${{translateY}}px) scale(${{currentZoom}})`;
            
            // Update zoom indicator
            document.getElementById('zoom-indicator').textContent = Math.round(currentZoom * 100) + '%';
        }}

        function zoomIn() {{
            currentZoom = Math.min(currentZoom * 1.2, 5);
            updateTransform();
        }}

        function zoomOut() {{
            currentZoom = Math.max(currentZoom * 0.8, 0.1);
            updateTransform();
        }}

        function resetZoom() {{
            currentZoom = 1;
            translateX = 0;
            translateY = 0;
            updateTransform();
        }}

        function fitToWindow() {{
            const container = document.getElementById('erd-container');
            const content = document.getElementById('erd-content');
            const diagram = document.querySelector('#mermaid-diagram svg');
            
            if (diagram) {{
                const containerRect = container.getBoundingClientRect();
                const diagramRect = diagram.getBoundingClientRect();
                
                const scaleX = (containerRect.width - 80) / diagramRect.width;
                const scaleY = (containerRect.height - 80) / diagramRect.height;
                
                currentZoom = Math.min(scaleX, scaleY, 1);
                translateX = 0;
                translateY = 0;
                updateTransform();
            }}
        }}

        function toggleFullscreen() {{
            const container = document.getElementById('erd-container');
            
            if (!isFullscreen) {{
                container.classList.add('fullscreen');
                isFullscreen = true;
            }} else {{
                container.classList.remove('fullscreen');
                isFullscreen = false;
            }}
        }}

        function downloadSVG() {{
            const svg = document.querySelector('#mermaid-diagram svg');
            if (svg) {{
                const svgData = new XMLSerializer().serializeToString(svg);
                const svgBlob = new Blob([svgData], {{type: 'image/svg+xml;charset=utf-8'}});
                const svgUrl = URL.createObjectURL(svgBlob);
                
                const downloadLink = document.createElement('a');
                downloadLink.href = svgUrl;
                downloadLink.download = 'database-erd.svg';
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
                URL.revokeObjectURL(svgUrl);
            }}
        }}

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {{
            if (e.key === '+' || e.key === '=') {{
                e.preventDefault();
                zoomIn();
            }} else if (e.key === '-') {{
                e.preventDefault();
                zoomOut();
            }} else if (e.key === '0') {{
                e.preventDefault();
                resetZoom();
            }} else if (e.key === 'f' || e.key === 'F') {{
                e.preventDefault();
                toggleFullscreen();
            }} else if (e.key === 'Escape' && isFullscreen) {{
                e.preventDefault();
                toggleFullscreen();
            }} else if (e.key === 'r' || e.key === 'R') {{
                e.preventDefault();
                fitToWindow();
            }}
        }});

        // Mouse wheel zoom
        document.getElementById('erd-container').addEventListener('wheel', function(e) {{
            if (e.ctrlKey) {{
                e.preventDefault();
                const factor = e.deltaY > 0 ? 0.9 : 1.1;
                currentZoom = Math.max(0.1, Math.min(5, currentZoom * factor));
                updateTransform();
            }}
        }});

        // Auto-fit on window resize
        window.addEventListener('resize', function() {{
            if (!isFullscreen) {{
                setTimeout(fitToWindow, 100);
            }}
        }});

        // Initial fit
        setTimeout(fitToWindow, 1000);
    </script>
</body>
</html>"""

            # Write the HTML file
            html_path = Path(output_path).with_suffix('.html')
            html_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"🎯 Standalone zoomable ERD generated: {html_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error generating standalone ERD: {e}")
            return False
    
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
    
    def generate_enhanced_html_documentation(self, output_path: str, create_debug_erd: bool = False, 
                                            show_all_tables_in_erd: bool = True) -> bool:
        """Generate comprehensive HTML documentation with interactive features."""
        try:
            from pathlib import Path
            
            print("🔍 Analyzing database structure...")
            db_info = self.get_database_info()
            tables = self.get_tables_info()
            
            # Generate clean Mermaid ERD for embedding
            erd_mermaid_code = self.generate_enhanced_mermaid_erd(
                tables,
                max_tables=None if show_all_tables_in_erd else 6,
                strict_subset=not show_all_tables_in_erd,
                include_zoom_controls=False  # We'll add our own HTML controls
            )
            
            # Extract just the mermaid code (remove ``` markers)
            mermaid_diagram_code = erd_mermaid_code.replace('```mermaid\n', '').replace('\n```', '').strip()
            
            # Optionally emit a debug .erd.mmd file
            if create_debug_erd:
                erd_path = Path(output_path).with_suffix(".erd.mmd")
                erd_path.write_text(erd_mermaid_code, encoding="utf-8")
                print(f"📊 ERD debug file written: {erd_path}")
            
            # Generate comprehensive HTML content
            html_content = self._generate_complete_html_documentation(
                db_info, tables, mermaid_diagram_code
            )
            
            # Write the HTML documentation
            output_file = Path(output_path).with_suffix('.html')
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Generate markdown version for LLM consumption
            markdown_path = output_file.parent / f"{output_file.stem}_schema.md"
            markdown_success = self.generate_markdown_documentation(str(markdown_path))
            
            print(f"✅ Enhanced HTML documentation generated: {output_file}")
            if markdown_success:
                print(f"📄 LLM-optimized markdown schema generated: {markdown_path}")
            else:
                print(f"⚠️ Warning: Markdown generation failed for: {markdown_path}")
            print(f"📊 Analyzed {len(tables)} tables with {sum(table['row_count'] for table in tables):,} total records")
            print(f"📄 Generated interactive HTML documentation with collapsible sections and Mermaid rendering")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating HTML documentation: {e}")
            return False

    def generate_markdown_documentation(self, output_path: str) -> bool:
        """
        Generate LLM-optimized markdown documentation for the database schema.
        
        Args:
            output_path: Path where the markdown documentation will be saved
            
        Returns:
            bool: True if documentation was generated successfully, False otherwise
        """
        try:
            db_info = self.get_database_info()
            tables = self.get_tables_info()
            
            if not tables:
                print("❌ No tables found in database")
                return False
            
            # Generate markdown content
            markdown_content = self._generate_markdown_content(db_info, tables)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating markdown documentation: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return False

    def _generate_markdown_content(self, db_info: dict, tables: list) -> str:
        """Generate the complete markdown content."""
        
        # Sort tables by category for better organization
        categorized_tables = {}
        for table in tables:
            category = self.get_table_category(table['name'])
            if category not in categorized_tables:
                categorized_tables[category] = []
            categorized_tables[category].append(table)
        
        # Start building markdown
        md_lines = [
            "# Database Schema Documentation",
            "",
            "**Generated for LLM Consumption**",
            "",
            "## Database Overview",
            "",
            f"- **Database Size**: {db_info['file_size_mb']} MB",
            f"- **SQLite Version**: {db_info['sqlite_version']}",
            f"- **Last Modified**: {db_info['last_modified'][:10]}",
            f"- **Total Tables**: {len(tables)}",
            f"- **Total Records**: {sum(table['row_count'] for table in tables):,}",
            "",
            "## Table of Contents",
            ""
        ]
        
        # Generate table of contents
        for category, category_tables in categorized_tables.items():
            md_lines.append(f"### {category}")
            for table in category_tables:
                md_lines.append(f"- [{table['name']}](#{table['name'].lower().replace('_', '-')})")
            md_lines.append("")
        
        md_lines.extend([
            "---",
            "",
            "## Database Relationships Overview",
            "",
            "### Key Foreign Key Relationships",
            ""
        ])
        
        # Generate relationship summary
        all_relationships = []
        for table in tables:
            for fk in table.get('foreign_keys', []):
                all_relationships.append(f"- `{table['name']}.{fk['column']}` → `{fk['references_table']}.{fk['references_column']}`")
        
        if all_relationships:
            md_lines.extend(all_relationships)
        else:
            md_lines.append("- No foreign key relationships found")
        
        md_lines.extend([
            "",
            "---",
            "",
            "## Detailed Table Specifications",
            ""
        ])
        
        # Generate detailed table documentation
        for category, category_tables in categorized_tables.items():
            md_lines.extend([
                f"## {category} Tables",
                ""
            ])
            
            for table in category_tables:
                md_lines.extend(self._generate_table_markdown(table))
        
        return "\n".join(md_lines)

    def _generate_table_markdown(self, table: dict) -> list:
        """Generate markdown documentation for a single table."""
        md_lines = [
            f"### {table['name']}",
            ""
        ]
        
        # Basic info
        md_lines.extend([
            f"**Records**: {table['row_count']:,}",
            ""
        ])
        
        if table.get('table_comment'):
            md_lines.extend([
                f"**Description**: {table['table_comment']}",
                ""
            ])
        
        # Columns
        md_lines.extend([
            "#### Schema",
            "",
            "| Column | Type | Constraints | Description |",
            "|--------|------|-------------|-------------|"
        ])
        
        for col in table.get('columns', []):
            constraints = []
            if col['is_primary_key']:
                constraints.append('PK')
            if any(fk['column'] == col['name'] for fk in table.get('foreign_keys', [])):
                constraints.append('FK')
            if col.get('notnull', False):
                constraints.append('NOT NULL')
            
            constraint_str = ', '.join(constraints) if constraints else '-'
            description = col['name'].replace('_', ' ').title()
            
            md_lines.append(f"| `{col['name']}` | {col['type'] or 'TEXT'} | {constraint_str} | {description} |")
        
        # Foreign Keys
        if table.get('foreign_keys'):
            md_lines.extend([
                "",
                "#### Foreign Key Relationships",
                ""
            ])
            
            for fk in table['foreign_keys']:
                md_lines.append(f"- `{fk['column']}` references `{fk['references_table']}.{fk['references_column']}`")
        
        # Sample Data
        if table.get('sample_rows') and len(table['sample_rows']) > 0:
            md_lines.extend([
                "",
                "#### Sample Data",
                ""
            ])
            
            # Show first sample record as JSON-like structure
            sample = table['sample_rows'][0]
            md_lines.append("```json")
            md_lines.append("{")
            
            for i, col in enumerate(table.get('columns', [])):
                field_name = col['name']
                field_value = sample.get(field_name, None)
                
                # Format value appropriately
                if field_value is None:
                    formatted_value = "null"
                elif isinstance(field_value, str):
                    # Truncate long strings
                    if len(field_value) > 100:
                        formatted_value = f'"{field_value[:100]}..."'
                    else:
                        formatted_value = f'"{field_value}"'
                elif isinstance(field_value, (int, float)):
                    formatted_value = str(field_value)
                else:
                    formatted_value = f'"{str(field_value)}"'
                
                # Add comma except for last item
                comma = "," if i < len(table['columns']) - 1 else ""
                md_lines.append(f'  "{field_name}": {formatted_value}{comma}')
            
            md_lines.extend([
                "}",
                "```",
                ""
            ])
            
            if len(table['sample_rows']) > 1:
                md_lines.append(f"*({len(table['sample_rows'])} sample records available)*")
                md_lines.append("")
        
        # Add separator
        md_lines.extend([
            "---",
            ""
        ])
        
        return md_lines
    
    def _generate_complete_html_documentation(self, db_info: dict, tables: list, mermaid_code: str) -> str:
        """Generate the complete HTML documentation with modern styling and interactive features."""
        
        # Helper method to categorize tables
        def get_table_category(table_name: str) -> str:
            for category, table_list in self.table_categories.items():
                if table_name.lower() in [t.lower() for t in table_list]:
                    return category
            return 'other'
        
        # Categorize tables for organization
        categorized_tables = {'core': [], 'analytics': [], 'system': [], 'other': []}
        for table in tables:
            category = get_table_category(table['name'])
            categorized_tables[category].append(table)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🗄️ Database Schema Documentation - NAB Skill Similarity Engine</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <style>
        /* Enhanced custom styles for better readability and visual hierarchy */
        .mermaid {{
            background: white;
            border-radius: 0.75rem;
            box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
            border: 1px solid #e2e8f0;
        }}
        
        /* Smooth animations for collapsible content */
        .collapsible-content {{
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            overflow: hidden;
        }}
        
        .collapsible-content.collapsed {{
            max-height: 0;
            opacity: 0;
            transform: translateY(-10px);
        }}
        
        .collapsible-content.expanded {{
            max-height: 3000px;
            opacity: 1;
            transform: translateY(0);
        }}
        
        /* Enhanced collapsible sections */
        .collapsible {{
            margin-bottom: 1.5rem;
        }}
        
        .collapsible-header {{
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border: 1px solid #e2e8f0;
            border-radius: 0.75rem;
            padding: 1.5rem;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .collapsible-header:hover {{
            background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
            border-color: #cbd5e1;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}
        
        .collapsible-body {{
            padding: 1.5rem;
            background: white;
            border: 1px solid #e2e8f0;
            border-top: none;
            border-radius: 0 0 0.75rem 0.75rem;
        }}
        
        /* Table section styles for collapsible + tabbed layout */
        .table-section {{
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            overflow: hidden;
            margin-bottom: 1.5rem;
        }}
        
        .table-section.collapsed .table-content {{
            max-height: 0;
            opacity: 0;
            transform: translateY(-10px);
        }}
        
        .table-section.expanded .table-content {{
            max-height: 2000px;
            opacity: 1;
            transform: translateY(0);
        }}
        
        .table-content {{
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        .table-header-btn {{
            transition: all 0.2s ease;
        }}
        
        .table-header-btn:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }}
        
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        
        .schema-code {{
            background: #1e293b;
            color: #e2e8f0;
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
            line-height: 1.5;
            overflow-x: auto;
        }}
        
        /* Smooth rotate animation for chevron */
        .chevron {{
            transition: transform 0.3s ease;
        }}
        
        .table-section.expanded .chevron {{
            transform: rotate(180deg);
        }}
        
        /* Table cards with enhanced visual hierarchy */
        .table-card {{
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 1rem;
            overflow: hidden;
            transition: all 0.3s ease;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            height: fit-content;
        }}
        
        .table-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
            border-color: #3b82f6;
        }}
        
        .table-header {{
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            color: white;
            padding: 1.5rem;
            position: relative;
        }}
        
        .table-header::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #60a5fa, #3b82f6, #1d4ed8);
        }}
        
        .table-name {{
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .table-meta {{
            font-size: 0.875rem;
            opacity: 0.9;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .table-content {{
            padding: 1.5rem;
        }}
        
        /* Enhanced statistics display */
        .table-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: #f8fafc;
            border-radius: 0.75rem;
            border: 1px solid #e2e8f0;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.25rem;
        }}
        
        .stat-label {{
            font-size: 0.75rem;
            color: #64748b;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        /* Category badges with color coding */
        .badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-left: 0.5rem;
        }}
        
        .badge.core {{
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
            color: #1d4ed8;
            border: 1px solid #93c5fd;
        }}
        
        .badge.analytics {{
            background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
            color: #166534;
            border: 1px solid #86efac;
        }}
        
        .badge.system {{
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            color: #92400e;
            border: 1px solid #fcd34d;
        }}
        
        .badge.other {{
            background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
            color: #6b21a8;
            border: 1px solid #c4b5fd;
        }}
        
        /* Toggle arrow animation */
        .toggle {{
            transition: transform 0.3s ease;
            font-size: 1.25rem;
            color: #64748b;
        }}
        
        /* Enhanced code blocks */
        .code-block {{
            background: #1e293b;
            color: #e2e8f0;
            padding: 1.5rem;
            border-radius: 0.75rem;
            font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
            font-size: 0.875rem;
            line-height: 1.6;
            overflow-x: auto;
            border: 1px solid #334155;
            position: relative;
            margin: 1rem 0;
        }}
        
        .code-block::before {{
            content: 'SQL';
            position: absolute;
            top: 0.75rem;
            right: 0.75rem;
            background: #3b82f6;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.625rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        /* Enhanced syntax highlighting for SQL */
        .keyword {{ color: #60a5fa; font-weight: 600; }}
        .string {{ color: #34d399; }}
        .comment {{ color: #94a3b8; font-style: italic; }}
        
        /* Sample data styling */
        .sample-record {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 0.75rem 0;
        }}
        
        .field {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin: 0.5rem 0;
        }}
        
        .field-name {{
            font-weight: 600;
            color: #475569;
            min-width: 120px;
            font-size: 0.875rem;
        }}
        
        .field-value {{
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            background: white;
            padding: 0.375rem 0.75rem;
            border-radius: 0.375rem;
            border: 1px solid #e2e8f0;
            flex: 1;
            font-size: 0.875rem;
            word-break: break-all;
        }}
        
        /* ERD container styling */
        .erd-container {{
            position: relative;
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 1rem;
            overflow: hidden;
            min-height: 500px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        .erd-controls {{
            position: absolute;
            top: 1rem;
            right: 1rem;
            z-index: 50;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid #e2e8f0;
            border-radius: 0.75rem;
            padding: 0.75rem;
            display: flex;
            gap: 0.5rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }}
        
        .erd-btn {{
            padding: 0.5rem;
            border: 1px solid #e2e8f0;
            background: white;
            border-radius: 0.5rem;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 1rem;
            min-width: 2.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .erd-btn:hover {{
            background: #f1f5f9;
            border-color: #3b82f6;
            transform: translateY(-1px);
        }}
        
        /* Feature lists with enhanced styling */
        .feature-list {{
            list-style: none;
            padding: 0;
            margin: 1rem 0;
        }}
        
        .feature-list li {{
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            margin: 0.75rem 0;
            padding: 1rem;
            background: #f8fafc;
            border-radius: 0.5rem;
            border-left: 4px solid #3b82f6;
            transition: all 0.2s ease;
        }}
        
        .feature-list li:hover {{
            background: #f1f5f9;
            transform: translateX(4px);
        }}
        
        .feature-list .icon {{
            font-size: 1.25rem;
            margin-top: 0.125rem;
            flex-shrink: 0;
        }}
        
        /* Responsive grid for table cards */
        .table-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }}
        
        /* Smooth scroll for anchor links */
        html {{
            scroll-behavior: smooth;
        }}
        
        /* Enhanced heading styles */
        h4 {{
            color: #1e293b;
            font-weight: 600;
            margin: 1.5rem 0 1rem 0;
            font-size: 1.125rem;
        }}
        
        /* Mobile responsive adjustments */
        @media (max-width: 768px) {{
            .table-grid {{
                grid-template-columns: 1fr;
            }}
            
            .table-stats {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .erd-controls {{
                position: static;
                margin-bottom: 1rem;
                justify-content: center;
            }}
            
            .collapsible-header {{
                padding: 1rem;
            }}
            
            .table-content {{
                padding: 1rem;
            }}
            
            .field {{
                flex-direction: column;
                align-items: flex-start;
                gap: 0.5rem;
            }}
            
            .field-name {{
                min-width: auto;
            }}
        }}
        
        /* Print styles */
        @media print {{
            .erd-controls {{
                display: none;
            }}
            
            .table-card {{
                break-inside: avoid;
            }}
            
            .collapsible-content {{
                max-height: none !important;
                opacity: 1 !important;
                transform: none !important;
            }}
        }}
    </style>
</head>
<body class="bg-slate-50 min-h-screen">
    <!-- Header -->
    <header class="bg-gradient-to-r from-blue-600 to-blue-700 text-white py-8 mb-8 shadow-lg">
        <div class="max-w-7xl mx-auto px-4">
            <h1 class="text-4xl font-bold mb-2">🗄️ Database Schema Documentation</h1>
            <div class="text-xl opacity-90 mb-6">NAB Skill Similarity Engine - Workforce Intelligence Database</div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
                <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                    <div class="text-sm opacity-80 mb-1">📅 Generated</div>
                    <div class="font-semibold text-lg">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                    <div class="text-sm opacity-80 mb-1">💾 Database Size</div>
                    <div class="font-semibold text-lg">{db_info['file_size_mb']} MB</div>
                </div>
                <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                    <div class="text-sm opacity-80 mb-1">📊 Total Tables</div>
                    <div class="font-semibold text-lg">{len(tables)}</div>
                </div>
                <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                    <div class="text-sm opacity-80 mb-1">🔢 Total Records</div>
                    <div class="font-semibold text-lg">{sum(table['row_count'] for table in tables):,}</div>
                </div>
            </div>
        </div>
    </header>

    <!-- Navigation -->
    <div class="sticky top-0 bg-white border-b border-slate-200 z-50 mb-8 shadow-sm">
        <div class="max-w-7xl mx-auto px-4">
            <nav class="flex items-center gap-8 py-4 overflow-x-auto">
                <a href="#overview" class="text-slate-600 hover:text-blue-600 hover:bg-slate-100 px-4 py-2 rounded-md whitespace-nowrap font-medium transition-all">📊 Overview</a>
                <a href="#erd" class="text-slate-600 hover:text-blue-600 hover:bg-slate-100 px-4 py-2 rounded-md whitespace-nowrap font-medium transition-all">🔗 ERD</a>
                <a href="#table-of-contents" class="text-slate-600 hover:text-blue-600 hover:bg-slate-100 px-4 py-2 rounded-md whitespace-nowrap font-medium transition-all">📑 Table of Contents</a>
                <a href="#tables" class="text-slate-600 hover:text-blue-600 hover:bg-slate-100 px-4 py-2 rounded-md whitespace-nowrap font-medium transition-all">📋 Tables</a>
                <a href="#business-context" class="text-slate-600 hover:text-blue-600 hover:bg-slate-100 px-4 py-2 rounded-md whitespace-nowrap font-medium transition-all">🏷️ Business Context</a>
                <a href="#developer-guide" class="text-slate-600 hover:text-blue-600 hover:bg-slate-100 px-4 py-2 rounded-md whitespace-nowrap font-medium transition-all">🔧 Developer Guide</a>
            </nav>
        </div>
    </div>

    <div class="max-w-7xl mx-auto px-4">
        <!-- Overview Section -->
        <section id="overview" class="bg-white rounded-xl p-8 mb-8 shadow-md">
            <h2 class="text-3xl font-bold text-blue-600 mb-6 flex items-center gap-2">📊 Database Overview</h2>
            <p>This comprehensive documentation covers the NAB Skill Similarity Engine SQLite database, which integrates job architecture, skill taxonomies, workforce context, movement analysis, and pre-computed similarities to support career pathway analysis, workforce planning, and strategic workforce intelligence.</p>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
                <!-- Database Information Card -->
                <div class="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="bg-white/20 rounded-lg p-2">
                            <span class="text-2xl">🗄️</span>
                        </div>
                        <h3 class="text-lg font-semibold">Database Info</h3>
                    </div>
                    <div class="space-y-2 text-sm">
                        <div class="flex items-center gap-2">
                            <span class="text-blue-200">📂</span>
                            <span class="opacity-90">Size: {db_info['file_size_mb']} MB</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="text-blue-200">⚙️</span>
                            <span class="opacity-90">SQLite {db_info['sqlite_version']}</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="text-blue-200">🕒</span>
                            <span class="opacity-90">Updated {db_info['last_modified'][:10]}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Quick Statistics Card -->
                <div class="bg-gradient-to-br from-emerald-500 to-emerald-600 text-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="bg-white/20 rounded-lg p-2">
                            <span class="text-2xl">📊</span>
                        </div>
                        <h3 class="text-lg font-semibold">Quick Stats</h3>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="text-center">
                            <div class="text-2xl font-bold mb-1">{len(categorized_tables['core'])}</div>
                            <div class="text-xs opacity-90 uppercase tracking-wide">Core Tables</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold mb-1">{len(categorized_tables['analytics'])}</div>
                            <div class="text-xs opacity-90 uppercase tracking-wide">Analytics</div>
                        </div>
                    </div>
                </div>
                
                <!-- Table Categories Card -->
                <div class="bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="bg-white/20 rounded-lg p-2">
                            <span class="text-2xl">🏷️</span>
                        </div>
                        <h3 class="text-lg font-semibold">Categories</h3>
                    </div>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between items-center">
                            <span class="opacity-90">System</span>
                            <span class="bg-white/20 px-2 py-1 rounded-full text-xs font-semibold">{len(categorized_tables['system'])}</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="opacity-90">Other</span>
                            <span class="bg-white/20 px-2 py-1 rounded-full text-xs font-semibold">{len(categorized_tables['other'])}</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="opacity-90">Total</span>
                            <span class="bg-white/30 px-2 py-1 rounded-full text-xs font-bold">{len(tables)}</span>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- ERD Section -->
        <section id="erd" class="bg-white rounded-xl p-8 mb-8 shadow-md">
            <h2 class="text-3xl font-bold text-blue-600 mb-6 flex items-center gap-2">🔗 Entity Relationship Diagram</h2>
            <p>Interactive diagram showing table relationships and key columns. Use the controls to zoom, pan, and explore the database structure.</p>
            
            <div class="erd-container">
                <div class="erd-controls">
                    <button class="erd-btn" onclick="zoomIn()" title="Zoom In">🔍+</button>
                    <button class="erd-btn" onclick="zoomOut()" title="Zoom Out">🔍−</button>
                    <button class="erd-btn" onclick="resetZoom()" title="Reset">⌂</button>
                    <button class="erd-btn" onclick="fitToWindow()" title="Fit to Window">⤢</button>
                </div>
                <div id="mermaid-container">
                    <div id="mermaid-diagram"></div>
                </div>
            </div>
            
            {self._generate_text_based_erd_html(tables)}
        </section>

        <!-- Table of Contents Section -->
        <section id="table-of-contents" class="bg-white rounded-xl p-8 mb-8 shadow-md">
            <h2 class="text-3xl font-bold text-blue-600 mb-6 flex items-center gap-2">📑 Table of Contents</h2>
            <p class="text-gray-600 mb-6">Quick navigation to all database tables organized by category. Click any table name to jump directly to its detailed documentation.</p>
            
            {self._generate_table_of_contents_html(categorized_tables)}
        </section>

        <!-- Tables Section -->
        <section id="tables" class="bg-white rounded-xl p-8 mb-8 shadow-md">
            <h2 class="text-3xl font-bold text-blue-600 mb-6 flex items-center gap-2">📋 Table Definitions</h2>
            
            {self._generate_table_categories_html(categorized_tables)}
        </section>

        <!-- Business Context Section -->
        <section id="business-context" class="bg-white rounded-xl p-8 mb-8 shadow-md">
            {self._generate_business_context_html()}
        </section>

        <!-- Developer Guide Section -->
        <section id="developer-guide" class="bg-white rounded-xl p-8 mb-8 shadow-md">
            {self._generate_developer_guide_html()}
        </section>
    </div>

    <script>
        // Initialize Mermaid
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{
                primaryColor: '#3b82f6',
                primaryTextColor: '#1e293b',
                primaryBorderColor: '#3b82f6',
                lineColor: '#64748b',
                secondaryColor: '#06b6d4',
                tertiaryColor: '#10b981'
            }},
            er: {{
                diagramPadding: 20,
                layoutDirection: 'TB',
                minEntityWidth: 100,
                minEntityHeight: 75,
                entityPadding: 15,
                stroke: '#64748b',
                fill: '#f8fafc',
                fontSize: 12
            }}
        }});

        // Mermaid diagram rendering
        const mermaidCode = `{mermaid_code}`;
        mermaid.render('erd-svg', mermaidCode).then((result) => {{
            document.getElementById('mermaid-diagram').innerHTML = result.svg;
            setupERDInteractivity();
        }});

        // ERD interaction variables
        let erdZoom = 1;
        let isDragging = false;
        let lastX = 0, lastY = 0;
        let translateX = 0, translateY = 0;

        function setupERDInteractivity() {{
            const container = document.getElementById('mermaid-container');
            const diagram = document.querySelector('#mermaid-diagram svg');
            
            if (diagram) {{
                diagram.style.cursor = 'grab';
                
                // Mouse events
                diagram.addEventListener('mousedown', startDrag);
                document.addEventListener('mousemove', drag);
                document.addEventListener('mouseup', endDrag);
                
                // Wheel zoom
                container.addEventListener('wheel', handleWheel);
            }}
        }}

        function startDrag(e) {{
            isDragging = true;
            lastX = e.clientX;
            lastY = e.clientY;
            document.querySelector('#mermaid-diagram svg').style.cursor = 'grabbing';
        }}

        function drag(e) {{
            if (!isDragging) return;
            
            const deltaX = e.clientX - lastX;
            const deltaY = e.clientY - lastY;
            
            translateX += deltaX;
            translateY += deltaY;
            
            updateTransform();
            
            lastX = e.clientX;
            lastY = e.clientY;
        }}

        function endDrag() {{
            isDragging = false;
            const svg = document.querySelector('#mermaid-diagram svg');
            if (svg) svg.style.cursor = 'grab';
        }}

        function handleWheel(e) {{
            if (e.ctrlKey) {{
                e.preventDefault();
                const factor = e.deltaY > 0 ? 0.9 : 1.1;
                erdZoom = Math.max(0.1, Math.min(3, erdZoom * factor));
                updateTransform();
            }}
        }}

        function updateTransform() {{
            const container = document.getElementById('mermaid-container');
            container.style.transform = `translate(${{translateX}}px, ${{translateY}}px) scale(${{erdZoom}})`;
        }}

        function zoomIn() {{
            erdZoom = Math.min(erdZoom * 1.2, 3);
            updateTransform();
        }}

        function zoomOut() {{
            erdZoom = Math.max(erdZoom * 0.8, 0.1);
            updateTransform();
        }}

        function resetZoom() {{
            erdZoom = 1;
            translateX = 0;
            translateY = 0;
            updateTransform();
        }}

        function fitToWindow() {{
            const container = document.querySelector('.erd-container');
            const mermaidContainer = document.getElementById('mermaid-container');
            const diagram = document.querySelector('#mermaid-diagram svg');
            
            if (diagram) {{
                const containerRect = container.getBoundingClientRect();
                const diagramRect = diagram.getBoundingClientRect();
                
                const scaleX = (containerRect.width - 40) / diagramRect.width;
                const scaleY = (containerRect.height - 40) / diagramRect.height;
                
                erdZoom = Math.min(scaleX, scaleY, 1);
                translateX = 0;
                translateY = 0;
                updateTransform();
            }}
        }}

        // Collapsible sections
        function toggleCollapsible(element) {{
            const content = element.querySelector('.collapsible-content');
            const toggle = element.querySelector('.toggle');
            
            if (content.classList.contains('expanded')) {{
                content.classList.remove('expanded');
                content.classList.add('collapsed');
                toggle.style.transform = 'rotate(0deg)';
            }} else {{
                content.classList.remove('collapsed');
                content.classList.add('expanded');
                toggle.style.transform = 'rotate(180deg)';
            }}
        }}
        
        // Table section toggle
        function toggleTableSection(tableId) {{
            const tableSection = document.getElementById(tableId);
            
            if (tableSection.classList.contains('collapsed')) {{
                tableSection.classList.remove('collapsed');
                tableSection.classList.add('expanded');
            }} else {{
                tableSection.classList.remove('expanded');
                tableSection.classList.add('collapsed');
            }}
        }}
        
        // Table tab switching
        function showTableTab(tableId, tabName) {{
            // Hide all tab contents for this table
            document.querySelectorAll(`#${{tableId}} .tab-content`).forEach(content => {{
                content.classList.remove('active');
            }});
            
            // Remove active class from all tab buttons for this table
            document.querySelectorAll(`.tab-btn-${{tableId}}`).forEach(button => {{
                button.classList.remove('active-tab');
                button.classList.add('border-transparent', 'text-gray-500');
                
                // Remove color-specific classes
                button.classList.remove('border-blue-500', 'text-blue-600');
                button.classList.remove('border-green-500', 'text-green-600');
                button.classList.remove('border-purple-500', 'text-purple-600');
                button.classList.remove('border-red-500', 'text-red-600');
                button.classList.remove('border-yellow-500', 'text-yellow-600');
            }});
            
            // Show selected tab content
            document.getElementById(`${{tableId}}-${{tabName}}`).classList.add('active');
            
            // Add active class to clicked tab button
            const clickedButton = event.target;
            clickedButton.classList.add('active-tab');
            clickedButton.classList.remove('border-transparent', 'text-gray-500');
            
            // Add appropriate color based on table category
            const tableCategory = clickedButton.getAttribute('data-category') || 'core';
            if (tableCategory === 'core') {{
                clickedButton.classList.add('border-blue-500', 'text-blue-600');
            }} else if (tableCategory === 'analytics') {{
                clickedButton.classList.add('border-green-500', 'text-green-600');
            }} else if (tableCategory === 'system') {{
                clickedButton.classList.add('border-purple-500', 'text-purple-600');
            }} else {{
                clickedButton.classList.add('border-gray-500', 'text-gray-600');
            }}
        }}
        
        // Expand/collapse all tables
        function expandAllTables() {{
            document.querySelectorAll('.table-section').forEach(section => {{
                section.classList.remove('collapsed');
                section.classList.add('expanded');
            }});
        }}
        
        function collapseAllTables() {{
            document.querySelectorAll('.table-section').forEach(section => {{
                section.classList.remove('expanded');
                section.classList.add('collapsed');
            }});
        }}

        // Smooth scrolling for navigation
        document.querySelectorAll('.nav a').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{
                        behavior: 'smooth',
                        block: 'start'
                    }});
                }}
            }});
        }});

        // Auto-expand first few table categories
        document.addEventListener('DOMContentLoaded', function() {{
            const collapsibles = document.querySelectorAll('.collapsible');
            collapsibles.forEach((collapsible, index) => {{
                if (index < 2) {{ // Auto-expand first 2 categories
                    collapsible.classList.add('expanded');
                }}
            }});
            
            // Auto-fit ERD after a short delay
            setTimeout(fitToWindow, 1000);
        }});
    </script>
</body>
</html>"""
        
        return html_content
    
    def _generate_text_based_erd_html(self, tables: list) -> str:
        """Generate HTML version of text-based ERD as fallback."""
        core_tables = [t for t in tables if t['name'].startswith('core_')]
        analytics_tables = [t for t in tables if t['name'].startswith('analytics_')]
        
        html_lines = ['<div class="border border-slate-200 rounded-lg mb-4 overflow-hidden">']
        html_lines.append('<div class="bg-slate-50 hover:bg-slate-100 p-4 cursor-pointer flex items-center justify-between font-semibold transition-colors" onclick="toggleCollapsible(this.parentElement)">')
        html_lines.append('<span class="text-slate-800">📋 Alternative Text-Based Relationship Map</span>')
        html_lines.append('<span class="toggle text-lg transition-transform duration-300">▼</span>')
        html_lines.append('</div>')
        html_lines.append('<div class="collapsible-content">')
        html_lines.append('<div class="p-6">')
        html_lines.append('<p><em>If the Mermaid diagram above doesn\'t render properly, here\'s a text-based view:</em></p>')
        
        if core_tables:
            html_lines.append('<h4>🏗️ Core Data Tables</h4>')
            html_lines.append('<ul class="feature-list">')
            for table in core_tables[:6]:
                pk_columns = [col['name'] for col in table['columns'] if col['is_primary_key']]
                fk_relationships = [f"→ {fk['references_table']}" for fk in table['foreign_keys']]
                
                html_lines.append(f'<li><span class="icon">📊</span>')
                html_lines.append(f'<strong>{table["name"]}</strong> ({table["row_count"]:,} records)')
                if pk_columns:
                    html_lines.append(f'<br><small>Primary Key: {", ".join(pk_columns)}</small>')
                if fk_relationships:
                    html_lines.append(f'<br><small>References: {", ".join(fk_relationships)}</small>')
                html_lines.append('</li>')
            html_lines.append('</ul>')
        
        if analytics_tables:
            html_lines.append('<h4>📊 Analytics Tables</h4>')
            html_lines.append('<ul class="feature-list">')
            for table in analytics_tables[:6]:
                pk_columns = [col['name'] for col in table['columns'] if col['is_primary_key']]
                fk_relationships = [f"→ {fk['references_table']}" for fk in table['foreign_keys']]
                
                html_lines.append(f'<li><span class="icon">📈</span>')
                html_lines.append(f'<strong>{table["name"]}</strong> ({table["row_count"]:,} records)')
                if pk_columns:
                    html_lines.append(f'<br><small>Primary Key: {", ".join(pk_columns)}</small>')
                if fk_relationships:
                    html_lines.append(f'<br><small>References: {", ".join(fk_relationships)}</small>')
                html_lines.append('</li>')
            html_lines.append('</ul>')
        
        html_lines.extend(['</div>', '</div>', '</div>'])
        return '\n'.join(html_lines)
    
    def _get_category_icon(self, category: str) -> str:
        """Get emoji icon for table category."""
        icons = {
            'core': '🏗️',
            'analytics': '📊', 
            'system': '⚙️',
            'other': '🔧'
        }
        return icons.get(category, '📋')
    
    def _generate_table_of_contents_html(self, categorized_tables: dict) -> str:
        """Generate table of contents with quick navigation to all tables."""
        html_content = []
        
        # Category color mapping
        category_colors = {
            'core': 'blue',
            'analytics': 'green', 
            'system': 'purple',
            'other': 'gray'
        }
        
        html_content.append('<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">')
        
        for category, tables in categorized_tables.items():
            if not tables:
                continue
                
            color = category_colors.get(category, 'gray')
            icon = self._get_category_icon(category)
            
            html_content.append(f'''
            <div class="bg-gradient-to-br from-{color}-50 to-{color}-100 border border-{color}-200 rounded-xl p-6">
                <div class="flex items-center gap-3 mb-4">
                    <span class="text-2xl">{icon}</span>
                    <h3 class="text-xl font-bold text-{color}-900 capitalize">{category} Tables</h3>
                    <span class="bg-{color}-200 text-{color}-800 px-2 py-1 rounded-full text-sm font-medium">{len(tables)}</span>
                </div>
                <div class="space-y-2">''')
            
            for table in tables:
                table_name = table['name']
                record_count = table.get('row_count', 0)
                column_count = len(table.get('columns', []))
                
                html_content.append(f'''
                    <a href="#table-{table_name}" class="block p-3 bg-white hover:bg-{color}-50 border border-{color}-200 rounded-lg transition-all duration-200 hover:shadow-md">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="font-medium text-{color}-900">{table_name}</div>
                                <div class="text-sm text-{color}-600">{record_count:,} records • {column_count} columns</div>
                            </div>
                            <svg class="w-4 h-4 text-{color}-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                            </svg>
                        </div>
                    </a>''')
            
            html_content.append('</div></div>')
        
        html_content.append('</div>')
        
        # Add expand/collapse all controls
        html_content.append('''
        <div class="flex justify-center space-x-4 mt-8">
            <button onclick="expandAllTables()" class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg transition-colors font-medium">
                📖 Expand All Tables
            </button>
            <button onclick="collapseAllTables()" class="bg-gray-500 hover:bg-gray-600 text-white px-6 py-3 rounded-lg transition-colors font-medium">
                📚 Collapse All Tables
            </button>
        </div>''')
        
        return '\n'.join(html_content)
    
    def _generate_table_categories_html(self, categorized_tables: dict) -> str:
        """Generate HTML for table categories with collapsible + tabbed sections."""
        categories = {
            'core': {'title': '🏗️ Core Data Tables', 'desc': 'Foundation tables containing primary business entities', 'color': 'blue'},
            'analytics': {'title': '📊 Analytics Tables', 'desc': 'Pre-computed analytics and derived insights', 'color': 'green'},
            'system': {'title': '⚙️ System Tables', 'desc': 'System metadata and configuration', 'color': 'purple'},
            'other': {'title': '🔧 Other Tables', 'desc': 'Additional tables and temporary structures', 'color': 'gray'}
        }
        
        html_sections = []
        table_counter = 0
        
        # Generate individual table sections with collapsible + tabbed layout
        for category, config in categories.items():
            if not categorized_tables[category]:
                continue
                
            for table in sorted(categorized_tables[category], key=lambda x: x['name']):
                table_counter += 1
                table_id = f"table-{table['name']}"
                color = config['color']
                icon = self._get_category_icon(category)
                
                # Count different column types
                pk_count = len([c for c in table['columns'] if c['is_primary_key']])
                fk_count = len(table['foreign_keys'])
                total_cols = len(table['columns'])
                
                html_sections.append(f'''
                <!-- Table {table_counter}: {table['name']} -->
                <div class="table-section expanded mb-6" id="{table_id}">
                    <!-- Collapsible Header -->
                    <button class="table-header-btn w-full bg-gradient-to-r from-{color}-500 to-{color}-600 text-white p-6 rounded-t-lg hover:from-{color}-600 hover:to-{color}-700 transition-all duration-200" onclick="toggleTableSection('{table_id}')">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-4">
                                <span class="text-3xl">{icon}</span>
                                <div class="text-left">
                                    <h3 class="text-2xl font-bold">{table['name']}</h3>
                                    <p class="text-{color}-100">{config['desc']}</p>
                                </div>
                                <span class="bg-{color}-100 text-{color}-800 px-3 py-1 rounded-full text-sm font-medium">{category.upper()}</span>
                            </div>
                            <div class="flex items-center space-x-4">
                                <div class="text-right">
                                    <div class="text-2xl font-bold">{table.get('row_count', 0):,}</div>
                                    <div class="text-{color}-100 text-sm">records</div>
                                </div>
                                <svg class="chevron w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                                </svg>
                            </div>
                        </div>
                    </button>
                    
                    <!-- Collapsible Content -->
                    <div class="table-content bg-white border border-gray-200 border-t-0 rounded-b-lg">
                        <!-- Tab Navigation -->
                        <div class="flex border-b border-gray-200">
                            <button class="tab-btn-{table_id} active-tab px-6 py-3 border-b-2 border-{color}-500 text-{color}-600 font-medium" data-category="{category}" onclick="showTableTab('{table_id}', 'overview')">
                                📋 Overview
                            </button>
                            <button class="tab-btn-{table_id} px-6 py-3 border-b-2 border-transparent text-gray-500 hover:text-gray-700" data-category="{category}" onclick="showTableTab('{table_id}', 'schema')">
                                🏗️ Schema
                            </button>
                            <button class="tab-btn-{table_id} px-6 py-3 border-b-2 border-transparent text-gray-500 hover:text-gray-700" data-category="{category}" onclick="showTableTab('{table_id}', 'data')">
                                📊 Data
                            </button>
                            <button class="tab-btn-{table_id} px-6 py-3 border-b-2 border-transparent text-gray-500 hover:text-gray-700" data-category="{category}" onclick="showTableTab('{table_id}', 'relationships')">
                                🔗 Relationships
                            </button>
                        </div>
                        
                        <!-- Tab Content -->
                        <div class="p-6">
                            {self._generate_table_overview_tab(table, color)}
                            {self._generate_table_schema_tab(table, table_id)}
                            {self._generate_table_data_tab(table, table_id)}
                            {self._generate_table_relationships_tab(table, table_id)}
                        </div>
                    </div>
                </div>''')
        
        return '\n'.join(html_sections)
    
    def _generate_table_overview_tab(self, table: dict, color: str) -> str:
        """Generate the overview tab content for a table."""
        pk_count = len([c for c in table['columns'] if c['is_primary_key']])
        fk_count = len(table['foreign_keys'])
        total_cols = len(table['columns'])
        
        return f'''
        <div id="table-{table['name']}-overview" class="tab-content active">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-{color}-50 p-4 rounded-lg">
                    <h4 class="font-semibold text-{color}-900 mb-2">📊 Statistics</h4>
                    <div class="space-y-1 text-sm">
                        <div><strong>Records:</strong> {table.get('row_count', 0):,}</div>
                        <div><strong>Columns:</strong> {total_cols}</div>
                        <div><strong>Primary Keys:</strong> {pk_count}</div>
                        <div><strong>Foreign Keys:</strong> {fk_count}</div>
                    </div>
                </div>
                <div class="bg-blue-50 p-4 rounded-lg">
                    <h4 class="font-semibold text-blue-900 mb-2">🎯 Purpose</h4>
                    <p class="text-sm text-blue-800">Table storing {table['name'].replace('_', ' ')} data with comprehensive metadata and relationships.</p>
                </div>
                <div class="bg-purple-50 p-4 rounded-lg">
                    <h4 class="font-semibold text-purple-900 mb-2">🔧 Usage</h4>
                    <p class="text-sm text-purple-800">Used for {table['name'].replace('analytics_', '').replace('core_', '').replace('_', ' ')} operations and analysis.</p>
                </div>
            </div>
        </div>'''
    
    def _generate_table_schema_tab(self, table: dict, table_id: str) -> str:
        """Generate the schema tab content for a table."""
        # Generate complete CREATE TABLE statement
        schema_lines = [f"CREATE TABLE {table['name']} ("]
        
        for i, col in enumerate(table['columns']):
            col_type = col['type'] or 'TEXT'
            constraints = []
            
            if col['is_primary_key']:
                constraints.append('PRIMARY KEY')
            if col.get('notnull', False):
                constraints.append('NOT NULL')
            if col.get('default_value'):
                constraints.append(f"DEFAULT {col['default_value']}")
                
            constraint_str = ' ' + ' '.join(constraints) if constraints else ''
            comma = ',' if i < len(table['columns']) - 1 or table['foreign_keys'] else ''
            
            schema_lines.append(f"&nbsp;&nbsp;{col['name']} {col_type}{constraint_str}{comma}")
        
        # Add foreign key constraints
        for i, fk in enumerate(table['foreign_keys']):
            comma = ',' if i < len(table['foreign_keys']) - 1 else ''
            schema_lines.append(f"&nbsp;&nbsp;FOREIGN KEY ({fk['column']}) REFERENCES {fk['references_table']}({fk['references_column']}){comma}")
        
        schema_lines.append(");")
        schema_sql = '<br>'.join(schema_lines)
        
        return f'''
        <div id="{table_id}-schema" class="tab-content">
            <div class="schema-code p-6 rounded-lg">
                {schema_sql}
            </div>
        </div>'''
    
    def _generate_table_data_tab(self, table: dict, table_id: str) -> str:
        """Generate the data tab content for a table with schema and sample data."""
        html = f'<div id="{table_id}-data" class="tab-content">'
        
        if table['columns']:
            # Field Definitions Section
            html += '''
            <div class="mb-8">
                <h4 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <span>🏗️</span> Field Definitions
                </h4>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Field</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Constraints</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">'''
            
            for i, col in enumerate(table['columns']):
                bg_class = 'bg-gray-50' if i % 2 == 1 else ''
                constraints = []
                
                if col['is_primary_key']:
                    constraints.append('🗝️ PK')
                if any(fk['column'] == col['name'] for fk in table['foreign_keys']):
                    constraints.append('🔗 FK')
                if col.get('notnull', False):
                    constraints.append('NOT NULL')
                    
                constraint_str = ', '.join(constraints) if constraints else '-'
                
                html += f'''
                            <tr class="{bg_class}">
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{col['name']}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{col['type'] or 'TEXT'}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{constraint_str}</td>
                                <td class="px-6 py-4 text-sm text-gray-500">{col['name'].replace('_', ' ').title()} field</td>
                            </tr>'''
            
            html += '''
                        </tbody>
                    </table>
                </div>
            </div>'''
            
            # Sample Data Section
            html += '''
            <div>
                <h4 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <span>📊</span> Sample Data
                </h4>'''
            
            if table.get('sample_rows') and len(table['sample_rows']) > 0:
                # Show sample records in a nice format
                html += '<div class="space-y-4">'
                
                for i, sample in enumerate(table['sample_rows'][:3], 1):  # Show up to 3 samples
                    html += f'''
                    <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
                        <div class="flex items-center gap-2 mb-3">
                            <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">Sample Record {i}</span>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">'''
                    
                    # Show each field and its value
                    for col in table['columns']:
                        field_name = col['name']
                        field_value = sample.get(field_name, 'NULL')
                        
                        # Format the value nicely
                        if field_value is None:
                            display_value = '<span class="text-gray-400 italic">NULL</span>'
                        elif isinstance(field_value, str) and len(str(field_value)) > 50:
                            display_value = f'<span class="text-gray-700">{str(field_value)[:50]}...</span>'
                        else:
                            display_value = f'<span class="text-gray-700">{str(field_value)}</span>'
                        
                        # Add constraint indicators
                        indicators = []
                        if col['is_primary_key']:
                            indicators.append('<span class="text-blue-600">🗝️</span>')
                        if any(fk['column'] == field_name for fk in table['foreign_keys']):
                            indicators.append('<span class="text-green-600">🔗</span>')
                        
                        indicator_str = ' '.join(indicators)
                        
                        html += f'''
                            <div class="bg-white p-3 rounded border border-blue-100">
                                <div class="text-xs font-medium text-blue-700 mb-1 flex items-center gap-1">
                                    {field_name} {indicator_str}
                                </div>
                                <div class="text-sm break-words">{display_value}</div>
                            </div>'''
                    
                    html += '</div></div>'
                
                html += '</div>'
                
                # Add note about truncation if there are more records
                if len(table['sample_rows']) > 3:
                    html += f'''
                    <div class="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                        <p class="text-sm text-gray-600 italic">
                            Showing 3 of {len(table['sample_rows'])} available sample records. 
                            Complete data available in the database.
                        </p>
                    </div>'''
            else:
                # No sample data available
                html += '''
                <div class="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
                    <div class="text-gray-400 text-4xl mb-2">📭</div>
                    <p class="text-gray-600 font-medium">No sample data available</p>
                    <p class="text-sm text-gray-500 mt-1">This table may be empty or sample data wasn't collected during schema analysis.</p>
                </div>'''
            
            html += '</div>'
        else:
            html += '<p class="text-gray-600">No column information available.</p>'
        
        html += '</div>'
        return html
    
    def _generate_table_relationships_tab(self, table: dict, table_id: str) -> str:
        """Generate the relationships tab content for a table."""
        html = f'<div id="{table_id}-relationships" class="tab-content"><div class="space-y-4">'
        
        # Foreign keys (what this table references)
        if table['foreign_keys']:
            html += '''
            <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                <h4 class="font-semibold text-green-800 mb-2">🔗 References (Foreign Keys)</h4>
                <div class="space-y-1 text-sm text-green-700">'''
            
            for fk in table['foreign_keys']:
                html += f'<div><strong>{fk["column"]}</strong> → {fk["references_table"]}.{fk["references_column"]}</div>'
            
            html += '</div></div>'
        
        # Referenced by (what tables reference this table)
        html += '''
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 class="font-semibold text-blue-800 mb-2">📊 Referenced By</h4>
            <p class="text-sm text-blue-700">Check other tables to see which ones reference this table.</p>
        </div>'''
        
        html += '</div></div>'
        return html
    
    def _generate_table_card_html(self, table: dict) -> str:
        """Generate HTML for individual table card."""
        # Count different column types
        pk_count = len([c for c in table['columns'] if c['is_primary_key']])
        fk_count = len(table['foreign_keys'])
        total_cols = len(table['columns'])
        
        # Create schema preview
        schema_preview = []
        for col in table['columns'][:5]:  # Show first 5 columns
            col_type = col['type'] or 'TEXT'
            pk_indicator = ' 🗝️' if col['is_primary_key'] else ''
            fk_indicator = ' 🔗' if any(fk['column'] == col['name'] for fk in table['foreign_keys']) else ''
            schema_preview.append(f"  {col['name']} {col_type}{pk_indicator}{fk_indicator}")
        
        if len(table['columns']) > 5:
            schema_preview.append(f"  ... and {len(table['columns']) - 5} more columns")
        
        # Foreign key relationships
        fk_html = ""
        if table['foreign_keys']:
            fk_html = '''
                <div style="margin-top: 1.5rem;">
                    <h4 style="margin-bottom: 0.75rem; color: #374151; font-weight: 600;">🔗 Foreign Key Relationships</h4>
                    <div class="space-y-2">
            '''
            for fk in table['foreign_keys'][:3]:  # Show first 3 FKs
                fk_html += f'''
                    <div class="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
                        <span class="text-blue-600 font-mono text-sm bg-blue-50 px-2 py-1 rounded">{fk["column"]}</span>
                        <span class="text-slate-400">→</span>
                        <span class="text-emerald-600 font-mono text-sm bg-emerald-50 px-2 py-1 rounded">{fk["references_table"]}.{fk["references_column"]}</span>
                    </div>
                '''
            if len(table['foreign_keys']) > 3:
                fk_html += f'<div class="text-sm text-slate-500 italic">... and {len(table["foreign_keys"]) - 3} more relationships</div>'
            fk_html += '</div></div>'
        
        # Sample data preview
        sample_html = ""
        if table['sample_rows']:
            sample_html = '''
                <div style="margin-top: 1.5rem;">
                    <h4 style="margin-bottom: 0.75rem; color: #374151; font-weight: 600;">📋 Sample Data</h4>
                    <div class="space-y-3">
            '''
            for i, sample in enumerate(table['sample_rows'][:2], 1):  # Show 2 samples
                sample_html += f'''
                    <div class="sample-record">
                        <div class="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                            <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">Record {i}</span>
                        </div>
                        <div class="grid grid-cols-1 gap-2">
                '''
                for key, value in list(sample.items())[:4]:  # Show first 4 fields
                    if value is not None:
                        display_value = str(value)[:60] + ('...' if len(str(value)) > 60 else '')
                        sample_html += f'''
                            <div class="field">
                                <span class="field-name">{key}:</span>
                                <span class="field-value">{display_value}</span>
                            </div>
                        '''
                sample_html += '</div></div>'
            sample_html += '</div></div>'
        
        # Table category for styling
        category = self.get_table_category(table['name'])
        
        # Category-specific header styling
        header_gradients = {
            'core': 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
            'analytics': 'linear-gradient(135deg, #059669 0%, #047857 100%)',
            'system': 'linear-gradient(135deg, #d97706 0%, #b45309 100%)',
            'other': 'linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%)'
        }
        
        header_style = f"background: {header_gradients.get(category, header_gradients['other'])};"
        
        return f'''
        <div class="table-card">
            <div class="table-header" style="{header_style}">
                <div class="table-name">
                    📊 {table['name']}
                    <span class="badge {category}">{category.title()}</span>
                </div>
                <div class="table-meta">
                    📈 {table['row_count']:,} records · {table['object_type'].title()}
                </div>
            </div>
            <div class="table-content">
                <div class="table-stats">
                    <div class="stat">
                        <div class="stat-value">{total_cols}</div>
                        <div class="stat-label">Columns</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{pk_count}</div>
                        <div class="stat-label">Primary Keys</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{fk_count}</div>
                        <div class="stat-label">Foreign Keys</div>
                    </div>
                </div>
                
                <div style="margin-top: 1.5rem;">
                    <h4 style="margin-bottom: 0.75rem; color: #374151; font-weight: 600;">📋 Schema Preview</h4>
                    <div class="code-block">
                        CREATE TABLE {table['name']} (<br/>{'<br/>'.join(schema_preview)}<br/>);
                    </div>
                </div>
                
                {fk_html}
                {sample_html}
            </div>
        </div>
        '''
    
    def _generate_business_context_html(self) -> str:
        """Generate HTML for business context guide."""
        return '''
        <h2 class="text-3xl font-bold text-blue-600 mb-6 flex items-center gap-2">🏷️ Business Context Guide</h2>
        <p class="text-slate-600 mb-6">Understanding what each table represents in business terms and how they support workforce intelligence.</p>
        
        <div class="collapsible mb-6 expanded">
            <div class="collapsible-header" onclick="toggleCollapsible(this.parentElement)">
                <div class="flex items-center gap-3">
                    <span class="text-2xl">🏗️</span>
                    <div>
                        <div class="text-xl font-semibold text-slate-800">Core Data Foundation</div>
                        <div class="text-sm text-slate-600 mt-1">Foundation tables containing primary business entities</div>
                    </div>
                </div>
                <span class="toggle text-lg transition-transform duration-300" style="transform: rotate(180deg);">▼</span>
            </div>
            <div class="collapsible-content expanded">
                <div class="collapsible-body">
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <div class="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-xl p-6 hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1">
                            <div class="mb-4">
                                <div class="flex items-center gap-2 mb-2">
                                    <span class="text-blue-600">🏢</span>
                                    <div class="text-lg font-semibold text-blue-800">core_job_architecture</div>
                                </div>
                            </div>
                            <div class="space-y-3 text-sm">
                                <div class="flex items-start gap-2">
                                    <span class="text-blue-500 mt-1">🎯</span>
                                    <div><strong class="text-slate-700">Purpose:</strong> <span class="text-slate-600">Defines the organisational job structure and hierarchies</span></div>
                                </div>
                                <div class="flex items-start gap-2">
                                    <span class="text-blue-500 mt-1">💼</span>
                                    <div><strong class="text-slate-700">Business Use:</strong> <span class="text-slate-600">Job family analysis, role comparison, organisational design</span></div>
                                </div>
                                <div class="flex items-start gap-2">
                                    <span class="text-blue-500 mt-1">🔄</span>
                                    <div><strong class="text-slate-700">Update Frequency:</strong> <span class="text-slate-600">Quarterly or when org structure changes</span></div>
                                </div>
                                <div class="flex items-start gap-2">
                                    <span class="text-blue-500 mt-1">💡</span>
                                    <div><strong class="text-slate-700">Key Insights:</strong> <span class="text-slate-600">Job relationships, management levels, customer-facing roles</span></div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="table-card">
                            <div class="table-header">
                                <div class="table-name">core_skills_taxonomy</div>
                            </div>
                            <div class="table-content">
                                <p><strong>Purpose:</strong> Master catalog of all skills with categorization and metadata</p>
                                <p><strong>Business Use:</strong> Skill gap analysis, capability mapping, training needs</p>
                                <p><strong>Update Frequency:</strong> Monthly with market skill trends</p>
                                <p><strong>Key Insights:</strong> Skill categories, types, emerging vs traditional skills</p>
                            </div>
                        </div>
                        
                        <div class="table-card">
                            <div class="table-header">
                                <div class="table-name">core_job_skill_requirements</div>
                            </div>
                            <div class="table-content">
                                <p><strong>Purpose:</strong> Links jobs to required skills (many-to-many relationship)</p>
                                <p><strong>Business Use:</strong> Career pathway analysis, recruitment planning</p>
                                <p><strong>Update Frequency:</strong> Bi-annually or when roles evolve</p>
                                <p><strong>Key Insights:</strong> Skill demand patterns, role complexity</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="collapsible">
            <div class="collapsible-header" onclick="toggleCollapsible(this.parentElement)">
                <span>📊 Analytics Intelligence</span>
                <span class="toggle">▼</span>
            </div>
            <div class="collapsible-content">
                <div class="collapsible-body">
                    <p>Pre-computed analytics tables that power business insights and decision-making.</p>
                    <div class="table-grid">
                        <div class="table-card">
                            <div class="table-header">
                                <div class="table-name">analytics_job_similarities</div>
                            </div>
                            <div class="table-content">
                                <p><strong>Purpose:</strong> Pre-computed similarity scores between all job pairs</p>
                                <p><strong>Business Use:</strong> Career pathway recommendations, lateral move suggestions</p>
                                <p><strong>Derived From:</strong> core_job_architecture + core_job_skill_requirements</p>
                                <p><strong>Refresh Trigger:</strong> Job architecture or skill requirements change</p>
                            </div>
                        </div>
                        
                        <div class="table-card">
                            <div class="table-header">
                                <div class="table-name">analytics_movement_patterns</div>
                            </div>
                            <div class="table-content">
                                <p><strong>Purpose:</strong> Historical career movement patterns and trends</p>
                                <p><strong>Business Use:</strong> Succession planning, career pathway validation</p>
                                <p><strong>Derived From:</strong> core_colleague_positions_history</p>
                                <p><strong>Refresh Trigger:</strong> Monthly with new position history</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
    
    def _generate_developer_guide_html(self) -> str:
        """Generate HTML for developer guide."""
        return '''
        <h2>🔧 Developer Guide</h2>
        
        <div class="collapsible expanded">
            <div class="collapsible-header" onclick="toggleCollapsible(this.parentElement)">
                <span>🚀 Common Query Patterns</span>
                <span class="toggle">▼</span>
            </div>
            <div class="collapsible-content">
                <div class="collapsible-body">
                    <h4>Career Pathway Analysis</h4>
                    <div class="code-block">
<span class="comment">-- Find career paths from a specific role</span>
<span class="keyword">SELECT</span> 
    j2.JobProfile <span class="keyword">as</span> target_role,
    js.similarity_score,
    j2.JobFunction,
    j2.ManagementLevel
<span class="keyword">FROM</span> analytics_job_similarities js
<span class="keyword">JOIN</span> core_job_architecture j1 <span class="keyword">ON</span> js.job_from = j1.JobProfileID
<span class="keyword">JOIN</span> core_job_architecture j2 <span class="keyword">ON</span> js.job_to = j2.JobProfileID
<span class="keyword">WHERE</span> j1.JobProfile = <span class="string">'Senior Business Analyst'</span>
  <span class="keyword">AND</span> js.similarity_score > 0.7
<span class="keyword">ORDER BY</span> js.similarity_score <span class="keyword">DESC</span>
<span class="keyword">LIMIT</span> 10;
                    </div>
                    
                    <h4>Skill Gap Analysis</h4>
                    <div class="code-block">
<span class="comment">-- Compare skills between current and target role</span>
<span class="keyword">SELECT</span> 
    st.Skill_Name,
    st.Category,
    <span class="keyword">CASE WHEN</span> current_skills.Skill_ID <span class="keyword">IS NOT NULL THEN</span> <span class="string">'HAS'</span> <span class="keyword">ELSE</span> <span class="string">'MISSING'</span> <span class="keyword">END</span> <span class="keyword">as</span> current_status,
    sr.rarity_category
<span class="keyword">FROM</span> core_job_skill_requirements target_skills
<span class="keyword">JOIN</span> core_skills_taxonomy st <span class="keyword">ON</span> target_skills.Skill_ID = st.Skill_ID
<span class="keyword">LEFT JOIN</span> analytics_skill_rarity sr <span class="keyword">ON</span> st.Skill_ID = sr.skill_id
<span class="keyword">WHERE</span> target_skills.JobProfileID = (
    <span class="keyword">SELECT</span> JobProfileID <span class="keyword">FROM</span> core_job_architecture 
    <span class="keyword">WHERE</span> JobProfile = <span class="string">'Target Role'</span>
);
                    </div>
                </div>
            </div>
        </div>
        
        <div class="collapsible">
            <div class="collapsible-header" onclick="toggleCollapsible(this.parentElement)">
                <span>⚡ Performance Tips</span>
                <span class="toggle">▼</span>
            </div>
            <div class="collapsible-content">
                <div class="collapsible-body">
                    <ul class="feature-list">
                        <li><span class="icon">🔍</span> <strong>Use Indexes:</strong> Key columns are automatically indexed, but consider composite indexes for complex queries</li>
                        <li><span class="icon">📊</span> <strong>Limit Results:</strong> Always use LIMIT for exploratory queries on large tables</li>
                        <li><span class="icon">🔗</span> <strong>Join Strategy:</strong> Start with smaller tables (job_architecture) and join to larger ones</li>
                        <li><span class="icon">⚡</span> <strong>Filter Early:</strong> Apply WHERE conditions on indexed columns first</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="collapsible">
            <div class="collapsible-header" onclick="toggleCollapsible(this.parentElement)">
                <span>🔗 Key Relationships</span>
                <span class="toggle">▼</span>
            </div>
            <div class="collapsible-content">
                <div class="collapsible-body">
                    <ul class="feature-list">
                        <li><span class="icon">🗝️</span> <strong>JobProfileID:</strong> Primary key linking jobs across all tables</li>
                        <li><span class="icon">🎯</span> <strong>Skill_ID:</strong> Primary key linking skills across taxonomy and requirements</li>
                        <li><span class="icon">📊</span> <strong>Similarity Scores:</strong> Pre-computed to avoid expensive calculations</li>
                        <li><span class="icon">📈</span> <strong>Movement Patterns:</strong> Aggregated to provide statistical significance</li>
                    </ul>
                </div>
            </div>
        </div>
        '''


def generate_enhanced_schema_docs(db_path: str, output_path: str, create_debug_erd: bool = False, 
                                 show_all_tables_in_erd: bool = True, create_standalone_erd: bool = True) -> bool:
    """
    Generate enhanced schema documentation with navigation and business context.
    
    Args:
        db_path: Path to SQLite database
        output_path: Path for output markdown file
        create_debug_erd: Whether to create a separate .erd.mmd debug file (default: False)
        show_all_tables_in_erd: Whether to include all tables in ERD or use filtered subset (default: True)
        create_standalone_erd: Whether to create a standalone interactive HTML ERD (default: True)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with EnhancedSchemaDocGenerator(db_path) as generator:
            return generator.generate_enhanced_html_documentation(output_path, create_debug_erd, show_all_tables_in_erd)
    except Exception as e:
        print(f"❌ Documentation generation failed: {e}")
        return False