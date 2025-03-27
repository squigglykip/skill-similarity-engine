"""
Example of using visualization features in production.
This code shows how to use the visualization components for generating
heatmaps and hexbin visualizations of job similarities.
"""

import sys
import os
import numpy as np

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
print(f"src path: {src_path}")  # Print the src path as confirmation
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pandas as pd
import matplotlib.pyplot as plt

from skill_similarity_engine.models.skills import Skill, SkillTaxonomy
from skill_similarity_engine.models.jobs import Job, JobArchitecture, JobLevel
from skill_similarity_engine.visualization.visualizer import VisualisationManager
from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator
from skill_similarity_engine.visualization.heatmaps import HeatmapConfig, SimilarityHeatmapGenerator
from skill_similarity_engine.visualization.hexbin import HexbinConfig

def setup_example_data():
    """Set up example skill taxonomy and job architecture."""
    # Create a simple skill taxonomy
    taxonomy = SkillTaxonomy()
    taxonomy.add_skill(Skill(skill_id="S001", name="Python"))
    taxonomy.add_skill(Skill(skill_id="S002", name="Data Analysis"))
    taxonomy.add_skill(Skill(skill_id="S003", name="Machine Learning"))
    
    # Create a simple job architecture
    job_arch = JobArchitecture()
    
    # Add example jobs
    jobs = [
        Job(
            job_id="J001",
            title="Data Scientist",
            department="Data",
            level=JobLevel.SENIOR,
            skills={"S001": 4, "S002": 5, "S003": 4}
        ),
        Job(
            job_id="J002",
            title="Data Engineer",
            department="Data",
            level=JobLevel.MID_LEVEL,
            skills={"S001": 5, "S002": 3}
        ),
        Job(
            job_id="J003",
            title="Machine Learning Engineer",
            department="AI",
            level=JobLevel.SENIOR,
            skills={"S001": 3, "S003": 5}
        ),
        Job(
            job_id="J004",
            title="AI Researcher",
            department="AI",
            level=JobLevel.SENIOR,
            skills={"S003": 5}
        )
    ]
    
    for job in jobs:
        job_arch.add_job(job)
    
    return taxonomy, job_arch

def main():
    """Main function demonstrating visualization features."""
    # Set up the data
    taxonomy, job_arch = setup_example_data()
    
    # Create output directory
    output_dir = "output/visualizations"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize the similarity calculator components
    vectorizer = TfidfVectorizer(taxonomy)
    similarity_calculator = CosineSimilarityCalculator(
        vectorizer=vectorizer,
        skill_taxonomy=taxonomy,
        job_architecture=job_arch
    )
    
    # Initialize the visualization manager
    vis_manager = VisualisationManager(
        skill_taxonomy=taxonomy,
        job_architecture=job_arch,
        output_dir=output_dir
    )
    
    # Calculate similarity matrix once
    similarity_matrix, matrix_job_ids = similarity_calculator.calculate_similarity_matrix("job")
    
    # 1. Generate a heatmap of job similarities
    print("Generating job similarity heatmap...")
    heatmap_path = os.path.join(output_dir, "job_similarity_heatmap.png")
    
    # Get job titles for labels
    job_titles = [job_arch.jobs[job_id].title for job_id in matrix_job_ids]
    
    # Create heatmap configuration
    config = HeatmapConfig(
        title="Job Similarity Heatmap",
        cmap="viridis",
        mask_diagonal=True,
        cluster=True,
        vmin=0.0,
        vmax=1.0
    )
    
    # Generate heatmap using the base heatmap generator
    fig = vis_manager._similarity_heatmap_generator.heatmap_generator.generate_heatmap(
        data=similarity_matrix,
        row_labels=job_titles,
        col_labels=job_titles,
        config=config,
        file_path=heatmap_path
    )
    print(f"Heatmap saved to: {heatmap_path}")
    
    # 2. Generate a hexbin visualization
    print("\nGenerating hexbin visualization...")
    hexbin_path = os.path.join(output_dir, "job_hexbin.png")
    
    fig, reduced_data = vis_manager.generate_job_similarity_hexbin(
        reduction_method="pca",
        file_path=hexbin_path
    )
    print(f"Hexbin visualization saved to: {hexbin_path}")
    
    # 3. Export similarity matrix
    print("\nExporting similarity matrix...")
    csv_path = os.path.join(output_dir, "job_similarity_matrix.csv")
    df = vis_manager.export_job_similarity_matrix(
        output_path=csv_path,
        threshold=0.5  # Only show pairs with similarity >= 0.5
    )
    print(f"Similarity matrix saved to: {csv_path}")
    print(f"Found {len(df)} job pairs with similarity >= 0.5")
    
    # 4. Show department-specific visualizations
    print("\nGenerating department-specific visualizations...")
    for dept in ["Data", "AI"]:
        dept_heatmap = os.path.join(output_dir, f"{dept.lower()}_heatmap.png")
        
        # Filter jobs by department
        dept_jobs = job_arch.get_jobs_by_department(dept)
        dept_job_ids = [job.job_id for job in dept_jobs]
        
        # Get indices of jobs to include
        indices = [i for i, job_id in enumerate(matrix_job_ids) if job_id in dept_job_ids]
        
        # Filter matrix and job IDs
        dept_matrix = similarity_matrix[np.ix_(indices, indices)]
        dept_job_ids = [matrix_job_ids[i] for i in indices]
        dept_job_titles = [job_arch.jobs[job_id].title for job_id in dept_job_ids]
        
        # Generate heatmap
        fig = vis_manager._similarity_heatmap_generator.heatmap_generator.generate_heatmap(
            data=dept_matrix,
            row_labels=dept_job_titles,
            col_labels=dept_job_titles,
            config=config,
            file_path=dept_heatmap
        )
        print(f"{dept} department heatmap saved to: {dept_heatmap}")

if __name__ == "__main__":
    main() 