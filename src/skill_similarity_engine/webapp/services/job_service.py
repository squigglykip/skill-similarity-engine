"""
Job Service for NAB Skills Intelligence Platform
===============================================

Provides job display management and formatting functionality.
Extracted from app.py as part of Phase 2 modularization.

Handles:
- Job display name management
- Display manager initialization
- Job formatting utilities
"""

from typing import Dict, Any, Optional
from flask import g

class JobService:
    """Service for job display management and formatting."""
    
    def __init__(self, display_manager=None, webapp_config=None):
        """Initialize job service with optional display manager and configuration."""
        self.display_manager = display_manager
        self.webapp_config = webapp_config
        self._display_manager_available = self._check_display_manager_availability()
        
        # Get service configuration
        if webapp_config:
            self.service_config = webapp_config.get_service_config().get_job_service_config()
        else:
            # Fallback configuration
            self.service_config = {
                'default_display_format': 'standard',
                'display_name_formats': ['standard', 'search', 'dropdown', 'compact'],
                'fallback_enabled': True,
            }
    
    def _check_display_manager_availability(self) -> bool:
        """Check if JobDisplayManager is available."""
        try:
            from ...utils.display import JobDisplayManager, DisplayFormat
            return True
        except ImportError:
            return False
    
    def get_display_manager(self):
        """Get JobDisplayManager instance for consistent job naming."""
        if self.display_manager:
            return self.display_manager
            
        if self._display_manager_available:
            try:
                from ...utils.display import JobDisplayManager
                db = g.get('db') if g else None
                if db:
                    return JobDisplayManager(db)
            except (ImportError, AttributeError):
                pass
        return None
    
    def add_display_names_to_job(self, job_data: Dict[str, Any], display_manager=None) -> Dict[str, Any]:
        """Add standardised display names to job data."""
        if not display_manager:
            display_manager = self.get_display_manager()
        
        if display_manager and job_data and self._display_manager_available:
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
    
    def format_job_for_display(self, job_data: Dict[str, Any], format_type: Optional[str] = None) -> Dict[str, Any]:
        """Format job data for display with specified format type."""
        if format_type is None:
            format_type = self.service_config['default_display_format']
            
        enhanced_job = self.add_display_names_to_job(job_data.copy())
        
        # Use the appropriate display name based on format type
        display_name_key = f'display_name_{format_type}'
        if display_name_key in enhanced_job:
            enhanced_job['formatted_name'] = enhanced_job[display_name_key]
        else:
            # Fallback to job title or basic formatting
            enhanced_job['formatted_name'] = enhanced_job.get('job_title') or enhanced_job.get('JobProfile') or 'Unknown Job'
        
        return enhanced_job
    
    def format_jobs_for_display(self, jobs_list: list, format_type: str = 'standard') -> list:
        """Format a list of jobs for display."""
        if not jobs_list:
            return []
        
        formatted_jobs = []
        display_manager = self.get_display_manager()
        
        for job in jobs_list:
            if isinstance(job, dict):
                job_dict = job
            else:
                # Convert sqlite Row to dict
                job_dict = dict(job)
            
            formatted_job = self.add_display_names_to_job(job_dict, display_manager)
            formatted_jobs.append(formatted_job)
        
        return formatted_jobs 