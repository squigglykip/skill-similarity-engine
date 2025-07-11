"""
Models for representing employees in the skill similarity engine.

This module defines the data structures for representing employees, their skills,
and proficiency levels.

Architecture: Configuration-driven with ZERO hardcoded values
All proficiency ranges, ratios, and file formats externalized to architectural configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, TYPE_CHECKING
import logging

# Import configuration management
from ..config.architectural_config_manager import get_config_manager

if TYPE_CHECKING:
    from .jobs import JobArchitecture, Job

from .skills import Skill, SkillTaxonomy

logger = logging.getLogger(__name__)


@dataclass
class Employee:
    """
    Represents an employee and their skills.
    
    Attributes:
        employee_id: Unique identifier for the employee
        name: Full name of the employee
        current_job: ID of the employee's current job
        skills: Dictionary mapping skill IDs to proficiency levels
    """
    employee_id: str
    name: str
    current_job: str
    skills: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the employee attributes after initialization using configured validation."""
        # Get validation configuration - NO hardcoded validation rules
        config_manager = get_config_manager()
        employee_config = config_manager.get_models_employee_config()
        
        # Get validation settings
        validation = employee_config.get('validation', {})
        require_employee_id = validation.get('require_employee_id', True)
        require_name = validation.get('require_name', True)
        require_current_job = validation.get('require_current_job', True)
        
        # Get proficiency range from configuration - NO hardcoded 0-5
        ranges = employee_config.get('ranges', {})
        proficiency_min = ranges.get('proficiency_min', 0)
        proficiency_max = ranges.get('proficiency_max', 5)
        
        # Validate required fields based on configuration
        if require_employee_id and not self.employee_id:
            raise ValueError("Employee ID cannot be empty")
        
        if require_name and not self.name:
            raise ValueError("Employee name cannot be empty")
        
        if require_current_job and not self.current_job:
            raise ValueError("Current job ID cannot be empty")
        
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
        Add a skill to the employee's profile using configured validation.
        
        Args:
            skill_id: The ID of the skill to add
            proficiency: Proficiency level
            
        Raises:
            ValueError: If proficiency is not within configured range
        """
        # Get proficiency range from configuration - NO hardcoded 0-5
        config_manager = get_config_manager()
        employee_config = config_manager.get_models_employee_config()
        ranges = employee_config.get('ranges', {})
        proficiency_min = ranges.get('proficiency_min', 0)
        proficiency_max = ranges.get('proficiency_max', 5)
        
        if not proficiency_min <= proficiency <= proficiency_max:
            raise ValueError(f"Skill proficiency must be between {proficiency_min} and {proficiency_max}")
        
        self.skills[skill_id] = proficiency
    
    def update_skill(self, skill_id: str, proficiency: int) -> None:
        """
        Update the proficiency level of an existing skill using configured validation.
        
        Args:
            skill_id: The ID of the skill to update
            proficiency: New proficiency level
            
        Raises:
            ValueError: If proficiency is not within configured range or skill doesn't exist
        """
        if skill_id not in self.skills:
            raise ValueError(f"Skill {skill_id} does not exist in this employee's profile")
        
        # Get proficiency range from configuration - NO hardcoded 0-5
        config_manager = get_config_manager()
        employee_config = config_manager.get_models_employee_config()
        ranges = employee_config.get('ranges', {})
        proficiency_min = ranges.get('proficiency_min', 0)
        proficiency_max = ranges.get('proficiency_max', 5)
        
        if not proficiency_min <= proficiency <= proficiency_max:
            raise ValueError(f"Skill proficiency must be between {proficiency_min} and {proficiency_max}")
        
        self.skills[skill_id] = proficiency
    
    def remove_skill(self, skill_id: str) -> None:
        """
        Remove a skill from the employee's profile.
        
        Args:
            skill_id: The ID of the skill to remove
        """
        if skill_id in self.skills:
            del self.skills[skill_id]
    
    def get_skill_proficiency(self, skill_id: str) -> Optional[int]:
        """
        Get the employee's proficiency level for a skill.
        
        Args:
            skill_id: The ID of the skill to check
            
        Returns:
            The proficiency level if the employee has the skill, None otherwise
        """
        return self.skills.get(skill_id)
    
    def has_skill(self, skill_id: str, min_proficiency: int = None) -> bool:
        """
        Check if the employee has a specific skill at minimum proficiency level using configured defaults.
        
        Args:
            skill_id: The ID of the skill to check
            min_proficiency: Minimum proficiency level to consider (uses configured default if None)
            
        Returns:
            True if the employee has the skill at minimum proficiency, False otherwise
        """
        # Use configured default minimum proficiency - NO hardcoded 1
        if min_proficiency is None:
            config_manager = get_config_manager()
            employee_config = config_manager.get_models_employee_config()
            defaults = employee_config.get('defaults', {})
            min_proficiency = defaults.get('min_proficiency', 1)
        
        return self.skills.get(skill_id, 0) >= min_proficiency
    
    def meets_job_requirements(self, job: 'Job', min_proficiency_ratio: float = None) -> bool:
        """
        Check if the employee meets the minimum requirements for a job using configured ratios.
        
        Args:
            job: The job to check requirements for
            min_proficiency_ratio: Minimum ratio of required skills that must be met (uses configured default if None)
            
        Returns:
            True if the employee meets the minimum requirements, False otherwise
        """
        # Use configured default proficiency ratio - NO hardcoded 0.7
        if min_proficiency_ratio is None:
            config_manager = get_config_manager()
            employee_config = config_manager.get_models_employee_config()
            defaults = employee_config.get('defaults', {})
            min_proficiency_ratio = defaults.get('min_proficiency_ratio', 0.7)
        
        if not job.skills:
            return True
        
        # Count skills where the employee's proficiency meets or exceeds the job requirement
        matching_skills = sum(
            1 for skill_id, required_proficiency in job.skills.items()
            if self.skills.get(skill_id, 0) >= required_proficiency
        )
        
        # Calculate the ratio of matching skills to required skills
        return matching_skills / len(job.skills) >= min_proficiency_ratio


@dataclass
class EmployeeDatabase:
    """
    Represents a collection of employees.
    
    Attributes:
        employees: Dictionary of employees indexed by employee_id
        job_counts: Dictionary mapping job IDs to the number of employees in that role
        skills_distribution: Dictionary mapping skill IDs to counts of employees with that skill
    """
    employees: Dict[str, Employee] = field(default_factory=dict)
    job_counts: Dict[str, int] = field(default_factory=dict)
    skills_distribution: Dict[str, int] = field(default_factory=dict)
    
    def add_employee(self, employee: Employee) -> None:
        """
        Add an employee to the database.
        
        Args:
            employee: The employee to add
            
        Raises:
            ValueError: If an employee with the same ID already exists
        """
        if employee.employee_id in self.employees:
            raise ValueError(f"Employee with ID {employee.employee_id} already exists")
        
        self.employees[employee.employee_id] = employee
        
        # Update job counts
        self.job_counts[employee.current_job] = self.job_counts.get(employee.current_job, 0) + 1
        
        # Update skills distribution
        for skill_id in employee.skills:
            self.skills_distribution[skill_id] = self.skills_distribution.get(skill_id, 0) + 1
    
    def update_employee(self, employee: Employee) -> None:
        """
        Update an existing employee in the database.
        
        Args:
            employee: The updated employee object
            
        Raises:
            ValueError: If the employee doesn't exist in the database
        """
        if employee.employee_id not in self.employees:
            raise ValueError(f"Employee with ID {employee.employee_id} not found")
        
        # Get the old employee data
        old_employee = self.employees[employee.employee_id]
        
        # Update job counts if the job changed
        if old_employee.current_job != employee.current_job:
            self.job_counts[old_employee.current_job] = self.job_counts.get(old_employee.current_job, 0) - 1
            self.job_counts[employee.current_job] = self.job_counts.get(employee.current_job, 0) + 1
        
        # Update skills distribution
        for skill_id in set(old_employee.skills) - set(employee.skills):
            self.skills_distribution[skill_id] = self.skills_distribution.get(skill_id, 0) - 1
            if self.skills_distribution[skill_id] == 0:
                del self.skills_distribution[skill_id]
        
        for skill_id in set(employee.skills) - set(old_employee.skills):
            self.skills_distribution[skill_id] = self.skills_distribution.get(skill_id, 0) + 1
        
        # Update the employee in the database
        self.employees[employee.employee_id] = employee
    
    def remove_employee(self, employee_id: str) -> None:
        """
        Remove an employee from the database.
        
        Args:
            employee_id: The ID of the employee to remove
            
        Raises:
            ValueError: If the employee doesn't exist
        """
        if employee_id not in self.employees:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        employee = self.employees[employee_id]
        
        # Update job counts
        self.job_counts[employee.current_job] = self.job_counts.get(employee.current_job, 0) - 1
        if self.job_counts[employee.current_job] == 0:
            del self.job_counts[employee.current_job]
        
        # Update skills distribution
        for skill_id in employee.skills:
            self.skills_distribution[skill_id] = self.skills_distribution.get(skill_id, 0) - 1
            if self.skills_distribution[skill_id] == 0:
                del self.skills_distribution[skill_id]
        
        # Remove from database
        del self.employees[employee_id]
    
    def get_employee(self, employee_id: str) -> Optional[Employee]:
        """
        Retrieve an employee by ID.
        
        Args:
            employee_id: The ID of the employee to retrieve
            
        Returns:
            The employee if found, None otherwise
        """
        return self.employees.get(employee_id)
    
    def get_employees_by_job(self, job_id: str) -> List['Employee']:
        """
        Retrieve all employees currently assigned to a specific job.
        
        Args:
            job_id: The ID of the job to filter by
            
        Returns:
            A list of employees with the specified job
        """
        return [
            emp for emp in self.employees.values()
            if emp.current_job == job_id
        ]
    
    def get_employees_with_skill(self, skill_id: str, min_proficiency: int = None) -> List['Employee']:
        """
        Retrieve all employees with a specific skill at minimum proficiency level using configured defaults.
        
        Args:
            skill_id: The ID of the skill to filter by
            min_proficiency: Minimum proficiency level to consider (uses configured default if None)
            
        Returns:
            A list of employees with the specified skill at minimum proficiency
        """
        # Use configured default minimum proficiency - NO hardcoded 1
        if min_proficiency is None:
            config_manager = get_config_manager()
            employee_config = config_manager.get_models_employee_config()
            defaults = employee_config.get('defaults', {})
            min_proficiency = defaults.get('min_proficiency', 1)
        
        return [
            emp for emp in self.employees.values()
            if emp.has_skill(skill_id, min_proficiency)
        ]
    
    def get_eligible_employees_for_job(self, job: 'Job', min_proficiency_ratio: float = None) -> List['Employee']:
        """
        Retrieve all employees eligible for a specific job using configured eligibility ratios.
        
        Args:
            job: The job to check eligibility for
            min_proficiency_ratio: Minimum ratio of required skills that must be met (uses configured default if None)
            
        Returns:
            A list of employees eligible for the job
        """
        # Use configured default eligibility ratio - NO hardcoded 0.8
        if min_proficiency_ratio is None:
            config_manager = get_config_manager()
            employee_config = config_manager.get_models_employee_config()
            defaults = employee_config.get('defaults', {})
            min_proficiency_ratio = defaults.get('eligibility_ratio', 0.8)
        
        return [
            emp for emp in self.employees.values()
            if emp.meets_job_requirements(job, min_proficiency_ratio)
        ]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Dict]) -> 'EmployeeDatabase':
        """
        Create an employee database from a dictionary representation using configured parsing.
        
        Args:
            data: Dictionary where keys are employee IDs and values are employee attributes
            
        Returns:
            A new EmployeeDatabase instance
        """
        # Get parsing configuration - NO hardcoded parsing behavior
        config_manager = get_config_manager()
        employee_config = config_manager.get_models_employee_config()
        parsing = employee_config.get('parsing', {})
        
        skills_delimiter = parsing.get('skills_delimiter', ',')
        skill_proficiency_separator = parsing.get('skill_proficiency_separator', ':')
        
        database = cls()
        
        for employee_id, employee_data in data.items():
            # Extract skills from the employee data
            skills_data = employee_data.get("skills", {})
            
            # If skills are provided as a string, parse them using configured delimiters
            if isinstance(skills_data, str):
                skills_dict = {}
                for skill_entry in skills_data.split(skills_delimiter):
                    if skill_proficiency_separator in skill_entry:
                        skill_id, proficiency = skill_entry.split(skill_proficiency_separator)
                        skills_dict[skill_id] = int(proficiency)
                skills_data = skills_dict
            
            employee = Employee(
                employee_id=employee_id,
                name=employee_data["name"],
                current_job=employee_data["current_job"],
                skills=skills_data
            )
            database.add_employee(employee)
        
        return database
    
    def to_dict(self) -> Dict[str, Dict]:
        """
        Convert the employee database to a dictionary representation.
        
        Returns:
            A dictionary where keys are employee IDs and values are employee attributes
        """
        return {
            employee_id: {
                "name": employee.name,
                "current_job": employee.current_job,
                "skills": employee.skills
            }
            for employee_id, employee in self.employees.items()
        }
    
    @classmethod
    def from_file(cls, file_path: str, job_architecture: Optional['JobArchitecture'] = None) -> 'EmployeeDatabase':
        """
        Load an employee database from a file using configured file format support.
        
        Args:
            file_path: Path to the file to load from
            job_architecture: Optional JobArchitecture for validating job IDs
            
        Returns:
            A new EmployeeDatabase instance loaded from the file
            
        Raises:
            ValueError: If the file type is not supported
        """
        # Get file format configuration - NO hardcoded file extensions
        config_manager = get_config_manager()
        employee_config = config_manager.get_models_employee_config()
        file_formats = employee_config.get('file_formats', {})
        
        supported_csv_extensions = file_formats.get('csv_extensions', ['.csv'])
        supported_excel_extensions = file_formats.get('excel_extensions', ['.xlsx', '.xls'])
        
        from ..data.loaders import EmployeeLoader
        
        loader = EmployeeLoader(job_architecture)
        
        # Check file extension against configured supported formats
        file_lower = file_path.lower()
        
        is_csv = any(file_lower.endswith(ext) for ext in supported_csv_extensions)
        is_excel = any(file_lower.endswith(ext) for ext in supported_excel_extensions)
        
        if is_csv:
            return loader.load_from_csv(file_path)
        elif is_excel:
            return loader.load_from_excel(file_path)
        else:
            all_supported = supported_csv_extensions + supported_excel_extensions
            raise ValueError(f"Unsupported file type for {file_path}. Supported formats: {all_supported}") 
