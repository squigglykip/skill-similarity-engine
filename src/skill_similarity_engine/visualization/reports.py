"""
Basic reporting functionality for exporting analysis results.

This module provides functionality for exporting analysis results to DataFrames,
CSV files, JSON files, and other formats.
"""

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pandas as pd

from ..config.settings import get_config, get_output_path
from ..models.employees import Employee, EmployeeDatabase
from ..models.jobs import Job, JobArchitecture
from ..models.skills import Skill, SkillTaxonomy


class ReportFormat(Enum):
    """Supported report formats."""
    DATAFRAME = "dataframe"
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"


@dataclass
class ReportConfiguration:
    """
    Configuration for report generation.
    
    Attributes:
        output_dir: Directory for output files
        include_headers: Whether to include headers in CSV files
        date_format: Format for date columns
        float_format: Format for float columns
        index: Whether to include index in exports
        encoding: Character encoding for text files
        indent: Indentation for JSON files
    """
    output_dir: str = field(default_factory=lambda: get_config().output_dir)
    include_headers: bool = True
    date_format: str = "%Y-%m-%d"
    float_format: str = "%.2f"
    index: bool = False
    encoding: str = "utf-8"
    indent: int = 2


class ReportGenerator:
    """
    Generator for creating and exporting reports.
    
    Attributes:
        config: Report configuration
    """
    
    def __init__(self, config: Optional[ReportConfiguration] = None):
        """
        Initialize the report generator.
        
        Args:
            config: Report configuration
        """
        self.config = config or ReportConfiguration()
    
    def export_dataframe(
        self,
        data: Union[pd.DataFrame, Dict, List],
        file_name: str,
        format: ReportFormat,
        **kwargs
    ) -> Optional[pd.DataFrame]:
        """
        Export data to a file in the specified format.
        
        Args:
            data: Data to export (DataFrame, dict, or list)
            file_name: Name of the output file
            format: Output format
            **kwargs: Additional arguments for export function
            
        Returns:
            DataFrame if format is DATAFRAME, None otherwise
            
        Raises:
            ValueError: If the data cannot be converted to a DataFrame
        """
        # Convert data to DataFrame if necessary
        df = self._ensure_dataframe(data)
        
        # Export based on format
        if format == ReportFormat.DATAFRAME:
            return df
        
        # Get full output path
        output_path = os.path.join(self.config.output_dir, file_name)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Export to file
        if format == ReportFormat.CSV:
            df.to_csv(
                output_path,
                header=self.config.include_headers,
                index=self.config.index,
                date_format=self.config.date_format,
                float_format=self.config.float_format,
                encoding=self.config.encoding,
                **kwargs
            )
        elif format == ReportFormat.JSON:
            df.to_json(
                output_path,
                date_format=self.config.date_format,
                orient=kwargs.get("orient", "records"),
                indent=self.config.indent,
                **{k: v for k, v in kwargs.items() if k != "orient"}
            )
        elif format == ReportFormat.EXCEL:
            df.to_excel(
                output_path,
                header=self.config.include_headers,
                index=self.config.index,
                float_format=self.config.float_format,
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        return None
    
    def _ensure_dataframe(self, data: Union[pd.DataFrame, Dict, List]) -> pd.DataFrame:
        """
        Ensure data is a DataFrame.
        
        Args:
            data: Data to convert
            
        Returns:
            DataFrame
            
        Raises:
            ValueError: If the data cannot be converted to a DataFrame
        """
        if isinstance(data, pd.DataFrame):
            return data
        
        if isinstance(data, dict):
            # Check if it's a dict of series-like objects
            if all(isinstance(v, (list, tuple, pd.Series)) for v in data.values()):
                return pd.DataFrame(data)
            
            # Single record dict
            return pd.DataFrame([data])
        
        if isinstance(data, list):
            if not data:
                return pd.DataFrame()
            
            if all(isinstance(item, dict) for item in data):
                return pd.DataFrame(data)
        
        raise ValueError("Cannot convert data to DataFrame")


class SimilarityReportGenerator:
    """
    Generator for creating similarity reports.
    
    Attributes:
        report_generator: Basic report generator
        skill_taxonomy: Skill taxonomy
        job_architecture: Job architecture
        employee_database: Employee database
    """
    
    def __init__(
        self,
        skill_taxonomy: SkillTaxonomy,
        job_architecture: JobArchitecture,
        employee_database: Optional[EmployeeDatabase] = None,
        report_config: Optional[ReportConfiguration] = None
    ):
        """
        Initialize the similarity report generator.
        
        Args:
            skill_taxonomy: Skill taxonomy
            job_architecture: Job architecture
            employee_database: Employee database
            report_config: Report configuration
        """
        self.report_generator = ReportGenerator(report_config)
        self.skill_taxonomy = skill_taxonomy
        self.job_architecture = job_architecture
        self.employee_database = employee_database
    
    def generate_job_similarity_report(
        self,
        job_id: str,
        top_n: int = 5,
        format: ReportFormat = ReportFormat.DATAFRAME,
        file_name: Optional[str] = None,
        **kwargs
    ) -> Optional[pd.DataFrame]:
        """
        Generate a report of jobs similar to a given job.
        
        Args:
            job_id: ID of the job
            top_n: Number of similar jobs to include
            format: Output format
            file_name: Name of the output file (default: job_similarity_{job_id}.{ext})
            **kwargs: Additional arguments for export function
            
        Returns:
            DataFrame if format is DATAFRAME, None otherwise
            
        Raises:
            ValueError: If the job ID is not found
            ImportError: If the similarity module is not available
        """
        try:
            from ..similarity.cosine import CosineSimilarityCalculator
        except ImportError:
            raise ImportError("Similarity module not available")
        
        if job_id not in self.job_architecture.jobs:
            raise ValueError(f"Job with ID {job_id} not found")
        
        # Create similarity calculator
        calculator = CosineSimilarityCalculator(
            vectorizer=None,  # Will be created by the calculator
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
        
        # Find similar jobs
        similar_jobs = calculator.find_similar_jobs(job_id, top_n)
        
        # Create report data
        report_data = []
        for similar_job_id, similarity_score in similar_jobs:
            job = self.job_architecture.jobs[similar_job_id]
            report_data.append({
                "job_id": similar_job_id,
                "job_title": job.title,
                "department": job.department,
                "level": job.level.value,
                "similarity_score": similarity_score,
                "common_skills_count": len(set(self.job_architecture.jobs[job_id].skills.keys()) & 
                                          set(job.skills.keys()))
            })
        
        # Generate the default file name if not provided
        if file_name is None:
            ext = format.value if format != ReportFormat.DATAFRAME else "csv"
            file_name = f"job_similarity_{job_id}.{ext}"
        
        # Export report
        return self.report_generator.export_dataframe(
            data=report_data,
            file_name=file_name,
            format=format,
            **kwargs
        )
    
    def generate_employee_similarity_report(
        self,
        employee_id: str,
        top_n: int = 5,
        format: ReportFormat = ReportFormat.DATAFRAME,
        file_name: Optional[str] = None,
        **kwargs
    ) -> Optional[pd.DataFrame]:
        """
        Generate a report of employees similar to a given employee.
        
        Args:
            employee_id: ID of the employee
            top_n: Number of similar employees to include
            format: Output format
            file_name: Name of the output file (default: employee_similarity_{employee_id}.{ext})
            **kwargs: Additional arguments for export function
            
        Returns:
            DataFrame if format is DATAFRAME, None otherwise
            
        Raises:
            ValueError: If the employee ID is not found or employee database is not set
            ImportError: If the similarity module is not available
        """
        if not self.employee_database:
            raise ValueError("Employee database not set")
        
        try:
            from ..similarity.cosine import CosineSimilarityCalculator
        except ImportError:
            raise ImportError("Similarity module not available")
        
        if employee_id not in self.employee_database.employees:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        # Create similarity calculator
        calculator = CosineSimilarityCalculator(
            vectorizer=None,  # Will be created by the calculator
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
        
        # Find similar employees
        similar_employees = calculator.find_similar_employees(employee_id, top_n)
        
        # Create report data
        report_data = []
        for similar_employee_id, similarity_score in similar_employees:
            employee = self.employee_database.employees[similar_employee_id]
            job = self.job_architecture.jobs.get(employee.current_job)
            job_title = job.title if job else "Unknown"
            
            report_data.append({
                "employee_id": similar_employee_id,
                "employee_name": employee.name,
                "current_job": employee.current_job,
                "job_title": job_title,
                "similarity_score": similarity_score,
                "common_skills_count": len(set(self.employee_database.employees[employee_id].skills.keys()) & 
                                          set(employee.skills.keys()))
            })
        
        # Generate the default file name if not provided
        if file_name is None:
            ext = format.value if format != ReportFormat.DATAFRAME else "csv"
            file_name = f"employee_similarity_{employee_id}.{ext}"
        
        # Export report
        return self.report_generator.export_dataframe(
            data=report_data,
            file_name=file_name,
            format=format,
            **kwargs
        )
    
    def generate_job_skill_distribution_report(
        self,
        department: Optional[str] = None,
        format: ReportFormat = ReportFormat.DATAFRAME,
        file_name: Optional[str] = None,
        **kwargs
    ) -> Optional[pd.DataFrame]:
        """
        Generate a report of skill distribution across jobs.
        
        Args:
            department: Department to filter by (all departments if None)
            format: Output format
            file_name: Name of the output file (default: job_skill_distribution.{ext})
            **kwargs: Additional arguments for export function
            
        Returns:
            DataFrame if format is DATAFRAME, None otherwise
        """
        # Get jobs to include in the report
        if department:
            jobs = self.job_architecture.get_jobs_by_department(department)
        else:
            jobs = list(self.job_architecture.jobs.values())
        
        # Count skills across jobs
        skill_counts = {}
        for job in jobs:
            for skill_id, proficiency in job.skills.items():
                if proficiency > 0:
                    if skill_id not in skill_counts:
                        skill_counts[skill_id] = 0
                    skill_counts[skill_id] += 1
        
        # Create report data
        report_data = []
        for skill_id, count in sorted(skill_counts.items(), key=lambda x: x[1], reverse=True):
            skill = self.skill_taxonomy.skills.get(skill_id)
            skill_name = skill.name if skill else "Unknown Skill"
            
            # Calculate percentage
            percentage = (count / len(jobs)) * 100 if jobs else 0
            
            report_data.append({
                "skill_id": skill_id,
                "skill_name": skill_name,
                "job_count": count,
                "percentage": percentage,
                "average_proficiency": sum(job.skills.get(skill_id, 0) for job in jobs) / count if count > 0 else 0
            })
        
        # Generate the default file name if not provided
        if file_name is None:
            dept_suffix = f"_{department}" if department else ""
            ext = format.value if format != ReportFormat.DATAFRAME else "csv"
            file_name = f"job_skill_distribution{dept_suffix}.{ext}"
        
        # Export report
        return self.report_generator.export_dataframe(
            data=report_data,
            file_name=file_name,
            format=format,
            **kwargs
        )


class GapAnalysisReportGenerator:
    """
    Generator for creating gap analysis reports.
    
    Attributes:
        report_generator: Basic report generator
        skill_taxonomy: Skill taxonomy
        job_architecture: Job architecture
        employee_database: Employee database
    """
    
    def __init__(
        self,
        skill_taxonomy: SkillTaxonomy,
        job_architecture: JobArchitecture,
        employee_database: EmployeeDatabase,
        report_config: Optional[ReportConfiguration] = None
    ):
        """
        Initialize the gap analysis report generator.
        
        Args:
            skill_taxonomy: Skill taxonomy
            job_architecture: Job architecture
            employee_database: Employee database
            report_config: Report configuration
        """
        self.report_generator = ReportGenerator(report_config)
        self.skill_taxonomy = skill_taxonomy
        self.job_architecture = job_architecture
        self.employee_database = employee_database
    
    def generate_employee_job_gap_report(
        self,
        employee_id: str,
        job_id: str,
        format: ReportFormat = ReportFormat.DATAFRAME,
        file_name: Optional[str] = None,
        **kwargs
    ) -> Optional[pd.DataFrame]:
        """
        Generate a report of skill gaps between an employee and a job.
        
        Args:
            employee_id: ID of the employee
            job_id: ID of the job
            format: Output format
            file_name: Name of the output file (default: employee_job_gap_{employee_id}_{job_id}.{ext})
            **kwargs: Additional arguments for export function
            
        Returns:
            DataFrame if format is DATAFRAME, None otherwise
            
        Raises:
            ValueError: If the employee ID or job ID is not found
            ImportError: If the gap analysis module is not available
        """
        try:
            from ..analysis.gap import SkillGapAnalyzer
        except ImportError:
            raise ImportError("Gap analysis module not available")
        
        # Create skill gap analyzer
        analyzer = SkillGapAnalyzer(
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
        
        # Analyze skill gap
        gap_analysis = analyzer.analyze_employee_job_gap(employee_id, job_id)
        
        # Convert to DataFrame
        df = gap_analysis.to_dataframe()
        
        # Generate the default file name if not provided
        if file_name is None:
            ext = format.value if format != ReportFormat.DATAFRAME else "csv"
            file_name = f"employee_job_gap_{employee_id}_{job_id}.{ext}"
        
        # Export report
        return self.report_generator.export_dataframe(
            data=df,
            file_name=file_name,
            format=format,
            **kwargs
        )
    
    def generate_reskilling_pathway_report(
        self,
        employee_id: str,
        target_job_id: str,
        format: ReportFormat = ReportFormat.DATAFRAME,
        file_name: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict]:
        """
        Generate a report of the reskilling pathway for an employee to a target job.
        
        Args:
            employee_id: ID of the employee
            target_job_id: ID of the target job
            format: Output format
            file_name: Name of the output file (default: reskilling_pathway_{employee_id}_{target_job_id}.{ext})
            **kwargs: Additional arguments for export function
            
        Returns:
            Dictionary with pathway data if format is DATAFRAME, None otherwise
            
        Raises:
            ValueError: If the employee ID or job ID is not found
            ImportError: If the gap analysis module is not available
        """
        try:
            from ..analysis.gap import SkillGapAnalyzer
        except ImportError:
            raise ImportError("Gap analysis module not available")
        
        # Create skill gap analyzer
        analyzer = SkillGapAnalyzer(
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
        
        # Generate reskilling pathway
        pathway = analyzer.generate_reskilling_pathway(employee_id, target_job_id)
        
        # Return pathway if format is DATAFRAME
        if format == ReportFormat.DATAFRAME:
            return pathway
        
        # Generate the default file name if not provided
        if file_name is None:
            ext = format.value
            file_name = f"reskilling_pathway_{employee_id}_{target_job_id}.{ext}"
        
        # Export pathway based on format
        output_path = os.path.join(self.report_generator.config.output_dir, file_name)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if format == ReportFormat.JSON:
            with open(output_path, "w", encoding=self.report_generator.config.encoding) as f:
                json.dump(
                    pathway,
                    f,
                    indent=self.report_generator.config.indent,
                    default=str  # Handle non-serializable objects
                )
        elif format == ReportFormat.CSV:
            # Convert nested structure to flat DataFrame
            all_skills = []
            
            # Add skills to develop
            for skill in pathway.get("skills_to_develop", []):
                all_skills.append({
                    "employee_id": pathway["employee_id"],
                    "employee_name": pathway["employee_name"],
                    "target_job_id": pathway["target_job_id"],
                    "target_job_title": pathway["target_job_title"],
                    "skill_id": skill["skill_id"],
                    "skill_name": skill["skill_name"],
                    "current_proficiency": skill["current_proficiency"],
                    "target_proficiency": skill["target_proficiency"],
                    "development_effort": skill.get("development_effort", ""),
                    "priority": skill.get("priority", ""),
                    "status": "To Develop",
                    "relevance": "Required"
                })
            
            # Add skills to maintain
            for skill in pathway.get("skills_to_maintain", []):
                all_skills.append({
                    "employee_id": pathway["employee_id"],
                    "employee_name": pathway["employee_name"],
                    "target_job_id": pathway["target_job_id"],
                    "target_job_title": pathway["target_job_title"],
                    "skill_id": skill["skill_id"],
                    "skill_name": skill["skill_name"],
                    "current_proficiency": skill["current_proficiency"],
                    "target_proficiency": skill["target_proficiency"],
                    "development_effort": "",
                    "priority": "",
                    "status": skill.get("status", "To Maintain"),
                    "relevance": "Required"
                })
            
            # Add potentially obsolete skills
            for skill in pathway.get("potentially_obsolete_skills", []):
                all_skills.append({
                    "employee_id": pathway["employee_id"],
                    "employee_name": pathway["employee_name"],
                    "target_job_id": pathway["target_job_id"],
                    "target_job_title": pathway["target_job_title"],
                    "skill_id": skill["skill_id"],
                    "skill_name": skill["skill_name"],
                    "current_proficiency": skill["current_proficiency"],
                    "target_proficiency": 0,
                    "development_effort": "",
                    "priority": "",
                    "status": "Excess",
                    "relevance": skill.get("relevance", "Not Required")
                })
            
            # Convert to DataFrame and export as CSV
            self.report_generator.export_dataframe(
                data=all_skills,
                file_name=file_name,
                format=ReportFormat.CSV,
                **kwargs
            )
        elif format == ReportFormat.EXCEL:
            # Create Excel writer
            import xlsxwriter
            with pd.ExcelWriter(output_path) as writer:
                # Create summary sheet
                summary_data = {
                    "Metric": [
                        "Employee ID",
                        "Employee Name",
                        "Target Job ID",
                        "Target Job Title",
                        "Overall Match Percentage",
                        "Overall Development Effort",
                        "Estimated Difficulty",
                        "Skills to Develop Count",
                        "Skills to Maintain Count",
                        "Potentially Obsolete Skills Count"
                    ],
                    "Value": [
                        pathway["employee_id"],
                        pathway["employee_name"],
                        pathway["target_job_id"],
                        pathway["target_job_title"],
                        f"{pathway.get('overall_match_percentage', 0):.2f}%",
                        f"{pathway.get('overall_development_effort', 0):.2f}",
                        f"{pathway.get('estimated_difficulty', 0):.2f}/5.0",
                        len(pathway.get("skills_to_develop", [])),
                        len(pathway.get("skills_to_maintain", [])),
                        len(pathway.get("potentially_obsolete_skills", []))
                    ]
                }
                pd.DataFrame(summary_data).to_excel(
                    writer,
                    sheet_name="Summary",
                    index=False
                )
                
                # Create sheet for skills to develop
                develop_data = pd.DataFrame(pathway.get("skills_to_develop", []))
                if not develop_data.empty:
                    develop_data.to_excel(
                        writer,
                        sheet_name="Skills to Develop",
                        index=False
                    )
                
                # Create sheet for skills to maintain
                maintain_data = pd.DataFrame(pathway.get("skills_to_maintain", []))
                if not maintain_data.empty:
                    maintain_data.to_excel(
                        writer,
                        sheet_name="Skills to Maintain",
                        index=False
                    )
                
                # Create sheet for potentially obsolete skills
                obsolete_data = pd.DataFrame(pathway.get("potentially_obsolete_skills", []))
                if not obsolete_data.empty:
                    obsolete_data.to_excel(
                        writer,
                        sheet_name="Potentially Obsolete Skills",
                        index=False
                    )
        
        return None
    
    def generate_workforce_gap_report(
        self,
        department: Optional[str] = None,
        min_gap_threshold: float = 2.0,
        format: ReportFormat = ReportFormat.DATAFRAME,
        file_name: Optional[str] = None,
        **kwargs
    ) -> Optional[pd.DataFrame]:
        """
        Generate a report of workforce skill gaps.
        
        Args:
            department: Department to filter by (all departments if None)
            min_gap_threshold: Minimum gap threshold to consider critical
            format: Output format
            file_name: Name of the output file (default: workforce_gap{_department}.{ext})
            **kwargs: Additional arguments for export function
            
        Returns:
            DataFrame if format is DATAFRAME, None otherwise
            
        Raises:
            ImportError: If the gap analysis module is not available
        """
        try:
            from ..analysis.gap import TeamGapAnalyzer
        except ImportError:
            raise ImportError("Gap analysis module not available")
        
        # Create team gap analyzer
        analyzer = TeamGapAnalyzer(
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
        
        # Identify critical skill gaps
        critical_gaps = analyzer.identify_critical_skill_gaps(department, min_gap_threshold)
        
        # Generate the default file name if not provided
        if file_name is None:
            dept_suffix = f"_{department}" if department else ""
            ext = format.value if format != ReportFormat.DATAFRAME else "csv"
            file_name = f"workforce_gap{dept_suffix}.{ext}"
        
        # Export report
        return self.report_generator.export_dataframe(
            data=critical_gaps,
            file_name=file_name,
            format=format,
            **kwargs
        )


class ReportConfig:
    """Configuration for export reports."""
    
    def __init__(
        self,
        include_metadata: bool = True,
        format: str = "csv",
        include_descriptions: bool = False,
        include_ids: bool = True,
        include_names: bool = True,
        add_opportunity_flags: bool = True,
        high_similarity_threshold: Optional[float] = None,
        low_gap_threshold: Optional[float] = None,
    ):
        """
        Initialize the report configuration.
        
        Args:
            include_metadata: Whether to include metadata columns
            format: Export format ('csv', 'excel', or 'json')
            include_descriptions: Whether to include description fields
            include_ids: Whether to include ID fields
            include_names: Whether to include name fields
            add_opportunity_flags: Whether to add opportunity flag columns
            high_similarity_threshold: Threshold for high similarity (0.0-1.0)
                If None, uses the value from global config
            low_gap_threshold: Threshold for low skill gap (development effort)
                If None, uses the value from global config
        """
        from ..config.settings import get_config
        
        config = get_config()
        
        self.include_metadata = include_metadata
        self.format = format
        self.include_descriptions = include_descriptions
        self.include_ids = include_ids
        self.include_names = include_names
        self.add_opportunity_flags = add_opportunity_flags
        self.high_similarity_threshold = high_similarity_threshold if high_similarity_threshold is not None else config.opportunity.high_similarity_threshold
        self.low_gap_threshold = low_gap_threshold if low_gap_threshold is not None else config.opportunity.low_gap_threshold


class DataExporter:
    """
    Exporter for tabular data from skill similarity analysis.
    
    Attributes:
        skill_taxonomy: Skill taxonomy
        job_architecture: Job architecture
        employee_database: Employee database
        output_dir: Directory for output files
    """
    
    def __init__(
        self,
        skill_taxonomy: SkillTaxonomy,
        job_architecture: JobArchitecture,
        employee_database: Optional[EmployeeDatabase] = None,
        output_dir: Optional[str] = None
    ):
        """
        Initialize the data exporter.
        
        Args:
            skill_taxonomy: Skill taxonomy
            job_architecture: Job architecture
            employee_database: Employee database
            output_dir: Directory for output files (default: from config)
        """
        self.skill_taxonomy = skill_taxonomy
        self.job_architecture = job_architecture
        self.employee_database = employee_database
        self.output_dir = output_dir or get_config().output_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def export_job_similarity_matrix(
        self,
        departments: Optional[List[str]] = None,
        threshold: Optional[float] = None,
        config: Optional[ReportConfig] = None,
        output_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Export the job similarity matrix as a tabular dataset.
        
        Args:
            departments: Departments to filter by (all departments if None)
            threshold: Similarity threshold (export all similarities if None)
            config: Report configuration
            output_path: Path to save the exported data
            
        Returns:
            DataFrame with job similarity data
        """
        if config is None:
            config = ReportConfig()
        
        # Filter jobs by department if specified
        if departments:
            job_ids = [
                job_id for job_id, job in self.job_architecture.jobs.items()
                if job.department in departments
            ]
        else:
            job_ids = list(self.job_architecture.jobs.keys())
        
        # Create dataframe with job-to-job similarities
        rows = []
        for i, job_id1 in enumerate(job_ids):
            job1 = self.job_architecture.jobs[job_id1]
            
            for job_id2 in job_ids[i+1:]:  # Only upper triangle to avoid duplicates
                job2 = self.job_architecture.jobs[job_id2]
                
                # Calculate similarity between jobs
                similarity = job1.skill_vector.cosine_similarity(job2.skill_vector)
                
                # Skip if below threshold
                if threshold is not None and similarity < threshold:
                    continue
                
                # Create row with basic data
                row = {
                    "job_id_1": job_id1,
                    "job_id_2": job_id2,
                    "similarity": similarity
                }
                
                # Add opportunity flag if requested
                if config.add_opportunity_flags:
                    # Flag high similarity jobs
                    is_high_similarity = similarity >= config.high_similarity_threshold
                    row["is_high_similarity_opportunity"] = is_high_similarity
                    
                    # Flag if in same department (internal mobility opportunity)
                    is_same_dept = job1.department == job2.department
                    row["is_internal_mobility_opportunity"] = is_high_similarity and is_same_dept
                    
                    # Flag if in different departments (cross-departmental opportunity)
                    row["is_cross_departmental_opportunity"] = is_high_similarity and not is_same_dept
                
                # Add metadata if requested
                if config.include_metadata:
                    row.update({
                        "department_1": job1.department,
                        "department_2": job2.department,
                        "same_department": job1.department == job2.department
                    })
                
                # Add names if requested
                if config.include_names:
                    row.update({
                        "job_title_1": job1.title,
                        "job_title_2": job2.title
                    })
                
                # Add descriptions if requested
                if config.include_descriptions and hasattr(job1, "description") and hasattr(job2, "description"):
                    row.update({
                        "job_description_1": job1.description,
                        "job_description_2": job2.description
                    })
                
                rows.append(row)
        
        # Create dataframe from rows
        df = pd.DataFrame(rows)
        
        # Export dataframe if output path is specified
        if output_path:
            self._export_dataframe(df, output_path, config.format)
        
        return df
    
    def export_employee_similarity_matrix(
        self,
        departments: Optional[List[str]] = None,
        threshold: Optional[float] = None,
        config: Optional[ReportConfig] = None,
        output_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Export the employee similarity matrix as a tabular dataset.
        
        Args:
            departments: Departments to filter by (all departments if None)
            threshold: Similarity threshold (export all similarities if None)
            config: Report configuration
            output_path: Path to save the exported data
            
        Returns:
            DataFrame with employee similarity data
            
        Raises:
            ValueError: If employee database is not set
        """
        if not self.employee_database:
            raise ValueError("Employee database not set")
            
        if config is None:
            config = ReportConfig()
        
        # Filter employees by department if specified
        if departments:
            employee_ids = [
                emp_id for emp_id, emp in self.employee_database.employees.items()
                if emp.department in departments
            ]
        else:
            employee_ids = list(self.employee_database.employees.keys())
        
        # Create dataframe with employee-to-employee similarities
        rows = []
        for i, emp_id1 in enumerate(employee_ids):
            emp1 = self.employee_database.employees[emp_id1]
            
            for emp_id2 in employee_ids[i+1:]:  # Only upper triangle to avoid duplicates
                emp2 = self.employee_database.employees[emp_id2]
                
                # Calculate similarity between employees
                similarity = emp1.skill_vector.cosine_similarity(emp2.skill_vector)
                
                # Skip if below threshold
                if threshold is not None and similarity < threshold:
                    continue
                
                # Create row with basic data
                row = {
                    "employee_id_1": emp_id1,
                    "employee_id_2": emp_id2,
                    "similarity": similarity
                }
                
                # Add opportunity flag if requested
                if config.add_opportunity_flags:
                    # Flag high similarity employees
                    is_high_similarity = similarity >= config.high_similarity_threshold
                    row["is_high_similarity_opportunity"] = is_high_similarity
                    
                    # Flag if same job (skill sharing opportunity)
                    is_same_job = emp1.job_id == emp2.job_id
                    row["is_skill_sharing_opportunity"] = is_high_similarity and is_same_job
                    
                    # Flag if different jobs but high similarity (potential job rotation)
                    row["is_job_rotation_opportunity"] = is_high_similarity and not is_same_job
                
                # Add metadata if requested
                if config.include_metadata:
                    row.update({
                        "department_1": emp1.department,
                        "department_2": emp2.department,
                        "same_department": emp1.department == emp2.department,
                        "job_id_1": emp1.job_id,
                        "job_id_2": emp2.job_id,
                        "same_job": emp1.job_id == emp2.job_id
                    })
                
                # Add names if requested
                if config.include_names:
                    row.update({
                        "employee_name_1": emp1.name,
                        "employee_name_2": emp2.name
                    })
                    
                    # Add job titles if available
                    if emp1.job_id in self.job_architecture.jobs:
                        row["job_title_1"] = self.job_architecture.jobs[emp1.job_id].title
                    if emp2.job_id in self.job_architecture.jobs:
                        row["job_title_2"] = self.job_architecture.jobs[emp2.job_id].title
                
                rows.append(row)
        
        # Create dataframe from rows
        df = pd.DataFrame(rows)
        
        # Export dataframe if output path is specified
        if output_path:
            self._export_dataframe(df, output_path, config.format)
        
        return df
    
    def export_skill_gap_analysis(
        self,
        employee_ids: List[str],
        job_ids: List[str],
        config: Optional[ReportConfig] = None,
        output_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Export the skill gap analysis as a tabular dataset.
        
        Args:
            employee_ids: IDs of employees to include
            job_ids: IDs of jobs to include
            config: Report configuration
            output_path: Path to save the exported data
            
        Returns:
            DataFrame with skill gap data
            
        Raises:
            ValueError: If employee database is not set
        """
        if not self.employee_database:
            raise ValueError("Employee database not set")
            
        if config is None:
            config = ReportConfig()
        
        # Get global configuration
        from ..config.settings import get_config
        global_config = get_config()
        
        # Validate employee and job IDs
        for emp_id in employee_ids:
            if emp_id not in self.employee_database.employees:
                raise ValueError(f"Employee ID not found: {emp_id}")
        
        for job_id in job_ids:
            if job_id not in self.job_architecture.jobs:
                raise ValueError(f"Job ID not found: {job_id}")
        
        # Create dataframe with skill gaps
        rows = []
        for emp_id in employee_ids:
            employee = self.employee_database.employees[emp_id]
            employee_skills = set(employee.skills.keys())
            
            for job_id in job_ids:
                job = self.job_architecture.jobs[job_id]
                required_skills = set(job.skills.keys())
                
                # Calculate metrics
                missing_skills = required_skills - employee_skills
                excess_skills = employee_skills - required_skills
                matching_skills = employee_skills.intersection(required_skills)
                
                if required_skills:
                    match_percentage = len(matching_skills) / len(required_skills) * 100
                else:
                    match_percentage = 100.0
                
                # Calculate development effort (simplified)
                development_effort = sum(
                    self.skill_taxonomy.skills[skill_id].difficulty
                    for skill_id in missing_skills
                    if skill_id in self.skill_taxonomy.skills
                )
                
                # Create row with basic data
                row = {
                    "employee_id": emp_id,
                    "job_id": job_id,
                    "match_percentage": match_percentage,
                    "development_effort": development_effort,
                    "missing_skill_count": len(missing_skills),
                    "excess_skill_count": len(excess_skills),
                    "matching_skill_count": len(matching_skills)
                }
                
                # Add opportunity flags if requested
                if config.add_opportunity_flags:
                    # Flag high match percentage (good fit)
                    is_high_match = match_percentage >= global_config.opportunity.high_match_percentage
                    row["is_good_fit_opportunity"] = is_high_match
                    
                    # Flag low development effort (easy transition)
                    is_low_effort = development_effort <= config.low_gap_threshold
                    row["is_easy_transition_opportunity"] = is_low_effort
                    
                    # Flag career advancement opportunities
                    if employee.job_id in self.job_architecture.jobs:
                        current_job = self.job_architecture.jobs[employee.job_id]
                        is_advancement = (
                            job.level > current_job.level if hasattr(job, "level") and hasattr(current_job, "level") else False
                        )
                        is_career_path = is_advancement and (is_high_match or is_low_effort)
                        row["is_career_advancement_opportunity"] = is_career_path
                
                # Add metadata if requested
                if config.include_metadata:
                    row.update({
                        "department": employee.department,
                        "job_department": job.department,
                        "current_job_id": employee.job_id,
                        "is_current_job": employee.job_id == job_id
                    })
                
                # Add names if requested
                if config.include_names:
                    row.update({
                        "employee_name": employee.name,
                        "job_title": job.title
                    })
                    
                    if employee.job_id in self.job_architecture.jobs:
                        row["current_job_title"] = self.job_architecture.jobs[employee.job_id].title
                
                # Add detailed skill information if requested
                if config.include_descriptions:
                    row.update({
                        "missing_skills": ",".join(missing_skills),
                        "excess_skills": ",".join(excess_skills),
                        "matching_skills": ",".join(matching_skills)
                    })
                
                rows.append(row)
        
        # Create dataframe from rows
        df = pd.DataFrame(rows)
        
        # Export dataframe if output path is specified
        if output_path:
            self._export_dataframe(df, output_path, config.format)
        
        return df
    
    def export_workforce_planning_data(
        self,
        departments: Optional[List[str]] = None,
        config: Optional[ReportConfig] = None,
        output_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Export workforce planning data as a tabular dataset.
        
        Args:
            departments: Departments to filter by (all departments if None)
            config: Report configuration
            output_path: Path to save the exported data
            
        Returns:
            DataFrame with workforce planning data
            
        Raises:
            ValueError: If employee database is not set
        """
        if not self.employee_database:
            raise ValueError("Employee database not set")
            
        if config is None:
            config = ReportConfig()
        
        # Get global configuration
        from ..config.settings import get_config
        global_config = get_config()
        
        # Filter by departments if specified
        if departments:
            dept_jobs = {
                job_id: job for job_id, job in self.job_architecture.jobs.items()
                if job.department in departments
            }
            dept_employees = {
                emp_id: emp for emp_id, emp in self.employee_database.employees.items()
                if emp.department in departments
            }
        else:
            dept_jobs = self.job_architecture.jobs
            dept_employees = self.employee_database.employees
        
        # Count employees per job
        job_counts = {job_id: 0 for job_id in dept_jobs}
        for emp in dept_employees.values():
            if emp.job_id in job_counts:
                job_counts[emp.job_id] += 1
        
        # Calculate skill coverage across the workforce
        workforce_skill_counts = {}
        for emp in dept_employees.values():
            for skill_id in emp.skills:
                if skill_id not in workforce_skill_counts:
                    workforce_skill_counts[skill_id] = 0
                workforce_skill_counts[skill_id] += 1
        
        # Calculate skill demand across jobs
        job_skill_demand = {}
        for job in dept_jobs.values():
            for skill_id in job.skills:
                if skill_id not in job_skill_demand:
                    job_skill_demand[skill_id] = 0
                job_skill_demand[skill_id] += 1
        
        # Calculate skill gaps at the workforce level
        rows = []
        for skill_id, demand_count in job_skill_demand.items():
            supply_count = workforce_skill_counts.get(skill_id, 0)
            
            # Calculate gap percentage
            if demand_count > 0:
                gap_percentage = max(0, demand_count - supply_count) / demand_count * 100
            else:
                gap_percentage = 0
            
            skill = self.skill_taxonomy.skills.get(skill_id, None)
            if not skill:
                continue
                
            # Create row with basic data
            row = {
                "skill_id": skill_id,
                "demand_count": demand_count,
                "supply_count": supply_count,
                "gap_count": max(0, demand_count - supply_count),
                "gap_percentage": gap_percentage,
                "category": skill.category,
                "difficulty": skill.difficulty
            }
            
            # Add opportunity flags if requested
            if config.add_opportunity_flags:
                # Flag critical skill gaps (high gap percentage)
                is_critical_gap = gap_percentage >= global_config.opportunity.critical_gap_percentage
                row["is_critical_skill_gap"] = is_critical_gap
                
                # Flag high demand skills (most demanded skills)
                is_high_demand = demand_count >= 10
                row["is_high_demand_skill"] = is_high_demand
                
                # Flag rare skills (low supply, but some demand)
                is_rare_skill = supply_count < demand_count * 0.2 and demand_count > 2
                row["is_rare_skill"] = is_rare_skill
                
                # Flag training opportunities (high gap but not too difficult)
                is_training_opportunity = gap_percentage >= 30.0 and skill.difficulty <= 3
                row["is_training_opportunity"] = is_training_opportunity
            
            # Add metadata if requested
            if config.include_metadata:
                # Count requirements by department
                dept_demands = {}
                for job_id, job in dept_jobs.items():
                    if skill_id in job.skills:
                        dept = job.department
                        if dept not in dept_demands:
                            dept_demands[dept] = 0
                        dept_demands[dept] += 1
                
                row["departments_requiring"] = ",".join(dept_demands.keys())
                row["department_count"] = len(dept_demands)
            
            # Add names if requested
            if config.include_names:
                row["skill_name"] = skill.name
            
            # Add descriptions if requested
            if config.include_descriptions and hasattr(skill, "description"):
                row["skill_description"] = skill.description
            
            rows.append(row)
        
        # Create dataframe from rows
        df = pd.DataFrame(rows)
        
        # Export dataframe if output path is specified
        if output_path:
            self._export_dataframe(df, output_path, config.format)
        
        return df
    
    def export_skill_vectors(
        self,
        entity_type: str = "job",
        departments: Optional[List[str]] = None,
        config: Optional[ReportConfig] = None,
        output_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Export skill vectors as a tabular dataset.
        
        Args:
            entity_type: Type of entity to export vectors for ('job' or 'employee')
            departments: Departments to filter by (all departments if None)
            config: Report configuration
            output_path: Path to save the exported data
            
        Returns:
            DataFrame with skill vector data
            
        Raises:
            ValueError: If employee database is not set and entity_type is 'employee'
        """
        if entity_type == "employee" and not self.employee_database:
            raise ValueError("Employee database not set")
            
        if config is None:
            config = ReportConfig()
        
        # Get entities based on type
        if entity_type == "job":
            entities = self.job_architecture.jobs
            id_field = "job_id"
            name_field = "job_title"
        else:  # entity_type == "employee"
            entities = self.employee_database.employees
            id_field = "employee_id"
            name_field = "employee_name"
        
        # Filter by departments if specified
        if departments:
            entities = {
                entity_id: entity for entity_id, entity in entities.items()
                if entity.department in departments
            }
        
        # Create rows for each entity
        rows = []
        for entity_id, entity in entities.items():
            # Create base row with ID
            row = {id_field: entity_id}
            
            # Add metadata if requested
            if config.include_metadata:
                row["department"] = entity.department
                
                if entity_type == "employee" and entity.job_id:
                    row["job_id"] = entity.job_id
                    if entity.job_id in self.job_architecture.jobs:
                        row["job_title"] = self.job_architecture.jobs[entity.job_id].title
            
            # Add name if requested
            if config.include_names:
                row[name_field] = entity.name if entity_type == "employee" else entity.title
            
            # Add skill vector data
            for skill_id in self.skill_taxonomy.skills:
                row[f"skill_{skill_id}"] = entity.skill_vector.get(skill_id, 0)
            
            rows.append(row)
        
        # Create dataframe from rows
        df = pd.DataFrame(rows)
        
        # Export dataframe if output path is specified
        if output_path:
            self._export_dataframe(df, output_path, config.format)
        
        return df
    
    def _export_dataframe(self, df: pd.DataFrame, path: str, format: str = "csv") -> None:
        """
        Export a dataframe to a file.
        
        Args:
            df: DataFrame to export
            path: Path to save the exported data
            format: Export format ('csv', 'excel', or 'json')
        """
        if format == "csv":
            df.to_csv(path, index=False)
        elif format == "excel":
            df.to_excel(path, index=False)
        elif format == "json":
            df.to_json(path, orient="records", indent=2)
        else:
            raise ValueError(f"Invalid export format: {format}") 