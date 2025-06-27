"""
Data analysis and threshold logic for Career Transition Analysis Generator.
"""

from typing import Dict, List, Optional, Tuple
import sqlite3
from pathlib import Path

# Import the SQL query system
import sys
sql_path = Path(__file__).parent.parent / 'sql'
if str(sql_path) not in sys.path:
    sys.path.append(str(sql_path))

try:
    from sql import queries
except ImportError:
    # Fallback if SQL module not available
    queries = None

class DataAnalyzer:
    """Analyzes job transition data for Career Transition Analysis Generator."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.sql_path = Path(__file__).parent / 'sql'
    
    def analyze_transition(self, job_from: str, job_to: Optional[str] = None, 
                          scenario: str = 'skills_gap_analysis',
                          filters: Optional[Dict] = None) -> Dict:
        """Analyze job transition data."""
        
        filters = filters or {}
        
        if job_to:
            # Specific job-to-job analysis
            analysis = self._analyze_specific_transition(job_from, job_to, filters)
        else:
            # Top 3 matched jobs analysis
            analysis = self._analyze_top_matches(job_from, filters)
        
        # Add scenario-specific analysis
        analysis['scenario'] = scenario
        analysis = self._enhance_with_scenario_data(analysis, scenario, filters)
        
        return analysis
    
    def _analyze_specific_transition(self, job_from: str, job_to: str, filters: Dict) -> Dict:
        """Analyze specific job-to-job transition."""
        
        try:
            # Get similarity score between the two jobs
            similarity_score = self._get_job_similarity(job_from, job_to)
            
            # Get skills analysis
            skills_data = self._get_skills_gap_analysis(job_from, job_to)
            
            # Get workforce impact data
            workforce_data = self._get_workforce_impact(job_from, filters)
            
            # Calculate confidence level based on similarity and data quality
            confidence_level = self._calculate_confidence_level(similarity_score, skills_data, workforce_data)
            
            return {
                'job_from': job_from,
                'job_to': job_to,
                'avg_similarity': similarity_score,
                'pathway_count': 1,
                'colleague_count': workforce_data.get('total_positions', 0),
                'confidence_level': confidence_level,
                'skills_shared': skills_data.get('shared_skills_count', 0),
                'skills_to_develop': skills_data.get('skills_gap_count', 0),
                'transferable_skills': skills_data.get('transferable_skills_count', 0),
                'source_job_details': workforce_data.get('source_job', {}),
                'target_job_details': self._get_job_details(job_to),
                'skills_breakdown': skills_data,
                'workforce_breakdown': workforce_data,
                'summary': f'Transition analysis from {job_from} to {job_to}'
            }
        except Exception as e:
            print(f"Error in specific transition analysis: {e}")
            return self._get_fallback_analysis(job_from, job_to)
    
    def _analyze_top_matches(self, job_from: str, filters: Dict) -> Dict:
        """Analyze top 3 matched jobs for given source job."""
        
        try:
            # Get top similar jobs using the SQL query system
            top_matches = self._get_top_similar_jobs(job_from, limit=3, filters=filters)
            
            if not top_matches:
                return self._get_fallback_analysis(job_from)
            
            # Calculate average similarity
            avg_similarity = sum(match['similarity_score'] for match in top_matches) / len(top_matches)
            
            # Get workforce data for source job
            workforce_data = self._get_workforce_impact(job_from, filters)
            
            # Get detailed analysis for each top match
            detailed_matches = []
            for match in top_matches:
                skills_data = self._get_skills_gap_analysis(job_from, match['id'])
                detailed_matches.append({
                    **match,
                    'skills_analysis': skills_data
                })
            
            confidence_level = self._calculate_confidence_level(avg_similarity, 
                                                              {'shared_skills_count': sum(m['skills_analysis'].get('shared_skills_count', 0) for m in detailed_matches) / len(detailed_matches)}, 
                                                              workforce_data)
            
            return {
                'job_from': job_from,
                'job_to': None,
                'avg_similarity': avg_similarity,
                'pathway_count': len(top_matches),
                'colleague_count': workforce_data.get('total_positions', 0),
                'confidence_level': confidence_level,
                'top_matches': detailed_matches,
                'source_job_details': workforce_data.get('source_job', {}),
                'workforce_breakdown': workforce_data,
                'summary': f'Top {len(top_matches)} pathway analysis from {job_from}'
            }
        except Exception as e:
            print(f"Error in top matches analysis: {e}")
            return self._get_fallback_analysis(job_from)
    
    def _get_job_similarity(self, job_from: str, job_to: str) -> float:
        """Get similarity score between two jobs using SQL queries."""
        try:
            # Use the similarities SQL query
            query = queries.get('similarities', 'get_similar_jobs_with_threshold') if queries else None
            if not query:
                # Fallback to direct query
                query = """
                SELECT similarity_score 
                FROM job_similarities 
                WHERE (job_from = ? AND job_to = ?) 
                   OR (job_from = ? AND job_to = ?)
                """
                cursor = self.db.execute(query, (job_from, job_to, job_to, job_from))
            else:
                # Modify the query to get specific similarity
                specific_query = """
                SELECT similarity_score 
                FROM job_similarities 
                WHERE (job_from = ? AND job_to = ?) 
                   OR (job_from = ? AND job_to = ?)
                """
                cursor = self.db.execute(specific_query, (job_from, job_to, job_to, job_from))
            
            result = cursor.fetchone()
            return float(result[0]) if result else 0.0
        except Exception as e:
            print(f"Error getting job similarity: {e}")
            return 0.0
    
    def _get_top_similar_jobs(self, job_from: str, limit: int = 3, filters: Optional[Dict] = None) -> List[Dict]:
        """Get top similar jobs using SQL query system with similarity range filtering."""
        try:
            # Extract similarity range from filters
            similarity_min = filters.get('similarity_min', 0.3) if filters else 0.3
            similarity_max = filters.get('similarity_max', 1.0) if filters else 1.0
            
            print(f"ðŸ” Filtering jobs with similarity between {similarity_min:.2f} and {similarity_max:.2f}")
            
            # Use the similarities query
            query = queries.get('similarities', 'get_similar_jobs') if queries else None
            if query:
                # Modify the query to include similarity range
                modified_query = query.replace('AND js.similarity_score > ?', 
                                             'AND js.similarity_score BETWEEN ? AND ?')
                cursor = self.db.execute(modified_query, (job_from, similarity_min, similarity_max, limit))
                results = [dict(row) for row in cursor.fetchall()]
                
                # Apply additional filters if provided
                if filters:
                    filtered_results = []
                    for result in results:
                        # Check division filter
                        if filters.get('division_to'):
                            division_check = self.db.execute(
                                "SELECT 1 FROM positions WHERE JobProfileID = ? AND Division = ?",
                                (result['id'], filters['division_to'])
                            ).fetchone()
                            if not division_check:
                                continue
                        
                        # Check management level filter
                        if filters.get('management_level'):
                            level_check = self.db.execute(
                                "SELECT 1 FROM jobs WHERE JobProfileID = ? AND ManagementLevel LIKE ?",
                                (result['id'], f"%{filters['management_level']}%")
                            ).fetchone()
                            if not level_check:
                                continue
                        
                        filtered_results.append(result)
                    
                    return filtered_results[:limit]
                
                return results
            else:
                # Fallback query
                return self._get_top_similar_jobs_fallback(job_from, limit, filters)
        except Exception as e:
            print(f"Error getting top similar jobs: {e}")
            return self._get_top_similar_jobs_fallback(job_from, limit, filters)
    
    def _get_top_similar_jobs_fallback(self, job_from: str, limit: int, filters: Optional[Dict]) -> List[Dict]:
        """Fallback method for getting top similar jobs with similarity range filtering."""
        # Extract similarity range from filters
        similarity_min = filters.get('similarity_min', 0.3) if filters else 0.3
        similarity_max = filters.get('similarity_max', 1.0) if filters else 1.0
        
        base_query = """
        SELECT 
            js.job_to as id,
            j.JobProfile as job_title,
            j.JobFunction as job_function,
            js.similarity_score
        FROM job_similarities js
        JOIN jobs j ON js.job_to = j.JobProfileID
        WHERE js.job_from = ?
          AND js.similarity_score BETWEEN ? AND ?
        """
        
        params = [job_from, similarity_min, similarity_max]
        
        if filters:
            if filters.get('division_to'):
                base_query += " AND EXISTS (SELECT 1 FROM positions p WHERE p.JobProfileID = j.JobProfileID AND p.Division = ?)"
                params.append(filters['division_to'])
            
            if filters.get('management_level'):
                base_query += " AND j.ManagementLevel LIKE ?"
                params.append(f"%{filters['management_level']}%")
        
        base_query += " ORDER BY js.similarity_score DESC LIMIT ?"
        params.append(str(limit))
        
        cursor = self.db.execute(base_query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def _get_skills_gap_analysis(self, job_from: str, job_to: str) -> Dict:
        """Analyze skills gap between two jobs using SQL queries."""
        try:
            # Use the skills transferable analysis query if available
            transferable_query = queries.get('skills', 'get_transferable_skills_analysis') if queries else None
            if transferable_query:
                cursor = self.db.execute(transferable_query, (job_from, job_to))
                results = cursor.fetchall()
                
                # Process the results to get summary statistics
                matched_count = 0
                develop_count = 0
                transferable_count = 0
                
                for row in results:
                    if row['skill_status'] == 'matched':
                        matched_count += row['skill_count']
                    elif row['skill_status'] == 'develop':
                        develop_count += row['skill_count']
                    elif row['skill_status'] == 'transferable':
                        transferable_count += row['skill_count']
                
                total_target_skills = matched_count + develop_count
                overlap_percentage = (matched_count / total_target_skills * 100) if total_target_skills > 0 else 0
                
                return {
                    'shared_skills_count': matched_count,
                    'skills_gap_count': develop_count,
                    'transferable_skills_count': matched_count + transferable_count,
                    'source_skills_total': matched_count + transferable_count,
                    'target_skills_total': total_target_skills,
                    'skills_overlap_percentage': overlap_percentage
                }
            else:
                return self._get_skills_gap_fallback(job_from, job_to)
        except Exception as e:
            print(f"Error in skills gap analysis: {e}")
            return self._get_skills_gap_fallback(job_from, job_to)
    
    def _get_skills_gap_fallback(self, job_from: str, job_to: str) -> Dict:
        """Fallback method for skills gap analysis."""
        # Get shared skills
        shared_skills_query = """
        SELECT COUNT(*) as shared_count
        FROM job_skills js1
        JOIN job_skills js2 ON js1.Skill_ID = js2.Skill_ID
        WHERE js1.JobProfileID = ? AND js2.JobProfileID = ?
        """
        
        # Get skills needed for target job
        target_skills_query = """
        SELECT COUNT(*) as target_skills_count
        FROM job_skills
        WHERE JobProfileID = ?
        """
        
        # Get skills from source job
        source_skills_query = """
        SELECT COUNT(*) as source_skills_count
        FROM job_skills
        WHERE JobProfileID = ?
        """
        
        shared_result = self.db.execute(shared_skills_query, (job_from, job_to)).fetchone()
        target_result = self.db.execute(target_skills_query, (job_to,)).fetchone()
        source_result = self.db.execute(source_skills_query, (job_from,)).fetchone()
        
        shared_count = shared_result[0] if shared_result else 0
        target_count = target_result[0] if target_result else 0
        source_count = source_result[0] if source_result else 0
        
        skills_gap = target_count - shared_count
        transferable_skills = shared_count
        
        return {
            'shared_skills_count': shared_count,
            'skills_gap_count': max(0, skills_gap),
            'transferable_skills_count': transferable_skills,
            'source_skills_total': source_count,
            'target_skills_total': target_count,
            'skills_overlap_percentage': (shared_count / target_count * 100) if target_count > 0 else 0
        }
    
    def _get_workforce_impact(self, job_from: str, filters: Dict) -> Dict:
        """Get workforce impact data using SQL queries."""
        try:
            # Use positions queries
            job_details_query = queries.get('jobs', 'get_job_details') if queries else None
            positions_query = queries.get('positions', 'get_positions_for_job') if queries else None
            
            if job_details_query:
                job_result = self.db.execute(job_details_query, (job_from,)).fetchone()
            else:
                # Fallback query
                job_result = self.db.execute("""
                    SELECT 
                        j.JobProfile as job_title,
                        j.JobFunction as job_function,
                        j.JobFunctionID as job_function_id,
                        COUNT(p.JobProfileID) as total_positions
                    FROM jobs j
                    LEFT JOIN positions p ON j.JobProfileID = p.JobProfileID
                    WHERE j.JobProfileID = ?
                    GROUP BY j.JobProfileID, j.JobProfile, j.JobFunction, j.JobFunctionID
                """, (job_from,)).fetchone()
            
            if positions_query:
                position_results = self.db.execute(positions_query, (job_from,)).fetchall()
            else:
                position_results = self.db.execute("""
                    SELECT * FROM positions WHERE JobProfileID = ?
                """, (job_from,)).fetchall()
            
            # Get geographic and divisional distribution
            geographic_results = self.db.execute("""
                SELECT 
                    COALESCE(p.Location, 'Unknown') as location,
                    COUNT(*) as position_count
                FROM positions p
                WHERE p.JobProfileID = ?
                GROUP BY p.Location
                ORDER BY position_count DESC
            """, (job_from,)).fetchall()
            
            divisional_results = self.db.execute("""
                SELECT 
                    COALESCE(p.Division, 'Unknown') as division,
                    COUNT(*) as position_count
                FROM positions p
                WHERE p.JobProfileID = ?
                GROUP BY p.Division
                ORDER BY position_count DESC
            """, (job_from,)).fetchall()
            
            if not job_result:
                return {'total_positions': 0, 'source_job': {}}
            
            return {
                'total_positions': len(position_results) if position_results else 0,
                'source_job': {
                    'job_title': job_result['job_title'] if hasattr(job_result, 'job_title') else job_result[1],
                    'job_function': job_result['job_function'] if hasattr(job_result, 'job_function') else job_result[2],
                    'job_function_id': job_result.get('job_function_id', '') if hasattr(job_result, 'get') else ''
                },
                'geographic_distribution': [dict(row) for row in geographic_results],
                'divisional_distribution': [dict(row) for row in divisional_results],
                'location_count': len(geographic_results),
                'division_count': len(divisional_results)
            }
        except Exception as e:
            print(f"Error getting workforce impact: {e}")
            return {'total_positions': 0, 'source_job': {}}
    
    def _get_job_details(self, job_id: str) -> Dict:
        """Get basic job details using SQL queries."""
        try:
            query = queries.get('jobs', 'get_job_details') if queries else None
            if query:
                result = self.db.execute(query, (job_id,)).fetchone()
            else:
                result = self.db.execute("""
                    SELECT 
                        JobProfile as job_title,
                        JobFunction as job_function,
                        JobFunctionID as job_function_id
                    FROM jobs
                    WHERE JobProfileID = ?
                """, (job_id,)).fetchone()
            
            if result:
                return {
                    'job_title': result['job_title'] if hasattr(result, 'job_title') else result[1],
                    'job_function': result['job_function'] if hasattr(result, 'job_function') else result[2],
                    'job_function_id': result.get('job_function_id', '') if hasattr(result, 'get') else ''
                }
            return {}
        except Exception as e:
            print(f"Error getting job details: {e}")
            return {}

    def _calculate_confidence_level(self, similarity_score: float, skills_data: Dict, workforce_data: Dict) -> str:
        """Calculate confidence level based on multiple factors."""
        
        # Base confidence from similarity score
        if similarity_score >= 0.8:
            base_confidence = 0.9
        elif similarity_score >= 0.6:
            base_confidence = 0.7
        elif similarity_score >= 0.4:
            base_confidence = 0.5
        else:
            base_confidence = 0.3
        
        # Adjust for skills overlap
        skills_overlap = skills_data.get('skills_overlap_percentage', 0) / 100
        skills_factor = 0.7 + (skills_overlap * 0.3)  # 0.7 to 1.0 range
        
        # Adjust for data quality (workforce size)
        workforce_size = workforce_data.get('total_positions', 0)
        if workforce_size >= 50:
            data_quality_factor = 1.0
        elif workforce_size >= 20:
            data_quality_factor = 0.9
        elif workforce_size >= 5:
            data_quality_factor = 0.8
        else:
            data_quality_factor = 0.7
        
        # Calculate final confidence
        final_confidence = base_confidence * skills_factor * data_quality_factor
        
        # Convert to descriptive level
        if final_confidence >= 0.8:
            return "High"
        elif final_confidence >= 0.6:
            return "Medium-High"
        elif final_confidence >= 0.4:
            return "Medium"
        elif final_confidence >= 0.2:
            return "Medium-Low"
        else:
            return "Low"

    def _enhance_with_scenario_data(self, analysis: Dict, scenario: str, filters: Dict) -> Dict:
        """Enhance analysis with scenario-specific data."""
        
        if scenario == 'skill_sunsetting':
            # Add obsolete skills analysis
            obsolete_skills = self._identify_obsolete_skills(analysis['job_from'])
            analysis['obsolete_skills'] = obsolete_skills
            analysis['obsolete_skills_count'] = len(obsolete_skills)
            
        elif scenario == 'division_restructure':
            # Add division-specific context
            if filters.get('division_from') or filters.get('division_to'):
                analysis['restructure_context'] = {
                    'source_division': filters.get('division_from', 'Current Division'),
                    'target_division': filters.get('division_to', 'Target Division'),
                    'cross_division_move': filters.get('division_from') != filters.get('division_to')
                }
        
        return analysis
    
    def _identify_obsolete_skills(self, job_id: str) -> List[str]:
        """Identify skills that may become obsolete (placeholder implementation)."""
        try:
            # Get skills for the job that might be at risk
            query = """
            SELECT s.Skill_Name
            FROM job_skills js
            JOIN skills s ON js.Skill_ID = s.Skill_ID
            WHERE js.JobProfileID = ?
              AND s.Category IN ('Legacy Systems', 'Outdated Technology', 'Manual Processes')
            """
            
            cursor = self.db.execute(query, (job_id,))
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error identifying obsolete skills: {e}")
            return []
    
    def _get_fallback_analysis(self, job_from: str, job_to: str = None) -> Dict:
        """Provide fallback analysis when main analysis fails."""
        return {
            'job_from': job_from,
            'job_to': job_to,
            'avg_similarity': 0.5,
            'pathway_count': 1 if job_to else 0,
            'colleague_count': 0,
            'confidence_level': 'Low',
            'skills_shared': 0,
            'skills_to_develop': 0,
            'transferable_skills': 0,
            'source_job_details': {'job_title': 'Unknown Job', 'job_function': 'Unknown'},
            'target_job_details': {'job_title': job_to if job_to else 'Unknown', 'job_function': 'Unknown'} if job_to else {},
            'skills_breakdown': {'shared_skills_count': 0, 'skills_gap_count': 0},
            'workforce_breakdown': {'total_positions': 0},
            'summary': f'Fallback analysis for {job_from}' + (f' to {job_to}' if job_to is not None else '')
        }

