"""
SQL queries for white paper data analysis.
"""

from pathlib import Path
import sqlite3
from typing import Dict, Any

class WhitePaperQueries:
    """Manages SQL queries for white paper generation."""
    
    def __init__(self):
        self.queries_path = Path(__file__).parent
        self.queries = self._load_queries()
    
    def _load_queries(self) -> Dict[str, str]:
        """Load SQL queries from files."""
        queries = {}
        
        # Load each SQL file
        for sql_file in self.queries_path.glob('*.sql'):
            if sql_file.name != '__init__.py':
                with open(sql_file, 'r', encoding='utf-8') as f:
                    queries[sql_file.stem] = f.read()
        
        return queries
    
    def get_query(self, query_name: str) -> str:
        """Get SQL query by name."""
        return self.queries.get(query_name, '')

# Create query loader instance
query_loader = WhitePaperQueries()
