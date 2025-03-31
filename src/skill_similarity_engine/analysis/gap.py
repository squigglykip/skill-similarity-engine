#!/usr/bin/env python3
"""
Gap analysis module for identifying skill gaps between employees and job requirements.

This module provides functionality for analyzing skill gaps between employees and job
requirements, calculating development effort required to close those gaps, and supporting
career path planning.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger("gap_analysis")

import numpy as np
import pandas as pd

from ..config.settings import get_config
from ..models.employees import Employee, EmployeeDatabase
from ..models.jobs import Job, JobArchitecture
from ..models.skills import Skill, SkillTaxonomy
from ..config.settings import GapAnalysisConfig


class SkillGapType(Enum):
    """Types of skill gaps in the analysis."""
    MISSING = "Missing"  # Skill required by job but missing or insufficient in employee
    EXCESS = "Excess"    # Skill present in employee but not required by job
    MATCH = "Match"      # Skill present in both with sufficient proficiency


@dataclass
class SkillGap:
    """
    Represents a gap between employee's skill level and job requirement.
    
    Attributes:
        skill_id: ID of the skill
        skill_name: Name of the skill
        job_proficiency: Required proficiency level for the job
        employee_proficiency: Current proficiency level of the employee
        category_id: ID of the skill category
        category_name: Name of the skill category
        proficiency_gap: Numeric gap between required and current proficiency
        development_effort: Calculated effort required to close the gap
        gap_type: Type of skill gap (missing, excess, or match)
    """
    skill_id: str
    skill_name: str
    job_proficiency: int  
    employee_proficiency: int = 0
    proficiency_gap: float = 0.0
    development_effort: float = 0.0
    category_id: str = ""
    category_name: str = ""
    gap_type: SkillGapType = SkillGapType.MISSING

    def __post_init__(self):
        """Calculate the proficiency gap after initialization."""
        self.proficiency_gap = max(0, self.job_proficiency - self.employee_proficiency)


@dataclass
class JobSkillGapResult:
    """
    Results of a job skill gap analysis.
    
    Attributes:
        employee_id: ID of the employee
        employee_name: Name of the employee
        job_id: ID of the job
        job_title: Title of the job
        missing_skills: Skills the employee is missing completely or below required level
        matching_skills: Skills that match required levels
        excess_skills: Skills the employee has but are not required for the job
        skill_match_percentage: Percentage of required skills that are matched
        total_development_effort: Total effort required to close all gaps
        reskilling_difficulty: Relative difficulty of reskilling on a scale of 1-5
    """
    employee_id: str
    employee_name: str
    job_id: str
    job_title: str
    missing_skills: List[SkillGap] = field(default_factory=list)
    matching_skills: List[SkillGap] = field(default_factory=list)
    excess_skills: List[SkillGap] = field(default_factory=list)
    skill_match_percentage: float = 0.0
    total_development_effort: float = 0.0
    reskilling_difficulty: float = 0.0
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the gap analysis result to a pandas DataFrame.
        
        Returns:
            DataFrame with all skills (missing, excess, matching) and their details
        """
        # Create a list of dictionaries to convert to DataFrame
        data = []
        
        # Add missing skills
        for gap in self.missing_skills:
            data.append({
                'skill_id': gap.skill_id,
                'skill_name': gap.skill_name,
                'category_id': gap.category_id,
                'category_name': gap.category_name,
                'job_proficiency': gap.job_proficiency,
                'employee_proficiency': gap.employee_proficiency,
                'proficiency_gap': gap.proficiency_gap,
                'development_effort': gap.development_effort,
                'gap_type': 'Missing'
            })
        
        # Add excess skills
        for gap in self.excess_skills:
            data.append({
                'skill_id': gap.skill_id,
                'skill_name': gap.skill_name,
                'category_id': gap.category_id,
                'category_name': gap.category_name,
                'job_proficiency': gap.job_proficiency,
                'employee_proficiency': gap.employee_proficiency,
                'proficiency_gap': 0,
                'development_effort': 0,
                'gap_type': 'Excess'
            })
        
        # Add matching skills
        for gap in self.matching_skills:
            data.append({
                'skill_id': gap.skill_id,
                'skill_name': gap.skill_name,
                'category_id': gap.category_id,
                'category_name': gap.category_name,
                'job_proficiency': gap.job_proficiency,
                'employee_proficiency': gap.employee_proficiency,
                'proficiency_gap': 0,
                'development_effort': 0,
                'gap_type': 'Match'
            })
        
        # Create DataFrame
        return pd.DataFrame(data)
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """
        Convert the gap analysis result to a summary dictionary.
        
        Returns:
            Dictionary with summary information about the gap analysis
        """
        return {
            'employee_id': self.employee_id,
            'employee_name': self.employee_name,
            'job_id': self.job_id,
            'job_title': self.job_title,
            'missing_skills_count': len(self.missing_skills),
            'matching_skills_count': len(self.matching_skills),
            'excess_skills_count': len(self.excess_skills),
            'total_skills_analyzed': len(self.missing_skills) + len(self.matching_skills) + len(self.excess_skills),
            'skill_match_percentage': self.skill_match_percentage,
            'total_development_effort': self.total_development_effort,
            'reskilling_difficulty': self.reskilling_difficulty
        }


