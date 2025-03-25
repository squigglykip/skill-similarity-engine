"""
Heatmap visualisation for similarity and gap analysis.

This module provides functionality for generating heatmaps from similarity matrices
and gap analysis results.
"""

import io
import os
from typing import Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from ..config.settings import get_config
from ..models.employees import EmployeeDatabase
from ..models.jobs import JobArchitecture
from ..models.skills import SkillTaxonomy


class HeatmapConfig:
    """Configuration for heatmap visualisation."""
    
    def __init__(
        self,
        title: str = "",
        cmap: str = "viridis",
        figsize: Tuple[int, int] = (10, 8),
        annot: bool = True,
        fmt: str = ".2f",
        linewidths: float = 0.5,
        cbar: bool = True,
        mask_diagonal: bool = False,
        cluster: bool = False,
        vmin: Optional[float] = None,
        vmax: Optional[float] = None
    ):
        """
        Initialize the heatmap configuration.
        
        Args:
            title: Title of the heatmap
            cmap: Colormap to use
            figsize: Figure size (width, height) in inches
            annot: Whether to annotate cells with values
            fmt: Format string for annotations
            linewidths: Width of lines between cells
            cbar: Whether to show a colorbar
            mask_diagonal: Whether to mask the diagonal (self-similarity)
            cluster: Whether to cluster rows and columns
            vmin: Minimum value for colormap
            vmax: Maximum value for colormap
        """
        self.title = title
        self.cmap = cmap
        self.figsize = figsize
        self.annot = annot
        self.fmt = fmt
        self.linewidths = linewidths
        self.cbar = cbar
        self.mask_diagonal = mask_diagonal
        self.cluster = cluster
        self.vmin = vmin
        self.vmax = vmax


