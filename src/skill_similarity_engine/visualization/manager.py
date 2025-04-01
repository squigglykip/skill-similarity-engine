"""
Visualisation manager for generating various visualizations of skill and job data.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture
from skill_similarity_engine.similarity.cosine import CosineSimilarityCalculator
from skill_similarity_engine.visualization.reports import DataExporter, ReportConfig


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
        similarity_calculator: CosineSimilarityCalculator,
        output_dir: str
    ):
        """Initialize the visualization manager.
        
        Args:
            skill_taxonomy: The skill taxonomy to visualize
            job_architecture: The job architecture to visualize
            similarity_calculator: Calculator for job similarities
            output_dir: Directory to save generated visualizations
        """
        self.taxonomy = skill_taxonomy
        self.job_arch = job_architecture
        self.calculator = similarity_calculator
        self.exporter = DataExporter(
            skill_taxonomy=skill_taxonomy,
            job_architecture=job_architecture,
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
                similarity_matrix,
                department=department
            )
        else:
            df = similarity_matrix
        
        # Create heatmap
        plt.figure(figsize=(12, 10))
        sns.heatmap(
            df,
            annot=True,
            cmap='YlOrRd',
            fmt='.2f',
            square=True,
            cbar_kws={'label': 'Similarity Score'}
        )
        
        # Customize plot
        plt.title(f'Job Similarity Heatmap{" - " + department if department else ""}')
        plt.xlabel('Jobs')
        plt.ylabel('Jobs')
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save plot
        output_path = os.path.join(output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Saved heatmap to: {output_path}")
    
    def generate_hexbin_visualization(
        self,
        department: str,
        output_path: Optional[str] = None,
        color_scheme: str = "viridis",
        figsize: tuple = (10, 8),
        dpi: int = 300
    ) -> str:
        """Generate a hexbin visualization of job similarities.
        
        Args:
            department: Department to visualize
            output_path: Path to save the visualization (if None, auto-generated)
            color_scheme: Matplotlib colormap name
            figsize: Figure size (width, height)
            dpi: Dots per inch for the output image
            
        Returns:
            Path to the generated visualization
        """
        # Get job similarities for the department
        df = self.exporter.export_job_similarity_matrix(
            department=department,
            config=ReportConfig(format="csv")
        )
        
        # Create hexbin plot
        plt.figure(figsize=figsize)
        
        # Determine column names based on what's in the DataFrame
        job1_col = "job1_id" if "job1_id" in df.columns else "job_id_1"
        job2_col = "job2_id" if "job2_id" in df.columns else "job_id_2"
        similarity_col = "similarity" if "similarity" in df.columns else "similarity_score"
        
        plt.hexbin(
            df[job1_col],
            df[job2_col],
            C=df[similarity_col],
            cmap=color_scheme,
            gridsize=20
        )
        plt.colorbar(label="Similarity")
        plt.title(f"Job Similarity Hexbin Plot - {department}")
        plt.xlabel("Job ID 1")
        plt.ylabel("Job ID 2")
        plt.tight_layout()
        
        # Save the plot
        if output_path is None:
            output_path = os.path.join(
                self.output_dir,
                f"job_similarity_hexbin_{department.lower()}.png"
            )
        plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
        plt.close()
        
        return output_path
    
    def export_job_similarity_matrix(
        self,
        department: Optional[str] = None,
        departments: Optional[List[str]] = None,
        threshold: float = 0.0,
        output_path: Optional[str] = None,
        config: Optional[ReportConfig] = None
    ) -> pd.DataFrame:
        """Export job similarity matrix to CSV or JSON.
        
        Args:
            department: Single department to include (for backward compatibility)
            departments: List of departments to include (None for all)
            threshold: Minimum similarity to include
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
        
        # Handle either single department or list of departments
        used_department = None
        if department:
            used_department = department
        elif departments and len(departments) > 0:
            used_department = departments[0]  # Just use the first department for now
        
        # Get the similarity matrix
        df = self.exporter.export_job_similarity_matrix(
            department=used_department,
            config=config,
            output_path=output_path
        )
        
        # Apply threshold if specified
        if threshold > 0:
            df = df[df["similarity"] >= threshold]
        
        # Save filtered results if output path is provided
        if output_path:
            if config.format.lower() == "csv":
                df.to_csv(output_path, index=False)
            elif config.format.lower() == "json":
                df.to_json(output_path, orient="records", indent=2)
            elif config.format.lower() == "excel":
                df.to_excel(output_path, index=False)
        
        return df 