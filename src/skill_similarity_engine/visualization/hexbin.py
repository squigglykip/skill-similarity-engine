"""
Hexbin visualization module for large-scale skill similarity data.

This module provides functionality to create hexbin plots and outputs tabular data for Power BI.
"""

import os
from typing import Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from umap import UMAP

from ..config.settings import get_config
from ..models.employees import EmployeeDatabase
from ..models.jobs import JobArchitecture
from ..models.skills import SkillTaxonomy


class HexbinConfig:
    """Configuration for hexbin plots."""
    
    def __init__(
        self,
        title: str = "Skill Similarity Hexbin",
        cmap: str = "viridis",
        gridsize: int = 50,
        bins: Optional[str] = "log",
        colorbar: bool = True,
        edgecolor: str = "none",
        alpha: float = 0.7,
        figsize: Tuple[int, int] = (10, 8),
    ):
        """
        Initialize the hexbin configuration.
        
        Args:
            title: Plot title
            cmap: Colormap name
            gridsize: Number of hexagons in the grid
            bins: Binning method ('log', 'linear', or None)
            colorbar: Whether to display a colorbar
            edgecolor: Edge color of hexagons
            alpha: Transparency of hexagons
            figsize: Figure size (width, height) in inches
        """
        self.title = title
        self.cmap = cmap
        self.gridsize = gridsize
        self.bins = bins
        self.colorbar = colorbar
        self.edgecolor = edgecolor
        self.alpha = alpha
        self.figsize = figsize


class DimensionalityReduction:
    """Methods for dimensionality reduction to create 2D projections."""
    
    @staticmethod
    def pca(
        data: np.ndarray,
        n_components: int = 2,
        random_state: int = 42
    ) -> np.ndarray:
        """
        Reduce dimensions using Principal Component Analysis.
        
        Args:
            data: Input data matrix
            n_components: Number of dimensions to reduce to
            random_state: Random seed for reproducibility
            
        Returns:
            Reduced data matrix
        """
        pca = PCA(n_components=n_components, random_state=random_state)
        return pca.fit_transform(data)
    
    @staticmethod
    def tsne(
        data: np.ndarray,
        n_components: int = 2,
        perplexity: float = 30.0,
        random_state: int = 42
    ) -> np.ndarray:
        """
        Reduce dimensions using t-SNE.
        
        Args:
            data: Input data matrix
            n_components: Number of dimensions to reduce to
            perplexity: t-SNE perplexity parameter
            random_state: Random seed for reproducibility
            
        Returns:
            Reduced data matrix
        """
        tsne = TSNE(
            n_components=n_components,
            perplexity=perplexity,
            random_state=random_state
        )
        return tsne.fit_transform(data)
    
    @staticmethod
    def umap(
        data: np.ndarray,
        n_components: int = 2,
        n_neighbors: int = 15,
        min_dist: float = 0.1,
        random_state: int = 42
    ) -> np.ndarray:
        """
        Reduce dimensions using UMAP.
        
        Args:
            data: Input data matrix
            n_components: Number of dimensions to reduce to
            n_neighbors: Number of neighbors to consider
            min_dist: Minimum distance parameter
            random_state: Random seed for reproducibility
            
        Returns:
            Reduced data matrix
        """
        umap = UMAP(
            n_components=n_components,
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            random_state=random_state
        )
        return umap.fit_transform(data)


