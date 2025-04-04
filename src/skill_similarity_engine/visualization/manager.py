"""
Visualisation manager for generating various visualizations of skill and job data.
"""

import os
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from ..models.skills import SkillTaxonomy
from ..models.jobs import JobArchitecture
from ..similarity.cosine import CosineSimilarityCalculator
from .reports import DataExporter, ReportConfig

logger = logging.getLogger("skill_similarity_engine")


@dataclass
class VisualizationConfig:
    """Configuration for visualization generation."""
    output_dir: str
    color_scheme: str = "viridis"
    figsize: tuple = (10, 8)
    dpi: int = 300
    similarity_threshold: float = 0.0
    departments: Optional[List[str]] = None


class VisualisationManager:
    """Manages the generation of various visualizations for skill and job data."""
    
    def __init__(
        self,
        skill_taxonomy: SkillTaxonomy,
        job_architecture: JobArchitecture,
        output_dir: str,
        similarity_calculator: Optional[CosineSimilarityCalculator] = None
    ):
        """Initialize the visualization manager.
        
        Args:
            skill_taxonomy: The skill taxonomy to visualize
            job_architecture: The job architecture to visualize
            output_dir: Directory to save generated visualizations
            similarity_calculator: Calculator for job similarities (optional)
        """
        self.taxonomy = skill_taxonomy
        self.job_architecture = job_architecture
        self.calculator = similarity_calculator
        self.exporter = DataExporter(
            skill_taxonomy=skill_taxonomy,
            job_architecture=job_architecture,
            similarity_calculator=similarity_calculator,
            output_dir=output_dir
        )
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_job_similarity_heatmap(
        self,
        similarity_matrix: pd.DataFrame,
        department: Optional[str] = None,
        output_dir: str = ".",
        filename: str = "job_similarity_heatmap.png"
    ) -> None:
        """
        Generate a heatmap visualization of job similarities.
        
        Args:
            similarity_matrix: DataFrame containing similarity scores
            department: Optional department to filter by
            output_dir: Directory to save the visualization
            filename: Name of the output file
        """
        logger.debug(f"Generating heatmap for department: {department}")
        
        # Get the similarity matrix for the department if specified
        if department:
            df = self.exporter.export_job_similarity_matrix(
                department=department,
                config=ReportConfig(format="csv")
            )
        else:
            df = similarity_matrix
            
        # Log the initial similarity matrix structure
        logger.debug(f"Initial similarity matrix columns: {df.columns}")
        logger.debug(f"Sample of similarity scores:\n{df.head()}")
        
        # Extract job IDs and create a pivot table for the heatmap
        job1_col = 'job1_id' if 'job1_id' in df.columns else 'job_id_1'
        job2_col = 'job2_id' if 'job2_id' in df.columns else 'job_id_2'
        similarity_col = 'similarity' if 'similarity' in df.columns else 'similarity_score'
        
        # Create pivot table for heatmap
        heatmap_data = df.pivot(
            index=job1_col,
            columns=job2_col,
            values=similarity_col
        )
        
        # Log the pivot table structure
        logger.debug(f"Pivot table shape: {heatmap_data.shape}")
        logger.debug(f"Diagonal values: {[heatmap_data.loc[idx, idx] for idx in heatmap_data.index if idx in heatmap_data.columns]}")
        
        # Fill missing symmetric values (if job1->job2 exists but job2->job1 doesn't)
        for i in heatmap_data.index:
            for j in heatmap_data.columns:
                if pd.isna(heatmap_data.loc[i, j]) and not pd.isna(heatmap_data.loc[j, i]):
                    heatmap_data.loc[i, j] = heatmap_data.loc[j, i]
        
        # Create readable labels using job title and department
        index_labels = []
        column_labels = []
        
        for job_id in heatmap_data.index:
            job = self.job_architecture.get_job(job_id)
            # Use title and department from internal model
            job_title = job.title  # Using title instead of role_set
            department = job.department  # This is already the internal field name
            label = f"{job_title}\n({department})" if department else job_title
            index_labels.append(label)
            
        for job_id in heatmap_data.columns:
            job = self.job_architecture.get_job(job_id)
            # Use title and department from internal model
            job_title = job.title  # Using title instead of role_set
            department = job.department  # This is already the internal field name
            label = f"{job_title}\n({department})" if department else job_title
            column_labels.append(label)
        
        # Create heatmap with larger figure size to accommodate labels
        plt.figure(figsize=(15, 12))
        sns.heatmap(
            heatmap_data,
            annot=True,
            cmap='YlOrRd',
            fmt='.2f',
            square=True,
            cbar_kws={'label': 'Similarity Score'},
            xticklabels=column_labels,
            yticklabels=index_labels
        )
        
        # Customize plot
        plt.title(f'Job Similarity Heatmap{" - " + department if department else ""}')
        plt.xlabel('Jobs')
        plt.ylabel('Jobs')
        
        # Rotate x-axis labels for better readability and adjust font size
        plt.xticks(rotation=45, ha='right', fontsize=8)
        plt.yticks(rotation=0, fontsize=8)
        
        # Adjust layout to prevent label cutoff with more padding
        plt.tight_layout(pad=2.0)
        
        # Save plot with high DPI and tight bounding box
        output_path = os.path.join(output_dir, filename)
        plt.savefig(output_path, bbox_inches='tight', dpi=300)
        plt.close()
        
        logger.info(f"Saved heatmap to: {output_path}")
    
    def generate_hexbin_visualization(
        self,
        similarity_matrix: pd.DataFrame,
        department: Optional[str] = None,
        output_dir: str = ".",
        filename: str = "job_similarity_hexbin.png",
        color_scheme: str = "viridis",
        figsize: tuple = (10, 8),
        dpi: int = 300
    ) -> None:
        """Generate a hexbin visualization of job similarities.
        
        Args:
            similarity_matrix: DataFrame containing similarity scores
            department: Optional department to filter by
            output_dir: Directory to save the visualization
            filename: Name of the output file
            color_scheme: Matplotlib colormap name
            figsize: Figure size (width, height)
            dpi: Dots per inch for the output image
        """
        # Get job similarities for the department
        df = similarity_matrix
        if department:
            df = self.exporter.export_job_similarity_matrix(
                department=department,
                config=ReportConfig(format="csv")
            )
        
        # Create hexbin plot
        plt.figure(figsize=figsize)
        plt.hexbin(
            df.index,
            df.columns,
            C=df.values.flatten(),
            cmap=color_scheme,
            gridsize=20
        )
        plt.colorbar(label="Similarity")
        plt.title(f"Job Similarity Hexbin Plot{' - ' + department if department else ''}")
        plt.xlabel("Job ID 1")
        plt.ylabel("Job ID 2")
        plt.tight_layout()
        
        # Save plot
        output_path = os.path.join(output_dir, filename)
        plt.savefig(output_path, dpi=dpi)
        plt.close()
        
        logger.info(f"Saved hexbin plot to: {output_path}")
    
    def export_job_similarity_matrix(
        self,
        similarity_matrix: pd.DataFrame,
        department: Optional[str] = None,
        output_path: Optional[str] = None,
        config: Optional[ReportConfig] = None
    ) -> pd.DataFrame:
        """Export job similarity matrix to CSV or JSON.
        
        Args:
            similarity_matrix: DataFrame containing similarity scores
            department: Optional department to filter by
            output_path: Path to save the export (if None, auto-generated)
            config: Report configuration (if None, defaults to CSV)
            
        Returns:
            DataFrame containing the similarity matrix
        """
        if config is None:
            config = ReportConfig(format="csv")
        
        if output_path is None:
            output_path = os.path.join(
                self.output_dir,
                "job_similarity_matrix.csv"
            )
        
        # Get the similarity matrix
        df = similarity_matrix
        if department:
            df = self.exporter.export_job_similarity_matrix(
                department=department,
                config=config
            )
        
        # Save results if output path is provided
        if output_path:
            if config.format.lower() == "csv":
                df.to_csv(output_path)
            elif config.format.lower() == "json":
                df.to_json(output_path, orient="split", indent=2)
            elif config.format.lower() == "excel":
                df.to_excel(output_path)
        
        return df
    
    def generate_job_similarity_heatmap_all_departments(
        self,
        output_dir: str,
        filename: str = "heatmap_all_departments.png",
        figsize: Tuple[int, int] = (20, 16),
        group_by_department: bool = True
    ) -> str:
        """
        Generate a heatmap visualization of job similarities across all departments.
        
        Args:
            output_dir: Directory to save the visualization
            filename: Name of the output file
            figsize: Size of the figure as (width, height)
            group_by_department: Whether to group jobs by department
            
        Returns:
            Path to the saved visualization file
        """
        # Get similarity matrix from the exporter
        df = self.exporter.export_job_similarity_matrix_all_departments()
        
        # Create pivot table for heatmap
        pivot_df = pd.pivot_table(
            df,
            values='similarity',
            index='job1_id',
            columns='job2_id',
            fill_value=0
        )
        
        # Get job metadata for labels
        job_labels = {}
        department_boundaries = []
        current_pos = 0
        
        # Sort jobs by department if grouping
        jobs = list(self.job_architecture.jobs.values())
        if group_by_department:
            jobs.sort(key=lambda x: (x.department or "", x.title or ""))
            
            # Track department boundaries
            current_dept = None
            for job in jobs:
                if job.department != current_dept:
                    if current_pos > 0:
                        department_boundaries.append(current_pos - 0.5)
                    current_dept = job.department
                current_pos += 1
        
        # Create labels
        for job in jobs:
            label = f"{job.title}\n({job.department})" if job.department else job.title
            job_labels[job.job_id] = label
        
        # Reorder matrix to match sorted jobs
        job_ids = [job.job_id for job in jobs]
        pivot_df = pivot_df.reindex(index=job_ids, columns=job_ids)
        
        # Create figure
        plt.figure(figsize=figsize)
        
        # Create heatmap
        sns.heatmap(
            pivot_df,
            cmap='YlOrRd',
            xticklabels=[job_labels[job_id] for job_id in pivot_df.columns],
            yticklabels=[job_labels[job_id] for job_id in pivot_df.index],
            cbar_kws={'label': 'Similarity Score'}
        )
        
        # Add department boundary lines if grouping
        if group_by_department and department_boundaries:
            for boundary in department_boundaries:
                plt.axhline(y=boundary, color='black', linewidth=0.5)
                plt.axvline(x=boundary, color='black', linewidth=0.5)
        
        # Rotate labels
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        # Add title
        plt.title('Job Similarity Heatmap - All Departments', pad=20)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save visualization
        output_path = os.path.join(output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path 