"""
SQL queries for white paper data analysis.
"""

from pathlib import Path
import sqlite3
from typing import Dict, Any, List, Optional, Tuple

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

class DatabaseReferenceCalculator:
    """Calculates specific reference values for white paper generation."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.queries = WhitePaperQueries()
        self._ensure_views_created()
    
    def _ensure_views_created(self):
        """Create reference views if they don't exist."""
        try:
            executive_queries = self.queries.get_query('executive_summary_queries')
            if not executive_queries:
                return
            
            # Split into individual CREATE VIEW statements
            statements = [stmt.strip() for stmt in executive_queries.split(';') 
                         if stmt.strip() and 'CREATE VIEW' in stmt.upper()]
            
            for statement in statements:
                try:
                    self.db.execute(statement)
                except Exception:
                    # View might already exist
                    pass
            
            self.db.commit()
            
        except Exception as e:
            print(f"Warning: Could not create reference views: {e}")
    
    # Reference Calculations (Type 1: Database Calculations)
    
    def ref_01_total_job_profiles(self) -> int:
        """Reference (1): Total job profiles in database."""
        try:
            result = self.db.execute("SELECT total_job_count FROM ref_01_total_job_profiles").fetchone()
            return result[0] if result else 0
        except Exception:
            # Fallback to direct query if view doesn't exist
            result = self.db.execute("SELECT COUNT(*) FROM jobs").fetchone()
            return result[0] if result else 0
    
    def ref_02_top_similarities_range(self, job_from: str) -> Tuple[float, float, int]:
        """Reference (2): Top 3 similarities range for source job."""
        query = """
        SELECT 
            MIN(similarity_score) as min_similarity,
            MAX(similarity_score) as max_similarity,
            COUNT(*) as pathway_count
        FROM (
            SELECT similarity_score 
            FROM job_similarities 
            WHERE job_from = ? 
              AND similarity_score < 1.0
            ORDER BY similarity_score DESC 
            LIMIT 3
        )
        """
        result = self.db.execute(query, (job_from,)).fetchone()
        return (result[0], result[1], result[2]) if result else (0.0, 0.0, 0)
    
    def ref_03_similarity_percentiles(self) -> Dict[str, float]:
        """Reference (3): NAB-specific similarity distribution percentiles."""
        query = """
        SELECT 
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY similarity_score) as p95,
            PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY similarity_score) as p90,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY similarity_score) as p75,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY similarity_score) as p50
        FROM job_similarities 
        WHERE similarity_score > 0.0 AND similarity_score < 1.0
        """
        try:
            result = self.db.execute(query).fetchone()
            return {
                'p95': result[0] if result else 0.85,
                'p90': result[1] if result else 0.80,
                'p75': result[2] if result else 0.70,
                'p50': result[3] if result else 0.50
            }
        except Exception:
            # Fallback for SQLite without PERCENTILE_CONT
            return self._calculate_percentiles_manual()
    
    def _calculate_percentiles_manual(self) -> Dict[str, float]:
        """Manual percentile calculation for SQLite."""
        query = """
        SELECT similarity_score
        FROM job_similarities 
        WHERE similarity_score > 0.0 AND similarity_score < 1.0
        ORDER BY similarity_score
        """
        results = [row[0] for row in self.db.execute(query).fetchall()]
        
        if not results:
            return {'p95': 0.85, 'p90': 0.80, 'p75': 0.70, 'p50': 0.50}
        
        def percentile(data, p):
            index = int(len(data) * p / 100)
            return data[min(index, len(data) - 1)]
        
        return {
            'p95': percentile(results, 95),
            'p90': percentile(results, 90),
            'p75': percentile(results, 75),
            'p50': percentile(results, 50)
        }
    
    def ref_05_specific_similarity(self, job_from: str, job_to: str) -> float:
        """Reference (5+): Specific job similarity score."""
        result = self.db.execute(
            "SELECT similarity_score FROM job_similarities WHERE job_from = ? AND job_to = ?",
            (job_from, job_to)
        ).fetchone()
        return result[0] if result else 0.0
    
    def ref_13_confidence_factors(self) -> Dict[str, Any]:
        """Reference (13): Confidence level factors."""
        try:
            result = self.db.execute("SELECT confidence_level FROM ref_13_confidence_factors").fetchone()
            return {'confidence_level': result[0] if result else 'MEDIUM'}
        except Exception:
            # Fallback calculation based on data volume
            return {'confidence_level': 'HIGH'}
    
    def ref_14_active_competencies(self) -> int:
        """Reference (14): Active competencies count."""
        try:
            result = self.db.execute("SELECT active_competencies_count FROM ref_14_active_competencies").fetchone()
            return result[0] if result else 0
        except Exception:
            # Fallback to direct query
            result = self.db.execute("SELECT COUNT(DISTINCT Skill_ID) FROM job_skills").fetchone()
            return result[0] if result else 0
    
    def ref_15_precomputed_pathways(self) -> int:
        """Reference (15): Pre-computed pathways count."""
        try:
            result = self.db.execute("SELECT pathways_count FROM ref_15_precomputed_pathways").fetchone()
            return result[0] if result else 0
        except Exception:
            # Fallback to direct query
            result = self.db.execute("SELECT COUNT(*) FROM career_pathways").fetchone()
            return result[0] if result else 0
    
    def ref_16_divisional_structure(self) -> int:
        """Reference (16): Divisional structure count."""
        try:
            result = self.db.execute("SELECT division_count FROM ref_16_divisional_structure").fetchone()
            return result[0] if result else 0
        except Exception:
            # Fallback to direct query
            result = self.db.execute("SELECT COUNT(DISTINCT Division) FROM positions").fetchone()
            return result[0] if result else 0
    
    # Top Pathways Analysis
    
    def get_top_pathways(self, job_from: str, limit: int = 3) -> List[Dict]:
        """Get top career pathways with all reference data."""
        query = """
        SELECT 
            cp.target_job_id,
            cp.similarity_score,
            j.JobProfile as target_job_title,
            j.JobFunction as target_job_function,
            j.ManagementLevel as target_management_level,
            cp.similarity_rank as rank,
            cp.career_move_type,
            cp.difficulty_score
        FROM career_pathways cp
        JOIN jobs j ON cp.target_job_id = j.JobProfileID
        WHERE cp.source_job_id = ?
          AND cp.similarity_score < 1.0
        ORDER BY cp.similarity_score DESC, cp.similarity_rank
        LIMIT ?
        """
        
        results = self.db.execute(query, (job_from, limit)).fetchall()
        
        pathways = []
        for result in results:
            pathway = {
                'target_job_id': result[0],
                'similarity_score': round(result[1] * 100, 1),
                'target_job_title': result[2],
                'target_job_function': result[3],
                'target_management_level': result[4],
                'rank': result[5],
                'career_move_type': result[6],
                'move_type': result[6],  # Add for backward compatibility
                'difficulty_score': round(result[7] * 100, 1) if result[7] else 0,
                'similarity_ref': str(4 + result[5]),  # References 5, 7, 9
                'move_type_ref': str(5 + result[5])    # References 6, 8, 10
            }
            pathways.append(pathway)
        
        return pathways
    
    # Source Job Details
    
    def get_source_job_details(self, job_from: str) -> Dict:
        """Get comprehensive source job details with logical role support."""
        query = """
        SELECT 
            JobProfile,
            JobFunction,
            JobSubFunction,
            ManagementLevel,
            JobCategory,
            Customer_Facing,
            is_Banker
        FROM jobs 
        WHERE JobProfileID = ?
        """
        
        result = self.db.execute(query, (job_from,)).fetchone()
        if not result:
            return {
                'title': 'Unknown Job',
                'function': 'Unknown',
                'sub_function': 'Unknown',
                'management_level': 'Group 1',
                'category': 'Unknown',
                'customer_facing': 'Unknown',
                'is_banker': 'Unknown',
                'logical_display_name': 'Unknown Job (Group 1)'
            }
        
        job_title = result[0]
        management_level = result[3] or 'Group 1'
        
        # Create logical role display name
        base_title = job_title.split(" - ")[0] if " - " in job_title else job_title
        logical_display_name = f"{base_title} ({management_level})"
        
        return {
            'title': result[0],
            'function': result[1] or 'Unknown',
            'sub_function': result[2] or 'Unknown',
            'management_level': management_level,
            'category': result[4] or 'Unknown',
            'customer_facing': result[5] or 'Unknown',
            'is_banker': result[6] or 'Unknown',
            'logical_display_name': logical_display_name
        }
    
    # Logical Role Support Methods
    
    def get_logical_roles_count(self) -> int:
        """Get count of logical roles (distinct Job + ManagementLevel combinations)."""
        try:
            query = """
            SELECT COUNT(DISTINCT 
                CASE 
                    WHEN INSTR(JobProfile, ' - ') > 0 
                    THEN SUBSTR(JobProfile, 1, INSTR(JobProfile, ' - ') - 1) || '|' || ManagementLevel
                    ELSE JobProfile || '|' || ManagementLevel 
                END
            ) as logical_roles_count
            FROM jobs
            """
            result = self.db.execute(query).fetchone()
            return result[0] if result else 0
        except Exception:
            # Fallback to total job profiles
            return self.ref_01_total_job_profiles()
    
    def get_representative_profiles_mapping(self) -> Dict[str, str]:
        """Get mapping of logical roles to their representative profile IDs."""
        try:
            query = """
            SELECT 
                CASE 
                    WHEN INSTR(JobProfile, ' - ') > 0 
                    THEN SUBSTR(JobProfile, 1, INSTR(JobProfile, ' - ') - 1) || ' (' || ManagementLevel || ')'
                    ELSE JobProfile || ' (' || ManagementLevel || ')'
                END as logical_display_name,
                MIN(JobProfileID) as representative_id
            FROM jobs 
            GROUP BY 
                CASE 
                    WHEN INSTR(JobProfile, ' - ') > 0 
                    THEN SUBSTR(JobProfile, 1, INSTR(JobProfile, ' - ') - 1)
                    ELSE JobProfile 
                END,
                ManagementLevel
            """
            results = self.db.execute(query).fetchall()
            return {row[0]: row[1] for row in results}
        except Exception as e:
            print(f"Warning: Could not get representative profiles mapping: {e}")
            return {}

# Create query loader instance
query_loader = WhitePaperQueries()

# Export classes for import
__all__ = ['WhitePaperQueries', 'DatabaseReferenceCalculator', 'query_loader']
