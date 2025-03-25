"""
Models for representing jobs and job architecture in the skill similarity engine.

This module defines the data structures for representing jobs, including their
required skills and proficiency levels.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

from .skills import Skill, SkillTaxonomy


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


@dataclass
class Job:
    """
    Represents a job in the job architecture.
    
    Attributes:
        job_id: Unique identifier for the job
        title: Human-readable title of the job
        department: Department the job belongs to
        level: Level of the job in the organizational hierarchy
        skills: Dictionary mapping skill IDs to required proficiency levels (0-5)
    """
    job_id: str
    title: str
    department: str
    level: JobLevel
    skills: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the job attributes after initialization."""
        if not self.job_id:
            raise ValueError("Job ID cannot be empty")
        
        if not self.title:
            raise ValueError("Job title cannot be empty")
        
        if not self.department:
            raise ValueError("Department cannot be empty")
        
        if not isinstance(self.level, JobLevel):
            try:
                self.level = JobLevel(self.level)
            except ValueError:
                raise ValueError(f"Invalid job level: {self.level}. "
                               f"Must be one of {[l.value for l in JobLevel]}")
        
        # Validate skill proficiency levels
        for skill_id, proficiency in list(self.skills.items()):
            if not isinstance(proficiency, int):
                try:
                    self.skills[skill_id] = int(proficiency)
                except ValueError:
                    raise ValueError(f"Skill proficiency for {skill_id} must be an integer")
            
            if not 0 <= self.skills[skill_id] <= 5:
                raise ValueError(f"Skill proficiency for {skill_id} must be between 0 and 5")
    
    def add_skill(self, skill_id: str, proficiency: int) -> None:
        """
        Add a required skill to the job.
        
        Args:
            skill_id: The ID of the skill to add
            proficiency: Required proficiency level (0-5)
            
        Raises:
            ValueError: If proficiency is not between 0 and 5
        """
        if not 0 <= proficiency <= 5:
            raise ValueError("Skill proficiency must be between 0 and 5")
        
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
    
    def has_skill(self, skill_id: str, min_proficiency: int = 1) -> bool:
        """
        Check if the job requires a specific skill at minimum proficiency level.
        
        Args:
            skill_id: The ID of the skill to check
            min_proficiency: Minimum proficiency level to consider
            
        Returns:
            True if the job requires the skill at minimum proficiency, False otherwise
        """
        return self.skills.get(skill_id, 0) >= min_proficiency


@dataclass
class JobArchitecture:
    """
    Represents a collection of jobs organized into an architecture.
    
    Attributes:
        jobs: Dictionary of jobs indexed by job_id
        departments: Set of all departments in the architecture
        levels: Set of all job levels in the architecture
    """
    jobs: Dict[str, Job] = field(default_factory=dict)
    departments: Set[str] = field(default_factory=set)
    levels: Set[JobLevel] = field(default_factory=set)
    
    def add_job(self, job: Job) -> None:
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
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Retrieve a job by its ID.
        
        Args:
            job_id: The ID of the job to retrieve
            
        Returns:
            The job if found, None otherwise
        """
        return self.jobs.get(job_id)
    
    def get_jobs_by_department(self, department: str) -> List[Job]:
        """
        Retrieve all jobs in a specific department.
        
        Args:
            department: The department to filter by
            
        Returns:
            A list of jobs in the specified department
        """
        return [job for job in self.jobs.values() if job.department == department]
    
    def get_jobs_by_level(self, level: JobLevel) -> List[Job]:
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
    
    def get_jobs_requiring_skill(self, skill_id: str, min_proficiency: int = 1) -> List[Job]:
        """
        Retrieve all jobs requiring a specific skill at minimum proficiency.
        
        Args:
            skill_id: The ID of the skill to check
            min_proficiency: Minimum required proficiency level
            
        Returns:
            A list of jobs requiring the specified skill
        """
        return [
            job for job in self.jobs.values()
            if job.has_skill(skill_id, min_proficiency)
        ]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Dict]) -> 'JobArchitecture':
        """
        Create a job architecture from a dictionary representation.
        
        Args:
            data: Dictionary where keys are job IDs and values are job attributes
            
        Returns:
            A new JobArchitecture instance
        """
        architecture = cls()
        
        for job_id, job_data in data.items():
            # Extract skills from the job data
            skills_data = job_data.get("skills", {})
            
            # If skills are provided as a string (e.g., "S001:4,S002:5"), parse them
            if isinstance(skills_data, str):
                skills_dict = {}
                for skill_entry in skills_data.split(","):
                    if ":" in skill_entry:
                        skill_id, proficiency = skill_entry.split(":")
                        skills_dict[skill_id] = int(proficiency)
                skills_data = skills_dict
            
            job = Job(
                job_id=job_id,
                title=job_data["title"],
                department=job_data["department"],
                level=job_data["level"],
                skills=skills_data
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
                "skills": job.skills
            }
            for job_id, job in self.jobs.items()
        }
    
    @classmethod
    def from_file(cls, file_path: str) -> 'JobArchitecture':
        """
        Load a job architecture from a file (CSV or Excel).
        
        Args:
            file_path: Path to the file to load from
            
        Returns:
            A new JobArchitecture instance loaded from the file
            
        Raises:
            ValueError: If the file type is not supported or if the SkillTaxonomy is not available
        """
        from ..data.loaders import JobArchitectureLoader
        from .skills import SkillTaxonomy
        
        # Create an empty skill taxonomy - the loader doesn't use it for validation
        # when loading the job architecture directly
        taxonomy = SkillTaxonomy()
        
        loader = JobArchitectureLoader(taxonomy)
        if file_path.endswith('.csv'):
            return loader.load_from_csv(file_path)
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            return loader.load_from_excel(file_path)
        else:
            raise ValueError(f"Unsupported file type for {file_path}. Use CSV or Excel files.") 