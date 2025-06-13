"""
Database Access Layer for NAB Skills Intelligence Platform
=========================================================

Centralizes all SQL queries and database operations for the Flask webapp.
Provides clean separation between business logic and data access.

Usage:
    from database import DatabaseManager
    
    db = DatabaseManager(app.config['DATABASE_PATH'])
    families = db.get_job_families()
    tree_data = db.get_career_tree_data('Data & Analytics')
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

class DatabaseManager:
    """Manages database connections and provides high-level query methods."""
    
    def __init__(self, database_path: Path):
        """Initialize database manager with path to SQLite database."""
        self.database_path = Path(database_path)
        if not self.database_path.exists():
            raise FileNotFoundError(f"Database not found: {database_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with automatic cleanup."""
        conn = sqlite3.connect(str(self.database_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute a SELECT query and return results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_query_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute a SELECT query and return first result or None."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
    
    # ================================================================
    # Job Family and Job Queries
    # ================================================================
    
    def get_job_families(self) -> List[Dict[str, Any]]:
        """Get all job families with job counts."""
        query = """
            SELECT JobFamily as name, COUNT(*) as job_count
            FROM jobs 
            WHERE JobFamily IS NOT NULL
            GROUP BY JobFamily
            ORDER BY job_count DESC
        """
        rows = self.execute_query(query)
        return [dict(row) for row in rows]
    
    def get_jobs_in_family(self, family_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get jobs within a specific job family."""
        query = """
            SELECT JobProfileID, JobProfile, JobFamily, JobID, Job
            FROM jobs 
            WHERE JobFamily = ?
            ORDER BY JobProfile
            LIMIT ?
        """
        rows = self.execute_query(query, (family_name, limit))
        return [dict(row) for row in rows]
    
    def search_jobs(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search jobs by name with LIKE pattern."""
        query = """
            SELECT DISTINCT JobProfileID, JobProfile, JobFamily, JobFamilyGroup 
            FROM jobs 
            WHERE JobProfile LIKE ? 
            ORDER BY JobProfile 
            LIMIT ?
        """
        rows = self.execute_query(query, (f'%{search_term}%', limit))
        return [dict(row) for row in rows]
    
    # ================================================================
    # Job Similarity Queries  
    # ================================================================
    
    def get_job_similarities(self, job_profile_id: str, 
                           min_similarity: float = 0.0, 
                           limit: int = 15) -> List[Dict[str, Any]]:
        """Get similar jobs for a given JobProfileID."""
        query = """
            SELECT j2.JobProfileID as similar_job_id, 
                   j2.JobProfile as job_name,
                   j2.JobFamily as job_family,
                   js.similarity_score,
                   js.shared_skills_count as skill_overlap
            FROM job_similarities js
            JOIN jobs j2 ON js.job_to = j2.JobProfileID
            WHERE js.job_from = ?
              AND js.similarity_score >= ?
              AND js.job_from != js.job_to
            ORDER BY js.similarity_score DESC
            LIMIT ?
        """
        rows = self.execute_query(query, (job_profile_id, min_similarity, limit))
        return [dict(row) for row in rows]
    
    def get_similarity_between_jobs(self, job_from: str, job_to: str) -> Optional[Dict[str, Any]]:
        """Get similarity score between two specific jobs."""
        query = """
            SELECT js.similarity_score, js.shared_skills_count,
                   j1.JobProfile as start_job, j1.JobFamily as start_family,
                   j2.JobProfile as target_job, j2.JobFamily as target_family
            FROM job_similarities js
            JOIN jobs j1 ON js.job_from = j1.JobProfileID
            JOIN jobs j2 ON js.job_to = j2.JobProfileID
            WHERE js.job_from = ? AND js.job_to = ?
        """
        row = self.execute_query_one(query, (job_from, job_to))
        return dict(row) if row else None
    
    # ================================================================
    # D3.js Tree Data Queries
    # ================================================================
    
    def get_career_tree_data(self, family_name: str, 
                           job_limit: int = 10,
                           similarity_threshold: float = 0.6,
                           similar_job_limit: int = 5) -> Dict[str, Any]:
        """Generate hierarchical tree data for D3.js visualization."""
        
        # Get jobs in the family
        jobs = self.get_jobs_in_family(family_name, job_limit)
        
        # Build tree structure
        tree_data = {
            'name': family_name,
            'type': 'family',
            'children': []
        }
        
        for job in jobs:
            job_node = {
                'name': job['JobProfile'],
                'type': 'job',
                'id': job['JobProfileID'],
                'family': job['JobFamily'],
                'children': []
            }
            
            # Get similar jobs for this job
            similar_jobs = self.get_similar_jobs_for_tree(
                job['JobProfileID'], 
                similarity_threshold, 
                similar_job_limit
            )
            
            for similar_job in similar_jobs:
                similar_node = {
                    'name': similar_job['JobProfile'],
                    'type': 'similar_job',
                    'id': similar_job['JobProfileID'],
                    'family': similar_job['JobFamily'],
                    'similarity': round(similar_job['similarity_score'], 3),
                    'size': int(similar_job['similarity_score'] * 100)
                }
                job_node['children'].append(similar_node)
            
            tree_data['children'].append(job_node)
        
        return tree_data
    
    def get_similar_jobs_for_tree(self, job_profile_id: str, 
                                min_similarity: float = 0.6,
                                limit: int = 5) -> List[Dict[str, Any]]:
        """Get similar jobs specifically formatted for tree visualization."""
        query = """
            SELECT j2.JobProfileID, j2.JobProfile, j2.JobFamily, 
                   js.similarity_score
            FROM job_similarities js
            JOIN jobs j2 ON js.job_to = j2.JobProfileID
            WHERE js.job_from = ?
              AND js.similarity_score >= ?
              AND js.job_from != js.job_to
            ORDER BY js.similarity_score DESC
            LIMIT ?
        """
        rows = self.execute_query(query, (job_profile_id, min_similarity, limit))
        return [dict(row) for row in rows]
    
    # ================================================================
    # Career Pathway Analysis Queries
    # ================================================================
    
    def get_career_pathway(self, start_job_id: str, target_job_id: str) -> Dict[str, Any]:
        """Get career pathway analysis between two jobs."""
        
        # Get direct similarity
        direct_path = self.get_similarity_between_jobs(start_job_id, target_job_id)
        if not direct_path:
            return {'error': 'No pathway found'}
        
        # Find intermediate jobs (high similarity to both start and target)
        query = """
            SELECT j.JobProfileID, j.JobProfile, j.JobFamily,
                   js1.similarity_score as start_similarity,
                   js2.similarity_score as target_similarity,
                   (js1.similarity_score + js2.similarity_score) / 2 as avg_similarity
            FROM jobs j
            JOIN job_similarities js1 ON j.JobProfileID = js1.job_to AND js1.job_from = ?
            JOIN job_similarities js2 ON j.JobProfileID = js2.job_from AND js2.job_to = ?
            WHERE j.JobProfileID != ? AND j.JobProfileID != ?
              AND js1.similarity_score > 0.6 AND js2.similarity_score > 0.6
            ORDER BY avg_similarity DESC
            LIMIT 3
        """
        
        intermediate_rows = self.execute_query(query, (start_job_id, target_job_id, start_job_id, target_job_id))
        
        return {
            'direct_path': direct_path,
            'intermediate_steps': [dict(row) for row in intermediate_rows]
        }
    
    # ================================================================
    # Skills Analysis Queries
    # ================================================================
    
    def get_skills_for_job(self, job_profile_id: str) -> List[Dict[str, Any]]:
        """Get all skills for a specific job."""
        query = """
            SELECT s.Skill_ID, s.Skill_Name, s.Category, s.Subcategory, 
                   s.SkillType, js.Skill_Weight
            FROM job_skills js
            JOIN skills s ON js.Skill_ID = s.Skill_ID
            WHERE js.JobProfileID = ?
            ORDER BY js.Skill_Weight DESC, s.Skill_Name
        """
        rows = self.execute_query(query, (job_profile_id,))
        return [dict(row) for row in rows]
    
    def get_skills_gap_analysis(self, source_job_id: str, target_job_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Compare skills between source and target jobs for transition planning."""
        query = """
            WITH source_skills AS (
                SELECT js.Skill_ID, s.Skill_Name, s.Category
                FROM job_skills js
                JOIN skills s ON js.Skill_ID = s.Skill_ID
                WHERE js.JobProfileID = ?
            ),
            target_skills AS (
                SELECT js.Skill_ID, s.Skill_Name, s.Category  
                FROM job_skills js
                JOIN skills s ON js.Skill_ID = s.Skill_ID
                WHERE js.JobProfileID = ?
            )
            SELECT 
                COALESCE(ts.Skill_Name, ss.Skill_Name) as skill_name,
                COALESCE(ts.Category, ss.Category) as skill_category,
                CASE 
                    WHEN ss.Skill_ID IS NOT NULL AND ts.Skill_ID IS NOT NULL THEN 'Transferable'
                    WHEN ss.Skill_ID IS NOT NULL AND ts.Skill_ID IS NULL THEN 'Source Only'
                    WHEN ss.Skill_ID IS NULL AND ts.Skill_ID IS NOT NULL THEN 'Target Required'
                END as skill_status,
                COALESCE(ts.Skill_ID, ss.Skill_ID) as skill_id
            FROM target_skills ts
            FULL OUTER JOIN source_skills ss ON ts.Skill_ID = ss.Skill_ID
            ORDER BY skill_status, skill_category, skill_name
        """
        
        rows = self.execute_query(query, (source_job_id, target_job_id))
        
        # Group by skill status
        result = {
            'transferable': [],
            'source_only': [],
            'target_required': []
        }
        
        for row in rows:
            status = row['skill_status'].lower().replace(' ', '_')
            if status in result:
                result[status].append(dict(row))
        
        return result
    
    # ================================================================
    # Position and Organizational Context Queries
    # ================================================================
    
    def get_positions_for_job(self, job_profile_id: str) -> List[Dict[str, Any]]:
        """Get available positions for a specific job."""
        query = """
            SELECT p."Position Number", p.JobProfileID, j.JobProfile,
                   p.Division, p.Business_Unit, p.Team, p.Location,
                   p."Employee Number",
                   CASE WHEN p."Employee Number" IS NULL THEN 'Vacant' ELSE 'Occupied' END as position_status
            FROM positions p
            JOIN jobs j ON p.JobProfileID = j.JobProfileID
            WHERE j.JobProfileID = ?
            ORDER BY p.Division, p.Business_Unit, p.Team
        """
        rows = self.execute_query(query, (job_profile_id,))
        return [dict(row) for row in rows]
    
    def get_organizational_distribution(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get organizational distribution statistics."""
        
        # Division distribution
        division_query = """
            SELECT Division, COUNT(*) as count 
            FROM positions 
            GROUP BY Division 
            ORDER BY count DESC 
            LIMIT 10
        """
        divisions = [dict(row) for row in self.execute_query(division_query)]
        
        # Job family distribution
        family_query = """
            SELECT JobFamily, COUNT(*) as count 
            FROM jobs 
            GROUP BY JobFamily 
            ORDER BY count DESC 
            LIMIT 10
        """
        families = [dict(row) for row in self.execute_query(family_query)]
        
        return {
            'divisions': divisions,
            'job_families': families
        }
    
    # ================================================================
    # Database Metadata and Health Checks
    # ================================================================
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics and health information."""
        tables = ['jobs', 'job_similarities', 'skills', 'job_skills', 'positions', 'schema_metadata']
        stats = {}
        
        for table in tables:
            try:
                count_query = f"SELECT COUNT(*) as count FROM {table}"
                result = self.execute_query_one(count_query)
                stats[table] = result['count'] if result else 0
            except sqlite3.Error:
                stats[table] = 'Error'
        
        # Get database file size
        stats['database_size_mb'] = round(self.database_path.stat().st_size / (1024 * 1024), 1)
        
        return stats
    
    def get_schema_metadata(self) -> Dict[str, str]:
        """Get schema metadata information."""
        query = "SELECT key, value FROM schema_metadata"
        rows = self.execute_query(query)
        return {row['key']: row['value'] for row in rows}


# ================================================================
# Convenience Functions for Flask Integration
# ================================================================

def create_database_manager(database_path: Path) -> DatabaseManager:
    """Factory function to create DatabaseManager instance."""
    return DatabaseManager(database_path)

def init_database_for_app(app):
    """Initialize database manager for Flask app."""
    db_path = app.config.get('DATABASE_PATH')
    if not db_path:
        raise ValueError("DATABASE_PATH not configured in Flask app")
    
    return DatabaseManager(db_path) 