"""
Gap analysis for identifying skill gaps between employees and target roles.

This module provides functionality for identifying skill gaps, calculating
development effort, and generating reskilling pathways.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

from ..config.settings import get_config
from ..models.employees import Employee, EmployeeDatabase
from ..models.jobs import Job, JobArchitecture
from ..models.skills import Skill, SkillTaxonomy


class SkillGapType(Enum):
    """Types of skill gaps in the analysis."""
    MISSING = "Missing"  # Skill required by job but missing or insufficient in employee
    EXCESS = "Excess"    # Skill present in employee but not required by job
    MATCH = "Match"      # Skill present in both with sufficient proficiency


@dataclass
class SkillGap:
    """
    Represents a gap in skill proficiency between an employee and a job.
    
    Attributes:
        skill_id: ID of the skill
        skill_name: Name of the skill
        employee_proficiency: Employee's proficiency level (0-5)
        job_proficiency: Job's required proficiency level (0-5)
        gap_type: Type of gap (missing, excess, or match)
        proficiency_gap: Difference in proficiency (job - employee)
        development_effort: Calculated effort to close the gap
    """
    skill_id: str
    skill_name: str
    employee_proficiency: int
    job_proficiency: int
    gap_type: SkillGapType
    proficiency_gap: int = 0
    development_effort: float = 0.0


@dataclass
class GapAnalysisResult:
    """
    Results of a gap analysis between an employee and a job.
    
    Attributes:
        employee_id: ID of the employee
        employee_name: Name of the employee
        job_id: ID of the job
        job_title: Title of the job
        missing_skills: List of skills required by job but missing/insufficient in employee
        excess_skills: List of skills present in employee but not required by job
        matching_skills: List of skills present in both with sufficient proficiency
        total_development_effort: Total calculated effort to close all gaps
        skill_match_percentage: Percentage of job skills that match employee skills
        reskilling_difficulty: Calculated difficulty rating for reskilling (1-5)
    """
    employee_id: str
    employee_name: str
    job_id: str
    job_title: str
    missing_skills: List[SkillGap] = field(default_factory=list)
    excess_skills: List[SkillGap] = field(default_factory=list)
    matching_skills: List[SkillGap] = field(default_factory=list)
    total_development_effort: float = 0.0
    skill_match_percentage: float = 0.0
    reskilling_difficulty: float = 0.0
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the gap analysis results to a DataFrame.
        
        Returns:
            DataFrame with all skill gaps
        """
        all_gaps = []
        
        # Add missing skills
        for gap in self.missing_skills:
            all_gaps.append({
                "employee_id": self.employee_id,
                "employee_name": self.employee_name,
                "job_id": self.job_id,
                "job_title": self.job_title,
                "skill_id": gap.skill_id,
                "skill_name": gap.skill_name,
                "employee_proficiency": gap.employee_proficiency,
                "job_proficiency": gap.job_proficiency,
                "gap_type": gap.gap_type.value,
                "proficiency_gap": gap.proficiency_gap,
                "development_effort": gap.development_effort
            })
        
        # Add excess skills
        for gap in self.excess_skills:
            all_gaps.append({
                "employee_id": self.employee_id,
                "employee_name": self.employee_name,
                "job_id": self.job_id,
                "job_title": self.job_title,
                "skill_id": gap.skill_id,
                "skill_name": gap.skill_name,
                "employee_proficiency": gap.employee_proficiency,
                "job_proficiency": gap.job_proficiency,
                "gap_type": gap.gap_type.value,
                "proficiency_gap": gap.proficiency_gap,
                "development_effort": gap.development_effort
            })
        
        # Add matching skills
        for gap in self.matching_skills:
            all_gaps.append({
                "employee_id": self.employee_id,
                "employee_name": self.employee_name,
                "job_id": self.job_id,
                "job_title": self.job_title,
                "skill_id": gap.skill_id,
                "skill_name": gap.skill_name,
                "employee_proficiency": gap.employee_proficiency,
                "job_proficiency": gap.job_proficiency,
                "gap_type": gap.gap_type.value,
                "proficiency_gap": gap.proficiency_gap,
                "development_effort": gap.development_effort
            })
        
        return pd.DataFrame(all_gaps)
    
    def to_summary_dict(self) -> Dict[str, Union[str, float, int]]:
        """
        Create a summary dictionary of the gap analysis results.
        
        Returns:
            Dictionary with summary metrics
        """
        return {
            "employee_id": self.employee_id,
            "employee_name": self.employee_name,
            "job_id": self.job_id,
            "job_title": self.job_title,
            "missing_skills_count": len(self.missing_skills),
            "excess_skills_count": len(self.excess_skills),
            "matching_skills_count": len(self.matching_skills),
            "total_development_effort": self.total_development_effort,
            "skill_match_percentage": self.skill_match_percentage,
            "reskilling_difficulty": self.reskilling_difficulty
        }


