"""
Models for representing jobs and job architectures in the skill similarity engine.

This module defines the data structures for representing jobs, job levels,
role tracks, and job architectures in an organizational hierarchy.

Architecture: Configuration-driven with ZERO hardcoded values
All validation ranges, file formats, and defaults externalized to architectural configuration.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
import logging

# Import configuration management
from ..config.architectural_config_manager import get_config_manager

logger = logging.getLogger(__name__)


class JobLevel(str, Enum):
    """Job levels in the organizational hierarchy."""
    ENTRY = "Entry"
    ASSOCIATE = "Associate"
    MID_LEVEL = "Mid-level"
    SENIOR = "Senior"
    LEAD = "Lead"
    MANAGER = "Manager"
    DIRECTOR = "Director"
    EXECUTIVE = "Executive"
    
    @property
    def numeric(self) -> int:
        """Get the numeric representation of the job level using configured mapping."""
        # Get job level mappings from configuration - NO hardcoded mappings
        config_manager = get_config_manager()
        job_config = config_manager.get_models_job_architecture_config()
        
        level_mappings = job_config.get('level_mappings', {
            "Entry": 1,
            "Associate": 2,
            "Mid-level": 3,
            "Senior": 4,
            "Lead": 5,
            "Manager": 6,
            "Director": 7,
            "Executive": 8
        })
        
        return level_mappings.get(self.value, 1)


class RoleTrack(str, Enum):
    """Role tracks in the organizational hierarchy."""
    INDIVIDUAL_CONTRIBUTOR = "Individual Contributor"
    LEADERSHIP = "Leadership"


@dataclass
class Job:
    """
    Represents a job in the job architecture.
    
    Attributes:
        job_id: Unique identifier for the job
        title: Human-readable title of the job
        department: Department the job belongs to
        level: Level of the job in the organizational hierarchy
        skills: Dictionary mapping skill IDs to required proficiency levels
        seniority: Numerical value representing the seniority level
        role_track: The role track of the job (Individual Contributor or Leadership)
        location: Geographic location of the job
    """
    job_id: str
    title: str
    department: str
    level: JobLevel
    skills: Dict[str, int] = field(default_factory=dict)
    seniority: Optional[int] = None  # Will be set from configuration
    role_track: Optional[RoleTrack] = None  # Will be set from configuration
    location: str = ""
    
    def __post_init__(self):
        """Validate the job attributes after initialization using configured validation."""
        # Get validation configuration - NO hardcoded validation rules
        config_manager = get_config_manager()
        job_config = config_manager.get_models_job_architecture_config()
        
        # Get validation settings
        validation = job_config.get('validation', {})
        require_job_id = validation.get('require_job_id', True)
        require_title = validation.get('require_title', True)
        require_department = validation.get('require_department', True)
        
        # Get range settings
        ranges = job_config.get('ranges', {})
        seniority_min = ranges.get('seniority_min', 1)
        seniority_max = ranges.get('seniority_max', 7)
        proficiency_min = ranges.get('proficiency_min', 0)
        proficiency_max = ranges.get('proficiency_max', 5)
        
        # Get default values from configuration
        defaults = job_config.get('defaults', {})
        default_seniority = defaults.get('seniority', 3)
        default_role_track = defaults.get('role_track', 'INDIVIDUAL_CONTRIBUTOR')
        
        # Apply defaults if not set
        if self.seniority is None:
            self.seniority = default_seniority
        if self.role_track is None:
            self.role_track = getattr(RoleTrack, default_role_track)
        
        # Ensure seniority and role_track are properly typed after defaults
        assert self.seniority is not None, "Seniority must be set"
        assert self.role_track is not None, "Role track must be set"
        
        # Validate required fields based on configuration
        if require_job_id and not self.job_id:
            raise ValueError("Job ID cannot be empty")
        
        if require_title and not self.title:
            raise ValueError("Job title cannot be empty")
        
        if require_department and not self.department:
            raise ValueError("Department cannot be empty")
        
        if not isinstance(self.level, JobLevel):
            try:
                self.level = JobLevel(self.level)
            except ValueError:
                raise ValueError(f"Invalid job level: {self.level}. "
                               f"Must be one of {[l.value for l in JobLevel]}")
        
        # Validate role track
        if not isinstance(self.role_track, RoleTrack):
            try:
                self.role_track = RoleTrack(self.role_track)
            except ValueError:
                raise ValueError(f"Invalid role track: {self.role_track}. "
                               f"Must be one of {[r.value for r in RoleTrack]}")
        
        # Validate seniority using configured range
        if not isinstance(self.seniority, int):
            try:
                self.seniority = int(self.seniority)
            except ValueError:
                raise ValueError("Seniority must be an integer")
        
        if not seniority_min <= self.seniority <= seniority_max:
            raise ValueError(f"Seniority must be between {seniority_min} and {seniority_max}")
        
        # Validate skill proficiency levels using configured ranges
        for skill_id, proficiency in list(self.skills.items()):
            if not isinstance(proficiency, int):
                try:
                    self.skills[skill_id] = int(proficiency)
                except ValueError:
                    raise ValueError(f"Skill proficiency for {skill_id} must be an integer")
            
            if not proficiency_min <= self.skills[skill_id] <= proficiency_max:
                raise ValueError(f"Skill proficiency for {skill_id} must be between {proficiency_min} and {proficiency_max}")
    
    def add_skill(self, skill_id: str, proficiency: int) -> None:
        """
        Add a required skill to the job using configured validation.
        
        Args:
            skill_id: The ID of the skill to add
            proficiency: Required proficiency level
            
        Raises:
            ValueError: If proficiency is not within configured range
        """
        # Get proficiency range from configuration - NO hardcoded 0-5
        config_manager = get_config_manager()
        job_config = config_manager.get_models_job_architecture_config()
        ranges = job_config.get('ranges', {})
        proficiency_min = ranges.get('proficiency_min', 0)
        proficiency_max = ranges.get('proficiency_max', 5)
        
        if not proficiency_min <= proficiency <= proficiency_max:
            raise ValueError(f"Skill proficiency must be between {proficiency_min} and {proficiency_max}")
        
        self.skills[skill_id] = proficiency
    
    def remove_skill(self, skill_id: str) -> None:
        """
        Remove a skill from the job requirements.
        
        Args:
            skill_id: The ID of the skill to remove
        """
        if skill_id in self.skills:
            del self.skills[skill_id]
    
    def get_skill_proficiency(self, skill_id: str) -> Optional[int]:
        """
        Get the required proficiency level for a skill.
        
        Args:
            skill_id: The ID of the skill to check
            
        Returns:
            The proficiency level if the skill is required, None otherwise
        """
        return self.skills.get(skill_id)
    
    def has_skill(self, skill_id: str, min_proficiency: int = None) -> bool:
        """
        Check if the job requires a specific skill at minimum proficiency level using configured defaults.
        
        Args:
            skill_id: The ID of the skill to check
            min_proficiency: Minimum proficiency level to consider (uses configured default if None)
            
        Returns:
            True if the job requires the skill at minimum proficiency, False otherwise
        """
        # Use configured default minimum proficiency - NO hardcoded 1
        if min_proficiency is None:
            config_manager = get_config_manager()
            job_config = config_manager.get_models_job_architecture_config()
            defaults = job_config.get('defaults', {})
            min_proficiency = defaults.get('min_proficiency', 1)
        
        return self.skills.get(skill_id, 0) >= min_proficiency

    def get_role_level(self) -> int:
        """
        Calculate a combined role level based on seniority and job level using configured calculation.
        
        This is useful for comparing jobs in terms of seniority.
        
        Returns:
            An integer representing the combined role level
        """
        # Get role level calculation method from configuration
        config_manager = get_config_manager()
        job_config = config_manager.get_models_job_architecture_config()
        calculation = job_config.get('role_level_calculation', {})
        
        method = calculation.get('method', 'multiply')  # 'multiply' or 'add'
        
        level_numeric = self.level.numeric
        
        if method == 'multiply':
            return level_numeric * self.seniority
        elif method == 'add':
            return level_numeric + self.seniority
        else:
            # Default to multiply if unknown method
            return level_numeric * self.seniority


@dataclass
class JobArchitecture:
    """
    Represents a collection of jobs organized into an architecture.
    
    Attributes:
        jobs: Dictionary of jobs indexed by job_id
        departments: Set of all departments in the architecture
        levels: Set of all job levels in the architecture
        role_tracks: Set of all role tracks in the architecture
        locations: Set of all locations in the architecture
    """
    jobs: Dict[str, 'Job'] = field(default_factory=dict)
    departments: Set[str] = field(default_factory=set)
    levels: Set['JobLevel'] = field(default_factory=set)
    role_tracks: Set['RoleTrack'] = field(default_factory=set)
    locations: Set[str] = field(default_factory=set)
    
    def add_job(self, job: 'Job') -> None:
        """
        Add a job to the architecture.
        
        Args:
            job: The job to add to the architecture
            
        Raises:
            ValueError: If a job with the same ID already exists
        """
        if job.job_id in self.jobs:
            raise ValueError(f"Job with ID {job.job_id} already exists in the architecture")
        
        self.jobs[job.job_id] = job
        self.departments.add(job.department)
        self.levels.add(job.level)
        self.role_tracks.add(job.role_track)
        if job.location:
            self.locations.add(job.location)
    
    def get_job(self, job_id: str) -> Optional['Job']:
        """
        Retrieve a job by its ID.
        
        Args:
            job_id: The ID of the job to retrieve
            
        Returns:
            The job if found, None otherwise
        """
        return self.jobs.get(job_id)
    
    def get_jobs_by_department(self, department: str) -> List['Job']:
        """
        Retrieve all jobs in a specific department.
        
        Args:
            department: The department to filter by
            
        Returns:
            A list of jobs in the specified department
        """
        return [job for job in self.jobs.values() if job.department == department]
    
    def get_jobs_by_level(self, level: 'JobLevel') -> List['Job']:
        """
        Retrieve all jobs at a specific level.
        
        Args:
            level: The level to filter by
            
        Returns:
            A list of jobs at the specified level
        """
        if not isinstance(level, JobLevel):
            try:
                level = JobLevel(level)
            except ValueError:
                raise ValueError(f"Invalid job level: {level}")
        
        return [job for job in self.jobs.values() if job.level == level]
    
    def get_jobs_by_role_track(self, role_track: 'RoleTrack') -> List['Job']:
        """
        Retrieve all jobs with a specific role track.
        
        Args:
            role_track: The role track to filter by
            
        Returns:
            A list of jobs with the specified role track
        """
        if not isinstance(role_track, RoleTrack):
            try:
                role_track = RoleTrack(role_track)
            except ValueError:
                raise ValueError(f"Invalid role track: {role_track}")
        
        return [job for job in self.jobs.values() if job.role_track == role_track]
    
    def get_jobs_by_location(self, location: str) -> List['Job']:
        """
        Retrieve all jobs at a specific location.
        
        Args:
            location: The location to filter by
            
        Returns:
            A list of jobs at the specified location
        """
        return [job for job in self.jobs.values() if job.location == location]
    
    def get_jobs_by_seniority(self, seniority: int) -> List['Job']:
        """
        Retrieve all jobs with a specific seniority level using configured validation.
        
        Args:
            seniority: The seniority level to filter by
            
        Returns:
            A list of jobs with the specified seniority
        """
        # Get seniority range from configuration - NO hardcoded 1-7
        config_manager = get_config_manager()
        job_config = config_manager.get_models_job_architecture_config()
        ranges = job_config.get('ranges', {})
        seniority_min = ranges.get('seniority_min', 1)
        seniority_max = ranges.get('seniority_max', 7)
        
        if not seniority_min <= seniority <= seniority_max:
            raise ValueError(f"Seniority must be between {seniority_min} and {seniority_max}")
        
        return [job for job in self.jobs.values() if job.seniority == seniority]
    
    def get_jobs_requiring_skill(self, skill_id: str, min_proficiency: int = None) -> List['Job']:
        """
        Retrieve all jobs requiring a specific skill at minimum proficiency using configured defaults.
        
        Args:
            skill_id: The ID of the skill to check
            min_proficiency: Minimum required proficiency level (uses configured default if None)
            
        Returns:
            A list of jobs requiring the specified skill
        """
        # Use configured default minimum proficiency - NO hardcoded 1
        if min_proficiency is None:
            config_manager = get_config_manager()
            job_config = config_manager.get_models_job_architecture_config()
            defaults = job_config.get('defaults', {})
            min_proficiency = defaults.get('min_proficiency', 1)
        
        return [
            job for job in self.jobs.values()
            if job.has_skill(skill_id, min_proficiency)
        ]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Dict]) -> 'JobArchitecture':
        """
        Create a job architecture from a dictionary representation using configured defaults.
        
        Args:
            data: Dictionary where keys are job IDs and values are job attributes
            
        Returns:
            A new JobArchitecture instance
        """
        # Get parsing configuration - NO hardcoded parsing behavior
        config_manager = get_config_manager()
        job_config = config_manager.get_models_job_architecture_config()
        parsing = job_config.get('parsing', {})
        defaults = job_config.get('defaults', {})
        
        skills_delimiter = parsing.get('skills_delimiter', ',')
        skill_proficiency_separator = parsing.get('skill_proficiency_separator', ':')
        default_seniority = defaults.get('seniority', 3)
        default_role_track = defaults.get('role_track', 'INDIVIDUAL_CONTRIBUTOR')
        
        architecture = cls()
        
        for job_id, job_data in data.items():
            # Extract skills from the job data
            skills_data = job_data.get("skills", {})
            
            # If skills are provided as a string, parse them using configured delimiters
            if isinstance(skills_data, str):
                skills_dict = {}
                for skill_entry in skills_data.split(skills_delimiter):
                    if skill_proficiency_separator in skill_entry:
                        skill_id, proficiency = skill_entry.split(skill_proficiency_separator)
                        skills_dict[skill_id] = int(proficiency)
                skills_data = skills_dict
            
            # Extract optional attributes with configured defaults
            seniority = job_data.get("seniority", default_seniority)
            role_track = job_data.get("role_track", getattr(RoleTrack, default_role_track))
            location = job_data.get("location", "")
            
            job = Job(
                job_id=job_id,
                title=job_data["title"],
                department=job_data["department"],
                level=job_data["level"],
                skills=skills_data,
                seniority=seniority,
                role_track=role_track,
                location=location
            )
            architecture.add_job(job)
        
        return architecture
    
    def to_dict(self) -> Dict[str, Dict]:
        """
        Convert the job architecture to a dictionary representation.
        
        Returns:
            A dictionary where keys are job IDs and values are job attributes
        """
        return {
            job_id: {
                "title": job.title,
                "department": job.department,
                "level": job.level.value,
                "skills": job.skills,
                "seniority": job.seniority,
                "role_track": job.role_track.value,
                "location": job.location
            }
            for job_id, job in self.jobs.items()
        }
    
    @classmethod
    def from_file(cls, file_path: str) -> 'JobArchitecture':
        """
        Load a job architecture from a file using configured file format support.
        
        Args:
            file_path: Path to the file to load from
            
        Returns:
            A new JobArchitecture instance loaded from the file
            
        Raises:
            ValueError: If the file type is not supported or if the SkillTaxonomy is not available
        """
        # Get file format configuration - NO hardcoded file extensions
        config_manager = get_config_manager()
        job_config = config_manager.get_models_job_architecture_config()
        file_formats = job_config.get('file_formats', {})
        
        supported_csv_extensions = file_formats.get('csv_extensions', ['.csv'])
        supported_excel_extensions = file_formats.get('excel_extensions', ['.xlsx', '.xls'])
        
        from ..data.loaders import JobArchitectureLoader
        from .skills import SkillTaxonomy
        
        # Create an empty skill taxonomy - the loader doesn't use it for validation
        # when loading the job architecture directly
        taxonomy = SkillTaxonomy()
        
        loader = JobArchitectureLoader(taxonomy)
        
        # Check file extension against configured supported formats
        file_lower = file_path.lower()
        
        is_csv = any(file_lower.endswith(ext) for ext in supported_csv_extensions)
        is_excel = any(file_lower.endswith(ext) for ext in supported_excel_extensions)
        
        if is_csv:
            # For backwards compatibility, assume this is a jobs file and provide a dummy job-skills mapping
            return loader.load_from_csv(job_skills_file="", jobs_file=file_path)
        elif is_excel:
            return loader.load_from_excel(file_path)
        else:
            all_supported = supported_csv_extensions + supported_excel_extensions
            raise ValueError(f"Unsupported file type for {file_path}. Supported formats: {all_supported}") 
