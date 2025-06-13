"""
SQL Query Loader for NAB Skills Intelligence Platform
===================================================

Loads and organizes SQL queries from .sql files in this directory.
Provides a clean interface for accessing queries by category and name.

Directory Structure:
    sql/
    ├── __init__.py              # This file - query loader
    ├── jobs.sql                 # Job and job family queries
    ├── similarities.sql         # Job similarity queries
    ├── career_pathways.sql      # Career pathway analysis
    ├── skills.sql               # Skills analysis queries
    ├── positions.sql            # Position and org context
    ├── d3_visualization.sql     # D3.js tree and network data
    └── metadata.sql             # Database stats and health

Usage:
    from sql import queries
    
    # Get a specific query
    query = queries.get('jobs', 'get_job_families')
    
    # List all available queries
    available = queries.list_all()
    
    # Get all queries in a category
    job_queries = queries.get_category('jobs')
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

class SQLQueryLoader:
    """Loads and manages SQL queries from .sql files."""
    
    def __init__(self):
        """Initialize the query loader."""
        self.sql_dir = Path(__file__).parent
        self._queries = {}
        self._load_all_queries()
    
    def _load_all_queries(self):
        """Load all .sql files and parse queries."""
        sql_files = list(self.sql_dir.glob("*.sql"))
        
        for sql_file in sql_files:
            category = sql_file.stem  # filename without extension
            self._queries[category] = self._parse_sql_file(sql_file)
    
    def _parse_sql_file(self, sql_file: Path) -> Dict[str, str]:
        """Parse a SQL file and extract named queries."""
        queries = {}
        
        try:
            content = sql_file.read_text(encoding='utf-8')
            
            # Split by query separators (-- query_name:)
            sections = content.split('-- query_name:')
            
            for section in sections[1:]:  # Skip first empty section
                lines = section.strip().split('\n')
                if not lines:
                    continue
                
                # First line is the query name
                query_name = lines[0].strip()
                
                # Rest is the SQL query (skip comment lines)
                query_lines = []
                for line in lines[1:]:
                    # Stop at next query separator or end of file
                    if line.strip().startswith('-- query_name:'):
                        break
                    # Skip standalone comment lines but keep inline comments
                    if line.strip() and not line.strip().startswith('--'):
                        query_lines.append(line)
                    elif line.strip().startswith('--') and any(c.isalnum() for c in line):
                        # Keep comment lines that have content (not just dashes)
                        if not line.strip().startswith('-- ===='):
                            query_lines.append(line)
                
                if query_lines:
                    queries[query_name] = '\n'.join(query_lines).strip()
        
        except Exception as e:
            print(f"Warning: Failed to parse {sql_file}: {e}")
        
        return queries
    
    def get(self, category: str, query_name: str) -> Optional[str]:
        """Get a specific query by category and name."""
        if category in self._queries and query_name in self._queries[category]:
            return self._queries[category][query_name]
        return None
    
    def get_category(self, category: str) -> Dict[str, str]:
        """Get all queries in a category."""
        return self._queries.get(category, {})
    
    def list_categories(self) -> List[str]:
        """List all available categories."""
        return list(self._queries.keys())
    
    def list_queries_in_category(self, category: str) -> List[str]:
        """List all query names in a category."""
        return list(self._queries.get(category, {}).keys())
    
    def list_all(self) -> Dict[str, List[str]]:
        """List all categories and their queries."""
        return {category: self.list_queries_in_category(category) 
                for category in self.list_categories()}
    
    def search_queries(self, search_term: str) -> Dict[str, List[str]]:
        """Search for queries containing the search term."""
        results = {}
        search_lower = search_term.lower()
        
        for category, queries in self._queries.items():
            matching_queries = []
            for query_name, query_sql in queries.items():
                if (search_lower in query_name.lower() or 
                    search_lower in query_sql.lower()):
                    matching_queries.append(query_name)
            
            if matching_queries:
                results[category] = matching_queries
        
        return results
    
    def get_query_info(self, category: str, query_name: str) -> Dict[str, str]:
        """Get detailed information about a query."""
        query = self.get(category, query_name)
        if not query:
            return {}
        
        # Count parameters (? placeholders)
        param_count = query.count('?')
        
        # Extract table names (basic pattern matching)
        tables = []
        lines = query.lower().split('\n')
        for line in lines:
            if 'from ' in line or 'join ' in line:
                words = line.split()
                for i, word in enumerate(words):
                    if word in ['from', 'join'] and i + 1 < len(words):
                        table = words[i + 1].strip('(),')
                        if table not in ['(', 'select'] and table not in tables:
                            tables.append(table)
        
        return {
            'category': category,
            'name': query_name,
            'sql': query,
            'parameter_count': param_count,
            'tables_used': tables,
            'line_count': len(query.split('\n'))
        }

# Create global instance
queries = SQLQueryLoader()

# Convenience functions for backward compatibility
def get_query(category: str, query_name: str) -> Optional[str]:
    """Get a specific query by category and name."""
    return queries.get(category, query_name)

def list_available_queries() -> Dict[str, List[str]]:
    """List all available queries organized by category."""
    return queries.list_all()

def search_queries(search_term: str) -> Dict[str, List[str]]:
    """Search for queries containing the search term."""
    return queries.search_queries(search_term) 