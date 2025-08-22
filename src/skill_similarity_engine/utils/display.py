"""
Job Display Name Formatting Module

This module provides centralised job display name formatting functionality,
consolidating and enhancing the LogicalRoleManager from the whitepaper system.
Supports multiple display formats for different use cases and prepares for 
the upcoming job architecture refactoring.

Key Features:
- Multiple display formats (current logical format, future standard format)  
- Database-driven job information retrieval
- Fallback handling for missing data
- Consistent job naming across the entire application

Usage:
    from skill_similarity_engine.utils.display import JobDisplayManager
    
    display_manager = JobDisplayManager(db_connection)
    
    # Current logical format: "Risk Analyst (Group 2)"
    logical_name = display_manager.get_logical_display_name("R0100.2")
    
    # Future standard format: "Risk Analyst - Senior Manager - Group 2"  
    standard_name = display_manager.get_standard_display_name("R0100.2")
    
    # Search-friendly format: "Risk Analyst - Senior Manager (Group 2)"
    search_name = display_manager.get_search_display_name("R0100.2")
"""

from typing import Dict, Optional, Any, List, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

# Set up logging
logger = logging.getLogger(__name__)


class DisplayFormat(str, Enum):
    """Available job display name formats."""
    LOGICAL = "logical"              # "Risk Analyst (Group 2)" - current format
    STANDARD = "standard"            # "Risk Analyst - Senior Manager - Group 2" - future format
    SEARCH = "search"               # "Risk Analyst - Senior Manager (Group 2)" - search-friendly
    COMPACT = "compact"             # "Risk Analyst (Sr Mgr)" - abbreviated format
    DROPDOWN = "dropdown"           # "Risk Analyst - Senior Manager" - dropdown format


@dataclass
class JobData:
    """Container for job information retrieved from database."""
    job_profile_id: str
    job_profile: str
    job: str
    profile_title_suffix: str
    management_level: str
    job_function: str
    job_sub_function: Optional[str] = None
    job_category: Optional[str] = None
    customer_facing: Optional[str] = None
    is_banker: Optional[str] = None


