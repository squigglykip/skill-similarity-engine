"""
Validation Service

Handles validation and sanitisation of form data for career analysis requests.
Ensures data integrity before passing to generators.
"""

from typing import Dict, Tuple, List, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)

class ValidationService:
    """
    Service for validating form data before career analysis generation.
    
    Validates job IDs, parameters, and sanitises input to prevent issues
    with the generators and database queries.
    """
    
    def __init__(self, db_connection):
        """Initialize with database connection for job validation."""
        self.db = db_connection
        logger.info("ValidationService initialized")
    
    def validate_form_data(self, form_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Validate and clean form data for career analysis.
        
        Args:
            form_data: Raw form data from web request
            
        Returns:
            Tuple of (is_valid, cleaned_data, error_messages)
        """
        errors = []
        cleaned_data = {}
        
        try:
            # Validate required job_from
            job_from = self._validate_job_id(form_data.get('job_from'), 'job_from', errors)
            if job_from:
                cleaned_data['job_from'] = job_from
            
            # Validate analysis mode
            analysis_mode = self._validate_analysis_mode(form_data.get('analysis_mode'), errors)
            cleaned_data['analysis_mode'] = analysis_mode
            
            # Validate optional job_to (for specific mode)
            if analysis_mode == 'specific':
                job_to = self._validate_job_id(form_data.get('job_to'), 'job_to', errors)
                if job_to:
                    cleaned_data['job_to'] = job_to
            
            # Validate similarity range
            similarity_min, similarity_max = self._validate_similarity_range(
                form_data.get('similarity_min'), 
                form_data.get('similarity_max'), 
                errors
            )
            cleaned_data['similarity_min'] = similarity_min
            cleaned_data['similarity_max'] = similarity_max
            
            # Validate top_n
            top_n = self._validate_top_n(form_data.get('top_n'), errors)
            cleaned_data['top_n'] = top_n
            
            # Validate boolean flags
            cleaned_data['include_organisational_deployment'] = bool(
                form_data.get('include_organisational_deployment', False)
            )
            
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.info(f"Form validation successful for job {cleaned_data['job_from']}")
            else:
                logger.warning(f"Form validation failed: {errors}")
            
            return is_valid, cleaned_data, errors
            
        except Exception as e:
            logger.error(f"Unexpected error during validation: {str(e)}", exc_info=True)
            errors.append(f"Validation error: {str(e)}")
            return False, {}, errors
    
    def _validate_job_id(self, job_id: Any, field_name: str, errors: List[str]) -> Optional[str]:
        """Validate job ID format and existence."""
        if not job_id:
            if field_name == 'job_from':
                errors.append(f"{field_name} is required")
            return None
        
        # Convert to string and clean
        job_id = str(job_id).strip().upper()
        
        # Check format (e.g., R0102.3, C1234.1)
        if not re.match(r'^[A-Z]\d{4}\.\d+$', job_id):
            errors.append(f"{field_name} must be in format like 'R0102.3' or 'C1234.1'")
            return None
        
        # Check if job exists in database using correct table name
        if not self._job_exists_in_database(job_id):
            errors.append(f"Job ID '{job_id}' not found in database")
            return None
        
        return job_id
    
    def _validate_analysis_mode(self, mode: Any, errors: List[str]) -> str:
        """Validate analysis mode."""
        if not mode:
            return 'top_matches'  # Default
        
        mode = str(mode).lower().strip()
        if mode not in ['top_matches', 'specific']:
            errors.append("analysis_mode must be 'top_matches' or 'specific'")
            return 'top_matches'
        
        return mode
    
    def _validate_similarity_range(self, min_val: Any, max_val: Any, errors: List[str]) -> Tuple[int, int]:
        """Validate similarity percentage range."""
        # Default values
        default_min, default_max = 40, 90
        
        try:
            similarity_min = int(min_val) if min_val is not None else default_min
            similarity_max = int(max_val) if max_val is not None else default_max
        except (ValueError, TypeError):
            errors.append("similarity_min and similarity_max must be integers")
            return default_min, default_max
        
        # Validate range
        if similarity_min < 0 or similarity_min > 100:
            errors.append("similarity_min must be between 0 and 100")
            similarity_min = default_min
        
        if similarity_max < 0 or similarity_max > 100:
            errors.append("similarity_max must be between 0 and 100")
            similarity_max = default_max
        
        if similarity_min >= similarity_max:
            errors.append("similarity_min must be less than similarity_max")
            return default_min, default_max
        
        return similarity_min, similarity_max
    
    def _validate_top_n(self, top_n: Any, errors: List[str]) -> int:
        """Validate top_n parameter."""
        if top_n is None:
            return 3  # Default
        
        try:
            top_n = int(top_n)
        except (ValueError, TypeError):
            errors.append("top_n must be an integer")
            return 3
        
        if top_n < 1 or top_n > 20:
            errors.append("top_n must be between 1 and 20")
            return 3
        
        return top_n
    
    def _job_exists_in_database(self, job_id: str) -> bool:
        """Check if job ID exists in the database using correct table name."""
        try:
            cursor = self.db.execute(
                "SELECT COUNT(*) as count FROM jobs WHERE JobProfileID = ?",
                (job_id,)
            )
            result = cursor.fetchone()
            return result['count'] > 0 if result else False
        except Exception as e:
            logger.error(f"Database error checking job existence: {str(e)}")
            return False
    
    def get_available_jobs(self, limit: int = 100) -> List[Dict[str, str]]:
        """Get list of available job IDs and titles for form validation."""
        try:
            cursor = self.db.execute("""
                SELECT JobProfileID, JobProfile 
                FROM jobs 
                ORDER BY JobProfile 
                LIMIT ?
            """, (limit,))
            
            return [
                {'id': row['JobProfileID'], 'title': row['JobProfile']}
                for row in cursor.fetchall()
            ]
        except Exception as e:
            logger.error(f"Error fetching available jobs: {str(e)}")
            return [] 