class HeatmapGenerator:
    """
    Generator for creating heatmap visualisations.
    
    Attributes:
        output_dir: Directory for output files
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the heatmap generator.
        
        Args:
            output_dir: Directory for output files (default: from config)
        """
        self.output_dir = output_dir or get_config().output_dir
    
    def generate_heatmap(
        self,
        data: Union[np.ndarray, pd.DataFrame],
        row_labels: Optional[List[str]] = None,
        col_labels: Optional[List[str]] = None,
        config: Optional[HeatmapConfig] = None,
        file_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Generate a heatmap visualisation.
        
        Args:
            data: Data matrix or DataFrame
            row_labels: Labels for rows (if data is a matrix)
            col_labels: Labels for columns (if data is a matrix)
            config: Heatmap configuration
            file_path: Path to save the heatmap image
            
        Returns:
            Matplotlib figure
            
        Raises:
            ValueError: If the data is not a matrix or DataFrame
        """
        # Use default configuration if not provided
        if config is None:
            config = HeatmapConfig()
        
        # Convert matrix to DataFrame if necessary
        if isinstance(data, np.ndarray):
            if row_labels is None:
                row_labels = [f"Row {i+1}" for i in range(data.shape[0])]
            
            if col_labels is None:
                col_labels = [f"Col {j+1}" for j in range(data.shape[1])]
            
            df = pd.DataFrame(data, index=row_labels, columns=col_labels)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("Data must be a numpy array or pandas DataFrame")
        
        # Create mask for diagonal if requested
        mask = None
        if config.mask_diagonal and df.shape[0] == df.shape[1]:
            mask = np.zeros_like(df.values, dtype=bool)
            np.fill_diagonal(mask, True)
        
        # Cluster data if requested
        if config.cluster:
            # Compute linkage for rows and columns
            from scipy.cluster.hierarchy import linkage
            row_linkage = linkage(df.values, method='average')
            col_linkage = linkage(df.values.T, method='average')
            
            # Create clustered heatmap
            g = sns.clustermap(
                df,
                cmap=config.cmap,
                annot=config.annot,
                fmt=config.fmt,
                linewidths=config.linewidths,
                cbar=config.cbar,
                mask=mask,
                figsize=config.figsize,
                vmin=config.vmin,
                vmax=config.vmax,
                row_linkage=row_linkage,
                col_linkage=col_linkage
            )
            
            plt.title(config.title)
            fig = g.fig
        else:
            # Create regular heatmap
            plt.figure(figsize=config.figsize)
            ax = sns.heatmap(
                df,
                cmap=config.cmap,
                annot=config.annot,
                fmt=config.fmt,
                linewidths=config.linewidths,
                cbar=config.cbar,
                mask=mask,
                vmin=config.vmin,
                vmax=config.vmax
            )
            
            plt.title(config.title)
            plt.tight_layout()
            fig = plt.gcf()
        
        # Save the figure if a file path is provided
        if file_path:
            # Create output directory if it doesn't exist
            output_path = os.path.join(self.output_dir, file_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            fig.savefig(output_path, dpi=300, bbox_inches='tight')
        
        return fig


class SimilarityHeatmapGenerator:
    """
    Generator for creating similarity heatmaps.
    
    Attributes:
        heatmap_generator: Basic heatmap generator
        skill_taxonomy: Skill taxonomy
        job_architecture: Job architecture
        employee_database: Employee database
    """
    
    def __init__(
        self,
        skill_taxonomy: SkillTaxonomy,
        job_architecture: JobArchitecture,
        employee_database: Optional[EmployeeDatabase] = None,
        output_dir: Optional[str] = None
    ):
        """
        Initialize the similarity heatmap generator.
        
        Args:
            skill_taxonomy: Skill taxonomy
            job_architecture: Job architecture
            employee_database: Employee database
            output_dir: Directory for output files
        """
        self.heatmap_generator = HeatmapGenerator(output_dir)
        self.skill_taxonomy = skill_taxonomy
        self.job_architecture = job_architecture
        self.employee_database = employee_database
    
    def generate_job_similarity_heatmap(
        self,
        department: Optional[str] = None,
        top_n: Optional[int] = None,
        config: Optional[HeatmapConfig] = None,
        file_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Generate a heatmap of job similarities.
        
        Args:
            department: Department to filter by (all departments if None)
            top_n: Number of top jobs to include (all jobs if None)
            config: Heatmap configuration
            file_path: Path to save the heatmap image
            
        Returns:
            Matplotlib figure
            
        Raises:
            ImportError: If the similarity module is not available
        """
        try:
            from ..similarity.cosine import CosineSimilarityCalculator
        except ImportError:
            raise ImportError("Similarity module not available")
        
        # Get jobs to include in the heatmap
        if department:
            jobs = self.job_architecture.get_jobs_by_department(department)
            job_ids = [job.job_id for job in jobs]
        else:
            job_ids = list(self.job_architecture.jobs.keys())
        
        # Create similarity calculator
        calculator = CosineSimilarityCalculator(
            vectorizer=None,  # Will be created by the calculator
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
        
        # Calculate similarity matrix
        similarity_matrix, matrix_job_ids = calculator.calculate_similarity_matrix("job")
        
        # Filter jobs if necessary
        if department or (top_n and top_n < len(job_ids)):
            # Get indices of jobs to include
            indices = [i for i, job_id in enumerate(matrix_job_ids) if job_id in job_ids]
            
            # Limit to top_n if specified
            if top_n and top_n < len(indices):
                indices = indices[:top_n]
            
            # Filter matrix and job IDs
            similarity_matrix = similarity_matrix[np.ix_(indices, indices)]
            matrix_job_ids = [matrix_job_ids[i] for i in indices]
        
        # Get job titles for labels
        job_titles = [self.job_architecture.jobs[job_id].title for job_id in matrix_job_ids]
        
        # Create default configuration if not provided
        if config is None:
            config = HeatmapConfig(
                title="Job Similarity Heatmap",
                cmap="viridis",
                mask_diagonal=True,
                vmin=0.0,
                vmax=1.0
            )
        
        # Generate default file path if not provided
        if file_path is None:
            dept_suffix = f"_{department}" if department else ""
            file_path = f"job_similarity_heatmap{dept_suffix}.png"
        
        # Generate heatmap
        return self.heatmap_generator.generate_heatmap(
            data=similarity_matrix,
            row_labels=job_titles,
            col_labels=job_titles,
            config=config,
            file_path=file_path
        )
    
    def generate_employee_similarity_heatmap(
        self,
        department: Optional[str] = None,
        top_n: Optional[int] = None,
        config: Optional[HeatmapConfig] = None,
        file_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Generate a heatmap of employee similarities.
        
        Args:
            department: Department to filter by (all departments if None)
            top_n: Number of top employees to include (all employees if None)
            config: Heatmap configuration
            file_path: Path to save the heatmap image
            
        Returns:
            Matplotlib figure
            
        Raises:
            ValueError: If employee database is not set
            ImportError: If the similarity module is not available
        """
        if not self.employee_database:
            raise ValueError("Employee database not set")
        
        try:
            from ..similarity.cosine import CosineSimilarityCalculator
        except ImportError:
            raise ImportError("Similarity module not available")
        
        # Get employees to include in the heatmap
        if department:
            employee_ids = []
            for employee_id, employee in self.employee_database.employees.items():
                job = self.job_architecture.jobs.get(employee.current_job)
                if job and job.department == department:
                    employee_ids.append(employee_id)
        else:
            employee_ids = list(self.employee_database.employees.keys())
        
        # Create similarity calculator
        calculator = CosineSimilarityCalculator(
            vectorizer=None,  # Will be created by the calculator
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
        
        # Calculate similarity matrix
        similarity_matrix, matrix_employee_ids = calculator.calculate_similarity_matrix("employee")
        
        # Filter employees if necessary
        if department or (top_n and top_n < len(employee_ids)):
            # Get indices of employees to include
            indices = [i for i, emp_id in enumerate(matrix_employee_ids) if emp_id in employee_ids]
            
            # Limit to top_n if specified
            if top_n and top_n < len(indices):
                indices = indices[:top_n]
            
            # Filter matrix and employee IDs
            similarity_matrix = similarity_matrix[np.ix_(indices, indices)]
            matrix_employee_ids = [matrix_employee_ids[i] for i in indices]
        
        # Get employee names for labels
        employee_names = [self.employee_database.employees[emp_id].name for emp_id in matrix_employee_ids]
        
        # Create default configuration if not provided
        if config is None:
            config = HeatmapConfig(
                title="Employee Similarity Heatmap",
                cmap="viridis",
                mask_diagonal=True,
                vmin=0.0,
                vmax=1.0
            )
        
        # Generate default file path if not provided
        if file_path is None:
            dept_suffix = f"_{department}" if department else ""
            file_path = f"employee_similarity_heatmap{dept_suffix}.png"
        
        # Generate heatmap
        return self.heatmap_generator.generate_heatmap(
            data=similarity_matrix,
            row_labels=employee_names,
            col_labels=employee_names,
            config=config,
            file_path=file_path
        )


class GapAnalysisHeatmapGenerator:
    """
    Generator for creating gap analysis heatmaps.
    
    Attributes:
        heatmap_generator: Basic heatmap generator
        skill_taxonomy: Skill taxonomy
        job_architecture: Job architecture
        employee_database: Employee database
    """
    
    def __init__(
        self,
        skill_taxonomy: SkillTaxonomy,
        job_architecture: JobArchitecture,
        employee_database: EmployeeDatabase,
        output_dir: Optional[str] = None
    ):
        """
        Initialize the gap analysis heatmap generator.
        
        Args:
            skill_taxonomy: Skill taxonomy
            job_architecture: Job architecture
            employee_database: Employee database
            output_dir: Directory for output files
        """
        self.heatmap_generator = HeatmapGenerator(output_dir)
        self.skill_taxonomy = skill_taxonomy
        self.job_architecture = job_architecture
        self.employee_database = employee_database
    
    def generate_skill_gap_heatmap(
        self,
        employee_ids: List[str],
        job_ids: List[str],
        metric: str = "match_percentage",
        config: Optional[HeatmapConfig] = None,
        file_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Generate a heatmap of skill gaps between employees and jobs.
        
        Args:
            employee_ids: IDs of employees to include
            job_ids: IDs of jobs to include
            metric: Metric to visualize ('match_percentage', 'development_effort', or 'reskilling_difficulty')
            config: Heatmap configuration
            file_path: Path to save the heatmap image
            
        Returns:
            Matplotlib figure
            
        Raises:
            ValueError: If any employee ID or job ID is not found
            ImportError: If the gap analysis module is not available
        """
        try:
            from ..analysis.gap import SkillGapAnalyzer
        except ImportError:
            raise ImportError("Gap analysis module not available")
        
        # Validate employee IDs
        for employee_id in employee_ids:
            if employee_id not in self.employee_database.employees:
                raise ValueError(f"Employee with ID {employee_id} not found")
        
        # Validate job IDs
        for job_id in job_ids:
            if job_id not in self.job_architecture.jobs:
                raise ValueError(f"Job with ID {job_id} not found")
        
        # Create skill gap analyzer
        analyzer = SkillGapAnalyzer(
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
        
        # Calculate gap matrix
        gap_matrix = np.zeros((len(employee_ids), len(job_ids)))
        
        for i, employee_id in enumerate(employee_ids):
            for j, job_id in enumerate(job_ids):
                try:
                    gap_analysis = analyzer.analyze_employee_job_gap(employee_id, job_id)
                    
                    if metric == "match_percentage":
                        gap_matrix[i, j] = gap_analysis.skill_match_percentage
                    elif metric == "development_effort":
                        gap_matrix[i, j] = gap_analysis.total_development_effort
                    elif metric == "reskilling_difficulty":
                        gap_matrix[i, j] = gap_analysis.reskilling_difficulty
                    else:
                        raise ValueError(f"Invalid metric: {metric}")
                except Exception as e:
                    print(f"Error analyzing gap for {employee_id} and {job_id}: {e}")
                    gap_matrix[i, j] = np.nan
        
        # Get employee names and job titles for labels
        employee_names = [self.employee_database.employees[emp_id].name for emp_id in employee_ids]
        job_titles = [self.job_architecture.jobs[job_id].title for job_id in job_ids]
        
        # Create default configuration if not provided
        if config is None:
            if metric == "match_percentage":
                title = "Skill Match Percentage Heatmap"
                cmap = "viridis"
                vmin = 0.0
                vmax = 100.0
            elif metric == "development_effort":
                title = "Development Effort Heatmap"
                cmap = "YlOrRd"
                vmin = 0.0
                vmax = None
            elif metric == "reskilling_difficulty":
                title = "Reskilling Difficulty Heatmap"
                cmap = "YlOrRd"
                vmin = 1.0
                vmax = 5.0
            
            config = HeatmapConfig(
                title=title,
                cmap=cmap,
                vmin=vmin,
                vmax=vmax
            )
        
        # Generate default file path if not provided
        if file_path is None:
            file_path = f"skill_gap_heatmap_{metric}.png"
        
        # Generate heatmap
        return self.heatmap_generator.generate_heatmap(
            data=gap_matrix,
            row_labels=employee_names,
            col_labels=job_titles,
            config=config,
            file_path=file_path
        )
    
    def generate_workforce_gap_heatmap(
        self,
        departments: Optional[List[str]] = None,
        min_gap_threshold: float = 2.0,
        max_skills: int = 20,
        config: Optional[HeatmapConfig] = None,
        file_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Generate a heatmap of workforce skill gaps across departments.
        
        Args:
            departments: Departments to include (all departments if None)
            min_gap_threshold: Minimum gap threshold to consider critical
            max_skills: Maximum number of skills to include
            config: Heatmap configuration
            file_path: Path to save the heatmap image
            
        Returns:
            Matplotlib figure
            
        Raises:
            ImportError: If the gap analysis module is not available
        """
        try:
            from ..analysis.gap import TeamGapAnalyzer
        except ImportError:
            raise ImportError("Gap analysis module not available")
        
        # Get departments if not provided
        if departments is None:
            departments = list(self.job_architecture.departments)
        
        # Create team gap analyzer
        analyzer = TeamGapAnalyzer(
            skill_taxonomy=self.skill_taxonomy,
            job_architecture=self.job_architecture,
            employee_database=self.employee_database
        )
        
        # Initialize data for heatmap
        skill_gaps = {}
        
        # Identify critical skill gaps for each department
        for department in departments:
            critical_gaps = analyzer.identify_critical_skill_gaps(department, min_gap_threshold)
            
            # Skip if no critical gaps found
            if critical_gaps.empty:
                continue
            
            # Store gaps for this department
            for _, row in critical_gaps.iterrows():
                skill_id = row["skill_id"]
                if skill_id not in skill_gaps:
                    skill_gaps[skill_id] = {
                        "skill_name": row["skill_name"],
                        "gaps": {},
                        "criticality": 0
                    }
                
                # Store gap and update total criticality
                skill_gaps[skill_id]["gaps"][department] = row["proficiency_gap"]
                skill_gaps[skill_id]["criticality"] += row["criticality"]
        
        # Sort skills by criticality and limit to max_skills
        top_skills = sorted(skill_gaps.items(), key=lambda x: x[1]["criticality"], reverse=True)[:max_skills]
        
        # Create matrix for heatmap
        skill_names = [skill[1]["skill_name"] for skill in top_skills]
        matrix = np.zeros((len(skill_names), len(departments)))
        
        for i, (skill_id, skill_data) in enumerate(top_skills):
            for j, department in enumerate(departments):
                matrix[i, j] = skill_data["gaps"].get(department, 0.0)
        
        # Create default configuration if not provided
        if config is None:
            config = HeatmapConfig(
                title="Workforce Skill Gap Heatmap",
                cmap="YlOrRd",
                vmin=0.0,
                vmax=None,
                figsize=(12, len(skill_names) * 0.5 + 2)
            )
        
        # Generate default file path if not provided
        if file_path is None:
            file_path = "workforce_gap_heatmap.png"
        
        # Generate heatmap
        return self.heatmap_generator.generate_heatmap(
            data=matrix,
            row_labels=skill_names,
            col_labels=departments,
            config=config,
            file_path=file_path
        )