class JobDisplayManager:
    """
    Manages job display name formatting with support for multiple formats.
    
    This class consolidates the LogicalRoleManager functionality from the whitepaper
    system and extends it to support the upcoming job architecture refactoring.
    """
    
    def __init__(self, db_connection):
        """
        Initialize the JobDisplayManager.
        
        Args:
            db_connection: Database connection object with execute() method
        """
        self.db = db_connection
        
        # Cache for job data to avoid repeated database queries
        self._job_cache: Dict[str, JobData] = {}
        
        # Abbreviation mappings for compact format
        self._abbreviations = {
            'Senior Manager': 'Sr Mgr',
            'Manager': 'Mgr', 
            'Senior Consultant': 'Sr Cons',
            'Consultant': 'Cons',
            'Lead Consultant': 'Lead Cons',
            'Associate': 'Assoc',
            'Analyst': 'Analyst',
            'Team Lead': 'TL',
            'Team Member': 'TM',
            'Head of': 'Head',
            'Group Executive': 'GE',
            'Group 1': 'G1',
            'Group 2': 'G2',
            'Group 3': 'G3',
            'Group 4': 'G4',
            'Group 5': 'G5',
            'Group 6': 'G6',
            'Group 7': 'G7',
            'Group NA': 'GNA'
        }
    
    def get_job_data(self, job_profile_id: str, use_cache: bool = True) -> Optional[JobData]:
        """
        Retrieve comprehensive job data from database.
        
        Args:
            job_profile_id: The JobProfileID to look up
            use_cache: Whether to use cached data if available
            
        Returns:
            JobData object with job information, or None if not found
        """
        # Validate input
        if not job_profile_id or not job_profile_id.strip():
            return None
            
        # Check cache first if enabled
        if use_cache and job_profile_id in self._job_cache:
            return self._job_cache[job_profile_id]
        
        try:
            query = """
            SELECT 
                JobProfileID,
                JobProfile,
                Job,
                ProfileTitleSuffix,
                ManagementLevel,
                JobFunction,
                JobSubFunction,
                JobCategory,
                Customer_Facing,
                is_Banker
            FROM core_job_architecture 
            WHERE JobProfileID = ?
            """
            
            result = self.db.execute(query, (job_profile_id,)).fetchone()
            
            if not result:
                logger.warning(f"Job not found: {job_profile_id}")
                return None
            
            # Create JobData object
            job_data = JobData(
                job_profile_id=result[0],
                job_profile=result[1] or "",
                job=result[2] or "",
                profile_title_suffix=result[3] or "",
                management_level=result[4] or "Group 1",
                job_function=result[5] or "",
                job_sub_function=result[6],
                job_category=result[7],
                customer_facing=result[8],
                is_banker=result[9]
            )
            
            # Cache the result
            if use_cache:
                self._job_cache[job_profile_id] = job_data
            
            return job_data
            
        except Exception as e:
            if job_profile_id:  # Only log if not empty
                logger.error(f"Error retrieving job data for {job_profile_id}: {e}")
            return None
    
    def get_logical_display_name(self, job_profile_id: str) -> str:
        """
        Get logical role display name: 'Job Title (Management Level)'
        
        This is the current format used in the whitepaper system.
        Compatible with existing LogicalRoleManager.get_logical_role_display_name()
        
        Args:
            job_profile_id: The JobProfileID to format
            
        Returns:
            Formatted display name or job_profile_id if formatting fails
            
        Examples:
            "Risk Analyst (Group 2)"
            "Data Scientist (Group 4)"
        """
        job_data = self.get_job_data(job_profile_id)
        
        if not job_data:
            return job_profile_id
            
        try:
            # Use the Job field (broader category) rather than JobProfile (specific instance)
            job_title = job_data.job or job_data.job_profile
            
            # Remove any existing suffix from JobProfile if Job is empty
            if not job_data.job and " - " in job_data.job_profile:
                job_title = job_data.job_profile.split(" - ")[0]
            
            return f"{job_title} ({job_data.management_level})"
            
        except Exception as e:
            logger.error(f"Error formatting logical display name for {job_profile_id}: {e}")
            return job_profile_id
    
    def get_standard_display_name(self, job_profile_id: str) -> str:
        """
        Get standard display name: 'Job - ProfileTitleSuffix - ManagementLevel'
        
        This is the target format for the job architecture refactoring.
        
        Args:
            job_profile_id: The JobProfileID to format
            
        Returns:
            Formatted display name or job_profile_id if formatting fails
            
        Examples:
            "Risk Analyst - Senior Manager - Group 2"
            "Data Scientist - Manager - Group 4"
        """
        job_data = self.get_job_data(job_profile_id)
        
        if not job_data:
            return job_profile_id
            
        try:
            job_title = job_data.job or job_data.job_profile.split(" - ")[0]
            suffix = job_data.profile_title_suffix
            level = job_data.management_level
            
            return f"{job_title} - {suffix} - {level}"
            
        except Exception as e:
            logger.error(f"Error formatting standard display name for {job_profile_id}: {e}")
            return job_profile_id
    
    def get_search_display_name(self, job_profile_id: str) -> str:
        """
        Get search-friendly display name: 'Job - ProfileTitleSuffix (ManagementLevel)'
        
        Optimised for search dropdowns and autocomplete functionality.
        
        Args:
            job_profile_id: The JobProfileID to format
            
        Returns:
            Formatted display name or job_profile_id if formatting fails
            
        Examples:
            "Risk Analyst - Senior Manager (Group 2)"
            "Data Scientist - Manager (Group 4)"
        """
        job_data = self.get_job_data(job_profile_id)
        
        if not job_data:
            return job_profile_id
            
        try:
            job_title = job_data.job or job_data.job_profile.split(" - ")[0]
            suffix = job_data.profile_title_suffix
            level = job_data.management_level
            
            return f"{job_title} - {suffix} ({level})"
            
        except Exception as e:
            logger.error(f"Error formatting search display name for {job_profile_id}: {e}")
            return job_profile_id
    
    def get_compact_display_name(self, job_profile_id: str) -> str:
        """
        Get compact display name with abbreviations: 'Job (Abbrev)'
        
        Useful for space-constrained displays like mobile or dashboard widgets.
        
        Args:
            job_profile_id: The JobProfileID to format
            
        Returns:
            Abbreviated display name or job_profile_id if formatting fails
            
        Examples:
            "Risk Analyst (Sr Mgr)"
            "Data Scientist (Mgr)"
        """
        job_data = self.get_job_data(job_profile_id)
        
        if not job_data:
            return job_profile_id
            
        try:
            job_title = job_data.job or job_data.job_profile.split(" - ")[0]
            
            # Abbreviate both suffix and level
            suffix_abbrev = self._abbreviations.get(job_data.profile_title_suffix, job_data.profile_title_suffix)
            level_abbrev = self._abbreviations.get(job_data.management_level, job_data.management_level)
            
            return f"{job_title} ({suffix_abbrev})"
            
        except Exception as e:
            logger.error(f"Error formatting compact display name for {job_profile_id}: {e}")
            return job_profile_id
    
    def get_dropdown_display_name(self, job_profile_id: str) -> str:
        """
        Get dropdown-optimised display name: 'Job - ProfileTitleSuffix'
        
        Excludes management level for cleaner dropdown appearance.
        
        Args:
            job_profile_id: The JobProfileID to format
            
        Returns:
            Formatted display name or job_profile_id if formatting fails
            
        Examples:
            "Risk Analyst - Senior Manager"
            "Data Scientist - Manager"
        """
        job_data = self.get_job_data(job_profile_id)
        
        if not job_data:
            return job_profile_id
            
        try:
            job_title = job_data.job or job_data.job_profile.split(" - ")[0]
            suffix = job_data.profile_title_suffix
            
            return f"{job_title} - {suffix}"
            
        except Exception as e:
            logger.error(f"Error formatting dropdown display name for {job_profile_id}: {e}")
            return job_profile_id
    
    def get_display_name(self, job_profile_id: str, format_type: DisplayFormat = DisplayFormat.LOGICAL) -> str:
        """
        Get job display name in the specified format.
        
        Args:
            job_profile_id: The JobProfileID to format
            format_type: The display format to use
            
        Returns:
            Formatted display name in the requested format
        """
        format_methods = {
            DisplayFormat.LOGICAL: self.get_logical_display_name,
            DisplayFormat.STANDARD: self.get_standard_display_name,
            DisplayFormat.SEARCH: self.get_search_display_name,
            DisplayFormat.COMPACT: self.get_compact_display_name,
            DisplayFormat.DROPDOWN: self.get_dropdown_display_name
        }
        
        method = format_methods.get(format_type, self.get_logical_display_name)
        return method(job_profile_id)
    
    def format_job_search_results(self, job_results: List[Dict[str, Any]], 
                                 format_type: DisplayFormat = DisplayFormat.SEARCH) -> List[Dict[str, Any]]:
        """
        Format a list of job search results with consistent display names.
        
        Args:
            job_results: List of job dictionaries (typically from database query)
            format_type: Display format to apply
            
        Returns:
            List of job dictionaries with added 'display_name' field
        """
        formatted_results = []
        
        for job in job_results:
            job_copy = job.copy()
            job_id = job.get('id') or job.get('JobProfileID') or job.get('job_profile_id')
            
            if job_id:
                job_copy['display_name'] = self.get_display_name(job_id, format_type)
            else:
                # Fallback: construct display name from available fields
                job_title = job.get('job_profile', job.get('JobProfile', ''))
                job_copy['display_name'] = job_title
            
            formatted_results.append(job_copy)
        
        return formatted_results
    
    def get_representative_profile_id(self, job_profile: str, management_level: str) -> Optional[str]:
        """
        Get representative JobProfileID for a logical role combination.
        
        This method is compatible with the existing LogicalRoleManager method.
        
        Args:
            job_profile: Base job profile name (without suffix)
            management_level: Management level (e.g., "Group 2")
            
        Returns:
            Representative JobProfileID or None if not found
        """
        try:
            # Remove suffix and get base job profile name
            base_job_profile = job_profile.split(" - ")[0] if " - " in job_profile else job_profile
            
            query = """
            SELECT MIN(JobProfileID) as representative_id
            FROM jobs 
            WHERE (Job = ? OR JobProfile LIKE ?)
              AND ManagementLevel = ?
            """
            
            like_pattern = f"{base_job_profile} - %"
            result = self.db.execute(query, (base_job_profile, like_pattern, management_level)).fetchone()
            return result[0] if result and result[0] else None
            
        except Exception as e:
            logger.error(f"Error getting representative profile for {job_profile}, {management_level}: {e}")
            return None
    
    def clear_cache(self):
        """Clear the job data cache."""
        self._job_cache.clear()
        logger.debug("Job display cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            'cached_jobs': len(self._job_cache),
            'memory_estimate_kb': len(self._job_cache) * 2  # Rough estimate
        }