class HexbinGenerator:
    """
    Generator for hexbin visualisations of large-scale skill data.
    
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
        Initialize the hexbin generator.
        
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
        self.dim_reduction = DimensionalityReduction()
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def generate_job_similarity_hexbin(
        self,
        departments: Optional[List[str]] = None,
        reduction_method: str = "umap",
        metric: str = "similarity",
        config: Optional[HexbinConfig] = None,
        save_to_file: bool = True,
        file_path: Optional[str] = None,
        export_data: bool = True,
        export_path: Optional[str] = None
    ) -> Tuple[plt.Figure, pd.DataFrame]:
        """
        Generate a hexbin plot for job similarities.
        
        Args:
            departments: Departments to filter by (all departments if None)
            reduction_method: Dimensionality reduction method ('pca', 'tsne', 'umap')
            metric: Metric to visualize ('similarity', 'skill_count', 'hierarchy_level')
            config: Hexbin configuration
            save_to_file: Whether to save the visualization to a file
            file_path: Path to save the hexbin image
            export_data: Whether to export data for Power BI
            export_path: Path to save the exported data
            
        Returns:
            Tuple of (matplotlib figure, DataFrame with projection data)
        """
        # Use default config if none provided
        if config is None:
            config = HexbinConfig(
                title="Job Similarity Hexbin",
                cmap="viridis",
                gridsize=50
            )
        
        # Get job skill vectors
        job_vectors = []
        job_ids = []
        job_titles = []
        job_depts = []
        
        for job_id, job in self.job_architecture.jobs.items():
            if departments and job.department not in departments:
                continue
            
            job_vectors.append(job.skill_vector.to_array())
            job_ids.append(job_id)
            job_titles.append(job.title)
            job_depts.append(job.department)
        
        if not job_vectors:
            raise ValueError("No jobs found matching the criteria")
        
        # Convert to numpy arrays
        job_vectors_array = np.array(job_vectors)
        
        # Apply dimensionality reduction
        if reduction_method == "pca":
            reduced_data = self.dim_reduction.pca(job_vectors_array)
        elif reduction_method == "tsne":
            reduced_data = self.dim_reduction.tsne(job_vectors_array)
        elif reduction_method == "umap":
            reduced_data = self.dim_reduction.umap(job_vectors_array)
        else:
            raise ValueError(f"Invalid reduction method: {reduction_method}")
        
        # Create dataframe with projection data
        projection_df = pd.DataFrame({
            "job_id": job_ids,
            "job_title": job_titles,
            "department": job_depts,
            "x": reduced_data[:, 0],
            "y": reduced_data[:, 1]
        })
        
        # Calculate metric values
        if metric == "similarity":
            # Already captured in the spatial proximity
            projection_df["metric_value"] = 1.0
        elif metric == "skill_count":
            projection_df["metric_value"] = [
                len(self.job_architecture.jobs[job_id].skills)
                for job_id in job_ids
            ]
        elif metric == "hierarchy_level":
            projection_df["metric_value"] = [
                self.job_architecture.jobs[job_id].level
                for job_id in job_ids
            ]
        else:
            raise ValueError(f"Invalid metric: {metric}")
        
        # Generate hexbin plot
        fig, ax = plt.subplots(figsize=config.figsize)
        
        # Use hexbin to plot the data
        hb = ax.hexbin(
            projection_df["x"],
            projection_df["y"],
            C=projection_df["metric_value"] if metric != "similarity" else None,
            gridsize=config.gridsize,
            cmap=config.cmap,
            bins=config.bins,
            edgecolor=config.edgecolor,
            alpha=config.alpha
        )
        
        if config.colorbar:
            cb = plt.colorbar(hb, ax=ax)
            cb.set_label(metric.replace("_", " ").title())
        
        ax.set_title(config.title)
        ax.set_xlabel(f"Dimension 1 ({reduction_method.upper()})")
        ax.set_ylabel(f"Dimension 2 ({reduction_method.upper()})")
        
        # Save plot to file if requested
        if save_to_file:
            output_file = file_path or os.path.join(
                self.output_dir, f"job_similarity_hexbin_{reduction_method}.png"
            )
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
        
        # Export data for Power BI if requested
        if export_data:
            output_data = export_path or os.path.join(
                self.output_dir, f"job_similarity_hexbin_data_{reduction_method}.csv"
            )
            projection_df.to_csv(output_data, index=False)
        
        return fig, projection_df
    
    def generate_employee_similarity_hexbin(
        self,
        departments: Optional[List[str]] = None,
        reduction_method: str = "umap",
        metric: str = "similarity",
        config: Optional[HexbinConfig] = None,
        save_to_file: bool = True,
        file_path: Optional[str] = None,
        export_data: bool = True,
        export_path: Optional[str] = None
    ) -> Tuple[plt.Figure, pd.DataFrame]:
        """
        Generate a hexbin plot for employee similarities.
        
        Args:
            departments: Departments to filter by (all departments if None)
            reduction_method: Dimensionality reduction method ('pca', 'tsne', 'umap')
            metric: Metric to visualize ('similarity', 'skill_count', 'tenure')
            config: Hexbin configuration
            save_to_file: Whether to save the visualization to a file
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
        
        # Use default config if none provided
        if config is None:
            config = HexbinConfig(
                title="Employee Similarity Hexbin",
                cmap="plasma",
                gridsize=50
            )
        
        # Get employee skill vectors
        employee_vectors = []
        employee_ids = []
        employee_names = []
        employee_depts = []
        employee_jobs = []
        
        for emp_id, employee in self.employee_database.employees.items():
            if departments and employee.department not in departments:
                continue
            
            employee_vectors.append(employee.skill_vector.to_array())
            employee_ids.append(emp_id)
            employee_names.append(employee.name)
            employee_depts.append(employee.department)
            employee_jobs.append(employee.job_id)
        
        if not employee_vectors:
            raise ValueError("No employees found matching the criteria")
        
        # Convert to numpy arrays
        employee_vectors_array = np.array(employee_vectors)
        
        # Apply dimensionality reduction
        if reduction_method == "pca":
            reduced_data = self.dim_reduction.pca(employee_vectors_array)
        elif reduction_method == "tsne":
            reduced_data = self.dim_reduction.tsne(employee_vectors_array)
        elif reduction_method == "umap":
            reduced_data = self.dim_reduction.umap(employee_vectors_array)
        else:
            raise ValueError(f"Invalid reduction method: {reduction_method}")
        
        # Create dataframe with projection data
        projection_df = pd.DataFrame({
            "employee_id": employee_ids,
            "employee_name": employee_names,
            "department": employee_depts,
            "job_id": employee_jobs,
            "job_title": [
                self.job_architecture.jobs.get(job_id, {"title": "Unknown"}).title
                if isinstance(self.job_architecture.jobs.get(job_id), dict)
                else self.job_architecture.jobs.get(job_id).title if job_id in self.job_architecture.jobs else "Unknown"
                for job_id in employee_jobs
            ],
            "x": reduced_data[:, 0],
            "y": reduced_data[:, 1]
        })
        
        # Calculate metric values
        if metric == "similarity":
            # Already captured in the spatial proximity
            projection_df["metric_value"] = 1.0
        elif metric == "skill_count":
            projection_df["metric_value"] = [
                len(self.employee_database.employees[emp_id].skills)
                for emp_id in employee_ids
            ]
        elif metric == "tenure":
            projection_df["metric_value"] = [
                self.employee_database.employees[emp_id].tenure
                for emp_id in employee_ids
            ]
        else:
            raise ValueError(f"Invalid metric: {metric}")
        
        # Generate hexbin plot
        fig, ax = plt.subplots(figsize=config.figsize)
        
        # Use hexbin to plot the data
        hb = ax.hexbin(
            projection_df["x"],
            projection_df["y"],
            C=projection_df["metric_value"] if metric != "similarity" else None,
            gridsize=config.gridsize,
            cmap=config.cmap,
            bins=config.bins,
            edgecolor=config.edgecolor,
            alpha=config.alpha
        )
        
        if config.colorbar:
            cb = plt.colorbar(hb, ax=ax)
            cb.set_label(metric.replace("_", " ").title())
        
        ax.set_title(config.title)
        ax.set_xlabel(f"Dimension 1 ({reduction_method.upper()})")
        ax.set_ylabel(f"Dimension 2 ({reduction_method.upper()})")
        
        # Save plot to file if requested
        if save_to_file:
            output_file = file_path or os.path.join(
                self.output_dir, f"employee_similarity_hexbin_{reduction_method}.png"
            )
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
        
        # Export data for Power BI if requested
        if export_data:
            output_data = export_path or os.path.join(
                self.output_dir, f"employee_similarity_hexbin_data_{reduction_method}.csv"
            )
            projection_df.to_csv(output_data, index=False)
        
        return fig, projection_df
    
    def generate_skill_distribution_hexbin(
        self,
        skill_ids: Optional[List[str]] = None,
        skill_categories: Optional[List[str]] = None,
        reduction_method: str = "umap",
        entity_type: str = "job",
        config: Optional[HexbinConfig] = None,
        save_to_file: bool = True,
        file_path: Optional[str] = None,
        export_data: bool = True,
        export_path: Optional[str] = None
    ) -> Tuple[plt.Figure, pd.DataFrame]:
        """
        Generate a hexbin plot showing the distribution of skills.
        
        Args:
            skill_ids: Skill IDs to include (all skills if None)
            skill_categories: Skill categories to include (all categories if None)
            reduction_method: Dimensionality reduction method ('pca', 'tsne', 'umap')
            entity_type: Type of entity to visualize ('job' or 'employee')
            config: Hexbin configuration
            save_to_file: Whether to save the visualization to a file
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
        
        # Use default config if none provided
        if config is None:
            config = HexbinConfig(
                title=f"Skill Distribution Hexbin ({entity_type.title()}s)",
                cmap="viridis",
                gridsize=50
            )
        
        # Filter skills
        filtered_skills = self.skill_taxonomy.skills.copy()
        if skill_ids:
            filtered_skills = {k: v for k, v in filtered_skills.items() if k in skill_ids}
        if skill_categories:
            filtered_skills = {
                k: v for k, v in filtered_skills.items() 
                if v.category in skill_categories
            }
        
        if not filtered_skills:
            raise ValueError("No skills found matching the criteria")
        
        # Create skill vector matrix
        skill_ids_list = list(filtered_skills.keys())
        
        if entity_type == "job":
            entities = self.job_architecture.jobs
            entity_label = "job"
        else:  # entity_type == "employee"
            entities = self.employee_database.employees
            entity_label = "employee"
        
        # Create matrix where each row is an entity and each column is a skill
        entity_skill_matrix = np.zeros((len(entities), len(skill_ids_list)))
        entity_ids = []
        entity_names = []
        entity_depts = []
        
        for i, (entity_id, entity) in enumerate(entities.items()):
            entity_ids.append(entity_id)
            entity_names.append(entity.title if entity_type == "job" else entity.name)
            entity_depts.append(entity.department)
            
            for j, skill_id in enumerate(skill_ids_list):
                if skill_id in entity.skills:
                    entity_skill_matrix[i, j] = 1
        
        # Apply dimensionality reduction
        if reduction_method == "pca":
            reduced_data = self.dim_reduction.pca(entity_skill_matrix)
        elif reduction_method == "tsne":
            reduced_data = self.dim_reduction.tsne(entity_skill_matrix)
        elif reduction_method == "umap":
            reduced_data = self.dim_reduction.umap(entity_skill_matrix)
        else:
            raise ValueError(f"Invalid reduction method: {reduction_method}")
        
        # Create dataframe with projection data
        projection_df = pd.DataFrame({
            f"{entity_label}_id": entity_ids,
            f"{entity_label}_name": entity_names,
            "department": entity_depts,
            "x": reduced_data[:, 0],
            "y": reduced_data[:, 1],
            "skill_count": entity_skill_matrix.sum(axis=1)
        })
        
        # Add individual skill columns for Power BI
        for j, skill_id in enumerate(skill_ids_list):
            skill_name = filtered_skills[skill_id].name
            projection_df[f"skill_{skill_id}"] = entity_skill_matrix[:, j]
            projection_df[f"skill_name_{skill_id}"] = skill_name
        
        # Generate hexbin plot
        fig, ax = plt.subplots(figsize=config.figsize)
        
        # Use hexbin to plot the data
        hb = ax.hexbin(
            projection_df["x"],
            projection_df["y"],
            C=projection_df["skill_count"],
            gridsize=config.gridsize,
            cmap=config.cmap,
            bins=config.bins,
            edgecolor=config.edgecolor,
            alpha=config.alpha
        )
        
        if config.colorbar:
            cb = plt.colorbar(hb, ax=ax)
            cb.set_label("Skill Count")
        
        ax.set_title(config.title)
        ax.set_xlabel(f"Dimension 1 ({reduction_method.upper()})")
        ax.set_ylabel(f"Dimension 2 ({reduction_method.upper()})")
        
        # Save plot to file if requested
        if save_to_file:
            output_file = file_path or os.path.join(
                self.output_dir, f"skill_distribution_hexbin_{entity_type}_{reduction_method}.png"
            )
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
        
        # Export data for Power BI if requested
        if export_data:
            output_data = export_path or os.path.join(
                self.output_dir, f"skill_distribution_hexbin_data_{entity_type}_{reduction_method}.csv"
            )
            projection_df.to_csv(output_data, index=False)
        
        return fig, projection_df
    
    def generate_skill_gap_hexbin(
        self,
        target_job_ids: List[str],
        reduction_method: str = "umap",
        max_employees: int = 5000,  # Limit to avoid memory issues
        config: Optional[HexbinConfig] = None,
        save_to_file: bool = True,
        file_path: Optional[str] = None,
        export_data: bool = True,
        export_path: Optional[str] = None
    ) -> Tuple[plt.Figure, pd.DataFrame]:
        """
        Generate a hexbin plot showing skill gaps between employees and target jobs.
        
        Args:
            target_job_ids: IDs of target jobs to compare against
            reduction_method: Dimensionality reduction method ('pca', 'tsne', 'umap')
            max_employees: Maximum number of employees to include
            config: Hexbin configuration
            save_to_file: Whether to save the visualization to a file
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
        
        # Use default config if none provided
        if config is None:
            config = HexbinConfig(
                title="Skill Gap Hexbin",
                cmap="coolwarm",
                gridsize=50
            )
        
        # Validate target jobs
        target_jobs = []
        for job_id in target_job_ids:
            if job_id not in self.job_architecture.jobs:
                raise ValueError(f"Job ID not found: {job_id}")
            target_jobs.append(self.job_architecture.jobs[job_id])
        
        # Limit number of employees if needed
        employee_list = list(self.employee_database.employees.items())
        if len(employee_list) > max_employees:
            # Sample employees to avoid memory issues
            np.random.seed(42)  # For reproducibility
            employee_list = np.random.choice(
                employee_list, size=max_employees, replace=False
            ).tolist()
        
        # Prepare data for visualization
        employee_ids = []
        employee_names = []
        employee_depts = []
        employee_job_ids = []
        employee_job_titles = []
        gap_scores = []
        skill_vectors = []
        
        for emp_id, employee in employee_list:
            employee_ids.append(emp_id)
            employee_names.append(employee.name)
            employee_depts.append(employee.department)
            employee_job_ids.append(employee.job_id)
            
            job_title = "Unknown"
            if employee.job_id in self.job_architecture.jobs:
                job_title = self.job_architecture.jobs[employee.job_id].title
            employee_job_titles.append(job_title)
            
            # Calculate gap scores for all target jobs
            employee_gap_scores = []
            for job in target_jobs:
                # Calculate skill match percentage (simplified)
                required_skills = set(job.skills.keys())
                employee_skills = set(employee.skills.keys())
                
                if not required_skills:
                    match_pct = 0
                else:
                    match_pct = len(required_skills.intersection(employee_skills)) / len(required_skills) * 100
                
                employee_gap_scores.append(match_pct)
            
            # Use average gap score across all target jobs
            gap_scores.append(np.mean(employee_gap_scores))
            
            # Store skill vector for dimensionality reduction
            skill_vectors.append(employee.skill_vector.to_array())
        
        # Apply dimensionality reduction
        skill_vectors_array = np.array(skill_vectors)
        
        if reduction_method == "pca":
            reduced_data = self.dim_reduction.pca(skill_vectors_array)
        elif reduction_method == "tsne":
            reduced_data = self.dim_reduction.tsne(skill_vectors_array)
        elif reduction_method == "umap":
            reduced_data = self.dim_reduction.umap(skill_vectors_array)
        else:
            raise ValueError(f"Invalid reduction method: {reduction_method}")
        
        # Create dataframe with projection data
        projection_df = pd.DataFrame({
            "employee_id": employee_ids,
            "employee_name": employee_names,
            "department": employee_depts,
            "current_job_id": employee_job_ids,
            "current_job_title": employee_job_titles,
            "x": reduced_data[:, 0],
            "y": reduced_data[:, 1],
            "avg_match_percentage": gap_scores
        })
        
        # Add individual job match columns for Power BI
        for i, job in enumerate(target_jobs):
            target_job_col = f"match_pct_{job.id}"
            projection_df[target_job_col] = [
                # Calculate match percentage for this specific job
                len(set(job.skills.keys()).intersection(set(self.employee_database.employees[emp_id].skills.keys()))) / 
                max(1, len(job.skills)) * 100  # Avoid division by zero
                for emp_id in employee_ids
            ]
            projection_df[f"target_job_title_{job.id}"] = job.title
        
        # Generate hexbin plot
        fig, ax = plt.subplots(figsize=config.figsize)
        
        # Use hexbin to plot the data
        hb = ax.hexbin(
            projection_df["x"],
            projection_df["y"],
            C=projection_df["avg_match_percentage"],
            gridsize=config.gridsize,
            cmap=config.cmap,
            bins=config.bins,
            edgecolor=config.edgecolor,
            alpha=config.alpha,
            vmin=0,
            vmax=100
        )
        
        if config.colorbar:
            cb = plt.colorbar(hb, ax=ax)
            cb.set_label("Average Match Percentage (%)")
        
        ax.set_title(config.title)
        ax.set_xlabel(f"Dimension 1 ({reduction_method.upper()})")
        ax.set_ylabel(f"Dimension 2 ({reduction_method.upper()})")
        
        # Save plot to file if requested
        if save_to_file:
            output_file = file_path or os.path.join(
                self.output_dir, f"skill_gap_hexbin_{reduction_method}.png"
            )
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
        
        # Export data for Power BI if requested
        if export_data:
            output_data = export_path or os.path.join(
                self.output_dir, f"skill_gap_hexbin_data_{reduction_method}.csv"
            )
            projection_df.to_csv(output_data, index=False)
        
        return fig, projection_df 
