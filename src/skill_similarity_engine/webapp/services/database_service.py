"""
Database Service for NAB Skills Intelligence Platform
====================================================

Provides core database operations and job queries for the webapp.
Extracted from app.py as part of Phase 2 modularization.

Handles:
- Sample job retrieval with enhanced display names
- Job search functionality using organised SQL
- Job similarity calculations and queries
"""

import sqlite3
from typing import List, Dict, Any, Optional
from flask import g

class DatabaseService:
    """Service for core database operations and job queries."""
    
    def __init__(self, db_connection=None, webapp_config=None, display_manager=None):
        """Initialize database service with optional dependencies."""
        self.db_connection = db_connection
        self.webapp_config = webapp_config
        self.display_manager = display_manager
        
        # Get service configuration
        if webapp_config:
            self.service_config = webapp_config.get_service_config().get_database_service_config()
        else:
            # Fallback configuration
            self.service_config = {
                'default_job_limit': 20,
                'default_search_limit': 10,
                'default_similarity_limit': 10,
                'default_similarity_threshold': 0.5,
                'min_similarity_threshold': 0.1,
                'max_similarity_threshold': 0.99,
                'fallback_enabled': True,
            }
    
    def get_db(self):
        """Get database connection from Flask context or use provided connection."""
        if self.db_connection:
            return self.db_connection
        return g.get('db') if g else None
    
    def add_display_names_to_job(self, job_data: Dict[str, Any], display_manager=None) -> Dict[str, Any]:
        """Add standardised display names to job data."""
        if not display_manager:
            display_manager = self.display_manager
        
        if display_manager and job_data:
            try:
                from ...utils.display import DisplayFormat
                job_id = job_data.get('id') or job_data.get('job_id') or job_data.get('JobProfileID')
                if job_id:
                    job_data['display_name_standard'] = display_manager.get_display_name(job_id, DisplayFormat.STANDARD)
                    job_data['display_name_search'] = display_manager.get_display_name(job_id, DisplayFormat.SEARCH) 
                    job_data['display_name_dropdown'] = display_manager.get_display_name(job_id, DisplayFormat.DROPDOWN)
                    job_data['display_name_compact'] = display_manager.get_display_name(job_id, DisplayFormat.COMPACT)
            except ImportError:
                # Fallback if display manager not available
                pass
        
        return job_data
    
    def get_sample_jobs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get sample jobs for testing using organised SQL with enhanced display names."""
        if limit is None:
            limit = self.service_config['default_job_limit']
            
        db = self.get_db()
        if not db:
            return []
        
        # Use a simplified version for samples with correct column names
        cursor = db.execute("""
            SELECT JobProfileID as id, JobProfile as job_title, JobFunction as job_function, JobFunctionID as job_function_id 
            FROM jobs 
            ORDER BY JobProfile 
            LIMIT ?
        """, (limit,))
        jobs = cursor.fetchall()
        
        # Enhance jobs with standardised display names
        enhanced_jobs = []
        for job in jobs:
            job_dict = dict(job)
            enhanced_job = self.add_display_names_to_job(job_dict, self.display_manager)
            enhanced_jobs.append(enhanced_job)
        
        return enhanced_jobs
    
    def search_jobs(self, query: str, limit: Optional[int] = None) -> List[sqlite3.Row]:
        """Search jobs by name using organised SQL."""
        if limit is None:
            limit = self.service_config['default_search_limit']
            
        db = self.get_db()
        if not db:
            return []
        
        try:
            from ..sql import queries
            search_query = queries.get('jobs', 'search_jobs')
            cursor = db.execute(search_query, (f'%{query}%', None, None))
            return cursor.fetchmany(limit)
        except (ImportError, AttributeError):
            # Fallback search if organised SQL not available
            cursor = db.execute("""
                SELECT JobProfileID as id, JobProfile as job_title, JobFunction as job_function
                FROM jobs 
                WHERE JobProfile LIKE ?
                ORDER BY JobProfile 
                LIMIT ?
            """, (f'%{query}%', limit))
            return cursor.fetchall()
    
    def get_job_similarities(self, job_id: str, limit: Optional[int] = None) -> List[sqlite3.Row]:
        """Get similar jobs using organised SQL."""
        if limit is None:
            limit = self.service_config['default_similarity_limit']
            
        db = self.get_db()
        if not db:
            return []
        
        try:
            from ..sql import queries
            similarities_query = queries.get('similarities', 'get_similar_jobs')
            threshold = self.service_config['default_similarity_threshold']
            cursor = db.execute(similarities_query, (job_id, threshold, limit))
            return cursor.fetchall()
        except (ImportError, AttributeError):
            # Fallback if organised SQL not available
            return []
    
    def get_job_similarities_with_threshold(self, job_id: str, min_similarity: float, limit: int) -> List[sqlite3.Row]:
        """Get similar jobs using organised SQL with a specified similarity threshold."""
        db = self.get_db()
        if not db:
            return []
        
        try:
            from ..sql import queries
            similarities_query = queries.get('similarities', 'get_similar_jobs_with_threshold')
            cursor = db.execute(similarities_query, (job_id, min_similarity, limit))
            return cursor.fetchall()
        except (ImportError, AttributeError):
            # Fallback if organised SQL not available
            return [] 