class SkillGapAnalyzer:
    """
    Analyzer for identifying skill gaps between employees and jobs.
    
    Attributes:
        skill_taxonomy: The skill taxonomy containing all skills
        job_architecture: The job architecture containing all jobs
        employee_database: The employee database containing all employees
        min_proficiency_ratio: Minimum ratio of employee's proficiency to required proficiency
        category_weights: Weights for different skill categories in development effort
    """
    
    def __init__(
        self,
        skill_taxonomy: SkillTaxonomy,
        job_architecture: JobArchitecture,
        employee_database: Optional[EmployeeDatabase] = None,
        min_proficiency_ratio: Optional[float] = None,
        category_weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize the skill gap analyzer.
        
        Args:
            skill_taxonomy: The skill taxonomy containing all skills
            job_architecture: The job architecture containing all jobs
            employee_database: The employee database containing all employees
            min_proficiency_ratio: Minimum ratio of employee's proficiency to required proficiency
            category_weights: Weights for different skill categories in development effort
        """
        self.skill_taxonomy = skill_taxonomy
        self.job_architecture = job_architecture
        self.employee_database = employee_database
        
        config = get_config().gap_analysis
        
        # Use configuration values if not provided
        self.min_proficiency_ratio = min_proficiency_ratio if min_proficiency_ratio is not None else config.min_proficiency_ratio
        self.category_weights = category_weights if category_weights is not None else config.category_weights
        self.skill_difficulty_factor = config.skill_difficulty_factor
    
    def analyze_employee_job_gap(
        self,
        employee_id: str,
        job_id: str
    ) -> GapAnalysisResult:
        """
        Analyze the skill gap between an employee and a job.
        
        Args:
            employee_id: ID of the employee
            job_id: ID of the job
            
        Returns:
            Gap analysis results
            
        Raises:
            ValueError: If the employee ID or job ID is not found
        """
        if not self.employee_database:
            raise ValueError("Employee database not set")
        
        if employee_id not in self.employee_database.employees:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        if job_id not in self.job_architecture.jobs:
            raise ValueError(f"Job with ID {job_id} not found")
        
        employee = self.employee_database.employees[employee_id]
        job = self.job_architecture.jobs[job_id]
        
        # Initialize result
        result = GapAnalysisResult(
            employee_id=employee_id,
            employee_name=employee.name,
            job_id=job_id,
            job_title=job.title
        )
        
        # Identify missing, excess, and matching skills
        self._identify_missing_skills(employee, job, result)
        self._identify_excess_skills(employee, job, result)
        self._identify_matching_skills(employee, job, result)
        
        # Calculate development effort
        total_effort = sum(gap.development_effort for gap in result.missing_skills)
        result.total_development_effort = total_effort
        
        # Calculate skill match percentage
        required_skills_count = len(job.skills)
        if required_skills_count > 0:
            result.skill_match_percentage = (len(result.matching_skills) / required_skills_count) * 100
        
        # Calculate reskilling difficulty (1-5 scale)
        max_possible_effort = 5 * required_skills_count  # Maximum possible effort if all skills were missing at max proficiency
        if max_possible_effort > 0:
            relative_effort = min(total_effort / max_possible_effort, 1.0)
            result.reskilling_difficulty = 1 + relative_effort * 4  # Scale to 1-5
        
        return result
    
    def _identify_missing_skills(
        self,
        employee: Employee,
        job: Job,
        result: GapAnalysisResult
    ) -> None:
        """
        Identify skills required by the job but missing or insufficient in the employee.
        
        Args:
            employee: The employee
            job: The job
            result: Gap analysis results to update
        """
        for skill_id, required_proficiency in job.skills.items():
            if required_proficiency == 0:
                continue  # Skip skills not required by the job
            
            employee_proficiency = employee.skills.get(skill_id, 0)
            
            # Check if employee has sufficient proficiency
            if employee_proficiency < required_proficiency * self.min_proficiency_ratio:
                # Get skill name
                skill_name = self.skill_taxonomy.skills[skill_id].name if skill_id in self.skill_taxonomy.skills else "Unknown Skill"
                
                # Calculate proficiency gap
                proficiency_gap = required_proficiency - employee_proficiency
                
                # Calculate development effort
                development_effort = self._calculate_development_effort(skill_id, proficiency_gap)
                
                # Create skill gap
                skill_gap = SkillGap(
                    skill_id=skill_id,
                    skill_name=skill_name,
                    employee_proficiency=employee_proficiency,
                    job_proficiency=required_proficiency,
                    gap_type=SkillGapType.MISSING,
                    proficiency_gap=proficiency_gap,
                    development_effort=development_effort
                )
                
                result.missing_skills.append(skill_gap)
    
    def _identify_excess_skills(
        self,
        employee: Employee,
        job: Job,
        result: GapAnalysisResult
    ) -> None:
        """
        Identify skills present in the employee but not required by the job.
        
        Args:
            employee: The employee
            job: The job
            result: Gap analysis results to update
        """
        for skill_id, employee_proficiency in employee.skills.items():
            if employee_proficiency == 0:
                continue  # Skip skills not possessed by the employee
            
            job_proficiency = job.skills.get(skill_id, 0)
            
            # Check if skill is not required by the job
            if job_proficiency == 0:
                # Get skill name
                skill_name = self.skill_taxonomy.skills[skill_id].name if skill_id in self.skill_taxonomy.skills else "Unknown Skill"
                
                # Create skill gap (negative proficiency gap indicates excess)
                skill_gap = SkillGap(
                    skill_id=skill_id,
                    skill_name=skill_name,
                    employee_proficiency=employee_proficiency,
                    job_proficiency=job_proficiency,
                    gap_type=SkillGapType.EXCESS,
                    proficiency_gap=-employee_proficiency,  # Negative to indicate excess
                    development_effort=0.0  # No development effort for excess skills
                )
                
                result.excess_skills.append(skill_gap)
    
    def _identify_matching_skills(
        self,
        employee: Employee,
        job: Job,
        result: GapAnalysisResult
    ) -> None:
        """
        Identify skills present in both the employee and job with sufficient proficiency.
        
        Args:
            employee: The employee
            job: The job
            result: Gap analysis results to update
        """
        for skill_id, required_proficiency in job.skills.items():
            if required_proficiency == 0:
                continue  # Skip skills not required by the job
            
            employee_proficiency = employee.skills.get(skill_id, 0)
            
            # Check if employee has sufficient proficiency
            if employee_proficiency >= required_proficiency * self.min_proficiency_ratio:
                # Get skill name
                skill_name = self.skill_taxonomy.skills[skill_id].name if skill_id in self.skill_taxonomy.skills else "Unknown Skill"
                
                # Calculate proficiency gap (might be small positive or negative)
                proficiency_gap = required_proficiency - employee_proficiency
                
                # Create skill gap
                skill_gap = SkillGap(
                    skill_id=skill_id,
                    skill_name=skill_name,
                    employee_proficiency=employee_proficiency,
                    job_proficiency=required_proficiency,
                    gap_type=SkillGapType.MATCH,
                    proficiency_gap=proficiency_gap,
                    development_effort=0.0  # No development effort for matching skills
                )
                
                result.matching_skills.append(skill_gap)
    
    def _calculate_development_effort(
        self,
        skill_id: str,
        proficiency_gap: int
    ) -> float:
        """
        Calculate the development effort required to close a skill gap.
        
        The calculation takes into account:
        - The proficiency gap
        - The skill difficulty (if available)
        - The skill category weight
        
        Args:
            skill_id: ID of the skill
            proficiency_gap: Difference in proficiency to close
            
        Returns:
            Development effort score
        """
        if proficiency_gap <= 0:
            return 0.0
        
        # Base effort is proportional to the proficiency gap
        effort = float(proficiency_gap)
        
        # Apply skill difficulty factor if available
        skill = self.skill_taxonomy.skills.get(skill_id)
        if skill and hasattr(skill, "difficulty") and skill.difficulty is not None:
            difficulty_multiplier = 0.5 + (skill.difficulty / 5.0) * self.skill_difficulty_factor
            effort *= difficulty_multiplier
        
        # Apply category weight if available
        if skill and skill.category_id:
            category = self.skill_taxonomy.categories.get(skill.category_id)
            if category:
                category_weight = self.category_weights.get(category.name, 1.0)
                effort *= category_weight
        
        return effort
    
    def generate_job_transition_report(
        self,
        employee_id: str,
        job_ids: Optional[List[str]] = None,
        top_n: int = 5
    ) -> pd.DataFrame:
        """
        Generate a report of job transition opportunities for an employee.
        
        Args:
            employee_id: ID of the employee
            job_ids: List of job IDs to analyze (all jobs if None)
            top_n: Number of top job opportunities to return
            
        Returns:
            DataFrame with job transition opportunities
            
        Raises:
            ValueError: If the employee ID is not found
        """
        if not self.employee_database:
            raise ValueError("Employee database not set")
        
        if employee_id not in self.employee_database.employees:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        # Default to all jobs if not specified
        if job_ids is None:
            job_ids = list(self.job_architecture.jobs.keys())
        
        # Analyze gap for each job
        results = []
        for job_id in job_ids:
            if job_id not in self.job_architecture.jobs:
                continue
            
            try:
                result = self.analyze_employee_job_gap(employee_id, job_id)
                results.append(result.to_summary_dict())
            except ValueError:
                continue
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Sort by skill match percentage (descending) and development effort (ascending)
        df = df.sort_values(
            by=["skill_match_percentage", "total_development_effort"],
            ascending=[False, True]
        )
        
        # Return top N results
        return df.head(top_n)
    
    def generate_reskilling_pathway(
        self,
        employee_id: str,
        target_job_id: str
    ) -> Dict[str, List[Dict[str, Union[str, int, float]]]]:
        """
        Generate a reskilling pathway for an employee to a target job.
        
        The pathway includes:
        - Skills to develop (missing skills)
        - Skills to maintain (matching skills)
        - Skills that may become less relevant (excess skills)
        
        Args:
            employee_id: ID of the employee
            target_job_id: ID of the target job
            
        Returns:
            Dictionary with reskilling pathway components
            
        Raises:
            ValueError: If the employee ID or job ID is not found
        """
        # Analyze gap between employee and target job
        result = self.analyze_employee_job_gap(employee_id, target_job_id)
        
        # Convert missing skills to development tasks
        skills_to_develop = []
        for gap in sorted(result.missing_skills, key=lambda g: g.development_effort, reverse=True):
            skills_to_develop.append({
                "skill_id": gap.skill_id,
                "skill_name": gap.skill_name,
                "current_proficiency": gap.employee_proficiency,
                "target_proficiency": gap.job_proficiency,
                "development_effort": gap.development_effort,
                "priority": "High" if gap.development_effort > 3 else "Medium" if gap.development_effort > 1 else "Low"
            })
        
        # Convert matching skills to maintenance tasks
        skills_to_maintain = []
        for gap in result.matching_skills:
            skills_to_maintain.append({
                "skill_id": gap.skill_id,
                "skill_name": gap.skill_name,
                "current_proficiency": gap.employee_proficiency,
                "target_proficiency": gap.job_proficiency,
                "status": "Above required" if gap.employee_proficiency > gap.job_proficiency else "Meets required"
            })
        
        # Convert excess skills to potential obsolescence
        potentially_obsolete_skills = []
        for gap in result.excess_skills:
            potentially_obsolete_skills.append({
                "skill_id": gap.skill_id,
                "skill_name": gap.skill_name,
                "current_proficiency": gap.employee_proficiency,
                "relevance": "Not required for target role"
            })
        
        # Create pathway
        pathway = {
            "employee_id": employee_id,
            "employee_name": result.employee_name,
            "target_job_id": target_job_id,
            "target_job_title": result.job_title,
            "skills_to_develop": skills_to_develop,
            "skills_to_maintain": skills_to_maintain,
            "potentially_obsolete_skills": potentially_obsolete_skills,
            "overall_match_percentage": result.skill_match_percentage,
            "overall_development_effort": result.total_development_effort,
            "estimated_difficulty": result.reskilling_difficulty
        }
        
        return pathway


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
        min_gap_threshold: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Identify critical skill gaps across a department or the entire organization.
        
        Args:
            department: Department to analyze (all departments if None)
            min_gap_threshold: Minimum gap threshold to consider critical (uses config value if None)
            
        Returns:
            DataFrame with critical skill gaps
        """
        # Use configuration value if not provided
        if min_gap_threshold is None:
            min_gap_threshold = get_config().gap_analysis.min_gap_threshold
        
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
