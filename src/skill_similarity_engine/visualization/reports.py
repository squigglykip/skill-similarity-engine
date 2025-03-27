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


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    format: str = "csv"
    include_metadata: bool = False
    add_opportunity_flags: bool = False
    department: Optional[str] = None
    departments: Optional[List[str]] = None
    threshold: float = 0.0


class DataExporter:
    """Exporter for job similarity data."""
    
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
            employee_database: Employee database (optional)
            output_dir: Directory for output files (default: from config)
        """
        self.skill_taxonomy = skill_taxonomy
        self.job_architecture = job_architecture
        self.employee_database = employee_database
        self.output_dir = output_dir or get_config().output_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Initialize similarity calculator
        from ..similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator
        self.vectorizer = TfidfVectorizer(skill_taxonomy)
        self.similarity_calculator = CosineSimilarityCalculator(
            vectorizer=self.vectorizer,
            skill_taxonomy=skill_taxonomy,
            job_architecture=job_architecture
        )
    
    def export_job_similarity_matrix(
        self,
        department: str,
        config: Optional[ReportConfig] = None,
        output_path: Optional[str] = None
    ) -> pd.DataFrame:
        """Export job similarity matrix to CSV or JSON.
        
        Args:
            department: Department to include
            config: Report configuration (if None, defaults to CSV)
            output_path: Path to save the export (if None, auto-generated)
            
        Returns:
            DataFrame containing the similarity matrix
        """
        if config is None:
            config = ReportConfig()
        
        # Get jobs for the specified department
        jobs = [j for j in self.job_architecture.jobs.values() if j.department == department]
        if not jobs:
            raise ValueError(f"No jobs found for department: {department}")
        
        # Calculate similarities using the similarity calculator
        similarities = []
        for i, job1 in enumerate(jobs):
            for j, job2 in enumerate(jobs[i+1:], i+1):
                similarity = self.similarity_calculator.calculate_job_similarity(job1.job_id, job2.job_id)
                
                # Skip if below threshold
                if similarity < config.threshold:
                    continue
                
                record = {
                    "job1_id": job1.job_id,
                    "job2_id": job2.job_id,
                    "similarity": similarity
                }
                
                if config.include_metadata:
                    record.update({
                        "job1_title": job1.title,
                        "job2_title": job2.title,
                        "department": department
                    })
                
                if config.add_opportunity_flags:
                    # Determine if this is an internal mobility opportunity
                    # based on level progression and skill similarity
                    is_internal_mobility = (
                        similarity >= 0.7 and  # High skill similarity
                        job1.level != job2.level and  # Different levels
                        (
                            (job1.level.value < job2.level.value) or  # Upward mobility
                            (job2.level.value < job1.level.value)  # Downward mobility
                        )
                    )
                    
                    record.update({
                        "is_high_similarity_opportunity": similarity >= 0.8,
                        "is_internal_mobility_opportunity": is_internal_mobility,
                        "is_cross_departmental_opportunity": False  # Same department
                    })
                
                similarities.append(record)
        
        # Create DataFrame
        df = pd.DataFrame(similarities)
        
        # Save to file if path provided
        if output_path:
            if config.format.lower() == "csv":
                df.to_csv(output_path, index=False)
            elif config.format.lower() == "json":
                df.to_json(output_path, orient="records", indent=2)
        
        return df
    
    def _calculate_job_similarity(self, job1: Any, job2: Any) -> float:
        """Calculate similarity between two jobs.
        
        Args:
            job1: First job
            job2: Second job
            
        Returns:
            Similarity score between 0 and 1
        """
        # This is a placeholder - in the real implementation,
        # this would use the similarity calculator
        return 0.7  # Fixed value for testing 