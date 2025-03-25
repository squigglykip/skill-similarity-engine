"""
Main visualisation module for the skill similarity engine.

This module provides a unified interface for generating various visualisations
including heatmaps, networks, and radar charts.
"""

import os
from typing import Dict, List, Optional, Set, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..config.settings import get_config
from ..models.employees import EmployeeDatabase
from ..models.jobs import JobArchitecture
from ..models.skills import SkillTaxonomy
from .heatmaps import (
    GapAnalysisHeatmapGenerator,
    HeatmapConfig,
    SimilarityHeatmapGenerator,
)
from .hexbin import HexbinConfig, HexbinGenerator
from .reports import DataExporter, ReportConfig


class VisualisationManager:
    """
    Main manager for generating different visualisations.
    
    This class provides a unified interface for generating various visualisations
    including heatmaps, networks, and radar charts.
    
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
        Initialize the visualisation manager.
        
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
        
        # Initialize visualisation generators
        self._similarity_heatmap_generator = SimilarityHeatmapGenerator(
            skill_taxonomy=skill_taxonomy,
            job_architecture=job_architecture,
            employee_database=employee_database,
            output_dir=self.output_dir
        )
        
        self._hexbin_generator = HexbinGenerator(
            skill_taxonomy=skill_taxonomy,
            job_architecture=job_architecture,
            employee_database=employee_database,
            output_dir=self.output_dir
        )
        
        self._data_exporter = DataExporter(
            skill_taxonomy=skill_taxonomy,
            job_architecture=job_architecture,
            employee_database=employee_database,
            output_dir=self.output_dir
        )
        
        if employee_database:
            self._gap_heatmap_generator = GapAnalysisHeatmapGenerator(
                skill_taxonomy=skill_taxonomy,
                job_architecture=job_architecture,
                employee_database=employee_database,
                output_dir=self.output_dir
            )
        else:
            self._gap_heatmap_generator = None
    
    def generate_job_similarity_heatmap(
        self,
        department: Optional[str] = None,
        top_n: Optional[int] = None,
        cluster: bool = False,
        save_to_file: bool = True,
        file_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Generate a heatmap of job similarities.
        
        Args:
            department: Department to filter by (all departments if None)
            top_n: Number of top jobs to include (all jobs if None)
            cluster: Whether to cluster similar jobs together
            save_to_file: Whether to save the visualisation to a file
            file_path: Path to save the heatmap image
            
        Returns:
            Matplotlib figure
        """
        config = HeatmapConfig(
            title="Job Similarity Heatmap",
            cmap="viridis",
            mask_diagonal=True,
            cluster=cluster,
            vmin=0.0,
            vmax=1.0
        )
        
        return self._similarity_heatmap_generator.generate_job_similarity_heatmap(
            department=department,
            top_n=top_n,
            config=config,
            file_path=file_path if save_to_file else None
        )
    
    def generate_employee_similarity_heatmap(
        self,
        department: Optional[str] = None,
        top_n: Optional[int] = None,
        cluster: bool = False,
        save_to_file: bool = True,
        file_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Generate a heatmap of employee similarities.
        
        Args:
            department: Department to filter by (all departments if None)
            top_n: Number of top employees to include (all employees if None)
            cluster: Whether to cluster similar employees together
            save_to_file: Whether to save the visualisation to a file
            file_path: Path to save the heatmap image
            
        Returns:
            Matplotlib figure
            
        Raises:
            ValueError: If employee database is not set
        """
        if not self.employee_database:
            raise ValueError("Employee database not set")
        
        config = HeatmapConfig(
            title="Employee Similarity Heatmap",
            cmap="viridis",
            mask_diagonal=True,
            cluster=cluster,
            vmin=0.0,
            vmax=1.0
        )
        
        return self._similarity_heatmap_generator.generate_employee_similarity_heatmap(
            department=department,
            top_n=top_n,
            config=config,
            file_path=file_path if save_to_file else None
        )
    
    def generate_skill_gap_heatmap(
        self,
        employee_ids: List[str],
        job_ids: List[str],
        metric: str = "match_percentage",
        save_to_file: bool = True,
        file_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Generate a heatmap of skill gaps between employees and jobs.
        
        Args:
            employee_ids: IDs of employees to include
            job_ids: IDs of jobs to include
            metric: Metric to visualize ('match_percentage', 'development_effort', or 'reskilling_difficulty')
            save_to_file: Whether to save the visualisation to a file
            file_path: Path to save the heatmap image
            
        Returns:
            Matplotlib figure
            
        Raises:
            ValueError: If employee database is not set
        """
        if not self._gap_heatmap_generator:
            raise ValueError("Employee database not set")
        
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
        else:
            raise ValueError(f"Invalid metric: {metric}")
        
        config = HeatmapConfig(
            title=title,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax
        )
        
        return self._gap_heatmap_generator.generate_skill_gap_heatmap(
            employee_ids=employee_ids,
            job_ids=job_ids,
            metric=metric,
            config=config,
            file_path=file_path if save_to_file else None
        )
    
    def generate_workforce_gap_heatmap(
        self,
        departments: Optional[List[str]] = None,
        min_gap_threshold: float = 2.0,
        max_skills: int = 20,
        save_to_file: bool = True,
        file_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Generate a heatmap of workforce skill gaps across departments.
        
        Args:
            departments: Departments to include (all departments if None)
            min_gap_threshold: Minimum gap threshold to consider critical
            max_skills: Maximum number of skills to include
            save_to_file: Whether to save the visualisation to a file
            file_path: Path to save the heatmap image
            
        Returns:
            Matplotlib figure
            
        Raises:
            ValueError: If employee database is not set
        """
        if not self._gap_heatmap_generator:
            raise ValueError("Employee database not set")
        
        config = HeatmapConfig(
            title="Workforce Skill Gap Heatmap",
            cmap="YlOrRd",
            vmin=0.0,
            vmax=None
        )
        
        return self._gap_heatmap_generator.generate_workforce_gap_heatmap(
            departments=departments,
            min_gap_threshold=min_gap_threshold,
            max_skills=max_skills,
            config=config,
            file_path=file_path if save_to_file else None
        )
    
    def generate_job_similarity_hexbin(
        self,
        departments: Optional[List[str]] = None,
        reduction_method: str = "umap",
        metric: str = "similarity",
        save_to_file: bool = True,
        file_path: Optional[str] = None,
        export_data: bool = True,
        export_path: Optional[str] = None
    ) -> Tuple[plt.Figure, pd.DataFrame]:
        """
        Generate a hexbin plot for job similarities.
        
        This method is optimised for large datasets by using dimensionality reduction
        and hexbin aggregation to visualise job similarities.
        
        Args:
            departments: Departments to filter by (all departments if None)
            reduction_method: Dimensionality reduction method ('pca', 'tsne', 'umap')
            metric: Metric to visualize ('similarity', 'skill_count', 'hierarchy_level')
            save_to_file: Whether to save the visualisation to a file
            file_path: Path to save the hexbin image
            export_data: Whether to export data for Power BI
            export_path: Path to save the exported data
            
        Returns:
            Tuple of (matplotlib figure, DataFrame with projection data)
        """
        config = HexbinConfig(
            title="Job Similarity Hexbin",
            cmap="viridis",
            gridsize=50
        )
        
        return self._hexbin_generator.generate_job_similarity_hexbin(
            departments=departments,
            reduction_method=reduction_method,
            metric=metric,
            config=config,
            save_to_file=save_to_file,
            file_path=file_path,
            export_data=export_data,
            export_path=export_path
        )
    
    def generate_employee_similarity_hexbin(
        self,
        departments: Optional[List[str]] = None,
        reduction_method: str = "umap",
        metric: str = "similarity",
        save_to_file: bool = True,
        file_path: Optional[str] = None,
        export_data: bool = True,
        export_path: Optional[str] = None
    ) -> Tuple[plt.Figure, pd.DataFrame]:
        """
        Generate a hexbin plot for employee similarities.
        
        This method is optimised for large datasets by using dimensionality reduction
        and hexbin aggregation to visualise employee similarities.
        
        Args:
            departments: Departments to filter by (all departments if None)
            reduction_method: Dimensionality reduction method ('pca', 'tsne', 'umap')
            metric: Metric to visualize ('similarity', 'skill_count', 'tenure')
            save_to_file: Whether to save the visualisation to a file
            file_path: Path to save the hexbin image
            export_data: Whether to export data for Power BI
            export_path: Path to save the exported data
            
        Returns:
            Tuple of (matplotlib figure, DataFrame with projection data)
            
        Raises:
            ValueError: If employee database is not set
        """
        if not self.employee_database:
            raise ValueError("Employee database not set")
        
        config = HexbinConfig(
            title="Employee Similarity Hexbin",
            cmap="plasma",
            gridsize=50
        )
        
        return self._hexbin_generator.generate_employee_similarity_hexbin(
            departments=departments,
            reduction_method=reduction_method,
            metric=metric,
            config=config,
            save_to_file=save_to_file,
            file_path=file_path,
            export_data=export_data,
            export_path=export_path
        )
    
    def generate_skill_distribution_hexbin(
        self,
        skill_ids: Optional[List[str]] = None,
        skill_categories: Optional[List[str]] = None,
        entity_type: str = "job",
        reduction_method: str = "umap",
        save_to_file: bool = True,
        file_path: Optional[str] = None,
        export_data: bool = True,
        export_path: Optional[str] = None
    ) -> Tuple[plt.Figure, pd.DataFrame]:
        """
        Generate a hexbin plot showing skill distribution across jobs or employees.
        
        This method is optimised for large datasets by using dimensionality reduction
        and hexbin aggregation to visualise skill distributions.
        
        Args:
            skill_ids: Skill IDs to include (all skills if None)
            skill_categories: Skill categories to include (all categories if None)
            entity_type: Type of entity to visualize ('job' or 'employee')
            reduction_method: Dimensionality reduction method ('pca', 'tsne', 'umap')
            save_to_file: Whether to save the visualisation to a file
            file_path: Path to save the hexbin image
            export_data: Whether to export data for Power BI
            export_path: Path to save the exported data
            
        Returns:
            Tuple of (matplotlib figure, DataFrame with projection data)
            
        Raises:
            ValueError: If employee database is not set and entity_type is 'employee'
        """
        if entity_type == "employee" and not self.employee_database:
            raise ValueError("Employee database not set")
        
        config = HexbinConfig(
            title=f"Skill Distribution Hexbin ({entity_type.title()}s)",
            cmap="viridis",
            gridsize=50
        )
        
        return self._hexbin_generator.generate_skill_distribution_hexbin(
            skill_ids=skill_ids,
            skill_categories=skill_categories,
            reduction_method=reduction_method,
            entity_type=entity_type,
            config=config,
            save_to_file=save_to_file,
            file_path=file_path,
            export_data=export_data,
            export_path=export_path
        )
    
    def generate_skill_gap_hexbin(
        self,
        target_job_ids: List[str],
        reduction_method: str = "umap",
        max_employees: int = 5000,
        save_to_file: bool = True,
        file_path: Optional[str] = None,
        export_data: bool = True,
        export_path: Optional[str] = None
    ) -> Tuple[plt.Figure, pd.DataFrame]:
        """
        Generate a hexbin plot showing skill gaps between employees and target jobs.
        
        This method is optimised for large datasets by using dimensionality reduction
        and hexbin aggregation to visualise skill gaps.
        
        Args:
            target_job_ids: IDs of target jobs to compare against
            reduction_method: Dimensionality reduction method ('pca', 'tsne', 'umap')
            max_employees: Maximum number of employees to include
            save_to_file: Whether to save the visualisation to a file
            file_path: Path to save the hexbin image
            export_data: Whether to export data for Power BI
            export_path: Path to save the exported data
            
        Returns:
            Tuple of (matplotlib figure, DataFrame with projection data)
            
        Raises:
            ValueError: If employee database is not set
        """
        if not self.employee_database:
            raise ValueError("Employee database not set")
        
        config = HexbinConfig(
            title="Skill Gap Hexbin",
            cmap="coolwarm",
            gridsize=50
        )
        
        return self._hexbin_generator.generate_skill_gap_hexbin(
            target_job_ids=target_job_ids,
            reduction_method=reduction_method,
            max_employees=max_employees,
            config=config,
            save_to_file=save_to_file,
            file_path=file_path,
            export_data=export_data,
            export_path=export_path
        )
    
    # Power BI Export Methods
    
    def export_job_similarity_matrix(
        self,
        departments: Optional[List[str]] = None,
        threshold: Optional[float] = None,
        format: str = "csv",
        include_metadata: bool = True,
        add_opportunity_flags: bool = True,
        high_similarity_threshold: Optional[float] = None,
        output_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Export job similarity matrix data for Power BI.
        
        Args:
            departments: Departments to filter by (all departments if None)
            threshold: Similarity threshold (export all similarities if None)
            format: Export format ('csv', 'excel', or 'json')
            include_metadata: Whether to include metadata columns
            add_opportunity_flags: Whether to add opportunity flag columns
            high_similarity_threshold: Threshold for high similarity (0.0-1.0)
                If None, uses the value from the global config
            output_path: Path to save the exported data
            
        Returns:
            DataFrame with job similarity data
        """
        config = ReportConfig(
            include_metadata=include_metadata,
            format=format,
            include_names=True,
            add_opportunity_flags=add_opportunity_flags,
            high_similarity_threshold=high_similarity_threshold
        )
        
        return self._data_exporter.export_job_similarity_matrix(
            departments=departments,
            threshold=threshold,
            config=config,
            output_path=output_path
        )
    
    def export_employee_similarity_matrix(
        self,
        departments: Optional[List[str]] = None,
        threshold: Optional[float] = None,
        format: str = "csv",
        include_metadata: bool = True,
        add_opportunity_flags: bool = True,
        high_similarity_threshold: Optional[float] = None,
        output_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Export employee similarity matrix data for Power BI.
        
        Args:
            departments: Departments to filter by (all departments if None)
            threshold: Similarity threshold (export all similarities if None)
            format: Export format ('csv', 'excel', or 'json')
            include_metadata: Whether to include metadata columns
            add_opportunity_flags: Whether to add opportunity flag columns
            high_similarity_threshold: Threshold for high similarity (0.0-1.0)
                If None, uses the value from the global config
            output_path: Path to save the exported data
            
        Returns:
            DataFrame with employee similarity data
            
        Raises:
            ValueError: If employee database is not set
        """
        config = ReportConfig(
            include_metadata=include_metadata,
            format=format,
            include_names=True,
            add_opportunity_flags=add_opportunity_flags,
            high_similarity_threshold=high_similarity_threshold
        )
        
        return self._data_exporter.export_employee_similarity_matrix(
            departments=departments,
            threshold=threshold,
            config=config,
            output_path=output_path
        )
    
    def export_skill_gap_analysis(
        self,
        employee_ids: List[str],
        job_ids: List[str],
        format: str = "csv",
        include_metadata: bool = True,
        include_descriptions: bool = False,
        add_opportunity_flags: bool = True,
        low_gap_threshold: Optional[float] = None,
        output_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Export skill gap analysis data for Power BI.
        
        Args:
            employee_ids: IDs of employees to include
            job_ids: IDs of jobs to include
            format: Export format ('csv', 'excel', or 'json')
            include_metadata: Whether to include metadata columns
            include_descriptions: Whether to include detailed skill information
            add_opportunity_flags: Whether to add opportunity flag columns
            low_gap_threshold: Threshold for low skill gap (development effort)
                If None, uses the value from the global config
            output_path: Path to save the exported data
            
        Returns:
            DataFrame with skill gap data
            
        Raises:
            ValueError: If employee database is not set
        """
        config = ReportConfig(
            include_metadata=include_metadata,
            format=format,
            include_names=True,
            include_descriptions=include_descriptions,
            add_opportunity_flags=add_opportunity_flags,
            low_gap_threshold=low_gap_threshold
        )
        
        return self._data_exporter.export_skill_gap_analysis(
            employee_ids=employee_ids,
            job_ids=job_ids,
            config=config,
            output_path=output_path
        )
    
    def export_workforce_planning_data(
        self,
        departments: Optional[List[str]] = None,
        format: str = "csv",
        include_metadata: bool = True,
        add_opportunity_flags: bool = True,
        output_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Export workforce planning data for Power BI.
        
        Args:
            departments: Departments to filter by (all departments if None)
            format: Export format ('csv', 'excel', or 'json')
            include_metadata: Whether to include metadata columns
            add_opportunity_flags: Whether to add opportunity flag columns
            output_path: Path to save the exported data
            
        Returns:
            DataFrame with workforce planning data
            
        Raises:
            ValueError: If employee database is not set
        """
        config = ReportConfig(
            include_metadata=include_metadata,
            format=format,
            include_names=True,
            add_opportunity_flags=add_opportunity_flags
        )
        
        return self._data_exporter.export_workforce_planning_data(
            departments=departments,
            config=config,
            output_path=output_path
        )
    
    def export_skill_vectors(
        self,
        entity_type: str = "job",
        departments: Optional[List[str]] = None,
        format: str = "csv",
        include_metadata: bool = True,
        output_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Export skill vector data for Power BI.
        
        Args:
            entity_type: Type of entity to export vectors for ('job' or 'employee')
            departments: Departments to filter by (all departments if None)
            format: Export format ('csv', 'excel', or 'json')
            include_metadata: Whether to include metadata columns
            output_path: Path to save the exported data
            
        Returns:
            DataFrame with skill vector data
            
        Raises:
            ValueError: If employee database is not set and entity_type is 'employee'
        """
        config = ReportConfig(
            include_metadata=include_metadata,
            format=format,
            include_names=True
        )
        
        return self._data_exporter.export_skill_vectors(
            entity_type=entity_type,
            departments=departments,
            config=config,
            output_path=output_path
        )


# Additional visualisation classes to be implemented:
#
# class NetworkVisualizer:
#     """Creates network graphs showing relationships between skills, jobs and employees."""
#     pass
#
# class RadarChartGenerator:
#     """Creates radar/spider charts comparing skill profiles."""
#     pass
#
# class CareerPathVisualizer:
#     """Visualizes career paths and transitions between jobs."""
#     pass 