"""
Visualisation manager for generating various visualizations of skill and job data.
"""

import os
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Optional, Dict, Any
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
                department=department,
                config=ReportConfig(format="csv")
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
                similarity_matrix,
                department=department
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