class SkillGapAnalyzer:
    """
    Analyzer for identifying skill gaps between employees and job roles.
    
    Attributes:
        skill_taxonomy: The skill taxonomy containing all skills
        job_architecture: The job architecture containing all jobs
        employee_database: The employee database containing all employees
    """
    
    def __init__(
        self,
        skill_taxonomy: Optional[SkillTaxonomy] = None,
        job_architecture: Optional[JobArchitecture] = None,
        employee_database: Optional[EmployeeDatabase] = None
    ):
        """
        Initialize the gap analyzer with supporting data structures.
        
        Args:
            skill_taxonomy: The skill taxonomy containing all skills
            job_architecture: The job architecture containing all jobs
            employee_database: The employee database containing all employees
        """
        self.skill_taxonomy = skill_taxonomy
        self.job_architecture = job_architecture
        self.employee_database = employee_database
        
        # Get configuration
        config = get_config()
        self.config = config.gap_analysis
        
        # Access configuration values
        self.min_proficiency_ratio = self.config.min_proficiency_ratio
        self.category_weights = self.config.category_weights
    
    def analyze_employee_job_gap(self, employee_id: str, job_id: str) -> JobSkillGapResult:
        """
        Analyze the skill gap between an employee and a job.
        
        Args:
            employee_id: ID of the employee
            job_id: ID of the job
            
        Returns:
            A JobSkillGapResult containing detailed gap information
        """
        if not self.job_architecture or not self.employee_database:
            raise ValueError("Job architecture and employee database must be set before analysis")
            
        # Get employee and job
        employee = self.employee_database.get_employee(employee_id)
        job = self.job_architecture.get_job(job_id)
        
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} not found")
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")
            
        # Initialize result
        result = JobSkillGapResult(
            employee_id=employee.employee_id,
            employee_name=employee.name,
            job_id=job.job_id,
            job_title=job.title
        )
        
        # Analyze each required skill
        total_required_skills = len(job.skills)
        matched_skills = 0
        
        for skill_id, required_proficiency in job.skills.items():
            # Get employee's proficiency
            employee_proficiency = employee.skills.get(skill_id, 0)
            
            # Get skill details
            skill = self.skill_taxonomy.get_skill(skill_id)
            if not skill:
                logger.warning(f"Skill {skill_id} not found in taxonomy")
                continue
                
            category = self.skill_taxonomy.get_category(skill.category_id)
            category_name = category.name if category else "Unknown"
            
            # Create skill gap object
            gap = SkillGap(
                skill_id=skill_id,
                skill_name=skill.name,
                job_proficiency=required_proficiency,
                employee_proficiency=employee_proficiency,
                category_id=skill.category_id,
                category_name=category_name,
                gap_type=SkillGapType.MISSING if employee_proficiency < required_proficiency * self.min_proficiency_ratio else SkillGapType.MATCH
            )
            
            # Calculate if the skill matches or is missing
            # A skill matches if employee's proficiency is at least min_proficiency_ratio of required
            if employee_proficiency >= required_proficiency * self.min_proficiency_ratio:
                result.matching_skills.append(gap)
                matched_skills += 1
            else:
                # Calculate development effort based on gap, skill difficulty and category weight
                category_weight = self.category_weights.get(category_name, 1.0)
                difficulty_factor = getattr(skill, 'difficulty', 1.0)
                gap.development_effort = gap.proficiency_gap * difficulty_factor * category_weight
                
                result.missing_skills.append(gap)
                result.total_development_effort += gap.development_effort
        
        # Identify excess skills (skills employee has but job doesn't require)
        for skill_id, proficiency in employee.skills.items():
            if skill_id not in job.skills:
                skill = self.skill_taxonomy.get_skill(skill_id)
                if not skill:
                    continue
                    
                category = self.skill_taxonomy.get_category(skill.category_id)
                category_name = category.name if category else "Unknown"
                
                excess_gap = SkillGap(
                    skill_id=skill_id,
                    skill_name=skill.name,
                    job_proficiency=0,
                    employee_proficiency=proficiency,
                    category_id=skill.category_id,
                    category_name=category_name,
                    gap_type=SkillGapType.EXCESS
                )
                result.excess_skills.append(excess_gap)
        
        # Calculate skill match percentage
        if total_required_skills > 0:
            result.skill_match_percentage = (matched_skills / total_required_skills) * 100
            
        # Calculate reskilling difficulty (normalized to 1-5 scale)
        # If total_development_effort is high, reskilling is more difficult
        if result.total_development_effort > 0:
            # Normalize to 1-5 scale based on total effort
            # This is a simple linear transformation that can be refined
            max_expected_effort = 100  # This could be a configuration parameter
            result.reskilling_difficulty = min(5, 1 + (result.total_development_effort / max_expected_effort) * 4)
        
        return result

    def calculate_employee_skill_gaps(self, employee_id: str) -> Dict[str, float]:
        """
        Calculate skill gaps for an employee in their current job.
        
        Args:
            employee_id: ID of the employee
            
        Returns:
            Dictionary mapping skill_id to gap size for all gaps above threshold
        """
        if not self.job_architecture or not self.employee_database:
            raise ValueError("Job architecture and employee database must be set before analysis")
            
        # Get employee and their current job
        employee = self.employee_database.get_employee(employee_id)
        if not employee or not employee.current_job:
            raise ValueError(f"Employee {employee_id} not found or has no current job")
            
        job = self.job_architecture.get_job(employee.current_job)
        if not job:
            raise ValueError(f"Job {employee.current_job} not found")
        
        # Calculate gaps
        gaps = {}
        for skill_id, required_proficiency in job.skills.items():
            # Get employee's proficiency
            employee_proficiency = employee.skills.get(skill_id, 0)
            
            # Calculate normalized gap
            proficiency_gap = required_proficiency - employee_proficiency
            
            # Only include significant gaps above threshold
            if proficiency_gap > required_proficiency * self.config.min_gap_threshold:
                gaps[skill_id] = proficiency_gap
                
        return gaps
        
    def calculate_role_transition_gaps(self, employee_id: str, target_job_id: str) -> Dict[str, float]:
        """
        Calculate skill gaps for an employee transitioning to a different job.
        
        Args:
            employee_id: ID of the employee
            target_job_id: ID of the target job
            
        Returns:
            Dictionary mapping skill_id to gap size for all gaps above threshold
        """
        if not self.job_architecture or not self.employee_database:
            raise ValueError("Job architecture and employee database must be set before analysis")
            
        # Get employee
        employee = self.employee_database.get_employee(employee_id)
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")
            
        # Get target job
        target_job = self.job_architecture.get_job(target_job_id)
        if not target_job:
            raise ValueError(f"Job {target_job_id} not found")
        
        # Calculate gaps
        gaps = {}
        for skill_id, required_proficiency in target_job.skills.items():
            # Get employee's proficiency
            employee_proficiency = employee.skills.get(skill_id, 0)
            
            # Calculate normalized gap
            proficiency_gap = required_proficiency - employee_proficiency
            
            # Only include significant gaps above threshold
            if proficiency_gap > required_proficiency * self.config.min_gap_threshold:
                gaps[skill_id] = proficiency_gap
                
        return gaps
    
    def calculate_development_effort(self, employee_id: str) -> float:
        """
        Calculate the total development effort required for an employee to close all gaps.
        
        Args:
            employee_id: ID of the employee
            
        Returns:
            Total development effort as a float
        """
        if not self.job_architecture or not self.employee_database:
            raise ValueError("Job architecture and employee database must be set before analysis")
            
        # Get employee and their current job
        employee = self.employee_database.get_employee(employee_id)
        if not employee or not employee.current_job:
            raise ValueError(f"Employee {employee_id} not found or has no current job")
            
        job = self.job_architecture.get_job(employee.current_job)
        if not job:
            raise ValueError(f"Job {employee.current_job} not found")
        
        # Get gaps
        gaps = self.calculate_employee_skill_gaps(employee_id)
        
        # Calculate total effort
        total_effort = 0.0
        for skill_id, gap_size in gaps.items():
            skill = self.skill_taxonomy.get_skill(skill_id)
            if not skill:
                continue
                
            category = self.skill_taxonomy.get_category(skill.category_id)
            category_name = category.name if category else "Unknown"
            
            # Apply difficulty factor and category weight
            category_weight = self.category_weights.get(category_name, 1.0)
            difficulty_factor = skill.difficulty
            
            # Add to total effort
            total_effort += gap_size * difficulty_factor * category_weight
            
        return total_effort
    
    def calculate_role_transition_effort(self, employee_id: str, target_job_id: str) -> float:
        """
        Calculate the development effort required for an employee to transition to a different job.
        
        Args:
            employee_id: ID of the employee
            target_job_id: ID of the target job
            
        Returns:
            Total transition effort as a float
        """
        if not self.job_architecture or not self.employee_database:
            raise ValueError("Job architecture and employee database must be set before analysis")
            
        # Get employee
        employee = self.employee_database.get_employee(employee_id)
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")
            
        # Get target job
        target_job = self.job_architecture.get_job(target_job_id)
        if not target_job:
            raise ValueError(f"Job {target_job_id} not found")
        
        # Get gaps
        gaps = self.calculate_role_transition_gaps(employee_id, target_job_id)
        
        # Calculate total effort
        total_effort = 0.0
        for skill_id, gap_size in gaps.items():
            skill = self.skill_taxonomy.get_skill(skill_id)
            if not skill:
                continue
                
            category = self.skill_taxonomy.get_category(skill.category_id)
            category_name = category.name if category else "Unknown"
            
            # Apply difficulty factor and category weight
            category_weight = self.category_weights.get(category_name, 1.0)
            difficulty_factor = skill.difficulty
            
            # Add to total effort
            total_effort += gap_size * difficulty_factor * category_weight
            
        return total_effort

    def generate_job_transition_report(self, employee_id: str, top_n: int = 5) -> pd.DataFrame:
        """
        Generate a report of potential job transitions for an employee.
        
        Args:
            employee_id: ID of the employee
            top_n: Number of top matches to include
            
        Returns:
            DataFrame with job transition analysis
        """
        if not self.job_architecture or not self.employee_database:
            raise ValueError("Job architecture and employee database must be set before analysis")
            
        # Get employee
        employee = self.employee_database.get_employee(employee_id)
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")
        
        # Get all jobs
        results = []
        for job_id, job in self.job_architecture.jobs.items():
            # Skip employee's current job if they have one
            if employee.current_job and job_id == employee.current_job:
                continue
                
            # Analyze gap
            result = self.analyze_employee_job_gap(employee_id=employee_id, job_id=job_id)
            
            # Add to results
            results.append({
                "job_id": job_id,
                "job_title": job.title,
                "department": job.department,
                "skill_match_percentage": result.skill_match_percentage,
                "total_development_effort": result.total_development_effort,
                "reskilling_difficulty": result.reskilling_difficulty,
                "missing_skills_count": len(result.missing_skills),
                "excess_skills_count": len(result.excess_skills),
                "matching_skills_count": len(result.matching_skills)
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Sort by skill match percentage (descending)
        df = df.sort_values("skill_match_percentage", ascending=False)
        
        # Get top N results
        if top_n > 0:
            df = df.head(top_n)
            
        return df


class TeamGapAnalyzer:
    """
    Analyzer for identifying skill gaps at team or organization level.
    
    Attributes:
        skill_gap_analyzer: The skill gap analyzer for individual gap analysis
        skill_taxonomy: The skill taxonomy containing all skills
        job_architecture: The job architecture containing all jobs
        employee_database: The employee database containing all employees
    """
    
    def __init__(
        self,
        skill_taxonomy: SkillTaxonomy,
        job_architecture: JobArchitecture,
        employee_database: EmployeeDatabase
    ):
        """
        Initialize the team gap analyzer.
        
        Args:
            skill_taxonomy: The skill taxonomy containing all skills
            job_architecture: The job architecture containing all jobs
            employee_database: The employee database containing all employees
        """
        self.skill_taxonomy = skill_taxonomy
        self.job_architecture = job_architecture
        self.employee_database = employee_database
        self.skill_gap_analyzer = SkillGapAnalyzer(
            skill_taxonomy,
            job_architecture,
            employee_database
        )
        # Get team analysis configuration
        team_config = get_config().team_analysis
        self.fully_covered_weight = team_config.fully_covered_weight
        self.partially_covered_weight = team_config.partially_covered_weight
    
    def analyze_team_skill_coverage(
        self,
        employee_ids: List[str],
        job_id: str
    ) -> Dict[str, Union[str, float, Dict]]:
        """
        Analyze how well a team's collective skills cover a job's requirements.
        
        Args:
            employee_ids: IDs of the employees in the team
            job_id: ID of the job to analyze coverage for
            
        Returns:
            Dictionary with coverage analysis results
            
        Raises:
            ValueError: If any employee ID or the job ID is not found
        """
        if job_id not in self.job_architecture.jobs:
            raise ValueError(f"Job with ID {job_id} not found")
        
        job = self.job_architecture.jobs[job_id]
        
        # Validate employee IDs
        valid_employee_ids = []
        for employee_id in employee_ids:
            if employee_id in self.employee_database.employees:
                valid_employee_ids.append(employee_id)
        
        if not valid_employee_ids:
            raise ValueError("No valid employee IDs provided")
        
        # Get maximum proficiency for each skill across the team
        team_skills = {}
        for employee_id in valid_employee_ids:
            employee = self.employee_database.employees[employee_id]
            for skill_id, proficiency in employee.skills.items():
                team_skills[skill_id] = max(team_skills.get(skill_id, 0), proficiency)
        
        # Check coverage for each required skill
        covered_skills = []
        partially_covered_skills = []
        uncovered_skills = []
        
        for skill_id, required_proficiency in job.skills.items():
            if required_proficiency == 0:
                continue
            
            skill_name = self.skill_taxonomy.skills[skill_id].name if skill_id in self.skill_taxonomy.skills else "Unknown Skill"
            team_proficiency = team_skills.get(skill_id, 0)
            
            coverage = {
                "skill_id": skill_id,
                "skill_name": skill_name,
                "required_proficiency": required_proficiency,
                "team_proficiency": team_proficiency,
                "gap": required_proficiency - team_proficiency
            }
            
            if team_proficiency >= required_proficiency:
                covered_skills.append(coverage)
            elif team_proficiency > 0:
                partially_covered_skills.append(coverage)
            else:
                uncovered_skills.append(coverage)
        
        # Calculate coverage percentages
        total_required_skills = len(job.skills)
        if total_required_skills > 0:
            fully_covered_percentage = (len(covered_skills) / total_required_skills) * 100
            partially_covered_percentage = (len(partially_covered_skills) / total_required_skills) * 100
            uncovered_percentage = (len(uncovered_skills) / total_required_skills) * 100
        else:
            fully_covered_percentage = 100.0
            partially_covered_percentage = 0.0
            uncovered_percentage = 0.0
        
        # Create coverage analysis
        coverage_analysis = {
            "job_id": job_id,
            "job_title": job.title,
            "team_size": len(valid_employee_ids),
            "fully_covered_skills": covered_skills,
            "partially_covered_skills": partially_covered_skills,
            "uncovered_skills": uncovered_skills,
            "fully_covered_percentage": fully_covered_percentage,
            "partially_covered_percentage": partially_covered_percentage,
            "uncovered_percentage": uncovered_percentage,
            "overall_coverage_score": fully_covered_percentage + (partially_covered_percentage * 0.5)
        }
        
        return coverage_analysis
    
    def identify_critical_skill_gaps(
        self,
        department: Optional[str] = None,
        min_gap_threshold: Optional[float] = None,
        max_skills: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Identify critical skill gaps across a department or the entire organization.
        
        Args:
            department: Department to analyze (all departments if None)
            min_gap_threshold: Minimum gap threshold to consider critical (uses config value if None)
            max_skills: Maximum number of skills to include in results (uses config value if None)
            
        Returns:
            DataFrame with critical skill gaps
        """
        # Use configuration values if not provided
        config = get_config()
        if min_gap_threshold is None:
            min_gap_threshold = config.gap_analysis.min_gap_threshold
        if max_skills is None:
            max_skills = config.workforce.max_skills_in_report
        
        # Get jobs to analyze
        if department:
            jobs = self.job_architecture.get_jobs_by_department(department)
        else:
            jobs = list(self.job_architecture.jobs.values())
        
        # Get employees to analyze
        if department:
            employees = [
                employee for employee in self.employee_database.employees.values()
                if self.job_architecture.jobs.get(employee.current_job) and
                self.job_architecture.jobs[employee.current_job].department == department
            ]
        else:
            employees = list(self.employee_database.employees.values())
        
        # Collect all skills required by jobs
        required_skills = {}
        for job in jobs:
            for skill_id, proficiency in job.skills.items():
                if proficiency > 0:
                    if skill_id not in required_skills:
                        required_skills[skill_id] = []
                    required_skills[skill_id].append((job.job_id, job.title, proficiency))
        
        # Calculate average proficiency for each employee skill
        available_skills = {}
        for employee in employees:
            for skill_id, proficiency in employee.skills.items():
                if skill_id not in available_skills:
                    available_skills[skill_id] = []
                available_skills[skill_id].append(proficiency)
        
        # Calculate average available proficiency
        avg_available_proficiency = {}
        for skill_id, proficiencies in available_skills.items():
            avg_available_proficiency[skill_id] = sum(proficiencies) / len(proficiencies)
        
        # Identify critical gaps
        critical_gaps = []
        
        for skill_id, job_requirements in required_skills.items():
            # Calculate average required proficiency
            avg_required = sum(req[2] for req in job_requirements) / len(job_requirements)
            
            # Get average available proficiency (default to 0 if not available)
            avg_available = avg_available_proficiency.get(skill_id, 0)
            
            # Calculate gap
            gap = avg_required - avg_available
            
            if gap >= min_gap_threshold:
                # Get skill name
                skill_name = self.skill_taxonomy.skills[skill_id].name if skill_id in self.skill_taxonomy.skills else "Unknown Skill"
                
                # Count how many jobs require this skill
                job_count = len(job_requirements)
                
                # Count how many employees have this skill
                employee_count = len(available_skills.get(skill_id, []))
                
                # Calculate coverage (percentage of employees with the skill)
                employee_coverage = (employee_count / len(employees)) * 100 if employees else 0
                
                critical_gaps.append({
                    "skill_id": skill_id,
                    "skill_name": skill_name,
                    "avg_required_proficiency": avg_required,
                    "avg_available_proficiency": avg_available,
                    "proficiency_gap": gap,
                    "job_count": job_count,
                    "employee_count": employee_count,
                    "employee_coverage_percentage": employee_coverage,
                    "criticality": gap * job_count  # Higher gap and more jobs = more critical
                })
        
        # Convert to DataFrame
        df = pd.DataFrame(critical_gaps)
        
        # Sort by criticality (descending)
        if not df.empty:
            df = df.sort_values("criticality", ascending=False)
        
        return df

# Create an alias for backward compatibility with tests
GapAnalysisResult = JobSkillGapResult
