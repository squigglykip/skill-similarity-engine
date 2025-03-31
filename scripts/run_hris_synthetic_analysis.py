#!/usr/bin/env python3
"""
Script for running similarity analysis on synthetic HRIS data.
This script transforms the synthetic data and runs the similarity analysis.
"""

import os
import sys
import click
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add the src directory to the path so we can import our package
src_path = str(Path(__file__).parent.parent / 'src')
sys.path.insert(0, src_path)

from skill_similarity_engine.models.skills import Skill, SkillTaxonomy
from skill_similarity_engine.models.jobs import Job, JobArchitecture, JobLevel, RoleTrack
from skill_similarity_engine.similarity import calculate_similarity_matrix

@click.group()
def cli():
    """Run similarity analysis on synthetic HRIS data."""
    pass

@cli.command()
@click.argument("jobs_file", type=click.Path(exists=True))
@click.argument("skills_file", type=click.Path(exists=True))
@click.argument("job_skills_file", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
@click.option("--config-file", type=click.Path(exists=True), 
              default="config/hris_schema_mapping.yaml",
              help="Path to HRIS schema mapping configuration file")
def run_analysis(jobs_file, skills_file, job_skills_file, output_dir, config_file):
    """Run similarity analysis on synthetic HRIS data."""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    click.echo("Loading data...")
    jobs_df = pd.read_csv(jobs_file)
    skills_df = pd.read_csv(skills_file)
    job_skills_df = pd.read_csv(job_skills_file)
    
    # Create job architecture
    click.echo("Creating job architecture...")
    job_arch = JobArchitecture()
    
    # Process each job
    for _, row in jobs_df.iterrows():
        job_id = row["JobID"]
        title = row["RoleSet"]
        department = row["Org Unit Name"]
        salary_group = row["Salary Group"]
        people_leader = row["People Leader Flag"]
        
        # Map salary group to level and PSA
        group_num = int(salary_group.split()[-1])
        level_mapping = {
            1: (JobLevel.ENTRY, "ENTRY"),
            2: (JobLevel.ASSOCIATE, "ENTRY"),
            3: (JobLevel.PROFESSIONAL, "MIDRANGE"),
            4: (JobLevel.PROFESSIONAL, "MIDRANGE"),
            5: (JobLevel.SENIOR, "SENIOR"),
            6: (JobLevel.PRINCIPAL, "LEADERSHIP"),
            7: (JobLevel.EXECUTIVE, "EXECUTIVE")
        }
        job_level, psa = level_mapping.get(group_num, (JobLevel.ASSOCIATE, "ENTRY"))
        
        # Map people leader flag to role track
        role_track = (RoleTrack.MANAGEMENT if people_leader == "People Leader" 
                     else RoleTrack.INDIVIDUAL_CONTRIBUTOR)
        
        # Get skills for this job
        job_skills = job_skills_df[job_skills_df["JobID"] == job_id]["Skill_ID"].tolist()
        skills_dict = {skill_id: 1 for skill_id in job_skills}  # Binary skill representation
        
        # Create job object
        job = Job(
            job_id=job_id,
            title=title,
            department=department,
            level=job_level,
            skills=skills_dict,
            pay_scale_area=psa,
            role_track=role_track
        )
        
        # Add to job architecture
        job_arch.add_job(job)
    
    # Create skills taxonomy
    click.echo("Creating skills taxonomy...")
    skills_taxonomy = SkillTaxonomy()
    
    for _, row in skills_df.iterrows():
        skill = Skill(
            skill_id=row["Skill_ID"],
            name=row["Skill_Name"],
            category=row["SkillType"],
            subcategory=row["Category"],
            subsubcategory=row["Subcategory"]
        )
        skills_taxonomy.add_skill(skill)
    
    # Calculate similarity matrix
    click.echo("Calculating similarity matrix...")
    similarity_matrix = calculate_similarity_matrix(job_arch, skills_taxonomy)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save similarity matrix
    similarity_file = os.path.join(output_dir, f"similarity_matrix_{timestamp}.csv")
    similarity_matrix.to_csv(similarity_file)
    
    # Generate top similar jobs for each job
    top_similar_file = os.path.join(output_dir, f"top_similar_jobs_{timestamp}.csv")
    top_similar = []
    
    for job_id in similarity_matrix.index:
        similar_jobs = similarity_matrix.loc[job_id].sort_values(ascending=False)[1:11]
        for similar_id, similarity in similar_jobs.items():
            top_similar.append({
                "JobID": job_id,
                "SimilarJobID": similar_id,
                "Similarity": similarity
            })
    
    pd.DataFrame(top_similar).to_csv(top_similar_file, index=False)
    
    click.echo(f"\nAnalysis complete. Results saved to:")
    click.echo(f"- Similarity matrix: {similarity_file}")
    click.echo(f"- Top similar jobs: {top_similar_file}")

if __name__ == "__main__":
    cli() 