# Convenience functions for backward compatibility
def get_logical_role_display_name(job_profile_id: str, db_connection) -> str:
    """
    Backward compatibility function for existing LogicalRoleManager usage.
    
    Args:
        job_profile_id: The JobProfileID to format
        db_connection: Database connection object
        
    Returns:
        Logical display name format: "Job Title (Management Level)"
    """
    manager = JobDisplayManager(db_connection)
    return manager.get_logical_display_name(job_profile_id)


def get_standard_display_name(job_profile_id: str, db_connection) -> str:
    """
    Get standard display name for job architecture refactoring.
    
    Args:
        job_profile_id: The JobProfileID to format  
        db_connection: Database connection object
        
    Returns:
        Standard display name format: "Job - ProfileTitleSuffix - ManagementLevel"
    """
    manager = JobDisplayManager(db_connection)
    return manager.get_standard_display_name(job_profile_id)


def format_job_display_name(job: str, profile_title_suffix: str, management_level: str) -> str:
    """
    Format job display name using standard convention (for future refactoring).
    
    Args:
        job: Base job title
        profile_title_suffix: Profile title suffix
        management_level: Management level
        
    Returns:
        Formatted display name: "Job - ProfileTitleSuffix - ManagementLevel"
    """
    return f"{job} - {profile_title_suffix} - {management_level}"


# Export main classes and functions
__all__ = [
    'JobDisplayManager',
    'JobData', 
    'DisplayFormat',
    'get_logical_role_display_name',
    'get_standard_display_name',
    'format_job_display_name'
] 
